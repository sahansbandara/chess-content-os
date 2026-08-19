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

**Superseded:** an earlier version of this file specified a persistent
bottom-centred "Presenter" mascot with a mouth-shape strip for lip sync. That
was chosen when the mascot was assumed to be a flat CSS character. It is
replaced by the popup model below, per `PROJECT_MASTER_CONTEXT.md` §2.3.

## Board

- Light squares `#EBECD0`, dark squares `#739552`
- Pieces from an original or verifiably permissively-licensed set, rasterised
  once to PNG sprites at target size. **No GPL-licensed piece art in monetised
  output** — several popular sets are GPL artwork.
- Pieces slide with easing; they never teleport
- Last-move squares stay highlighted
- Arrows and circles are drawn only from verified moves or engine output — never
  decorative

## Mascot — popup model

### Character identity: BLOCKED

The ten generated concept images in `assets/Character/` are **not cleared for
use**. They were generated from a reference image of Sherman from DreamWorks'
*Mr. Peabody & Sherman*, and the selected set retains that character's
identifying combination — ginger swept-up hair, large round black-rimmed
glasses, amber eyes, child proportions, and the peek-around-an-edge pose.
Generating new pixels from a copyrighted character produces a derivative work;
it does not create an original one.

This violates the original-IP rule in `PROJECT_MASTER_CONTEXT.md` §2.1.

Resolution required before any mascot art ships. Preferred direction, in order:

1. **A non-human mascot — a chess piece character** (knight or pawn with eyes and
   expressions). No human-character IP surface at all, thematically native,
   unmistakably owned, cheap to animate, and a simple silhouette stays legible at
   any on-screen size.
2. **A redesigned human character** changing at least three identifiers
   simultaneously: hair colour *and* silhouette, glasses shape, and a different
   signature pose. Changing one identifier is not sufficient.

Everything below is character-agnostic and survives either choice.

### Sprite contract

The mascot is a **swappable sprite set**, so replacing the art is a file copy,
not a code change:

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
├── facepalm.png
└── outro_wave.png
```

Requirements for every sprite:

- transparent alpha channel (the current concept images have none — all are
  opaque 3-channel PNGs)
- no baked-in decorations. No `?`, `!`, thought bubbles, toppling pieces, or
  impact lines. **The renderer owns every overlay** — a sprite carrying its own
  bubble fights the renderer's bubble, and a baked chess prop can assert an event
  that contradicts the real position.
- if a pose grips a surface, the gripped surface is part of the sprite —
  otherwise the hands grip nothing once the background is removed
- consistent across the set: same face proportions, hair, glasses, outfit,
  emblem, and rendering style. Only pose and expression change.

Naming: `intro_peek.png` on disk. `mascot_intro_peek` as the logical asset id in
`scene.json`. Both spellings exist in `PROJECT_MASTER_CONTEXT.md` §2.2 and §2.7;
this is the reconciliation.

**Matting note:** background removal on these concept renders is not a fuzz key.
Measured on the current set: the background is a gradient, not a flat colour, and
the light hoodie reads *brighter* than the backdrop — naive keying destroys the
character before it clears the background. Proper matting plus manual cleanup of
fine hair is required per sprite.

No mouth-shape strip. Lip-syncing a photoreal render is disproportionately hard
and invisible on a ~2.5 s popup. The bubble carries the speech.

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

Right-edge and left-edge are the primary moves. Alternate between them so the
format does not become repetitive.

If the chosen character's poses are edge-anchored, **edge-peek is the signature
move** and variety comes from which edge, lean depth, scale, and reaction — not
from inventing poses that break the character's visual logic. One recognisable
move is branding, not a limitation.

### Occlusion is enforced, not requested

The renderer knows the discussed move's from/to squares from the anchored ply in
`scene.json`. If the mascot's settled bounding box intersects either square, the
scene **fails** — reposition to the opposite edge or drop the cue. An unenforced
rule gets broken on the first busy position.

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
