# Chess Content OS

An AI-assisted, human-approved pipeline that turns my own chess games into
short-form social content — where every chess claim published is verifiably true.

Not a video generator. A small content operating system: reusable workers,
deterministic validators, provider seams, an approval gate, publishing, and a
performance feedback loop.

## The positioning

Most chess channels teach from authority: *"the best move here is Nf6."*

This one doesn't. I'm learning chess in public, and the content is my own
mistakes: *"2 mistakes and I got mated in 11 — don't do what I did."* Same chess
data, opposite posture. The goal is a community of learners, with me in it as a
student, not a guru talking down from the front of the room.

## The core rule

> Deterministic systems establish chess state and legality. AI helps interpret
> ambiguous visual evidence and generate language. **AI never becomes the
> authority on move truth.**

A vision model asked to read a whole game returns confident, wrong moves — this
project tested that and rejected it. Instead, local perception proposes board
states, `python-chess` constrains them to legal paths, ambiguity is surfaced
rather than guessed, and a human resolves what evidence cannot.

## Pipeline

```text
screen recording
  → board crop + calibration
  → 64-square perception  ──────────────►  piece-placement FEN per timestamp
  → legal bridge search (python-chess)
  → ambiguity audit
  → visual scoring + constrained VLM evidence
  → human confirmation
  → moves.json  ◄── the contract seam; nothing downstream touches pixels
  → Stockfish analysis (best / inaccuracy / mistake / blunder)
  → moment selection (my biggest mistake, not the prettiest tactic)
  → deterministic renderer (9:16, easing, eval bar, mascot)
  → script + voice + burned captions
  → validators
  → human approval  ◄── mandatory, no autonomous publishing
  → publish
  → analytics → what to make next
```

Two loops, never mixed:

- **Truth loop** — visual state → candidates → legality → ambiguity → more evidence
- **Content loop** — verified data → render/script → evaluator → revision → approval

A better explanation cannot repair an unverified move sequence.

## Status

Working: board calibration, 64-square scanner, temporal state extraction, legal
bridge reconstruction, ambiguity auditing, local visual disambiguation, a
constrained-VLM evidence probe (its control case passes), and a two-key provider
fallback client.

Not built yet: the `moves.json` contract, Stockfish analysis, moment selection,
the renderer, script and voice, validators, the Telegram approval gate, the
publisher, and analytics.

Honest summary: the truth layer is most of the way there and accounts for all of
the code so far. The half the audience actually sees does not exist yet.

See [Agent/TODO.md](Agent/TODO.md) for the live roadmap and
[docs/PLAN.md](docs/PLAN.md) for the phased build plan.

## Layout

```text
Agent/           BRIEF, TODO, MEMORY, DECISIONS — read these first
src/
  workers/       perception, state extraction, move reconstruction, probes
  providers/     external model seams (Gemini)
  validators/    chess-truth and content validators
  agents/        orchestration
  approval/      human approval gate
  publishers/    platform upload
  database/      results store
assets/
  templates/     piece recognition templates (duolingo_v2)
  raw/           source recordings
  processed/     derived media
skills/          reusable operating procedures
rules/           always-follow engineering guidelines
workflows/       repeatable multi-step procedures
docs/            architecture, automation, evaluation, permissions, plan
inbox/           drop a recording here to process it
output/          rendered media and evidence
logs/            run logs, probe results (never secrets)
```

## Requirements

- macOS on Apple Silicon (developed on an M4)
- Python 3.11 via [uv](https://github.com/astral-sh/uv)
- FFmpeg 8.x, ImageMagick
- Stockfish (pending)
- A Gemini API key, referenced by environment variable only

```bash
uv sync
```

Environment variable **names** are documented in [docs/ENV_VARS.md](docs/ENV_VARS.md).
Values live in `.env`, which is gitignored and never committed.

## Conventions

- Agent files in `Agent/` are the project's memory — they get updated every session
- Conventional commits; `main` is fast-forward only, never force-pushed
- Experiments are preserved, not overwritten — a new approach gets a new file
- No secrets in code, logs, prompts, commits, or documentation
- No third-party characters, branding, or app UI in published output

## Licence note

`python-chess` is GPL-3.0. That has no practical effect while this repository is
private, and would need addressing before making it public.

Piece and mascot artwork must be original or verifiably licensed for commercial
use — several popular chess piece sets are GPL-licensed art and are not suitable
for monetised video.
