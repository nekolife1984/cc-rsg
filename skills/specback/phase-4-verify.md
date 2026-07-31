## Phase 4: Verify (checks + loopback)

### Purpose
Run inventory cross-check, per-chapter quality metrics, MECE check, and consistency checks automatically, looping failing chapters back to Phase 3.

### 🆕 Multi-scope execution

When `goal.multi_scope == true`, the following steps apply:

1. **Determine the current scope**: Read `goal.current_scope` (index into `goal.scopes[]`). Let `scope = goal.scopes[current_scope]`.
2. **Set scope-specific paths**:
   - `SPECBACK_DIR = ".specback-{scope.name}"` (e.g. `.specback-auth`)
   - `TARGET_ROOT = scope.root` (e.g. `services/auth`)
   - `OUTPUT_DIR = "{output_dir}/{scope.name}"` (e.g. `.specback/final/auth`)
3. **Ensure `.skill-path`**: `mkdir -p {SPECBACK_DIR} && ln -sf $(cat .specback/.skill-path) {SPECBACK_DIR}/.skill-path`
4. **Run the phase procedure below** using `{SPECBACK_DIR}` as the specback directory (for scripts: `--specback-dir {SPECBACK_DIR}`) and `{TARGET_ROOT}` as the target codebase root (for source-map: `--target {TARGET_ROOT}`).
5. **On completion**: Increment `goal.current_scope` in `.specback/goal.json`. If `current_scope >= scopes.length`, reset to `0` (all scopes done for this phase).
6. **Resume support**: After each scope completes, save `state.json` with `current_scope` so the session can resume from the correct scope.
7. **At the START of this phase**: If `goal.current_scope > 0` and `goal.multi_scope == true`, this is a resume — skip already-completed scopes and start from `goal.current_scope`.

When `goal.multi_scope == false` (default), run the phase procedure once with `.specback/` and the project root as before.

---


### Procedure

1. **Generate trace.json**
   ```bash
   python "$(cat .specback/.skill-path)/scripts/build-trace.py" --specback-dir .specback --output-dir {output_dir} --target-dir-for-required drafts
   ```
   This resolves every `[REF: path:line]` in `drafts/*.md` to a SRC unit and produces the MECE aggregation.

2. **Run coverage-check.py (mandatory; exit code is binding)**
   ```bash
   python "$(cat .specback/.skill-path)/scripts/coverage-check.py" \
     --specback-dir .specback \
     --output-dir {output_dir} \
     --target-dir-for-required drafts \
     --output-format text
   ```
   This invocation is **non-optional**. The script's exit code is the gate:

   **`--output-dir` vs `--target-dir-for-required` resolution:**

   | `--target-dir-for-required` | `--output-dir` (default: `.specback`) | Resolved path | Notes |
   |----------------------------|---------------------------------------|---------------|-------|
   | `drafts` | `.specback` | `.specback/drafts/` ✅ | Drafts always live here in Phase 4 |
   | `drafts` | `specs` (or any other dir) | `specs/drafts/` ❌ → **fallback**: `specs/drafts/` does not exist; the script tries `drafts/` as a standalone path → still missing → fails as expected |
   | `.specback/drafts` | `specs` | `specs/.specback/drafts/` ❌ → **fallback**: tries `.specback/drafts/` ✅ | Useful when `--output-dir` is custom and drafts are at `.specback/drafts/` |
   | `final` | `.specback` | `.specback/final/` ✅ | Used in Phase 6; not normally needed in Phase 4 |

   Fallback resolution: when `--output-dir / --target-dir-for-required` does not exist, the script automatically tries `--target-dir-for-required` as a standalone path (absolute or relative). This allows passing `.specback/drafts` directly without path arithmetic.
   - `0` → all checks pass; Phase 4 may proceed.
   - `1` → at least one check failed; go to step 3 (loopback). Recording `all_quality_gates_passed: true` in `state.json` while exit is 1 is forbidden.
   - `2` → required artefacts (e.g. `inventory.json`) missing; surface to user.

   **`--code-block-line-weight` (default: `0.5`):**
   Controls how non-blank lines inside fenced code blocks contribute to the body-lines count.
   - `0.5` (default): every two code-block lines count as one body line
   - `1.0`: code-block lines count as full body lines
   - `0.0`: code-block lines are excluded entirely (original behaviour)
   
   This prevents chapters with substantial code examples (API specs, internal structure, usage examples) from being penalised solely for having many code blocks. The weight is adjustable per project needs via the CLI flag.

   Checks performed (12 total):
   - inventory count (min: `max(50, files / 20)`)
   - macro-type INV ratio (max 20%)
   - covered_by fill rate (90%)
   - per-chapter body lines (≥ 200), `[REF:]` count (≥ 10), code blocks (≥ 3), Mermaid (≥ 1), Sources Read items (≥ 5) — **applied only to `kind: "standard"` chapters; `user_custom` chapters are exempt**
   - questions count (≥ 10), open ratio (≤ 20%)
   - MECE coverage (≥ 70%)
   - **Check 12 — User-custom deliverables**: every filename in `goal.json.user_custom_deliverables` must exist in the target directory (`.specback/drafts/` in Phase 4, `{output_dir}/` (default: `.specback/final/`) in Phase 6) AND have a non-empty body (≥ 10 non-blank lines outside code fences).

