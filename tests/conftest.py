"""Explicit historical source fixtures; production baseline guards stay frozen."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def frozen_v1_source_files(monkeypatch, tmp_path):
    """Reconstruct V1 text bytes for historical plan tests, using real Git hashing.

    Only these tests opt in. All other inputs still come from the workspace,
    and production plan() continues to reject unaccepted V2 source identities.
    """
    from tmnt_design_studio import smoke01

    root = Path(__file__).resolve().parents[1]
    revision = "de52f57a24a5c29a258573ad673051a0aa5c7e5c"
    original = smoke01._git_text_identity
    historical = {}
    for name in ("engine07.py", "pilot07.py", "stage002.py", "smoke01.py"):
        relative = f"src/tmnt_design_studio/{name}"
        target = tmp_path / name
        target.write_bytes(
            subprocess.check_output(["git", "show", f"{revision}:{relative}"], cwd=root)
        )
        historical[relative] = target

    def identity(root, relative, source=None):
        return original(root, relative, source or historical.get(relative))

    monkeypatch.setattr(smoke01, "_git_text_identity", identity)
