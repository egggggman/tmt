"""Bounded synthetic reproductions for the PR #386 final fidelity gate."""

import pytest

from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, TurnStep
from tmnt_design_studio.pilot07 import AcceptancePilot
from tmnt_design_studio.stage002 import (
    DeckSpec,
    GameSpec,
    _drain_ordinary_step_priority,
    _drain_priority,
    _finish_presence,
    _initial_presence,
    _run_main_action_stages,
    reconcile_snapshot,
    stable_digest,
)

LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
SWAMP = CardFact("Swamp", "", 0, "Basic Land — Swamp")
RATS = CardFact(
    "Tunnel Rats",
    "{1}{B}",
    2,
    "Creature — Rat",
    "{4}{B}: Return this card from your graveyard to the battlefield tapped.",
    power=2,
    toughness=2,
)
FROG = CardFact(
    "Frog Butler",
    "{1}{G}",
    2,
    "Creature — Frog Spirit",
    (
        "Deathtouch\n{T}: Add one mana of any color.\n"
        "{2}: This creature gains reach until end of turn."
    ),
    keywords=("Deathtouch",),
    power=2,
    toughness=2,
)
MANA_FRAGMENT = "{T}: Add one mana of any color."
REACH_FRAGMENT = "{2}: This creature gains reach until end of turn."
FLYER = CardFact(
    "Synthetic Flyer", "{1}{U}", 2, "Creature — Bird", keywords=("Flying",), power=2, toughness=2
)
ATTACKER = CardFact("Synthetic Attacker", "{1}{W}", 2, "Creature — Human", power=2, toughness=2)
BLOCKER = CardFact("Synthetic Blocker", "{1}{W}", 2, "Creature — Human", power=1, toughness=3)
DROID = CardFact(
    "Fugitive Droid",
    "{U}",
    1,
    "Artifact Creature — Robot Scientist",
    "This creature can't be blocked if an artifact entered the battlefield under your "
    "control this turn.",
    power=1,
    toughness=2,
)
ARTIFACT = CardFact("Synthetic Artifact", "{1}", 1, "Artifact")
SPELL = CardFact("Synthetic Spell", "{1}", 1, "Creature — Wizard", power=1, toughness=1)


class PassPriorityPilot:
    def choose_priority(self, _view, options):
        return next(option for option in options if option.kind is ActionKind.PASS_PRIORITY)


class TargetPriorityPilot(PassPriorityPilot):
    def __init__(self, game, source_id, fragment, predicate):
        self.game = game
        self.source_id = source_id
        self.fragment = fragment
        self.predicate = predicate
        self.used = False
        self.epochs = []

    def choose_priority(self, _view, options):
        if not self.used and self.predicate(self.game):
            target = next(
                (
                    option
                    for option in options
                    if option.kind is ActionKind.ACTIVATE_ABILITY
                    and option.object_id == self.source_id
                    and option.oracle_fragment == self.fragment
                ),
                None,
            )
            if target is not None:
                self.used = True
                self.epochs.append(target.priority_epoch)
                return target
        return super().choose_priority(_view, options)


class MultiActivationPriorityPilot(PassPriorityPilot):
    def __init__(self, game, sources):
        self.game = game
        self.sources = sources
        self.used = []
        self.epochs = []

    def choose_priority(self, _view, options):
        state = self.game.priority_state
        if (
            not self.game.stack
            and len(self.used) < len(self.sources)
            and (not self.used or state.epoch > self.epochs[0])
        ):
            source = self.sources[len(self.used)]
            option = next(
                (
                    option
                    for option in options
                    if option.kind is ActionKind.ACTIVATE_ABILITY
                    and option.object_id == source.object_id
                    and option.oracle_fragment == REACH_FRAGMENT
                ),
                None,
            )
            if option is not None:
                self.used.append(source.object_id)
                self.epochs.append(option.priority_epoch)
                return option
        return super().choose_priority(_view, options)


def _report(game, initial_presence):
    snapshot = game.snapshot()
    snapshot["stage002_presence"] = _finish_presence(initial_presence, snapshot["events"])
    fragments = {}
    # Freeze the fixture's static card facts before executing actions. The manifest
    # never learns semantic identity or attribution from runtime execution records.
    for item in initial_presence:
        fragments.setdefault(
            item["semantic_key"],
            {
                "semantic_key": item["semantic_key"],
                "oracle_fragment": item["oracle_fragment"],
                "limitations": [],
            },
        )
    manifest = {
        "manifest_digest": stable_digest(
            sorted(fragments.values(), key=lambda row: row["semantic_key"])
        ),
        "decks": [{"cards": [{"fragments": list(fragments.values())}]}],
    }
    spec = GameSpec(
        "synthetic-final-fidelity",
        "synthetic-final-fidelity",
        game.rng.seed,
        "canonical",
        (
            DeckSpec("synthetic-active", "synthetic-active.txt"),
            DeckSpec("synthetic-opponent", "synthetic-opponent.txt"),
        ),
    )
    report = reconcile_snapshot(spec, snapshot, manifest)
    return snapshot, report


