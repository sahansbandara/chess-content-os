"""Turn engine evaluations into move-quality labels.

Uses win-percentage delta rather than raw centipawn loss. Dropping 200cp while
already lost barely changes the game; dropping 200cp from equality loses it.
Centipawns cannot distinguish those, win percentage can.
"""

import math

# Lichess's logistic mapping from centipawns to win probability.
_K = -0.00368208

# Win-percentage drop, for the side that just moved.
BLUNDER = 20.0
MISTAKE = 10.0
INACCURACY = 5.0


def win_percent(centipawns):
    """Win probability for the side to move, 0-100."""
    return 50 + 50 * (2 / (1 + math.exp(_K * centipawns)) - 1)


def classify(win_percent_drop, played_best=False):
    """Label a move from how much win probability it gave away.

    `played_best` protects the engine's own top choice from being demoted by
    rounding noise — but only when the drop is small. In a lost position the top
    move can still shed a lot of win probability, and calling that 'best' would
    flatter the player at the cost of an accurate video.
    """
    if win_percent_drop >= BLUNDER:
        return "blunder"
    if win_percent_drop >= MISTAKE:
        return "mistake"
    if win_percent_drop >= INACCURACY:
        return "inaccuracy"
    if played_best:
        return "best"
    return "good"
