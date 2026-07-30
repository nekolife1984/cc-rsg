# Release Process

## Versioning

This project follows **Semantic Versioning** (`MAJOR.MINOR.PATCH`):

| Bump | When | Example |
|------|------|---------|
| **MAJOR** | Breaking changes, stable release (v1.0) | `v0.8.0` → `v1.0.0` |
| **MINOR** | New features, non-breaking enhancements | `v0.7.0` → `v0.8.0` |
| **PATCH** | Bug fixes, hotfixes | `v0.8.0` → `v0.8.1` |

Pre-release suffixes: `v0.8.0-alpha.1`, `v0.8.0-beta.1`

## Step-by-Step

### 1. Prepare CHANGELOG

Ensure `CHANGELOG.md` is up to date with all changes since the last release. The format follows [Keep a Changelog](https://keepachangelog.com/):

```markdown
## [v0.8.0] - 2026-07-29

### Added
- feat: Question Bank custom categories UI (#31)
- feat: Kotlin extractor for source_map_v2 (#28)

### Changed
- chore: upgrade pytest to 8.x
```

### 2. Update README Roadmap

Mark completed items as `~~done~~` in the Roadmap section. Move the next planned items from the backlog.

The Roadmap lives in [`README.md`](../README.md) under the `## Status` section.

### 3. Tag and Push

```bash
# From main, after PR merge
git tag -a v0.8.0 -m "v0.8.0 — UI for custom categories"
git push origin v0.8.0
```

### 4. Create GitHub Release

```bash
gh release create v0.8.0 \
  --title "v0.8.0 — UI for custom categories" \
  --notes "See CHANGELOG.md for details"
```

Or create it manually at https://github.com/nekolife1984/specback/releases/new

## Hotfix Release

For urgent fixes on a released version:

```bash
git checkout -b fix/hotfix-crash main
# fix → commit → PR → squash merge → main
git tag -a v0.8.1 -m "v0.8.1 — crash fix"
git push origin v0.8.1
```

## Release Cadence

There is no fixed schedule. Releases are made when:

- A meaningful feature milestone is reached
- A critical bug is fixed
- A breaking change needs coordination

Current trajectory: `v0.7.x` → `v0.8.x` (feature additions) → `v1.0` (stable release after real-project validation).

## Release Checklist

- [ ] CHANGELOG.md updated
- [ ] README Roadmap updated (completed items struck through)
- [ ] Version string in `skills/specback/SKILL.md` updated (if applicable)
- [ ] Tag created and pushed
- [ ] GitHub Release created
