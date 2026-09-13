from tmnt_design_studio.engine07 import (
    CardFact,
    CastKind,
    Game,
    StackObject,
    TemporaryKeyword,
    TemporaryKeywordEffect,
)

LAND = CardFact("Forest", "", 0, "Basic Land ? Forest")
FROG = CardFact(
    "Frog Butler",
    "{1}{G}",
    2,
    "Creature ? Frog Spirit",
    "Deathtouch\n{T}: Add one mana of any color.\n"
    "{2}: This creature gains reach until end of turn.",
    power=2,
    toughness=2,
    keywords=("Deathtouch",),
)
FLYER = CardFact(
    "Sky Drake",
    "{1}{U}",
    2,
    "Creature ? Drake",
    "Flying",
    keywords=("Flying",),
    power=2,
    toughness=2,
)
FRAGMENT = "{2}: This creature gains reach until end of turn."


def pass_priority(game):
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            game.process_priority_resolution()
        else:
            game.execute_priority_action(
                game.legal_priority_actions(game.priority_state.player_index)[0]
            )


def setup():
    g = Game(([LAND] * 30, [LAND] * 30), seed=4141)
    g.begin_turn()
    g.create_permanent(LAND, 0, summoning_sick=False)
    g.create_permanent(LAND, 0, summoning_sick=False)
    frog = g.create_permanent(FROG, 0, summoning_sick=False)
    dummy = StackObject(g._allocate_object_id(), FROG, 1, 1, CastKind.CREATURE)
    g._register(dummy)
    g.stack.append(dummy)
    return g, frog


def activate(g, frog):
    g._begin_priority_window()
    ability = g.announce_activated_ability(0, frog, FRAGMENT)
    assert ability is not None
    pass_priority(g)


def test_frog_butler_reach_exact_activation_and_payment():
    g, frog = setup()
    activate(g, frog)
    assert g.has_temporary_keyword(frog, TemporaryKeyword.REACH)
    assert any(
        e["event"] == "frog_butler_reach_granted" and e["source_id"] == frog.object_id
        for e in g.events
    )


def test_reach_changes_defensive_flying_block_legality():
    g, frog = setup()
    assert not g.has_temporary_keyword(frog, TemporaryKeyword.REACH)
    frog.temporary_keyword_effects.append(
        TemporaryKeywordEffect(
            TemporaryKeyword.REACH, "until_end_of_turn", frog.object_id, FRAGMENT
        )
    )
    assert g.has_temporary_keyword(frog, TemporaryKeyword.REACH)


def test_reach_expires_at_end_of_turn():
    g, frog = setup()
    activate(g, frog)
    assert g.has_temporary_keyword(frog, TemporaryKeyword.REACH)
    g._perform_cleanup()
    assert not g.has_temporary_keyword(frog, TemporaryKeyword.REACH)


def test_reach_source_departure_fails_closed():
    g, frog = setup()
    g._begin_priority_window()
    g.announce_activated_ability(0, frog, FRAGMENT)
    g.destroy(frog)
    pass_priority(g)
    assert frog.temporary_keyword_effects == []


def test_reach_repeated_activation_is_deterministic():
    def run():
        g, frog = setup()
        activate(g, frog)
        return g.authoritative_state_fingerprint(), tuple(
            (e["event"], e.get("source_id"))
            for e in g.events
            if e["event"].startswith("frog_butler")
        )

    assert run() == run()
