"""Human confirmation for ambiguous bridges — the only way a bridge gets resolved.

An ambiguous bridge is a span of plies where several legal move sequences reach
exactly the same observed board state. No amount of extra pixel evidence can
separate them, because the pixels are identical: the board after `Rdxe5` and the
board after `Rexe5` are the same sixty-four squares. Only the owner, watching the
recording, knows which rook actually slid.

So this module never picks. It refuses. An unanswered bridge raises, an index
outside the candidate list raises, and a chosen line that does not replay to the
observed final board raises. The one thing that cannot happen is candidate #1
quietly becoming truth because it printed first.

Confirmed plies carry `verification_status: human_confirmed` on a
`verification_basis: ["human_confirmed"]`. Everything else keeps the
`unique_path` basis the bridge search already earned.

Run:
  uv run python src/workers/confirm_bridges.py logs/extracted_game.json \
      --content-id 2026-08-20-duolingo-003-full --out tests/fixtures/full_game_moves.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import chess  # noqa: E402

from src.perception.bridge_search import board_from_placement  # noqa: E402

TIME_TOLERANCE_S = 1e-6


class ConfirmationError(Exception):
    """A move sequence could not be produced that anyone should trust."""


class UnresolvedBridge(ConfirmationError):
    """A bridge has no valid human choice, so there is no sequence to write."""


class ReplayMismatch(ConfirmationError):
    """The chosen lines replay to a board the recording never showed."""


def _same_time(a, b):
    return math.isclose(a, b, abs_tol=TIME_TOLERANCE_S)


def _start_board(extraction):
    return board_from_placement(
        extraction.get("start_board_fen", chess.STARTING_BOARD_FEN),
        extraction.get("start_side_to_move", "w"),
    )


def bridges(extraction):
    """Every ambiguous bridge, with the plies it covers and the line currently held.

    The extraction records bridges and moves separately; they are joined on the
    observation timestamp, which every ply inside one bridge shares.
    """
    moves = extraction["moves"]
    found = []
    for bridge in extraction["reconstruction"]["ambiguous_bridges"]:
        covered = [
            m for m in moves
            if m["ambiguous_bridge"] and _same_time(m["t_observed_s"], bridge["t"])
        ]
        found.append({
            "t": bridge["t"],
            "candidates": list(bridge["candidates"]),
            "plies": [m["ply"] for m in covered],
            "current_line": " ".join(m["san"] for m in covered),
        })
    return found


def _choice_for(bridge, choices):
    for t, index in choices.items():
        if _same_time(t, bridge["t"]):
            if not isinstance(index, int) or not 0 <= index < len(bridge["candidates"]):
                raise UnresolvedBridge(
                    f"t={bridge['t']}: choice {index!r} is not one of "
                    f"{len(bridge['candidates'])} candidates"
                )
            return index
    raise UnresolvedBridge(
        f"t={bridge['t']} has {len(bridge['candidates'])} candidates and no human choice — "
        "the sequence stays unresolved rather than defaulting to the first one"
    )


def _record(ply, board, move, t, status, basis):
    return {
        "ply": ply,
        "uci": move.uci(),
        "san": board.san(move),
        "side": "w" if board.turn == chess.WHITE else "b",
        "t_observed_s": t,
        "verification_status": status,
        "verification_basis": list(basis),
    }


def apply_choices(extraction, choices):
    """Replay the game with the human's chosen line at every ambiguous bridge.

    `choices` maps a bridge timestamp to a candidate index. Every bridge must
    appear, and the result must reach the observed final board, or nothing is
    returned at all.
    """
    found = bridges(extraction)
    starts = {}
    covered = set()
    for bridge in found:
        index = _choice_for(bridge, choices)
        if not bridge["plies"]:
            raise UnresolvedBridge(f"t={bridge['t']} covers no plies — extraction is inconsistent")
        starts[bridge["plies"][0]] = (bridge, index)
        covered.update(bridge["plies"])

    board = _start_board(extraction)
    moves = []
    for observed in extraction["moves"]:
        if observed["ply"] in starts:
            bridge, index = starts[observed["ply"]]
            for san in bridge["candidates"][index].split():
                try:
                    move = board.parse_san(san)
                except ValueError as exc:
                    raise ReplayMismatch(
                        f"t={bridge['t']} candidate {index} does not replay: {san} — {exc}"
                    ) from exc
                moves.append(_record(
                    len(moves) + 1, board, move, bridge["t"],
                    "human_confirmed", ["human_confirmed"],
                ))
                board.push(move)
            continue

        if observed["ply"] in covered:
            continue

        move = chess.Move.from_uci(observed["uci"])
        if move not in board.legal_moves:
            raise ReplayMismatch(
                f"ply {observed['ply']} ({observed['uci']}) is illegal after the chosen lines"
            )
        moves.append(_record(
            len(moves) + 1, board, move, observed["t_observed_s"],
            "verified", ["unique_path"],
        ))
        board.push(move)

    observed_final = extraction.get("final_board_fen")
    if observed_final and board.board_fen() != observed_final:
        raise ReplayMismatch(
            f"the chosen lines end on {board.board_fen()}, "
            f"but the recording ends on {observed_final}"
        )
    return moves


def build_document(extraction, choices, *, content_id, owner_side="black", source=None):
    """Assemble a moves.json document from the extraction and the human's choices."""
    moves = apply_choices(extraction, choices)

    start = _start_board(extraction)
    end = _start_board(extraction)
    for m in moves:
        end.push(chess.Move.from_uci(m["uci"]))

    statuses = [m["verification_status"] for m in moves]
    return {
        "schema_version": "1.0",
        "content_id": content_id,
        "source": source or {"path": extraction.get("video"), "kind": "duolingo_screen_recording"},
        "start_position": {
            "piece_placement": {"value": start.board_fen(), "provenance": "observed"},
            "side_to_move": {"value": "w" if start.turn == chess.WHITE else "b", "provenance": "observed"},
            "castling_rights": {"value": start.castling_xfen(), "provenance": "inferred"},
            "en_passant": {"value": None, "provenance": "observed"},
        },
        "owner_side": owner_side,
        "moves": moves,
        "final_piece_placement": {"value": end.board_fen(), "provenance": "observed"},
        "verification_summary": {
            "verified": statuses.count("verified"),
            "human_confirmed": statuses.count("human_confirmed"),
            "unresolved": 0,
        },
    }


