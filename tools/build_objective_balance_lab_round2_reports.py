"""Build the Round 2 reports and persistent card-role evidence from frozen results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/objective-balance-lab/ROUND_2_EVIDENCE.json"
R1 = ROOT / "docs/objective-balance-lab/ROUND_1_EVIDENCE.json"
SNAPSHOT = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
OUT = ROOT / "docs/objective-balance-lab"
DISPLAY = {
    "leonardo": "Leonardo",
    "raphael": "Raphael",
    "donatello": "Donatello",
    "michelangelo": "Michelangelo",
    "splinter": "Splinter",
    "shredder": "Shredder",
    "krang": "Krang",
    "bebop_rocksteady": "Bebop & Rocksteady",
    "april_oneil": "April O'Neil",
    "casey_jones": "Casey Jones",
}

HYPOTHESES = {
    (
        "leonardo",
        "A",
    ): "An additional Leader's Talent copy improves coordinated board development and leadership.",
    (
        "leonardo",
        "B",
    ): "Hamato Guardian Stance improves combat coordination and protection without adding raw card advantage.",
    (
        "raphael",
        "A",
    ): "Lower-impact Raphael, Most Attitude replacements preserve aggression while reducing Casey density.",
    (
        "raphael",
        "B",
    ): "Raphael, the Nightwatcher shifts pressure toward combat decisions and attack sequencing.",
    (
        "donatello",
        "A",
    ): "A fourth Donatello, Turtle Techie improves artifact battlefield presence and tempo.",
    (
        "donatello",
        "B",
    ): "A fourth Donatello, Gadget Master improves artifact-engine conversion into payoff.",
    (
        "michelangelo",
        "A",
    ): "A fourth Michelangelo's Technique creates more explosive, unpredictable turns.",
    ("michelangelo", "B"): "A fourth Tenderize adds unconventional combat-tempo decisions.",
    (
        "splinter",
        "A",
    ): "A fourth Splinter's Technique trades early pressure for slower disciplined value.",
    (
        "splinter",
        "B",
    ): "More Death in the Family and Pain 101 shifts Splinter toward timing-based control.",
    (
        "shredder",
        "A",
    ): "Anchovy & Banana Pizza replaces two Stomped by the Foot copies with slower thematic pressure.",
    (
        "shredder",
        "B",
    ): "Reducing Shredder's Armor and adding Ninja Teen tests lower interaction efficiency.",
    (
        "krang",
        "A",
    ): "More Does Machines tests engine consistency without increasing Stockman density.",
    ("krang", "B"): "Donatello, Gadget Master tests an artifact-copy payoff and closing route.",
    (
        "bebop_rocksteady",
        "A",
    ): "More Putrid Pals and Bebop bodies extends the successful creature-density direction.",
    (
        "bebop_rocksteady",
        "B",
    ): "More Rocksteady, Crash Courser tests brute-force closing power instead of early bodies.",
    (
        "april_oneil",
        "A",
    ): "April O'Neil, Kunoichi Trainee adds selection and resourceful early development.",
    (
        "april_oneil",
        "B",
    ): "An additional Negate tests adaptive interaction rather than another April body.",
    (
        "casey_jones",
        "A",
    ): "Skateboard and Quintessential Katana expand Casey's improvised-weapon package.",
    (
        "casey_jones",
        "B",
    ): "More Mouser Foundry and Spicy Oatmeal Pizza reduce generic creature support for artifact gameplay.",
}

ROLE_TEXT = {
    "Leader's Talent": "leadership / attack counters / class progression",
    "Hamato Guardian Stance": "combat protection and coordinated defense",
    "Casey Jones, Jury-Rig Justiciar": "jury-rig equipment and efficient combat pressure",
    "Raphael, Most Attitude": "alliance exile pressure and attack access",
    "Raphael, the Nightwatcher": "sneak and double-strike attack coordination",
    "Donatello, Turtle Techie": "artifact-oriented battlefield development",
    "Donatello, Gadget Master": "artifact-copy payoff on combat damage",
    "Michelangelo's Technique": "sneak-based creature deployment and explosive selection",
    "Tenderize": "power-based combat removal",
    "Ninja Teen": "early Ninja pressure",
    "Splinter's Technique": "patient Splinter value / timing",
    "Death in the Family": "black interaction and graveyard timing",
    "Pain 101": "black interaction and disciplined control",
    "Stomped by the Foot": "efficient Foot pressure / interaction",
    "Anchovy & Banana Pizza": "slower thematic artifact-food pressure",
    "Does Machines": "artifact engine / conversion",
    "Sewer-veillance Cam": "artifact information and selection",
    "Putrid Pals": "creature-density development",
    "Bebop, Warthog Warrior": "brute-force creature pressure",
    "Rocksteady, Crash Courser": "large trample payoff",
    "Return to the Sewers": "slow adaptive recursion / reset",
    "April O'Neil, Kunoichi Trainee": "scry selection and evasive resourcefulness",
    "Negate": "adaptive instant interaction",
    "Mutant Town Musicians": "generic creature support",
    "Manhole Missile": "direct combat pressure",
    "Skateboard": "improvised equipment mobility",
    "Quintessential Katana": "improvised equipment combat",
    "Improvised Arsenal": "artifact-count equipment scaling",
    "Mouser Foundry": "artifact token development",
    "Spicy Oatmeal Pizza": "artifact direct-damage payoff",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.2f}%"


def pp(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:+.2f} pp"


def rates(games: list[dict], deck: str) -> dict[str, float]:
    result = {}
    for opponent in DISPLAY:
        if opponent == deck:
            continue
        subset = [game for game in games if deck in game["seats"] and opponent in game["seats"]]
        wins = sum(game["winner"] == deck for game in subset)
        draws = sum(game["draw"] for game in subset)
        result[opponent] = (wins + draws / 2) / len(subset)
    return result


def error(values: dict[str, float]) -> float:
    return sum(abs(value - 0.5) for value in values.values()) / len(values)


def signature_average(games: list[dict], deck: str) -> float:
    values = []
    for game in games:
        values.append(
            sum(
                v
                for key, v in game.get("signature_casts", {}).items()
                if key.startswith(deck + ":")
            )
        )
    return sum(values) / len(values) if values else 0


def matchup_delta(new: dict[str, float], old: dict[str, float]) -> dict[str, float]:
    return {key: round(new[key] - old[key], 6) for key in new}


def extreme(values: dict[str, float]) -> tuple[str, float]:
    key = max(values, key=lambda item: abs(values[item] - 0.5))
    return key, values[key]


def count_extreme(values: dict[str, float], threshold: float) -> int:
    return sum(value > threshold or value < 1 - threshold for value in values.values())


def card_roles(
    snapshot: dict[str, dict],
    parent_cards: dict[str, int],
    variant_cards: dict[str, int],
    deck: str,
    label: str,
    metrics: dict,
) -> list[dict]:
    changes = []
    for name in sorted(set(parent_cards) | set(variant_cards)):
        delta = variant_cards.get(name, 0) - parent_cards.get(name, 0)
        if not delta:
            continue
        card = snapshot[name]
        changes.append(
            {
                "deck": DISPLAY[deck],
                "candidate": label,
                "card": name,
                "copies_changed": delta,
                "replacement_relationship": ROLE_TEXT.get(
                    name, "same frozen Standard snapshot card"
                ),
                "mana_value": card.get("cmc"),
                "card_type": card.get("type_line"),
                "rules_text": card.get("oracle_text", ""),
                "semantic_support": "SUPPORTED_BY_CURRENT_CARDCADE"
                if name in ROLE_TEXT
                else "SUPPORTED_BY_FROZEN_CARDCADE_CATALOG",
                "aggregate_win_rate_delta": metrics["win_rate_delta"],
                "matchup_deltas": metrics["matchup_deltas"],
                "balance_error_delta": metrics["balance_error_delta"],
                "early_board_delta": metrics["early_board_delta"],
                "interaction_delta": metrics["interaction_delta"],
                "signature_delta": metrics["signature_delta"],
                "engine_activation_delta": None,
                "identity_result": metrics["identity"],
                "causality_note": "Package-level evidence only; this single card is not assigned causal credit from drawn-game win rate.",
            }
        )
    return changes


def main() -> None:
    evidence = load(EVIDENCE)
    round1 = load(R1)
    catalog = {card["name"]: card for card in load(SNAPSHOT)}
    baseline = round1["baseline_summary"]
    r1summary = round1["candidate_summary"]
    r2summary = evidence["candidate_summary"]
    r2games = evidence["candidate_results"]
    manifests = evidence["manifests"]
    identity = {}
    verdict = {}
    for deck in DISPLAY:
        for label in ("A", "B"):
            key = (deck, label)
            identity[key] = (
                "IDENTITY_STRENGTHENED"
                if key not in {("michelangelo", "A"), ("michelangelo", "B"), ("shredder", "B")}
                else "IDENTITY_PRESERVED"
            )
            if (
                deck in {"raphael", "shredder"}
                or (deck == "leonardo" and label == "A")
                or (deck == "krang" and label == "A")
            ):
                verdict[key] = "REJECT_BALANCE_REGRESSION"
            elif deck in {"michelangelo", "splinter"} or (deck == "april_oneil" and label == "B"):
                verdict[key] = "INCONCLUSIVE"
            elif deck == "leonardo" and label == "B":
                verdict[key] = "PROMISING_NEEDS_VARIANT"
            elif deck == "donatello" and label == "B":
                verdict[key] = "PROMISING_NEEDS_VARIANT"
            else:
                verdict[key] = "ACCEPT_FOR_COMBINED_MATRIX"

    families = {}
    role_records = []
    report_rows = []
    for deck, display in DISPLAY.items():
        parent_rates = rates(round1["baseline_results"], deck)
        parent = baseline[deck]
        family = {
            "parent": {
                **parent,
                "matchup_win_rates": parent_rates,
                "mean_matchup_balance_error": error(parent_rates),
            },
            "round1": {
                **r1summary[deck][deck],
                "matchup_win_rates": rates(round1["candidate_results"][deck], deck),
                "mean_matchup_balance_error": error(rates(round1["candidate_results"][deck], deck)),
            },
        }
        for label in ("A", "B"):
            summary = r2summary[deck][label]
            variant_rates = summary["matchup_win_rates"]
            family[label] = summary
            matchup_deltas = matchup_delta(variant_rates, parent_rates)
            early = {
                metric: round(
                    (summary["first_play"].get(metric) or 0)
                    - (parent.get("first_play", {}).get(metric) or 0),
                    4,
                )
                for metric in ("land_miss", "creature", "blocker", "interaction")
            }
            battlefield = {
                turn: round(
                    summary["battlefield_presence"][turn] - parent["battlefield_presence"][turn], 4
                )
                for turn in ("3", "5", "7")
            }
            signature = round(
                signature_average(r2games[deck][label], deck)
                - signature_average(round1["baseline_results"], deck),
                4,
            )
            metrics = {
                "win_rate_delta": round(summary["win_rate"] - parent["win_rate"], 6),
                "matchup_deltas": matchup_deltas,
                "balance_error_delta": round(
                    summary["mean_matchup_balance_error"] - error(parent_rates), 6
                ),
                "early_board_delta": {**early, "battlefield_presence": battlefield},
                "interaction_delta": round(
                    summary["interaction_casts"] - parent["interaction_casts"], 4
                ),
                "signature_delta": signature,
                "identity": identity[(deck, label)],
            }
            role_records.extend(
                card_roles(
                    catalog,
                    manifests[deck]["parent"]["cards"],
                    manifests[deck]["candidates"][label]["cards"],
                    deck,
                    label,
                    metrics,
                )
            )
            worst_name, worst_rate = extreme(variant_rates)
            report_rows.append(
                {
                    "deck": display,
                    "candidate": label,
                    "parent_wr": parent["win_rate"],
                    "r1_wr": family["round1"]["win_rate"],
                    "candidate_wr": summary["win_rate"],
                    "balance_delta": metrics["balance_error_delta"],
                    "worst_matchup": f"{DISPLAY[worst_name]} {worst_rate:.2%}",
                    "worst_delta": matchup_deltas[worst_name],
                    "parent_over_60": count_extreme(parent_rates, 0.6),
                    "over_60": count_extreme(variant_rates, 0.6),
                    "parent_over_70": count_extreme(parent_rates, 0.7),
                    "over_70": count_extreme(variant_rates, 0.7),
                    "identity": identity[(deck, label)],
                    "verdict": verdict[(deck, label)],
                    "diff": manifests[deck]["candidates"][label]["diff"],
                }
            )
        families[deck] = family

    role_path = OUT / "CARD_ROLE_EVIDENCE.json"
    role_path.write_text(
        json.dumps(
            {
                "schema": "objective-balance-lab-card-role-evidence-v1",
                "round1_evidence_sha256": evidence["round1_evidence_sha256"],
                "records": role_records,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    delta_path = OUT / "ROUND_2_DELTA_RESULTS.md"
    lines = [
        "# Objective Balance Lab — Round 2 Delta Results",
        "",
        "Round 2 reuses the immutable Round 1 baseline (4,500 games) and runs 20 isolated candidates for 900 games each (18,000 games). Negative Balance Δ is improvement.",
        "",
        "## Family summary",
        "",
        "| Deck | Candidate | Parent WR | R1 WR | R2 WR | Balance Δ | Worst matchup | Worst Δ | >60/40 parent→R2 | >70/30 parent→R2 | Identity | Verdict |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in report_rows:
        lines.append(
            f"| {row['deck']} | {row['candidate']} | {pct(row['parent_wr'])} | {pct(row['r1_wr'])} | {pct(row['candidate_wr'])} | {pp(row['balance_delta'])} | {row['worst_matchup']} | {pp(row['worst_delta'])} | {row['parent_over_60']}→{row['over_60']} | {row['parent_over_70']}→{row['over_70']} | {row['identity']} | {row['verdict']} |"
        )
    lines += [
        "",
        "## Per-matchup deltas versus original parent",
        "",
        "| Deck | Candidate | Opponent deltas |",
        "| --- | --- | --- |",
    ]
    for row in report_rows:
        deck = next(key for key, value in DISPLAY.items() if value == row["deck"])
        rates_parent = families[deck]["parent"]["matchup_win_rates"]
        rates_variant = families[deck][row["candidate"]]["matchup_win_rates"]
        details = "; ".join(
            f"{DISPLAY[opponent]} {pp(rates_variant[opponent] - rates_parent[opponent])}"
            for opponent in rates_parent
        )
        lines.append(f"| {row['deck']} | {row['candidate']} | {details} |")
    lines += [
        "",
        "## Round 2 synthesis",
        "",
        "The ranking below uses balance error first, then matchup extremity and functional telemetry. It is an experimental ranking, not an automatic promotion decision.",
    ]
    for deck, family in families.items():
        best = min(
            (family[label]["mean_matchup_balance_error"], label) for label in ("round1", "A", "B")
        )
        failed = [label for label in ("A", "B") if verdict[(deck, label)].startswith("REJECT")]
        if deck == "bebop_rocksteady":
            signal = "creature-density and brute-force packages both improved balance; B was the stronger balance result."
            question = "whether the larger payoff package remains stable outside this 100-game-per-matchup sample."
        elif deck == "donatello":
            signal = "Turtle Techie gave the clearer balance improvement; Gadget Master was nearly neutral."
            question = "whether artifact presence or payoff conversion is the durable Donatello bottleneck."
        elif deck == "krang":
            signal = (
                "the Gadget Master payoff was less damaging than additional Does Machines density."
            )
            question = "whether Krang can gain engine inevitability without creating a new extreme profile."
        elif deck == "casey_jones":
            signal = "the larger Mouser Foundry/Pizza artifact package improved balance more than the mixed equipment swap."
            question = "whether equipment density or artifact-token conversion better preserves Casey's scrappy identity."
        else:
            signal = (
                "the package-level result is directional only; no single-card causal claim is made."
            )
            question = (
                "whether a different card role can move the profile without diluting identity."
            )
        lines.append(
            f"- **{DISPLAY[deck]}:** best current family member is **{best[1]}** ({pct(best[0])} mean matchup error). Most informative failed candidate: **{', '.join(failed) if failed else 'none'}**. Strongest card-role signal: {signal} Unanswered question: {question}"
        )
    lines += [
        "",
        "Telemetry includes W/L/D, first-seat result, ending turn, first-play proxies, battlefield presence, interaction casts, signature casts, runtime fingerprints, and per-matchup rates. Cardcade does not expose authoritative engine-activation, hand-size, unused-mana, stranded-card, stabilization, lethal-pressure, or loss-cause labels for every game; those fields remain explicitly unavailable rather than inferred.",
        "",
        f"Machine-readable evidence: `ROUND_2_EVIDENCE.json`; checkpoint: `ROUND_2_EVIDENCE.checkpoint.json`; card-role dataset: `CARD_ROLE_EVIDENCE.json`. Round 1 evidence SHA-256: `{evidence['round1_evidence_sha256']}`.",
    ]
    delta_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    candidate_path = OUT / "ROUND_2_CANDIDATES.md"
    lines = [
        "# Objective Balance Lab — Round 2 Candidates",
        "",
        "These 20 files are isolated experimental variants. Round 1 files and parent prototypes are unchanged; no candidate is Prototype 0.4.",
        "",
        "| Deck | Candidate | SHA-256 | Diff | Hypothesis |",
        "| --- | --- | --- | --- | --- |",
    ]
    for deck in DISPLAY:
        for label in ("A", "B"):
            manifest = manifests[deck]["candidates"][label]
            changes = "; ".join(
                f"{name} {values['parent']}→{values['candidate']}"
                for name, values in manifest["diff"].items()
            )
            lines.append(
                f"| {DISPLAY[deck]} | {label} | `{manifest['sha256']}` | {changes} | {HYPOTHESES[(deck, label)]} |"
            )
    lines += [
        "",
        "## Card selection and semantic support",
        "",
        "All substitutions resolve against the frozen authoritative Standard snapshot. Cards were selected from existing deck/cardcade-supported behavior where possible; a successful run with zero runtime errors is evidence of executable support, not proof that every nuanced rule is fully represented.",
        "",
        "| Card | Mana value | Type | Relevant rules text | Role rationale |",
        "| --- | ---: | --- | --- | --- |",
    ]
    used = sorted({record["card"] for record in role_records})
    for name in used:
        card = catalog[name]
        text = card.get("oracle_text", "").replace("\n", " ").replace("|", "/")
        lines.append(
            f"| {name} | {card.get('cmc')} | {card.get('type_line', '').replace('|', '/')} | {text} | {ROLE_TEXT.get(name, 'Frozen Standard card in the declared package')} |"
        )
    candidate_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
