"""Combined 006 must authenticate every reused game cell and frozen identity."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_combined_006_r7a", ROOT / "tools/validate_combined_006_r7a.py"
)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def test_full_45_cell_authentication() -> None:
    accepted = validator.validate()
    assert accepted["acceptance"] == "PASS_COMBINED_INDEPENDENT_READ_ONLY"
    assert accepted["cells"] == 45
    assert accepted["games"] == 4500


@pytest.mark.parametrize("source", ["candidate", "combined"])
def test_modified_source_game_fails_closed(monkeypatch: pytest.MonkeyPatch, source: str) -> None:
    target = validator.CANDIDATE if source == "candidate" else validator.EVIDENCE
    original = validator.load

    def altered(path: Path) -> dict:
        value = original(path)
        if path == target:
            value = copy.deepcopy(value)
            key = "games" if source == "candidate" else "combined_games"
            value[key][0]["winner"] = None
        return value

    monkeypatch.setattr(validator, "load", altered)
    with pytest.raises(AssertionError):
        validator.validate()
