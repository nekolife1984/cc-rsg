# Issue #90 設計: 機能仕様書（機能一覧と各機能の処理定義）の生成対応

## 1. 課題

現在の specback テンプレートには「機能仕様書」に相当する独立した章がない。機能に関する情報は複数章に分散しており、一覧性に欠ける：

| 現状の分散先 | 含まれる機能情報 |
|---|---|
| 画面詳細（Screen details） | 画面に紐づく機能の断片 |
| ドメインルール（Domain rules） | ビジネスルールとしての制約 |
| エンドポイント仕様（Endpoint specs） | API としての機能 |
| ユースケース概要（Use case overview） | 高レベルの機能概要のみ |

**問題点**: 「このシステムにはどんな機能があるのか」を一覧できる章が存在しない。保守開発者が機能単位の影響範囲を把握するには複数章を横断する必要がある。

## 2. 提案

各テンプレートに **「機能仕様書 (Feature Specifications)」** 章を新設し、以下の 2 層構造で出力する：

### Layer 1: 機能カタログ表 (Feature Catalogue Table)

全機能を網羅した一覧表。1 行 = 1 機能。

| 列 | 内容 | 抽出元 |
|---|---|---|
| Feature ID | F-001, F-002, ... | 自動採番 |
| Feature name | 機能名（コードのクラス名・メソッド名から推測） | コード解析 |
| Category | 機能カテゴリ（認証 / データ管理 / レポート 等） | コード + 推測 |
| Related use case | Ch1 のユースケースへの相互参照 | Ch1 との照合 |
| Related items | 画面・エンドポイント・ジョブ・API への相互参照 | コード解析 |
| Auth required | 認証要否 | コード解析 |
| Priority | P0/P1/P2（コードから推測） | 推測 ⚠️ |
| Summary | 1 行サマリ（≤ 80 文字） | コード + 推測 |
| Confidence | 🟢 VERIFIED / 🟡 INFERRED / 🔴 ASSUMED | 読取判定 |

### Layer 2: 機能別処理定義 (Per-feature Processing Definitions)

各機能について、以下の構造化情報を記述：

```
### F-001: {機能名}

#### Overview
- この機能が何をするか
- どのようなビジネス価値を提供するか

#### Trigger
- 起動条件（ユーザー操作 / システムイベント / 外部呼出）

#### Pre-conditions
- 実行前に成立すべき条件

#### Main Flow
1. Step 1 [REF: path:line]
2. Step 2 [REF: path:line]
3. ...

#### Alternative Flows
- Alt-1: [条件] → [動作] [REF: path:line]

#### Error Handling
- エラー種別ごとの動作 [REF: path:line]

#### Post-conditions
- 実行後の状態

#### Related Business Rules
- → Ch? (ドメインルール章) への相互参照

#### Related Chapters
- → Ch? (画面詳細 / エンドポイント / データモデル) への相互参照

#### Confidence
🟢/🟡/🔴
```

## 3. テンプレート別の章構成

### Web App テンプレート (templates/web-app.md)

| 新番号 | 章タイトル | 変更 |
|---|---|---|
| 1 | Overview | （既存、変更なし） |
| **2** | **Feature Specifications** | **新設 🆕** |
| 3 | Architecture overview | 旧 2 → 繰り下げ |
| 4 | Screens and screen transitions | 旧 3 → 繰り下げ |
| 5 | Routes / endpoints | 旧 4 → 繰り下げ |
| 6 | Data model | 旧 5 → 繰り下げ |
| 7 | Authentication and authorisation | 旧 6 → 繰り下げ |
| 8 | External-system integration | 旧 7 → 繰り下げ |
| 9 | Operations settings | 旧 8 → 繰り下げ |
| 10 | Known constraints | 旧 9 → 繰り下げ |

### API Service テンプレート (templates/api-service.md)

| 新番号 | 章タイトル | 変更 |
|---|---|---|
| 1 | Overview | （既存、変更なし） |
| **2** | **Feature Specifications** | **新設 🆕** |
| 3 | Architecture overview | 旧 2 → 繰り下げ |
| 4 | Endpoint catalogue | 旧 3 → 繰り下げ |
| 5 | Request / response specifications | 旧 4 → 繰り下げ |
| 6 | Error codes / error responses | 旧 5 → 繰り下げ |
| 7 | Authentication | 旧 6 → 繰り下げ |
| 8 | Rate limiting / quotas | 旧 7 → 繰り下げ |
| 9 | Versioning | 旧 8 → 繰り下げ |
| 10 | SLA / performance requirements | 旧 9 → 繰り下げ |
| 11 | Operations settings | 旧 10 → 繰り下げ |
| 12 | Known constraints | 旧 11 → 繰り下げ |

### Batch System テンプレート (templates/batch-system.md)

| 新番号 | 章タイトル | 変更 |
|---|---|---|
| 1 | Overview | （既存、変更なし） |
| **2** | **Feature Specifications** | **新設 🆕** |
| 3 | Architecture overview | 旧 2 → 繰り下げ |
| 4 | Job catalogue | 旧 3 → 繰り下げ |
| 5 | Triggers and schedule | 旧 4 → 繰り下げ |
| 6 | Data flow | 旧 5 → 繰り下げ |
| 7 | Error handling and retry policy | 旧 6 → 繰り下げ |
| 8 | Recovery procedures | 旧 7 → 繰り下げ |
| 9 | Operations calendar | 旧 8 → 繰り下げ |
| 10 | Monitoring / alerts | 旧 9 → 繰り下げ |
| 11 | Known constraints | 旧 10 → 繰り下げ |

