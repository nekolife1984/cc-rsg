#!/bin/sh
# scripts/install-hooks.sh — Install git hooks for specback
set -e

echo "🔧 Installing specback git hooks..."

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

# Check gitleaks availability
if command -v gitleaks >/dev/null 2>&1; then
  echo "  ✅ gitleaks found — secret scanning enabled"
else
  echo ""
  echo "  ⚠️  gitleaks not found — secret scanning will be skipped"
  echo "     Install: brew install gitleaks"
fi

echo ""
echo "✅ Done. Hooks installed:"
echo "   - pre-commit : test coverage + gitleaks secret scan"
echo "   - pre-push   : block direct pushes to main"
