#!/usr/bin/env python3
"""specback ADW — Full pipeline entry point.

Runs all phases in sequence. Each phase calls its corresponding ADW script
or executes inline logic. Envelopes (typed data) are passed between phases.

Usage:
    uv run adws/adw_specback_full.py --target /path/to/codebase
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path for adw_modules imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from adws.adw_modules import session  # noqa: E402
from adws.adw_modules.utils import add_common_args  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="specback ADW — Full pipeline")
    add_common_args(parser)
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"Error: target directory not found: {target}", file=sys.stderr)
        return 1

    # Start a new ADW run
    run = session.ensure(adw_id=args.adw_id)

    # Phase 0: Setup & Goal
    with run.phase(session.PhaseParams(
        name="setup", kind="engineer", owner="engineer",
        description="Goal definition via engineer dialogue",
    )) as ph:
        print(f"[ADW] Phase 0: Setup — defining goal for {target}")
        ph.log(target=str(target))
        # TODO: Implement Phase 0 dialogue
        # goal = GoalOutput(...)

    # Phase 1: Recon
    with run.phase(session.PhaseParams(
        name="recon", kind="agent", owner="scout",
        description="Codebase reconnaissance",
    )) as ph:
        print(f"[ADW] Phase 1: Recon — analyzing {target}")
        ph.log(target=str(target))
        # TODO: Implement Phase 1 agent call

    print("[ADW] Full pipeline bootstrap — phases beyond 0-1 are scaffold only.")
    print("[ADW] Run `uv run adws/adw_specback_verify.py --target <path>` for Phase 4.")

    return run.finish(accepted=True)


if __name__ == "__main__":
    sys.exit(main())
