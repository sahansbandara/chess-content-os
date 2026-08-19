from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np


CALIBRATION_TIMESTAMP = 10.0

# Measured from the calibration recording.
BOARD_TOP_RATIO = 962 / 2868

# This calibration frame is shown from Black's perspective.
ORIENTATION = "black"

# Known pieces visible in the calibration frame.
TEMPLATES = {
    "white_pawn": "h2",
    "white_rook": "h1",
    "white_knight": "e5",
    "white_bishop": "c3",
    "white_queen": "d2",
    "white_king": "e1",

    "black_pawn": "d5",
    "black_rook": "a8",
    "black_knight": "f6",
    "black_bishop": "c8",
    "black_queen": "d8",
    "black_king": "g8",
}


def require_tool(name: str) -> str:
    path = shutil.which(name)

    if not path:
        raise RuntimeError(
            f"{name} was not found in PATH"
        )

    return path


def probe_resolution(
    video_path: Path,
) -> tuple[int, int]:

    ffprobe = require_tool("ffprobe")

    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "json",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)

    stream = data["streams"][0]

    return (
        int(stream["width"]),
        int(stream["height"]),
    )


def extract_frame(
    video_path: Path,
    timestamp: float,
    width: int,
    height: int,
) -> np.ndarray:

    ffmpeg = require_tool("ffmpeg")

    result = subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-ss",
            str(timestamp),
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ],
        stdout=subprocess.PIPE,
        check=True,
    )

    raw = np.frombuffer(
        result.stdout,
        dtype=np.uint8,
    )

    expected = (
        width
        * height
        * 3
    )

    if raw.size != expected:
        raise RuntimeError(
            "Unexpected extracted frame size"
        )

    return raw.reshape(
        height,
        width,
        3,
    )


def square_to_grid(
    square: str,
    orientation: str,
) -> tuple[int, int]:

    file_index = (
        ord(square[0]) - ord("a")
    )

    rank_index = (
        int(square[1]) - 1
    )

    if orientation == "white":
        row = 7 - rank_index
        column = file_index

    elif orientation == "black":
        row = rank_index
        column = 7 - file_index

    else:
        raise ValueError(
            f"Unsupported orientation: "
            f"{orientation}"
        )

    return row, column


def extract_square(
    frame: np.ndarray,
    board_top: int,
    square_size: int,
    square: str,
) -> np.ndarray:

    row, column = square_to_grid(
        square,
        ORIENTATION,
    )

    y1 = (
        board_top
        + row * square_size
    )

    y2 = y1 + square_size

    x1 = column * square_size
    x2 = x1 + square_size

    return frame[
        y1:y2,
        x1:x2,
    ]


def create_piece_mask(
    square_image: np.ndarray,
) -> np.ndarray:

    size = square_image.shape[0]

    border = max(
        8,
        int(size * 0.12),
    )

    corners = np.concatenate(
        [
            square_image[
                :border,
                :border,
            ].reshape(-1, 3),

            square_image[
                :border,
                -border:,
            ].reshape(-1, 3),

            square_image[
                -border:,
                :border,
            ].reshape(-1, 3),

            square_image[
                -border:,
                -border:,
            ].reshape(-1, 3),
        ],
        axis=0,
    )

    background = np.median(
        corners,
        axis=0,
    )

    pixels = (
        square_image
        .astype(np.float32)
    )

    distance = np.linalg.norm(
        pixels - background,
        axis=2,
    )

    mask = (
        distance > 25.0
    ).astype(np.uint8)

    margin = max(
        5,
        int(size * 0.05),
    )

    mask[
        :margin,
        :
    ] = 0

    mask[
        -margin:,
        :
    ] = 0

    mask[
        :,
        :margin
    ] = 0

    mask[
        :,
        -margin:
    ] = 0

    return mask


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Create reusable Duolingo "
            "chess-piece templates."
        )
    )

    parser.add_argument(
        "video",
        type=Path,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "assets/templates/duolingo"
        ),
    )

    args = parser.parse_args()

    video_path = (
        args.video
        .expanduser()
        .resolve()
    )

    output_dir = (
        args.output_dir
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
        width, height = (
            probe_resolution(
                video_path
            )
        )

        if width % 8 != 0:
            raise RuntimeError(
                "Video width is not "
                "divisible by 8"
            )

        square_size = width // 8

        board_top = round(
            height
            * BOARD_TOP_RATIO
        )

        frame = extract_frame(
            video_path=video_path,
            timestamp=CALIBRATION_TIMESTAMP,
            width=width,
            height=height,
        )

        if (
            board_top
            + width
            > height
        ):
            raise RuntimeError(
                "Calculated board region "
                "is outside the frame"
            )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(
            "=== DUOLINGO TEMPLATE BOOTSTRAP ==="
        )

        print(
            f"Frame            : "
            f"{width}x{height}"
        )

        print(
            f"Timestamp        : "
            f"{CALIBRATION_TIMESTAMP:.2f}s"
        )

        print(
            f"Board top        : "
            f"{board_top}px"
        )

        print(
            f"Square size      : "
            f"{square_size}px"
        )

        print(
            f"Orientation      : "
            f"{ORIENTATION}"
        )

        print()

        metadata = {
            "timestamp": (
                CALIBRATION_TIMESTAMP
            ),
            "board_top_ratio": (
                BOARD_TOP_RATIO
            ),
            "orientation": (
                ORIENTATION
            ),
            "frame_width": width,
            "frame_height": height,
            "square_size": square_size,
            "templates": {},
        }

        for name, square in (
            TEMPLATES.items()
        ):

            square_image = (
                extract_square(
                    frame=frame,
                    board_top=board_top,
                    square_size=square_size,
                    square=square,
                )
            )

            mask = create_piece_mask(
                square_image
            )

            output_file = (
                output_dir
                / f"{name}.npy"
            )

            np.save(
                output_file,
                mask,
            )

            occupancy = float(
                mask.mean()
            )

            metadata[
                "templates"
            ][name] = {
                "square": square,
                "occupancy": occupancy,
                "file": output_file.name,
            }

            print(
                f"{name:14s} "
                f"{square:>3s} | "
                f"occupancy="
                f"{occupancy:.3f}"
            )

        metadata_path = (
            output_dir
            / "profile.json"
        )

        metadata_path.write_text(
            json.dumps(
                metadata,
                indent=2,
            ),
            encoding="utf-8",
        )

        print()

        print(
            f"Profile saved    : "
            f"{metadata_path}"
        )

        print(
            f"Templates saved  : "
            f"{len(TEMPLATES)}"
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
