"""Contract tests for moves.json — the truth seam.

Every rule here is a hard failure by specification (docs/PLAN.md 1.1). A
validator that downgrades any of these to a warning is broken: the whole point
of the contract is that nothing downstream has to re-check chess truth.
"""

from src.validators.moves_contract import validate_moves

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"


def build_doc(moves, piece_placement=START_FEN, side_to_move="w"):
    """Minimal well-formed document, so each test varies exactly one thing."""
    return {
        "schema_version": "1.0",
        "content_id": "test-001",
        "source": {"path": "assets/raw/test.mov", "kind": "test"},
        "start_position": {
            "piece_placement": {"value": piece_placement, "provenance": "observed"},
            "side_to_move": {"value": side_to_move, "provenance": "inferred"},
            "castling_rights": {"value": None, "provenance": "unknown"},
            "en_passant": {"value": None, "provenance": "unknown"},
        },
        "owner_side": "black",
        "moves": moves,
    }


def move(ply, uci, san, side, status="verified", basis=None, model_support=None):
    m = {
        "ply": ply,
        "uci": uci,
        "san": san,
        "side": side,
        "verification_status": status,
        "verification_basis": ["unique_path"] if basis is None else basis,
    }
    if model_support is not None:
        m["model_support"] = model_support
    return m


def test_illegal_move_is_rejected():
    """Rule 1: the sequence must be legal from start_position."""
    doc = build_doc([move(1, "e2e5", "e5", "w")])

    errors = validate_moves(doc)

    assert any(e["rule"] == "sequence_legal" for e in errors), errors


def test_same_side_moving_twice_is_reported_as_such():
    """Rule 2: consecutive same-side moves get their own diagnosis.

    Board replay would reject this as 'illegal' anyway, but that is the wrong
    diagnosis. Two moves by the same side means the perception layer duplicated
    or dropped a ply, and the message has to say so.
    """
    doc = build_doc([move(1, "e2e4", "e4", "w"), move(2, "d2d4", "d4", "w")])

    errors = validate_moves(doc)

    assert any(e["rule"] == "alternating_sides" for e in errors), errors


def test_san_disagreeing_with_uci_is_rejected():
    """Rule 3: stored SAN must equal the SAN derived from the UCI.

    This is the rule that stops UCI and SAN drifting apart silently. A caption
    generator reads SAN; if it disagrees with the move actually played, the
    video states a falsehood while every other check passes.
    """
    doc = build_doc([move(1, "e2e4", "Nf3", "w")])

    errors = validate_moves(doc)

    assert any(e["rule"] == "san_matches_uci" for e in errors), errors


def test_unresolved_move_is_rejected():
    """Rule 4: no unresolved move may reach a downstream consumer."""
    doc = build_doc([move(1, "e2e4", "e4", "w", status="unresolved", basis=[])])

    errors = validate_moves(doc)

    assert any(e["rule"] == "no_unresolved" for e in errors), errors


def test_model_support_alone_cannot_verify_a_move():
    """Rule 5: a VLM agreeing with a candidate is not evidence it happened.

    model_support is an annotation. If it is the only thing backing a move,
    the move is not verified, however confident the model claims to be.
    """
    doc = build_doc(
        [
            move(
                1, "e2e4", "e4", "w",
                basis=[],
                model_support={"provider": "gemini", "supported": True, "confidence": "high"},
            )
        ]
    )

    errors = validate_moves(doc)

    assert any(e["rule"] == "model_support_is_not_a_basis" for e in errors), errors


def test_start_position_field_without_provenance_is_rejected():
    """Rule 6: observed facts and inferred metadata must never be mixed."""
    doc = build_doc([move(1, "e2e4", "e4", "w")])
    doc["start_position"]["side_to_move"] = {"value": "w"}  # provenance dropped

    errors = validate_moves(doc)

    assert any(e["rule"] == "provenance_required" for e in errors), errors


def test_valid_document_produces_no_errors():
    """Baseline: the happy path must stay clean, or the rules are unusable."""
    doc = build_doc(
        [
            move(1, "e2e4", "e4", "w"),
            move(2, "e7e5", "e5", "b", status="human_confirmed", basis=["human_confirmed"]),
            move(3, "g1f3", "Nf3", "w", basis=["legal_path", "local_visual"]),
        ]
    )

    assert validate_moves(doc) == []


# --- regression against the real prototype recording -------------------------
# Guards the documented 36-move chain so a future scanner change cannot silently
# alter it (Agent/MEMORY.md, docs/PLAN.md testing priorities).

import json
import pathlib

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "prototype_moves.json"


def load_fixture():
    return json.loads(FIXTURE.read_text())


def test_prototype_chain_replays_to_the_observed_final_position():
    """The 36-ply chain must still reach State24, exactly."""
    import chess

    doc = load_fixture()
    board = chess.Board(None)
    board.set_board_fen(doc["start_position"]["piece_placement"]["value"])
    board.turn = chess.WHITE

    for m in doc["moves"]:
        mv = chess.Move.from_uci(m["uci"])
        assert mv in board.legal_moves, f"ply {m['ply']} {m['uci']} became illegal"
        assert m["san"] == board.san(mv), f"ply {m['ply']} SAN drifted"
        board.push(mv)

    assert board.board_fen() == doc["final_piece_placement"]["value"]


def test_full_prototype_chain_is_blocked_by_the_renderer_gate():
    """Plies 16-36 are unresolved, so the whole document must not render."""
    errors = validate_moves(load_fixture())

    assert errors, "unresolved plies must block the renderer"
    assert {e["rule"] for e in errors} == {"no_unresolved"}


def test_resolved_prefix_of_the_prototype_chain_passes():
    """Plies 1-15 are resolved, and that is the section a short would use."""
    doc = load_fixture()
    doc["moves"] = [m for m in doc["moves"] if m["ply"] <= 15]

    assert validate_moves(doc) == []


def test_castling_is_legal_when_the_start_position_grants_the_rights():
    """A piece-placement FEN carries no castling rights, so the document does.

    Ignoring them makes O-O read as illegal and rejects every game where either
    side castles — which is most of them.
    """
    doc = build_doc([
        move(1, "e1g1", "O-O", "w"),
        move(2, "e8g8", "O-O", "b"),
    ], piece_placement="r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R")
    doc["start_position"]["castling_rights"] = {"value": "KQkq", "provenance": "inferred"}

    assert validate_moves(doc) == []


def test_castling_stays_illegal_when_the_document_grants_no_rights():
    doc = build_doc([move(1, "e1g1", "O-O", "w")],
                    piece_placement="r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R")
    doc["start_position"]["castling_rights"] = {"value": None, "provenance": "unknown"}

    assert [e["rule"] for e in validate_moves(doc)] == ["sequence_legal"]
