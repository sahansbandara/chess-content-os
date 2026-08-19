---
name: tool-router
description: Select the safest and most reliable interface for external tools, web data, services, and software.
user-invocable: true
---

# Tool Router

## Routing priorities

For general external actions:

```text
1. Direct API
2. MCP integration
3. Browser automation
4. Computer Use
```

For web-data acquisition:

```text
1. Official API
2. MCP
3. HTTP/RSS/sitemap/export
4. Crawl4AI
5. Browser Use
6. Computer Use
```

## Workflow

1. Convert requirements into concrete actions.
2. Identify available official APIs.
3. Identify MCP integrations.
4. For web data, use `skills/web-data-acquisition/SKILL.md`.
5. Select the least fragile interface.
6. Define permissions, inputs, outputs, timeout, retries, and fallback.
7. Define sandbox requirement.
8. Define approval level.
9. Update `docs/TOOLS.md` or `docs/WEB_DATA_TOOLS.md`.
10. Add environment-variable names only.

## Quality checklist

- [ ] API/MCP checked first
- [ ] Web-data routing applied when relevant
- [ ] Least privilege used
- [ ] Failure behavior defined
- [ ] Fallback defined
- [ ] No secrets stored
- [ ] Approval boundary defined

## Stop conditions

Stop before granting new permissions, storing credentials, bypassing access controls, or performing unapproved external changes.
