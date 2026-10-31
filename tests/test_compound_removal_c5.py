"""C5: generic optional removal followed by Mutagen creation."""

from dataclasses import replace

from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import CardFact, Game

CHAIN = CardFact(
    "Compound spell fixture",
    "{2}{G}",
    3,
    "Sorcery",
    "Destroy up to one target artifact, enchantment, or creature with flying. "
    "Create a Mutagen token. (It's an artifact with \"{1}, {T}, Sacrifice this token: "
    'Put a +1/+1 counter on target creature. Activate only as a sorcery.")',
)
LAND = CardFact("Forest", "", 0, "Basic Land — Forest")
ARTIFACT = CardFact("Relic", "{2}", 2, "Artifact")
GROUND = CardFact("Bear", "{2}", 2, "Creature — Bear", power=2, toughness=2)
FLYER = CardFact("Bat", "{1}{B}", 2, "Creature — Bat", power=1, toughness=1, keywords=("Flying",))


def ready(seed: int = 5005) -> Game:
    game = Game(([LAND] * 20, [LAND] * 20), seed=seed)
    game.begin_turn()
    for _ in range(3):
        game.create_permanent(LAND, 0, summoning_sick=False)
    return game


def mutagens(game: Game):
    return [p for p in game.players[0].battlefield if p.card.name == "Mutagen"]


def test_interpreter_requires_complete_compound_program():
    interpreter = CardInterpreter()
    assert interpreter.cast_program(CHAIN).kind is CastKind.COMPOUND_REMOVAL_TOKEN
    assert interpreter.compound_removal_token_program(CHAIN).executable
    assert interpreter.unsupported_fragments(CHAIN) == ()
    incomplete = replace(CHAIN, oracle_text=CHAIN.oracle_text + " Draw a card.")
    assert interpreter.compound_removal_token_program(incomplete) is None


def test_optional_target_destroyed_before_mutagen_enters_in_order():
    game = ready()
    target = game.create_permanent(ARTIFACT, 1, summoning_sick=False)
    card = game.set_hand_for_testing(0, [CHAIN])[0]
    assert game.cast(0, card, target)
    assert target.zone == "former"
    assert len(mutagens(game)) == 1
    resolution = next(e for e in game.events if e["event"] == "compound_removal_token_resolved")
    assert resolution["ordering"] == ("removal", "token_creation")
    assert game.events.index(
        next(
            e
            for e in game.events
            if e["event"] == "zone_changed" and e.get("source_object_id") == target.object_id
        )
    ) < game.events.index(next(e for e in game.events if e["event"] == "tokens_created"))


def test_declining_optional_removal_still_creates_mutagen():
    game = ready(5006)
    card = game.set_hand_for_testing(0, [CHAIN])[0]
    assert game.cast(0, card, None)
    assert len(mutagens(game)) == 1
    assert not any(e["event"] == "destroyed" for e in game.events)


def test_illegal_target_at_cast_fails_without_payment_or_token():
    game = ready(5007)
    target = game.create_permanent(GROUND, 1, summoning_sick=False)
    card = game.set_hand_for_testing(0, [CHAIN])[0]
    assert game.announce_spell(0, card, target) is None
    assert card.zone == "hand"
    assert not mutagens(game)


def test_target_departure_before_resolution_does_not_fizzle_token_clause():
    game = ready(5008)
    target = game.create_permanent(FLYER, 1, summoning_sick=False)
    card = game.set_hand_for_testing(0, [CHAIN])[0]
    spell = game.announce_spell(0, card, target)
    assert spell is not None
    game.move_object(target, "graveyard", reason="c5_target_departed")
    game.resolve_top_of_stack()
    assert len(mutagens(game)) == 1
    assert any(
        e["event"] == "compound_removal_token_resolved" and not e["removal_applied"]
        for e in game.events
    )
