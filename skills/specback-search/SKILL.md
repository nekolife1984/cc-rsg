---
name: specback-search
description: specback search — find spec↔code cross-refs, coverage, drift.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task
metadata:
  short-description: >-
    Query specback-generated JSON artifacts (source-map, trace, inventory, questions, drift).
---

# specback search CLI

Query specback-generated structured data (`source-map.json`, `trace.json`, `inventory.json`, `questions.json`, `drift-report.json`) without manually reading raw JSON files.

This skill is a **companion to specback**. Install it alongside the main specback skill.

## コマンド

```bash
python scripts/build-search-index.py [query] [flags]
```

## フラグ一覧

| フラグ | 説明 | データソース |
|--------|------|-------------|
| `query` (positional) | sourceユニット名/パスの部分一致検索 | `source-map.json` |
| `--uncovered` | 未カバーのsourceユニット一覧 | `trace.json` |
| `--confidence 🟢/🟡/🔴` | 確度でフィルタ（Phase 2 — spec章のREFをパース） | spec章ファイル |
| `--questions [open\|all]` | 未解決質問（デフォルト: `open`） | `questions.json` |
| `--chapter <slug>` | 特定の章がカバーするユニット | `trace.json` |
| `--role <role>` | sourceユニットロールでフィルタ | `source-map.json` |
| `--drift` | 最新ドリフトレポート | `drift-report.json` |
| `--specback-dir <path>` | `.specback/` のパス（デフォルト: カレントの `.specback/`） | — |
| `--format text\|json` | 出力形式（デフォルト: `text`） | — |

## 使用例

```bash
# 名前/パス検索
python scripts/build-search-index.py "User"

# 未カバー
python scripts/build-search-index.py --uncovered

# 未カバーのモジュールだけ
python scripts/build-search-index.py --uncovered --role module

# 特定の章がカバーするユニット
python scripts/build-search-index.py --chapter 03-data-model

# ロールでフィルタ
python scripts/build-search-index.py --role endpoint

# 未解決質問
python scripts/build-search-index.py --questions open

# ドリフトレポート
python scripts/build-search-index.py --drift

# 複合フィルタ
python scripts/build-search-index.py "payment" --confidence 🔴
python scripts/build-search-index.py --chapter 02-feature-specs --drift

# JSON出力
python scripts/build-search-index.py "User" --format json

# 別ディレクトリ
python scripts/build-search-index.py --specback-dir /path/to/project/.specback
```

## 出力例（text）

```
🔍 「User」 — 2件

  SRC-0002 🟢 app/models/user.py:5-80
    → User (model, python)
    → 📘 03-data-model.md (§3.1 Entities)
    → INV-002: User model (orm_model)
```

## 出力フィールド

| フィールド | 意味 |
|-----------|------|
| `SRC-NNNN` | sourceユニットID |
| `🟢/🟡/🔴` | 確度（spec章の`[REF: ...]`から抽出） |
| `📘 Chapter` | カバーするspec章セクション |
| `INV-NNN` | インベントリ項目 |

## 注意点

- `.specback/` 必須（specback未実行だとエラー）
- `--questions` は `questions.json` がなくてもエラーにならない（「なし」と表示するだけ）
- `--drift` は `drift-report.json` が存在しない場合でもエラーにならない（detect-drift.pyの実行を促すメッセージを表示）
- `--role` は `source-map.json` のロール文字列に完全一致（小文字スネークケース）
- クエリは部分一致・大文字小文字区別なし
- 複数のフィルタを組み合わせるとAND条件になる
