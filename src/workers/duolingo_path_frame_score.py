from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import chess
import numpy as np

from duolingo_move_chain_probe import (
    make_board,
    scan_runs,
)

from duolingo_multi_ply_probe import (
    recover_chain,
    chain_score,
)

from duolingo_path_ambiguity_probe import (
    enumerate_paths,
)

from duolingo_board_scanner import (
    calculate_thresholds,
    classify_piece,
    load_templates,
)

from duolingo_template_bootstrap import (
    create_piece_mask,
    probe_resolution,
)

from duolingo_color_template_bootstrap import (
    square_to_grid,
)


ANALYSIS_FPS = 60
MAX_PLIES = 3
TOP_RESULTS = 5


def get_best_chain(
    runs: list[dict],
) -> tuple[tuple, bool]:

    white_chain = recover_chain(
        runs,
        chess.WHITE,
    )

    black_chain = recover_chain(
        runs,
        chess.BLACK,
    )

    if (
        chain_score(white_chain, 0)
        >= chain_score(black_chain, 0)
    ):
        return white_chain, chess.WHITE

    return black_chain, chess.BLACK


def next_turn(
    turn: bool,
    plies: int,
) -> bool:

    return (
        turn
        if plies % 2 == 0
        else not turn
    )


def extract_rgb_board_frames(
    video_path: Path,
    start: float,
    end: float,
    profile: dict,
) -> tuple[np.ndarray, np.ndarray]:

    width, height = probe_resolution(
        video_path
    )

    board_top = round(
        height
        * float(
            profile["board_top_ratio"]
        )
    )

    duration = end - start

    command = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        str(video_path),
        "-ss",
        f"{start:.6f}",
        "-t",
        f"{duration:.6f}",
        "-vf",
        (
            f"crop={width}:{width}:"
            f"0:{board_top},"
            f"fps={ANALYSIS_FPS},"
            "format=rgb24"
        ),
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-",
    ]

    raw_bytes = subprocess.check_output(
        command
    )

    frame_size = (
        width
        * width
        * 3
    )

    raw = np.frombuffer(
        raw_bytes,
        dtype=np.uint8,
    )

    frame_count = (
        len(raw) // frame_size
    )

    if frame_count < 2:
        raise RuntimeError(
            "Not enough video frames"
        )

    raw = raw[
        :frame_count * frame_size
    ]

    frames = raw.reshape(
        frame_count,
        width,
        width,
        3,
    )

    timestamps = (
        start
        + np.arange(
            frame_count,
            dtype=np.float64,
        ) / ANALYSIS_FPS
    )

    return frames, timestamps


def scan_board_frame(
    frame: np.ndarray,
    orientation: str,
    templates: dict,
    empty_threshold: float,
    color_threshold: float,
) -> dict[str, str]:

    board_size = frame.shape[0]

    square_size = (
        board_size // 8
    )

    detected: dict[
        str,
        str,
    ] = {}

    for square_name in chess.SQUARE_NAMES:

        row, column = square_to_grid(
            square_name,
            orientation,
        )

        y1 = (
            row
            * square_size
        )

        x1 = (
            column
            * square_size
        )

        image = frame[
            y1:y1 + square_size,
            x1:x1 + square_size,
        ]

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
            color_threshold=color_threshold,
        )

        detected[
            square_name
        ] = result[
            "symbol"
        ]

    return detected


def fen_to_map(
    board_fen: str,
) -> dict[str, str]:

    board = chess.Board(
        f"{board_fen} "
        f"w - - 0 1"
    )

    result = {}

    for square, piece in (
        board.piece_map().items()
    ):

        result[
            chess.square_name(
                square
            )
        ] = piece.symbol()

    return result


def expected_intermediate_maps(
    source_fen: str,
    turn: bool,
    path: list[
        tuple[
            str,
            str,
            str,
        ]
    ],
) -> list[dict[str, str]]:

    board = make_board(
        source_fen,
        turn,
    )

    states = []

    # Do not include final target state.
    # All candidates share that same state,
    # so it does not help disambiguation.
    for index, (
        _color,
        _san,
        uci,
    ) in enumerate(path):

        move = chess.Move.from_uci(
            uci
        )

        board.push(
            move
        )

        if index < len(path) - 1:
            states.append(
                fen_to_map(
                    board.board_fen()
                )
            )

    return states


