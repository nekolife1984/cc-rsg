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

## Release Process

```bash
# Semver: MAJOR.MINOR.PATCH
git tag -a v0.8.0 -m "v0.8.0 — description"
git push origin v0.8.0

# Pre-release: v0.8.0-alpha.1, v0.8.0-beta.1
```

Tags are created from `main` after a PR merge. Update `CHANGELOG.md` with each release.

## Hotfix Flow

For urgent fixes on a released version:

```bash
git checkout -b fix/hotfix-crash main
# fix → commit → PR → squash merge → main
git tag -a v0.8.1 -m "v0.8.1 — crash fix"
git push origin v0.8.1
```

## CI Gates (Planned)

| Check | Required | When |
|-------|----------|------|
| `pytest tests/ -q` | ✅ | On PR |
| `mypy . --strict` | ✅ | On PR (if Python) |
| Trace/drift gate | ✅ | On PR (if specbridge enabled) |
| CHANGELOG updated | 📋 Manual | Before merge |
| Branch strategy doc updated | 📋 Manual | When strategy changes |
