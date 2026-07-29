# Contributing to cc-rsg

フィードバック・テンプレート追加要望・バグ報告は [GitHub Issues](https://github.com/nekolife1984/cc-rsg/issues) にて受け付けます。

特に以下の貢献を歓迎します：

- 新しい言語・フレームワークのインベントリ単位定義
- 新しいテンプレート（DWH、機械学習パイプライン、IaC、モバイルアプリ 等）
- 検証チェックリストの拡充
- 実プロジェクト適用例のレポート

## クイックスタート

```bash
# 1. main からブランチを作成
git checkout main
git pull origin main
git checkout -b feat/your-feature

# 2. 変更を加えてコミット
git add .
git commit -m "feat: add plantuml template"

# 3. PRを作成
git push origin feat/your-feature
# → GitHubでPRを作成
```

## 開発ガイド

| ガイド | 説明 |
|--------|------|
| [ブランチ戦略](docs/ja/01-branching-strategy.md) | GitHub Flow、ブランチ命名規則、上流同期 |
| [コミット規約](docs/ja/02-commit-conventions.md) | Conventional Commits、1変更1コミット、メッセージ形式 |
| [PRレビュープロセス](docs/ja/03-pr-review-process.md) | PRテンプレート、レビュアーチェックリスト、squash merge |
| [リリース手順](docs/ja/04-release-process.md) | バージョニング、CHANGELOG、Zenodo |

## ルール

- **1変更1コミット** — コミットメッセージは `feat:` / `fix:` / `chore:` / `docs:` / `upstream:` のプレフィックスを使用
- **PR必須** — ソースコード・テスト・機能変更は必ずPR経由
- **Squash merge** — mainの履歴をまっすぐ保つ
- **CIゲート通過必須** — GitHub Actions（`.github/workflows/ci.yml`）が PR 上で自動実行:
  - `pytest`（scripts/ および source_map_v2/）
  - `mypy`（アドバイザリ、警告表示）
  - Smoke import チェック（全スクリプトの import 検証）
- **ドキュメント同期** — EN + JA の両方を更新（ドキュメント変更時）

## 英語版

For English: see the [English README](README.md) and [docs/en/](docs/en/) directory.
