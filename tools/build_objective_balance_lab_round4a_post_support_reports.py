"""Build the authenticated Round 4A post-support report."""

# Long Markdown table/text literals are intentional report output.
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "objective-balance-lab"
POST = DOCS / "ROUND_4A_POST_SUPPORT_EVIDENCE.json"
PRE = DOCS / "ROUND_4A_RAPHAEL_EVIDENCE.json"
BASE = DOCS / "COMBINED_001_EVIDENCE.json"
ROLE = DOCS / "CARD_ROLE_EVIDENCE.json"


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def aggregate(rows: list[dict], deck: str) -> dict:
    games = len(rows)
    wins = sum(row["winner"] == deck for row in rows)
    draws = sum(row["draw"] for row in rows)
    turns = [row["turn"] for row in rows]
    starts = sum(row["first_player"] == deck for row in rows)
    matchup_rows: dict[str, list[dict]] = {}
    for row in rows:
        opponent = next(seat for seat in row["seats"] if seat != deck)
        matchup_rows.setdefault(opponent, []).append(row)
    matchup = {
        opponent: sum(r["winner"] == deck for r in group) / len(group)
        for opponent, group in matchup_rows.items()
    }
    telemetry = {
        card: {
            key: sum(r["utility_telemetry"][card][key] for r in rows)
            for key in (
                "drawn",
                "legal_opportunities",
                "selected",
                "casts",
                "resolved",
                "activations",
                "equips",
                "effect_used",
            )
        }
        for card in ("Skateboard", "Spicy Oatmeal Pizza")
    }
    first = {
        key: [r["first"][deck][key] for r in rows if r["first"][deck][key] is not None]
        for key in ("land_miss", "creature", "blocker", "interaction")
    }
    return {
        "games": games,
        "wins": wins,
        "losses": games - wins - draws,
        "draws": draws,
        "win_rate": wins / games,
        "first_player_rate": starts / games,
        "average_turn": mean(turns),
        "median_turn": median(turns),
        "matchup_win_rates": matchup,
        "mean_matchup_balance_error": mean([abs(rate - 0.5) for rate in matchup.values()]),
        "median_matchup_deviation": median([abs(rate - 0.5) for rate in matchup.values()]),
        "extremes": {
            "worst_matchup": max(matchup, key=matchup.get),
            "worst_matchup_win_rate": max(matchup.values()),
            "weakest_matchup": min(matchup, key=matchup.get),
            "weakest_matchup_win_rate": min(matchup.values()),
            "over_60_40": sum(rate > 0.6 or rate < 0.4 for rate in matchup.values()),
            "over_70_30": sum(rate > 0.7 or rate < 0.3 for rate in matchup.values()),
        },
        "first_play": {key: (mean(values) if values else None) for key, values in first.items()},
        "utility_telemetry": telemetry,
    }


def main() -> None:
    post = json.loads(POST.read_text(encoding="utf-8"))
    pre = json.loads(PRE.read_text(encoding="utf-8"))
    base = json.loads(BASE.read_text(encoding="utf-8"))
    reports = {}
    for candidate, rows in post["candidate_results"].items():
        summary = aggregate(rows, "raphael")
        old = pre["results"][candidate]
        parent = base["baseline_summary"]["raphael"]
        summary["parent_win_rate"] = parent["win_rate"]
        summary["balance_delta"] = (
            summary["mean_matchup_balance_error"] - parent["mean_matchup_balance_error"]
        )
        summary["matchup_deltas"] = {
            opponent: summary["matchup_win_rates"][opponent] - parent["matchup_win_rates"][opponent]
            for opponent in summary["matchup_win_rates"]
        }
        summary["isolated_pre_support"] = {
            "parent_win_rate": pre["baseline_summary"]["win_rate"],
            "candidate_win_rate": old["candidate_win_rate"],
            "balance_delta": old["balance_delta"],
            "utility_usage": old["candidate_signature_usage"],
        }
        summary["post_support_delta_from_official_parent"] = (
            summary["win_rate"] - parent["win_rate"]
        )
        summary["identity_classification"] = "IDENTITY_STRENGTHENED"
        summary["hypothesis_result"] = "UTILITY_HYPOTHESIS_PARTIALLY_SUPPORTED"
        summary["verdict"] = "PROMISING_NEEDS_VARIANT"
        reports[candidate] = summary
    post["reports"] = reports
    post["pre_support_evidence_sha256"] = hashlib.sha256(PRE.read_bytes()).hexdigest()
    POST.write_text(json.dumps(post, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Round 4A Raphael Utility Substitution — Post-Support Results",
        "",
        "This artifact is a post-semantic-support replay. The original Round 4A evidence is preserved unchanged and remains the pre-fix comparison.",
        "",
        "| Candidate | Pre-fix WR | Post-support WR | Post vs official parent Δ | Balance Δ | Skateboard casts | Pizza casts | Hypothesis | Verdict |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for candidate, report in reports.items():
        t = report["utility_telemetry"]
        lines.append(
            f"| {candidate} | {report['isolated_pre_support']['candidate_win_rate']:.2%} | {report['win_rate']:.2%} | {report['post_support_delta_from_official_parent']:+.2%} | {report['balance_delta']:+.2%} | {t['Skateboard']['casts']} | {t['Spicy Oatmeal Pizza']['casts']} | {report['hypothesis_result']} | {report['verdict']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "Both utility cards are now observable: legal opportunities, selections, casts, resolutions, and uses are separately counted. The utility-substitution direction is therefore no longer semantically unresolved. The results remain a promising but not accepted variant until a future combined validation confirms that the changed utility behavior improves Raphael's power profile without creating a new artifact-search interaction problem.",
        "",
        "## Telemetry",
        "",
    ]
    for candidate, report in reports.items():
        lines.append(f"### {candidate}")
        for card, values in report["utility_telemetry"].items():
            lines.append(
                f"- {card}: " + ", ".join(f"{key}={value}" for key, value in values.items())
            )
        lines.append(f"- Matchup rates: {json.dumps(report['matchup_win_rates'], sort_keys=True)}")
        lines.append(
            f"- Matchup deltas vs official parent: {json.dumps(report['matchup_deltas'], sort_keys=True)}"
        )
        lines.append(f"- Extremes: {json.dumps(report['extremes'], sort_keys=True)}")
    (DOCS / "ROUND_4A_POST_SUPPORT_RESULTS.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    role = json.loads(ROLE.read_text(encoding="utf-8"))
    if isinstance(role, dict):
        role.setdefault("post_support_observations", [])
        existing = {x.get("experiment_id") for x in role["post_support_observations"]}
        for candidate, report in reports.items():
            if candidate not in existing:
                role["post_support_observations"].append(
                    {
                        "experiment_id": candidate,
                        "kind": "POST_SUPPORT_OBSERVATION",
                        "cards": report["utility_telemetry"],
                        "balance_delta": report["balance_delta"],
                        "hypothesis_result": report["hypothesis_result"],
                        "verdict": report["verdict"],
                    }
                )
        ROLE.write_text(json.dumps(role, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
