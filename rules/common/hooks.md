# Hooks System

## Hook Types

- **PreToolUse**: Before tool execution (validation, parameter modification)
- **PostToolUse**: After tool execution (auto-format, checks)
- **Stop**: After every assistant turn (final verification, wrap-up gates)

## Configured hooks

Registered in `.claude/settings.json`. Scripts live in `.claude/hooks/`.

| Event | Script | Behavior |
|---|---|---|
| `Stop` | `session-wrap.sh` | Detects uncommitted or unpushed work. Blocks once and injects the `/wrap-session` checklist so agent files, `main`, and the deployment are brought up to date. Silent and non-blocking when the tree is clean. |

Supporting scripts, invoked from the checklist rather than by an event:

| Script | Behavior |
|---|---|
| `git-sync-main.sh` | Pushes the current branch, then fast-forwards `main` and pushes it. Handles the case where `main` is checked out in another worktree. Never commits, never force-pushes, refuses non-fast-forwards. |
| `deploy.sh` | Config-driven deploy (`deploy/deploy.config.json`, gitignored). Inert when absent or disabled. Exits 3 when configured without `auto_deploy`, requiring human confirmation before a `DEPLOY_CONFIRMED=1` re-run. |

### Writing a Stop hook that blocks

A `Stop` hook that returns `{"decision":"block","reason":"..."}` sends the reason
back to the model and continues the turn. Two guards are mandatory or it loops
forever:

1. Exit early when the input JSON has `stop_hook_active: true` — that flags a turn
   this hook already triggered.
2. Keep a cooldown timestamp on disk so a turn that fails to clear the condition
   cannot re-block immediately. `session-wrap.sh` uses `.claude/.wrap-state`
   with a 180-second window.

Also exit 0 silently when outside a git repository, and never let a hook failure
take down the turn.

## Auto-Accept Permissions

Use with caution:
- Enable for trusted, well-defined plans
- Disable for exploratory work
- Never use dangerously-skip-permissions flag
- Configure `allowedTools` in `~/.claude.json` instead

## TodoWrite Best Practices

Use TodoWrite tool to:
- Track progress on multi-step tasks
- Verify understanding of instructions
- Enable real-time steering
- Show granular implementation steps

Todo list reveals:
- Out of order steps
- Missing items
- Extra unnecessary items
- Wrong granularity
- Misinterpreted requirements
