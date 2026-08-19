"""Find the move path between two observed board states.

The naive search enumerates every legal move at every ply, which branches by
about 35 and becomes infeasible past three plies — measured: a depth-8 search on
this recording did not finish in ten minutes.

Two constraints make deeper bridges tractable without giving up completeness
within the searched depth:

1. **Difference bound.** One ply changes at most four squares (castling moves
   two pieces; en passant clears a third). So if more than 4 * remaining_plies
   squares still differ from the target, no continuation can arrive in time and
   the branch is dead.

2. **Difference-guided ordering.** A move that touches no square where the two
   boards disagree cannot reduce the difference on this ply. Such moves are
   searched last rather than excluded, because a piece sometimes has to step
   aside before another can arrive.

Ambiguity is still reported, never resolved: the search returns every shortest
path it finds, up to a cap.
"""

import chess

MAX_CANDIDATES = 8


def board_diff(board, target_map):
    """Squares where `board` disagrees with the target piece map."""
    current = board.piece_map()
    squares = set(current) | set(target_map)
    return {
        s for s in squares
        if (current.get(s).symbol() if current.get(s) else None)
        != (target_map.get(s).symbol() if target_map.get(s) else None)
    }


def _target_map(target_fen):
    b = chess.Board(None)
    b.set_board_fen(target_fen)
    return b.piece_map()


def find_paths(board, target_fen, max_plies=6, limit=MAX_CANDIDATES):
    """All shortest legal paths from `board` to `target_fen`, as move lists."""
    target = _target_map(target_fen)

    if board.board_fen() == target_fen:
        return [[]]

    frontier = [(board.copy(stack=False), [])]

    for depth in range(max_plies):
        remaining = max_plies - depth
        found, nxt = [], []

        for state, path in frontier:
            diff = board_diff(state, target)

            # Nothing can close this gap in the plies that are left.
            if len(diff) > 4 * remaining:
                continue

            moves = list(state.legal_moves)
            # Touching a disputed square first; the rest still get searched.
            moves.sort(key=lambda m: not ({m.from_square, m.to_square} & diff))

            for move in moves:
                child = state.copy(stack=False)
                child.push(move)
                step = path + [move]

                if child.board_fen() == target_fen:
                    found.append(step)
                    if len(found) >= limit:
                        return found
                else:
                    nxt.append((child, step))

        if found:
            return found
        frontier = nxt

    return []


def san_line(board, path):
    b = board.copy(stack=False)
    out = []
    for move in path:
        out.append(b.san(move))
        b.push(move)
    return out


def board_from_placement(piece_placement, side_to_move="w"):
    """Build a board from an observed placement, inferring castling rights.

    A piece-placement FEN carries no castling rights, and `set_board_fen` clears
    them. That silently removes O-O and O-O-O from the legal moves, so any game
    where a side castles becomes unreconstructable — the search simply cannot
    express the move that was played.

    Rights are inferred from where the kings and rooks stand. This is an
    assumption, not an observation: a king that has moved and returned to e1
    would be granted rights it no longer has. Record it with `inferred`
    provenance, never as observed.
    """
    board = chess.Board(None)
    board.set_board_fen(piece_placement)
    board.turn = chess.WHITE if side_to_move == "w" else chess.BLACK

    rights = ""
    if board.piece_at(chess.E1) == chess.Piece(chess.KING, chess.WHITE):
        if board.piece_at(chess.H1) == chess.Piece(chess.ROOK, chess.WHITE):
            rights += "K"
        if board.piece_at(chess.A1) == chess.Piece(chess.ROOK, chess.WHITE):
            rights += "Q"
    if board.piece_at(chess.E8) == chess.Piece(chess.KING, chess.BLACK):
        if board.piece_at(chess.H8) == chess.Piece(chess.ROOK, chess.BLACK):
            rights += "k"
        if board.piece_at(chess.A8) == chess.Piece(chess.ROOK, chess.BLACK):
            rights += "q"

    board.set_castling_fen(rights or "-")
    return board
