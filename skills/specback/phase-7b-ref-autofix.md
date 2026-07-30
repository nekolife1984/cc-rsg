## Phase 7b: REF Auto-Fix

### Purpose

Auto-correct `[REF: path:line]` markers in spec files that have become stale due to source code changes. Run `scripts/fix-refs.py` to parse `git diff -U0` hunk headers and update line numbers.

### Procedure

1. **Run fix-refs.py** (default: dry-run)
   ```bash
   python .specback/skill/scripts/fix-refs.py \
     --specback-dir .specback \
     --output-dir {output_dir}
   ```

2. **Review the proposed changes**

3. **Apply corrections**
   ```bash
   python .specback/skill/scripts/fix-refs.py \
     --specback-dir .specback \
     --output-dir {output_dir} \
     --apply
   ```

4. **CI check mode**
   ```bash
   python .specback/skill/scripts/fix-refs.py \
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
python .specback/skill/scripts/snapshot-hashes.py --specback-dir .specback
```

This creates `.specback/source-hashes.json` which `detect-drift.py --mode hash` uses as its comparison baseline.

---
