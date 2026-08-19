# Design Direction — Chess Content OS

> Last updated: 2026-08-19
> Governs the deterministic renderer. Keep in sync with what is actually built.

## Brand posture

A learner's notebook, not a broadcaster's studio. Clean, confident, slightly
playful — but never slick enough to imply expertise the owner does not have. The
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

Platform UI paints over the video and nothing readable may sit underneath:

| Zone | Reserved |
|---|---|
| Top | ~7% |
| Right edge | ~13% (action buttons) |
| Bottom | ~14% (title, channel, description) |

All text, badges, the mascot, and the eval bar live inside the remaining central
band. This is a hard constraint, not a guideline.

## Layout — "Presenter" (selected)

```text
┌─────────────────────────┐
│      [safe zone]        │
│        HOOK TEXT        │  large, 2 lines max
│                         │
│    ┌───────────────┐    │
│    │               │    │
│    │  CHESS BOARD  │    │  ~70% width, centred
│    │               │    │
│    └───────────────┘    │
│                         │
│  ┌───────────────────┐  │
│  │  speech bubble /  │  │  narration caption
│  │  caption line     │  │  doubles as the bubble
│  └─────────┬─────────┘  │
│         ( mascot )      │  centred, bottom
│      [safe zone]        │
└─────────────────────────┘
```

The speech bubble and the subtitle are **the same element** — narration text
appears in the mascot's bubble rather than competing with a separate caption band.

Rejected alternatives: board-dominant with a thin caption line (too little room
for narration), and mascot peeking from the right edge (collides with platform
action buttons).

## Board

- Light squares `#EBECD0`, dark squares `#739552`
- Pieces from an original or verifiably permissively-licensed set, rasterised once
  to PNG sprites at target size. **No GPL-licensed piece art in monetised output.**
- Pieces slide with easing; they never teleport between squares
- Last-move squares stay highlighted
- Arrows and circles are drawn only from verified moves or engine output — never decorative

## Mascot

Original character. **No third-party mascots, characters, or app UI, ever.**

- Ships as a swappable sprite set: a folder of expression PNGs plus a mouth-shape
  strip. Replacing the art is a file copy, not a code change.
- Expressions: idle, happy, shocked, thinking, wincing, celebrating
- Mouth flaps driven by audio amplitude; gentle idle bob; periodic blink
- Role is **fellow student reacting**, not teacher explaining. He is surprised by
  mistakes alongside the viewer, he does not lecture them.

## Move-quality treatments

Triggered by Stockfish classification. Thresholds live in the analysis stage, not here.

| Label | Badge | Board | Mascot |
|---|---|---|---|
| Brilliant | gold, sparkle ring | gold burst on square | eyes wide |
| Best move | green | green pulse | approving bob |
| Good | soft green tick | none | idle |
| Inaccuracy | yellow | yellow ring | head tilt |
| Mistake | orange | orange flash | wince |
| Blunder | red | red flash + board shake | shocked |

## Motion principles

Perceived polish comes mostly from these, not from the character art:

- **Easing on everything.** Pieces accelerate and settle. Badges overshoot slightly, then land. The eval bar animates rather than jumping.
- **The freeze beat.** Before the reveal: board holds, screen dims, "…did you see it?" One second of runtime, the single biggest retention device in puzzle content.
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

The renderer is driven by an explicit `renderFrame(n)` call, never by wall-clock
CSS animation. Identical `moves.json` plus identical assets must produce an
identical video. If the renderer alters, reorders, or drops verified moves, the
renderer is rejected — see `CLAUDE.md` Non-negotiables.

## Accessibility

- Burned-in captions on every video
- Contrast checked against the board and the bubble background
- No information conveyed by colour alone — every move-quality colour also carries
  a symbol and a word
