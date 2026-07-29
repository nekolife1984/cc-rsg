# cc-rsg — Agent Guide

## Branching Strategy

GitHub Flow. Details:
- EN: [docs/en/01-branching-strategy.md](docs/en/01-branching-strategy.md)
- JA: [docs/ja/01-branching-strategy.md](docs/ja/01-branching-strategy.md)

## Key Files

| Purpose | Path |
|---------|------|
| Contributing guide | [CONTRIBUTING.md](CONTRIBUTING.md) |
| PR template | [.github/pull_request_template.md](.github/pull_request_template.md) |
| README (EN) | [README.md](README.md) |

## Rules

- **No direct commits to `main`** — always feature branch → PR → squash merge
- **One logical change per branch** — conventional commit prefix required
- **CI gates** — `pytest` + `mypy` (when applicable) must pass on PR
- **Docs sync** — update both EN + JA docs when behaviors change
