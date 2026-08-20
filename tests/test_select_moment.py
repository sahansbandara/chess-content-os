"""Tests for moment selection — which few plies become the short.

The rule from docs/PLAN.md 1.4: the owner's largest win-% drop, padded with
setup and the punishment. Two things it must never do — pick the opponent's
blunder because it was bigger, and pick anything at all when the owner never
erred.
"""

import pytest

from src.analysis.select_moment import NoMoment, select_moment, slice_moves


def scored(ply, side, san, drop, label, best="Ke6"):
    return {
        "ply": ply, "side": side, "san": san, "win_percent_drop": drop,
        "label": label, "best_move_san": best,
    }


def analysis(moves):
    return {"content_id": "test-001", "owner_side": "black", "moves": moves}


def test_it_picks_the_owners_worst_move_not_the_biggest_one_on_the_board():
    doc = analysis([
        scored(1, "w", "e4", 0.0, "best"),
        scored(2, "b", "e5", 4.0, "good"),
        scored(3, "w", "Qh5", 47.0, "blunder"),   # bigger, but not the owner's
        scored(4, "b", "Nf6", 12.0, "mistake"),
        scored(5, "w", "Nc3", 0.0, "best"),
        scored(6, "b", "d6", 9.0, "inaccuracy"),
    ])

    moment = select_moment(doc, setup_plies=2, punishment_plies=1)

    assert moment["ply"] == 4
    assert moment["san"] == "Nf6"
    assert moment["label"] == "mistake"


def test_the_window_covers_the_setup_the_mistake_and_the_punishment():
    doc = analysis([
        scored(1, "w", "e4", 0.0, "best"), scored(2, "b", "e5", 0.0, "best"),
        scored(3, "w", "Nf3", 0.0, "best"), scored(4, "b", "Nf6", 0.0, "best"),
        scored(5, "w", "Nc3", 0.0, "best"), scored(6, "b", "d6", 20.0, "blunder"),
        scored(7, "w", "Bb5", 0.0, "best"), scored(8, "b", "Bd7", 0.0, "best"),
    ])

    moment = select_moment(doc, setup_plies=4, punishment_plies=2)

    assert (moment["start_ply"], moment["end_ply"]) == (2, 8)


def test_the_window_is_clamped_to_the_game_it_has():
    doc = analysis([
        scored(1, "w", "e4", 0.0, "best"),
        scored(2, "b", "f6", 30.0, "blunder"),
        scored(3, "w", "d4", 0.0, "best"),
    ])

    moment = select_moment(doc, setup_plies=4, punishment_plies=6)

    assert (moment["start_ply"], moment["end_ply"]) == (1, 3)


def test_a_tie_takes_the_earlier_ply_so_the_choice_is_repeatable():
    doc = analysis([
        scored(1, "w", "e4", 0.0, "best"),
        scored(2, "b", "f6", 15.0, "mistake"),
        scored(3, "w", "d4", 0.0, "best"),
        scored(4, "b", "g5", 15.0, "mistake"),
    ])

    assert select_moment(doc)["ply"] == 2


def test_a_game_the_owner_played_cleanly_has_no_moment_and_says_so():
    doc = analysis([
        scored(1, "w", "e4", 0.0, "best"),
        scored(2, "b", "e5", 3.0, "good"),
        scored(3, "w", "Qh5", 47.0, "blunder"),
    ])

    with pytest.raises(NoMoment):
        select_moment(doc)


def test_a_good_move_is_never_a_moment_however_large_its_drop():
    """`good` is above the mistake threshold by definition — trust the label."""
    doc = analysis([
        scored(1, "w", "e4", 0.0, "best"),
        scored(2, "b", "e5", 4.9, "good"),
    ])

    with pytest.raises(NoMoment):
        select_moment(doc)


# --- slicing the window out of a moves.json ----------------------------------

import chess  # noqa: E402

from src.validators.moves_contract import validate_moves  # noqa: E402


def move_doc(ucis, start=chess.STARTING_BOARD_FEN, castling="KQkq"):
    board = chess.Board(None)
    board.set_board_fen(start)
    board.turn = chess.WHITE
    board.set_castling_fen(castling)

    moves = []
    for ply, uci in enumerate(ucis, start=1):
        mv = chess.Move.from_uci(uci)
        moves.append({
            "ply": ply, "uci": uci, "san": board.san(mv),
            "side": "w" if board.turn == chess.WHITE else "b",
            "verification_status": "verified", "verification_basis": ["unique_path"],
        })
        board.push(mv)

    return {
        "schema_version": "1.0", "content_id": "test-001",
        "source": {"path": "inbox/test.mov", "kind": "test"},
        "start_position": {
            "piece_placement": {"value": start, "provenance": "observed"},
            "side_to_move": {"value": "w", "provenance": "observed"},
            "castling_rights": {"value": castling, "provenance": "inferred"},
            "en_passant": {"value": None, "provenance": "observed"},
        },
        "owner_side": "black", "moves": moves,
        "final_piece_placement": {"value": board.board_fen(), "provenance": "observed"},
    }


def test_the_slice_keeps_only_the_window():
    doc = move_doc(["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6"])

    sliced = slice_moves(doc, 3, 5)

    assert [m["ply"] for m in sliced["moves"]] == [3, 4, 5]
    assert sliced["window_plies"] == [3, 5]


def test_ply_numbers_survive_the_slice():
    """They are the join key into analysis.json and drive the on-screen move number."""
    doc = move_doc(["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6"])

    sliced = slice_moves(doc, 5, 6)

    assert [m["ply"] for m in sliced["moves"]] == [5, 6]
    assert [m["san"] for m in sliced["moves"]] == ["Bb5", "a6"]


def test_the_slice_starts_from_the_position_the_window_actually_begins_in():
    doc = move_doc(["e2e4", "e7e5", "g1f3", "b8c6"])

    sliced = slice_moves(doc, 3, 4)

    board = chess.Board()
    board.push_san("e4")
    board.push_san("e5")
    assert sliced["start_position"]["piece_placement"]["value"] == board.board_fen()
    assert sliced["start_position"]["side_to_move"]["value"] == "w"


def test_the_final_placement_is_the_end_of_the_window_not_the_end_of_the_game():
    doc = move_doc(["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6"])

    sliced = slice_moves(doc, 1, 2)

    board = chess.Board()
    board.push_san("e4")
    board.push_san("e5")
    assert sliced["final_piece_placement"]["value"] == board.board_fen()


def test_castling_rights_are_carried_into_the_window():
    doc = move_doc(["e2e4", "e7e5", "g1f3", "g8f6", "f1c4", "f8c5", "e1g1"])

    sliced = slice_moves(doc, 5, 7)

    assert "K" in sliced["start_position"]["castling_rights"]["value"]
    assert validate_moves(sliced) == []


def test_an_en_passant_square_survives_the_window_boundary():
    """Slice immediately after a double push and the capture must stay legal."""
    doc = move_doc(["e2e4", "a7a6", "e4e5", "d7d5", "e5d6"])

    sliced = slice_moves(doc, 5, 5)

    assert sliced["start_position"]["en_passant"]["value"] == "d6"
    assert validate_moves(sliced) == []


def test_a_window_outside_the_document_is_refused():
    doc = move_doc(["e2e4", "e7e5"])

    with pytest.raises(NoMoment):
        slice_moves(doc, 40, 44)
