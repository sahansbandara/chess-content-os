"""Tests for review-rewind detection.

The source recording is Duolingo's "Review your game" screen, not a live game.
The review steps backwards to demonstrate a better move and then steps forward
again to the move that was actually played. A reconstructor that assumes board
states only move forward bridges that rewind by inventing plies.

The rule these tests pin: the game advances only while the review sits on the
newest position it has ever shown. Anything observed while it sits behind that
tip is a demonstration, and demonstrations are not moves.
"""

from src.validators.review_rewind import split_mainline


def run(t, fen):
    return {"t_start": t, "t_end": t + 0.2, "board_fen": fen, "frames": 12}


# Four positions from the real recording: P1 after Rf5+, P2 after Kg6,
# P3 the coach's suggested Ke6, P4 after Rd5.
P1 = "8/p4kp1/2r4p/2P2RP1/7P/8/P1P5/2K5"
P2 = "8/p5p1/2r3kp/2P2RP1/7P/8/P1P5/2K5"
P3 = "8/p5p1/2r1k2p/2P2RP1/7P/8/P1P5/2K5"
P4 = "8/p5p1/2r3kp/2PR2P1/7P/8/P1P5/2K5"


def test_a_forward_only_sequence_is_left_alone():
    runs = [run(1.0, P1), run(2.0, P2), run(3.0, P4)]

    mainline, report = split_mainline(runs)

    assert [r["board_fen"] for r in mainline] == [P1, P2, P4]
    assert report["rewinds"] == []
    assert report["branch_states"] == []


def test_a_demonstration_between_two_rewinds_is_dropped():
    # Play to P2, rewind to P1, demonstrate P3, rewind to P2, continue to P4.
    runs = [
        run(20.3, P1), run(20.8, P2),
        run(21.8, P1),
        run(23.7, P3), run(24.3, P3),
        run(24.8, P2),
        run(26.4, P4),
    ]

    mainline, report = split_mainline(runs)

    assert [r["board_fen"] for r in mainline] == [P1, P2, P4]
    assert [r["t_start"] for r in report["branch_states"]] == [23.7, 24.3]


def test_every_rewind_is_reported_with_both_timestamps():
    runs = [run(20.3, P1), run(20.8, P2), run(21.8, P1), run(24.8, P2), run(26.4, P4)]

    _, report = split_mainline(runs)

    assert report["rewinds"] == [
        {"t": 21.8, "back_to_t": 20.3, "board_fen": P1},
        {"t": 24.8, "back_to_t": 20.8, "board_fen": P2},
    ]


def test_a_demonstration_that_never_returns_is_dropped_and_reported():
    runs = [run(20.3, P1), run(20.8, P2), run(21.8, P1), run(23.7, P3)]

    mainline, report = split_mainline(runs)

    assert [r["board_fen"] for r in mainline] == [P1, P2]
    assert [r["t_start"] for r in report["branch_states"]] == [23.7]
    assert report["ends_off_mainline"] is True


def test_a_sequence_that_ends_on_the_tip_is_not_marked_unfinished():
    runs = [run(1.0, P1), run(2.0, P2)]

    _, report = split_mainline(runs)

    assert report["ends_off_mainline"] is False
