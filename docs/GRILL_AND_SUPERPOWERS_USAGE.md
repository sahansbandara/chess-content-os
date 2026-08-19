# Grill + Superpowers Usage

This template includes built-in equivalents inspired by two useful workflow patterns:

1. `grill-project` — pre-project interrogation gate
2. `development-methodology` — disciplined implementation workflow

## Important

Do not copy external skill repositories directly into every project unless needed. This template already includes project-specific versions that match the folder structure and memory system.

## Use before every project

After explaining the project idea, tell the agent:

```text
Read PROJECT_SETUP_AGENT_PROMPT.md. First run the pre-project grill gate using skills/grill-project/SKILL.md, then customize the template. Do not write app code until CLAUDE.md is switched from TEMPLATE_MODE to PROJECT_MODE.
```

## Use after setup

After `PROJECT_MODE`, tell the agent:

```text
Use skills/development-methodology/SKILL.md before implementing this feature. Plan first, then build in small verified steps.
```

## Best workflow

| Phase | File/skill |
|---|---|
| Raw idea | `agent/BRIEF.md` |
| Challenge weak assumptions | `skills/grill-project/SKILL.md` |
| Customize template | `PROJECT_SETUP_AGENT_PROMPT.md` |
| Start project mode | `CLAUDE.md` |
| Plan implementation | `skills/development-methodology/SKILL.md` |
| Build | `workflows/build.md` |
| Test | `workflows/test.md` |
| Review | `workflows/audit.md` |
| Handoff | `workflows/handoff.md` |
