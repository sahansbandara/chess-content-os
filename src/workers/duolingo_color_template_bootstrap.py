from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from duolingo_template_bootstrap import (
    create_piece_mask,
    extract_frame,
    probe_resolution,
)


def square_to_grid(
    square: str,
    orientation: str,
) -> tuple[int, int]:

    file_index = ord(square[0]) - ord("a")
    rank_index = int(square[1]) - 1

    if orientation == "white":
        return 7 - rank_index, file_index

    if orientation == "black":
        return rank_index, 7 - file_index

    raise ValueError(
        f"Unsupported orientation: {orientation}"
    )


def extract_square(
    frame: np.ndarray,
    board_top: int,
    square_size: int,
    square: str,
    orientation: str,
) -> np.ndarray:

    row, column = square_to_grid(
        square,
        orientation,
    )

    y1 = board_top + row * square_size
    x1 = column * square_size

    return frame[
        y1:y1 + square_size,
        x1:x1 + square_size,
    ]


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Create color-aware Duolingo "
            "chess piece templates."
        )
    )

    parser.add_argument(
        "video",
        type=Path,
    )

    parser.add_argument(
        "--source-profile",
        type=Path,
        default=Path(
            "assets/templates/duolingo/profile.json"
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "assets/templates/duolingo_v2"
        ),
    )

    args = parser.parse_args()

    video_path = (
        args.video.expanduser().resolve()
    )

    profile_path = (
        args.source_profile
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
            f"ERROR: Video not found: {video_path}",
            file=sys.stderr,
        )
        return 1

    if not profile_path.is_file():
        print(
            f"ERROR: Profile not found: {profile_path}",
            file=sys.stderr,
        )
        return 1

    try:
        profile = json.loads(
            profile_path.read_text(
                encoding="utf-8"
            )
        )

        width, height = probe_resolution(
            video_path
        )

        timestamp = float(
            profile["timestamp"]
        )

        board_top_ratio = float(
            profile["board_top_ratio"]
        )

        orientation = profile[
            "orientation"
        ]

        board_top = round(
            height * board_top_ratio
        )

        square_size = width // 8

        frame = extract_frame(
            video_path=video_path,
            timestamp=timestamp,
            width=width,
            height=height,
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_profile = {
            "timestamp": timestamp,
            "board_top_ratio": board_top_ratio,
            "orientation": orientation,
            "frame_width": width,
            "frame_height": height,
            "square_size": square_size,
            "templates": {},
        }

        print(
            "=== COLOR TEMPLATE BOOTSTRAP ==="
        )

        print(
            f"Frame       : {width}x{height}"
        )

        print(
            f"Timestamp   : {timestamp:.2f}s"
        )

        print(
            f"Orientation : {orientation}"
        )

        print()

        for name, details in (
            profile["templates"].items()
        ):

            square = details["square"]

            image = extract_square(
                frame=frame,
                board_top=board_top,
                square_size=square_size,
                square=square,
                orientation=orientation,
            )

            mask = create_piece_mask(
                image
            )

            piece_pixels = image[
                mask.astype(bool)
            ]

            if piece_pixels.size == 0:
                raise RuntimeError(
                    f"No piece pixels found "
                    f"for {name}"
                )

            mean_rgb = (
                piece_pixels
                .astype(np.float64)
                .mean(axis=0)
            )

            luminance = (
                0.2126 * piece_pixels[:, 0]
                + 0.7152 * piece_pixels[:, 1]
                + 0.0722 * piece_pixels[:, 2]
            )

            mean_luma = float(
                luminance.mean()
            )

            output_file = (
                output_dir
                / f"{name}.npz"
            )

            np.savez_compressed(
                output_file,
                rgb=image,
                mask=mask,
            )

            output_profile[
                "templates"
            ][name] = {
                "square": square,
                "file": output_file.name,
                "occupancy": float(
                    mask.mean()
                ),
                "mean_rgb": [
                    round(
                        float(value),
                        2,
                    )
                    for value in mean_rgb
                ],
                "mean_luma": round(
                    mean_luma,
                    2,
                ),
            }

            print(
                f"{name:14s} "
                f"{square:>3s} | "
                f"occ={mask.mean():.3f} | "
                f"luma={mean_luma:.2f}"
            )

        new_profile = (
            output_dir
            / "profile.json"
        )

        new_profile.write_text(
            json.dumps(
                output_profile,
                indent=2,
            ),
            encoding="utf-8",
        )

        print()
        print(
            f"Profile saved : {new_profile}"
        )

        print(
            f"Templates     : "
            f"{len(output_profile['templates'])}"
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
