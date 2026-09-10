"""Bounded, recipient-specific observations; no legality or execution authority.

Only the current face-up battlefield and Stack, the recipient's hand, and the
engine-supplied Scry inspection are described. No registry or history lookup is
used to recover departed targets. Unsupported observation kinds fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from tmnt_design_studio.engine07 import CardFact, Game


@dataclass(frozen=True, slots=True)
class CardDescription:
    object_id: str
    name: str
    mana_cost: str
    mana_value: int
    type_line: str
    oracle_text: str
    power: int | None
    toughness: int | None
    keywords: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BattlefieldViewV2:
    object_id: str
    name: str
    owner: int
    controller: int
    card: CardDescription
    type_line: str
    power: int | None
    toughness: int | None
    tapped: bool
    damage: int
    is_token: bool
    counters: tuple[tuple[str, int], ...]
    summoning_sick: bool
    represented_keyword_status: tuple[tuple[str, bool], ...]
    represented_land_payment_color: str | None
    land_payment_untapped: bool | None


@dataclass(frozen=True, slots=True)
class DecisionContextV2:
    observer_index: int
    turn: int
    active_player: int
    phase: str
    step: str
    life: tuple[int, ...]
    hand_sizes: tuple[int, ...]
    library_sizes: tuple[int, ...]
    own_hand: tuple[CardDescription, ...]
    battlefields: tuple[tuple[BattlefieldViewV2, ...], ...]
    own_lands_played: int
    schema_version: int = field(default=2, init=False)


@dataclass(frozen=True, slots=True)
class ScryViewV2:
    player_index: int
    requested: int
    cards: tuple[tuple[str, str], ...]
    context: DecisionContextV2
    inspected_cards: tuple[CardDescription, ...]
    schema_version: int = field(default=2, init=False)


@dataclass(frozen=True, slots=True)
class HandBottomDrawViewV2:
    player_index: int
    cards: tuple[tuple[str, str], ...]
    context: DecisionContextV2
    schema_version: int = field(default=2, init=False)


@dataclass(frozen=True, slots=True)
class DiscardDrawViewV2:
    player_index: int
    cards: tuple[tuple[str, str], ...]
    context: DecisionContextV2
    schema_version: int = field(default=2, init=False)


@dataclass(frozen=True, slots=True)
class PublicTargetV2:
    object_id: str
    announcement_zone: None
    current_public_zone: Literal["battlefield", "stack"] | None
    status: Literal["resolved", "unresolved"]
    description: CardDescription | None


@dataclass(frozen=True, slots=True)
class PublicStackItemV2:
    object_id: str
    kind: Literal["spell", "activated", "triggered"]
    controller: int
    spell_card: CardDescription | None
    source_card: CardDescription | None
    source_id: str | None
    public_effect_text: str
    represented_effect_tag: str | None
    targets: tuple[PublicTargetV2, ...]


@dataclass(frozen=True, slots=True)
class PriorityViewV2:
    context: DecisionContextV2
    priority_player: int
    priority_epoch: int
    consecutive_passes: tuple[int, ...]
    stack_bottom_to_top: tuple[PublicStackItemV2, ...]
    schema_version: int = field(default=2, init=False)


@dataclass(frozen=True, slots=True)
class GameViewV2:
    observer_index: int
    turn: int
    active_player: int
    phase: str
    step: str
    life: tuple[int, ...]
    hands: tuple[tuple[tuple[str, str, int, bool], ...], ...]
    battlefields: tuple[tuple[BattlefieldViewV2, ...], ...]
    hand_sizes: tuple[int, ...]
    schema_version: int = field(default=2, init=False)


def describe_card(object_id: str, card: CardFact) -> CardDescription:
    return CardDescription(
        object_id,
        card.name,
        card.mana_cost,
        card.mana_value,
        card.type_line,
        card.oracle_text,
        card.power,
        card.toughness,
        tuple(card.keywords),
    )


def decision_context(game: Game, observer_index: int) -> DecisionContextV2:
    from tmnt_design_studio.engine07 import StrikeKeyword, TemporaryKeyword

    if type(observer_index) is not int or observer_index not in (0, 1):
        raise ValueError("V2 observation requires an explicit seat 0 or 1")
    boards = []
    for player in game.players:
        rows = []
        for permanent in player.battlefield:
            strike = game.evaluated_strike_keywords(permanent)
            # These tags describe exactly the existing bounded queries. Other
            # printed keywords remain text, with no inferred executable status.
            status = tuple((tag.value, tag in strike) for tag in StrikeKeyword)
            status += (
                ("trample", game.evaluated_trample(permanent)),
                ("lifelink", game.evaluated_lifelink(permanent)),
            )
            status += tuple(
                ("temporary_" + tag.value, game.has_temporary_keyword(permanent, tag))
                for tag in TemporaryKeyword
            )
            rows.append(
                BattlefieldViewV2(
                    permanent.object_id,
                    permanent.card.name,
                    permanent.owner,
                    permanent.controller,
                    describe_card(permanent.object_id, permanent.card),
                    permanent.type_line,
                    permanent.power if permanent.card.is_creature else None,
                    permanent.toughness if permanent.card.is_creature else None,
                    permanent.tapped,
                    permanent.damage,
                    permanent.is_token,
                    tuple(sorted(permanent.counters.items())),
                    permanent.summoning_sick,
                    status,
                    game._mana_color(permanent) if permanent.card.is_land else None,
                    not permanent.tapped if permanent.card.is_land else None,
                )
            )
        boards.append(tuple(rows))
    return DecisionContextV2(
        observer_index,
        game.turn,
        game.active_player,
        game.phase,
        game.step.value,
        tuple(p.life for p in game.players),
        tuple(len(p.hand) for p in game.players),
        tuple(len(p.library) for p in game.players),
        tuple(describe_card(c.object_id, c.card) for c in game.players[observer_index].hand),
        tuple(boards),
        game.players[observer_index].lands_played,
    )


def pilot_view(game: Game, observer_index: int) -> GameViewV2:
    context = decision_context(game, observer_index)
    own_rows = tuple(
        (c.object_id, c.name, c.mana_value, "Creature" in c.type_line) for c in context.own_hand
    )
    return GameViewV2(
        observer_index,
        context.turn,
        context.active_player,
        context.phase,
        context.step,
        context.life,
        tuple(own_rows if i == observer_index else () for i in range(2)),
        context.battlefields,
        context.hand_sizes,
    )


def priority_view(game: Game, observer_index: int) -> PriorityViewV2:
    from tmnt_design_studio.engine07 import (
        ActivatedAbilityObject,
        StackObject,
        TriggeredAbilityObject,
    )

    context = decision_context(game, observer_index)
    priority = game.priority_state
    if priority is None or priority.resolution_pending or priority.player_index != observer_index:
        raise ValueError("V2 Priority observation requires the current decision owner")
    public = {
        row.object_id: ("battlefield", row.card) for board in context.battlefields for row in board
    }
    for item in game.stack:
        if type(item) is StackObject:
            public[item.object_id] = ("stack", describe_card(item.object_id, item.card))
        elif type(item) in (ActivatedAbilityObject, TriggeredAbilityObject):
            public[item.object_id] = ("stack", describe_card(item.source_id, item.source_card))
        else:
            raise ValueError("unsupported V2 public Stack kind")

    def target(object_id: str) -> PublicTargetV2:
        current = public.get(object_id)
        # Announcement-zone provenance is not stored in the bounded structures.
        return PublicTargetV2(
            object_id,
            None,
            current[0] if current else None,
            "resolved" if current else "unresolved",
            current[1] if current else None,
        )

    rows = []
    for item in game.stack:
        if type(item) is StackObject:
            rows.append(
                PublicStackItemV2(
                    item.object_id,
                    "spell",
                    item.controller,
                    describe_card(item.object_id, item.card),
                    None,
                    None,
                    item.card.oracle_text,
                    None,
                    tuple(target(i) for i in (() if item.target_id is None else (item.target_id,))),
                )
            )
        else:
            activated = type(item) is ActivatedAbilityObject
            ids = (
                item.target_ids
                if activated
                else (() if item.target_id is None else (item.target_id,))
            )
            rows.append(
                PublicStackItemV2(
                    item.object_id,
                    "activated" if activated else "triggered",
                    item.controller,
                    None,
                    describe_card(item.source_id, item.source_card),
                    item.source_id,
                    item.oracle_fragment,
                    None if activated else item.effect.value,
                    tuple(target(i) for i in ids),
                )
            )
    return PriorityViewV2(
        context,
        priority.player_index,
        priority.epoch,
        tuple(priority.consecutive_passes),
        tuple(rows),
    )
