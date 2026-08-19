---
name: record-to-skill
description: Convert a narrated manual demonstration into a reusable skill, SOP, validation rules, examples, and evaluation rubric.
user-invocable: true
---

# Record to Skill

## When to use

Use when a repeated manual workflow should become consistent and reusable, such as Telegram posting, screenshot selection, trading formatting, bot testing, competitor research, reporting, or data preparation.

## Required demonstration content

Capture what is done, why decisions are made, inputs checked, rejection conditions, exceptions, and success criteria.

## Workflow

1. Obtain a recording, transcript, notes, or narrated demonstration.
2. Extract ordered actions.
3. Extract decision rules.
4. Extract rejection rules.
5. Extract exceptions.
6. Define success criteria.
7. Create an SOP.
8. Create a skill package with `SKILL.md`, examples, validation rules, and an evaluation rubric.
9. Test on at least two cases.
10. Improve based on failures.

## Output format

```text
SKILL EXTRACTION:
- Workflow name:
- Inputs:
- Ordered actions:
- Decision rules:
- Rejection rules:
- Exceptions:
- Success criteria:
- Required tools:
- Test cases:
```

## Quality checklist

- [ ] Decisions captured, not only clicks
- [ ] Rejection conditions captured
- [ ] Exceptions captured
- [ ] Success criteria measurable
- [ ] Skill tested
- [ ] Examples included
- [ ] Evaluator included

## Stop conditions

Stop if the demonstration does not explain reasoning needed for important decisions.
