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

# Prototype settings for validation.
BURST_PERCENTILE = 65
MIN_BURST_FRAMES = 2
MERGE_GAP_FRAMES = 2
MIN_STATE_GAP_SECONDS = 0.30


def find_motion_bursts(
    timestamps: np.ndarray,
    motion: np.ndarray,
    start: float,
    end: float,
) -> tuple[list[tuple[int, int]], float]:

    valid = np.flatnonzero(
        (timestamps >= start)
        & (timestamps <= end)
        & np.isfinite(motion)
    )

    if valid.size == 0:
        return [], 0.0

    threshold = float(
        np.percentile(
            motion[valid],
            BURST_PERCENTILE,
        )
    )

    active = [
        int(index)
        for index in valid
        if motion[index] >= threshold
    ]

    if not active:
        return [], threshold

    raw_runs: list[tuple[int, int]] = []

    run_start = active[0]
    previous = active[0]

    for index in active[1:]:
        if index == previous + 1:
            previous = index
            continue

        raw_runs.append(
            (run_start, previous)
        )

        run_start = index
        previous = index

    raw_runs.append(
        (run_start, previous)
    )

    merged: list[tuple[int, int]] = []

    for run in raw_runs:
        if not merged:
            merged.append(run)
            continue

        previous_start, previous_end = merged[-1]
        current_start, current_end = run

        gap_frames = (
            current_start
            - previous_end
            - 1
        )

        if gap_frames <= MERGE_GAP_FRAMES:
            merged[-1] = (
                previous_start,
                current_end,
            )
        else:
            merged.append(run)

    bursts = [
        run
        for run in merged
        if (
            run[1]
            - run[0]
            + 1
        ) >= MIN_BURST_FRAMES
    ]

    return bursts, threshold


def lowest_motion_index(
    motion: np.ndarray,
    start_index: int,
    end_index: int,
) -> int | None:

    if end_index < start_index:
        return None

    indices = np.arange(
        start_index,
        end_index + 1,
    )

    finite = indices[
        np.isfinite(
            motion[indices]
        )
    ]

    if finite.size == 0:
        return None

    return int(
        finite[
            np.argmin(
                motion[finite]
            )
        ]
    )


def find_valley_candidates(
    timestamps: np.ndarray,
    motion: np.ndarray,
    bursts: list[tuple[int, int]],
    rapid_start: float,
    rapid_end: float,
) -> list[int]:

    rapid_indices = np.flatnonzero(
        (timestamps >= rapid_start)
        & (timestamps <= rapid_end)
    )

    if rapid_indices.size == 0:
        return []

    first_index = int(
        rapid_indices[0]
    )

    last_index = int(
        rapid_indices[-1]
    )

    candidates: list[int] = []

    if not bursts:
        candidate = lowest_motion_index(
            motion,
            first_index,
            last_index,
        )

        return (
            [candidate]
            if candidate is not None
            else []
        )

    # Stable state before first burst.
    candidate = lowest_motion_index(
        motion,
        first_index,
        bursts[0][0] - 1,
    )

    if candidate is not None:
        candidates.append(candidate)

    # Lowest-motion valley between each pair of bursts.
    for current, following in zip(
        bursts,
        bursts[1:],
    ):
        candidate = lowest_motion_index(
            motion,
            current[1] + 1,
            following[0] - 1,
        )

        if candidate is not None:
            candidates.append(candidate)

    # Stable state after final burst.
    candidate = lowest_motion_index(
        motion,
        bursts[-1][1] + 1,
        last_index,
    )

    if candidate is not None:
        candidates.append(candidate)

    return candidates


def remove_time_duplicates(
    timestamps: np.ndarray,
    candidates: list[int],
) -> list[int]:

    accepted: list[int] = []

    for index in candidates:
        if not accepted:
            accepted.append(index)
            continue

        if (
            timestamps[index]
            - timestamps[accepted[-1]]
            >= MIN_STATE_GAP_SECONDS
        ):
            accepted.append(index)

    return accepted


def analyze(
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
            "threshold": None,
            "bursts": [],
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

    bursts, threshold = (
        find_motion_bursts(
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
        find_valley_candidates(
            timestamps=timestamps,
            motion=motion,
            bursts=bursts,
            rapid_start=float(
                rapid["start"]
            ),
            rapid_end=float(
                rapid["end"]
            ),
        )
    )

    candidates = (
        remove_time_duplicates(
            timestamps,
            candidates,
        )
    )

    states = []

    previous_index = None

    for index in candidates:
        distance = None

        if previous_index is not None:
            distance = board_state_distance(
                frames[previous_index],
                frames[index],
            )

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
                "distance_from_previous": (
                    round(
                        float(distance),
                        2,
                    )
                    if distance is not None
                    else None
                ),
            }
        )

        previous_index = index

    burst_results = [
        {
            "start": round(
                float(
                    timestamps[start]
                ),
                2,
            ),
            "end": round(
                float(
                    timestamps[end]
                ),
                2,
            ),
        }
        for start, end in bursts
    ]

    return {
        "rapid_cluster": rapid,
        "threshold": round(
            threshold,
            4,
        ),
        "bursts": burst_results,
        "states": states,
    }


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Detect readable board states "
            "between chess movement bursts."
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
        result = analyze(
            input_path
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

    print(
        "=== RAPID RECAP V3 ==="
    )

    rapid = result[
        "rapid_cluster"
    ]

    if not rapid:
        print(
            "Rapid section : none"
        )
        return 0

    print(
        f"Rapid section : "
        f"{rapid['start']:.2f}s - "
        f"{rapid['end']:.2f}s"
    )

    print(
        f"Burst threshold : "
        f"{result['threshold']:.4f}"
    )

    bursts = result["bursts"]

    print(
        f"Motion bursts   : "
        f"{len(bursts)}"
    )

    for number, burst in enumerate(
        bursts,
        start=1,
    ):
        print(
            f"Burst {number:02d}       : "
            f"{burst['start']:.2f}s - "
            f"{burst['end']:.2f}s"
        )

    states = result["states"]

    print()
    print(
        f"Valley states   : "
        f"{len(states)}"
    )

    for number, state in enumerate(
        states,
        start=1,
    ):
        distance = (
            "-"
            if state[
                "distance_from_previous"
            ] is None
            else f"{state['distance_from_previous']:.2f}"
        )

        print(
            f"State {number:02d}       : "
            f"{state['timestamp']:.2f}s | "
            f"motion={state['motion']:.4f} | "
            f"distance={distance}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
