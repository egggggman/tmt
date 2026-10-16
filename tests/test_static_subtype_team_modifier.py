"""Generic regular-subtype static team modifiers in the P/T modification layer."""

from dataclasses import replace
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, load_facts

LAND = CardFact("Swamp", "", 0, "Basic Land — Swamp")
FRAGMENT = "Other Ninjas you control get +1/+1."
SOURCE = CardFact(
    "Example Mentor",
    "{2}{B}",
    3,
    "Legendary Creature — Mutant Ninja Rat",
    FRAGMENT,
    power=3,
    toughness=3,
)
NINJA = CardFact("Example Ninja", "{1}{B}", 2, "Creature — Ninja", power=1, toughness=1)
OTHER = CardFact("Example Rat", "{1}{B}", 2, "Creature — Rat", power=1, toughness=1)
RESTRICTED = CardFact(
    "Example Evader",
    "{B}",
    1,
    "Creature — Rat",
    "This creature can't be blocked by creatures with power 2 or greater.",
    power=1,
    toughness=1,
)


def game(seed=289):
    current = Game(([LAND] * 30, [LAND] * 30), seed=seed)
    current.begin_turn()
    return current


def enter(current, card, controller):
    permanent = current.create_permanent(card, controller, summoning_sick=False)
    current.refresh_static_pt_modifiers()
    return permanent


def test_frozen_oracle_and_generic_regular_plural_fail_closed():
    catalog = Path(__file__).resolve().parents[1] / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
    frozen = load_facts(
        load_card_data(catalog, catalog.with_suffix(".manifest.json")),
        {"Splinter, Hamato Yoshi"},
    )["Splinter, Hamato Yoshi"]
    interpreter = CardInterpreter()
    assert frozen.oracle_text.endswith(FRAGMENT)
    for card in (frozen, SOURCE, replace(SOURCE, name="Unrelated Mentor")):
        semantics = interpreter.static_team_modifier_semantic_coverage(card, FRAGMENT)
        assert semantics is not None and semantics.coverage.fully_supported
        assert (
            semantics.program.quality,
            semantics.program.power,
            semantics.program.toughness,
        ) == (
            "Ninja",
            1,
            1,
        )
        assert FRAGMENT not in dict(interpreter.unsupported_fragments(card))
    for fragment in (
        "Other Ninjas you control get +1/+1 and have menace.",
        "Other Ninjas get +1/+1.",
        "Other Elves you control get +1/+1.",
    ):
        assert interpreter.static_team_modifier_semantic_coverage(SOURCE, fragment) is None

    current = game(seed=292)
    splinter = enter(current, frozen, 0)
    ninja = enter(current, NINJA, 0)
    assert splinter.power == int(frozen.power)
    assert (ninja.power, ninja.toughness) == (2, 2)
    current.check_invariants()


def test_subtype_control_source_exit_suppression_and_reentry_recalculate():
    def replay():
        current = game()
        source = enter(current, SOURCE, 0)
        own = enter(current, NINJA, 0)
        opponent = enter(current, NINJA, 1)
        rat = enter(current, OTHER, 0)
        assert (source.power, own.power, own.toughness, opponent.power, rat.power) == (
            3,
            2,
            2,
            1,
            1,
        )
        catalog = (
            Path(__file__).resolve().parents[1] / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
        )
        aura_card = load_facts(
            load_card_data(catalog, catalog.with_suffix(".manifest.json")), {"Retro-Mutation"}
        )["Retro-Mutation"]
        aura = current.create_permanent(aura_card, 1)
        current.attach_aura(aura, source)
        assert own.power == own.toughness == 1
        current.move_object(aura, "graveyard", reason="test_aura_departure")
        assert own.power == 2
        current.change_controller(source, 1)
        assert own.power == 1 and opponent.power == 2 and source.power == 3
        current.change_controller(source, 0)
        assert own.power == 2 and opponent.power == 1
        gone = current.move_object(source, "graveyard", reason="test_departure")
        assert own.power == 1 and gone.object_id != source.object_id
        returned = current.move_object(gone, "battlefield", controller=0, reason="test_return")
        assert returned.object_id != source.object_id and own.power == 2
        current.check_invariants()
        return current.events, current.snapshot()

    assert replay() == replay()


def test_subtype_changes_stack_and_combat_blocking_power():
    current = game(seed=290)
    first = enter(current, SOURCE, 0)
    second = enter(current, SOURCE, 0)
    ninja = enter(current, NINJA, 0)
    rat = enter(current, OTHER, 0)
    enemy = enter(current, RESTRICTED, 1)
    assert (first.power, second.power, ninja.power, ninja.toughness) == (4, 4, 3, 3)
    assert not current.can_block(enemy, ninja, 0)
    rat.type_line_override = "Creature — Ninja"
    current.refresh_static_pt_modifiers()
    assert (rat.power, rat.toughness) == (3, 3)
    ninja.type_line_override = "Creature — Rat"
    current.refresh_static_pt_modifiers()
    assert ninja.power == ninja.toughness == 1
    assert current.can_block(enemy, ninja, 0)
    current.move_object(first, "graveyard", reason="test_departure")
    assert second.power == 3 and rat.power == 2
    current.move_object(second, "graveyard", reason="test_departure")
    assert rat.power == 1
    current.check_invariants()


def test_loss_of_toughness_exposes_lethal_damage_on_source_departure():
    current = game(seed=291)
    source = enter(current, SOURCE, 0)
    ninja = enter(current, NINJA, 0)
    ninja.damage = 1
    current.check_state_based_actions()
    assert current.is_authoritative(ninja, "battlefield")
    current.move_object(source, "graveyard", reason="test_departure")
    current.check_state_based_actions()
    assert ninja.zone == "former"
    assert any(card.card is NINJA for card in current.players[0].graveyard)
    current.check_invariants()
