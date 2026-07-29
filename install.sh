#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# cc-rsg installer — interactive skill installer for coding agents
#
# Usage:
#   ./install.sh              interactive mode
#   ./install.sh --dry-run    print what would be done, no changes
#
# Supports: Claude Code, Codex CLI, OpenCode, GitHub Copilot, Cursor, Other
# ---------------------------------------------------------------------------

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

# ── Resolve script directory ──────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$SCRIPT_DIR/skills/cc-rsg"

if [[ ! -d "$SKILL_SRC" ]]; then
  echo "Error: skills/cc-rsg/ not found alongside this script."
  echo "Run this script from the root of the cc-rsg repository."
  exit 1
fi

# ── Agent list ────────────────────────────────────────────────────────
AGENTS=()
AGENT_KEYS=()

populate_agents() {
  AGENTS+=("Claude Code")
  AGENT_KEYS+=("claude")
  AGENTS+=("Codex CLI")
  AGENT_KEYS+=("codex")
  AGENTS+=("OpenCode")
  AGENT_KEYS+=("opencode")
  AGENTS+=("GitHub Copilot")
  AGENT_KEYS+=("copilot")
  AGENTS+=("Cursor")
  AGENT_KEYS+=("cursor")
  AGENTS+=("Other (.agents/skills/)")
  AGENT_KEYS+=("other")
}

# ── Install paths ─────────────────────────────────────────────────────
USER_PATHS() {
  local key="$1"
  case "$key" in
    claude)   echo "$HOME/.claude/skills/cc-rsg" ;;
    codex)    echo "$HOME/.codex/skills/cc-rsg" ;;
    opencode) echo "$HOME/.opencode/skills/cc-rsg" ;;
    copilot)  echo "$HOME/.copilot/skills/cc-rsg" ;;
    cursor)   echo "$HOME/.cursor/skills/cc-rsg" ;;
    other)    echo "$HOME/.agents/skills/cc-rsg" ;;
    *)        echo "" ;;
  esac
}

PROJ_PATHS() {
  local key="$1"
  case "$key" in
    claude)   echo ".claude/skills/cc-rsg" ;;
    codex)    echo ".codex/skills/cc-rsg" ;;
    opencode) echo ".opencode/skills/cc-rsg" ;;
    copilot)  echo ".github/skills/cc-rsg" ;;
    cursor)   echo ".cursor/skills/cc-rsg" ;;
    other)    echo ".agents/skills/cc-rsg" ;;
    *)        echo "" ;;
  esac
}

# ── Install function ──────────────────────────────────────────────────
install_skill() {
  local dest="$1"
  local label="$2"

  if [[ -z "$dest" ]]; then
    return
  fi

  if $DRY_RUN; then
    echo "  ⏺  $dest/ ($label)"
    return
  fi

  mkdir -p "$dest"
  cp -r "$SKILL_SRC"/* "$dest/"
  echo "  ✅ $dest/ ($label)"
}

# ── Main ──────────────────────────────────────────────────────────────
echo ""
echo "cc-rsg installer v0.1.0"
echo "======================="
echo ""

populate_agents

# ── Select level ──────────────────────────────────────────────────────
echo "Select install level:"
echo "  1) User level (available for all projects)"
echo "  2) Project level (this directory only)"
echo "  3) Both"
read -rp "> " LEVEL_CHOICE
echo ""

case "$LEVEL_CHOICE" in
  2) INSTALL_USER=false; INSTALL_PROJ=true  ;;
  3) INSTALL_USER=true;  INSTALL_PROJ=true  ;;
  *) INSTALL_USER=true;  INSTALL_PROJ=false ;;
esac

# ── Select agents ─────────────────────────────────────────────────────
echo "Available agents:"
for i in "${!AGENTS[@]}"; do
  echo "  $((i+1))) ${AGENTS[$i]}"
done
echo ""
echo "Select agents to install (comma separated, e.g. 1,3,6):"
read -rp "> " AGENT_SEL
echo ""

SELECTED_INDICES=()
IFS=',' read -ra SEL_NUMS <<< "$AGENT_SEL"
for n in "${SEL_NUMS[@]}"; do
  n="$(echo "$n" | xargs)"  # trim
  idx=$((n - 1))
  if [[ $idx -ge 0 && $idx -lt ${#AGENTS[@]} ]]; then
    SELECTED_INDICES+=("$idx")
  fi
done

# ── Install ───────────────────────────────────────────────────────────
echo ""
echo "Installing cc-rsg to:"
echo ""

INSTALLED=0
for idx in "${SELECTED_INDICES[@]}"; do
  key="${AGENT_KEYS[$idx]}"
  label="${AGENTS[$idx]}"

  if $INSTALL_USER; then
    dest="$(USER_PATHS "$key")"
    install_skill "$dest" "$label"
    INSTALLED=$((INSTALLED + 1))
  fi

  if $INSTALL_PROJ; then
    dest="$(PROJ_PATHS "$key")"
    if [[ -n "$dest" ]]; then
      install_skill "$dest" "$label"
      INSTALLED=$((INSTALLED + 1))
    fi
  fi
done

echo ""
if $DRY_RUN; then
  echo "Dry-run complete. No changes were made."
else
  echo "Done. cc-rsg is now installed."
fi
echo ""
