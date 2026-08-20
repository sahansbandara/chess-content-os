# Asset generation prompts

Two prompts, one per asset, plus the geometry they have to hit. Sizes come from
the measured renderer layout (Option A in `design.md`): board 720x720, squares
90x90, mascot band 880x354.

Generate the **board first, as code**, and the **pieces as a single sheet**. Both
choices exist to dodge specific failure modes, listed under each prompt.

Read `Non-negotiables` 7 in `CLAUDE.md` before generating anything: original or
verifiably licensed only, and "generated from a reference" is a derivative work.
Chess pieces themselves are safe — the Staunton pattern is public domain from
1849 — but a set that recognisably reproduces Duolingo's or Chess.com's artwork
is not.

---

## Prompt 1 — the board

Ask for **SVG or HTML code, not an image**. A chessboard is 64 flat rectangles;
generating it as a picture and tracing it back to vectors adds noise, blur and
thousands of stray nodes for zero gain. Paste this into a coding-capable model
(Claude, ChatGPT), not an image generator.

```text
Write a single self-contained HTML file that renders a chessboard as inline SVG.

Exact geometry, non-negotiable:
- Total board 720 x 720 pixels, viewBox "0 0 720 720".
- 8 x 8 grid, every square exactly 90 x 90 pixels, no gaps, no gutters.
- Square a1 is the BOTTOM-LEFT of the grid as drawn. Light and dark alternate,
  with a1 dark.
- The SVG's outer edge is the board's outer edge. No border, no frame, no
  margin, no padding, no drop shadow, no rounded corners.
- No coordinate labels. No letters a-h, no numbers 1-8, no text of any kind.
- Nothing but the 64 squares. No pieces, no highlights, no arrows.

Style:
- Flat solid colours only. Exactly two fills, one for light squares and one for
  dark squares.
- No gradients, no textures, no wood grain, no noise, no bevels, no inner
  shadows, no per-square opacity variation.
- Light squares #EBECD0, dark squares #739552. If you propose a different
  palette, keep both colours flat, keep the contrast between them at least as
  strong, and keep both light enough that a semi-transparent amber overlay
  (#E0A33E at 34% opacity) laid over any single square still reads clearly as a
  highlight.

Output:
- One HTML file. All CSS inline. No external stylesheets, fonts, scripts or
  images. No JavaScript.
- Each square must be its own <rect> with explicit x, y, width, height. Do not
  use a <pattern>, a CSS background, or a repeating-gradient — the squares are
  addressed individually by the renderer.
- Give every square an id of its algebraic name, id="a1" through id="h8".
```

**What goes wrong without those lines**

| Failure | Why it breaks the renderer |
|---|---|
| A decorative border or frame | Eats into the platform safe zones and pushes the grid off the coordinates the piece layer uses |
| Coordinate labels baked in | The board flips to the owner's side per video; baked labels end up upside-down and wrong |
| Wood texture or gradient | Traces into thousands of nodes, and the translucent last-move highlight stops reading against it |
| `<pattern>` or CSS background | No individually addressable squares, so no highlight layer and no per-square effects |
| Non-square, or padding inside the viewBox | Squares stop landing on 90px boundaries and every piece sits slightly off its square |
| Rounded corners | I round the board's corners in CSS; baked-in rounding double-rounds and clips the corner squares |

---

## Prompt 2 — the pieces

Generate **all twelve in one image**, as a sheet. This is the single most
important instruction on the page: twelve separate generations produce twelve
different scales, stroke weights and lighting angles, and a chess set that is
not one family looks worse than no custom set at all. One image forces one style.

```text
Create a single flat 2D vector-style sprite sheet of a complete chess piece set.

Layout, exact:
- Image 1080 x 360 pixels, transparent background.
- A 6-column by 2-row grid of cells, each cell exactly 180 x 180 pixels.
- Top row, left to right: white king, white queen, white rook, white bishop,
  white knight, white pawn.
- Bottom row, left to right: the same six pieces in black.
- One piece per cell, horizontally centred in its cell.

Scale and baseline — the part that usually goes wrong:
- Every piece STANDS ON A COMMON BASELINE. The bottom of each piece's base sits
  on the same horizontal line, 12 pixels above the bottom edge of its cell.
- Pieces are NOT scaled to fill their cells. They differ in height, in this
  exact order and roughly these proportions of the cell height:
  king 92%, queen 86%, rook 70%, bishop 78%, knight 76%, pawn 60%.
- The corresponding white and black piece are identical in shape and size.
  Only the colours differ.
- Every piece's base is roughly the same width, so the set looks like one family.

Style:
- Flat 2D side-profile silhouettes, like a clean app icon set.
- Solid fill plus a single uniform outline. The outline is the SAME thickness on
  every piece and every part of every piece.
- White pieces: cream #F2EDDF fill, deep navy #1E2A44 outline.
- Black pieces: deep navy #1E2A44 fill, cream #F2EDDF outline.
- The knight faces LEFT in every cell.
- Readable as a pure silhouette at 90 x 90 pixels. Interior detail that
  disappears at that size should not be there at all.

Do not include:
- No 3D rendering, no perspective, no photographic look, no marble or wood.
- No gradients, no shading, no highlights, no reflections, no ambient occlusion.
- No drop shadows and no glow, on the pieces or under them.
- No background of any kind. No board, no squares, no cell borders, no grid
  lines, no separators between cells.
- No text, letters, numbers, labels, captions or watermark.
- No cropping. Nothing may touch or overflow its cell edge.
```

**What goes wrong without those lines**

| Failure | Consequence |
|---|---|
| Each piece scaled to fill its own cell | The pawn ends up as tall as the king; the board reads as nonsense |
| No stated baseline | Pieces float at different heights inside their squares — the exact flaw the current set was replaced for |
| 3D render or shading | Auto-trace turns smooth shading into hundreds of stacked colour bands; file balloons, edges go muddy |
| Drop shadow | Background removal leaves a grey halo that shows on light squares |
| Ornate detail | Invisible at 90px; adds trace nodes and render time for nothing |
| Cell borders or a background | They survive background removal as a rectangle around every piece |
| Knight facing inconsistently | The set reads as two different sets |
| Anti-aliased edge against a white background | Removing white leaves a white fringe on dark squares. Transparent background from the start avoids it |

---

## After generating

1. Send the **board HTML** and the **piece sheet** before doing anything else.
2. Verification pass, in this order, before any of it is committed:
   - squares land on exact 90px boundaries;
   - piece heights follow the stated order, and every base sits on one baseline;
   - each piece is legible as a silhouette rendered at 90px;
   - no fringe or halo after background removal;
   - the traced SVG is real vector geometry and not a raster `<image>` wrapped in
     an `<svg>` tag — Canva's auto-trace produces the latter more often than not.
3. Only then wire into `src/renderer/scene.html`, keeping the existing vector
   glyph set in the tree as the fallback.

The renderer's determinism test must stay green: every image has to be fully
decoded before the first screenshot, or frame 0 differs from every later frame.
That bug has already bitten once, on SVG antialiasing.
