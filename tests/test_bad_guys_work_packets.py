from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, TemporaryKeyword, TurnStep

LAND = CardFact("Plains", "", 0, "Basic Land — Plains")
BEAR = CardFact("Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)
FOOT_ELITE = CardFact(
    "Foot Elite",
    "{2}{B}",
    3,
    "Creature — Human Ninja",
    "Whenever this creature attacks, another target creature you control gets +1/+0 "
    'and gains indestructible until end of turn. (Damage and effects that say "destroy" '
    "don't destroy it.)",
    2,
    4,
)
FOOT_MYSTIC = CardFact(
    "Foot Mystic",
    "{2}{B}",
    3,
    "Creature — Human Ninja Warlock",
    "Lifelink\nDisappear — When this creature enters, if a permanent left the battlefield "
    "under your control this turn, create a 1/1 black Ninja creature token.",
    2,
    4,
    ("Lifelink", "Disappear"),
)


def game():
    current = Game(([LAND] * 60, [LAND] * 60))
    current.begin_turn()
    return current


def test_work_packet_fragments_are_fully_interpreted():
    interpreter = CardInterpreter()
    assert interpreter.unsupported_fragments(FOOT_ELITE) == ()
    assert interpreter.unsupported_fragments(FOOT_MYSTIC) == ()


def test_foot_elite_targets_another_creature_and_indestructibility_expires():
    current = game()
    elite = current.create_permanent(FOOT_ELITE, 0, summoning_sick=False)
    ally = current.create_permanent(BEAR, 0, summoning_sick=False)
    current.advance_to(TurnStep.DECLARE_ATTACKERS)
    option = current.legal_attack_options(0)[-1]
    current.execute_attack_action(option)
    assert ally.power == 3
    assert current.has_temporary_keyword(ally, TemporaryKeyword.INDESTRUCTIBLE)
    ally.damage = ally.toughness
    current.check_state_based_actions()
    assert current.is_authoritative(ally, "battlefield")
    current.destroy(ally)
    assert current.is_authoritative(ally, "battlefield")
    current._perform_cleanup()
    assert not current.has_temporary_keyword(ally, TemporaryKeyword.INDESTRUCTIBLE)
    ally.damage = ally.toughness
    current.check_state_based_actions()
    assert not current.is_authoritative(ally, "battlefield")
    assert elite.zone == "battlefield"


def test_foot_mystic_requires_same_turn_departure_under_its_controller():
    current = game()
    departed = current.create_permanent(BEAR, 0, summoning_sick=False)
    current.move_object(departed, "graveyard")
    mystic = current.create_permanent(FOOT_MYSTIC, 0, summoning_sick=False)
    current._process_creature_entered_triggers(mystic)
    assert [p.card.name for p in current.players[0].battlefield].count("Ninja") == 1

    other = game()
    foreign = other.create_permanent(BEAR, 1, summoning_sick=False)
    other.move_object(foreign, "graveyard")
    other_mystic = other.create_permanent(FOOT_MYSTIC, 0, summoning_sick=False)
    other._process_creature_entered_triggers(other_mystic)
    assert not any(p.card.name == "Ninja" for p in other.players[0].battlefield)
