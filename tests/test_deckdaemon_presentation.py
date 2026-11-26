"""Gate B bounded presentation tests; no display or gameplay required."""

from __future__ import annotations

from dataclasses import replace

import pytest

from deckdaemon_viewer.presentation import InspectionSession, ROSTER, TITLE, describe
from deckdaemon_viewer.reader import (
    DECK_SLUGS,
    EvidenceReadError,
    InspectedEvidence,
)


def _evidence(verified: bool = False) -> InspectedEvidence:
    return InspectedEvidence(
        relative_path="decks/leonardo/PROTOTYPE_0.1.txt",
        content="4 Test Card\n",
        observed_sha256="a" * 64,
        verified=verified,
        provenance="unverified local snapshot" if not verified else "independently supplied SHA-256 matched",
        classification="Preserved Prototype 0.1",
    )


def test_roster_matches_gate_a_allowlist() -> None:
    assert set(ROSTER) == DECK_SLUGS
    assert len(ROSTER) == 10
    assert len(set(ROSTER)) == 10
    assert "NO GAMEPLAY" in TITLE


def test_unverified_status_and_literal_content() -> None:
    label, body = describe(_evidence())
    assert label == "UNVERIFIED LOCAL SNAPSHOT"
    assert "decks/leonardo/PROTOTYPE_0.1.txt" in body
    assert "a" * 64 in body
    assert body.endswith("4 Test Card\n")


def test_supplied_digest_status_label() -> None:
    label, body = describe(replace(_evidence(), verified=True))
    assert label == "VERIFIED AGAINST SUPPLIED DIGEST"
    assert "Observed SHA-256" in body


def test_session_only_calls_gate_a_reader(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    deck_calls: list[tuple[object, str]] = []
    baseline_calls: list[object] = []

    def fake_deck(root, slug):
        deck_calls.append((root, slug))
        return _evidence()

    def fake_baseline(root):
        baseline_calls.append(root)
        return replace(
            _evidence(),
            classification="Historical Baseline 005 — not live",
            relative_path="docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json",
        )

    monkeypatch.setattr("deckdaemon_viewer.presentation.read_prototype_01", fake_deck)
    monkeypatch.setattr("deckdaemon_viewer.presentation.read_baseline_005", fake_baseline)

    session = InspectionSession(tmp_path)
    assert session.deck("leonardo")[0] == "UNVERIFIED LOCAL SNAPSHOT"
    assert "Historical Baseline 005" in session.baseline()[1]
    assert deck_calls == [(tmp_path, "leonardo")]
    assert baseline_calls == [tmp_path]


def test_unknown_deck_does_not_touch_reader(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("unapproved deck invoked reader")

    monkeypatch.setattr("deckdaemon_viewer.presentation.read_prototype_01", forbidden)
    with pytest.raises(EvidenceReadError, match="allowlist"):
        InspectionSession(tmp_path).deck("../unapproved")


def test_missing_evidence_rejection_is_not_reclassified(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    def broken(*args, **kwargs):
        raise EvidenceReadError("evidence cannot be read")

    monkeypatch.setattr("deckdaemon_viewer.presentation.read_baseline_005", broken)
    with pytest.raises(EvidenceReadError, match="cannot be read"):
        InspectionSession(tmp_path).baseline()
