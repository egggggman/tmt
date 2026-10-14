"""Oracle-derived generic mana discounts and payment revalidation."""

from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    Game,
    ManaRequirement,
    TurnStep,
    load_facts,
)

ROOT = Path(__file__).resolve().parents[1]
ISLAND = CardFact("Island", "", 0, "Basic Land — Island")
FOREST = CardFact("Forest", "", 0, "Basic Land — Forest")
MOUNTAIN = CardFact("Mountain", "", 0, "Basic Land — Mountain")
ARTIFACT = CardFact("Tool", "{1}", 1, "Artifact")
TURTLE = CardFact(
    "Generic Turtle", "{1}{G}", 2, "Creature — Mutant Ninja Turtle", power=2, toughness=2
)
CONDITIONAL = CardFact(
    "Generic Conditional",
    "{2}{G}",
    3,
    "Creature — Beast",
    "This spell costs {1} less to cast if you control a Turtle.",
    3,
    3,
)
AFFINITY = CardFact(
    "Generic Affinity",
    "{3}{U}{U}",
    5,
    "Artifact Creature — Construct",
    "Affinity for artifacts (This spell costs {1} less to cast for each artifact you control.)",
    4,
    4,
)
RESTRICTED = CardFact(
    "Generic Restricted",
    "{1}{R}",
    2,
    "Creature — Rogue",
    "{T}: Add {R}. Spend this mana only to cast an artifact spell or to activate an ability.",
    2,
    2,
)
RED_SPELL = CardFact("Red Spell", "{R}", 1, "Creature — Test", power=1, toughness=1)
SNEAK = CardFact(
    "Generic Sneak",
    "{5}{G}",
    6,
    "Creature — Ninja",
    "Sneak {3}{G} (You may cast this spell for {3}{G} if you also return an unblocked "
    "attacker you control to hand during the declare blockers step. It enters tapped and "
    "attacking.)\nThis spell costs {1} less to cast if you control a Turtle.",
    4,
    4,
)


def frozen_facts():
    catalog = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    return load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Krang, Master Mind", "Saved by the Shell", "Purple Dragon Punks"},
    )


def game(card, *, lands=()):
    current = Game(([ISLAND] * 60, [ISLAND] * 60), seed=947)
    current.begin_turn()
    current.set_hand_for_testing(0, [card])
    for land in lands:
        current.create_permanent(land, 0, summoning_sick=False)
    return current


def test_affinity_counts_controlled_artifacts_at_current_types_and_caps_at_zero():
    current = game(AFFINITY, lands=(ISLAND, ISLAND))
    card = current.players[0].hand[0]
    assert Game.mana_requirement(card) == ManaRequirement(3, ("U", "U"))
    assert current.casting_requirement(0, card) == ManaRequirement(3, ("U", "U"))
    first = current.create_permanent(ARTIFACT, 0)
    first.tapped = True
    current.create_permanent(ARTIFACT, 1)
    second = current.create_permanent(ARTIFACT, 0)
    assert current.casting_requirement(0, card) == ManaRequirement(1, ("U", "U"))
    assert current.payment_plan(0, card) is None
    second.type_line_override = "Creature — Construct"
    assert current.casting_requirement(0, card).generic == 2
    second.type_line_override = "Artifact Creature — Construct"
    for _ in range(4):
        current.create_permanent(ARTIFACT, 0)
    assert current.casting_requirement(0, card) == ManaRequirement(0, ("U", "U"))
    plan = current.payment_plan(0, card)
    assert plan is not None and len(plan.source_ids) == 2


def test_affinity_cast_records_payment_and_deterministic_source_witnesses():
    def run():
        current = game(AFFINITY, lands=(ISLAND, ISLAND))
        sources = [current.create_permanent(ARTIFACT, 0) for _ in range(3)]
        card = current.players[0].hand[0]
        assert any(
            option.kind is ActionKind.CAST and option.object_id == card.object_id
            for option in current.legal_main_actions(0)
        )
        spell = current.announce_spell(0, card)
        assert spell is not None and spell.cast_kind is CastKind.PERMANENT
        reduction = next(e for e in current.events if e["event"] == "casting_cost_reduced")
        assert reduction["printed_generic"] == 3 and reduction["paid_generic"] == 0
        assert reduction["reductions"][0]["qualifying_source_ids"] == [s.object_id for s in sources]
        current.resolve_top_of_stack()
        current.check_invariants()
        return current.snapshot()

    assert run() == run()


