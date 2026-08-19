from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import chess
import numpy as np

from duolingo_template_bootstrap import (
    create_piece_mask,
    extract_frame,
    probe_resolution,
)

from duolingo_color_template_bootstrap import (
    extract_square,
)


# Prototype heuristic:
# treat occupancy below 45% of the smallest
# known piece occupancy as an empty square.
EMPTY_OCCUPANCY_FACTOR = 0.45


PIECE_SYMBOLS = {
    "white_pawn": "P",
    "white_knight": "N",
    "white_bishop": "B",
    "white_rook": "R",
    "white_queen": "Q",
    "white_king": "K",

    "black_pawn": "p",
    "black_knight": "n",
    "black_bishop": "b",
    "black_rook": "r",
    "black_queen": "q",
    "black_king": "k",
}


def mask_iou(
    first: np.ndarray,
    second: np.ndarray,
) -> float:

    first_bool = first.astype(bool)
    second_bool = second.astype(bool)

    intersection = np.logical_and(
        first_bool,
        second_bool,
    ).sum()

    union = np.logical_or(
        first_bool,
        second_bool,
    ).sum()

    if union == 0:
        return 0.0

    return float(
        intersection / union
    )


def occupancy_similarity(
    current: float,
    template: float,
) -> float:

    largest = max(
        current,
        template,
    )

    if largest <= 0:
        return 0.0

    difference = abs(
        current - template
    )

    return max(
        0.0,
        1.0 - difference / largest,
    )


def piece_luma(
    image: np.ndarray,
    mask: np.ndarray,
) -> float:

    pixels = image[
        mask.astype(bool)
    ]

    if pixels.size == 0:
        return 0.0

    pixels = pixels.astype(
        np.float64
    )

    luminance = (
        0.2126 * pixels[:, 0]
        + 0.7152 * pixels[:, 1]
        + 0.0722 * pixels[:, 2]
    )

    return float(
        luminance.mean()
    )


def load_templates(
    profile_path: Path,
) -> tuple[dict, dict]:

    profile = json.loads(
        profile_path.read_text(
            encoding="utf-8"
        )
    )

    template_dir = (
        profile_path.parent
    )

    templates = {}

    for name, details in (
        profile["templates"].items()
    ):

        file_path = (
            template_dir
            / details["file"]
        )

        data = np.load(
            file_path
        )

        templates[name] = {
            "mask": data["mask"],
            "occupancy": float(
                details["occupancy"]
            ),
            "mean_luma": float(
                details["mean_luma"]
            ),
        }

    return profile, templates


def calculate_thresholds(
    templates: dict,
) -> tuple[float, float]:

    occupancies = [
        data["occupancy"]
        for data in templates.values()
    ]

    empty_threshold = (
        min(occupancies)
        * EMPTY_OCCUPANCY_FACTOR
    )

    white_lumas = [
        data["mean_luma"]
        for name, data in templates.items()
        if name.startswith("white_")
    ]

    black_lumas = [
        data["mean_luma"]
        for name, data in templates.items()
        if name.startswith("black_")
    ]

    darkest_white = min(
        white_lumas
    )

    brightest_black = max(
        black_lumas
    )

    color_threshold = (
        darkest_white
        + brightest_black
    ) / 2

    return (
        empty_threshold,
        color_threshold,
    )


