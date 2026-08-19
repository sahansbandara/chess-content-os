"""Render a 1080x1920 short from moves.json + analysis.json.

The renderer never reads pixels and never touches move truth. It builds a scene
from the two contract files, drives scene.html one frame at a time through an
explicit renderFrame(n) call, screenshots each frame, and muxes with FFmpeg.

Determinism: no wall-clock animation anywhere. Frame n always renders identically,
so the same inputs always produce the same video.

Run:  uv run python -m src.renderer.render_short
"""

import json
import subprocess
from pathlib import Path

import chess
from playwright.sync_api import sync_playwright

from src.validators.moves_contract import validate_moves

ROOT = Path(__file__).resolve().parents[2]
MOVES = ROOT / "tests/fixtures/prototype_moves.json"
ANALYSIS = ROOT / "output/content/2026-08-19-duolingo-001/analysis.json"
TEMPLATE = ROOT / "src/renderer/scene.html"
OUT_DIR = ROOT / "output/content/2026-08-19-duolingo-001"
FRAME_DIR = OUT_DIR / "frames"
VIDEO = OUT_DIR / "short.mp4"

W, H, FPS = 1080, 1920, 30
HOOK_S = 1.6      # hold on the starting position before the first move
STEP_S = 0.95     # time per ply
SLIDE_S = 0.55    # of which this much is the piece actually travelling
OUTRO_S = 2.0

HOOK = "I was already losing<br>and I had no idea"
OPENING_CAPTION = "White is two pawns up before this clip even starts."


def build_scene():
    doc = json.loads(MOVES.read_text())
    doc = dict(doc)
    doc["moves"] = [m for m in doc["moves"] if m["verification_status"] != "unresolved"]

    errors = validate_moves(doc)
    if errors:
        raise SystemExit(f"refusing to render: {len(errors)} contract failures: {errors[:3]}")

    analysis = {a["ply"]: a for a in json.loads(ANALYSIS.read_text())["moves"]}

    board = chess.Board(None)
    board.set_board_fen(doc["start_position"]["piece_placement"]["value"])
    board.turn = chess.WHITE if doc["start_position"]["side_to_move"]["value"] == "w" else chess.BLACK

    moves = []
    for m in doc["moves"]:
        mv = chess.Move.from_uci(m["uci"])
        before = {chess.square_name(sq): p.symbol() for sq, p in board.piece_map().items()}

        captured_square = captured_piece = None
        if board.is_capture(mv):
            cap_sq = chess.square_name(chess.parse_square(m["uci"][2:4]))
            if board.is_en_passant(mv):
                cap_sq = chess.square_name(mv.to_square + (-8 if board.turn == chess.WHITE else 8))
            captured_square = cap_sq
            captured_piece = before.get(cap_sq)

        a = analysis.get(m["ply"], {})
        # eval is stored from the mover's point of view; normalise to White
        wp = a.get("win_percent_after", 50.0)
        white_win = wp if m["side"] == "w" else 100.0 - wp

        moves.append(
            {
                "number": f"{(m['ply'] + 1) // 2}.{'' if m['side'] == 'w' else '..'}",
                "san": m["san"],
                "from": m["uci"][:2],
                "to": m["uci"][2:4],
                "piece": before[m["uci"][:2]],
                "captured_square": captured_square,
                "captured_piece": captured_piece,
                "before": before,
                "white_win": round(white_win, 2),
                "caption": caption_for(m, a),
            }
        )
        board.push(mv)

    return {
        "fps": FPS,
        # a1 is bottom-left for White, top-right for Black
        "flip": doc["owner_side"] == "black",
        "hook_s": HOOK_S,
        "step_s": STEP_S,
        "slide_s": SLIDE_S,
        "hook": HOOK,
        "opening_caption": OPENING_CAPTION,
        "moves": moves,
    }


def caption_for(m, a):
    """Captions are built from engine facts only. Never invented."""
    label = a.get("label")
    if label == "inaccuracy":
        return f"{m['san']} — inaccuracy. {a['best_move_san']} was better."
    if label in ("mistake", "blunder"):
        return f"{m['san']} — {label}. {a['best_move_san']} was the move."
    if m["side"] == "b":
        return f"{m['san']}. Still losing, still not seeing it."
    return f"{m['san']}."


def warm_up(page, shots=3):
    """Discard the first few captures so the raster cache is warm.

    Chromium's first screenshot after load antialiases the SVG pieces slightly
    differently from every subsequent one — measured at ~700 px, max channel
    delta 41, confined to the board. It settles after the first capture and is
    then byte-stable. Without this, frame 0 of a render is subtly different from
    the same frame produced by any later run, which breaks the determinism
    guarantee in design.md.
    """
    for _ in range(shots):
        page.evaluate("n => renderFrame(n)", 0)
        page.screenshot()


def render():
    scene = build_scene()
    total_frames = int((HOOK_S + len(scene["moves"]) * STEP_S + OUTRO_S) * FPS)

    FRAME_DIR.mkdir(parents=True, exist_ok=True)
    for old in FRAME_DIR.glob("*.png"):
        old.unlink()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.add_init_script(f"window.__SCENE__ = {json.dumps(scene)};")
        page.goto(TEMPLATE.as_uri())
        warm_up(page)

        for n in range(total_frames):
            page.evaluate("n => renderFrame(n)", n)
            page.screenshot(path=str(FRAME_DIR / f"f{n:05d}.png"))
            if n % 60 == 0:
                print(f"  frame {n}/{total_frames}", flush=True)

        browser.close()

    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-framerate", str(FPS),
            "-i", str(FRAME_DIR / "f%05d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            "-movflags", "+faststart",
            str(VIDEO),
        ],
        check=True,
    )
    return total_frames


if __name__ == "__main__":
    frames = render()
    print(f"\nrendered {frames} frames -> {VIDEO}")
