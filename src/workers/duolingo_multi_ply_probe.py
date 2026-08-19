from __future__ import annotations

import argparse
import functools
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import chess

from duolingo_move_chain_probe import (
    scan_runs,
    make_board,
)


# Prototype limits chosen from the current rapid replay.
# We observed that some useful sampled states are separated
# by more than one actual chess move.
MAX_PLIES_PER_BRIDGE = 3
MAX_OBSERVED_LOOKAHEAD = 3


@dataclass(frozen=True)
class RecoveredMove:
    color: str
    san: str
    uci: str


@dataclass(frozen=True)
class Bridge:
    source_index: int
    target_index: int
    skipped_states: int
    moves: tuple[RecoveredMove, ...]


@functools.lru_cache(maxsize=None)
def find_legal_path(
    source_fen: str,
    target_fen: str,
    start_turn: bool,
    max_plies: int,
) -> tuple[RecoveredMove, ...] | None:

    start_board = make_board(
        source_fen,
        start_turn,
    )

    if (
        start_board.board_fen()
        == target_fen
    ):
        return ()

    frontier: list[
        tuple[
            chess.Board,
            tuple[RecoveredMove, ...],
        ]
    ] = [
        (
            start_board,
            (),
        )
    ]

    visited = {
        (
            start_board.board_fen(),
            start_board.turn,
        )
    }

    for _depth in range(
        1,
        max_plies + 1,
    ):

        next_frontier = []

        for board, path in frontier:

            for move in list(
                board.legal_moves
            ):

                color = (
                    "White"
                    if board.turn
                    == chess.WHITE
                    else "Black"
                )

                san = board.san(
                    move
                )

                uci = move.uci()

                next_board = (
                    board.copy(
                        stack=False
                    )
                )

                next_board.push(
                    move
                )

                next_path = (
                    *path,
                    RecoveredMove(
                        color=color,
                        san=san,
                        uci=uci,
                    ),
                )

                if (
                    next_board.board_fen()
                    == target_fen
                ):
                    return next_path

                key = (
                    next_board.board_fen(),
                    next_board.turn,
                )

                if key in visited:
                    continue

                visited.add(
                    key
                )

                next_frontier.append(
                    (
                        next_board,
                        next_path,
                    )
                )

        frontier = (
            next_frontier
        )

        if not frontier:
            break

    return None


def next_turn_after(
    start_turn: bool,
    move_count: int,
) -> bool:

    if (
        move_count % 2
        == 0
    ):
        return start_turn

    return not start_turn


def chain_score(
    chain: tuple[Bridge, ...],
    starting_index: int,
) -> tuple[int, int, int]:

    if chain:
        final_index = (
            chain[-1]
            .target_index
        )
    else:
        final_index = (
            starting_index
        )

    total_moves = sum(
        len(bridge.moves)
        for bridge in chain
    )

    total_skips = sum(
        bridge.skipped_states
        for bridge in chain
    )

    # Priority:
    # 1. Reach the latest observed state.
    # 2. Recover the most legal moves.
    # 3. Skip the fewest observed states.
    return (
        final_index,
        total_moves,
        -total_skips,
    )


def recover_chain(
    runs: list[dict],
    start_turn: bool,
) -> tuple[Bridge, ...]:

    @functools.lru_cache(
        maxsize=None
    )
    def search(
        source_index: int,
        turn: bool,
    ) -> tuple[Bridge, ...]:

        best: tuple[
            Bridge,
            ...
        ] = ()

        maximum_target = min(
            len(runs),
            source_index
            + MAX_OBSERVED_LOOKAHEAD
            + 1,
        )

        for target_index in range(
            source_index + 1,
            maximum_target,
        ):

            path = find_legal_path(
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
                start_turn=turn,
                max_plies=(
                    MAX_PLIES_PER_BRIDGE
                ),
            )

            if path is None:
                continue

            if len(path) == 0:
                continue

            following_turn = (
                next_turn_after(
                    turn,
                    len(path),
                )
            )

            remainder = search(
                target_index,
                following_turn,
            )

            bridge = Bridge(
                source_index=(
                    source_index
                ),
                target_index=(
                    target_index
                ),
                skipped_states=(
                    target_index
                    - source_index
                    - 1
                ),
                moves=path,
            )

            candidate = (
                bridge,
                *remainder,
            )

            if (
                chain_score(
                    candidate,
                    source_index,
                )
                >
                chain_score(
                    best,
                    source_index,
                )
            ):
                best = (
                    candidate
                )

        return best

    return search(
        0,
        start_turn,
    )


def flatten_moves(
    chain: tuple[Bridge, ...],
) -> list[RecoveredMove]:

    moves = []

    for bridge in chain:
        moves.extend(
            bridge.moves
        )

    return moves


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Recover multiple legal chess "
            "moves between sparse Duolingo "
            "board-state samples."
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
            recover_chain(
                runs,
                chess.WHITE,
            )
        )

        black_chain = (
            recover_chain(
                runs,
                chess.BLACK,
            )
        )

        white_score = (
            chain_score(
                white_chain,
                0,
            )
        )

        black_score = (
            chain_score(
                black_chain,
                0,
            )
        )

        if white_score >= black_score:
            chain = white_chain
            start_turn = "White"
        else:
            chain = black_chain
            start_turn = "Black"

        moves = flatten_moves(
            chain
        )

        final_state = (
            chain[-1].target_index
            if chain
            else 0
        )

        print(
            "=== DUOLINGO MULTI-PLY RECOVERY ==="
        )

        print(
            f"Rapid section     : "
            f"{rapid_start:.2f}s - "
            f"{rapid_end:.2f}s"
        )

        print(
            f"Observed states   : "
            f"{len(runs)}"
        )

        print(
            f"Starting turn     : "
            f"{start_turn}"
        )

        print(
            f"Bridges recovered : "
            f"{len(chain)}"
        )

        print(
            f"Chess moves       : "
            f"{len(moves)}"
        )

        print(
            f"Final state       : "
            f"{final_state + 1}"
        )

        print(
            f"States remaining  : "
            f"{len(runs) - final_state - 1}"
        )

        print()

        print(
            "=== BRIDGES ==="
        )

        for number, bridge in enumerate(
            chain,
            start=1,
        ):

            source = runs[
                bridge.source_index
            ]

            target = runs[
                bridge.target_index
            ]

            move_text = " → ".join(
                move.san
                for move in bridge.moves
            )

            print(
                f"Bridge {number:02d} | "
                f"State "
                f"{bridge.source_index + 1:02d}"
                f" -> "
                f"{bridge.target_index + 1:02d} | "
                f"{source['start']:.2f}s "
                f"-> "
                f"{target['start']:.2f}s | "
                f"plies={len(bridge.moves)} | "
                f"skipped="
                f"{bridge.skipped_states}"
            )

            print(
                f"  {move_text}"
            )

        print()

        print(
            "=== RECOVERED MOVE LIST ==="
        )

        for number, move in enumerate(
            moves,
            start=1,
        ):
            print(
                f"{number:02d}. "
                f"{move.color:5s} | "
                f"{move.san:8s} | "
                f"{move.uci}"
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
