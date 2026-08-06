#!/usr/bin/env python3
"""Tests for data_types.py — typed envelopes and state tracking."""

import json
import sys
from pathlib import Path

# Ensure data_types.py is importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data_types import (  # noqa: E402
    GoalOutput,
    ReconOutput,
    WBSOutput,
    InvestigateOutput,
    VerifyOutput,
    DialogueOutput,
    DeliverOutput,
    DeepDiveOutput,
    DriftOutput,
    RefAutofixOutput,
    ChangeSpecOutput,
    ConfigRefreshOutput,
    StateTracking,
    envelope_for_phase,
    build_persistent_state,
    EnvelopeBase,
)

import pytest  # noqa: E402


# ===================================================================
# EnvelopeBase
# ===================================================================


class TestEnvelopeBase:
    def test_defaults(self) -> None:
        e = EnvelopeBase()
        assert e.status == "success"
        assert e.artifacts == []
        assert e.summary == ""

    def test_to_dict_roundtrip(self) -> None:
        e = EnvelopeBase(status="fail", summary="something broke",
                         artifacts=["log.txt"])
        d = e.to_dict()
        restored = EnvelopeBase.from_dict(d)
        assert restored.status == "fail"
        assert restored.summary == "something broke"
        assert restored.artifacts == ["log.txt"]
        assert restored.notes_for_next_phase == ""

    def test_validate_empty(self) -> None:
        assert EnvelopeBase().validate() == []


# ===================================================================
# GoalOutput
# ===================================================================


class TestGoalOutput:
    def test_defaults(self) -> None:
        g = GoalOutput(output_language="en", output_dir="specs")
        assert g.output_language == "en"
        assert g.output_dir == "specs"
        assert g.primary_reader == "maintenance_developer"

    def test_to_goal_json(self) -> None:
        g = GoalOutput(output_language="ja", output_dir="docs/specs",
                       granularity="detailed")
        j = g.to_goal_json()
        assert j["output_language"] == "ja"
        assert j["output_dir"] == "docs/specs"
        assert j["granularity"] == "detailed"

    def test_validate_passes(self) -> None:
        g = GoalOutput(output_language="en", output_dir="specs")
        assert g.validate() == []

    def test_validate_fails_empty_dir(self) -> None:
        g = GoalOutput(output_language="en", output_dir="")
        errors = g.validate()
        assert any("output_dir" in e for e in errors)

    def test_validate_fails_empty_scopes(self) -> None:
        g = GoalOutput(output_language="en", output_dir="specs",
                       multi_scope=True, scopes=[])
        errors = g.validate()
        assert any("scopes" in e for e in errors)

    def test_validate_fails_negative_scope(self) -> None:
        g = GoalOutput(output_language="en", output_dir="specs",
                       current_scope=-1)
        errors = g.validate()
        assert any("current_scope" in e for e in errors)

    def test_schema_includes_literal_enums(self) -> None:
        s = GoalOutput.schema()
        props = s["properties"]
        assert "enum" in props["output_language"]
        assert set(props["output_language"]["enum"]) == {"en", "ja"}

    def test_to_dict_roundtrip(self) -> None:
        g = GoalOutput(output_language="ja", output_dir="specs",
                       user_custom_deliverables=["manual.md"],
                       multi_scope=True,
                       scopes=[{"name": "auth", "root": "services/auth"}])
        d = g.to_dict()
        restored = GoalOutput.from_dict(d)
        assert restored.output_language == "ja"
        assert restored.user_custom_deliverables == ["manual.md"]
        assert restored.scopes == [{"name": "auth", "root": "services/auth"}]


# ===================================================================
# ReconOutput
# ===================================================================