def relevant_squares(
    paths: list[
        list[
            tuple[
                str,
                str,
                str,
            ]
        ]
    ],
) -> list[str]:

    squares = set()

    for path in paths:
        for (
            _color,
            _san,
            uci,
        ) in path:

            squares.add(
                uci[:2]
            )

            squares.add(
                uci[2:4]
            )

    return sorted(
        squares
    )


def board_similarity(
    observed: dict[str, str],
    expected: dict[str, str],
    squares: list[str],
) -> float:

    if not squares:
        return 0.0

    matches = 0

    for square in squares:

        observed_piece = (
            observed.get(
                square
            )
        )

        expected_piece = (
            expected.get(
                square
            )
        )

        if (
            observed_piece
            == expected_piece
        ):
            matches += 1

    return (
        matches
        / len(squares)
    )


def best_ordered_score(
    expected_states: list[
        dict[str, str]
    ],
    observed_states: list[
        dict[str, str]
    ],
    timestamps: np.ndarray,
    squares: list[str],
) -> tuple[
    float,
    list[float],
]:

    if not expected_states:
        return (
            1.0,
            [],
        )

    stage_count = len(
        expected_states
    )

    frame_count = len(
        observed_states
    )

    if frame_count < stage_count:
        return (
            0.0,
            [],
        )

    scores = np.zeros(
        (
            stage_count,
            frame_count,
        ),
        dtype=np.float64,
    )

    for stage in range(
        stage_count
    ):
        for frame_index in range(
            frame_count
        ):
            scores[
                stage,
                frame_index,
            ] = board_similarity(
                observed_states[
                    frame_index
                ],
                expected_states[
                    stage
                ],
                squares,
            )

    dp = np.full(
        (
            stage_count,
            frame_count,
        ),
        -np.inf,
        dtype=np.float64,
    )

    previous = np.full(
        (
            stage_count,
            frame_count,
        ),
        -1,
        dtype=np.int32,
    )

    dp[0] = scores[0]

    for stage in range(
        1,
        stage_count
    ):

        for frame_index in range(
            stage,
            frame_count
        ):

            earlier = dp[
                stage - 1,
                :frame_index,
            ]

            if earlier.size == 0:
                continue

            best_previous = int(
                np.argmax(
                    earlier
                )
            )

            best_value = (
                earlier[
                    best_previous
                ]
            )

            if not np.isfinite(
                best_value
            ):
                continue

            dp[
                stage,
                frame_index,
            ] = (
                best_value
                + scores[
                    stage,
                    frame_index,
                ]
            )

            previous[
                stage,
                frame_index,
            ] = (
                best_previous
            )

    last_stage = (
        stage_count - 1
    )

    final_index = int(
        np.argmax(
            dp[last_stage]
        )
    )

    best_total = (
        dp[
            last_stage,
            final_index,
        ]
    )

    if not np.isfinite(
        best_total
    ):
        return (
            0.0,
            [],
        )

    selected_indices = [
        final_index
    ]

    current_index = (
        final_index
    )

    for stage in range(
        last_stage,
        0,
        -1,
    ):
        current_index = int(
            previous[
                stage,
                current_index,
            ]
        )

        selected_indices.append(
            current_index
        )

    selected_indices.reverse()

    matched_times = [
        float(
            timestamps[index]
        )
        for index
        in selected_indices
    ]

    average_score = (
        float(best_total)
        / stage_count
    )

    return (
        average_score,
        matched_times,
    )


