"""Synthetic regressions for state-informed pilot choices and restricted-mana follow-ups."""

from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    CardFact,
    Game,
    StrikeKeyword,
    TriggeredAbilityObject,
    TriggerEffect,
)
from tmnt_design_studio.pilot07 import AcceptancePilot
from tmnt_design_studio.stage002 import (
    _matching_main_followup,
    _run_main_action_stages,
    _wire_damage_target_chooser,
)

LAND = CardFact("Forest", "", 0, "Basic Land — Forest")
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature — Bear", "", 2, 2)
PIZZA = CardFact(
    "Synthetic Damage Artifact",
    "{R}",
    1,
    "Artifact",
    "When this artifact enters, it deals 4 damage to any target and 3 damage to you.",
)
ARTIFACT_CREATURE = CardFact(
    "Synthetic Artifact Creature", "{R}", 1, "Artifact Creature — Test", "", 1, 1
)
RED_CREATURE = CardFact("Synthetic Red Creature", "{R}", 1, "Creature — Test", "", 1, 1)
RESTRICTED_ABILITY_CREATURE = CardFact(
    "Synthetic Restricted Ability Creature",
    "",
    0,
    "Creature — Test",
    "{R}: Synthetic Restricted Ability Creature gains first strike until end of turn.",
    2,
    2,
)
PUNKS = CardFact(
    "Purple Dragon Punks",
    "{2}{R}",
    3,
    "Creature — Mutant",
    "{T}: Add {R}. Spend this mana only to cast an artifact spell or to activate an ability.",
    3,
    3,
    oracle_id="d1edb950-a118-4b4d-a0ef-9a6683d74c9f",
)
FROG = CardFact(
    "Frog Butler",
    "{1}{G}",
    2,
    "Creature — Frog Spirit",
    "{T}: Add one mana of any color.\n{2}: This creature gains reach until end of turn.",
    2,
    2,
)
FROG_REACH = "{2}: This creature gains reach until end of turn."
FROG_MANA = "{T}: Add one mana of any color."
PUNKS_MANA = (
    "{T}: Add {R}. Spend this mana only to cast an artifact spell or to activate an ability."
)


def make_game():
    game = Game(([LAND] * 20, [LAND] * 20), seed=39601)
    game.begin_turn()
    return game


def test_pizza_pilot_chooses_only_an_engine_offered_lethal_target():
    game = make_game()
    game.players[0].life = 12
    game.players[1].life = 4
    offered = ("player:0", "player:1")

    selected = AcceptancePilot.choose_damage_target(game.pilot_view(0), offered)

    assert selected == "player:1"
    assert selected in offered


def test_pizza_pilot_prefers_a_win_to_a_creature_target():
    game = make_game()
    game.players[0].life = 10
    game.players[1].life = 4
    creature = game.create_permanent(BEAR, 1, summoning_sick=False)
    offered = (creature.object_id, "player:1")

    assert AcceptancePilot.choose_damage_target(game.pilot_view(0), offered) == "player:1"


def test_pizza_pilot_prefers_a_draw_to_a_loss_from_mandatory_self_damage():
    game = make_game()
    game.players[0].life = 3
    game.players[1].life = 4
    creature = game.create_permanent(BEAR, 1, summoning_sick=False)
    offered = (creature.object_id, "player:1")

    assert AcceptancePilot.choose_damage_target(game.pilot_view(0), offered) == "player:1"


def test_pizza_pilot_removes_a_lethal_opposing_creature_before_nonlethal_player_damage():
    game = make_game()
    game.players[0].life = 12
    game.players[1].life = 20
    creature = game.create_permanent(BEAR, 1, summoning_sick=False)
    offered = ("player:1", creature.object_id)

    assert AcceptancePilot.choose_damage_target(game.pilot_view(0), offered) == creature.object_id


def test_pizza_pilot_returns_none_when_engine_offers_no_targets():
    game = make_game()

    assert AcceptancePilot.choose_damage_target(game.pilot_view(0), ()) is None


