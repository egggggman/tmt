"""Oracle grammar, targeting, stack, life, and entry-event checks for shared removal."""

from dataclasses import replace

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import CardFact, Game
from tmnt_design_studio.pilot07 import AcceptancePilot
from tmnt_design_studio.stage02 import _authoritative_state_stops, _terminal_outcome_stops

LAND = CardFact("Mountain", "", 0, "Basic Land — Mountain")
FOREST = CardFact("Forest", "", 0, "Basic Land — Forest")
SWAMP = CardFact("Swamp", "", 0, "Basic Land — Swamp")
PIZZA = CardFact(
    "Generic Hot Food",
    "{2}{R}",
    3,
    "Artifact — Food",
    "When this artifact enters, it deals 4 damage to any target and 3 damage to you.\n"
    "{2}, {T}, Sacrifice this artifact: You gain 3 life.",
)
CHAIN = CardFact(
    "Generic Cleanup",
    "{2}{G}",
    3,
    "Sorcery",
    "Destroy up to one target artifact, enchantment, or creature with flying. "
    "Create a Mutagen token. (It's an artifact with \"{1}, {T}, Sacrifice this token: "
    'Put a +1/+1 counter on target creature. Activate only as a sorcery.")',
)
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)
FLIER = replace(BEAR, name="Bird", keywords=("Flying",))
SHROUD = replace(FLIER, name="Veiled Bird", keywords=("Flying", "Shroud"))
ARTIFACT = CardFact("Device", "{1}", 1, "Artifact")
ENCHANTMENT = CardFact("Ward", "{1}", 1, "Enchantment")
INDSTRUCTIBLE = replace(ARTIFACT, name="Shielded Device", keywords=("Indestructible",))
CONDITIONAL = CardFact(
    "Generic Conditional Removal",
    "{1}{B}{G}",
    3,
    "Instant",
    "Destroy target artifact or creature. If its mana value was 4 or less, create a Food token. "
    '(It\'s an artifact with "{2}, {T}, Sacrifice this token: You gain 3 life.")',
)


def setup(*, chooser=None):
    game = Game(([LAND] * 60, [LAND] * 60), seed=289, damage_target_chooser=chooser)
    game.begin_turn()
    for side in (0, 1):
        for land in (LAND, LAND, LAND, FOREST, FOREST, SWAMP):
            game.create_permanent(land, side, summoning_sick=False)
    return game


def options(game, card):
    game.set_hand_for_testing(0, [card])
    return tuple(
        option
        for option in game.legal_main_actions(0)
        if option.object_id == game.players[0].hand[0].object_id
    )


def resolve(game):
    for _ in range(2):
        player = game.priority_state.player_index
        game.execute_priority_action(
            next(o for o in game.legal_priority_actions(player) if o.kind.value == "pass_priority")
        )
    game.process_priority_resolution()


def test_oracle_grammar_and_coverage_are_card_name_independent():
    interpreter = CardInterpreter()
    assert interpreter.cast_program(CHAIN).kind is CastKind.OPTIONAL_DESTROY_AND_CREATE
    assert interpreter.cast_program(PIZZA).kind is CastKind.PERMANENT
    assert interpreter.cast_program(CONDITIONAL).kind is CastKind.CONDITIONAL_DESTROY_AND_CREATE
    assert not interpreter.unsupported_fragments(CONDITIONAL)
    assert interpreter.shared_removal_semantic_coverage(CHAIN, CHAIN.oracle_text).fully_supported
    assert interpreter.shared_removal_semantic_coverage(
        PIZZA, PIZZA.oracle_text.splitlines()[0]
    ).fully_supported
    assert interpreter.token_semantic_coverage(CHAIN, CHAIN.oracle_text).fully_supported
    assert not interpreter.unsupported_fragments(CHAIN)
    assert (
        interpreter.optional_destroy_and_create_program(
            replace(CHAIN, oracle_text=CHAIN.oracle_text.replace("with flying", "without flying"))
        )
        is None
    )


