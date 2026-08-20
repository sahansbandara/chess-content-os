"""Tests for mascot cue timing.

design.md fixes three rules that are easy to break and expensive to notice late:
three popups per short and no more, cues anchored to a ply rather than to a
hand-written timestamp, and the bubble replacing the caption band rather than
stacking above it. The timing lives here so it can be checked without rendering
a frame.
"""

import pytest

from src.renderer.mascot import cues_for, MAX_POPUPS


def scene_moves(n, moment=3):
    return [
        {"ply": i, "san": f"m{i}", "caption": f"c{i}",
         "label": "blunder" if i == moment else "good"}
        for i in range(1, n + 1)
    ]


def test_a_short_never_gets_more_than_three_popups():
    cues = cues_for(scene_moves(20), moment_ply=3, fps=30, hook_s=1.6, step_s=0.95)

    assert len(cues) <= MAX_POPUPS


def test_the_reaction_is_anchored_to_the_moment_not_to_a_timestamp():
    early = cues_for(scene_moves(9), moment_ply=3, fps=30, hook_s=1.6, step_s=0.95)
    late = cues_for(scene_moves(9), moment_ply=7, fps=30, hook_s=1.6, step_s=0.95)

    reaction_early = next(c for c in early if c["kind"] == "reaction")
    reaction_late = next(c for c in late if c["kind"] == "reaction")

    assert reaction_late["start_frame"] > reaction_early["start_frame"]
    assert reaction_early["anchor_ply"] == 3
    assert reaction_late["anchor_ply"] == 7


def test_the_reaction_waits_until_the_move_has_landed():
    """Reacting while the piece is still sliding reads as reacting to nothing."""
    hook_s, step_s, fps = 1.6, 0.95, 30
    cues = cues_for(scene_moves(9), moment_ply=3, fps=fps, hook_s=hook_s, step_s=step_s)

    reaction = next(c for c in cues if c["kind"] == "reaction")
    landed_s = hook_s + 3 * step_s

    assert reaction["start_frame"] >= round(landed_s * fps)


def test_cues_never_overlap():
    cues = cues_for(scene_moves(9), moment_ply=3, fps=30, hook_s=1.6, step_s=0.95)

    for earlier, later in zip(cues, cues[1:]):
        assert earlier["end_frame"] <= later["start_frame"], (earlier["kind"], later["kind"])


def test_every_cue_lasts_long_enough_to_be_read():
    """1.2s of a popup is pure transition, so anything shorter shows nothing."""
    fps = 30
    cues = cues_for(scene_moves(9), moment_ply=3, fps=fps, hook_s=1.6, step_s=0.95)

    for c in cues:
        assert (c["end_frame"] - c["start_frame"]) / fps >= 1.6, c["kind"]


def test_the_reaction_text_quotes_the_engine_rather_than_inventing_one():
    moves = scene_moves(9)
    moves[2]["caption"] = "Kg6 — blunder. Ke6 was the move."

    cues = cues_for(moves, moment_ply=3, fps=30, hook_s=1.6, step_s=0.95)

    assert next(c for c in cues if c["kind"] == "reaction")["text"] == moves[2]["caption"]


def test_a_game_with_no_moment_still_gets_a_hook_and_an_outro():
    cues = cues_for(scene_moves(9), moment_ply=None, fps=30, hook_s=1.6, step_s=0.95)

    assert [c["kind"] for c in cues] == ["hook", "outro"]


def test_a_short_too_brief_to_hold_three_popups_drops_the_optional_ones():
    cues = cues_for(scene_moves(2), moment_ply=1, fps=30, hook_s=0.4, step_s=0.5)

    assert [c["kind"] for c in cues] == ["outro"]
