from __future__ import annotations

import argparse
import functools
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import chess

from pacing_detector import detect_rapid_cluster

from duolingo_board_scanner import (
    calculate_thresholds,
    load_templates,
)

from duolingo_template_bootstrap import (
    probe_resolution,
)

from duolingo_state_sequence_probe import (
    SAMPLE_INTERVAL,
    compress_runs,
    scan_board_at_time,
)


MAX_LOOKAHEAD_STATES = 4


@dataclass
class Transition:
    source_index: int
    target_index: int
    move: chess.Move
    san: str
    uci: str
    color: str
    skipped: int


def make_board(
    board_fen: str,
    turn: bool,
) -> chess.Board:

    turn_field = (
        "w"
        if turn == chess.WHITE
        else "b"
    )

    fen = (
        f"{board_fen} "
        f"{turn_field} "
        f"- - 0 1"
    )

    return chess.Board(
        fen
    )


def find_exact_legal_move(
    source_fen: str,
    target_fen: str,
    turn: bool,
) -> tuple[chess.Move, str] | None:

    board = make_board(
        source_fen,
        turn,
    )

    for move in list(
        board.legal_moves
    ):
        try:
            san = board.san(move)

            board.push(move)

            matches = (
                board.board_fen()
                == target_fen
            )

            board.pop()

            if matches:
                return move, san

        except (
            AssertionError,
            ValueError,
        ):
            if board.move_stack:
                board.pop()

    return None


def recover_best_chain(
    runs: list[dict],
    start_turn: bool,
) -> list[Transition]:

    @functools.lru_cache(
        maxsize=None
    )
    def search(
        source_index: int,
        turn: bool,
    ) -> tuple[Transition, ...]:

        best: tuple[
            Transition,
            ...
        ] = ()

        maximum_target = min(
            len(runs),
            source_index
            + MAX_LOOKAHEAD_STATES
            + 1,
        )

        for target_index in range(
            source_index + 1,
            maximum_target,
        ):

            result = (
                find_exact_legal_move(
                    source_fen=(
                        runs[
                            source_index
                        ]["board_fen"]
                    ),
                    target_fen=(
                        runs[
                            target_index
                        ]["board_fen"]
                    ),
                    turn=turn,
                )
            )

            if result is None:
                continue

            move, san = result

            transition = Transition(
                source_index=(
                    source_index
                ),
                target_index=(
                    target_index
                ),
                move=move,
                san=san,
                uci=move.uci(),
                color=(
                    "White"
                    if turn
                    == chess.WHITE
                    else "Black"
                ),
                skipped=(
                    target_index
                    - source_index
                    - 1
                ),
            )

            remainder = search(
                target_index,
                not turn,
            )

            candidate = (
                transition,
                *remainder,
            )

            if len(candidate) > len(best):
                best = candidate

            elif (
                len(candidate)
                == len(best)
                and candidate
                and best
            ):
                candidate_skips = sum(
                    item.skipped
                    for item in candidate
                )

                best_skips = sum(
                    item.skipped
                    for item in best
                )

                if (
                    candidate_skips
                    < best_skips
                ):
                    best = candidate

        return best

    return list(
        search(
            0,
            start_turn,
        )
    )


def scan_runs(
    video_path: Path,
    profile_path: Path,
) -> tuple[list[dict], float, float]:

    profile, templates = (
        load_templates(
            profile_path
        )
    )

    (
        empty_threshold,
        color_threshold,
    ) = calculate_thresholds(
        templates
    )

    width, height = (
        probe_resolution(
            video_path
        )
    )

    pacing = detect_rapid_cluster(
        video_path
    )

    rapid = pacing.get(
        "rapid_cluster"
    )

    if not rapid:
        raise RuntimeError(
            "No rapid section detected"
        )

    start = float(
        rapid["start"]
    )

    end = float(
        rapid["end"]
    )

    scans = []

    timestamp = start

    while timestamp <= end + 0.001:

        scans.append(
            scan_board_at_time(
                video_path=video_path,
                timestamp=timestamp,
                profile=profile,
                templates=templates,
                empty_threshold=(
                    empty_threshold
                ),
                color_threshold=(
                    color_threshold
                ),
                width=width,
                height=height,
            )
        )

        timestamp += (
            SAMPLE_INTERVAL
        )

    return (
        compress_runs(scans),
        start,
        end,
    )


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Recover legal chess moves "
            "while skipping transient "
            "Duolingo animation states."
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
        (
            runs,
            rapid_start,
            rapid_end,
        ) = scan_runs(
            video_path,
            profile_path,
        )

        white_chain = (
            recover_best_chain(
                runs,
                chess.WHITE,
            )
        )

        black_chain = (
            recover_best_chain(
                runs,
                chess.BLACK,
            )
        )

        if (
            len(white_chain)
            >= len(black_chain)
        ):
            chain = white_chain
            start_turn = "White"
        else:
            chain = black_chain
            start_turn = "Black"

        print(
            "=== DUOLINGO LEGAL MOVE CHAIN ==="
        )

        print(
            f"Rapid section  : "
            f"{rapid_start:.2f}s - "
            f"{rapid_end:.2f}s"
        )

        print(
            f"State runs     : "
            f"{len(runs)}"
        )

        print(
            f"Start turn     : "
            f"{start_turn}"
        )

        print(
            f"Moves recovered: "
            f"{len(chain)}"
        )

        print(
            f"States skipped : "
            f"{sum(x.skipped for x in chain)}"
        )

        print()

        for number, item in enumerate(
            chain,
            start=1,
        ):

            source = runs[
                item.source_index
            ]

            target = runs[
                item.target_index
            ]

            print(
                f"Move {number:02d} | "
                f"{item.color:5s} | "
                f"{item.san:8s} | "
                f"{item.uci:5s} | "
                f"{source['start']:.2f}s "
                f"-> "
                f"{target['start']:.2f}s | "
                f"skipped="
                f"{item.skipped}"
            )

        if chain:

            final_index = (
                chain[-1]
                .target_index
            )

            unresolved = (
                len(runs)
                - final_index
                - 1
            )

            print()

            print(
                f"Final state     : "
                f"{final_index + 1}"
            )

            print(
                f"Remaining states: "
                f"{unresolved}"
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
