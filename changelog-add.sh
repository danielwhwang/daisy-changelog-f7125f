#!/bin/bash
# changelog-add.sh — ONE command, ONE approval to publish a SHIPPED entry to the
# daisy-changelog. Appends a row to feature_log.tsv, then runs publish.sh
# (rebuild -> commit -> push, incident-sync-race safe).
#
# INTENTIONALLY NOT ALLOWLISTED: the single approval you see when this runs IS the
# content review for the public changelog page (the row text is right there in the
# command). The mechanical build/commit/push underneath is silent (publish.sh is a
# child process, not a separate approval). So: 2 prompts -> 1, and the 1 is the part
# that matters. (Decided with Daniel 2026-06-16; see reference_changelog_repo_workflow.)
#
# Usage:
#   changelog-add.sh "name" "what" "why" [location] [surface] [status]
# Defaults: location=""  surface="daisy"  status="Live"  date=today  approx=0
#   - name:     short headline
#   - what:     what shipped (can be long; tabs/newlines are auto-neutralized)
#   - why:      why it matters
#   - location: a memory slug or path (optional)
#   - surface:  daisy | infra | ...   (default daisy)
#   - status:   Live | ...            (default Live)

set -uo pipefail
REPO="$HOME/daisy-changelog"
cd "$REPO" || { echo "repo not found: $REPO"; exit 1; }

NAME="${1:-}"; WHAT="${2:-}"; WHY="${3:-}"
LOCATION="${4:-}"; SURFACE="${5:-daisy}"; STATUS="${6:-Live}"

if [ -z "$NAME" ] || [ -z "$WHAT" ] || [ -z "$WHY" ]; then
  echo "usage: changelog-add.sh \"name\" \"what\" \"why\" [location] [surface] [status]"
  exit 2
fi

DATE="$(date +%F)"

# Build + append the TSV row with python so a stray tab/newline in any field can't
# shift columns and corrupt the table.
python3 - "$DATE" "$NAME" "$SURFACE" "$STATUS" "$WHAT" "$WHY" "$LOCATION" <<'PY'
import sys
date, name, surface, status, what, why, location = sys.argv[1:8]
clean = lambda s: " ".join(s.replace("\t", " ").split("\n"))  # no tabs, no newlines
# Clean EVERY text field (not just what/why) — a stray tab anywhere shifts columns.
fields = [date, clean(name), clean(surface), clean(status),
          clean(what), clean(why), clean(location), "0"]
data = open("feature_log.tsv").read()
prefix = "" if (data == "" or data.endswith("\n")) else "\n"
with open("feature_log.tsv", "a") as f:
    f.write(prefix + "\t".join(fields) + "\n")
print("row added:", name)
PY

# Sanity check: the just-added row must have exactly 8 tab-separated columns.
COLS="$(tail -1 feature_log.tsv | awk -F'\t' '{print NF}')"
if [ "$COLS" != "8" ]; then
  echo "ERROR: appended row has $COLS columns (want 8); NOT publishing. Inspect feature_log.tsv tail."
  exit 1
fi

# Hand off to the existing one-command publisher (rebuild + commit + push, race-safe).
exec "$REPO/publish.sh" "Add: $NAME"
