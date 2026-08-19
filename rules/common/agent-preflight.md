# Agent Preflight — Run Before Any Coding

Every code agent MUST run this preflight before writing, editing, or generating code in this project. It engages three efficiency/discipline systems. Each check degrades gracefully: if a system is not installed, note it and continue — never hard-fail.

## The three systems

| System | Purpose | Trigger |
|---|---|---|
| **superpowers** | Skill discipline — brainstorming, TDD, debugging, verification-before-completion | ALWAYS before coding |
| **headroom** | Context compression (15–20% fewer tokens for coding agents, 60–95% for JSON/data) | When handling large tool results, data, or long context |
| **caveman** | Output compression (~75% fewer output tokens, full technical accuracy) | Optional — for terse working sessions |

## Preflight checklist

Run in order before the first code change:

1. **superpowers — MANDATORY**
   - Check for a matching skill BEFORE acting. If even a 1% chance a skill applies, invoke it via the `Skill` tool.
   - Process skills first (brainstorming, systematic-debugging), then implementation skills.
   - "Let's build X" → `brainstorming` skill first. "Fix this bug" → `systematic-debugging` first. New feature → `test-driven-development`.
   - If superpowers is not available, fall back to `skills/development-methodology/SKILL.md` and `rules/common/development-workflow.md`.

2. **headroom — USE WHEN CONTEXT IS HEAVY**
   - Before ingesting large tool outputs, JSON payloads, logs, or multi-file dumps, route them through headroom compression (`headroom_compress` / CLI `headroom`).
   - Use `headroom_retrieve` to expand compressed context when full detail is needed.
   - Check `headroom_stats` to confirm savings on long sessions.
   - If headroom is not installed, note it and proceed; do not block coding.

3. **caveman — OPTIONAL OUTPUT MODE**
   - For terse working sessions, enable caveman (`/caveman full|lite`) to cut output tokens ~75%.
   - Caveman NEVER applies to committed code, commit messages, PR bodies, or security/irreversible-action warnings — those stay full and clear.
   - Off by default; enable only when the user asks or a long iterative session benefits.

## Report line

After preflight, state one line before coding:

```
Preflight: superpowers=[used skill X | fallback methodology] · headroom=[on | absent] · caveman=[on | off]
```

## Rules

- superpowers skill check is non-negotiable and comes BEFORE any clarifying question or exploration.
- headroom is applied to context/data, not to source code being written.
- caveman affects chat output only, never the artifacts committed to the repo.
- None of these override `rules/common/thinking-methodology.md` — that framework runs on top of all three.
- User instructions always win. "stop caveman", "skip headroom", or a direct coding order overrides this preflight.
