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
   - 🆕 **Tree-sitter availability**: Check whether `tree-sitter` is installed (`python -c "import tree_sitter"`). Record as `tree_sitter_available: true/false` in recon-report.md. When unavailable, note that some language extractors will fall back to file-level granularity.

2. **Present template candidates**
   - Consult `references/template-catalog.md` and propose candidates suitable for the target codebase.
   - Use `AskUserQuestion` to present the candidates to the user.

   **Example template choices**:
   - I have my own template (specify path)
   - Web application spec (`templates/web-app.md`)
   - Batch processing system spec (`templates/batch-system.md`)
   - API service spec (`templates/api-service.md`)
   - Library/SDK spec (`templates/library-sdk.md`)
   - Use whichever the agent recommends from reconnaissance

3. **Adjust the chosen template**
   - If the user accepts the recommended template, display the chapter outline and ask "Are there chapters to add, remove, or rename?".
   - Reflect any additions/removals.

4. **🆕 Monorepo detection and scope setup**

   After the template is finalised, check whether the target codebase is a monorepo containing multiple independent systems.

   **Detection heuristics** (check in order):
   1. **Workspace manifests**: Does `pnpm-workspace.yaml`, `lerna.json`, `turbo.json`, `nx.json`, or `package.json.workspaces` exist?
   2. **Multi-service directories**: Do `services/`, `apps/`, or `packages/` directories contain independent package manifests (`package.json`, `setup.py`, `go.mod`, `composer.json`)?
   3. **Multiple entrypoints**: Are there multiple `main` files, `Dockerfile`s, or deployment configs across different subdirectories?

   If ANY heuristic matches, use `AskUserQuestion` to present the option:

   ```
   This repository appears to contain [N] independent systems/components.
   How would you like to generate specs?

   1. Individual specs per system (recommended for monorepos)
      → Each system gets its own state dir and spec output
   2. One combined spec for the whole repo
      → All systems merged into a single document
   3. Select specific systems only
      → Free-form: list the systems you want
   ```

   - If the user chooses option 1 or 3, set `goal.multi_scope = true`.
   - **Auto-detect scope boundaries**: For each candidate system, determine its root directory and assign a short `name` slug (derived from the directory name, e.g. `auth`, `payment`, `frontend`). Use the following rules:
     - `services/{name}/` or `apps/{name}/` → `{name}`
     - `packages/{name}/` with a package manifest → `{name}`
     - Top-level directories with their own `Dockerfile` → `{dir_name}`
   - Populate `goal.scopes = [{"name": "auth", "root": "services/auth"}, ...]`
   - **When option 3** (select specific systems): parse the user's free-form input, match each entry against detected systems, and include only the matched ones. If a name doesn't match, ask for clarification.
   - **Confirmation**: Show the final scope list and ask for confirmation:
     ```
     Scopes to generate:
       auth      → services/auth/    (Web application spec)
       payment   → services/payment/ (API service spec)
       frontend  → apps/frontend/    (Library/SDK spec)

     OK? (yes / redo)
     ```
   - Each scope may have a **different template** (detected independently in Phase 2).

   **State isolation**: When `multi_scope == true`:
   - Each scope uses its own state directory: `.specback-{name}/` (e.g. `.specback-auth/`)
   - `.skill-path` is shared (symlink or copy): `ln -sf $(cat .specback/.skill-path) .specback-auth/.skill-path`
   - The project root `.specback/` stores only the shared `goal.json` and `state.json` (which tracks `current_scope` across phases).
   - Script invocations use `--specback-dir .specback-{name}`.

   When `multi_scope == false` (default), proceed with the original `.specback/` flow unchanged.

5. **Register high-level questions**
   - Add the fundamental questions surfaced during reconnaissance (questions that block big-picture understanding) into `questions.json`.
   - Examples:
     - What business problem is this system trying to solve?
     - How wide is the scope (which module inside the monorepo)?
     - When existing docs disagree with the code, which is authoritative?
   - See "Question Bank operation" below for the structure used at registration.

6. **🆕 depth-mode & tone decision (scale-based)**
   - Record the **total file count** and **estimated code lines** observed during reconnaissance at the top of `recon-report.md`. Persist as `total_files` and `total_lines` in `.specback/state.json`.
   - **If total_lines > 500**, ask the user with `AskUserQuestion` to choose a **depth mode**:
     - `comprehensive`: full chapter set (all chapters from the template). **Recommended only when exhaustive coverage is required (audit, regulatory).** Estimated 2–4 hours for most projects (Phase 3 parallel investigation scales with concurrency).
     - `outline` (**recommended default**): minimal chapters — tables + Mermaid diagrams + deep-dive candidate list. Details produced on-demand in dialogue after Phase 6. **Best for typical use.**
     - `interactive`: same flow as outline, plus continued deep-dive acceptance after Phase 6 completes. **Use when a team will continue referencing the spec.**
   - **If total_lines ≤ 500**, default to `outline` automatically (no question for depth_mode). The user may still override.
   - Then, ask the user to choose a **writing tone** (regardless of depth_mode):
     - `concise` (**default**): compact. Facts, REFs, and essential explanations only. No padding prose.
     - `thorough`: more detailed explanations. Include background, rationale, and alternatives where relevant.
   - Persist both to `.specback/goal.json` as:
     - `depth_mode: "comprehensive" | "outline" | "interactive"`
     - `tone: "concise" | "thorough"`
   - Phases 2 / 3 / 4 / 6 branch on these values.
   - Question wording example:
     > The target codebase has ~{total_lines} lines across ~{total_files} files. Choose a depth mode for the spec.
     > (Outline → deep-dive items of interest later, in practice, is recommended.)
     >
     > Writing tone:
     > → concise (compact, facts + REFs only) [default]
     > → thorough (detailed explanations)

7. **Phase 1 complete**
   - Update `state.json` and proceed to Phase 2.

### Phase-specific cautions
- Reconnaissance follows the principle "shallow but wide". Detailed logic understanding is deferred to Phase 3.
- Without noise exclusion (`node_modules`, `vendor`, `.git`, etc.) the output explodes.
- If the user brings their own template, you may point out the recommended template differs, but the decision is the user's.

---
