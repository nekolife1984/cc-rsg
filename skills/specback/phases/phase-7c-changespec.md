## Phase 7c: ChangeSpec

### Purpose

Generate a **human-readable change specification document** (`change-spec.md`) from source code changes. Unlike the raw diff, ChangeSpec explains *what changed, why, and what it means* in natural language.

### 🆕 Multi-scope execution

When `goal.multi_scope == true`, iterate over each scope and run the procedure for each:
1. Read `goal.scopes[]`.
2. For each scope, set `SPECBACK_DIR = ".specback-{scope.name}"` and run the procedure below.
3. Each scope generates its own `change-spec.md` under `{output_dir}/{scope.name}/`.

When `goal.multi_scope == false` (default), run the procedure once with `.specback/`.

### Prerequisites

- Phase 7 drift report must exist (`drift-report.md` / `drift-report.json`)
- `source-map.json` and `trace.json` accessible
- `git` (for git mode) or `source-hashes.json` (for hash mode)

### Procedure

1. **Confirm with user** (AskUserQuestion):
   - "ChangeSpec can generate a human-readable change specification. Run it?"
   - Choices: Yes / No
   - If No, skip Phase 7c entirely.

2. **Run change-spec.py** (mechanical extraction):
   ```bash
   python "$(cat .specback/.skill-path)/scripts/change-spec.py" \
     --specback-dir .specback \
     --output-dir {output_dir}
   ```
   This produces `{output_dir}/change-spec.json` — structured facts only, no interpretation.

3. **Generate change-spec.md** (AI interpretation):
   - Read `{output_dir}/change-spec.json`
   - Read `{output_dir}/drift-report.json` for context
   - For each changed file, write an explanation covering:
     - **Before/After code** (git mode) or **current code** (hash mode)
     - **Intent**: why the change was made (from naming, comments, diff context)
     - **Impact**: linked spec sections from trace.json
     - **Breaking changes**: API changes clearly flagged
   - Output the result as `{output_dir}/change-spec.md`

4. **Display the output** to the user as a completion summary.

### Usage examples

```bash
# Git mode (default)
python "$(cat .specback/.skill-path)/scripts/change-spec.py" --specback-dir .specback

# Hash mode
python "$(cat .specback/.skill-path)/scripts/change-spec.py" --specback-dir .specback --mode hash

# Pipe diff
git diff -U5 main...HEAD | python "$(cat .specback/.skill-path)/scripts/change-spec.py" --diff -
```

### Output

- `{output_dir}/change-spec.json` — structured change facts (mechanical)
- `{output_dir}/change-spec.md` — human-readable change specification (AI-generated)

### Quality standards

See `references/change-specification.md` for the full design document.

---
