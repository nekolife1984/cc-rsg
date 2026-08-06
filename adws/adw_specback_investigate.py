#!/usr/bin/env python3
"""ADW — Phase 3: Investigate.

Code-first ADW (serial investigation). Reads source code through file analysis,
then writes chapter drafts based on structural extraction.

For each standard chapter in wbs.json:
1. Finds relevant source files from inventory.json
2. Extracts key structures (classes, functions, imports)
3. Generates draft content with REF markers and Sources Read
4. Builds questions.json from uncertainty markers

Usage:
    uv run adws/adw_specback_investigate.py --target /path/to/codebase
    uv run adws/adw_specback_investigate.py --specback-dir .specback --depth-mode comprehensive
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from adws.adw_modules import session  # noqa: E402
from adws.adw_modules.utils import (  # noqa: E402
    add_common_args,
    resolve_specback_dir,
)
from scripts.data_types import GoalOutput, InvestigateOutput  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="specback ADW — Phase 3: Investigate"
    )
    add_common_args(parser)
    parser.add_argument(
        "--output-dir",
        type=str, default=None,
        help="Output directory (default: current dir)",
    )
    parser.add_argument(
        "--depth-mode",
        type=str, default="outline",
        choices=["comprehensive", "outline"],
        help="Investigation depth mode (default: outline)",
    )
    parser.add_argument(
        "--envelope-out",
        type=str, default=None,
        help="Path to write the InvestigateOutput envelope JSON",
    )
    return parser


def load_json(path: Path) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _pretty_lang(lang: str) -> str:
    """Pretty-print a language name."""
    mapping = {
        "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript",
        "java": "Java", "go": "Go", "rust": "Rust", "ruby": "Ruby",
        "php": "PHP", "csharp": "C#", "swift": "Swift", "kotlin": "Kotlin",
        "cpp": "C++", "c": "C", "dart": "Dart", "sql": "SQL", "shell": "Shell",
    }
    return mapping.get(lang, lang.capitalize())


def extract_functions(file_path: Path, target_root: Path) -> list[dict[str, Any]]:
    """Extract function/class definitions from a source file using regex.

    Returns a list of {name, type, line} dicts.
    """
    result: list[dict[str, Any]] = []
    if not file_path.is_file():
        return result
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except (OSError, PermissionError):
        return result

    rel_path = str(file_path.relative_to(target_root)) if file_path.is_relative_to(target_root) else file_path.name
    ext = file_path.suffix.lower()

    patterns: list[tuple[str, str]] = []
    if ext == ".py":
        patterns = [
            (r"^\s*(?:async\s+)?def\s+(\w+)\s*\(", "function"),
            (r"^\s*class\s+(\w+)", "class"),
        ]
    elif ext in (".js", ".ts", ".tsx", ".jsx"):
        patterns = [
            (r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(", "function"),
            (r"(?:export\s+)?class\s+(\w+)", "class"),
            (r"(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(?", "arrow_function"),
        ]
    elif ext in (".java", ".kt", ".kts"):
        patterns = [
            (r"(?:public|private|protected)?\s*(?:static\s+)?\w+\s+(\w+)\s*\(", "method"),
            (r"(?:public|private|protected)?\s*class\s+(\w+)", "class"),
        ]
    elif ext == ".go":
        patterns = [
            (r"^func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(", "function"),
            (r"^type\s+(\w+)\s+struct", "struct"),
        ]
    elif ext == ".rs":
        patterns = [
            (r"^fn\s+(\w+)\s*\(", "function"),
            (r"^struct\s+(\w+)", "struct"),
            (r"^enum\s+(\w+)", "enum"),
        ]
    elif ext == ".rb":
        patterns = [
            (r"^\s*def\s+(?:self\.)?(\w+)", "method"),
            (r"^\s*class\s+(\w+)", "class"),
        ]
    elif ext == ".php":
        patterns = [
            (r"function\s+(\w+)\s*\(", "function"),
            (r"class\s+(\w+)", "class"),
        ]

    for line_no, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        for pattern, kind in patterns:
            m = re.match(pattern, stripped)
            if m:
                result.append({
                    "name": m.group(1),
                    "type": kind,
                    "file": rel_path,
                    "line": line_no,
                })
                break

    return result


def write_chapter_draft(
    chapter_info: dict[str, str],
    inventory: list[dict[str, str]],
    target_root: Path,
    drafts_dir: Path,
    depth_mode: str,
    lang_name: str,
) -> tuple[bool, int]:
    """Write a single chapter draft based on source analysis.

    Args:
        chapter_info: dict with filename, title, kind.
        inventory: list of inventory entries.
        target_root: target codebase root.
        drafts_dir: directory to write draft to.
        depth_mode: comprehensive or outline.
        lang_name: pretty language name.

    Returns:
        (success, sources_read_count)
    """
    fname = chapter_info["filename"]
    title = chapter_info["title"]
    kind = chapter_info.get("kind", "standard")
    draft_path = drafts_dir / fname

    # Reserved chapters are handled separately
    if kind == "reserved" or fname in ("00-metadata.md", "99-unresolved.md", "traceability.md"):
        return True, 0

    # Find relevant source files for this chapter
    chapter_keywords = title.lower().replace("-", " ").split()
    relevant_sources: list[str] = []
    for entry in inventory:
        file_path = entry.get("file", "")
        role = entry.get("role", "")
        ftype = entry.get("type", "")

        # Match by role/type
        if "architecture" in chapter_keywords and role in ("implementation", "interface"):
            relevant_sources.append(file_path)
        elif "data" in chapter_keywords and ftype == "data":
            relevant_sources.append(file_path)
        elif "api" in chapter_keywords and ftype in ("source", "config"):
            relevant_sources.append(file_path)
        elif "overview" in chapter_keywords or "introduction" in chapter_keywords:
            relevant_sources.append(file_path)
        elif role in ("configuration", "documentation"):
            relevant_sources.append(file_path)

    # Limit sources
    relevant_sources = sorted(set(relevant_sources))[:20]

    # Extract structures from relevant sources
    all_structures: list[dict] = []
    for src in relevant_sources:
        src_path = target_root / src
        structures = extract_functions(src_path, target_root)
        all_structures.extend(structures)

    # Generate draft content
    lines: list[str] = []
    lines.append(f"# {title}\n")
    lines.append(f"\n<!-- Chapter: {fname} -->\n")

    if depth_mode == "comprehensive":
        lines.append(f"\n## Overview\n\n")
        lines.append(f"This chapter covers the {title.lower()} of the system.\n")

        if relevant_sources:
            lines.append(f"\n## Key Files\n\n")
            for src in relevant_sources[:10]:
                lines.append(f"- `{src}`\n")

        if all_structures:
            lines.append(f"\n## Key Components\n\n")
            for s in all_structures[:20]:
                ref = f"<!-- REF: {s['file']}:{s['line']} -->"
                lines.append(f"- **`{s['name']}`** ({s['type']}) {ref}\n")
    else:
        # Outline mode: table-first
        lines.append(f"\n| Aspect | Description |\n")
        lines.append(f"|--------|-------------|\n")
        lines.append(f"| Purpose | (to be determined) |\n")
        if relevant_sources:
            lines.append(f"| Key files | {len(relevant_sources)} file(s) identified |\n")
        if all_structures:
            classes = [s for s in all_structures if s["type"] in ("class", "struct")]
            functions = [s for s in all_structures if s["type"] in ("function", "method")]
            lines.append(f"| Classes | {len(classes)} |\n")
            lines.append(f"| Functions | {len(functions)} |\n")

    # Sources Read section
    if relevant_sources:
        lines.append(f"\n## Sources Read\n\n")
        for src in relevant_sources[:10]:
            lines.append(f"- `{src}`\n")

    # Uncertainty marker for thin content
    body = "".join(lines)
    if len(body.splitlines()) < 20:
        marker = "<!-- CONFIDENCE: LOW — generated from file analysis, may need manual review -->\n"
        body = marker + body

    draft_path.write_text(body, encoding="utf-8")
    return True, len(relevant_sources)


def generate_questions_from_drafts(
    drafts_dir: Path,
    inventory: list[dict[str, str]],
    lang_name: str,
) -> list[dict[str, str]]:
    """Generate questions.json from uncertainty markers in drafts."""
    questions: list[dict[str, str]] = []
    if drafts_dir.is_dir():
        for f in sorted(drafts_dir.iterdir()):
            if f.suffix == ".md":
                content = f.read_text(encoding="utf-8", errors="replace")
                # Flag thin chapters as questions
                body_lines = [l for l in content.splitlines()
                              if l.strip() and not l.startswith("<!--")]
                if len(body_lines) < 15:
                    questions.append({
                        "title": f"Chapter {f.stem} needs review",
                        "status": "open",
                        "severity": "important",
                        "category": "completeness",
                        "question": f"The draft for {f.stem} is thin ({len(body_lines)} lines). "
                                    f"Does it cover all required content?",
                    })
    return questions


def run_investigate(
    specback_dir: Path,
    output_dir: Path,
    target_root: Path,
    depth_mode: str = "outline",
) -> InvestigateOutput:
    """Execute Phase 3 investigation and return an InvestigateOutput envelope.

    Args:
        specback_dir: Path to .specback directory.
        output_dir: Output directory.
        target_root: Target codebase root.
        depth_mode: comprehensive or outline.

    Returns:
        InvestigateOutput envelope.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    drafts_dir = specback_dir / "drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)

    # Load wbs and inventory
    wbs = load_json(specback_dir / "wbs.json")
    inventory = load_json(specback_dir / "inventory.json")
    goal = load_json(specback_dir / "goal.json")

    chapters = wbs.get("chapters", [])
    if not chapters:
        print("  ⚠️  No chapters in wbs.json — using default structure")
        chapters = [
            {"filename": "01-overview.md", "title": "System Overview", "kind": "standard"},
            {"filename": "02-architecture.md", "title": "System Architecture", "kind": "standard"},
            {"filename": "03-data-flow.md", "title": "Data Flow", "kind": "standard"},
            {"filename": "traceability.md", "title": "Traceability", "kind": "reserved"},
            {"filename": "99-unresolved.md", "title": "Unresolved Items", "kind": "reserved"},
        ]

    if not isinstance(inventory, list):
        inventory = []

    lang_name = _pretty_lang(goal.get("output_language", "en"))
    completed = 0
    blocked: list[str] = []

    # Process each chapter
    for ch in chapters:
        fname = ch["filename"]
        title = ch["title"]
        kind = ch.get("kind", "standard")

        if kind == "reserved":
            continue  # Handle reserved separately

        ok, count = write_chapter_draft(
            ch, inventory, target_root, drafts_dir,
            depth_mode, lang_name,
        )
        if ok:
            completed += 1
            print(f"  ✍️  {fname}: {count} source(s) referenced")
        else:
            blocked.append(fname)
            print(f"  ⚠️  {fname}: blocked")

    # Generate questions from thin drafts
    questions = generate_questions_from_drafts(drafts_dir, inventory, lang_name)
    questions_path = specback_dir / "questions.json"

    # Merge with existing questions
    existing_questions = load_json(questions_path)
    if isinstance(existing_questions, list):
        existing_questions.extend(questions)
        existing_questions = existing_questions
    elif isinstance(existing_questions, dict):
        existing_questions.setdefault("questions", []).extend(questions)
    else:
        existing_questions = {"questions": questions}

    with open(questions_path, "w", encoding="utf-8") as f:
        json.dump(existing_questions, f, ensure_ascii=False, indent=2)

    # Count draft files
    draft_files = [f for f in drafts_dir.iterdir() if f.suffix == ".md"] if drafts_dir.is_dir() else []
    all_files_ok = all(
        len(f.read_text(encoding="utf-8", errors="replace").splitlines()) >= 5
        for f in draft_files
    )

    # Calculate confidence
    total_chapters = len([c for c in chapters if c.get("kind") != "reserved"])
    confidence = completed / total_chapters if total_chapters > 0 else 1.0
    confidence = min(confidence * 0.8, 0.8)  # Cap at 0.8 since this is automated analysis

    print(f"\n  📊 {completed}/{total_chapters} standard chapter(s) completed")
    print(f"  📋 {len(questions)} question(s) generated for review")
    print(f"  📈 Confidence: {confidence:.0%}")

    return InvestigateOutput(
        chapters_completed=completed,
        chapters_blocked=blocked,
        questions_added=len(questions),
        confidence_overall=round(confidence, 2),
        depth_mode_used=depth_mode,
        drafts_path=str(drafts_dir),
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"Error: target directory not found: {target}", file=sys.stderr)
        return 1

    specback_dir = resolve_specback_dir(str(target), args.specback_dir)
    if not specback_dir.is_dir():
        print(f"Error: specback directory not found: {specback_dir}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir or ".").resolve()

    run = session.ensure(adw_id=args.adw_id)

    with run.phase(session.PhaseParams(
        name="investigate", kind="code", owner="code",
        description="Source code investigation and chapter draft generation",
    )) as ph:
        envelope = run_investigate(
            specback_dir=specback_dir,
            output_dir=output_dir,
            target_root=target,
            depth_mode=args.depth_mode,
        )
        ph.log(envelope=envelope.to_dict())

        if args.envelope_out:
            out_path = Path(args.envelope_out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(envelope.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        print(f"\n  ✅ Investigate complete: {envelope.chapters_completed} chapter(s)")
        return run.finish(accepted=True)


if __name__ == "__main__":
    sys.exit(main())
