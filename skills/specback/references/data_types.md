# Typed Envelopes Reference

## Overview

`scripts/data_types.py` defines typed envelopes for every specback phase.
Each phase produces a typed ``Envelope`` subclass that declares exactly what
data it passes to the next phase.  This makes the contract between phases
explicit, validated, and self-documenting.

## Design Principles

1. **stdlib only** — uses ``dataclass``, no pydantic dependency.
2. **Immutable by convention** — envelopes are created, read, serialised,
   never mutated in place.
3. **Backward compatible** — ``to_state_dict()`` / ``from_state_dict()``
   bridge the old ``state.json`` schema.
4. **Self-validating** — each envelope has a ``validate()`` method.
5. **JSON round-trip** — ``to_dict()`` ↔ ``from_dict()`` are symmetric.

## Available Envelopes

| Phase | Envelope | Key Fields |
|-------|----------|------------|
| 0 — Goal | `GoalOutput` | output_language, output_dir, primary_reader, granularity, perspectives, multi_scope, scopes |
| 1 — Recon | `ReconOutput` | frameworks, total_files, template_selected, depth_mode, tree_sitter_available |
| 2 — WBS | `WBSOutput` | chapters[], inventory_count |
| 3 — Investigate | `InvestigateOutput` | chapters_completed, chapters_blocked[], confidence_overall |
| 4 — Verify | `VerifyOutput` | all_gates_passed, failures[], mece_coverage_rate |
| 5 — Dialogue | `DialogueOutput` | questions_resolved, questions_abandoned, open_ratio |
| 6 — Deliver | `DeliverOutput` | output_path, chapters_delivered, user_custom_delivered |
| 6.5 — Deep-Dive | `DeepDiveOutput` | deep_dives_completed, deep_dive_paths[] |
| 7 — Drift | `DriftOutput` | affected_sections, drift_mode_used |
| 7b — REF Auto-Fix | `RefAutofixOutput` | refs_corrected, refs_orphaned |
| 7c — ChangeSpec | `ChangeSpecOutput` | changespec_path, files_changed, breaking_changes |
| 7d — Config Refresh | `ConfigRefreshOutput` | source_map_entries, trace_sections |

## Usage

```python
from data_types import GoalOutput, ReconOutput, StateTracking

# Create an envelope
goal = GoalOutput(
    output_language="en",
    output_dir="specs",
    primary_reader="maintenance_developer",
    granularity="medium",
    perspectives=["functional_correctness", "security"],
)

# Serialise / deserialise
raw = goal.to_dict()
restored = GoalOutput.from_dict(raw)

# Validate
errors = goal.validate()
if errors:
    print("Validation errors:", errors)
```

## StateTracking

`StateTracking` manages the overall session lifecycle — which phase is
active, progress tracking, and session history for resume support.

```python
from data_types import StateTracking

# Fresh session
st = StateTracking.fresh()
st.advance_phase(1)

# Track progress
st.init_phase_progress(3, total=12)
st.complete_subtask(3, "chapter-1")
st.block_subtask(3, "chapter-auth")

# Serialise
state_json = st.to_dict()
```

## Compatibility Layer

The old ``state.json`` format can be bridged via ``build_persistent_state()``:

```python
from data_types import GoalOutput, StateTracking, build_persistent_state

goal = GoalOutput(output_language="en", output_dir="specs")
tracking = StateTracking.fresh()

# Build a dict compatible with old state.json
state = build_persistent_state(goal, tracking, envelopes={0: goal})

# This dict can be written to .specback/state.json
```

## Envelope Registry

```python
from data_types import envelope_for_phase

env_class = envelope_for_phase(3)    # → InvestigateOutput
env_class = envelope_for_phase("7b") # → RefAutofixOutput
```

## Schema Generation

Each envelope has a ``schema()`` classmethod that returns a JSON Schema
draft-07 description:

```python
schema = GoalOutput.schema()
print(schema["properties"]["output_language"]["enum"])  # → ["en", "ja"]
```
