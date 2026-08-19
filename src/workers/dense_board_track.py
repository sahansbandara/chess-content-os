"""Dense per-square board tracking with temporal smoothing.

Why this exists. The earlier scanners spawn one ffmpeg process per timestamp,
which made dense sampling impractical, so sampling stayed at 0.25-0.5s. Coarse
sampling is exactly what makes extraction fragile: a single misclassified frame
becomes a "state", and a state that happens to be legally reachable silently
injects moves that were never played.

Observed in the prototype recording at 36.0s: a white pawn on c5 read as a
BISHOP on c6 for one frame, with a pawn on c6 before and after. Pieces do not
transmute. Also at 27.5s a rook read as a pawn.

Two changes, and they reinforce each other:

1. One ffmpeg pass decodes the cropped board at a fixed rate, so sampling can be
   dense without paying a process spawn per frame.
2. Each square is then smoothed over time by majority vote. A piece that appears
   for one frame out of five is noise, not a move. This removes both animation
   transients (a piece mid-flight reads as absent) and one-off misreads.

Run:
  uv run python src/workers/dense_board_track.py <video> --start 0 --end 41.4
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np

WORKERS = Path(__file__).resolve().parent
if str(WORKERS) not in sys.path:
    sys.path.insert(0, str(WORKERS))

import chess  # noqa: E402

from duolingo_board_scanner import calculate_thresholds, classify_piece, load_templates  # noqa: E402
from duolingo_color_template_bootstrap import extract_square  # noqa: E402
from duolingo_template_bootstrap import create_piece_mask, probe_resolution  # noqa: E402

DEFAULT_PROFILE = Path("assets/templates/duolingo_v2/profile.json")
SQUARES = [f"{f}{r}" for r in range(1, 9) for f in "abcdefgh"]


def decode_board_frames(video_path, board_top, board_size, fps, start, end):
    """Yield cropped board frames from a single ffmpeg pass."""
    cmd = [
        "ffmpeg", "-v", "error",
        "-ss", str(start), "-to", str(end),
        "-i", str(video_path),
        "-vf", f"crop={board_size}:{board_size}:0:{board_top},fps={fps}",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ]
    nbytes = board_size * board_size * 3
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    try:
        while True:
            buf = proc.stdout.read(nbytes)
            if not buf or len(buf) < nbytes:
                break
            yield np.frombuffer(buf, dtype=np.uint8).reshape(board_size, board_size, 3)
    finally:
        proc.stdout.close()
        proc.wait()


def classify_frame(frame, profile, templates, empty_threshold, color_threshold, square_size):
    """Per-square symbol for one frame. None means empty."""
    out = {}
    for name in SQUARES:
        image = extract_square(
            frame=frame, board_top=0, square_size=square_size,
            square=name, orientation=profile["orientation"],
        )
        mask = create_piece_mask(image)
        if float(mask.mean()) < empty_threshold:
            out[name] = None
            continue
        result = classify_piece(
            image=image, mask=mask, templates=templates, color_threshold=color_threshold,
        )
        out[name] = result["symbol"] if result else None
    return out


def smooth(tracks, window):
    """Majority vote per square over a centred window. Kills one-frame artefacts."""
    n = len(tracks)
    half = window // 2
    smoothed = []
    for i in range(n):
        lo, hi = max(0, i - half), min(n, i + half + 1)
        frame = {}
        for sq in SQUARES:
            votes = Counter(tracks[j][sq] for j in range(lo, hi))
            frame[sq] = votes.most_common(1)[0][0]
        smoothed.append(frame)
    return smoothed


def to_fen(frame):
    board = chess.Board(None)
    for sq, sym in frame.items():
        if sym:
            board.set_piece_at(chess.parse_square(sq), chess.Piece.from_symbol(sym))
    return board.board_fen()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video", type=Path)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--fps", type=float, default=10.0)
    ap.add_argument("--window", type=int, default=5, help="smoothing window in frames (odd)")
    ap.add_argument("--min-hold", type=int, default=3, help="frames a state must persist to be real")
    ap.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    video = args.video.expanduser().resolve()
    profile, templates = load_templates(args.profile.expanduser().resolve())
    empty_threshold, color_threshold = calculate_thresholds(templates)
    width, height = probe_resolution(video)

    board_top = round(height * float(profile["board_top_ratio"]))
    board_size = width
    square_size = width // 8

    print(f"decoding {args.start}-{args.end}s @ {args.fps}fps, board {board_size}px crop at y={board_top}")

    raw = []
    for i, frame in enumerate(decode_board_frames(video, board_top, board_size, args.fps, args.start, args.end)):
        raw.append(classify_frame(frame, profile, templates, empty_threshold, color_threshold, square_size))
        if i % 50 == 0:
            print(f"  frame {i}", flush=True)

    print(f"classified {len(raw)} frames; smoothing with window={args.window}")
    sm = smooth(raw, args.window)

    raw_fens = [to_fen(f) for f in raw]
    sm_fens = [to_fen(f) for f in sm]

    def runs_of(fens):
        runs = []
        for i, f in enumerate(fens):
            t = args.start + i / args.fps
            if runs and runs[-1]["board_fen"] == f:
                runs[-1]["t_end"] = round(t, 3)
                runs[-1]["frames"] += 1
            else:
                runs.append({"t_start": round(t, 3), "t_end": round(t, 3), "board_fen": f, "frames": 1})
        return runs

    raw_runs = runs_of(raw_fens)
    sm_runs = [r for r in runs_of(sm_fens) if r["frames"] >= args.min_hold]

    print(f"\nraw:      {len(raw_runs)} states")
    print(f"smoothed: {len(runs_of(sm_fens))} states, {len(sm_runs)} after dropping holds < {args.min_hold} frames")

    for i, r in enumerate(sm_runs, 1):
        print(f"  S{i:02d} {r['t_start']:>6.2f}-{r['t_end']:<6.2f} x{r['frames']:<3} {r['board_fen']}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({
            "window": [args.start, args.end], "fps": args.fps,
            "smoothing_window": args.window, "min_hold": args.min_hold,
            "raw_state_count": len(raw_runs), "runs": sm_runs,
        }, indent=2) + "\n")
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
