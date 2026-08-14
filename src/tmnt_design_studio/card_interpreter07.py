"""Pure Oracle-to-rules-construct interpretation for Cardcade Engine 0.8b."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class CardDefinition(Protocol):
    name: str
    oracle_text: str
    type_line: str
    power: int | None
    toughness: int | None
    keywords: tuple[str, ...]

    @property
    def is_creature(self) -> bool: ...


class CastKind(Enum):
    CREATURE = "creature"
    DAMAGE_3_OPPOSING_CREATURE = "damage_3_opposing_creature"
    DESTROY_OPPOSING_POWER_4 = "destroy_opposing_power_4"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class CastProgram:
    kind: CastKind


class CardInterpreter:
    """Derive reusable executable constructs without legality, mutation, or strategy."""

    STATIC_OTHER_CREATURES = re.compile(
        r"^.+ gets \+(\d+)/\+(\d+) for each other creature you control\.$"
    )
    ALLIANCE_THIS_UNTIL_EOT = re.compile(
        r"^Alliance — Whenever another creature you control enters, this creature gets "
        r"\+(\d+)/\+(\d+) until end of turn\.$"
    )
    SNEAK_ETB_TEAM_UNTIL_EOT = re.compile(
        r"^When .+ enters, if (?:his|her|its) sneak cost was paid, creatures you control get "
        r"\+(\d+)/\+(\d+) until end of turn\.$"
    )
    ATTACK_OTHER_ATTACKERS_UNTIL_EOT = re.compile(
        r"^Whenever .+ attacks, each other attacking creature gets "
        r"\+(\d+)/\+(\d+) until end of turn\.$"
    )
    CANT_BE_BLOCKED_BY_POWER_OR_GREATER = re.compile(
        r"^.+ can't be blocked by creatures with power (\d+) or greater\.$"
    )
    CANT_BE_BLOCKED_BY_GREATER_POWER = re.compile(
        r"^This creature can't be blocked by creatures with greater power\.$"
    )
    ALLIANCE_TARGET_PLUS_COUNTER = re.compile(
        r"^Alliance — Whenever another creature you control enters, put "
        r"(?:a|one|([0-9]+)) \+1/\+1 counters? on target creature you control\.$"
    )
    GAIN_LIFE_SELF_PLUS_COUNTER = re.compile(
        r"^Whenever you gain life, put a \+1/\+1 counter on .+\.$"
    )
    ALLIANCE_MODAL_HEADER = re.compile(
        r"^Alliance — Whenever another creature you control enters, choose one that hasn't "
        r"been chosen this turn\.$"
    )
    SELF_PLUS_COUNTER_MODE = re.compile(r"^• Put a \+1/\+1 counter on .+\.$")
    DAMAGE_3_TARGET_CREATURE = re.compile(r"^.+ deals 3 damage to target creature\.")
    DESTROY_ARTIFACT_ENCHANTMENT_OR_POWER_4_CREATURE = re.compile(
        r"^Destroy target artifact, enchantment, or creature with power 4 or greater\.$"
    )

    def cast_program(self, card: CardDefinition) -> CastProgram:
        if self.DAMAGE_3_TARGET_CREATURE.match(card.oracle_text):
            return CastProgram(CastKind.DAMAGE_3_OPPOSING_CREATURE)
        if self.DESTROY_ARTIFACT_ENCHANTMENT_OR_POWER_4_CREATURE.fullmatch(card.oracle_text):
            return CastProgram(CastKind.DESTROY_OPPOSING_POWER_4)
        if card.is_creature and card.power is not None and card.toughness is not None:
            return CastProgram(CastKind.CREATURE)
        return CastProgram(CastKind.UNSUPPORTED)

    @staticmethod
    def fragments(card: CardDefinition) -> tuple[str, ...]:
        return tuple(line.strip() for line in card.oracle_text.splitlines() if line.strip())

    def supports_pt_fragment(self, fragment: str) -> bool:
        return any(
            pattern.fullmatch(fragment)
            for pattern in (
                self.STATIC_OTHER_CREATURES,
                self.ALLIANCE_THIS_UNTIL_EOT,
                self.SNEAK_ETB_TEAM_UNTIL_EOT,
                self.ATTACK_OTHER_ATTACKERS_UNTIL_EOT,
            )
        )

    def supports_blocking_fragment(self, fragment: str) -> bool:
        return any(
            pattern.fullmatch(fragment)
            for pattern in (
                self.CANT_BE_BLOCKED_BY_POWER_OR_GREATER,
                self.CANT_BE_BLOCKED_BY_GREATER_POWER,
            )
        )

    def supports_counter_fragment(self, card: CardDefinition, fragment: str) -> bool:
        if self.ALLIANCE_MODAL_HEADER.fullmatch(fragment):
            return any(
                self.SELF_PLUS_COUNTER_MODE.fullmatch(candidate)
                for candidate in self.fragments(card)
            )
        return any(
            pattern.fullmatch(fragment)
            for pattern in (
                self.ALLIANCE_TARGET_PLUS_COUNTER,
                self.GAIN_LIFE_SELF_PLUS_COUNTER,
                self.SELF_PLUS_COUNTER_MODE,
            )
        )

    def unsupported_fragments(self, card: CardDefinition) -> tuple[tuple[str, str], ...]:
        fragments = self.fragments(card)
        unsupported: list[tuple[str, str]] = []
        for keyword in sorted(set(card.keywords) - {"Haste"}):
            if not any(re.search(rf"\b{re.escape(keyword)}\b", line, re.I) for line in fragments):
                unsupported.append((keyword, "keyword_not_implemented"))
        for fragment in fragments:
            if (
                fragment.casefold() == "haste"
                or self.supports_pt_fragment(fragment)
                or self.supports_blocking_fragment(fragment)
                or self.supports_counter_fragment(card, fragment)
            ):
                continue
            unsupported.append((fragment, "oracle_ability_not_implemented"))
        return tuple(unsupported)
