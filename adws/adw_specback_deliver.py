#!/usr/bin/env python3
"""ADW — Phase 6: Deliver.

Code-only ADW (no agent calls). Merges chapter drafts from .specback/drafts/
into the final output directory, generates metadata/traceability/unresolved
chapters, and runs coverage-check as a final gate.

Usage:
    uv run adws/adw_specback_deliver.py --target /path/to/codebase
    uv run adws/adw_specback_deliver.py --specback-dir .specback --output-dir specs
"""

from __future__ import annotations

import argparse
import json
import shutil
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
from scripts.data_types import DeliverOutput  # noqa: E402

# Reserved files that are always created
RESERVED_FILES = [
    "00-metadata.md",
    "99-unresolved.md",
    "traceability.md",
    "README.md",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="specback ADW — Phase 6: Deliver"
    )
    add_common_args(parser)
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for final spec (default: current dir)",
    )
    parser.add_argument(
        "--skip-kg",
        action="store_true",
        help="Skip Knowledge Graph export",
    )
    parser.add_argument(
        "--envelope-out",
        type=str,
        default=None,
        help="Path to write the DeliverOutput envelope JSON",
    )
    return parser


def load_json(path: Path) -> dict:
    """Load and return JSON from a file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def make_commit_hash() -> str:
    """Try to get the current commit hash of the target repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return "unknown"


def strip_meta_comment(content: str) -> str:
    """Strip the leading HTML meta comment from a chapter draft."""
    lines = content.splitlines()
    if not lines:
        return content
    if lines[0].strip().startswith("<!--"):
        if lines[0].strip().endswith("-->"):
            # Single-line comment: <!-- ... -->
            return "\n".join(lines[1:]).strip()
        # Multi-line comment
        end = 1
        while end < len(lines) and not lines[end].strip().endswith("-->"):
            end += 1
        return "\n".join(lines[end + 1:]).strip()
    return content


