#!/bin/sh
# scripts/merge-pr.sh — Merge a PR only if CI checks pass
# Usage: scripts/merge-pr.sh <PR-number>
#   or:  scripts/merge-pr.sh        (uses current branch's PR)
#
# `gh pr checks` exit codes:
#   0  = all checks passed
#   8  = checks still pending
#   1  = at least one check failed, OR a real fetch error
# This script preserves gh's exit code so pending / fail / fetch-error are
# handled distinctly instead of treating everything as a fetch failure.

set -e

PR_NUMBER="${1:-}"

if [ -z "$PR_NUMBER" ]; then
  # Try to find PR for current branch
  BRANCH=$(git rev-parse --abbrev-ref HEAD)
  PR_NUMBER=$(gh pr list --head "$BRANCH" --json number --jq '.[0].number' 2>/dev/null || echo "")
  if [ -z "$PR_NUMBER" ]; then
    echo "❌ No PR number given and no open PR found for current branch ($BRANCH)."
    echo "Usage: scripts/merge-pr.sh <PR-number>"
    exit 1
  fi
  echo "🔍 Found PR #$PR_NUMBER for branch '$BRANCH'"
fi

echo "🔍 Checking CI status for PR #$PR_NUMBER..."

# Fetch checks as JSON with the `bucket` field (pass/fail/pending/skipping/cancel).
# Preserve gh's exit code so pending (8) is not confused with fetch failure (1).
CHECK_EXIT=0
CHECKS_JSON=$(gh pr checks "$PR_NUMBER" --json name,state,bucket 2>&1) || CHECK_EXIT=$?

# Count checks by bucket (JSON is compact, so grep is sufficient)
PASS_COUNT=$(printf '%s' "$CHECKS_JSON" | grep -o '"bucket":"pass"' | wc -l | tr -d ' ')
FAIL_COUNT=$(printf '%s' "$CHECKS_JSON" | grep -o '"bucket":"fail"' | wc -l | tr -d ' ')
PENDING_COUNT=$(printf '%s' "$CHECKS_JSON" | grep -o '"bucket":"pending"' | wc -l | tr -d ' ')

echo "   ✅ $PASS_COUNT passed | ❌ $FAIL_COUNT failed | ⏳ $PENDING_COUNT pending"

# Show checks in a readable list (with mark symbols)
show_checks() {
  printf '%s' "$1" | python3 -c '
import json, sys
marks = {"pass": "✅", "fail": "❌", "pending": "⏳"}
try:
    checks = json.load(sys.stdin)
except Exception:
    raise SystemExit(0)
for c in checks:
    print("   {} {} ({})".format(marks.get(c["bucket"], "·"), c["name"], c["state"]))
' 2>/dev/null || printf '%s\n' "$1"
}

# A non-zero exit that is NOT pending (8) and lists no checks is a real fetch error
if [ "$CHECK_EXIT" -ne 0 ] && [ "$CHECK_EXIT" -ne 8 ] && [ "$FAIL_COUNT" -eq 0 ] && [ "$PENDING_COUNT" -eq 0 ]; then
  echo "❌ Failed to fetch checks for PR #$PR_NUMBER"
  printf '%s\n' "$CHECKS_JSON"
  exit 1
fi

if [ "$FAIL_COUNT" -gt 0 ]; then
  echo ""
  echo "❌ CI checks are FAILING — merge blocked!"
  show_checks "$CHECKS_JSON"
  exit 1
fi

if [ "$PENDING_COUNT" -gt 0 ]; then
  echo ""
  echo "⏳ CI checks still pending — waiting for them to finish..."
  gh pr checks "$PR_NUMBER" --watch 2>&1 || true
  echo ""
  # Re-check after watch
  CHECKS_JSON=$(gh pr checks "$PR_NUMBER" --json name,state,bucket 2>&1) || true
  FAIL_COUNT=$(printf '%s' "$CHECKS_JSON" | grep -o '"bucket":"fail"' | wc -l | tr -d ' ')
  PENDING_COUNT=$(printf '%s' "$CHECKS_JSON" | grep -o '"bucket":"pending"' | wc -l | tr -d ' ')
  PASS_COUNT=$(printf '%s' "$CHECKS_JSON" | grep -o '"bucket":"pass"' | wc -l | tr -d ' ')
  echo "   ✅ $PASS_COUNT passed | ❌ $FAIL_COUNT failed | ⏳ $PENDING_COUNT pending"
  if [ "$FAIL_COUNT" -gt 0 ]; then
    echo "❌ CI checks failed after waiting. Merge blocked."
    show_checks "$CHECKS_JSON"
    exit 1
  fi
  if [ "$PENDING_COUNT" -gt 0 ]; then
    echo "❌ CI checks still pending after waiting. Merge blocked."
    show_checks "$CHECKS_JSON"
    exit 1
  fi
fi

echo ""
echo "✅ All CI checks passed! Merging PR #$PR_NUMBER..."
gh pr merge "$PR_NUMBER" --squash --delete-branch
