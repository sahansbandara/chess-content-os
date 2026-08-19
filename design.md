# Design Direction — Chess Content OS

> Last updated: 2026-08-19
> Governs the deterministic renderer. Keep in sync with what is actually built.

## Brand posture

A learner's notebook, not a broadcaster's studio. Clean, confident, slightly
playful — never slick enough to imply expertise the owner does not have. The
production quality signals *effort and honesty*, not authority.

## Output format

| Property | Value |
|---|---|
| Resolution | 1080 × 1920 (9:16) |
| Frame rate | 30 fps |
| Duration | 30–40 s, driven by narration length, not a fixed target |
| Audio | Owner's recorded voice (first-person content); Kokoro-82M TTS (non-personal content) |
| Captions | Always burned in — most short-form views start muted |
| Ending | Loop-friendly |

## Safe zones

Platform UI paints over the video. Nothing readable may sit underneath:

| Zone | Reserved |
|---|---|
| Top | ~7% |
| Right edge | ~13% (action buttons) |
| Bottom | ~14% (title, channel, description) |

Hard constraint, not a guideline. Applies to text, badges, the mascot, and the
eval bar.

## Layout — board-primary, mascot transient

The board is the information surface for the whole video. The mascot is a
reaction layer that arrives, speaks, and leaves.

```text
┌─────────────────────────┐
│      [safe zone]        │
│        HOOK TEXT        │  large, 2 lines max
│                         │
│    ┌───────────────┐    │
│    │               │    │
│    │  CHESS BOARD  │    │  ~76% width, centred
│    │               │    │
│    └───────────────┘    │
│                         │
│      eval bar / badge   │
│                         │
│   ┌─────────────────┐   │  caption band — always present
│   │ narration line  │   │
│   └─────────────────┘   │
│      [safe zone]        │
└─────────────────────────┘
```

When a mascot popup is active, it enters from a screen edge and its speech
bubble **replaces** the caption band rather than stacking above it — one text
surface, never two competing.

## Board

- Light squares `#EBECD0`, dark squares `#739552`
- **Pieces are original vector glyphs drawn by the renderer**, matching the
  mascot's outline weight and palette. This removes the piece-art licensing
  problem rather than solving it: several popular chess piece sets are GPL
  artwork and unsuitable for monetised video, and shipping original vector
  pieces means there is nothing to license and nothing to attribute.
- If raster piece art is ever commissioned instead, it must be original or
  verifiably licensed for commercial use, rasterised once to PNG at target size.
- Pieces slide with easing; they never teleport
- Last-move squares stay highlighted
- Arrows and circles are drawn only from verified moves or engine output — never
  decorative

## Mascot — the pawn, popup model

### Character: an original pawn

The mascot is a **pawn** with eyes and expressions. Not a human character.

Why the pawn specifically, over a knight or any other piece:

- **It is the learner's piece.** Weakest, most numerous, and the one beginners
  throw away carelessly. That is the channel's subject matter in one object.
- **It promotes.** No other piece carries an improvement arc in its own rules. A
  pawn that becomes something stronger *is* the "900 → 1200, here is every
  mistake that got me there" spine, expressed visually.
- **Simplest silhouette in chess.** A sphere on a tapered collar and base. It
  stays legible at any on-screen size, which was the entire reason the earlier
  full-body human concept was rejected.
- **Zero human-character IP surface.** A pawn cannot be a derivative of somebody
  else's character.
- **It can be drawn by the renderer.** No illustrator, no image generation, no
  background matting, no licence question. Vector shapes only, so it is
  deterministic and recolourable — which unblocks Phase 0 with no external
  dependency.

Small stub arms are included: `outro_wave` and any hands-to-face beat need them.

### Palette

The mascot sits **outside** the board, against the dark page background, so it
must not collide with either the board or the move-quality colours.

| Element | Value | Reason |
|---|---|---|
| Body | cream `#F2EDDF` | echoes a white pawn; reads against the dark background |
| Outline & features | deep navy `#1E2A44` | separates the body from light board squares if they ever overlap |
| Accent | warm amber `#E0A33E` | one accent only; not used by any move-quality label |

Move-quality treatments own green, yellow, orange, red and gold. The mascot never
uses those as body colour, so a badge firing next to it never reads as part of it.

### Expression set

Ten states. Expression comes from eyes, eyebrows, stub arms, and whole-body
squash / stretch / tilt — a pawn has no face to over-animate, which is a feature.

| Asset id | Expression |
|---|---|
| `intro_peek` | leans in from the edge, eyebrows raised |
| `confused` | head tilt, one eyebrow up |
| `good_move` | eyes closed happy, small bounce |
| `shocked` | eyes wide, body stretched tall, leaning back |
| `thinking` | eyes up and to one side, slight lean |
| `explain` | leaning forward toward the board |
| `celebrate` | squash then stretch, eyes closed, arms up |
| `shh` | eyes narrowed, one stub arm raised |
| `deflated` | body drooping, eyes shut — replaces "facepalm", which needs hands a pawn does not really have |
| `outro_wave` | stub arm waving, gentle side-to-side tip |

### Promotion as a channel mechanic

Documented now, built later. As the owner's rating climbs, the mascot promotes:

