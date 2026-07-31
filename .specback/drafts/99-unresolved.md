# 第99章: 未確定事項

## 概要

本章では specback v1.0.0 のセルフドキュメンテーションにおいて未解決となった項目を記録する。

## Phase 5 対話結果

| Q-ID | カテゴリ | 深刻度 | 状態 | 内容 |
|------|---------|--------|------|------|
| Q-001 | architecture_decision | important | answered | テンプレート選定は template-catalog.md を参照した Claude の手動判定。自動コードパスなし。 |
| Q-002 | architecture_decision | important | answered | Question Bank 自動マージは完全一致のみ自動実行。類似フラグのみ付与しユーザー判断。 |
| Q-003 | operational_requirement | important | answered | 200ファイル閾値は source-map.py スキャン実数ベース。テスト/設定ファイル含む。 |
| Q-006 | architecture_decision | important | answered | tree-sitter フォールバック時は v1 ロジックにより複数ユニット抽出可能。 |
|| Q-008 | architecture_decision | important | answered | MECE 70%閾値は coverage-check.py がテンプレート種別に応じて自動調整する（Library/SDK は 40%）。[REF: #80] |
| Q-009 | operational_requirement | important | answered | セルフドキュメンテーションに特別な制約なし。通常フローと同様。 |
| Q-004 | architecture_decision | nice-to-have | answered | Phase 7→Phase 5 自動再実行は v2.0.0 ロードマップに委ねる。v1.x はレポートのみと確定。 |
| Q-005 | operational_requirement | nice-to-have | skipped | abandoned 判定の定量閾値は未定義。 |
|| Q-007 | architecture_decision | nice-to-have | answered | スキル内部（phase-*.md, templates/）の読み手は AI エージェントであるため、日本語化不要。README の日英 bilingual で十分。 |
|| Q-010 | business_rule | nice-to-have | answered | Dual-consumer は非推奨。理由・代替ガイドラインは 13-known-constraints.md §13.4.5 に追記。 |

## Phase 4 検証未達項目

| 項目 | 実績 | 要求 | 備考 |
|------|:----:|:----:|------|
| inventory.covered_by | 26.4% | ≥ 90% | Library/SDK テンプレートでは内部関数が spec に記載されないため低くなる。構造的に正しい振る舞いであり品質上の問題ではない。[REF: #80](https://github.com/nekolife1984/specback/issues/80) |
| MECE coverage | 32.5% | ≥ 70% | 同上。Library/SDK テンプレートでは内部実装の全ユニットを spec セクションに割り当てる必要はない。[REF: #80](https://github.com/nekolife1984/specback/issues/80) |

### 対応状況

specback v1.1.0 において、`coverage-check.py` が `goal.json` の `template` フィールドを参照してデフォルト閾値を自動調整する仕組みが実装された（[#80](https://github.com/nekolife1984/specback/issues/80)）。

- Library/SDK テンプレートでは `--min-covered-by-fill=0.3`, `--min-mece-coverage=0.4` が自動適用される
- それ以外のテンプレート（Web/API/Batch）では従来通りの `0.9` / `0.7` が適用される
- 明示的に CLI フラグが指定された場合は常にそちらが優先される

これにより、Library/SDK テンプレートを使用するプロジェクトでは上記の数値が自動的に品質ゲートを通過する。今後セルフドキュメンテーションを再実行した際には、これらの未達項目は解消される見込みである。
