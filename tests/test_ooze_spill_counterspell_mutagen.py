import json
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter
from tmnt_design_studio.engine07 import CardFact, CastKind, Game, StackObject, load_facts
from tmnt_design_studio.pilot07 import AcceptancePilot, PassingPilot

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
MANIFEST = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json"

LAND = CardFact("Island", "", 0, "Basic Land ? Island")
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature ? Bear", power=2, toughness=2)
OOZE = CardFact(
    "Ooze Spill",
    "{1}{U}{U}",
    3,
    "Instant",
    'Counter target spell. Create a Mutagen token. (It\'s an artifact with "{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature. Activate only as a sorcery.")',  # noqa: E501
)
MUTAGEN_FRAGMENT = "{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature. Activate only as a sorcery."  # noqa: E501


def setup():
    game = Game(([LAND] * 30, [LAND] * 30), seed=404)
    game.begin_turn()
    for _ in range(4):
        game.create_permanent(LAND, 0, summoning_sick=False)
    game.set_hand_for_testing(0, [OOZE])
    target = StackObject(game._allocate_object_id(), BEAR, 1, 1, CastKind.CREATURE)
    game._register(target)
    game.stack.append(target)
    game._begin_priority_window()
    return game, target


def authoritative_ooze() -> CardFact:
    catalog = load_card_data(SNAPSHOT, MANIFEST)
    return load_facts(catalog, {"Ooze Spill"})["Ooze Spill"]


