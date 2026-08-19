"""Repair a misclassified piece using the chess position as the constraint.

The perception layer reads each square independently, so it can call a queen a
rook. Legality will not notice — a legal game can be reconstructed through
misidentified pieces, which is exactly how the prototype's move chain came to
rest on a queen that had been read as a rook.

The position itself carries the answer. Between two observed boards a side's
material can only shrink, or convert a pawn by promotion. So when a side gains a
piece type without spending a pawn, and simultaneously loses another type, the
gained piece IS the lost one, misread. The only thing left to determine is which
square.

That is settled by elimination: a square holding the gained type that no piece of
that type could have come from. If more than one square qualifies, this refuses
rather than picking — same rule as every other ambiguity in this project.
"""

import chess

TRACKED = (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)


def _by_type(board, color, piece_type):
    return {
        chess.square_name(s)
        for s, p in board.piece_map().items()
        if p.color == color and p.piece_type == piece_type
    }


def _counts(board, color):
    pieces = [p for p in board.piece_map().values() if p.color == color]
    return {t: sum(1 for p in pieces if p.piece_type == t) for t in (*TRACKED, chess.PAWN)}


def resolve_misread(before_fen, after_fen):
    """Return a repair for `after_fen`, or None if there is nothing to repair.

    A returned dict has: square, observed, corrected_to, corrected_fen, side.
    A dict with ambiguous=True means a repair is needed but not determined.
    """
    before = chess.Board(None)
    before.set_board_fen(before_fen)
    after = chess.Board(None)
    after.set_board_fen(after_fen)

    for color, side in ((chess.WHITE, "white"), (chess.BLACK, "black")):
        b, a = _counts(before, color), _counts(after, color)

        pawns_spent = max(0, b[chess.PAWN] - a[chess.PAWN])
        gained = {t: a[t] - b[t] for t in TRACKED if a[t] > b[t]}
        lost = {t: b[t] - a[t] for t in TRACKED if b[t] > a[t]}

        if not gained or sum(gained.values()) <= pawns_spent:
            continue  # explained by promotion, or nothing gained

        # Exactly one unexplained extra piece, and exactly one type went missing
        # to account for it. More than that is not determined by material alone.
        if sum(gained.values()) != 1 or sum(lost.values()) != 1:
            return {"ambiguous": True, "side": side, "gained": gained, "lost": lost}

        gained_type = next(iter(gained))
        lost_type = next(iter(lost))

        # Which square holds the piece that should not exist? The one that no
        # piece of that type could have arrived at, because every other square
        # of that type is accounted for by a piece that was already there.
        before_squares = _by_type(before, color, gained_type)
        after_squares = _by_type(after, color, gained_type)
        candidates = sorted(after_squares - before_squares)

        if len(candidates) != 1:
            return {
                "ambiguous": True,
                "side": side,
                "gained": gained,
                "lost": lost,
                "candidate_squares": candidates,
            }

        square = candidates[0]
        corrected = after.copy()
        corrected.set_piece_at(chess.parse_square(square), chess.Piece(lost_type, color))

        observed = chess.Piece(gained_type, color).symbol()
        corrected_to = chess.Piece(lost_type, color).symbol()

        return {
            "ambiguous": False,
            "side": side,
            "square": square,
            "observed": observed,
            "corrected_to": corrected_to,
            "corrected_fen": corrected.board_fen(),
            "reason": (
                f"{side} appeared to gain a {chess.piece_name(gained_type)} while losing a "
                f"{chess.piece_name(lost_type)} with {pawns_spent} pawn(s) spent. Pieces do not "
                f"change type, so {square} is the {chess.piece_name(lost_type)}, misread."
            ),
        }

    return None


def drop_transient_states(runs):
    """Remove observed states that under-count because a piece was mid-move.

    A piece in flight sits on neither its origin nor its destination, so the
    frame reports one piece fewer than reality. The signature is a state whose
    outgoing transition shows a piece "gained" with nothing lost to explain it:
    nothing appeared, the earlier frame simply failed to see it.

    Distinguishing this from a real capture matters. A capture reduces material
    permanently, so the following transition shows no gain. Only a transient is
    followed by material coming back.

    Returns (kept, dropped).
    """
    from src.validators.material_sanity import check_transition

    transient_indices = set()
    for i in range(1, len(runs)):
        findings = check_transition(runs[i - 1]["board_fen"], runs[i]["board_fen"])
        for f in findings:
            if f["rule"] != "piece_type_appeared":
                continue
            res = resolve_misread(runs[i - 1]["board_fen"], runs[i]["board_fen"])
            # nothing was lost to account for the gain => the earlier frame
            # under-counted, rather than a piece having been misidentified
            if res and res.get("ambiguous") and not res.get("lost"):
                transient_indices.add(i - 1)

    kept = [r for i, r in enumerate(runs) if i not in transient_indices]
    dropped = [r for i, r in enumerate(runs) if i in transient_indices]
    return kept, dropped