def _assert_rejected_transition_without_mutation(game):
    before = game.authoritative_state_fingerprint()
    events = tuple(game.events)
    step = game.step
    with pytest.raises(ValueError, match="open priority window"):
        game.advance_step()
    assert game.authoritative_state_fingerprint() == before
    assert tuple(game.events) == events
    assert game.step is step


def test_transition_rejects_open_empty_priority_window_before_passes():
    game = Game(([LAND] * 12, [LAND] * 12), seed=3861)
    game.begin_turn()
    game._begin_priority_window(allow_empty=True)
    assert game.priority_state.consecutive_passes == ()
    game.check_invariants()
    _assert_rejected_transition_without_mutation(game)


def test_transition_rejects_open_empty_priority_window_after_one_pass():
    game = Game(([LAND] * 12, [LAND] * 12), seed=3862)
    game.begin_turn()
    game._begin_priority_window(allow_empty=True)
    option = next(
        option
        for option in game.legal_priority_actions(0)
        if option.kind is ActionKind.PASS_PRIORITY
    )
    game.execute_priority_action(option)
    assert game.priority_state.consecutive_passes == (0,)
    game.check_invariants()
    _assert_rejected_transition_without_mutation(game)


def test_transition_rejects_two_passes_until_empty_window_closure_is_processed():
    game = Game(([LAND] * 12, [LAND] * 12), seed=3863)
    game.begin_turn()
    game._begin_priority_window(allow_empty=True)
    for _ in range(2):
        state = game.priority_state
        option = next(
            option
            for option in game.legal_priority_actions(state.player_index)
            if option.kind is ActionKind.PASS_PRIORITY
        )
        game.execute_priority_action(option)
    assert game.priority_state.resolution_pending
    game.check_invariants()
    _assert_rejected_transition_without_mutation(game)
    game.process_priority_resolution()
    assert game.priority_state is None
    game.advance_step()
    assert game.step is TurnStep.BEGINNING_OF_COMBAT


def test_priority_action_from_closed_epoch_is_rejected_without_mutation():
    game = Game(([LAND] * 12, [LAND] * 12), seed=3875)
    game.begin_turn()
    game._begin_priority_window(allow_empty=True)
    stale = next(
        option
        for option in game.legal_priority_actions(0)
        if option.kind is ActionKind.PASS_PRIORITY
    )
    for _ in range(2):
        state = game.priority_state
        option = next(
            option
            for option in game.legal_priority_actions(state.player_index)
            if option.kind is ActionKind.PASS_PRIORITY
        )
        game.execute_priority_action(option)
    game.process_priority_resolution()
    game._begin_priority_window(allow_empty=True)
    assert game.priority_state.epoch > stale.priority_epoch
    before = game.authoritative_state_fingerprint()
    events = tuple(game.events)
    with pytest.raises(ValueError, match="not currently legal"):
        game.execute_priority_action(stale)
    assert game.authoritative_state_fingerprint() == before
    assert tuple(game.events) == events


def test_stack_resolution_and_legacy_combat_transitions_remain_valid():
    game = Game(([LAND] * 12, [LAND] * 12), seed=3864)
    game.begin_turn()
    for _ in range(2):
        game.create_permanent(LAND, 0, summoning_sick=False)
    game.create_permanent(FROG, 0, summoning_sick=False)
    reach_option = next(
        option
        for option in game.legal_main_actions(0)
        if option.kind is ActionKind.ACTIVATE_ABILITY and option.oracle_fragment == REACH_FRAGMENT
    )
    assert game.execute_main_action(reach_option)
    for _ in range(2):
        state = game.priority_state
        option = next(
            option
            for option in game.legal_priority_actions(state.player_index)
            if option.kind is ActionKind.PASS_PRIORITY
        )
        game.execute_priority_action(option)
    with pytest.raises(ValueError, match="unresolved stack"):
        game.advance_step()
    game.process_priority_resolution()
    assert game.priority_state is None and game.stack == []
    game.advance_step()
    assert game.step is TurnStep.BEGINNING_OF_COMBAT

    legacy = Game(([LAND] * 12, [LAND] * 12), seed=3865)
    legacy.begin_turn()
    attacker = legacy.create_permanent(ATTACKER, 0, summoning_sick=False)
    legacy.create_permanent(BLOCKER, 1, summoning_sick=False)
    legacy.advance_step()
    legacy.advance_step()
    legacy.combat([attacker], blocks={})
    assert legacy.step is TurnStep.END_OF_COMBAT
    assert legacy.priority_state is None


