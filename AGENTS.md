# cc-rsg — Agent Guide

## Branching Strategy

GitHub Flow. Details:
- EN: [docs/en/01-branching-strategy.md](docs/en/01-branching-strategy.md)
- JA: [docs/ja/01-branching-strategy.md](docs/ja/01-branching-strategy.md)

## Key Files

| Purpose | Path |
|---------|------|
| Contributing guide | [CONTRIBUTING.md](CONTRIBUTING.md) |
| PR template | [.github/pull_request_template.md](.github/pull_request_template.md) |
| README (EN) | [README.md](README.md) |

## Git Hooks

| Hook | 役割 | ファイル |
|------|------|---------|
| **pre-commit** | 新規 `.py` 追加時に対応テストファイルの存在をチェック | `.githooks/pre-commit` |
| **pre-push** | main 直pushをブロック | `.githooks/pre-push` |

```bash
# 初回clone後は以下を実行
sh scripts/install-hooks.sh
```

## Rules

- **No direct commits to `main`** — always feature branch → PR → squash merge (enforced by pre-push hook)
- **New scripts must have tests** — pre-commit hook checks `tests/test_<name>.py` exists (enforced by pre-commit hook)
- **One logical change per branch** — conventional commit prefix required
- **CI gates** — `pytest tests/ -v` + `mypy` (when applicable) must pass on PR
- **Docs sync** — update both EN + JA docs when behaviors change

## Bypass (Emergency Only)

```bash
git commit --no-verify              # Skips pre-commit hook
git push --no-verify origin main    # Skips pre-push hook
```
