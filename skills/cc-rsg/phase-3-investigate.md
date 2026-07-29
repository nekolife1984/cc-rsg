## Phase 3: Investigate (read code, then write chapters)

### Purpose
Based on the WBS, **read the real source code first, then write each chapter**.

### 🆕 depth-mode branching (important)

`.cc-rsg/goal.json`'s `depth_mode` **changes Phase 3's overall behaviour**:

| depth_mode | Main behaviour | Chapter body shape |
|---|---|---|
| `comprehensive` | Apply STEP A-F below to every chapter | Long form: ≥ 200 lines + ≥ 10 REFs + ≥ 1 Mermaid + ≥ 5 Sources Read |
| **`outline` / `interactive`** | **STEP A-F are replaced for Layer 1 / 2 chapters** (see "outline-mode chapter writing" below) | Table-first + relationship diagrams + deep-dive candidate list |

In `outline` / `interactive` mode the following `comprehensive`-only STEPs do NOT apply:
- "200 lines or more" body length enforcement
- "10 REFs or more" citation enforcement
- "5 Sources Read or more" required count

Instead, use the **outline-mode writing rules** (below).

---

### Mandatory principles (strict) — for `comprehensive` mode

To make "writing a chapter without opening the code" structurally impossible, perform each chapter in this order:

#### STEP A: Sources Read (mandatory; skipping causes Phase 4 failure)

For every INV in that chapter's `wbs.json.chapters[*].assigned_inventory_ids`, **use the Read tool on the corresponding real source files**.

List the viewed file paths and line ranges at the **top of the chapter under a `## Sources Read` section**:

```markdown
# Chapter 5: Data Model

## Sources Read
- `app/models/issue.rb` (lines 1-440)
- `app/models/project.rb` (lines 1-690)
- `app/models/user.rb` (lines 1-120)
- `db/migrate/0042_create_orders.rb` (lines 1-50)
- `app/models/concerns/soft_delete.rb` (lines 1-95)

## 5.1 Overview
...
```

**Minimum 5 files** under Sources Read. `coverage-check.py` enforces this count. Writing `[REF:]` citations for files that are not listed is forbidden.

> Examples shown use Rails conventions. For catalogues covering PHP /
> Python (FastAPI / Django) / Java (Spring) / JavaScript & TypeScript
> (Express / Fastify / Hono) / Ruby on Rails, see
> `references/inventory-units.md`.


#### STEP B: Citation extraction (mandatory)

Extract at least **10 concrete citations** from the viewed code, all in **exactly one format**:

```
[REF: <workspace-relative path>:<start>]
[REF: <workspace-relative path>:<start>-<end>]
```

Examples:

```
[REF: app/models/issue.rb:42-56]
[REF: app/models/issue.rb:120-145]
[REF: config/routes.rb:7]
```

