"""Agent configuration loader and LLM CLI caller for ADW scripts.

Loads model/agent assignments from sssf.config.yaml and provides
a unified ``call_llm()`` interface that supports multiple CLI backends:

- **opencode** (default): ``opencode run <prompt>``
- **claude-code**: ``claude -p <prompt>``
- **codex**: ``codex run <prompt>``
- **copilot** (default): ``copilot -p <prompt>`` (standalone; falls back to ``gh copilot -p <prompt>``)
- **pi**: ``pi <prompt>``
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Literal

CLIBackend = Literal["opencode", "claude-code", "codex", "copilot", "pi"]

# Maps short config keys to CLI binary names
_CLI_BINARIES: dict[CLIBackend, str] = {
    "opencode": "opencode",
    "claude-code": "claude",
    "codex": "codex",
    "copilot": "copilot",  # standalone binary (official); falls back to gh copilot
    "pi": "pi",
}


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
            if not isinstance(agent_def, dict):
                issues.append(f"Agent '{name}' is not a dict")
                continue
            if "provider" not in agent_def:
                issues.append(f"Agent '{name}' missing 'provider'")
            if "model" not in agent_def:
                issues.append(f"Agent '{name}' missing 'model'")

    # defaults section is optional but must be a dict if present
    if "defaults" in cfg and not isinstance(cfg["defaults"], dict):
        issues.append("'defaults' must be a dict")

    # roster section is optional but must be a dict of phase→agent mappings
    if "roster" in cfg:
        if not isinstance(cfg["roster"], dict):
            issues.append("'roster' must be a dict")
        else:
            for phase, agent_name in cfg["roster"].items():
                if not isinstance(agent_name, str):
                    issues.append(f"Roster entry '{phase}' must map to a string agent name")

    return issues


def _resolve_backend(agent_def: dict[str, Any] | None) -> CLIBackend:
    """Resolve which CLI backend to use for an agent definition.

    Priority:
    1. ``agent_def.cli`` — per-agent override
    2. ``ADW_CLI`` env var — global override
    3. ``opencode`` — hard default
    """
    if agent_def and "cli" in agent_def:
        return agent_def["cli"]  # type: ignore[return-value]

    env_cli = _normalize_backend(
        os.environ.get("ADW_CLI", "")
    )
    if env_cli:
        return env_cli

    return "opencode"


def _normalize_backend(name: str) -> CLIBackend | None:
    """Normalize a CLI name string to a CLIBackend literal."""
    name = name.strip().lower().replace("-", " ").replace("_", " ")
    mapping: dict[str, CLIBackend] = {
        "opencode": "opencode",
        "open code": "opencode",
        "claude": "claude-code",
        "claude code": "claude-code",
        "claude-code": "claude-code",
        "codex": "codex",
        "copilot": "copilot",
        "github copilot": "copilot",
        "gh": "copilot",
        "pi": "pi",
        "pi ai": "pi",
        "pi.ai": "pi",
    }
    return mapping.get(name)


def get_defaults(config_path: str | Path | None = None) -> dict[str, Any] | None:
    """Load the ``defaults`` section from sssf.config.yaml.

    Args:
        config_path: Path to the config file. Defaults to the standard
            location (``adws/adw_sssf_config/sssf.config.yaml``).

    Returns:
        Dict of default values (model, provider, cli) or None if not found.
    """
    if config_path is None:
        config_path = (
            Path(__file__).resolve().parent.parent
            / "adw_sssf_config"
            / "sssf.config.yaml"
        )
    try:
        cfg = load_config(str(config_path))
        defaults = cfg.get("defaults")
        return dict(defaults) if isinstance(defaults, dict) else None
    except (FileNotFoundError, ImportError, AttributeError):
        return None


def build_cli_command(
    backend: CLIBackend,
    prompt: str,
    agent_def: dict[str, Any] | None = None,
) -> list[str]:
    """Build a CLI command list for the given backend and prompt.

    Args:
        backend: Which CLI to use.
        prompt: The LLM prompt text.
        agent_def: Optional agent config (may contain model override).

    Returns:
        ``list[str]`` suitable for ``subprocess.run()``.
    """
    binary = _CLI_BINARIES[backend]

    if backend == "opencode":
        cmd = [binary, "run", prompt]
        model = (agent_def or {}).get("model") or os.environ.get("ADW_MODEL")
        if model:
            cmd.extend(["--model", model])
        return cmd

    if backend == "claude-code":
        cmd = [binary, "-p", prompt]
        model = (agent_def or {}).get("model")
        if model:
            cmd.extend(["--model", model])
        return cmd

    if backend == "codex":
        return [binary, "run", prompt]

    if backend == "copilot":
        import shutil
        if shutil.which("copilot"):
            cmd = [binary, "-p", prompt]
            model = (agent_def or {}).get("model")
            if model:
                cmd.extend(["--model", model])
            return cmd
        if shutil.which("gh"):
            return ["gh", "copilot", "-p", prompt]
        raise FileNotFoundError(
            f"Copilot CLI not found. Expected 'copilot' (standalone) "
            f"or 'gh' (legacy extension) on PATH. "
            f"Install via: npm install -g @githubnext/github-copilot-cli"
        )

    if backend == "pi":
        cmd = [binary, prompt]
        model = (agent_def or {}).get("model")
        if model:
            cmd = [binary, "--model", model, prompt]
        return cmd

    raise ValueError(f"Unknown CLI backend: {backend}")


def call_llm(
    prompt: str,
    agent_def: dict[str, Any] | None = None,
    timeout: int = 120,
) -> str:
    """Call an LLM via the configured CLI backend and return the response.

    The backend is resolved from ``agent_def.cli`` → ``ADW_CLI`` env var →
    ``opencode`` (hard default).

    Args:
        prompt: The LLM prompt text.
        agent_def: Optional agent configuration dict (from sssf.config.yaml).
            If None, defaults from sssf.config.yaml are used as fallback.
        timeout: Max seconds to wait for the CLI.

    Returns:
        The LLM response as a string (stdout of the CLI).

    Raises:
        FileNotFoundError: If the CLI binary is not found on PATH.
        subprocess.TimeoutExpired: If the CLI times out.
        RuntimeError: If the CLI returns a non-zero exit code.
    """
    if agent_def is None:
        agent_def = get_defaults()
    backend = _resolve_backend(agent_def)
    cmd = build_cli_command(backend, prompt, agent_def)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        raise FileNotFoundError(
            f"CLI backend '{backend}' not found on PATH. "
            f"Install it or set ADW_CLI to a different backend.\n"
            f"Expected binary: {_CLI_BINARIES[backend]}"
        )
    except subprocess.TimeoutExpired:
        raise TimeoutError(
            f"CLI backend '{backend}' timed out after {timeout}s"
        )

    if result.returncode != 0:
        raise RuntimeError(
            f"CLI backend '{backend}' exited with code {result.returncode}.\n"
            f"Stderr: {result.stderr[:500]}"
        )

    return result.stdout.strip()
