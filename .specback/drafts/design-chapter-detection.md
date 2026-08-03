# Issue 設計: コード分析ベースの章構成自動カスタマイズ

## 1. 課題

Phase 1 でテンプレート選択後、ユーザーに「章を追加・削除・リネームしますか？」と**手動で質問**している。テンプレートは全章を含む包括的なリストだが、実際のプロジェクトには存在しない機能（認証がないのに認証章がある、ジョブがないのにジョブ章がある）があり、ユーザーは毎回手動で削除している。

**現状のユーザーフロー:**

```
テンプレート選択
  → 「どの章を追加・削除しますか？」（ユーザーが考える）
    → Phase 2: スケルトン生成
```

## 2. 提案

Phase 1 の Step 2（テンプレート選択）と Step 3（調整）の間に、**コード分析による章構成の自動カスタマイズ**を追加する。

**提案フロー:**

```
テンプレート選択
  → コード分析（grep / glob / file existence）
    → カスタマイズされた章構成の提示（自動推奨）
      → ユーザー確認・微調整
        → Phase 2: スケルトン生成
```

### 分析の種類

各章に対して、以下の検出パターンを組み合わせて判定する:

| パターン | 方法 | 例 |
|---------|------|----|
| **ファイル存在** | `glob` / `test -f` | `routes/` ディレクトリの有無 |
| **インポート検出** | `rg "^import \|^require \|^use "` | `requests`, `axios`, `devise` の有無 |
| **フレームワーク固有パターン** | 設定ファイル・マニフェスト | `composer.json` の `"require": {"laravel/passport"}` |
| **キーワード検出** | ソース内の特定キーワード | `session`, `AuthMiddleware`, `@login_required` |
| **設定ファイルパース** | JSON/YAML/TOML 読み取り | CI設定、Dockerfile、crontab |

### 判定結果の種類

| 結果 | 表示 | ユーザーアクション | フェーズ2以降の挙動 |
|------|------|-------------------|-------------------|
| **✅ 検出** | 緑チェック | そのまま | 含める（通常どおり） |
| **❌ 未検出** | 取り消し線 + 理由 | 復活可能 | スケルトン生成から除外 |
| **⚠️ 不明瞭** | 警告 + 理由 | 判断を委ねる | 含めるが `optional` フラグ付き |
| **➕ 追加候補** | 緑プラス + 検出根拠 | 確認して追加 | 自動追加（ユーザー確認後） |

## 3. 検出ルール定義（Webアプリテンプレートを例に）

各テンプレートの章ごとに検出ルールを定義する。以下のフォーマットで `references/template-catalog.md` に追記する:

```yaml
chapters:
  - id: ch-screens
    title: Screens and screen transitions
    detection:
      always_include: false  # true → 常に含める（概要・設計判断など）
      require_any:            # いずれか一つでもマッチすれば ✅
        - pattern: "glob:views/**"
        - pattern: "glob:templates/**"
        - pattern: "glob:pages/**"
        - pattern: "glob:app/views/**"
      exclude_if_no_match: true  # マッチなし → ❌ 未検出
      extra_chapter: false

  - id: ch-auth
    title: Authentication and authorisation
    detection:
      always_include: false
      require_any:
        - pattern: "rg:session|auth|login|logout|password_reset"
          file_glob: "*.py"
        - pattern: "rg:devise|passport|authlogic|omniauth"
          file_glob: "Gemfile|composer.json|package.json"
        - pattern: "glob:app/middleware/**auth*"
        - pattern: "glob:middleware/**auth*"
        - pattern: "rg:@login_required|@auth|Authenticate|AuthMiddleware"
      exclude_if_no_match: true
      extra_chapter: false
      note_when_excluded: "認証フレームワーク・認証関連コードが見つかりませんでした"

  - id: ch-external-interfaces
    title: External interfaces
    detection:
      always_include: false
      require_any:
        - pattern: "rg:requests\\.(get|post|put|delete)"
        - pattern: "rg:axios\\.(get|post|put|delete)"
        - pattern: "rg:import.*httpclient|import.*requests"
        - pattern: "rg:RestTemplate|WebClient\\."
        - pattern: "rg:curl_|HttpClient"
        - pattern: "glob:config/**/external*"
      exclude_if_no_match: true
      extra_chapter: false
      note_when_excluded: "HTTPクライアントライブラリの使用や外部連携設定が見つかりませんでした"

  - id: ch-operations
    title: Operations settings
    detection:
      always_include: false
      require_any:
        - pattern: "glob:Dockerfile"
        - pattern: "glob:docker-compose*"
        - pattern: "glob:deploy/**"
        - pattern: "glob:ci/**"
        - pattern: "glob:.github/workflows/**"
        - pattern: "glob:Jenkinsfile"
        - pattern: "glob:k8s/**"
        - pattern: "glob:helm/**"
      exclude_if_no_match: true
      extra_chapter: false
      note_when_excluded: "DockerfileやCI/CD設定が見つかりませんでした"

  - id: ch-data-model
    title: Data model
    detection:
      always_include: false
      require_any:
        - pattern: "glob:migrations/**"
        - pattern: "glob:db/migrate/**"
        - pattern: "glob:database/migrations/**"
        - pattern: "glob:prisma/**"
        - pattern: "glob:schema/**"
        - pattern: "glob:models/**"
        - pattern: "glob:app/models/**"
        - pattern: "glob:Entities/**"
      exclude_if_no_match: false  # 未検出でも含める（使用するDBがないプロジェクトは稀）
      optional: true              # ただしoptionalフラグ
      note_when_excluded: "データモデル定義（migration / model / schema）が見つかりません"

  - id: ch-routes
    title: Routes / endpoints
    detection:
      always_include: false
      require_any:
        - pattern: "glob:routes/**"
        - pattern: "glob:config/routes*"
        - pattern: "glob:urls.py"
        - pattern: "glob:app/**/urls.py"
        - pattern: "glob:router/**"
        - pattern: "glob:routes.rb"
      exclude_if_no_match: true
      extra_chapter: false
      note_when_excluded: "ルーティング定義ファイルが見つかりませんでした"
```