def run_deliver(
    specback_dir: Path,
    output_dir: Path,
    skip_kg: bool = False,
) -> DeliverOutput:
    """Execute the Deliver phase and produce a DeliverOutput envelope.

    Args:
        specback_dir: Path to .specback directory.
        output_dir: Path to output directory for final spec.
        skip_kg: If True, skip Knowledge Graph export.

    Returns:
        DeliverOutput envelope.
    """
    drafts_dir = specback_dir / "drafts"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load wbs.json for chapter order (if available)
    chapters: list[str] = []
    wbs_path = specback_dir / "wbs.json"
    if wbs_path.exists():
        wbs = load_json(wbs_path)
        chapters = [c.get("filename", "") for c in wbs.get("chapters", [])]

    reserved_delivered: list[str] = []

    # --- Step 1: Merge chapter drafts ---
    chapter_count = 0
    for chapter_file in chapters:
        src = drafts_dir / chapter_file
        dst = output_dir / chapter_file
        if not src.exists() and chapter_file not in RESERVED_FILES:
            # Create a placeholder for missing chapters
            dst.write_text(
                f"<!-- Chapter {chapter_file} not available — draft missing -->\n",
                encoding="utf-8",
            )
            continue
        if src.exists():
            content = src.read_text(encoding="utf-8")
            content = strip_meta_comment(content)
            dst.write_text(content, encoding="utf-8")
            chapter_count += 1

    # Copy any extra draft files not in wbs.json
    if drafts_dir.is_dir():
        for f in sorted(drafts_dir.iterdir()):
            if f.is_file() and f.name not in chapters and f.name not in RESERVED_FILES:
                content = strip_meta_comment(f.read_text(encoding="utf-8"))
                (output_dir / f.name).write_text(content, encoding="utf-8")
                chapter_count += 1

    # --- Step 2: Generate traceability.md ---
    trace_path = output_dir / "traceability.md"
    trace_src = specback_dir / "drafts" / "traceability.md"
    if trace_src.exists():
        shutil.copy2(trace_src, trace_path)
    else:
        # Generate a basic traceability table from build-traceability.py
        bt_script = _PROJECT_ROOT / "scripts" / "build-traceability.py"
        if bt_script.exists():
            subprocess.run(
                [sys.executable, str(bt_script),
                 "--specback-dir", str(specback_dir),
                 "--output-dir", str(output_dir),
                 "--stage", "final"],
                capture_output=True, text=True, timeout=30,
            )
        if not trace_path.exists():
            trace_path.write_text(
                "# Traceability\n\n| Spec section | Source |\n|--------------|--------|\n| (no traceability data) | |\n",
                encoding="utf-8",
            )
    reserved_delivered.append("traceability.md")

    # --- Step 3: Generate 99-unresolved.md ---
    unresolved_path = output_dir / "99-unresolved.md"
    questions_path = specback_dir / "questions.json"
    unresolved_items: list[dict] = []
    if questions_path.exists():
        questions = load_json(questions_path)
        entries = questions if isinstance(questions, list) else questions.get("questions", [])
        unresolved_items = [
            q for q in entries
            if q.get("status") == "abandoned"
        ]

    unresolved_content = "# Chapter 99: Unresolved Items\n\n"
    if unresolved_items:
        for item in unresolved_items:
            unresolved_content += (
                f"- **{item.get('title', 'Unknown')}**"
                f" — {item.get('reason', 'Not resolved')}\n"
            )
    else:
        unresolved_content += "No unresolved items.\n"
    unresolved_path.write_text(unresolved_content, encoding="utf-8")
    reserved_delivered.append("99-unresolved.md")

    # --- Step 4: Generate 00-metadata.md ---
    metadata_path = output_dir / "00-metadata.md"
    goal = {}
    goal_path = specback_dir / "goal.json"
    if goal_path.exists():
        goal = load_json(goal_path)

    metadata_content = (
        "# Chapter 00: Metadata\n\n"
        f"- **Generated**: {datetime.utcnow().isoformat()} UTC\n"
        f"- **Commit**: {make_commit_hash()}\n"
        f"- **Template**: {goal.get('template', 'N/A')}\n"
        f"- **Language**: {goal.get('output_language', 'N/A')}\n"
        f"- **Specback version**: 1.2.0\n"
    )
    metadata_path.write_text(metadata_content, encoding="utf-8")
    reserved_delivered.append("00-metadata.md")

    # --- Step 5: Generate README.md ---
    readme_path = output_dir / "README.md"
    readme_content = (
        "# Specification Document\n\n"
        f"Generated by specback v1.2.0\n\n"
        f"- **Target**: {goal.get('title', 'N/A')}\n"
        f"- **Template**: {goal.get('template', 'N/A')}\n"
        f"- **Generated at**: {datetime.utcnow().isoformat()} UTC\n"
        f"- **Chapters delivered**: {chapter_count}\n"
    )
    readme_path.write_text(readme_content, encoding="utf-8")
    reserved_delivered.append("README.md")

    # --- Step 6: Knowledge Graph export ---
    if not skip_kg:
        kg_script = _PROJECT_ROOT / "scripts" / "build-knowledge-graph.py"
        if kg_script.exists():
            subprocess.run(
                [sys.executable, str(kg_script),
                 "--specback-dir", str(specback_dir),
                 "--output-dir", str(output_dir)],
                capture_output=True, text=True, timeout=30,
            )

    # --- Step 7: Final coverage check ---
    cov_script = _PROJECT_ROOT / "scripts" / "coverage-check.py"
    if cov_script.exists():
        subprocess.run(
            [sys.executable, str(cov_script),
             "--specback-dir", str(specback_dir),
             "--output-dir", str(output_dir),
             "--output-format", "text"],
            capture_output=True, text=True, timeout=30,
        )

    return DeliverOutput(
        output_path=str(output_dir),
        chapters_delivered=chapter_count,
        reserved_files_delivered=reserved_delivered,
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
        name="deliver", kind="code", owner="code",
        description="Merge drafts and generate final deliverables",
    )) as ph:
        envelope = run_deliver(
            specback_dir=specback_dir,
            output_dir=output_dir,
            skip_kg=args.skip_kg,
        )
        ph.log(envelope=envelope.to_dict())

        if args.envelope_out:
            out_path = Path(args.envelope_out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(envelope.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        print(f"  ✅ Delivered {envelope.chapters_delivered} chapters to {output_dir}")
        if envelope.reserved_files_delivered:
            print(f"  📋 Reserved files: {', '.join(envelope.reserved_files_delivered)}")
        return run.finish(accepted=True)


if __name__ == "__main__":
    sys.exit(main())
