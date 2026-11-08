"""Independent challenge cases for PR #401's follow-up stage handoff."""

from tmnt_design_studio.engine07 import ActionKind, CardFact, Game
from tmnt_design_studio.pilot07 import AcceptancePilot
from tmnt_design_studio.stage002 import _run_main_action_stages

LAND = CardFact("Forest", "", 0, "Basic Land — Forest")
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
TARGETED_ARTIFACT = CardFact(
    "Manhole Missile",
    "{R}",
    1,
    "Artifact Instant",
    "Manhole Missile deals 3 damage to target creature.",
)
LARGE_CREATURE = CardFact("Large Test Target", "", 0, "Creature — Test", "", 5, 5)
SMALL_CREATURE = CardFact("Small Test Target", "", 0, "Creature — Test", "", 1, 1)
RESTRICTED_ABILITY = CardFact(
    "Synthetic Ability Source",
    "",
    0,
    "Creature — Test",
    "{R}: Synthetic Ability Source gains first strike until end of turn.",
    2,
    2,
)


def make_game(seed):
    game = Game(([LAND] * 10, [LAND] * 10), seed=seed)
    game.begin_turn()
    punks = game.create_permanent(PUNKS, 0, summoning_sick=False)
    large = game.create_permanent(LARGE_CREATURE, 1, summoning_sick=False)
    small = game.create_permanent(SMALL_CREATURE, 1, summoning_sick=False)
    spell = game.set_hand_for_testing(0, [TARGETED_ARTIFACT])[0]
    ability_source = game.create_permanent(RESTRICTED_ABILITY, 0, summoning_sick=False)
    return game, punks, large, small, spell, ability_source


def test_followup_defers_after_pass_and_selects_same_spell_at_later_cast_stage():
    game, punks, large, small, spell, ability_source = make_game(40101)
    initial = game.legal_main_actions(0)
    punks_action = next(option for option in initial if option.object_id == punks.object_id)
    assert f"cast:{spell.object_id}" in punks_action.mana_followups
    assert any(
        value.startswith(f"activate:{ability_source.object_id}:")
        for value in punks_action.mana_followups
    )

    class DeferringPilot(AcceptancePilot):
        def __init__(self):
            self.decisions = []
            self.selected_target = None

        def choose_main_action(self, view, options, stage):
            self.decisions.append((stage, options))
            if stage == "damage":
                assert all(
                    item.kind is ActionKind.PASS
                    or (item.kind is ActionKind.CAST and item.object_id == spell.object_id)
                    for item in options
                )
                return next(item for item in options if item.kind is ActionKind.PASS)
            if stage == "destroy":
                matching = [
                    item
                    for item in options
                    if item.kind is ActionKind.CAST and item.object_id == spell.object_id
                ]
                assert len(matching) == 2
                self.selected_target = small.object_id
                return next(item for item in matching if item.target_id == small.object_id)
            return super().choose_main_action(view, options, stage)

    pilot = DeferringPilot()
    _run_main_action_stages(game, pilot)

    assert [stage for stage, _options in pilot.decisions] == [
        "land",
        "activate",
        "damage",
        "destroy",
        "creature",
    ]
    assert pilot.selected_target == small.object_id
    assert small.zone == "former"
    assert large.damage == 0
    assert not any(
        event.get("event") == "activation_announced"
        and event.get("source_id") == ability_source.object_id
        for event in game.events
    )
    production = next(
        event
        for event in game.events
        if event.get("event") == "floating_mana_produced"
        and event.get("source_id") == punks.object_id
    )
    assert any(
        allocation.source_event_id == production["stack_object_id"]
        and allocation.spending_context.value == "artifact_spell"
        for allocation in game.floating_mana.consumptions(0)
    )


def test_pilot_passes_do_not_speculatively_spend_preferred_followup_mana():
    game, punks, large, small, spell, ability_source = make_game(40102)

    class PassingPilot(AcceptancePilot):
        def __init__(self):
            self.callback_fingerprints = []

        def choose_main_action(self, view, options, stage):
            before = game.authoritative_state_fingerprint()
            self.callback_fingerprints.append(before)
            if stage in {"damage", "destroy", "creature"}:
                assert all(
                    item.kind is ActionKind.PASS
                    or (item.kind is ActionKind.CAST and item.object_id == spell.object_id)
                    for item in options
                )
                return next(item for item in options if item.kind is ActionKind.PASS)
            return super().choose_main_action(view, options, stage)

    _run_main_action_stages(game, PassingPilot())

    assert game.floating_mana.snapshot(0, "artifact_spell") == {"R": 1}
    assert spell.zone == "hand"
    assert large.damage == 0
    assert small.zone == "battlefield"
    assert not any(
        event.get("event") == "activation_announced"
        and event.get("source_id") == ability_source.object_id
        for event in game.events
    )
    assert (
        len(
            [
                event
                for event in game.events
                if event.get("event") == "floating_mana_produced"
                and event.get("source_id") == punks.object_id
            ]
        )
        == 1
    )
