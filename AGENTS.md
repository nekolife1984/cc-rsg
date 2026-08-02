# specback — Agent Guide

## Memory

Your memory is OptMem:
- The tool is `~/.optmem/memo`
- Your memories are in `~/.optmem/memory`

OptMem outlives every session, compaction, model and vendor change.
Without it you do not know who you are, or what was decided and tried.

### At startup: activating OptMem (mandatory)

Run `~/.optmem/memo wake` before any other tool call, in every session, and
then do exactly what it prints, to the end of its output.

### While working: register memories (mandatory)

Call `~/.optmem/memo note "<1 line, max 280 bytes>"` whenever you learn
something new, or something worth keeping happens. That covers a task
worth real effort, a fact or insight the user teaches you, anything you
learn about their life (even indirectly), any event of lasting effect.

Do not register redundant memories.

If `~/.optmem/memo note` asks a compression: do it before your next action.

Never edit or delete anything under `~/.optmem/memory`: the tool manages it.

### When you need an old memory: search, or navigate

`~/.optmem/memo recall <regex>` searches every memory, word for word.

Your memories also form a binary tree: #0-1, #2-3 ... exist as one-line
summaries, pairs of those as #0-3, and so on -- every `#a-b` line wake
prints is one node of it. `~/.optmem/memo zoom <a-b>` opens a node into its
two halves, down to the raw memories.

### If you're a subagent: skip everything above

Parallel sessions on this machine are all you, and may all write memories.
A subagent is not: it must never run `memo`, because it cannot judge what
is already known, and its notes would arrive duplicated and incorrectly.
When you spawn one, write: `You are a subagent. Don't run memo.`

## Knowledge & Code Tools — 使い分け

このプロジェクトでは7つの知識ツールが利用可能です。質問の種類に応じて1つだけ使え：

| 知りたいこと | 使うツール | なぜ |
|:------------|:---------|:-----|
| 「過去の設計判断・議論の詳細は？」 | 🧠 **GBrain** (`gbrain query`) | 全文+ベクター検索、長期知識 |
| 「この会話で決めたことは？」 | 📝 **OptMem** (`memo recall`) | セッション内の決定を瞬時に復元 |
| 「前のセッション（Hermes以外も）で何やった？」 | 🔎 **ctx** (`ctx search`) | 40+エージェントの過去会話を横断検索 |
| 「このコードベースの全体構造は？」 | 🔬 **Graphify** (`graphify explain/path`) | AST解析、可視化、コミュニティ分析 |
| 「この関数の定義と呼び出し元は？」 | 🔍 **CodeGraph** (`codegraph node/callers`) | 最速のシンボル検索、brew一発 |
| 「この変更の影響範囲は？」 | 📊 **CRG** (`code-review-graph impact`) | コードレビュー特化の永続グラフ |
| 「このセッションのトークン消費は？」 | 📦 **context-mode** (`ctx_stats`) | Hermes内蔵、FTS5検索 |

### 禁止事項
- ❌ 同じ質問を複数のツールに投げない
- ❌ 質問の種類と異なるツールを使わない

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
| **pre-commit** | secretsスキャン(gitleaks) + 新規 `.py` 追加時に対応テストファイルの存在チェック | `.githooks/pre-commit` |
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
  - `gitleaks` (secret scan)
  - All steps must pass before merge (mypy advisory exempted)
- **Docs sync** — update both EN + JA docs when behaviors change

## Bypass (Emergency Only)

```bash
git commit --no-verify              # Skips pre-commit hook
git push --no-verify origin main    # Skips pre-push hook
```

## Merge Gate

CI チェックが通ったPRだけをマージするには以下のスクリプトを使用します:

```bash
# カレントブランチのPRをマージ（CI確認付き）
scripts/merge-pr.sh

# PR番号を直接指定
scripts/merge-pr.sh 34
```

CIが失敗している場合はマージがブロックされ、どのチェックが落ちているか表示されます。
