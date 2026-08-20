"""When the pawn appears, and what it says.

design.md fixes the budget at three popups per short — hook, reaction to the
owner's mistake, and the outro. Five was the original sketch and it spends about
six seconds of a thirty-six second video on a character moving, in a format
whose entire job is "look at this position".

Cues are anchored to a **ply**, never to a hand-written timestamp. The moment
selector can move the window by a few plies and the pacing constant will change
again when narration drives it; an absolute timestamp goes stale the first time
either happens, and it goes stale silently.

The text is never written here. The reaction quotes the caption the engine
already produced, so a mascot cannot say something about the position that
`analysis.json` does not support.
"""

MAX_POPUPS = 3

ENTER_S = 0.40   # slide in, overshoot, settle
EXIT_S = 0.25    # bubble closes, mascot leaves
HOLD_S = 1.9     # readable time between the two
MIN_VISIBLE_S = ENTER_S + EXIT_S + 1.0


def _window(start_s, end_s, fps):
    return round(start_s * fps), round(end_s * fps)


def cues_for(moves, moment_ply, fps, hook_s, step_s, outro_s=2.0):
    """Resolve the popup schedule to frame numbers for this render.

    Returns cues in time order. Each carries the frame range it owns, so the
    renderer never computes timing and the two cannot disagree.
    """
    if not moves:
        return []

    plies = [m["ply"] for m in moves]
    last_landed_s = hook_s + len(moves) * step_s
    total_s = last_landed_s + outro_s

    # The reaction is placed first because the hook has to end before it starts.
    reaction = None
    if moment_ply is not None and moment_ply in plies:
        index = plies.index(moment_ply) + 1
        # Waits for the move to land: reacting mid-slide reads as reacting to
        # nothing, because the piece being discussed is still in the air.
        landed_s = hook_s + index * step_s
        end_s = min(landed_s + ENTER_S + HOLD_S + EXIT_S, last_landed_s)
        if end_s - landed_s >= MIN_VISIBLE_S:
            reaction = {
                "kind": "reaction", "anchor_ply": moment_ply,
                "text": moves[index - 1].get("caption", ""),
                "start_s": landed_s, "end_s": end_s,
            }

    # The hook opens the video and may run past the opening hold — nothing has
    # happened yet, so there is nothing for it to cover.
    hook_end = min(hook_s + 2 * step_s, reaction["start_s"] if reaction else total_s)
    hook = None
    if hook_end >= MIN_VISIBLE_S:
        hook = {
            "kind": "hook", "anchor_ply": None,
            "text": "Watch what I do here.",
            "start_s": 0.0, "end_s": hook_end,
        }

    # The outro lives in the hold after the final move, which exists precisely so
    # the video does not cut on a slide.
    outro = None
    if total_s - last_landed_s >= MIN_VISIBLE_S:
        outro = {
            "kind": "outro", "anchor_ply": None,
            "text": "What would you have played?",
            "start_s": last_landed_s, "end_s": total_s,
        }

    cues = [c for c in (hook, reaction, outro) if c]
    for c in cues:
        c["start_frame"], c["end_frame"] = _window(c.pop("start_s"), c.pop("end_s"), fps)
    return cues[:MAX_POPUPS]