def classify_piece(
    image: np.ndarray,
    mask: np.ndarray,
    templates: dict,
    color_threshold: float,
) -> dict:

    occupancy = float(
        mask.mean()
    )

    luma = piece_luma(
        image,
        mask,
    )

    color = (
        "white"
        if luma >= color_threshold
        else "black"
    )

    candidates = []

    for name, template in (
        templates.items()
    ):

        if not name.startswith(
            f"{color}_"
        ):
            continue

        iou = mask_iou(
            mask,
            template["mask"],
        )

        occupancy_score = (
            occupancy_similarity(
                occupancy,
                template["occupancy"],
            )
        )

        # Shape dominates; occupancy is a
        # secondary calibration signal.
        combined_score = (
            0.75 * iou
            + 0.25 * occupancy_score
        )

        candidates.append(
            {
                "name": name,
                "iou": iou,
                "occupancy_score": (
                    occupancy_score
                ),
                "score": combined_score,
            }
        )

    candidates.sort(
        key=lambda item:
        item["score"],
        reverse=True,
    )

    best = candidates[0]

    second_score = (
        candidates[1]["score"]
        if len(candidates) > 1
        else 0.0
    )

    confidence_margin = (
        best["score"]
        - second_score
    )

    return {
        "piece": best["name"],
        "symbol": PIECE_SYMBOLS[
            best["name"]
        ],
        "color": color,
        "luma": luma,
        "occupancy": occupancy,
        "score": best["score"],
        "confidence_margin": (
            confidence_margin
        ),
    }


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Scan all 64 Duolingo chess "
            "squares and reconstruct the "
            "visible board position."
        )
    )

    parser.add_argument(
        "video",
        type=Path,
    )

    parser.add_argument(
        "--profile",
        type=Path,
        default=Path(
            "assets/templates/"
            "duolingo_v2/profile.json"
        ),
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(
            "logs/calibration_board_scan.json"
        ),
    )

    args = parser.parse_args()

    video_path = (
        args.video
        .expanduser()
        .resolve()
    )

    profile_path = (
        args.profile
        .expanduser()
        .resolve()
    )

    output_path = (
        args.output
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

    if not profile_path.is_file():
        print(
            f"ERROR: Profile not found: "
            f"{profile_path}",
            file=sys.stderr,
        )
        return 1

    try:
        profile, templates = (
            load_templates(
                profile_path
            )
        )

        width, height = (
            probe_resolution(
                video_path
            )
        )

        timestamp = float(
            profile["timestamp"]
        )

        orientation = profile[
            "orientation"
        ]

        board_top_ratio = float(
            profile[
                "board_top_ratio"
            ]
        )

        board_top = round(
            height * board_top_ratio
        )

        square_size = (
            width // 8
        )

        frame = extract_frame(
            video_path=video_path,
            timestamp=timestamp,
            width=width,
            height=height,
        )

        (
            empty_threshold,
            color_threshold,
        ) = calculate_thresholds(
            templates
        )

        board = chess.Board(
            None
        )

        detected = {}

        print(
            "=== DUOLINGO BOARD SCAN ==="
        )

        print(
            f"Timestamp       : "
            f"{timestamp:.2f}s"
        )

        print(
            f"Orientation     : "
            f"{orientation}"
        )

        print(
            f"Empty threshold : "
            f"{empty_threshold:.4f}"
        )

        print(
            f"Color threshold : "
            f"{color_threshold:.2f}"
        )

        print()
        print(
            "Detected pieces:"
        )

        for rank in range(
            1,
            9,
        ):
            for file_letter in (
                "abcdefgh"
            ):

                square_name = (
                    f"{file_letter}{rank}"
                )

                image = extract_square(
                    frame=frame,
                    board_top=board_top,
                    square_size=square_size,
                    square=square_name,
                    orientation=orientation,
                )

                mask = create_piece_mask(
                    image
                )

                occupancy = float(
                    mask.mean()
                )

                if (
                    occupancy
                    < empty_threshold
                ):
                    continue

                result = classify_piece(
                    image=image,
                    mask=mask,
                    templates=templates,
                    color_threshold=(
                        color_threshold
                    ),
                )

                detected[
                    square_name
                ] = result

                chess_square = (
                    chess.parse_square(
                        square_name
                    )
                )

                board.set_piece_at(
                    chess_square,
                    chess.Piece.from_symbol(
                        result["symbol"]
                    ),
                )

                print(
                    f"{square_name:3s} "
                    f"{result['piece']:14s} | "
                    f"occ={result['occupancy']:.3f} | "
                    f"luma={result['luma']:.2f} | "
                    f"score={result['score']:.3f} | "
                    f"margin="
                    f"{result['confidence_margin']:.3f}"
                )

        board_fen = (
            board.board_fen()
        )

        print()
        print(
            f"Pieces detected : "
            f"{len(detected)}"
        )

        print(
            f"Board FEN       : "
            f"{board_fen}"
        )

        print()
        print(
            "=== BOARD ==="
        )

        print(
            board.unicode(
                borders=True
            )
        )

        output = {
            "timestamp": timestamp,
            "orientation": orientation,
            "empty_threshold": (
                empty_threshold
            ),
            "color_threshold": (
                color_threshold
            ),
            "piece_count": (
                len(detected)
            ),
            "board_fen": (
                board_fen
            ),
            "pieces": detected,
        }

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            json.dumps(
                output,
                indent=2,
            ),
            encoding="utf-8",
        )

        print()
        print(
            f"Saved            : "
            f"{output_path}"
        )

    except (
        RuntimeError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        KeyError,
        ValueError,
        IndexError,
    ) as exc:

        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
