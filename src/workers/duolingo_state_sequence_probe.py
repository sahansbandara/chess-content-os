from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import chess

from pacing_detector import detect_rapid_cluster

from duolingo_template_bootstrap import (
    create_piece_mask,
    extract_frame,
    probe_resolution,
)

from duolingo_color_template_bootstrap import (
    extract_square,
)

from duolingo_board_scanner import (
    load_templates,
    calculate_thresholds,
    classify_piece,
)


# Prototype sampling interval.
SAMPLE_INTERVAL = 0.25


def probe_duration(video_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return float(result.stdout.strip())


def scan_board_at_time(
    video_path: Path,
    timestamp: float,
    profile: dict,
    templates: dict,
    empty_threshold: float,
    color_threshold: float,
    width: int,
    height: int,
) -> dict:

    orientation = profile["orientation"]

    board_top = round(
        height
        * float(profile["board_top_ratio"])
    )

    square_size = width // 8

    frame = extract_frame(
        video_path=video_path,
        timestamp=timestamp,
        width=width,
        height=height,
    )

    board = chess.Board(None)

    detected = {}

    for rank in range(1, 9):
        for file_letter in "abcdefgh":

            square_name = (
                f"{file_letter}{rank}"
            )

            image = extract_square(
                frame=frame,
                board_top=board_top,
                square_size=square_size,
                square=square_name,
                orientation=orientation,
            )

            mask = create_piece_mask(
                image
            )

            occupancy = float(
                mask.mean()
            )

            if occupancy < empty_threshold:
                continue

            result = classify_piece(
                image=image,
                mask=mask,
                templates=templates,
                color_threshold=color_threshold,
            )

            detected[square_name] = result

            board.set_piece_at(
                chess.parse_square(
                    square_name
                ),
                chess.Piece.from_symbol(
                    result["symbol"]
                ),
            )

    symbols = [
        item["symbol"]
        for item in detected.values()
    ]

    white_kings = symbols.count("K")
    black_kings = symbols.count("k")

    # A readable chess position must retain
    # exactly one king for each side.
    valid = (
        white_kings == 1
        and black_kings == 1
    )

    margins = [
        float(
            item["confidence_margin"]
        )
        for item in detected.values()
    ]

    mean_margin = (
        sum(margins) / len(margins)
        if margins
        else 0.0
    )

    return {
        "timestamp": timestamp,
        "valid": valid,
        "piece_count": len(detected),
        "board_fen": board.board_fen(),
        "mean_margin": mean_margin,
    }


def compress_runs(
    scans: list[dict],
) -> list[dict]:

    runs: list[dict] = []

    for scan in scans:

        if not scan["valid"]:
            continue

        if (
            runs
            and runs[-1]["board_fen"]
            == scan["board_fen"]
        ):
            runs[-1]["end"] = (
                scan["timestamp"]
            )

            runs[-1]["samples"] += 1

            runs[-1][
                "mean_margin_sum"
            ] += scan["mean_margin"]

            continue

        runs.append(
            {
                "start": scan["timestamp"],
                "end": scan["timestamp"],
                "samples": 1,
                "piece_count": (
                    scan["piece_count"]
                ),
                "board_fen": (
                    scan["board_fen"]
                ),
                "mean_margin_sum": (
                    scan["mean_margin"]
                ),
            }
        )

    for run in runs:
        run["mean_margin"] = (
            run["mean_margin_sum"]
            / run["samples"]
        )

        del run[
            "mean_margin_sum"
        ]

    return runs


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Probe consecutive Duolingo "
            "chess board states."
        )
    )

    parser.add_argument(
        "video",
        type=Path,
    )

    parser.add_argument(
        "--profile",
        type=Path,
        default=Path(
            "assets/templates/"
            "duolingo_v2/profile.json"
        ),
    )

    args = parser.parse_args()

    video_path = (
        args.video
        .expanduser()
        .resolve()
    )

    profile_path = (
        args.profile
        .expanduser()
        .resolve()
    )

    if not video_path.is_file():
        print(
            f"ERROR: Video not found: "
            f"{video_path}",
            file=sys.stderr,
        )
        return 1

    try:
        profile, templates = (
            load_templates(
                profile_path
            )
        )

        (
            empty_threshold,
            color_threshold,
        ) = calculate_thresholds(
            templates
        )

        width, height = (
            probe_resolution(
                video_path
            )
        )

        pacing = detect_rapid_cluster(
            video_path
        )

        rapid = pacing.get(
            "rapid_cluster"
        )

        if not rapid:
            print(
                "ERROR: No rapid section detected",
                file=sys.stderr,
            )
            return 2

        start = float(
            rapid["start"]
        )

        end = float(
            rapid["end"]
        )

        scans = []

        timestamp = start

        while timestamp <= end + 0.001:

            scan = scan_board_at_time(
                video_path=video_path,
                timestamp=timestamp,
                profile=profile,
                templates=templates,
                empty_threshold=empty_threshold,
                color_threshold=color_threshold,
                width=width,
                height=height,
            )

            scans.append(
                scan
            )

            timestamp += (
                SAMPLE_INTERVAL
            )

        runs = compress_runs(
            scans
        )

        print(
            "=== DUOLINGO STATE SEQUENCE ==="
        )

        print(
            f"Rapid section : "
            f"{start:.2f}s - "
            f"{end:.2f}s"
        )

        print(
            f"Sample step   : "
            f"{SAMPLE_INTERVAL:.2f}s"
        )

        print(
            f"Frames scanned: "
            f"{len(scans)}"
        )

        print(
            f"Valid scans   : "
            f"{sum(1 for x in scans if x['valid'])}"
        )

        print(
            f"State runs    : "
            f"{len(runs)}"
        )

        print()

        for number, run in enumerate(
            runs,
            start=1,
        ):

            print(
                f"State {number:02d} | "
                f"{run['start']:.2f}s - "
                f"{run['end']:.2f}s | "
                f"samples={run['samples']} | "
                f"pieces={run['piece_count']} | "
                f"margin={run['mean_margin']:.3f}"
            )

            print(
                f"  {run['board_fen']}"
            )

    except (
        RuntimeError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        KeyError,
        ValueError,
        IndexError,
    ) as exc:

        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
