"""Move-quality classification from engine evaluations.

Classification drives what the video *says* about a move, so the thresholds are
tested at their boundaries. Win-percentage delta is used rather than raw
centipawns: losing 200cp when you are already lost barely matters, losing 200cp
from equality is a disaster, and centipawns cannot tell those apart.
"""

import pytest

from src.analysis.move_quality import classify, win_percent


def test_zero_centipawns_is_an_even_game():
    assert win_percent(0) == pytest.approx(50.0, abs=0.01)


def test_win_percent_is_symmetric_about_equality():
    assert win_percent(300) + win_percent(-300) == pytest.approx(100.0, abs=0.01)


def test_win_percent_saturates_when_completely_winning():
    assert win_percent(10000) > 99.0


@pytest.mark.parametrize(
    "drop,expected",
    [
        (0.0, "best"),
        (4.9, "good"),
        (5.0, "inaccuracy"),
        (9.9, "inaccuracy"),
        (10.0, "mistake"),
        (19.9, "mistake"),
        (20.0, "blunder"),
        (60.0, "blunder"),
    ],
)
def test_classification_boundaries(drop, expected):
    assert classify(drop, played_best=(drop == 0.0)) == expected


def test_playing_the_engines_top_move_is_best_even_with_a_tiny_drop():
    """Rounding noise must not demote the actual best move to 'good'."""
    assert classify(0.4, played_best=True) == "best"


def test_a_large_drop_is_still_a_blunder_even_if_it_was_the_top_move():
    """Only forced-loss positions do this. Truth beats flattery."""
    assert classify(35.0, played_best=True) == "blunder"
