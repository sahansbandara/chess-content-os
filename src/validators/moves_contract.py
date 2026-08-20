"""Validator for moves.json — the truth seam.

Every finding is a hard failure. See docs/PLAN.md 1.1.
"""

import chess

# Evidence that can actually carry a move. `model_support` is deliberately absent:
# a model agreeing with a candidate is an annotation, never a basis.
VALID_BASES = {"unique_path", "legal_path", "local_visual", "human_confirmed"}

RENDERABLE_STATUSES = {"verified", "human_confirmed"}

START_POSITION_FIELDS = ("piece_placement", "side_to_move", "castling_rights", "en_passant")


def start_board(start_position):
    board = chess.Board(None)
    board.set_board_fen(start_position["piece_placement"]["value"])
    board.turn = chess.WHITE if start_position["side_to_move"]["value"] == "w" else chess.BLACK

    # A piece-placement FEN carries no castling rights and `set_board_fen` clears
    # them, so O-O would be illegal in every document unless the rights recorded
    # in the contract are applied here.
    rights = (start_position.get("castling_rights") or {}).get("value")
    board.set_castling_fen(rights or "-")

    # Same reasoning for en passant. A document that starts mid-game — a window
    # sliced out for a short — can open on the move right after a double push,
    # and that capture is illegal unless the square is restored.
    square = (start_position.get("en_passant") or {}).get("value")
    board.ep_square = chess.parse_square(square) if square else None
    return board


def validate_moves(doc):
    """Return a list of hard-failure findings. Empty list means the document is valid."""
    errors = []
    start_position = doc["start_position"]

    for field in START_POSITION_FIELDS:
        entry = start_position.get(field)
        if entry is not None and "provenance" not in entry:
            errors.append(
                {
                    "rule": "provenance_required",
                    "field": field,
                    "message": f"start_position.{field} has no provenance — observed and inferred facts must stay distinguishable",
                }
            )

    board = start_board(start_position)

    previous_side = None
    for m in doc["moves"]:
        if m["verification_status"] not in RENDERABLE_STATUSES:
            errors.append(
                {
                    "rule": "no_unresolved",
                    "ply": m["ply"],
                    "message": f"verification_status is {m['verification_status']!r} — it must not reach a downstream consumer",
                }
            )

        basis = m.get("verification_basis") or []
        model_support = m.get("model_support") or {}
        if model_support.get("supported") and not (set(basis) & VALID_BASES):
            errors.append(
                {
                    "rule": "model_support_is_not_a_basis",
                    "ply": m["ply"],
                    "message": "model support is the only backing for this move — a model agreeing is not evidence it happened",
                }
            )

        if m["side"] == previous_side:
            errors.append(
                {
                    "rule": "alternating_sides",
                    "ply": m["ply"],
                    "message": f"{m['side']} moved twice in a row — a ply was duplicated or dropped",
                }
            )
            break
        previous_side = m["side"]

        move = chess.Move.from_uci(m["uci"])
        if move not in board.legal_moves:
            errors.append(
                {
                    "rule": "sequence_legal",
                    "ply": m["ply"],
                    "message": f"{m['uci']} is not legal in this position",
                }
            )
            break

        derived_san = board.san(move)
        if m["san"] != derived_san:
            errors.append(
                {
                    "rule": "san_matches_uci",
                    "ply": m["ply"],
                    "message": f"san {m['san']!r} disagrees with {m['uci']}, which is {derived_san!r}",
                }
            )

        board.push(move)

    return errors
