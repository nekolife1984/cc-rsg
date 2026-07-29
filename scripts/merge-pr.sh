#!/bin/sh
# scripts/merge-pr.sh — Merge a PR only if CI checks pass
# Usage: scripts/merge-pr.sh <PR-number>
#   or:  scripts/merge-pr.sh        (uses current branch's PR)

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

# Get all check runs for the latest commit on the PR
CHECKS=$(gh pr checks "$PR_NUMBER" 2>&1) || {
  echo "❌ Failed to fetch checks for PR #$PR_NUMBER"
  exit 1
}

# Count pass/fail
FAIL_COUNT=$(echo "$CHECKS" | grep -c "fail" || true)
PASS_COUNT=$(echo "$CHECKS" | grep -c "pass" || true)
PENDING_COUNT=$(echo "$CHECKS" | grep -c "pending" || true)

echo "   ✅ $PASS_COUNT passed | ❌ $FAIL_COUNT failed | ⏳ $PENDING_COUNT pending"

if [ "$FAIL_COUNT" -gt 0 ]; then
  echo ""
  echo "❌ CI checks are FAILING — merge blocked!"
  echo "$CHECKS" | while IFS= read -r line; do
    case "$line" in
      *fail*) echo "   ❌ $line" ;;
      *pass*) echo "   ✅ $line" ;;
      *pending*) echo "   ⏳ $line" ;;
    esac
  done
  exit 1
fi

if [ "$PENDING_COUNT" -gt 0 ]; then
  echo ""
  echo "⏳ CI checks still pending — waiting up to 120s..."
  gh pr checks "$PR_NUMBER" --watch 2>&1
  echo ""
  # Re-check after watch
  CHECKS=$(gh pr checks "$PR_NUMBER" 2>&1)
  FAIL_COUNT=$(echo "$CHECKS" | grep -c "fail" || true)
  if [ "$FAIL_COUNT" -gt 0 ]; then
    echo "❌ CI checks failed after waiting. Merge blocked."
    exit 1
  fi
fi

echo ""
echo "✅ All CI checks passed! Merging PR #$PR_NUMBER..."
gh pr merge "$PR_NUMBER" --squash --delete-branch