### 追加検出（extra_chapter）

特定のパターンがマッチした場合に、標準テンプレートにない章を自動追加する:

```yaml
extra_chapters:
  - id: ch-background-jobs
    title: Background jobs
    detection:
      require_any:
        - pattern: "rg:sidekiq|resque|delayed_job|active_job|good_job"
          file_glob: "Gemfile"
        - pattern: "rg:celery|dramatiq|huey|rq|apscheduler"
          file_glob: "requirements.txt|pyproject.toml"
        - pattern: "rg:@Celery\\(|cron_job|BackgroundJob"
        - pattern: "glob:app/jobs/**"
        - pattern: "glob:app/workers/**"
        - pattern: "glob:jobs/**"
        - pattern: "glob:workers/**"
    insert_after: ch-external-interfaces
    note_when_detected: "バックグラウンドジョブフレームワーク（Sidekiq/Celery等）を検出しました → 自動追加"

  - id: ch-caching
    title: Caching strategy
    detection:
      require_any:
        - pattern: "rg:redis|memcache|dalli"
          file_glob: "Gemfile|requirements.txt|pyproject.toml|composer.json|package.json"
        - pattern: "rg:cache_store|cache|Cache::"
        - pattern: "glob:config/**/cache*"
    insert_after: ch-data-model
    note_when_detected: "キャッシュ関連の設定やライブラリを検出しました → 追加候補"
```

## 4. 全9テンプレートの検出ルール概要

完全なルール定義は Issue 実装時に各テンプレートの frontmatter として記述する。ここでは概要のみ:

| テンプレート | 常時含める章 | 状況依存の章 | 自動追加候補 |
|:----------|:-----------|:-----------|:-----------|
| **web-app** | Overview, Feature specs, Architecture, Design decisions, Known constraints | Screens, Routes, Auth, External interfaces, Operations, Data model | Background jobs, Caching |
| **api-service** | Overview, Feature specs, Architecture, Design decisions, Known constraints | Endpoint catalogue, Request/response, Data model, Auth, Rate limiting, Versioning, SLA, Operations | SDK/client libraries, Webhook support |
| **batch-system** | Overview, Feature specs, Architecture, Design decisions, Known constraints | Job catalogue, Triggers, Data flow, Data model, Forms/Reports, Error handling, Recovery, Operations calendar, Monitoring | External interfaces |
| **library-sdk** | Overview, Feature specs, Module architecture, Design decisions, Known constraints | Installation, Public API catalogue, Usage examples, Configuration, Compatibility, Extension points, Migration guide, Internal structure | —（ほぼ全て常時） |
| **cli-tool** | Overview, Feature specs, Architecture, Design decisions, Known constraints | Installation, Command reference, Arguments, Configuration, Usage examples, Output formats, Exit codes, Shell completion, Extension points | — |
| **infrastructure** | Overview, Feature specs, Design decisions, Known constraints | Resource inventory, Network topology, Deployment pipeline, Configuration, Monitoring, DR/Backup, Cost | Compliance/audit |
| **mobile-app** | Overview, Feature specs, Module architecture, Design decisions, Known constraints | Screen list, State management, Data persistence, Platform API, Push notifications, Networking, Build/Deploy | — |
| **desktop-app** | Overview, Feature specs, Module architecture, Design decisions, Known constraints | Window management, UI components, Platform integration, State persistence, Auto-update, Networking, Keyboard shortcuts, Build/Deploy | — |
| **event-driven** | Overview, Feature specs, Module architecture, Design decisions, Known constraints | Event catalogue, Producers, Consumers, Serialization, Delivery guarantees, Partitioning, Error handling, Monitoring | Schema registry integration |

