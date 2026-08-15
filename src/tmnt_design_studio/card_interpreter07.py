"""Pure Oracle-to-rules-construct interpretation for Cardcade Engine 0.8b."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from tmnt_design_studio.semantic_coverage import SemanticCoverage


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
    DEAL_DAMAGE = "deal_damage"
    DESTROY_OPPOSING_POWER_4 = "destroy_opposing_power_4"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class CastProgram:
    kind: CastKind


class DamageTargetKind(Enum):
    """The bounded recipient classes represented by Deal Damage."""

    PLAYER = "player"
    CREATURE = "creature"


@dataclass(frozen=True)
class DamageProgram:
    """One Oracle-derived damage payload, independent of delivery and mutation."""

    amount: int | None
    target_kind: DamageTargetKind | None
    target_scope: str | None
    unsupported_reason: str | None = None
    retained_limitation: str | None = None
    additional_limitation: str | None = None

    @property
    def executable(self) -> bool:
        return (
            self.amount is not None
            and self.amount > 0
            and self.target_kind is not None
            and self.target_scope in {"target_opponent", "each_opponent", "you", "target_creature"}
            and self.unsupported_reason is None
            and self.additional_limitation is None
        )


@dataclass(frozen=True)
class InterpretedDamageSemantics:
    """An Action-specific damage program paired with generic coverage evidence."""

    program: DamageProgram
    coverage: SemanticCoverage
    parent_limitation: str | None = None

    @property
    def limitations(self) -> tuple[str, ...]:
        return self.coverage.limitations


@dataclass(frozen=True)
class ScryProgram:
    """One Oracle-derived fixed-number Scry payload."""

    amount: int | None
    unsupported_reason: str | None = None

    @property
    def executable(self) -> bool:
        return self.amount is not None and self.amount > 0 and self.unsupported_reason is None


@dataclass(frozen=True)
class InterpretedScrySemantics:
    """An Action-specific Scry program paired with generic coverage evidence."""

    program: ScryProgram
    coverage: SemanticCoverage
    parent_limitation: str | None = None

    @property
    def limitations(self) -> tuple[str, ...]:
        return self.coverage.limitations


class StrikeKeyword(Enum):
    FIRST_STRIKE = "first_strike"
    DOUBLE_STRIKE = "double_strike"


class StrikeApplicability(Enum):
    SELF = "self"
    SELF_DURING_CONTROLLER_TURN = "self_during_controller_turn"
    ATTACKING_CREATURES_YOU_CONTROL = "attacking_creatures_you_control"


@dataclass(frozen=True)
class StrikeProgram:
    """One Oracle-derived First/Double Strike payload, separate from delivery."""

    keyword: StrikeKeyword
    applicability: StrikeApplicability | None

    @property
    def executable(self) -> bool:
        return True


@dataclass(frozen=True)
class InterpretedStrikeSemantics:
    """An Action-specific strike program paired with generic coverage evidence."""

    program: StrikeProgram
    coverage: SemanticCoverage
    parent_limitation: str | None = None

    @property
    def limitations(self) -> tuple[str, ...]:
        return self.coverage.limitations


@dataclass(frozen=True)
class TokenDefinition:
    """Immutable characteristics for one Oracle-derived token kind."""

    name: str
    type_line: str
    colors: tuple[str, ...] = ()
    power: int | None = None
    toughness: int | None = None
    oracle_text: str = ""
    keywords: tuple[str, ...] = ()
    mana_cost: str = ""
    mana_value: int = 0

    @property
    def is_land(self) -> bool:
        return "Land" in self.type_line

    @property
    def is_creature(self) -> bool:
        return "Creature" in self.type_line


@dataclass(frozen=True)
class TokenCreationProgram:
    """One recognized token-creation instruction, executable only when fully bounded."""

    definition: TokenDefinition | None
    quantity: int | None
    tapped: bool = False
    unsupported_reason: str | None = None
    retained_limitation: str | None = None

    @property
    def executable(self) -> bool:
        return (
            self.definition is not None
            and self.quantity is not None
            and self.quantity > 0
            and self.unsupported_reason is None
        )


@dataclass(frozen=True)
class InterpretedTokenSemantics:
    """An Action-specific token program paired with Action-agnostic coverage evidence."""

    program: TokenCreationProgram
    coverage: SemanticCoverage
    parent_limitation: str | None = None

    @property
    def payload_executable(self) -> bool:
        return self.coverage.payload_executable

    @property
    def parent_executable(self) -> bool:
        return self.coverage.parent_executable

    @property
    def followup_executable(self) -> bool:
        return self.coverage.followup_executable

    @property
    def fully_supported(self) -> bool:
        return self.coverage.fully_supported

    @property
    def limitations(self) -> tuple[str, ...]:
        return self.coverage.limitations


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
    DEAL_DAMAGE = re.compile(
        r"\bdeals? (?:(?P<amount>[0-9]+|X|that much) damage|damage equal to "
        r"(?P<dynamic_amount>.+?)) to (?P<target>target opponent, creature an opponent "
        r"controls, or planeswalker an opponent controls|each of (?:one or two|up to [0-9]+) "
        r"targets|each opponent|target opponent|you|that player|target player|target attacking "
        r"or blocking creature|target creature(?: an opponent controls)?|each creature|"
        r"each non-Wall creature|any target|any other target|one or two targets|"
        r"each of those creatures)\b",
        re.IGNORECASE,
    )
    SCRY = re.compile(r"\bscry (?P<amount>[0-9]+|X|that many)\b", re.IGNORECASE)
    STRIKE_KEYWORD = re.compile(r"\b(?P<keyword>first strike|double strike)\b", re.IGNORECASE)
    DESTROY_ARTIFACT_ENCHANTMENT_OR_POWER_4_CREATURE = re.compile(
        r"^Destroy target artifact, enchantment, or creature with power 4 or greater\.$"
    )
    CREATE_TOKEN = re.compile(
        r"\bcreates? (?P<quantity>a|an|one|two|three|four|five|[0-9]+|x|that many|"
        r"a number of|one or more) (?P<body>.*?\btokens?)\b",
        re.IGNORECASE,
    )
    EXPLICIT_CREATURE_TOKEN = re.compile(
        r"(?P<power>[0-9]+)/(?P<toughness>[0-9]+)\s+"
        r"(?P<descriptor>.+?)\s+creature tokens?\b",
        re.IGNORECASE,
    )
    TOKEN_COLORS = {
        "white": "W",
        "blue": "U",
        "black": "B",
        "red": "R",
        "green": "G",
    }
    TOKEN_QUANTITIES = {
        "a": 1,
        "an": 1,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
    }
    PREDEFINED_TOKENS = {
        "food": TokenDefinition(
            "Food",
            "Artifact — Food",
            oracle_text="{2}, {T}, Sacrifice this token: You gain 3 life.",
        ),
        "mutagen": TokenDefinition(
            "Mutagen",
            "Artifact — Mutagen",
            oracle_text=(
                "{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature. "
                "Activate only as a sorcery."
            ),
        ),
        "treasure": TokenDefinition(
            "Treasure",
            "Artifact — Treasure",
            oracle_text="{T}, Sacrifice this token: Add one mana of any color.",
        ),
        "clue": TokenDefinition(
            "Clue",
            "Artifact — Clue",
            oracle_text="{2}, Sacrifice this token: Draw a card.",
        ),
    }

    def cast_program(self, card: CardDefinition) -> CastProgram:
        if self.DAMAGE_3_TARGET_CREATURE.match(card.oracle_text):
            return CastProgram(CastKind.DAMAGE_3_OPPOSING_CREATURE)
        damage = self.damage_semantic_coverage(card, card.oracle_text)
        if (
            damage is not None
            and damage.coverage.payload_executable
            and damage.coverage.parent_executable
            and damage.program.target_kind is DamageTargetKind.CREATURE
        ):
            return CastProgram(CastKind.DEAL_DAMAGE)
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

    def token_creation_program(self, fragment: str) -> TokenCreationProgram | None:
        """Recognize reusable token creation without dispatching on a source card name."""
        match = self.CREATE_TOKEN.search(fragment)
        if match is None:
            return None
        quantity_text = match.group("quantity").casefold()
        quantity = self.TOKEN_QUANTITIES.get(quantity_text)
        if quantity is None and quantity_text.isdecimal():
            quantity = int(quantity_text)
        variable_quantity = quantity is None or bool(
            re.search(
                r"\b(?:for each|equal to|twice that many|where X|that many)\b", fragment, re.I
            )
        )
        if re.search(
            r"\btoken(?:s)? (?:that are|that's|that is) (?:a )?cop(?:y|ies)\b", fragment, re.I
        ):
            return TokenCreationProgram(
                None, quantity, unsupported_reason="token_copy_not_implemented"
            )
        if re.search(r"\bwould create\b|\binstead\b", fragment, re.I):
            return TokenCreationProgram(
                None,
                quantity,
                unsupported_reason="token_replacement_effect_not_implemented",
            )

        body = match.group("body")
        definition = next(
            (
                token
                for name, token in self.PREDEFINED_TOKENS.items()
                if re.search(rf"\b{re.escape(name)} tokens?\b", body, re.I)
            ),
            None,
        )
        explicit = self.EXPLICIT_CREATURE_TOKEN.search(body)
        if definition is None and explicit is not None:
            descriptor = explicit.group("descriptor").split()
            colors: list[str] = []
            if descriptor and descriptor[0].casefold() == "colorless":
                descriptor.pop(0)
            while descriptor and descriptor[0].casefold() in self.TOKEN_COLORS:
                colors.append(self.TOKEN_COLORS[descriptor.pop(0).casefold()])
            artifact = any(word.casefold() == "artifact" for word in descriptor)
            descriptor = [word for word in descriptor if word.casefold() != "artifact"]
            token_name = " ".join(descriptor) or "Creature"
            type_line = f"{'Artifact ' if artifact else ''}Creature"
            if descriptor:
                type_line += f" — {token_name}"
            keywords = tuple(
                keyword
                for keyword in ("Flying", "Haste", "Vigilance", "Trample", "Menace")
                if re.search(rf"\bwith {keyword.casefold()}\b", fragment, re.I)
            )
            definition = TokenDefinition(
                token_name,
                type_line,
                tuple(colors),
                int(explicit.group("power")),
                int(explicit.group("toughness")),
                keywords=keywords,
            )

        unsupported_reason = None
        if definition is None:
            unsupported_reason = "token_characteristics_not_safely_derived"
        elif variable_quantity:
            unsupported_reason = "variable_token_quantity_not_implemented"
        elif re.search(r"\b(?:tapped and attacking|attacking that player)\b", fragment, re.I):
            unsupported_reason = "token_attacking_context_not_implemented"

        tapped = bool(re.search(r"\b(?:create|enters?)\b[^.]*\btapped\b", fragment, re.I))
        retained_limitation = None
        if definition is not None and definition.oracle_text:
            retained_limitation = "token_activated_ability_not_implemented"
        elif re.search(
            r"\b(?:attach (?:this|that)|destroy it|sacrifice it|gains? haste until end of turn|"
            r"then if|and put)\b",
            fragment[match.end() :],
            re.I,
        ):
            retained_limitation = "token_followup_semantics_not_implemented"
        return TokenCreationProgram(
            definition,
            quantity,
            tapped=tapped,
            unsupported_reason=unsupported_reason,
            retained_limitation=retained_limitation,
        )

    def damage_program(self, fragment: str) -> DamageProgram | None:
        """Recognize damage payloads without confusing damage with adjacent outcomes."""
        match = self.DEAL_DAMAGE.search(fragment)
        if match is None:
            return None
        amount_text = (match.group("amount") or match.group("dynamic_amount")).casefold()
        amount = int(amount_text) if amount_text.isdecimal() else None
        target_text = match.group("target").casefold()
        target_kind = None
        target_scope = None
        amount_limitation = "dynamic_damage_amount_not_implemented" if amount is None else None
        targeting_limitation = None
        if target_text in {"target opponent", "each opponent", "you"}:
            target_kind = DamageTargetKind.PLAYER
            target_scope = target_text.replace(" ", "_")
        elif target_text in {"that player", "target player"}:
            target_kind = DamageTargetKind.PLAYER
            target_scope = target_text.replace(" ", "_")
            targeting_limitation = "damage_referential_player_not_implemented"
        elif target_text in {
            "target creature",
            "target creature an opponent controls",
            "target attacking or blocking creature",
        }:
            target_kind = DamageTargetKind.CREATURE
            target_scope = "target_creature"
            if target_text == "target attacking or blocking creature":
                targeting_limitation = "damage_target_combat_status_not_implemented"
        elif target_text in {
            "each creature",
            "each non-wall creature",
            "one or two targets",
            "each of those creatures",
        }:
            targeting_limitation = "multiple_damage_targets_not_implemented"
        elif re.fullmatch(r"each of (?:one or two|up to [0-9]+) targets", target_text):
            targeting_limitation = "variable_count_multiple_damage_targets_not_implemented"
        elif target_text.startswith("target opponent,"):
            targeting_limitation = "damage_multi_kind_target_not_implemented"
        else:
            targeting_limitation = "damage_any_target_not_implemented"

        suffix = fragment[match.end() :]
        retained = None
        if suffix.strip(" .") or re.search(
            r"\b(?:if that creature would die|then|and [^.]*(?:draw|create|put|destroy|"
            r"exile|sacrifice))\b",
            suffix,
            re.I,
        ):
            retained = "damage_followup_semantics_not_implemented"
        unsupported_reason = amount_limitation or targeting_limitation
        additional_limitation = (
            targeting_limitation if amount_limitation and targeting_limitation else None
        )
        return DamageProgram(
            amount,
            target_kind,
            target_scope,
            unsupported_reason,
            retained,
            additional_limitation,
        )

    def damage_semantic_coverage(
        self, card: CardDefinition, fragment: str
    ) -> InterpretedDamageSemantics | None:
        """Classify a damage payload separately from its parent and follow-up."""
        program = self.damage_program(fragment)
        if program is None:
            return None
        match = self.DEAL_DAMAGE.search(fragment)
        assert match is not None
        prefix = fragment[: match.start()]
        alliance = bool(
            re.match(r"^Alliance — Whenever another creature you control enters,", fragment)
        )
        direct_spell = not prefix.strip() or bool(
            re.match(r"^(?:• )?[^,.]+ deals?\b", fragment, re.I)
        )
        if alliance:
            parent_executable = True
            parent_limitation = None
        elif fragment.startswith("• "):
            parent_executable = False
            parent_limitation = "damage_choice_context_not_implemented"
        elif re.match(r"^(?:When|Whenever|At )", fragment, re.I):
            parent_executable = False
            parent_limitation = "damage_trigger_context_not_implemented"
        elif ":" in prefix:
            parent_executable = False
            parent_limitation = "damage_activation_context_not_implemented"
        elif direct_spell:
            parent_executable = True
            parent_limitation = None
        else:
            parent_executable = False
            parent_limitation = "damage_preceding_effect_not_implemented"
        limitations = tuple(
            dict.fromkeys(
                reason
                for reason in (
                    program.unsupported_reason,
                    program.additional_limitation,
                    parent_limitation,
                    program.retained_limitation,
                )
                if reason is not None
            )
        )
        coverage = SemanticCoverage(
            program.executable,
            parent_executable,
            program.retained_limitation is None,
            limitations,
        )
        return InterpretedDamageSemantics(program, coverage, parent_limitation)

    def scry_program(self, fragment: str) -> ScryProgram | None:
        """Recognize only explicit Oracle Scry instructions, never similar library actions."""
        match = self.SCRY.search(fragment)
        if match is None:
            return None
        amount_text = match.group("amount").casefold()
        if not amount_text.isdecimal():
            return ScryProgram(None, "dynamic_scry_amount_not_implemented")
        amount = int(amount_text)
        if amount <= 0:
            return ScryProgram(amount, "scry_zero_not_represented")
        return ScryProgram(amount)

    def scry_semantic_coverage(
        self, card: CardDefinition, fragment: str
    ) -> InterpretedScrySemantics | None:
        """Keep the Scry payload distinct from delivery and surrounding instructions."""
        program = self.scry_program(fragment)
        if program is None:
            return None
        match = self.SCRY.search(fragment)
        assert match is not None
        fragments = self.fragments(card)
        alliance_mode = fragment.startswith("• ") and any(
            self.ALLIANCE_MODAL_HEADER.fullmatch(candidate) for candidate in fragments
        )
        direct_creature_etb = "Creature" in card.type_line and bool(
            re.match(r"^When .+ enters, scry\b", fragment, re.I)
        )
        prefix = fragment[: match.start()]
        if alliance_mode or direct_creature_etb:
            parent_executable = True
            parent_limitation = None
        elif re.search(r"\bif\b", prefix, re.I):
            parent_executable = False
            parent_limitation = "scry_condition_context_not_implemented"
        elif re.search(r"(?:^|\.\s+)(?:When|Whenever|At)\b", prefix, re.I):
            parent_executable = False
            parent_limitation = "scry_preceding_or_trigger_context_not_implemented"
        elif ":" in prefix:
            parent_executable = False
            parent_limitation = "scry_activation_context_not_implemented"
        elif re.match(r"^(?:When|Whenever|At |Disappear)", fragment, re.I):
            parent_executable = False
            parent_limitation = "scry_preceding_or_trigger_context_not_implemented"
        elif fragment.startswith("• "):
            parent_executable = False
            parent_limitation = "scry_choice_context_not_implemented"
        elif prefix.strip():
            parent_executable = False
            parent_limitation = "scry_preceding_effect_not_implemented"
        else:
            parent_executable = True
            parent_limitation = None

        suffix = fragment[match.end() :]
        suffix_without_reminder = re.sub(
            r"^\.?(?:\s*\((?:Look at|You may put)[\s\S]*\))?\.?$", "", suffix, flags=re.I
        )
        followup_limitation = (
            "scry_followup_semantics_not_implemented" if suffix_without_reminder.strip() else None
        )
        limitations = tuple(
            reason
            for reason in (
                program.unsupported_reason,
                parent_limitation,
                followup_limitation,
            )
            if reason is not None
        )
        coverage = SemanticCoverage(
            program.executable,
            parent_executable,
            followup_limitation is None,
            limitations,
        )
        return InterpretedScrySemantics(program, coverage, parent_limitation)

    def strike_program(self, fragment: str) -> StrikeProgram | None:
        """Recognize First/Double Strike without treating its parent as executable."""
        match = self.STRIKE_KEYWORD.search(fragment)
        if match is None:
            return None
        keyword = (
            StrikeKeyword.FIRST_STRIKE
            if match.group("keyword").casefold() == "first strike"
            else StrikeKeyword.DOUBLE_STRIKE
        )
        reminder = r"(?:\s*\([^)]*\))?\.?"
        if re.fullmatch(rf"{match.group('keyword')}{reminder}", fragment, re.I):
            applicability = StrikeApplicability.SELF
        elif re.fullmatch(
            rf"During your turn, this creature has {match.group('keyword')}\.", fragment, re.I
        ):
            applicability = StrikeApplicability.SELF_DURING_CONTROLLER_TURN
        elif re.fullmatch(
            rf"Attacking creatures you control have {match.group('keyword')}\.", fragment, re.I
        ):
            applicability = StrikeApplicability.ATTACKING_CREATURES_YOU_CONTROL
        else:
            applicability = None
        return StrikeProgram(keyword, applicability)

    def strike_semantic_coverage(
        self, card: CardDefinition, fragment: str
    ) -> InterpretedStrikeSemantics | None:
        """Keep combat-step mechanics separate from grants and surrounding semantics."""
        program = self.strike_program(fragment)
        if program is None:
            return None
        match = self.STRIKE_KEYWORD.search(fragment)
        assert match is not None
        if program.applicability is not None:
            parent_executable = True
            parent_limitation = None
        elif re.search(r"\bEquipped creature\b", fragment, re.I):
            parent_executable = False
            parent_limitation = "strike_attachment_context_not_implemented"
        elif ":" in fragment[: match.start()]:
            parent_executable = False
            parent_limitation = "strike_activation_context_not_implemented"
        elif re.match(r"^(?:When|Whenever|At )", fragment, re.I):
            parent_executable = False
            parent_limitation = "strike_trigger_context_not_implemented"
        elif re.match(r"^(?:Choose one|•|Target )", fragment, re.I):
            parent_executable = False
            parent_limitation = "strike_temporary_grant_context_not_implemented"
        else:
            parent_executable = False
            parent_limitation = "strike_parent_context_not_implemented"

        suffix = fragment[match.end() :]
        suffix_without_reminder_or_duration = re.sub(
            r"^(?: until end of turn)?\.?(?:\s*\([^)]*\))?\.?$", "", suffix, flags=re.I
        )
        followup_limitation = (
            "strike_followup_semantics_not_implemented"
            if suffix_without_reminder_or_duration.strip()
            else None
        )
        limitations = tuple(
            reason for reason in (parent_limitation, followup_limitation) if reason is not None
        )
        coverage = SemanticCoverage(
            program.executable,
            parent_executable,
            followup_limitation is None,
            limitations,
        )
        return InterpretedStrikeSemantics(program, coverage, parent_limitation)

    def token_semantic_coverage(
        self, card: CardDefinition, fragment: str
    ) -> InterpretedTokenSemantics | None:
        """Keep a bounded child payload separate from its delivery and follow-up semantics."""
        program = self.token_creation_program(fragment)
        if program is None:
            return None

        match = self.CREATE_TOKEN.search(fragment)
        assert match is not None
        fragments = self.fragments(card)
        alliance_mode = fragment.startswith("• ") and any(
            self.ALLIANCE_MODAL_HEADER.fullmatch(candidate) for candidate in fragments
        )
        source_is_creature = "Creature" in card.type_line
        direct_creature_etb = source_is_creature and bool(
            re.match(
                r"^(?:When|Whenever) .+ enters(?: or attacks)?, (?:you )?creates?\b",
                fragment,
                re.I,
            )
        )
        direct_creature_attack = source_is_creature and bool(
            re.match(
                r"^Whenever .+ (?:attacks|enters or attacks), (?:you )?creates?\b",
                fragment,
                re.I,
            )
        )
        if alliance_mode or direct_creature_etb or direct_creature_attack:
            return self._token_semantics(program, True)

        prefix = fragment[: match.start()]
        if re.match(
            r"^Starting with you, each player may .+ Repeat this process until ",
            fragment,
            re.I,
        ):
            reason = "token_iterative_choice_context_unknown"
        elif re.search(r"\bif\b", prefix, re.I):
            reason = "token_condition_context_not_implemented"
        elif re.match(r"^(?:When|Whenever|At |Disappear|Raid|Investigate)", fragment, re.I):
            reason = "token_trigger_context_not_implemented"
        elif ":" in prefix:
            reason = "token_activation_context_not_implemented"
        elif fragment.startswith("• "):
            reason = "token_choice_context_not_implemented"
        elif prefix.strip():
            reason = "token_preceding_effect_not_implemented"
        else:
            reason = "token_spell_context_not_implemented"
        return self._token_semantics(program, False, reason)

    @staticmethod
    def _token_semantics(
        program: TokenCreationProgram,
        parent_executable: bool,
        parent_limitation: str | None = None,
    ) -> InterpretedTokenSemantics:
        limitations = tuple(
            dict.fromkeys(
                reason
                for reason in (
                    program.unsupported_reason,
                    parent_limitation,
                    program.retained_limitation,
                )
                if reason is not None
            )
        )
        coverage = SemanticCoverage(
            payload_executable=program.executable,
            parent_executable=parent_executable,
            followup_executable=program.retained_limitation is None,
            limitations=limitations,
        )
        return InterpretedTokenSemantics(program, coverage, parent_limitation)

    def unsupported_fragments(self, card: CardDefinition) -> tuple[tuple[str, str], ...]:
        fragments = self.fragments(card)
        unsupported: list[tuple[str, str]] = []
        for keyword in sorted(set(card.keywords) - {"Haste"}):
            if not any(re.search(rf"\b{re.escape(keyword)}\b", line, re.I) for line in fragments):
                unsupported.append((keyword, "keyword_not_implemented"))
        for fragment in fragments:
            token_coverage = self.token_semantic_coverage(card, fragment)
            if token_coverage is not None:
                for reason in token_coverage.limitations:
                    unsupported.append((fragment, reason))
                continue
            damage_coverage = self.damage_semantic_coverage(card, fragment)
            if damage_coverage is not None:
                for reason in damage_coverage.limitations:
                    unsupported.append((fragment, reason))
                if damage_coverage.coverage.fully_supported:
                    continue
                if not damage_coverage.limitations:
                    unsupported.append((fragment, "damage_semantics_not_implemented"))
                continue
            scry_coverage = self.scry_semantic_coverage(card, fragment)
            if scry_coverage is not None:
                for reason in scry_coverage.limitations:
                    unsupported.append((fragment, reason))
                continue
            strike_coverage = self.strike_semantic_coverage(card, fragment)
            if strike_coverage is not None:
                for reason in strike_coverage.limitations:
                    unsupported.append((fragment, reason))
                continue
            if (
                fragment.casefold() == "haste"
                or self.supports_pt_fragment(fragment)
                or self.supports_blocking_fragment(fragment)
                or self.supports_counter_fragment(card, fragment)
            ):
                continue
            unsupported.append((fragment, "oracle_ability_not_implemented"))
        return tuple(unsupported)
