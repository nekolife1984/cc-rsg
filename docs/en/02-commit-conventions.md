# Commit Conventions

## Overview

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification for all commit messages. This keeps the history readable, enables automated changelog generation, and makes it easy to understand what each change does at a glance.

## Prefixes

| Prefix | Usage | Example |
|--------|-------|---------|
| `feat:` | New feature or enhancement | `feat: add plantuml template` |
| `fix:` | Bug fix | `fix: detect encoding in py files` |
| `chore:` | CI, maintenance, refactoring, dependencies | `chore: update pytest to 8.x` |
| `docs:` | Documentation only (no code change) | `docs: fix typo in branching-strategy` |
| `test:` | Test addition or modification | `test: add coverage for build-trace.py` |

When in doubt, use `chore:` for changes that don't add a feature or fix a bug.

## One Change, One Commit

Each commit should represent **one logical change**. If you find yourself listing multiple unrelated points in the body, split them into separate commits.

**Good:**
```
feat: add Flask extraction guide to references

- Covers Blueprints, view functions, hooks, Jinja2 templates
- Includes Flask-WTF forms and Flask-SQLAlchemy models

Closes #42
```

**Avoid:**
```
feat: add Flask extraction guide and fix typos in README
```

The two changes are unrelated — `fix typos in README` should be its own `docs:` commit.

## Message Format

```
<prefix>: <short description> (#<issue-N>)

<optional body — bullet points explaining what and why>

<optional footer — Closes #N, refs #N>
```

### Subject (first line)
- Capitalize the first letter after the prefix
- No period at the end
- Max 72 characters
- Reference the issue number in the PR merge title, not necessarily in every commit

### Body
- Use bullet points (`- `) for multiple items
- Explain **why**, not just **what**
- Reference related files or concepts when helpful

### Footer
- `Closes #N` — auto-closes an issue on merge
- `refs #N` — references an issue without closing

## Squash Merge Convention

Since we use **squash merge**, only the PR title and description become the commit message on `main`. This means:

- The **PR title** becomes the commit subject — use the conventional prefix format:
  `feat: add Flask extraction guide`
- The **PR description** becomes the commit body
- Individual commit messages inside the branch are for the author's reference

**TL;DR:** Make your PR title a good conventional commit message.
