"""Extract a game from a recording in overlapping chunks, verified at the seams.

The idea is the owner's: cut the recording into chunks, analyse each one on its
own, then check that consecutive chunks agree about the board where they meet.
If they disagree, that chunk is wrong and gets retried rather than trusted.

Three deliberate departures from the original sketch:

1. The file is never split. ffmpeg seeks inside the original, so there is no
   re-encode. Writing chunk files would shift timestamps and soften the piece
   edges the templates match against — degrading the very thing being measured.

2. Chunks OVERLAP rather than butting together. A cut at exactly 10.0s can land
   mid-move, so both sides see a piece in flight and the seam fails for a reason
   that is not a real error. With an overlap, the two chunks must agree across a
   shared span, which is a much stronger check than comparing one endpoint.

3. Retry means something specific — denser sampling and a wider smoothing window
   — not the same computation repeated. If it still disagrees the seam is
   reported unresolved for a human, never guessed.

A verified seam is a real checksum: two independent passes over different frames
reached the same board. That is evidence, and it is recorded as such.

Run:
  uv run python src/workers/chunked_extract.py <video> --duration 41.4
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKERS = Path(__file__).resolve().parent
if str(WORKERS) not in sys.path:
    sys.path.insert(0, str(WORKERS))

import chess  # noqa: E402

from dense_board_track import (  # noqa: E402
    DEFAULT_PROFILE, calculate_thresholds, classify_frame, decode_board_frames,
    load_templates, probe_resolution, smooth, to_fen,
)

CHUNK_S = 10.0
OVERLAP_S = 1.0
RETRY = [
    {"fps": 10.0, "window": 5, "min_hold": 3},   # first attempt
    {"fps": 20.0, "window": 9, "min_hold": 5},   # denser + smoother
    {"fps": 30.0, "window": 13, "min_hold": 7},  # last automatic attempt
]


def track_window(video, profile, templates, thresholds, geom, start, end, fps, window, min_hold):
    empty_threshold, color_threshold = thresholds
    board_top, board_size, square_size = geom

    raw = [
        classify_frame(f, profile, templates, empty_threshold, color_threshold, square_size)
        for f in decode_board_frames(video, board_top, board_size, fps, start, end)
    ]
    if not raw:
        return []

    fens = [to_fen(f) for f in smooth(raw, window)]

    runs = []
    for i, fen in enumerate(fens):
        t = start + i / fps
        if runs and runs[-1]["board_fen"] == fen:
            runs[-1]["t_end"] = round(t, 3)
            runs[-1]["frames"] += 1
        else:
            runs.append({"t_start": round(t, 3), "t_end": round(t, 3), "board_fen": fen, "frames": 1})
    return [r for r in runs if r["frames"] >= min_hold]


def states_in(runs, lo, hi):
    """Distinct board states observed inside a time span, in order."""
    seen, out = set(), []
    for r in runs:
        if r["t_end"] >= lo and r["t_start"] <= hi and r["board_fen"] not in seen:
            seen.add(r["board_fen"])
            out.append(r["board_fen"])
    return out


def seam_agrees(prev_runs, next_runs, lo, hi):
    """Do the two chunks agree about the board in the span they share?"""
    a, b = states_in(prev_runs, lo, hi), states_in(next_runs, lo, hi)
    if not a or not b:
        return False, a, b
    return bool(set(a) & set(b)), a, b


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video", type=Path)
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--chunk", type=float, default=CHUNK_S)
    ap.add_argument("--overlap", type=float, default=OVERLAP_S)
    ap.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    ap.add_argument("--out", type=Path, default=Path("logs/chunked_extract.json"))
    args = ap.parse_args()

    video = args.video.expanduser().resolve()
    profile, templates = load_templates(args.profile.expanduser().resolve())
    thresholds = calculate_thresholds(templates)
    width, height = probe_resolution(video)
    geom = (round(height * float(profile["board_top_ratio"])), width, width // 8)

    bounds = []
    t = 0.0
    while t < args.duration:
        bounds.append((round(t, 2), round(min(t + args.chunk + args.overlap, args.duration), 2)))
        t += args.chunk

    print(f"{len(bounds)} chunks of {args.chunk}s with {args.overlap}s overlap\n")

    chunks = []
    for i, (lo, hi) in enumerate(bounds):
        for attempt, cfg in enumerate(RETRY, 1):
            runs = track_window(video, profile, templates, thresholds, geom, lo, hi, **cfg)

            if i == 0:
                ok, a, b = True, [], []
            else:
                seam_lo, seam_hi = bounds[i][0], bounds[i - 1][1]
                ok, a, b = seam_agrees(chunks[-1]["runs"], runs, seam_lo, seam_hi)

            if ok:
                print(f"  chunk {i+1} [{lo:>5.1f}-{hi:<5.1f}] {len(runs):>3} states  "
                      f"attempt {attempt} @ {cfg['fps']:.0f}fps  seam {'OK' if i else '-'}")
                chunks.append({"index": i, "start": lo, "end": hi, "attempt": attempt,
                               "config": cfg, "seam_verified": bool(i), "runs": runs})
                break
            if attempt == len(RETRY):
                print(f"  chunk {i+1} [{lo:>5.1f}-{hi:<5.1f}] SEAM UNRESOLVED after {attempt} attempts")
                print(f"      prev chunk saw: {a[:2]}")
                print(f"      this chunk saw: {b[:2]}")
                chunks.append({"index": i, "start": lo, "end": hi, "attempt": attempt,
                               "config": cfg, "seam_verified": False,
                               "seam_prev": a, "seam_this": b, "runs": runs})

    verified = sum(1 for c in chunks[1:] if c["seam_verified"])
    print(f"\n{verified}/{len(chunks)-1} seams verified")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        "video": str(video.name), "duration_s": args.duration,
        "chunk_s": args.chunk, "overlap_s": args.overlap,
        "seams_verified": verified, "seams_total": len(chunks) - 1,
        "chunks": chunks,
    }, indent=2) + "\n")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
