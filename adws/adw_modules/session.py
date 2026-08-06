"""ADW session — Run / Phase context manager for specback ADW scripts.

SSSF-compatible minimal implementation. Provides:
- Session.ensure() / Run.phase() / Run.finish()
- PhaseContext for logging and agent calls
- Envelope-based data passing between phases
- ``--adw-id`` resume support via state.json persistence
"""

from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
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


# Phase name → agent config key mapping (code default)
# Overridden by `roster` section in sssf.config.yaml if present.
_PHASE_TO_AGENT: dict[str, str] = {
    "setup": "engineer",
    "recon": "scout",
    "wbs": "engineer",
    "investigate": "investigator",
    "verify": "engineer",
    "refine": "engineer",
    "deliver": "engineer",
    "drift": "engineer",
    "changespec": "changespec",
}

# Cache for parsed config (avoids re-reading on every resolve)
_config_cache: dict[str, Any] | None = None


def _load_full_config() -> dict[str, Any]:
    """Load and cache the full sssf.config.yaml contents.

    Returns a dict with at minimum empty defaults/defaults for
    agents/roster keys so callers don't need defensive checks.
    """
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    try:
        from adws.adw_modules import agents as agents_mod  # noqa
        config_path = Path(__file__).resolve().parent.parent / "adw_sssf_config" / "sssf.config.yaml"
        cfg = agents_mod.load_config(str(config_path))
    except (FileNotFoundError, ImportError, AttributeError):
        cfg = {}
    _config_cache = {
        "defaults": cfg.get("defaults", {}),
        "agents": cfg.get("agents", {}),
        "roster": cfg.get("roster", {}),
    }
    return _config_cache

PhaseKind = Literal["engineer", "agent", "code"]


def _resolve_agent_def(phase_name: str) -> dict | None:
    """Load agent definition for a phase from sssf.config.yaml.

    Resolution order:
    1. Look up ``roster`` section in config for the phase → agent name
    2. Fall back to ``_PHASE_TO_AGENT`` code mapping
    3. Fall back to the phase name itself as the agent name
    4. Look up agent by name in ``agents`` section of config
    5. Apply ``defaults`` section as fallback for missing fields
    """
    cfg = _load_full_config()
    roster = cfg.get("roster", {})
    defaults = cfg.get("defaults", {})
    agents_cfg = cfg.get("agents", {})

    # 1. Roster from config → 2. Code fallback → 3. Phase name itself
    agent_name = roster.get(phase_name) or _PHASE_TO_AGENT.get(phase_name) or phase_name

    # 4. Look up agent definition
    agent_def = agents_cfg.get(agent_name)
    if agent_def is None:
        # No agent defined for this phase — return defaults only
        result = dict(defaults) if defaults else None
        if result is not None:
            result["_agent_name"] = agent_name
        return result

    # 5. Merge defaults under agent definition (agent values win)
    merged = dict(defaults)
    merged.update(agent_def)
    merged["_agent_name"] = agent_name  # internal metadata
    return merged


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
        entry = {"ts": datetime.now(timezone.utc).isoformat(), **kwargs}
        self._log.append(entry)

    def call(self, ac: AgentCall) -> Any:
        """Execute an agent call within this phase.

        Dispatches to ``agents.call_llm()`` which supports multiple CLI
        backends: opencode (default), claude-code, codex, copilot, pi.
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
    Supports resume via state.json persistence.
    """

    adw_id: str
    specback_dir: Path | None = None
    envelopes: dict[str, Any] = field(default_factory=dict)
    _phases: list[dict[str, Any]] = field(default_factory=list)
    _completed_phases: set[str] = field(default_factory=set)
    _completed: bool = False

    # ── Public API for pipeline orchestration ─────────────────────────

    def is_completed(self, phase_name: str) -> bool:
        """Check if a phase has been completed (public API)."""
        return phase_name in self._completed_phases

    def mark_completed(self, phase_name: str) -> None:
        """Mark a phase as completed and persist state (public API)."""
        self._completed_phases.add(phase_name)
        self._save_state()

    # ── Context manager for phase execution ───────────────────────────

    @contextmanager
    def phase(self, pp: PhaseParams) -> Iterator[PhaseContext]:
        """Context manager for a single phase execution.

        If this phase was already completed (in resume mode), skip execution
        and yield a no-op context.
        """
        if pp.name in self._completed_phases:
            noop = PhaseContext(name=pp.name, kind=pp.kind)
            noop.log(skipped=True, reason="Already completed (resume)")
            yield noop
            return

        ctx = PhaseContext(name=pp.name, kind=pp.kind)
        phase_record = {
            "name": pp.name,
            "kind": pp.kind,
            "owner": pp.owner,
            "description": pp.description,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            yield ctx
        finally:
            phase_record["completed_at"] = datetime.now(timezone.utc).isoformat()
            phase_record["log"] = ctx._log
            self._phases.append(phase_record)
            self._completed_phases.add(pp.name)
            self._save_state()

    def finish(self, accepted: bool = True) -> int:
        """Complete the run and return exit code.

        Returns 0 on acceptance, 1 on rejection.
        Should be called OUTSIDE the with run.phase() block.
        """
        self._completed = True
        self._save_state()
        return 0 if accepted else 1

    # ── State persistence ─────────────────────────────────────────────

    def _state_path(self) -> Path | None:
        """Get the path to state.json for this run."""
        if self.specback_dir:
            return self.specback_dir / f"run-{self.adw_id}.json"
        return None

    def _save_state(self) -> None:
        """Persist run state to JSON for resume support."""
        state_path = self._state_path()
        if state_path is None:
            return
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "adw_id": self.adw_id,
            "completed_phases": sorted(self._completed_phases),
            "completed": self._completed,
        }
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def _load_state(cls, specback_dir: Path, adw_id: str) -> set[str] | None:
        """Load completed phases from saved state. Returns None if no state."""
        state_path = specback_dir / f"run-{adw_id}.json"
        if not state_path.exists():
            return None
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            return set(state.get("completed_phases", []))
        except json.JSONDecodeError:
            return None


def ensure(
    cfg: dict[str, Any] | None = None,
    adw_id: str | None = None,
    specback_dir: str | Path | None = None,
) -> Run:
    """Create or resume a Run.

    If ``adw_id`` is provided and a corresponding state file exists in
    ``specback_dir``, the run resumes with already-completed phases skipped.

    Args:
        cfg: ADW configuration dict (from sssf.config.yaml). Reserved for future use.
        adw_id: Existing run ID for resume, or None for new.
        specback_dir: Path to .specback directory (for state persistence).

    Returns:
        A ``Run`` instance, possibly with pre-populated completed_phases.
    """
    run_id = adw_id or new_id()
    sb_path = Path(specback_dir) if specback_dir else None

    run = Run(adw_id=run_id, specback_dir=sb_path)

    if adw_id and sb_path:
        completed = Run._load_state(sb_path, adw_id)
        if completed is not None:
            run._completed_phases = completed
            print(f"  🔄 Resume: {len(completed)} phase(s) already completed")

    return run


def new_id() -> str:
    """Generate a new unique ADW run ID."""
    return f"adw-{uuid.uuid4().hex[:12]}"
