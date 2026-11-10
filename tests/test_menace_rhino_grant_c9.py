from dataclasses import replace

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, TurnStep

LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
RHINO = CardFact("Rhino", "{2}", 2, "Creature — Rhino", power=3, toughness=3)
BEAR = CardFact("Bear", "{1}", 1, "Creature — Bear", power=2, toughness=2)
GRANTER = CardFact(
    "Warthog Grantor",
    "{2}{R}",
    3,
    "Creature — Boar Mutant",
    "Menace\nRhinos you control have menace.",
    power=3,
    toughness=3,
    keywords=("Menace",),
)


def _game():
    game = Game(([LAND] * 20, [LAND] * 20), seed=9210)
    game.begin_turn()
    return game


def _attack(game, attacker):
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    option = next(
        item for item in game.legal_attack_options(0) if item.attacker_ids == (attacker.object_id,)
    )
    game.execute_attack_action(option)
    return option


def test_exact_grant_grammar_is_generic_and_supported():
    interpreter = CardInterpreter()
    fragment = "Rhinos you control have menace."
    assert interpreter.static_keyword_grant_semantic_coverage(
        GRANTER, fragment
    ).coverage.fully_supported
    assert interpreter.static_keyword_grant_semantic_coverage(
        replace(GRANTER, name="Generic Grantor"), fragment
    ).coverage.fully_supported
    assert (
        interpreter.static_keyword_grant_semantic_coverage(
            GRANTER, "Rhinos you control have flying."
        ).coverage.fully_supported
        is False
    )


def test_rhino_grant_requires_controller_and_live_source():
    game = _game()
    grantor = game.create_permanent(GRANTER, 0, summoning_sick=False)
    rhino = game.create_permanent(RHINO, 0, summoning_sick=False)
    assert game._has_menace(rhino)
    game.change_controller(grantor, 1)
    assert not game._has_menace(rhino)
    game.change_controller(grantor, 0)
    game.move_object(grantor, "graveyard", reason="grant_source_departure")
    assert not game._has_menace(rhino)


def test_rhino_grant_is_dynamic_for_entry_and_non_rhino_creatures():
    game = _game()
    game.create_permanent(GRANTER, 0, summoning_sick=False)
    first = game.create_permanent(RHINO, 0, summoning_sick=False)
    bear = game.create_permanent(BEAR, 0, summoning_sick=False)
    assert game._has_menace(first)
    assert not game._has_menace(bear)
    second = game.create_permanent(RHINO, 0, summoning_sick=False)
    assert game._has_menace(second)
    assert game._has_menace(first)


def test_grants_are_controller_scoped_for_friendly_and_opposing_rhinos():
    game = _game()
    grantor = game.create_permanent(GRANTER, 0, summoning_sick=False)
    friendly = game.create_permanent(RHINO, 0, summoning_sick=False)
    opposing = game.create_permanent(RHINO, 1, summoning_sick=False)
    assert game._has_menace(friendly)
    assert not game._has_menace(opposing)
    game.change_controller(grantor, 1)
    assert not game._has_menace(friendly)
    assert game._has_menace(opposing)


def test_overlapping_grants_recalculate_when_sources_leave():
    game = _game()
    grantor_a = game.create_permanent(GRANTER, 0, summoning_sick=False)
    grantor_b = game.create_permanent(
        replace(GRANTER, name="Second Grantor"), 0, summoning_sick=False
    )
    rhino = game.create_permanent(RHINO, 0, summoning_sick=False)
    assert game._has_menace(rhino)
    game.move_object(grantor_a, "graveyard", reason="first_grant_departure")
    assert game._has_menace(rhino)
    game.move_object(grantor_b, "graveyard", reason="second_grant_departure")
    assert not game._has_menace(rhino)


def test_granted_menace_requires_two_blockers_and_conflicts_with_single_limit():
    game = _game()
    grantor = game.create_permanent(GRANTER, 0, summoning_sick=False)
    grantor.tapped = True
    attacker = game.create_permanent(RHINO, 0, summoning_sick=False)
    [game.create_permanent(BEAR, 1, summoning_sick=False) for _ in range(2)]
    attack = _attack(game, attacker)
    options = game.legal_block_options(attack, 1)
    assert all(len(option.blocks) != 1 for option in options)
    assert any(len(option.blocks) == 2 for option in options)
    limited = replace(
        RHINO,
        oracle_text="This creature can't be blocked by more than one creature.",
    )
    game2 = _game()
    grantor2 = game2.create_permanent(GRANTER, 0, summoning_sick=False)
    grantor2.tapped = True
    limited_attacker = game2.create_permanent(limited, 0, summoning_sick=False)
    game2.create_permanent(BEAR, 1, summoning_sick=False)
    game2.create_permanent(BEAR, 1, summoning_sick=False)
    attack2 = _attack(game2, limited_attacker)
    assert [option.blocks for option in game2.legal_block_options(attack2, 1)] == [()]


def test_grant_replay_is_deterministic():
    def observe():
        game = _game()
        grantor = game.create_permanent(GRANTER, 0, summoning_sick=False)
        grantor.tapped = True
        attacker = game.create_permanent(RHINO, 0, summoning_sick=False)
        game.create_permanent(BEAR, 1, summoning_sick=False)
        game.create_permanent(BEAR, 1, summoning_sick=False)
        attack = _attack(game, attacker)
        return game.snapshot(), game.legal_block_options(attack, 1)

    assert observe() == observe()
