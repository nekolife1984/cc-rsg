"""Tests for adws/adw_specback_refine.py — Phase 5 Refine ADW."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ADW_REFINE = ROOT / "adws" / "adw_specback_refine.py"


def test_imports() -> None:
    """Verify the ADW script can be imported without errors."""
    result = subprocess.run(
        [sys.executable, "-c", f"""
import sys
sys.path.insert(0, '{ROOT}')
from adws.adw_specback_refine import run_refine, build_parser, DialogueOutput
print('  ✅ ADW refine imports OK')
"""],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, f"Import failed:\n{result.stderr}"


def test_help() -> None:
    """Verify --help works."""
    result = subprocess.run(
        [sys.executable, str(ADW_REFINE), "--help"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "specback ADW" in result.stdout
    assert "--target" in result.stdout


def test_no_specback_dir(tmp_path: Path) -> None:
    """Verify exits with error when .specback dir doesn't exist."""
    result = subprocess.run(
        [sys.executable, str(ADW_REFINE), "--target", str(tmp_path)],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 1
    assert "specback directory not found" in result.stderr


def test_non_interactive_no_questions(tmp_path: Path) -> None:
    """Verify non-interactive mode with no questions works."""
    sb_dir = tmp_path / ".specback"
    sb_dir.mkdir()
    (sb_dir / "goal.json").write_text('{"title": "test"}', encoding="utf-8")
    (sb_dir / "state.json").write_text('{"current_phase": "refine"}', encoding="utf-8")
    # No questions.json — edge case

    result = subprocess.run(
        [
            sys.executable, str(ADW_REFINE),
            "--target", str(tmp_path),
            "--non-interactive",
            "--envelope-out", str(tmp_path / "refine-envelope.json"),
        ],
        capture_output=True, text=True, timeout=30,
    )

    assert result.returncode == 0, f"Refine failed:\n{result.stderr}"
    envelope_path = tmp_path / "refine-envelope.json"
    assert envelope_path.exists()
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    assert envelope["questions_resolved"] == 0
    assert envelope["open_ratio"] == 0.0


def test_non_interactive_with_questions(tmp_path: Path) -> None:
    """Verify non-interactive mode auto-resolves open questions."""
    sb_dir = tmp_path / ".specback"
    sb_dir.mkdir()

    questions = [
        {"title": "Auth mechanism", "status": "open", "severity": "critical"},
        {"title": "DB choice", "status": "resolved", "severity": "important"},
        {"title": "Cache strategy", "status": "open", "severity": "nice_to_have"},
    ]
    (sb_dir / "questions.json").write_text(
        json.dumps(questions), encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable, str(ADW_REFINE),
            "--target", str(tmp_path),
            "--non-interactive",
            "--envelope-out", str(tmp_path / "refine-envelope.json"),
        ],
        capture_output=True, text=True, timeout=30,
    )

    assert result.returncode == 0, f"Refine failed:\n{result.stderr}"
    envelope_path = tmp_path / "refine-envelope.json"
    assert envelope_path.exists()
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    assert envelope["questions_resolved"] >= 2
    assert envelope["open_ratio"] == 0.0  # All resolved
