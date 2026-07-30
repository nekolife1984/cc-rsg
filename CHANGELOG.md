# Changelog

All notable changes to the specback project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Kotlin extractor for source_map_v2 ([#37])
- C, C++, Dart, Swift extractors for source_map_v2 ([#42])
- Rust extractor for source_map_v2 ([#52])
- Knowledge Graph (JSON-LD) export from source-map.json and trace.json ([#53])
- GitHub Actions CI workflow with pytest, mypy, and smoke import checks ([#32])
- `--agent` / `--level` CLI flags for install.sh and install.ps1 ([#35])
- Phase 7c ChangeSpec — change specification generation option ([#14])
- Phase 7 Drift Detection + Phase 7b REF Auto-Fix with hash mode ([#12])
- Resume phase → file loading instructions
- SKILL.md split into per-phase files with lightweight index ([#18])
- Multi-agent skill installer (install.sh / install.ps1)
- Pre-commit hook enforcing tests for new scripts ([#13])
- Phase 0: skill path recording via `.specback/.skill-path` (replaces bundle staging copy)
- Customizable output directory for specification documents ([#10])
- Pre-push hook blocking direct pushes to main ([#1])
- GitHub Flow branching strategy docs (EN + JA)
- Japanese-localized PR/Issue templates ([#2])
- Python dependency management via requirements.txt with `--install-deps` installer option ([#55])

### Changed

- Repository renamed from `cc-rsg` to `specback` ([#57])
- source_map_v2 role-typing connected to Phase 2 inventory.json ([#36])
- Drafts always go to `.cc-rsg/drafts/` regardless of output_dir
- Final spec output path simplified (no `/final/` subdirectory)
- Kept `.cc-rsg/final/` as default path; custom paths go direct
- Removed Claude Code-specific wording from docs and skill
- Removed Versioning/changelog and License sections from SKILL.md (moved to separate files)
- Updated PR template references (CHANGELOG.md / daishir0) ([#51])

### Fixed

- Kotlin extractor annotation + Ktor path bugs ([#38])
- Redundant separator (`---`) at end of README ([#11])

### Docs

- New language/framework addition guide in CONTRIBUTING.md ([#34])
- Commit conventions, PR review, and release process docs added to docs/ ([#33])
- README: Branching strategy link and directory structure update

## [v0.7.0] - 2026-06-30

### Added

- `scripts/source_map_v2/` — role-typed, framework-aware, tree-sitter-based mechanical source map (schema 0.2.0)
- Per-language extractors for Python, TS/JS, Ruby/Rails, PHP, Java, C#, Go, SQL, COBOL
- Framework detection for source_map_v2
- Loud warnings instead of silent drops for unsupported languages
- Coexistence with v1 `source-map.py`

### Docs

- README: v0.7.0 status, Roadmap update, source_map_v2 directory structure

## [v0.6.0] - 2026-06-29

### Added

- Phase 0 bundle staging into `.specback/skill/`
- [REF:] placeholder consistency (no leading `L`)
- Variants/B — Context Optimization mode B reference variant

### Fixed

- Ruby top-level method extraction in source-map scripts
- Sources Read counter fix

## [v0.5.0] - 2026-06-15

### Added

- Mermaid styling contract (host-themed palette)
- `user_custom_deliverables` enforcement
- Strict `[REF: path:line]` format enforcement
- Phase 5 skip prevention
- Intent-vs-delivery audit
- Context Optimization mode B variant (`variants/B/`)

### Docs

- README: v0.5.0 status, Roadmap update, variants/ directory structure

## [v0.4.1] - 2026-06-11

### Changed

- Neutralized runtime-specific terminology for standalone use

## [v0.4.0] - 2026-06-09

### Added

- English-base migration of the entire skill bundle
- Bilingual output via `output_language` option
- English-first README structure
- English-base templates, references, scripts, and agent configurations

## [v0.3.0] - 2026-06-08

### Added

- Depth modes: comprehensive / outline / interactive
- Phase 6.5 interactive deep-dive mode
- `outline-tables.md` and outline-mode validations

## [v0.2.0] - 2026-06-06

### Added

- Chapter file naming convention enforcement
- Required files (3-file mandatory structure) validation
- Per-chapter sub-agent delegation
- Phase 4 loopback verification
- Granularity rules for spec generation
- Rails framework catalog
- Output-language selection
- French version support
- Framework-specific inventory units: Next.js, Expo, Flask, FastAPI
- Multi-language README (English + French added)

### Infrastructure

- Initial agent scripts and Phase 3/4/5 hardening
- Verification script with naming/required-file checks
- Project renamed: Claude Code Reverse Spec Generator

## [v0.1.0] - 2026-05-01

### Added

- Initial release of the Reverse Spec Generator (cc-rsg)
- Core Phase 1–7 pipeline structure
- Basic source-map extraction (v1)
- Question Bank (FAQ-based dialog refinement)
- Template-based specification document generation

[#1]: https://github.com/nekolife1984/specback/pull/1
[#2]: https://github.com/nekolife1984/specback/pull/2
[#10]: https://github.com/nekolife1984/specback/pull/10
[#11]: https://github.com/nekolife1984/specback/pull/11
[#12]: https://github.com/nekolife1984/specback/pull/12
[#13]: https://github.com/nekolife1984/specback/pull/13
[#14]: https://github.com/nekolife1984/specback/pull/14
[#18]: https://github.com/nekolife1984/specback/pull/18
[#32]: https://github.com/nekolife1984/specback/pull/32
[#33]: https://github.com/nekolife1984/specback/pull/33
[#34]: https://github.com/nekolife1984/specback/pull/34
[#35]: https://github.com/nekolife1984/specback/pull/35
[#36]: https://github.com/nekolife1984/specback/pull/36
[#37]: https://github.com/nekolife1984/specback/pull/37
[#38]: https://github.com/nekolife1984/specback/pull/38
[#42]: https://github.com/nekolife1984/specback/pull/42
[#51]: https://github.com/nekolife1984/specback/pull/51
[#52]: https://github.com/nekolife1984/specback/pull/52
[#53]: https://github.com/nekolife1984/specback/pull/53
[#55]: https://github.com/nekolife1984/specback/pull/55
[#57]: https://github.com/nekolife1984/specback/pull/57
