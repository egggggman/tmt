import pytest

from tmnt_design_studio.card_interpreter07 import CastKind
from tmnt_design_studio.engine07 import CardFact, CardObject, Game, Permanent, StackObject, TurnStep

PLAINS = CardFact("Plains", "", 0, "Basic Land — Plains")
BEAR = CardFact("Bear", "{1}{W}", 2, "Creature — Bear", power=2, toughness=2)
LION = CardFact("Lion", "{1}{W}", 2, "Creature — Cat", power=2, toughness=2)
BOLT = CardFact(
    "Test Missile",
    "{1}{W}",
    2,
    "Instant",
    "Test Missile deals 3 damage to target creature.",
)
DESTROY = CardFact(
    "Test Removal",
    "{1}{W}",
    2,
    "Sorcery",
    "Destroy target artifact, enchantment, or creature with power 4 or greater.",
)
UNSUPPORTED = CardFact("Unknown Spell", "{1}{W}", 2, "Sorcery", "Draw two cards.")


def prepared_game(hand: list[CardFact]) -> Game:
    deck = [PLAINS] * 60
    current = Game((deck, deck), seed=81)
    current.begin_turn()
    for _ in range(8):
        current.create_permanent(PLAINS, 0, summoning_sick=False)
    current.set_hand_for_testing(0, hand)
    return current


def test_creature_uses_authoritative_hand_stack_battlefield_lifecycle():
    current = prepared_game([BEAR])
    hand_object = current.players[0].hand[0]

    spell = current.announce_spell(0, hand_object)

    assert isinstance(spell, StackObject)
    assert spell.card is BEAR
    assert spell.owner == 0
    assert spell.controller == 0
    assert spell.cast_kind is CastKind.CREATURE
    assert spell.object_id != hand_object.object_id
    assert hand_object.zone == "former"
    assert current.stack == [spell]
    assert current.is_authoritative(spell, "stack")
    current.check_invariants()

    permanent = current.resolve_top_of_stack()

    assert isinstance(permanent, Permanent)
    assert permanent.object_id not in {hand_object.object_id, spell.object_id}
    assert spell.zone == "former"
    assert current.stack == []
    assert current.is_authoritative(permanent, "battlefield")
    zone_events = [event for event in current.events if event["event"] == "zone_changed"]
    assert [event["event"] for event in zone_events[-2:]] == ["zone_changed", "zone_changed"]
    assert [
        (event["source_zone"], event["destination_zone"])
        for event in current.events
        if event["event"] == "zone_changed" and event["card"] == BEAR.name
    ] == [("hand", "stack"), ("stack", "battlefield")]
    current.check_invariants()


def test_stack_is_lifo_and_turn_cannot_advance_around_unresolved_spell():
    current = prepared_game([BEAR, LION])
    bear, lion = current.players[0].hand
    bear_spell = current.announce_spell(0, bear)
    lion_spell = current.announce_spell(0, lion)

    assert [spell.card.name for spell in current.stack] == [BEAR.name, LION.name]
    with pytest.raises(ValueError, match="unresolved stack"):
        current.transition_to(TurnStep.BEGINNING_OF_COMBAT)

    first = current.resolve_top_of_stack()
    second = current.resolve_top_of_stack()

    assert first.card is LION
    assert second.card is BEAR
    assert lion_spell is not None and lion_spell.zone == "former"
    assert bear_spell is not None and bear_spell.zone == "former"


def test_locked_target_is_revalidated_and_illegal_target_spell_has_no_effect():
    current = prepared_game([BOLT])
    target = current.create_permanent(BEAR, 1, summoning_sick=False)
    spell = current.announce_spell(0, current.players[0].hand[0], target)
    assert spell is not None and spell.target_id == target.object_id
    current.destroy(target)

    result = current.resolve_top_of_stack()

    assert isinstance(result, CardObject)
    assert result.zone == "graveyard"
    assert current.players[1].graveyard[-1].card is BEAR
    assert any(
        event["event"] == "spell_resolved_no_effect" and event["reason"] == "all_targets_illegal"
        for event in current.events
    )


def test_announcement_rejects_fabricated_stale_and_illegal_target_without_mutation():
    current = prepared_game([DESTROY])
    real_card = current.players[0].hand[0]
    small_target = current.create_permanent(BEAR, 1, summoning_sick=False)
    fabricated = CardObject("object-fabricated", DESTROY, 0, 0, "hand")
    before_events = len(current.events)
    tapped_before = [land.tapped for land in current.players[0].battlefield]

    assert current.announce_spell(0, fabricated, small_target) is None
    assert current.announce_spell(0, real_card, small_target) is None
    assert len(current.events) == before_events + 1  # only the real card reaches target validation
    assert [land.tapped for land in current.players[0].battlefield] == tapped_before
    assert current.players[0].hand == [real_card]
    assert current.stack == []


def test_unsupported_spell_remains_explicit_and_never_enters_stack_or_pays():
    current = prepared_game([UNSUPPORTED])
    card = current.players[0].hand[0]
    tapped_before = [land.tapped for land in current.players[0].battlefield]

    assert current.announce_spell(0, card) is None

    assert current.is_authoritative(card, "hand")
    assert current.stack == []
    assert [land.tapped for land in current.players[0].battlefield] == tapped_before
    assert any(
        event["event"] == "unsupported_semantics" and event["card"] == UNSUPPORTED.name
        for event in current.events
    )


def test_stack_rejects_fabricated_occupants_and_empty_resolution():
    current = prepared_game([])
    with pytest.raises(ValueError, match="empty stack"):
        current.resolve_top_of_stack()

    fake = StackObject("object-fake", BEAR, 0, 0, CastKind.CREATURE)
    current.stack.append(fake)
    with pytest.raises(ValueError, match="not authoritative"):
        current.resolve_top_of_stack()
    with pytest.raises(AssertionError, match="unregistered"):
        current.check_invariants()
