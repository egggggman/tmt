"""Small, deterministic, rules-grounded Cardcade Engine 0.7 foundation.

This module deliberately implements only the rules surface it can represent honestly.  It is
separate from the preserved Engine 0.1--0.6 heuristic simulator.
"""

from __future__ import annotations

import json
import random
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal, Protocol

ENGINE_VERSION = "cardcade-0.7.0-alpha.4"

# Engine 0.6 intentionally omitted combat characteristics. These current Oracle values are
# versioned here as the minimal 0.7 facts delta for Acceptance Match #001.
ACCEPTANCE_CREATURE_STATS = {
    "April O'Neil, Kunoichi Trainee": (2, 2),
    "Casey Jones, Jury-Rig Justiciar": (2, 1),
    "Leonardo, Big Brother": (1, 3),
    "Leonardo, Cutting Edge": (1, 1),
    "Leonardo, Leader in Blue": (2, 1),
    "Leonardo, Sewer Samurai": (3, 3),
    "Lita, Little Orphan Amphibian": (2, 1),
    "Mighty Mutanimals": (2, 1),
    "Mutant Town Musicians": (2, 4),
    "Null Group Biological Assets": (3, 1),
    "Prehistoric Pet": (1, 2),
    "Raphael, Most Attitude": (4, 3),
    "Raphael, Ninja Destroyer": (4, 4),
    "Raphael, Tough Turtle": (1, 3),
    "Raphael, the Nightwatcher": (2, 3),
    "Wingnut, Bat on the Belfry": (1, 2),
}


@dataclass(frozen=True)
class CardFact:
    name: str
    mana_cost: str
    mana_value: int
    type_line: str
    oracle_text: str = ""
    power: int | None = None
    toughness: int | None = None
    keywords: tuple[str, ...] = ()

    @property
    def is_land(self) -> bool:
        return "Land" in self.type_line

    @property
    def is_creature(self) -> bool:
        return "Creature" in self.type_line


@dataclass
class PowerToughnessModifier:
    power: int
    toughness: int
    duration: Literal["persistent", "until_end_of_turn"]
    source_card: str
    oracle_fragment: str
    created_turn: int
    derived_static: bool = False


@dataclass
class Permanent:
    card: CardFact
    controller: int
    tapped: bool = False
    summoning_sick: bool = True
    damage: int = 0
    counters: dict[str, int] = field(default_factory=dict)
    pt_modifiers: list[PowerToughnessModifier] = field(default_factory=list)

    @property
    def printed_power(self) -> int:
        assert self.card.power is not None
        return self.card.power

    @property
    def printed_toughness(self) -> int:
        assert self.card.toughness is not None
        return self.card.toughness

    def counter_delta(self) -> tuple[int, int]:
        plus = self.counters.get("+1/+1", 0)
        minus = self.counters.get("-1/-1", 0)
        return plus - minus, plus - minus

    @property
    def power(self) -> int:
        counter_power, _ = self.counter_delta()
        return self.printed_power + counter_power + sum(x.power for x in self.pt_modifiers)

    @property
    def toughness(self) -> int:
        _, counter_toughness = self.counter_delta()
        return (
            self.printed_toughness + counter_toughness + sum(x.toughness for x in self.pt_modifiers)
        )


@dataclass
class PlayerState:
    name: str
    library: list[CardFact]
    hand: list[CardFact] = field(default_factory=list)
    battlefield: list[Permanent] = field(default_factory=list)
    graveyard: list[CardFact] = field(default_factory=list)
    life: int = 20
    lands_played: int = 0
    lost: bool = False
    loss_reason: str | None = None


class StateBasedAction(Protocol):
    """One reusable state-based check applied until the game state stabilizes."""

    name: str

    def apply(self, game: Game) -> bool: ...


@dataclass(frozen=True)
class LethalDamageStateBasedAction:
    name: str = "lethal_damage"

    def apply(self, game: Game) -> bool:
        changed = False
        for player in game.players:
            for permanent in list(player.battlefield):
                if permanent.card.is_creature and permanent.damage >= permanent.toughness:
                    game.destroy(permanent, state_based_action=self.name)
                    changed = True
        return changed


