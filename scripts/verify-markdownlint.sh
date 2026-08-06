#!/bin/bash
# verify-markdownlint.sh — Run markdownlint-cli2 on generated spec files
#
# Usage:
#   bash verify-markdownlint.sh --specback-dir .specback
#
# Options:
#   --specback-dir DIR   Specback state directory (default: .specback)
#   --target-dir DIR     Target directory with spec files (default: <specback-dir>/drafts)
#   --config FILE        Path to markdownlint config (default: references/markdownlint-config.yaml)
#   --help               Show this help
#
# Exit codes:
#   0 — All checks passed
#   1 — Markdownlint violations found
#   2 — Config file not found

set -euo pipefail

SPECBACK_DIR=".specback"
TARGET_DIR=""
CONFIG_FILE=""
SKILL_DIR=""

# Locate the skill directory (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --specback-dir)
      SPECBACK_DIR="$2"
      shift 2
      ;;
    --target-dir)
      TARGET_DIR="$2"
      shift 2
      ;;
    --config)
      CONFIG_FILE="$2"
      shift 2
      ;;
    --help)
      head -20 "$0"
      exit 0
      ;;
    *)
      echo "ERROR: Unknown option: $1" >&2
      echo "Usage: bash verify-markdownlint.sh --specback-dir .specback" >&2
      exit 2
      ;;
  esac
done

# Resolve target directory
if [[ -z "$TARGET_DIR" ]]; then
  TARGET_DIR="$SPECBACK_DIR/drafts"
fi

# Resolve config file
if [[ -z "$CONFIG_FILE" ]]; then
  CONFIG_FILE="$SKILL_DIR/references/markdownlint-config.yaml"
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "ERROR: Config file not found: $CONFIG_FILE" >&2
  exit 2
fi

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "WARNING: Target directory does not exist: $TARGET_DIR (skipping markdownlint check)" >&2
  exit 0
fi

echo "verify-markdownlint.sh: checking $TARGET_DIR/*.md with $CONFIG_FILE"

# Run markdownlint-cli2 via npx
# --yes: auto-download if not cached
npx --yes markdownlint-cli2 \
  --config "$CONFIG_FILE" \
  "$TARGET_DIR/*.md"

EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 ]]; then
  echo "verify-markdownlint.sh: ✅ All markdown checks passed"
else
  echo "verify-markdownlint.sh: ❌ Markdown violations found (exit $EXIT_CODE)" >&2
fi

exit $EXIT_CODE
