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

6. **🆕 depth-mode decision (scale-based)**
   - Record the **total file count** observed during reconnaissance at the top of `recon-report.md`. Persist as `total_files` in `.specback/state.json`.
   - **If file count > 200**, ask the user with `AskUserQuestion` to choose a **depth mode**:
     - `comprehensive`: classic behaviour. All chapters detailed, full MECE, full REFs. **Recommended only when exhaustive coverage is required (audit, regulatory).** Estimated 2–4 hours for most projects (Phase 3 parallel investigation scales with concurrency).
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
