"""Telemetry does not open checkpoint paths or grant resume authority."""

import multiprocessing
import time

import pytest

from tmnt_design_studio import resume_status as status
from tmnt_design_studio.resume_authorization import ResumeRefused, encoded


def payload():
    return dict(
        protocol=status.PROTOCOL,
        authorization="test",
        committed_games=733,
        checkpoint_sha256="a" * 64,
        heartbeat=time.time(),
    )


def test_actual_read_handle_is_closed_and_read_only(tmp_path):
    path = tmp_path / status.STATUS_NAME
    status.publish_status(path, authorization="test", count=733, checkpoint_sha256="a" * 64)
    before = path.read_bytes()
    observed = status._read_shared(str(path))
    assert status.parse_status(observed, authorization="test")["committed_games"] == 733
    assert path.read_bytes() == before
    replacement = tmp_path / "replacement"
    replacement.write_bytes(before)
    replacement.replace(path)  # Must succeed after reader closure on Windows too.


@pytest.mark.parametrize(
    "field,value",
    [
        ("protocol", "old"),
        ("authorization", "other"),
        ("committed_games", True),
        ("committed_games", 901),
        ("checkpoint_sha256", "bad"),
        ("heartbeat", 0),
        ("heartbeat", float("inf")),
    ],
)
def test_incompatible_status(field, value):
    value_dict = payload()
    value_dict[field] = value
    with pytest.raises((ResumeRefused, ValueError)):
        status.parse_status(encoded(value_dict), authorization="test")


def test_status_cannot_override_display_state():
    assert (
        status.parse_status(encoded(dict(payload(), state="VERIFIED")), authorization="test")[
            "state"
        ]
        == "REPORTED_ONLY"
    )


@pytest.mark.parametrize("data", [b"[]", b"{}", b"x" * 4097, b'{"a":1,"a":2}'])
def test_malformed_or_oversized_status(data):
    with pytest.raises((ResumeRefused, ValueError)):
        status.parse_status(data, authorization="test")


def test_checkpoint_argument_refused(tmp_path):
    path = tmp_path / "checkpoint.json"
    path.write_bytes(b"protected fixture")
    assert status.read_status(path, authorization="test") == {"state": "UNKNOWN"}
    assert path.read_bytes() == b"protected fixture"


def test_deadline_terminates_and_joins_worker(monkeypatch, tmp_path):
    calls = []

    class Pipe:
        def close(self):
            calls.append("close")

        def poll(self, timeout):
            assert 0 <= timeout <= 0.25
            return False

    class Process:
        pid = 123

        def start(self):
            calls.append("start")

        def is_alive(self):
            return True

        def terminate(self):
            calls.append("terminate")

        def join(self):
            calls.append("join")

    class Context:
        def Pipe(self, **_):
            return Pipe(), Pipe()

        def Process(self, **_):
            return Process()

    monkeypatch.setattr(multiprocessing, "get_context", lambda _: Context())
    assert status.read_status(tmp_path / status.STATUS_NAME, authorization="test") == {
        "state": "UNKNOWN"
    }
    assert calls.index("terminate") < calls.index("join")
