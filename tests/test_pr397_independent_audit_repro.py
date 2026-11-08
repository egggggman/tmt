"""Independent synthetic probes for PR #397 decision behavior."""

import pytest

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
PREEXISTING_ABILITY = CardFact(
    "Synthetic Preexisting Ability",
    "",
    0,
    "Creature — Test",
    "{1}: Synthetic Preexisting Ability gains first strike until end of turn.",
    2,
    2,
)
ARTIFACT_CREATURE = CardFact(
    "Synthetic Artifact Creature", "{R}", 1, "Artifact Creature — Test", "", 1, 1
)
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature — Bear", "", 2, 2)


@pytest.mark.parametrize(
    ("own_life", "opponent_life", "target_kind", "expected"),
    [
        (10, 4, "creature", "player:1"),
        (3, 4, "creature", "player:1"),
        (2, 20, "players", "player:1"),
    ],
    ids=("win-over-creature", "draw-over-loss", "least-bad-losing-line"),
)
def test_pizza_target_policy_ranks_terminal_outcomes(
    own_life, opponent_life, target_kind, expected
):
    game = Game(([LAND] * 20, [LAND] * 20), seed=39702)
    game.begin_turn()
    game.players[0].life = own_life
    game.players[1].life = opponent_life
    offered = ("player:0", "player:1")
    if target_kind == "creature":
        creature = game.create_permanent(BEAR, 1, summoning_sick=False)
        offered = (creature.object_id, "player:1")

    assert AcceptancePilot.choose_damage_target(game.pilot_view(0), offered) == expected


def test_pilot_executes_the_artifact_followup_that_justified_punks_mana():
    game = Game(([LAND] * 20, [LAND] * 20), seed=39701)
    game.begin_turn()
    punks = game.create_permanent(PUNKS, 0, summoning_sick=False)
    other_ability = game.create_permanent(PREEXISTING_ABILITY, 0, summoning_sick=False)
    game.create_permanent(LAND, 0, summoning_sick=False)
    artifact = game.set_hand_for_testing(0, [ARTIFACT_CREATURE])[0]

    before = game.legal_main_actions(0)
    assert any(
        item.kind is ActionKind.ACTIVATE_ABILITY and item.object_id == other_ability.object_id
        for item in before
    )
    punks_option = next(item for item in before if item.object_id == punks.object_id)
    assert punks_option.mana_followups == (f"cast:{artifact.object_id}",)
    assert not any(
        item.kind is ActionKind.CAST and item.object_id == artifact.object_id for item in before
    )

    _run_main_action_stages(game, AcceptancePilot())

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
    assert not any(
        event.get("event") == "activation_announced"
        and event.get("source_id") == other_ability.object_id
        for event in game.events
    )
    assert artifact.zone == "former"
