"""Slice an illustrated piece sheet into one sprite per square.

The sheet is drawn by an illustrator, not laid out on a grid. Pieces sit at
whatever height and width they were drawn at, the columns are unevenly spaced,
and — on the set this was written for — the black half is drawn larger than the
white half, by as much as 11.6% on the rook. A board where the black rook is
visibly taller than the white one looks broken in a way viewers notice without
being able to say why.

So nothing here assumes a grid. Pieces are found by their own alpha, twins are
forced to a common height, and the artist's own hierarchy is preserved rather
than replaced with numbers from a spec: this set already reads king > queen >
bishop > knight > rook > pawn, which is the whole point of the exercise.

Run:
  uv run python src/workers/build_piece_sprites.py \
      assets/renderer/pieces/chess_piece_sprite_sheet.png --cell 270
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

NAMES = ["king", "queen", "rook", "bishop", "knight", "pawn"]
COLOURS = ["white", "black"]
SYMBOLS = {"king": "K", "queen": "Q", "rook": "R", "bishop": "B", "knight": "N", "pawn": "P"}

ALPHA_FLOOR = 24  # below this is antialiasing fringe, not the piece
MIN_RUN = 8       # a band narrower than this is a stray speck


def _bands(present, min_run=MIN_RUN):
    """Contiguous runs of True in a 1-D mask, as (start, end_exclusive)."""
    out, start = [], None
    for i, value in enumerate(present):
        if value and start is None:
            start = i
        elif not value and start is not None:
            if i - start >= min_run:
                out.append((start, i))
            start = None
    if start is not None and len(present) - start >= min_run:
        out.append((start, len(present)))
    return out


def piece_boxes(alpha, alpha_floor=ALPHA_FLOOR):
    """Find each piece's tight bounding box. Keyed `white-king` … `black-pawn`.

    Columns are scanned per row rather than across the whole sheet, because the
    two rows do not have to share column positions and on a hand-laid-out sheet
    they usually don't.
    """
    mask = np.asarray(alpha) > alpha_floor
    rows = _bands(mask.any(axis=1))
    if len(rows) != 2:
        raise ValueError(f"expected 2 rows of pieces, found {len(rows)}")

    boxes = {}
    for colour, (r0, r1) in zip(COLOURS, rows):
        strip = mask[r0:r1]
        columns = _bands(strip.any(axis=0))
        if len(columns) != len(NAMES):
            raise ValueError(f"{colour} row: expected {len(NAMES)} pieces, found {len(columns)}")
        for name, (c0, c1) in zip(NAMES, columns):
            ys = np.where(strip[:, c0:c1].any(axis=1))[0]
            boxes[f"{colour}-{name}"] = {
                "x": c0, "w": c1 - c0,
                "top": r0 + int(ys[0]), "bottom": r0 + int(ys[-1]) + 1,
                "h": int(ys[-1]) - int(ys[0]) + 1,
            }
    return boxes


def normalised_heights(boxes, cell, king_fraction=0.92):
    """Target pixel height for every piece, twins matched, hierarchy preserved.

    A twin pair is averaged rather than one side being copied onto the other:
    picking white would silently shrink every black piece and picking black
    would inflate every white one, and neither half is more correct than the
    other. The whole set is then scaled so the king reaches `king_fraction` of
    the square, which fixes the set's footprint without touching its internals.
    """
    averaged = {n: (boxes[f"white-{n}"]["h"] + boxes[f"black-{n}"]["h"]) / 2 for n in NAMES}
    scale = cell * king_fraction / averaged["king"]
    return {f"{c}-{n}": round(averaged[n] * scale, 1) for c in COLOURS for n in NAMES}


def build(sheet_path, out_dir, cell, king_fraction=0.92, baseline_pad=None):
    """Write one square PNG per piece, all on a shared baseline."""
    sheet = Image.open(sheet_path).convert("RGBA")
    boxes = piece_boxes(sheet.getchannel("A"))
    heights = normalised_heights(boxes, cell, king_fraction)
    pad = round(cell * 0.045) if baseline_pad is None else baseline_pad

    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for key, box in boxes.items():
        piece = sheet.crop((box["x"], box["top"], box["x"] + box["w"], box["bottom"]))
        target_h = heights[key]
        ratio = target_h / box["h"]
        size = (max(1, round(box["w"] * ratio)), max(1, round(target_h)))
        piece = piece.resize(size, Image.LANCZOS)

        canvas = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
        canvas.alpha_composite(piece, ((cell - size[0]) // 2, cell - pad - size[1]))

        colour, name = key.split("-")
        # `wK` / `bK`, never `K` / `k`. macOS is case-insensitive by default, so
        # the lowercase file IS the uppercase file and every black piece would
        # silently overwrite its white twin, leaving a board of black pieces.
        path = out_dir / f"{colour[0]}{SYMBOLS[name]}.png"
        canvas.save(path)
        written.append((path.stem, size, path))
    return written, boxes, heights


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("sheet", type=Path)
    parser.add_argument("--out", type=Path, default=Path("assets/renderer/pieces/sprites"))
    parser.add_argument("--cell", type=int, default=270, help="3x the 90px board square")
    parser.add_argument("--king-fraction", type=float, default=0.92)
    args = parser.parse_args(argv)

    written, boxes, heights = build(args.sheet, args.out, args.cell, args.king_fraction)

    print(f"source heights (white / black) -> normalised, cell {args.cell}px\n")
    for name in NAMES:
        w, b = boxes[f"white-{name}"]["h"], boxes[f"black-{name}"]["h"]
        drift = (b - w) / w * 100
        print(f"  {name:<7} {w:>4} / {b:<4} ({drift:+5.1f}%)  ->  "
              f"{heights[f'white-{name}']:>6}px  ({heights[f'white-{name}']/args.cell*100:>4.1f}% of square)")
    print(f"\nwrote {len(written)} sprites to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
