# コミット規約

## 概要

このプロジェクトは [Conventional Commits](https://www.conventionalcommits.org/ja/v1.0.0/) に従います。履歴の可読性維持、自動チェンジログ生成、変更内容の即時把握が目的です。

## プレフィックス

| プレフィックス | 用途 | 例 |
|--------------|------|----|
| `feat:` | 新機能・機能拡張 | `feat: add plantuml template` |
| `fix:` | バグ修正 | `fix: detect encoding in py files` |
| `chore:` | CI・メンテナンス・リファクタリング・依存関係 | `chore: update pytest to 8.x` |
| `docs:` | ドキュメントのみ（コード変更なし） | `docs: fix typo in branching-strategy` |
| `test:` | テストの追加・修正 | `test: add coverage for build-trace.py` |

迷ったら `chore:` を使ってください。機能追加でもバグ修正でもない変更はすべて `chore:` です。

## 1変更1コミット

1つのコミットは **1つの論理変更** を表します。本文に無関係な変更を複数列挙したくなったら、コミットを分割してください。

**良い例:**
```
feat: add Flask extraction guide to references

- Covers Blueprints, view functions, hooks, Jinja2 templates
- Includes Flask-WTF forms and Flask-SQLAlchemy models

Closes #42
```

**避けるべき例:**
```
feat: add Flask extraction guide and fix typos in README
```

2つの変更は無関係です。`fix typos in README` は別の `docs:` コミットにすべきです。

## メッセージ形式

```
<プレフィックス>: <短い説明> （#<Issue番号>）

<任意の本文 — 何をなぜ変更したかを箇条書きで>

<任意のフッター — Closes #N, refs #N>
```

### 件名（1行目）
- 英語で記述（日本語混在不可）
- プレフィックス後の最初の文字は大文字
- 末尾にピリオド不要
- 72文字以内
- Issue番号はPRマージタイトルで参照すれば十分（各コミットでは必須ではありません）

### 本文
- 複数項目は箇条書き（`- `）を使用
- **何を**ではなく**なぜ**を説明
- 関連ファイルや概念を適宜参照

### フッター
- `Closes #N` — マージ時に自動クローズ
- `refs #N` — Issueを参照（クローズしない）

## Squash Merge の約束

このプロジェクトは **squash merge** を使用するため、`main` に記録されるのはPRのタイトルと説明のみです。つまり：

- **PRタイトル** = コミットの件名 — conventional prefix 形式で記述
  `feat: add Flask extraction guide`
- **PR説明文** = コミットの本文
- ブランチ内の個々のコミットメッセージは作成者自身の参考用

**要するに：** PRタイトルを良い conventional commit メッセージにしてください。