class TestReconOutput:
    def test_defaults(self) -> None:
        r = ReconOutput()
        assert r.frameworks == []
        assert r.total_files == 0

    def test_to_dict_roundtrip(self) -> None:
        r = ReconOutput(frameworks=["FastAPI", "SQLAlchemy"],
                        total_files=120,
                        template_selected="api-service",
                        depth_mode="comprehensive",
                        tree_sitter_available=True)
        d = r.to_dict()
        restored = ReconOutput.from_dict(d)
        assert restored.frameworks == ["FastAPI", "SQLAlchemy"]
        assert restored.template_selected == "api-service"


# ===================================================================
# WBSOutput
# ===================================================================


class TestWBSOutput:
    def test_defaults(self) -> None:
        w = WBSOutput()
        assert w.inventory_count == 0

    def test_validate_fails_empty(self) -> None:
        w = WBSOutput()
        errors = w.validate()
        assert any("chapters" in e for e in errors)
        assert any("inventory_count" in e for e in errors)

    def test_validate_passes(self) -> None:
        w = WBSOutput(chapters=[{"file": "01-overview.md"}],
                      inventory_count=5)
        assert w.validate() == []


# ===================================================================
# InvestigateOutput
# ===================================================================


class TestInvestigateOutput:
    def test_validate_confidence(self) -> None:
        inv = InvestigateOutput(confidence_overall=1.5)
        errors = inv.validate()
        assert any("confidence_overall" in e for e in errors)

    def test_valid_confidence(self) -> None:
        inv = InvestigateOutput(confidence_overall=0.85,
                                chapters_completed=10)
        assert inv.validate() == []


# ===================================================================
# VerifyOutput
# ===================================================================


class TestVerifyOutput:
    def test_passed_property(self) -> None:
        v = VerifyOutput(all_gates_passed=True)
        assert v.passed
        v2 = VerifyOutput(all_gates_passed=False)
        assert not v2.passed


# ===================================================================
# DialogueOutput
# ===================================================================


class TestDialogueOutput:
    def test_validate_open_ratio(self) -> None:
        d = DialogueOutput(open_ratio=1.5)
        errors = d.validate()
        assert any("open_ratio" in e for e in errors)

    def test_valid_open_ratio(self) -> None:
        d = DialogueOutput(open_ratio=0.15, questions_resolved=20)
        assert d.validate() == []


# ===================================================================
# DeliverOutput
# ===================================================================


class TestDeliverOutput:
    def test_defaults(self) -> None:
        d = DeliverOutput()
        assert d.chapters_delivered == 0


# ===================================================================
# DeepDiveOutput
# ===================================================================


class TestDeepDiveOutput:
    def test_roundtrip(self) -> None:
        dd = DeepDiveOutput(deep_dives_completed=3,
                            deep_dive_paths=["deep/D-001.md", "deep/D-002.md"])
        d = dd.to_dict()
        restored = DeepDiveOutput.from_dict(d)
        assert restored.deep_dives_completed == 3
        assert len(restored.deep_dive_paths) == 2


# ===================================================================
# Phase 7 envelopes
# ===================================================================


class TestPhase7Envelopes:
    def test_drift_output(self) -> None:
        d = DriftOutput(affected_sections=5, impact_high=2,
                        drift_mode_used="git")
        assert d.affected_sections == 5
        assert d.impact_high == 2

    def test_ref_autofix(self) -> None:
        r = RefAutofixOutput(refs_corrected=12, refs_orphaned=0,
                             dry_run=False)
        assert r.refs_corrected == 12
        assert not r.dry_run

    def test_changespec(self) -> None:
        c = ChangeSpecOutput(files_changed=8, breaking_changes=1)
        assert c.files_changed == 8
        assert c.breaking_changes == 1

    def test_config_refresh(self) -> None:
        cr = ConfigRefreshOutput(source_map_entries=150,
                                 trace_sections=45)
        assert cr.source_map_entries == 150


# ===================================================================
# StateTracking
# ===================================================================


