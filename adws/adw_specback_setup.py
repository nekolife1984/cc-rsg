#!/usr/bin/env python3
"""ADW — Phase 0: Setup & Goal.

Interactive CLI wizard (engineer + code hybrid). Asks the user 6 goal-definition
questions, selects a template, and persists goal.json + state.json.

Usage:
    uv run adws/adw_specback_setup.py --target /path/to/codebase
    uv run adws/adw_specback_setup.py --target /path --non-interactive  # use defaults
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from adws.adw_modules import session  # noqa: E402
from adws.adw_modules.utils import (  # noqa: E402
    add_common_args,
    resolve_specback_dir,
)
from scripts.data_types import GoalOutput  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="specback ADW — Phase 0: Setup & Goal"
    )
    add_common_args(parser)
    parser.add_argument(
        "--output-dir",
        type=str, default=None,
        help="Output directory for final spec (default: specs)",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Use defaults instead of prompting",
    )
    parser.add_argument(
        "--language",
        type=str, default=None,
        choices=["en", "ja"],
        help="Output language (overrides interactive prompt if set)",
    )
    parser.add_argument(
        "--envelope-out",
        type=str, default=None,
        help="Path to write the GoalOutput envelope JSON",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing state.json",
    )
    return parser


def _ask(question: str, choices: list[str], default: int = 0) -> str:
    """Interactive prompt with numbered choices. Returns the selected value."""
    print(f"\n{question}")
    for i, choice in enumerate(choices, 1):
        marker = " [default]" if i - 1 == default else ""
        print(f"  {i}. {choice}{marker}")
    while True:
        try:
            raw = input(f"Enter choice (1-{len(choices)}) or value: ").strip()
            if not raw:
                return choices[default]
            num = int(raw)
            if 1 <= num <= len(choices):
                return choices[num - 1]
            print(f"Please enter 1-{len(choices)}")
        except ValueError:
            print(f"Please enter 1-{len(choices)}")
        except EOFError:
            return choices[default]


def _ask_multi(question: str, choices: list[str]) -> list[str]:
    """Interactive multi-select prompt. Returns list of selected values."""
    print(f"\n{question}")
    print("  Enter numbers separated by commas (e.g. '1,3,5')")
    for i, choice in enumerate(choices, 1):
        print(f"  {i}. {choice}")
    while True:
        try:
            raw = input("Select: ").strip()
            if not raw:
                return [choices[0]]
            indices = [int(x.strip()) for x in raw.split(",")]
            selected = [choices[i - 1] for i in indices if 1 <= i <= len(choices)]
            if selected:
                return selected
            print("No valid selections")
        except ValueError:
            print("No valid selections")
        except EOFError:
            return [choices[0]]


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_setup(
    target: Path,
    output_dir: Path | None = None,
    non_interactive: bool = False,
    language: str | None = None,
    resume: bool = False,
) -> GoalOutput:
    """Execute Phase 0 setup and return a GoalOutput envelope.

    Args:
        target: Target codebase directory.
        output_dir: Output directory for spec.
        non_interactive: Skip interactive prompts (use defaults).
        language: Force output language.
        resume: Resume from existing state.json.

    Returns:
        GoalOutput envelope.
    """
    specback_dir = resolve_specback_dir(str(target), str(output_dir / ".specback") if output_dir else None)

    goal_path = specback_dir / "goal.json"
    if resume and goal_path.exists():
        existing = GoalOutput.from_dict(json.loads(goal_path.read_text(encoding="utf-8")))
        print(f"  🔄 Resumed from {goal_path}")
        return existing

    if output_dir:
        out = str(output_dir)
    elif non_interactive:
        out = "specs"
    else:
        out = _ask(
            "Where should the spec documents be written?",
            ["specs (default)", "docs", "Custom path"],
        )
        if out == "specs (default)":
            out = "specs"
        elif out == "docs":
            out = "docs"

    if language:
        lang: Literal["en", "ja"] = language
    elif non_interactive:
        lang = "en"
    else:
        sel = _ask(
            "Select output language / 出力言語を選択",
            ["English", "日本語 (Japanese)"],
        )
        lang = "en" if sel.startswith("English") else "ja"

    if non_interactive:
        return GoalOutput(
            output_language=lang,
            output_dir=out,
        )

    primary_reader = _ask(
        "Who is the primary reader of the spec?",
        ["Maintenance developer", "Delivery customer", "SME", "Regulator", "Other"],
    )
    reader_map = {
        "Maintenance developer": "maintenance_developer",
        "Delivery customer": "delivery_customer",
        "SME": "sme",
        "Regulator": "regulator",
    }

    reader_action = _ask(
        "What will the reader do after reading the spec?",
        ["Code change", "Approval decision", "Audit", "Learning", "Other"],
    )
    action_map = {
        "Code change": "code_change",
        "Approval decision": "approval_decision",
        "Audit": "audit",
        "Learning": "learning",
    }

    granularity = _ask(
        "What level of granularity is preferred?",
        ["High-level overview", "Medium", "Detailed", "Other"],
    )
    granularity_map = {
        "High-level overview": "high_level_overview",
        "Medium": "medium",
        "Detailed": "detailed",
    }

    perspectives = _ask_multi(
        "Which perspectives should be emphasised? (multi-select)",
        ["Functional correctness", "Business validity", "Security", "Operability", "Performance", "Other"],
    )
    perspective_map = {
        "Functional correctness": "functional_correctness",
        "Business validity": "business_validity",
        "Security": "security",
        "Operability": "operability",
        "Performance": "performance",
    }

    existing_docs = _ask(
        "What about existing documentation?",
        ["No existing docs", "Update existing", "Coexist with existing", "Retire existing", "Other"],
    )
    docs_map = {
        "No existing docs": "none",
        "Update existing": "update",
        "Coexist with existing": "coexist",
        "Retire existing": "retire",
    }

    free_text = input("\nAny additional notes or requirements? (press Enter to skip): ").strip()

    return GoalOutput(
        output_language=lang,
        output_dir=out,
        primary_reader=reader_map.get(primary_reader, "maintenance_developer"),
        reader_action=action_map.get(reader_action, "code_change"),
        granularity=granularity_map.get(granularity, "medium"),
        perspectives=[perspective_map.get(p, p.lower().replace(" ", "_")) for p in perspectives],
        existing_docs=docs_map.get(existing_docs, "none"),
        free_text_notes=free_text,
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"Error: target directory not found: {target}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir or "specs")
    specback_dir = Path(args.specback_dir).resolve() if args.specback_dir else (output_dir / ".specback")

    run = session.ensure(adw_id=args.adw_id, specback_dir=specback_dir)

    with run.phase(session.PhaseParams(
        name="setup", kind="engineer", owner="engineer",
        description="Goal definition via interactive wizard",
    )) as ph:
        envelope = run_setup(
            target=target,
            output_dir=output_dir,
            non_interactive=args.non_interactive,
            language=args.language,
            resume=args.resume,
        )
        ph.log(envelope=envelope.to_dict())

        _write_json(specback_dir / "goal.json", envelope.to_goal_json())
        skill_path = specback_dir / ".skill-path"
        skill_path.write_text(str(_PROJECT_ROOT), encoding="utf-8")
        _write_json(specback_dir / "state.json", {
            "current_phase": "setup",
            "output_dir": str(output_dir),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

        if args.envelope_out:
            out_path = Path(args.envelope_out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(envelope.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        print(f"\n  ✅ Goal defined")
        print(f"     Language: {envelope.output_language}")
        print(f"     Reader: {envelope.primary_reader}")
        print(f"     Action: {envelope.reader_action}")
        print(f"     Granularity: {envelope.granularity}")
        print(f"     Output: {output_dir}")

    # finish() outside the with block
    return run.finish(accepted=True)


if __name__ == "__main__":
    sys.exit(main())