### Library / SDK テンプレート (templates/library-sdk.md)

| 新番号 | 章タイトル | 変更 |
|---|---|---|
| 1 | Overview | （既存、変更なし） |
| **2** | **Feature Specifications** | **新設 🆕** |
| 3 | Installation | 旧 2 → 繰り下げ |
| 4 | Public API catalogue | 旧 3 → 繰り下げ |
| 5 | Usage examples | 旧 4 → 繰り下げ |
| 6 | Configuration options | 旧 5 → 繰り下げ |
| 7 | Compatibility | 旧 6 → 繰り下げ |
| 8 | Extension points / plugin system | 旧 7 → 繰り下げ |
| 9 | Migration guide | 旧 8 → 繰り下げ |
| 10 | Internal structure (optional) | 旧 9 → 繰り下げ |
| 11 | Known constraints | 旧 10 → 繰り下げ |

## 4. コードからの抽出方針 (outline-tables.md 追記)

コードは機能単位ではなくレイヤー単位で構成されているため、以下の戦略で機能を推定・グループ化する：

### 4.1 コメントベースのグループ化 (信頼度: 🟢 または 🟡)
- `# Feature:`, `# @feature`, `/** @feature ... */` などのマーカーを検索
- 関数・クラスの docstring に機能名が明示されている場合

### 4.2 命名規則ベースのグループ化 (信頼度: 🟡)
- `*Service`, `*Handler`, `*Manager`, `*UseCase` クラス = 1 機能
- 例: `UserRegistrationService` → 機能「ユーザー登録」
- URL パスプレフィックスからの機能推定
  - `/api/users/*` → 機能「ユーザー管理」
  - `/api/payments/*` → 機能「決済」

### 4.3 画面・エンドポイント集約 (信頼度: 🟡)
- 同一画面に関連する全エンドポイント・モデル・ルールを「機能」としてグループ化
- Web App: 画面（SC-NNN）を単位として機能定義
- API Service: リソース（User / Issue / Project）単位で機能定義

### 4.4 ユースケースマッピング (信頼度: 🔴)
- Ch1 で定義されたユースケースを機能候補として使用
- 各ユースケースに該当するコードパスを特定できた場合のみ 🟢 に格上げ

### 4.5 抽出時の制約
- 機能の「目的」や「なぜ」はコードに書かれていないことが多い
- 🔴 ASSUMED の増加を許容し、Question Bank で管理
- 機能単位の完全自動抽出は不可能なため、**最低限の機能カタログ表 + SME 確認が必要な機能のリスト**を出力目標とする

## 5. 影響を受けるファイル一覧

| # | ファイル | 変更内容 |
|---|---|---|
| 1 | `templates/web-app.md` | Ch2 として機能仕様書を追加。既存章を繰り下げ |
| 2 | `templates/api-service.md` | 同上 |
| 3 | `templates/batch-system.md` | 同上 |
| 4 | `templates/library-sdk.md` | 同上 |
| 5 | `references/outline-tables.md` | 「機能グループ化パターン」セクションを追加 |
| 6 | `references/template-catalog.md` | 各テンプレートの章構成に新章を反映 |
| 7 | `agents/chapter-investigator.md` | 機能仕様書章の調査手順（STEP F/F2）を追加。処理定義の書き方を記載 |
| 8 | `phase-3-investigate.md` | 機能仕様書の調査に関する Note を追加（Layer 1/2/3 の分類） |
| 9 | `phase-4-verify.md` | 機能カバレッジの検証ルール追加（任意） |
| 10 | `SKILL.md` | Phase overview テーブルの章数更新（任意） |

## 6. 実装手順

1. `templates/` の 4 ファイルを修正（新章追加 + 繰り下げ）
2. `references/outline-tables.md` に機能グループ化セクションを追加
3. `references/template-catalog.md` の章構成を更新
4. `agents/chapter-investigator.md` に機能仕様書用の STEP 拡張を追加
5. `phase-3-investigate.md` に注意書きを追加
6. `phase-4-verify.md` に機能カバレッジ検証ルールを追加
7. PR 作成 → マージ

## 7. 注意点・制約

- **機能の特定は推測に依存する**: コードから 100% 正確な機能一覧を抽出することは理論上不可能。🔴 ASSUMED の割合が他の章より高くなることを許容する
- **Question Bank との連携**: 確定できない機能情報は `spec_missing` カテゴリの質問として蓄積 → Phase 5 で SME 確認
- **Phase 4 検証**: 機能カバレッジ率（全 INV のうち機能にマッピングされた割合）を表示するが、合格閾値は設けない（機能マッピングの網羅性はコード構造に依存するため）
- **既存 Issue #89 との関係**: #89（画面詳細の項目定義表化）で画面項目が構造化されると、機能仕様書との相互参照が容易になる。両者を同時に実装すると相乗効果が高い

## 8. 決定事項（Phase 0 スタイル）

**Question**: 「機能一覧」を独立した章として追加するか、既存章内にセクションとして追加するか？
**Answer**: **独立した章**。一覧性を最優先し、1 章で全機能を俯瞰できる設計とする。

**Question**: 章の配置は Overview の直後か、文書末尾か？
**Answer**: **Overview の直後（Ch2）**。読者が最初に「このシステムの機能全体像」を把握してから詳細に入る構成。

**Question**: 機能のグルーピング単位は？
**Answer**: **テンプレート種別に応じて可変**。
- Web App: 画面（SC-NNN）単位
- API Service: リソース（User / Issue / Payment 等）単位
- Batch System: ジョブグループ単位
- Library/SDK: 機能カテゴリ（解析・変換・出力等）単位
