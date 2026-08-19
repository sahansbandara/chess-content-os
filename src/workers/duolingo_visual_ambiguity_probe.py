from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import chess
import numpy as np

from duolingo_move_chain_probe import (
    scan_runs,
)

from duolingo_multi_ply_probe import (
    recover_chain,
    chain_score,
)

from duolingo_path_ambiguity_probe import (
    enumerate_paths,
)

from duolingo_template_bootstrap import (
    probe_resolution,
)

from duolingo_color_template_bootstrap import (
    square_to_grid,
)


ANALYSIS_FPS = 60
INNER_MARGIN_RATIO = 0.15

# Prototype motion threshold settings.
MOTION_PERCENTILE = 70
MAD_MULTIPLIER = 3.0
MIN_LEAD_FRAMES = 2


def extract_board_frames(
    video_path: Path,
    start: float,
    end: float,
    profile: dict,
) -> np.ndarray:

    width, height = probe_resolution(
        video_path
    )

    board_top = round(
        height
        * float(
            profile["board_top_ratio"]
        )
    )

    duration = (
        end - start
    )

    command = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        str(video_path),
        "-ss",
        f"{start:.6f}",
        "-t",
        f"{duration:.6f}",
        "-vf",
        (
            f"crop={width}:{width}:"
            f"0:{board_top},"
            f"fps={ANALYSIS_FPS},"
            "format=gray"
        ),
        "-f",
        "rawvideo",
        "-pix_fmt",
        "gray",
        "-",
    ]

    raw_bytes = subprocess.check_output(
        command
    )

    frame_size = (
        width * width
    )

    raw = np.frombuffer(
        raw_bytes,
        dtype=np.uint8,
    )

    frame_count = (
        len(raw) // frame_size
    )

    if frame_count < 2:
        raise RuntimeError(
            "Not enough frames extracted"
        )

    raw = raw[
        :frame_count * frame_size
    ]

    return raw.reshape(
        frame_count,
        width,
        width,
    )


def square_motion(
    frames: np.ndarray,
    square: str,
    orientation: str,
) -> np.ndarray:

    board_size = (
        frames.shape[1]
    )

    square_size = (
        board_size // 8
    )

    row, column = square_to_grid(
        square,
        orientation,
    )

    y1 = row * square_size
    y2 = y1 + square_size

    x1 = column * square_size
    x2 = x1 + square_size

    margin = round(
        square_size
        * INNER_MARGIN_RATIO
    )

    region = frames[
        :,
        y1 + margin:
        y2 - margin,
        x1 + margin:
        x2 - margin,
    ]

    differences = np.abs(
        region[1:].astype(np.int16)
        - region[:-1].astype(np.int16)
    ).mean(axis=(1, 2))

    return differences


def analyze_square(
    motion: np.ndarray,
    bridge_start: float,
) -> dict:

    if motion.size == 0:
        raise RuntimeError(
            "No motion samples"
        )

    median = float(
        np.median(motion)
    )

    mad = float(
        np.median(
            np.abs(
                motion - median
            )
        )
    )

    percentile_threshold = float(
        np.percentile(
            motion,
            MOTION_PERCENTILE,
        )
    )

    robust_threshold = (
        median
        + MAD_MULTIPLIER * mad
    )

    threshold = max(
        percentile_threshold,
        robust_threshold,
    )

    active = np.flatnonzero(
        motion >= threshold
    )

    onset_index = (
        int(active[0])
        if active.size
        else None
    )

    peak_index = int(
        np.argmax(motion)
    )

    onset_time = (
        bridge_start
        + (onset_index + 1)
        / ANALYSIS_FPS
        if onset_index is not None
        else None
    )

    peak_time = (
        bridge_start
        + (peak_index + 1)
        / ANALYSIS_FPS
    )

    return {
        "threshold": threshold,
        "onset_index": onset_index,
        "onset_time": onset_time,
        "peak_time": peak_time,
        "peak_motion": float(
            motion[peak_index]
        ),
    }


def get_best_chain(
    runs: list[dict],
) -> tuple[tuple, bool]:

    white_chain = recover_chain(
        runs,
        chess.WHITE,
    )

    black_chain = recover_chain(
        runs,
        chess.BLACK,
    )

    white_score = chain_score(
        white_chain,
        0,
    )

    black_score = chain_score(
        black_chain,
        0,
    )

    if white_score >= black_score:
        return white_chain, chess.WHITE

    return black_chain, chess.BLACK


