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
| Q-008 | architecture_decision | important | answered | MECE 70%閾値はテンプレート種別による調整機構なし。手動調整が必要。 |
| Q-009 | operational_requirement | important | answered | セルフドキュメンテーションに特別な制約なし。通常フローと同様。 |
| Q-004 | architecture_decision | nice-to-have | skipped | Phase 7→Phase 5 相互作用は未確認。phase-7-drift.md 未読のため。 |
| Q-005 | operational_requirement | nice-to-have | skipped | abandoned 判定の定量閾値は未定義。 |
| Q-007 | architecture_decision | nice-to-have | skipped | スキル本体の日本語化方針は未確定。 |
|| Q-010 | business_rule | nice-to-have | answered | Dual-consumer は非推奨。理由・代替ガイドラインは 09-known-constraints.md §9.4.5 に追記。 |

## Phase 4 検証未達項目

| 項目 | 実績 | 要求 | 備考 |
|------|:----:|:----:|------|
| inventory.covered_by | 26.4% | ≥ 90% | Library/SDK テンプレートでは内部関数が spec に記載されないため低くなる。構造的に正しい振る舞いであり品質上の問題ではない。[REF: #80](https://github.com/nekolife1984/specback/issues/80) |
| MECE coverage | 32.5% | ≥ 70% | 同上。Library/SDK テンプレートでは内部実装の全ユニットを spec セクションに割り当てる必要はない。[REF: #80](https://github.com/nekolife1984/specback/issues/80) |

### 対応方針

これらの検証未達は Library/SDK テンプレートの構造的制約によるものであり、spec の品質を上げるために無理に全関数を記載することはしない。代わりに `coverage-check.py` が `goal.json` のテンプレート種別を参照してデフォルト閾値を自動調整する仕組みを導入する（[#80](https://github.com/nekolife1984/specback/issues/80)）。