```text
pawn → knight → bishop → rook → queen
```

Each promotion is a channel milestone the audience can see coming, tied to the
rating spine already in `BRIEF.md`. It gives the series a visible reward
structure that no competitor's mascot can copy, because it is derived from the
owner's own progress. Keep the same eyes, outline and palette across promotions
so it stays recognisably the same character.

### How it is drawn

**Primary: vector, drawn by the renderer.** SVG/CSS shapes composed at render
time. No asset files, no alpha channel problem, no matting, no licensing.
Identical input produces identical output.

**Upgrade route, if raster art is ever commissioned:** the renderer keeps a
swappable sprite interface, so the vector mascot can be replaced by a PNG set
without touching scene logic:

```text
assets/renderer/mascot/
├── intro_peek.png
├── confused.png
├── good_move.png
├── shocked.png
├── thinking.png
├── explain.png
├── celebrate.png
├── shh.png
├── deflated.png
└── outro_wave.png
```

Requirements if that route is taken: transparent alpha channel; **no baked-in
decorations** — no `?`, `!`, thought bubbles, toppling pieces or impact lines,
because the renderer owns every overlay and a sprite carrying its own bubble
fights it, while a baked chess prop can assert an event that contradicts the real
position; consistent proportions, outline weight and palette across the set, with
only pose and expression changing.

Naming: `intro_peek.png` on disk, `mascot_intro_peek` as the logical asset id in
`scene.json`. Both spellings appear in `PROJECT_MASTER_CONTEXT.md` §2.2 and §2.7;
this is the reconciliation.

No mouth-shape strip and no lip sync. The bubble carries the speech.

### Superseded

Two earlier directions in this file are dead:

1. A persistent bottom-centred "Presenter" mascot with a mouth-shape strip —
   replaced by the popup model, per `PROJECT_MASTER_CONTEXT.md` §2.3.
2. The human character concepts in `assets/Character/` — blocked as derivative
   works of a copyrighted character. Untracked from the repository and not to be
   used in output. See `Agent/DECISIONS.md`.

### Popup lifecycle

Driven by `renderFrame(n)`, never wall-clock animation.

```text
0.00s  fully outside frame
0.15s  begins sliding in
0.30s  reaches target with slight overshoot
0.40s  settles
       ↓ idle: gentle bob, occasional blink, faint scale breathing
       ↓ speech bubble open, narration line visible
-0.25s bubble closes
       mascot begins exit
+0.25s fully outside frame
```

Roughly 1.2 s of every popup is pure transition. Budget accordingly.

### Popup budget — three per short

Hook, mistake reaction, outro CTA. That is the whole allowance.

`PROJECT_MASTER_CONTEXT.md` §2.4 sketches five. Five spends ~6 s of a 36 s video
on the character moving and never lets the board hold attention for more than
~8 s — in a format whose entire job is "look at this position". The explain beat
works as voice over board with no character present.

### Entry directions

Right-edge and left-edge are primary; alternate between them so the format does
not become repetitive. A bottom pop-up is also available now that the character
is not edge-anchored by its pose — the pawn stands on a base and can rise from
below the caption band.

### Occlusion is enforced, not requested

The renderer knows the discussed move's from/to squares from the anchored ply in
`scene.json`. If the mascot's settled bounding box intersects either square, the
scene **fails** — reposition to another edge or drop the cue. An unenforced rule
gets broken on the first busy position.

## Move-quality treatments

Triggered by Stockfish classification. Thresholds live in the analysis stage.

| Label | Badge | Board | Mascot |
|---|---|---|---|
| Brilliant | gold, sparkle ring | gold burst on square | eyes wide |
| Best move | green | green pulse | approving |
| Good | soft green tick | none | absent |
| Inaccuracy | yellow | yellow ring | head tilt |
| Mistake | orange | orange flash | wince |
| Blunder | red | red flash + board shake | shocked |

"Good" deliberately triggers no popup. Not every move deserves an interruption.

## Motion principles

Perceived polish comes mostly from these, not from the character art:

- **Easing on everything.** Pieces accelerate and settle. Badges overshoot
  slightly, then land. The eval bar animates rather than jumping.
- **The freeze beat.** Before the reveal: board holds, screen dims, "…did you see
  it?" One second of runtime, the single biggest retention device in puzzle
  content.
- **Live eval bar.** Viewers should *see* the position collapse, not be told it did.
- **Lingering glow** on the square where it went wrong.
- Nothing moves without a reason. No decorative animation.

See `skills/motion/SKILL.md` before implementing timing curves.

## Typography

- Mobile legibility first. Heavy weights, generous tracking, high contrast.
- Hook: large, bold, at most two lines.
- Captions: medium weight, never more than three lines at once.
- Fonts must be licensed for commercial use and embedded locally.

## Determinism requirement

The renderer is driven by an explicit `renderFrame(n)` call. Identical
`moves.json` + `scene.json` + assets must produce an identical video. If the
renderer alters, reorders, or drops verified moves, the renderer is rejected —
see `CLAUDE.md` Non-negotiables.

## Accessibility

- Burned-in captions on every video
- Contrast checked against both the board and the bubble background
- No information conveyed by colour alone — every move-quality colour also
  carries a symbol and a word
