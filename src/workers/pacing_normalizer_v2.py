from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from pacing_detector import detect_rapid_cluster


TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920

TOP_CROP_RATIO = 0.07

# Prototype pacing values.
SHOULDER_SPEED = 0.90
CORE_SPEED = 0.70


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"{name} not found in PATH")
    return path


def probe_media(file_path: Path) -> dict:
    ffprobe = require_tool("ffprobe")

    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(file_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return json.loads(result.stdout)


def media_duration(info: dict) -> float:
    return float(
        info.get("format", {}).get("duration")
        or 0
    )


def has_audio(info: dict) -> bool:
    return any(
        stream.get("codec_type") == "audio"
        for stream in info.get("streams", [])
    )


def add_video_segment(
    filters: list[str],
    labels: list[str],
    index: int,
    start: float,
    end: float,
    speed: float,
) -> int:

    label = f"v{index}"

    filters.append(
        f"[0:v]"
        f"trim=start={start:.3f}:end={end:.3f},"
        f"setpts=(PTS-STARTPTS)/{speed:.5f}"
        f"[{label}]"
    )

    labels.append(f"[{label}]")

    return index + 1


def add_audio_segment(
    filters: list[str],
    labels: list[str],
    index: int,
    start: float,
    end: float,
    speed: float,
) -> int:

    label = f"a{index}"

    filters.append(
        f"[0:a]"
        f"atrim=start={start:.3f}:end={end:.3f},"
        f"asetpts=PTS-STARTPTS,"
        f"atempo={speed:.5f}"
        f"[{label}]"
    )

    labels.append(f"[{label}]")

    return index + 1


def build_segments(
    rapid_start: float,
    core_start: float,
    core_end: float,
    rapid_end: float,
    duration: float,
) -> list[tuple[float, float, float]]:

    boundaries = [
        (0.0, rapid_start, 1.00),
        (rapid_start, core_start, SHOULDER_SPEED),
        (core_start, core_end, CORE_SPEED),
        (core_end, rapid_end, SHOULDER_SPEED),
        (rapid_end, duration, 1.00),
    ]

    return [
        (start, end, speed)
        for start, end, speed in boundaries
        if end - start > 0.05
    ]


def render(
    input_path: Path,
    output_path: Path,
    segments: list[tuple[float, float, float]],
    audio_exists: bool,
) -> None:

    ffmpeg = require_tool("ffmpeg")

    filters: list[str] = []

    video_labels: list[str] = []
    video_index = 0

    for start, end, speed in segments:
        video_index = add_video_segment(
            filters,
            video_labels,
            video_index,
            start,
            end,
            speed,
        )

    filters.append(
        "".join(video_labels)
        + f"concat=n={len(video_labels)}:"
        f"v=1:a=0[vcat]"
    )

    crop_height = 1.0 - TOP_CROP_RATIO

    filters.append(
        f"[vcat]"
        f"crop=iw:ih*{crop_height:.5f}:"
        f"0:ih*{TOP_CROP_RATIO:.5f},"
        f"split=2[bgsrc][fgsrc]"
    )

    filters.append(
        f"[bgsrc]"
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:"
        f"force_original_aspect_ratio=increase,"
        f"crop={TARGET_WIDTH}:{TARGET_HEIGHT},"
        f"gblur=sigma=35[bg]"
    )

    filters.append(
        f"[fgsrc]"
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:"
        f"force_original_aspect_ratio=decrease"
        f"[fg]"
    )

    filters.append(
        f"[bg][fg]"
        f"overlay=(W-w)/2:(H-h)/2:"
        f"shortest=1,"
        f"format=yuv420p[vout]"
    )

    audio_labels: list[str] = []

    if audio_exists:
        audio_index = 0

        for start, end, speed in segments:
            audio_index = add_audio_segment(
                filters,
                audio_labels,
                audio_index,
                start,
                end,
                speed,
            )

        filters.append(
            "".join(audio_labels)
            + f"concat=n={len(audio_labels)}:"
            f"v=0:a=1[aout]"
        )

    command = [
        ffmpeg,
        "-y",
        "-i",
        str(input_path),
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[vout]",
    ]

    if audio_exists:
        command += [
            "-map",
            "[aout]",
        ]
    else:
        command += ["-an"]

    command += [
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
    ]

    if audio_exists:
        command += [
            "-c:a",
            "aac",
            "-b:a",
            "192k",
        ]

    command += [
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    subprocess.run(
        command,
        check=True,
    )


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "input",
        type=Path,
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(
            "output/smooth-rhythm-preview.mp4"
        ),
    )

    args = parser.parse_args()

    input_path = (
        args.input
        .expanduser()
        .resolve()
    )

    output_path = (
        args.output
        .expanduser()
        .resolve()
    )

    if not input_path.is_file():
        print(
            f"ERROR: File not found: "
            f"{input_path}",
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

        core = pacing.get(
            "core_cluster"
        )

        if not rapid or not core:
            print(
                "No rapid section detected."
            )
            return 2

        info = probe_media(
            input_path
        )

        duration = media_duration(
            info
        )

        rapid_start = float(
            rapid["start"]
        )

        rapid_end = float(
            rapid["end"]
        )

        core_start = float(
            core["start"]
        )

        core_end = float(
            core["end"]
        )

        segments = build_segments(
            rapid_start=rapid_start,
            core_start=core_start,
            core_end=core_end,
            rapid_end=rapid_end,
            duration=duration,
        )

        print(
            "=== SMOOTH PACING ==="
        )

        print(
            f"Rapid section : "
            f"{rapid_start:.2f}s - "
            f"{rapid_end:.2f}s"
        )

        print(
            f"Core section  : "
            f"{core_start:.2f}s - "
            f"{core_end:.2f}s"
        )

        print()

        for number, (
            start,
            end,
            speed,
        ) in enumerate(
            segments,
            start=1,
        ):
            print(
                f"Segment {number:02d}   : "
                f"{start:.2f}s - "
                f"{end:.2f}s | "
                f"{speed:.2f}x"
            )

        render(
            input_path=input_path,
            output_path=output_path,
            segments=segments,
            audio_exists=has_audio(info),
        )

        output_info = probe_media(
            output_path
        )

        print()
        print("=== OUTPUT ===")

        print(
            f"File     : "
            f"{output_path}"
        )

        print(
            f"Duration : "
            f"{media_duration(output_info):.2f}s"
        )

    except (
        RuntimeError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        KeyError,
        ValueError,
    ) as exc:

        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )

        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
