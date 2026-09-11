"""Reconstruct an unsealed, model-sensitive preparation diagnostic; never call a Pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from dataclasses import asdict
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.engine07 import Game, load_deck, load_facts

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
CATALOG_MANIFEST = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json"


def deck_path(name):
    version = "0.2" if name in {"donatello", "krang"} else "0.1"
    return ROOT / f"decks/{name}/PROTOTYPE_{version}.txt"


@lru_cache(maxsize=1)
def load_inputs():
    catalog = load_card_data(SNAPSHOT, CATALOG_MANIFEST)
    names = set()
    for path in ROOT.glob("decks/*/PROTOTYPE_0.*.txt"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line and line[0].isdigit():
                names.add(line.split(" ", 1)[1])
    return load_facts(catalog, names)


def ordered_game(decks, draw_sequences, seed=72001):
    facts = load_inputs()
    rng = random.Random(seed)
    inputs = []
    for deck, sequence in zip(decks, draw_sequences, strict=True):
        remaining = list(load_deck(deck_path(deck), facts))
        top = []
        for name in sequence:
            card = next(c for c in remaining if c.name == name)
            remaining.remove(card)
            top.append(card)
        desired = remaining + list(reversed(top))
        permutation = list(range(60))
        rng.shuffle(permutation)
        input_deck = [None] * 60
        for output_index, input_index in enumerate(permutation):
            input_deck[input_index] = desired[output_index]
        assert Counter(c.name for c in input_deck) == Counter(
            c.name for c in load_deck(deck_path(deck), facts)
        )
        inputs.append(input_deck)
    return Game(tuple(inputs), seed=seed)


def play_named(game, seat, name):
    cards = {c.object_id: c for c in game.players[seat].hand}
    options = game.legal_main_actions(seat)
    matching = [o for o in options if o.object_id in cards and cards[o.object_id].name == name]
    if not matching:
        raise ValueError(
            (game.turn, name, [c.name for c in cards.values()], [asdict(o) for o in options])
        )
    option = matching[0]
    game.execute_main_action(option)
    drain(game)


def reachable_filter_setup(role, seat):
    label, objective, retained, _, _ = role
    # The opening permutation is reconstruction evidence, never an oracle input.
    burn = [
        "Purple Dragon Punks",
        "Ravenous Robots",
        "Rock Soldiers",
        "Purple Dragon Punks",
        "Mutant Town Musicians",
        "Null Group Biological Assets",
    ]
    sequence = ["Mountain"] * 4 + burn[:3]
    sequence += ["Mountain", burn[3], burn[4], burn[5], retained[0], "Manhole Missile"]
    sequence += ["Mountain" if objective == "creature" else "Purple Dragon Punks"]
    sequence += retained[1:]
    own_turn_endpoint = 8 + len(retained) - 1 + seat
    if seat:
        sequence += ["Ravenous Robots", "Ravenous Robots"]
    sequences = [sequence, ["Plains", "Prehistoric Pet"]]
    decks = ["casey_jones", "leonardo"]
    if seat:
        decks.reverse()
        sequences.reverse()
    game = ordered_game(decks, sequences)
    while True:
        game.begin_turn()
        active = game.active_player
        own_turn = (game.turn + 1) // 2
        if active == seat:
            if own_turn <= 5:
                play_named(game, active, "Mountain")
            if 2 <= own_turn <= 7:
                play_named(game, active, burn[own_turn - 2])
            if own_turn == 8:
                play_named(game, active, sequences[seat][13])
            if seat and own_turn in (own_turn_endpoint - 1, own_turn_endpoint):
                play_named(game, active, "Ravenous Robots")
            if own_turn == own_turn_endpoint:
                assert Counter(c.name for c in game.players[seat].hand) == Counter(
                    ["Manhole Missile", *retained]
                ), (seat, label, [c.name for c in game.players[seat].hand])
                game.check_invariants()
                return game
        elif own_turn == 1:
            play_named(game, active, "Plains")
            play_named(game, active, "Prehistoric Pet")
        game.end_turn()


def drain(game):
    for _ in range(100):
        if game.priority_state is None:
            return
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            options = game.legal_priority_actions(game.priority_state.player_index)
            game.execute_priority_action(options[0])
    raise ValueError("bounded Priority drain exceeded")


FILTER_ROLES = (
    ("land_filter", "land", ["Rock Soldiers"], 2, 0),
    ("creature_filter", "creature", ["Mountain"], 5, 1),
    ("land_retain", "land", ["Mountain"], 2, 0),
    ("creature_retain", "creature", ["Purple Dragon Punks"], 5, 1),
    ("competing_identity", "land", ["Mountain", "Rock Soldiers"], 2, 0),
    ("exact_tie", "land", ["Mountain", "Mountain"], 2, 0),
)


def filtering_probe(role, seat=0, replacement=None, selection=0):
    from tmnt_design_studio.engine07 import ActionKind

    label, objective, retained, lands, lands_played = role
    game = reachable_filter_setup(role, seat)
    if replacement is not None:
        library = game.players[seat].library
        index = next(i for i, c in enumerate(library) if c.name == replacement)
        library[index], library[-1] = library[-1], library[index]
    captured = []

    def observe(view, options):
        captured.append({"view": asdict(view), "options": [asdict(o) for o in options]})
        return options[selection]

    game.hand_bottom_draw_chooser = observe
    option = next(o for o in game.legal_main_actions(seat) if o.target_id)
    game.execute_main_action(option)
    drain(game)
    assert len(captured) == 1
    game.check_invariants()
    assert len(game.players[seat].hand) == len(captured[0]["view"]["cards"])
    endpoint_options = game.legal_main_actions(seat)
    if objective == "land":
        resource = any(o.kind is ActionKind.PLAY_LAND for o in endpoint_options)
    else:
        ids = {c.object_id for c in game.players[seat].hand if c.is_creature}
        resource = any(o.kind is ActionKind.CAST and o.object_id in ids for o in endpoint_options)
    creature_in_hand = int(any(c.is_creature for c in game.players[seat].hand))
    return captured[0], int(resource), game.winner, creature_in_hand


def check_filter_roles():
    facts = load_inputs()
    prior = Counter(c.name for c in load_deck(deck_path("casey_jones"), facts))
    results = []
    for role in FILTER_ROLES:
        for seat in (0, 1):
            base, _, _, _ = filtering_probe(role, seat)
            rows = []
            for selection in range(len(base["options"])):
                total = Fraction(0)
                alternative = Fraction(0)
                branches = []
                for card, count in sorted(prior.items()):
                    obs, value, winner, creature = filtering_probe(role, seat, card, selection)
                    assert obs == base
                    assert winner is None
                    total += Fraction(count * value, 60)
                    alternative += Fraction(count * creature, 60)
                    branches.append(
                        {
                            "card": card,
                            "multiplicity": count,
                            "u": value,
                            "creature_in_hand": creature,
                        }
                    )
                rows.append(
                    {
                        "option": base["options"][selection],
                        "Q": str(total),
                        "alternative_creature_Q": str(alternative),
                        "branches": branches,
                    }
                )
            results.append({"role": role[0], "seat": seat, "input": base, "rows": rows})
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-diagnostic", action="store_true")
    args = parser.parse_args()
    result = check_filter_roles()
    assert "tmnt_design_studio.pilot07" not in sys.modules
    for record in result:
        for row in record["rows"]:
            assert sum(b["multiplicity"] for b in row["branches"]) == 60
            for value_key, q_key in (("u", "Q"), ("creature_in_hand", "alternative_creature_Q")):
                q = sum(
                    (Fraction(b["multiplicity"] * b[value_key], 60) for b in row["branches"]),
                    Fraction(0),
                )
                assert q == Fraction(row[q_key])
        primary = max(Fraction(row["Q"]) for row in record["rows"])
        alternative = max(Fraction(row["alternative_creature_Q"]) for row in record["rows"])
        record["primary_optimal_indices"] = [
            i for i, row in enumerate(record["rows"]) if Fraction(row["Q"]) == primary
        ]
        record["alternative_optimal_indices"] = [
            i
            for i, row in enumerate(record["rows"])
            if Fraction(row["alternative_creature_Q"]) == alternative
        ]
        record["ranking_stable"] = (
            record["primary_optimal_indices"] == record["alternative_optimal_indices"]
        )
        record["pilot_outputs"] = []
    for record in result:
        if record["role"] == "land_filter":
            assert record["primary_optimal_indices"] == [1]
            assert record["alternative_optimal_indices"] == [0]
    sources = [
        Path(__file__).resolve(),
        ROOT / "docs/cardcade/PILOT_FITNESS_ASSESSMENT_SPEC_V2.md",
        ROOT / "src/tmnt_design_studio/engine07.py",
        ROOT / "src/tmnt_design_studio/card_interpreter07.py",
        ROOT / "src/tmnt_design_studio/pilot_input_v2.py",
        ROOT / "src/tmnt_design_studio/pilot07.py",
        ROOT / "src/tmnt_design_studio/stage002.py",
        ROOT / "src/tmnt_design_studio/smoke01.py",
        SNAPSHOT,
        CATALOG_MANIFEST,
        deck_path("casey_jones"),
        deck_path("leonardo"),
    ]
    hashes = {
        str(path.relative_to(ROOT)).replace(chr(92), "/"): hashlib.sha256(
            path.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        for path in sources
    }
    report = {
        "status": "MODEL-SENSITIVE / RETURN TO HQ / NOT SEALED",
        "accepted_spec_commit": "19b9bde600df4c46cb3a434d8e740278d7e6e55a",
        "accepted_interface_commit": "fa3f4944a7209f22e70d783d9a7f9abca3b37534",
        "frozen_gameplay_reference": "de52f57a24a5c29a258573ad673051a0aa5c7e5c",
        "controlling_specification": (
            "section 6; sections 4.1 and 9 prohibit filling/sealing unresolved cases"
        ),
        "canonical_fixtures_sealed": 0,
        "canonical_fixture_quota": 72,
        "role_probes": 6,
        "seat_constructions_per_probe": 2,
        "pilot_invocations": 0,
        "pilot_outputs": [],
        "privacy_K": None,
        "final_invocation_count": None,
        "unsealed_invocation_formula": "1728 + 4K",
        "setup_seed": 72001,
        "seed_use": "opening-permutation reconstruction only; never action ranking",
        "prior": dict(
            sorted(
                Counter(c.name for c in load_deck(deck_path("casey_jones"), load_inputs())).items()
            )
        ),
        "prior_denominator": 60,
        "primary_land_objective": (
            "At the instruction endpoint, at least one engine-generated PLAY_LAND option exists."
        ),
        "primary_creature_objective": (
            "At the instruction endpoint, at least one engine-generated CAST option"
            " for an own creature card exists."
        ),
        "sensitivity_objective": (
            "At the same endpoint, own hand contains at least one creature card."
        ),
        "common_constraints": (
            "Same horizon; same prior; same legal filter options; unchanged total "
            "hand size; equal terminal status. No life/card/mana exchange rate."
        ),
        "sensitivity_disposition": (
            "The land-filter proposal does not justify preferring immediate mana "
            "development over retention of a creature card. Opposite strict "
            "rankings cannot be treated as an exact tie or silently resolved."
        ),
        "limitations": [
            "No impossibility claim for alternative fixture designs or the remaining hooks.",
            "These are role probes, not six accepted canonical fixtures.",
            (
                "Seat reconstructions have different setup histories, boards and some Q"
                " values; a complete seat-transformation certificate is not claimed."
            ),
            (
                "No complete quota, control, transformation, privacy-K, final "
                "invocation, or sealing certificate exists."
            ),
            (
                "The prospective resource objectives are not HQ-approved action "
                "rankings or observed Pilot results."
            ),
        ],
        "checks": {
            "all_hypothetical_replacements_reconstructed": True,
            "same_predecision_V2_view_and_options_across_replacement_branches": True,
            "all_branch_endpoints_have_no_winner": True,
            "exact_fraction_arithmetic_recomputed": True,
            "pilot_module_not_imported": True,
            "setup_uses_ordinary_land_plays_casts_and_turn_transitions": True,
            "setup_deck_multiplicities_conserved": True,
            "engine_check_invariants_passed": True,
        },
        "source_sha256_canonical_LF": hashes,
        "results": result,
    }
    payload = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode(
        "utf-8"
    )
    digest = hashlib.sha256(payload).hexdigest()
    if args.write_diagnostic:
        path = ROOT / "docs/cardcade/PILOT_FITNESS_V2_RESOURCE_SENSITIVITY_DIAGNOSTIC.json"
        path.write_bytes(payload)
        Path(str(path) + ".sha256").write_bytes((digest + "  " + path.name + "\n").encode("ascii"))
    print(
        json.dumps(
            {
                "status": report["status"],
                "diagnostic_sha256": digest,
                "pilot_invocations": 0,
                "canonical_fixtures_sealed": 0,
            }
        )
    )
    raise SystemExit(2)
