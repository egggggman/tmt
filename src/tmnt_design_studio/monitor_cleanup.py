"""Owned monitor lifecycle; no caller-thread process control or unbounded joins.

OS process creation/termination cannot be forcibly cancelled by Python. One
supervisor retains unresolved ownership; a new sample cannot accumulate children.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

POLL_SECONDS = 0.025
REAP_SECONDS = 0.5


class MonitorOwner:
    def __init__(self, deadline: float):
        self.deadline = deadline
        self.work_deadline = time.monotonic() + max(0, deadline - time.monotonic()) * 0.6
        self.worker = None
        self.buffer = None
        self.result = None
        self.closed = threading.Event()
        self.finished = threading.Event()
        self.cancelled = threading.Event()
        self.stage = "STARTING"
        self.process_state = "UNKNOWN"
        self.errors: list[tuple[str, Exception]] = []
        self.thread: threading.Thread | None = None
        self._guard = threading.Lock()

    def record(self, operation: str, error: Exception) -> None:
        # Preserve exception objects and ordering; snapshots are JSON-safe views.
        if not any(previous == operation for previous, _ in self.errors):
            self.errors.append((operation, error))

    def snapshot(self) -> dict:
        return {
            "state": "CLOSED"
            if self.closed.is_set()
            else "UNRESOLVED"
            if self.finished.is_set()
            else "PENDING",
            "operation": self.stage,
            "process_state": self.process_state,
            "errors": [
                dict(
                    operation=op,
                    type=type(error).__name__,
                    message=str(error),
                    errno=getattr(error, "errno", None),
                    winerror=getattr(error, "winerror", None),
                )
                for op, error in tuple(self.errors)
            ],
        }

    def launch(self, operation: Callable[[], None]) -> None:
        def supervised():
            try:
                operation()
            except Exception as error:
                self.record(self.stage, error)
            finally:
                self.cleanup(request_stop=self.result is None or self.cancelled.is_set())

        self.thread = threading.Thread(target=supervised, daemon=True)
        self.thread.start()

    def cleanup(self, *, request_stop: bool) -> None:
        worker = self.worker
        if worker is None:
            self.stage = "CLOSED"
            self.closed.set()
            self.finished.set()
            return
        try:
            if request_stop:
                try:
                    self.stage = "TERMINATING"
                    if worker.pid is not None and worker.is_alive():
                        worker.terminate()  # May block/fail; never on caller thread.
                except Exception as error:
                    self.record("terminate", error)
            self.reap()
        finally:
            self.finished.set()

    def reap(self) -> None:
        worker = self.worker
        self.stage = "REAPING"
        limit = time.monotonic() + REAP_SECONDS
        while True:
            try:
                if worker.pid is None or not worker.is_alive():
                    if worker.pid is not None:
                        self.process_state = "EXIT_CONFIRMED"
                        try:
                            worker.join(timeout=0)
                        except Exception as error:
                            self.record("join", error)
                    else:
                        self.process_state = "NO_PROCESS_HANDLE"
                    worker.close()
                    self.stage = "CLOSED"
                    self.closed.set()
                    return
                if time.monotonic() >= limit:
                    break
                worker.join(timeout=min(POLL_SECONDS, max(0, limit - time.monotonic())))
            except Exception as error:
                self.record("reap", error)
                break
        # The handle and error remain owned, not dropped or falsely closed.
        self.stage = "UNRESOLVED"

    def refresh(self) -> None:
        """Observe late exits without creating another child or retrying termination."""
        with self._guard:
            if self.closed.is_set() or (
                self.thread is not None and self.thread.is_alive() and not self.finished.is_set()
            ):
                return
            self.finished.clear()

            def observe():
                try:
                    self.reap()
                finally:
                    self.finished.set()

            self.thread = threading.Thread(target=observe, daemon=True)
            self.thread.start()


class MonitorFailure(dict):
    """Legacy UNKNOWN mapping with explicit lifecycle diagnostics for callers.

    Use report() for serialization; the supported CLI does so. No equality
    override: UNKNOWN remains a failure even for legacy mapping consumers.
    Outcome is fixed; a late sample can never become a successful response.
    """

    def __init__(self, outcome: str, owner: MonitorOwner):
        super().__init__(state="UNKNOWN")
        self.outcome = outcome
        self.owner = owner

    @property
    def original_error(self) -> Exception | None:
        return self.owner.errors[0][1] if self.owner.errors else None

    @property
    def cleanup_error(self) -> Exception | None:
        return next(
            (
                error
                for operation, error in self.owner.errors
                if operation in ("terminate", "reap", "join")
            ),
            None,
        )

    def report(self) -> dict:
        return {**self, "outcome": self.outcome, "cleanup": self.owner.snapshot()}


_OWNER: MonitorOwner | None = None
_GUARD = threading.Lock()


def claim_monitor(deadline: float) -> tuple[MonitorOwner, bool]:
    global _OWNER
    with _GUARD:
        if _OWNER is not None and not _OWNER.closed.is_set():
            _OWNER.refresh()
            return _OWNER, False
        _OWNER = MonitorOwner(deadline)
        return _OWNER, True


def cleanup_status(*, refresh: bool = False) -> dict:
    with _GUARD:
        if _OWNER is None:
            return {"state": "IDLE"}
        if refresh:
            _OWNER.refresh()
        return _OWNER.snapshot()
