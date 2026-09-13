from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, TurnStep

LAND = CardFact("Plains", "", 0, "Basic Land ? Plains")
LEONARDO = CardFact(
    "Leonardo, Sewer Samurai",
    "{3}{W}",
    4,
    "Legendary Creature ? Mutant Ninja Turtle Samurai",
    "Sneak {2}{W}{W}\nDouble strike\n"
    "During your turn, you may cast creature spells with power or toughness 1 or less "
    "from your graveyard. If you cast a spell this way, that creature enters with a finality "
    "counter on it.",
    power=3,
    toughness=3,
    keywords=("Double strike", "Sneak"),
)
QUALIFYING = CardFact(
    "Small Grave Creature", "{1}{W}", 2, "Creature ? Turtle", power=1, toughness=3
)
POWER_TWO = CardFact("Power Two", "{1}{W}", 2, "Creature ? Turtle", power=2, toughness=2)
TOUGHNESS_ONE = CardFact(
    "Fragile Grave Creature", "{2}{W}", 3, "Creature ? Turtle", power=3, toughness=1
)


def game():
    current = Game(([LAND] * 20, [LAND] * 20), seed=9200)
    current.begin_turn()
    for _ in range(4):
        current.create_permanent(LAND, 0, summoning_sick=False)
    current.create_permanent(LEONARDO, 0, summoning_sick=False)
    current.advance_to(TurnStep.PRECOMBAT_MAIN)
    return current


def put_in_graveyard(current, card, owner=0):
    obj = current.set_hand_for_testing(owner, [card])[0]
    return current.move_object(obj, "graveyard", reason="test_setup")


def grave_cast_option(current, card):
    grave = put_in_graveyard(current, card)
    option = next(
        option
        for option in current.legal_main_actions(0)
        if option.kind is ActionKind.CAST and option.object_id == grave.object_id
    )
    return grave, option


def test_qualifying_own_graveyard_cast_pays_on_stack_and_enters_with_finality():
    current = game()
    grave, option = grave_cast_option(current, QUALIFYING)
    assert option.oracle_fragment is not None
    spell = current.announce_spell(0, grave, cast_from_graveyard=True)
    assert spell is not None and spell.cast_from_graveyard is True
    assert spell.finality_on_entry is True
    assert spell.object_id in {item.object_id for item in current.stack}
    assert all(land.tapped for land in current.players[0].battlefield if land.card is LAND) is False
    current.resolve_top_of_stack()
    permanent = current.players[0].battlefield[-1]
    assert permanent.card is QUALIFYING
    assert permanent.object_id != grave.object_id
    assert permanent.counters == {"finality": 1}
    assert any(event["event"] == "finality_counter_placed" for event in current.events)


def test_graveyard_permission_enforces_own_zone_and_power_toughness_or_boundary():
    current = game()
    qualifying = put_in_graveyard(current, QUALIFYING)
    fragile = put_in_graveyard(current, TOUGHNESS_ONE)
    too_large = put_in_graveyard(current, POWER_TWO)
    opponent = put_in_graveyard(current, QUALIFYING, owner=1)
    options = current.legal_main_actions(0)
    ids = {
        option.object_id
        for option in options
        if option.oracle_fragment is not None and "from your graveyard" in option.oracle_fragment
    }
    assert ids == {qualifying.object_id, fragile.object_id}
    assert too_large.object_id not in ids and opponent.object_id not in ids


def test_finality_replaces_later_death_with_exile_and_keeps_incarnations_distinct():
    current = game()
    grave, option = grave_cast_option(current, QUALIFYING)
    current.execute_main_action(option)
    incarnation = next(
        permanent for permanent in current.players[0].battlefield if permanent.card is QUALIFYING
    )
    incarnation.damage = incarnation.toughness
    current.check_state_based_actions()
    assert all(permanent.card is not QUALIFYING for permanent in current.players[0].battlefield)
    assert not current.players[0].graveyard
    assert len(current.players[0].exile) == 1
    exiled = current.players[0].exile[0]
    assert exiled.card is QUALIFYING
    assert exiled.object_id != incarnation.object_id != grave.object_id
    assert exiled.zone == "exile"
    assert any(event["event"] == "permanent_to_exile" for event in current.events)


def test_graveyard_cast_requires_normal_timing_and_mana_payment():
    current = game()
    grave = put_in_graveyard(current, QUALIFYING)
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    assert not any(option.object_id == grave.object_id for option in current.legal_main_actions(0))
    current = game()
    grave = put_in_graveyard(current, QUALIFYING)
    for land in current.players[0].battlefield:
        if land.card is LAND:
            land.tapped = True
    assert not any(option.object_id == grave.object_id for option in current.legal_main_actions(0))


""