def test_stage_runner_wires_pizza_selection_through_engine_offered_targets():
    game = make_game()
    game.players[0].life = 12
    game.players[1].life = 4
    _wire_damage_target_chooser(game, AcceptancePilot())
    source = game.create_permanent(PIZZA, 0, summoning_sick=False)

    game._process_creature_entered_triggers(source)

    trigger = next(
        item
        for item in game.stack
        if isinstance(item, TriggeredAbilityObject) and item.effect is TriggerEffect.DEAL_DAMAGE
    )
    assert trigger.target_player == 1


def test_punks_is_selected_only_when_pure_hypothetical_payment_enables_artifact_cast():
    game = make_game()
    source = game.create_permanent(PUNKS, 0, summoning_sick=False)
    card = game.set_hand_for_testing(0, [ARTIFACT_CREATURE])[0]
    pilot = AcceptancePilot()
    before = game.snapshot()
    options = game.legal_main_actions(0)
    punk_action = next(item for item in options if item.object_id == source.object_id)

    assert punk_action.mana_followups == (f"cast:{card.object_id}",)
    assert game.legal_main_actions(0) == options
    assert pilot.choose_main_action(game.pilot_view(0), options, "activate") == punk_action
    assert game.snapshot() == before
    assert game.floating_mana.snapshot(0, "artifact_spell") == {}


def test_punks_activation_makes_artifact_cast_available_for_reconsidered_main_actions():
    game = make_game()
    source = game.create_permanent(PUNKS, 0, summoning_sick=False)
    card = game.set_hand_for_testing(0, [ARTIFACT_CREATURE])[0]
    pilot = AcceptancePilot()
    action = next(
        item
        for item in game.legal_main_actions(0)
        if item.object_id == source.object_id and item.mana_followups
    )

    assert game.execute_main_action(action)
    refreshed = game.legal_main_actions(0)
    cast = next(item for item in refreshed if item.kind is ActionKind.CAST)
    assert cast.object_id == card.object_id
    assert pilot.choose_main_action(game.pilot_view(0), refreshed, "creature") == cast


def test_main_action_driver_rechecks_after_useful_punks_mana_activation():
    game = make_game()
    source = game.create_permanent(PUNKS, 0, summoning_sick=False)
    game.set_hand_for_testing(0, [ARTIFACT_CREATURE])

    _run_main_action_stages(game, AcceptancePilot())

    assert source.tapped
    assert any(permanent.card == ARTIFACT_CREATURE for permanent in game.players[0].battlefield)


def test_main_action_driver_prefers_advertised_activated_ability_followup():
    game = make_game()
    punks = game.create_permanent(PUNKS, 0, summoning_sick=False)
    ability_source = game.create_permanent(RESTRICTED_ABILITY_CREATURE, 0, summoning_sick=False)
    options = game.legal_main_actions(0)
    punks_option = next(item for item in options if item.object_id == punks.object_id)
    assert punks_option.mana_followups == (
        f"activate:{ability_source.object_id}:{RESTRICTED_ABILITY_CREATURE.oracle_text}",
    )

    _run_main_action_stages(game, AcceptancePilot())

    activation = next(
        event
        for event in game.events
        if event.get("event") == "activation_announced"
        and event.get("source_id") == ability_source.object_id
    )
    production = next(
        event
        for event in game.events
        if event.get("event") == "floating_mana_produced"
        and event.get("source_id") == punks.object_id
    )
    allocation = next(
        item
        for item in game.floating_mana.consumptions(0)
        if item.payment_id == activation["stack_object_id"]
    )
    assert allocation.source_event_id == production["stack_object_id"]
    assert allocation.spending_context.value == "activated_ability"
    assert StrikeKeyword.FIRST_STRIKE in game.evaluated_strike_keywords(ability_source)