def test_pizza_selects_legal_creature_and_applies_both_damage_instances():
    game = setup(
        chooser=lambda _controller, offered: next(x for x in offered if x.startswith("object-"))
    )
    creature = game.create_permanent(BEAR, 1)
    game.execute_main_action(options(game, PIZZA)[0])
    assert game.priority_state is not None
    assert game.players[0].life == 20 and creature.zone == "battlefield"
    resolve(game)
    assert creature.zone == "former"
    assert game.players[0].life == 17
    assert (
        len([e for e in game.events if e["event"] == "damage_dealt" and e["amount"] in (3, 4)]) == 2
    )
    assert any(
        e["event"] == "entry_damage_resolved" and e["result"] == "resolved" for e in game.events
    )
    game.check_invariants()


def test_pizza_can_target_either_player_and_simultaneous_life_loss_draws():
    game = setup(chooser=lambda controller, _offered: f"player:{1 - controller}")
    game.players[0].life = 3
    game.players[1].life = 4
    game.execute_main_action(options(game, PIZZA)[0])
    resolve(game)
    assert [p.lost for p in game.players] == [True, True]
    assert game.winner is None and game.is_terminal and game.snapshot()["terminal_draw"]
    assert sum(e["event"] == "game_draw" for e in game.events) == 1
    assert game.authoritative_state_fingerprint_evidence()["terminal_draw"]
    assert _authoritative_state_stops(game.snapshot()) == []
    assert _terminal_outcome_stops(game.snapshot()) == []
    game.check_invariants()


def test_pizza_rejects_illegal_choice_without_mutation():
    game = setup(chooser=lambda _controller, _offered: "obj-forged")
    options(game, PIZZA)
    with pytest.raises(ValueError, match="not legal"):
        game.execute_main_action(
            next(o for o in game.legal_main_actions(0) if o.kind.value == "cast")
        )
    assert game.players[0].life == 20


def test_pizza_trigger_survives_source_departure():
    game = setup()
    source = game.create_permanent(PIZZA, 0)
    game._process_creatures_entered_triggers((source,), defer_triggers=True)
    game.destroy(source)
    game._begin_priority_window()
    resolve(game)
    assert source.zone == "former"
    assert game.players[0].life == 17 and game.players[1].life == 16
    assert any(e["event"] == "entry_damage_resolved" for e in game.events)


def test_pizza_invalidated_creature_target_prevents_both_damage_instances():
    game = setup(
        chooser=lambda _controller, offered: next(x for x in offered if x.startswith("object-"))
    )
    target = game.create_permanent(BEAR, 1)
    source = game.create_permanent(PIZZA, 0)
    game._process_creatures_entered_triggers((source,), defer_triggers=True)
    game.destroy(target)
    game._begin_priority_window()
    resolve(game)
    assert (game.players[0].life, game.players[1].life) == (20, 20)
    assert any(
        e["event"] == "entry_damage_resolved" and e["result"] == "all_targets_illegal"
        for e in game.events
    )


@pytest.mark.parametrize("target_fact", [FLIER, ARTIFACT, ENCHANTMENT, INDSTRUCTIBLE])
def test_chain_optional_target_destroys_eligible_permanent_and_creates_token(target_fact):
    game = setup()
    target = game.create_permanent(target_fact, 1)
    chosen = next(o for o in options(game, CHAIN) if o.target_id == target.object_id)
    game.execute_main_action(chosen)
    resolve(game)
    assert (target.zone == "battlefield") == (target_fact is INDSTRUCTIBLE)
    assert [p.card.name for p in game.players[0].battlefield].count("Mutagen") == 1
    assert any(e["event"] == "optional_removal_resolved" for e in game.events)
    game.check_invariants()


def test_chain_can_decline_optional_target_and_nonflying_creature_is_ineligible():
    game = setup()
    bear = game.create_permanent(BEAR, 1)
    selected = options(game, CHAIN)
    assert len(selected) == 1 and selected[0].target_id is None
    game.execute_main_action(selected[0])
    resolve(game)
    assert bear.zone == "battlefield"
    assert any(p.card.name == "Mutagen" for p in game.players[0].battlefield)


