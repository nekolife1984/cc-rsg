# Branching Strategy — GitHub Flow

## Overview

This project uses **GitHub Flow** — a lightweight, branch-based workflow with a single permanent branch (`main`) and short-lived feature branches.

> GitHub Flow is chosen because:
> - Single developer — minimal ceremony
> - Upstream (`daishir0/cc-rsg`) sync is straightforward via dedicated branch prefix
> - Aligns with existing conventions (PR mandatory, squash merge, one-change-one-commit)

## Permanent Branches

| Branch | Protection | Purpose |
|--------|-----------|---------|
| `main` | ✅ No direct push | Single source of truth. All changes arrive via PR. |

## Branch Naming Conventions

All work branches branch from `main` and are deleted after merge.

| Prefix | Example | When to use |
|--------|---------|-------------|
| `feat/<kebab-case>` | `feat/add-plantuml-template` | New feature or enhancement |
| `fix/<kebab-case>` | `fix/detect-py-encoding` | Bug fix |
| `chore/<kebab-case>` | `chore/update-deps` | CI, maintenance, refactoring, dependencies |
| `docs/<kebab-case>` | `docs/branching-strategy` | Documentation only |
| `upstream/<kebab-case>` | `upstream/merge-v0.8.0` | Sync from `daishir0/cc-rsg` upstream |

## PR Lifecycle

```
main → feat/xxx → commits → open PR → CI (pytest + mypy + trace gates)
                                    ↓
                          All green? → squash merge to main → delete branch
                                    ↓
                          Failed? → fix & push → CI re-runs
```

### Rules

1. **Branch from the latest `main`** — rebase if behind
2. **Short-lived branches** — hours to days, never weeks
3. **One logical change per branch** — corresponds to one conventional commit
4. **Squash merge** — keeps `main` history linear and clean
5. **Conventional commit message on merge** — `feat: description (#N)`
6. **Delete branch after merge** — both remote and local

### Direct Push Exceptions

| Change type | Direct push? | Condition |
|-------------|-------------|-----------|
| Typo / comment fix | ✅ Allowed | CI passes |
| CI config tweak | ✅ Allowed | Verified working |
| Minor docs | ✅ Allowed | No spec/content change |
| Source code / tests / features | ❌ **PR required** | Must pass CI + trace gates |

For this project, **prefer PR for everything** — it forces a review pass even as a single developer.

## Upstream Sync (daishir0/cc-rsg)

When the upstream `daishir0/cc-rsg` has updates worth merging:

```bash
# Add upstream remote (one-time)
git remote add upstream https://github.com/daishir0/cc-rsg.git

# Create sync branch
git checkout main
git pull origin main
git checkout -b upstream/merge-v0.8.0
git pull upstream main

# Resolve conflicts if any, then
git push origin upstream/merge-v0.8.0
# → Open PR → squash merge → main
```

## CI Gates

GitHub Actions (`.github/workflows/ci.yml`) runs on every PR. See [03-pr-review-process.md](03-pr-review-process.md) for details.

## Release Process

See [04-release-process.md](04-release-process.md) for the full release procedure including versioning, CHANGELOG, and Zenodo updates.

Quick tag command:

```bash
git tag -a v0.8.0 -m "v0.8.0 — description"
git push origin v0.8.0
```

## Related Documents

| Document | Description |
|----------|-------------|
| [02-commit-conventions.md](02-commit-conventions.md) | Conventional Commits format, one-change-one-commit rule |
| [03-pr-review-process.md](03-pr-review-process.md) | PR lifecycle, template, reviewer checklist, squash merge |
| [04-release-process.md](04-release-process.md) | Versioning, CHANGELOG, Roadmap, Zenodo, release checklist |
