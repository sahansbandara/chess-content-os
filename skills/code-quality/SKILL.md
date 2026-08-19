---
name: code-quality
description: Build checks, tests, linting, maintainability, and safe refactoring.
user-invocable: true
---

# Code Quality


## When to use

Use after code changes, before handoff, before commit, or when debugging.

## Inputs to check

- package/build scripts
- test setup
- lint setup
- changed files
- known risks

## Workflow

1. Review changed files.
2. Check for secrets and unsafe logs.
3. Run available lint/build/test commands.
4. Fix small issues.
5. Explain failed checks clearly.
6. Do not hide errors.

## Output format

- Checks run
- Passed
- Failed
- Fixes made
- Remaining risks

## Quality checklist

- [ ] Build checked when available
- [ ] Tests checked when available
- [ ] No production secrets
- [ ] Error handling present
- [ ] Small functions and clear structure

## Stop conditions

Stop before large refactors unless user asked for refactor scope.
