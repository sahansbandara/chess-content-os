"""The analyser must hand Stockfish the position the document describes.

It built its own start board and left out the castling rights the document
carries. python-chess still moves the rook — it recognises a castle by its
shape, not by the rights — so the placement stayed correct. What went wrong is
subtler and entirely invisible in the output: every position before a castle was
sent to the engine with castling unavailable to both sides, and Stockfish
evaluated a position that was not the one on the board.
"""

import chess
import chess.engine

from src.analysis.analyze_moves import analyse


class FirstLegalMoveEngine:
    """Enough of an engine to replay a document without launching Stockfish.

    It also keeps every position it was handed, which is what the assertions
    actually care about: the analyser's board, not the engine's opinion.
    """

    def __init__(self):
        self.seen = []

    def analyse(self, board, limit):
        self.seen.append(board.copy())
        return {
            "pv": [next(iter(board.legal_moves))],
            "score": chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE),
        }


def doc_with_castling():
    def move(ply, uci, san, side):
        return {
            "ply": ply, "uci": uci, "san": san, "side": side,
            "verification_status": "verified", "verification_basis": ["unique_path"],
        }

    return {
        "content_id": "castle-001",
        "owner_side": "white",
        "start_position": {
            "piece_placement": {"value": "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R",
                                "provenance": "observed"},
            "side_to_move": {"value": "w", "provenance": "observed"},
            "castling_rights": {"value": "KQkq", "provenance": "inferred"},
            "en_passant": {"value": None, "provenance": "observed"},
        },
        # Rfe1 is only legal if castling actually moved the rook to f1.
        "moves": [
            move(1, "e1g1", "O-O", "w"),
            move(2, "e8g8", "O-O", "b"),
            move(3, "f1e1", "Rfe1", "w"),
        ],
    }


def position_before(engine, ply):
    """The board the engine was asked to evaluate before that ply was played."""
    return engine.seen[2 * (ply - 1)]


def test_the_engine_is_given_the_castling_rights_the_document_records():
    engine = FirstLegalMoveEngine()

    results = analyse(doc_with_castling(), engine, depth=1)

    opening = position_before(engine, 1)
    assert opening.has_kingside_castling_rights(chess.WHITE)
    assert opening.has_queenside_castling_rights(chess.BLACK)
    assert [r["san"] for r in results] == ["O-O", "O-O", "Rfe1"]


def test_castling_still_moves_the_rook_so_the_placement_was_never_wrong():
    """The bug was in what the engine was told, not in where the pieces ended up."""
    engine = FirstLegalMoveEngine()

    analyse(doc_with_castling(), engine, depth=1)

    board = position_before(engine, 3)
    assert board.piece_at(chess.F1) == chess.Piece(chess.ROOK, chess.WHITE)
    assert board.piece_at(chess.G1) == chess.Piece(chess.KING, chess.WHITE)
