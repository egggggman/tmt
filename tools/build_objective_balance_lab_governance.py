"""Build the permanent OBL registry, experiment ledger, and promotion policy records."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

# The generator contains long human-readable ledger/table strings by design.
# ruff: noqa: E501, E702

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
R1_PATH = OBL / "ROUND_1_EVIDENCE.json"
R2_PATH = OBL / "ROUND_2_EVIDENCE.json"
MAIN = "4f2d69d87bf5a3cbb4d8d9a2508be3851eb2e836"
DECKS = (
    "leonardo",
    "raphael",
    "donatello",
    "michelangelo",
    "splinter",
    "shredder",
    "krang",
    "bebop_rocksteady",
    "april_oneil",
    "casey_jones",
)
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
PARENT_VERSION = {
    "leonardo": "Prototype 0.1",
    "raphael": "Prototype 0.3",
    "donatello": "Prototype 0.3c",
    "michelangelo": "Prototype 0.1",
    "splinter": "Prototype 0.1",
    "shredder": "Prototype 0.3",
    "krang": "Prototype 0.2",
    "bebop_rocksteady": "Prototype 0.1",
    "april_oneil": "Prototype 0.1",
    "casey_jones": "Prototype 0.3",
}
PARENT_PATH = {
    "leonardo": "decks/leonardo/PROTOTYPE_0.1.txt",
    "raphael": "decks/raphael/PROTOTYPE_0.3.txt",
    "donatello": "decks/donatello/PROTOTYPE_0.3c.txt",
    "michelangelo": "decks/michelangelo/PROTOTYPE_0.1.txt",
    "splinter": "decks/splinter/PROTOTYPE_0.1.txt",
    "shredder": "decks/shredder/PROTOTYPE_0.3.txt",
    "krang": "decks/krang/PROTOTYPE_0.2.txt",
    "bebop_rocksteady": "decks/bebop_rocksteady/PROTOTYPE_0.1.txt",
    "april_oneil": "decks/april_oneil/PROTOTYPE_0.1.txt",
    "casey_jones": "decks/casey_jones/PROTOTYPE_0.3.txt",
}
BASELINE_ERROR = {
    "leonardo": 0.1678,
    "raphael": 0.2678,
    "donatello": 0.1811,
    "michelangelo": 0.1833,
    "splinter": 0.2167,
    "shredder": 0.2456,
    "krang": 0.2089,
    "bebop_rocksteady": 0.1978,
    "april_oneil": 0.2433,
    "casey_jones": 0.1833,
}
IDENTITY = {
    "leonardo": "coordinated board / disciplined leadership",
    "raphael": "confrontation / aggressive pressure",
    "donatello": "artifacts / inventions / technical synergy",
    "michelangelo": "energetic / unconventional play",
    "splinter": "patient / disciplined value-control",
    "shredder": "ruthless interaction / villain pressure",
    "krang": "technology / artifact engine",
    "bebop_rocksteady": "brute-force aggression",
    "april_oneil": "resourceful / adaptive play",
    "casey_jones": "improvised weapons / scrappy aggression",
}
HYPOTHESIS = {
    "OBL-R1-LEONARDO-A": "A fourth leadership Class improves coordinated combat and disciplined board development.",
    "OBL-R1-RAPHAEL-A": "Reducing Casey to cameo density and increasing Raphael threats improves direct combat pressure.",
    "OBL-R1-DONATELLO-A": "More early artifact bodies improve stabilization and feed the Mouser/artifact engine.",
    "OBL-R1-MICHELANGELO-A": "More represented Mutagen/counter unpredictability improves unconventional board conversion.",
    "OBL-R1-SPLINTER-A": "A denser patient interaction package improves timing and disciplined value.",
    "OBL-R1-SHREDDER-A": "Preserve ruthless pressure while testing whether excess efficiency can be reduced.",
    "OBL-R1-KRANG-A": "More artifact-engine density improves inevitability through represented draw/discard conversion.",
    "OBL-R1-BEBOP_ROCKSTEADY-A": "More bodies and brute-force threats improve straightforward pressure.",
    "OBL-R1-APRIL_ONEIL-A": "More represented April card advantage improves resourcefulness and adaptability.",
    "OBL-R1-CASEY_JONES-A": "A denser equipment package improves scrappy weapon conversion without exporting Casey density.",
    "OBL-R2-LEONARDO-A": "An additional Leader's Talent copy improves coordinated board development and leadership.",
    "OBL-R2-LEONARDO-B": "Hamato Guardian Stance improves combat coordination and protection without adding raw card advantage.",
    "OBL-R2-RAPHAEL-A": "Lower-impact Raphael, Most Attitude replacements preserve aggression while reducing Casey density.",
    "OBL-R2-RAPHAEL-B": "Raphael, the Nightwatcher shifts pressure toward combat decisions and attack sequencing.",
    "OBL-R2-DONATELLO-A": "A fourth Donatello, Turtle Techie improves artifact battlefield presence and tempo.",
    "OBL-R2-DONATELLO-B": "A fourth Donatello, Gadget Master improves artifact-engine conversion into payoff.",
    "OBL-R2-MICHELANGELO-A": "A fourth Michelangelo's Technique creates more explosive, unpredictable turns.",
    "OBL-R2-MICHELANGELO-B": "A fourth Tenderize adds unconventional combat-tempo decisions.",
    "OBL-R2-SPLINTER-A": "A fourth Splinter's Technique trades early pressure for slower disciplined value.",
    "OBL-R2-SPLINTER-B": "More Death in the Family and Pain 101 shifts Splinter toward timing-based control.",
    "OBL-R2-SHREDDER-A": "Anchovy & Banana Pizza replaces Stomped by the Foot with slower thematic pressure.",
    "OBL-R2-SHREDDER-B": "Reducing Shredder's Armor and adding Ninja Teen tests lower interaction efficiency.",
    "OBL-R2-KRANG-A": "More Does Machines tests engine consistency without increasing Stockman density.",
    "OBL-R2-KRANG-B": "Donatello, Gadget Master tests an artifact-copy payoff and closing route.",
    "OBL-R2-BEBOP_ROCKSTEADY-A": "More Putrid Pals and Bebop bodies extends the successful creature-density direction.",
    "OBL-R2-BEBOP_ROCKSTEADY-B": "More Rocksteady, Crash Courser tests brute-force closing power instead of early bodies.",
    "OBL-R2-APRIL_ONEIL-A": "April O'Neil, Kunoichi Trainee adds selection and resourceful early development.",
    "OBL-R2-APRIL_ONEIL-B": "An additional Negate tests adaptive interaction rather than another April body.",
    "OBL-R2-CASEY_JONES-A": "Skateboard and Quintessential Katana expand Casey's improvised-weapon package.",
    "OBL-R2-CASEY_JONES-B": "More Mouser Foundry and Spicy Oatmeal Pizza reduce generic creature support for artifact gameplay.",
}
IDENTITY_RESULT = {
    "OBL-R1-LEONARDO-A": "IDENTITY_STRENGTHENED",
    "OBL-R1-RAPHAEL-A": "IDENTITY_STRENGTHENED",
    "OBL-R1-DONATELLO-A": "IDENTITY_STRENGTHENED",
    "OBL-R1-MICHELANGELO-A": "IDENTITY_PRESERVED",
    "OBL-R1-SPLINTER-A": "IDENTITY_PRESERVED",
    "OBL-R1-SHREDDER-A": "IDENTITY_PRESERVED",
    "OBL-R1-KRANG-A": "IDENTITY_STRENGTHENED",
    "OBL-R1-BEBOP_ROCKSTEADY-A": "IDENTITY_STRENGTHENED",
    "OBL-R1-APRIL_ONEIL-A": "IDENTITY_STRENGTHENED",
    "OBL-R1-CASEY_JONES-A": "IDENTITY_STRENGTHENED",
    "OBL-R2-LEONARDO-A": "IDENTITY_STRENGTHENED",
    "OBL-R2-LEONARDO-B": "IDENTITY_STRENGTHENED",
    "OBL-R2-RAPHAEL-A": "IDENTITY_STRENGTHENED",
    "OBL-R2-RAPHAEL-B": "IDENTITY_STRENGTHENED",
    "OBL-R2-DONATELLO-A": "IDENTITY_STRENGTHENED",
    "OBL-R2-DONATELLO-B": "IDENTITY_STRENGTHENED",
    "OBL-R2-MICHELANGELO-A": "IDENTITY_PRESERVED",
    "OBL-R2-MICHELANGELO-B": "IDENTITY_PRESERVED",
    "OBL-R2-SPLINTER-A": "IDENTITY_STRENGTHENED",
    "OBL-R2-SPLINTER-B": "IDENTITY_STRENGTHENED",
    "OBL-R2-SHREDDER-A": "IDENTITY_STRENGTHENED",
    "OBL-R2-SHREDDER-B": "IDENTITY_PRESERVED",
    "OBL-R2-KRANG-A": "IDENTITY_STRENGTHENED",
    "OBL-R2-KRANG-B": "IDENTITY_STRENGTHENED",
    "OBL-R2-BEBOP_ROCKSTEADY-A": "IDENTITY_STRENGTHENED",
    "OBL-R2-BEBOP_ROCKSTEADY-B": "IDENTITY_STRENGTHENED",
    "OBL-R2-APRIL_ONEIL-A": "IDENTITY_STRENGTHENED",
    "OBL-R2-APRIL_ONEIL-B": "IDENTITY_STRENGTHENED",
    "OBL-R2-CASEY_JONES-A": "IDENTITY_STRENGTHENED",
    "OBL-R2-CASEY_JONES-B": "IDENTITY_STRENGTHENED",
}
VERDICT = {
    "OBL-R1-LEONARDO-A": "ACCEPTED_FOR_COMBINED_MATRIX",
    "OBL-R1-RAPHAEL-A": "REJECT_BALANCE_REGRESSION",
    "OBL-R1-DONATELLO-A": "REJECT_BALANCE_REGRESSION",
    "OBL-R1-MICHELANGELO-A": "INCONCLUSIVE",
    "OBL-R1-SPLINTER-A": "INCONCLUSIVE",
    "OBL-R1-SHREDDER-A": "INCONCLUSIVE",
    "OBL-R1-KRANG-A": "REJECT_BALANCE_REGRESSION",
    "OBL-R1-BEBOP_ROCKSTEADY-A": "ACCEPTED_FOR_COMBINED_MATRIX",
    "OBL-R1-APRIL_ONEIL-A": "ACCEPTED_FOR_COMBINED_MATRIX",
    "OBL-R1-CASEY_JONES-A": "ACCEPTED_FOR_COMBINED_MATRIX",
    "OBL-R2-LEONARDO-A": "REJECT_BALANCE_REGRESSION",
    "OBL-R2-LEONARDO-B": "PROMISING_NEEDS_VARIANT",
    "OBL-R2-RAPHAEL-A": "REJECT_BALANCE_REGRESSION",
    "OBL-R2-RAPHAEL-B": "REJECT_BALANCE_REGRESSION",
    "OBL-R2-DONATELLO-A": "ACCEPTED_FOR_COMBINED_MATRIX",
    "OBL-R2-DONATELLO-B": "PROMISING_NEEDS_VARIANT",
    "OBL-R2-MICHELANGELO-A": "INCONCLUSIVE",
    "OBL-R2-MICHELANGELO-B": "INCONCLUSIVE",
    "OBL-R2-SPLINTER-A": "INCONCLUSIVE",
    "OBL-R2-SPLINTER-B": "INCONCLUSIVE",
    "OBL-R2-SHREDDER-A": "REJECT_BALANCE_REGRESSION",
    "OBL-R2-SHREDDER-B": "REJECT_BALANCE_REGRESSION",
    "OBL-R2-KRANG-A": "REJECT_BALANCE_REGRESSION",
    "OBL-R2-KRANG-B": "ACCEPTED_FOR_COMBINED_MATRIX",
    "OBL-R2-BEBOP_ROCKSTEADY-A": "ACCEPTED_FOR_COMBINED_MATRIX",
    "OBL-R2-BEBOP_ROCKSTEADY-B": "ACCEPTED_FOR_COMBINED_MATRIX",
    "OBL-R2-APRIL_ONEIL-A": "ACCEPTED_FOR_COMBINED_MATRIX",
    "OBL-R2-APRIL_ONEIL-B": "INCONCLUSIVE",
    "OBL-R2-CASEY_JONES-A": "ACCEPTED_FOR_COMBINED_MATRIX",
    "OBL-R2-CASEY_JONES-B": "ACCEPTED_FOR_COMBINED_MATRIX",
}
STRONGEST = {
    "leonardo": ("OBL-R1-LEONARDO-A", "ACCEPTED_FOR_COMBINED_MATRIX"),
    "raphael": (None, "NONE_ACCEPTED"),
    "donatello": ("OBL-R2-DONATELLO-A", "ACCEPTED_FOR_COMBINED_MATRIX"),
    "michelangelo": (None, "NONE_INCONCLUSIVE"),
    "splinter": (None, "NONE_INCONCLUSIVE"),
    "shredder": (None, "NONE_PROMOTABLE"),
    "krang": ("OBL-R2-KRANG-B", "ACCEPTED_FOR_COMBINED_MATRIX"),
    "bebop_rocksteady": ("OBL-R2-BEBOP_ROCKSTEADY-B", "ACCEPTED_FOR_COMBINED_MATRIX"),
    "april_oneil": ("OBL-R1-APRIL_ONEIL-A", "ACCEPTED_FOR_COMBINED_MATRIX"),
    "casey_jones": ("OBL-R2-CASEY_JONES-B", "ACCEPTED_FOR_COMBINED_MATRIX"),
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def matchup_rates(games: list[dict], deck: str, decks: tuple[str, ...] = DECKS) -> dict[str, float]:
    result = {}
    for opponent in decks:
        if opponent == deck:
            continue
        subset = [game for game in games if deck in game["seats"] and opponent in game["seats"]]
        wins = sum(game["winner"] == deck for game in subset)
        draws = sum(game["draw"] for game in subset)
        result[opponent] = (wins + draws / 2) / len(subset)
    return result


def error(rates: dict[str, float]) -> float:
    return sum(abs(value - 0.5) for value in rates.values()) / len(rates)


def extremes(rates: dict[str, float]) -> dict[str, object]:
    worst = max(rates, key=lambda name: abs(rates[name] - 0.5))
    return {
        "worst_matchup": worst,
        "worst_matchup_win_rate": round(rates[worst], 6),
        "over_60_40": sum(rate > 0.6 or rate < 0.4 for rate in rates.values()),
        "over_70_30": sum(rate > 0.7 or rate < 0.3 for rate in rates.values()),
    }


def diff_parts(change: dict[str, dict[str, int]]) -> tuple[dict[str, int], dict[str, int]]:
    additions = {
        name: row["candidate"] - row["parent"]
        for name, row in change.items()
        if row["candidate"] > row["parent"]
    }
    removals = {
        name: row["parent"] - row["candidate"]
        for name, row in change.items()
        if row["candidate"] < row["parent"]
    }
    return additions, removals


def experiment_record(
    exp_id: str,
    deck: str,
    round_name: str,
    label: str,
    parent: dict,
    candidate: dict,
    games: list[dict],
    evidence_path: str,
    evidence_sha: str,
    schedule_identity: str,
) -> dict:
    parent_rates = matchup_rates(games["parent_games"], deck)
    candidate_rates = matchup_rates(games["candidate_games"], deck)
    parent_error = error(parent_rates)
    candidate_error = error(candidate_rates)
    additions, removals = diff_parts(candidate["diff"])
    parent_games = [game for game in games["parent_games"] if deck in game["seats"]]
    parent_wr = sum(game["winner"] == deck for game in parent_games) / len(parent_games)
    candidate_wr = sum(game["winner"] == deck for game in games["candidate_games"]) / len(
        games["candidate_games"]
    )
    result_extremes = extremes(candidate_rates)
    parent_extremes = extremes(parent_rates)
    return {
        "experiment_id": exp_id,
        "round": round_name,
        "deck": DISPLAY[deck],
        "deck_key": deck,
        "parent": {
            "path": parent["path"],
            "sha256": parent["sha256"],
            "version": PARENT_VERSION[deck],
        },
        "candidate": {"path": candidate["path"], "sha256": candidate["sha256"], "label": label},
        "exact_additions": additions,
        "exact_removals": removals,
        "hypothesis": HYPOTHESIS[exp_id],
        "schedule_identity": schedule_identity,
        "source_evidence": {"path": evidence_path, "sha256": evidence_sha},
        "result_metrics": {
            "parent_win_rate": round(parent_wr, 6),
            "candidate_win_rate": round(candidate_wr, 6),
            "balance_error_parent": round(parent_error, 6),
            "balance_error_candidate": round(candidate_error, 6),
            "balance_delta": round(candidate_error - parent_error, 6),
            "matchup_deltas": {
                opponent: round(candidate_rates[opponent] - parent_rates[opponent], 6)
                for opponent in parent_rates
            },
            "parent_extremes": parent_extremes,
            "candidate_extremes": result_extremes,
        },
        "identity_classification": IDENTITY_RESULT[exp_id],
        "verdict": VERDICT[exp_id],
        "promotion_status": "NOT_PROMOTED_COMBINED_MATRIX_REQUIRED",
    }


def main() -> None:
    r1 = load(R1_PATH)
    r2 = load(R2_PATH)
    r1_sha = file_sha("docs/objective-balance-lab/ROUND_1_EVIDENCE.json")
    r2_sha = file_sha("docs/objective-balance-lab/ROUND_2_EVIDENCE.json")
    schedule_identity = r2["schedule_sha256"]
    baseline = r1["manifests"]["baseline"]
    registry_decks = []
    records = []
    for deck in DECKS:
        parent = baseline[deck]
        candidates = []
        r1_candidate = r1["manifests"]["candidate"][deck]
        r1_id = f"OBL-R1-{deck.upper()}-A"
        r1_record = experiment_record(
            r1_id,
            deck,
            "R1",
            "A",
            parent,
            r1_candidate,
            {
                "parent_games": r1["baseline_results"],
                "candidate_games": r1["candidate_results"][deck],
            },
            "docs/objective-balance-lab/ROUND_1_EVIDENCE.json",
            r1_sha,
            schedule_identity,
        )
        records.append(r1_record)
        candidates.append(r1_id)
        for label in ("A", "B"):
            candidate = r2["manifests"][deck]["candidates"][label]
            exp_id = f"OBL-R2-{deck.upper()}-{label}"
            r2_record = experiment_record(
                exp_id,
                deck,
                "R2",
                label,
                parent,
                candidate,
                {
                    "parent_games": r1["baseline_results"],
                    "candidate_games": r2["candidate_results"][deck][label],
                },
                "docs/objective-balance-lab/ROUND_2_EVIDENCE.json",
                r2_sha,
                schedule_identity,
            )
            records.append(r2_record)
            candidates.append(exp_id)
        strongest_id, strongest_status = STRONGEST[deck]
        registry_decks.append(
            {
                "deck": DISPLAY[deck],
                "deck_key": deck,
                "official_current_baseline_version": PARENT_VERSION[deck],
                "source_path": parent["path"],
                "sha256": parent["sha256"],
                "aggregate_baseline_win_rate": r1["baseline_summary"][deck]["win_rate"],
                "mean_matchup_balance_error": BASELINE_ERROR[deck],
                "candidate_lineage": candidates,
                "current_strongest_experimental_candidate": strongest_id,
                "candidate_status": strongest_status,
                "identity_status": "IDENTITY_PROTECTED: " + IDENTITY[deck],
                "semantic_confidence_status": "PARTIALLY_REPRESENTED; no core semantic block in Round 1 audit",
                "promotion_status": "BASELINE_UNCHANGED; no candidate promoted",
                "next_experimental_question": {
                    "leonardo": "Select between accepted R1 leadership and promising R2B protection before combined validation.",
                    "raphael": "Find a lower-efficiency confrontation package that reduces the major overperformance.",
                    "donatello": "Select whether battlefield presence or payoff conversion is the better artifact bottleneck probe.",
                    "michelangelo": "Find a mechanically observable unconventional lever; current swaps are zero-delta.",
                    "splinter": "Find a mechanically observable patient-control lever; current swaps are zero-delta.",
                    "shredder": "Reduce major overperformance with a Cardcade-distinguishable pressure or interaction change.",
                    "krang": "Select a route toward center without adding new matchup extremes.",
                    "bebop_rocksteady": "Select between creature density and brute-force payoff for combined validation.",
                    "april_oneil": "Select between R1 resource advantage and R2A selection before combined validation.",
                    "casey_jones": "Select the stronger artifact/equipment package before combined validation.",
                }[deck],
            }
        )
    registry = {
        "schema": "objective-balance-lab-environment-registry-v1",
        "environment_id": "OBL-BASELINE-000",
        "repository_sha": MAIN,
        "status": "BASELINE",
        "promotion_status": "NO_PROMOTIONS",
        "evidence": [
            {"path": "docs/objective-balance-lab/ROUND_1_EVIDENCE.json", "sha256": r1_sha},
            {"path": "docs/objective-balance-lab/ROUND_2_EVIDENCE.json", "sha256": r2_sha},
        ],
        "schedule_identity": schedule_identity,
        "next_gate": "SELECT COMBINED-MATRIX CANDIDATES",
        "decks": registry_decks,
    }
    ledger = {
        "schema": "objective-balance-lab-experiment-ledger-v1",
        "repository_sha": MAIN,
        "environment_id": "OBL-BASELINE-000",
        "experiments": records,
    }
    (OBL / "ENVIRONMENT_REGISTRY.json").write_text(
        json.dumps(registry, indent=2) + "\n", encoding="utf-8"
    )
    (OBL / "EXPERIMENT_LEDGER.json").write_text(
        json.dumps(ledger, indent=2) + "\n", encoding="utf-8"
    )
    write_registry_md(registry)
    write_ledger_md(records)


def write_registry_md(registry: dict) -> None:
    lines = [
        "# Objective Balance Lab — Environment Registry",
        "",
        "This is the authoritative human-readable record of the frozen ten-deck environment. Experiments are cheap. Promotion is expensive. No Round 1 or Round 2 candidate has been promoted.",
        "",
        "## Environment",
        "",
        f"- Environment ID: `{registry['environment_id']}`",
        f"- Repository SHA: `{registry['repository_sha']}`",
        "- State: `BASELINE`",
        "- Next gate: **SELECT COMBINED-MATRIX CANDIDATES**",
        "- Promotion rule: isolated evidence, candidate selection, combined-environment validation, then explicit promotion.",
        "",
        "## Official baselines",
        "",
        "| Deck | Official version | Source | SHA-256 | Baseline WR | Mean Matchup Balance Error | Strongest experiment | Candidate status | Identity | Semantic confidence | Promotion | Next question |",
        "|---|---|---|---|---:|---:|---|---|---|---|---|---|",
    ]
    for deck in registry["decks"]:
        lines.append(
            f"| {deck['deck']} | {deck['official_current_baseline_version']} | `{deck['source_path']}` | `{deck['sha256']}` | {deck['aggregate_baseline_win_rate']:.2%} | {deck['mean_matchup_balance_error']:.2%} | `{deck['current_strongest_experimental_candidate'] or 'none'}` | {deck['candidate_status']} | {deck['identity_status']} | {deck['semantic_confidence_status']} | {deck['promotion_status']} | {deck['next_experimental_question']} |"
        )
    lines += [
        "",
        "## Lineage and evidence",
        "",
        "Each deck's candidate lineage is recorded in `ENVIRONMENT_REGISTRY.json`. Full game-level evidence remains in the immutable Round 1 and Round 2 artifacts; this registry references those files by SHA-256 rather than duplicating them.",
        "",
        "The current environment is intentionally named `OBL-BASELINE-000`. Future promoted environments increment the numeric suffix. Experimental combined environments use `OBL-COMBINED-R<round>-<variant>` or another stable documented identifier.",
    ]
    (OBL / "ENVIRONMENT_REGISTRY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_ledger_md(records: list[dict]) -> None:
    lines = [
        "# Objective Balance Lab — Experiment Ledger",
        "",
        "Every Round 1 and Round 2 candidate is permanent evidence. Rejection or inconclusiveness does not delete an experiment. No record below authorizes a baseline replacement or promotion.",
        "",
        "| Experiment ID | Round | Deck | Parent | Exact diff | Candidate WR | Parent WR | Balance Δ (pp) | Matchup-extreme change | Identity | Verdict | Promotion eligibility | Evidence | Key lesson |",
        "|---|---|---|---|---|---:|---:|---:|---|---|---|---|---|---|",
    ]
    for record in records:
        additions = ", ".join(
            f"+{count} {name}" for name, count in record["exact_additions"].items()
        )
        removals = ", ".join(f"-{count} {name}" for name, count in record["exact_removals"].items())
        metrics = record["result_metrics"]
        p = metrics["parent_extremes"]
        c = metrics["candidate_extremes"]
        lesson = (
            "Package-level result only; no single-card causal claim."
            if record["verdict"] == "INCONCLUSIVE"
            else (
                "Balance improved, but combined-matrix validation is still required."
                if metrics["balance_delta"] < 0
                else "The package did not reduce the balance problem; preserve as regression evidence."
            )
        )
        lines.append(
            f"| `{record['experiment_id']}` | {record['round']} | {record['deck']} | `{record['parent']['sha256'][:12]}…` | {removals}; {additions} | {metrics['candidate_win_rate']:.2%} | {metrics['parent_win_rate']:.2%} | {metrics['balance_delta'] * 100:+.2f} pp | {p['over_60_40']}→{c['over_60_40']} >60/40; {p['over_70_30']}→{c['over_70_30']} >70/30; worst `{p['worst_matchup']}`→`{c['worst_matchup']}` | {record['identity_classification']} | {record['verdict']} | `NOT_PROMOTED_COMBINED_MATRIX_REQUIRED` | `{record['source_evidence']['path']}` | {lesson} |"
        )
    lines += [
        "",
        "Stable IDs use `OBL-R<round>-<DECK>-<variant>`. Round 1 has one candidate per deck and uses variant `A`; Round 2 has isolated `A` and `B` candidates.",
    ]
    (OBL / "EXPERIMENT_LEDGER.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