@dataclass(frozen=True)
class LegendRuleStateBasedAction:
    name: str = "legend_rule"

    def apply(self, game: Game) -> bool:
        changed = False
        for player_index, player in enumerate(game.players):
            groups: dict[str, list[Permanent]] = {}
            for permanent in player.battlefield:
                if "Legendary" in permanent.card.type_line:
                    groups.setdefault(permanent.card.name, []).append(permanent)
            for name, permanents in groups.items():
                if len(permanents) < 2:
                    continue
                keep = game.legend_rule_chooser(player_index, tuple(permanents))
                if keep not in permanents:
                    raise ValueError("legend-rule chooser must return one of the listed permanents")
                game.log(
                    "legend_rule_choice",
                    player=player.name,
                    card=name,
                    kept_battlefield_index=player.battlefield.index(keep),
                    moved_to_graveyard=len(permanents) - 1,
                )
                for permanent in permanents:
                    if permanent is not keep:
                        game.put_into_graveyard(permanent, state_based_action=self.name)
                        changed = True
        return changed


DEFAULT_STATE_BASED_ACTIONS: tuple[StateBasedAction, ...] = (
    LegendRuleStateBasedAction(),
    LethalDamageStateBasedAction(),
)


class Game:
    """Two-player deterministic game state and the supported legal transitions."""

    def __init__(
        self,
        decks: tuple[list[CardFact], list[CardFact]],
        names=("A", "B"),
        seed=1,
        *,
        state_based_actions: tuple[StateBasedAction, ...] = DEFAULT_STATE_BASED_ACTIONS,
        legend_rule_chooser=None,
        counter_target_chooser=None,
        alliance_mode_chooser=None,
    ):
        rng = random.Random(seed)
        shuffled = []
        for deck in decks:
            cards = list(deck)
            rng.shuffle(cards)
            shuffled.append(cards)
        self.players = [PlayerState(names[i], shuffled[i]) for i in range(2)]
        self.turn = 0
        self.active_player = 0
        self.phase = "setup"
        self.winner: int | None = None
        self.events: list[dict[str, object]] = []
        self.limitations: set[str] = set()
        self.state_based_actions = state_based_actions
        self.legend_rule_chooser = legend_rule_chooser or (
            lambda _player_index, permanents: permanents[0]
        )
        self.counter_target_chooser = counter_target_chooser or (
            lambda _player_index, _source, permanents: permanents[0]
        )
        self.alliance_mode_chooser = alliance_mode_chooser or (
            lambda _player_index, _source, modes: modes[0]
        )
        self.alliance_modes_chosen: dict[int, set[str]] = {}
        for player in self.players:
            self.draw(player, 7, setup=True)
        self.log("game_started", seed=seed, starting_player=names[0])

    _STATIC_OTHER_CREATURES = re.compile(
        r"^.+ gets \+(\d+)/\+(\d+) for each other creature you control\.$"
    )
    _ALLIANCE_THIS_UNTIL_EOT = re.compile(
        r"^Alliance — Whenever another creature you control enters, this creature gets "
        r"\+(\d+)/\+(\d+) until end of turn\.$"
    )
    _SNEAK_ETB_TEAM_UNTIL_EOT = re.compile(
        r"^When .+ enters, if (?:his|her|its) sneak cost was paid, creatures you control get "
        r"\+(\d+)/\+(\d+) until end of turn\.$"
    )
    _ATTACK_OTHER_ATTACKERS_UNTIL_EOT = re.compile(
        r"^Whenever .+ attacks, each other attacking creature gets "
        r"\+(\d+)/\+(\d+) until end of turn\.$"
    )
    _CANT_BE_BLOCKED_BY_POWER_OR_GREATER = re.compile(
        r"^.+ can't be blocked by creatures with power (\d+) or greater\.$"
    )
    _CANT_BE_BLOCKED_BY_GREATER_POWER = re.compile(
        r"^This creature can't be blocked by creatures with greater power\.$"
    )
    _ALLIANCE_TARGET_PLUS_COUNTER = re.compile(
        r"^Alliance — Whenever another creature you control enters, put "
        r"(?:a|one|([0-9]+)) \+1/\+1 counters? on target creature you control\.$"
    )
    _GAIN_LIFE_SELF_PLUS_COUNTER = re.compile(
        r"^Whenever you gain life, put a \+1/\+1 counter on .+\.$"
    )
    _ALLIANCE_MODAL_HEADER = re.compile(
        r"^Alliance — Whenever another creature you control enters, choose one that hasn't "
        r"been chosen this turn\.$"
    )
    _SELF_PLUS_COUNTER_MODE = re.compile(r"^• Put a \+1/\+1 counter on .+\.$")

    def log(self, event: str, **details: object) -> None:
        self.events.append({"turn": self.turn, "phase": self.phase, "event": event, **details})

    def unsupported(
        self, card: CardFact, reason: str, *, player_index: int, oracle_fragment: str
    ) -> None:
        player = self.players[player_index]
        message = f"{card.name}: {oracle_fragment}: {reason}"
        self.limitations.add(message)
        self.log(
            "unsupported_semantics",
            card=card.name,
            oracle_fragment=oracle_fragment,
            player=player.name,
            reason=reason,
        )

    @staticmethod
    def oracle_fragments(card: CardFact) -> list[str]:
        return [line.strip() for line in card.oracle_text.splitlines() if line.strip()]

    def supports_pt_fragment(self, fragment: str) -> bool:
        return any(
            pattern.fullmatch(fragment)
            for pattern in (
                self._STATIC_OTHER_CREATURES,
                self._ALLIANCE_THIS_UNTIL_EOT,
                self._SNEAK_ETB_TEAM_UNTIL_EOT,
                self._ATTACK_OTHER_ATTACKERS_UNTIL_EOT,
            )
        )

    def supports_blocking_fragment(self, fragment: str) -> bool:
        return any(
            pattern.fullmatch(fragment)
            for pattern in (
                self._CANT_BE_BLOCKED_BY_POWER_OR_GREATER,
                self._CANT_BE_BLOCKED_BY_GREATER_POWER,
            )
        )

    def supports_counter_fragment(self, card: CardFact, fragment: str) -> bool:
        if self._ALLIANCE_MODAL_HEADER.fullmatch(fragment):
            return any(
                self._SELF_PLUS_COUNTER_MODE.fullmatch(candidate)
                for candidate in self.oracle_fragments(card)
            )
        return any(
            pattern.fullmatch(fragment)
            for pattern in (
                self._ALLIANCE_TARGET_PLUS_COUNTER,
                self._GAIN_LIFE_SELF_PLUS_COUNTER,
                self._SELF_PLUS_COUNTER_MODE,
            )
        )

    def report_unsupported_abilities(self, player_index: int, card: CardFact) -> None:
        """Report each unresolved Oracle line without interpreting or combining its meaning."""
        fragments = self.oracle_fragments(card)
        for keyword in sorted(set(card.keywords) - {"Haste"}):
            if not any(re.search(rf"\b{re.escape(keyword)}\b", line, re.I) for line in fragments):
                self.unsupported(
                    card,
                    "keyword_not_implemented",
                    player_index=player_index,
                    oracle_fragment=keyword,
                )
        for fragment in fragments:
            if (
                fragment.casefold() == "haste"
                or self.supports_pt_fragment(fragment)
                or self.supports_blocking_fragment(fragment)
                or self.supports_counter_fragment(card, fragment)
            ):
                continue
            self.unsupported(
                card,
                "oracle_ability_not_implemented",
                player_index=player_index,
                oracle_fragment=fragment,
            )

    def place_counters(
        self,
        target: Permanent,
        counter_type: str,
        quantity: int,
        *,
        source_card: str,
        oracle_fragment: str,
    ) -> None:
        if not counter_type or not isinstance(quantity, int) or isinstance(quantity, bool):
            raise ValueError("counter placement requires a named counter and integer quantity")
        if quantity <= 0:
            raise ValueError("counter placement quantity must be positive")
        if not any(
            candidate is target for player in self.players for candidate in player.battlefield
        ):
            raise ValueError("counter target must be a battlefield permanent")
        target.counters[counter_type] = target.counters.get(counter_type, 0) + quantity
        self.log(
            "counters_placed",
            target=target.card.name,
            counter_type=counter_type,
            quantity=quantity,
            total=target.counters[counter_type],
            source=source_card,
            oracle_fragment=oracle_fragment,
        )
        self.check_state_based_actions()

    def resolve_creature_entered_counter_effects(self, entering: Permanent) -> None:
        controller = entering.controller
        sources = list(self.players[controller].battlefield)
        for source in sources:
            if source is entering:
                continue
            fragments = self.oracle_fragments(source.card)
            for fragment in fragments:
                match = self._ALLIANCE_TARGET_PLUS_COUNTER.fullmatch(fragment)
                if match:
                    candidates = tuple(
                        permanent
                        for permanent in self.players[controller].battlefield
                        if permanent.card.is_creature
                    )
                    target = self.counter_target_chooser(controller, source, candidates)
                    if not any(candidate is target for candidate in candidates):
                        raise ValueError("counter target chooser must return a listed creature")
                    quantity = int(match.group(1) or 1)
                    self.place_counters(
                        target,
                        "+1/+1",
                        quantity,
                        source_card=source.card.name,
                        oracle_fragment=fragment,
                    )
            if not any(self._ALLIANCE_MODAL_HEADER.fullmatch(x) for x in fragments):
                continue
            modes = tuple(fragment for fragment in fragments if fragment.startswith("• "))
            chosen = self.alliance_modes_chosen.setdefault(id(source), set())
            available = tuple(mode for mode in modes if mode not in chosen)
            if not available:
                self.log("alliance_no_available_mode", source=source.card.name)
                continue
            mode = self.alliance_mode_chooser(controller, source, available)
            if mode not in available:
                raise ValueError("Alliance mode chooser must return an available mode")
            chosen.add(mode)
            if self._SELF_PLUS_COUNTER_MODE.fullmatch(mode):
                self.place_counters(
                    source,
                    "+1/+1",
                    1,
                    source_card=source.card.name,
                    oracle_fragment=mode,
                )
            else:
                self.log(
                    "alliance_mode_not_executed",
                    source=source.card.name,
                    oracle_fragment=mode,
                    reason="chosen_mode_semantics_not_implemented",
                )

    def gain_life(
        self, player_index: int, amount: int, *, source_card: str, oracle_fragment: str
    ) -> None:
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("life gain amount must be a positive integer")
        player = self.players[player_index]
        player.life += amount
        self.log(
            "life_gained",
            player=player.name,
            amount=amount,
            source=source_card,
            oracle_fragment=oracle_fragment,
        )
        for permanent in list(player.battlefield):
            for fragment in self.oracle_fragments(permanent.card):
                if self._GAIN_LIFE_SELF_PLUS_COUNTER.fullmatch(fragment):
                    self.place_counters(
                        permanent,
                        "+1/+1",
                        1,
                        source_card=permanent.card.name,
                        oracle_fragment=fragment,
                    )

    def apply_pt_modifier(
        self,
        target: Permanent,
        power: int,
        toughness: int,
        *,
        duration: Literal["persistent", "until_end_of_turn"],
        source_card: str,
        oracle_fragment: str,
        derived_static: bool = False,
        log_event: bool = True,
    ) -> None:
        target.pt_modifiers.append(
            PowerToughnessModifier(
                power=power,
                toughness=toughness,
                duration=duration,
                source_card=source_card,
                oracle_fragment=oracle_fragment,
                created_turn=self.turn,
                derived_static=derived_static,
            )
        )
        if log_event:
            self.log(
                "pt_modifier_applied",
                target=target.card.name,
                source=source_card,
                power=power,
                toughness=toughness,
                duration=duration,
                oracle_fragment=oracle_fragment,
            )

    def refresh_static_pt_modifiers(self) -> None:
        previous: dict[int, tuple[int, int]] = {}
        for player in self.players:
            for permanent in player.battlefield:
                previous[id(permanent)] = (
                    sum(x.power for x in permanent.pt_modifiers if x.derived_static),
                    sum(x.toughness for x in permanent.pt_modifiers if x.derived_static),
                )
                permanent.pt_modifiers = [
                    modifier for modifier in permanent.pt_modifiers if not modifier.derived_static
                ]
        for player in self.players:
            creatures = [
                permanent for permanent in player.battlefield if permanent.card.is_creature
            ]
            for source in creatures:
                for fragment in self.oracle_fragments(source.card):
                    match = self._STATIC_OTHER_CREATURES.fullmatch(fragment)
                    if match:
                        count = len(creatures) - 1
                        self.apply_pt_modifier(
                            source,
                            int(match.group(1)) * count,
                            int(match.group(2)) * count,
                            duration="persistent",
                            source_card=source.card.name,
                            oracle_fragment=fragment,
                            derived_static=True,
                            log_event=False,
                        )
                        current = (
                            int(match.group(1)) * count,
                            int(match.group(2)) * count,
                        )
                        if previous.get(id(source), (0, 0)) != current:
                            self.log(
                                "pt_static_modifier_refreshed",
                                target=source.card.name,
                                source=source.card.name,
                                power=current[0],
                                toughness=current[1],
                                oracle_fragment=fragment,
                            )

    def resolve_creature_entered_pt_effects(self, entering: Permanent) -> None:
        for fragment in self.oracle_fragments(entering.card):
            match = self._SNEAK_ETB_TEAM_UNTIL_EOT.fullmatch(fragment)
            if match:
                self.log(
                    "pt_effect_condition_not_met",
                    source=entering.card.name,
                    condition="sneak_cost_paid",
                    oracle_fragment=fragment,
                )
        for source in list(self.players[entering.controller].battlefield):
            if source is entering:
                continue
            for fragment in self.oracle_fragments(source.card):
                match = self._ALLIANCE_THIS_UNTIL_EOT.fullmatch(fragment)
                if match:
                    self.apply_pt_modifier(
                        source,
                        int(match.group(1)),
                        int(match.group(2)),
                        duration="until_end_of_turn",
                        source_card=source.card.name,
                        oracle_fragment=fragment,
                    )

    def resolve_attack_pt_effects(self, attackers: list[Permanent]) -> None:
        for source in attackers:
            for fragment in self.oracle_fragments(source.card):
                match = self._ATTACK_OTHER_ATTACKERS_UNTIL_EOT.fullmatch(fragment)
                if not match:
                    continue
                for target in attackers:
                    if target is not source:
                        self.apply_pt_modifier(
                            target,
                            int(match.group(1)),
                            int(match.group(2)),
                            duration="until_end_of_turn",
                            source_card=source.card.name,
                            oracle_fragment=fragment,
                        )

    def draw(self, player: PlayerState, count: int = 1, *, setup: bool = False) -> bool:
        for _ in range(count):
            if not player.library:
                player.lost = True
                player.loss_reason = "draw_from_empty_library"
                self.winner = 1 - self.players.index(player)
                self.log("player_lost", player=player.name, reason=player.loss_reason)
                return False
            player.hand.append(player.library.pop())
            self.log("card_drawn", player=player.name, setup=setup)
        return True

    def begin_turn(self) -> None:
        self.turn += 1
        self.active_player = (self.turn - 1) % 2
        player = self.players[self.active_player]
        self.phase = "beginning"
        player.lands_played = 0
        for permanent in player.battlefield:
            permanent.tapped = False
            permanent.summoning_sick = False
            permanent.damage = 0
        self.log("turn_started", player=player.name)
        if not (self.turn == 1 and self.active_player == 0):
            self.draw(player)
        else:
            self.log("draw_skipped", player=player.name, reason="starting_player_first_turn")
        self.phase = "precombat_main"

    def play_land(self, player_index: int, card: CardFact) -> bool:
        player = self.players[player_index]
        if player_index != self.active_player or "main" not in self.phase:
            return False
        if not card.is_land or card not in player.hand or player.lands_played >= 1:
            return False
        player.hand.remove(card)
        player.battlefield.append(Permanent(card, player_index, summoning_sick=False))
        self.refresh_static_pt_modifiers()
        player.lands_played += 1
        self.log("land_played", player=player.name, card=card.name)
        return True

    def available_mana(self, player_index: int) -> tuple[int, str]:
        lands = [
            p for p in self.players[player_index].battlefield if p.card.is_land and not p.tapped
        ]
        color = "W" if any(p.card.name == "Plains" for p in lands) else "R"
        return len(lands), color

    def can_afford(self, player_index: int, card: CardFact) -> bool:
        available, color = self.available_mana(player_index)
        colored = re.findall(r"\{([WUBRG])\}", card.mana_cost)
        return available >= card.mana_value and all(symbol == color for symbol in colored)

    def _pay(self, player_index: int, amount: int) -> None:
        lands = [
            p for p in self.players[player_index].battlefield if p.card.is_land and not p.tapped
        ]
        for land in lands[:amount]:
            land.tapped = True

    def cast(self, player_index: int, card: CardFact, target: Permanent | None = None) -> bool:
        player = self.players[player_index]
        if (
            player_index != self.active_player
            or card not in player.hand
            or not self.can_afford(player_index, card)
        ):
            return False
        if card.name == "Manhole Missile":
            if target is None or target.controller == player_index:
                self.log(
                    "dead_interaction", player=player.name, card=card.name, reason="no_legal_target"
                )
                return False
            self._pay(player_index, card.mana_value)
            player.hand.remove(card)
            player.graveyard.append(card)
            target.damage += 3
            self.log("spell_resolved", player=player.name, card=card.name, target=target.card.name)
            self.check_state_based_actions()
            return True
        if card.name == "Make Your Move":
            if target is None or target.controller == player_index or target.power < 4:
                self.log(
                    "dead_interaction", player=player.name, card=card.name, reason="no_legal_target"
                )
                return False
            self._pay(player_index, card.mana_value)
            player.hand.remove(card)
            player.graveyard.append(card)
            self.destroy(target)
            self.log("spell_resolved", player=player.name, card=card.name, target=target.card.name)
            return True
        if card.is_creature and card.power is not None and card.toughness is not None:
            self._pay(player_index, card.mana_value)
            player.hand.remove(card)
            haste = "Haste" in card.keywords
            permanent = Permanent(card, player_index, summoning_sick=not haste)
            player.battlefield.append(permanent)
            self.log("creature_resolved", player=player.name, card=card.name)
            self.refresh_static_pt_modifiers()
            self.resolve_creature_entered_pt_effects(permanent)
            self.resolve_creature_entered_counter_effects(permanent)
            self.report_unsupported_abilities(player_index, card)
            self.check_state_based_actions()
            return True
        fragments = [line.strip() for line in card.oracle_text.splitlines() if line.strip()]
        for fragment in fragments or [card.type_line]:
            self.unsupported(
                card,
                "spell_or_permanent_semantics_not_implemented",
                player_index=player_index,
                oracle_fragment=fragment,
            )
        return False

    def legal_attackers(self, player_index: int) -> list[Permanent]:
        return [
            p
            for p in self.players[player_index].battlefield
            if p.card.is_creature and not p.tapped and not p.summoning_sick
        ]

    def blocking_restriction(
        self, attacker: Permanent, blocker: Permanent
    ) -> tuple[str, str] | None:
        """Return the first Oracle-derived restriction that makes this block illegal."""
        for fragment in self.oracle_fragments(attacker.card):
            match = self._CANT_BE_BLOCKED_BY_POWER_OR_GREATER.fullmatch(fragment)
            if match and blocker.power >= int(match.group(1)):
                return fragment, "blocker_power_at_or_above_restriction"
            if (
                self._CANT_BE_BLOCKED_BY_GREATER_POWER.fullmatch(fragment)
                and blocker.power > attacker.power
            ):
                return fragment, "blocker_power_greater_than_attacker"
        return None

    def can_block(self, attacker: Permanent, blocker: Permanent, defender_index: int) -> bool:
        return (
            blocker.controller == defender_index
            and any(candidate is blocker for candidate in self.players[defender_index].battlefield)
            and blocker.card.is_creature
            and not blocker.tapped
            and self.blocking_restriction(attacker, blocker) is None
        )

    def generate_blocks(
        self, attackers: list[Permanent], defender_index: int
    ) -> dict[int, Permanent]:
        """Generate deterministic one-to-one blocks using the same legality as validation."""
        available = [
            permanent
            for permanent in self.players[defender_index].battlefield
            if permanent.card.is_creature and not permanent.tapped
        ]
        blocks: dict[int, Permanent] = {}
        for attacker in attackers:
            for blocker in available:
                restriction = self.blocking_restriction(attacker, blocker)
                if restriction is not None:
                    fragment, reason = restriction
                    self.log(
                        "block_candidate_rejected",
                        attacker=attacker.card.name,
                        blocker=blocker.card.name,
                        oracle_fragment=fragment,
                        reason=reason,
                        attacker_power=attacker.power,
                        blocker_power=blocker.power,
                    )
                    continue
                blocks[id(attacker)] = blocker
                available.remove(blocker)
                break
        return blocks

    def combat(
        self,
        attackers: list[Permanent],
        blocks: dict[int, Permanent] | None = None,
        *,
        auto_assign_blockers: bool = False,
    ) -> None:
        self.phase = "combat"
        defender_index = 1 - self.active_player
        legal = self.legal_attackers(self.active_player)
        if any(attacker not in legal for attacker in attackers):
            raise ValueError("illegal attacker")
        for attacker in attackers:
            attacker.tapped = True
        self.resolve_attack_pt_effects(attackers)
        if auto_assign_blockers:
            if blocks is not None:
                raise ValueError("cannot provide blocks when auto-assigning blockers")
            blocks = self.generate_blocks(attackers, defender_index)
        else:
            blocks = blocks or {}
        attacker_ids = {id(attacker) for attacker in attackers}
        if any(attacker_id not in attacker_ids for attacker_id in blocks):
            raise ValueError("block assigned to a nonattacker")
        used_blockers: set[int] = set()
        for attacker in attackers:
            blocker = blocks.get(id(attacker))
            if blocker is None:
                self.players[defender_index].life -= attacker.power
                self.log("combat_damage_player", source=attacker.card.name, damage=attacker.power)
            else:
                if id(blocker) in used_blockers or not self.can_block(
                    attacker, blocker, defender_index
                ):
                    raise ValueError("illegal blocker")
                used_blockers.add(id(blocker))
                blocker.damage += attacker.power
                attacker.damage += blocker.power
                self.log(
                    "combat_damage_creatures",
                    attacker=attacker.card.name,
                    blocker=blocker.card.name,
                )
        self.check_state_based_actions()
        self.check_life()
        self.phase = "postcombat_main"

    def end_turn(self) -> None:
        player = self.players[self.active_player]
        self.phase = "cleanup"
        expired = 0
        for current in self.players:
            for permanent in current.battlefield:
                before = len(permanent.pt_modifiers)
                permanent.pt_modifiers = [
                    modifier
                    for modifier in permanent.pt_modifiers
                    if modifier.duration != "until_end_of_turn"
                ]
                expired += before - len(permanent.pt_modifiers)
                permanent.damage = 0
        self.refresh_static_pt_modifiers()
        self.alliance_modes_chosen.clear()
        self.log("cleanup_completed", expired_pt_modifiers=expired)
        self.check_state_based_actions()
        self.phase = "ending"
        self.log("turn_ended", player=player.name)

    def put_into_graveyard(
        self, permanent: Permanent, *, state_based_action: str | None = None
    ) -> None:
        owner = self.players[permanent.controller]
        owner.battlefield.remove(permanent)
        self.alliance_modes_chosen.pop(id(permanent), None)
        owner.graveyard.append(permanent.card)
        self.refresh_static_pt_modifiers()
        self.log(
            "permanent_to_graveyard",
            player=owner.name,
            card=permanent.card.name,
            state_based_action=state_based_action,
        )

    def destroy(self, permanent: Permanent, *, state_based_action: str | None = None) -> None:
        self.put_into_graveyard(permanent, state_based_action=state_based_action)

    def check_state_based_actions(self) -> None:
        self.refresh_static_pt_modifiers()
        while True:
            changed = False
            for action in self.state_based_actions:
                if action.apply(self):
                    changed = True
                    self.refresh_static_pt_modifiers()
            if not changed:
                break
        self.check_invariants()

    def check_invariants(self) -> None:
        for player_index, player in enumerate(self.players):
            legendary_names: set[str] = set()
            for permanent in player.battlefield:
                if permanent.controller != player_index:
                    raise AssertionError("battlefield controller does not match player zone")
                if permanent.card.is_creature:
                    if permanent.card.power is None or permanent.card.toughness is None:
                        raise AssertionError("creature permanent lacks printed power/toughness")
                    if permanent.toughness <= 0:
                        raise AssertionError("nonpositive toughness must be handled by an SBA")
                invalid_counters = any(
                    not isinstance(counter_type, str)
                    or not counter_type
                    or not isinstance(value, int)
                    or isinstance(value, bool)
                    or value <= 0
                    for counter_type, value in permanent.counters.items()
                )
                if invalid_counters:
                    raise AssertionError("counter quantities must be nonnegative integers")
                for modifier in permanent.pt_modifiers:
                    if modifier.duration not in {"persistent", "until_end_of_turn"}:
                        raise AssertionError("unknown P/T modifier duration")
                    if modifier.created_turn > self.turn:
                        raise AssertionError("P/T modifier originates in a future turn")
                if "Legendary" in permanent.card.type_line:
                    if permanent.card.name in legendary_names:
                        raise AssertionError("legend rule left duplicate names on battlefield")
                    legendary_names.add(permanent.card.name)

    def check_life(self) -> None:
        for index, player in enumerate(self.players):
            if player.life <= 0:
                player.lost = True
                player.loss_reason = "life_zero_or_less"
                self.winner = 1 - index
                self.log("player_lost", player=player.name, reason=player.loss_reason)

    def snapshot(self) -> dict[str, object]:
        return {
            "engine_version": ENGINE_VERSION,
            "turn": self.turn,
            "active_player": self.players[self.active_player].name,
            "phase": self.phase,
            "winner": None if self.winner is None else self.players[self.winner].name,
            "players": [
                {
                    "name": p.name,
                    "life": p.life,
                    "library": len(p.library),
                    "hand": [c.name for c in p.hand],
                    "battlefield": [asdict(x) for x in p.battlefield],
                    "graveyard": [c.name for c in p.graveyard],
                    "lost": p.lost,
                    "loss_reason": p.loss_reason,
                }
                for p in self.players
            ],
            "limitations": sorted(self.limitations),
            "events": self.events,
        }


def load_facts(path: Path) -> dict[str, CardFact]:
    rows = json.loads(path.read_text(encoding="utf-8"))["cards"]
    facts = {}
    for name, row in rows.items():
        power, toughness = ACCEPTANCE_CREATURE_STATS.get(name, (None, None))
        facts[name] = CardFact(
            name=name,
            mana_cost=row["mana_cost"],
            mana_value=int(row["mana_value"]),
            type_line=row["type_line"],
            oracle_text=row.get("oracle_text", ""),
            power=power,
            toughness=toughness,
            keywords=tuple(row.get("keywords", [])),
        )
    return facts


def load_deck(path: Path, facts: dict[str, CardFact]) -> list[CardFact]:
    cards: list[CardFact] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line == "Deck":
            continue
        quantity, name = line.split(" ", 1)
        cards.extend([facts[name]] * int(quantity))
    if len(cards) != 60:
        raise ValueError(f"{path}: expected 60 cards, found {len(cards)}")
    return cards
