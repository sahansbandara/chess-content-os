"""Tests for the human bridge-confirmation step.

An ambiguous bridge is a span of plies where several legal move sequences reach
the same observed board state. The board cannot tell them apart; only the owner
watching the recording can. These tests pin the two rules that matter:

  1. nothing is chosen for the human — an unanswered bridge is refused, never
     silently resolved to the first candidate;
  2. a confirmed bridge is marked `human_confirmed`, and nothing else is.
"""

import chess
import pytest

from src.validators.moves_contract import validate_moves
from src.workers.confirm_bridges import (
    ReplayMismatch,
    UnresolvedBridge,
    apply_choices,
    bridges,
    build_document,
)

# Two white rooks, on d5 and e1, and a recapture chain on e5. Whichever rook
# captures first is the one that gets taken, so both lines end on an identical
# board and no pixel can separate them. This is the real Bridge 1 in miniature.
TWO_ROOK_FEN = "4r2k/8/8/3Rp3/8/8/8/4R2K"


def extraction(moves, ambiguous, final_fen, start=TWO_ROOK_FEN):
    return {
        "video": "assets/raw/test.mov",
        "complete": True,
        "start_board_fen": start,
        "final_board_fen": final_fen,
        "reconstruction": {"ambiguous_bridges": ambiguous, "unreachable_states": []},
        "moves": moves,
    }


def move(ply, uci, san, side, t, ambiguous=False):
    return {
        "ply": ply,
        "uci": uci,
        "san": san,
        "side": side,
        "t_observed_s": t,
        "ambiguous_bridge": ambiguous,
    }


def two_rook_extraction():
    """Rdxe5 Rxe5 Rxe5, then Kg8 — the chain could equally have started Rexe5."""
    board = chess.Board(None)
    board.set_board_fen(TWO_ROOK_FEN)
    board.turn = chess.WHITE
    for san in ("Rdxe5", "Rxe5", "Rxe5", "Kg8"):
        board.push_san(san)
    return extraction(
        moves=[
            move(1, "d5e5", "Rdxe5", "w", 1.0, ambiguous=True),
            move(2, "e8e5", "Rxe5", "b", 1.0, ambiguous=True),
            move(3, "e1e5", "Rxe5", "w", 1.0, ambiguous=True),
            move(4, "h8g8", "Kg8", "b", 1.5),
        ],
        ambiguous=[{"t": 1.0, "candidates": ["Rdxe5 Rxe5 Rxe5", "Rexe5 Rxe5 Rxe5"]}],
        final_fen=board.board_fen(),
    )


def test_bridges_groups_the_plies_that_share_the_bridge_timestamp():
    doc = two_rook_extraction()

    found = bridges(doc)

    assert len(found) == 1
    assert found[0]["t"] == 1.0
    assert found[0]["plies"] == [1, 2, 3]
    assert found[0]["candidates"] == ["Rdxe5 Rxe5 Rxe5", "Rexe5 Rxe5 Rxe5"]


def test_choosing_the_second_candidate_replaces_the_move():
    doc = two_rook_extraction()

    moves = apply_choices(doc, {1.0: 1})

    assert moves[0]["san"] == "Rexe5"
    assert moves[0]["uci"] == "e1e5"
    assert [m["uci"] for m in moves] == ["e1e5", "e8e5", "d5e5", "h8g8"]


def test_an_unanswered_bridge_is_refused_rather_than_defaulted():
    doc = two_rook_extraction()

    with pytest.raises(UnresolvedBridge):
        apply_choices(doc, {})


def test_a_candidate_index_outside_the_candidate_list_is_refused():
    doc = two_rook_extraction()

    with pytest.raises(UnresolvedBridge):
        apply_choices(doc, {1.0: 7})


def test_confirmed_plies_are_human_confirmed_and_the_rest_are_verified():
    doc = two_rook_extraction()

    moves = apply_choices(doc, {1.0: 0})

    assert [m["verification_status"] for m in moves] == [
        "human_confirmed", "human_confirmed", "human_confirmed", "verified",
    ]
    assert moves[0]["verification_basis"] == ["human_confirmed"]
    assert moves[3]["verification_basis"] == ["unique_path"]


def test_a_choice_that_does_not_reach_the_observed_final_board_is_refused():
    doc = two_rook_extraction()
    # Legal, and the rest of the game still replays — but it lands somewhere else.
    doc["reconstruction"]["ambiguous_bridges"][0]["candidates"] = [
        "Rdxe5 Rxe5 Rxe5", "Rdxe5 Rxe5 Kg1",
    ]

    with pytest.raises(ReplayMismatch):
        apply_choices(doc, {1.0: 1})


def test_plies_are_renumbered_from_one_without_gaps():
    doc = two_rook_extraction()

    moves = apply_choices(doc, {1.0: 1})

    assert [m["ply"] for m in moves] == [1, 2, 3, 4]


def test_the_built_document_passes_the_moves_contract():
    doc = two_rook_extraction()

    built = build_document(doc, {1.0: 1}, content_id="test-001")

    assert validate_moves(built) == []
    assert built["verification_summary"] == {
        "verified": 1,
        "human_confirmed": 3,
        "unresolved": 0,
    }


def test_parse_choice_reads_timestamp_and_candidate_index():
    from src.workers.confirm_bridges import parse_choice

    assert parse_choice("16.733=1") == (16.733, 1)


def test_parse_choice_rejects_a_malformed_argument():
    from src.workers.confirm_bridges import parse_choice

    with pytest.raises(ValueError):
        parse_choice("16.733")


def test_the_bridge_description_numbers_candidates_without_recommending_one():
    from src.workers.confirm_bridges import describe_bridge

    text = describe_bridge(bridges(two_rook_extraction())[0])

    assert "t=1.0" in text
    assert "[0] Rdxe5 Rxe5 Rxe5" in text
    assert "[1] Rexe5 Rxe5 Rxe5" in text
    for word in ("recommend", "default", "likely", "best"):
        assert word not in text.lower()
