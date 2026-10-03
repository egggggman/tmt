"""A direct promotion must retain its combined authority's metric identity."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import pytest

from tools.objective_balance_lab_promotion_metrics import (
    AUTHORITY_PATH,
    historical_baseline002_registry,
    load,
    recorded_evidence_sha_bytes,
    validate_direct_promotion,
)


@pytest.fixture(scope="module")
def promotion_inputs():
    baseline = load("docs/objective-balance-lab/baselines/OBL_BASELINE_002_MANIFEST.json")
    authority = load(AUTHORITY_PATH)
    return (
        baseline,
        authority,
        load(
            "docs/objective-balance-lab/combined/OBL_COMBINED_003_RUNTIME_COMPATIBLE_MANIFEST.json"
        ),
        historical_baseline002_registry(
            baseline, authority, load("docs/objective-balance-lab/ENVIRONMENT_REGISTRY.json")
        ),
    )


def test_direct_promotion_matches_raw_authority(promotion_inputs):
    metrics, rates, fingerprint_digest = validate_direct_promotion(
        *promotion_inputs, AUTHORITY_PATH
    )
    assert metrics["mean_matchup_balance_error"] == 0.189556
    assert rates["raphael"] == 0.702222
    assert len(fingerprint_digest) == 64


def test_historical_evidence_hash_matches_lf_and_crlf_checkouts():
    lf = b'{"games": 4500}\n'
    crlf = lf.replace(b"\n", b"\r\n")
    expected = hashlib.sha256(crlf).hexdigest()
    assert recorded_evidence_sha_bytes(lf) == expected
    assert recorded_evidence_sha_bytes(crlf) == expected


def test_legacy_prototype_hash_reconstructs_from_lf_checkout(promotion_inputs):
    manifest = promotion_inputs[0]
    michelangelo = next(row for row in manifest["decks"] if row["deck_key"] == "michelangelo")
    raw = Path(michelangelo["source_path"]).read_bytes().replace(b"\r\n", b"\n")
    assert recorded_evidence_sha_bytes(raw) == michelangelo["sha256"]


@pytest.mark.parametrize(
    "mutation",
    [
        "global_metric",
        "deck_rate",
        "deck_hash",
        "semantic_runtime",
        "cell_fingerprint",
        "source_evidence",
    ],
)
def test_direct_promotion_rejects_mismatched_identity(promotion_inputs, mutation):
    baseline, authority, authority_manifest, registry = (
        copy.deepcopy(value) for value in promotion_inputs
    )
    if mutation == "global_metric":
        baseline["environment_metrics"]["mean_matchup_balance_error"] = 0.193333
    elif mutation == "deck_rate":
        registry["decks"][0]["aggregate_baseline_win_rate"] = 0.5
    elif mutation == "deck_hash":
        baseline["decks"][0]["sha256"] = "0" * 64
    elif mutation == "semantic_runtime":
        baseline["semantic_runtime_sha256"] = "0" * 64
    elif mutation == "source_evidence":
        registry["source_combined_evidence"]["path"] = (
            "docs/objective-balance-lab/COMBINED_001_EVIDENCE.json"
        )
    else:
        authority["provenance"][0]["fingerprint"] = "0" * 64
    with pytest.raises(ValueError):
        validate_direct_promotion(baseline, authority, authority_manifest, registry, AUTHORITY_PATH)
