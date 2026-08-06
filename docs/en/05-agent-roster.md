# Agent Roster — Phase-Specific Model Optimization

## Overview

The **Agent Roster** assigns different LLM models to different ADW phases based on their capability and cost requirements. Instead of running all phases with the same model, you can optimize costs by using cheap models for simple phases and reserving expensive models for phases that need deep reasoning.

## How it works

### Configuration

All roster configuration lives in `adws/adw_sssf_config/sssf.config.yaml`:

```yaml
# Global defaults (all agents inherit these)
defaults:
  provider: opencode-zen
  model: ds-v4-flash
  cli: opencode

# Phase → Agent roster
roster:
  setup: engineer
  recon: scout
  wbs: engineer
  investigate: investigator
  verify: engineer
  refine: engineer
  deliver: engineer
  drift: engineer
  changespec: changespec

# Agent definitions
agents:
  engineer:
    provider: opencode-zen
    model: ds-v4-flash
    cli: opencode
  scout:
    provider: opencode-zen
    model: ds-v4-flash
    cli: opencode
  investigator:
    provider: opencode-zen
    model: ds-v4-flash
    cli: opencode
  changespec:
    provider: opencode-zen
    model: ds-v4-flash
    cli: opencode
```

### Resolution order

When a phase needs an LLM call, the system resolves the agent in this order:

1. **Roster lookup** — `roster.{phase_name}` from config
2. **Code fallback** — `_PHASE_TO_AGENT` dictionary in `session.py`
3. **Phase name fallback** — Use the phase name itself as the agent name
4. **Defaults merge** — Agent definition fields override `defaults`; missing fields inherit from `defaults`

### CLI backend resolution

1. Per-agent `cli` field
2. `defaults.cli` from config
3. `ADW_CLI` environment variable
4. Hard default: `opencode`

### Model resolution

1. Per-agent `model` field
2. `defaults.model` from config
3. `ADW_MODEL` environment variable
4. Hard default: `ds-v4-flash`

## Cost optimization strategy

| Phase | Required capability | Recommended model class | Relative cost |
|-------|--------------------|------------------------|---------------|
| Setup | Goal definition | Flash-class | 💰 Low |
| Recon | File scan + summary | Flash-class | 💰 Low |
| WBS | Structuring + classification | Flash-class | 💰 Low |
| Investigate | Deep code understanding | Reasoning-class | 💰💰 Medium |
| Verify | Code phase (no LLM) | — | $0 |
| Refine | User interaction | High-reasoning-class | 💰💰💰 High |
| Deliver | Aggregation | Flash-class | 💰 Low |
| Drift | Diff analysis | Flash-class | 💰 Low |
| Changespec | Change narration | Flash-class | 💰 Low |

### Example: Optimized roster

To use different models per phase, edit the `roster` and `agents` sections in `sssf.config.yaml`:

```yaml
roster:
  recon: recon-agent            # cheap model for scanning
  investigate: deep-investigator  # expensive model for deep analysis
  refine: dialogue-agent        # interactive reasoning
  # ... other phases use engineer (default)

agents:
  recon-agent:
    provider: opencode-zen
    model: google/gemini-3.6-flash    # cheap & fast
    cli: opencode
  deep-investigator:
    provider: fireworks
    model: fireworks/accounts/fireworks/models/kimi-k3  # deep reasoning
    cli: opencode
  dialogue-agent:
    provider: openai
    model: openai/gpt-5.6-terra       # high-reasoning
    cli: opencode
```

### Cost comparison (1000-file codebase estimate)

| Scenario | Input tokens | Estimated cost |
|----------|-------------|---------------|
| All Flash-class | Full × 1 model | $2.50 |
| Optimized (Flash + K3 + Terra) | Per-phase | $10–20 |
| All high-end (Opus 5) | Full × 1 model | $150+ |

→ The optimized roster saves **~87% vs. all high-end** while allocating expensive models only where they're needed.

## Programmatic API

### `agents.get_defaults()`

Loads the `defaults` section from `sssf.config.yaml`:

```python
from adws.adw_modules import agents
defaults = agents.get_defaults()
# Returns: {"provider": "opencode-zen", "model": "ds-v4-flash", "cli": "opencode"}
```

### `session._resolve_agent_def(phase_name)`

Resolves the merged agent definition for a phase (internal API):

```python
from adws.adw_modules import session
agent_def = session._resolve_agent_def("investigate")
# Returns merged dict: defaults + agent-specific overrides
```

## Phase kinds

| Kind | Description | LLM needed? |
|------|-------------|-------------|
| `engineer` | Interactive engineering phase | Yes |
| `agent` | Automated agent phase | Yes |
| `code` | Pure code phase (no LLM) | No |

Phases with kind `code` (verify, deliver, drift) do not make LLM calls and therefore don't consume model budget — they run entirely as Python scripts.
