## Phase 0: Setup & Goal

### Purpose
Right after the skill starts, fix the scope and the goal. Every later decision derives from the goal defined here.

### Procedure

1. **Project confirmation**
   - Start from the current working directory and identify the target project.
   - Ask the user "Is this the right root directory for the target codebase?". If not, obtain the correct path.

2. **Initialize the state directory**
   - Create the `.cc-rsg/` directory.
   - **Stage the skill bundle into `.cc-rsg/skill/`**: every helper invocation in this document refers to the scripts and references through a `.cc-rsg/skill/...` path (e.g. `python .cc-rsg/skill/scripts/source-map.py ...`, `Consult .cc-rsg/skill/references/outline-tables.md`). Those paths only resolve if the bundle is copied next to the target repo's working directory. Copy this skill's `scripts/`, `references/`, `templates/`, and `agents/` directories into `.cc-rsg/skill/` once, at the start of Phase 0:
     ```bash
     mkdir -p .cc-rsg/skill
     cp -r <skill_dir>/{scripts,references,templates,agents} .cc-rsg/skill/
     ```
     `<skill_dir>` is the directory that contains this SKILL.md (the installed skill root). This copy is idempotent — re-running it on resume simply refreshes the staged bundle. Skip nothing: until this step runs, the very first script call of every phase fails with "No such file or directory".
   - If an existing `.cc-rsg/state.json` is found, branch to resume mode (see "State management and resume" below). Resume mode still re-stages the bundle (the step above) before continuing, in case the skill was reinstalled or upgraded.

