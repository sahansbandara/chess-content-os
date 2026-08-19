# AGENTS.md — Chess Content OS

Instructions for any agent runtime working in this repository (Codex, Gemini CLI,
Copilot, or another harness). `CLAUDE.md` is the full project brain; this file is
the portable subset. Where they differ, `CLAUDE.md` wins.

## What this project is

Chess Content OS turns the owner's own chess play into accurate, human-approved
short-form social content: verified moves → engine analysis → deterministic
render → script and voice → validators → human approval → publish → analytics.

It is not a video generator. It is a content pipeline whose core property is that
**published chess claims are true**.

## Read before acting

1. `rules/common/thinking-methodology.md`
2. `rules/common/agent-preflight.md`
3. `Agent/BRIEF.md` — scope, positioning, acceptance criteria
4. `Agent/TODO.md` — current objective and blockers
5. `Agent/MEMORY.md` — durable project knowledge, calibration numbers, falsification rules
6. `Agent/DECISIONS.md` — dated architecture decisions and their status
7. `design.md` — visual direction

Agent files live in `Agent/` (capitalised).

## Non-negotiables

1. **Chess truth is deterministic.** Local perception establishes board state; `python-chess` establishes legality and SAN. An LLM or VLM may compare pre-enumerated visual candidates. It may never author, invent, or certify a move sequence. A model's stated confidence is untrusted data.
2. **Ambiguity is surfaced, never resolved silently.** Multiple legal paths to the same observed state must be marked. Never take candidate #1 because it printed first. Never break a tie with chess plausibility.
3. **`moves.json` is the contract.** Everything downstream reads it, never pixels. Each move carries a status: `unique`, `visual_resolved`, `model_supported`, `human_confirmed`, `unresolved`.
4. **The renderer may not change move truth.**
5. **A human approves before anything publishes.** No autonomous posting. A single flag must kill all outward publishing.
6. **No secrets outside environment variables** — not in Markdown, logs, prompts, commits, or approval messages. Credential labels only.
7. **Own IP only in published output.** No third-party characters, mascots, branding, or app UI in video. Art must be original or verifiably licensed for commercial use.
8. **Voice matches the claim.** First-person content uses the owner's real recorded voice; synthetic TTS only where no personal claim is made.
9. **Preserve experiments.** New approach → new file. Do not delete or overwrite prior probes without explicit approval.

## Positioning — governs all generated copy

The channel is a **learner sharing mistakes**, not a guru teaching from authority.

```text
Everyone else:  "The best move here is Nf6."
This channel:   "2 mistakes and I got mated in 11. Don't do what I did."
```

- Never claim expertise the owner does not have.
- Lead with the owner's own mistake and what it cost.
- Frame lessons as avoidance, not instruction.
- Ask rather than lecture.
- Every chess claim traces to verified moves plus engine output, never model opinion.

## Stack

Python 3.11 (uv), `python-chess`, FFmpeg, `opencv-python-headless`, Pillow,
Stockfish (pending), Gemini behind a provider seam, Kokoro-82M TTS, HTML/CSS
renderer screenshotted frame-by-frame and muxed with FFmpeg.

Local macOS only. No cloud deployment. No backend; SQLite when a results store is
needed.

## Working agreements

- Conventional commits. Never commit secrets or `.env`.
- Review the diff before committing.
- Many small files over few large ones.
- Handle errors explicitly; never silently swallow.
- Stop on invalid chess state and preserve intermediate evidence rather than
  producing output that might be wrong.
- Do not add MCP, a framework, or infrastructure to look more agentic.

## End of session

Update `Agent/TODO.md` (always) plus any other agent file that actually changed,
commit with a conventional message, then:

```bash
bash .claude/hooks/git-sync-main.sh
```

That script pushes the branch and fast-forwards `main`. It never commits, never
rewrites history, never force-pushes, and refuses non-fast-forward updates.

Full checklist: `.claude/commands/wrap-session.md`.