def test_chain_fizzles_when_its_only_selected_target_changes_zone():
    game = setup()
    target = game.create_permanent(ARTIFACT, 1)
    game.set_hand_for_testing(0, [CHAIN])
    spell = game.announce_spell(0, game.players[0].hand[0], target)
    assert spell is not None
    game.destroy(target)
    game.resolve_top_of_stack()
    assert not any(p.card.name == "Mutagen" for p in game.players[0].battlefield)
    assert any(e["event"] == "spell_resolved_no_effect" for e in game.events)


@pytest.mark.parametrize(
    "target_fact,food",
    [(ARTIFACT, True), (INDSTRUCTIBLE, True), (replace(BEAR, mana_value=5), False)],
)
def test_conditional_removal_uses_last_known_value_and_legal_target(target_fact, food):
    game = setup()
    target = game.create_permanent(target_fact, 1)
    chosen = next(o for o in options(game, CONDITIONAL) if o.target_id == target.object_id)
    game.execute_main_action(chosen)
    resolve(game)
    event = next(e for e in game.events if e["event"] == "conditional_removal_resolved")
    assert event["last_known_mana_value"] == target_fact.mana_value
    assert len(event["token_ids"]) == int(food)
    assert (target.zone == "battlefield") == (target_fact is INDSTRUCTIBLE)
    game.check_invariants()


def test_conditional_removal_fizzles_without_food_when_target_changes_zone():
    game = setup()
    target = game.create_permanent(ARTIFACT, 1)
    options(game, CONDITIONAL)
    assert game.announce_spell(0, game.players[0].hand[0], target) is not None
    game.destroy(target)
    game.resolve_top_of_stack()
    assert not any(p.card.name == "Food" for p in game.players[0].battlefield)
    assert any(e["event"] == "spell_resolved_no_effect" for e in game.events)


def test_chain_pilot_selects_hostile_target_without_card_name_dispatch():
    game = setup()
    target = game.create_permanent(ARTIFACT, 1)
    options(game, CHAIN)
    choice = AcceptancePilot().choose_main_action(
        game.pilot_view(0), game.legal_main_actions(0), "destroy"
    )
    assert choice.target_id == target.object_id


def test_noncreature_artifact_token_produces_permanent_entry_event():
    game = setup()
    options(game, CHAIN)
    game.execute_main_action(next(o for o in game.legal_main_actions(0) if o.kind.value == "cast"))
    resolve(game)
    token = next(p for p in game.players[0].battlefield if p.card.name == "Mutagen")
    assert any(
        e.kind.value == "permanent_entered" and e.subject_ids == (token.object_id,)
        for e in game._rules_events.values()
    )
    game.check_invariants()


def test_noncreature_artifact_token_delivers_existing_entry_trigger():
    source = CardFact(
        "Counter Source",
        "{1}{G}",
        2,
        "Creature — Turtle",
        "Whenever an artifact you control enters, put a +1/+1 counter on this creature.",
        power=2,
        toughness=2,
    )
    game = setup()
    existing = game.create_permanent(source, 0)
    game.execute_main_action(options(game, CHAIN)[0])
    resolve(game)
    assert existing.counters.get("+1/+1") == 1
    assert any(e["event"] == "trigger_stacked" and e["source"] == source.name for e in game.events)
    game.check_invariants()


def test_replay_of_scoped_effects_is_byte_deterministic():
    def play():
        game = setup()
        target = game.create_permanent(FLIER, 1)
        game.execute_main_action(
            next(o for o in options(game, CHAIN) if o.target_id == target.object_id)
        )
        resolve(game)
        for land in game.players[0].battlefield:
            if land.card.type_line.startswith("Basic Land"):
                land.tapped = False
        game.execute_main_action(options(game, PIZZA)[0])
        resolve(game)
        game.check_invariants()
        return game.snapshot()

    assert play() == play()