class TestStateTracking:
    def test_fresh(self) -> None:
        st = StateTracking.fresh()
        assert st.current_phase == 0
        assert st.started_at
        assert len(st.session_history) == 1
        assert st.session_history[0]["event"] == "started"

    def test_advance_phase(self) -> None:
        st = StateTracking.fresh()
        st.advance_phase(1)
        assert st.current_phase == 1
        assert len(st.session_history) == 2
        assert st.session_history[-1]["event"] == "transitioned"
        assert st.last_updated

    def test_phase_progress(self) -> None:
        st = StateTracking.fresh()
        st.init_phase_progress(3, total=12)
        assert st.phase_progress["phase_3"]["total_subtasks"] == 12
        st.complete_subtask(3, "chapter-1")
        assert st.phase_progress["phase_3"]["completed_subtasks"] == 1
        st.block_subtask(3, "chapter-auth")
        assert "chapter-auth" in st.phase_progress["phase_3"]["blocked_subtasks"]

    def test_to_dict_from_dict(self) -> None:
        st = StateTracking.fresh()
        st.advance_phase(2)
        d = st.to_dict()
        restored = StateTracking.from_dict(d)
        assert restored.current_phase == 2
        assert len(restored.session_history) == 2

    def test_record_event(self) -> None:
        st = StateTracking.fresh()
        st.record_event("custom_event", phase=5)
        assert st.session_history[-1]["event"] == "custom_event"
        assert st.session_history[-1]["phase"] == 5


# ===================================================================
# Envelope registry
# ===================================================================


class TestEnvelopeRegistry:
    def test_envelope_for_phase_int(self) -> None:
        assert envelope_for_phase(0) is GoalOutput
        assert envelope_for_phase(1) is ReconOutput
        assert envelope_for_phase(2) is WBSOutput
        assert envelope_for_phase(3) is InvestigateOutput
        assert envelope_for_phase(4) is VerifyOutput
        assert envelope_for_phase(5) is DialogueOutput
        assert envelope_for_phase(6) is DeliverOutput
        assert envelope_for_phase(7) is DriftOutput

    def test_envelope_for_phase_string_keys(self) -> None:
        assert envelope_for_phase("7b") is RefAutofixOutput
        assert envelope_for_phase("7c") is ChangeSpecOutput
        assert envelope_for_phase("7d") is ConfigRefreshOutput

    def test_envelope_for_phase_unknown(self) -> None:
        with pytest.raises(KeyError):
            envelope_for_phase(99)

    def test_all_phases_have_envelopes(self) -> None:
        """Every phase 0–7d should have a registered envelope."""
        for phase in range(0, 8):
            assert envelope_for_phase(phase), f"Missing envelope for phase {phase}"
        for key in ("7b", "7c", "7d"):
            assert envelope_for_phase(key), f"Missing envelope for {key}"


# ===================================================================
# Compatibility layer
# ===================================================================


class TestCompatibility:
    def test_build_persistent_state(self) -> None:
        goal = GoalOutput(output_language="en", output_dir="specs")
        tracking = StateTracking.fresh()
        envelopes: dict[int | str, EnvelopeBase] = {0: goal}
        state = build_persistent_state(goal, tracking, envelopes)
        assert "goal" in state
        assert "state" in state
        assert "envelopes" in state
        assert state["goal"]["output_language"] == "en"
        assert state["state"]["current_phase"] == 0

    def test_build_persistent_state_no_envelopes(self) -> None:
        goal = GoalOutput(output_language="en", output_dir="specs")
        tracking = StateTracking.fresh()
        state = build_persistent_state(goal, tracking)
        assert "goal" in state
        assert "state" in state
        assert "envelopes" not in state


# ===================================================================
# Schema generation
# ===================================================================


class TestSchema:
    def test_goal_output_schema(self) -> None:
        s = GoalOutput.schema()
        assert s["title"] == "GoalOutput"
        assert "output_language" in s["properties"]
        assert "output_dir" in s["properties"]

    def test_schema_valid_json(self) -> None:
        """Schema output must be JSON-serialisable."""
        s = GoalOutput.schema()
        # Should not raise
        json.dumps(s)
