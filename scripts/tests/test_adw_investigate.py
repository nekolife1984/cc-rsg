"""Tests for adws/adw_specback_investigate.py — Phase 3 Investigate ADW."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ADW_INV = ROOT / "adws" / "adw_specback_investigate.py"


def test_imports() -> None:
    """Verify the ADW script can be imported without errors."""
    result = subprocess.run(
        [sys.executable, "-c", f"""
import sys
sys.path.insert(0, '{ROOT}')
from adws.adw_specback_investigate import (
    run_investigate, build_parser, extract_functions,
    write_chapter_draft, InvestigateOutput,
)
print('  ✅ ADW investigate imports OK')
"""],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, f"Import failed:\n{result.stderr}"


def test_help() -> None:
    """Verify --help works."""
    result = subprocess.run(
        [sys.executable, str(ADW_INV), "--help"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "specback ADW" in result.stdout
    assert "--target" in result.stdout


def test_no_target(tmp_path: Path) -> None:
    """Verify exits with error when target doesn't exist."""
    result = subprocess.run(
        [sys.executable, str(ADW_INV), "--target", str(tmp_path / "nonexistent")],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 1
    assert "target directory not found" in result.stderr


def test_extract_functions_python(tmp_path: Path) -> None:
    """Verify function extraction from Python files."""
    from adws.adw_specback_investigate import extract_functions

    py_file = tmp_path / "main.py"
    py_file.write_text(
        "def hello():\n    pass\n\nclass MyClass:\n    pass\n",
        encoding="utf-8",
    )

    result = extract_functions(py_file, tmp_path)
    assert len(result) >= 2
    names = {r["name"] for r in result}
    assert "hello" in names
    assert "MyClass" in names


def test_write_chapter_draft(tmp_path: Path) -> None:
    """Verify chapter draft writing."""
    from adws.adw_specback_investigate import write_chapter_draft

    drafts_dir = tmp_path / ".specback" / "drafts"
    drafts_dir.mkdir(parents=True)

    chapter = {
        "filename": "01-overview.md",
        "title": "System Overview",
        "kind": "standard",
    }
    inventory = [
        {"file": "src/main.py", "type": "source", "role": "implementation"},
        {"file": "README.md", "type": "doc", "role": "documentation"},
    ]

    ok, count = write_chapter_draft(
        chapter, inventory, tmp_path, drafts_dir, "outline", "en",
    )
    assert ok
    assert count >= 0

    draft_path = drafts_dir / "01-overview.md"
    assert draft_path.exists()
    content = draft_path.read_text(encoding="utf-8")
    assert "System Overview" in content


def test_full_investigate(tmp_path: Path) -> None:
    """Verify full investigation flow with mock project."""
    # Create mock project
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text(
        "def run():\n    pass\n\nclass App:\n    pass\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Project", encoding="utf-8")

    # Create .specback with wbs.json and inventory.json
    sb_dir = tmp_path / ".specback"
    sb_dir.mkdir()
    drafts_dir = sb_dir / "drafts"
    drafts_dir.mkdir()

    wbs = {
        "chapters": [
            {"filename": "01-overview.md", "title": "System Overview", "kind": "standard"},
            {"filename": "02-architecture.md", "title": "Architecture", "kind": "standard"},
            {"filename": "traceability.md", "title": "Traceability", "kind": "reserved"},
        ]
    }
    (sb_dir / "wbs.json").write_text(json.dumps(wbs), encoding="utf-8")

    inventory = [
        {"file": "src/main.py", "type": "source", "role": "implementation"},
        {"file": "README.md", "type": "doc", "role": "documentation"},
    ]
    (sb_dir / "inventory.json").write_text(json.dumps(inventory), encoding="utf-8")

    (sb_dir / "goal.json").write_text(
        json.dumps({"output_language": "en"}), encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable, str(ADW_INV),
            "--target", str(tmp_path),
            "--depth-mode", "outline",
            "--envelope-out", str(tmp_path / "investigate-envelope.json"),
        ],
        capture_output=True, text=True, timeout=30,
    )

    assert result.returncode == 0, f"Investigate failed:\n{result.stderr}"

    envelope_path = tmp_path / "investigate-envelope.json"
    assert envelope_path.exists()
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    assert envelope["chapters_completed"] >= 1
    assert envelope["depth_mode_used"] == "outline"
    assert envelope["drafts_path"]

    # Check draft files were created
    assert (sb_dir / "drafts" / "01-overview.md").exists()
    assert (sb_dir / "drafts" / "02-architecture.md").exists()

    # Check questions.json was created
    questions_path = sb_dir / "questions.json"
    assert questions_path.exists()
