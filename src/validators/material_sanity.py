"""Is this observed board's material possible in a real game?

Legality is not enough. A misclassified piece can yield a position that is
perfectly legal to play on, and the bridge search will happily build a legal
move sequence through it. That is exactly how the prototype's 36-move chain came
to rest on a black queen that the scanner had read as a rook: the position was
legal, every move was legal, and the game was still not the one that was played.

These checks ask whether the material could have arisen at all. They catch
classification errors that legality cannot see.

Applies to observed board states — never to a position a human has confirmed.
"""

import chess

# Starting counts per side.
INITIAL = {
    chess.PAWN: 8,
    chess.KNIGHT: 2,
    chess.BISHOP: 2,
    chess.ROOK: 2,
    chess.QUEEN: 1,
}

NAMES = {
    chess.PAWN: "pawn",
    chess.KNIGHT: "knight",
    chess.BISHOP: "bishop",
    chess.ROOK: "rook",
    chess.QUEEN: "queen",
}


def check_material(piece_placement):
    """Return a list of findings. Empty means the material is plausible."""
    board = chess.Board(None)
    board.set_board_fen(piece_placement)
    findings = []

    for color, side in ((chess.WHITE, "white"), (chess.BLACK, "black")):
        pieces = [p for p in board.piece_map().values() if p.color == color]
        counts = {t: sum(1 for p in pieces if p.piece_type == t) for t in INITIAL}
        kings = sum(1 for p in pieces if p.piece_type == chess.KING)

        if kings != 1:
            findings.append(
                {
                    "rule": "king_count",
                    "side": side,
                    "message": f"{side} has {kings} kings; a board has exactly one per side",
                }
            )

        pawns = counts[chess.PAWN]
        if pawns > INITIAL[chess.PAWN]:
            findings.append(
                {
                    "rule": "impossible_material",
                    "side": side,
                    "message": f"{side} has {pawns} pawns; a side never has more than 8",
                }
            )

        # Every piece above the starting count must be explained by a promotion,
        # and each promotion costs a pawn.
        promotions_needed = sum(
            max(0, counts[t] - INITIAL[t]) for t in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)
        )
        promotions_available = max(0, INITIAL[chess.PAWN] - pawns)

        if promotions_needed > promotions_available:
            excess = [
                f"{counts[t]} {NAMES[t]}s" for t in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)
                if counts[t] > INITIAL[t]
            ]
            findings.append(
                {
                    "rule": "impossible_material",
                    "side": side,
                    "message": (
                        f"{side} has {', '.join(excess)} with {pawns} pawns — that needs "
                        f"{promotions_needed} promotion(s) but only {promotions_available} "
                        f"pawn(s) are missing. A piece has been misread."
                    ),
                }
            )

    for square, piece in board.piece_map().items():
        if piece.piece_type == chess.PAWN and chess.square_rank(square) in (0, 7):
            findings.append(
                {
                    "rule": "pawn_on_back_rank",
                    "side": "white" if piece.color else "black",
                    "message": f"pawn on {chess.square_name(square)} — pawns cannot occupy rank 1 or 8",
                }
            )

    return findings


def _counts(piece_placement, color):
    board = chess.Board(None)
    board.set_board_fen(piece_placement)
    pieces = [p for p in board.piece_map().values() if p.color == color]
    return {t: sum(1 for p in pieces if p.piece_type == t) for t in INITIAL}


def check_transition(before, after):
    """Could `after` follow `before` in a real game, materially speaking?

    Between two observed boards a side's material can only shrink (captures) or
    convert a pawn into another piece (promotion). A piece type that gains a unit
    without a pawn being spent did not appear on the board — it appeared in the
    classifier.

    This is what catches a queen being read as a rook. The position on its own
    looks possible; the transition does not.
    """
    findings = []

    for color, side in ((chess.WHITE, "white"), (chess.BLACK, "black")):
        b, a = _counts(before, color), _counts(after, color)

        pawns_spent = max(0, b[chess.PAWN] - a[chess.PAWN])
        gained = {t: a[t] - b[t] for t in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN) if a[t] > b[t]}

        if not gained:
            continue

        # Every gained piece needs its own promoted pawn.
        if sum(gained.values()) > pawns_spent:
            detail = ", ".join(f"+{n} {NAMES[t]}{'s' if n > 1 else ''}" for t, n in gained.items())
            findings.append(
                {
                    "rule": "piece_type_appeared",
                    "side": side,
                    "message": (
                        f"{side} gained {detail} while losing {pawns_spent} pawn(s). "
                        f"Pieces do not appear or change type — one of these boards misread a piece."
                    ),
                }
            )

    return findings
