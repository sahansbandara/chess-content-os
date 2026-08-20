"""Render a 1080x1920 short from moves.json + analysis.json.

The renderer never reads pixels and never touches move truth. It builds a scene
from the two contract files, drives scene.html one frame at a time through an
explicit renderFrame(n) call, screenshots each frame, and muxes with FFmpeg.

Determinism: no wall-clock animation anywhere. Frame n always renders identically,
so the same inputs always produce the same video.

Run:  uv run python -m src.renderer.render_short
"""

import base64
import json
import subprocess
from pathlib import Path

import chess
from playwright.sync_api import sync_playwright

from src.validators.moves_contract import validate_moves

ROOT = Path(__file__).resolve().parents[2]
MOVES = ROOT / "tests/fixtures/prototype_moves.json"
TEMPLATE = ROOT / "src/renderer/scene.html"
SPRITES = ROOT / "assets/renderer/pieces/sprites"

W, H, FPS = 1080, 1920, 30
HOOK_S = 1.6      # hold on the starting position before the first move
STEP_S = 0.95     # time per ply
SLIDE_S = 0.55    # of which this much is the piece actually travelling
OUTRO_S = 2.0

HOOK = "I was already losing<br>and I had no idea"
OPENING_CAPTION = "White is two pawns up before this clip even starts."


def build_scene(moves_path=None, hook=None, opening_caption=None):
    doc = json.loads(Path(moves_path or MOVES).read_text())
    doc = dict(doc)
    doc["moves"] = [m for m in doc["moves"] if m["verification_status"] != "unresolved"]

    errors = validate_moves(doc)
    if errors:
        raise SystemExit(f"refusing to render: {len(errors)} contract failures: {errors[:3]}")

    analysis_path = ROOT / "output/content" / doc["content_id"] / "analysis.json"
    analysis = {a["ply"]: a for a in json.loads(analysis_path.read_text())["moves"]}

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
        "hook": hook or HOOK,
        "opening_caption": opening_caption or OPENING_CAPTION,
        "moves": moves,
        "content_id": doc["content_id"],
    }


def piece_sprites(sprite_dir=None):
    """Load the piece art as data URIs, keyed by the FEN symbol.

    Inlined rather than referenced by path: the page is loaded over file://,
    where a relative image request is a separate load the screenshot can race.
    A data URI is part of the document, so once the page has parsed the bytes
    are already there. Missing art is not an error — the scene falls back to its
    own vector glyphs, which is what shipped before this set arrived.
    """
    sprite_dir = Path(sprite_dir or SPRITES)
    if not sprite_dir.is_dir():
        return {}

    out = {}
    for path in sorted(sprite_dir.glob("[wb][KQRBNP].png")):
        colour, letter = path.stem[0], path.stem[1]
        symbol = letter if colour == "w" else letter.lower()
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        out[symbol] = f"data:image/png;base64,{encoded}"
    return out


def caption_for(m, a):
    """Captions are built from engine facts only. Never invented."""
    label = a.get("label")
    if label == "inaccuracy":
        return f"{m['san']} — inaccuracy. {a['best_move_san']} was better."
    if label in ("mistake", "blunder"):
        return f"{m['san']} — {label}. {a['best_move_san']} was the move."
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


def render(moves_path=None, hook=None, opening_caption=None):
    scene = build_scene(moves_path, hook, opening_caption)
    out_dir = ROOT / "output/content" / scene["content_id"]
    frame_dir = out_dir / "frames"
    video = out_dir / "short.mp4"
    total_frames = int((HOOK_S + len(scene["moves"]) * STEP_S + OUTRO_S) * FPS)

    frame_dir.mkdir(parents=True, exist_ok=True)
    for old in frame_dir.glob("*.png"):
        old.unlink()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.add_init_script(
            f"window.__SCENE__ = {json.dumps(scene)};\n"
            f"window.__PIECE_ART__ = {json.dumps(piece_sprites())};"
        )
        page.goto(TEMPLATE.as_uri())
        warm_up(page)

        for n in range(total_frames):
            page.evaluate("n => renderFrame(n)", n)
            page.screenshot(path=str(frame_dir / f"f{n:05d}.png"))
            if n % 60 == 0:
                print(f"  frame {n}/{total_frames}", flush=True)

        browser.close()

    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-framerate", str(FPS),
            "-i", str(frame_dir / "f%05d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            "-movflags", "+faststart",
            str(video),
        ],
        check=True,
    )
    return total_frames, video


if __name__ == "__main__":
    import sys
    mp = sys.argv[1] if len(sys.argv) > 1 else None
    hk = sys.argv[2] if len(sys.argv) > 2 else None
    oc = sys.argv[3] if len(sys.argv) > 3 else None
    frames, video = render(mp, hk, oc)
    print(f"\nrendered {frames} frames -> {video}")
