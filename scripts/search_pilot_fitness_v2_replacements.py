"""Bounded, unscored replacement search; preserves the earlier failed diagnostic."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from dataclasses import asdict
from fractions import Fraction
from itertools import combinations_with_replacement
from pathlib import Path

from prepare_pilot_fitness_v2 import ROOT, deck_path, drain, load_inputs, reachable_filter_setup

from tmnt_design_studio.engine07 import ActionKind, load_deck

OBJECTIVES = {
    "land_play": (
        "An engine-issued land play is available at the endpoint: immediate mana development."
    ),
    "creature_cast": (
        "An engine-issued creature cast is available at the endpoint: immediate board development."
    ),
    "targeted_cast": (
        "An engine-issued targeted spell cast is available at the endpoint: immediate interaction."
    ),
}


def probe(hand, mode, seat, replacement, selection):
    role = ("replacement", mode, list(hand), 0, 0)
    game = reachable_filter_setup(role, seat)
    library = game.players[seat].library
    index = next((i for i, card in enumerate(library) if card.name == replacement), None)
    if index is None:
        return None
    library[index], library[-1] = library[-1], library[index]
    captured = []

    def choose(view, options):
        captured.append({"view": asdict(view), "options": [asdict(o) for o in options]})
        return options[selection]

    game.hand_bottom_draw_chooser = choose
    ids = {c.object_id for c in game.players[seat].hand if c.name == "Manhole Missile"}
    action = next(o for o in game.legal_main_actions(seat) if o.object_id in ids and o.target_id)
    game.execute_main_action(action)
    drain(game)
    game.check_invariants()
    assert len(captured) == 1
    assert game.winner is None
    assert len(game.players[seat].hand) == len(hand)
    options = game.legal_main_actions(seat)
    creatures = {c.object_id for c in game.players[seat].hand if c.is_creature}
    values = {
        "land_play": int(any(o.kind is ActionKind.PLAY_LAND for o in options)),
        "creature_cast": int(
            any(o.kind is ActionKind.CAST and o.object_id in creatures for o in options)
        ),
        "targeted_cast": int(any(o.kind is ActionKind.CAST and o.target_id for o in options)),
    }
    return captured[0], {
        "values": values,
        "endpoint_options": [asdict(o) for o in options],
        "endpoint_hand": [(c.object_id, c.name) for c in game.players[seat].hand],
        "life": [p.life for p in game.players],
        "winner": game.winner,
    }


def main():
    prior = Counter(c.name for c in load_deck(deck_path("casey_jones"), load_inputs()))
    # Finite prospective sweep, not random search or action-sequencing optimization.
    hands = [(name,) for name in sorted(prior)]
    hands += list(
        combinations_with_replacement(["Mountain", "Purple Dragon Punks", "Rock Soldiers"], 2)
    )
    records = []
    for hand in hands:
        for mode in ("land", "creature"):
            for seat in (0, 1):
                record = {"hand": hand, "mode": mode, "seat": seat, "rows": []}
                try:
                    reachable_filter_setup(("replacement", mode, list(hand), 0, 0), seat)
                except StopIteration:
                    record["disposition"] = "REJECTED_SETUP_MULTIPLICITY"
                    record["reason"] = "Opening sequence exceeds frozen deck multiplicities."
                    records.append(record)
                    continue
                base = None
                missing = set()
                for selection in range(len(hand) + 1):
                    branches = []
                    for card, count in sorted(prior.items()):
                        outcome = probe(hand, mode, seat, card, selection)
                        if outcome is None:
                            missing.add(card)
                            continue
                        observed, endpoint = outcome
                        if base is None:
                            base = observed
                        assert observed == base
                        branches.append({"replacement": card, "weight": count, **endpoint})
                    record["rows"].append({"selection": selection, "branches": branches})
                record["input"] = base
                record["missing_positive_weight_completions"] = sorted(missing)
                if missing:
                    context = base["view"]["context"]
                    visible = Counter(c["name"] for c in context["own_hand"])
                    visible.update(c["name"] for c in context["battlefields"][seat])
                    record["visible_exhaustion_counts"] = {c: visible[c] for c in sorted(missing)}
                    assert all(visible[c] == prior[c] for c in missing)
                    record["disposition"] = "REJECTED_SUPPORT_CONSISTENCY"
                else:
                    for row in record["rows"]:
                        assert sum(b["weight"] for b in row["branches"]) == 60
                        row["reference_prior_expected_value"] = {
                            key: str(
                                sum(
                                    (
                                        Fraction(b["weight"] * b["values"][key], 60)
                                        for b in row["branches"]
                                    ),
                                    Fraction(),
                                )
                            )
                            for key in OBJECTIVES
                        }
                    q = [
                        {k: Fraction(v) for k, v in row["reference_prior_expected_value"].items()}
                        for row in record["rows"]
                    ]
                    record["strict_reversals"] = [
                        {"actions": [a, b], "objectives": [x, y]}
                        for a in range(len(q))
                        for b in range(a + 1, len(q))
                        for x, y in combinations_with_replacement(OBJECTIVES, 2)
                        if (q[a][x] - q[b][x]) * (q[a][y] - q[b][y]) < 0
                    ]
                    record["optimal_sets"] = {
                        key: [
                            i for i, values in enumerate(q) if values[key] == max(v[key] for v in q)
                        ]
                        for key in OBJECTIVES
                    }
                    record["disposition"] = (
                        "REJECTED_MODEL_SENSITIVE"
                        if record["strict_reversals"]
                        else "UNRESOLVED_NOT_ACCEPTED"
                    )
                records.append(record)
                print(
                    json.dumps({k: record[k] for k in ("hand", "mode", "seat", "disposition")}),
                    flush=True,
                )
    assert "tmnt_design_studio.pilot07" not in sys.modules
    report = {
        "status": "READINESS_STOP_NOT_SEALED",
        "prior": dict(sorted(prior.items())),
        "prior_denominator": 60,
        "failed_evidence_commit": "3f60166",
        "specification": "ACCEPTED_UNCHANGED",
        "horizon": (
            "Manhole Missile resolution, state-based actions and automatic "
            "triggers drained; no subsequent action or Draw."
        ),
        "objectives_screened": OBJECTIVES,
        "objective_inventory_limits": [
            (
                "These are immediate legal opportunities, not executed gains; "
                "resource retention and specific creature/ability distinctions "
                "still need context-specific justification."
            ),
            (
                "Total hand size and terminal status are checked equal; equality "
                "alone is not a useful U objective."
            ),
            (
                "Life, battlefield material and spent mana do not change with the "
                "filter choice in these endpoints; verify recorded life and "
                "automatic consequences before accepting any later design."
            ),
            (
                "Creature reserve without a cast opportunity is not credited as a "
                "concrete endpoint consequence."
            ),
            "Future draws, long-term deck quality and future mana curves lie outside this horizon.",
            "No candidate is accepted merely for surviving this necessary rejection screen.",
        ],
        "canonical_fixture_quota": 72,
        "canonical_fixtures_sealed": 0,
        "pilot_invocations": 0,
        "pilot_outputs": [],
        "privacy_K": None,
        "final_invocation_count": None,
        "invocation_formula": "1728 + 4K",
        "search_limit": (
            "All 13 singleton identities and six specified two-card multisets, "
            "two reachable setup modes, both seats; not an exhaustive proof "
            "over legal game states."
        ),
        "records": records,
    }
    sources = [
        Path(__file__),
        ROOT / "scripts/prepare_pilot_fitness_v2.py",
        ROOT / "docs/cardcade/PILOT_FITNESS_ASSESSMENT_SPEC_V2.md",
        ROOT / "src/tmnt_design_studio/engine07.py",
        ROOT / "src/tmnt_design_studio/pilot07.py",
    ]
    report["source_sha256_canonical_LF"] = {
        str(p.resolve().relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(
            p.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        for p in sources
    }
    path = ROOT / "docs/cardcade/PILOT_FITNESS_V2_REPLACEMENT_SEARCH.json"
    payload = (
        json.dumps(report, indent=2, sort_keys=True, default=lambda item: item.value) + "\n"
    ).encode()
    path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    Path(str(path) + ".sha256").write_text(digest + "  " + path.name + "\n", encoding="ascii")
    print(
        json.dumps(
            {"sha256": digest, "dispositions": dict(Counter(r["disposition"] for r in records))}
        )
    )


if __name__ == "__main__":
    main()
