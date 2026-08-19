from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np


SAMPLE_FPS = 6
ANALYSIS_WIDTH = 96
ANALYSIS_HEIGHT = 96

BOARD_TOP_RATIO = 0.34
BOARD_HEIGHT_RATIO = 0.46

THRESHOLD_MAD_MULTIPLIER = 1.5
MIN_CLUSTER_SECONDS = 2
PADDING_SECONDS = 1.5


def require_tool(name: str) -> str:
    path = shutil.which(name)

    if not path:
        raise RuntimeError(f"{name} was not found in PATH")

    return path


def probe_duration(file_path: Path) -> float:
    ffprobe = require_tool("ffprobe")

    command = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(file_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)

    return float(data["format"]["duration"])


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

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        check=True,
    )

    frame_size = ANALYSIS_WIDTH * ANALYSIS_HEIGHT

    raw = np.frombuffer(
        result.stdout,
        dtype=np.uint8,
    )

    complete_frames = len(raw) // frame_size

    if complete_frames < 2:
        raise RuntimeError(
            "Not enough frames were extracted for pacing analysis"
        )

    raw = raw[: complete_frames * frame_size]

    return raw.reshape(
        complete_frames,
        ANALYSIS_HEIGHT,
        ANALYSIS_WIDTH,
    )


def calculate_second_activity(frames: np.ndarray) -> np.ndarray:
    differences = np.abs(
        frames[1:].astype(np.int16)
        - frames[:-1].astype(np.int16)
    ).mean(axis=(1, 2))

    timestamps = (
        np.arange(
            1,
            len(frames),
            dtype=np.float64,
        )
        / SAMPLE_FPS
    )

    second_count = int(
        math.ceil(timestamps[-1])
    )

    scores = np.zeros(
        second_count,
        dtype=np.float64,
    )

    for second in range(second_count):
        mask = (
            (timestamps >= second)
            & (timestamps < second + 1)
        )

        if np.any(mask):
            scores[second] = differences[mask].mean()

    return scores


def find_longest_cluster(
    active_seconds: np.ndarray,
) -> tuple[int, int] | None:

    if active_seconds.size == 0:
        return None

    clusters = []

    start = int(active_seconds[0])
    previous = start

    for value in active_seconds[1:]:
        current = int(value)

        if current == previous + 1:
            previous = current
            continue

        clusters.append(
            (start, previous + 1)
        )

        start = current
        previous = current

    clusters.append(
        (start, previous + 1)
    )

    valid_clusters = [
        cluster
        for cluster in clusters
        if cluster[1] - cluster[0]
        >= MIN_CLUSTER_SECONDS
    ]

    if not valid_clusters:
        return None

    return max(
        valid_clusters,
        key=lambda cluster:
        cluster[1] - cluster[0],
    )


def detect_rapid_cluster(
    file_path: Path,
) -> dict:

    duration = probe_duration(file_path)

    frames = extract_board_frames(
        file_path
    )

    scores = calculate_second_activity(
        frames
    )

    median_score = float(
        np.median(scores)
    )

    mad = float(
        np.median(
            np.abs(
                scores - median_score
            )
        )
    )

    threshold = (
        median_score
        + THRESHOLD_MAD_MULTIPLIER * mad
    )

    active_seconds = np.flatnonzero(
        scores > threshold
    )

    core_cluster = find_longest_cluster(
        active_seconds
    )

    result = {
        "duration": duration,
        "median_activity": median_score,
        "mad": mad,
        "threshold": threshold,
        "core_cluster": None,
        "rapid_cluster": None,
    }

    if core_cluster is None:
        return result

    core_start, core_end = core_cluster

    padded_start = max(
        0.0,
        core_start - PADDING_SECONDS,
    )

    padded_end = min(
        duration,
        core_end + PADDING_SECONDS,
    )

    result["core_cluster"] = {
        "start": float(core_start),
        "end": float(core_end),
    }

    result["rapid_cluster"] = {
        "start": round(padded_start, 2),
        "end": round(padded_end, 2),
    }

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Detect unusually rapid chess-board "
            "activity in a gameplay recording."
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
        result = detect_rapid_cluster(
            input_path
        )

    except (
        RuntimeError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        KeyError,
    ) as exc:

        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )

        return 1

    print("=== PACING ANALYSIS ===")

    print(
        f"Duration       : "
        f"{result['duration']:.2f}s"
    )

    print(
        f"Median activity: "
        f"{result['median_activity']:.4f}"
    )

    print(
        f"MAD            : "
        f"{result['mad']:.4f}"
    )

    print(
        f"Threshold      : "
        f"{result['threshold']:.4f}"
    )

    core = result["core_cluster"]
    rapid = result["rapid_cluster"]

    if not core or not rapid:
        print(
            "Rapid cluster  : none detected"
        )
        return 0

    print(
        f"Core activity  : "
        f"{core['start']:.2f}s - "
        f"{core['end']:.2f}s"
    )

    print(
        f"Rapid cluster  : "
        f"{rapid['start']:.2f}s - "
        f"{rapid['end']:.2f}s"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
