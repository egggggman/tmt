"""Pilot strategies that select immutable options supplied by the rules engine."""

from __future__ import annotations

import re
from typing import Protocol

from tmnt_design_studio.engine07 import (
    ActionKind,
    ActionOption,
    DiscardDrawOption,
    HandBottomDrawOption,
    ScryOption,
)
from tmnt_design_studio.pilot_input_v2 import (
    DiscardDrawViewV2 as DiscardDrawView,
)
from tmnt_design_studio.pilot_input_v2 import (
    GameViewV2 as GameView,
)
from tmnt_design_studio.pilot_input_v2 import (
    HandBottomDrawViewV2 as HandBottomDrawView,
)
from tmnt_design_studio.pilot_input_v2 import (
    PriorityViewV2,
)
from tmnt_design_studio.pilot_input_v2 import (
    ScryViewV2 as ScryView,
)


class Pilot(Protocol):
    def choose_main_action(
        self, view: GameView, options: tuple[ActionOption, ...], stage: str
    ) -> ActionOption: ...

    def choose_attack(self, view: GameView, options: tuple[ActionOption, ...]) -> ActionOption: ...

    def choose_blocks(self, view: GameView, options: tuple[ActionOption, ...]) -> ActionOption: ...

    def choose_sneak(self, view: GameView, options: tuple[ActionOption, ...]) -> ActionOption: ...

    def choose_scry(self, view: ScryView, options: tuple[ScryOption, ...]) -> ScryOption: ...

    def choose_hand_bottom_draw(
        self, view: HandBottomDrawView, options: tuple[HandBottomDrawOption, ...]
    ) -> HandBottomDrawOption: ...

    def choose_discard_draw(
        self, view: DiscardDrawView, options: tuple[DiscardDrawOption, ...]
    ) -> DiscardDrawOption: ...

    def choose_priority(
        self, view: PriorityViewV2, options: tuple[ActionOption, ...]
    ) -> ActionOption: ...

    def choose_damage_target(self, view: GameView, offered: tuple[str, ...]) -> str | None: ...


