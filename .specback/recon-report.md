# Recon Report — specback (self-targeting)

> Generated at Phase 1 of specback pipeline.
> Output language: Japanese

## Target Overview

| Item | Value |
|------|-------|
| Project | specback — Reverse Spec Generator |
| Root | `/Users/genya/GitHub/specback` |
| Total files | 85 (excluding .git, node_modules) |
| Depth mode | comprehensive (auto-selected: ≤200 files) |
| Template | Library/SDK Spec |

## Language Mix

- **Markdown**: 77 files (phase definitions, templates, documentation, references)
- **Python**: ~50 files (scripts, source_map_v2, tests)
- **Shell**: 5 files (install.sh, install-hooks.sh, merge-pr.sh, pre-commit, pre-push)
- **PowerShell**: 1 file (install.ps1)
- **JSON**: 3 files (package-lock.json, package.json, .gitignore)
- **YAML**: 1 file (.github/workflows/ci.yml)
- **Other**: LICENSE, .gitignore

## File Tree (depth 3, noise excluded)

```
specback/
├── .githooks/
│   ├── pre-commit
│   └── pre-push
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── pull_request_template.md
│   └── workflows/
│       └── ci.yml
├── .opencode/
│   ├── package.json
│   └── skills/specback/    ← primary skill location (OpenCode)
├── docs/
│   ├── en/ (4 files: branching, commit, PR, release)
│   └── ja/ (4 files, same content)
├── scripts/
│   ├── install-hooks.sh
│   └── merge-pr.sh
├── skills/specback/          ← also present for manual install
│   ├── SKILL.md, phase-*.md, question-bank.md, subagent-behavior.md, state-management.md
│   ├── agents/chapter-investigator.md
│   ├── references/ (6 files)
│   ├── templates/ (4)
│   ├── variants/B/ (3)
│   └── scripts/ (11 Python scripts + source_map_v2/ with 14 extractors + tests)
├── install.sh
├── install.ps1
├── README.md (bilingual)
├── CHANGELOG.md
├── CONTRIBUTING.md
├── AGENTS.md
└── LICENSE (MIT)
```

## Entry Points

| Type | Path | Description |
|------|------|-------------|
| Skill entry | `SKILL.md` | Agent skill definition (~90 lines, lightweight index) |
| Installer (Unix) | `install.sh` | Interactive installer for 6 agent types |
| Installer (Win) | `install.ps1` | PowerShell variant |
| Git hooks | `.githooks/pre-commit` | Secrets scan + test existence check |
| Git hooks | `.githooks/pre-push` | Block direct pushes to main |
| CI | `.github/workflows/ci.yml` | pytest + mypy + gitleaks on every PR |

## Key Architectural Observations

1. **Dual-location structure**: `skills/specback/` exists at both `.opencode/skills/specback/` (OpenCode plugin) and `skills/specback/` (manual install source). The `.opencode/` copy is the active install; the root `skills/` is the distribution source.
2. **Phase-based state machine**: 7 primary phases + 3 auxiliary (6.5, 7b, 7c), each as a standalone `.md` file.
3. **Python scripts as backend**: source extraction (`source-map.py`, `source_map_v2/`), traceability, coverage check, drift detection.
4. **No application framework**: Pure documentation + Python scripts. No web server, no API.
5. **Comprehensive test suite**: source_map_v2 has per-language test files; scripts/ has dedicated test files.