**Strict format requirements** (the UI's REF chip click-to-source feature parses these — variant formats render as plain non-clickable text, breaking reviewer flow):

- Use **`[REF: path:line]` or `[REF: path:start-end]` only**. The square brackets, the `REF:` prefix, and the colon between path and line numbers are all mandatory.
- The path is workspace-relative (`app/...` for an env with `archiveRoot = "myapp-main"`). Absolute paths are forbidden.
- Line numbers are integers. Use a single line (`:42`) when a single line is being cited; use a range (`:42-56`) when an extent matters. Do NOT use `L42`, `line 42`, ` lines 42-56`, parentheses, or any other decoration.
- Forbidden alternative forms include but are not limited to:
  - ❌ `Gemfile (lines 1-138)` — parenthesised line annotation
  - ❌ `<!-- Gemfile lines 1-138 -->` — HTML comment marker
  - ❌ `// app.js lines 1-5` — JS-style comment marker
  - ❌ `[REF: Gemfile L1-L138]` — leading `L`
  - ❌ `[REF: Gemfile, lines 1-138]` — comma + word "lines"
  - ❌ `[REF: Gemfile]` — no line numbers at all

Line ranges are precise (coarse ranges like `:1-500` are not acceptable). Cover class definitions, key methods, configuration values, callbacks, validations, exception handling, etc.

#### STEP C: Write the chapter body (required quality bar)

Incorporate the citations into the body. **Per-chapter mandatory requirements**:

| Item | Minimum | Verification script |
|------|---------|-------------|
| Body lines | ≥ 200 | coverage-check.py |
| `[REF:]` count | ≥ 10 | coverage-check.py |
| fenced code block | ≥ 3 | coverage-check.py |
| Mermaid diagrams | ≥ 1 | coverage-check.py |
| Sources Read items | ≥ 5 | coverage-check.py |

Chapters that fail these are rejected in Phase 4 and loop back to Phase 3 for correction.

Around each `[REF: ...]`, add prose explaining "what is happening". Writing only what Rails/Laravel-style frameworks "typically do" is forbidden — write what the **actual code** does after reading it.

#### STEP D: Uncertainty markers

Surface uncertainty in each statement:
- `[CONFIDENCE: HIGH | MED | LOW]`
- `[ASK SME]` (needs confirmation from a subject-matter expert)
- `[ASSUMED: ...]` (basis for the inference)

#### STEP E: Add detail questions to the Question Bank

Questions that surface while writing a chapter are added to `questions.json` (at least 1 per chapter). The final `questions.json` must contain **≥ 10 items** (`coverage-check.py` enforces this).

Examples:
- Is this method retrying three times because of a technical constraint or a business requirement?
- What is the rationale for this configuration value?
- Is this commented-out code a transient remnant or part of the spec?

#### STEP F: Handle critical questions

If a critical question is hit, leave the corresponding section as `[BLOCKED: see Q-042]` (empty). Loop back from Phase 5 (after dialogue) to Phase 3 to fill it in.

#### STEP G: Per-chapter sub-agent delegation (use when the `task` tool is available; recommended)

In environments where the `task` tool is available, **delegate each chapter to an isolated `chapter-investigator` sub-agent**. Writing every chapter directly in the main agent degrades context; investigating each chapter in its own context yields higher quality.

**Sub-agent invocation template:**

```
task(
  description="ch05 data-model investigation",
  prompt=\"\"\"
You are the chapter-investigator handling Chapter 5: Data Model.

Target inventory_ids:
- INV-012 (Project)
- INV-013 (Issue)
- INV-014 (User)
- INV-015 (Role)

Corresponding real sources (Read these with the Read tool):
- app/models/project.rb
- app/models/issue.rb
- app/models/user.rb
- app/models/role.rb
- db/schema.rb (relevant portions)

Draft output path: {output_dir}/drafts/05-data-model.md

Quality bar:
- Body ≥ 200 lines
- [REF: path:start-end] ≥ 10
- fenced code blocks ≥ 3
- Mermaid diagrams ≥ 1 (ER diagram)
- ≥ 5 files under ## Sources Read

When done, return the chapter's key points + a list of detail questions raised.
The detail questions are material for the main agent to append into questions.json.

NOTE: If goal.output_language == "ja", render the chapter body, headings,
prose, and detail-question text in Japanese. Keep code blocks, file paths,
JSON keys, [REF: ...] markers, and the literal heading "## Sources Read"
in English.
\"\"\",
  subagent_type="chapter-investigator"
)
```

**Important constraints**:

- **MANDATORY: Emit ALL chapter `task()` calls in a SINGLE assistant turn (parallel dispatch).**
  This is the most important rule of Phase 3. Read carefully — getting it wrong makes Phase 3 take **N× longer** than it needs to.

  **WRONG (sequential — DO NOT DO THIS):**
  ```
  Assistant turn 1: task("ch-02 ...")             ← issue ONE task
                    ← wait for the Observation
  Assistant turn 2: task("ch-03 ...")             ← then issue the next
                    ← wait
  Assistant turn 3: task("ch-06 ...")
                    ...
  ```
  This pattern serialises everything. If each `chapter-investigator` takes 4 minutes and you have 8 chapters, Phase 3 takes ~32 minutes. The runtime's sub-agent concurrency pool is **wasted** because you only ever have 1 sub-agent in flight at a time.

  **CORRECT (parallel — REQUIRED):**
  ```
  Assistant turn 1: task("ch-02 ...")
                    task("ch-03 ...")
                    task("ch-06 ...")
                    task("ch-08 ...")
                    task("ch-11 ...")
                    ... (one task() per chapter, ALL emitted back-to-back)
                    ← yield, do NOT plan / think / write anything else
  Single Observation turn: receives all N results at once
  ```
  In one assistant turn, emit one `task()` tool call per chapter, back-to-back, with NO intervening text, NO `thought`-style narration, NO partial writes — just the task calls. Then yield control. The runtime fans them out concurrently and returns all Observations together when they complete.

  With a sub-agent concurrency of 5 and 8 chapters: ~2 batches of ~4 minutes each → ~8 minutes total instead of 32. **Wall time scales by `1 / concurrency`**.

  **Self-check before emitting `task()`:**
  Have you written the prompts for **every** chapter that needs investigation in this Phase 3 round? If not, finish drafting them first, THEN emit them all together. Never emit one and "see how it goes" — that is the sequential anti-pattern.

  **Runtime concurrency mechanics.** The runtime's `Task` tool dispatches sub-agents in parallel up to its own pool. Other runtimes integrating the same skill should configure their own sub-agent pool similarly so the batch actually runs in parallel rather than being serialised at the executor level.

- **Prompt cache is NOT shared**: each sub-agent has an isolated LLM context, so token usage is 5–10× the main agent.
- **The sub-agent writes the chapter draft directly via the Write tool** (saved as a file, NOT returned in the task result text). The main agent reads the return value and appends detail questions into `questions.json`.
- **One `task()` per chapter**. Bundling all chapters into a single `task` call defeats the purpose (the isolated context per chapter disappears).

**When the `task` tool is unavailable**, the main agent performs STEP A-F itself per chapter.

---

### 🆕 outline-mode chapter writing (when `depth_mode == "outline" | "interactive"`)

This section does NOT apply in `comprehensive` mode. In outline mode, Phase 3's behaviour is replaced by OUT-A through OUT-D below.

#### OUT-A: Generate Layer 1 chapters (02-entities / 03-actions / 04-data / 05-dependencies)

Each Layer 1 chapter **exhaustively lists the "overview table" for that language**. Procedure:

1. Consult `.cc-rsg/skill/references/outline-tables.md` for the per-language catalogue.
2. **Use `glob` + `grep` to mechanically extract every entity**:
   - Ruby/Rails models: `grep "^class \\w+" --type ruby app/models/`
   - Controllers: `grep "^class \\w+Controller" --type ruby app/controllers/`
   - Etc., using the patterns from outline-tables.md for the target language.
3. Render the result as an **exhaustive Markdown table** — no omissions. 1 entity = 1 row.
4. Always add a **Confidence label** in each cell (🟢 VERIFIED / 🟡 INFERRED / 🔴 ASSUMED):
   - 🟢: the file of that entity was confirmed by reading it with the Read tool
   - 🟡: only the `grep` hit was confirmed; body unread
   - 🔴: inference based on framework-typical behaviour
5. The summary column is 1 line (≤ 80 characters). **Do not write detailed logic** — leave that to Layer 3 deep-dives.

**At the end of each chapter you MUST place a "deep-dive candidates" section** (see OUT-C).

#### OUT-B: Generate Layer 2 chapter (06-diagrams) — Mermaid

- ER diagram (auto-derived from Entities + Data tables)
- Module dependency diagram
- Representative sequence (1–3 of the most typical request flows)
- State-transition diagram (when key entities have `status` columns, etc.)

Each diagram has a **one-line caption** and a "how to read this" hint. If a diagram cell is `[INFERRED]`, say so explicitly.

#### OUT-C: "Deep-dive candidates" list at the end of each Layer 1 chapter

Place at the end of each chapter, using this format:

```markdown
### Deep-dive candidates (refer to them by ID)

- **D-001**: M-013 `Issue` class — authorisation guard logic [🔴 ASSUMED, complex]
- **D-002**: C-018 `ProjectsController#index` — visibility decision [🟡 INFERRED, business-critical]
- **D-003**: Sequence "Issue notification delivery" — subscribers resolution [🔴 ASSUMED]
```

Selection criteria (see the end of references/outline-tables.md):
1. Rows with many 🔴 ASSUMED labels.
2. High-complexity rows (top 10% by method count / association count / file line count).
3. Rows containing business-critical keywords (auth / payment / permission / audit, etc.).

#### OUT-D: Drop the body-length constraints

In outline mode:
- **The "200 lines / 10 REFs / 5 Sources Read" requirements do NOT apply.**
- Instead the MECE criterion is "**every entity appears in some row of some table**" (Phase 4's `coverage-check.py` decides this automatically).
- The chapter body consists of: table + 1–2 paragraphs of explanation + Mermaid diagrams (where applicable) + the deep-dive candidates list.

---

### Phase-specific cautions
- **In `comprehensive` mode**: writing a chapter without reading the code is forbidden. You may cite only files listed in Sources Read. ≥ 200 lines / ≥ 10 REFs / ≥ 5 Sources Read must be satisfied.
- **In `outline` / `interactive` mode**: "exhaustive entity listing" takes precedence. Apply Confidence labels honestly per cell — do NOT over-apply 🟢 (only for files actually viewed).
- Cross-chapter consistency is checked in Phase 4.
- Do not hide uncertainty markers; keep them explicit in the draft. They are the starting point for Phase 5 dialogue.
- **Phase 3 progression gate (mandatory)**: do NOT declare Phase 3 complete unless **every** chapter in `wbs.json.chapters[]` (standard, reserved, AND user_custom) has a non-empty body in `drafts/` (at least 10 non-blank lines outside of code fences). The agent MUST verify this before updating `state.json` to mark Phase 3 complete; declaring "complete" while chapters are still stubs is a contract violation and triggers an immediate Phase 4 fail.

---
