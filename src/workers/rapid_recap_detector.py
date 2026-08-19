from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

from pacing_detector import detect_rapid_cluster


SAMPLE_FPS = 12
ANALYSIS_WIDTH = 96
ANALYSIS_HEIGHT = 96

BOARD_TOP_RATIO = 0.34
BOARD_HEIGHT_RATIO = 0.46

# Noise suppression settings for the prototype.
MIN_CANDIDATE_GAP_SECONDS = 0.25
STATE_CHANGE_THRESHOLD = 35.0


def require_tool(name: str) -> str:
    path = shutil.which(name)

    if not path:
        raise RuntimeError(f"{name} was not found in PATH")

    return path


def extract_board_frames(
    file_path: Path,
) -> tuple[np.ndarray, np.ndarray]:

    ffmpeg = require_tool("ffmpeg")

    video_filter = (
        f"crop=iw:ih*{BOARD_HEIGHT_RATIO}:0:"
        f"ih*{BOARD_TOP_RATIO},"
        f"fps={SAMPLE_FPS},"
        f"scale={ANALYSIS_WIDTH}:"
        f"{ANALYSIS_HEIGHT},"
        "format=gray"
    )

    command = [
        ffmpeg,
        "-v",
        "error",
        "-i",
        str(file_path),
        "-vf",
        video_filter,
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
        ANALYSIS_WIDTH
        * ANALYSIS_HEIGHT
    )

    raw = np.frombuffer(
        raw_bytes,
        dtype=np.uint8,
    )

    frame_count = (
        len(raw) // frame_size
    )

    if frame_count < 3:
        raise RuntimeError(
            "Not enough frames for board analysis"
        )

    raw = raw[
        : frame_count * frame_size
    ]

    frames = raw.reshape(
        frame_count,
        ANALYSIS_HEIGHT,
        ANALYSIS_WIDTH,
    )

    timestamps = (
        np.arange(
            frame_count,
            dtype=np.float64,
        )
        / SAMPLE_FPS
    )

    return frames, timestamps


def calculate_motion(
    frames: np.ndarray,
) -> np.ndarray:

    motion = np.full(
        len(frames),
        np.inf,
        dtype=np.float64,
    )

    previous_difference = np.abs(
        frames[1:-1].astype(np.int16)
        - frames[:-2].astype(np.int16)
    ).mean(axis=(1, 2))

    next_difference = np.abs(
        frames[2:].astype(np.int16)
        - frames[1:-1].astype(np.int16)
    ).mean(axis=(1, 2))

    motion[1:-1] = (
        previous_difference
        + next_difference
    ) / 2

    return motion


def find_local_stable_candidates(
    timestamps: np.ndarray,
    motion: np.ndarray,
    start: float,
    end: float,
) -> list[int]:

    valid_indices = np.flatnonzero(
        (timestamps >= start)
        & (timestamps <= end)
    )

    candidates: list[int] = []

    for index in valid_indices:
        if (
            index <= 0
            or index >= len(motion) - 1
        ):
            continue

        if (
            motion[index]
            <= motion[index - 1]
            and motion[index]
            < motion[index + 1]
        ):
            candidates.append(index)

    # Prefer the most stable candidate first,
    # but do not allow several frames from
    # effectively the same moment.
    selected: list[int] = []

    for index in sorted(
        candidates,
        key=lambda item: motion[item],
    ):
        timestamp = timestamps[index]

        if all(
            abs(
                timestamp
                - timestamps[existing]
            )
            >= MIN_CANDIDATE_GAP_SECONDS
            for existing in selected
        ):
            selected.append(index)

    return sorted(
        selected,
        key=lambda item:
        timestamps[item],
    )


def board_feature(
    frame: np.ndarray,
) -> np.ndarray:

    square_height = (
        ANALYSIS_HEIGHT // 8
    )

    square_width = (
        ANALYSIS_WIDTH // 8
    )

    features: list[float] = []

    for row in range(8):
        for column in range(8):

            y1 = row * square_height
            y2 = (
                (row + 1)
                * square_height
            )

            x1 = column * square_width
            x2 = (
                (column + 1)
                * square_width
            )

            square = frame[
                y1:y2,
                x1:x2,
            ]

            # Ignore square borders.
            inner = square[
                2:-2,
                2:-2,
            ]

            features.extend(
                [
                    float(inner.mean()),
                    float(inner.std()),
                ]
            )

    return np.asarray(
        features,
        dtype=np.float64,
    )


def board_state_distance(
    first: np.ndarray,
    second: np.ndarray,
) -> float:

    first_features = board_feature(
        first
    ).reshape(64, 2)

    second_features = board_feature(
        second
    ).reshape(64, 2)

    square_distances = np.linalg.norm(
        first_features
        - second_features,
        axis=1,
    )

    # A chess move normally affects only
    # a small number of squares, so focus
    # on the strongest changed squares
    # instead of averaging the whole board.
    strongest = np.sort(
        square_distances
    )[-4:]

    return float(
        strongest.mean()
    )


def deduplicate_states(
    frames: np.ndarray,
    candidate_indices: list[int],
) -> list[int]:

    if not candidate_indices:
        return []

    accepted = [
        candidate_indices[0]
    ]

    for index in candidate_indices[1:]:

        previous = accepted[-1]

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


def detect_recap_states(
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

    candidates = (
        find_local_stable_candidates(
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

    accepted = deduplicate_states(
        frames,
        candidates,
    )

    states = [
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
        }
        for index in accepted
    ]

    return {
        "rapid_cluster": rapid,
        "states": states,
    }


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Detect stable, visually distinct "
            "chess-board states inside an "
            "automatically detected rapid section."
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
        result = detect_recap_states(
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

    rapid = result[
        "rapid_cluster"
    ]

    states = result[
        "states"
    ]

    print(
        "=== RAPID RECAP ANALYSIS ==="
    )

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
        f"States found  : "
        f"{len(states)}"
    )

    for number, state in enumerate(
        states,
        start=1,
    ):
        print(
            f"State {number:02d}     : "
            f"{state['timestamp']:.2f}s "
            f"(motion "
            f"{state['motion']:.4f})"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
