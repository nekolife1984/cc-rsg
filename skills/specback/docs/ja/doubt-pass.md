# Doubt-pass: 敵対的レビュープロトコル

## 概要

doubt-pass サブフェーズ（Phase 4、ステップ7）は、[addyosmani/agent-skills doubt-driven-development](https://github.com/addyosmani/agent-skills/blob/main/skills/doubt-driven-development/SKILL.md) の原則を specback 検証パイプラインに適用します。生成されたドラフト仕様書の主要な主張に対して、ソースコードを**フレッシュコンテキスト**（初めて見るかのように）で再読し、解釈の正当性を検証します。

## コアワークフロー

```
CLAIM → EXTRACT → DOUBT → RECONCILE → STOP
```

| ステップ | 説明 |
|---------|------|
| **CLAIM** | ドラフトから1つの主張を特定（例: "`IssuesController#create` は成功時に201を返す"）。主張をソースチャプターと`<!-- REF: ... -->`アンカーとともに記録。 |
| **EXTRACT** | 主張を支えるコードファイルと行を特定。ドラフト内の既存の`<!-- REF: ... -->`のみを使用。 |
| **RECONCILE** | 誤り → 修正ノートとともに Phase 3 にループバック。不正確 → 文言調整＋`<!-- REF: ... -->`範囲の絞り込み。過小信頼 → マーカー昇格（🔴→🟡 or 🟡→🟢）。 |
| **STOP** | 信頼度スコア（1.0＝確実、0.0＝矛盾）を割り当て。`.specback/doubt-report.json` に記録。 |

## Doubt トリガールールセット

### トリガー条件（詳細）

| トリガー | 検出方法 | 優先度 | デフォルト |
|---------|---------|--------|---------|
| 🔴 **ASSUMED** | チャプター内で `rg "🔴"` 検索 | 最高（自動） | 常に含む |
| 🟡 **INFERRED 連鎖 ≥ 3** | チャプター内で INFERRED が3連続以上続き、間に VERIFIED がない | 高 | オン |
| 🟢 **VERIFIED だがコメント矛盾** | `<!-- REF: ... -->` ソース行と主張テキストを比較 — ソースコメントが "// Fallback only" なのに主張が "primary path" としている | 中 | オン |
| **クロスチャプター公理** | 同じ文が2チャプター以上に出現し、`<!-- REF: ... -->`引用がゼロ | 最高（自動） | 常に含む |

### 閾値チューニング

`goal.json.doubt` 内の以下のキーで動作を制御します：

| キー | 型 | デフォルト | 説明 |
|-----|----|---------|------|
| `enabled` | bool | `true` | doubt-pass 全体の有効/無効 |
| `scope` | string[] | `["assumed", "inferred", "verified", "axiom"]` | 処理するトリガータイプ |
| `inferred_chain_min` | int | `3` | INFERRED 連鎖トリガーの最小長 |
| `max_claims` | int | `10` | 1回の実行でレビューする最大主張数 |
| `fresh_context_strict` | bool | `true` | trueの場合、DOUBT ステップは実際にコードを再読しなければならない |
| `confidence_threshold` | float | `0.5` | このスコア未満の主張は自動的に Phase 3 にループバック |

### scope ショートハンド

| 値 | 展開されるトリガー |
|-------|-------------------|
| `"assumed_only"` | ASSUMED のみ（最速） |
| `"core"` | ASSUMED + クロスチャプター公理 |
| `"full"` | 全4トリガー（デフォルト） |

## フレッシュコンテキスト要件

DOUBT ステップではコードを**ゼロから**再読しなければなりません。以下は DOUBT 中に**禁止**です：

- Phase 3 調査ノート、チャプタードラフト、事前分析ログの参照
- 実際のファイルを再読せずに以前の読取りを記憶から呼び出すこと
- 以前のセッションのキャッシュされた観察結果の利用

許容されるフレッシュコンテキスト読取り：

```bash
# `<!-- REF: ... -->`が引用する正確なコード行を読む
read_file path/to/file.py --line 45-58

# エッジケース検出のための周辺コンテキストを読む
read_file path/to/file.py --line 40-63
```

読み取り出力は**新しい情報**として扱わなければなりません — コードを初めて見るかのように評価します。このフレッシュリードと仕様書の主張の間に矛盾があれば、それは真の doubt ヒットです。

## 信頼度スコアリング

各主張は DOUBT 後に信頼度スコアを受け取ります：

| スコア | 意味 | アクション |
|-------|------|---------|
| 1.0 | コードが主張と完全一致、エッジケースなし | ✅ 合格 — 主張をそのまま維持 |
| 0.8–0.9 | 軽微な不正確さ（🟡→🟢へのラベル昇格可能） | ✅ 合格 — 文言調整 |
| 0.5–0.7 | エッジケースまたは代替パスがカバーされていない | ⚠️ Phase 3 にループバック — 不足コンテキストを追加 |
| 0.1–0.4 | 主張が実質的に誤っている | 🔴 Phase 3 にループバック — 主張を修正 |
| 0.0 | 主張がコードと完全に矛盾 | 🔴 Phase 3 にループバック + `[NEEDS SME]` マーカーを追加 |

## Doubt-report.json スキーマ

出力ファイルは `.specback/doubt-report.json` に生成されます：

```json
{
  "$schema": "doubt-report.schema.json",
  "doubt-pass": true,
  "generated_at": "2026-08-02T12:00:00Z",
  "claims_reviewed": 5,
  "claims_passed": 3,
  "claims_needing_correction": 2,
  "confidence_avg": 0.72,
  "doubt_resolution_rate": 0.6,
  "failures": [
    {
      "chapter": "02-feature-specifications.md",
      "claim": "IssuesController#create returns 201 on success",
      "ref_source": "src/controllers/issues_controller.rb:45",
      "confidence": 0.3,
      "discrepancy": "Code raises 422 on validation failure; the claim only describes the happy path",
      "recommendation": "Split into success (201) and failure (422) sub-entries"
    }
  ]
}
```

フィールド：

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `doubt-pass` | bool | 全主張が合格または修正された場合に true |
| `generated_at` | string (ISO 8601) | タイムスタンプ |
| `claims_reviewed` | int | 処理された主張の総数 |
| `claims_passed` | int | スコアが `confidence_threshold` 以上の主張 |
| `claims_needing_correction` | int | 閾値未満の主張 |
| `confidence_avg` | float | 全主張の平均信頼度 |
| `doubt_resolution_rate` | float | `claims_passed / claims_reviewed` |
| `failures[]` | array | 各不合格主張の詳細 |

## Question Bank 統合

| Doubt 結果 | Question カテゴリ | 重要度 | 例 |
|-----------|-------------------|-------|-----|
| コードパスの欠落（バリデーション、エラー、代替） | `architecture_decision` | critical | "`create` は冪等性キーも処理するのか？" |
| コードの裏付けが全く見つからない | `spec_missing` | critical | "仕様書で '一括エクスポート' 機能が言及されているがコードパスが見つからない" |
| 再読後も不確か（明確な矛盾なし） | `architecture_decision` | important | "リトライロジックがフレームワーク標準かカスタムか — コードだけでは不明" |

## トラブルシューティング

| 症状 | 原因 | 対策 |
|------|------|------|
| Doubt-pass が多すぎる主張を処理する | `max_claims` が高すぎる | `goal.json.doubt.max_claims` を 5 または 3 に下げる |
| Doubt が何も見つからない（全合格） | `scope` が狭すぎる、またはコードが自明 | `scope` を `"full"` に拡張、または `"axiom"` を追加 |
| Phase 5 にまだ多すぎる質問がある | Doubt-pass のスコープが狭すぎる | `"verified"` と `"axiom"` トリガーを有効化 |
| Doubt が同じチャプターを繰り返しループバックする | チャプターまたは主張が根本的に曖昧 | `[NEEDS SME]` として記録して進む — 無限ループしない |
| 信頼度スコアが恣意的に見える | フレッシュコンテキストの強制が不足 | `fresh_context_strict: true` を設定し、DOUBT ステップが実際にファイルを再読していることを確認 |

## 他フェーズとの相互作用

| フェーズ | 相互作用 |
|---------|---------|
| **Phase 3（調査）** | Doubt-pass は調整ループバックを介して主張を Phase 3 に戻す可能性がある。ループバックは3回試行制限にカウントされる。 |
| **Phase 4（検証）— coverage-check** | Doubt-pass は coverage-check 合格後に実行される。それを置き換えるものではない。 |
| **Phase 5（対話）** | Doubt-pass はコード解釈の質問を解決し、それらが Phase 5 に到達しないようにする。真に SME が必要な質問は通常通り流れる。 |
| **Phase 6（納品）** | `doubt-report.json` はレビューの厳密性を示す裏付け証拠として最終仕様ディレクトリに含まれる。 |

---

*[addyosmani/agent-skills: doubt-driven-development](https://github.com/addyosmani/agent-skills/blob/main/skills/doubt-driven-development/SKILL.md) に触発されています*
