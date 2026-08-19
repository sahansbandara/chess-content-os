from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import chess

from duolingo_move_chain_probe import (
    make_board,
    scan_runs,
)

from duolingo_multi_ply_probe import (
    recover_chain,
    chain_score,
)


MAX_PLIES = 3
MAX_SOLUTIONS_PER_BRIDGE = 50


def enumerate_paths(
    source_fen: str,
    target_fen: str,
    start_turn: bool,
    max_plies: int,
) -> list[list[tuple[str, str, str]]]:

    start_board = make_board(
        source_fen,
        start_turn,
    )

    solutions: list[
        list[tuple[str, str, str]]
    ] = []

    def dfs(
        board: chess.Board,
        path: list[tuple[str, str, str]],
        remaining: int,
    ) -> None:

        if len(solutions) >= MAX_SOLUTIONS_PER_BRIDGE:
            return

        if (
            path
            and board.board_fen()
            == target_fen
        ):
            solutions.append(
                path.copy()
            )
            return

        if remaining == 0:
            return

        for move in list(
            board.legal_moves
        ):
            color = (
                "White"
                if board.turn == chess.WHITE
                else "Black"
            )

            san = board.san(
                move
            )

            next_board = board.copy(
                stack=False
            )

            next_board.push(
                move
            )

            path.append(
                (
                    color,
                    san,
                    move.uci(),
                )
            )

            dfs(
                next_board,
                path,
                remaining - 1,
            )

            path.pop()

    dfs(
        start_board,
        [],
        max_plies,
    )

    # Keep only shortest paths.
    if not solutions:
        return []

    shortest = min(
        len(path)
        for path in solutions
    )

    return [
        path
        for path in solutions
        if len(path) == shortest
    ]


def next_turn(
    turn: bool,
    plies: int,
) -> bool:

    return (
        turn
        if plies % 2 == 0
        else not turn
    )


def main() -> int:

    parser = argparse.ArgumentParser()

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

    try:
        (
            runs,
            rapid_start,
            rapid_end,
        ) = scan_runs(
            video_path,
            profile_path,
        )

        white_chain = recover_chain(
            runs,
            chess.WHITE,
        )

        black_chain = recover_chain(
            runs,
            chess.BLACK,
        )

        if (
            chain_score(
                white_chain,
                0,
            )
            >=
            chain_score(
                black_chain,
                0,
            )
        ):
            chain = white_chain
            turn = chess.WHITE
        else:
            chain = black_chain
            turn = chess.BLACK

        print(
            "=== PATH AMBIGUITY AUDIT ==="
        )

        print(
            f"Rapid section : "
            f"{rapid_start:.2f}s - "
            f"{rapid_end:.2f}s"
        )

        print()

        unique_count = 0
        ambiguous_count = 0

        for number, bridge in enumerate(
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

            current_path = " → ".join(
                move.san
                for move in bridge.moves
            )

            print(
                f"Bridge {number:02d} | "
                f"State "
                f"{bridge.source_index + 1:02d}"
                f" -> "
                f"{bridge.target_index + 1:02d}"
            )

            print(
                f"  Current    : "
                f"{current_path}"
            )

            print(
                f"  Candidates : "
                f"{len(paths)}"
            )

            if len(paths) == 1:
                status = "UNIQUE"
                unique_count += 1

            elif len(paths) > 1:
                status = "AMBIGUOUS"
                ambiguous_count += 1

            else:
                status = "NO PATH"

            print(
                f"  Status     : {status}"
            )

            if (
                len(paths) > 1
                and len(paths) <= 5
            ):
                for index, path in enumerate(
                    paths,
                    start=1,
                ):
                    text = " → ".join(
                        item[1]
                        for item in path
                    )

                    print(
                        f"    Alt {index:02d}: "
                        f"{text}"
                    )

            print()

            turn = next_turn(
                turn,
                len(bridge.moves),
            )

        print(
            "=== SUMMARY ==="
        )

        print(
            f"Unique bridges    : "
            f"{unique_count}"
        )

        print(
            f"Ambiguous bridges : "
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