**常時含める章の原則:**
- **Overview**（第1章）: プロジェクト内容に関わらず必要
- **Feature specifications**（第2章）: コードから抽出可能な機能一覧 — 空でも章自体は必要
- **Architecture overview / Module architecture**: コードベースの構造理解に必須
- **Design decisions**: コードから推論した設計判断を記録 — 内容が少なくても章として存在すべき
- **Known constraints**: 予約ファイルと同様、常に存在すべき

## 5. 影響範囲

| # | ファイル | 変更内容 |
|---|---------|---------|
| 1 | `references/template-catalog.md` | 各テンプレートの章ごとに `detection_rules` セクションを追加 |
| 2 | `phase-1-recon.md` | Step 2（テンプレート選択）と Step 3（調整）の間に **「コード分析による章構成カスタマイズ」** ステップを追加 |
| 3 | `templates/*.md`（全9ファイル） | frontmatter に `detection:` セクションを追加 |
| 4 | `agents/chapter-investigator.md` | 検出結果（`excluded_chapters`）を WBS 作成時に参照する指示を追加 |
| 5 | `phase-2-wbs.md` | 除外された章をスキップするロジックを追加。`wbs.json` に除外理由を含める |
| 6 | `phase-4-verify.md` | 除外された章に対する coverage-check の挙動（スキップ）を定義 |
| 7 | `goal.schema.json` | カスタマイズ結果を保持する `customized_chapters[]` フィールドを追加（各エントリ: `chapter_id`, `title`, `status: included/excluded/auto_added`, `detection_note`, `detection_confidence`） |
| 8 | `state.json` スキーマ | Phase 1 のサブステップとして `phase_1_step: "selecting_template" | "analyzing_chapters" | "presenting_chapters"` を追加（resume時対応） |

## 6. 実装手順

1. **テンプレート frontmatter に検出パターンを追加**: まず web-app をパイロットとして実装し、テスト
2. **Phase 1 recon.md に分析ステップを追加**: テンプレート選択後 → コード分析 → カスタマイズ結果提示
3. **goal.schema.json に customized_chapters フィールド追加**: スキーマバリデーション通過確認
4. **Phase 2 wbs.md に除外章スキップロジック追加**: `wbs.json.chapters` に customized_chapters を反映
5. **Phase 4 verify.md に除外章スキップルール追加**: coverage-check で除外章がカウントされないように
6. **残り8テンプレートに検出パターンを展開**: api-service, batch-system, library-sdk, cli-tool, infrastructure, mobile-app, desktop-app, event-driven
7. **tests/ に統合テスト追加**: ダミープロジェクトに対して検出が正しく動作することを確認
8. **PR → merge + self-documentation**

## 6.5 コード量に応じた章の統合・分割（granularity adjustment）

削除・追加だけでなく、プロジェクトのコード量に応じて**章の粒度**を調整する。

### 統合（merge）: コードが少ない場合

Small project（total_lines < 2000 程度）では、関連する複数の章を一章にまとめる。

| 条件 | 統合元 | 統合先 |
|:----|:------|:-------|
| 画面数 <= 3 AND ルート定義 <= 10 | Screens + Routes | 「Webインターフェース」一章に |
| auth関連ファイル < 3 AND 認証ロジックが単純 | Authの章全体 | Operations の一部として内包 |
| 外部連携箇所 < 2 | External interfaces | Operations に内包 |
| job定義 < 3 | Background jobs | 他章に内包 or 削除 |

### 分割（split）: コードが多い場合

Large project（total_lines > 20000、または特定ドメインのファイル数が多い）では、一章を複数に分割する。

