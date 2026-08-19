---
name: development-methodology
description: Superpowers-style execution discipline for planning, implementation, testing, review, and handoff after PROJECT_MODE.
user-invocable: true
---

# Development Methodology

Use this after `CLAUDE.md` is switched to `PROJECT_MODE`.

This is the execution gate for software work. It prevents jumping from rough idea directly into messy implementation.

## When to use

Use for:
- new feature implementation
- refactors
- database/API changes
- UI flows
- auth/payments/security work
- deployment work
- unclear bug fixes
- architecture-impacting work

Skip for:
- one-line typo fixes
- simple text edits
- non-code answers
- already-approved tiny changes

## Inputs to check

- `CLAUDE.md`
- `agent/BRIEF.md`
- `agent/TODO.md`
- `agent/MEMORY.md`
- `agent/DECISIONS.md`
- selected rules
- relevant source files
- available tests/build commands

## Core workflow

1. Confirm `PROJECT_MODE`.
2. Understand the task and inspect relevant files.
3. Brainstorm if the task is vague.
4. Present the design/spec in clear chunks.
5. Ask approval before architecture-impacting changes.
6. Write a small implementation plan.
7. Implement in small tasks.
8. Test or verify each meaningful step.
9. Run review gate.
10. Update TODO/MEMORY/DECISIONS only when useful.
11. Give a final handoff.

## Planning rules

The plan must include:
- target files
- intended changes
- data/API impact
- UI impact
- tests/checks
- rollback or recovery note if risky

## TDD rule

Use test-driven development when tests exist or the change is high-risk:

1. Write or identify failing test.
2. Confirm failure.
3. Implement minimal fix.
4. Confirm pass.
5. Refactor safely.
6. Run related checks.

If tests do not exist, use a practical verification checklist and document that limitation.

## Review gate

Before saying complete, check:
- Does it satisfy the task?
- Did it break existing behavior?
- Are loading/error/empty states handled if UI?
- Are API/database/auth/security impacts handled?
- Are secrets avoided?
- Were tests/build/lint run if available?
- Are unresolved risks documented?

## Output format

Before implementation:

```text
PLAN:
- Goal:
- Files:
- Steps:
- Checks:
- Risks:
- Approval needed: yes/no
```

After implementation:

```text
RESULT:
- Changed:
- Checks run:
- Passed:
- Failed:
- Risks:
- Next step:
```

## Quality checklist

- [ ] PROJECT_MODE confirmed
- [ ] Relevant files inspected
- [ ] Plan written before implementation
- [ ] Small tasks used
- [ ] Tests/checks run where available
- [ ] Review gate completed
- [ ] No destructive change without approval
- [ ] Handoff updated

## Stop conditions

Stop before destructive file operations, database migrations, auth/security weakening, deployment, commit/push, major rewrite, or unapproved architecture changes.
