"""Agent configuration loader for ADW scripts.

Loads model/agent assignments from sssf.config.yaml.
Minimal SSSF-compatible implementation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_config(config_path: str | Path) -> dict[str, Any]:
    """Load ADW configuration from sssf.config.yaml.

    Returns a dict with at minimum an 'agents' key containing
    agent name → definition mappings.
    """
    import yaml  # type: ignore[import-untyped]

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"ADW config not found: {path}")

    with open(path, encoding="utf-8") as f:
        cfg: dict[str, Any] = yaml.safe_load(f)

    return cfg


def validate(cfg: dict[str, Any]) -> list[str]:
    """Validate configuration structure.

    Returns a list of validation warnings/errors (empty if valid).
    """
    issues: list[str] = []

    if "agents" not in cfg:
        issues.append("Missing 'agents' key in config")
    else:
        for name, agent_def in cfg["agents"].items():
            if "provider" not in agent_def:
                issues.append(f"Agent '{name}' missing 'provider'")
            if "model" not in agent_def:
                issues.append(f"Agent '{name}' missing 'model'")

    return issues