| 条件 | 分割元 | 分割先 |
|:----|:------|:-------|
| Entity数 > 20 または modelファイル > 15 | Data model | 「Core entities」 + 「Analytics/Reporting」 |
| 外部連携箇所 > 5 | External interfaces | 「REST API連携」 + 「DB/Queue」 |
| エンドポイント数 > 50 | Endpoint catalogue | 「Public API」 + 「Internal API」 |
| ジョブ定義 > 15 | Job catalogue | 「Online jobs」 + 「Batch jobs」 |

### 検出基準とデータソース

Phase 1 で収集した情報を再利用する:

| メトリクス | 取得方法 | 利用箇所 |
|:---------|:--------|:--------|
| `total_files`, `total_lines` | レコネッサンス（既存） | 全体の規模判定 |
| 画面数 | `glob views/** templates/** pages/**` → ファイル数 | Screens統合判断 |
| ルート定義数 | `rg "^get\|^post\|^put\|^delete\|^resource\|^resources"` routes/ | Routes統合判断 |
| Entity数 | `glob models/** entities/**` → ファイル数 | Data model分割判断 |
| エンドポイント数 | `rg "@\\(get\|@\\(post\|@RequestMapping\|router\\.(get\|post)"` | Endpoint分割判断 |
| authファイル数 | `rg "auth\|login\|register\|session" --count` + 認証FW | Auth統合判断 |
| 外部連携数 | `rg "requests\\.get\|axios\|RestTemplate" --count` | External IF分割判断 |

### depth_mode との関係

```
depth_mode = comprehensive + 章構成の粒度調整:
  コード少量 → 章を統合（comprehensive だけど細かすぎない）
  コード適量 → 既定のテンプレート（通常どおり）
  コード多量 → 章を分割（comprehensive でかつ十分な粒度）

depth_mode = outline:
  固定テーブルファースト構成のため統合・分割は適用しない
```

### 実装上の注意

- **統合後の章名**: 統合先の章名は説明的に（`Ch5+6: Web interface (screens & routes)`）
- **分割後の numbering**: 親の番号を継承（`Ch7: Data model (core entities)`, `Ch8: Data model (analytics)`）
- **reader_order との整合**: 統合・分割後の章リストで reader_order を再計算
- **ユーザーの選択権**: 統合・分割の提案はユーザーが上書き可能にする

## 7. 注意点・制約

### 過剰除去の防止
- 「認証がない」=「認証章を除外」は合理的だが、プロジェクトのライフサイクルを考慮する（まだ認証が実装されていない段階かもしれない = それは別途 Issues に書くべき話）
- **除外するときは理由を明示し、ユーザーが簡単に復活できるようにする**
- **判定「不明瞭」の章は含めたまま `optional` フラグを付ける**（あとでユーザーが削除判断できる）

### reader_order との統合
- `reader_order` が章の並び替えを定義している（maintenance_developer / sme / delivery_customer / regulator）
- 除外された章は reader_order のリストからも除外し、番号を詰める
- `reader_order` が `null`（デフォルト順）の場合はテンプレートの自然順を使用

### outline モードとの関係
- Outline モードは「テーブルファースト」の固定章構成（`01-modules-overview`, `02-entities`, ...）を使う
- これらの章は全ての言語で必ず存在する抽象化なので、**検出による除外は行わない**
- 検出カスタマイズは主に **comprehensive モード** 向け

### 複合プロジェクト（composite）の場合
- 複数のテンプレートを合成する場合、各テンプレートの検出結果をマージする
- 競合（両方のテンプレートが同じ章を提案）した場合は1つにまとめる
- composite 専用の共通章（System architecture, API contract, Data flow）は常時含める

### detect-drift.py に検出結果の更新機能
- ドリフト検出時（Phase 7）に新しいコードが追加され、以前は存在しなかった機能（認証、キュー etc.）が増えている場合、章構成の見直しを推奨する

### 既存の recon との重複注意
- Phase 1 レコネッサンスですでに「ファイルツリー・パッケージマネージャ・エントリポイント」を確認している
- 分析ステップではその情報を**再利用**する（ゼロから grep し直さない）
- `recon-report.md` に検出結果を追記し、Phase 2 で参照できるようにする

## 8. 質問バンク連携

検出結果が「不明瞭」だった章は Question Bank に投入:

```json
{
  "id": "Q-DETECT-001",
  "category": "architecture_decision",
  "question": "認証関連のコードが検出されませんでしたが、このプロジェクトに認証機能はありますか？（例: session, JWT, OAuth）",
  "context": "Phase 1 コード分析で認証フレームワーク・認証関連のコードパターンが検出されませんでした。",
  "severity": "important",
  "status": "open"
}
```

