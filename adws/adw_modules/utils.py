"""CLI utilities for ADW scripts.

Shared argument parsing, path resolution, and prompt helpers.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add standard ADW CLI arguments to a parser."""
    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="Target codebase directory",
    )
    parser.add_argument(
        "--adw-id",
        type=str,
        default=None,
        help="Existing ADW run ID for resume",
    )
    parser.add_argument(
        "--specback-dir",
        type=str,
        default=None,
        help=".specback directory (default: <target>/.specback)",
    )


def resolve_specback_dir(target: str, specback_dir: str | None) -> Path:
    """Resolve the .specback directory path.

    If ``specback_dir`` is explicitly provided, returns it resolved.
    Otherwise defaults to ``<target>/.specback``.

    Note: The full pipeline and setup script override this default
    to use ``<output_dir>/.specback`` instead.
    """
    if specback_dir:
        return Path(specback_dir).resolve()
    return Path(target).resolve() / ".specback"


def resolve_ref_path(repo_root: str | Path, *parts: str) -> Path:
    """Resolve a path relative to the repo root.

    Helper for phase scripts that reference files in scripts/,
    references/, schemas/, etc.
    """
    return Path(repo_root).resolve().joinpath(*parts)
