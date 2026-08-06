#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# specback installer — interactive or CLI-driven skill installer
#
# Usage:
#   ./install.sh                                          interactive mode
#   ./install.sh --dry-run                                dry-run (interactive)
#   ./install.sh --agent claude,opencode --level user     non-interactive
#   ./install.sh --agent all --level both                 all agents, both levels
#   ./install.sh --agent copilot --level project --dry-run  dry-run with flags
#
# Environment variables (lower priority than CLI flags):
#   SPECBACK_AGENT=claude,opencode   SPECBACK_LEVEL=user
#
# Supports: Claude Code, Codex CLI, OpenCode, GitHub Copilot, Cursor, Other
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$SCRIPT_DIR/skills/specback"
SEARCH_SKILL_SRC="$SCRIPT_DIR/skills/specback-search"
SHARED_DIRS="scripts references schemas agents templates variants"

if [[ ! -d "$SKILL_SRC" ]]; then
  echo "Error: skills/specback/ not found alongside this script."
  echo "Run this script from the root of the specback repository."
  exit 1
fi

# ── Defaults ───────────────────────────────────────────────────────────
DRY_RUN=false
CLI_AGENT=""
CLI_LEVEL=""
INSTALL_DEPS=false

# ── Parse flags ────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --agent)
      if [[ -z "${2:-}" ]]; then echo "Error: --agent requires a value"; exit 1; fi
      CLI_AGENT="$2"
      shift 2
      ;;
    --install-deps)
      INSTALL_DEPS=true
      shift
      ;;
    --level)
      if [[ -z "${2:-}" ]]; then echo "Error: --level requires a value"; exit 1; fi
      case "$2" in
        user|project|both) CLI_LEVEL="$2" ;;
        *) echo "Error: --level must be 'user', 'project', or 'both'"; exit 1 ;;
      esac
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --dry-run           Print what would be done, no changes"
      echo "  --install-deps      Install optional Python dependencies (tree-sitter grammars)"
      echo "  --agent AGENTS      Comma-separated agent keys: claude,codex,opencode,copilot,cursor,other,all"
      echo "  --level LEVEL       Install level: user, project, both"
      echo "  --help, -h          Show this message"
      echo ""
      echo "Environment:"
      echo "  SPECBACK_AGENT=claude    (fallback when --agent not given)"
      echo "  SPECBACK_LEVEL=user      (fallback when --level not given)"
      echo ""
      echo "Examples:"
      echo "  $0"
      echo "  $0 --agent claude,opencode --level user"
      echo "  $0 --agent all --level both --dry-run"
      exit 0
      ;;
    *)
      echo "Error: Unknown option: $1"
      echo "Usage: $0 [--agent AGENTS] [--level LEVEL] [--dry-run]"
      exit 1
      ;;
  esac
done

# ── Resolve agent list ────────────────────────────────────────────────
populate_agents() {
  AGENTS=()
  AGENT_KEYS=()
  AGENTS+=("Claude Code");               AGENT_KEYS+=("claude")
  AGENTS+=("Codex CLI");                 AGENT_KEYS+=("codex")
  AGENTS+=("OpenCode");                  AGENT_KEYS+=("opencode")
  AGENTS+=("GitHub Copilot");            AGENT_KEYS+=("copilot")
  AGENTS+=("Cursor");                    AGENT_KEYS+=("cursor")
  AGENTS+=("Other (.agents/skills/)");   AGENT_KEYS+=("other")
}

populate_agents

# ── Resolve input source: CLI > env > interactive ────────────────────
RESOLVED_AGENT="${CLI_AGENT:-${SPECBACK_AGENT:-}}"
RESOLVED_LEVEL="${CLI_LEVEL:-${SPECBACK_LEVEL:-}}"

# ── Helper: validate agent key ───────────────────────────────────────
is_valid_agent_key() {
  local k="$1"
  for ak in "${AGENT_KEYS[@]}"; do
    [[ "$k" == "$ak" ]] && return 0
  done
  return 1
}

# ── Helper: install paths ─────────────────────────────────────────────
USER_PATHS() {
  local key="$1"
  case "$key" in
    claude)   echo "$HOME/.claude/skills/specback" ;;
    codex)    echo "$HOME/.codex/skills/specback" ;;
    opencode) echo "$HOME/.opencode/skills/specback" ;;
    copilot)  echo "$HOME/.copilot/skills/specback" ;;
    cursor)   echo "$HOME/.cursor/skills/specback" ;;
    other)    echo "$HOME/.agents/skills/specback" ;;
    *)        echo "" ;;
  esac
}

