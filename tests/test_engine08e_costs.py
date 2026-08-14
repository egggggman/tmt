import pytest

from tmnt_design_studio.card_interpreter07 import CastKind
from tmnt_design_studio.engine07 import CardFact, Game, ManaRequirement, PaymentPlan

PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains", "({T}: Add {W}.)")
MOUNTAIN = CardFact("Mountain", "", 0, "Basic Land — Mountain", "({T}: Add {R}.)")
BEAR = CardFact("Bear", "{1}{W}", 2, "Creature — Bear", power=2, toughness=2)
MULTICOLOR = CardFact(
    "Multicolor Test",
    "{1}{W}{R}",
    3,
    "Creature — Test",
    power=3,
    toughness=3,
)
HYBRID = CardFact(
    "Hybrid Test",
    "{W/R}",
    1,
    "Creature — Test",
    power=1,
    toughness=1,
)


def prepared_game(hand: list[CardFact]) -> Game:
    deck = [PLAINS] * 60
    current = Game((deck, deck), seed=82)
    current.begin_turn()
    current.set_hand_for_testing(0, hand)
    return current


def test_typed_cost_construction_is_exact_and_rejects_unrepresented_symbols():
    assert Game.mana_requirement(BEAR) == ManaRequirement(1, ("W",))
    assert Game.mana_requirement(MULTICOLOR) == ManaRequirement(1, ("W", "R"))
    assert Game.mana_requirement(HYBRID) is None
    inconsistent = CardFact("Bad Value", "{1}{W}", 3, "Creature", power=1, toughness=1)
    assert Game.mana_requirement(inconsistent) is None


def test_payment_plan_uses_colored_sources_first_then_deterministic_generic_source():
    current = prepared_game([MULTICOLOR])
    generic = current.create_permanent(PLAINS, 0, summoning_sick=False)
    red = current.create_permanent(MOUNTAIN, 0, summoning_sick=False)
    white = current.create_permanent(PLAINS, 0, summoning_sick=False)
    card = current.players[0].hand[0]

    plan = current.payment_plan(0, card)

    assert plan == PaymentPlan(
        0,
        card.object_id,
        ManaRequirement(1, ("W", "R")),
        (generic.object_id, red.object_id, white.object_id),
    )
    assert not any(source.tapped for source in (generic, red, white))


def test_announcement_atomically_commits_payment_and_stack_movement():
    current = prepared_game([BEAR])
    first = current.create_permanent(PLAINS, 0, summoning_sick=False)
    second = current.create_permanent(PLAINS, 0, summoning_sick=False)
    card = current.players[0].hand[0]

    spell = current.announce_spell(0, card)

    assert spell is not None and spell.cast_kind is CastKind.CREATURE
    assert (first.tapped, second.tapped) == (True, True)
    event = next(event for event in current.events if event["event"] == "cost_paid")
    assert event["source_ids"] == [first.object_id, second.object_id]
    assert event["generic"] == 1
    assert event["colored"] == ["W"]


def test_stale_or_fabricated_payment_plan_is_rejected_before_mutation():
    current = prepared_game([BEAR])
    first = current.create_permanent(PLAINS, 0, summoning_sick=False)
    second = current.create_permanent(PLAINS, 0, summoning_sick=False)
    card = current.players[0].hand[0]
    plan = current.payment_plan(0, card)
    assert plan is not None
    first.tapped = True

    with pytest.raises(ValueError, match="no longer legal"):
        current._commit_announcement_payment(
            card, plan, cast_kind=CastKind.CREATURE, target_id=None
        )

    assert current.players[0].hand == [card]
    assert current.stack == []
    assert first.tapped and not second.tapped


def test_zone_failure_rolls_back_every_payment_source(monkeypatch):
    current = prepared_game([BEAR])
    first = current.create_permanent(PLAINS, 0, summoning_sick=False)
    second = current.create_permanent(PLAINS, 0, summoning_sick=False)
    card = current.players[0].hand[0]
    plan = current.payment_plan(0, card)
    assert plan is not None

    def fail_move(*_args, **_kwargs):
        raise RuntimeError("injected zone failure")

    monkeypatch.setattr(current, "move_object", fail_move)
    with pytest.raises(RuntimeError, match="injected zone failure"):
        current._commit_announcement_payment(
            card, plan, cast_kind=CastKind.CREATURE, target_id=None
        )

    assert not first.tapped and not second.tapped
    assert current.players[0].hand == [card]
    assert current.stack == []


def test_unsupported_cost_stays_explicit_and_never_pays_or_moves():
    current = prepared_game([HYBRID])
    source = current.create_permanent(PLAINS, 0, summoning_sick=False)
    card = current.players[0].hand[0]

    assert current.announce_spell(0, card) is None

    assert not source.tapped
    assert current.players[0].hand == [card]
    assert current.stack == []
    assert any(
        event["event"] == "unsupported_semantics"
        and event["reason"] == "mana_cost_not_implemented"
        and event["oracle_fragment"] == "{W/R}"
        for event in current.events
    )
