#!/usr/bin/env python3
"""Tests for gates.py — GateReport and all gate functions."""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure gates.py is importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import gates  # noqa: E402


# ===========================================================================
# GateReport unit tests
# ===========================================================================


class TestGateReport:
    def test_empty_report_passes(self) -> None:
        r = gates.GateReport("empty_test")
        assert r.passed
        assert r.summary == "✓ PASS empty_test: 0/0 checks passed"
        assert r.failures == []

    def test_all_pass(self) -> None:
        r = gates.GateReport("all_good")
        r.check("check-1", True, "ok")
        r.check("check-2", True, "ok")
        assert r.passed
        assert len(r.failures) == 0
        assert r.summary == "✓ PASS all_good: 2/2 checks passed"

    def test_one_failure(self) -> None:
        r = gates.GateReport("has_fail")
        r.check("passing", True, "")
        r.check("failing", False, "reason")
        assert not r.passed
        assert len(r.failures) == 1
        assert r.failures[0]["item"] == "failing"
        assert r.failures[0]["note"] == "reason"

    def test_to_dict(self) -> None:
        r = gates.GateReport("dict_test")
        r.check("item-x", True, "note")
        d = r.to_dict()
        assert d["gate"] == "dict_test"
        assert d["passed"] is True
        assert d["check_count"] == 1
        assert d["checks"][0]["item"] == "item-x"

    def test_str(self) -> None:
        r = gates.GateReport("str_test")
        r.check("a", True, "")
        assert str(r) == r.summary


# ===========================================================================
# Script path resolution
# ===========================================================================


class TestScriptPath:
    def test_script_path_resolves(self) -> None:
        """_script_path should point to existing sibling scripts."""
        script = gates._script_path("validate-schema.py")
        assert script.exists(), f"Expected {script} to exist"

    def test_script_path_via_fallback(self) -> None:
        """_resolve_skill_path falls back when .skill-path is absent."""
        with tempfile.TemporaryDirectory() as tmp:
            sp = gates._resolve_skill_path(tmp)
            # Fallback should point to the parent of scripts/
            assert sp.name == "specback" or (sp / "scripts").exists()


# ===========================================================================
# coverage_mece gate
# ===========================================================================


class TestCoverageMece:
    def test_returns_report(self) -> None:
        """Gate always returns a GateReport regardless of script outcome."""
        r = gates.coverage_mece(
            specback_dir="/nonexistent/specback",
            output_dir="/nonexistent",
        )
        assert isinstance(r, gates.GateReport)
        assert r.name == "coverage_mece"
        # Should fail because the path doesn't exist
        assert not r.passed
        assert len(r._checks) > 0


# ===========================================================================
# schema_valid gate
# ===========================================================================


class TestSchemaValid:
    def test_returns_report_on_missing_file(self) -> None:
        """Missing data file should produce a failing report."""
        r = gates.schema_valid(
            data_file="/nonexistent/data.json",
            schema_path="/nonexistent/schema.json",
        )
        assert isinstance(r, gates.GateReport)
        assert r.name == "schema_valid"
        assert not r.passed

    def test_returns_report_on_valid_schema(self) -> None:
        """Valid JSON against its schema should pass."""
        schema = {
            "$schema": "https://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        data = {"name": "test"}
        with tempfile.TemporaryDirectory() as tmp:
            schema_p = Path(tmp) / "test.schema.json"
            data_p = Path(tmp) / "test.json"
            schema_p.write_text(json.dumps(schema), encoding="utf-8")
            data_p.write_text(json.dumps(data), encoding="utf-8")
            r = gates.schema_valid(str(data_p), str(schema_p))
        assert isinstance(r, gates.GateReport)
        assert r.passed, f"Expected pass, got: {r.failures}"


# ===========================================================================
# traceability_full gate
# ===========================================================================


class TestTraceabilityFull:
    def test_returns_report(self) -> None:
        """Gate always returns a GateReport."""
        r = gates.traceability_full(
            specback_dir="/nonexistent/specback",
            output_dir="/nonexistent",
        )
        assert isinstance(r, gates.GateReport)
        assert r.name == "traceability_full"
        assert not r.passed  # should fail due to missing directory


# ===========================================================================
# drift_detected gate
# ===========================================================================


class TestDriftDetected:
    def test_returns_report(self) -> None:
        """Gate always returns a GateReport."""
        r = gates.drift_detected(
            specback_dir="/nonexistent/specback",
            output_dir="/nonexistent",
        )
        assert isinstance(r, gates.GateReport)
        assert r.name == "drift_detected"


# ===========================================================================
# run_gates
# ===========================================================================


class TestRunGates:
    def test_run_single_gate(self) -> None:
        """run_gates with one name returns one report."""
        reports = gates.run_gates("schema_valid", data_file="/x.json", schema="/x.json")
        assert len(reports) == 1
        assert reports[0].name == "schema_valid"

    def test_run_multiple_gates(self) -> None:
        """run_gates with multiple names returns reports in order."""
        reports = gates.run_gates("coverage_mece", "traceability_full",
                                   specback_dir="/nonexistent")
        assert len(reports) == 2
        assert reports[0].name == "coverage_mece"
        assert reports[1].name == "traceability_full"


# ===========================================================================
# CLI entry point
# ===========================================================================


class TestCLI:
    def test_cli_help(self) -> None:
        """--help should not crash."""
        try:
            gates.main()
        except SystemExit:
            pass


if __name__ == "__main__":
    pytest.main([__file__])
