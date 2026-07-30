## Phase 1: Recon & Template

### Purpose
Get a rough mental model of the codebase via a shallow reconnaissance, then pick an appropriate spec template. At the end of Phase 1, register the high-level questions into the Question Bank.

### Procedure

1. **Run the shallow reconnaissance**
   Read the following and summarise them in `recon-report.md`:
   - File tree structure (limited to depth 3-4, noise excluded)
   - Package-manager files (`package.json`, `composer.json`, `requirements.txt`, `pom.xml`, `build.gradle`, etc.)
   - Entry-point candidates (`main` functions, `index` files, routing definitions, etc.)
   - Existing documentation (`README.md`, `docs/`, `wiki`, etc.)
   - Build/deploy configuration (`Dockerfile`, `Makefile`, CI configs, etc.)
   - Language mix and estimated line counts

2. **Present template candidates**
   - Consult `references/template-catalog.md` and propose candidates suitable for the target codebase.
   - Use `AskUserQuestion` to present the candidates to the user.

   **Example template choices**:
   - I have my own template (specify path)
   - Web application spec (`templates/web-app.md`)
   - Batch processing system spec (`templates/batch-system.md`)
   - API service spec (`templates/api-service.md`)
   - Library/SDK spec (`templates/library-sdk.md`)
   - Use whichever Claude recommends from reconnaissance

3. **Adjust the chosen template**
   - If the user accepts Claude's recommendation, display the chapter outline and ask "Are there chapters to add, remove, or rename?".
   - Reflect any additions/removals.

4. **Persist template name to goal.json**
   - Write the chosen template name to `goal.json` under the `template` field. This allows downstream tools (e.g. `coverage-check.py`) to adjust their behaviour based on the template type.
   - Use the template identifier from the selection (e.g. `"web-app"`, `"batch-system"`, `"api-service"`, `"library-sdk"`).
   - If the user brought their own template, write `"custom"`.
   - Update the existing `goal.json` file in-place:
     ```bash
     python3 -c "
     import json
     with open('.specback/goal.json') as f:
         g = json.load(f)
     g['template'] = 'library-sdk'
     with open('.specback/goal.json', 'w') as f:
         json.dump(g, f, indent=2, ensure_ascii=False)
         f.write('\n')
     "
     ```

5. **Register high-level questions**
   - Add the fundamental questions surfaced during reconnaissance (questions that block big-picture understanding) into `questions.json`.
   - Examples:
     - What business problem is this system trying to solve?
     - How wide is the scope (which module inside the monorepo)?
     - When existing docs disagree with the code, which is authoritative?
   - See "Question Bank operation" below for the structure used at registration.

6. **🆕 depth-mode decision (scale-based)**
   - Record the **total file count** observed during reconnaissance at the top of `recon-report.md`. Persist as `total_files` in `.specback/state.json`.
   - **If file count > 200**, ask the user with `AskUserQuestion` to choose a **depth mode**:
     - `comprehensive`: classic behaviour. All chapters detailed, full MECE, full REFs. **Recommended only when exhaustive coverage is required (audit, regulatory).** Takes hours to days.
     - `outline` (**recommended default**): each level's entities are **listed exhaustively in tables** + Mermaid diagrams + a "deep-dive candidates" list at the end of each table. Details are produced on-demand in dialogue after Phase 6. **Best for typical use.**
     - `interactive`: same flow as outline, plus continued deep-dive acceptance after Phase 6 completes. **Use when a team will continue referencing the spec.**
   - **If file count ≤ 200**, default to `comprehensive` automatically (no question). The user may still override.
   - Persist the result to `.specback/goal.json` as `depth_mode: "comprehensive" | "outline" | "interactive"`. Phases 2 / 3 / 4 / 6 branch on this value.
   - Question wording example:
     > The target codebase is large (N files / X lines). Choose a depth mode for the spec.
     > (Overview-only → deep-dive items of interest later, in practice, is recommended.)

7. **Phase 1 complete**
   - Update `state.json` and proceed to Phase 2.

### Phase-specific cautions
- Reconnaissance follows the principle "shallow but wide". Detailed logic understanding is deferred to Phase 3.
- Without noise exclusion (`node_modules`, `vendor`, `.git`, etc.) the output explodes.
- If the user brings their own template, you may point out "Claude's recommendation differs", but the decision is the user's.

---
