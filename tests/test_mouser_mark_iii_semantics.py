from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.engine07 import CardFact, Game, TurnStep, load_facts

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
MANIFEST = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json"

ISLAND = CardFact("Island", "", 0, "Basic Land - Island", "{T}: Add {U}.")
MOUNTAIN = CardFact("Mountain", "", 0, "Basic Land - Mountain", "{T}: Add {R}.")
MOUSER = CardFact(
    "Mouser Mark III",
    "{1}{U/R}",
    2,
    "Artifact Creature - Robot",
    "This creature can't attack unless you control another artifact.",
    power=2,
    toughness=3,
)
ARTIFACT_CREATURE = CardFact(
    "Artifact Bot", "{1}", 1, "Artifact Creature - Robot", power=1, toughness=1
)
ARTIFACT = CardFact("Artifact Device", "{1}", 1, "Artifact")
ORDINARY = CardFact("Ordinary Bear", "{1}", 1, "Creature - Bear", power=2, toughness=2)


def game_with_battlefield(*cards: tuple[CardFact, int], seed: int = 3011) -> Game:
    game = Game(([ISLAND] * 60, [ISLAND] * 60), seed=seed)
    game.begin_turn()
    for card, controller in cards:
        game.create_permanent(card, controller, summoning_sick=False)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)
    return game


def authoritative_mouser() -> CardFact:
    catalog = load_card_data(SNAPSHOT, MANIFEST)
    return load_facts(catalog, {"Mouser Mark III"})["Mouser Mark III"]


def test_actual_mouser_card_data_matches_the_authoritative_snapshot():
    card = authoritative_mouser()
    assert (card.mana_cost, card.mana_value, card.type_line) == (
        "{1}{U/R}",
        2,
        "Artifact Creature — Robot",
    )
    assert card.power == 2 and card.toughness == 3
    assert card.oracle_text == "This creature can't attack unless you control another artifact."


def test_actual_mouser_casts_from_blue_and_enters_as_a_two_three():
    game = Game(([ISLAND] * 60, [ISLAND] * 60), seed=3012)
    game.begin_turn()
    card = game.set_hand_for_testing(0, [authoritative_mouser()])[0]
    land = game.create_permanent(ISLAND, 0, summoning_sick=False)
    game.create_permanent(ISLAND, 0, summoning_sick=False)

    spell = game.announce_spell(0, card)
    assert spell is not None
    assert land.tapped
    game.resolve_top_of_stack()

    mouser = next(
        permanent
        for permanent in game.players[0].battlefield
        if permanent.card.name == card.card.name
    )
    assert (mouser.power, mouser.toughness) == (2, 3)


def test_mouser_alone_cannot_attack():
    game = game_with_battlefield((MOUSER, 0))

    assert game.legal_attackers(0) == []
    assert not any(option.attacker_ids for option in game.legal_attack_options(0))


def test_mouser_can_attack_with_another_artifact_creature():
    game = game_with_battlefield((MOUSER, 0), (ARTIFACT_CREATURE, 0))

    assert [permanent.card.name for permanent in game.legal_attackers(0)] == [
        MOUSER.name,
        ARTIFACT_CREATURE.name,
    ]


def test_mouser_can_attack_with_a_noncreature_artifact():
    game = game_with_battlefield((MOUSER, 0), (ARTIFACT, 0))

    assert [permanent.card.name for permanent in game.legal_attackers(0)] == [MOUSER.name]


def test_opponent_artifact_does_not_enable_mouser():
    game = game_with_battlefield((MOUSER, 0), (ARTIFACT, 1))

    assert game.legal_attackers(0) == []


def test_hand_and_graveyard_artifacts_do_not_enable_mouser():
    game = game_with_battlefield((MOUSER, 0))
    hand_artifact = game.set_hand_for_testing(0, [ARTIFACT])[0]
    game.move_object(hand_artifact, "graveyard")

    assert game.legal_attackers(0) == []


def test_two_mousers_see_each_other_as_another_artifact():
    game = game_with_battlefield((MOUSER, 0), (MOUSER, 0))

    assert len(game.legal_attackers(0)) == 2


def test_mouser_can_block_without_another_artifact():
    game = Game(([ISLAND] * 60, [ISLAND] * 60), seed=3013)
    game.begin_turn()
    mouser = game.create_permanent(MOUSER, 0, summoning_sick=False)
    attacker = game.create_permanent(ORDINARY, 1, summoning_sick=False)

    assert game.can_block(attacker, mouser, 0)


def test_mouser_restriction_tracks_artifact_entry_and_departure():
    game = game_with_battlefield((MOUSER, 0))
    artifact = game.create_permanent(ARTIFACT, 0, summoning_sick=False)
    assert game.legal_attackers(0)[0].card.name == MOUSER.name

    game.put_into_graveyard(artifact)
    assert game.legal_attackers(0) == []


def test_mouser_does_not_change_summoning_sickness_or_existing_combat_legality():
    game = Game(([ISLAND] * 60, [ISLAND] * 60), seed=3014)
    game.begin_turn()
    game.create_permanent(MOUSER, 0, summoning_sick=True)
    game.create_permanent(ARTIFACT, 0, summoning_sick=False)
    game.advance_to(TurnStep.DECLARE_ATTACKERS)

    assert game.legal_attackers(0) == []
