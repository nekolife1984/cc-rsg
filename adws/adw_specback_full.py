#!/usr/bin/env python3
"""specback ADW — Full pipeline entry point.

Runs all 10 phases in sequence. Each phase calls its corresponding ADW script
or executes inline logic. Envelopes (typed data) are passed between phases.

Supports ``--adw-id`` for resume: already-completed phases are skipped.

Usage:
    uv run adws/adw_specback_full.py --target /path/to/codebase
    uv run adws/adw_specback_full.py --target /path --adw-id adw-abc123 (resume)
    uv run adws/adw_specback_full.py --target /path --non-interactive
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from adws.adw_modules import session  # noqa: E402
from adws.adw_modules.utils import (  # noqa: E402
    add_common_args,
)


PHASES: list[dict[str, str | bool]] = [
    {"name": "setup", "script": "adw_specback_setup.py", "kind": "engineer",
     "desc": "Goal definition", "interactive": True},
    {"name": "recon", "script": "adw_specback_recon.py", "kind": "agent",
     "desc": "Codebase reconnaissance", "interactive": False},
    {"name": "wbs", "script": "adw_specback_wbs.py", "kind": "agent",
     "desc": "Work breakdown structure", "interactive": False},
    {"name": "investigate", "script": "adw_specback_investigate.py", "kind": "agent",
     "desc": "Chapter investigation", "interactive": False},
    {"name": "verify", "script": "adw_specback_verify.py", "kind": "code",
     "desc": "Verification gates", "interactive": False},
    {"name": "refine", "script": "adw_specback_refine.py", "kind": "engineer",
     "desc": "Dialogue refinement", "interactive": True},
    {"name": "deliver", "script": "adw_specback_deliver.py", "kind": "code",
     "desc": "Final deliverable", "interactive": False},
    {"name": "drift", "script": "adw_specback_drift.py", "kind": "code",
     "desc": "Drift detection", "interactive": False},
    {"name": "changespec", "script": "adw_specback_changespec.py", "kind": "code",
     "desc": "Change specification", "interactive": True},
]

# Phases where failure is non-fatal (self-reporting)
_NON_FATAL_PHASES = {"verify", "drift"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="specback ADW — Full pipeline (all 10 phases)"
    )
    add_common_args(parser)
    parser.add_argument(
        "--output-dir",
        type=str, default=None,
        help="Output directory (default: specs)",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip interactive phases (setup, refine, changespec)",
    )
    parser.add_argument(
        "--skip-phases",
        type=str, nargs="*",
        default=None,
        help="Phase names to skip (e.g. --skip-phases drift changespec)",
    )
    parser.add_argument(
        "--from-phase",
        type=str, default=None,
        help="Start from this phase (e.g. --from-phase verify)",
    )
    parser.add_argument(
        "--depth-mode",
        type=str, default="outline",
        choices=["comprehensive", "outline"],
        help="Investigation depth mode (default: outline)",
    )
    parser.add_argument(
        "--language",
        type=str, default=None,
        choices=["en", "ja"],
        help="Output language (default: en)",
    )
    return parser


def _run_adw(script_name: str, base_args: list[str]) -> int:
    """Run a single ADW script as a subprocess."""
    script_path = _PROJECT_ROOT / "adws" / script_name
    if not script_path.exists():
        print(f"  ⚠️  Script not found: {script_name}", file=sys.stderr)
        return 1

    print(f"\n{'='*60}")
    print(f"  ▶ Phase: {script_name.replace('adw_specback_', '').replace('.py', '')}")
    print(f"{'='*60}")

    result = subprocess.run(
        [sys.executable, str(script_path)] + base_args,
        capture_output=False,
        text=True,
        timeout=600,
    )
    return result.returncode


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"Error: target directory not found: {target}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir or "specs").resolve()
    specback_dir = Path(args.specback_dir).resolve() if args.specback_dir else (output_dir / ".specback")
    specback_dir.mkdir(parents=True, exist_ok=True)

    base_args = [
        "--target", str(target),
        "--output-dir", str(output_dir),
    ]
    if args.adw_id:
        base_args.extend(["--adw-id", args.adw_id])
    if args.specback_dir:
        base_args.extend(["--specback-dir", args.specback_dir])
    if args.non_interactive:
        base_args.append("--non-interactive")
    if args.depth_mode:
        base_args.extend(["--depth-mode", args.depth_mode])
    if args.language:
        base_args.extend(["--language", args.language])

    skip_phases = set(args.skip_phases or [])
    if args.from_phase:
        found = False
        for p in PHASES:
            if p["name"] == args.from_phase:
                found = True
            if not found:
                skip_phases.add(p["name"])

    run = session.ensure(
        adw_id=args.adw_id,
        specback_dir=specback_dir,
    )

    for phase in PHASES:
        pname = phase["name"]
        script = phase["script"]
        interactive = phase["interactive"]

        if run.is_completed(pname):
            print(f"  ⏭️  Phase '{pname}' already completed — skipping")
            continue

        if pname in skip_phases:
            print(f"  ⏭️  Phase '{pname}' skipped by user request")
            continue

        if interactive and args.non_interactive:
            print(f"  ⏭️  Phase '{pname}' skipped (interactive, --non-interactive)")
            continue

        rc = _run_adw(script, base_args)

        if rc != 0:
            print(f"\n  ❌ Phase '{pname}' failed with exit code {rc}", file=sys.stderr)
            if pname in _NON_FATAL_PHASES:
                continue
            return rc

        run.mark_completed(pname)

    print(f"\n{'='*60}")
    print(f"  ✅ Full pipeline complete!")
    print(f"  📍 Target: {target}")
    print(f"  📍 Output: {output_dir}")
    print(f"  📍 ADW ID: {run.adw_id}")
    print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
