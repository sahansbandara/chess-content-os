#!/usr/bin/env bash
#
# Land the current branch's committed work on `main` and push it.
#
# Assumes the caller has already committed. Never commits, never rewrites
# history, never force-pushes. Refuses anything that is not a fast-forward so
# a divergent main is surfaced instead of silently clobbered.
#
# Handles the git-worktree case: when `main` is checked out in another
# worktree, git forbids updating its ref from here, so the merge is performed
# inside that worktree instead.
#
set -uo pipefail

MAIN_BRANCH="${MAIN_BRANCH:-main}"

fail() { echo "git-sync-main: $*" >&2; exit 1; }

root=$(git rev-parse --show-toplevel 2>/dev/null) || fail "not a git repository"
cd "$root" || fail "cannot enter $root"

[ -n "$(git status --porcelain)" ] && fail "working tree is dirty — commit first, then re-run"

branch=$(git rev-parse --abbrev-ref HEAD)
[ "$branch" = "HEAD" ] && fail "detached HEAD — check out a branch first"

git remote get-url origin >/dev/null 2>&1 || fail "no 'origin' remote configured"

# --- already on main: nothing to merge -------------------------------------
if [ "$branch" = "$MAIN_BRANCH" ]; then
  git push origin "$MAIN_BRANCH" || fail "push of $MAIN_BRANCH failed"
  echo "git-sync-main: pushed $MAIN_BRANCH ($(git rev-parse --short HEAD))"
  exit 0
fi

# --- feature branch: push it, then fast-forward main ------------------------
git push -u origin "$branch" || fail "push of $branch failed"

if ! git rev-parse --verify "$MAIN_BRANCH" >/dev/null 2>&1; then
  git branch "$MAIN_BRANCH" HEAD || fail "could not create $MAIN_BRANCH"
  git push origin "$MAIN_BRANCH" || fail "push of $MAIN_BRANCH failed"
  echo "git-sync-main: created and pushed $MAIN_BRANCH from $branch"
  exit 0
fi

if ! git merge-base --is-ancestor "$MAIN_BRANCH" HEAD; then
  fail "$MAIN_BRANCH has commits that $branch does not — not a fast-forward.
       Rebase or merge $MAIN_BRANCH into $branch, then re-run. Nothing was pushed to $MAIN_BRANCH."
fi

# Is main checked out in some other worktree?
main_wt=$(git worktree list --porcelain \
  | awk -v b="refs/heads/$MAIN_BRANCH" '
      /^worktree /{wt=substr($0,10)}
      $0=="branch "b{print wt; exit}')

if [ -n "$main_wt" ] && [ "$main_wt" != "$root" ]; then
  [ -n "$(git -C "$main_wt" status --porcelain)" ] && \
    fail "$MAIN_BRANCH worktree at $main_wt is dirty — clean it, then re-run"
  git -C "$main_wt" merge --ff-only "$branch" || fail "fast-forward merge into $MAIN_BRANCH failed"
  git -C "$main_wt" push origin "$MAIN_BRANCH" || fail "push of $MAIN_BRANCH failed"
else
  git branch -f "$MAIN_BRANCH" HEAD || fail "could not fast-forward $MAIN_BRANCH"
  git push origin "$MAIN_BRANCH" || fail "push of $MAIN_BRANCH failed"
fi

echo "git-sync-main: $branch pushed; $MAIN_BRANCH fast-forwarded to $(git rev-parse --short HEAD) and pushed"
