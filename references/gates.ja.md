# Gates リファレンス

## 概要

`scripts/gates.py` は specback の検証処理を統一インターフェースで提供します。
すべての検証ゲートは以下のパターンに従います：

```python
report = some_gate(**kwargs)
if report.passed:
    print("✓ すべてのチェックが通過しました")
```

各ゲートは個別のチェック項目を含む `GateReport` を返すため、呼び出し側は
必要な粒度で pass/fail を判断できます。

## 利用可能なゲート

| ゲート | ラップするスクリプト | 説明 |
|--------|---------------------|------|
| `coverage_mece` | `coverage-check.py` | 章カバレッジ、REF数、MECE、質問バンク |
| `schema_valid` | `validate-schema.py` | JSON Schema による設定ファイル検証 |
| `traceability_full` | `build-trace.py` | trace.json 生成と構造的整合性 |
| `drift_detected` | `detect-drift.py` | ドリフト検出とレポートアーティファクト検証 |

## GateReport

```python
from gates import GateReport

report = GateReport(name="my_gate")
report.check("inventory exists", True, "42 件のアイテムを確認")
report.check("all REFs resolved", False, "3 つの孤立 REF")

report.passed    # → False（2つ目のチェックが失敗）
report.failures  # → [{"item": "all REFs resolved", "ok": False, "note": "..."}]
report.summary   # → "✗ FAIL my_gate: 1/2 checks passed"
report.to_dict() # → JSON シリアライズ可能な dict
```

## ゲートシグネチャ

### coverage_mece

```python
coverage_mece(
    specback_dir: str = ".specback",
    output_dir: str = ".",
    target_dir_for_required: str = ".specback/drafts",
    **extra,
) -> GateReport
```

`coverage-check.py --output-format json` を実行し、JSON出力から
チェック単位の詳細を抽出します。

### schema_valid

```python
schema_valid(
    data_file: str,
    schema_path: str,
) -> GateReport
```

`validate-schema.py` を実行し、人間可読な stderr から違反の詳細を
解析します。違反ごとに1つのチェック項目を返します。

### traceability_full

```python
traceability_full(
    specback_dir: str = ".specback",
    output_dir: str = ".",
) -> GateReport
```

`build-trace.py` を実行後、`trace.json` の構造的整合性
（by_source、by_section、MECE、schema_version）を検証します。

### drift_detected

```python
drift_detected(
    specback_dir: str = ".specback",
    output_dir: str = ".",
) -> GateReport
```

`detect-drift.py` を実行し、`drift-report.md` と `drift-report.json`
が生成されたことを確認します。

## CLI 使用法

```bash
python gates.py --gate coverage_mece --specback-dir .specback
python gates.py --gate schema_valid --schema schemas/goal.schema.json --data-file .specback/goal.json
python gates.py --gate traceability_full --specback-dir .specback
python gates.py --gate drift_detected --specback-dir .specback
```

終了コード: `0`（成功）または `1`（失敗）。

出力: デフォルトはJSON。`--text` で人間可読形式。

## Python API 使用法

```python
from gates import coverage_mece, schema_valid

# 複合チェック
report = coverage_mece(specback_dir=".specback", output_dir="specs")
if report.passed:
    proceed_to_next_phase()

# スキーマチェック
report = schema_valid(
    data_file=".specback/goal.json",
    schema_path="schemas/goal.schema.json",
)
```

## run_gates（バッチ実行）

```python
from gates import run_gates

reports = run_gates("coverage_mece", "traceability_full",
                     specback_dir=".specback")
all_passed = all(r.passed for r in reports)
```

## 設計原則

1. **ゲートは主張を検証し、予測はしない。** 各ゲートは処理*後に*実行され、
   実際に生成された成果物をチェックします。
2. **後方互換。** 既存のスクリプトはそのままスタンドアロンで使用可能。
   `gates.py` は subprocess 経由でラップするのみで、内部の再構築は不要。
3. **1ゲート、1レポート。** ゲートは例外を発生させず、失敗をレポートの
   チェック項目として記録します。
4. **ツール向けはJSON、人間向けはテキスト。** `to_dict()` が機械用、
   `summary` がエージェント用のインターフェースです。
5. **ADWへの自然な橋渡し。** このゲートインターフェースは SSSF の
   ADW ゲートと同じ形状であり、ADW移行（Issue #203/#204）を
   機械的な変更にします。