class AcceptancePilot:
    """Preserved Acceptance Match strategy; it never owns legality or state mutation."""

    @staticmethod
    def _card(view: GameView, player: int, object_id: str | None):
        return next((row for row in view.hands[player] if row[0] == object_id), None)

    @staticmethod
    def _hand_cycling(view: GameView, option: ActionOption) -> bool:
        """Recognize a legal cycling choice from its public option and hand zone."""
        return (
            option.kind is ActionKind.ACTIVATE_ABILITY
            and option.oracle_fragment is not None
            and re.match(r"^[A-Za-z]+cycling\s+\{", option.oracle_fragment) is not None
            and any(card[0] == option.object_id for card in view.hands[option.player_index])
        )

    @staticmethod
    def choose_damage_target(view: GameView, offered: tuple[str, ...]) -> str | None:
        """Choose among engine-offered Pizza targets using terminal and board state."""
        if not offered:
            return None
        controller = view.observer_index
        opponent = 1 - controller
        battlefield = {
            permanent.object_id: permanent for side in view.battlefields for permanent in side
        }

        def outcome_rank(own_life: int, opposing_life: int) -> int:
            if own_life <= 0 and opposing_life <= 0:
                return 1  # draw
            if opposing_life <= 0:
                return 3  # win
            if own_life <= 0:
                return 0  # loss
            return 2  # ongoing

        def score(target_id: str, index: int) -> tuple[int, int, int, int, int]:
            life = list(view.life)
            victim = None
            if target_id.startswith("player:"):
                try:
                    victim = int(target_id.partition(":")[2])
                except ValueError:
                    victim = None
                if victim not in (0, 1):
                    return (-1, 0, 0, 0, -index)
                life[victim] -= 4
            # The Oracle's mandatory follow-up damage is applied to the controller.
            life[controller] -= 3
            rank = outcome_rank(life[controller], life[opponent])
            permanent = battlefield.get(target_id)
            removes_opponent = int(
                permanent is not None
                and permanent.controller == opponent
                and permanent.toughness is not None
                and permanent.damage + 4 >= permanent.toughness
            )
            removes_creature = int(
                permanent is not None
                and permanent.toughness is not None
                and permanent.damage + 4 >= permanent.toughness
            )
            threat = (permanent.power or 0) if removes_opponent and permanent else 0
            opponent_damage = 4 if victim == opponent else 0
            return (rank, removes_opponent, removes_creature, threat + opponent_damage, -index)

        return max(enumerate(offered), key=lambda row: score(row[1], row[0]))[1]

    def choose_main_action(
        self, view: GameView, options: tuple[ActionOption, ...], stage: str
    ) -> ActionOption:
        fallback = next(option for option in options if option.kind is ActionKind.PASS)
        if stage == "land":
            return next(
                (option for option in options if option.kind is ActionKind.PLAY_LAND), fallback
            )
        if stage == "activate":
            useful_mana = next(
                (
                    option
                    for option in options
                    if option.kind is ActionKind.ACTIVATE_ABILITY and option.mana_followups
                ),
                None,
            )
            if useful_mana is not None:
                return useful_mana
            return next(
                (
                    option
                    for option in options
                    if option.kind is ActionKind.ACTIVATE_ABILITY
                    and not self._hand_cycling(view, option)
                    and not (option.restricted_mana_ability and not option.mana_followups)
                ),
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
            # A semantic action tag, independent of card/deck/opponent identity.
            battlefield = {obj.object_id: obj for side in view.battlefields for obj in side}
            suppression = [
                option
                for option in casts
                if option.oracle_fragment is not None
                and option.oracle_fragment.startswith("Enchanted creature is a ")
                and option.target_id in battlefield
                and battlefield[option.target_id].controller != option.player_index
            ]
            if suppression:
                return max(
                    suppression,
                    key=lambda option: (
                        battlefield[option.target_id].power or 0,
                        battlefield[option.target_id].toughness or 0,
                    ),
                )
            return next(
                (
                    option
                    for option in casts
                    if (card := self._card(view, option.player_index, option.object_id))
                    and card[1] == "Make Your Move"
                ),
                fallback,
            )
        draw_casts = [
            option
            for option in casts
            if option.oracle_fragment is not None
            and option.oracle_fragment.casefold().startswith("draw ")
        ]
        if draw_casts:
            return draw_casts[0]
        setup_casts = [
            option
            for option in casts
            if option.oracle_fragment is not None
            and option.oracle_fragment.casefold().startswith("when this class enters")
        ]
        if setup_casts:
            return setup_casts[0]
        if stage == "creature":
            creatures = [
                (option, card)
                for option in casts
                if (card := self._card(view, option.player_index, option.object_id)) and card[3]
            ]
            if creatures:
                return min(creatures, key=lambda row: (row[1][2], row[1][1]))[0]
            utility = [
                option
                for option in casts
                if (card := self._card(view, option.player_index, option.object_id))
                and card[1] in {"Skateboard", "Spicy Oatmeal Pizza"}
            ]
            if utility:
                return min(
                    utility,
                    key=lambda option: self._card(view, option.player_index, option.object_id)[2],
                )
            # A hand cycling option competes with casting. Use it for resource
            # development only when no ordinary spell is currently castable.
            if not casts:
                return next(
                    (option for option in options if self._hand_cycling(view, option)),
                    fallback,
                )
        return fallback

    def choose_attack(self, view: GameView, options: tuple[ActionOption, ...]) -> ActionOption:
        del view
        return max(options, key=lambda option: len(option.attacker_ids))

    def choose_blocks(self, view: GameView, options: tuple[ActionOption, ...]) -> ActionOption:
        del view
        return max(options, key=lambda option: len(option.blocks))

    def choose_sneak(self, view: GameView, options: tuple[ActionOption, ...]) -> ActionOption:
        """Choose the first engine-generated Sneak cast; legality remains engine-owned."""
        del view
        return next(
            (option for option in options if option.kind is ActionKind.CAST),
            next(option for option in options if option.kind is ActionKind.PASS),
        )

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

    def choose_discard_draw(
        self, view: DiscardDrawView, options: tuple[DiscardDrawOption, ...]
    ) -> DiscardDrawOption:
        """Deterministically take the optional one-card filter when available."""
        del view
        return next(
            (option for option in options if option.card_id is not None),
            next(option for option in options if option.card_id is None),
        )

    def choose_priority(
        self, view: PriorityViewV2, options: tuple[ActionOption, ...]
    ) -> ActionOption:
        """Take a supplied counter to an opposing public spell, otherwise pass."""
        opposing_spells = {
            item.object_id
            for item in view.stack_bottom_to_top
            if item.kind == "spell" and item.controller != view.priority_player
        }
        for option in options:
            if (
                option.kind in {ActionKind.ACTIVATE_ABILITY, ActionKind.CAST}
                and option.target_id in opposing_spells
            ):
                return option
        for option in options:
            if option.kind is ActionKind.ACTIVATE_ABILITY and option.mana_followups:
                return option
        for option in options:
            if option.kind is ActionKind.ACTIVATE_ABILITY and option.uses_restricted_mana:
                return option
        return next(option for option in options if option.kind is ActionKind.PASS_PRIORITY)


class PassingPilot(AcceptancePilot):
    """Deliberately poor but legal strategy used to prove legality is strategy-independent."""

    def choose_priority(
        self, view: PriorityViewV2, options: tuple[ActionOption, ...]
    ) -> ActionOption:
        del view
        return next(option for option in options if option.kind is ActionKind.PASS_PRIORITY)

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

    def choose_sneak(self, view: GameView, options: tuple[ActionOption, ...]) -> ActionOption:
        del view
        return next(option for option in options if option.kind is ActionKind.PASS)

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

    def choose_discard_draw(
        self, view: DiscardDrawView, options: tuple[DiscardDrawOption, ...]
    ) -> DiscardDrawOption:
        del view
        return next(option for option in options if option.card_id is None)
