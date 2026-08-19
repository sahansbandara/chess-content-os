---
name: wrap-session
description: Post-coding-session wrap-up — update agent files, commit, land on main.
allowed_tools: ["Bash", "Read", "Write", "Edit", "Grep", "Glob"]
---

# /wrap-session

End-of-coding-session protocol for Chess Content OS. Fires automatically from the
`Stop` hook (`.claude/hooks/session-wrap.sh`) whenever the repo has uncommitted or
unpushed work. Also invocable by hand.

Standing policy: do not ask whether to run this. Run it.

Agent files live in `Agent/` (capitalised) in this repository.

## Step 1 — Update the agent files (never skip)

Update only what actually changed this session. Do not pad with restatements of
the diff — git already has that.

| File | Update when | What goes in |
|---|---|---|
| `Agent/TODO.md` | always | Move finished items to **Done**. Add anything discovered but not done to **Next** or **Blocked**. Rewrite **Current** and **Last session summary**. |
| `Agent/MEMORY.md` | when something non-obvious was learned | Project knowledge, mistakes to avoid, patterns that worked, calibration numbers, dependency/version gotchas, environment notes. Never secrets, keys, or tokens — credential *labels* only. |
| `Agent/DECISIONS.md` | when a design or tooling choice was made | One dated entry in the file's format: decision, reason, alternatives considered, risk, status. |
| `Agent/BRIEF.md` | when scope, positioning, users, or the problem statement moved | Keep it current; it is the first thing the next session reads. |
| `CLAUDE.md` | when a stack/tool/platform choice changed | Update the **Current selections** block. |
| `design.md` | when the visual direction changed | Keep in sync with what was actually built. |

If nothing meaningful changed for a file, leave it alone. `Agent/TODO.md` is the
exception — it always gets a pass.

### Project-specific recording rules

- New calibration numbers, template profiles, or scanner behaviour → `MEMORY.md`.
- Any change to how ambiguity is resolved, or a falsification rule passing/failing → `DECISIONS.md` **and** `MEMORY.md`.
- Never record a move sequence as "verified" in the agent files unless every bridge carries a verification status.

## Step 2 — Commit

Review the diff first, then commit with a conventional-commit message
(`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`, `perf:`, `ci:`).

Before staging, confirm the diff contains no secrets, `.env` files, API keys, or
credentials. `.env` and `.env.*` are gitignored — verify that is still true rather
than assuming it.

Also confirm no third-party IP (characters, branding, UI chrome) has been added to
`assets/` for use in published output.

Work that is genuinely mid-flight still gets committed — record the state in
`Agent/TODO.md` under **Current** and commit it as WIP. Unrecorded work is worse
than an untidy commit.

## Step 3 — Land it on `main`

```bash
bash .claude/hooks/git-sync-main.sh
```

Pushes the current branch, then fast-forwards `main` and pushes it. Never commits,
never rewrites history, never force-pushes, and refuses anything that is not a
fast-forward — if it reports a divergence, integrate `main` into the branch, then
re-run. Nothing is pushed to `main` on failure.

## Step 4 — Report one line

```
Wrap-up: agent files=[TODO,MEMORY] · commit=<sha> · main=pushed
```

Report what actually happened. If a step was skipped or failed, say so plainly and
quote the error.

## Not in this project

There is no deploy step. Chess Content OS runs locally; `deploy.sh` and
`deploy/deploy.config.json` were deliberately not copied from the template. If a
production worker or dashboard is added later, add the step back here and record
the decision in `Agent/DECISIONS.md`.
