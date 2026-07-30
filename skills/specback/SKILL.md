---
name: specback
description: Reverse-engineer comprehensive specification documents from existing codebases through goal-driven reconnaissance, WBS-based parallel investigation, and iterative question-bank dialogue.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Task, AskUserQuestion, WebFetch, WebSearch
metadata:
  short-description: >-
    Reverse-spec generator for legacy codebases.
    Phased reconnaissance → WBS → parallel investigation →
    verification → dialogue refinement → delivery.
---

# specback (Reverse Spec Generator)

A general-purpose framework that reverse-engineers maintenance- or delivery-targeted specification documents from existing codebases (legacy or current).

This skill operates in the "code → spec" direction; it is the symmetric counterpart of `cc-sdd` (Spec Driven Development).

> **🌐 Language policy:** English is the base language; Japanese is opt-in.
> The Phase 0 dialogue confirms the output language. All machine-readable
> elements (IDs, `[REF: ...]`, confidence markers, JSON keys, file slugs)
> stay English regardless of language choice.

---

## Design principles

1. **Goal-driven**: Phase 0 fixes the goal through a choice-based dialogue persisted to `.specback/goal.json`. All subsequent phases reference this goal.
2. **Hybrid template decision**: Supports user's own template, Claude-recommended template, or user-adjusted recommendation.
3. **Reference-based inventory unit selection**: `references/inventory-units.md` lists typical units per language/framework.
4. **Inventory-based gap prevention**: Enumerate every extractable unit from the code and mechanically verify coverage.
5. **Question Bank populated at 3 moments**: end of reconnaissance, during sub-agent investigation, and at verification.
6. **Sub-agents decide dynamically based on question severity**: Critical → block section; Important/nice-to-have → proceed with inference marker.
7. **Question merge is automatic only for "obviously identical"**: Similar questions are grouped for user judgement.
8. **Dialogue protocol is agent-driven**: Choice-based questions by default; free-form fallback.
9. **Unanswerable questions marked `abandoned`**: Recorded in final spec under "unresolved items".
10. **Dual-consumer handling reduced to one in goal**: Restart for multiple views instead of overloading a single spec.
11. **Output language chosen in Phase 0**: English or Japanese. All natural-language output follows this choice.

---

## Mermaid styling contract (mandatory)

Every Mermaid diagram MUST be **structure-only — no color, no node-level fill, no per-node styling**. The rendering host supplies a theme-aware palette via CSS variables. Hardcoded colors override the host palette and break dark mode.

**Forbidden**: `style A fill:#...`, `classDef foo fill:#...`, `stroke:#...`, `color:#...`.

**Allowed**: arrow types, edge labels, node shapes (rectangle/round/diamond/etc.), subgraphs, diagram types, direction modifiers.

**Direction rule**: `graph TD` / `flowchart TD` (top-to-bottom) is the default for all graph/flowchart diagrams. Use `graph LR` (left-to-right) **only** when the diagram has ≤8 nodes AND the node labels are short enough to fit horizontally. For any diagram with many nodes, complex labels, or subgraphs, always prefer `TD`. This prevents the cramped/squished appearance that occurs when `LR` diagrams have many blocks.

**Active-diagram rule**: Every section describing something complex — whether processing (conditional branching, multi-step flows, state transitions, decision logic, async/callback chains), structure (module relationships, data flow, class hierarchies, ER), or behavior (authorization flows, screen transitions, integration sequences) — MUST be accompanied by an appropriate Mermaid diagram (flowchart, sequence, state-diagram, ER, component, class, etc.). A section that uses text alone where a diagram would make things clearer is a defect. When in doubt, add a diagram — readers always benefit from the visual.

Use **shape** (not color) for visual emphasis.

---

## Phase overview

| Phase | Name | Detail file | Main deliverables |
|-------|------|------------|------------|
| 0 | Setup & Goal | `phase-0-setup.md` | `.specback/goal.json` |
| 1 | Recon & Template | `phase-1-recon.md` | `recon-report.md`, template |
| 2 | Plan & WBS | `phase-2-wbs.md` | `inventory.json`, `wbs.json` |
| 3 | Investigate | `phase-3-investigate.md` | `.specback/drafts/*.md` (intermediate) |
| 4 | Verify | `phase-4-verify.md` | coverage report |
| 5 | Refine via Dialogue | `phase-5-dialogue.md` | resolved `questions.json` |
| 6 | Deliver | `phase-6-deliver.md` | `{output_dir}/` (final spec; default: `.specback/final/`) |
| 6.5 | Interactive Deep-Dive | `phase-6-5-deepdive.md` | on-demand deep-dive chapters |
| 7 | Drift Detection | `phase-7-drift.md` | `drift-report.md` |
| 7b | REF Auto-Fix | `phase-7b-ref-autofix.md` | corrected REF lines |
| 7c | ChangeSpec | `phase-7c-changespec.md` | `change-spec.md` |

## Common reference files

| File | Contents |
|------|----------|
| `question-bank.md` | Question Bank data structure, categories, severity, status transitions |
| `subagent-behavior.md` | Sub-agent prompt template, decision logic |
| `state-management.md` | `state.json` schema, resume behaviour |

---

## Execution rules (MUST read)

1. **Before starting any phase, Read the corresponding detail file first.** The phase overview table above maps each phase to its file.
2. **Question Bank operations** → read `question-bank.md` before Phase 1 step 4.
3. **Sub-agent delegation** → read `subagent-behavior.md` before Phase 3.
4. **State management & resume** → read `state-management.md` when resuming. It contains a phase→file mapping table that tells you exactly which detail files to load based on `state.json.current_phase`.
5. **On resume, after user confirms, load the phase file corresponding to `state.json.current_phase`** (see mapping in `state-management.md`). Without this, the phase instructions are not in the system prompt.
6. **The 11 design principles above are universal across all phases.**
7. **The Mermaid styling contract applies to every diagram in `.specback/drafts/` and `{output_dir}/`.**
8. **Context-saving note**: This SKILL.md is intentionally lightweight. Phase detail files are loaded only when needed via the Read tool, reducing per-invocation context overhead — especially important for Claude Code which injects SKILL.md into the system prompt.
