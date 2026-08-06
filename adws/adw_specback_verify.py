#!/usr/bin/env python3
"""ADW — Phase 4: Verify.

Code-only ADW (no agent calls). Runs all verification gates (coverage_mece,
schema_valid, traceability_full, drift_detected) against a specback output
directory and produces a VerifyOutput envelope.

Usage:
    uv run adws/adw_specback_verify.py --target /path/to/codebase
    uv run adws/adw_specback_verify.py --specback-dir .specback --output-dir specs
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from adws.adw_modules import session  # noqa: E402
from adws.adw_modules.utils import (  # noqa: E402
    add_common_args,
    resolve_specback_dir,
)
from scripts.data_types import VerifyOutput  # noqa: E402
from scripts.gates import (  # noqa: E402
    coverage_mece,
    drift_detected,
    schema_valid,
    traceability_full,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="specback ADW — Phase 4: Verify"
    )
    add_common_args(parser)
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory with spec content (default: .)",
    )
    parser.add_argument(
        "--gates",
        type=str,
        nargs="*",
        default=None,
        help="Specific gates to run (default: all)",
    )
    parser.add_argument(
        "--envelope-out",
        type=str,
        default=None,
        help="Path to write the VerifyOutput envelope JSON",
    )
    return parser


def _run_schema_valid_gate(specback_dir: Path) -> "GateReport":
    """Run schema_valid gate against all schemas in .specback.

    schema_valid takes (data_file, schema_path) instead of
    (specback_dir, output_dir), so special handling is needed.
    """
    import os
    from scripts.gates import GateReport, schema_valid

    combined = GateReport(name="schema_valid")
    schema_dir = _PROJECT_ROOT / "schemas"

    schema_map: list[tuple[str, str]] = [
        ("goal.json", os.fspath(schema_dir / "goal.schema.json")),
        ("state.json", os.fspath(schema_dir / "state.schema.json")),
    ]

    for data_name, schema_path in schema_map:
        data_file = specback_dir / data_name
        if not data_file.exists():
            combined.check(item=data_name, ok=True, note="File not found (skipped)")
            continue
        report = schema_valid(
            data_file=os.fspath(data_file),
            schema_path=schema_path,
        )
        for c in report.to_dict()["checks"]:
            combined.check(**c)

    return combined


def run_verify(
    specback_dir: Path,
    output_dir: Path,
    gate_names: list[str] | None = None,
) -> VerifyOutput:
    """Run verification gates and produce a VerifyOutput envelope.

    Args:
        specback_dir: Path to .specback directory.
        output_dir: Path to output directory with spec content.
        gate_names: List of gate names to run. None = run all.

    Returns:
        VerifyOutput envelope.
    """
    sb_dir = str(specback_dir)
    out_dir = str(output_dir)

    available_gates = {
        "coverage_mece": lambda: coverage_mece(
            specback_dir=sb_dir, output_dir=out_dir
        ),
        "schema_valid": lambda: _run_schema_valid_gate(
            specback_dir=specback_dir
        ),
        "traceability_full": lambda: traceability_full(
            specback_dir=sb_dir, output_dir=out_dir
        ),
        "drift_detected": lambda: drift_detected(
            specback_dir=sb_dir, output_dir=out_dir
        ),
    }

    names = gate_names or list(available_gates.keys())
    unknown = [n for n in names if n not in available_gates]
    if unknown:
        raise ValueError(f"Unknown gates: {unknown}. Available: {list(available_gates.keys())}")

    failures: list[str] = []
    chapter_metrics: list[dict] = []

    for name in names:
        gate_fn = available_gates[name]
        report = gate_fn()
        if not report.passed:
            check_list = report.to_dict()["checks"] if hasattr(report, "to_dict") else []
            failures.append(
                f"{name}: {len([c for c in check_list if not c.get('ok', False)])} check(s) failed"
            )
        chapter_metrics.append({
            "gate": name,
            "passed": report.passed,
            "checks": report.to_dict().get("checks", []),
        })

    return VerifyOutput(
        all_gates_passed=len(failures) == 0,
        failures=failures,
        chapter_metrics=chapter_metrics,
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    specback_dir = resolve_specback_dir(
        args.target, args.specback_dir
    )
    if not specback_dir.is_dir():
        print(f"Error: specback directory not found: {specback_dir}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir or ".").resolve()

    run = session.ensure(adw_id=args.adw_id)

    with run.phase(session.PhaseParams(
        name="verify", kind="code", owner="code",
        description="Run verification gates on spec output",
    )) as ph:
        envelope = run_verify(
            specback_dir=specback_dir,
            output_dir=output_dir,
            gate_names=args.gates,
        )
        ph.log(envelope=envelope.to_dict())

        if args.envelope_out:
            out_path = Path(args.envelope_out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(envelope.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        if not envelope.passed:
            for f in envelope.failures:
                print(f"  ❌ {f}")
            return run.finish(accepted=False)

        gate_count = len(args.gates) if args.gates else 4
        print(f"  ✅ All {gate_count} gate(s) passed")
        return run.finish(accepted=True)


if __name__ == "__main__":
    sys.exit(main())
