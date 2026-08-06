# Gates Reference

## Overview

`scripts/gates.py` provides a unified verification interface for specback.
Every verification gate follows the same pattern:

```python
report = some_gate(**kwargs)
if report.passed:
    print("✓ All checks passed")
```

Each gate returns a `GateReport` with individual check items, so consumers
can decide pass/fail at whatever granularity they need.

## Available Gates

| Gate | Wraps | Description |
|------|-------|-------------|
| `coverage_mece` | `coverage-check.py` | Chapter coverage, REF counts, MECE, Question Bank |
| `schema_valid` | `validate-schema.py` | JSON Schema validation for config files |
| `traceability_full` | `build-trace.py` | Trace.json generation and structural integrity |
| `drift_detected` | `detect-drift.py` | Drift detection and report artifact verification |

## GateReport

```python
from gates import GateReport

report = GateReport(name="my_gate")
report.check("inventory exists", True, "found 42 items")
report.check("all REFs resolved", False, "3 orphaned REFs")

report.passed    # → False (second check failed)
report.failures  # → [{"item": "all REFs resolved", "ok": False, "note": "..."}]
report.summary   # → "✗ FAIL my_gate: 1/2 checks passed"
report.to_dict() # → JSON-serialisable dict
```

## Gate Signatures

### coverage_mece

```python
coverage_mece(
    specback_dir: str = ".specback",
    output_dir: str = ".",
    target_dir_for_required: str = ".specback/drafts",
    **extra,
) -> GateReport
```

Runs `coverage-check.py --output-format json` and extracts per-check
granularity from the JSON output.

### schema_valid

```python
schema_valid(
    data_file: str,
    schema_path: str,
) -> GateReport
```

Runs `validate-schema.py` and parses human-readable stderr for violation
details. Returns one check per violation.

### traceability_full

```python
traceability_full(
    specback_dir: str = ".specback",
    output_dir: str = ".",
) -> GateReport
```

Runs `build-trace.py` then validates `trace.json` for structural integrity
(by_source, by_section, MECE, schema_version).

### drift_detected

```python
drift_detected(
    specback_dir: str = ".specback",
    output_dir: str = ".",
) -> GateReport
```

Runs `detect-drift.py` and verifies that `drift-report.md` and
`drift-report.json` were generated.

## CLI Usage

```bash
python gates.py --gate coverage_mece --specback-dir .specback
python gates.py --gate schema_valid --schema schemas/goal.schema.json --data-file .specback/goal.json
python gates.py --gate traceability_full --specback-dir .specback
python gates.py --gate drift_detected --specback-dir .specback
```

Exit code: `0` (passed) or `1` (failed).

Output: JSON by default; use `--text` for human-readable format.

## Python API Usage

```python
from gates import coverage_mece, schema_valid

# Combined check
report = coverage_mece(specback_dir=".specback", output_dir="specs")
if report.passed:
    proceed_to_next_phase()

# Schema check
report = schema_valid(
    data_file=".specback/goal.json",
    schema_path="schemas/goal.schema.json",
)
```

## run_gates (batch)

```python
from gates import run_gates

reports = run_gates("coverage_mece", "traceability_full",
                     specback_dir=".specback")
all_passed = all(r.passed for r in reports)
```

## Design Principles

1. **Gates verify claims, never predictions.** Each gate runs *after* the
   fact and checks what was actually produced.
2. **Backward compatible.** Existing scripts remain standalone. `gates.py`
   wraps them via subprocess — no internal restructuring required.
3. **One gate, one report.** A gate never raises exceptions; it captures
   failures as check items in the report.
4. **JSON for tooling, text for humans.** `to_dict()` is the machine
   interface; `summary` is for the agent.
5. **Natural bridge to ADW.** This gate interface is the same shape SSSF
   uses for its ADW gates, making ADW migration (Issues #203/#204) a
   mechanical change.
