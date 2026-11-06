from tmnt_design_studio.card_interpreter07 import TokenCreationProgram, TokenDefinition
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
    assert sum(entry[2] == attacker.object_id for entry in game._artifact_entries_this_turn) == 1
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


def test_artifact_token_entry_is_recorded_once_and_uses_entry_controller():
    game, attacker, blocker = _game()
    token = game.create_tokens(
        1,
        TokenCreationProgram(TokenDefinition("Artifact", "Artifact"), 1),
        controller=1,
        source_card="Synthetic token maker",
        oracle_fragment="Create an artifact token.",
    )[0]
    assert sum(entry[2] == token.object_id for entry in game._artifact_entries_this_turn) == 1
    game.change_controller(token, 0)

    assert game._artifact_entries_this_turn[-1] == (game.turn, 1, token.object_id)
    assert game.blocking_restriction(attacker, blocker) is None


def test_artifact_moved_from_graveyard_enters_as_a_new_tracked_object():
    game, attacker, blocker = _game()
    card = game._create_card_object(ARTIFACT, 0, "graveyard")
    game.players[0].graveyard.append(card)
    permanent = game.move_object(
        card, "battlefield", controller=0, summoning_sick=False, reason="synthetic_return"
    )

    assert permanent.object_id != card.object_id
    assert sum(entry[2] == permanent.object_id for entry in game._artifact_entries_this_turn) == 1
    assert game.blocking_restriction(attacker, blocker) is not None


def test_fugitive_droid_artifact_entry_condition_expires_at_next_turn():
    game, attacker, blocker = _game()
    game.create_permanent(ARTIFACT, 0, summoning_sick=False)
    assert game.blocking_restriction(attacker, blocker) is not None

    while game.step is not TurnStep.END_STEP:
        if game.step is TurnStep.COMBAT_DAMAGE:
            game.resolve_combat_damage()
        game.advance_step()
    game.transition_to(TurnStep.CLEANUP)
    game._perform_cleanup()
    game.transition_to(TurnStep.UNTAP)

    assert game.blocking_restriction(attacker, blocker) is None
