"""Summarize authenticated Krang R6-A cells and append their ledger evidence."""

# Report paragraphs and Markdown table templates intentionally remain single literals.
# ruff: noqa: E501

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
sys.path.insert(0, str(ROOT / "tools"))

import build_objective_balance_lab_round5_results as r5  # noqa: E402
import run_objective_balance_lab_round1 as r1  # noqa: E402
import run_objective_balance_lab_round6a as r6  # noqa: E402

HYPOTHESIS = "PARTIALLY_SUPPORTED"
VERDICT = "RETURN_TO_DESIGN_STUDIO_REJECT_POLARIZATION"
IDENTITY = "IDENTITY_PRESERVED"


def fmt(value: float) -> str:
    return f"{value * 100:.2f}%"


def pp(value: float) -> str:
    return f"{value * 100:+.2f} pp"


def write_json(path: Path, value: dict) -> None:
    r6.atomic_json(path, value)


def build() -> dict:
    _manifest, schedule, paths, parent_games = r6.preflight()
    evidence = json.loads(r6.EVIDENCE.read_text(encoding="utf-8"))
    checkpoint = json.loads(r6.CHECKPOINT.read_text(encoding="utf-8"))
    r6.verify(evidence, schedule)
    r6.verify(checkpoint, schedule)
    assert evidence == checkpoint
    assert evidence["stage1_decision"] == "CONTINUE"
    assert evidence["completed_games"] == evidence["effect_replay_verified_games"] == 900
    assert len(evidence["cells"]) == 9
    games = [
        game
        for opponent in r1.DECKS
        if opponent in evidence["cells"]
        for game in evidence["cells"][opponent]
    ]
    parent = r5.summarize(parent_games, "krang")
    candidate = r5.summarize(games, "krang")
    comparison = r5.comparison(parent, candidate)
    prior = json.loads((OBL / "ROUND_5_EVIDENCE.json").read_text(encoding="utf-8"))
    r5b = r5.summarize(prior["candidate_results"]["OBL-R5-KRANG-B"], "krang")
    effect = {
        key: sum(game["turtle_techie_effects"][key] for game in games)
        for key in ("resolved", "condition_met", "cards_drawn")
    }
    assert effect["resolved"] >= effect["condition_met"] >= effect["cards_drawn"]
    assert candidate["signature_casts"].get("Donatello, Turtle Techie", 0) > 0
    assert candidate["matchup_win_rates"]["shredder"] == 0.17
    assert candidate["matchup_win_rates"]["raphael"] == 0.14
    assert candidate["mean_matchup_balance_error"] > parent["mean_matchup_balance_error"]
    assert candidate["over_60_40"] > parent["over_60_40"]
    assert candidate["matchup_win_rates"]["april_oneil"] > 0.6
    results = {
        "hypothesis_result": HYPOTHESIS,
        "cardcade_verdict": VERDICT,
        "identity_classification": IDENTITY,
        "comparison": comparison,
        "round5_b_context": {
            "environment_id": "OBL-BASELINE-002",
            "win_rate": r5b["win_rate"],
            "mean_matchup_balance_error": r5b["mean_matchup_balance_error"],
            "over_60_40": r5b["over_60_40"],
            "over_70_30": r5b["over_70_30"],
            "matchup_win_rates": r5b["matchup_win_rates"],
            "comparison_warning": "Different parent environment; distribution counts are context, not paired delta.",
        },
        "turtle_techie_casts": candidate["signature_casts"]["Donatello, Turtle Techie"],
        "turtle_techie_effect_events": effect,
        "card_draw_telemetry": None,
        "runtime_errors": 0,
        "cell_fingerprints": {
            opponent: r6.digest(cell) for opponent, cell in evidence["cells"].items()
        },
        "stage1": {
            opponent: {
                "candidate_win_rate": candidate["matchup_win_rates"][opponent],
                "parent_win_rate": parent["matchup_win_rates"][opponent],
                "games": 100,
                "candidate_first_games": 50,
                "candidate_first_wins": sum(
                    game["winner"] == "krang" and game["first_player"] == "krang"
                    for game in evidence["cells"][opponent]
                ),
                "opponent_first_games": 50,
                "opponent_first_wins": sum(
                    game["winner"] == opponent and game["first_player"] == opponent
                    for game in evidence["cells"][opponent]
                ),
                "mean_ending_turn": round(
                    sum(game["turn"] for game in evidence["cells"][opponent]) / 100, 4
                ),
                "median_ending_turn": statistics.median(
                    game["turn"] for game in evidence["cells"][opponent]
                ),
                "first_creature_proxy": r1.aggregate(evidence["cells"][opponent], ("krang",))[
                    "krang"
                ]["first_play"]["creature"],
                "battlefield_presence_proxy": r1.aggregate(evidence["cells"][opponent], ("krang",))[
                    "krang"
                ]["battlefield_presence"],
                "turtle_techie_casts": sum(
                    game["signature_casts"].get("krang:Donatello, Turtle Techie", 0)
                    for game in evidence["cells"][opponent]
                ),
                "turtle_techie_effect_events": {
                    key: sum(
                        game["turtle_techie_effects"][key] for game in evidence["cells"][opponent]
                    )
                    for key in ("resolved", "condition_met", "cards_drawn")
                },
                "interaction_casts": sum(
                    count
                    for game in evidence["cells"][opponent]
                    for name, count in game["signature_casts"].items()
                    if name.startswith("krang:") and name.split(":", 1)[1] in r5.interaction_names()
                ),
            }
            for opponent in r6.STAGE1
        },
    }
    evidence["results"] = results
    checkpoint["results"] = results
    write_json(r6.EVIDENCE, evidence)
    write_json(r6.CHECKPOINT, checkpoint)

    lines = [
        "# Cardcade — Krang Round 6-A isolated validation",
        "",
        "Design Studio's [preserved candidate](candidates/KRANG_OBL_R6_A.txt) was tested byte-for-byte against [OBL-BASELINE-003](baselines/OBL_BASELINE_003_MANIFEST.json). No deck or Cardcade semantics changed. [Game-level evidence](ROUND_6_A_EVIDENCE.json) and [checkpoint](ROUND_6_A_CHECKPOINT.json) preserve the 900 frozen games and 900 matching deterministic replays. The predeclared Stage 1 rule permitted Stage 2 after Shredder improved 12→17% and Raphael 13→14%.",
        "",
        f"Candidate checked-out SHA-256: `{r6.CANDIDATE_SHA}`; Git-blob SHA-256: `{r6.CANDIDATE_GIT_SHA}`. Parent SHA-256: `{r6.PARENT_SHA}`. Runtime: `{r6.RUNTIME}`. Schedule: `{evidence['schedule_sha256']}`. These two candidate hashes differ only because Windows checkout uses CRLF while the preserved Git blob uses LF; the list and card content were not edited.",
        "",
        "Exact diff: -1 Negate, +1 Donatello, Turtle Techie. Candidate is 60 cards, Standard-legal, mono-blue, and preserves Krang's artifact-engine identity.",
        "",
        "Mean Matchup Balance Error = mean of `abs((wins + draws/2)/100 - 0.5)` over nine opponents. Counts above 60/40 and 70/30 use strict `>` thresholds; negative balance delta is improvement.",
        "",
        "| Metric | Baseline 003 Krang | R6-A | Delta |",
        "|---|---:|---:|---:|",
        f"| Aggregate WR | {fmt(parent['win_rate'])} | {fmt(candidate['win_rate'])} | {pp(comparison['aggregate_win_rate_delta'])} |",
        f"| Mean balance error | {fmt(parent['mean_matchup_balance_error'])} | {fmt(candidate['mean_matchup_balance_error'])} | {pp(comparison['balance_delta'])} |",
        f"| >60/40 | {parent['over_60_40']} | {candidate['over_60_40']} | {comparison['over_60_40_delta']:+d} |",
        f"| >70/30 | {parent['over_70_30']} | {candidate['over_70_30']} | {comparison['over_70_30_delta']:+d} |",
        f"| Worst matchup | {parent['worst_matchup']['opponent']} {fmt(parent['worst_matchup']['win_rate'])} | {candidate['worst_matchup']['opponent']} {fmt(candidate['worst_matchup']['win_rate'])} | — |",
        f"| Candidate-first result | {fmt(parent['first_player_result_rate'])} | {fmt(candidate['first_player_result_rate'])} | — |",
        f"| Mean / median ending turn | {parent['mean_ending_turn']} / {parent['median_ending_turn']} | {candidate['mean_ending_turn']} / {candidate['median_ending_turn']} | — |",
        "",
        "| Opponent | Baseline 003 | R6-A | Delta |",
        "|---|---:|---:|---:|",
    ]
    for opponent, rate in parent["matchup_win_rates"].items():
        lines.append(
            f"| {opponent} | {fmt(rate)} | {fmt(candidate['matchup_win_rates'][opponent])} | {pp(comparison['matchup_deltas'][opponent])} |"
        )
    lines += [
        "",
        "Stage 1 used 100 frozen games per cell, 50 starts per side, no adaptive/replacement seeds. Shredder: 12→17%; Raphael: 13→14%. Both severe diagnostics moved toward center, so Stage 2 was authorized. Detailed seat splits, game lengths, and all fingerprints are in machine evidence.",
        "",
        "| Stage 1 opponent | Krang first-seat wins / 50 | Opponent first-seat wins / 50 | Mean / median ending turn | First-creature proxy | Turtle Techie casts / resolved draws | Interaction casts |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for opponent in r6.STAGE1:
        cell = results["stage1"][opponent]
        lines.append(
            f"| {opponent} | {cell['candidate_first_wins']} | {cell['opponent_first_wins']} | "
            f"{cell['mean_ending_turn']} / {cell['median_ending_turn']} | "
            f"{cell['first_creature_proxy']} | {cell['turtle_techie_casts']} / "
            f"{cell['turtle_techie_effect_events']['cards_drawn']} | {cell['interaction_casts']} |"
        )
    lines += [
        "",
        "Stage 1 battlefield-presence proxies t3/t5/t7 are in machine evidence; missing observations are not zero.",
        "",
        f"First-creature timing (conditional mean when observed): {parent['first_play']['creature']} → {candidate['first_play']['creature']}. Battlefield-presence proxies t3/t5/t7 (observed-only conditional means): {parent['battlefield_presence']} → {candidate['battlefield_presence']}. Missing observations are not zero.",
        "",
        f"Interaction casts (Oracle-text matched): {parent['interaction_casts_total']} → {candidate['interaction_casts_total']}; Negate signature casts in parent: {parent['signature_casts'].get('Negate', 0)}; Turtle Techie signature casts: {results['turtle_techie_casts']}. Supported ETB effect events in replay: resolved {effect['resolved']}, artifact condition met {effect['condition_met']}, cards drawn {effect['cards_drawn']}. Drawn-card frequency from hand is unavailable, not zero.",
        "",
        "Distribution test: Shredder improved; Raphael improved slightly; overall mean balance error worsened; >60/40 increased 6→7; >70/30 stayed 4; previously near-even April (53%) became 67% Krang-favored. The one-copy package is less polarizing by >60/40 count than historical R5-B's two-copy result (8), but still introduces an additional extreme and does not smooth the Baseline 003 distribution. R5-B used Baseline 002 opponents, so its 43% WR and 17.89% balance error are historical context, not a paired comparison to this Baseline 003 test.",
        "",
        f"Hypothesis: **{HYPOTHESIS}**. Cardcade verdict: **{VERDICT}**. Identity: **{IDENTITY}**. The active artifact-linked body raises WR and improves the primary diagnostic, but the core smooth-distribution claim fails. Return this evidence to Design Studio; Cardcade does not originate R6-B or recommend promotion from this isolated result.",
        "",
        "Nine 100-game cells, 450 starts per side in aggregate, 900/900 games, zero runtime errors, and 900/900 matching deterministic replay fingerprints. No baseline evidence was regenerated. No candidate-vs-candidate games were run.",
        "",
    ]
    (OBL / "ROUND_6_A_RESULTS.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")

    ledger_path = OBL / "EXPERIMENT_LEDGER.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    existing_ledger = [
        row for row in ledger["experiments"] if row.get("experiment_id") == r6.EXPERIMENT
    ]
    if existing_ledger:
        assert len(existing_ledger) == 1
    else:
        ledger["experiments"].append(
            {
                "experiment_id": r6.EXPERIMENT,
                "round": "R6",
                "deck": "Krang",
                "deck_key": "krang",
                "parent": {
                    "environment_id": "OBL-BASELINE-003",
                    "path": paths["krang"],
                    "sha256": r6.PARENT_SHA,
                },
                "candidate": {
                    "path": r6.CANDIDATE,
                    "sha256": r6.CANDIDATE_SHA,
                    "git_blob_sha256": r6.CANDIDATE_GIT_SHA,
                    "label": "A",
                },
                "exact_additions": {"Donatello, Turtle Techie": 1},
                "exact_removals": {"Negate": 1},
                "hypothesis": "One Turtle Techie captures midgame artifact conversion without R5-B's two-copy polarization.",
                "schedule_identity": evidence["schedule_sha256"],
                "semantic_runtime_sha256": r6.RUNTIME,
                "source_evidence": "docs/objective-balance-lab/ROUND_6_A_EVIDENCE.json",
                "result_metrics": {
                    "candidate_win_rate": candidate["win_rate"],
                    "parent_win_rate": parent["win_rate"],
                    "balance_delta": comparison["balance_delta"],
                    "extremes": {
                        "worst_matchup": candidate["worst_matchup"],
                        "over_60_40": candidate["over_60_40"],
                        "over_70_30": candidate["over_70_30"],
                    },
                    "matchup_deltas": comparison["matchup_deltas"],
                },
                "identity_classification": IDENTITY,
                "hypothesis_result": HYPOTHESIS,
                "verdict": VERDICT,
                "promotion_status": "EXPERIMENTAL",
                "promotion": None,
            }
        )
    write_json(ledger_path, ledger)
    ledger_md = OBL / "EXPERIMENT_LEDGER.md"
    if r6.EXPERIMENT not in ledger_md.read_text(encoding="utf-8"):
        with ledger_md.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(
                "\nRound 6 Design Studio handoff: [Krang R6-A evidence](ROUND_6_A_EVIDENCE.json) and [result](ROUND_6_A_RESULTS.md).\n\n"
            )
            stream.write(
                "| Experiment | Round | Deck | Parent SHA-256 | Candidate SHA-256 | Cardcade verdict | Promotion |\n"
            )
            stream.write("|---|---|---|---|---|---|---|\n")
            stream.write(
                f"| `{r6.EXPERIMENT}` | R6 | Krang | `{r6.PARENT_SHA}` | `{r6.CANDIDATE_SHA}` | {VERDICT} | EXPERIMENTAL |\n"
            )

    role_path = OBL / "CARD_ROLE_EVIDENCE.json"
    role = json.loads(role_path.read_text(encoding="utf-8"))
    existing_role = [row for row in role["records"] if row.get("experiment_id") == r6.EXPERIMENT]
    assert not existing_role or {row["card"] for row in existing_role} == {
        "Negate",
        "Donatello, Turtle Techie",
    }
    support = {
        "Negate": "COUNTERSPELL_SEMANTICS_SUPPORTED;ZERO_PARENT_CASTS_OBSERVED",
        "Donatello, Turtle Techie": "CREATURE_CAST_AND_ARTIFACT_ETB_DRAW_EXECUTED",
    }
    for row in existing_role:
        row["semantic_support"] = support[row["card"]]
    for card, copies in () if existing_role else (("Negate", -1), ("Donatello, Turtle Techie", 1)):
        role["records"].append(
            {
                "experiment_id": r6.EXPERIMENT,
                "round": "R6",
                "deck": "Krang",
                "candidate": r6.EXPERIMENT,
                "card": card,
                "copies_changed": copies,
                "replacement_relationship": {
                    "removals": {"Negate": 1},
                    "additions": {"Donatello, Turtle Techie": 1},
                },
                "role_hypothesis": "Midgame artifact conversion with less polarization than a two-copy package.",
                "semantic_support": support[card],
                "aggregate_win_rate_delta": comparison["aggregate_win_rate_delta"],
                "matchup_deltas": comparison["matchup_deltas"],
                "balance_error_delta": comparison["balance_delta"],
                "early_board_delta": comparison["battlefield_presence_mean_deltas"],
                "interaction_delta": comparison["interaction_casts_per_game_delta"],
                "signature_delta": (
                    candidate["signature_casts"].get(card, 0)
                    - parent["signature_casts"].get(card, 0)
                ),
                "supported_effect_events": effect if copies > 0 else None,
                "identity_result": IDENTITY,
                "hypothesis_result": HYPOTHESIS,
                "cardcade_verdict": VERDICT,
                "causality_note": "Paired deck-level association, not drawn-card causality.",
            }
        )
    write_json(role_path, role)
    return results


if __name__ == "__main__":
    result = build()
    print(
        json.dumps(
            {
                "verdict": result["cardcade_verdict"],
                "candidate_win_rate": result["comparison"]["candidate"]["win_rate"],
            }
        )
    )
