"""Check that a simulation-free baseline promotion retains its combined evidence."""

from __future__ import annotations

import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
AUTHORITY_PATH = "docs/objective-balance-lab/COMBINED_003_RUNTIME_COMPATIBLE_EVIDENCE.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def recorded_evidence_sha_bytes(raw: bytes) -> str:
    """Reconstruct the CRLF byte hash recorded by the Windows promotion run."""
    lf = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(lf.replace(b"\n", b"\r\n")).hexdigest()


def recorded_evidence_sha(relative: str) -> str:
    return recorded_evidence_sha_bytes((ROOT / relative).read_bytes())


def fingerprint(games: list[dict]) -> str:
    raw = json.dumps(games, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def group_games(games: list[dict]) -> dict[tuple[str, str], list[dict]]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for game in games:
        require(len(game["seats"]) == 2, "A game must have two seats")
        grouped[tuple(sorted(game["seats"]))].append(game)
    return dict(grouped)


def recompute(games: list[dict]) -> tuple[dict, dict[str, float], list[dict]]:
    """Use game records, not stored matchup or summary values."""
    grouped = group_games(games)
    require(len(games) == 4500 and len(grouped) == 45, "Expected a complete 45-cell matrix")
    require(all(len(cell) == 100 for cell in grouped.values()), "Expected 100 games per cell")
    decks = sorted({deck for pair in grouped for deck in pair})
    require(len(decks) == 10, "Expected ten decks")
    rows = []
    for pair, cell in sorted(grouped.items()):
        draws = sum(bool(game["draw"]) for game in cell)
        rates = {
            deck: round((sum(game["winner"] == deck for game in cell) + draws / 2) / 100, 6)
            for deck in pair
        }
        winner = max(rates, key=rates.get)
        rows.append(
            {
                "decks": list(pair),
                "games": 100,
                "win_rates": rates,
                "winner_side": winner,
                "deviation": round(abs(rates[winner] - 0.5), 6),
            }
        )
    per_deck = {}
    first_seat_rates = []
    for deck in decks:
        own = [game for game in games if deck in game["seats"]]
        starts = [game for game in own if game["first_player"] == deck]
        require(len(own) == 900 and len(starts) == 450, f"Unbalanced sample for {deck}")
        draws = sum(bool(game["draw"]) for game in own)
        per_deck[deck] = round(
            (sum(game["winner"] == deck for game in own) + draws / 2) / len(own), 6
        )
        # The authoritative OBL first-seat metric counts wins, then averages the
        # ten deck-specific rates. It does not award half a win for a draw here.
        first_seat_rates.append(
            round(sum(game["winner"] == deck for game in starts) / len(starts), 6)
        )
    turns = [game["turn"] for game in games if game.get("turn") is not None]
    deviations = [row["deviation"] for row in rows]
    metrics = {
        "mean_matchup_balance_error": round(statistics.mean(deviations), 6),
        "median_matchup_deviation": round(statistics.median(deviations), 6),
        "worst_matchup": max(rows, key=lambda row: row["deviation"]),
        "over_60_40": sum(row["deviation"] > 0.1 for row in rows),
        "over_70_30": sum(row["deviation"] > 0.2 for row in rows),
        "aggregate_win_rate_spread": round(max(per_deck.values()) - min(per_deck.values()), 6),
        "aggregate_win_rate_stddev": round(statistics.pstdev(per_deck.values()), 6),
        "mean_first_player_result_rate": round(statistics.mean(first_seat_rates), 6),
        "mean_ending_turn": round(statistics.mean(turns), 4),
        "median_ending_turn": statistics.median(turns),
    }
    return metrics, per_deck, rows


def validate_direct_promotion(
    baseline: dict,
    authority: dict,
    authority_manifest: dict,
    registry: dict,
    authority_path: str,
) -> tuple[dict, dict[str, float], str]:
    """Reusable invariant for direct promotions with zero new simulations."""
    source = baseline["source_combined_evidence"]
    require(source["path"] == authority_path, "Wrong combined authority evidence path")
    require(
        source["sha256"] == recorded_evidence_sha(source["path"]),
        "Combined authority SHA mismatch",
    )
    require(
        baseline["source_combined_environment"]
        == authority["environment_id"]
        == authority_manifest["environment_id"],
        "Promotion authority environment mismatch",
    )
    require(
        baseline["semantic_runtime_sha256"]
        == authority["semantic_runtime_sha256"]
        == authority_manifest["semantic_runtime_sha256"],
        "Promotion semantic runtime mismatch",
    )
    require(
        baseline["schedule_identity"]
        == authority["schedule_sha256"]
        == authority_manifest["schedule_sha256"],
        "Promotion seed schedule mismatch",
    )
    require(
        authority["newly_executed_games"] == authority_manifest["newly_executed_games"] == 0,
        "This direct promotion must have zero new games",
    )
    require(
        authority["logical_games"] == authority_manifest["logical_games"] == 4500,
        "Wrong authority game count",
    )
    # The builder hashes its LF-rendered JSON text; Windows checkout may store CRLF.
    authority_manifest_text = (ROOT / authority["manifest_path"]).read_text(encoding="utf-8")
    require(
        authority["manifest_sha256"]
        == hashlib.sha256(authority_manifest_text.encode()).hexdigest(),
        "Combined authority manifest SHA mismatch",
    )
    baseline_decks = {row["deck_key"]: row for row in baseline["decks"]}
    authority_decks = {row["deck_key"]: row for row in authority_manifest["decks"]}
    registry_decks = {row["deck_key"]: row for row in registry["decks"]}
    require(
        len(baseline_decks) == len(authority_decks) == len(registry_decks) == 10,
        "Promotion requires ten unique decks",
    )
    for deck, row in baseline_decks.items():
        require(deck in authority_decks and deck in registry_decks, f"Missing deck {deck}")
        require(
            row["sha256"] == authority_decks[deck]["sha256"] == registry_decks[deck]["sha256"],
            f"Deck hash mismatch: {deck}",
        )
        path = ROOT / row["source_path"]
        require(path.is_file(), f"Missing deck file: {deck}")
        # Legacy prototype hashes were recorded from CRLF bytes. Promoted
        # candidate hashes use LF text. Reconstruct exactly the convention
        # declared by the deck's source type on either checkout platform.
        raw = path.read_bytes()
        if row["source_kind"] == "retained_baseline":
            actual = recorded_evidence_sha_bytes(raw)
        else:
            require(row["source_kind"] == "promoted_candidate", f"Unknown source type: {deck}")
            lf = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            actual = hashlib.sha256(lf).hexdigest()
        require(actual == row["sha256"], f"Deck file hash mismatch: {deck}")
    groups = group_games(authority["combined_games"])
    require(len(authority["provenance"]) == 45, "Wrong provenance cell count")
    fingerprints = []
    for record in authority["provenance"]:
        pair = tuple(record["decks"])
        require(pair in groups, f"Missing source cell: {pair}")
        require(record["games"] == len(groups[pair]) == 100, f"Wrong game count: {pair}")
        require(
            Counter(game["schedule"]["orientation"] for game in groups[pair])
            == Counter({"canonical": 50, "reversed": 50}),
            f"Orientation mismatch: {pair}",
        )
        require(
            record["deck_hashes"] == {deck: baseline_decks[deck]["sha256"] for deck in pair},
            f"Provenance deck hashes differ: {pair}",
        )
        require(
            record["schedule_sha256"] == baseline["schedule_identity"]
            and record["semantic_runtime_sha256"] == baseline["semantic_runtime_sha256"],
            f"Provenance identity mismatch: {pair}",
        )
        require(
            record["fingerprint"] == fingerprint(groups[pair]), f"Cell fingerprint mismatch: {pair}"
        )
        fingerprints.append({"decks": list(pair), "fingerprint": record["fingerprint"]})
    require(len({tuple(row["decks"]) for row in fingerprints}) == 45, "Duplicate provenance cell")
    metrics, per_deck, rows = recompute(authority["combined_games"])
    require(rows == authority["matchups"], "Authority matchup summary differs from raw games")
    require(
        metrics == authority["combined_global_metrics"],
        "Authority global metrics differ from raw games",
    )
    require(
        metrics == baseline["environment_metrics"],
        "Baseline reference metrics differ from authority",
    )
    require(metrics == registry["environment_metrics"], "Registry metrics differ from authority")
    require(
        registry["source_combined_environment"] == authority["environment_id"]
        and registry["source_combined_evidence"] == source
        and registry["reference_evidence"] == source,
        "Registry points to a different combined evidence source",
    )
    for deck, rate in per_deck.items():
        require(
            rate == authority["combined_deck_summary"][deck]["win_rate"], f"Authority WR: {deck}"
        )
        require(rate == registry_decks[deck]["aggregate_baseline_win_rate"], f"Registry WR: {deck}")
    digest = hashlib.sha256(
        json.dumps(
            sorted(fingerprints, key=lambda row: row["decks"]),
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    return metrics, per_deck, digest


def validate_baseline002() -> tuple[dict, dict[str, float], str]:
    baseline = load("docs/objective-balance-lab/baselines/OBL_BASELINE_002_MANIFEST.json")
    authority = load(AUTHORITY_PATH)
    authority_manifest = load(
        "docs/objective-balance-lab/combined/OBL_COMBINED_003_RUNTIME_COMPATIBLE_MANIFEST.json"
    )
    registry = load("docs/objective-balance-lab/ENVIRONMENT_REGISTRY.json")
    require(
        baseline["environment_id"] == registry["environment_id"] == "OBL-BASELINE-002",
        "Baseline identity mismatch",
    )
    return validate_direct_promotion(
        baseline, authority, authority_manifest, registry, AUTHORITY_PATH
    )
