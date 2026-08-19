from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"{name} was not found in PATH")
    return path


def probe_video(file_path: Path) -> dict:
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

    data = json.loads(result.stdout)

    video_stream = next(
        (stream for stream in data.get("streams", []) if stream.get("codec_type") == "video"),
        None,
    )

    if not video_stream:
        raise RuntimeError("No video stream found")

    return data


def fps_to_float(value: str | None) -> float:
    if not value or value == "0/0":
        return 0.0

    if "/" in value:
        numerator, denominator = value.split("/", 1)
        denominator_value = float(denominator)
        return float(numerator) / denominator_value if denominator_value else 0.0

    return float(value)


def print_video_info(data: dict) -> None:
    video_stream = next(
        stream
        for stream in data["streams"]
        if stream.get("codec_type") == "video"
    )

    audio_stream = next(
        (
            stream
            for stream in data["streams"]
            if stream.get("codec_type") == "audio"
        ),
        None,
    )

    duration = float(data.get("format", {}).get("duration") or 0)
    fps = fps_to_float(
        video_stream.get("avg_frame_rate")
        or video_stream.get("r_frame_rate")
    )

    print("=== INPUT VIDEO ===")
    print(f"Resolution : {video_stream.get('width')}x{video_stream.get('height')}")
    print(f"Codec      : {video_stream.get('codec_name')}")
    print(f"FPS        : {fps:.2f}")
    print(f"Duration   : {duration:.2f}s")
    print(f"Audio      : {'yes' if audio_stream else 'no'}")


def render(input_path: Path, output_path: Path) -> None:
    ffmpeg = require_tool("ffmpeg")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    filter_complex = (
        f"[0:v]split=2[background][foreground];"
        f"[background]"
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={TARGET_WIDTH}:{TARGET_HEIGHT},"
        f"gblur=sigma=35[background_blur];"
        f"[foreground]"
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease"
        f"[foreground_scaled];"
        f"[background_blur][foreground_scaled]"
        f"overlay=(W-w)/2:(H-h)/2:shortest=1,"
        f"format=yuv420p[outv]"
    )

    command = [
        ffmpeg,
        "-y",
        "-i",
        str(input_path),
        "-filter_complex",
        filter_complex,
        "-map",
        "[outv]",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    print()
    print("=== RENDERING ===")
    print(f"Input  : {input_path}")
    print(f"Output : {output_path}")

    subprocess.run(command, check=True)

    print()
    print("Render completed.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize a continuous chess screen recording for short-form social media."
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Source gameplay recording",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output/master.mp4"),
        help="Output MP4 path",
    )

    args = parser.parse_args()

    input_path = args.input.expanduser().resolve()
    output_path = args.output.expanduser().resolve()

    if not input_path.is_file():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        input_info = probe_video(input_path)
        print_video_info(input_info)

        render(input_path, output_path)

        print()
        output_info = probe_video(output_path)
        print_video_info(output_info)

    except (RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
