from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import chess

from duolingo_move_chain_probe import (
    scan_runs,
)

from duolingo_multi_ply_probe import (
    recover_chain,
    chain_score,
)

from duolingo_path_ambiguity_probe import (
    enumerate_paths,
)

from duolingo_visual_ambiguity_probe import (
    extract_board_frames,
)

from duolingo_departure_probe import (
    square_sequence,
    state_progress,
    find_persistent_departure,
    ANALYSIS_FPS,
    MIN_LEAD_FRAMES,
)


MAX_PLIES = 3


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


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Audit every ambiguous Duolingo "
            "legal bridge using source-square "
            "departure timing."
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

        ambiguous_total = 0
        resolved_total = 0
        reduced_total = 0
        unresolved_total = 0

        print(
            "=== DEPARTURE AMBIGUITY AUDIT ==="
        )

        print(
            f"Rapid section : "
            f"{rapid_start:.2f}s - "
            f"{rapid_end:.2f}s"
        )

        print()

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

            ambiguous_total += 1

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

            frames = extract_board_frames(
                video_path=video_path,
                start=bridge_start,
                end=bridge_end,
                profile=profile,
            )

            source_squares = sorted(
                {
                    path[0][2][:2]
                    for path in paths
                }
            )

            departures = {}

            for square in source_squares:

                sequence = square_sequence(
                    frames=frames,
                    square=square,
                    orientation=profile[
                        "orientation"
                    ],
                )

                progress = state_progress(
                    sequence
                )

                departure_index = (
                    find_persistent_departure(
                        progress
                    )
                )

                departures[square] = {
                    "index": departure_index,
                    "time": (
                        bridge_start
                        + departure_index
                        / ANALYSIS_FPS
                        if departure_index
                        is not None
                        else None
                    ),
                }

            valid = [
                (
                    square,
                    result,
                )
                for square, result
                in departures.items()
                if result["index"]
                is not None
            ]

            valid.sort(
                key=lambda item:
                item[1]["index"]
            )

            print(
                f"Bridge {bridge_number:02d} | "
                f"State "
                f"{bridge.source_index + 1:02d}"
                f" -> "
                f"{bridge.target_index + 1:02d}"
            )

            print(
                f"  Candidates before : "
                f"{len(paths)}"
            )

            for square, result in valid:

                print(
                    f"  {square:3s} departure    : "
                    f"{result['time']:.4f}s"
                )

            if not valid:
                unresolved_total += 1

                print(
                    "  Status            : "
                    "UNRESOLVED"
                )

                print()

                turn = next_turn(
                    turn,
                    len(bridge.moves),
                )

                continue

            earliest_square = (
                valid[0][0]
            )

            matching_paths = [
                path
                for path in paths
                if path[0][2][:2]
                == earliest_square
            ]

            lead_frames = None

            if len(valid) >= 2:
                lead_frames = (
                    valid[1][1]["index"]
                    - valid[0][1]["index"]
                )

            print(
                f"  Earliest source   : "
                f"{earliest_square}"
            )

            print(
                f"  Candidates after  : "
                f"{len(matching_paths)}"
            )

            if lead_frames is not None:
                print(
                    f"  Lead frames       : "
                    f"{lead_frames}"
                )

            if (
                len(matching_paths) == 1
                and (
                    lead_frames is None
                    or lead_frames
                    >= MIN_LEAD_FRAMES
                )
            ):
                resolved_total += 1

                selected = " -> ".join(
                    item[1]
                    for item
                    in matching_paths[0]
                )

                print(
                    "  Status            : "
                    "RESOLVED"
                )

                print(
                    f"  Selected path     : "
                    f"{selected}"
                )

            elif (
                len(matching_paths)
                < len(paths)
            ):
                reduced_total += 1

                print(
                    "  Status            : "
                    "REDUCED"
                )

                if len(matching_paths) <= 5:
                    for number, path in enumerate(
                        matching_paths,
                        start=1,
                    ):
                        text = " -> ".join(
                            item[1]
                            for item in path
                        )

                        print(
                            f"    Candidate "
                            f"{number:02d}      : "
                            f"{text}"
                        )

            else:
                unresolved_total += 1

                print(
                    "  Status            : "
                    "UNRESOLVED"
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
            f"Ambiguous bridges : "
            f"{ambiguous_total}"
        )

        print(
            f"Resolved          : "
            f"{resolved_total}"
        )

        print(
            f"Reduced           : "
            f"{reduced_total}"
        )

        print(
            f"Unresolved        : "
            f"{unresolved_total}"
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
