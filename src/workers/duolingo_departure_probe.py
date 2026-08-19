from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import chess
import numpy as np

from duolingo_move_chain_probe import scan_runs

from duolingo_multi_ply_probe import (
    recover_chain,
    chain_score,
)

from duolingo_path_ambiguity_probe import (
    enumerate_paths,
)

from duolingo_visual_ambiguity_probe import (
    extract_board_frames,
)

from duolingo_color_template_bootstrap import (
    square_to_grid,
)


ANALYSIS_FPS = 60

REFERENCE_FRAMES = 2

# Prototype validation settings.
END_STATE_THRESHOLD = 0.65
PERSIST_FRAMES = 3
MIN_LEAD_FRAMES = 3

INNER_MARGIN_RATIO = 0.08


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

    if (
        chain_score(
            white_chain,
            0,
        )
        >=
        chain_score(
            black_chain,
            0,
        )
    ):
        return (
            white_chain,
            chess.WHITE,
        )

    return (
        black_chain,
        chess.BLACK,
    )


def next_turn(
    turn: bool,
    plies: int,
) -> bool:

    if plies % 2 == 0:
        return turn

    return not turn


def square_sequence(
    frames: np.ndarray,
    square: str,
    orientation: str,
) -> np.ndarray:

    board_size = frames.shape[1]

    square_size = (
        board_size // 8
    )

    row, column = square_to_grid(
        square,
        orientation,
    )

    y1 = row * square_size
    x1 = column * square_size

    margin = round(
        square_size
        * INNER_MARGIN_RATIO
    )

    return frames[
        :,
        y1 + margin:
        y1 + square_size - margin,
        x1 + margin:
        x1 + square_size - margin,
    ]


def reference_frame(
    frames: np.ndarray,
    first: bool,
) -> np.ndarray:

    count = min(
        REFERENCE_FRAMES,
        len(frames),
    )

    if first:
        selection = frames[:count]
    else:
        selection = frames[-count:]

    return np.median(
        selection.astype(
            np.float32
        ),
        axis=0,
    )


def state_progress(
    sequence: np.ndarray,
) -> np.ndarray:

    start_reference = (
        reference_frame(
            sequence,
            first=True,
        )
    )

    end_reference = (
        reference_frame(
            sequence,
            first=False,
        )
    )

    current = sequence.astype(
        np.float32
    )

    distance_from_start = (
        np.abs(
            current
            - start_reference
        )
        .mean(axis=(1, 2))
    )

    distance_from_end = (
        np.abs(
            current
            - end_reference
        )
        .mean(axis=(1, 2))
    )

    denominator = (
        distance_from_start
        + distance_from_end
        + 1e-6
    )

    # 0 = visually like start state
    # 1 = visually like end state
    return (
        distance_from_start
        / denominator
    )


def find_persistent_departure(
    progress: np.ndarray,
) -> int | None:

    active = (
        progress
        >= END_STATE_THRESHOLD
    )

    for index in range(
        0,
        len(active)
        - PERSIST_FRAMES
        + 1,
    ):

        if np.all(
            active[
                index:
                index + PERSIST_FRAMES
            ]
        ):
            return index

    return None


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Resolve ambiguous chess paths "
            "using source-square departure timing."
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

        frames = extract_board_frames(
            video_path=video_path,
            start=bridge_start,
            end=bridge_end,
            profile=profile,
        )

        first_sources = sorted(
            {
                path[0][2][:2]
                for path in target_paths
            }
        )

        results = {}

        for square in first_sources:

            sequence = square_sequence(
                frames=frames,
                square=square,
                orientation=profile[
                    "orientation"
                ],
            )

            progress = state_progress(
                sequence
            )

            departure_index = (
                find_persistent_departure(
                    progress
                )
            )

            departure_time = (
                bridge_start
                + departure_index
                / ANALYSIS_FPS
                if departure_index
                is not None
                else None
            )

            results[square] = {
                "index": departure_index,
                "time": departure_time,
                "max_progress": float(
                    progress.max()
                ),
            }

        print(
            "=== SOURCE DEPARTURE PROBE ==="
        )

        print(
            f"Bridge       : "
            f"State "
            f"{target_bridge.source_index + 1:02d}"
            f" -> "
            f"{target_bridge.target_index + 1:02d}"
        )

        print(
            f"Window       : "
            f"{bridge_start:.2f}s - "
            f"{bridge_end:.2f}s"
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
                f"Alt {index:02d}       : "
                f"{move_text}"
            )

            print(
                f"First source : "
                f"{path[0][2][:2]}"
            )

        print()

        print(
            "=== DEPARTURE TIMES ==="
        )

        valid = []

        for square, result in (
            results.items()
        ):

            time_value = result[
                "time"
            ]

            time_text = (
                f"{time_value:.4f}s"
                if time_value is not None
                else "none"
            )

            print(
                f"{square:3s} | "
                f"departure="
                f"{time_text} | "
                f"max_progress="
                f"{result['max_progress']:.3f}"
            )

            if (
                result["index"]
                is not None
            ):
                valid.append(
                    (
                        square,
                        result,
                    )
                )

        valid.sort(
            key=lambda item:
            item[1]["index"]
        )

        print()
        print(
            "=== DEPARTURE RESULT ==="
        )

        if len(valid) < 2:
            print(
                "Status        : "
                "UNRESOLVED"
            )
            return 0

        winner_square = (
            valid[0][0]
        )

        lead_frames = (
            valid[1][1]["index"]
            - valid[0][1]["index"]
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
            and len(matching_paths)
            == 1
        ):

            selected = " -> ".join(
                item[1]
                for item
                in matching_paths[0]
            )

            print(
                "Status        : RESOLVED"
            )

            print(
                f"First source  : "
                f"{winner_square}"
            )

            print(
                f"Lead frames   : "
                f"{lead_frames}"
            )

            print(
                f"Selected path : "
                f"{selected}"
            )

        else:

            print(
                "Status        : "
                "UNRESOLVED"
            )

            print(
                f"Earliest      : "
                f"{winner_square}"
            )

            print(
                f"Lead frames   : "
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
