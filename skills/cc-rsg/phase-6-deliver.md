## Phase 6: Deliver

### Purpose
Output the final spec as Markdown under `{output_dir}/final/`.

### Procedure

File names follow the ASCII slug convention finalised in Phase 2 (`^(0\d|[1-9]\d)-[a-z0-9-]+\.md$`; reserved files: `00-metadata.md` / `99-unresolved.md` / `traceability.md`). Phase 6 does not create new names; it fills in the skeleton files generated in Phase 2.

1. **Merge chapter drafts**
   - Copy every chapter in `wbs.json.chapters[]` — standard, reserved, AND user_custom — from `drafts/` to `{output_dir}/final/` in the template-defined order (user-custom chapters typically appear at the end unless the user's intent suggests otherwise).
   - Do NOT change the file names (use the names finalised in Phase 2).
   - Do NOT silently skip a chapter just because its draft body is short — that is a Phase 3 / Phase 4 failure and must be surfaced, not papered over.
   - Strip the meta comment at the top of each chapter file.

2. **Generate the traceability table (fill in `traceability.md`)**
   - Phase 2 created `traceability.md` as an empty file; write its body now.
   - Generate a table mapping each chapter/section to the source code it references.
   - Format example:

   ```markdown
   | Spec section | Source |
   |----------------|--------|
   | 3.2 User deactivation | src/jobs/UserDeactivationJob.php:12-58 |
   ```

3. **Generate the "Unresolved items" chapter (fill in `99-unresolved.md`)**
   - Phase 2 created the empty file; write its body now.
   - Aggregate `questions.json` entries with `status: abandoned`.
   - For each unresolved item, record "why it could not be resolved", "how far we inferred", "what is needed to resolve it in the future".
   - The chapter title in the body follows `goal.json.output_language` (EN example: `Chapter 99: Unresolved Items` / JA example: 「第99章: 未確定事項」). The file name `99-unresolved.md` is fixed regardless of language.

4. **Generate metadata (fill in `00-metadata.md`)**
   - Phase 2 created the empty file; write its body now.
   - Include: generation timestamp, commit hash of the target codebase (if available), goal definition finalised in Phase 0, template selection result, cc-rsg version.

5. **Final deliverable layout**
   ```
   {output_dir}/final/
   ├── 00-metadata.md       # metadata (created Phase 2, filled Phase 6)
   ├── 01-overview.md       # Chapter 1: Overview
   ├── 02-architecture.md   # Chapter 2: Architecture
   ├── 03-...each chapter...md
   ├── 99-unresolved.md     # Unresolved items (created Phase 2, filled Phase 6)
   ├── traceability.md      # Traceability table (created Phase 2, filled Phase 6)
   ├── manual.md            # Example: a user-custom deliverable declared in goal.json
   └── README.md            # Reader's guide for the deliverable (generated in Phase 6)
   ```
   Note: standard / reserved file names are ASCII slug-fixed (language-independent); user-custom file names match the verbatim entries in `goal.json.user_custom_deliverables`. Chapter titles in the body follow `goal.json.output_language` (EN example: `# Chapter 1: Overview` / JA example: `# 第1章: 概要`).

6. **Intent-vs-delivery audit (mandatory; the final gate before completion)**
   - Re-run `coverage-check.py` against `--target-dir-for-required final`. Exit code must be 0.
   - Verify that every filename listed in `goal.json.user_custom_deliverables` exists at `{output_dir}/final/{name}` AND has a non-empty body (≥ 10 non-blank lines outside code fences). Demoting any of these to `99-unresolved.md` or recording them as "for next time" in `state.json` is forbidden.
   - Verify that the three reserved files (`00-metadata.md`, `99-unresolved.md`, `traceability.md`) all exist under `final/`.
   - **Verify state.json invariants**:
     - `current_phase` must equal `6` (and only `6`) when Phase 6 completes. Earlier values such as `2` while `phase_6.status: "complete"` are inconsistent and indicate the agent advanced phases out of order — fail Phase 6 in that case.
     - For every `i` from 0 to 6, if `phase_i.status == "complete"`, then `phase_j.status` for `j < i` MUST also be `"complete"`. No skipping allowed.
     - `session_history[]` array MUST be present and non-empty. Missing or empty `session_history` indicates the agent never recorded any phase transition and is a contract violation.
     - The Phase 5 skip-prevention conditions (see Phase 5 "skip prevention" section) must hold: `questions.json` open-ratio ≤ 20%, ≥ 1 `AskUserQuestion` emitted in Phase 5, ≥ 1 question with populated `answer` field.
   - If ANY check fails: do NOT mark Phase 6 complete. Instead, reopen the offending chapter(s) (`wbs.json.chapters[].status = "pending"`), return to Phase 3 or Phase 5 as appropriate, and loop. Repeat until every check passes.
   - If after additional Phase 3/4 iterations the agent still cannot deliver a `user_custom` chapter (e.g. the source code does not support it), use `AskUserQuestion` to obtain explicit user permission to drop the deliverable; only an explicit user opt-out justifies skipping the file. Record the decision in `state.json.phase_6.user_opt_outs[]` with the reason.

7. **Timestamps in `state.json`**
   - Every entry in `state.json.session_history[]` and every `last_updated` / `completed_at` / `timestamp` field MUST use a real UTC timestamp captured at write time (e.g. `date -u +%FT%TZ`). Using a placeholder like `2026-01-01T00:00:00Z` for every event is forbidden — it makes post-mortem analysis impossible.
   - **Detector for placeholder timestamps**: if every `session_history` entry shares the same suspiciously round timestamp (`T00:00:00Z`, `T12:00:00Z`, or evenly-spaced 10-minute intervals like `T12:00:00Z`, `T12:10:00Z`, …), that is almost certainly synthetic. Regenerate `session_history` with real capture-time values, even retroactively if the original timing was not recorded — note that the timestamps are approximations and explain why in `00-metadata.md`. Never silently keep synthetic timestamps.

8. **Completion notification**
   - Report to the user the deliverable location, the total page (or section) count, number of resolved questions, number of unresolved items, AND the list of `user_custom_deliverables` that were delivered.
   - Mark `state.json` as complete only after step 6 passes.

### Phase-specific cautions
- The "unresolved items" chapter (`99-unresolved.md`) must NOT be omitted. It is the root of the spec's credibility.
- Omitting the metadata chapter (`00-metadata.md`) loses "when, from which version of the code" the spec was generated.
- Omitting the traceability table (`traceability.md`) makes every statement's origin untraceable.
- The presence of the three required files (`00-metadata.md` / `99-unresolved.md` / `traceability.md`) AND every file in `goal.json.user_custom_deliverables` is verified by `scripts/coverage-check.py`; missing files raise errors.
- **Pushing a user-promised deliverable into "future improvements" of `99-unresolved.md` is a contract breach**, not a graceful degradation. The user did not ask for a recommendation that the file be made; they asked for the file. If the file cannot be made, ask the user, do not invent a workaround.

---
