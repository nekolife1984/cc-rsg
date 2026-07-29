#!/bin/sh
# scripts/install-hooks.sh — Install git hooks for cc-rsg
set -e

echo "🔧 Installing cc-rsg git hooks..."

HOOK_DIR="$(cd "$(dirname "$0")/.." && pwd)"

for hook in pre-commit pre-push; do
  src="$HOOK_DIR/.githooks/$hook"
  dst="$HOOK_DIR/.git/hooks/$hook"
  if [ -f "$src" ]; then
    # Backup existing hook if it's a real file (not our symlink)
    if [ -f "$dst" ] && [ ! -L "$dst" ]; then
      cp "$dst" "$dst.backup.$(date +%s)"
      echo "  ⚠  Backed up existing $hook to $hook.backup.*"
    fi
    ln -sf "../../.githooks/$hook" "$dst"
    chmod +x "$dst"
    echo "  ✅ Installed $hook hook"
  fi
done

echo "✅ Done. main branch protected; new scripts require tests."
