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

## Workflow

1. **Issue作成** — 作業内容をIssueに書く（日本語）
|2. **確認待ち** — 管理者がGoを出すまで待機
|3. **Go → 実装** — ブランチ作成 → 実装 → PR作成
|4. **確認待ち** — 管理者がOKを出すまで待機
5. **OK → マージ** — squash merge → ブランチ削除

## Git Hooks

main直pushをローカルで防ぐpre-push hookが `.githooks/pre-push` にあります。

```bash
# 初回clone後は以下を実行
sh scripts/install-hooks.sh
```

## Rules

- **No direct commits to `main`** — always feature branch → PR → squash merge (enforced by pre-push hook)
- **One logical change per branch** — conventional commit prefix required
- **CI gates** — `pytest` + `mypy` (when applicable) must pass on PR
- **Docs sync** — update both EN + JA docs when behaviors change

## Bypass (Emergency Only)

```bash
git push --no-verify origin main   # Skips pre-push hook
```
