"""Event tracer for ADW runs.

Records phase lifecycle events to JSONL.
Future: migrate to SQLite (#205).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class Tracer:
    """Minimal event tracer writing to JSONL."""

    def __init__(self, trace_dir: str | Path) -> None:
        self._path = Path(trace_dir)
        self._path.mkdir(parents=True, exist_ok=True)

    def _event_file(self, adw_id: str) -> Path:
        return self._path / f"trace-{adw_id}.jsonl"

    def emit(self, adw_id: str, event_type: str, data: dict[str, Any]) -> None:
        """Write a single event to the trace file."""
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "adw_id": adw_id,
            "type": event_type,
            "data": data,
        }
        with open(self._event_file(adw_id), "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
