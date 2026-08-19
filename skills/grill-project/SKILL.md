---
name: grill-project
description: Pre-project interrogation gate that stress-tests the idea before template customization or coding.
user-invocable: true
---

# Grill Project

Use this before switching from `TEMPLATE_MODE` to `PROJECT_MODE`, especially when the idea is vague, risky, large, architecture-impacting, business-critical, AI/ML-heavy, trading-related, Telegram-related, database-heavy, payment-related, or security-sensitive.

This is a critique gate, not a coding skill.

## When to use

Use for:
- new project start
- unclear MVP
- unclear user roles
- unclear stack
- unclear database/API/auth/payment decisions
- risky AI/ML, Telegram, trading, fintech, or business logic
- implementation plans that feel like guessing

Skip for:
- tiny UI edits
- typo fixes
- already-scoped bugs
- complete specifications

## Inputs to check

- `agent/BRIEF.md`
- user project idea
- `agent/TODO.md`
- `agent/MEMORY.md`
- `agent/DECISIONS.md`
- selected stack, if any

## Workflow

1. Read the project idea and current brief.
2. Identify the weakest assumption.
3. Ask one hard question at a time.
4. For each question, include:
   - why this question matters
   - recommended answer
   - impact if answered differently
5. Continue until MVP, users, main flow, stack, data, security, and first milestone are clear.
6. Write resolved answers into:
   - `agent/BRIEF.md`
   - `agent/DECISIONS.md`
   - `agent/TODO.md`
   - `agent/MEMORY.md` only if reusable
7. Stop grilling when more questions would delay execution more than reduce risk.

## Required question areas

| Area | Clarify |
|---|---|
| User | Who exactly uses this? |
| Pain | What problem is painful enough? |
| Main flow | First action → final result |
| MVP | What is version 1 only? |
| Stack | Required vs assumed technology |
| Data | What must be stored? |
| Auth | Who can access what? |
| Payments | Is money involved? |
| AI/ML | Training, inference, dataset, metrics |
| Telegram | Bot/channel/admin/user flow |
| Trading | Risk, disclaimer, no guaranteed-profit claims |
| Deployment | Where it runs |
| Failure | What can go wrong? |

## Output format

For each question:

```text
QUESTION:
[One hard question]

WHY IT MATTERS:
[Short reason]

RECOMMENDED ANSWER:
[Default answer the agent recommends]

IF DIFFERENT:
[What changes if the user answers differently]
```

After grilling is complete:

```text
GRILL RESULT:
- Clear MVP:
- Key decisions:
- Biggest risk:
- First milestone:
- Ready for setup: yes/no
```

## Quality checklist

- [ ] One question at a time
- [ ] No 20-question dumps
- [ ] Recommended answer included
- [ ] Weak assumptions challenged
- [ ] Decisions recorded
- [ ] MVP narrowed
- [ ] No coding started
- [ ] No secrets stored

## Stop conditions

Stop before coding, destructive changes, deployment, commit, push, or secret storage.
