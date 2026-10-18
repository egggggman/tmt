"""Generic combat-damage artifact-copy triggers."""

from dataclasses import replace
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    Game,
    TurnStep,
    load_facts,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
DONATELLO = load_facts(
    load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")),
    {"Donatello, Gadget Master"},
)["Donatello, Gadget Master"]
ARTIFACT = CardFact(
    "Test Device",
    "{2}",
    2,
    "Artifact — Equipment",
    "Equipped creature gets +1/+0.",
)
LAND = CardFact("Island", "", 0, "Basic Land — Island")
FRAGMENT = (
    "Whenever Donatello deals combat damage to a player, create a token that's a copy of "
    "target artifact you control."
)


def setup(seed=901):
    game = Game(([LAND] * 40, [LAND] * 40), seed=seed)
    game.begin_turn()
    source = game.create_permanent(DONATELLO, 0, summoning_sick=False)
    target = game.create_permanent(ARTIFACT, 0, summoning_sick=False)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    game.execute_attack_action(
        next(
            option
            for option in game.legal_attack_options(0)
            if option.attacker_ids == (source.object_id,)
        )
    )
    game.execute_block_action(ActionOption(ActionKind.DECLARE_BLOCKERS, 1, blocks=()))
    return game, source, target


def drain(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                next(
                    option
                    for option in game.legal_priority_actions(game.priority_state.player_index)
                    if option.kind is ActionKind.PASS_PRIORITY
                )
            )


def test_parser_is_generic_and_complete():
    interpreter = CardInterpreter()
    assert interpreter.combat_damage_artifact_copy(DONATELLO, FRAGMENT)
    renamed = replace(
        DONATELLO,
        name="Anonymous Gadget",
        oracle_text=DONATELLO.oracle_text.replace("Donatello", "Anonymous Gadget"),
    )
    renamed_fragment = FRAGMENT.replace("Donatello", "Anonymous Gadget")
    assert interpreter.combat_damage_artifact_copy(renamed, renamed_fragment)
    assert not interpreter.combat_damage_artifact_copy(
        DONATELLO, FRAGMENT.replace("target artifact", "target creature")
    )


def test_damage_trigger_selects_and_copies_target_artifact():
    game, source, target = setup()
    game.resolve_combat_damage()
    assert game.stack[-1].target_id == target.object_id
    drain(game)
    copies = [
        permanent
        for permanent in game.players[0].battlefield
        if permanent.is_token and permanent.card.name == ARTIFACT.name
    ]
    assert len(copies) == 1
    assert copies[0].attached_to is None
    assert any(event["event"] == "combat_artifact_copy_target_selected" for event in game.events)
    assert any(event["event"] == "combat_artifact_copy_resolved" for event in game.events)
    game.check_invariants()


def test_target_departure_fizzles_and_source_departure_is_independent():
    game, source, target = setup(seed=902)
    game.resolve_combat_damage()
    game.move_object(target, "graveyard", reason="priority_response")
    game.move_object(source, "graveyard", reason="priority_response")
    drain(game)
    assert not any(event["event"] == "copied_artifact_token_created" for event in game.events)
    assert any(
        event["event"] == "combat_artifact_copy_resolved" and not event["legal_target"]
        for event in game.events
    )
    game.check_invariants()
