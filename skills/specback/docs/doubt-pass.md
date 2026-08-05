# Doubt-pass: Adversarial Review Protocol

## Overview

The doubt-pass subphase (Phase 4, step 7) applies [addyosmani/agent-skills doubt-driven-development](https://github.com/addyosmani/agent-skills/blob/main/skills/doubt-driven-development/SKILL.md) principles to the specback verification pipeline. It questions every major claim in generated draft specs by re-reading the source code in a **fresh context** — as if the code were seen for the first time — and checking whether the interpretation is correct.

## Core workflow

```
CLAIM → EXTRACT → DOUBT → RECONCILE → STOP
```

| Step | Description |
|------|-------------|
| **CLAIM** | Isolate one specific claim from the draft (e.g. "`IssuesController#create` returns a 201 status on success"). Record the claim verbatim with source chapter and `<!-- REF: ... -->` anchor. |
| **EXTRACT** | Identify exact code file(s) and line(s) supporting the claim. Only use `<!-- REF: ... -->` citations already in the draft. |
| **RECONCILE** | Wrong -> loop to Phase 3 with corrective note. Imprecise -> adjust wording + tighten `<!-- REF: ... -->` range. Under-confident -> upgrade marker (🔴->🟡 or 🟡->🟢). |
| **STOP** | Assign confidence score (1.0 = certain, 0.0 = contradictory). Record in `{output_dir}/.specback/doubt-report.json`. |

## Doubt-trigger ruleset

### Trigger conditions (detail)

| Trigger | Detection | Priority | Default |
|---------|-----------|----------|---------|
| 🔴 **ASSUMED** | `rg "🔴"` in chapter content | Highest (auto) | Always included |
| 🟡 **INFERRED chain ≥ 3** | Count sequential INFERRED claims in a chapter with no VERIFIED between them | High | On |
| 🟢 **VERIFIED with comment conflict** | Compare `<!-- REF: ... -->` source line contents with claim text — if source comment says "// Fallback only" but claim says "primary path" | Medium | On |
| **Cross-chapter axiom** | Same statement text (fuzzy match) in >=2 chapters with zero `<!-- REF: ... -->` citations | Highest (auto) | Always included |

### Threshold tuning

The following keys in `goal.json.doubt` control behaviour:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable doubt-pass entirely |
| `scope` | string[] | `["assumed", "inferred", "verified", "axiom"]` | Which trigger types to process |
| `inferred_chain_min` | int | `3` | Minimum INFERRED chain length to trigger |
| `max_claims` | int | `10` | Max claims to review per run |
| `fresh_context_strict` | bool | `true` | When `true`, DOUBT step must actually re-read code (not reuse cached notes) |
| `confidence_threshold` | float | `0.5` | Claims below this score auto-loop to Phase 3 |

### scope shorthand

| Value | Expanded triggers |
|-------|-------------------|
| `"assumed_only"` | Assumed markers only (fastest) |
| `"core"` | Assumed + cross-chapter axioms |
| `"full"` | All 4 triggers (default) |

## Fresh context requirement

The DOUBT step **MUST** re-read the code from scratch. The following are **forbidden** during DOUBT:

- Referencing Phase 3 investigation notes, chapter drafts, or any prior analysis logs
- Recalling a previous read from memory without re-reading the actual file
- Using cached observations from an earlier session

Acceptable fresh-context reads:

```bash
# Read the exact code lines the <!-- REF: ... --> cites
read_file path/to/file.py --line 45-58

# Read surrounding context for edge case detection
read_file path/to/file.py --line 40-63
```

The read output must be treated as **new information** — evaluate it as if seeing the code for the first time. Any discrepancy found between this fresh read and the claim in the spec is a genuine doubt hit.

## Confidence scoring

Each claim receives a confidence score after DOUBT:

| Score | Meaning | Action |
|-------|---------|--------|
| 1.0 | Code fully matches the claim, no edge cases missed | ✅ Pass — keep claim as-is |
| 0.8–0.9 | Minor imprecision (label upgrade from 🟡 to 🟢 possible) | ✅ Pass — adjust wording |
| 0.5–0.7 | Edge case or alternative path not covered | ⚠️ Loop to Phase 3 — add missing context |
| 0.1–0.4 | Claim materially wrong | 🔴 Loop to Phase 3 — correct claim |
| 0.0 | Claim contradicts code completely | 🔴 Loop to Phase 3 + add `[NEEDS SME]` marker |

## Doubt-report.json schema

The output file lives at `{output_dir}/.specback/doubt-report.json`:

```json
{
  "$schema": "doubt-report.schema.json",
  "doubt-pass": true,
  "generated_at": "2026-08-02T12:00:00Z",
  "claims_reviewed": 5,
  "claims_passed": 3,
  "claims_needing_correction": 2,
  "confidence_avg": 0.72,
  "doubt_resolution_rate": 0.6,
  "failures": [
    {
      "chapter": "02-feature-specifications.md",
      "claim": "IssuesController#create returns 201 on success",
      "ref_source": "src/controllers/issues_controller.rb:45",
      "confidence": 0.3,
      "discrepancy": "Code raises 422 on validation failure; the claim only describes the happy path",
      "recommendation": "Split into success (201) and failure (422) sub-entries"
    }
  ]
}
```

Fields:

| Field | Type | Description |
|-------|------|-------------|
| `doubt-pass` | bool | True if all claims passed or were corrected |
| `generated_at` | string (ISO 8601) | Timestamp |
| `claims_reviewed` | int | Total claims processed |
| `claims_passed` | int | Claims with score ≥ `confidence_threshold` |
| `claims_needing_correction` | int | Claims below threshold |
| `confidence_avg` | float | Average confidence across all claims |
| `doubt_resolution_rate` | float | `claims_passed / claims_reviewed` |
| `failures[]` | array | Details of each failing claim |

## Question bank integration

| Doubt outcome | Question category | Severity | Example |
|---------------|-------------------|----------|---------|
| Missing code path (validation, error, alternative) | `architecture_decision` | critical | "Does `create` also handle idempotency keys?" |
| No code backing found at all | `spec_missing` | critical | "Feature 'bulk export' referenced in spec but no code path found" |
| Confidence uncertain after re-read (no clear contradiction) | `architecture_decision` | important | "The retry logic may be framework-blessed or custom — unclear from code" |

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Doubt-pass takes too many claims | `max_claims` too high | Lower `goal.json.doubt.max_claims` to 5 or 3 |
| Doubt finds nothing (all pass) | `scope` too narrow, or code is straightforward | Expand `scope` to `"full"` or add `"axiom"` |
| Phase 5 still has too many questions | Doubt-pass scope too narrow | Enable `"verified"` and `"axiom"` triggers |
| Doubt loops back same chapter repeatedly | Chapter or claim is fundamentally ambiguous | Record as `[NEEDS SME]` and advance — do not infinite-loop |
| Confidence scores seem arbitrary | Missing fresh-context enforcement | Set `fresh_context_strict: true` and verify DOUBT step actually re-reads files |

## Interaction with other phases

| Phase | Interaction |
|-------|-------------|
| **Phase 3 (Investigate)** | Doubt-pass may push claims back to Phase 3 via reconciliation loopback. Loopbacks count toward the 3-attempt limit. |
| **Phase 4 (Verify) — coverage-check** | Doubt-pass runs AFTER coverage-check passes. It does not replace it. |
| **Phase 5 (Dialogue)** | Doubt-pass resolves code-interpretation questions so they do NOT reach Phase 5. Genuine SME questions still flow through. |
| **Phase 6 (Deliver)** | `doubt-report.json` is carried into the final spec directory as supporting evidence of review rigour. |

---

*Inspired by [addyosmani/agent-skills: doubt-driven-development](https://github.com/addyosmani/agent-skills/blob/main/skills/doubt-driven-development/SKILL.md)*
