"""Recompute Baseline 003 reference metrics from Combined 005 raw game cells."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))

import build_combined003_runtime_compatible as b3  # noqa: E402
import build_combined_004_reports as b4  # noqa: E402
import run_combined_004 as c4  # noqa: E402
import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round5 as r5  # noqa: E402
from objective_balance_lab_promotion_metrics import recompute, require  # noqa: E402


def read(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def validate() -> dict:
    baseline = read("docs/objective-balance-lab/baselines/OBL_BASELINE_003_MANIFEST.json")
    registry = read("docs/objective-balance-lab/ENVIRONMENT_REGISTRY.json")
    combined = read("docs/objective-balance-lab/COMBINED_005_EVIDENCE.json")
    combined_manifest = read("docs/objective-balance-lab/combined/OBL_COMBINED_005_MANIFEST.json")
    authority_path = "docs/objective-balance-lab/COMBINED_005_EVIDENCE.json"
    require(
        baseline["environment_id"] == registry["environment_id"] == "OBL-BASELINE-003",
        "Wrong baseline ID",
    )
    require(baseline["state"] == registry["status"] == "OFFICIAL_BASELINE", "Not official")
    require(baseline["lineage_parent_environment"] == "OBL-BASELINE-002", "Wrong parent")
    require(
        baseline["source_combined_environment"] == combined["environment_id"] == "OBL-COMBINED-005",
        "Wrong authority",
    )
    require(
        baseline["source_combined_state"]
        == registry["source_combined_state"]
        == "COMBINED_VALIDATED",
        "Combined state missing",
    )
    require(
        combined["environment_decision"] == "COMBINED_ENVIRONMENT_IMPROVED",
        "Combined result not improved",
    )
    require(baseline["source_combined_evidence"]["path"] == authority_path, "Wrong evidence path")
    require(
        baseline["source_combined_evidence"]["sha256"] == r5.git_blob_sha(authority_path),
        "Evidence SHA mismatch",
    )
    require(
        registry["source_combined_evidence"] == baseline["source_combined_evidence"],
        "Registry evidence mismatch",
    )
    require(
        registry["reference_evidence"] == baseline["source_combined_evidence"],
        "Registry reference mismatch",
    )
    require(
        registry["promotion_evidence"] == baseline["promotion_evidence"],
        "Registry promotion evidence mismatch",
    )
    require(
        baseline["source_combined_manifest"]["sha256"]
        == r5.git_blob_sha(baseline["source_combined_manifest"]["path"]),
        "Authority manifest SHA mismatch",
    )
    require(
        combined["manifest_content_sha256"] == r5.digest(combined_manifest),
        "Authority manifest content mismatch",
    )
    require(
        baseline["semantic_runtime_sha256"]
        == registry["semantic_runtime_sha256"]
        == combined["semantic_runtime_sha256"]
        == combined_manifest["semantic_runtime_sha256"],
        "Runtime mismatch",
    )
    require(
        baseline["schedule_identity"]
        == registry["schedule_identity"]
        == combined["schedule_sha256"]
        == combined_manifest["schedule_sha256"],
        "Schedule mismatch",
    )
    require(
        combined["logical_matchups"] == combined_manifest["logical_matchups"] == 45,
        "Wrong matchup count",
    )
    require(
        combined["logical_games"] == combined_manifest["logical_games"] == 4500,
        "Wrong logical games",
    )
    require(
        combined["reused_games"] == combined_manifest["reused_games"] == 4500, "Wrong reused games"
    )
    require(
        combined["newly_executed_games"] == combined_manifest["newly_executed_games"] == 0,
        "New games present",
    )
    require(combined["runtime_errors"] == 0, "Runtime errors present")
    require(len(combined["combined_games"]) == 4500, "Incomplete raw games")
    selected = {row["deck_key"]: row for row in combined_manifest["decks"]}
    baseline_decks = {row["deck_key"]: row for row in baseline["decks"]}
    require(len(selected) == len(baseline_decks) == 10, "Wrong deck roster")
    for deck, row in selected.items():
        require(row["sha256"] == baseline_decks[deck]["sha256"], f"Deck hash mismatch: {deck}")
    groups = c4.grouped(combined["combined_games"])
    schedule = c4.schedules_by_pair(r1.schedule())
    provenance = {tuple(row["decks"]): row for row in combined["provenance"]}
    require(len(groups) == len(schedule) == len(provenance) == 45, "Incomplete cell provenance")
    require(set(groups) == set(schedule) == set(provenance), "Cell pairing mismatch")
    fingerprints = []
    for pair in sorted(groups):
        row = provenance[pair]
        games = groups[pair]
        require(row["game_count"] == len(games) == 100, f"Cell size mismatch: {pair}")
        require(
            row["orientation_counts"] == {"canonical": 50, "reversed": 50},
            f"Start mismatch: {pair}",
        )
        require(
            Counter(game["schedule"]["orientation"] for game in games)
            == {"canonical": 50, "reversed": 50},
            f"Actual start mismatch: {pair}",
        )
        require(
            row["semantic_runtime_sha256"] == baseline["semantic_runtime_sha256"],
            f"Runtime cell mismatch: {pair}",
        )
        require(
            row["schedule_sha256"] == baseline["schedule_identity"], f"Seed cell mismatch: {pair}"
        )
        require(
            row["deck_sha256"] == {deck: baseline_decks[deck]["sha256"] for deck in pair},
            f"Cell deck mismatch: {pair}",
        )
        require(
            row["matchup_fingerprint"] == c4.verify_cell(games, schedule[pair], str(pair)),
            f"Cell fingerprint mismatch: {pair}",
        )
        fingerprints.append({"decks": list(pair), "fingerprint": row["matchup_fingerprint"]})
    digest = hashlib.sha256(
        json.dumps(fingerprints, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    require(baseline["matchup_fingerprint_digest_sha256"] == digest, "Cell digest mismatch")
    metrics, win_rates, rows = recompute(combined["combined_games"])
    require(rows == combined["matchups"], "Raw matchup summary differs")
    require(
        metrics == combined["combined_005_global_metrics"], "Combined metrics differ from raw games"
    )
    require(
        metrics == baseline["environment_metrics"] == registry["environment_metrics"],
        "Direct-promotion global metric mismatch",
    )
    summary = r1.aggregate(combined["combined_games"], r1.DECKS)
    deck_metrics = b3.per_deck(summary, b3.matchup_rows(combined["combined_games"]))
    deck_metrics = {
        deck: {**row, "most_extreme_matchup": b4._most_extreme(row)}
        for deck, row in deck_metrics.items()
    }
    require(win_rates == baseline["per_deck_win_rates"], "Baseline deck WR mismatch")
    registry_decks = {row["deck_key"]: row for row in registry["decks"]}
    for deck in baseline_decks:
        require(summary[deck]["win_rate"] == win_rates[deck], f"Raw deck WR mismatch: {deck}")
        require(
            win_rates[deck] == combined["combined_005_deck_summary"][deck]["win_rate"],
            f"Authority deck WR mismatch: {deck}",
        )
        require(
            deck_metrics[deck] == combined["per_deck_comparison"][deck]["combined_005"],
            f"Authority deck metrics mismatch: {deck}",
        )
        require(
            deck_metrics[deck]
            == baseline["per_deck_metrics"][deck]
            == registry["per_deck_metrics"][deck],
            f"Baseline deck metrics mismatch: {deck}",
        )
        require(
            registry_decks[deck]["aggregate_baseline_win_rate"] == win_rates[deck],
            f"Registry deck WR mismatch: {deck}",
        )
        require(
            registry_decks[deck]["mean_matchup_balance_error"]
            == deck_metrics[deck]["mean_matchup_balance_error"],
            f"Registry deck balance mismatch: {deck}",
        )
    require(
        metrics["worst_matchup"]["win_rates"] == {"krang": 0.12, "shredder": 0.88},
        "Carried-forward risk missing",
    )
    return {
        "status": "PASS",
        "environment": "OBL-BASELINE-003",
        "matchups": 45,
        "logical_games": 4500,
        "new_simulations": 0,
        "mean_matchup_balance_error": metrics["mean_matchup_balance_error"],
        "fingerprint_digest_sha256": digest,
    }


def main() -> int:
    print(json.dumps(validate(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
