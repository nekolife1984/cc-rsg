"""Tests for adws/adw_specback_recon.py — Phase 1 Reconnaissance ADW."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ADW_RECON = ROOT / "adws" / "adw_specback_recon.py"


def test_imports() -> None:
    """Verify the ADW script can be imported without errors."""
    result = subprocess.run(
        [sys.executable, "-c", f"""
import sys
sys.path.insert(0, '{ROOT}')
from adws.adw_specback_recon import (
    scan_languages, estimate_complexity, recommend_template,
    run_recon, build_parser, ReconOutput,
)
print('  ✅ ADW recon imports OK')
"""],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, f"Import failed:\n{result.stderr}"


def test_help() -> None:
    """Verify --help works."""
    result = subprocess.run(
        [sys.executable, str(ADW_RECON), "--help"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "specback ADW" in result.stdout
    assert "--target" in result.stdout


def test_no_target(tmp_path: Path) -> None:
    """Verify exits with error when target doesn't exist."""
    result = subprocess.run(
        [sys.executable, str(ADW_RECON), "--target", str(tmp_path / "nonexistent")],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 1
    assert "target directory not found" in result.stderr


def test_scan_languages_python(tmp_path: Path) -> None:
    """Verify scan_languages detects Python files."""
    from adws.adw_specback_recon import scan_languages

    # Create Python files
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("import sys\n", encoding="utf-8")
    (tmp_path / "src" / "utils.py").write_text("def helper(): pass\n", encoding="utf-8")

    result = scan_languages(tmp_path)
    assert "python" in result["languages"]
    assert result["languages"]["python"] >= 2
    assert "Python" in result["language_names"]
    assert result["total_files"] >= 2


def test_scan_languages_multi(tmp_path: Path) -> None:
    """Verify scan_languages detects multiple languages."""
    from adws.adw_specback_recon import scan_languages

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("import sys\n", encoding="utf-8")
    (tmp_path / "src" / "app.js").write_text("console.log('hello');\n", encoding="utf-8")
    (tmp_path / "src" / "styles.ts").write_text("const x: number = 1;\n", encoding="utf-8")

    result = scan_languages(tmp_path)
    assert "python" in result["languages"]
    assert "javascript" in result["languages"]
    assert "typescript" in result["languages"]
    assert "Python" in result["language_names"]
    assert "JavaScript" in result["language_names"]
    assert "TypeScript" in result["language_names"]
    assert result["total_files"] >= 3


def test_scan_languages_empty(tmp_path: Path) -> None:
    """Verify scan_languages handles empty directory."""
    from adws.adw_specback_recon import scan_languages

    result = scan_languages(tmp_path)
    assert result["languages"] == {}
    assert result["total_files"] == 0


def test_scan_languages_skips_node_modules(tmp_path: Path) -> None:
    """Verify scan_languages skips node_modules."""
    from adws.adw_specback_recon import scan_languages

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("import sys\n", encoding="utf-8")
    (tmp_path / "node_modules").mkdir(parents=True)
    (tmp_path / "node_modules" / "big.js").write_text("// big\n", encoding="utf-8")

    result = scan_languages(tmp_path)
    assert "python" in result["languages"]
    assert result["languages"]["python"] == 1
    # node_modules should be skipped
    assert result["total_files"] == 1


def test_scan_languages_skips_git(tmp_path: Path) -> None:
    """Verify scan_languages skips .git directory."""
    from adws.adw_specback_recon import scan_languages

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("import sys\n", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("[core]\n", encoding="utf-8")

    result = scan_languages(tmp_path)
    assert result["total_files"] == 1


def test_scan_languages_frameworks(tmp_path: Path) -> None:
    """Verify scan_languages detects frameworks from package manifests."""
    from adws.adw_specback_recon import scan_languages

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("import django\n", encoding="utf-8")
    (tmp_path / "manage.py").write_text("#!/usr/bin/env python\n", encoding="utf-8")

    result = scan_languages(tmp_path)
    assert "python" in result["languages"]
    assert "Django" in result["frameworks"]


def test_scan_languages_top_level_dirs(tmp_path: Path) -> None:
    """Verify scan_languages returns top-level directories."""
    from adws.adw_specback_recon import scan_languages

    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "src" / "main.py").write_text("import sys\n", encoding="utf-8")

    result = scan_languages(tmp_path)
    assert "src" in result["top_level_dirs"]
    assert "tests" in result["top_level_dirs"]
    assert "docs" in result["top_level_dirs"]


def test_estimate_complexity_low(tmp_path: Path) -> None:
    """Verify estimate_complexity returns low for simple projects."""
    from adws.adw_specback_recon import estimate_complexity

    result = estimate_complexity(tmp_path, {"python": 10}, [])
    assert result == "low"


def test_estimate_complexity_medium(tmp_path: Path) -> None:
    """Verify estimate_complexity returns medium for moderate projects."""
    from adws.adw_specback_recon import estimate_complexity

    result = estimate_complexity(tmp_path, {"python": 50, "javascript": 30}, ["React", "Flask"])
    assert result == "medium"


def test_estimate_complexity_high(tmp_path: Path) -> None:
    """Verify estimate_complexity returns high for complex projects."""
    from adws.adw_specback_recon import estimate_complexity

    languages = {
        "python": 200, "javascript": 150, "typescript": 100,
        "go": 50, "rust": 30, "java": 20, "sql": 40,
    }
    frameworks = ["React", "Django", "Express", "Spring Boot", "GORM", "Tokio", "Serde"]
    result = estimate_complexity(tmp_path, languages, frameworks)
    assert result == "high"


def test_recommend_template_web(tmp_path: Path) -> None:
    """Verify recommend_template returns web-app for web frameworks."""
    from adws.adw_specback_recon import recommend_template

    templates_dir = ROOT / "templates"
    result = recommend_template({"python": 10, "javascript": 5}, ["Django", "React"], "medium", templates_dir)
    assert result == "web-app"


def test_recommend_template_api(tmp_path: Path) -> None:
    """Verify recommend_template returns api-service for API frameworks."""
    from adws.adw_specback_recon import recommend_template

    templates_dir = ROOT / "templates"
    result = recommend_template({"go": 20, "python": 5}, ["Gin", "FastAPI"], "medium", templates_dir)
    assert result == "api-service"


def test_recommend_template_cli(tmp_path: Path) -> None:
    """Verify recommend_template returns cli-tool for shell-heavy projects."""
    from adws.adw_specback_recon import recommend_template

    templates_dir = ROOT / "templates"
    result = recommend_template({"shell": 30}, [], "low", templates_dir)
    assert result == "cli-tool"


def test_recommend_template_library(tmp_path: Path) -> None:
    """Verify recommend_template returns library-sdk for library patterns."""
    from adws.adw_specback_recon import recommend_template

    templates_dir = ROOT / "templates"
    result = recommend_template({"python": 40}, ["Pydantic", "SQLAlchemy"], "medium", templates_dir)
    assert result == "library-sdk"


def test_recommend_template_mobile(tmp_path: Path) -> None:
    """Verify recommend_template returns mobile-app for mobile frameworks."""
    from adws.adw_specback_recon import recommend_template

    templates_dir = ROOT / "templates"
    result = recommend_template({"dart": 30, "kotlin": 10}, ["Flutter"], "medium", templates_dir)
    assert result == "mobile-app"


def test_recommend_template_infrastructure(tmp_path: Path) -> None:
    """Verify recommend_template returns infrastructure for infra frameworks."""
    from adws.adw_specback_recon import recommend_template

    templates_dir = ROOT / "templates"
    result = recommend_template({"terraform": 15, "yaml": 10}, ["Terraform"], "medium", templates_dir)
    assert result == "infrastructure"


def test_recommend_template_fallback(tmp_path: Path) -> None:
    """Verify recommend_template falls back to api-service."""
    from adws.adw_specback_recon import recommend_template

    templates_dir = ROOT / "templates"
    result = recommend_template({"unknown_ext": 5}, [], "low", templates_dir)
    available = {p.stem for p in templates_dir.glob("*.md") if p.is_file() and not p.stem.startswith("_")}
    assert result in available  # fallback picks something available


def test_dominant_language() -> None:
    """Verify dominant_language returns the top language."""
    from adws.adw_specback_recon import dominant_language

    assert dominant_language({"python": 50, "javascript": 30}) == "python"


def test_dominant_language_empty() -> None:
    """Verify dominant_language handles empty dict."""
    from adws.adw_specback_recon import dominant_language

    assert dominant_language({}) == "unknown"


def test_recon_output_type() -> None:
    """Verify ReconOutput dataclass works correctly."""
    from adws.adw_specback_recon import ReconOutput

    output = ReconOutput(
        frameworks=["Python", "Flask"],
        total_files=42,
        template_selected="api-service",
        depth_mode="outline",
        recon_report_path="/tmp/recon.json",
    )
    assert output.frameworks == ["Python", "Flask"]
    assert output.total_files == 42
    assert output.template_selected == "api-service"
    assert output.depth_mode == "outline"
    assert output.recon_report_path == "/tmp/recon.json"

    # Test serialisation round-trip
    d = output.to_dict()
    restored = ReconOutput.from_dict(d)
    assert restored.frameworks == output.frameworks
    assert restored.template_selected == output.template_selected


def test_full_recon(tmp_path: Path) -> None:
    """Verify full recon run with mock project."""
    # Create mock project
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("import sys\nfrom flask import Flask\n", encoding="utf-8")
    (tmp_path / "src" / "utils.py").write_text("def helper(): pass\n", encoding="utf-8")
    (tmp_path / "src" / "app.js").write_text("import React from 'react';\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Project", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable, str(ADW_RECON),
            "--target", str(tmp_path),
            "--non-interactive",
            "--envelope-out", str(tmp_path / "recon-envelope.json"),
        ],
        capture_output=True, text=True, timeout=30,
    )

    assert result.returncode == 0, f"Recon failed:\n{result.stderr}"

    # Check envelope
    envelope_path = tmp_path / "recon-envelope.json"
    assert envelope_path.exists(), f"Envelope not written:\n{result.stdout}"
    envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    assert envelope["template_selected"]
    assert envelope["total_files"] >= 2
    assert envelope["recon_report_path"]
    assert "frameworks" in envelope
    assert "depth_mode" in envelope

    # Check recon.json report
    recon_report = Path(envelope["recon_report_path"])
    assert recon_report.exists()
    report = json.loads(recon_report.read_text(encoding="utf-8"))
    assert "languages" in report
    assert "estimated_complexity" in report
    assert "recommended_template" in report
    assert report["recommended_template"] == envelope["template_selected"]
