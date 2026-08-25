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


@dataclass(frozen=True)
class SneakProgram:
    """One Oracle-derived bounded Sneak alternative-cost instruction."""

    mana_cost: str | None
    creature_spell: bool
    direct_keyword_ability: bool
    fixed_supported_cost: bool

    @property
    def executable(self) -> bool:
        return (
            self.mana_cost is not None
            and self.creature_spell
            and self.direct_keyword_ability
            and self.fixed_supported_cost
        )


@dataclass(frozen=True)
class InterpretedSneakSemantics:
    """Sneak-specific facts paired with Action-generic coverage evidence."""

    program: SneakProgram
    coverage: SemanticCoverage

    @property
    def limitations(self) -> tuple[str, ...]:
        return self.coverage.limitations


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
class ReturnToHandProgram:
    """One Oracle-derived return payload, independent of delivery and mutation."""

    another_target_creature_you_control: bool
    destination_owners_hand: bool

    @property
    def executable(self) -> bool:
        return self.another_target_creature_you_control and self.destination_owners_hand


@dataclass(frozen=True)
class ReturnClause:
    """The authoritative textual boundary of one recognized Return instruction."""

    text: str
    start: int
    end: int
    preceding_text: str
    following_text: str


@dataclass(frozen=True)
class InterpretedReturnToHandSemantics:
    """Return payload facts paired with Action-generic semantic coverage."""

    program: ReturnToHandProgram
    coverage: SemanticCoverage
    clause: ReturnClause
    preceding_semantics: str
    following_semantics: str
    preceding_executable: bool
    followup_executable: bool

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
class TrampleProgram:
    """One Oracle-derived Trample characteristic, separate from combat mutation."""

    self_static: bool
    deathtouch_modified: bool = False

    @property
    def executable(self) -> bool:
        return self.self_static and not self.deathtouch_modified


@dataclass(frozen=True)
class InterpretedTrampleSemantics:
    """A Trample program paired with Action-generic semantic coverage."""

    program: TrampleProgram
    coverage: SemanticCoverage
    parent_limitation: str | None = None

    @property
    def limitations(self) -> tuple[str, ...]:
        return self.coverage.limitations


@dataclass(frozen=True)
class LifelinkProgram:
    """One Oracle-derived intrinsic Lifelink characteristic."""

    self_static: bool

    @property
    def executable(self) -> bool:
        return self.self_static


@dataclass(frozen=True)
class InterpretedLifelinkSemantics:
    """A Lifelink program paired with Action-generic semantic coverage."""

    program: LifelinkProgram
    coverage: SemanticCoverage
    parent_limitation: str | None = None

    @property
    def limitations(self) -> tuple[str, ...]:
        return self.coverage.limitations


@dataclass(frozen=True)
class HandBottomDrawProgram:
    """One bounded optional Hand -> Library-bottom move followed by fixed Draw."""

    hand_quantity: int | None
    draw_quantity: int | None
    optional: bool
    draw_conditional_on_move: bool
    unsupported_reason: str | None = None

    @property
    def executable(self) -> bool:
        return (
            self.hand_quantity == 1
            and self.draw_quantity == 1
            and self.optional
            and self.draw_conditional_on_move
            and self.unsupported_reason is None
        )


@dataclass(frozen=True)
class InterpretedHandBottomDrawSemantics:
    """Action-specific filter/Draw facts paired with generic semantic coverage."""

    program: HandBottomDrawProgram
    coverage: SemanticCoverage
    clause_text: str
    clause_start: int
    clause_end: int
    parent_limitation: str | None = None

    @property
    def limitations(self) -> tuple[str, ...]:
        return self.coverage.limitations


@dataclass(frozen=True)
class DiscardDrawProgram:
    """One bounded optional Hand -> Graveyard move followed by fixed Draw."""

    discard_quantity: int | None
    draw_quantity: int | None
    optional: bool
    draw_conditional_on_discard: bool

    @property
    def executable(self) -> bool:
        return (
            self.discard_quantity == 1
            and self.draw_quantity == 1
            and self.optional
            and self.draw_conditional_on_discard
        )


@dataclass(frozen=True)
class InterpretedDiscardDrawSemantics:
    """Discard/Draw facts paired with Action-generic semantic coverage."""

    program: DiscardDrawProgram
    coverage: SemanticCoverage
    clause_text: str
    clause_start: int
    clause_end: int

    @property
    def limitations(self) -> tuple[str, ...]:
        return self.coverage.limitations


