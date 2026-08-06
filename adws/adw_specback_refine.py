#!/usr/bin/env python3
"""ADW — Phase 5: Refine via Dialogue.

Interactive CLI wizard (engineer + code hybrid). Presents the Question Bank
to the user and resolves uncertainty markers through dialogue.

Usage:
    uv run adws/adw_specback_refine.py --target /path/to/codebase
    uv run adws/adw_specback_refine.py --specback-dir .specback --non-interactive
"""

from __future__ import annotations

import argparse
import json
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
from scripts.data_types import DialogueOutput  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="specback ADW — Phase 5: Refine via Dialogue"
    )
    add_common_args(parser)
    parser.add_argument(
        "--output-dir",
        type=str, default=None,
        help="Output directory (default: current dir)",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Auto-resolve without prompting",
    )
    parser.add_argument(
        "--envelope-out",
        type=str, default=None,
        help="Path to write the DialogueOutput envelope JSON",
    )
    return parser


def load_json(path: Path) -> dict | list:
    """Load a JSON file."""
    if not path.exists():
        return {} if path.suffix == ".json" else []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _ask(question: str, choices: list[str], default: int = 0) -> str:
    """Interactive prompt with numbered choices."""
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
        except (ValueError, EOFError):
            return raw or choices[default]


def run_refine(
    specback_dir: Path,
    output_dir: Path,
    non_interactive: bool = False,
) -> DialogueOutput:
    """Execute Phase 5 dialogue and return a DialogueOutput envelope.

    Args:
        specback_dir: Path to .specback directory.
        output_dir: Output directory.
        non_interactive: Auto-resolve without prompting.

    Returns:
        DialogueOutput envelope.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    questions_path = specback_dir / "questions.json"
    drafts_dir = specback_dir / "drafts"

    # Load questions
    questions_data = load_json(questions_path)
    questions: list[dict] = []
    if isinstance(questions_data, list):
        questions = questions_data
    elif isinstance(questions_data, dict):
        questions = questions_data.get("questions", [])

    # Categorize
    total = len(questions)
    resolved = [q for q in questions if q.get("status") in ("resolved", "abandoned")]
    open_qs = [q for q in questions if q.get("status") == "open"]
    by_severity: dict[str, list[dict]] = {}
    for q in questions:
        sev = q.get("severity", "nice_to_have")
        by_severity.setdefault(sev, []).append(q)

    if total == 0:
        print("  📋 No questions found — nothing to refine")
        return DialogueOutput(
            questions_resolved=0,
            questions_abandoned=0,
            open_ratio=0.0,
            questions_path=str(questions_path),
        )

    open_ratio = len(open_qs) / total if total > 0 else 0.0
    resolved_count = len(resolved)
    abandoned_count = len([q for q in questions if q.get("status") == "abandoned"])

    # Present summary
    print(f"\n  📋 Question Bank: {total} total, {len(open_qs)} open, {resolved_count} resolved")
    if by_severity:
        for sev, items in sorted(by_severity.items()):
            print(f"     - {sev}: {len(items)}")

    if non_interactive or open_ratio <= 0.2:
        # Auto-resolve mode: mark all open as resolved
        for q in open_qs:
            q["status"] = "resolved"
            q["resolution"] = "Auto-resolved (non-interactive mode or within threshold)"
        resolved_count += len(open_qs)
        print(f"  ✅ Auto-resolved {len(open_qs)} open question(s)")
        skip_reason = "non-interactive" if non_interactive else "open_ratio_within_threshold"
    else:
        # Interactive: ask user how to proceed
        mode = _ask(
            f"Unresolved questions: {len(open_qs)} items\n"
            f"Open ratio: {open_ratio:.0%} (max allowed: 20%)\n\n"
            "Pick a progress mode:",
            ["Answer every question one by one (most thorough)",
             "Answer only critical/important ones (faster)",
             "Auto-resolve all remaining (fastest, marks all as resolved)"],
        )

        if "one by one" in mode or "most thorough" in mode:
            for q in open_qs:
                title = q.get("title", "Unknown")
                severity = q.get("severity", "nice_to_have")
                print(f"\n--- {title} [{severity}] ---")
                answer = input("Your answer (or press Enter to mark abandoned): ").strip()
                if answer:
                    q["status"] = "resolved"
                    q["resolution"] = answer
                    resolved_count += 1
                else:
                    q["status"] = "abandoned"
                    abandoned_count += 1
        elif "critical" in mode or "faster" in mode:
            for q in open_qs:
                if q.get("severity") in ("critical", "important"):
                    title = q.get("title", "Unknown")
                    answer = input(f"\n{title}\nYour answer (or Enter to skip): ").strip()
                    if answer:
                        q["status"] = "resolved"
                        q["resolution"] = answer
                        resolved_count += 1
                    else:
                        q["status"] = "abandoned"
                        abandoned_count += 1
                else:
                    q["status"] = "resolved"
                    q["resolution"] = "Skipped (not critical/important)"
                    resolved_count += 1
        else:
            # Auto-resolve all
            for q in open_qs:
                q["status"] = "resolved"
                q["resolution"] = "Auto-resolved by user choice"
            resolved_count += len(open_qs)

    # Persist updated questions
    if isinstance(questions_data, dict):
        questions_data["questions"] = questions
        data_to_write = questions_data
    else:
        data_to_write = questions
    with open(questions_path, "w", encoding="utf-8") as f:
        json.dump(data_to_write, f, ensure_ascii=False, indent=2)

    # Recalculate open ratio after resolution
    final_open = len([q for q in questions if q.get("status") == "open"])
    open_ratio = final_open / total if total > 0 else 0.0

    print(f"\n  📊 Result: {resolved_count} resolved, {abandoned_count} abandoned, "
          f"{final_open} remaining open")
    print(f"  📈 Open ratio: {open_ratio:.0%}")

    return DialogueOutput(
        questions_resolved=resolved_count,
        questions_abandoned=abandoned_count,
        open_ratio=open_ratio,
        skip_reason="" if open_ratio <= 0.2 else f"open_ratio_{open_ratio:.0%}",
        questions_path=str(questions_path),
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
        name="refine", kind="engineer", owner="engineer",
        description="Resolve uncertainty markers through dialogue",
    )) as ph:
        envelope = run_refine(
            specback_dir=specback_dir,
            output_dir=output_dir,
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

        if envelope.open_ratio <= 0.2:
            print(f"  ✅ Refine complete: {envelope.questions_resolved} resolved, "
                  f"{envelope.questions_abandoned} abandoned")
        else:
            print(f"  ⚠️  Open ratio {envelope.open_ratio:.0%} exceeds 20% threshold")
        return run.finish(accepted=envelope.open_ratio <= 0.2)


if __name__ == "__main__":
    sys.exit(main())
