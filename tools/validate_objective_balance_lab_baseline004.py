"""Validate OBL Baseline 004 promotion without running simulations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
RUNTIME = "f40c4888ef9128d03819fc1be86dde1316b2115fd0d4fb365cd03b288453afa1"
PARENT = "OBL-BASELINE-003"
BASELINE = "OBL-BASELINE-004"
COMBINED = "OBL-COMBINED-006"
CANDIDATE_SHA = "2d598af2d05212ffb0f19fe5f315b7bf8f85501975155f394448b0a48fa81ab1"
PARENT_KRANG_SHA = "5a52bc59b5de1034721ba17d1c1d4f12c493ec70681c1a910c8230808e4e4f96"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> int:
    old = load(OBL / "baselines/OBL_BASELINE_003_MANIFEST.json")
    new = load(OBL / "baselines/OBL_BASELINE_004_MANIFEST.json")
    combined = load(OBL / "combined/OBL_COMBINED_006_MANIFEST.json")
    registry = load(OBL / "ENVIRONMENT_REGISTRY.json")
    ledger = load(OBL / "EXPERIMENT_LEDGER.json")

    assert old["environment_id"] == PARENT
    assert (
        new["environment_id"] == registry["environment_id"] == ledger["environment_id"] == BASELINE
    )
    )
    assert new["lineage_parent_environment"] == PARENT
    assert new["source_combined_environment"] == COMBINED
    assert new["promotion_id"] == "OBL-PROMOTION-004"
    assert new["promotion_experiment_ids"] == ["OBL-R7-KRANG-A"]
    assert new["semantic_runtime_sha256"] == combined["semantic_runtime_sha256"] == RUNTIME
    assert combined["parent_environment"] == PARENT
    assert combined["selected_experiments"] == ["OBL-R7-KRANG-A"]
    assert combined["logical_matchups"] == 45
    assert combined["logical_games"] == combined["reused_games"] == 4500
    assert combined["newly_executed_games"] == 0
    assert combined["promotion_authorized"] is False

    old_decks = {row["deck_key"]: row for row in old["decks"]}
    new_decks = {row["deck_key"]: row for row in new["decks"]}
    assert old_decks.keys() == new_decks.keys()
    changed = [key for key in old_decks if old_decks[key]["sha256"] != new_decks[key]["sha256"]]
    assert changed == ["krang"]
    for key in old_decks:
        if key != "krang":
            assert new_decks[key]["sha256"] == old_decks[key]["sha256"]

    assert old_decks["krang"]["sha256"] == PARENT_KRANG_SHA
    assert new_decks["krang"]["sha256"] == CANDIDATE_SHA
    assert new_decks["krang"]["exact_diff"] == {
        "removals": {"Does Machines": 1, "Negate": 1},
        "additions": {"Ray Fillet, Man Ray": 1, "Stockman, Mad Fly-entist": 1},
    }

    candidate = OBL / "candidates/KRANG_OBL_R7_A.txt"
    promoted = OBL / "baselines/KRANG_OBL_BASELINE_004.txt"
    prototype = ROOT / "decks/krang/PROTOTYPE_0.3.txt"
    assert sha256(candidate) == sha256(promoted) == sha256(prototype) == CANDIDATE_SHA
    assert sha256(ROOT / "decks/krang/PROTOTYPE_0.2.txt") == PARENT_KRANG_SHA

    assert new["environment_metrics"]["mean_matchup_balance_error"] == 0.220667
    assert new["environment_metrics"]["over_60_40"] == 33
    assert new["environment_metrics"]["over_70_30"] == 22
    assert new["per_deck_win_rates"]["krang"] == 0.3878
    assert new["per_deck_metrics"]["krang"]["mean_matchup_balance_error"] == 0.2233

    record = next(row for row in ledger["experiments"] if row["experiment_id"] == "OBL-R7-KRANG-A")
    assert record["promotion_status"] == record["verdict"] == "PROMOTED"
    assert record["promotion"]["new_environment"] == BASELINE
    assert record["promotion"]["source_combined_environment"] == COMBINED

    history = (OBL / "PROMOTION_HISTORY.md").read_text(encoding="utf-8")
    assert "## Promotion OBL-PROMOTION-004" in history
    assert "**Krang is the only deck changed from Baseline 003.**" in history
    assert "New simulations for promotion: `0`" in history

    print("OBL Baseline 004 promotion validation: PASS")
    print("Changed deck hashes from Baseline 003: krang only")
    print(f"Semantic runtime: {RUNTIME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
