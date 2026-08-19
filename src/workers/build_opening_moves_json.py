"""Build moves.json for the opening of the prototype recording (0.00s - 5.25s).

Reconstructed from the observed board states by src/workers/reconstruct_from_states.py.
Every bridge in this window resolved to a unique shortest legal path — no ambiguity
— so every ply is `verified` on a `unique_path` basis.

One observed state at t=3.00 was skipped as an animation transient: the f1 bishop
reads as absent while it is mid-flight to c4. It sits inside a bridge that still
resolved uniquely, so no move depends on it.

Run:  uv run python src/workers/build_opening_moves_json.py
"""

import json
from pathlib import Path

import chess

OUT = Path("tests/fixtures/opening_moves.json")

UCI = ["e2e4", "e7e5", "g1f3", "g8f6", "b1c3", "c7c6", "f1c4", "f8c5", "f3e5"]
T_OBSERVED = [0.50, 1.00, 1.50, 2.00, 2.25, 2.75, 3.25, 3.75, 5.25]


def build():
    board = chess.Board()
    moves = []
    for ply, (uci, t) in enumerate(zip(UCI, T_OBSERVED), start=1):
        mv = chess.Move.from_uci(uci)
        if mv not in board.legal_moves:
            raise SystemExit(f"ply {ply} ({uci}) illegal — reconstruction is wrong")
        moves.append({
            "ply": ply,
            "uci": uci,
            "san": board.san(mv),
            "side": "w" if board.turn == chess.WHITE else "b",
            "t_observed_s": t,
            "verification_status": "verified",
            "verification_basis": ["unique_path"],
        })
        board.push(mv)

    doc = {
        "schema_version": "1.0",
        "content_id": "2026-08-19-duolingo-002-opening",
        "source": {
            "path": "inbox/ScreenRecording_08-18-2026 7-16-25 pm_1.mov",
            "kind": "duolingo_screen_recording",
            "duration_s": 41.401678,
            "fps": 60,
            "window_s": [0.0, 5.25],
            "sha256": "776bf242f9efebee63e271812afe9a131b15375dce04d89e9b3dd31b6cbcc261",
        },
        "start_position": {
            "piece_placement": {"value": chess.STARTING_BOARD_FEN, "provenance": "observed"},
            "side_to_move": {"value": "w", "provenance": "observed"},
            "castling_rights": {"value": "KQkq", "provenance": "inferred"},
            "en_passant": {"value": None, "provenance": "observed"},
        },
        "owner_side": "black",
        "moves": moves,
        "final_piece_placement": {"value": board.board_fen(), "provenance": "observed"},
        "verification_summary": {"verified": len(moves), "human_confirmed": 0, "unresolved": 0},
    }
    return doc


if __name__ == "__main__":
    d = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(d, indent=2) + "\n")
    print(f"wrote {OUT} ({len(d['moves'])} plies, {d['verification_summary']})")
