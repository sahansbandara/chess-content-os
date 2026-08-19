"""Build the hand-written moves.json fixture for the prototype recording.

This is the first `moves.json`, produced deliberately by hand rather than by the
extraction pipeline, so the contract can be frozen against a sequence whose
provenance is already understood (docs/PLAN.md 1.1).

SAN is never typed in. It is derived from the UCI by python-chess against the
replayed board, which is the same rule the validator enforces — so the fixture
cannot be born with a SAN/UCI disagreement.

Verification status is assigned conservatively:

  plies 1-15   verified   bridges 1-10 are documented as resolved in Agent/MEMORY.md
  plies 16-36  unresolved bridges 16-19 are documented as ambiguous, and the
                          bridge -> ply mapping is not recorded anywhere
                          machine-readable. Rather than guess which late plies
                          are affected, every ply after the last known-good
                          bridge is marked unresolved. Narrowing this requires
                          re-running duolingo_path_ambiguity_probe.py and
                          recording its bridge boundaries.

Run:  uv run python src/workers/build_prototype_moves_json.py
"""

import json
from pathlib import Path

import chess

OUT = Path("tests/fixtures/prototype_moves.json")

# State01 of the rapid replay window, t=13.50s (Agent/MEMORY.md).
START_PIECE_PLACEMENT = "r1b1r1k1/pp3ppp/8/3rP3/4n3/1BB5/PPP2PPP/2KR3R"

UCI = [
    "b3d5", "e4c3", "b2c3", "c8e6", "d5b7", "a8b8", "b7d5", "e6d5", "d1d5", "f7f6",
    "h1e1", "f6e5", "d5e5", "e8e5", "e1e5", "b8f8", "f2f4", "f8f4", "c3c4", "f4f2",
    "c4c5", "f2f6", "g2g4", "f6e6", "e5h5", "e6c6", "h5e5", "g8h8", "h2h4", "h8g8",
    "e5e8", "g8f7", "e8e5", "f7g8", "g4g5", "g8f7",
]

# Last ply covered by a resolved bridge. Bridge 10 (State12 -> State14) is plies
# 13-15: Rdxe5, Rxe5, Rxe5 — resolved to the d5-rook-first path by local
# departure timing, and independently supported by the constrained Gemini control.
LAST_RESOLVED_PLY = 15
BRIDGE_10_PLIES = {13, 14, 15}

# Recorded so the annotation is traceable, not so it can verify anything.
BRIDGE_10_MODEL_SUPPORT = {
    "provider": "gemini",
    "model": "gemini-3.6-flash",
    "supported": True,
    "confidence": "medium",
    "log": "logs/gemini_bridge10_image_probe.json",
}


def build():
    board = chess.Board(None)
    board.set_board_fen(START_PIECE_PLACEMENT)
    board.turn = chess.WHITE

    moves = []
    for ply, uci in enumerate(UCI, start=1):
        move = chess.Move.from_uci(uci)
        if move not in board.legal_moves:
            raise SystemExit(f"ply {ply} ({uci}) is illegal — the documented chain is wrong")

        entry = {
            "ply": ply,
            "uci": uci,
            "san": board.san(move),
            "side": "w" if board.turn == chess.WHITE else "b",
        }

        if ply <= LAST_RESOLVED_PLY:
            entry["verification_status"] = "verified"
            entry["verification_basis"] = (
                ["legal_path", "local_visual"] if ply in BRIDGE_10_PLIES else ["unique_path"]
            )
            if ply in BRIDGE_10_PLIES:
                entry["bridge_id"] = 10
                entry["model_support"] = BRIDGE_10_MODEL_SUPPORT
        else:
            entry["verification_status"] = "unresolved"
            entry["verification_basis"] = []
            entry["note"] = "bridge -> ply mapping unrecorded; re-run the ambiguity probe to narrow"

        moves.append(entry)
        board.push(move)

    doc = {
        "schema_version": "1.0",
        "content_id": "2026-08-19-duolingo-001",
        "source": {
            "path": "<MoneyPrinterTurbo>/storage/local_videos/material-3cc02343e1b64dbeb464b7127ad0187b.mov",
            "kind": "duolingo_screen_recording",
            "duration_s": 41.40,
            "fps": 60,
            "rapid_window_s": [13.50, 19.50],
            "board": {
                "x": 0, "y": 962, "size_px": 1320, "square_px": 165,
                "orientation": "black_perspective_180",
            },
        },
        "start_position": {
            "piece_placement": {"value": START_PIECE_PLACEMENT, "provenance": "observed"},
            "side_to_move": {"value": "w", "provenance": "inferred"},
            "castling_rights": {"value": None, "provenance": "unknown"},
            "en_passant": {"value": None, "provenance": "unknown"},
        },
        "owner_side": "black",
        "moves": moves,
        "final_piece_placement": {"value": board.board_fen(), "provenance": "observed"},
    }

    summary = {"verified": 0, "human_confirmed": 0, "unresolved": 0}
    for m in moves:
        summary[m["verification_status"]] += 1
    doc["verification_summary"] = summary

    return doc


if __name__ == "__main__":
    doc = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {OUT}  ({len(doc['moves'])} plies, {doc['verification_summary']})")