def test_unavailable_advertised_followup_is_ignored_in_favor_of_current_options():
    current = ActionOption(ActionKind.ACTIVATE_ABILITY, 0, "live", oracle_fragment="{R}: Live.")
    unrelated = ActionOption(ActionKind.PASS, 0)

    assert (
        _matching_main_followup(
            (current, unrelated),
            ("cast:stale-card", "activate:live:{R}: Live."),
        )
        == current
    )
    assert _matching_main_followup((unrelated,), ("cast:stale-card",)) is None


def test_main_action_followup_rechecks_stop_after_three_mana_activations():
    class RepeatingManaGame:
        active_player = 0
        terminal = False
        priority_state = None

        def __init__(self):
            self.enumerations = 0
            self.executions = 0
            self.mana_executions = 0

        def legal_main_actions(self, _player):
            self.enumerations += 1
            if 2 <= self.enumerations <= 4:
                return (
                    ActionOption(
                        ActionKind.ACTIVATE_ABILITY,
                        0,
                        "mana-source",
                        mana_followups=("cast:no-longer-available",),
                    ),
                    ActionOption(ActionKind.PASS, 0),
                )
            return (ActionOption(ActionKind.PASS, 0),)

        def authoritative_state_fingerprint(self):
            return str(self.executions)

        def pilot_view(self, _player):
            return None

        def execute_main_action(self, option):
            self.executions += 1
            if option.kind is ActionKind.ACTIVATE_ABILITY:
                self.mana_executions += 1
            return True

    class RepeatingManaPilot:
        def choose_main_action(self, _view, options, _stage):
            return next(
                (item for item in options if item.kind is ActionKind.ACTIVATE_ABILITY),
                next(item for item in options if item.kind is ActionKind.PASS),
            )

    game = RepeatingManaGame()
    _run_main_action_stages(game, RepeatingManaPilot())

    assert game.mana_executions == 3


def test_punks_is_not_activated_for_a_nonartifact_spell_without_an_ability_followup():
    game = make_game()
    source = game.create_permanent(PUNKS, 0, summoning_sick=False)
    game.set_hand_for_testing(0, [RED_CREATURE])
    options = game.legal_main_actions(0)
    punk_action = next(item for item in options if item.object_id == source.object_id)

    assert punk_action.mana_followups == ()
    assert (
        AcceptancePilot().choose_main_action(game.pilot_view(0), options, "activate").kind
        is ActionKind.PASS
    )


def test_unrestricted_frog_mana_choice_remains_available_to_the_pilot():
    game = make_game()
    frog = game.create_permanent(FROG, 0, summoning_sick=False)
    options = game.legal_main_actions(0)
    mana_action = next(
        item
        for item in options
        if item.object_id == frog.object_id and item.oracle_fragment == FROG_MANA
    )

    assert not mana_action.restricted_mana_ability
    assert (
        AcceptancePilot().choose_main_action(game.pilot_view(0), options, "activate") == mana_action
    )


def test_punks_priority_hint_enables_and_reselects_frog_reach_activation():
    game = make_game()
    source = game.create_permanent(PUNKS, 0, summoning_sick=False)
    game.create_permanent(LAND, 0, summoning_sick=False)
    frog = game.create_permanent(FROG, 0, summoning_sick=False)
    game.advance_step()
    game.advance_step()
    game._attackers_declared = True
    game._begin_priority_window(allow_empty=True)
    pilot = AcceptancePilot()
    before = game.snapshot()
    options = game.legal_priority_actions(0)
    punk_action = next(item for item in options if item.object_id == source.object_id)

    assert punk_action.mana_followups == (f"activate:{frog.object_id}:{FROG_REACH}",)
    assert game.legal_priority_actions(0) == options
    assert game.snapshot() == before
    assert pilot.choose_priority(game.priority_view(0), options) == punk_action
    assert game.execute_priority_action(punk_action)

    refreshed = game.legal_priority_actions(game.priority_state.player_index)
    reach_action = next(
        item
        for item in refreshed
        if item.object_id == frog.object_id and item.oracle_fragment == FROG_REACH
    )
    assert reach_action.uses_restricted_mana
    assert pilot.choose_priority(game.priority_view(0), refreshed) == reach_action
    assert game.execute_priority_action(reach_action)
