"""Gate A synthetic-only tests: no engine, launcher, network, or GUI."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from deckdaemon_viewer.reader import (
    BASELINE_PATH,
    DECK_SLUGS,
    EvidenceReadError,
    read_baseline_005,
    read_prototype_01,
)


def fixture_manifest() -> dict:
    return {
        "schema": "objective-balance-lab-official-baseline-v1",
        "environment_id": "OBL-BASELINE-005",
        "state": "OFFICIAL_BASELINE",
        "repository_sha": "a" * 40,
        "per_deck_metrics": {
            slug: {
                "win_rate": 0.5,
                "matchup_win_rates": {opp: 0.5 for opp in DECK_SLUGS if opp != slug},
            }
            for slug in DECK_SLUGS
        },
    }


def fixture_root(tmp_path: Path) -> Path:
    deck = tmp_path / "decks/leonardo/PROTOTYPE_0.1.txt"
    deck.parent.mkdir(parents=True)
    deck.write_bytes(b"4 Test Turtle\n")
    manifest = tmp_path / BASELINE_PATH
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps(fixture_manifest()), encoding="utf-8")
    return tmp_path


def test_read_exact_allowlisted_deck_and_verified_digest(tmp_path):
    root = fixture_root(tmp_path)
    expected = hashlib.sha256(b"4 Test Turtle\n").hexdigest()
    before = (root / "decks/leonardo/PROTOTYPE_0.1.txt").read_bytes()
    item = read_prototype_01(root, "leonardo", expected_sha256=expected)
    assert item.verified and item.observed_sha256 == expected
    assert item.relative_path == "decks/leonardo/PROTOTYPE_0.1.txt"
    assert item.content == "4 Test Turtle\n"
    assert (root / item.relative_path).read_bytes() == before


def test_unverified_observed_digest_is_not_a_provenance_claim(tmp_path):
    item = read_prototype_01(fixture_root(tmp_path), "leonardo")
    assert not item.verified and item.provenance == "unverified local snapshot"


@pytest.mark.parametrize("slug", ["../leonardo", "leonardo/../raphael", "missing", "", None])
def test_deck_allowlist_rejects_other_paths(tmp_path, slug):
    with pytest.raises(EvidenceReadError, match="allowlist"):
        read_prototype_01(fixture_root(tmp_path), slug)


def test_missing_and_inaccessible_inputs_fail_closed(tmp_path):
    root = fixture_root(tmp_path)
    (root / "decks/leonardo/PROTOTYPE_0.1.txt").unlink()
    with pytest.raises(EvidenceReadError):
        read_prototype_01(root, "leonardo")
    with pytest.raises(EvidenceReadError):
        read_baseline_005(root / "does-not-exist")


def test_symlink_file_and_directory_fail_closed(tmp_path):
    root = fixture_root(tmp_path)
    deck = root / "decks/leonardo/PROTOTYPE_0.1.txt"
    deck.unlink()
    try:
        deck.symlink_to(root / BASELINE_PATH)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not permitted on this host")
    with pytest.raises(EvidenceReadError, match="linked|non-link"):
        read_prototype_01(root, "leonardo")
    linked_root = tmp_path / "alternate"
    linked_root.symlink_to(root, target_is_directory=True)
    with pytest.raises(EvidenceReadError, match="linked|non-link"):
        read_prototype_01(linked_root, "leonardo")


@pytest.mark.parametrize("location", ["root", "intermediate", "file"])
def test_windows_junction_components_fail_closed_without_symlink_privileges(
    tmp_path, monkeypatch, location
):
    """Exercise Path.is_junction fail-closed checks without creating privileged links."""
    root = fixture_root(tmp_path)
    destination = {
        "root": root,
        "intermediate": root / "decks" / "leonardo",
        "file": root / "decks" / "leonardo" / "PROTOTYPE_0.1.txt",
    }[location]
    original = Path.is_junction

    def simulated_junction(path):
        return path == destination or original(path)

    monkeypatch.setattr(Path, "is_junction", simulated_junction)
    with pytest.raises(EvidenceReadError, match="non-link|linked"):
        read_prototype_01(root, "leonardo")


def test_oversized_or_non_utf8_deck_rejected(tmp_path):
    root = fixture_root(tmp_path)
    deck = root / "decks/leonardo/PROTOTYPE_0.1.txt"
    deck.write_bytes(b"X" * (1_048_576 + 1))
    with pytest.raises(EvidenceReadError, match="byte limit"):
        read_prototype_01(root, "leonardo")
    deck.write_bytes(b"\xff")
    with pytest.raises(EvidenceReadError, match="UTF-8"):
        read_prototype_01(root, "leonardo")


def test_wrong_or_malformed_digest_rejected(tmp_path):
    root = fixture_root(tmp_path)
    with pytest.raises(EvidenceReadError, match="mismatch"):
        read_prototype_01(root, "leonardo", expected_sha256="0" * 64)
    with pytest.raises(EvidenceReadError, match="64 hexadecimal"):
        read_prototype_01(root, "leonardo", expected_sha256="not a digest")


def test_baseline_is_historical_and_exactly_parsed(tmp_path):
    root = fixture_root(tmp_path)
    manifest = root / BASELINE_PATH
    blob = manifest.read_bytes()
    result = read_baseline_005(root, expected_sha256=hashlib.sha256(blob).hexdigest())
    assert result.verified
    assert result.parsed["environment_id"] == "OBL-BASELINE-005"
    assert "Historical" in result.classification and "live" in result.classification
    assert manifest.read_bytes() == blob


@pytest.mark.parametrize("bad", ["{", '{"schema":"x"}', '{"a":1,"a":2}', '{"x":NaN}'])
def test_bad_json_and_duplicate_keys_rejected(tmp_path, bad):
    root = fixture_root(tmp_path)
    (root / BASELINE_PATH).write_text(bad, encoding="utf-8")
    with pytest.raises(EvidenceReadError):
        read_baseline_005(root)


def test_wrong_schema_roster_and_rate_rejected(tmp_path):
    root = fixture_root(tmp_path)
    path = root / BASELINE_PATH
    for mutation in ("schema", "roster", "rate", "opponents"):
        data = fixture_manifest()
        if mutation == "schema":
            data["schema"] = "wrong"
        elif mutation == "roster":
            del data["per_deck_metrics"]["krang"]
        elif mutation == "rate":
            data["per_deck_metrics"]["krang"]["win_rate"] = 1.2
        else:
            del data["per_deck_metrics"]["krang"]["matchup_win_rates"]["raphael"]
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(EvidenceReadError):
            read_baseline_005(root)