def next_turn(
    turn: bool,
    plies: int,
) -> bool:

    if plies % 2 == 0:
        return turn

    return not turn


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Use source-square motion to "
            "disambiguate legal move paths."
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
        profile = json.loads(
            profile_path.read_text(
                encoding="utf-8"
            )
        )

        (
            runs,
            _rapid_start,
            _rapid_end,
        ) = scan_runs(
            video_path,
            profile_path,
        )

        chain, turn = get_best_chain(
            runs
        )

        target_bridge = None
        target_paths = None
        target_turn = None

        for bridge in chain:

            source_fen = runs[
                bridge.source_index
            ]["board_fen"]

            target_fen = runs[
                bridge.target_index
            ]["board_fen"]

            paths = enumerate_paths(
                source_fen=source_fen,
                target_fen=target_fen,
                start_turn=turn,
                max_plies=3,
            )

            if len(paths) > 1:
                target_bridge = bridge
                target_paths = paths
                target_turn = turn
                break

            turn = next_turn(
                turn,
                len(bridge.moves),
            )

        if (
            target_bridge is None
            or target_paths is None
        ):
            print(
                "No ambiguous bridge found."
            )
            return 0

        source = runs[
            target_bridge.source_index
        ]

        target = runs[
            target_bridge.target_index
        ]

        bridge_start = float(
            source["start"]
        )

        bridge_end = float(
            target["start"]
        )

        first_sources = sorted(
            {
                path[0][2][:2]
                for path in target_paths
            }
        )

        frames = extract_board_frames(
            video_path=video_path,
            start=bridge_start,
            end=bridge_end,
            profile=profile,
        )

        results = {}

        for square in first_sources:

            motion = square_motion(
                frames=frames,
                square=square,
                orientation=profile[
                    "orientation"
                ],
            )

            results[square] = (
                analyze_square(
                    motion,
                    bridge_start,
                )
            )

        print(
            "=== VISUAL AMBIGUITY PROBE ==="
        )

        print(
            f"Bridge          : "
            f"State "
            f"{target_bridge.source_index + 1:02d}"
            f" -> "
            f"{target_bridge.target_index + 1:02d}"
        )

        print(
            f"Window          : "
            f"{bridge_start:.2f}s - "
            f"{bridge_end:.2f}s"
        )

        print(
            f"Candidates      : "
            f"{len(target_paths)}"
        )

        print()

        for index, path in enumerate(
            target_paths,
            start=1,
        ):
            move_text = " -> ".join(
                item[1]
                for item in path
            )

            print(
                f"Alt {index:02d}          : "
                f"{move_text}"
            )

            print(
                f"First source    : "
                f"{path[0][2][:2]}"
            )

        print()

        print(
            "=== SOURCE-SQUARE MOTION ==="
        )

        valid_results = []

        for square, result in (
            results.items()
        ):

            onset = result[
                "onset_time"
            ]

            onset_text = (
                f"{onset:.4f}s"
                if onset is not None
                else "none"
            )

            print(
                f"{square:3s} | "
                f"onset={onset_text} | "
                f"peak="
                f"{result['peak_time']:.4f}s | "
                f"peak_motion="
                f"{result['peak_motion']:.4f}"
            )

            if (
                result["onset_index"]
                is not None
            ):
                valid_results.append(
                    (
                        square,
                        result,
                    )
                )

        valid_results.sort(
            key=lambda item:
            item[1]["onset_index"]
        )

        print()
        print(
            "=== VISUAL RESULT ==="
        )

        if len(valid_results) < 2:
            print(
                "Status          : "
                "UNRESOLVED"
            )

            return 0

        winner_square = (
            valid_results[0][0]
        )

        winner_index = (
            valid_results[0][1][
                "onset_index"
            ]
        )

        second_index = (
            valid_results[1][1][
                "onset_index"
            ]
        )

        lead_frames = (
            second_index
            - winner_index
        )

        matching_paths = [
            path
            for path in target_paths
            if (
                path[0][2][:2]
                == winner_square
            )
        ]

        if (
            lead_frames
            >= MIN_LEAD_FRAMES
            and len(matching_paths) == 1
        ):
            move_text = " -> ".join(
                item[1]
                for item in matching_paths[0]
            )

            print(
                "Status          : "
                "RESOLVED"
            )

            print(
                f"First mover     : "
                f"{winner_square}"
            )

            print(
                f"Lead frames     : "
                f"{lead_frames}"
            )

            print(
                f"Selected path   : "
                f"{move_text}"
            )

        else:
            print(
                "Status          : "
                "UNRESOLVED"
            )

            print(
                f"Earliest square : "
                f"{winner_square}"
            )

            print(
                f"Lead frames     : "
                f"{lead_frames}"
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
