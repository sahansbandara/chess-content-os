"""Scan an arbitrary time window of a recording into a board-state sequence.

The existing duolingo_state_sequence_probe auto-detects the rapid replay cluster
and scans only that. This scans whatever window you ask for, which is what you
need to look at the parts of a recording nobody has reconstructed yet.

New file rather than a modification: the rapid-cluster probe works and is the
basis of the existing verified sequence.

Run:
  uv run python src/workers/scan_time_window.py <video> --start 0 --end 13.5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKERS = Path(__file__).resolve().parent
if str(WORKERS) not in sys.path:
    sys.path.insert(0, str(WORKERS))

from duolingo_board_scanner import calculate_thresholds, load_templates  # noqa: E402
from duolingo_state_sequence_probe import scan_board_at_time  # noqa: E402
from duolingo_template_bootstrap import probe_resolution  # noqa: E402

DEFAULT_PROFILE = Path("assets/templates/duolingo_v2/profile.json")
DEFAULT_INTERVAL = 0.25


def scan_window(video_path, profile_path, start, end, interval):
    profile, templates = load_templates(profile_path)
    empty_threshold, color_threshold = calculate_thresholds(templates)
    width, height = probe_resolution(video_path)

    scans = []
    t = start
    while t <= end + 1e-9:
        scan = scan_board_at_time(
            video_path=video_path,
            timestamp=round(t, 3),
            profile=profile,
            templates=templates,
            empty_threshold=empty_threshold,
            color_threshold=color_threshold,
            width=width,
            height=height,
        )
        scans.append({"t": round(t, 3), "board_fen": scan["board_fen"], "pieces": scan.get("piece_count")})
        t += interval

    # Collapse identical consecutive observations into stable runs.
    runs = []
    for s in scans:
        if runs and runs[-1]["board_fen"] == s["board_fen"]:
            runs[-1]["t_end"] = s["t"]
            runs[-1]["samples"] += 1
        else:
            runs.append({"t_start": s["t"], "t_end": s["t"], "board_fen": s["board_fen"], "samples": 1})

    return scans, runs


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video", type=Path)
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--interval", type=float, default=DEFAULT_INTERVAL)
    ap.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    video = args.video.expanduser().resolve()
    if not video.is_file():
        raise SystemExit(f"video not found: {video}")

    scans, runs = scan_window(
        video, args.profile.expanduser().resolve(), args.start, args.end, args.interval
    )

    print(f"window {args.start}s -> {args.end}s @ {args.interval}s = {len(scans)} samples, {len(runs)} stable states\n")
    for i, r in enumerate(runs, 1):
        span = f"{r['t_start']:>6.2f}-{r['t_end']:<6.2f}"
        print(f"  S{i:02d} {span} x{r['samples']:<2}  {r['board_fen']}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"window": [args.start, args.end], "runs": runs}, indent=2) + "\n")
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
