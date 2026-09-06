from tmnt_design_studio.card_interpreter07 import (
    ActivatedEffectKind,
    CardInterpreter,
    TokenCreationProgram,
    TokenDefinition,
)
from tmnt_design_studio.engine07 import CardFact, Game, TemporaryKeyword

LAND = CardFact("Mountain", "", 0, "Basic Land - Mountain", "({T}: Add {R}.)")
FRAGMENT = "{R}, {T}: Creature tokens you control gain haste until end of turn."
SOURCE = CardFact(
    "Ravenous Robots", "{2}{R}", 3, "Creature - Robot", FRAGMENT, power=2, toughness=2
)
TOKEN = CardFact("Robot token", "", 0, "Artifact Creature - Robot", power=1, toughness=1)


def setup():
    g = Game(([LAND] * 20, [LAND] * 20), seed=2200)
    g.begin_turn()
    land = g.create_permanent(LAND, 0, summoning_sick=False)
    source = g.create_permanent(SOURCE, 0, summoning_sick=False)
    token = g.create_tokens(
        0,
        TokenCreationProgram(
            TokenDefinition("Robot token", "Artifact Creature - Robot", power=1, toughness=1), 1
        ),
        source_card="test",
        oracle_fragment="test",
    )[0]
    return g, land, source, token


def resolve(g):
    while g.priority_state is not None:
        if g.priority_state.resolution_pending:
            g.process_priority_resolution()
        else:
            g.execute_priority_action(g.legal_priority_actions(g.priority_state.player_index)[0])


def test_exact_recognizer_and_neighbor():
    i = CardInterpreter()
    sem = i.activated_ability_semantics(SOURCE, FRAGMENT)
    assert (
        sem
        and sem.coverage.fully_supported
        and sem.program.effect_kind is ActivatedEffectKind.GRANT_TOKEN_HASTE_UNTIL_EOT
    )
    neighbor = i.activated_ability_semantics(
        SOURCE,
        "Whenever you cast an artifact spell, create a 1/1 colorless Robot artifact "
        "creature token.",
    )
    assert neighbor is None or not neighbor.coverage.fully_supported


def test_payment_stack_and_resolution_time_recipient():
    g, land, source, token = setup()
    ability = g.announce_activated_ability(0, source, FRAGMENT)
    assert (
        ability
        and land.tapped
        and source.tapped
        and not g.has_temporary_keyword(token, TemporaryKeyword.HASTE)
    )
    late = g.create_tokens(
        0,
        TokenCreationProgram(
            TokenDefinition("Robot token", "Artifact Creature - Robot", power=1, toughness=1), 1
        ),
        source_card="test",
        oracle_fragment="test",
    )[0]
    resolve(g)
    assert g.has_temporary_keyword(token, TemporaryKeyword.HASTE) and g.has_temporary_keyword(
        late, TemporaryKeyword.HASTE
    )


def test_source_leaving_does_not_cancel_effect_and_filters_recipients():
    g, land, source, token = setup()
    g.announce_activated_ability(0, source, FRAGMENT)
    g.move_object(source, "graveyard", reason="test")
    resolve(g)
    assert g.has_temporary_keyword(token, TemporaryKeyword.HASTE)


def test_insufficient_mana_or_tapped_source_fails_without_mutation():
    g = Game(([LAND] * 2, [LAND] * 2), seed=2201)
    g.begin_turn()
    source = g.create_permanent(SOURCE, 0, summoning_sick=False)
    assert g.announce_activated_ability(0, source, FRAGMENT) is None and not source.tapped


def test_exclusions_and_cleanup():
    g, land, source, token = setup()
    nontoken = g.create_permanent(SOURCE, 0, summoning_sick=False)
    noncreature = g.create_tokens(
        0,
        TokenCreationProgram(TokenDefinition("Relic", "Artifact"), 1),
        source_card="test",
        oracle_fragment="test",
    )[0]
    opponent = g.create_tokens(
        1,
        TokenCreationProgram(
            TokenDefinition("Robot token", "Creature - Robot", power=1, toughness=1), 1
        ),
        source_card="test",
        oracle_fragment="test",
    )[0]
    g.announce_activated_ability(0, source, FRAGMENT)
    resolve(g)
    assert g.has_temporary_keyword(token, TemporaryKeyword.HASTE)
    assert not g.has_temporary_keyword(nontoken, TemporaryKeyword.HASTE)
    assert not g.has_temporary_keyword(noncreature, TemporaryKeyword.HASTE)
    assert not g.has_temporary_keyword(opponent, TemporaryKeyword.HASTE)
    g._perform_cleanup()
    assert not g.has_temporary_keyword(token, TemporaryKeyword.HASTE)


def test_tapped_source_cannot_activate():
    g, land, source, token = setup()
    source.tapped = True
    assert g.announce_activated_ability(0, source, FRAGMENT) is None