@dataclass(frozen=True)
class ActivationCostProgram:
    """Oracle-derived activation costs, before authoritative payment."""

    mana_cost: str
    tap_source: bool
    sacrifice_source: bool
    executable: bool
    limitations: tuple[str, ...] = ()


class ActivatedEffectKind(Enum):
    GRANT_SELF_FIRST_STRIKE_UNTIL_EOT = "grant_self_first_strike_until_eot"
    RETURN_ANOTHER_CREATURE_YOU_CONTROL_TO_OWNERS_HAND = (
        "return_another_creature_you_control_to_owners_hand"
    )
    GAIN_THREE_LIFE = "gain_three_life"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ActivatedAbilityProgram:
    """One activated ability, separate from engine legality and mutation."""

    cost_text: str
    effect_text: str
    cost: ActivationCostProgram
    effect_kind: ActivatedEffectKind
    target_count: int
    choices_required: bool
    activation_instructions: str | None = None


@dataclass(frozen=True)
class InterpretedActivatedAbilitySemantics:
    """Action-specific activation facts paired with generic coverage evidence."""

    program: ActivatedAbilityProgram
    coverage: SemanticCoverage
    activation_recognized: bool
    activation_parent_executable: bool
    costs_executable: bool
    targets_choices_executable: bool
    child_payload_executable: bool
    followup_executable: bool

    @property
    def limitations(self) -> tuple[str, ...]:
        return self.coverage.limitations


