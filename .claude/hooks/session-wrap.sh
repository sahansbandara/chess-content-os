#!/usr/bin/env bash
#
# Stop hook — post-coding-session wrap-up gate.
#
# Fires after every assistant turn. If the repository has uncommitted or
# unpushed work, it blocks once and hands Claude the wrap-up checklist so the
# agent files, the main branch, and the deployment are brought up to date
# without the user having to ask.
#
# Exits 0 (silent, non-blocking) when there is nothing to wrap up.
#
set -uo pipefail

COOLDOWN_SECONDS=180
CHECKLIST=".claude/commands/wrap-session.md"

payload=$(cat 2>/dev/null || echo '{}')

# Never re-block a turn that this hook already triggered — that is an infinite loop.
if [ "$(printf '%s' "$payload" | jq -r '.stop_hook_active // false' 2>/dev/null)" = "true" ]; then
  exit 0
fi

root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$root" || exit 0

state_file="$root/.claude/.wrap-state"
now=$(date +%s)

# Cooldown: if the wrap-up was requested very recently, stay quiet. Prevents a
# stuck turn from blocking repeatedly.
if [ -f "$state_file" ]; then
  last=$(cat "$state_file" 2>/dev/null || echo 0)
  case "$last" in
    ''|*[!0-9]*) last=0 ;;
  esac
  if [ $((now - last)) -lt "$COOLDOWN_SECONDS" ]; then
    exit 0
  fi
fi

dirty=$(git status --porcelain 2>/dev/null)

unpushed=""
if git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
  unpushed=$(git log --oneline '@{u}..HEAD' 2>/dev/null)
elif git rev-parse --verify origin/main >/dev/null 2>&1; then
  unpushed=$(git log --oneline origin/main..HEAD 2>/dev/null)
fi

if [ -z "$dirty" ] && [ -z "$unpushed" ]; then
  exit 0
fi

printf '%s' "$now" > "$state_file" 2>/dev/null || true

summary=""
[ -n "$dirty" ] && summary="uncommitted changes:
$(printf '%s' "$dirty" | head -20)"
[ -n "$unpushed" ] && summary="$summary

unpushed commits:
$(printf '%s' "$unpushed" | head -10)"

reason="POST-SESSION WRAP-UP REQUIRED (automatic — Stop hook).

This repository has work that has not been recorded, pushed, or deployed:

$summary

Read $CHECKLIST and follow it in order, now. Do not skip the agent-file step and
do not ask the user whether to run it — this wrap-up is standing policy.

If the work in progress is genuinely incomplete (mid-refactor, failing tests),
say so in one line, record the state in agent/TODO.md, commit it as a WIP
commit, and still push. Never leave the session with unrecorded work."

jq -n --arg reason "$reason" '{decision: "block", reason: $reason}'
exit 0
