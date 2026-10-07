"""Read-only B&R loss-signature diagnosis from the corrected Baseline 004 control."""

# Full Markdown report rows are retained as literals.
# ruff: noqa: E501

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
CONTROL = OBL / "BASELINE_004_CYCLING_PILOT_CONTROL.json.gz"
ANALYSIS = OBL / "BASELINE_004_CYCLING_PILOT_ANALYSIS.json"
MANIFEST = OBL / "baselines/OBL_BASELINE_004_MANIFEST.json"
OUTPUT = OBL / "ROUND_8_BEBOP_CORRECTED_CONTROL_DIAGNOSTIC.json"
REPORT = OBL / "ROUND_8_BEBOP_CORRECTED_CONTROL_DIAGNOSTIC.md"
B = "bebop_rocksteady"
FUNCTIONAL = ("donatello", "leonardo", "krang")
SEVERE = ("raphael", "shredder", "splinter")
CYCLERS = ("Bebop, Warthog Warrior", "Rocksteady, Crash Courser")
DECKS = (
    "leonardo",
    "raphael",
    "donatello",
    "michelangelo",
    "splinter",
    "shredder",
    "krang",
    B,
    "april_oneil",
    "casey_jones",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def first4(game: dict, deck: str) -> bool:
    turn = game["first"][deck]["creature"]
    return turn is not None and turn <= 4


def cycling(game: dict) -> list[dict]:
    return [
        event
        for event in game["activation_events"]
        if event["event"] == "activation_announced"
        and event.get("player") == B
        and event.get("source") in CYCLERS
        and "cycling" in event.get("oracle_fragment", "").lower()
    ]


def aggregate(games: list[dict]) -> dict:
    assert games
    opponents = {next(deck for deck in game["seats"] if deck != B) for game in games}
    casts = Counter()
    opposing_casts = Counter()
    for game in games:
        opponent = next(deck for deck in game["seats"] if deck != B)
        for key, quantity in game["signature_casts"].items():
            if key.startswith(f"{B}:"):
                casts[key[len(B) + 1 :]] += quantity
            if key.startswith(f"{opponent}:"):
                opposing_casts[key] += quantity
    result = {
        "games": len(games),
        "wins": sum(game["winner"] == B for game in games),
        "draws": sum(game["draw"] for game in games),
        "first_player_games": sum(game["first_player"] == B for game in games),
        "first_player_wins": sum(
            game["winner"] == B and game["first_player"] == B for game in games
        ),
        "bebop_first_creature_by_turn_4": sum(first4(game, B) for game in games),
        "opponent_first_creature_by_turn_4": sum(
            first4(game, next(deck for deck in game["seats"] if deck != B)) for game in games
        ),
        "bebop_no_creature": sum(game["first"][B]["creature"] is None for game in games),
        "bebop_casts": sum(game["casts"].get(B, 0) for game in games),
        "opponent_casts": sum(
            game["casts"].get(next(deck for deck in game["seats"] if deck != B), 0)
            for game in games
        ),
        "bebop_cycler_casts": {card: casts[card] for card in CYCLERS},
        "bebop_cycling_activations": sum(len(cycling(game)) for game in games),
        "bebop_cycling_games": sum(bool(cycling(game)) for game in games),
        "bebop_battlefield_presence_mean": {
            str(turn): round(
                statistics.mean(
                    game["battlefield_presence"].get(B, {}).get(str(turn), 0) for game in games
                ),
                4,
            )
            for turn in (3, 5, 7)
        },
        "opponent_battlefield_presence_mean": {
            str(turn): round(
                statistics.mean(
                    game["battlefield_presence"]
                    .get(next(deck for deck in game["seats"] if deck != B), {})
                    .get(str(turn), 0)
                    for game in games
                ),
                4,
            )
            for turn in (3, 5, 7)
        },
        "mean_ending_turn": round(statistics.mean(game["turn"] for game in games), 4),
        "ending_by_turn_17": sum(game["turn"] <= 17 for game in games),
        "ending_turn_histogram": dict(
            sorted(
                Counter(str(game["turn"]) for game in games).items(),
                key=lambda item: int(item[0]),
            )
        ),
        "bebop_signature_casts": dict(sorted(casts.items())),
        "opponent_signature_casts": dict(sorted(opposing_casts.items())),
        "opponents": sorted(opponents),
    }
    return result


def build() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    analysis = json.loads(ANALYSIS.read_text(encoding="utf-8"))
    control = json.loads(gzip.decompress(CONTROL.read_bytes()))
    assert manifest["environment_id"] == control["environment_id"] == "OBL-BASELINE-004"
    assert control["status"] == "COMPLETE" and control["runtime_errors"] == 0
    assert len(control["games"]) == 4500 and len(control["cell_hashes"]) == 45
    assert len(control["replays"]) == 6
    assert analysis["control_evidence_sha256"] == sha(CONTROL)
    assert analysis["baseline_manifest_sha256"] == sha(MANIFEST)
    assert analysis["new_semantic_runtime_sha256"] == control["semantic_runtime_sha256"]
    assert (
        analysis["schedule_sha256"] == control["schedule_sha256"] == manifest["schedule_identity"]
    )
    assert {row["deck_key"]: row["sha256"] for row in control["baseline_decks"]} == {
        row["deck_key"]: row["sha256"] for row in manifest["decks"]
    }
    games = [game for game in control["games"] if B in game["seats"]]
    assert len(games) == 900 and all(game["runtime_error"] is None for game in games)
    by_opponent = {}
    for opponent in DECKS:
        if opponent == B:
            continue
        cell = [game for game in games if opponent in game["seats"]]
        assert len(cell) == 100
        assert Counter(game["first_player"] for game in cell) == {B: 50, opponent: 50}
        wins = [game for game in cell if game["winner"] == B]
        losses = [game for game in cell if game["winner"] != B]
        by_opponent[opponent] = {
            "all": aggregate(cell),
            "wins": aggregate(wins) if wins else None,
            "nonwins": aggregate(losses) if losses else None,
            "prior_win_rate": analysis["prior_per_deck"][B]["matchup_win_rates"][opponent],
            "corrected_win_rate": analysis["new_per_deck"][B]["matchup_win_rates"][opponent],
        }
        assert (
            by_opponent[opponent]["all"]["wins"] / 100
            == by_opponent[opponent]["corrected_win_rate"]
        )
    groups = {}
    for label, opponents in (("relatively_functional", FUNCTIONAL), ("severe", SEVERE)):
        selected = [game for game in games if any(opp in game["seats"] for opp in opponents)]
        assert len(selected) == 300
        groups[label] = {
            "all": aggregate(selected),
            "wins": aggregate([game for game in selected if game["winner"] == B]),
            "nonwins": aggregate([game for game in selected if game["winner"] != B]),
        }
    assert sum(row["all"]["wins"] for row in by_opponent.values()) == 210
    return {
        "schema": "obl-round8-bebop-corrected-control-diagnostic-v1",
        "status": "DIAGNOSTIC_ONLY_RETURN_TO_DESIGN_STUDIO",
        "environment_id": "OBL-BASELINE-004",
        "control_id": control["evidence_id"],
        "control_sha256": sha(CONTROL),
        "analysis_sha256": sha(ANALYSIS),
        "manifest_git_blob_sha1": "cc17b1760410d7a8547626bb9dbd4a0cd534207f",
        "semantic_runtime_sha256": control["semantic_runtime_sha256"],
        "schedule_sha256": control["schedule_sha256"],
        "baseline_decks": {row["deck_key"]: row["sha256"] for row in manifest["decks"]},
        "games_analyzed": 900,
        "new_games": 0,
        "by_opponent": by_opponent,
        "comparison_groups": groups,
        "telemetry_limits": [
            "No attack declarations or per-turn life/damage progression in game summaries.",
            "No resolved removal target history, per-turn hand composition, or unused mana.",
            "Cast totals depend on game length; grouped cast differences are descriptive, not causal.",
            "Battlefield presence uses available fixed-turn snapshots; absent snapshots count zero.",
            "First creature is a game summary timing proxy, not threat-quality measurement.",
        ],
        "candidate_authorized": False,
        "promotion_authorized": False,
    }


def report(data: dict) -> str:
    rows = data["by_opponent"]
    labels = {
        "raphael": "Raphael",
        "shredder": "Shredder",
        "splinter": "Splinter",
        "casey_jones": "Casey Jones",
        "donatello": "Donatello",
        "leonardo": "Leonardo",
        "krang": "Krang",
        "michelangelo": "Michelangelo",
        "april_oneil": "April O'Neil",
    }
    lines = [
        "# Round 8 — B&R corrected-control loss signatures",
        "",
        "**Diagnostic only.** Exact Baseline 004 B&R list, no new games, no candidate or promotion. This uses the merged 4,500-game cycling-pilot control; B&R appears in 900 games, 100 against each opponent with 50 starts on each side.",
        "",
        f"Runtime `{data['semantic_runtime_sha256']}`; control `{data['control_id']}`; schedule `{data['schedule_sha256']}`. All ten deck hashes match the immutable Baseline 004 manifest. Raw and derived evidence are hash-linked in the [machine diagnosis](ROUND_8_BEBOP_CORRECTED_CONTROL_DIAGNOSTIC.json).",
        "",
        "## Nine matchups",
        "",
        "| Opponent | Old → corrected B&R WR | B&R first creature ≤4 | Opponent first creature ≤4 | B&R casts | Cycler casts | Cycling activations | Mean end turn |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for opponent in (
        "raphael",
        "shredder",
        "splinter",
        "casey_jones",
        "donatello",
        "leonardo",
        "krang",
        "michelangelo",
        "april_oneil",
    ):
        item = rows[opponent]
        cell = item["all"]
        cycler_casts = sum(cell["bebop_cycler_casts"].values())
        lines.append(
            f"| {labels[opponent]} | {item['prior_win_rate']:.0%} → {item['corrected_win_rate']:.0%} | {cell['bebop_first_creature_by_turn_4']}/100 | {cell['opponent_first_creature_by_turn_4']}/100 | {cell['bebop_casts']} | {cycler_casts} | {cell['bebop_cycling_activations']} | {cell['mean_ending_turn']:.1f} |"
        )
    functional = data["comparison_groups"]["relatively_functional"]["all"]
    severe = data["comparison_groups"]["severe"]["all"]
    lines += [
        "",
        "## What separates the groups",
        "",
        "The relatively functional Donatello/Leonardo/Krang cells total **97/300 B&R wins (32.33%)**. Raphael/Shredder/Splinter total **36/300 (12.00%)**; Casey is **16/100**. These are descriptive groupings, not deck-change experiments.",
        "",
        f"B&R has a first creature by turn 4 in **{functional['bebop_first_creature_by_turn_4']}/300** functional games and **{severe['bebop_first_creature_by_turn_4']}/300** severe games. The opponent reaches that timing in **{functional['opponent_first_creature_by_turn_4']}/300** versus **{severe['opponent_first_creature_by_turn_4']}/300**. B&R's early creature timing alone does not explain the severe split. Leonardo reaches an early creature in 93/100 games yet B&R wins 31/100 there, so opposing first-creature timing is not a complete explanation either.",
        "",
        f"Severe games end sooner on average (**{severe['mean_ending_turn']:.1f}** vs **{functional['mean_ending_turn']:.1f}** turns). B&R records **{sum(severe['bebop_cycler_casts'].values())}** Bebop/Rocksteady casts in the severe group versus **{sum(functional['bebop_cycler_casts'].values())}** in the functional group, with **{severe['bebop_cycling_activations']}** versus **{functional['bebop_cycling_activations']}** cycling activations. Total B&R casts are **{severe['bebop_casts']}** versus **{functional['bebop_casts']}**. Shorter games reduce casting opportunities, so these counts identify a conversion gap without proving its cause.",
        "",
        f"B&R's turn-5 battlefield-presence proxy is **{functional['bebop_battlefield_presence_mean']['5']:.2f}** in functional cells and **{severe['bebop_battlefield_presence_mean']['5']:.2f}** in severe cells. Its early board is not simply absent in the severe group. The summaries do not say how much damage that board dealt or how it traded.",
        "",
        "Across all 900 corrected games, the cast signatures still record zero casts of Bebop & Rocksteady, Mutagen Man, Living Ooze, Cowabunga!, Mutant Chain Reaction, Stomped by the Foot, and Illegitimate Business. This is an execution/measurement limit of the fixed-pilot simulation; the summaries do not establish why each card was absent.",
        "",
        "Against Raphael, Shredder, Splinter, and Casey, the mean end turn is 15.7–17.1; B&R's corrected WR is 11–16%. Donatello, Leonardo, and Krang games last 19.3–24.5 turns on average and yield 27–39% B&R WR. The corrected pilot restored the choice to cast cycling creatures, while severe cells still show a poor measured conversion of early board presence into wins.",
        "",
        "## Execution and telemetry boundary",
        "",
        "The full per-opponent and win/nonwin splits include cast signatures, early creature timing, fixed-turn board presence, cycling activations, and ending-turn histograms. Opponent casts and named-card associations can be inspected there. These summaries do not contain attack declarations, damage/life trajectories, resolved removal targets, per-turn hands, or unused mana. They cannot establish a particular lethal sequence or credit a specific card as the cause of a loss. Recorded casts are also sensitive to ending turn.",
        "",
        "## Design Studio handoff",
        "",
        "**Diagnosis authorized; candidate design remains unauthorized.** The simulation reference for unchanged Baseline 004 is the corrected control. Design Studio should interpret the early timing and conversion gap, particularly Raphael/Shredder/Splinter and Casey, before choosing any card intervention. The original Combined 006 promotion record remains historical; no Baseline 005 is created.",
        "",
        "[Corrected control](BASELINE_004_CYCLING_PILOT_CONTROL.json.gz) · [45-cell analysis](BASELINE_004_CYCLING_PILOT_ANALYSIS.json) · [machine diagnosis](ROUND_8_BEBOP_CORRECTED_CONTROL_DIAGNOSTIC.json).",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    data = build()
    if args.write:
        OUTPUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        REPORT.write_text(report(data), encoding="utf-8")
    print(
        json.dumps(
            {"status": data["status"], "games_analyzed": data["games_analyzed"], "new_games": 0}
        )
    )


if __name__ == "__main__":
    main()