## 9. 結果の保存形式

`goal.json` に保存:

```json
{
  "customized_chapters": [
    {"chapter_id": "ch-overview", "title": "Overview", "status": "included", "detection_note": null, "detection_confidence": "always"},
    {"chapter_id": "ch-auth", "title": "Authentication and authorisation", "status": "excluded", "detection_note": "認証フレームワーク・認証関連コードが見つかりませんでした", "detection_confidence": "high"},
    {"chapter_id": "ch-background-jobs", "title": "Background jobs", "status": "auto_added", "detection_note": "Sidekiq設定検出", "detection_confidence": "high"},
    {"chapter_id": "ch-data-model", "title": "Data model", "status": "included", "detection_note": "optional: データモデル定義未確認", "detection_confidence": "low"}
  ]
}
```

## 10. E2E イメージ

### 中規模プロジェクト（削除 + 追加）

```
Phase 1 レコネッサンス完了
→ Webアプリケーションテンプレートを推奨
→ ユーザーが承認
→ 📋 コード分析中...

  ✅ 第1章: 概要（常時）
  ✅ 第2章: 機能仕様（常時）
  ✅ 第3章: アーキテクチャ概要（常時）
  ✅ 第4章: クラス/モジュール設計（常時）
  ✅ 第5章: 画面一覧・遷移（app/views/ 検出）
  ✅ 第6章: ルーティング（config/routes.rb 検出）
  ❌ 第7章: データモデル（migration/models 未検出）
  ❌ 第8章: 認証・認可（認証FW未検出）
  ✅ 第9章: 外部インターフェース（HTTPクライアント使用検出）
  ✅ 第10章: 運用設定（Dockerfile 検出）
  ✅ 第11章: 設計判断（常時）
  ✅ 第12章: 既知の制約（常時）
  ➕ 第13章: バックグラウンドジョブ（Sidekiq検出 → 自動追加）

  除外された章: データモデル, 認証・認可
  自動追加された章: バックグラウンドジョブ

  この構成で進めますか？
  （はい / 章を手動調整する）
```

### 小規模プロジェクト（統合）

```
→ 📋 コード分析中...（total_lines: ~800, small project）

  ✅ 第1章: 概要（常時）
  ✅ 第2章: 機能仕様（常時）
  ✅ 第3章: アーキテクチャ概要（常時）
  🔗 第4章: Webインターフェース（画面3 + ルート8 → Screens+Routes統合）
  🔗 第5章: 運用設定（認証login/logoutのみ + Dockerfile + 外部IF1件 → 統合）
  ✅ 第6章: データモデル（models/ 検出）
  ✅ 第7章: 設計判断（常時）
  ✅ 第8章: 既知の制約（常時）

  統合された章: Screens+Routes → Webインターフェース, Auth+Ops+ExtIF → 運用設定
  （全12章 → 8章に）

  この構成で進めますか？
  （はい / 章を分割する / 手動調整する）
```

### 大規模プロジェクト（分割）

```
→ 📋 コード分析中...（total_lines: ~85000, large project）
  検出: エンドポイント120+, Entity数45, 外部連携8

  ✅ 第1章: 概要（常時）
  ✅ 第2章: 機能仕様（常時）
  ✅ 第3章: アーキテクチャ概要（常時）
  ✅ 第4章: クラス/モジュール設計（常時）
  ✅ 第5章: 画面一覧・遷移（views/ 検出, 画面12）
  ✅ 第6章: ルーティング（routes/ 検出, エンドポイント120+）
  🔀 第7章: データモデル（Entity数45）
      └ 第7-a: データモデル（Core entities, 30エンティティ）
      └ 第7-b: データモデル（Analytics/Reporting, 15エンティティ）
  ✅ 第8章: 認証・認可（認証FW検出）
  🔀 第9章: 外部インターフェース（外部連携8）
      └ 第9-a: REST API連携（5連携）
      └ 第9-b: メッセージキュー/DB（3連携）
  ✅ 第10章: 運用設定（Dockerfile + CI 検出）
  ➕ 第11章: バックグラウンドジョブ（Sidekiq検出 → 自動追加）
  ✅ 第12章: 設計判断（常時）
  ✅ 第13章: 既知の制約（常時）
  → 全13章（標準12章からData model + External IFを分割し、Jobsを追加）

  分割された章: Data model → Core + Analytics, External IF → REST + Queue
  自動追加された章: Background jobs

  この構成で進めますか？
  （はい / 章を統合する / 手動調整する）
```
