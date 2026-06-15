#!/bin/bash
# publish.sh — one-command publish for the daisy-changelog repo
# (the shipped/feature log + the drawing board). Collapses the whole safe
# workflow into a single allowlisted command so updating the log doesn't cost
# a string of approval prompts.
#
# What it does: rebuild both pages from the TSVs -> commit -> push, and it
# auto-handles the Mini's hourly incident-sync race (which always conflicts on
# the GENERATED index.html — we regenerate the page, we NEVER hand-merge it).
#
# Usage:
#   1. Edit feature_log.tsv (shipped) and/or ideas.tsv (board).
#   2. /Users/hwangda/daisy-changelog/publish.sh "commit message"
#
# Source of truth for the repo conventions: reference_changelog_repo_workflow memory.

set -uo pipefail
cd "$HOME/daisy-changelog" || { echo "repo not found"; exit 1; }

MSG="${1:-Update changelog}"

rebuild() {
  python3 build.py       >/dev/null 2>&1 || { echo "build.py failed";       return 1; }
  python3 build_board.py >/dev/null 2>&1 || { echo "build_board.py failed"; return 1; }
}

stage() { git add feature_log.tsv ideas.tsv index.html board/index.html 2>/dev/null; }

# 1) Rebuild from current TSVs (captures your edits), then stage + commit.
rebuild || exit 1
stage
if git diff --cached --quiet; then
  echo "Nothing to commit — syncing only."
else
  git commit -q -m "$MSG" || { echo "commit failed"; exit 1; }
fi

# 2) Push, auto-resolving the incident-sync race (remote moves ahead; the
#    generated index.html conflicts). Only ever the generated pages conflict —
#    regenerate from the merged TSVs and continue; never hand-merge.
for attempt in 1 2 3 4; do
  if git push -q 2>/dev/null; then
    echo "pushed ✓  ($MSG)"
    exit 0
  fi
  echo "push rejected (try $attempt) — remote moved ahead; rebasing…"
  if git pull --rebase -q 2>/dev/null; then
    continue   # clean fast-forward/rebase, no conflict — retry push
  fi
  # Conflict: regenerate the pages from the (already-merged) TSVs, stage, continue.
  rebuild || { git rebase --abort 2>/dev/null; echo "rebuild during rebase failed — aborted"; exit 1; }
  stage
  if ! GIT_EDITOR=true git rebase --continue >/dev/null 2>&1; then
    git rebase --abort 2>/dev/null
    echo "rebase --continue failed — aborted; resolve by hand (git status)"
    exit 1
  fi
done

echo "still couldn't push after retries — check 'git status' by hand"
exit 1
