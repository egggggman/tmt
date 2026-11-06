from tmnt_design_studio.engine07 import CardFact, Game, TurnStep

LAND = CardFact("Island", "", 0, "Basic Land — Island")
ARTIFACT = CardFact("Artifact", "{1}", 1, "Artifact")
DROID = CardFact(
    "Fugitive Droid",
    "{U}",
    1,
    "Artifact Creature — Robot Scientist",
    "This creature can't be blocked if an artifact entered the battlefield under your "
    "control this turn.",
    power=1,
    toughness=1,
)
BLOCKER = CardFact("Blocker", "{1}{W}", 2, "Creature — Human", power=2, toughness=2)


def _game():
    game = Game(([LAND] * 12, [LAND] * 12), seed=411)
    attacker = game.create_permanent(DROID, 0, summoning_sick=False)
    game.begin_turn()
    blocker = game.create_permanent(BLOCKER, 1, summoning_sick=False)
    return game, attacker, blocker


def test_fugitive_droid_cannot_be_blocked_after_controlled_artifact_entry_even_if_it_left():
    game, attacker, blocker = _game()
    artifact = game.create_permanent(ARTIFACT, 0, summoning_sick=False)
    game.move_object(artifact, "graveyard", reason="synthetic_departure")

    assert game.blocking_restriction(attacker, blocker) == (
        "This creature can't be blocked if an artifact entered the battlefield under your "
        "control this turn.",
        "artifact_entered_under_your_control_this_turn",
    )
    assert not game.can_block(attacker, blocker, 1)


def test_fugitive_droid_does_not_get_unblockability_from_artifact_entering_for_opponent():
    game, attacker, blocker = _game()
    artifact = game.create_permanent(ARTIFACT, 1, summoning_sick=False)
    game.change_controller(artifact, 0)

    assert game.blocking_restriction(attacker, blocker) is None
    assert game.can_block(attacker, blocker, 1)


def test_fugitive_droid_artifact_entry_condition_expires_at_next_turn():
    game, attacker, blocker = _game()
    game.create_permanent(ARTIFACT, 0, summoning_sick=False)
    assert game.blocking_restriction(attacker, blocker) is not None

    game._step = TurnStep.CLEANUP
    game.transition_to(TurnStep.UNTAP)

    assert game.blocking_restriction(attacker, blocker) is None
