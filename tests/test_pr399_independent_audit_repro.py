"""Independent synthetic checks for PR #399 follow-up selection."""

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


def make_targeting_game(seed):
    game = Game(([LAND] * 10, [LAND] * 10), seed=seed)
    game.begin_turn()
    punks = game.create_permanent(PUNKS, 0, summoning_sick=False)
    large = game.create_permanent(LARGE_CREATURE, 1, summoning_sick=False)
    small = game.create_permanent(SMALL_CREATURE, 1, summoning_sick=False)
    spell = game.set_hand_for_testing(0, [TARGETED_ARTIFACT])[0]
    return game, punks, large, small, spell


def test_punks_followup_preserves_existing_target_policy_for_targeted_casts():
    control, control_punks, control_large, control_small, _spell = make_targeting_game(39901)
    mana_action = next(
        option
        for option in control.legal_main_actions(0)
        if option.kind is ActionKind.ACTIVATE_ABILITY
        and option.object_id == control_punks.object_id
    )
    assert mana_action.mana_followups
    assert control.execute_main_action(mana_action)
    cast_options = control.legal_main_actions(0)
    expected = AcceptancePilot().choose_main_action(control.pilot_view(0), cast_options, "damage")
    assert expected.target_id == control_small.object_id
    _run_main_action_stages(control, AcceptancePilot())
    assert control_small.zone == "former"
    assert control_large.damage == 0

    game, _punks, large, small, _spell = make_targeting_game(39902)
    _run_main_action_stages(game, AcceptancePilot())

    # The recheck currently takes the first CAST option for the advertised card ID,
    # bypassing the existing target chooser that selects the lethal small creature.
    assert small.zone == "former"
    assert large.damage == 0
