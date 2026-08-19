---
name: automation-readiness
description: Decide whether a manual workflow is stable and safe enough to schedule or trigger automatically.
user-invocable: true
---

# Automation Readiness

## When to use

Use before scheduled tasks, webhooks, automatic publishing, monitoring jobs, unattended agents, or event-driven workflows.

## Inputs to check

- Manual workflow results
- Trigger
- Inputs
- Tool reliability
- Success criteria
- Failure handling
- Retry limits
- Notifications
- Approval points
- Audit logging
- Kill switch

## Workflow

1. Confirm the workflow succeeds manually.
2. Confirm inputs and outputs are stable.
3. Define trigger and schedule.
4. Define timeout and retry behavior.
5. Define failure notifications.
6. Define approval boundaries.
7. Define logging and monitoring.
8. Define kill switch.
9. Run a limited test.
10. Approve production automation only after the test passes.

## Readiness checklist

- [ ] Manual workflow works
- [ ] Inputs are stable
- [ ] Tools are reliable
- [ ] Success is measurable
- [ ] Failure handling exists
- [ ] Retry limits exist
- [ ] Notifications exist
- [ ] Approval gates exist
- [ ] Audit logging exists
- [ ] Kill switch exists

## Output format

```text
AUTOMATION READINESS:
- Workflow:
- Manual success evidence:
- Trigger:
- Risk level:
- Missing controls:
- Test plan:
- Ready: yes/no
```

## Stop conditions

Stop if the workflow has not succeeded manually, lacks failure handling or a kill switch, or performs high-risk actions without approval.
