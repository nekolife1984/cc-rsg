# cc-rsg — Agent Guide

## Contributor Docs

| Guide | EN | JA |
|-------|----|----|
| Branching Strategy | [docs/en/01-branching-strategy.md](docs/en/01-branching-strategy.md) | [docs/ja/01-branching-strategy.md](docs/ja/01-branching-strategy.md) |
| Commit Conventions | [docs/en/02-commit-conventions.md](docs/en/02-commit-conventions.md) | [docs/ja/02-commit-conventions.md](docs/ja/02-commit-conventions.md) |
| PR Review Process | [docs/en/03-pr-review-process.md](docs/en/03-pr-review-process.md) | [docs/ja/03-pr-review-process.md](docs/ja/03-pr-review-process.md) |
| Release Process | [docs/en/04-release-process.md](docs/en/04-release-process.md) | [docs/ja/04-release-process.md](docs/ja/04-release-process.md) |

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
- **CI gates** — GitHub Actions (`.github/workflows/ci.yml`) runs on every PR:
  - `pytest` (scripts/ + source_map_v2/)
  - `mypy` (advisory, warnings displayed)
  - Smoke import check (source_map_v2 module + pytest collect)
  - All steps must pass before merge (mypy advisory exempted)
- **Docs sync** — update both EN + JA docs when behaviors change

## Bypass (Emergency Only)

```bash
git commit --no-verify              # Skips pre-commit hook
git push --no-verify origin main    # Skips pre-push hook
```
