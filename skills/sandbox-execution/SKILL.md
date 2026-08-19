---
name: sandbox-execution
description: Run unfamiliar or risky code in an isolated environment before touching the main machine or production.
user-invocable: true
---

# Sandbox Execution

## When to use

Use for unknown repositories, generated scripts, dependency upgrades, migration tests, browser automation, security tests, third-party code, parallel tasks, or commands that may alter the environment.

Skip simple Markdown changes, documentation, and read-only analysis.

## Sandbox options

- Local Docker
- Daytona
- GitHub Codespaces
- Vercel Sandbox
- Temporary VM
- CI runner
- Disposable worktree

Do not force one provider across every project.

## Workflow

1. Identify execution risks.
2. Select the lightest safe isolation method.
3. Define allowed resources and network access.
4. Load only required files.
5. Install dependencies.
6. Run changes and tests.
7. Capture logs and results.
8. Export only approved changes or artifacts.
9. Destroy or archive the sandbox.
10. Record important findings.

## Output format

```text
SANDBOX PLAN:
- Reason:
- Sandbox type:
- Files/repository:
- Commands:
- Network access:
- Secrets required:
- Expected outputs:
- Cleanup:
```

## Quality checklist

- [ ] Main machine protected
- [ ] Production data excluded
- [ ] Secrets minimized
- [ ] Resource limits considered
- [ ] Logs captured
- [ ] Cleanup completed

## Stop conditions

Stop before using production credentials, connecting to production data, or exporting unreviewed changes.
