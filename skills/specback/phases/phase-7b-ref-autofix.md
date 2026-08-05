## Phase 7b: REF Auto-Fix

### Purpose

Auto-correct `<!-- REF: path:line -->` markers in spec files that have become stale due to source code changes. Run `scripts/fix-refs.py` to parse `git diff -U0` hunk headers and update line numbers.

### 🆕 Multi-scope execution

When `goal.multi_scope == true`, iterate over each scope and run the procedure for each:
1. Read `goal.scopes[]`.
2. For each scope, set `SPECBACK_DIR = ".specback-{scope.name}"` and run the procedure below.
3. The `--output-dir` should include the scope name: `{output_dir}/{scope.name}` or the combined output.

When `goal.multi_scope == false` (default), run the procedure once with `.specback/`.

### Procedure

1. **Run fix-refs.py** (default: dry-run)
   ```bash
   python "$(cat .specback/.skill-path)/scripts/fix-refs.py" \
     --specback-dir .specback \
     --output-dir {output_dir}
   ```

2. **Review the proposed changes**

3. **Apply corrections**
   ```bash
   python "$(cat .specback/.skill-path)/scripts/fix-refs.py" \
     --specback-dir .specback \
     --output-dir {output_dir} \
     --apply
   ```

4. **CI check mode**
   ```bash
   python "$(cat .specback/.skill-path)/scripts/fix-refs.py" \
     --specback-dir .specback \
     --output-dir {output_dir} \
     --check
   ```

### Safety

- **Dry-run by default**: no files are modified until `--apply` is passed
- **Backups**: originals saved to `.specback/backups/<file>.bak` before modification
- **Check mode**: exits with code 1 if orphaned REFs remain after correction

### Snapshot management (hash mode)

For non-Git projects, generate a hash snapshot after Phase 6 completes:

```bash
python "$(cat .specback/.skill-path)/scripts/snapshot-hashes.py" --specback-dir .specback
```

### Phase-specific cautions
- Dry-run by default: review proposed changes before applying with `--apply`.
- Backups are saved to `.specback/backups/<file>.bak` — verify they exist before applying.
- REF corrections shift line numbers in the spec files. After applying, re-run `coverage-check.py` to verify structural integrity.
- Multi-scope: run per scope — shared `.skill-path` but separate `SPECBACK_DIR`.

---