PROJ_PATHS() {
  local key="$1"
  case "$key" in
    claude)   echo ".claude/skills/specback" ;;
    codex)    echo ".codex/skills/specback" ;;
    opencode) echo ".opencode/skills/specback" ;;
    copilot)  echo ".github/skills/specback" ;;
    cursor)   echo ".cursor/skills/specback" ;;
    other)    echo ".agents/skills/specback" ;;
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
  # Copy shared assets (scripts/, references/, schemas/, agents/, templates/, variants/)
  for dir in $SHARED_DIRS; do
    if [[ -d "$SCRIPT_DIR/$dir" ]]; then
      cp -r "$SCRIPT_DIR/$dir" "$dest/"
    fi
  done
  echo "  ✅ $dest/ ($label)"

  # Install companion: specback-search
  local search_dest="${dest%specback}specback-search"
  if [[ -d "$SEARCH_SKILL_SRC" ]]; then
    mkdir -p "$search_dest"
    cp -r "$SEARCH_SKILL_SRC"/* "$search_dest/"
    echo "  ✅ $search_dest/ ($label, specback-search)"
  fi
}

# ── Optional dependency installer ──────────────────────────────────────
install_deps() {
  local req="$SCRIPT_DIR/scripts/requirements.txt"
  if [[ ! -f "$req" ]]; then
    echo "  ⚠️  requirements.txt not found at $req"
    return
  fi
  if $DRY_RUN; then
    echo "  ⏺  pip install -r $req"
    return
  fi
  echo ""
  echo "Installing optional Python dependencies (tree-sitter grammars)..."
  pip install -r "$req" 2>&1 | tail -3
  echo "  ✅ Optional dependencies installed"
}

# ── Main ──────────────────────────────────────────────────────────────
echo ""
echo "specback installer v0.2.0"
echo "======================="
echo ""

# ── Non-interactive mode ──────────────────────────────────────────────
if [[ -n "$RESOLVED_AGENT" ]]; then
  # Parse agent keys
  SELECTED_KEYS=()
  IFS=',' read -ra PARTS <<< "$RESOLVED_AGENT"
  for part in "${PARTS[@]}"; do
    part="$(echo "$part" | xargs)"  # trim
    if [[ "$part" == "all" ]]; then
      SELECTED_KEYS=( "${AGENT_KEYS[@]}" )
      break
    elif is_valid_agent_key "$part"; then
      SELECTED_KEYS+=("$part")
    else
      echo "Warning: unknown agent key '$part', skipping"
    fi
  done

  # Resolve level
  case "${RESOLVED_LEVEL:-both}" in
    project) INSTALL_USER=false; INSTALL_PROJ=true  ;;
    both)    INSTALL_USER=true;  INSTALL_PROJ=true  ;;
    *)       INSTALL_USER=true;  INSTALL_PROJ=false ;;
  esac

  if [[ ${#SELECTED_KEYS[@]} -eq 0 ]]; then
    echo "No valid agents selected. Use: claude, codex, opencode, copilot, cursor, other, all"
    exit 1
  fi

  echo "Installing specback to:"
  echo ""

  INSTALLED=0
  for key in "${SELECTED_KEYS[@]}"; do
    # Find the display name
    label="$key"
    for i in "${!AGENT_KEYS[@]}"; do
      if [[ "${AGENT_KEYS[$i]}" == "$key" ]]; then
        label="${AGENTS[$i]}"
        break
      fi
    done

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
    $INSTALL_DEPS && install_deps
    echo "Done. specback and specback-search are now installed."
  fi
  echo ""
  exit 0
fi

# ── Interactive mode (no CLI agent flags) ──────────────────────────────

# ── Select level ──────────────────────────────────────────────────────
INTERACTIVE_LEVEL="${RESOLVED_LEVEL:-}"
if [[ -z "$INTERACTIVE_LEVEL" ]]; then
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
else
  case "$INTERACTIVE_LEVEL" in
    project) INSTALL_USER=false; INSTALL_PROJ=true  ;;
    both)    INSTALL_USER=true;  INSTALL_PROJ=true  ;;
    *)       INSTALL_USER=true;  INSTALL_PROJ=false ;;
  esac
fi

# ── Select agents ─────────────────────────────────────────────────────
INTERACTIVE_AGENT="${RESOLVED_AGENT:-}"
if [[ -z "$INTERACTIVE_AGENT" ]]; then
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
else
  # CLI might have only passed --level, no --agent — handle comma list
  SELECTED_KEYS=()
  IFS=',' read -ra PARTS <<< "$INTERACTIVE_AGENT"
  for part in "${PARTS[@]}"; do
    part="$(echo "$part" | xargs)"
    if [[ "$part" == "all" ]]; then
      SELECTED_KEYS=( "${AGENT_KEYS[@]}" )
      break
    elif is_valid_agent_key "$part"; then
      SELECTED_KEYS+=("$part")
    fi
  done
  SELECTED_INDICES=()
  for key in "${SELECTED_KEYS[@]}"; do
    for i in "${!AGENT_KEYS[@]}"; do
      if [[ "${AGENT_KEYS[$i]}" == "$key" ]]; then
        SELECTED_INDICES+=("$i")
        break
      fi
    done
  done
fi

# ── Install ───────────────────────────────────────────────────────────
echo ""
echo "Installing specback to:"
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
  $INSTALL_DEPS && install_deps
  echo "Done. specback is now installed."
fi
echo ""