def test_natural_tunnel_rats_execution_authenticates_through_reconciler():
    game = Game(([SWAMP, LAND, LAND, LAND, LAND] * 4, [LAND] * 20), seed=3866)
    game.begin_turn()
    for card in (SWAMP, LAND, LAND, LAND, LAND):
        game.create_permanent(card, 0, summoning_sick=False)
    source = game._create_card_object(RATS, 0, "graveyard")
    game.players[0].graveyard.append(source)
    initial = _initial_presence(game)
    while game.step is not TurnStep.END_STEP:
        if game.step is TurnStep.COMBAT_DAMAGE:
            game.resolve_combat_damage()
        game.advance_step()
    pilot = TargetPriorityPilot(
        game,
        source.object_id,
        RATS.oracle_text,
        lambda current: current.step is TurnStep.END_STEP,
    )
    _drain_ordinary_step_priority(game, pilot)
    snapshot, report = _report(game, initial)
    reference = next(
        item
        for item in report["authenticated_executed_references"]
        if item["evidence_kind"] == "activated_ability" and item["source_id"] == source.object_id
    )
    assert pilot.used and game.step is TurnStep.END_STEP
    assert reference["oracle_fragment"] == RATS.oracle_text
    assert (
        source.object_id
        in next(item for item in snapshot["stage002_presence"] if item["card"] == RATS.name)[
            "object_ids"
        ]
    )
    assert not report["stop_records"]
    assert len([event for event in game.events if event["event"] == "tunnel_rats_returned"]) == 1


def test_frog_mana_action_produces_pays_and_expires_with_authenticated_lineage():
    game = Game(([LAND] * 20, [LAND] * 20), seed=3867)
    game.begin_turn()
    frogs = [game.create_permanent(FROG, 0, summoning_sick=False) for _ in range(2)]
    game.create_permanent(LAND, 0, summoning_sick=False)
    for frog, color in zip(frogs, ("U", "G"), strict=True):
        option = next(
            option
            for option in game.legal_main_actions(0)
            if option.object_id == frog.object_id
            and option.oracle_fragment == MANA_FRAGMENT
            and option.choice_ids == (color,)
        )
        assert game.execute_main_action(option)
    blue = next(item for item in game.floating_mana.productions(0) if item.color == "U")
    spell_card = CardFact(
        "Blue Synthetic Spell", "{U}", 1, "Creature — Wizard", power=1, toughness=1
    )
    spell_source = game.set_hand_for_testing(0, [spell_card])[0]
    initial = _initial_presence(game)
    spell_option = next(
        option for option in game.legal_main_actions(0) if option.kind is ActionKind.CAST
    )
    assert game.execute_main_action(spell_option)
    spell_id = next(
        event["stack_object_id"]
        for event in game.events
        if event["event"] == "spell_cast" and event["card"] == spell_card.name
    )
    consumption = next(item for item in game.floating_mana.consumptions(0) if item.color == "U")
    assert consumption.source_event_id == blue.event_id
    assert consumption.payment_id == spell_source.object_id
    assert any(
        event["event"] == "zone_changed"
        and event["source_object_id"] == spell_source.object_id
        and event["destination_object_id"] == spell_id
        for event in game.events
    )
    assert game.floating_mana.snapshot(0) == {"G": 1}
    game.advance_step()
    assert game.floating_mana.snapshot(0) == {}
    assert any(
        event["event"] == "mana_pool_emptied" and event["mana"] == {"G": 1} for event in game.events
    )
    snapshot, report = _report(game, initial)
    expected_sources = {frog.object_id for frog in frogs}
    authenticated = [
        item
        for item in report["authenticated_executed_references"]
        if item["oracle_fragment"] == MANA_FRAGMENT
    ]
    assert {item["source_id"] for item in authenticated} == expected_sources
    assert all(
        item["resolved"]
        for item in snapshot["activated_abilities"]
        if item["oracle_fragment"] == MANA_FRAGMENT
    )
    assert not report["stop_records"]


