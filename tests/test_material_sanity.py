"""Material plausibility of an observed board.

Legality is not enough. A misclassified piece can produce a position that is
perfectly legal to play on, and a legal move sequence can be reconstructed
through it — which is exactly how the prototype's 36-move chain came to be built
on a black queen that had been read as a rook.

These checks ask a different question: could this material have arisen from a
real game at all?
"""

import pytest

from src.validators.material_sanity import check_material

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"


def test_starting_position_is_sane():
    assert check_material(START) == []


def test_normal_midgame_position_is_sane():
    assert check_material("r1bqr1k1/pp3ppp/2n2n2/3pN3/3P4/1BB5/PPPQ1PPP/R3K2R") == []


def test_three_rooks_alone_is_not_enough_to_condemn_a_position():
    """Position-level counting cannot catch the prototype failure, and must not pretend to.

    Black has 3 rooks and no queen, but is also missing 3 pawns — so "lost the
    queen, promoted a pawn" is materially possible in isolation. What actually
    disproves it is the transition, not the position. See test_transitions below.
    """
    assert check_material("r1b1r1k1/pp3ppp/8/3rP3/4n3/1BB5/PPP2PPP/2KR3R") == []


def test_extra_rook_is_allowed_when_promotion_could_explain_it():
    """8 pawns and 3 rooks is impossible; 7 pawns and 3 rooks is not."""
    # black: 3 rooks, 7 pawns -> one pawn could have promoted
    assert check_material("r2rk2r/ppppppp1/8/8/8/8/PPPPPPPP/RNBQKBNR") == []


def test_two_kings_are_required():
    assert any(f["rule"] == "king_count" for f in check_material("8/8/8/8/8/8/8/K7"))


def test_nine_pawns_is_rejected():
    findings = check_material("rnbqkbnr/pppppppp/p7/8/8/8/PPPPPPPP/RNBQKBNR")

    assert any(f["rule"] == "impossible_material" for f in findings), findings


@pytest.mark.parametrize("square", ["a1", "h1", "a8", "h8"])
def test_a_pawn_on_the_back_rank_is_rejected(square):
    """Pawns cannot exist on rank 1 or 8 — they must have promoted."""
    board = {"a1": "P", "h1": "P", "a8": "p", "h8": "p"}[square]
    fen = {"a1": "4k3/8/8/8/8/8/8/P3K3", "h1": "4k3/8/8/8/8/8/8/4K2P",
           "a8": "p3k3/8/8/8/8/8/8/4K3", "h8": "4k2p/8/8/8/8/8/8/4K3"}[square]

    assert any(f["rule"] == "pawn_on_back_rank" for f in check_material(fen))


# --- transition-level checks -------------------------------------------------

from src.validators.material_sanity import check_transition  # noqa: E402


def test_a_queen_cannot_become_a_rook():
    """The real prototype failure, caught where it is actually visible.

    12.87s: black has a queen on d8 and two rooks.
    13.27s: black has no queen and three rooks, with pawns unchanged.
    A queen does not turn into a rook, and no pawn promoted. A piece was misread.
    """
    before = "r1bqr1k1/pp3ppp/8/3QP3/4n3/1BB5/PPP2PPP/2KR3R"
    after = "r1b1r1k1/pp3ppp/8/3rP3/4n3/1BB5/PPP2PPP/2KR3R"

    findings = check_transition(before, after)

    assert any(f["rule"] == "piece_type_appeared" for f in findings), findings
    assert any("rook" in f["message"] for f in findings), findings


def test_a_normal_capture_transition_is_accepted():
    """White queen captures on d5; black simply loses a pawn."""
    before = "r1bqr1k1/pp3ppp/8/3pP3/4n3/1BB5/PPPQ1PPP/2KR3R"
    after = "r1bqr1k1/pp3ppp/8/3QP3/4n3/1BB5/PPP2PPP/2KR3R"

    assert check_transition(before, after) == []


def test_a_real_promotion_is_accepted():
    """A pawn disappears from the 7th and a queen appears — that is legal."""
    before = "4k3/P7/8/8/8/8/8/4K3"
    after = "Q3k3/8/8/8/8/8/8/4K3"

    assert check_transition(before, after) == []


def test_a_piece_appearing_from_nowhere_is_rejected():
    """No capture, no promotion, an extra knight. Something was misread."""
    before = "4k3/8/8/8/8/8/8/4K3"
    after = "4k3/8/8/4N3/8/8/8/4K3"

    assert any(f["rule"] == "piece_type_appeared" for f in check_transition(before, after))
