"""Explicit source fixtures; production baseline guards stay frozen."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def frozen_v1_source_files(monkeypatch, tmp_path):
    """Supply the exact pre-change source blobs for the frozen v1 plan.

    Only these tests opt in. All other inputs still come from the workspace,
    and production plan() continues to reject unaccepted source identities.
    """
    from tmnt_design_studio import smoke01

    root = Path(__file__).resolve().parents[1]
    original = smoke01._git_text_identity
    revisions = {
        "engine07.py": "1a05fb646479494c1585bb8b2582d1ff6721797e",
        "card_interpreter07.py": "1a05fb646479494c1585bb8b2582d1ff6721797e",
        "pilot07.py": "de52f57a24a5c29a258573ad673051a0aa5c7e5c",
        "stage002.py": "de52f57a24a5c29a258573ad673051a0aa5c7e5c",
        "smoke01.py": "de52f57a24a5c29a258573ad673051a0aa5c7e5c",
    }
    historical = {}
    for name, revision in revisions.items():
        relative = f"src/tmnt_design_studio/{name}"
        target = tmp_path / name
        target.write_bytes(
            subprocess.check_output(["git", "show", f"{revision}:{relative}"], cwd=root)
        )
        historical[relative] = target

    def identity(root, relative, source=None):
        return original(root, relative, source or historical.get(relative))

    monkeypatch.setattr(smoke01, "_git_text_identity", identity)