@dataclass(frozen=True)
class InterpretedFoodActivationSemantics:
    """Canonical Food activation paired with Action-generic coverage."""

    program: ActivatedAbilityProgram
    coverage: SemanticCoverage
    clause_text: str

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
    TRAMPLE_KEYWORD = re.compile(r"\btrample\b", re.IGNORECASE)
    LIFELINK_KEYWORD = re.compile(r"\blifelink\b", re.IGNORECASE)
    HAND_BOTTOM_DRAW = re.compile(
        r"(?P<clause>You may put a card from your hand on the bottom of your library\. "
        r"If you do, draw a card\.)",
        re.IGNORECASE,
    )
    DISCARD_DRAW = re.compile(
        r"(?P<clause>you may discard a card\. If you do, draw a card\.)",
        re.IGNORECASE,
    )
    DIES_DRAW_ONE = re.compile(
        r"^When this creature dies, draw a card\.$",
        re.IGNORECASE,
    )
    ETB_DRAIN_GAIN_SCRY_ONE = re.compile(
        r"^When (?P<source>this creature|[^,]+) enters, each opponent loses 1 life "
        r"and you gain 1 life\. Scry 1\."
        r"(?: \(Look at the top card of your library\. You may put that card on the bottom\.\))?$",
        re.IGNORECASE,
    )
    ETB_ARTIFACT_DRAW_ONE = re.compile(
        r"^When (?P<source>this source|[^,]+) enters, if "
        r"(?P<condition>its controller controls|you control) an artifact, draw a card\.$",
        re.IGNORECASE,
    )
    ANOTHER_PERMANENT_LEFT_SELF_COUNTER = re.compile(
        r"^Whenever another permanent leaves the battlefield, put a \+1/\+1 counter on "
        r"(?P<source>[^.]+)\.$",
        re.IGNORECASE,
    )
    STATIC_KEYWORD_NAMES = frozenset(
        {
            "deathtouch",
            "double strike",
            "first strike",
            "flying",
            "haste",
            "hexproof",
            "indestructible",
            "lifelink",
            "menace",
            "reach",
            "trample",
            "vigilance",
        }
    )
    PERMANENT_CARD_TYPES = frozenset(
        {"Artifact", "Battle", "Creature", "Enchantment", "Land", "Planeswalker"}
    )
    ACTIVATION_MANA_SYMBOL = re.compile(r"\{(?:[0-9]+|[WUBRG])\}", re.IGNORECASE)
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
    CANONICAL_FOOD_ACTIVATION = "{2}, {T}, Sacrifice this token: You gain 3 life."
    FOOD_ACTIVATION = re.compile(r"\{2\}, \{T\}, Sacrifice this token: You gain 3 life\.", re.I)

    @classmethod
    def _is_canonical_food_source(cls, card: CardDefinition) -> bool:
        """Identify the canonical Food subtype and ability without source-card dispatch."""
        return bool(
            "Food" in card.type_line.split(" — ")[-1].split()
            and cls.FOOD_ACTIVATION.fullmatch(card.oracle_text.strip())
        )

    SNEAK_ABILITY = re.compile(r"^Sneak (?P<cost>(?:\{[^}]+\})+)(?:\s|$)", re.I)
    FIXED_SNEAK_COST = re.compile(r"^(?:\{(?:\d+|[WUBRG])\})+$")

    def sneak_semantic_coverage(
        self, card: CardDefinition, fragment: str
    ) -> InterpretedSneakSemantics | None:
        """Recognize Sneak references while bounding execution to fixed-cost creatures."""
        if not re.search(r"\bsneak\b", fragment, re.I):
            return None
        match = self.SNEAK_ABILITY.match(fragment)
        mana_cost = None if match is None else match.group("cost")
        direct = match is not None
        creature = "Creature" in card.type_line
        fixed = mana_cost is not None and self.FIXED_SNEAK_COST.fullmatch(mana_cost) is not None
        program = SneakProgram(mana_cost, creature, direct, fixed)
        limitations: list[str] = []
        if not direct:
            limitations.append("sneak_reference_or_granted_ability_not_implemented")
        elif not fixed:
            limitations.append("sneak_cost_shape_not_implemented")
        elif not creature:
            limitations.append("sneak_noncreature_spell_not_implemented")
        coverage = SemanticCoverage(
            payload_executable=program.executable,
            parent_executable=program.executable,
            followup_executable=program.executable,
            limitations=tuple(limitations),
        )
        return InterpretedSneakSemantics(program, coverage)

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

    def dies_draw_semantic_coverage(
        self, card: CardDefinition, fragment: str
    ) -> SemanticCoverage | None:
        """Recognize only the bounded self-death trigger whose complete effect is Draw one."""
        if self.DIES_DRAW_ONE.fullmatch(fragment) is None:
            return None
        creature_source = "Creature" in card.type_line
        return SemanticCoverage(
            payload_executable=creature_source,
            parent_executable=creature_source,
            followup_executable=creature_source,
            limitations=(() if creature_source else ("dies_draw_source_is_not_a_creature",)),
        )

    def etb_drain_gain_scry_semantic_coverage(
        self, card: CardDefinition, fragment: str
    ) -> SemanticCoverage | None:
        """Recognize only the bounded self-ETB drain/gain followed by Scry one."""
        match = self.ETB_DRAIN_GAIN_SCRY_ONE.fullmatch(fragment)
        if match is None:
            return None
        source_text = match.group("source")
        self_reference = source_text.casefold() == "this creature" or (
            source_text.casefold() == card.name.casefold()
        )
        creature_source = "Creature" in card.type_line
        executable = self_reference and creature_source
        limitations = tuple(
            reason
            for condition, reason in (
                (self_reference, "etb_drain_gain_scry_source_mismatch"),
                (creature_source, "etb_drain_gain_scry_source_is_not_a_creature"),
            )
            if not condition
        )
        return SemanticCoverage(executable, executable, executable, limitations)

    def permanent_left_self_counter_semantic_coverage(
        self, card: CardDefinition, fragment: str
    ) -> SemanticCoverage | None:
        """Recognize only another-permanent departure followed by one self +1/+1 counter."""
        match = self.ANOTHER_PERMANENT_LEFT_SELF_COUNTER.fullmatch(fragment)
        if match is None:
            return None
        source_text = match.group("source")
        if source_text.casefold() == "this permanent":
            return None
        self_reference = source_text.casefold() == "this source" or (
            source_text.casefold() == card.name.casefold()
        )
        permanent_source = any(
            re.search(rf"\b{card_type}\b", card.type_line)
            for card_type in self.PERMANENT_CARD_TYPES
        )
        executable = self_reference and permanent_source
        limitations = tuple(
            reason
            for condition, reason in (
                (self_reference, "permanent_left_counter_source_mismatch"),
                (permanent_source, "permanent_left_counter_source_is_not_a_permanent"),
            )
            if not condition
        )
        return SemanticCoverage(
            executable,
            executable,
            executable,
            limitations,
        )

    def etb_artifact_draw_semantic_coverage(
        self, card: CardDefinition, fragment: str
    ) -> SemanticCoverage | None:
        """Recognize one self-ETB intervening-if artifact condition followed by Draw one."""
        match = self.ETB_ARTIFACT_DRAW_ONE.fullmatch(fragment)
        if match is None:
            return None
        source_text = match.group("source")
        condition_text = match.group("condition").casefold()
        generic_form = (
            source_text.casefold() == "this source" and condition_text == "its controller controls"
        )
        source_names = {card.name.casefold(), card.name.split(",", 1)[0].casefold()}
        printed_form = source_text.casefold() in source_names and condition_text == "you control"
        self_reference = generic_form or printed_form
        creature_source = "Creature" in card.type_line
        executable = self_reference and creature_source
        limitations = tuple(
            reason
            for condition, reason in (
                (self_reference, "etb_artifact_draw_source_or_condition_mismatch"),
                (creature_source, "etb_artifact_draw_source_is_not_a_creature"),
            )
            if not condition
        )
        return SemanticCoverage(executable, executable, executable, limitations)

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
        if (
            definition is not None
            and definition.oracle_text
            and not self._is_canonical_food_source(definition)
        ):
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
        hand_bottom_draw = self.HAND_BOTTOM_DRAW.fullmatch(suffix.strip().lstrip(". "))
        if hand_bottom_draw is None and (
            suffix.strip(" .")
            or re.search(
                r"\b(?:if that creature would die|then|and [^.]*(?:draw|create|put|destroy|"
                r"exile|sacrifice))\b",
                suffix,
                re.I,
            )
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

    def hand_bottom_draw_semantic_coverage(
        self, card: CardDefinition, fragment: str
    ) -> InterpretedHandBottomDrawSemantics | None:
        """Recognize one optional Hand-bottom move with its dependent fixed Draw."""
        del card
        match = self.HAND_BOTTOM_DRAW.search(fragment)
        if match is None:
            return None
        prefix = fragment[: match.start()].strip()
        suffix = fragment[match.end() :].strip()
        parent_executable = False
        parent_limitation = None
        if prefix:
            damage = self.damage_program(prefix)
            if damage is not None and damage.executable:
                parent_executable = True
            else:
                parent_limitation = "hand_bottom_draw_parent_context_not_implemented"
        else:
            parent_executable = True
        followup_limitation = (
            "hand_bottom_draw_followup_semantics_not_implemented" if suffix else None
        )
        program = HandBottomDrawProgram(1, 1, True, True)
        limitations = tuple(
            reason for reason in (parent_limitation, followup_limitation) if reason is not None
        )
        return InterpretedHandBottomDrawSemantics(
            program,
            SemanticCoverage(
                payload_executable=program.executable,
                parent_executable=parent_executable,
                followup_executable=followup_limitation is None,
                limitations=limitations,
            ),
            match.group("clause"),
            match.start(),
            match.end(),
            parent_limitation,
        )

    def discard_draw_semantic_coverage(
        self, card: CardDefinition, fragment: str
    ) -> InterpretedDiscardDrawSemantics | None:
        """Recognize the bounded optional discard/conditional Draw instruction."""
        match = self.DISCARD_DRAW.search(fragment)
        if match is None:
            return None
        prefix = fragment[: match.start()]
        suffix = fragment[match.end() :]
        source_names = {card.name, card.name.split(",", 1)[0]}
        self_reference = (
            "(?:"
            + "|".join(
                [
                    "this creature",
                    *(re.escape(name) for name in sorted(source_names, key=len, reverse=True)),
                ]
            )
            + ")"
        )
        parent_executable = bool(
            re.fullmatch(rf"Whenever {self_reference} attacks,\s*", prefix, re.IGNORECASE)
        )
        parent_limitation = (
            None if parent_executable else "discard_draw_attack_trigger_context_not_implemented"
        )
        followup_executable = not suffix.strip()
        followup_limitation = (
            None if followup_executable else "discard_draw_followup_semantics_not_implemented"
        )
        program = DiscardDrawProgram(1, 1, True, True)
        limitations = tuple(
            reason for reason in (parent_limitation, followup_limitation) if reason is not None
        )
        return InterpretedDiscardDrawSemantics(
            program,
            SemanticCoverage(
                payload_executable=program.executable,
                parent_executable=parent_executable,
                followup_executable=followup_executable,
                limitations=limitations,
            ),
            match.group("clause"),
            match.start(),
            match.end(),
        )

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

    def trample_semantic_coverage(
        self, card: CardDefinition, fragment: str
    ) -> InterpretedTrampleSemantics | None:
        """Recognize Trample while keeping grants and parent delivery unsupported."""
        del card
        match = self.TRAMPLE_KEYWORD.search(fragment)
        if match is None:
            return None
        reminder = re.sub(r"\s*\([^)]*\)\.?$", "", fragment).strip().rstrip(".")
        keyword_parts = tuple(
            part.strip().casefold() for part in re.split(r",\s*(?:and\s+)?|\s+and\s+", reminder)
        )
        self_static = "trample" in keyword_parts and all(
            part in self.STATIC_KEYWORD_NAMES for part in keyword_parts
        )
        deathtouch_modified = self_static and "deathtouch" in keyword_parts
        if self_static:
            parent_limitation = None
        elif re.search(r"\bEquipped creature\b|\benchanted creature\b", fragment, re.I):
            parent_limitation = "trample_attachment_context_not_implemented"
        elif ":" in fragment[: match.start()]:
            parent_limitation = "trample_activation_context_not_implemented"
        elif re.match(r"^(?:When|Whenever|At |Alliance)", fragment, re.I):
            parent_limitation = "trample_trigger_context_not_implemented"
        elif re.match(r"^(?:Choose one|•|Target )", fragment, re.I):
            parent_limitation = "trample_choice_or_grant_context_not_implemented"
        else:
            parent_limitation = "trample_parent_context_not_implemented"
        unsupported_companions = tuple(
            part for part in keyword_parts if part not in {"trample", "haste"}
        )
        followup_limitation = (
            "trample_followup_semantics_not_implemented" if unsupported_companions else None
        )
        limitations = tuple(
            reason
            for reason in (
                "trample_deathtouch_lethal_not_implemented" if deathtouch_modified else None,
                parent_limitation,
                followup_limitation,
            )
            if reason is not None
        )
        program = TrampleProgram(self_static, deathtouch_modified)
        return InterpretedTrampleSemantics(
            program,
            SemanticCoverage(
                program.executable,
                self_static,
                followup_limitation is None,
                limitations,
            ),
            parent_limitation,
        )

    def lifelink_semantic_coverage(
        self, card: CardDefinition, fragment: str
    ) -> InterpretedLifelinkSemantics | None:
        """Recognize intrinsic Lifelink without upgrading grants or attachments."""
        del card
        match = self.LIFELINK_KEYWORD.search(fragment)
        if match is None:
            return None
        reminder = re.sub(r"\s*\([^)]*\)\.?$", "", fragment).strip().rstrip(".")
        keyword_parts = tuple(
            part.strip().casefold() for part in re.split(r",\s*(?:and\s+)?|\s+and\s+", reminder)
        )
        self_static = keyword_parts == ("lifelink",)
        if self_static:
            parent_limitation = None
        elif re.search(r"\bEquipped creature\b|\benchanted creature\b", fragment, re.I):
            parent_limitation = "lifelink_attachment_context_not_implemented"
        elif ":" in fragment[: match.start()]:
            parent_limitation = "lifelink_activation_context_not_implemented"
        elif re.match(r"^(?:When|Whenever|At |Alliance|[IVX]+\s+[—-])", fragment, re.I):
            parent_limitation = "lifelink_trigger_context_not_implemented"
        elif re.search(r"\b(?:gains?|has)\b", fragment[: match.start()], re.I):
            parent_limitation = "lifelink_grant_context_not_implemented"
        else:
            parent_limitation = "lifelink_parent_context_not_implemented"
        followup_limitation = None if self_static else "lifelink_compound_semantics_not_implemented"
        limitations = tuple(
            reason for reason in (parent_limitation, followup_limitation) if reason is not None
        )
        program = LifelinkProgram(self_static)
        return InterpretedLifelinkSemantics(
            program,
            SemanticCoverage(
                payload_executable=program.executable,
                parent_executable=self_static,
                followup_executable=followup_limitation is None,
                limitations=limitations,
            ),
            parent_limitation,
        )

    @staticmethod
    def _top_level_colon(fragment: str) -> int | None:
        depth = 0
        quoted = False
        for index, character in enumerate(fragment):
            if character == '"':
                quoted = not quoted
            elif not quoted and character == "(":
                depth += 1
            elif not quoted and character == ")":
                depth = max(0, depth - 1)
            elif character == ":" and not quoted and depth == 0:
                return index
        return None

    def activated_ability_semantics(
        self, card: CardDefinition, fragment: str
    ) -> InterpretedActivatedAbilitySemantics | None:
        """Recognize activated syntax without upgrading unsupported costs or children."""
        if ":" not in fragment:
            return None
        colon = self._top_level_colon(fragment)
        if colon is None:
            program = ActivatedAbilityProgram(
                "",
                fragment,
                ActivationCostProgram(
                    "", False, False, False, ("activation_nested_context_not_implemented",)
                ),
                ActivatedEffectKind.UNSUPPORTED,
                0,
                False,
            )
            coverage = SemanticCoverage(
                False,
                False,
                False,
                ("activation_nested_context_not_implemented",),
            )
            return InterpretedActivatedAbilitySemantics(
                program, coverage, True, False, False, False, False, False
            )

        cost_text = fragment[:colon].strip()
        effect_text = fragment[colon + 1 :].strip()
        cost_parts = tuple(part.strip() for part in cost_text.split(",") if part.strip())
        tap_source = "{T}" in {part.upper() for part in cost_parts}
        canonical_food = bool(
            self._is_canonical_food_source(card)
            and self.FOOD_ACTIVATION.fullmatch(fragment.strip())
        )
        sacrifice_source = canonical_food and any(
            part.casefold() == "sacrifice this token" for part in cost_parts
        )
        mana_parts = tuple(
            part
            for part in cost_parts
            if part.upper() != "{T}"
            and not (sacrifice_source and part.casefold() == "sacrifice this token")
        )
        mana_cost = "".join(mana_parts)
        fixed_mana = all(
            "".join(self.ACTIVATION_MANA_SYMBOL.findall(part)) == part for part in mana_parts
        )
        unsupported_cost_parts = tuple(
            part
            for part in cost_parts
            if part.upper() != "{T}"
            and not (sacrifice_source and part.casefold() == "sacrifice this token")
            and "".join(self.ACTIVATION_MANA_SYMBOL.findall(part)) != part
        )
        cost_limitations: list[str] = []
        if unsupported_cost_parts:
            cost_limitations.append("activation_nonmana_cost_not_implemented")
        if re.search(r"\{X\}|\{[^}]+/[^}]+\}|\{[CP]\}", cost_text, re.I):
            cost_limitations.append("activation_complex_mana_cost_not_implemented")
        costs_executable = fixed_mana and not cost_limitations

        target_count = len(re.findall(r"\btarget\b", effect_text, re.I))
        choices_required = bool(re.search(r"\bchoose\b|\byour choice\b", effect_text, re.I))
        targets_choices_executable = target_count == 0 and not choices_required

        instructions = None
        instruction_match = re.search(r"\bActivate only\b.+$", effect_text, re.I)
        semantic_effect = effect_text
        if instruction_match:
            instructions = instruction_match.group(0)
            semantic_effect = effect_text[: instruction_match.start()].rstrip()

        source_names = {card.name, card.name.split(",", 1)[0]}
        self_reference = (
            "(?:"
            + "|".join(
                [
                    *(re.escape(name) for name in sorted(source_names, key=len, reverse=True)),
                    "this creature",
                ]
            )
            + ")"
        )
        first_strike = re.match(
            rf"^{self_reference} gains first strike until end of turn\.(?P<followup>.*)$",
            semantic_effect,
            re.I,
        )
        return_semantics = self.return_to_hand_semantics(card, fragment)
        targeted_return = bool(
            return_semantics is not None and return_semantics.coverage.payload_executable
        )
        if first_strike:
            effect_kind = ActivatedEffectKind.GRANT_SELF_FIRST_STRIKE_UNTIL_EOT
            action_match = first_strike
        elif targeted_return:
            effect_kind = ActivatedEffectKind.RETURN_ANOTHER_CREATURE_YOU_CONTROL_TO_OWNERS_HAND
            action_match = targeted_return
        elif canonical_food and effect_text.casefold() == "you gain 3 life.":
            effect_kind = ActivatedEffectKind.GAIN_THREE_LIFE
            action_match = True
        else:
            effect_kind = ActivatedEffectKind.UNSUPPORTED
            action_match = None
        child_payload_executable = effect_kind is not ActivatedEffectKind.UNSUPPORTED
        supported_turn_instruction = bool(
            targeted_return
            and instructions
            and return_semantics is not None
            and return_semantics.coverage.parent_executable
        )
        activation_parent_executable = (
            return_semantics.coverage.parent_executable
            if targeted_return and return_semantics is not None
            else instructions is None
        )
        targets_choices_executable = not choices_required and (
            target_count == 0 or bool(targeted_return) and target_count == 1
        )
        if targeted_return and return_semantics is not None:
            followup_executable = return_semantics.coverage.followup_executable
        elif canonical_food:
            followup_executable = bool(action_match)
        else:
            followup_executable = bool(action_match) and not action_match.group("followup").strip()

        limitations = list(cost_limitations)
        if targeted_return and return_semantics is not None:
            limitations.extend(return_semantics.limitations)
        if not targets_choices_executable:
            limitations.append("activation_targets_choices_not_implemented")
        if not child_payload_executable:
            limitations.append("activation_child_semantics_not_implemented")
        elif not followup_executable and not targeted_return:
            limitations.append("activation_followup_semantics_not_implemented")
        if instructions is not None and not supported_turn_instruction and not targeted_return:
            limitations.append("activation_timing_restriction_not_implemented")
        limitations = list(dict.fromkeys(limitations))
        parent_executable = (
            activation_parent_executable and costs_executable and targets_choices_executable
        )
        coverage = SemanticCoverage(
            child_payload_executable,
            parent_executable,
            followup_executable,
            tuple(limitations),
        )
        program = ActivatedAbilityProgram(
            cost_text,
            effect_text,
            ActivationCostProgram(
                mana_cost,
                tap_source,
                sacrifice_source,
                costs_executable,
                tuple(cost_limitations),
            ),
            effect_kind,
            target_count,
            choices_required,
            instructions,
        )
        return InterpretedActivatedAbilitySemantics(
            program,
            coverage,
            True,
            activation_parent_executable,
            costs_executable,
            targets_choices_executable,
            child_payload_executable,
            followup_executable,
        )

    def food_activation_semantic_coverage(
        self, card: CardDefinition, fragment: str
    ) -> InterpretedFoodActivationSemantics | None:
        """Recognize canonical Food use without upgrading its surrounding context."""
        match = self.FOOD_ACTIVATION.search(fragment)
        if match is None:
            return None
        token = self.PREDEFINED_TOKENS["food"]
        activation = self.activated_ability_semantics(token, match.group(0))
        assert activation is not None
        token_context = self.token_semantic_coverage(card, fragment)
        if token_context is None and not self._is_canonical_food_source(card):
            return None
        if token_context is None:
            parent_executable = fragment.strip() == match.group(0)
            followup_executable = parent_executable
            limitations: tuple[str, ...] = (
                () if parent_executable else ("food_activation_context_not_implemented",)
            )
        else:
            parent_executable = token_context.coverage.parent_executable
            followup_executable = token_context.coverage.followup_executable
            limitations = token_context.limitations
        coverage = SemanticCoverage(
            activation.coverage.payload_executable,
            parent_executable,
            followup_executable,
            limitations,
        )
        return InterpretedFoodActivationSemantics(
            activation.program,
            coverage,
            match.group(0),
        )

    def return_to_hand_semantics(
        self, card: CardDefinition, fragment: str
    ) -> InterpretedReturnToHandSemantics | None:
        """Recognize return-to-hand text broadly while bounding executable targets."""
        del card
        payload_pattern = re.compile(
            r"Return another target creature you control to (?:its|their) owner's hand",
            re.I,
        )
        colon = self._top_level_colon(fragment)
        if colon is None:
            effect_text = fragment
            effect_offset = 0
        else:
            raw_effect = fragment[colon + 1 :]
            leading_space = len(raw_effect) - len(raw_effect.lstrip())
            effect_text = raw_effect.strip()
            effect_offset = colon + 1 + leading_space
        instruction_match = re.search(r"\bActivate only\b.+$", effect_text, re.I)
        semantic_effect = effect_text
        instructions = None
        if instruction_match:
            instructions = instruction_match.group(0)
            semantic_effect = effect_text[: instruction_match.start()].rstrip()
        semantic_clause = self._return_clause(semantic_effect)
        if semantic_clause is None:
            return None
        absolute_start = semantic_clause.start + effect_offset
        absolute_end = semantic_clause.end + effect_offset
        clause = ReturnClause(
            fragment[absolute_start:absolute_end],
            absolute_start,
            absolute_end,
            fragment[:absolute_start],
            fragment[absolute_end:],
        )
        payload = payload_pattern.fullmatch(clause.text)
        program = ReturnToHandProgram(bool(payload), bool(payload))
        preceding_semantics = semantic_clause.preceding_text
        following_semantics = semantic_clause.following_text
        preceding_executable = not self._meaningful_semantic_text(preceding_semantics)
        followup_executable = not self._meaningful_semantic_text(following_semantics)
        cost_executable = False
        if colon is not None:
            cost_parts = tuple(part.strip() for part in fragment[:colon].split(",") if part.strip())
            cost_executable = all(
                part.upper() == "{T}" or "".join(self.ACTIVATION_MANA_SYMBOL.findall(part)) == part
                for part in cost_parts
            )
        activation_context_executable = bool(
            payload
            and colon is not None
            and cost_executable
            and (
                instructions is None
                or re.fullmatch(r"Activate only during your turn\.", instructions, re.I)
            )
        )
        limitations: list[str] = []
        if not program.executable:
            limitations.append("return_target_shape_not_implemented")
        if not activation_context_executable:
            limitations.append("return_parent_context_not_implemented")
        if not preceding_executable:
            limitations.append("return_preceding_semantics_not_implemented")
        if not followup_executable:
            limitations.append("return_followup_semantics_not_implemented")
        parent_executable = activation_context_executable and preceding_executable
        coverage = SemanticCoverage(
            program.executable,
            parent_executable,
            followup_executable,
            tuple(limitations),
        )
        return InterpretedReturnToHandSemantics(
            program,
            coverage,
            clause,
            preceding_semantics,
            following_semantics,
            preceding_executable,
            followup_executable,
        )

    @staticmethod
    def _meaningful_semantic_text(text: str) -> bool:
        """Distinguish punctuation surrounding a clause from unclassified instructions."""
        return bool(re.sub(r"[\s.;,:—–-]+", "", text))

    @staticmethod
    def _return_clause(text: str) -> ReturnClause | None:
        """Locate a Return-to-hand clause without claiming that its payload is executable."""
        returns = tuple(re.finditer(r"\breturn\b", text, re.I))
        for match in returns:
            sentence_end = text.find(".", match.end())
            if sentence_end < 0:
                sentence_end = len(text)
            next_return = next(
                (candidate.start() for candidate in returns if candidate.start() > match.start()),
                len(text),
            )
            search_end = min(sentence_end, next_return)
            destination = re.search(r"\b(?:hand|hands)\b", text[match.end() : search_end], re.I)
            if destination is None:
                continue
            end = match.end() + destination.end()
            return ReturnClause(
                text[match.start() : end],
                match.start(),
                end,
                text[: match.start()],
                text[end:],
            )
        return None

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
        for keyword in sorted(set(card.keywords) - {"Haste", "Trample"}):
            if not any(re.search(rf"\b{re.escape(keyword)}\b", line, re.I) for line in fragments):
                unsupported.append((keyword, "keyword_not_implemented"))
        for fragment in fragments:
            etb_artifact_draw = self.etb_artifact_draw_semantic_coverage(card, fragment)
            if etb_artifact_draw is not None:
                for reason in etb_artifact_draw.limitations:
                    unsupported.append((fragment, reason))
                continue
            permanent_left_counter = self.permanent_left_self_counter_semantic_coverage(
                card, fragment
            )
            if permanent_left_counter is not None:
                for reason in permanent_left_counter.limitations:
                    unsupported.append((fragment, reason))
                continue
            etb_drain_gain_scry = self.etb_drain_gain_scry_semantic_coverage(card, fragment)
            if etb_drain_gain_scry is not None:
                for reason in etb_drain_gain_scry.limitations:
                    unsupported.append((fragment, reason))
                continue
            dies_draw = self.dies_draw_semantic_coverage(card, fragment)
            if dies_draw is not None:
                for reason in dies_draw.limitations:
                    unsupported.append((fragment, reason))
                continue
            sneak_coverage = self.sneak_semantic_coverage(card, fragment)
            if sneak_coverage is not None and sneak_coverage.program.direct_keyword_ability:
                if self.supports_pt_fragment(fragment):
                    continue
                for reason in sneak_coverage.limitations:
                    unsupported.append((fragment, reason))
                continue
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
            hand_bottom_draw = self.hand_bottom_draw_semantic_coverage(card, fragment)
            if hand_bottom_draw is not None:
                for reason in hand_bottom_draw.limitations:
                    unsupported.append((fragment, reason))
                continue
            discard_draw = self.discard_draw_semantic_coverage(card, fragment)
            if discard_draw is not None:
                for reason in discard_draw.limitations:
                    unsupported.append((fragment, reason))
                continue
            scry_coverage = self.scry_semantic_coverage(card, fragment)
            if scry_coverage is not None:
                for reason in scry_coverage.limitations:
                    unsupported.append((fragment, reason))
                continue
            activation_coverage = self.activated_ability_semantics(card, fragment)
            if activation_coverage is not None:
                for reason in activation_coverage.limitations:
                    unsupported.append((fragment, reason))
                continue
            strike_coverage = self.strike_semantic_coverage(card, fragment)
            if strike_coverage is not None:
                for reason in strike_coverage.limitations:
                    unsupported.append((fragment, reason))
                continue
            trample_coverage = self.trample_semantic_coverage(card, fragment)
            if trample_coverage is not None:
                for reason in trample_coverage.limitations:
                    unsupported.append((fragment, reason))
                continue
            lifelink_coverage = self.lifelink_semantic_coverage(card, fragment)
            if lifelink_coverage is not None:
                for reason in lifelink_coverage.limitations:
                    unsupported.append((fragment, reason))
                continue
            if sneak_coverage is not None:
                if self.supports_pt_fragment(fragment):
                    continue
                for reason in sneak_coverage.limitations:
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