3. **Failure → loop back to Phase 3**
   - When exit code is 1, read the "gate decision" section of the output and:
     1. Identify the failed chapter (e.g. `chapter 05-data-model.md: [REF:] count is 7 < required 10`)
     2. **Read additional sources** corresponding to the chapter's `assigned_inventory_ids`
     3. Add to Sources Read, raise `[REF:]` count, thicken the body
     4. Re-run coverage-check.py
   - For `user_custom` chapters that are missing or empty, treat the failure the same way: return to Phase 3 and fill the chapter using `wbs.json.chapters[].source_intent` and any Phase 5 dialogue answers that pertain to it.
   - Maximum iterations: **3**. If a `kind: "standard"` chapter still fails after 3 attempts, record it in `99-unresolved.md` as "insufficient quality" and continue. A failing `kind: "user_custom"` chapter must NOT be silently demoted to `99-unresolved.md`; instead, prompt the user via `AskUserQuestion` to (a) keep retrying, (b) reduce scope, or (c) abandon the deliverable explicitly.

4. **Cross-reference verification**
   - Check whether any cross-chapter inconsistency exists for the same concept.
   - File inconsistencies into `questions.json` with `priority: critical`.

5. **Deduplicate questions**
   - Detect duplicates across the entire Question Bank.
   - Merge only the "obviously identical"; flag the "similar but subtly different" as groups for Phase 5 confirmation.

6. **Save the verification report**
   - Save `coverage-check.py --output-format json` output to `.specback/coverage-report.json`.
   - Save a human-readable version to `.specback/coverage-report.md`.

7. **Phase 4 complete**
   - Once every chapter passes (or hits the 3-attempt qualitative limit), update `state.json` and proceed to Phase 5.

### Phase-specific cautions
- **Do not proceed to Phase 5 until coverage-check.py PASSes** (up to 3 loop iterations). Setting `phase_4.all_quality_gates_passed: true` is only allowed when the most recent `coverage-check.py` invocation returned exit code 0.
- The loopback is not "padding the prose" — its purpose is to **read more real code, add more citations, and thicken the explanation**.
- Missing cross-chapter inconsistencies makes Phase 5 dialogue explode. Squash them in Phase 4.
- **`coverage_rate` < 100% with `all_quality_gates_passed: true` is a contradiction** and is never permitted. If full coverage is impossible within 3 iterations, leave `all_quality_gates_passed: false`, record the unfinished chapters, and surface to the user instead of advancing.
- **Feature specifications chapter (Ch2) note**: This chapter often has a higher 🔴 ASSUMED ratio than other chapters because code is organised by layer, not by feature. The Phase 3 investigation compensates by using multiple grouping strategies (see `references/outline-tables.md`). The 🔴 ratio warning in `coverage-check.py` is **informational only** for Ch2; it does not block the Phase 4 gate. The body-length and REF-count requirements still apply in `comprehensive` mode.
- **System design chapter note**: This chapter uses import analysis and pattern detection. The ADR section may have many 🔴 entries (design rationale is rarely in code). The 🔴 ratio warning in `coverage-check.py` is **informational only** for this chapter. Body-length and REF-count requirements still apply in `comprehensive` mode.

---
