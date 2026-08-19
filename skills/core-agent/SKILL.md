---
name: core-agent
description: Session control, boot sequence, safe file changes, memory, and handoff.
user-invocable: true
---

# Core Agent


## When to use

Use at the start of every agent session.

## Inputs to check

- `CLAUDE.md`
- `AGENTS.md`
- `agent/BRIEF.md`
- `agent/TODO.md`
- `agent/MEMORY.md`
- `agent/DECISIONS.md`

## Workflow

1. Check current mode: TEMPLATE_MODE or PROJECT_MODE.
2. Read brief, TODO, memory, decisions.
3. Identify active task and relevant skills.
4. Make the smallest safe change.
5. Run checks when available.
6. Update TODO/MEMORY only at meaningful points.
7. End with a handoff summary.

## Output format

- Current mode
- Task understood
- Files changed
- Checks run
- Risks
- Next step

## Quality checklist

- [ ] Read required context
- [ ] Did not start coding in TEMPLATE_MODE
- [ ] No secrets stored
- [ ] No destructive change without approval
- [ ] Handoff updated if session ends

## Stop conditions

Stop before delete, overwrite, deploy, migration, commit, push, or permission change.