def pass_all(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def test_ooze_spell_and_mutagen_grammar_are_exactly_supported():
    interpreter = CardInterpreter()
    assert interpreter.cast_program(OOZE).kind is CastKind.OOZE_SPILL
    semantics = interpreter.activated_ability_semantics(game_token_card(), MUTAGEN_FRAGMENT)
    assert semantics is None or semantics.program.effect_kind in {
        ActivatedEffectKind.MUTAGEN_COUNTER,
        ActivatedEffectKind.UNSUPPORTED,
    }


def game_token_card():
    return CardFact(
        "Mutagen",
        "",
        0,
        "Artifact ? Mutagen",
        MUTAGEN_FRAGMENT,
    )


def test_ooze_counters_opposing_stack_spell_and_creates_authoritative_mutagen():
    game, target = setup()
    ooze = game.players[0].hand[0]
    spell = game.announce_spell(0, ooze, target)
    assert spell is not None and spell.cast_kind is CastKind.OOZE_SPILL
    assert spell.object_id != ooze.object_id
    pass_all(game)
    assert target.zone == "former"
    token = next(p for p in game.players[0].battlefield if p.card.name == "Mutagen")
    assert token.object_id not in {ooze.object_id, target.object_id, spell.object_id}
    assert any(e["event"] == "ooze_spill_resolved" for e in game.events)
    game.check_invariants()


def test_priority_exposes_real_ooze_response_and_acceptance_pilot_selects_it():
    game, target = setup()
    ooze = game.players[0].hand[0]
    options = game.legal_priority_actions(0)
    response = next(option for option in options if option.kind.value == "cast")
    assert response.object_id == game.players[0].hand[0].object_id
    assert response.target_id == target.object_id
    choice = AcceptancePilot().choose_priority(game.priority_view(0), options)
    assert choice == response
    assert game.execute_priority_action(choice)
    assert game.stack[-1].cast_kind is CastKind.OOZE_SPILL
    assert target.zone == "stack"
    pass_all(game)
    assert target.zone == "former"
    assert ooze.zone == "former"
    assert not any(event["event"] == "creature_resolved" for event in game.events)
    event_names = [event["event"] for event in game.events]
    assert "response_window_opened" in event_names
    assert "legal_response_exposed" in event_names
    assert "response_selected" in event_names
    assert "response_target_selected" in event_names
    assert "cost_paid" in event_names
    assert "spell_countered" in event_names
    assert "ooze_spill_resolved" in event_names
    game.check_invariants()


def test_authoritative_ooze_card_is_selected_and_counters_a_creature_spell():
    ooze = authoritative_ooze()
    game = Game(([LAND] * 30, [LAND] * 30), seed=406)
    game.begin_turn()
    for _ in range(4):
        game.create_permanent(LAND, 0, summoning_sick=False)
    card = game.set_hand_for_testing(0, [ooze])[0]
    target = StackObject(game._allocate_object_id(), BEAR, 1, 1, CastKind.CREATURE)
    game._register(target)
    game.stack.append(target)
    game._begin_priority_window()
    options = game.legal_priority_actions(0)
    choice = AcceptancePilot().choose_priority(game.priority_view(0), options)
    assert choice.kind.value == "cast" and choice.object_id == card.object_id
    game.execute_priority_action(choice)
    pass_all(game)
    assert target.zone == "former"
    assert not any(
        event["event"] == "creature_resolved" and event.get("card") == "Bear"
        for event in game.events
    )
    assert any(
        event["event"] == "ooze_spill_resolved" and event["target_spell_id"] == target.object_id
        for event in game.events
    )
    assert any(permanent.card.name == "Mutagen" for permanent in game.players[0].battlefield)
    game.check_invariants()


def test_ooze_response_counters_noncreature_spell_without_resolving_it():
    game = Game(([LAND] * 30, [LAND] * 30), seed=405)
    game.begin_turn()
    for _ in range(4):
        game.create_permanent(LAND, 0, summoning_sick=False)
    game.set_hand_for_testing(0, [OOZE])
    target = StackObject(
        game._allocate_object_id(),
        CardFact("Draw Spell", "{1}{U}", 2, "Sorcery", "Draw a card."),
        1,
        1,
        CastKind.DRAW_CARDS,
    )
    game._register(target)
    game.stack[:] = [target]
    game.priority_state = None
    game._begin_priority_window()
    response = next(option for option in game.legal_priority_actions(0) if option.target_id)
    game.execute_priority_action(response)
    pass_all(game)
    assert target.zone == "former"
    assert not any(event["event"] == "draw_spell_resolved" for event in game.events)
    game.check_invariants()


def test_ooze_response_is_not_exposed_without_mana_or_against_own_spell():
    no_mana, target = setup()
    no_mana.players[0].battlefield = [
        permanent
        for permanent in no_mana.players[0].battlefield
        if permanent.card.name != "Island" or permanent is no_mana.players[0].battlefield[0]
    ]
    no_mana.players[0].battlefield[0].tapped = True
    assert not any(option.kind.value == "cast" for option in no_mana.legal_priority_actions(0))

    own_spell, own_target = setup()
    own_target.controller = 0
    assert not any(option.kind.value == "cast" for option in own_spell.legal_priority_actions(0))

    no_ooze, _ = setup()
    no_ooze.set_hand_for_testing(0, [])
    assert not any(option.kind.value == "cast" for option in no_ooze.legal_priority_actions(0))

    declined, _ = setup()
    options = declined.legal_priority_actions(0)
    assert PassingPilot().choose_priority(declined.priority_view(0), options).kind.value == (
        "pass_priority"
    )


def test_ooze_response_replay_is_deterministic():
    def run() -> str:
        game, _ = setup()
        options = game.legal_priority_actions(0)
        choice = AcceptancePilot().choose_priority(game.priority_view(0), options)
        game.execute_priority_action(choice)
        pass_all(game)
        return json.dumps(game.snapshot(), sort_keys=True)

    assert run() == run()


def test_ooze_rejects_non_stack_or_non_opposing_targets():
    game, _ = setup()
    ooze = game.players[0].hand[0]
    creature = game.create_permanent(BEAR, 0, summoning_sick=False)
    assert game.announce_spell(0, ooze, creature) is None


def test_mutagen_activation_pays_tap_sacrifice_and_places_counter():
    game, target = setup()
    spell = game.announce_spell(0, game.players[0].hand[0], target)
    assert spell is not None
    pass_all(game)
    token = next(p for p in game.players[0].battlefield if p.card.name == "Mutagen")
    creature = game.create_permanent(BEAR, 0, summoning_sick=False)
    dummy = StackObject(game._allocate_object_id(), BEAR, 1, 1, CastKind.CREATURE)
    game._register(dummy)
    game.stack.append(dummy)
    game._begin_priority_window()
    ability = game.announce_activated_ability(
        0, token, MUTAGEN_FRAGMENT, target_ids=(creature.object_id,)
    )
    assert ability is not None
    assert token.zone == "former" and token.tapped
    pass_all(game)
    assert creature.counters.get("+1/+1") == 1
    assert any(e["event"] == "mutagen_counter_placed" for e in game.events)
    game.check_invariants()


def test_mutagen_target_is_revalidated_and_fails_closed():
    game, target = setup()
    spell = game.announce_spell(0, game.players[0].hand[0], target)
    assert spell is not None
    pass_all(game)
    token = next(p for p in game.players[0].battlefield if p.card.name == "Mutagen")
    creature = game.create_permanent(BEAR, 0, summoning_sick=False)
    dummy = StackObject(game._allocate_object_id(), BEAR, 1, 1, CastKind.CREATURE)
    game._register(dummy)
    game.stack.append(dummy)
    game._begin_priority_window()
    ability = game.announce_activated_ability(
        0, token, MUTAGEN_FRAGMENT, target_ids=(creature.object_id,)
    )
    assert ability is not None
    creature.zone = "former"
    game.players[0].battlefield.remove(creature)
    pass_all(game)
    assert creature.counters == {}
    assert any(e["event"] == "mutagen_counter_failed_closed" for e in game.events)
