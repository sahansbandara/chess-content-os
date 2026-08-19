from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

from pacing_detector import detect_rapid_cluster


SAMPLE_FPS = 12
ANALYSIS_WIDTH = 128
ANALYSIS_HEIGHT = 128

BOARD_TOP_RATIO = 0.34
BOARD_HEIGHT_RATIO = 0.46

PEAK_PERCENTILE = 60
MIN_EVENT_GAP_SECONDS = 0.40


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"{name} was not found in PATH")
    return path


def extract_board_frames(file_path: Path) -> np.ndarray:
    ffmpeg = require_tool("ffmpeg")

    video_filter = (
        f"crop=iw:ih*{BOARD_HEIGHT_RATIO}:0:ih*{BOARD_TOP_RATIO},"
        f"fps={SAMPLE_FPS},"
        f"scale={ANALYSIS_WIDTH}:{ANALYSIS_HEIGHT},"
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

    raw_bytes = subprocess.check_output(command)

    frame_size = ANALYSIS_WIDTH * ANALYSIS_HEIGHT

    raw = np.frombuffer(
        raw_bytes,
        dtype=np.uint8,
    )

    frame_count = len(raw) // frame_size

    if frame_count < 3:
        raise RuntimeError("Not enough frames for move detection")

    raw = raw[: frame_count * frame_size]

    return raw.reshape(
        frame_count,
        ANALYSIS_HEIGHT,
        ANALYSIS_WIDTH,
    )


def frame_activity(frames: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    differences = np.abs(
        frames[1:].astype(np.int16)
        - frames[:-1].astype(np.int16)
    ).mean(axis=(1, 2))

    # Small smoothing window to reduce single-frame noise.
    smooth = np.convolve(
        differences,
        np.ones(3) / 3,
        mode="same",
    )

    timestamps = (
        np.arange(1, len(frames), dtype=np.float64)
        / SAMPLE_FPS
    )

    return timestamps, smooth


def find_move_events(
    timestamps: np.ndarray,
    activity: np.ndarray,
    start: float,
    end: float,
) -> list[dict]:

    mask = (
        (timestamps >= start)
        & (timestamps <= end)
    )

    times = timestamps[mask]
    values = activity[mask]

    if len(values) < 3:
        return []

    threshold = float(
        np.percentile(values, PEAK_PERCENTILE)
    )

    candidates: list[tuple[float, float]] = []

    for index in range(1, len(values) - 1):
        current = values[index]

        if (
            current >= threshold
            and current >= values[index - 1]
            and current > values[index + 1]
        ):
            candidates.append(
                (float(current), float(times[index]))
            )

    # Keep strongest peaks while preventing several detections
    # from the same piece animation.
    selected: list[tuple[float, float]] = []

    for score, timestamp in sorted(
        candidates,
        key=lambda item: item[0],
        reverse=True,
    ):
        if all(
            abs(timestamp - existing_time)
            >= MIN_EVENT_GAP_SECONDS
            for _, existing_time in selected
        ):
            selected.append(
                (score, timestamp)
            )

    selected.sort(
        key=lambda item: item[1]
    )

    return [
        {
            "timestamp": round(timestamp, 2),
            "activity": round(score, 4),
        }
        for score, timestamp in selected
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Detect individual move-animation events "
            "inside an automatically detected rapid chess section."
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
            f"ERROR: Input file not found: {input_path}",
            file=sys.stderr,
        )
        return 1

    try:
        pacing = detect_rapid_cluster(
            input_path
        )

        rapid = pacing.get(
            "rapid_cluster"
        )

        if not rapid:
            print("Rapid cluster: none")
            return 2

        frames = extract_board_frames(
            input_path
        )

        timestamps, activity = frame_activity(
            frames
        )

        events = find_move_events(
            timestamps=timestamps,
            activity=activity,
            start=float(rapid["start"]),
            end=float(rapid["end"]),
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

    print("=== MOVE EVENT ANALYSIS ===")

    print(
        f"Rapid section : "
        f"{rapid['start']:.2f}s - "
        f"{rapid['end']:.2f}s"
    )

    print(
        f"Events found  : {len(events)}"
    )

    for number, event in enumerate(
        events,
        start=1,
    ):
        print(
            f"Move {number:02d}      : "
            f"{event['timestamp']:.2f}s "
            f"(activity {event['activity']:.4f})"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
