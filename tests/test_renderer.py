"""Renderer guarantees.

Slow — these launch Chromium. Run with:  uv run pytest -m renderer
Skipped by default so the fast contract suite stays instant.
"""

import hashlib
import json

import chess
import pytest

pytestmark = pytest.mark.renderer

playwright = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402

from src.renderer.render_short import (  # noqa: E402
    TEMPLATE, build_scene, mascot_sprites, piece_sprites, warm_up,
)

SQ = 90  # the board is 720px across, eight squares


def init_page(page, scene):
    """Set the page up exactly the way render_short does, art included."""
    page.add_init_script(
        f"window.__SCENE__ = {json.dumps(scene)};\n"
        f"window.__PIECE_ART__ = {json.dumps(piece_sprites())};\n"
        f"window.__MASCOT_ART__ = {json.dumps(mascot_sprites())};"
    )
    page.goto(TEMPLATE.as_uri())


def test_original_teen_mascot_has_both_required_emotional_states():
    art = mascot_sprites()

    assert set(art) == {"confident", "regretful"}
    assert all(uri.startswith("data:image/png;base64,") for uri in art.values())


def test_renderer_never_alters_the_move_sequence():
    """design.md: if the renderer changes move truth, reject the renderer."""
    doc = json.loads((TEMPLATE.parents[2] / "tests/fixtures/prototype_moves.json").read_text())
    truth = [(m["ply"], m["uci"], m["san"]) for m in doc["moves"] if m["verification_status"] != "unresolved"]

    scene = build_scene()
    rendered = [(i + 1, m["from"] + m["to"], m["san"]) for i, m in enumerate(scene["moves"])]

    assert rendered == truth


def test_scene_only_contains_moves_the_contract_allows():
    """No unresolved ply may reach the renderer."""
    doc = json.loads((TEMPLATE.parents[2] / "tests/fixtures/prototype_moves.json").read_text())
    unresolved = {m["san"] for m in doc["moves"] if m["verification_status"] == "unresolved"}

    scene = build_scene()

    assert not ({m["san"] for m in scene["moves"]} & unresolved)


def test_board_matches_python_chess_at_the_starting_position():
    """Every piece on the right square, in the right colour."""
    scene = build_scene()
    board = chess.Board(None)
    board.set_board_fen("r1b1r1k1/pp3ppp/8/3rP3/4n3/1BB5/PPP2PPP/2KR3R")
    expected = {chess.square_name(s): p.symbol() for s, p in board.piece_map().items()}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        init_page(page, scene)
        warm_up(page)
        page.evaluate("n => renderFrame(n)", 20)
        rendered = page.evaluate(
            """() => [...document.querySelectorAll('#pieces .pc')].map(d => ({
                left: parseFloat(d.style.left), top: parseFloat(d.style.top),
                piece: d.dataset.piece}))"""
        )
        browser.close()

    got = {
        (round(d["left"] / SQ), round(d["top"] / SQ)): ("white" if d["piece"].isupper() else "black")
        for d in rendered
    }
    assert len(rendered) == len(expected)

    for square, symbol in expected.items():
        f, r = ord(square[0]) - 97, int(square[1])
        cell = (7 - f, r - 1) if scene["flip"] else (f, 8 - r)
        assert got[cell] == ("white" if symbol.isupper() else "black"), f"{square} ({symbol})"


def test_identical_input_produces_byte_identical_frames():
    """The determinism guarantee in design.md, enforced.

    Regression guard for a real bug: Chromium's first screenshot after page load
    antialiases the SVG pieces differently from every later one, so without a
    warm-up pass frame 0 of one render differed from frame 0 of the next.
    """
    scene = build_scene()
    probe = [0, 133, 401]

    def run():
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1080, "height": 1920})
            init_page(page, scene)
            warm_up(page)
            out = {}
            for n in probe:
                page.evaluate("n => renderFrame(n)", n)
                out[n] = hashlib.sha256(page.screenshot()).hexdigest()
            browser.close()
            return out

    first, second = run(), run()

    assert first == second
