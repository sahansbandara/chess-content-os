---
name: output-evaluator
description: Evaluate generated outputs against explicit validation rules, scores, hard failures, and bounded revision loops.
user-invocable: true
---

# Output Evaluator

## When to use

Use where accuracy, format, compliance, consistency, or quality matters, including Telegram posts, prompts, reports, research, AI/ML results, trading content, structured JSON, and code changes.

## Inputs to check

- Required output format
- Approved examples
- Validation rules
- Criteria and weights
- Passing score
- Hard-failure conditions
- Maximum revisions
- Human approval requirements

## Workflow

1. Receive the candidate output.
2. Run hard validation first.
3. Score every rubric criterion.
4. Explain weaknesses with evidence.
5. Revise failed areas only.
6. Re-evaluate.
7. Stop at a pass, maximum revisions, a hard blocker, or a human decision.
8. Save project rules in `docs/EVALUATION.md`.

## Default loop

```text
Generate → Validate → Score → Revise → Re-evaluate → Stop
```

Default maximum revisions: 3.

## Output format

```text
EVALUATION:
- Hard validation: pass/fail
- Score: __/100
- Passing score:
- Failed criteria:
- Required corrections:
- Revision number:
- Final status: pass/fail/human-review
```

## Quality checklist

- [ ] Rubric exists
- [ ] Hard failures defined
- [ ] Passing score defined
- [ ] Revision count bounded
- [ ] Weaknesses explained
- [ ] High-risk output independently reviewed
- [ ] Unsupported claims not marked verified

## Stop conditions

Stop when evidence is unavailable, maximum revisions are reached, or human judgment is required.