def test_payment_plan_rechecks_discount_before_any_mana_or_zone_mutation():
    current = game(AFFINITY, lands=(ISLAND, ISLAND))
    sources = [current.create_permanent(ARTIFACT, 0) for _ in range(3)]
    card = current.players[0].hand[0]
    plan = current.payment_plan(0, card)
    assert plan is not None
    current.move_object(sources[-1], "graveyard", reason="test_source_departure")
    with pytest.raises(ValueError, match="no longer legal"):
        current._commit_announcement_payment(
            card, plan, cast_kind=CastKind.PERMANENT, target_id=None
        )
    assert all(not land.tapped for land in current.players[0].battlefield if land.card.is_land)
    assert current.is_authoritative(card, "hand")


def test_conditional_subtype_reduction_is_controller_scoped_and_nonstacking():
    current = game(CONDITIONAL, lands=(FOREST, FOREST))
    card = current.players[0].hand[0]
    assert current.payment_plan(0, card) is None
    current.create_permanent(TURTLE, 1)
    assert current.casting_requirement(0, card).generic == 2
    turtle = current.create_permanent(TURTLE, 0)
    current.create_permanent(TURTLE, 0)
    assert current.casting_requirement(0, card) == ManaRequirement(1, ("G",))
    assert current.payment_plan(0, card) is not None
    turtle.type_line_override = "Creature — Beast"
    assert current.casting_requirement(0, card).generic == 1  # the second Turtle still qualifies
    current.announce_spell(0, card)
    assert next(e for e in current.events if e["event"] == "cost_paid")["generic"] == 1


def test_frozen_krang_discount_and_saved_payload_execute():
    facts = frozen_facts()
    krang, saved, punks = (
        facts[name] for name in ("Krang, Master Mind", "Saved by the Shell", "Purple Dragon Punks")
    )
    interpreter = CardInterpreter()
    assert interpreter.generic_cost_reduction_program(krang, interpreter.fragments(krang)[0])
    current = game(krang, lands=(ISLAND, ISLAND))
    for _ in range(6):
        current.create_permanent(ARTIFACT, 0)
    card = current.players[0].hand[0]
    assert current.payment_plan(0, card).requirement == ManaRequirement(0, ("U", "U"))
    assert current.announce_spell(0, card) is not None
    current.resolve_top_of_stack()
    current.check_invariants()

    current = game(saved, lands=(FOREST,))
    current.create_permanent(TURTLE, 0)
    assert current.payment_plan(0, current.players[0].hand[0]).requirement == ManaRequirement(
        0, ("G",)
    )
    assert interpreter.cast_program(saved).kind is CastKind.TARGETED_COUNTER_KEYWORD_GRANT
    assert any(option.kind is ActionKind.CAST for option in current.legal_main_actions(0))

    current = game(RED_SPELL, lands=(MOUNTAIN,))
    source = current.create_permanent(punks, 0, summoning_sick=False)
    assert (
        interpreter.activated_ability_semantics(
            punks, interpreter.fragments(punks)[0]
        ).coverage.fully_supported
        is True
    )
    assert current._mana_colors(source) == ()
    current.players[0].battlefield[0].tapped = True
    assert current.payment_plan(0, current.players[0].hand[0]) is None


def test_casting_discount_does_not_grant_instant_timing_or_change_other_costs():
    current = game(CONDITIONAL, lands=(FOREST, FOREST))
    current.create_permanent(TURTLE, 0)
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    assert current.payment_plan(0, current.players[0].hand[0]) is not None
    assert current.announce_spell(0, current.players[0].hand[0]) is None
    assert Game.mana_requirement(replace(CONDITIONAL, oracle_text="")) == ManaRequirement(2, ("G",))


def test_discount_applies_to_sneak_alternative_without_changing_cast_timing():
    current = game(SNEAK, lands=(FOREST, FOREST, FOREST, FOREST))
    attacker = current.create_permanent(
        CardFact("Attacker", "{G}", 1, "Creature — Beast", power=1, toughness=1),
        0,
        summoning_sick=False,
    )
    card = current.players[0].hand[0]
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    current.execute_attack_action(
        ActionOption(ActionKind.DECLARE_ATTACKERS, 0, attacker_ids=(attacker.object_id,))
    )
    current.execute_block_action(ActionOption(ActionKind.DECLARE_BLOCKERS, 1))
    current.players[0].battlefield[0].tapped = True
    assert current.sneak_payment_plan(0, card, attacker) is None
    current.create_permanent(TURTLE, 0)
    plan = current.sneak_payment_plan(0, card, attacker)
    assert plan is not None and plan.requirement == ManaRequirement(2, ("G",))
    option = next(a for a in current.legal_sneak_actions(0) if a.kind is ActionKind.CAST)
    current.execute_sneak_action(option)
    assert current.stack[-1].name == SNEAK.name
    current.check_invariants()
