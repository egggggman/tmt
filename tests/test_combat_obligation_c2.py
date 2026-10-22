"""C2 coverage for generic attack/block sacrifice-or-discard obligations."""

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, TriggerEffect

LAND = CardFact("Forest", "", 0, "Basic Land — Forest")
OBLIGATION = CardFact(
    "Generic Combat Obligation",
    "{2}{B}",
    3,
    "Creature — Mutant",
    "Whenever Generic Combat Obligation attack or block, sacrifice a permanent unless you "
    "discard a card.",
    power=3,
    toughness=3,
)
BEAR = CardFact("Bear", "{1}", 1, "Creature — Bear", power=2, toughness=2)


def resolve_all(game: Game) -> None:
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def fixture(*, chooser=None):
    game = Game(([LAND] * 20, [LAND] * 20), seed=44001, combat_obligation_chooser=chooser)
    game.begin_turn()
    source = game.create_permanent(OBLIGATION, 0, summoning_sick=False)
    permanent = game.create_permanent(BEAR, 0, summoning_sick=False)
    card = game._create_card_object(BEAR, 0, "hand")
    game.players[0].hand.append(card)
    return game, source, permanent, card


def test_interpreter_supports_exact_attack_or_block_clause_generically():
    assert CardInterpreter().unsupported_fragments(OBLIGATION) == ()


def test_attack_obligation_can_discard_and_leaves_permanent_intact():
    game, source, permanent, card = fixture(
        chooser=lambda _controller, _source, _sacrifices, discards: ("discard", discards[-1])
    )
    game.resolve_attack_pt_effects([source])
    assert game.stack[-1].effect is TriggerEffect.COMBAT_SACRIFICE_OR_DISCARD
    resolve_all(game)
    assert all(item.card is not card.card for item in game.players[0].hand)
    assert any(item.object_id == permanent.object_id for item in game.players[0].battlefield)
    assert any(
        event.get("event") == "combat_obligation_resolved" and event.get("action") == "discard"
        for event in game.events
    )


def test_attack_obligation_can_sacrifice_when_chosen():
    game, source, permanent, card = fixture(
        chooser=lambda _controller, _source, sacrifices, _discards: ("sacrifice", sacrifices[-1])
    )
    game.resolve_attack_pt_effects([source])
    resolve_all(game)
    assert permanent.object_id not in {item.object_id for item in game.players[0].battlefield}
    assert any(item.card is permanent.card for item in game.players[0].graveyard)
    assert any(item.card is card.card for item in game.players[0].hand)


def test_block_obligation_is_delivered_and_no_option_is_terminal():
    game = Game(([LAND] * 20, []), seed=44002)
    game.begin_turn()
    game.create_permanent(BEAR, 0, summoning_sick=False)
    blocker = game.create_permanent(OBLIGATION, 1, summoning_sick=False)
    game.resolve_block_pt_effects([blocker])
    game.move_object(blocker, "graveyard", reason="c2_no_option_departure")
    resolve_all(game)
    assert any(event.get("event") == "combat_obligation_no_option" for event in game.events)
    assert any(item.card is blocker.card for item in game.players[1].graveyard)


def test_obligation_source_may_leave_before_resolution_but_forged_event_fails():
    game, source, _permanent, _card = fixture()
    game.resolve_attack_pt_effects([source])
    game.move_object(source, "graveyard", reason="c2_source_departure")
    resolve_all(game)
    assert any(event.get("event") == "combat_obligation_resolved" for event in game.events)

    trigger = next(
        item
        for item in game._triggers.values()
        if item.effect is TriggerEffect.COMBAT_SACRIFICE_OR_DISCARD
    )
    with pytest.raises(ValueError, match="rules event"):
        from dataclasses import replace

        game._authenticate_original_rules_event(replace(trigger.event, event_id="forged"))


def test_obligation_chooser_rejects_illegal_object():
    game, source, _permanent, _card = fixture(
        chooser=lambda _controller, _source, _sacrifices, _discards: ("discard", "forged")
    )
    game.resolve_attack_pt_effects([source])
    with pytest.raises(ValueError, match="discard choice is illegal"):
        resolve_all(game)


def test_multiple_attackers_create_independent_obligations_and_keep_original_controller():
    chosen = []

    def choose(controller, source_id, sacrifices, discards):
        chosen.append((controller, source_id))
        return ("discard", discards[-1])

    game = Game(([LAND] * 20, [LAND] * 20), seed=44003, combat_obligation_chooser=choose)
    game.begin_turn()
    first = game.create_permanent(OBLIGATION, 0, summoning_sick=False)
    second = game.create_permanent(OBLIGATION, 0, summoning_sick=False)
    game.resolve_attack_pt_effects([first, second])
    resolve_all(game)
    assert len(chosen) == 2
    assert {source_id for _controller, source_id in chosen} == {first.object_id, second.object_id}


def test_control_change_does_not_reassign_already_created_obligation():
    seen = []

    def choose(controller, source_id, sacrifices, discards):
        seen.append(controller)
        return ("discard", discards[-1])

    game, source, _permanent, _card = fixture(chooser=choose)
    game.resolve_attack_pt_effects([source])
    game.change_controller(source, 1)
    resolve_all(game)
    assert seen == [0]
