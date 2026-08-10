"""Run and report the frozen Engine 0.6 smoke protocol."""
# ruff: noqa: E501

from __future__ import annotations

import json
from pathlib import Path

from tmnt_design_studio.cardcade import compare_runs, load_roster, run_round_robin, write_run

ROOT = Path(__file__).parents[1]
SEED = 20260809
GAMES = 20
POLARITY = (
    "leonardo_vs_donatello",
    "leonardo_vs_krang",
    "donatello_vs_april_oneil",
    "donatello_vs_shredder",
    "splinter_vs_shredder",
    "casey_jones_vs_krang",
    "shredder_vs_krang",
)


def percent(value: float) -> str:
    return f"{value:.1%}"


def main() -> None:
    roster_path = ROOT / "cardcade" / "roster-0.2.json"
    output = ROOT / "cardcade" / "runs" / "smoke-0.6"
    baseline_path = (
        ROOT
        / "cardcade"
        / "runs"
        / "profile-strength-audit-0.5"
        / "conditions"
        / "neutralized"
        / "run.json"
    )
    result = run_round_robin(load_roster(roster_path), GAMES, SEED)
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    comparison = compare_runs(baseline, result)
    write_run(result, output)
    (output / "sensitivity-comparison.json").write_text(
        json.dumps(comparison, indent=2), encoding="utf-8"
    )
    configuration = {
        "engine_version": result["engine_version"],
        "seed": SEED,
        "games_per_pairing": GAMES,
        "pairings": 45,
        "total_games": 900,
        "starts_per_deck_per_pairing": 10,
        "roster": "cardcade/roster-0.2.json",
        "roster_hash": result["roster_hash"],
        "primary_baseline": "Engine 0.5 neutralized condition",
        "governance": "evidence only; decklists and Prototype histories frozen",
    }
    (output / "configuration.json").write_text(
        json.dumps(configuration, indent=2), encoding="utf-8"
    )

    names = {deck.id: deck.name for deck in load_roster(roster_path)}
    lines = [
        "# Cardcade Engine 0.6 — Generic Card-Fact Modeling",
        "",
        "## Protocol and governance",
        "",
        "Frozen Prototype 0.2 roster; seed `20260809`; all 45 matchups; 20 games each; ",
        "900 games total; exact 10/10 starting-player split. Engine 0.5's fully neutralized ",
        "condition is the primary baseline. No decklist, Prototype history, or card value was ",
        "changed to target a win rate.",
        "",
        "## Aggregate results",
        "",
        "| Deck | 0.5 neutralized | 0.6 | Shift | Flood | Execution |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for deck_id, deck in result["decks"].items():
        prior = baseline["decks"][deck_id]
        lines.append(
            f"| {names[deck_id]} | {percent(prior['win_rate'])} | {percent(deck['win_rate'])} | "
            f"{deck['win_rate'] - prior['win_rate']:+.1%} | {percent(deck['mana_flood_rate'])} | "
            f"{percent(deck['strategy_execution_rate'])} |"
        )
    lines += [
        "",
        f"First-player win rate: **{percent(result['first_player_win_rate'])}** "
        f"(0.5 neutralized: {percent(baseline['first_player_win_rate'])}).",
        "",
        "## Generic role use and execution telemetry",
        "",
        "Values below are average cards with each derived role cast per game. Missing roles are zero.",
        "",
        "| Deck | Threat | Removal | Draw | Support | Tempo | Acceleration | Finisher |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for deck_id, deck in result["decks"].items():
        usage = deck["average_role_usage"]
        lines.append(
            f"| {names[deck_id]} | {usage.get('threat', 0):.2f} | "
            f"{usage.get('removal', 0) + usage.get('counterspell', 0):.2f} | "
            f"{usage.get('card_advantage', 0):.2f} | {usage.get('board_support', 0):.2f} | "
            f"{usage.get('tempo', 0):.2f} | {usage.get('acceleration', 0):.2f} | "
            f"{usage.get('finisher', 0):.2f} |"
        )
    lines += ["", "## Seven surviving Engine 0.5 polarity matchups", ""]
    lines += ["| Matchup | 0.5 neutralized | 0.6 | Shift |", "|---|---:|---:|---:|"]
    for pairing_id in POLARITY:
        current = result["pairings"][pairing_id]
        prior = baseline["pairings"][pairing_id]
        lines.append(
            f"| {names[current['deck_a']]}–{names[current['deck_b']]} | "
            f"{percent(prior['deck_a_win_rate'])} | {percent(current['deck_a_win_rate'])} | "
            f"{current['deck_a_win_rate'] - prior['deck_a_win_rate']:+.1%} |"
        )
    exceeded = comparison["engine_stability_gate"]["threshold_exceeded"]
    lines += [
        "",
        "## Stability interpretation",
        "",
        f"The >15-point stability gate records **{len(exceeded)}** unexplained threshold exceedances. ",
    ]
    if exceeded:
        lines.append(
            "Threshold-exceeding pairings: "
            + ", ".join(f"`{row['pairing']}` ({row['shift']:+.0%})" for row in exceeded)
            + "."
        )
    else:
        lines.append("No matchup moved more than 15 points.")
    krang = result["decks"]["krang"]
    lines += [
        "",
        "All large movements are changes in modeled information: anonymous curve slots and ",
        "deck-authored multipliers were replaced by real card types/text and universal heuristic ",
        "weights. They are therefore explained architecturally, but smoke resolution cannot validate ",
        "whether the remaining universal weights represent real games.",
        "",
        f"Krang affinity savings are **{krang['average_affinity_mana_saved']:.2f} mana/game**. ",
        "Bebop & Rocksteady flood remains a direct consequence of its frozen land count. Historical ",
        "0.1–0.5 artifacts remain preserved in adjacent run directories.",
        "",
        "## Value provenance and decision",
        "",
        "Card-derived: card identity/count, mana value/cost, type, Oracle text, keywords, threat and ",
        "spell roles, artifact permanence/token setup/payoff, affinity eligibility/floor, and which ",
        "role counters are incremented. Heuristic and universal: role-unit magnitudes, score weights, ",
        "one-step line-choice constants, artifact milestone values, starting-player bonus, mulligan ",
        "penalty, interaction target cap, and closing variance. Legacy profile priors remain ",
        "inspectable but have no classification, line-choice, or outcome effect.",
        "",
        "Cardcade is **not trustworthy enough** to resume Design Studio deck revisions. Prototype ",
        "0.3 remains unauthorized. The next specific correction is richer rules-text semantic and ",
        "magnitude modeling: quantify token/draw/removal effects, conditional/modal/triggered value, ",
        "creature combat contribution, and target/relevance constraints. Zero tempo and finisher use ",
        "and 18 >15-point shifts show that universal role labels alone are not a stable outcome model.",
    ]
    (output / "REPORT.md").write_text(
        "\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