def test_frog_mana_ability_is_an_immediate_priority_action_with_color_choice():
    game = Game(([LAND] * 12, [LAND] * 12), seed=3874)
    game.begin_turn()
    frog = game.create_permanent(FROG, 0, summoning_sick=False)
    initial = _initial_presence(game)
    game._begin_priority_window(allow_empty=True)
    epoch = game.priority_state.epoch
    option = next(
        option
        for option in game.legal_priority_actions(0)
        if option.kind is ActionKind.ACTIVATE_ABILITY
        and option.object_id == frog.object_id
        and option.oracle_fragment == MANA_FRAGMENT
        and option.choice_ids == ("R",)
    )
    assert game.execute_priority_action(option)
    assert game.priority_state.epoch == epoch
    assert game.stack == [] and game.floating_mana.snapshot(0) == {"R": 1}
    snapshot, report = _report(game, initial)
    assert any(
        item["source_id"] == frog.object_id and item["oracle_fragment"] == MANA_FRAGMENT
        for item in report["authenticated_executed_references"]
    )
    assert snapshot["activated_abilities"][0]["resolved"]
    assert not report["stop_records"]


def test_defender_reach_execution_authenticates_before_block_declaration():
    game = Game(([LAND] * 20, [LAND] * 20), seed=3868)
    game.begin_turn()
    attacker = game.create_permanent(FLYER, 0, summoning_sick=False)
    frog = game.create_permanent(FROG, 1, summoning_sick=True)
    for _ in range(2):
        game.create_permanent(LAND, 1, summoning_sick=False)
    initial = _initial_presence(game)
    game.advance_step()
    _drain_ordinary_step_priority(game, PassPriorityPilot())
    game.advance_step()
    attack = next(
        option
        for option in game.legal_attack_options(0)
        if option.attacker_ids == (attacker.object_id,)
    )
    game.execute_attack_action(attack, defer_step_transition=True)
    pilot = TargetPriorityPilot(
        game,
        frog.object_id,
        REACH_FRAGMENT,
        lambda current: (
            current.step is TurnStep.DECLARE_ATTACKERS and current.players[1].life == 20
        ),
    )
    _drain_ordinary_step_priority(game, pilot)
    assert pilot.used and game.step is TurnStep.DECLARE_ATTACKERS
    game.advance_step()
    assert game.step is TurnStep.DECLARE_BLOCKERS
    assert any(
        (attacker.object_id, frog.object_id) in option.blocks
        for option in game.legal_block_options(attack, 1)
    )
    snapshot, report = _report(game, initial)
    assert any(
        item["source_id"] == frog.object_id and item["oracle_fragment"] == REACH_FRAGMENT
        for item in report["authenticated_executed_references"]
    )
    assert not report["stop_records"]
    assert snapshot["priority"] is None


def test_fugitive_droid_controller_specific_entry_restriction_survives_reconcile():
    game = Game(([LAND] * 20, [LAND] * 20), seed=3869)
    game.begin_turn()
    droid = game.create_permanent(DROID, 0, summoning_sick=False)
    blocker = game.create_permanent(BLOCKER, 1, summoning_sick=False)
    artifact = game.create_permanent(ARTIFACT, 0, summoning_sick=False)
    game.move_object(artifact, "graveyard", reason="synthetic_artifact_departure")
    opponent_artifact = game.create_permanent(ARTIFACT, 1, summoning_sick=False)
    game.change_controller(opponent_artifact, 0)
    initial = _initial_presence(game)
    game.advance_step()
    _drain_ordinary_step_priority(game, PassPriorityPilot())
    game.advance_step()
    attack = next(
        option
        for option in game.legal_attack_options(0)
        if option.attacker_ids == (droid.object_id,)
    )
    game.execute_attack_action(attack, defer_step_transition=True)
    _drain_ordinary_step_priority(game, PassPriorityPilot())
    game.advance_step()
    assert game.blocking_restriction(droid, blocker) is not None
    assert not any(
        (droid.object_id, blocker.object_id) in option.blocks
        for option in game.legal_block_options(attack, 1)
    )
    _snapshot, report = _report(game, initial)
    assert report["authenticated_executed_references"] == []
    assert not report["stop_records"]


