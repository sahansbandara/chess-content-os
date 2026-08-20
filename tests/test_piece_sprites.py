"""Tests for slicing the piece sheet into per-square sprites.

The sheet arrives as one image with the twelve pieces laid out by an
illustrator, not by a grid: pieces sit at whatever height and width they were
drawn, and the white and black halves do not match each other. Three things have
to come out the other side or the board looks wrong:

  1. each piece found by its own alpha, not by assuming even cells;
  2. a white piece and its black twin exactly the same height;
  3. the artist's hierarchy preserved — king tallest through pawn shortest.
"""

import numpy as np
import pytest

from src.workers.build_piece_sprites import NAMES, normalised_heights, piece_boxes


def sheet(heights, widths=None, gap=20, margin=10):
    """A synthetic sheet: six columns, two rows, pieces of the given heights.

    heights is {(row, col): height}. Every piece sits on its row's baseline, so
    the fixture has the one property the real sheet has.
    """
    widths = widths or {}
    row_h = max(h for h in heights.values()) + 2 * margin
    col_w = 60
    W = margin + 6 * (col_w + gap)
    H = margin + 2 * (row_h + gap)
    a = np.zeros((H, W), dtype=np.uint8)

    for (r, c), h in heights.items():
        w = widths.get((r, c), 40)
        baseline = margin + r * (row_h + gap) + row_h
        x = margin + c * (col_w + gap)
        a[baseline - h:baseline, x:x + w] = 255
    return a


def even_sheet():
    return sheet({(r, c): 200 - c * 20 for r in (0, 1) for c in range(6)})


def test_every_piece_is_found_by_its_own_alpha():
    boxes = piece_boxes(even_sheet())

    assert len(boxes) == 12
    assert set(boxes) == {f"{col}-{n}" for col in ("white", "black") for n in NAMES}


def test_a_box_is_tight_around_the_piece():
    a = sheet({(r, c): 200 - c * 20 for r in (0, 1) for c in range(6)},
              widths={(0, 0): 33})

    box = piece_boxes(a)["white-king"]

    assert box["h"] == 200
    assert box["w"] == 33


def test_a_piece_and_its_twin_come_out_the_same_height():
    """The real sheet's black rook is 11.6% taller than its white one."""
    heights = {(0, c): 200 - c * 20 for c in range(6)}
    heights.update({(1, c): 220 - c * 20 for c in range(6)})

    out = normalised_heights(piece_boxes(sheet(heights)), cell=180, king_fraction=0.92)

    for n in NAMES:
        assert out[f"white-{n}"] == out[f"black-{n}"], n


def test_the_king_lands_on_the_requested_fraction_of_the_cell():
    out = normalised_heights(piece_boxes(even_sheet()), cell=180, king_fraction=0.92)

    assert out["white-king"] == pytest.approx(180 * 0.92, abs=0.5)


def test_the_artists_hierarchy_survives():
    out = normalised_heights(piece_boxes(even_sheet()), cell=180, king_fraction=0.92)
    ordered = [out[f"white-{n}"] for n in NAMES]

    assert ordered == sorted(ordered, reverse=True)


def test_nothing_is_scaled_past_the_cell():
    out = normalised_heights(piece_boxes(even_sheet()), cell=180, king_fraction=0.92)

    assert max(out.values()) <= 180


def rgba_sheet(tmp_path):
    """A synthetic sheet with visibly different white and black halves."""
    from PIL import Image

    a = sheet({(r, c): 200 - c * 20 for r in (0, 1) for c in range(6)})
    rgba = np.zeros((*a.shape, 4), dtype=np.uint8)
    rgba[..., 3] = a
    half = a.shape[0] // 2
    rgba[:half, :, :3] = 240   # near-white pieces on the top row
    rgba[half:, :, :3] = 30    # near-black on the bottom row

    path = tmp_path / "sheet.png"
    Image.fromarray(rgba, "RGBA").save(path)
    return path


def test_white_and_black_sprites_do_not_collide_on_a_case_insensitive_filesystem():
    """macOS APFS is case-insensitive by default, so K.png and k.png are one file.

    Written as a test rather than a comment because the failure is silent: the
    black piece simply overwrites its white twin and every sprite comes out dark.
    """
    from src.workers.build_piece_sprites import build

    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        written, _, _ = build(rgba_sheet(tmp), tmp / "out", cell=90)

        names = [p.name for _, _, p in written]
        assert len(names) == 12
        assert len({n.lower() for n in names}) == 12, f"names collide when case is folded: {names}"


def test_a_white_sprite_keeps_its_own_colour():
    from PIL import Image

    from src.workers.build_piece_sprites import build

    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        out = tmp / "out"
        build(rgba_sheet(tmp), out, cell=90)

        white = np.array(Image.open(out / "wK.png").convert("RGBA"))
        black = np.array(Image.open(out / "bK.png").convert("RGBA"))
        white_px = white[white[..., 3] > 200][:, :3].mean()
        black_px = black[black[..., 3] > 200][:, :3].mean()

        assert white_px > black_px + 100, f"white {white_px:.0f} vs black {black_px:.0f}"
