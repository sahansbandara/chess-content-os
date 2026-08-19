"""Repairing a misread piece using the chess constraint.

When a transition shows a side gaining a piece type without spending a pawn, a
piece was misclassified. The chess position itself says what it must have been:
pieces do not appear, and they do not change type.

This never guesses. If more than one square could be the misread one, it refuses
and reports ambiguity — the same rule the rest of the pipeline follows.
"""

from src.validators.constrained_reclassify import resolve_misread

# The real prototype failure at 12.87s -> 13.27s.
BEFORE = "r1bqr1k1/pp3ppp/8/3QP3/4n3/1BB5/PPP2PPP/2KR3R"
AFTER_MISREAD = "r1b1r1k1/pp3ppp/8/3rP3/4n3/1BB5/PPP2PPP/2KR3R"
AFTER_CORRECT = "r1b1r1k1/pp3ppp/8/3qP3/4n3/1BB5/PPP2PPP/2KR3R"


def test_a_queen_read_as_a_rook_is_repaired():
    result = resolve_misread(BEFORE, AFTER_MISREAD)

    assert result is not None
    assert result["corrected_fen"] == AFTER_CORRECT
    assert result["square"] == "d5"
    assert result["observed"] == "r"
    assert result["corrected_to"] == "q"


def test_the_repair_makes_the_transition_materially_sane():
    from src.validators.material_sanity import check_transition

    result = resolve_misread(BEFORE, AFTER_MISREAD)

    assert check_transition(BEFORE, result["corrected_fen"]) == []


def test_a_clean_transition_is_left_alone():
    """White queen captures on d5. Nothing to repair."""
    before = "r1bqr1k1/pp3ppp/8/3pP3/4n3/1BB5/PPPQ1PPP/2KR3R"
    after = "r1bqr1k1/pp3ppp/8/3QP3/4n3/1BB5/PPP2PPP/2KR3R"

    assert resolve_misread(before, after) is None


def test_a_genuine_rook_move_is_not_treated_as_a_misread():
    """a8 rook goes to d8. Counts are unchanged, so nothing fires."""
    before = "r2qk3/8/8/8/8/8/8/4K3"
    after = "3rk3/8/8/8/8/8/8/4K3"

    assert resolve_misread(before, after) is None


def test_a_real_promotion_is_not_treated_as_a_misread():
    before = "4k3/P7/8/8/8/8/8/4K3"
    after = "Q3k3/8/8/8/8/8/8/4K3"

    assert resolve_misread(before, after) is None


def test_it_refuses_when_two_squares_could_be_the_misread_one():
    """Two new rooks appear at once — which one was the queen is not determined."""
    before = "3qk3/8/8/8/8/8/8/4K3"
    after = "r2rk3/8/8/8/8/8/8/4K3"

    result = resolve_misread(before, after)

    assert result is None or result.get("ambiguous") is True


def test_it_flags_but_cannot_repair_when_nothing_was_lost_to_explain_the_gain():
    """A knight appears with no piece lost.

    There is no candidate type to correct it to, so no repair is possible — but
    returning None would say "nothing wrong" about a board that is provably
    corrupt. It reports the problem as unrepairable instead.
    """
    before = "4k3/8/8/8/8/8/8/4K3"
    after = "4k3/8/8/4n3/8/8/8/4K3"

    result = resolve_misread(before, after)

    assert result["ambiguous"] is True
    assert result["lost"] == {}


# --- animation transients ----------------------------------------------------

from src.validators.constrained_reclassify import drop_transient_states  # noqa: E402


def test_a_state_missing_a_piece_in_flight_is_dropped():
    """A piece mid-move is on neither square, so the frame under-counts.

    Real case at 3.00s: the f1 bishop travelling to c4 leaves 31 pieces for one
    tenth of a second, between two 32-piece states.
    """
    runs = [
        {"t_start": 2.63, "board_fen": "rnbqkb1r/pp1p1ppp/2p2n2/4p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R"},
        {"t_start": 3.00, "board_fen": "rnbqkb1r/pp1p1ppp/2p2n2/4p3/4P3/2N2N2/PPPP1PPP/R1BQK2R"},
        {"t_start": 3.10, "board_fen": "rnbqkb1r/pp1p1ppp/2p2n2/4p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R"},
    ]

    kept, dropped = drop_transient_states(runs)

    assert [r["t_start"] for r in kept] == [2.63, 3.10]
    assert [r["t_start"] for r in dropped] == [3.00]


def test_a_genuine_capture_is_not_dropped():
    """Material really does fall when a piece is taken. That must survive."""
    runs = [
        {"t_start": 1.0, "board_fen": "r1bqr1k1/pp3ppp/8/3pP3/4n3/1BB5/PPPQ1PPP/2KR3R"},
        {"t_start": 2.0, "board_fen": "r1bqr1k1/pp3ppp/8/3QP3/4n3/1BB5/PPP2PPP/2KR3R"},
    ]

    kept, dropped = drop_transient_states(runs)

    assert len(kept) == 2
    assert dropped == []
