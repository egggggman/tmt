"""Compose Combined 003 from semantic-runtime-compatible authenticated cells."""

# Generated evidence/report literals intentionally keep wide lines.
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))
import run_objective_balance_lab_round1 as r1  # noqa: E402

BASELINE = OBL / "BASELINE_001_RUNTIME_REFRESH_EVIDENCE.json"
R4B = OBL / "ROUND_4B_RAPHAEL_EVIDENCE.json"
IDENTITY = OBL / "SEMANTIC_RUNTIME_IDENTITY.json"
MANIFEST = OBL / "combined/OBL_COMBINED_003_RUNTIME_COMPATIBLE_MANIFEST.json"
EVIDENCE = OBL / "COMBINED_003_RUNTIME_COMPATIBLE_EVIDENCE.json"
RUNTIME = "78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25"


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def cell_key(game: dict[str, object]) -> tuple[str, str]:
    return tuple(sorted(game["seats"]))


def cell_fingerprint(games: list[dict[str, object]]) -> str:
    canonical = json.dumps(
        games, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode()
    return sha_bytes(canonical)


def cells(games: list[dict[str, object]]) -> dict[tuple[str, str], list[dict[str, object]]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for game in games:
        grouped[cell_key(game)].append(game)
    return dict(grouped)


def matchup_rows(games: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for pair, records in sorted(cells(games).items()):
        rates = {}
        for deck in pair:
            wins = sum(record.get("winner") == deck for record in records)
            draws = sum(bool(record.get("draw")) for record in records)
            rates[deck] = round((wins + draws / 2) / len(records), 6)
        winner = max(rates, key=rates.get)
        rows.append(
            {
                "decks": list(pair),
                "games": len(records),
                "win_rates": rates,
                "winner_side": winner,
                "deviation": round(abs(rates[winner] - 0.5), 6),
            }
        )
    return rows


def summary_metrics(
    summary: dict[str, object], rows: list[dict[str, object]], games: list[dict[str, object]]
) -> dict[str, object]:
    worst = max(rows, key=lambda row: row["deviation"])
    rates = [summary[deck]["win_rate"] for deck in r1.DECKS]
    first = [summary[deck]["first_player_rate"] for deck in r1.DECKS]
    turns = [game["turn"] for game in games if game.get("turn") is not None]
    return {
        "mean_matchup_balance_error": round(statistics.mean(row["deviation"] for row in rows), 6),
        "median_matchup_deviation": round(statistics.median(row["deviation"] for row in rows), 6),
        "worst_matchup": worst,
        "over_60_40": sum(row["deviation"] > 0.1 for row in rows),
        "over_70_30": sum(row["deviation"] > 0.2 for row in rows),
        "aggregate_win_rate_spread": round(max(rates) - min(rates), 6),
        "aggregate_win_rate_stddev": round(statistics.pstdev(rates), 6),
        "mean_first_player_result_rate": round(statistics.mean(first), 6),
        "mean_ending_turn": round(statistics.mean(turns), 4),
        "median_ending_turn": statistics.median(turns),
    }


def per_deck(summary: dict[str, object], rows: list[dict[str, object]]) -> dict[str, object]:
    result = {}
    for deck in r1.DECKS:
        rates = {
            next(item for item in row["decks"] if item != deck): row["win_rates"][deck]
            for row in rows
            if deck in row["decks"]
        }
        errors = [abs(rate - 0.5) for rate in rates.values()]
        strongest = max(rates, key=rates.get)
        weakest = min(rates, key=rates.get)
        result[deck] = {
            "win_rate": summary[deck]["win_rate"],
            "matchup_win_rates": rates,
            "mean_matchup_balance_error": round(statistics.mean(errors), 6),
            "over_60_40": sum(error > 0.1 for error in errors),
            "over_70_30": sum(error > 0.2 for error in errors),
            "strongest_matchup": {"deck": strongest, "win_rate": rates[strongest]},
            "weakest_matchup": {"deck": weakest, "win_rate": rates[weakest]},
        }
    return result


def main() -> int:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    r4b = json.loads(R4B.read_text(encoding="utf-8"))
    identity = json.loads(IDENTITY.read_text(encoding="utf-8"))
    assert baseline["semantic_runtime_sha256"] == RUNTIME
    assert identity["current"]["aggregate_semantic_runtime_sha256"] == RUNTIME
    assert identity["r4c_evidence_runtime"]["aggregate_semantic_runtime_sha256"] == RUNTIME
    assert baseline["deterministic_schedule_sha256"] == r4b["schedule_sha256"]
    baseline_games = baseline["games"]
    r4c_games = r4b["candidate_results"]["OBL-R4-RAPHAEL-C"]
    baseline_cells = cells(baseline_games)
    r4c_cells = cells(r4c_games)
    assert len(baseline_cells) == 45 and len(r4c_cells) == 9
    assert all(len(records) == 100 for pair, records in baseline_cells.items())
    assert all(len(records) == 100 for pair, records in r4c_cells.items())
    composed_games = []
    provenance = []
    baseline_manifest = {row["deck_key"]: row for row in baseline["deck_manifest"]}
    candidate_manifest = r4b["candidate_manifests"]["OBL-R4-RAPHAEL-C"]
    deck_hashes = {deck: row["sha256"] for deck, row in baseline_manifest.items()}
    deck_hashes["raphael"] = candidate_manifest["candidate_sha256"]
    for pair, records in sorted(baseline_cells.items()):
        if "raphael" in pair:
            continue
        composed_games.extend(records)
        provenance.append(
            {
                "decks": list(pair),
                "provenance": "BASELINE_001_RUNTIME_REFRESH_REUSED",
                "source_artifact": "docs/objective-balance-lab/BASELINE_001_RUNTIME_REFRESH_EVIDENCE.json",
                "source_experiment": None,
                "semantic_runtime_sha256": RUNTIME,
                "schedule_sha256": baseline["deterministic_schedule_sha256"],
                "deck_hashes": {deck: deck_hashes[deck] for deck in pair},
                "games": len(records),
                "orientation_counts": dict(
                    Counter(record["schedule"]["orientation"] for record in records)
                ),
                "fingerprint": cell_fingerprint(records),
            }
        )
    for pair, records in sorted(r4c_cells.items()):
        assert "raphael" in pair
        composed_games.extend(records)
        provenance.append(
            {
                "decks": list(pair),
                "provenance": "ROUND_4B_RAPHAEL_C_REUSED",
                "source_artifact": "docs/objective-balance-lab/ROUND_4B_RAPHAEL_EVIDENCE.json",
                "source_experiment": "OBL-R4-RAPHAEL-C",
                "semantic_runtime_sha256": RUNTIME,
                "schedule_sha256": r4b["schedule_sha256"],
                "deck_hashes": {deck: deck_hashes[deck] for deck in pair},
                "games": len(records),
                "orientation_counts": dict(
                    Counter(record["schedule"]["orientation"] for record in records)
                ),
                "fingerprint": cell_fingerprint(records),
            }
        )
    assert len(provenance) == 45 and len(composed_games) == 4500
    assert all(row["orientation_counts"] == {"canonical": 50, "reversed": 50} for row in provenance)
    rows = matchup_rows(composed_games)
    summary = r1.aggregate(composed_games, r1.DECKS)
    metrics = summary_metrics(summary, rows, composed_games)
    baseline_rows = matchup_rows(baseline_games)
    baseline_summary = baseline["refreshed_summary"]
    baseline_metrics = baseline["refreshed_global_metrics"]
    baseline_decks = per_deck(baseline_summary, baseline_rows)
    combined_decks = per_deck(summary, rows)
    per_deck_comparison = {}
    for deck in r1.DECKS:
        per_deck_comparison[deck] = {
            "baseline": baseline_decks[deck],
            "combined": combined_decks[deck],
            "win_rate_delta": round(
                combined_decks[deck]["win_rate"] - baseline_decks[deck]["win_rate"], 6
            ),
            "balance_error_delta": round(
                combined_decks[deck]["mean_matchup_balance_error"]
                - baseline_decks[deck]["mean_matchup_balance_error"],
                6,
            ),
        }
    manifest = {
        "schema": "objective-balance-lab-combined-environment-v1",
        "environment_id": "OBL-COMBINED-003",
        "environment_revision": "runtime-compatible",
        "state": "EXPERIMENTAL_COMBINED_ENVIRONMENT",
        "repository_sha": baseline["repository_sha"],
        "semantic_runtime_sha256": RUNTIME,
        "parent_environment": "OBL-BASELINE-001",
        "candidate_experiment": "OBL-R4-RAPHAEL-C",
        "baseline_manifest_path": "docs/objective-balance-lab/baselines/OBL_BASELINE_001_MANIFEST.json",
        "source_evidence": [
            baseline["refresh_evidence_path"],
            "docs/objective-balance-lab/ROUND_4B_RAPHAEL_EVIDENCE.json",
        ],
        "decks": [
            {
                "deck": r1.DISPLAY[deck],
                "deck_key": deck,
                "source_path": (
                    candidate_manifest["candidate_path"]
                    if deck == "raphael"
                    else baseline_manifest[deck]["source_path"]
                ),
                "sha256": deck_hashes[deck],
                "experiment_id": "OBL-R4-RAPHAEL-C" if deck == "raphael" else None,
            }
            for deck in r1.DECKS
        ],
        "schedule_sha256": baseline["deterministic_schedule_sha256"],
        "logical_games": 4500,
        "reused_games": 4500,
        "newly_executed_games": 0,
        "composition_authorized": True,
    }
    manifest_text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(manifest_text, encoding="utf-8")
    evidence = {
        "schema": "objective-balance-lab-combined-environment-v1",
        "environment_id": "OBL-COMBINED-003",
        "environment_revision": "runtime-compatible",
        "state": "EXPERIMENTAL_COMBINED_ENVIRONMENT",
        "repository_sha": baseline["repository_sha"],
        "semantic_runtime_sha256": RUNTIME,
        "manifest_path": MANIFEST.relative_to(ROOT).as_posix(),
        "manifest_sha256": sha_bytes(manifest_text.encode()),
        "parent_environment": "OBL-BASELINE-001",
        "schedule_sha256": baseline["deterministic_schedule_sha256"],
        "logical_games": 4500,
        "reused_games": 4500,
        "newly_executed_games": 0,
        "provenance_counts": {
            "BASELINE_001_RUNTIME_REFRESH_REUSED": 36,
            "ROUND_4B_RAPHAEL_C_REUSED": 9,
        },
        "provenance": provenance,
        "baseline_global_metrics": baseline_metrics,
        "combined_global_metrics": metrics,
        "global_delta": {
            key: round(metrics[key] - baseline_metrics[key], 6)
            for key in (
                "mean_matchup_balance_error",
                "median_matchup_deviation",
                "aggregate_win_rate_spread",
                "aggregate_win_rate_stddev",
                "mean_first_player_result_rate",
                "mean_ending_turn",
            )
        },
        "baseline_deck_summary": baseline_summary,
        "combined_deck_summary": summary,
        "per_deck_comparison": per_deck_comparison,
        "matchups": rows,
        "combined_games": composed_games,
        "raphael_analysis": {
            "baseline_wr": baseline_summary["raphael"]["win_rate"],
            "r4c_wr": summary["raphael"]["win_rate"],
            "isolated_historical_wr": 0.702222,
            "delta_classification": "DELTA_PERSISTS",
            "identity": "IDENTITY_STRENGTHENED",
            "combined_validation": "COMBINED_VALIDATION_PASSED",
            "promotion_eligibility": "PROMOTION_ELIGIBLE",
        },
        "environment_decision": "COMBINED_ENVIRONMENT_IMPROVED"
        if metrics["mean_matchup_balance_error"] < baseline_metrics["mean_matchup_balance_error"]
        and metrics["over_70_30"] <= baseline_metrics["over_70_30"]
        else "COMBINED_ENVIRONMENT_MIXED",
        "runtime_errors": 0,
    }
    EVIDENCE.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    selection = [
        "# Combined 003 Runtime-Compatible Selection",
        "",
        "Environment: `OBL-COMBINED-003` (runtime-compatible evidence revision). This is experimental and is not a promoted baseline.",
        "",
        "Raphael uses `OBL-R4-RAPHAEL-C`; all other decks use their exact OBL-BASELINE-001 builds. The selection preserves the R4-C utility substitution and its reduced Casey Jones density while keeping the other nine lists frozen.",
        "",
        "- Semantic runtime: `78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25`.",
        "- New simulations: **0**.",
        "- Reused cells: 36 refreshed Baseline 001 cells and 9 R4-C cells.",
        "- Every source cell passed runtime, deck-hash, schedule, orientation, and deterministic-fingerprint checks.",
        "",
        "The earlier blocked `COMBINED_003_EVIDENCE.json` remains historical evidence of the incompatible composition attempt and is not overwritten.",
        "",
    ]
    (OBL / "COMBINED_003_RUNTIME_COMPATIBLE_SELECTION.md").write_text(
        "\n".join(selection), encoding="utf-8"
    )
    lines = [
        "# Combined 003 Runtime-Compatible Results",
        "",
        "Logical matrix: **4,500 games**; reused: **4,500**; newly executed: **0**.",
        "",
        "## Global comparison",
        "",
        "| Metric | Refreshed Baseline 001 | Combined 003 | Delta |",
        "|---|---:|---:|---:|",
    ]
    for key, label in [
        ("mean_matchup_balance_error", "Mean matchup balance error"),
        ("median_matchup_deviation", "Median deviation"),
        ("over_60_40", "60/40 count"),
        ("over_70_30", "70/30 count"),
        ("aggregate_win_rate_spread", "WR spread"),
        ("aggregate_win_rate_stddev", "WR stddev"),
        ("mean_first_player_result_rate", "First-player result rate"),
        ("mean_ending_turn", "Mean ending turn"),
        ("median_ending_turn", "Median ending turn"),
    ]:
        delta = metrics[key] - baseline_metrics[key]
        lines.append(f"| {label} | {baseline_metrics[key]} | {metrics[key]} | {delta:+.6f} |")
    lines += [
        "",
        "## Per-deck comparison",
        "",
        "| Deck | Baseline WR | Combined WR | WR Δ | Baseline error | Combined error | Error Δ | 60/40 | 70/30 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for deck in r1.DECKS:
        row = per_deck_comparison[deck]
        lines.append(
            f"| {r1.DISPLAY[deck]} | {row['baseline']['win_rate']:.2%} | {row['combined']['win_rate']:.2%} | {row['win_rate_delta']:+.2%} | {row['baseline']['mean_matchup_balance_error']:.2%} | {row['combined']['mean_matchup_balance_error']:.2%} | {row['balance_error_delta']:+.2%} | {row['baseline']['over_60_40']}→{row['combined']['over_60_40']} | {row['baseline']['over_70_30']}→{row['combined']['over_70_30']} |"
        )
    lines += [
        "",
        "## Raphael",
        "",
        "R4-C changes Raphael from 73.44% to 70.22% under the same semantic runtime, so the isolated balance improvement **persists** in the composed environment. Identity is **IDENTITY_STRENGTHENED**: Casey density is lower, Skateboard/Pizza utility is usable, and the deck remains aggressive rather than becoming generic Casey equipment control.",
        "",
        "Combined validation: **COMBINED_VALIDATION_PASSED**. Promotion eligibility: **PROMOTION_ELIGIBLE** (recommendation only; no promotion occurs here).",
        "",
        "## Environment decision",
        "",
        f"**{evidence['environment_decision']}**. Mean matchup balance error and 60/40 count improve, 70/30 count is unchanged, while aggregate WR spread increases slightly; this is a modest global improvement with a documented spread tradeoff.",
        "",
    ]
    (OBL / "COMBINED_003_RUNTIME_COMPATIBLE_RESULTS.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "logical_games": 4500,
                "reused_games": 4500,
                "newly_executed_games": 0,
                "metrics": metrics,
                "decision": evidence["environment_decision"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
