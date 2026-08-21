"""Pilot strategies that select immutable options supplied by the rules engine."""

from __future__ import annotations

from typing import Protocol

from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    GameView,
    HandBottomDrawOption,
    HandBottomDrawView,
    ScryOption,
    ScryView,
)


class Pilot(Protocol):
    def choose_main_action(
        self, view: GameView, options: tuple[ActionOption, ...], stage: str
    ) -> ActionOption: ...

    def choose_attack(self, view: GameView, options: tuple[ActionOption, ...]) -> ActionOption: ...

    def choose_blocks(self, view: GameView, options: tuple[ActionOption, ...]) -> ActionOption: ...

    def choose_scry(self, view: ScryView, options: tuple[ScryOption, ...]) -> ScryOption: ...

    def choose_hand_bottom_draw(
        self, view: HandBottomDrawView, options: tuple[HandBottomDrawOption, ...]
    ) -> HandBottomDrawOption: ...

    def choose_priority(
        self, view: GameView, options: tuple[ActionOption, ...]
    ) -> ActionOption: ...


class AcceptancePilot:
    """Preserved Acceptance Match strategy; it never owns legality or state mutation."""

    @staticmethod
    def _card(view: GameView, player: int, object_id: str | None):
        return next((row for row in view.hands[player] if row[0] == object_id), None)

    def choose_main_action(
        self, view: GameView, options: tuple[ActionOption, ...], stage: str
    ) -> ActionOption:
        fallback = next(option for option in options if option.kind is ActionKind.PASS)
        if stage == "land":
            return next(
                (option for option in options if option.kind is ActionKind.PLAY_LAND), fallback
            )
        if stage == "activate":
            return next(
                (option for option in options if option.kind is ActionKind.ACTIVATE_ABILITY),
                fallback,
            )
        casts = [option for option in options if option.kind is ActionKind.CAST]
        if stage == "damage":
            candidates = [
                option
                for option in casts
                if (card := self._card(view, option.player_index, option.object_id))
                and card[1] == "Manhole Missile"
            ]
            if candidates:
                battlefield = {obj.object_id: obj for side in view.battlefields for obj in side}
                return min(
                    candidates,
                    key=lambda option: (
                        battlefield[option.target_id].toughness
                        - battlefield[option.target_id].damage
                    ),
                )
        if stage == "destroy":
            return next(
                (
                    option
                    for option in casts
                    if (card := self._card(view, option.player_index, option.object_id))
                    and card[1] == "Make Your Move"
                ),
                fallback,
            )
        if stage == "creature":
            creatures = [
                (option, card)
                for option in casts
                if (card := self._card(view, option.player_index, option.object_id)) and card[3]
            ]
            if creatures:
                return min(creatures, key=lambda row: (row[1][2], row[1][1]))[0]
        return fallback

    def choose_attack(self, view: GameView, options: tuple[ActionOption, ...]) -> ActionOption:
        del view
        return max(options, key=lambda option: len(option.attacker_ids))

    def choose_blocks(self, view: GameView, options: tuple[ActionOption, ...]) -> ActionOption:
        del view
        return max(options, key=lambda option: len(option.blocks))

    def choose_scry(self, view: ScryView, options: tuple[ScryOption, ...]) -> ScryOption:
        """Deterministically keep the inspected cards on top in their current order."""
        current = tuple(object_id for object_id, _name in view.cards)
        return next(
            option for option in options if option.top_ids == current and not option.bottom_ids
        )

    def choose_hand_bottom_draw(
        self, view: HandBottomDrawView, options: tuple[HandBottomDrawOption, ...]
    ) -> HandBottomDrawOption:
        """Deterministically take the optional filter when a hand card is available."""
        return next(
            (option for option in options if option.card_id is not None),
            next(option for option in options if option.card_id is None),
        )

    def choose_priority(self, view: GameView, options: tuple[ActionOption, ...]) -> ActionOption:
        """Deliberately pass; passing is a legal strategy, not an engine shortcut."""
        del view
        return next(option for option in options if option.kind is ActionKind.PASS_PRIORITY)


class PassingPilot(AcceptancePilot):
    """Deliberately poor but legal strategy used to prove legality is strategy-independent."""

    def choose_main_action(
        self, view: GameView, options: tuple[ActionOption, ...], stage: str
    ) -> ActionOption:
        del view, stage
        return next(option for option in options if option.kind is ActionKind.PASS)

    def choose_attack(self, view: GameView, options: tuple[ActionOption, ...]) -> ActionOption:
        del view
        return min(options, key=lambda option: len(option.attacker_ids))

    def choose_blocks(self, view: GameView, options: tuple[ActionOption, ...]) -> ActionOption:
        del view
        return min(options, key=lambda option: len(option.blocks))

    def choose_scry(self, view: ScryView, options: tuple[ScryOption, ...]) -> ScryOption:
        """A poor but legal choice: put every inspected card on the bottom."""
        current = tuple(object_id for object_id, _name in view.cards)
        return next(
            option for option in options if not option.top_ids and option.bottom_ids == current
        )

    def choose_hand_bottom_draw(
        self, view: HandBottomDrawView, options: tuple[HandBottomDrawOption, ...]
    ) -> HandBottomDrawOption:
        del view
        return next(option for option in options if option.card_id is None)
