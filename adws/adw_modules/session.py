"""ADW session — Run / Phase context manager for specback ADW scripts.

SSSF-compatible minimal implementation. Provides:
- Session.ensure() / Run.phase() / Run.finish()
- PhaseContext for logging and agent calls
- Envelope-based data passing between phases
"""

from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Literal


# ── Forward reference for optional LLM call ──────────────────────────
_AGENTS_MODULE = None  # lazy import to avoid circular deps


def _call_llm(prompt: str, agent_def: dict | None = None, timeout: int = 120) -> str:
    """Thin wrapper — import agents.call_llm lazily."""
    global _AGENTS_MODULE
    if _AGENTS_MODULE is None:
        from adws.adw_modules import agents as _AGENTS_MODULE  # noqa
    return _AGENTS_MODULE.call_llm(prompt, agent_def=agent_def, timeout=timeout)

PhaseKind = Literal["engineer", "agent", "code"]


def _resolve_agent_def(phase_name: str) -> dict | None:
    """Load agent definition for a phase from sssf.config.yaml.

    Uses the phase name as the agent key. Falls back to env var ADW_PROVIDER.
    Returns None if no config found (caller will use defaults).
    """
    try:
        from adws.adw_modules import agents as agents_mod  # noqa
        config_path = Path(__file__).resolve().parent.parent / "adw_sssf_config" / "sssf.config.yaml"
        cfg = agents_mod.load_config(str(config_path))
        return cfg.get("agents", {}).get(phase_name)
    except (FileNotFoundError, KeyError, AttributeError):
        return None


@dataclass
class PhaseParams:
    """Phase definition passed to Run.phase()."""

    name: str
    kind: PhaseKind
    owner: str | None = None
    description: str = ""


@dataclass
class AgentCall:
    """Agent execution request within a phase.

    output_type: expected return type (dataclass)
    prompt: instruction text for the agent
    gates: list of Gate functions to verify output
    """

    output_type: type
    prompt: str
    gates: list = field(default_factory=list)


@dataclass
class PhaseContext:
    """Context yielded by Run.phase() for a single phase execution."""

    name: str
    kind: PhaseKind
    _log: list[dict[str, Any]] = field(default_factory=list)
    _events: list[dict[str, Any]] = field(default_factory=list)

    def log(self, **kwargs: Any) -> None:
        """Log structured data during this phase."""
        entry = {"ts": datetime.utcnow().isoformat(), **kwargs}
        self._log.append(entry)

    def call(self, ac: AgentCall) -> Any:
        """Execute an agent call within this phase.

        Dispatches to ``agents.call_llm()`` which supports multiple CLI
        backends: opencode (default), claude-code, codex.

        The backend is resolved from:
        1. ``agent_def.cli`` in sssf.config.yaml
        2. ``ADW_CLI`` environment variable
        3. ``opencode`` (hard default)

        The agent definition (provider, model, cli) is loaded from
        ``adws/adw_sssf_config/sssf.config.yaml`` using the phase owner name.
        """
        agent_def = _resolve_agent_def(self.name)
        response_text = _call_llm(ac.prompt, agent_def=agent_def, timeout=120)
        self._log.append({"agent_call": ac.prompt[:100], "response_length": len(response_text)})
        return response_text


@dataclass
class Run:
    """A single ADW run identified by adw_id.

    Manages envelopes (typed data passed between phases),
    phase execution order, and completion state.
    """

    adw_id: str
    envelopes: dict[str, Any] = field(default_factory=dict)
    _phases: list[dict[str, Any]] = field(default_factory=list)
    _completed: bool = False
    _trace_path: Path | None = None

    @contextmanager
    def phase(self, pp: PhaseParams) -> Iterator[PhaseContext]:
        """Context manager for a single phase execution.

        Usage:
            with run.phase(PhaseParams(name="recon", kind="agent")) as ph:
                report = ph.call(AgentCall(...))
                ph.log(result="ok")
        """
        ctx = PhaseContext(name=pp.name, kind=pp.kind)
        phase_record = {
            "name": pp.name,
            "kind": pp.kind,
            "owner": pp.owner,
            "description": pp.description,
            "started_at": datetime.utcnow().isoformat(),
        }
        try:
            yield ctx
        finally:
            phase_record["completed_at"] = datetime.utcnow().isoformat()
            phase_record["log"] = ctx._log
            self._phases.append(phase_record)

    def finish(self, accepted: bool = True) -> int:
        """Complete the run and return exit code.

        Returns 0 on acceptance, 1 on rejection.
        """
        self._completed = True
        return 0 if accepted else 1


def ensure(cfg: dict[str, Any] | None = None, adw_id: str | None = None) -> Run:
    """Create or resume a Run.

    cfg: ADW configuration dict (from sssf.config.yaml)
    adw_id: existing run ID for resume, or None for new
    """
    run_id = adw_id or new_id()
    return Run(adw_id=run_id)


def new_id() -> str:
    """Generate a new unique ADW run ID."""
    return f"adw-{uuid.uuid4().hex[:12]}"
