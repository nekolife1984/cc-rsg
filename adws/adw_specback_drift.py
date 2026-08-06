#!/usr/bin/env python3
"""ADW — Phase 7: Drift Detection.

Code-only ADW (no agent calls). Detects spec drift by running detect-drift.py
and produces a DriftOutput envelope.

Also handles Phase 7b (REF Auto-Fix via fix-refs.py) and
Phase 7d (Config Refresh via source-map.py + build-trace.py).

Usage:
    uv run adws/adw_specback_drift.py --target /path/to/codebase
    uv run adws/adw_specback_drift.py --specback-dir .specback --mode git
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from adws.adw_modules import session  # noqa: E402
from adws.adw_modules.utils import (  # noqa: E402
    add_common_args,
    resolve_specback_dir,
)
from scripts.data_types import DriftOutput  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="specback ADW — Phase 7: Drift Detection"
    )
    add_common_args(parser)
    parser.add_argument(
        "--output-dir",
        type=str, default=None,
        help="Output directory (default: current dir)",
    )
    parser.add_argument(
        "--mode",
        type=str, default="auto",
        choices=["auto", "git", "hash"],
        help="Drift detection mode (default: auto)",
    )
    parser.add_argument(
        "--base",
        type=str, default=None,
        help="Git base ref for drift comparison (default: auto-detected)",
    )
    parser.add_argument(
        "--skip-fix-refs",
        action="store_true",
        help="Skip Phase 7b (REF Auto-Fix)",
    )
    parser.add_argument(
        "--skip-config-refresh",
        action="store_true",
        help="Skip Phase 7d (Config Refresh)",
    )
    parser.add_argument(
        "--envelope-out",
        type=str, default=None,
        help="Path to write the DriftOutput envelope JSON",
    )
    return parser


def _run_script(
    script_path: Path, args: list[str], timeout: int = 60,
) -> tuple[int, str, str]:
    """Run a Python script and return (returncode, stdout, stderr).

    Handles FileNotFoundError, TimeoutExpired, and other subprocess errors.
    """
    if not script_path.exists():
        return (-1, "", f"Script not found: {script_path}")
    cmd = [sys.executable, str(script_path)] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (result.returncode, result.stdout, result.stderr)
    except subprocess.TimeoutExpired as e:
        return (-1, "", f"Timed out after {timeout}s: {e}")
    except FileNotFoundError as e:
        return (-1, "", f"Python not found: {e}")
    except OSError as e:
        return (-1, "", f"OS error: {e}")


def run_drift(
    specback_dir: Path,
    output_dir: Path,
    mode: str = "auto",
    base: str | None = None,
    skip_fix_refs: bool = False,
    skip_config_refresh: bool = False,
) -> DriftOutput:
    """Execute drift detection and optional sub-phases.

    Args:
        specback_dir: Path to .specback directory.
        output_dir: Path to output directory.
        mode: Detection mode (auto, git, hash).
        base: Git base ref.
        skip_fix_refs: Skip Phase 7b.
        skip_config_refresh: Skip Phase 7d.

    Returns:
        DriftOutput envelope.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    sb_str = str(specback_dir)
    out_str = str(output_dir)

    # --- Phase 7: Drift Detection ---
    detect_script = _PROJECT_ROOT / "scripts" / "detect-drift.py"
    drift_args = [
        "--specback-dir", sb_str,
        "--output-dir", out_str,
        "--mode", mode,
        "--json",
    ]
    if base:
        drift_args.extend(["--base", base])

    rc, stdout, stderr = _run_script(detect_script, drift_args)
    if rc != 0:
        print(f"  ⚠️  detect-drift.py exit={rc}: {stderr[:200]}", file=sys.stderr)

    # Parse drift report
    report_path = output_dir / "drift-report.json"
    affected_chapters: list[str] = []
    if report_path.exists():
        try:
            report_data = json.loads(report_path.read_text(encoding="utf-8"))
            affected_chapters = report_data.get("affected_sections", [])
        except (json.JSONDecodeError, KeyError):
            pass

    print(f"  📡 Drift: {len(affected_chapters)} affected section(s) detected")

    # --- Phase 7b: REF Auto-Fix ---
    ref_issues_corrected = 0
    if not skip_fix_refs:
        fix_script = _PROJECT_ROOT / "scripts" / "fix-refs.py"
        rc2, stdout2, stderr2 = _run_script(fix_script, [
            "--specback-dir", sb_str,
            "--output-dir", out_str,
            "--apply",
            "--json",
        ])
        if rc2 != 0:
            print(f"  ⚠️  fix-refs.py exit={rc2}: {stderr2[:200]}", file=sys.stderr)
        else:
            # Parse JSON output for correction count
            try:
                fix_data = json.loads(stdout2)
                ref_issues_corrected = fix_data.get("corrections_applied", 0)
            except json.JSONDecodeError:
                pass
        print(f"  🔧 REF Auto-Fix: {ref_issues_corrected} issue(s) corrected")

    # --- Phase 7d: Config Refresh ---
    if not skip_config_refresh:
        source_map_script = _PROJECT_ROOT / "scripts" / "source-map.py"
        build_trace_script = _PROJECT_ROOT / "scripts" / "build-trace.py"

        if source_map_script.exists():
            rc3, _, stderr3 = _run_script(source_map_script, [
                "--target", str(specback_dir.parent),
                "--output", sb_str,
            ])
            if rc3 != 0:
                print(f"  ⚠️  source-map.py exit={rc3}: {stderr3[:200]}", file=sys.stderr)

        if build_trace_script.exists():
            rc4, _, stderr4 = _run_script(build_trace_script, [
                "--specback-dir", sb_str,
            ])
            if rc4 != 0:
                print(f"  ⚠️  build-trace.py exit={rc4}: {stderr4[:200]}", file=sys.stderr)

        print("  🔄 Config refreshed (source-map.json + trace.json)")

    return DriftOutput(
        affected_sections=len(affected_chapters),
        drift_report_path=str(report_path) if report_path.exists() else "",
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    specback_dir = resolve_specback_dir(args.target, args.specback_dir)
    if not specback_dir.is_dir():
        print(f"Error: specback directory not found: {specback_dir}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir or ".").resolve()

    run = session.ensure(adw_id=args.adw_id)

    with run.phase(session.PhaseParams(
        name="drift", kind="code", owner="code",
        description="Drift detection with optional REF auto-fix and config refresh",
    )) as ph:
        envelope = run_drift(
            specback_dir=specback_dir,
            output_dir=output_dir,
            mode=args.mode,
            base=args.base,
            skip_fix_refs=args.skip_fix_refs,
            skip_config_refresh=args.skip_config_refresh,
        )
        ph.log(envelope=envelope.to_dict())

        if args.envelope_out:
            out_path = Path(args.envelope_out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(envelope.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        count = envelope.affected_sections
        if count > 0:
            print(f"  ⚠️  Drift detected in {count} section(s) — see {envelope.drift_report_path}")
        else:
            print(f"  ✅ No drift detected")
        return run.finish(accepted=True)


if __name__ == "__main__":
    sys.exit(main())
