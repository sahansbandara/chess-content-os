---
name: security-privacy
description: Security review, privacy, permissions, secrets, abuse cases, and safe defaults.
user-invocable: true
---

# Security Privacy


## When to use

Use for auth, payments, personal data, admin panels, APIs, bots, file uploads, webhooks, and production readiness.

## Inputs to check

- user data collected
- auth model
- permissions
- secrets
- payments
- file uploads
- webhooks
- logging
- rate limits

## Workflow

1. Identify protected data.
2. Check auth and authorization.
3. Check secrets handling.
4. Check input validation.
5. Check logging/privacy.
6. Add rate limits and abuse protection where needed.
7. Document risks.

## Output format

- Security risks
- Required controls
- Privacy notes
- Abuse cases
- Fix checklist

## Quality checklist

- [ ] No secrets in code
- [ ] Permissions clear
- [ ] Input validation
- [ ] Sensitive logs avoided
- [ ] Abuse cases considered

## Stop conditions

Stop if a requested change exposes secrets, weakens auth, or bypasses safety controls.
