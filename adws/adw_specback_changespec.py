#!/usr/bin/env python3
"""ADW — Phase 7c: ChangeSpec.

Code-only ADW (no agent calls). Runs change-spec.py for mechanical extraction,
then generates a human-readable change specification document (change-spec.md).

Usage:
    uv run adws/adw_specback_changespec.py --target /path/to/codebase
    uv run adws/adw_specback_changespec.py --specback-dir .specback --mode git
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from adws.adw_modules import session  # noqa: E402
from adws.adw_modules.utils import (  # noqa: E402
    add_common_args,
    resolve_specback_dir,
)
from scripts.data_types import ChangeSpecOutput  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="specback ADW — Phase 7c: ChangeSpec"
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
        help="Detection mode (default: auto)",
    )
    parser.add_argument(
        "--base",
        type=str, default=None,
        help="Git base ref to diff against",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip user confirmation",
    )
    parser.add_argument(
        "--envelope-out",
        type=str, default=None,
        help="Path to write the ChangeSpecOutput envelope JSON",
    )
    return parser


def _run_script(script_path: Path, args: list[str], timeout: int = 60) -> tuple[int, str, str]:
    """Run a Python script and return (returncode, stdout, stderr)."""
    if not script_path.exists():
        return (-1, "", f"Script not found: {script_path}")
    cmd = [sys.executable, str(script_path)] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (result.returncode, result.stdout, result.stderr)
    except subprocess.TimeoutExpired as e:
        return (-1, "", f"Timed out after {timeout}s: {e}")
    except (FileNotFoundError, OSError) as e:
        return (-1, "", f"Error: {e}")


def _generate_changespec_md(
    json_data: list[dict],
    output_dir: Path,
    drift_report_path: str = "",
) -> str:
    """Generate a human-readable change-spec.md from structured JSON data.

    Args:
        json_data: List of changed file entries from change-spec.json.
        output_dir: Output directory for the markdown file.
        drift_report_path: Optional path to drift report for context.

    Returns:
        Path to the generated change-spec.md.
    """
    lines = [
        "# Change Specification\n\n",
        f"**Generated**: {datetime.utcnow().isoformat()} UTC\n\n",
    ]

    breaking_count = 0
    for entry in json_data:
        file_path = entry.get("file", "unknown")
        change_type = entry.get("change_type", "modified")
        impact = entry.get("impact", "unknown")
        summary = entry.get("summary", "")
        if impact == "breaking":
            breaking_count += 1

        lines.append(f"## {file_path}\n\n")
        lines.append(f"- **Change type**: {change_type}\n")
        lines.append(f"- **Impact**: {impact}\n")
        if summary:
            lines.append(f"- **Summary**: {summary}\n")
        lines.append("\n")

    if not json_data:
        lines.append("No changes detected.\n")

    md_path = output_dir / "change-spec.md"
    md_path.write_text("".join(lines), encoding="utf-8")
    return str(md_path)


def run_changespec(
    specback_dir: Path,
    output_dir: Path,
    mode: str = "auto",
    base: str | None = None,
    non_interactive: bool = False,
) -> ChangeSpecOutput:
    """Execute Phase 7c ChangeSpec and return a ChangeSpecOutput envelope.

    Args:
        specback_dir: Path to .specback directory.
        output_dir: Output directory.
        mode: Detection mode.
        base: Git base ref.
        non_interactive: Skip user confirmation.

    Returns:
        ChangeSpecOutput envelope.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    sb_str = str(specback_dir)
    out_str = str(output_dir)

    # Step 1: User confirmation
    if not non_interactive:
        try:
            answer = input("\nGenerate a human-readable change specification? [Y/n]: ").strip().lower()
            if answer in ("n", "no"):
                print("  ⏭️  ChangeSpec skipped by user")
                return ChangeSpecOutput(
                    changespec_path="",
                    files_changed=0,
                    breaking_changes=0,
                )
        except (EOFError, KeyboardInterrupt):
            print("  ⏭️  ChangeSpec skipped")
            return ChangeSpecOutput(
                changespec_path="",
                files_changed=0,
                breaking_changes=0,
            )

    # Step 2: Run change-spec.py
    cs_script = _PROJECT_ROOT / "scripts" / "change-spec.py"
    cs_args = [
        "--specback-dir", sb_str,
        "--output", str(specback_dir / "change-spec.json"),
        "--mode", mode,
    ]
    if base:
        cs_args.extend(["--base", base])

    rc, stdout, stderr = _run_script(cs_script, cs_args)
    if rc != 0:
        print(f"  ⚠️  change-spec.py exit={rc}: {stderr[:200]}", file=sys.stderr)

    # Parse change-spec.json
    cs_json_path = specback_dir / "change-spec.json"
    changed_files: list[dict] = []
    if cs_json_path.exists():
        try:
            changed_files = json.loads(cs_json_path.read_text(encoding="utf-8"))
            if not isinstance(changed_files, list):
                changed_files = [changed_files]
        except json.JSONDecodeError:
            pass

    # Step 3: Generate change-spec.md
    drift_report_path = output_dir / "drift-report.json"
    drift_path_str = str(drift_report_path) if drift_report_path.exists() else ""

    md_path = _generate_changespec_md(
        changed_files, output_dir, drift_path_str,
    )

    # Count breaking changes
    breaking_count = sum(
        1 for entry in changed_files if entry.get("impact") == "breaking"
    )

    print(f"  📝 ChangeSpec written to {md_path}")
    print(f"  📊 {len(changed_files)} file(s) changed, {breaking_count} breaking")

    return ChangeSpecOutput(
        changespec_path=md_path,
        files_changed=len(changed_files),
        breaking_changes=breaking_count,
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
        name="changespec", kind="code", owner="code",
        description="Generate change specification from source changes",
    )) as ph:
        envelope = run_changespec(
            specback_dir=specback_dir,
            output_dir=output_dir,
            mode=args.mode,
            base=args.base,
            non_interactive=args.non_interactive,
        )
        ph.log(envelope=envelope.to_dict())

        if args.envelope_out:
            out_path = Path(args.envelope_out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(envelope.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        if envelope.changespec_path:
            print(f"  ✅ ChangeSpec complete: {envelope.files_changed} file(s), "
                  f"{envelope.breaking_changes} breaking")
        return run.finish(accepted=True)


if __name__ == "__main__":
    sys.exit(main())
