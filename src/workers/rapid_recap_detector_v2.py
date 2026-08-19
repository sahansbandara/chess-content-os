from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np

from pacing_detector import detect_rapid_cluster
from rapid_recap_detector import (
    extract_board_frames,
    calculate_motion,
    board_state_distance,
)


SAMPLE_FPS = 12

# Prototype settings, 2026-08-18.
STABILITY_PERCENTILE = 30
MIN_STABLE_FRAMES = 3
MIN_STATE_GAP_SECONDS = 0.35
STATE_CHANGE_THRESHOLD = 35.0


def find_stable_runs(
    timestamps: np.ndarray,
    motion: np.ndarray,
    start: float,
    end: float,
) -> tuple[list[tuple[int, int]], float]:

    valid_mask = (
        (timestamps >= start)
        & (timestamps <= end)
        & np.isfinite(motion)
    )

    valid_motion = motion[valid_mask]

    if valid_motion.size == 0:
        return [], 0.0

    stability_threshold = float(
        np.percentile(
            valid_motion,
            STABILITY_PERCENTILE,
        )
    )

    stable_mask = (
        valid_mask
        & (motion <= stability_threshold)
    )

    stable_indices = np.flatnonzero(
        stable_mask
    )

    if stable_indices.size == 0:
        return [], stability_threshold

    runs: list[tuple[int, int]] = []

    run_start = int(stable_indices[0])
    previous = run_start

    for raw_index in stable_indices[1:]:
        index = int(raw_index)

        if index == previous + 1:
            previous = index
            continue

        if (
            previous - run_start + 1
            >= MIN_STABLE_FRAMES
        ):
            runs.append(
                (run_start, previous)
            )

        run_start = index
        previous = index

    if (
        previous - run_start + 1
        >= MIN_STABLE_FRAMES
    ):
        runs.append(
            (run_start, previous)
        )

    return runs, stability_threshold


def choose_run_representatives(
    runs: list[tuple[int, int]],
    motion: np.ndarray,
) -> list[int]:

    representatives: list[int] = []

    for start, end in runs:
        indices = np.arange(
            start,
            end + 1,
        )

        best = int(
            indices[
                np.argmin(
                    motion[indices]
                )
            ]
        )

        representatives.append(best)

    return representatives


def deduplicate_states(
    frames: np.ndarray,
    timestamps: np.ndarray,
    candidates: list[int],
) -> list[int]:

    if not candidates:
        return []

    accepted = [
        candidates[0]
    ]

    for index in candidates[1:]:

        previous = accepted[-1]

        gap = (
            timestamps[index]
            - timestamps[previous]
        )

        if gap < MIN_STATE_GAP_SECONDS:
            continue

        distance = board_state_distance(
            frames[previous],
            frames[index],
        )

        if (
            distance
            >= STATE_CHANGE_THRESHOLD
        ):
            accepted.append(index)

    return accepted


def detect_recap_states_v2(
    file_path: Path,
) -> dict:

    pacing = detect_rapid_cluster(
        file_path
    )

    rapid = pacing.get(
        "rapid_cluster"
    )

    if not rapid:
        return {
            "rapid_cluster": None,
            "stability_threshold": None,
            "states": [],
        }

    frames, timestamps = (
        extract_board_frames(
            file_path
        )
    )

    motion = calculate_motion(
        frames
    )

    runs, threshold = (
        find_stable_runs(
            timestamps=timestamps,
            motion=motion,
            start=float(
                rapid["start"]
            ),
            end=float(
                rapid["end"]
            ),
        )
    )

    candidates = (
        choose_run_representatives(
            runs,
            motion,
        )
    )

    accepted = (
        deduplicate_states(
            frames,
            timestamps,
            candidates,
        )
    )

    states = []

    for index in accepted:

        containing_run = next(
            (
                run
                for run in runs
                if run[0]
                <= index
                <= run[1]
            ),
            None,
        )

        stable_duration = 0.0

        if containing_run:
            stable_duration = (
                containing_run[1]
                - containing_run[0]
                + 1
            ) / SAMPLE_FPS

        states.append(
            {
                "timestamp": round(
                    float(
                        timestamps[index]
                    ),
                    2,
                ),
                "motion": round(
                    float(
                        motion[index]
                    ),
                    4,
                ),
                "stable_duration": round(
                    stable_duration,
                    2,
                ),
            }
        )

    return {
        "rapid_cluster": rapid,
        "stability_threshold": round(
            threshold,
            4,
        ),
        "states": states,
    }


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Detect readable chess-board states "
            "using stable dwell periods."
        )
    )

    parser.add_argument(
        "input",
        type=Path,
    )

    args = parser.parse_args()

    input_path = (
        args.input
        .expanduser()
        .resolve()
    )

    if not input_path.is_file():
        print(
            f"ERROR: Input file not found: "
            f"{input_path}",
            file=sys.stderr,
        )
        return 1

    try:
        result = (
            detect_recap_states_v2(
                input_path
            )
        )

    except (
        RuntimeError,
        subprocess.CalledProcessError,
    ) as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 1

    rapid = result[
        "rapid_cluster"
    ]

    print(
        "=== RAPID RECAP V2 ==="
    )

    if not rapid:
        print(
            "Rapid section       : none"
        )
        return 0

    print(
        f"Rapid section       : "
        f"{rapid['start']:.2f}s - "
        f"{rapid['end']:.2f}s"
    )

    print(
        f"Stability threshold : "
        f"{result['stability_threshold']:.4f}"
    )

    states = result[
        "states"
    ]

    print(
        f"Readable states      : "
        f"{len(states)}"
    )

    for number, state in enumerate(
        states,
        start=1,
    ):
        print(
            f"State {number:02d}            : "
            f"{state['timestamp']:.2f}s | "
            f"motion={state['motion']:.4f} | "
            f"stable={state['stable_duration']:.2f}s"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