3. **Output language selection**

   - **This step alone is presented bilingually** because the user's preferred language has not yet been confirmed. The question body and choice labels appear in both English and Japanese.
   - Use `AskUserQuestion` with:
     - Question: `Select the output language for the dialogue and the generated specs / 対話と生成ドキュメントの出力言語を選択してください`
     - Choices (**fixed order; English is the default**):
       1. `English`
       2. `日本語 (Japanese)`
     - `allow_multiple = false`, `allow_free_text = false`
   - Map the selected label to `output_language`: `English` → `"en"`, `日本語 (Japanese)` → `"ja"`. Persistence to `goal.json` happens together with the other answers in Step 5.
   - **Default policy (English-base)**: when the user submits without changing the highlighted choice, treat the answer as `"en"`. This matches the cc-rsg upstream policy.
   - **Parent-harness hint precedence**: when the parent harness injects a `userUiLanguage` hint into the initial prompt, use that hint to decide which choice is **pre-highlighted** (`en` highlights `English`; `ja` highlights `日本語 (Japanese)`). The hint never overrides the user's explicit selection. Priority order:
     1. The user's explicit click in this step (highest)
     2. `userUiLanguage` hint passed from the parent harness's initial prompt
     3. Hard default `"en"` (lowest)
   - **All natural-language output from Step 4 onward** — `AskUserQuestion` bodies and choices, confirmation summaries, chapter titles, generated spec body, `questions.json` body text, etc. — is rendered in the language selected here (see Design Principle #11).
   - **Resume mode**: when `.cc-rsg/goal.json` already exists, read the persisted `output_language` and skip this step entirely.

4. **Run the 6 goal-definition questions**
   - Use `AskUserQuestion` to ask the following 6 questions in sequence. **Question bodies, choice labels, and free-form-input placeholders are all rendered in the `output_language` selected in Step 3.** The choice labels below are shown when `output_language == "en"`; the agent dynamically translates them when `output_language == "ja"` (enum values such as `primary_reader: "maintenance_developer"` stay as language-independent English enums in `goal.json`). Each question is choice-based first with a free-form field as a fallback.
   - **Question-text quality contract (applies to every `AskUserQuestion` call in every phase, especially when translating into `output_language == "ja"`)**:
     1. **NEVER JSON-escape characters.** Emit raw UTF-8 only. If you find yourself writing `あ` or any other `\uXXXX` form inside the `question` or `choices` strings, that is a defect — decode it before emitting. A user who sees `次の中` on screen will reject the run.
     2. **Use only standard Japanese kanji.** Stay within JIS Level 1 / 常用漢字 / 人名用漢字. Do NOT mix in Chinese-simplified variants (e.g. `优 (Chinese)` ← write `優 (Japanese)`; `寸叧` is not a valid word — `対応` is). The runtime has no automatic fix for these; they reach the user verbatim.
     3. **Self-check before emit.** After translating a label to Japanese, mentally re-read it. If any kanji feels unusual for the surrounding context — e.g. `妊` (pregnancy) appearing in `業務妊当性` instead of `妥` (`妥当性` = validity) — regenerate the entire label. Common confusion pairs to double-check: 妥/妊, 暑/署, 復/複, 製/制, 即/則.
     4. **No invented characters / kanji.** If you are unsure of a kanji, use kana (e.g. write `たいおう` instead of `寸叧`). Hiragana is always safer than a wrong kanji.
     5. These rules apply to **`AskUserQuestion` bodies and choices**, but they do NOT relax the rule that JSON keys, enum values, file names, and machine-readable markers stay English (see Principle #11).

   **Q1. Who is the primary reader of the spec?**
   - Maintenance developer
   - Delivery customer
   - SME (subject-matter expert)
   - Regulator
   - Other (free-form)

   **Q2. What will the reader do after reading the spec?**
   - Code change
   - Approval decision
   - Audit
   - Learning
   - Other (free-form)

   **Q3. What level of granularity is preferred?**
   - High-level overview
   - Medium
   - Detailed
   - Other (free-form)

   **Q4. Which perspectives should be emphasised? (multi-select)**
   - Functional correctness
   - Business validity
   - Security
   - Operability
   - Performance
   - Other (free-form)

   **Q5. What about existing documentation?**
   - No existing docs
   - Existing docs / want to update
   - Existing docs / want to coexist
   - Existing docs / want to retire
   - Other (free-form)

   **Q6. Where should the spec documents be written?**
   - Default (.cc-rsg)
   - Custom path (free-form, relative to project root)

   - Q6 specifies the **spec output directory** for the final deliverables. Default is `.cc-rsg` (same as the state directory). When a custom path like `docs/specs` is given, **final spec files go directly to `{output_dir}/`** (e.g. `docs/specs/`), while **draft files always stay at `.cc-rsg/drafts/`** (intermediate artifacts). State files (goal.json, state.json, trace.json, etc.) remain in `.cc-rsg/` regardless.
   - In resume mode, read `goal.json.output_dir` and skip this question.

5. **Extract `user_custom_deliverables` from `free_text_notes`**
   - **Mandatory.** Before persisting `goal.json`, scan `free_text_notes` for explicit deliverable filenames using the regex `\b[a-z][a-z0-9_-]*\.md\b` (case-insensitive). De-duplicate and exclude any name matching the chapter-naming regex `^(0\d|[1-9]\d)-[a-z0-9-]+\.md$` or the reserved names `00-metadata.md` / `99-unresolved.md` / `traceability.md` (those are handled by the standard chapter pipeline).
   - The remaining names are **user-promised custom deliverables**. They MUST appear in `{output_dir}/` at Phase 6 completion; missing any of them is a hard failure (check 12 in `coverage-check.py`).
   - Example: `free_text_notes = "顧客向けドキュメント。Mermaid図による視覚的説明と、紙芝居的な manual.md を含める。"` → `user_custom_deliverables = ["manual.md"]`.
   - If the free-form text is empty or contains no `*.md` references, the list is `[]`.
   - User-custom files are **exempt from comprehensive per-chapter quality gates** (the 200-lines / 10-REFs / Mermaid / Sources Read minimums) because their quality bar is the user's intent recorded in `free_text_notes`, not the source-derived spec-chapter bar. Only existence + non-empty body is enforced.

6. **Persist to `goal.json`**
   - Save the language choice from Step 3, the 6 answers from Step 4, and the `user_custom_deliverables` array from Step 5 as a structured `goal.json` under `.cc-rsg/`. Schema:

   ```json
   {
     "output_language": "en",
     "output_dir": ".cc-rsg",
     "primary_reader": "maintenance_developer",
     "reader_action": "code_change",
     "granularity": "medium",
     "perspectives": ["functional_correctness", "operational"],
     "existing_docs": "none",
     "free_text_notes": "...",
     "user_custom_deliverables": ["manual.md"]
   }
   ```
   - `output_language` is required and must be `"en"` or `"ja"`. Other enum fields (`primary_reader`, `reader_action`, `granularity`, `perspectives`, `existing_docs`) are language-independent English enums (localized only at display time using `output_language`).
   - `output_dir` specifies the final spec output directory (default `.cc-rsg`). Final spec files go to `{output_dir}/`. Drafts always stay at `.cc-rsg/drafts/`. State files remain in `.cc-rsg/`.
   - `user_custom_deliverables` is a (possibly empty) array of file names that the user explicitly requested in `free_text_notes`. These bypass the chapter-naming regex; their filenames are preserved verbatim. Phase 2 adds them to `wbs.json` as `kind: "user_custom"` chapters; Phase 6 verifies every one of them exists in `{output_dir}/`.

7. **Phase 0 complete**
   - Update `state.json` and proceed to Phase 1.

### Phase-specific cautions
- Minimise the user's burden by leading with choice-based UI; never force the user to type the same thing twice.
- Treat the free-form field as a "none of the above" safety net; it is unnecessary when the user picked one of the choices.
- The goal influences every later phase, so do not skip summarising the answers and asking the user to confirm. **The confirmation summary is also rendered in `output_language`.**
- The output-language selection (Step 3) is **bilingual only for that first dialogue**. From Step 4 on, use the confirmed language exclusively. If the user requests a language switch mid-flight, update `goal.json.output_language` and individually check whether existing `drafts/` and `questions.json` bodies need to be re-rendered.

---
