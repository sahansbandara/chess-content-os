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

# Internal preview defaults, 2026-08-18.
RAPID_SECTION_SPEED = 0.85
TOP_CROP_RATIO = 0.07


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"{name} was not found in PATH")
    return path


def probe_media(file_path: Path) -> dict:
    ffprobe = require_tool("ffprobe")

    command = [
        ffprobe,
        "-v",
        "error",
        "-show_streams",
        "-show_format",
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

    return json.loads(result.stdout)


def has_audio_stream(media_info: dict) -> bool:
    return any(
        stream.get("codec_type") == "audio"
        for stream in media_info.get("streams", [])
    )


def get_duration(media_info: dict) -> float:
    return float(
        media_info.get("format", {}).get("duration") or 0
    )


def build_video_timeline(
    start: float,
    end: float,
    duration: float,
    speed: float,
) -> tuple[str, str]:

    filters: list[str] = []
    labels: list[str] = []
    index = 0

    if start > 0.05:
        label = f"v{index}"

        filters.append(
            f"[0:v]"
            f"trim=start=0:end={start:.3f},"
            f"setpts=PTS-STARTPTS"
            f"[{label}]"
        )

        labels.append(f"[{label}]")
        index += 1

    label = f"v{index}"

    filters.append(
        f"[0:v]"
        f"trim=start={start:.3f}:end={end:.3f},"
        f"setpts=(PTS-STARTPTS)/{speed:.5f}"
        f"[{label}]"
    )

    labels.append(f"[{label}]")
    index += 1

    if end < duration - 0.05:
        label = f"v{index}"

        filters.append(
            f"[0:v]"
            f"trim=start={end:.3f},"
            f"setpts=PTS-STARTPTS"
            f"[{label}]"
        )

        labels.append(f"[{label}]")

    concat_filter = (
        "".join(labels)
        + f"concat=n={len(labels)}:v=1:a=0[vcat]"
    )

    filters.append(concat_filter)

    crop_height = 1.0 - TOP_CROP_RATIO

    filters.append(
        f"[vcat]"
        f"crop=iw:ih*{crop_height:.5f}:0:ih*{TOP_CROP_RATIO:.5f},"
        f"split=2[background][foreground]"
    )

    filters.append(
        f"[background]"
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:"
        f"force_original_aspect_ratio=increase,"
        f"crop={TARGET_WIDTH}:{TARGET_HEIGHT},"
        f"gblur=sigma=35"
        f"[bg]"
    )

    filters.append(
        f"[foreground]"
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:"
        f"force_original_aspect_ratio=decrease"
        f"[fg]"
    )

    filters.append(
        f"[bg][fg]"
        f"overlay=(W-w)/2:(H-h)/2:shortest=1,"
        f"format=yuv420p"
        f"[vout]"
    )

    return ";".join(filters), "[vout]"


def build_audio_timeline(
    start: float,
    end: float,
    duration: float,
    speed: float,
) -> tuple[str, str]:

    filters: list[str] = []
    labels: list[str] = []
    index = 0

    if start > 0.05:
        label = f"a{index}"

        filters.append(
            f"[0:a]"
            f"atrim=start=0:end={start:.3f},"
            f"asetpts=PTS-STARTPTS"
            f"[{label}]"
        )

        labels.append(f"[{label}]")
        index += 1

    label = f"a{index}"

    filters.append(
        f"[0:a]"
        f"atrim=start={start:.3f}:end={end:.3f},"
        f"asetpts=PTS-STARTPTS,"
        f"atempo={speed:.5f}"
        f"[{label}]"
    )

    labels.append(f"[{label}]")
    index += 1

    if end < duration - 0.05:
        label = f"a{index}"

        filters.append(
            f"[0:a]"
            f"atrim=start={end:.3f},"
            f"asetpts=PTS-STARTPTS"
            f"[{label}]"
        )

        labels.append(f"[{label}]")

    filters.append(
        "".join(labels)
        + f"concat=n={len(labels)}:v=0:a=1[aout]"
    )

    return ";".join(filters), "[aout]"


def render(
    input_path: Path,
    output_path: Path,
    rapid_start: float,
    rapid_end: float,
    duration: float,
    has_audio: bool,
) -> None:

    ffmpeg = require_tool("ffmpeg")

    video_filters, video_map = build_video_timeline(
        rapid_start,
        rapid_end,
        duration,
        RAPID_SECTION_SPEED,
    )

    filter_parts = [video_filters]

    if has_audio:
        audio_filters, audio_map = build_audio_timeline(
            rapid_start,
            rapid_end,
            duration,
            RAPID_SECTION_SPEED,
        )

        filter_parts.append(audio_filters)

    filter_complex = ";".join(filter_parts)

    command = [
        ffmpeg,
        "-y",
        "-i",
        str(input_path),
        "-filter_complex",
        filter_complex,
        "-map",
        video_map,
    ]

    if has_audio:
        command += [
            "-map",
            audio_map,
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

    if has_audio:
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
    parser = argparse.ArgumentParser(
        description=(
            "Automatically normalize rapid gameplay pacing."
        )
    )

    parser.add_argument(
        "input",
        type=Path,
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(
            "output/auto-rhythm-preview.mp4"
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
            print(
                "No rapid cluster detected."
            )
            return 2

        media_info = probe_media(
            input_path
        )

        duration = get_duration(
            media_info
        )

        audio_exists = has_audio_stream(
            media_info
        )

        rapid_start = float(
            rapid["start"]
        )

        rapid_end = float(
            rapid["end"]
        )

        print("=== AUTOMATIC PACING ===")
        print(
            f"Detected start : "
            f"{rapid_start:.2f}s"
        )
        print(
            f"Detected end   : "
            f"{rapid_end:.2f}s"
        )
        print(
            f"Speed          : "
            f"{RAPID_SECTION_SPEED:.2f}x"
        )
        print(
            f"Top crop       : "
            f"{TOP_CROP_RATIO * 100:.1f}%"
        )
        print(
            f"Audio          : "
            f"{'yes' if audio_exists else 'no'}"
        )

        render(
            input_path=input_path,
            output_path=output_path,
            rapid_start=rapid_start,
            rapid_end=rapid_end,
            duration=duration,
            has_audio=audio_exists,
        )

        output_info = probe_media(
            output_path
        )

        output_duration = get_duration(
            output_info
        )

        print()
        print("=== OUTPUT ===")
        print(
            f"File     : {output_path}"
        )
        print(
            f"Duration : "
            f"{output_duration:.2f}s"
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
