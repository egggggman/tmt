"""Generic copiable-characteristic Equipment token activation."""

from dataclasses import replace
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, TurnStep, load_facts

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
FACTS = load_facts(
    load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")), {"Improvised Arsenal"}
)
EQUIPMENT = FACTS["Improvised Arsenal"]
LAND = CardFact("Mountain", "", 0, "Basic Land — Mountain")
CREATURE = CardFact("Bearer", "{1}{R}", 2, "Creature — Human", power=2, toughness=2)
FRAGMENT = "{4}{R}: Create a token that's a copy of this Equipment."


def setup(seed=902):
    game = Game(([LAND] * 40, [LAND] * 40), seed=seed)
    game.begin_turn()
    source = game.create_permanent(EQUIPMENT, 0, summoning_sick=False)
    bearer = game.create_permanent(CREATURE, 0, summoning_sick=False)
    source.attached_to = bearer.object_id
    for _ in range(5):
        game.create_permanent(LAND, 0, tapped=False)
    game.advance_to(TurnStep.PRECOMBAT_MAIN)
    return game, source, bearer


def resolve(game):
    first = game.legal_priority_actions(game.priority_state.player_index)[0]
    game.execute_priority_action(first)
    second = game.legal_priority_actions(game.priority_state.player_index)[0]
    game.execute_priority_action(second)
    game.process_priority_resolution()


def test_parser_is_generic_and_rejects_partial_copy_clauses():
    interpreter = CardInterpreter()
    semantics = interpreter.activated_ability_semantics(EQUIPMENT, FRAGMENT)
    assert semantics is not None
    assert semantics.coverage.fully_supported
    assert semantics.program.effect_kind is ActivatedEffectKind.COPY_THIS_EQUIPMENT
    renamed = replace(EQUIPMENT, name="Anonymous Equipment")
    assert interpreter.activated_ability_semantics(renamed, FRAGMENT).coverage.fully_supported
    partial = interpreter.activated_ability_semantics(
        renamed, FRAGMENT.replace("this Equipment", "target Equipment")
    )
    assert partial is not None and not partial.coverage.fully_supported


def test_legal_activation_pays_and_creates_unattached_independent_copy():
    game, source, bearer = setup()
    options = tuple(
        option
        for option in game.legal_activated_ability_actions(0)
        if option.object_id == source.object_id and option.oracle_fragment == FRAGMENT
    )
    assert len(options) == 1
    ability = game.announce_activated_ability(0, source, FRAGMENT)
    assert ability is not None
    resolve(game)
    copies = [
        permanent
        for permanent in game.players[0].battlefield
        if permanent.is_token and permanent.card.name == EQUIPMENT.name
    ]
    assert len(copies) == 1
    copy = copies[0]
    assert copy.type_line == EQUIPMENT.type_line
    assert copy.card.oracle_text == EQUIPMENT.oracle_text
    assert copy.card.mana_cost == EQUIPMENT.mana_cost
    assert copy.attached_to is None
    assert source.attached_to == bearer.object_id
    proof = [event for event in game.events if event["event"] == "copied_artifact_token_created"]
    assert len(proof) == 1
    assert proof[0]["source_id"] == source.object_id
    game.check_invariants()


def test_copy_source_departure_fails_closed_and_replay_is_exact():
    def run():
        game, source, _bearer = setup(seed=903)
        ability = game.announce_activated_ability(0, source, FRAGMENT)
        assert ability is not None
        game.move_object(source, "graveyard", reason="before_copy_resolution")
        resolve(game)
        assert not any(event["event"] == "copied_artifact_token_created" for event in game.events)
        game.check_invariants()
        return game.snapshot(), game.events, game.rng.records

    assert run() == run()


def test_invalid_non_equipment_copy_does_not_become_supported():
    interpreter = CardInterpreter()
    card = replace(EQUIPMENT, type_line="Artifact — Vehicle")
    semantics = interpreter.activated_ability_semantics(card, FRAGMENT)
    assert semantics is not None and not semantics.coverage.fully_supported
