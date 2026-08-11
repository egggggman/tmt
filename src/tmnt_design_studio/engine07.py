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

ENGINE_VERSION = "cardcade-0.7.0-alpha.1"

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
class Permanent:
    card: CardFact
    controller: int
    tapped: bool = False
    summoning_sick: bool = True
    damage: int = 0

    @property
    def power(self) -> int:
        assert self.card.power is not None
        return self.card.power

    @property
    def toughness(self) -> int:
        assert self.card.toughness is not None
        return self.card.toughness


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


class Game:
    """Two-player deterministic game state and the supported legal transitions."""

    def __init__(self, decks: tuple[list[CardFact], list[CardFact]], names=("A", "B"), seed=1):
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
        for player in self.players:
            self.draw(player, 7, setup=True)
        self.log("game_started", seed=seed, starting_player=names[0])

    def log(self, event: str, **details: object) -> None:
        self.events.append({"turn": self.turn, "phase": self.phase, "event": event, **details})

    def unsupported(self, card: CardFact, reason: str) -> None:
        message = f"{card.name}: {reason}"
        self.limitations.add(message)
        self.log("unsupported_semantics", card=card.name, reason=reason)

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
            if "Legendary" in card.type_line and any(
                p.card.name == card.name for p in player.battlefield
            ):
                self.unsupported(
                    card, "legend rule choice is not implemented; duplicate cast skipped"
                )
                return False
            self._pay(player_index, card.mana_value)
            player.hand.remove(card)
            haste = "Haste" in card.keywords
            player.battlefield.append(Permanent(card, player_index, summoning_sick=not haste))
            self.log("creature_resolved", player=player.name, card=card.name)
            unsupported = set(card.keywords) - {"Haste"}
            if unsupported or card.oracle_text:
                self.unsupported(card, "non-foundation abilities do not resolve")
            return True
        self.unsupported(card, "spell/permanent semantics not implemented")
        return False

    def legal_attackers(self, player_index: int) -> list[Permanent]:
        return [
            p
            for p in self.players[player_index].battlefield
            if p.card.is_creature and not p.tapped and not p.summoning_sick
        ]

    def combat(
        self, attackers: list[Permanent], blocks: dict[int, Permanent] | None = None
    ) -> None:
        self.phase = "combat"
        defender_index = 1 - self.active_player
        blocks = blocks or {}
        legal = self.legal_attackers(self.active_player)
        if any(attacker not in legal for attacker in attackers):
            raise ValueError("illegal attacker")
        used_blockers: set[int] = set()
        for attacker in attackers:
            attacker.tapped = True
            blocker = blocks.get(id(attacker))
            if blocker is None:
                self.players[defender_index].life -= attacker.power
                self.log("combat_damage_player", source=attacker.card.name, damage=attacker.power)
            else:
                if (
                    blocker.controller != defender_index
                    or blocker.tapped
                    or id(blocker) in used_blockers
                    or not blocker.card.is_creature
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

    def destroy(self, permanent: Permanent) -> None:
        owner = self.players[permanent.controller]
        owner.battlefield.remove(permanent)
        owner.graveyard.append(permanent.card)
        self.log("permanent_to_graveyard", player=owner.name, card=permanent.card.name)

    def check_state_based_actions(self) -> None:
        for player in self.players:
            for permanent in list(player.battlefield):
                if permanent.card.is_creature and permanent.damage >= permanent.toughness:
                    self.destroy(permanent)

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
