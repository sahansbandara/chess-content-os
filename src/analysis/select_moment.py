"""Pick the few plies that become a short, and cut them out of the game.

docs/PLAN.md 1.4: the owner's largest win-% drop, padded with setup and the
punishment. Two failure modes this exists to prevent.

The first is picking the biggest number on the board. The prototype game's
largest drop is White's 71.c4 at -47.24%, but a channel built on the owner's own
mistakes cannot lead with someone else's. The selector only ever looks at the
owner's plies.

The second is manufacturing a lesson. If the owner never played a move the
engine calls an inaccuracy or worse, there is no moment, and this raises rather
than returning the least-good move as though it were an error.

Ties break toward the earlier ply, so the same analysis always yields the same
short.
"""

import chess

from src.validators.moves_contract import start_board

# Labels that describe an error. `good` and `best` are not errors, whatever
# their drop — the thresholds live in move_quality and are trusted here.
ERROR_LABELS = ("inaccuracy", "mistake", "blunder")

SETUP_PLIES = 4       # two full moves of run-up: enough to see why it went wrong
PUNISHMENT_PLIES = 2  # the reply and its consequence


class NoMoment(Exception):
    """The owner made no error worth building a short around."""


def select_moment(analysis, setup_plies=SETUP_PLIES, punishment_plies=PUNISHMENT_PLIES):
    """Return the owner's worst moment and the ply window that frames it."""
    owner = "w" if analysis["owner_side"].startswith("w") else "b"
    plies = analysis["moves"]

    candidates = [
        m for m in plies
        if m["side"] == owner and m.get("label") in ERROR_LABELS
    ]
    if not candidates:
        raise NoMoment(
            f"{analysis['owner_side']} played no inaccuracy, mistake or blunder in "
            f"{len(plies)} plies — this game has no lesson to lead with"
        )

    # max() keeps the first of equal drops, and the list is in ply order.
    worst = max(candidates, key=lambda m: m["win_percent_drop"])

    first_ply, last_ply = plies[0]["ply"], plies[-1]["ply"]
    return {
        "ply": worst["ply"],
        "san": worst["san"],
        "side": worst["side"],
        "label": worst["label"],
        "win_percent_drop": worst["win_percent_drop"],
        "best_move_san": worst.get("best_move_san"),
        "start_ply": max(first_ply, worst["ply"] - setup_plies),
        "end_ply": min(last_ply, worst["ply"] + punishment_plies),
    }


def slice_moves(doc, start_ply, end_ply):
    """Cut a moves.json down to one window, as a document that still validates.

    Ply numbers are deliberately **not** renumbered. They are the join key into
    analysis.json and they drive the move numbers on screen, so a short of plies
    52-58 has to keep calling them 52-58 or the video labels the wrong move.

    The window's opening position is replayed rather than guessed — castling
    rights and any en-passant square included, since a window that begins right
    after a double push contains a capture that is illegal without it.
    """
    board = start_board(doc["start_position"])
    opening = None
    kept = []

    for m in doc["moves"]:
        if m["ply"] == start_ply:
            opening = {
                "piece_placement": {"value": board.board_fen(), "provenance": "replayed"},
                "side_to_move": {
                    "value": "w" if board.turn == chess.WHITE else "b",
                    "provenance": "replayed",
                },
                "castling_rights": {"value": board.castling_xfen(), "provenance": "replayed"},
                "en_passant": {
                    "value": chess.square_name(board.ep_square) if board.ep_square else None,
                    "provenance": "replayed",
                },
            }
        if start_ply <= m["ply"] <= end_ply:
            kept.append(m)
        board.push(chess.Move.from_uci(m["uci"]))
        if m["ply"] == end_ply:
            closing = board.board_fen()

    if opening is None or not kept:
        raise NoMoment(
            f"plies {start_ply}-{end_ply} are not in this document, "
            f"which runs {doc['moves'][0]['ply']}-{doc['moves'][-1]['ply']}"
        )

    statuses = [m["verification_status"] for m in kept]
    sliced = dict(doc)
    sliced["start_position"] = opening
    sliced["moves"] = kept
    sliced["window_plies"] = [start_ply, end_ply]
    sliced["final_piece_placement"] = {"value": closing, "provenance": "replayed"}
    sliced["verification_summary"] = {
        "verified": statuses.count("verified"),
        "human_confirmed": statuses.count("human_confirmed"),
        "unresolved": statuses.count("unresolved"),
    }
    return sliced


def main(argv=None):
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("moves", type=Path, help="a verified moves.json")
    parser.add_argument("--setup-plies", type=int, default=SETUP_PLIES)
    parser.add_argument("--punishment-plies", type=int, default=PUNISHMENT_PLIES)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    doc = json.loads(args.moves.read_text())
    analysis_path = Path("output/content") / doc["content_id"] / "analysis.json"
    analysis = json.loads(analysis_path.read_text())

    try:
        moment = select_moment(analysis, args.setup_plies, args.punishment_plies)
    except NoMoment as exc:
        parser.exit(2, f"no moment: {exc}\n")

    sliced = slice_moves(doc, moment["start_ply"], moment["end_ply"])
    sliced["moment"] = moment

    out = args.out or analysis_path.parent / "short_moves.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(sliced, indent=2) + "\n")

    labelled = {a["ply"]: a for a in analysis["moves"]}
    print(f"moment: ply {moment['ply']} {moment['san']} — {moment['label']}, "
          f"-{moment['win_percent_drop']}% win, {moment['best_move_san']} was the move")
    print(f"window: plies {moment['start_ply']}-{moment['end_ply']}\n")
    for m in sliced["moves"]:
        q = labelled[m["ply"]]
        mark = "  <-- the moment" if m["ply"] == moment["ply"] else ""
        print(f"  {m['ply']:>3} {m['side']} {m['san']:<8} {q['label']:<10} "
              f"-{q['win_percent_drop']:>5.2f}%{mark}")
    print(f"\nwrote {out} ({len(sliced['moves'])} plies)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
