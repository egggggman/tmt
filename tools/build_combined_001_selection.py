"""Materialize the governed OBL-COMBINED-001 ten-deck selection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

# Selection rationales and generated Markdown rows are intentionally long.
# ruff: noqa: E501

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
SELECTION = {
    "leonardo": (
        "OBL-R1-LEONARDO-A",
        "Round 1 has the stronger balance-error improvement (-0.56 pp); R2B improves the >70/30 count but is balance-neutral, so R1 is selected.",
        "candidate",
    ),
    "raphael": (
        None,
        "No candidate is accepted; preserve the baseline while the Casey-density reduction goal remains unresolved.",
        "baseline",
    ),
    "donatello": (
        "OBL-R2-DONATELLO-A",
        "Accepted R2A improves balance error by -0.78 pp, strengthens identity, and reduces >70/30 matchups 5→4.",
        "candidate",
    ),
    "michelangelo": (
        None,
        "R1 and R2 produced zero observable delta; preserve baseline pending a semantically observable experiment.",
        "baseline",
    ),
    "splinter": (
        None,
        "R1 and R2 produced zero observable delta; preserve baseline pending a semantically observable experiment.",
        "baseline",
    ),
    "shredder": (
        None,
        "No candidate produced a downward power delta; preserve this major overperformer unchanged for environmental interaction measurement.",
        "baseline",
    ),
    "krang": (
        "OBL-R2-KRANG-B",
        "Accepted R2B is the only tested route with a balance-error improvement, but its >60/40 count rises 6→8; select for combined interaction testing, not promotion.",
        "candidate",
    ),
    "bebop_rocksteady": (
        "OBL-R2-BEBOP_ROCKSTEADY-B",
        "Strongest accepted package: balance error improves -3.44 pp while identity strengthens.",
        "candidate",
    ),
    "april_oneil": (
        "OBL-R1-APRIL_ONEIL-A",
        "R1 improves balance error -2.44 pp versus R2A -0.44 pp; choose the stronger global balance signal.",
        "candidate",
    ),
    "casey_jones": (
        "OBL-R2-CASEY_JONES-B",
        "R2B improves balance error -1.22 pp versus R1 -1.00 pp and strengthens Casey's artifact identity.",
        "candidate",
    ),
}
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


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    registry = json.loads((OBL / "ENVIRONMENT_REGISTRY.json").read_text(encoding="utf-8"))
    ledger = json.loads((OBL / "EXPERIMENT_LEDGER.json").read_text(encoding="utf-8"))
    by_id = {record["experiment_id"]: record for record in ledger["experiments"]}
    selected = []
    for deck in registry["decks"]:
        deck_key = deck["deck_key"]
        experiment_id, rationale, source_kind = SELECTION[deck_key]
        if experiment_id:
            record = by_id[experiment_id]
            assert record["verdict"] == "ACCEPTED_FOR_COMBINED_MATRIX"
            source_path = record["candidate"]["path"]
            selected_sha = record["candidate"]["sha256"]
            diff = {"additions": record["exact_additions"], "removals": record["exact_removals"]}
        else:
            source_path = deck["source_path"]
            selected_sha = deck["sha256"]
            diff = {"additions": {}, "removals": {}}
        assert sha(ROOT / source_path) == selected_sha
        selected.append(
            {
                "deck": deck["deck"],
                "deck_key": deck_key,
                "experiment_id": experiment_id,
                "source_kind": source_kind,
                "source_path": source_path,
                "selected_sha256": selected_sha,
                "parent_baseline_sha256": deck["sha256"],
                "exact_diff": diff,
                "selection_rationale": rationale,
            }
        )
    manifest = {
        "schema": "objective-balance-lab-combined-environment-v1",
        "environment_id": "OBL-COMBINED-001",
        "state": "EXPERIMENTAL_COMBINED_ENVIRONMENT",
        "repository_sha": "0017d9d3b65d57474789ef24471deb615a9b1e54",
        "parent_environment_id": "OBL-BASELINE-000",
        "selection_gate": "SELECT COMBINED-MATRIX CANDIDATES",
        "baseline_evidence": {
            "path": "docs/objective-balance-lab/ROUND_1_EVIDENCE.json",
            "sha256": sha(OBL / "ROUND_1_EVIDENCE.json"),
        },
        "round2_evidence": {
            "path": "docs/objective-balance-lab/ROUND_2_EVIDENCE.json",
            "sha256": sha(OBL / "ROUND_2_EVIDENCE.json"),
        },
        "selected_decks": selected,
    }
    combined = OBL / "combined"
    combined.mkdir(exist_ok=True)
    (combined / "OBL_COMBINED_001_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# OBL-COMBINED-001 Selection",
        "",
        "This is a provisional combined validation environment, not a baseline and not a promotion. Selection follows the governance gate and uses only preserved baseline or accepted candidate files.",
        "",
        "- Environment: `OBL-COMBINED-001`",
        "- State: `EXPERIMENTAL_COMBINED_ENVIRONMENT`",
        "- Parent: `OBL-BASELINE-000`",
        "- Repository SHA: `0017d9d3b65d57474789ef24471deb615a9b1e54`",
        "",
        "| Deck | Selected experiment | Source | Selected SHA-256 | Parent baseline SHA-256 | Diff | Rationale |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in selected:
        additions = (
            ", ".join(f"+{n} {c}" for c, n in item["exact_diff"]["additions"].items()) or "none"
        )
        removals = (
            ", ".join(f"-{n} {c}" for c, n in item["exact_diff"]["removals"].items()) or "none"
        )
        lines.append(
            f"| {item['deck']} | `{item['experiment_id'] or 'BASELINE'}` | `{item['source_path']}` | `{item['selected_sha256']}` | `{item['parent_baseline_sha256']}` | {removals}; {additions} | {item['selection_rationale']} |"
        )
    lines += [
        "",
        "No candidate is promoted. Krang R2B is selected for interaction testing despite its isolated 6→8 increase in >60/40 matchups because it is accepted for combined-matrix validation; that concern is a specific combined gate question.",
    ]
    (OBL / "COMBINED_001_SELECTION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
