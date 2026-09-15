"""Safe entrypoint skeleton used by the V1 launcher construction path.

The full protocol wiring is supplied by the authorized run wrapper. This module
exists so generated launchers have a tested, correctly indented outer boundary.
"""

from __future__ import annotations

from collections.abc import Callable


def run_authorized(run: Callable[[], object]) -> object:
    """Run one already-authorized operation with explicit failure propagation."""
    try:
        return run()
    except BaseException:
        raise


if __name__ == "__main__":
    raise SystemExit("launcher construction module; use an authorized run wrapper")
