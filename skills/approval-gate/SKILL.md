---
name: approval-gate
description: Classify agent actions by risk and require the correct human approval before execution.
user-invocable: true
---

# Approval Gate

## When to use

Use whenever an action can affect files, accounts, users, production systems, money, public content, permissions, or external services.

## Default risk model

### Low risk — may run automatically

- Read files
- Search documentation
- Analyze content
- Draft outputs
- Run tests in a sandbox
- Create reports
- Collect public metrics

### Medium risk — notify or request approval

- Create branches
- Open pull requests
- Publish to a test channel
- Modify non-production data
- Schedule drafts
- Create external resources with no material cost
- Run limited browser automation

### High risk — explicit approval required

- Publish publicly
- Merge pull requests
- Deploy production systems
- Change production secrets or permissions
- Execute trades or payments
- Delete files or records
- Run destructive migrations
- Contact customers
- Enable unrestricted Computer Use

## Workflow

1. Describe the exact action.
2. Identify affected files, data, accounts, users, and environments.
3. Assign risk level.
4. Explain impact and rollback.
5. Request approval when required.
6. Record the result.
7. Execute only the approved scope.

## Output format

```text
APPROVAL REQUEST:
- Proposed action:
- Risk level:
- Expected impact:
- Affected files/data/accounts:
- Recovery method:
- Approval required:
- Approval status:
```

## Quality checklist

- [ ] Risk classified
- [ ] Impact explained
- [ ] Rollback explained
- [ ] Scope is specific
- [ ] Approval recorded
- [ ] No action exceeds approved scope

## Stop conditions

Stop whenever required approval has not been explicitly granted.
