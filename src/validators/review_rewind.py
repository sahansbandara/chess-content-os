"""Separate the game the review is replaying from the moves it is demonstrating.

Duolingo's "Review your game" screen does not only replay what was played. It
steps backwards to a position, shows the move the coach would have preferred,
then steps forward again to the move actually made. To a reconstructor that
assumes board states only ever move forward, that backward step looks like a
move, and the demonstration that follows looks like more moves. In the prototype
recording it manufactured eight plies that nobody played, including a position
with a king standing in check.

The tell is cheap and deterministic: the review can only rewind to a position it
has already shown. So the game advances while the review sits on the newest
position it has ever displayed — the tip — and everything observed while it sits
behind the tip is a demonstration.

Limitation, and it is a real one: this treats *any* return to a previous
placement as a rewind. A genuine threefold repetition in a live game would be
discarded the same way. That is safe for review recordings, which is all this
project ingests today, and wrong for a recording of live play. Every rewind is
reported so the discard is visible rather than silent.
"""


def split_mainline(runs):
    """Split observed board states into the replayed game and the demonstrations.

    Returns `(mainline, report)`. The report carries every rewind, every state
    dropped as a demonstration, and whether the recording ended off the mainline
    — which means the tail of the game was never shown and is simply missing.
    """
    mainline = []
    index_of = {}
    rewinds = []
    branch_states = []
    cursor = -1

    for state in runs:
        fen = state["board_fen"]
        seen_at = index_of.get(fen)

        if seen_at is not None:
            if seen_at != cursor:
                rewinds.append({
                    "t": state["t_start"],
                    "back_to_t": mainline[seen_at]["t_start"],
                    "board_fen": fen,
                })
            cursor = seen_at
            continue

        if cursor == len(mainline) - 1:
            mainline.append(state)
            index_of[fen] = len(mainline) - 1
            cursor += 1
        else:
            branch_states.append(state)

    return mainline, {
        "rewinds": rewinds,
        "branch_states": branch_states,
        "ends_off_mainline": cursor != len(mainline) - 1,
    }