def parse_choice(text):
    """Parse a `--choose t=index` argument into (timestamp, candidate index)."""
    t, _, index = text.partition("=")
    if not _:
        raise ValueError(f"expected TIMESTAMP=INDEX, got {text!r}")
    return float(t), int(index)


def describe_bridge(bridge):
    """Render one bridge for the owner.

    Candidates are numbered and nothing else. No ordering hint, no plausibility
    note, no marked default: the point of asking is that the machine does not know.
    """
    lines = [
        f"t={bridge['t']}s  plies {bridge['plies'][0]}-{bridge['plies'][-1]}  "
        f"({len(bridge['candidates'])} legal lines reach the same board)",
    ]
    lines += [f"  [{i}] {c}" for i, c in enumerate(bridge["candidates"])]
    return "\n".join(lines)


def prompt_for_choices(found, stream=None):
    """Ask the owner to pick a candidate for every bridge. Blocks until answered."""
    out = stream or sys.stdout
    choices = {}
    for bridge in found:
        print(f"\n{describe_bridge(bridge)}", file=out)
        print(f"  scrub the recording to {bridge['t']}s and watch which piece moves", file=out)
        while True:
            raw = input(f"  choice [0-{len(bridge['candidates']) - 1}]: ").strip()
            try:
                index = int(raw)
            except ValueError:
                print("  not a number", file=out)
                continue
            if 0 <= index < len(bridge["candidates"]):
                choices[bridge["t"]] = index
                break
            print("  out of range", file=out)
    return choices


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("extraction", type=Path, help="logs/extracted_game.json")
    parser.add_argument("--content-id", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--owner-side", default="black", choices=["white", "black"])
    parser.add_argument(
        "--choose", action="append", default=[], metavar="T=INDEX",
        help="answer a bridge non-interactively; repeatable",
    )
    args = parser.parse_args(argv)

    extraction = json.loads(args.extraction.read_text())
    found = bridges(extraction)
    if not found:
        print("no ambiguous bridges — nothing to confirm")

    choices = dict(parse_choice(c) for c in args.choose)
    missing = [b for b in found if not any(_same_time(t, b["t"]) for t in choices)]
    if missing and sys.stdin.isatty():
        choices.update(prompt_for_choices(missing))

    try:
        doc = build_document(
            extraction, choices,
            content_id=args.content_id, owner_side=args.owner_side,
        )
    except ConfirmationError as exc:
        parser.exit(2, f"refused: {exc}\n")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {args.out} ({len(doc['moves'])} plies, {doc['verification_summary']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
