# Contributing to cc-rsg

フィードバック・テンプレート追加要望・バグ報告は [GitHub Issues](https://github.com/nekolife1984/cc-rsg/issues) にて受け付けます。

特に以下の貢献を歓迎します：

- 新しい言語・フレームワークのインベントリ単位定義
- 新しいテンプレート（DWH、機械学習パイプライン、IaC、モバイルアプリ 等）
- 検証チェックリストの拡充
- 実プロジェクト適用例のレポート

## 開発の流れ

ブランチ戦略は **GitHub Flow** を採用しています。詳細は以下を参照してください：

- EN: [Branching Strategy](docs/en/01-branching-strategy.md)
- JA: [ブランチ戦略](docs/ja/01-branching-strategy.md)

### クイックスタート

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

### ルール

- **1変更1コミット** — コミットメッセージは `feat:` / `fix:` / `chore:` / `docs:` / `upstream:` のプレフィックスを使用
- **PR必須** — ソースコード・テスト・機能変更は必ずPR経由
- **Squash merge** — mainの履歴をまっすぐ保つ
- **CIゲート通過必須** — `pytest` + `mypy`（該当時）+ trace gate
- **ドキュメント同期** — EN + JA の両方を更新（ドキュメント変更時）
