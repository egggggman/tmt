from __future__ import annotations

import json
from pathlib import Path

import pytest

from tmnt_design_studio.baseline005_provenance import ProvenanceError, verify_overlay

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_PROVENANCE_OVERLAY_001.json"


def test_overlay_authenticates_all_ten_decks():
    result = verify_overlay(ROOT, OVERLAY)
    assert len(result["verified_decks"]) == 10
    methods = {row["deck_key"]: row["method"] for row in result["verified_decks"]}
    assert methods["michelangelo"] == "authorized_crlf_equivalence"
    assert methods["splinter"] == "authorized_crlf_equivalence"
    assert sum(method == "raw_bytes" for method in methods.values()) == 8


def test_overlay_rejects_wrong_content(tmp_path):
    overlay = json.loads(OVERLAY.read_text())
    target = overlay["decks"][0]
    source = ROOT / target["source_path"]
    original = source.read_bytes()
    try:
        source.write_bytes(original.replace(b"Deck", b"DeckX", 1))
        with pytest.raises(ProvenanceError):
            verify_overlay(ROOT, OVERLAY)
    finally:
        source.write_bytes(original)


def test_overlay_rejects_wrong_path_and_identity():
    overlay = json.loads(OVERLAY.read_text())
    overlay["decks"][0]["source_path"] = "decks/missing.txt"
    path = ROOT / "tests/.tmp-provenance-overlay.json"
    try:
        path.write_text(json.dumps(overlay), encoding="utf-8")
        with pytest.raises(ProvenanceError):
            verify_overlay(ROOT, path)
    finally:
        path.unlink(missing_ok=True)


def test_overlay_rejects_unauthorized_crlf_equivalence(tmp_path):
    overlay = json.loads(OVERLAY.read_text())
    overlay["decks"][3]["serialization_convention"] = "LF"
    path = tmp_path / "overlay.json"
    path.write_text(json.dumps(overlay), encoding="utf-8")
    with pytest.raises(ProvenanceError):
        verify_overlay(ROOT, path)