def test_follow_on_empty_priority_after_resolution_can_execute_reach():
    game = Game(([LAND] * 20, [LAND] * 20), seed=3870)
    game.begin_turn()
    for _ in range(4):
        game.create_permanent(LAND, 0, summoning_sick=False)
    frogs = [game.create_permanent(FROG, 0, summoning_sick=False) for _ in range(2)]
    initial = _initial_presence(game)
    game._begin_priority_window(allow_empty=True)
    pilot = MultiActivationPriorityPilot(game, frogs)
    _drain_priority(game, pilot, follow_on_empty_window=True)
    assert pilot.used == [frog.object_id for frog in frogs]
    assert pilot.epochs[1] > pilot.epochs[0]
    assert any(
        event["event"] == "response_window_opened"
        and event["stack_object_id"] is None
        and event["priority_epoch"] > pilot.epochs[0]
        for event in game.events
    )
    _snapshot, report = _report(game, initial)
    assert {
        item["source_id"]
        for item in report["authenticated_executed_references"]
        if item["oracle_fragment"] == REACH_FRAGMENT
    } == {frog.object_id for frog in frogs}
    assert not report["stop_records"]


def test_existing_main_action_policy_runs_during_postcombat_main():
    game = Game(([LAND] * 20, [LAND] * 20), seed=3871)
    game.begin_turn()
    for _ in range(2):
        game.create_permanent(LAND, 0, summoning_sick=False)
    game.set_hand_for_testing(0, [SPELL])
    game._step = TurnStep.END_OF_COMBAT
    game.advance_step()
    assert game.step is TurnStep.POSTCOMBAT_MAIN
    assert any(option.kind is ActionKind.CAST for option in game.legal_main_actions(0))

    _run_main_action_stages(game, AcceptancePilot())

    assert any(permanent.card.name == SPELL.name for permanent in game.players[0].battlefield)
    assert game.winner is None


def test_full_combat_priority_and_sneak_sequence_uses_fresh_epochs():
    game = Game(([LAND] * 20, [LAND] * 20), seed=3872)
    game.begin_turn()
    attacker = game.create_permanent(ATTACKER, 0, summoning_sick=False)
    blocker = game.create_permanent(BLOCKER, 1, summoning_sick=False)
    pilot = PassPriorityPilot()
    expected_steps = [
        TurnStep.BEGINNING_OF_COMBAT,
        TurnStep.DECLARE_ATTACKERS,
        TurnStep.DECLARE_BLOCKERS,
        TurnStep.COMBAT_DAMAGE,
        TurnStep.END_OF_COMBAT,
        TurnStep.POSTCOMBAT_MAIN,
        TurnStep.END_STEP,
    ]
    observed = []

    game.advance_step()
    _drain_ordinary_step_priority(game, pilot)
    observed.append(game.step)
    game.advance_step()
    attack = next(
        option
        for option in game.legal_attack_options(0)
        if option.attacker_ids == (attacker.object_id,)
    )
    game.execute_attack_action(attack, defer_step_transition=True)
    _drain_ordinary_step_priority(game, pilot)
    observed.append(game.step)
    game.advance_step()
    block = next(
        option
        for option in game.legal_block_options(attack, 1)
        if (attacker.object_id, blocker.object_id) in option.blocks
    )
    game.execute_block_action(block, defer_step_transition=True)
    sneak_pass = next(
        option for option in game.legal_sneak_actions(0) if option.kind is ActionKind.PASS
    )
    assert game.execute_sneak_action(sneak_pass, defer_step_transition=True)
    _drain_ordinary_step_priority(game, pilot)
    observed.append(game.step)
    game.advance_step()
    assert game.step is TurnStep.COMBAT_DAMAGE
    observed.append(game.step)
    game.resolve_combat_damage()
    observed.append(game.step)
    _drain_ordinary_step_priority(game, pilot)
    game.advance_step()
    observed.append(game.step)
    _drain_ordinary_step_priority(game, pilot)
    game.advance_step()
    observed.append(game.step)
    _drain_ordinary_step_priority(game, pilot)

    assert observed == expected_steps
    epochs = {}
    for event in game.events:
        if event["event"] == "priority_passed":
            epochs.setdefault(event["priority_epoch"], []).append(event["player_index"])
    assert all(passes == [0, 1] for passes in epochs.values())
    assert len(epochs) >= len(expected_steps) - 1
    assert game.priority_state is None and game.stack == [] and game.winner is None
    game.check_invariants()


def test_priority_driver_stops_prompting_after_winner():
    game = Game(([LAND] * 8, [LAND] * 8), seed=3873)
    game.begin_turn()
    game.players[1].life = 0
    game.check_state_based_actions()
    assert game.winner == 0
    openings = sum(event["event"] == "response_window_opened" for event in game.events)
    _drain_ordinary_step_priority(game, PassPriorityPilot())
    assert sum(event["event"] == "response_window_opened" for event in game.events) == openings
    assert game.priority_state is None