def path_text(
    path: list[
        tuple[
            str,
            str,
            str,
        ]
    ],
) -> str:

    return " -> ".join(
        item[1]
        for item in path
    )


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Rank ambiguous legal chess "
            "paths against high-FPS "
            "Duolingo board frames."
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

    if not video_path.is_file():
        print(
            f"ERROR: Video not found: "
            f"{video_path}",
            file=sys.stderr,
        )
        return 1

    try:
        profile = json.loads(
            profile_path.read_text(
                encoding="utf-8"
            )
        )

        (
            templates_profile,
            templates,
        ) = load_templates(
            profile_path
        )

        (
            empty_threshold,
            color_threshold,
        ) = calculate_thresholds(
            templates
        )

        (
            runs,
            rapid_start,
            rapid_end,
        ) = scan_runs(
            video_path,
            profile_path,
        )

        chain, turn = get_best_chain(
            runs
        )

        print(
            "=== FULL PATH FRAME SCORING ==="
        )

        print(
            f"Rapid section : "
            f"{rapid_start:.2f}s - "
            f"{rapid_end:.2f}s"
        )

        print()

        ambiguous_count = 0

        for bridge_number, bridge in enumerate(
            chain,
            start=1,
        ):

            source_fen = runs[
                bridge.source_index
            ]["board_fen"]

            target_fen = runs[
                bridge.target_index
            ]["board_fen"]

            paths = enumerate_paths(
                source_fen=source_fen,
                target_fen=target_fen,
                start_turn=turn,
                max_plies=MAX_PLIES,
            )

            if len(paths) <= 1:

                turn = next_turn(
                    turn,
                    len(bridge.moves),
                )

                continue

            ambiguous_count += 1

            source_run = runs[
                bridge.source_index
            ]

            target_run = runs[
                bridge.target_index
            ]

            bridge_start = float(
                source_run["start"]
            )

            bridge_end = float(
                target_run["start"]
            )

            frames, timestamps = (
                extract_rgb_board_frames(
                    video_path=video_path,
                    start=bridge_start,
                    end=bridge_end,
                    profile=profile,
                )
            )

            observed_states = [
                scan_board_frame(
                    frame=frame,
                    orientation=profile[
                        "orientation"
                    ],
                    templates=templates,
                    empty_threshold=(
                        empty_threshold
                    ),
                    color_threshold=(
                        color_threshold
                    ),
                )
                for frame in frames
            ]

            squares = relevant_squares(
                paths
            )

            ranked = []

            for path in paths:

                expected_states = (
                    expected_intermediate_maps(
                        source_fen=source_fen,
                        turn=turn,
                        path=path,
                    )
                )

                score, times = (
                    best_ordered_score(
                        expected_states=(
                            expected_states
                        ),
                        observed_states=(
                            observed_states
                        ),
                        timestamps=timestamps,
                        squares=squares,
                    )
                )

                ranked.append(
                    {
                        "path": path,
                        "score": score,
                        "times": times,
                    }
                )

            ranked.sort(
                key=lambda item:
                item["score"],
                reverse=True,
            )

            print(
                f"Bridge {bridge_number:02d} | "
                f"State "
                f"{bridge.source_index + 1:02d}"
                f" -> "
                f"{bridge.target_index + 1:02d}"
            )

            print(
                f"  Window          : "
                f"{bridge_start:.2f}s - "
                f"{bridge_end:.2f}s"
            )

            print(
                f"  Candidate paths : "
                f"{len(paths)}"
            )

            print(
                f"  Frames analyzed : "
                f"{len(frames)}"
            )

            print(
                f"  Relevant squares: "
                f"{' '.join(squares)}"
            )

            print()

            for rank, item in enumerate(
                ranked[:TOP_RESULTS],
                start=1,
            ):

                times_text = (
                    ", ".join(
                        f"{value:.4f}s"
                        for value
                        in item["times"]
                    )
                    if item["times"]
                    else "-"
                )

                print(
                    f"  Rank {rank:02d} | "
                    f"score="
                    f"{item['score']:.4f}"
                )

                print(
                    f"    Path  : "
                    f"{path_text(item['path'])}"
                )

                print(
                    f"    Frames: "
                    f"{times_text}"
                )

            if len(ranked) >= 2:

                gap = (
                    ranked[0]["score"]
                    - ranked[1]["score"]
                )

                print()

                print(
                    f"  Top score gap   : "
                    f"{gap:.4f}"
                )

            print()
            print(
                "--------------------------------"
            )
            print()

            bridge_plies = (
                len(paths[0])
                if paths
                else len(
                    bridge.moves
                )
            )

            turn = next_turn(
                turn,
                bridge_plies,
            )

        print(
            "=== SUMMARY ==="
        )

        print(
            f"Ambiguous bridges scored : "
            f"{ambiguous_count}"
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
