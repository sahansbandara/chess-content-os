---
name: prompt-maker
description: Create self-contained, high-quality prompts for agents and tools.
user-invocable: true
---

# Prompt Maker


## When to use

Use when creating prompts for Codex, Claude, ChatGPT, Cursor, image generation, research, business, academic, or coding tasks.

## Inputs to check

- Target tool/model
- Goal
- Context
- Constraints
- Input files
- Required output format
- Stop conditions

## Workflow

1. Define ROLE.
2. Define TASK.
3. Add CONTEXT.
4. Add REASONING steps.
5. Add OUTPUT contract.
6. Add STOPPING rules.
7. Add CHECKLIST.
8. Make the prompt self-contained.

## Output format

Use one copy-ready prompt block with:

- ROLE
- TASK
- CONTEXT
- REASONING
- OUTPUT
- STOPPING
- CHECKLIST

## Quality checklist

- [ ] Self-contained
- [ ] No vague wording
- [ ] Includes constraints
- [ ] Includes output format
- [ ] Includes stopping rules
- [ ] Includes quality checklist

## Stop conditions

Stop if the prompt would ask the model to violate safety, copy leaked prompts, expose secrets, or bypass permissions.
