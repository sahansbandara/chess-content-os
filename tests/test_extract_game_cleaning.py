"""The cleaning stage must hand the reconstructor a game, not a review traversal.

`clean` already drops animation transients and repairs misread pieces. It also
has to strip the review screen's demonstrations, because the reconstructor that
follows will otherwise bridge every rewind with invented plies.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "workers"))

from extract_game import clean  # noqa: E402

P1 = "8/p4kp1/2r4p/2P2RP1/7P/8/P1P5/2K5"
P2 = "8/p5p1/2r3kp/2P2RP1/7P/8/P1P5/2K5"
P3 = "8/p5p1/2r1k2p/2P2RP1/7P/8/P1P5/2K5"
P4 = "8/p5p1/2r3kp/2PR2P1/7P/8/P1P5/2K5"


def run(t, fen):
    return {"t_start": t, "t_end": t + 0.3, "board_fen": fen, "frames": 20}


def test_clean_strips_the_review_demonstration_and_keeps_the_played_line():
    runs = [
        run(20.3, P1), run(20.8, P2),
        run(21.8, P1),
        run(23.7, P3),
        run(24.8, P2),
        run(26.4, P4),
    ]

    kept, report = clean(runs)

    assert [r["board_fen"] for r in kept] == [P1, P2, P4]
    assert [b["t_start"] for b in report["review"]["branch_states"]] == [23.7]
    assert len(report["review"]["rewinds"]) == 2
