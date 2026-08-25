"""Small, deterministic, rules-grounded Cardcade Engine 0.7 foundation.

This module deliberately implements only the rules surface it can represent honestly.  It is
separate from the preserved Engine 0.1--0.6 heuristic simulator.
"""

from __future__ import annotations

import random
import re
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from enum import Enum
from hashlib import sha256
from itertools import permutations
from pathlib import Path
from typing import Literal, Protocol

from tmnt_design_studio.card_data import CardDataCatalog
from tmnt_design_studio.card_interpreter07 import (
    ActivatedAbilityProgram,
    ActivatedEffectKind,
    CardInterpreter,
    CastKind,
    DamageTargetKind,
    DiscardDrawProgram,
    HandBottomDrawProgram,
    ScryProgram,
    SneakProgram,
    StrikeApplicability,
    StrikeKeyword,
    TokenCreationProgram,
    TokenDefinition,
)
from tmnt_design_studio.conformance07 import (
    AuthoritativeOpportunityContext,
    ConformanceStopRecord,
    OpportunityWitness,
    SemanticOccurrence,
    fragment_digest,
    opportunity_context_key,
    semantic_key,
)

ENGINE_VERSION = "cardcade-0.9.0-alpha.1"

Zone = Literal["library", "hand", "stack", "battlefield", "graveyard", "former"]


class TurnStep(Enum):
    SETUP = "setup"
    UNTAP = "untap"
    UPKEEP = "upkeep"
    DRAW = "draw"
    PRECOMBAT_MAIN = "precombat_main"
    BEGINNING_OF_COMBAT = "beginning_of_combat"
    DECLARE_ATTACKERS = "declare_attackers"
    DECLARE_BLOCKERS = "declare_blockers"
    COMBAT_DAMAGE = "combat_damage"
    END_OF_COMBAT = "end_of_combat"
    POSTCOMBAT_MAIN = "postcombat_main"
    END_STEP = "end_step"
    CLEANUP = "cleanup"


class TurnPhase(Enum):
    SETUP = "setup"
    BEGINNING = "beginning"
    PRECOMBAT_MAIN = "precombat_main"
    COMBAT = "combat"
    POSTCOMBAT_MAIN = "postcombat_main"
    ENDING = "ending"


class CombatDamageStepKind(Enum):
    NONE = "none"
    FIRST_STRIKE = "first_strike"
    REGULAR = "regular"
    COMPLETE = "complete"


STEP_PHASE = {
    TurnStep.SETUP: TurnPhase.SETUP,
    TurnStep.UNTAP: TurnPhase.BEGINNING,
    TurnStep.UPKEEP: TurnPhase.BEGINNING,
    TurnStep.DRAW: TurnPhase.BEGINNING,
    TurnStep.PRECOMBAT_MAIN: TurnPhase.PRECOMBAT_MAIN,
    TurnStep.BEGINNING_OF_COMBAT: TurnPhase.COMBAT,
    TurnStep.DECLARE_ATTACKERS: TurnPhase.COMBAT,
    TurnStep.DECLARE_BLOCKERS: TurnPhase.COMBAT,
    TurnStep.COMBAT_DAMAGE: TurnPhase.COMBAT,
    TurnStep.END_OF_COMBAT: TurnPhase.COMBAT,
    TurnStep.POSTCOMBAT_MAIN: TurnPhase.POSTCOMBAT_MAIN,
    TurnStep.END_STEP: TurnPhase.ENDING,
    TurnStep.CLEANUP: TurnPhase.ENDING,
}


def phase_for_step(step: TurnStep | str) -> str:
    """Return the engine's canonical phase for one authenticated turn step."""
    resolved = step if isinstance(step, TurnStep) else TurnStep(step)
    return STEP_PHASE[resolved].value


NEXT_STEP = {
    TurnStep.SETUP: TurnStep.UNTAP,
    TurnStep.UNTAP: TurnStep.UPKEEP,
    TurnStep.UPKEEP: TurnStep.DRAW,
    TurnStep.DRAW: TurnStep.PRECOMBAT_MAIN,
    TurnStep.PRECOMBAT_MAIN: TurnStep.BEGINNING_OF_COMBAT,
    TurnStep.BEGINNING_OF_COMBAT: TurnStep.DECLARE_ATTACKERS,
    TurnStep.DECLARE_ATTACKERS: TurnStep.DECLARE_BLOCKERS,
    TurnStep.DECLARE_BLOCKERS: TurnStep.COMBAT_DAMAGE,
    TurnStep.COMBAT_DAMAGE: TurnStep.END_OF_COMBAT,
    TurnStep.END_OF_COMBAT: TurnStep.POSTCOMBAT_MAIN,
    TurnStep.POSTCOMBAT_MAIN: TurnStep.END_STEP,
    TurnStep.END_STEP: TurnStep.CLEANUP,
    TurnStep.CLEANUP: TurnStep.UNTAP,
}


class ActionKind(Enum):
    PLAY_LAND = "play_land"
    CAST = "cast"
    ACTIVATE_ABILITY = "activate_ability"
    PASS_PRIORITY = "pass_priority"
    DECLARE_ATTACKERS = "declare_attackers"
    DECLARE_BLOCKERS = "declare_blockers"
    PASS = "pass"


@dataclass(frozen=True)
class ActionOption:
    """Immutable, identity-only input a pilot may select but never execute itself."""

    kind: ActionKind
    player_index: int
    object_id: str | None = None
    target_id: str | None = None
    cost_object_id: str | None = None
    oracle_fragment: str | None = None
    attacker_ids: tuple[str, ...] = ()
    blocks: tuple[tuple[str, str], ...] = ()
    priority_epoch: int | None = None


@dataclass(frozen=True)
class PriorityState:
    """Authoritative bounded 1v1 priority state for a nonempty stack."""

    epoch: int
    player_index: int
    consecutive_passes: tuple[int, ...] = ()
    resolution_pending: bool = False


@dataclass(frozen=True)
class ManaRequirement:
    """The represented total mana cost after construction, before payment."""

    generic: int
    colored: tuple[str, ...]

    @property
    def total(self) -> int:
        return self.generic + len(self.colored)


@dataclass(frozen=True)
class PaymentPlan:
    """An immutable proposed payment using authoritative mana-source runtime IDs."""

    player_index: int
    card_object_id: str
    requirement: ManaRequirement
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class SneakPaymentPlan:
    """A proposed fixed Sneak payment using only authoritative runtime IDs."""

    player_index: int
    card_object_id: str
    returned_attacker_id: str
    requirement: ManaRequirement
    mana_source_ids: tuple[str, ...]
    defending_player: int
    oracle_fragment: str


@dataclass(frozen=True)
class SneakEvidence:
    """Immutable announcement-through-resolution evidence for one Sneak spell."""

    card_name: str
    hand_object_id: str
    controller: int
    turn: int
    step: str
    oracle_fragment: str
    mana_requirement: ManaRequirement
    mana_source_ids: tuple[str, ...]
    returned_attacker_id: str
    returned_hand_id: str
    defending_player: int
    stack_object_id: str
    priority_epoch: int
    resolved_object_id: str | None = None
    entered_tapped: bool | None = None
    entered_attacking: bool | None = None


@dataclass(frozen=True)
class ActivationPaymentPlan:
    """A proposed bounded activation payment using authoritative IDs."""

    player_index: int
    source_id: str
    oracle_fragment: str
    requirement: ManaRequirement
    mana_source_ids: tuple[str, ...]
    tap_source: bool
    sacrifice_source: bool


@dataclass(frozen=True)
class ActivationEvidence:
    """Immutable evidence for one announced and resolved activated ability."""

    stack_object_id: str
    source_id: str
    controller: int
    oracle_fragment: str
    mana_source_ids: tuple[str, ...]
    tap_source: bool
    resolved: bool


@dataclass(frozen=True)
class FoodActivationEvidence:
    """Immutable announcement-through-resolution evidence for canonical Food use."""

    source_id: str
    source_name: str
    source_type_line: str
    source_owner: int
    controller: int
    source_was_token: bool
    oracle_fragment: str
    turn: int
    step: str
    source_zone_before: str
    mana_requirement: ManaRequirement
    mana_source_ids: tuple[str, ...]
    source_tapped_before: bool
    tap_paid: bool
    sacrifice_paid: bool
    sacrificed_destination_id: str
    sacrificed_destination_zone: str
    stack_object_id: str
    priority_epoch: int
    resolved: bool
    priority_passes: tuple[int, ...] = ()
    resolution_permitted: bool = False
    life_before: int | None = None
    life_after: int | None = None
    amount_gained: int | None = None
    final_source_disposition: str = "graveyard"


class RulesEventKind(Enum):
    CREATURE_ENTERED = "creature_entered"
    CREATURE_DIED = "creature_died"
    TOKENS_CREATED = "tokens_created"
    LIFE_GAINED = "life_gained"
    ATTACKERS_DECLARED = "attackers_declared"
    DAMAGE_DEALT = "damage_dealt"
    SCRIED = "scried"
    HAND_BOTTOM_DRAW = "hand_bottom_draw"
    DISCARD_DRAW = "discard_draw"
    PERMANENT_LEFT = "permanent_left"


class TriggerEffect(Enum):
    ALLIANCE_PT = "alliance_pt"
    ALLIANCE_COUNTER = "alliance_counter"
    ALLIANCE_MODAL = "alliance_modal"
    LIFE_GAIN_COUNTER = "life_gain_counter"
    ATTACK_PT = "attack_pt"
    SNEAK_ETB_CONDITION = "sneak_etb_condition"
    CREATE_TOKEN = "create_token"
    DEAL_DAMAGE = "deal_damage"
    SCRY = "scry"
    DISCARD_DRAW = "discard_draw"
    DIES_DRAW = "dies_draw"
    ETB_DRAIN_GAIN_SCRY = "etb_drain_gain_scry"
    PERMANENT_LEFT_SELF_COUNTER = "permanent_left_self_counter"
    ETB_ARTIFACT_DRAW = "etb_artifact_draw"


@dataclass(frozen=True)
class RulesEvent:
    event_id: str
    kind: RulesEventKind
    player_index: int
    subject_ids: tuple[str, ...]
    source_id: str | None = None
    target_player: int | None = None
    amount: int | None = None
    turn: int = 0
    step: str = "setup"
    active_player: int = 0
    battlefield_authority: tuple[tuple[str, int], ...] = ()
    battlefield_characteristics: tuple[tuple[str, int, str], ...] = ()
    last_known_battlefield: tuple[tuple[str, int, str, bool], ...] = ()


@dataclass(frozen=True)
class RulesEventEvidence:
    """Independent immutable trust anchor for one original authoritative rules event."""

    event_id: str
    event_cursor: int
    kind: RulesEventKind
    player_index: int
    subject_ids: tuple[str, ...]
    source_id: str | None
    target_player: int | None
    amount: int | None
    turn: int
    step: str
    active_player: int
    battlefield_authority: tuple[tuple[str, int], ...]
    battlefield_characteristics: tuple[tuple[str, int, str], ...]
    last_known_battlefield: tuple[tuple[str, int, str, bool], ...]


@dataclass(frozen=True)
class DamageTransaction:
    """A fully specified proposal validated before authoritative damage mutation."""

    controller: int
    source: CardObject | StackObject | Permanent
    target_kind: DamageTargetKind
    amount: int
    oracle_fragment: str
    target: Permanent | None = None
    target_player: int | None = None


@dataclass(frozen=True)
class ScryOption:
    """One immutable legal ordering; IDs are top-first and bottom-first respectively."""

    top_ids: tuple[str, ...]
    bottom_ids: tuple[str, ...]


@dataclass(frozen=True)
class ScryView:
    """Private immutable choice view, separate from the public game view and library."""

    player_index: int
    requested: int
    cards: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class ScryEvidence:
    """Typed committed Scry evidence; ordering uses the same top/bottom convention."""

    event_id: str
    player_index: int
    requested: int
    inspected_ids: tuple[str, ...]
    top_ids: tuple[str, ...]
    bottom_ids: tuple[str, ...]
    source_card: str
    oracle_fragment: str
    source_id: str | None = None


@dataclass(frozen=True)
class EtbDrainGainScryEvidence:
    """Immutable facts for the bounded ETB drain/gain followed by Scry transaction."""

    event_id: str
    stack_object_id: str
    source_id: str
    source_card: str
    controller: int
    opponent: int
    oracle_fragment: str
    turn: int
    step: str
    opponent_life_before: int
    opponent_life_after: int
    controller_life_before: int
    controller_life_after: int
    scry_event_id: str | None
    terminal_after_life_loss: bool


@dataclass(frozen=True)
class HandBottomDrawOption:
    """One immutable optional hand-card selection; ``None`` declines the action."""

    card_id: str | None


@dataclass(frozen=True)
class HandBottomDrawView:
    """Private immutable hand view for the bounded filtering choice."""

    player_index: int
    cards: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class HandBottomDrawPlan:
    """Validated instruction-point choice plus immutable authoritative pre-state."""

    choice: HandBottomDrawOption
    selected: CardObject | None
    offered_choice_ids: tuple[str | None, ...]
    pre_hand_ids: tuple[str, ...]
    pre_library_ids: tuple[str, ...]


@dataclass(frozen=True)
class HandBottomDrawEvidence:
    """Immutable before/after facts for one resolved optional filter instruction."""

    event_id: str
    player_index: int
    source_id: str
    oracle_fragment: str
    offered_choice_ids: tuple[str | None, ...]
    pre_hand_ids: tuple[str, ...]
    pre_library_ids: tuple[str, ...]
    selected_hand_id: str | None
    library_bottom_id: str | None
    movement_succeeded: bool
    conditional_draw_performed: bool
    drawn_library_id: str | None
    drawn_hand_id: str | None
    post_hand_ids: tuple[str, ...]
    post_library_ids: tuple[str, ...]
    declined: bool


@dataclass(frozen=True)
class DiscardDrawOption:
    """One immutable optional discard selection; ``None`` declines."""

    card_id: str | None


@dataclass(frozen=True)
class DiscardDrawView:
    """Private immutable hand view at triggered-ability resolution."""

    player_index: int
    cards: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class DiscardDrawPlan:
    choice: DiscardDrawOption
    selected: CardObject | None
    offered_choice_ids: tuple[str | None, ...]
    pre_hand_ids: tuple[str, ...]
    pre_library_ids: tuple[str, ...]
    pre_graveyard_ids: tuple[str, ...]


@dataclass(frozen=True)
class DiscardDrawEvidence:
    """Immutable evidence for optional Discard followed by conditional Draw."""

    event_id: str
    player_index: int
    attack_provenance: AttackTriggerProvenance
    stack_object_id: str
    source_id: str
    oracle_fragment: str
    offered_choice_ids: tuple[str | None, ...]
    pre_hand_ids: tuple[str, ...]
    pre_library_ids: tuple[str, ...]
    pre_graveyard_ids: tuple[str, ...]
    selected_hand_id: str | None
    discarded_graveyard_id: str | None
    movement_succeeded: bool
    conditional_draw_performed: bool
    pre_draw_top_id: str | None
    drawn_hand_id: str | None
    post_hand_ids: tuple[str, ...]
    post_library_ids: tuple[str, ...]
    post_graveyard_ids: tuple[str, ...]
    declined: bool


@dataclass(frozen=True)
class AttackTriggerProvenance:
    """Immutable attack-event facts carried by one Action #10 transaction."""

    event_id: str
    event_kind: RulesEventKind
    event_player_index: int
    subject_ids: tuple[str, ...]
    attacker_id: str
    controller: int
    turn: int
    step: str
    active_player: int


@dataclass(frozen=True)
class CombatDamageAssignment:
    """One immutable combat-damage assignment within an authoritative damage step."""

    source_id: str
    target_id: str | None
    target_player: int | None
    amount: int
    role: Literal[
        "first_strike",
        "double_strike_first",
        "regular",
        "double_strike_second",
    ]
    trample: bool = False
    lethal_required: int | None = None


@dataclass(frozen=True)
class TrampleDamageEvidence:
    """Immutable before/after facts for one bounded Trample assignment result."""

    attacker_id: str
    blocker_id: str | None
    damage_step: CombatDamageStepKind
    attacker_power: int
    blocker_toughness: int | None
    blocker_marked_damage_before: int | None
    lethal_required: int
    blocker_damage_assigned: int
    player_damage_assigned: int
    defending_player: int
    defending_life_before: int
    defending_life_after: int
    blocker_marked_damage_after: int | None
    blocker_survived: bool


@dataclass(frozen=True)
class LifelinkEvidence:
    """Immutable damage-result facts for one source's Lifelink life gain."""

    event_id: str
    source_id: str
    controller: int
    amount: int
    combat: bool
    damage_step: CombatDamageStepKind | None
    target_ids: tuple[str, ...]
    target_players: tuple[int, ...]
    life_before: int
    life_after: int


@dataclass(frozen=True)
class CombatDamageStepEvidence:
    """Typed evidence for one completed first-strike or regular damage step."""

    kind: CombatDamageStepKind
    sequence: int
    total_steps: int
    assignments: tuple[CombatDamageAssignment, ...]
    removed_before_next_step: tuple[str, ...]
    trample_results: tuple[TrampleDamageEvidence, ...] = ()


@dataclass(frozen=True)
class TemporaryKeywordEffect:
    keyword: StrikeKeyword
    duration: Literal["until_end_of_turn"]
    source_id: str
    oracle_fragment: str


@dataclass(frozen=True)
class TriggerInstance:
    trigger_id: str
    controller: int
    source_id: str
    source_card: CardFact
    oracle_fragment: str
    effect: TriggerEffect
    event: RulesEvent


@dataclass(frozen=True)
class PublicObjectView:
    object_id: str
    name: str
    controller: int
    power: int | None
    toughness: int | None
    tapped: bool
    damage: int
    is_token: bool = False


@dataclass(frozen=True)
class GameView:
    turn: int
    active_player: int
    phase: str
    step: str
    life: tuple[int, int]
    hands: tuple[tuple[tuple[str, str, int, bool], ...], ...]
    battlefields: tuple[tuple[PublicObjectView, ...], ...]


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
    oracle_id: str = ""

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
    created_order: int = 0
    derived_static: bool = False


class CharacteristicLayer(Enum):
    COPY = 1
    CONTROL = 2
    TEXT = 3
    TYPE = 4
    COLOR = 5
    ABILITY = 6
    POWER_TOUGHNESS = 7


class PowerToughnessSubLayer(Enum):
    CHARACTERISTIC_DEFINING = "7a"
    SET_BASE = "7b"
    MODIFY = "7c"
    SWITCH = "7d"


class CharacteristicOperation(Enum):
    SET = "set"
    ADD = "add"
    SWITCH = "switch"


@dataclass(frozen=True)
class CharacteristicEffect:
    effect_id: str
    layer: CharacteristicLayer
    sublayer: PowerToughnessSubLayer | None
    operation: CharacteristicOperation
    power: int = 0
    toughness: int = 0
    timestamp: tuple[int, int] = (0, 0)
    depends_on: tuple[str, ...] = ()
    source_card: str = ""


def _ordered_characteristic_effects(
    effects: list[CharacteristicEffect],
) -> list[CharacteristicEffect]:
    """Order by layer/sublayer, then declared dependencies and stable timestamps."""
    sublayer_order = {value: index for index, value in enumerate(PowerToughnessSubLayer)}
    groups: dict[tuple[int, int], list[CharacteristicEffect]] = {}
    for effect in effects:
        key = (
            effect.layer.value,
            -1 if effect.sublayer is None else sublayer_order[effect.sublayer],
        )
        groups.setdefault(key, []).append(effect)
    ordered: list[CharacteristicEffect] = []
    for key in sorted(groups):
        remaining = list(groups[key])
        resolved: set[str] = set()
        group_ids = {effect.effect_id for effect in remaining}
        while remaining:
            ready = [
                effect
                for effect in remaining
                if not (set(effect.depends_on) & group_ids) - resolved
            ]
            if not ready:
                raise ValueError("cyclic characteristic-effect dependency")
            ready.sort(key=lambda effect: (effect.timestamp, effect.effect_id))
            effect = ready[0]
            ordered.append(effect)
            resolved.add(effect.effect_id)
            remaining.remove(effect)
    return ordered


@dataclass(eq=False)
class CardObject:
    """One authoritative runtime incarnation of an immutable card definition."""

    object_id: str
    card: CardFact | TokenDefinition
    owner: int
    controller: int
    zone: Zone
    is_token: bool = False

    @property
    def name(self) -> str:
        return self.card.name

    @property
    def mana_cost(self) -> str:
        return self.card.mana_cost

    @property
    def mana_value(self) -> int:
        return self.card.mana_value

    @property
    def type_line(self) -> str:
        return self.card.type_line

    @property
    def oracle_text(self) -> str:
        return self.card.oracle_text

    @property
    def keywords(self) -> tuple[str, ...]:
        return self.card.keywords

    @property
    def is_land(self) -> bool:
        return self.card.is_land

    @property
    def is_creature(self) -> bool:
        return self.card.is_creature

    @property
    def power(self) -> int | None:
        return self.card.power

    @property
    def toughness(self) -> int | None:
        return self.card.toughness


@dataclass(eq=False)
class StackObject:
    """One authoritative spell incarnation with announcement-time choices locked in."""

    object_id: str
    card: CardFact
    owner: int
    controller: int
    cast_kind: CastKind
    target_id: str | None = None
    sneak_returned_attacker_id: str | None = None
    sneak_returned_hand_id: str | None = None
    sneak_defending_player: int | None = None
    sneak_oracle_fragment: str | None = None
    sneak_mana_source_ids: tuple[str, ...] = ()
    zone: Zone = "stack"

    @property
    def name(self) -> str:
        return self.card.name


@dataclass(eq=False)
class TriggeredAbilityObject:
    """One authoritative triggered ability on the stack, independent of its source."""

    object_id: str
    controller: int
    source_id: str
    source_card: CardFact
    oracle_fragment: str
    effect: TriggerEffect
    event: RulesEvent
    trigger_id: str | None = None
    zone: Zone = "stack"

    @property
    def owner(self) -> int:
        return self.controller


@dataclass(eq=False)
class ActivatedAbilityObject:
    """An authoritative activated ability on the stack, independent of its source."""

    object_id: str
    controller: int
    source_id: str
    source_card: CardFact | TokenDefinition
    oracle_fragment: str
    program: ActivatedAbilityProgram
    mana_source_ids: tuple[str, ...]
    tap_source: bool
    sacrifice_source: bool = False
    sacrificed_destination_id: str | None = None
    target_ids: tuple[str, ...] = ()
    choice_ids: tuple[str, ...] = ()
    zone: Zone = "stack"

    @property
    def owner(self) -> int:
        return self.controller


@dataclass(eq=False)
class Permanent:
    object_id: str
    card: CardFact | TokenDefinition
    owner: int
    controller: int
    zone: Zone = "battlefield"
    tapped: bool = False
    summoning_sick: bool = True
    entered_battlefield_turn: int = 0
    damage: int = 0
    counters: dict[str, int] = field(default_factory=dict)
    pt_modifiers: list[PowerToughnessModifier] = field(default_factory=list)
    characteristic_effects: list[CharacteristicEffect] = field(default_factory=list)
    temporary_keyword_effects: list[TemporaryKeywordEffect] = field(default_factory=list)
    is_token: bool = False
    type_line_override: str | None = None

    @property
    def type_line(self) -> str:
        """The permanent's current authoritative type line on the battlefield."""
        return self.card.type_line if self.type_line_override is None else self.type_line_override

    @property
    def is_creature(self) -> bool:
        return "Creature" in self.type_line

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
        return self.evaluate_power_toughness()[0]

    @property
    def toughness(self) -> int:
        return self.evaluate_power_toughness()[1]

    def evaluate_power_toughness(self) -> tuple[int, int]:
        counter_power, counter_toughness = self.counter_delta()
        effects = list(self.characteristic_effects)
        if counter_power or counter_toughness:
            effects.append(
                CharacteristicEffect(
                    f"{self.object_id}:counters",
                    CharacteristicLayer.POWER_TOUGHNESS,
                    PowerToughnessSubLayer.MODIFY,
                    CharacteristicOperation.ADD,
                    counter_power,
                    counter_toughness,
                    (-1, -1),
                    source_card="counters",
                )
            )
        effects.extend(
            CharacteristicEffect(
                f"{self.object_id}:modifier:{index}",
                CharacteristicLayer.POWER_TOUGHNESS,
                PowerToughnessSubLayer.MODIFY,
                CharacteristicOperation.ADD,
                modifier.power,
                modifier.toughness,
                (modifier.created_turn, modifier.created_order),
                source_card=modifier.source_card,
            )
            for index, modifier in enumerate(self.pt_modifiers)
        )
        power, toughness = self.printed_power, self.printed_toughness
        for effect in _ordered_characteristic_effects(effects):
            if effect.layer is not CharacteristicLayer.POWER_TOUGHNESS:
                continue
            if effect.operation is CharacteristicOperation.SET:
                power, toughness = effect.power, effect.toughness
            elif effect.operation is CharacteristicOperation.ADD:
                power += effect.power
                toughness += effect.toughness
            elif effect.operation is CharacteristicOperation.SWITCH:
                power, toughness = toughness, power
        return power, toughness


@dataclass
class PlayerState:
    name: str
    library: list[CardObject]
    hand: list[CardObject] = field(default_factory=list)
    battlefield: list[Permanent] = field(default_factory=list)
    graveyard: list[CardObject] = field(default_factory=list)
    life: int = 20
    lands_played: int = 0
    lost: bool = False
    loss_reason: str | None = None
    failed_draw_pending: bool = False


class StateBasedAction(Protocol):
    """One reusable state-based check applied until the game state stabilizes."""

    name: str

    def apply(self, game: Game) -> bool: ...


@dataclass(frozen=True)
class LethalDamageStateBasedAction:
    name: str = "lethal_damage"

    def apply(self, game: Game) -> bool:
        lethal = tuple(
            permanent
            for player in game.players
            for permanent in player.battlefield
            if permanent.card.is_creature and permanent.damage >= permanent.toughness
        )
        if lethal:
            game.put_permanents_into_graveyard(lethal, state_based_action=self.name)
        return bool(lethal)


@dataclass(frozen=True)
class FailedDrawStateBasedAction:
    """CR 704.5b: lose after failing to draw since the previous SBA check."""

    name: str = "failed_draw"

    def apply(self, game: Game) -> bool:
        changed = False
        for index, player in enumerate(game.players):
            if not player.failed_draw_pending:
                continue
            player.failed_draw_pending = False
            if not player.lost:
                player.lost = True
                player.loss_reason = "draw_from_empty_library"
                game.winner = 1 - index
                game.log(
                    "player_lost",
                    player=player.name,
                    reason=player.loss_reason,
                    state_based_action=self.name,
                )
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
                choices = tuple(permanent.object_id for permanent in permanents)
                keep_id = game.legend_rule_chooser(player_index, choices)
                keep = next(
                    (permanent for permanent in permanents if permanent.object_id == keep_id), None
                )
                if keep is None:
                    raise ValueError("legend-rule chooser must return one of the listed permanents")
                game.log(
                    "legend_rule_choice",
                    player=player.name,
                    card=name,
                    kept_battlefield_index=player.battlefield.index(keep),
                    moved_to_graveyard=len(permanents) - 1,
                )
                leaving = tuple(permanent for permanent in permanents if permanent is not keep)
                game.put_permanents_into_graveyard(leaving, state_based_action=self.name)
                changed = True
        return changed


@dataclass(frozen=True)
class TokenCeasesStateBasedAction:
    """CR 704.5d: a token in a zone other than the battlefield ceases to exist."""

    name: str = "token_ceases"

    def apply(self, game: Game) -> bool:
        changed = False
        for player in game.players:
            for zone_name in ("library", "hand", "graveyard"):
                zone = getattr(player, zone_name)
                for obj in list(zone):
                    if isinstance(obj, CardObject) and obj.is_token:
                        zone.remove(obj)
                        obj.zone = "former"
                        game.log(
                            "token_ceased",
                            object_id=obj.object_id,
                            token=obj.card.name,
                            owner=game.players[obj.owner].name,
                            previous_zone=zone_name,
                            state_based_action=self.name,
                        )
                        changed = True
        return changed


DEFAULT_STATE_BASED_ACTIONS: tuple[StateBasedAction, ...] = (
    FailedDrawStateBasedAction(),
    LegendRuleStateBasedAction(),
    LethalDamageStateBasedAction(),
    TokenCeasesStateBasedAction(),
)


@dataclass(frozen=True)
class RNGRecord:
    sequence: int
    domain: str
    operation: str
    result: tuple[int, ...] | int
    state_before: str
    state_after: str


class DeterministicRNG:
    """Game-owned, auditable, serializable deterministic randomness service."""

    def __init__(self, seed: int):
        self.seed = seed
        self._random = random.Random(seed)
        self.records: list[RNGRecord] = []

    @staticmethod
    def _digest(state: object) -> str:
        return sha256(repr(state).encode("utf-8")).hexdigest()

    @property
    def state_digest(self) -> str:
        return self._digest(self._random.getstate())

    def export_state(self) -> tuple:
        """Return the JSON-serializable Python RNG state accepted by `restore_state`."""
        return self._random.getstate()

    def restore_state(self, state: tuple | list) -> None:
        """Restore an exported state without inventing a randomness consumption."""
        if not isinstance(state, (tuple, list)) or len(state) != 3:
            raise ValueError("invalid deterministic RNG state")

        def tuples(value):
            if isinstance(value, list):
                return tuple(tuples(item) for item in value)
            if isinstance(value, tuple):
                return tuple(tuples(item) for item in value)
            return value

        try:
            self._random.setstate(tuples(state))
        except (TypeError, ValueError) as error:
            raise ValueError("invalid deterministic RNG state") from error
        self.records.clear()

    def shuffled(self, values: list, *, domain: str) -> list:
        """Return the exact `random.shuffle` permutation and record its state transition."""
        if not domain:
            raise ValueError("RNG consumption requires a domain")
        indexed = list(enumerate(values))
        before = self.state_digest
        self._random.shuffle(indexed)
        after = self.state_digest
        permutation = tuple(index for index, _value in indexed)
        self.records.append(
            RNGRecord(
                len(self.records) + 1,
                domain,
                "shuffle",
                permutation,
                before,
                after,
            )
        )
        return [value for _index, value in indexed]

    def randrange(self, stop: int, *, domain: str) -> int:
        """Consume one bounded random integer with auditable state evidence."""
        if not domain or not isinstance(stop, int) or isinstance(stop, bool) or stop <= 0:
            raise ValueError("RNG randrange requires a positive bound and domain")
        before = self.state_digest
        result = self._random.randrange(stop)
        after = self.state_digest
        self.records.append(
            RNGRecord(len(self.records) + 1, domain, "randrange", result, before, after)
        )
        return result


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
        scry_chooser=None,
        hand_bottom_draw_chooser=None,
        discard_draw_chooser=None,
        interpreter: CardInterpreter | None = None,
    ):
        self.rng = DeterministicRNG(seed)
        shuffled: list[list[CardFact]] = []
        for owner, deck in enumerate(decks):
            shuffled.append(self.rng.shuffled(list(deck), domain=f"opening_library:{owner}"))
        self._next_object_number = 1
        self._objects: dict[
            str,
            CardObject | StackObject | TriggeredAbilityObject | ActivatedAbilityObject | Permanent,
        ] = {}
        self.stack: list[StackObject | TriggeredAbilityObject | ActivatedAbilityObject] = []
        self.priority_state: PriorityState | None = None
        self._priority_resolution_in_progress = False
        self._next_priority_epoch = 1
        self.pending_triggers: list[TriggerInstance] = []
        self._triggers: dict[str, TriggerInstance] = {}
        self._next_event_number = 1
        self._rules_events: dict[str, RulesEvent] = {}
        self._rules_event_evidence: list[RulesEventEvidence] = []
        self._next_semantic_occurrence_number = 1
        self._next_opportunity_witness_number = 1
        self._next_opportunity_context_number = 1
        self.semantic_occurrences: list[SemanticOccurrence] = []
        self.opportunity_witnesses: list[OpportunityWitness] = []
        self.opportunity_contexts: list[AuthoritativeOpportunityContext] = []
        self.conformance_stop_records: list[ConformanceStopRecord] = []
        self._next_trigger_number = 1
        self._next_effect_number = 1
        self.players = [PlayerState(names[i], []) for i in range(2)]
        for owner, cards in enumerate(shuffled):
            self.players[owner].library.extend(
                self._create_card_object(card, owner, "library") for card in cards
            )
        self._turn = 0
        self._active_player = 0
        self._step = TurnStep.SETUP
        self._combat_attackers: tuple[str, ...] = ()
        self._combat_blocks: tuple[tuple[str, str], ...] = ()
        self._attackers_declared = False
        self._blockers_declared = False
        self._combat_damage_resolved = False
        self._combat_damage_step_kind = CombatDamageStepKind.NONE
        self._combat_damage_step_number = 0
        self._combat_damage_total_steps = 0
        self._first_damage_qualified_ids: tuple[str, ...] = ()
        self._first_double_strike_ids: tuple[str, ...] = ()
        self._regular_damage_initial_ids: tuple[str, ...] = ()
        self.winner: int | None = None
        self.events: list[dict[str, object]] = []
        self.scry_evidence: list[ScryEvidence] = []
        self.etb_drain_gain_scry_evidence: list[EtbDrainGainScryEvidence] = []
        self.hand_bottom_draw_evidence: list[HandBottomDrawEvidence] = []
        self.discard_draw_evidence: list[DiscardDrawEvidence] = []
        self.combat_damage_evidence: list[CombatDamageStepEvidence] = []
        self.lifelink_evidence: list[LifelinkEvidence] = []
        self.activation_evidence: list[ActivationEvidence] = []
        self.food_activation_evidence: list[FoodActivationEvidence] = []
        self.sneak_evidence: list[SneakEvidence] = []
        self.limitations: set[str] = set()
        self.state_based_actions = state_based_actions
        self.interpreter = interpreter or CardInterpreter()
        self.legend_rule_chooser = legend_rule_chooser or (
            lambda _player_index, object_ids: object_ids[0]
        )
        self.counter_target_chooser = counter_target_chooser or (
            lambda _player_index, _source_id, object_ids: object_ids[0]
        )
        self.alliance_mode_chooser = alliance_mode_chooser or (
            lambda _player_index, _source_id, modes: modes[0]
        )
        self.scry_chooser = scry_chooser or (
            lambda view, options: next(
                option
                for option in options
                if option.top_ids == tuple(object_id for object_id, _name in view.cards)
                and not option.bottom_ids
            )
        )
        self.hand_bottom_draw_chooser = hand_bottom_draw_chooser or (
            lambda _view, options: next(option for option in options if option.card_id is None)
        )
        self.discard_draw_chooser = discard_draw_chooser or (
            lambda _view, options: next(option for option in options if option.card_id is None)
        )
        self.alliance_modes_chosen: dict[str, set[str]] = {}
        for player in self.players:
            self.draw(player, 7, setup=True)
        self.log("game_started", seed=seed, starting_player=names[0])

    @property
    def turn(self) -> int:
        return self._turn

    @property
    def active_player(self) -> int:
        return self._active_player

    @property
    def step(self) -> TurnStep:
        return self._step

    @property
    def phase(self) -> str:
        return phase_for_step(self._step)

    def _allocate_object_id(self) -> str:
        object_id = f"object-{self._next_object_number:06d}"
        self._next_object_number += 1
        return object_id

    def _register(
        self,
        obj: CardObject | StackObject | TriggeredAbilityObject | ActivatedAbilityObject | Permanent,
    ) -> CardObject | StackObject | TriggeredAbilityObject | ActivatedAbilityObject | Permanent:
        if obj.object_id in self._objects:
            raise ValueError(f"duplicate runtime object ID: {obj.object_id}")
        self._objects[obj.object_id] = obj
        return obj

    def _create_card_object(self, card: CardFact, owner: int, zone: Zone) -> CardObject:
        if zone not in {"library", "hand", "graveyard"}:
            raise ValueError(f"card object cannot be created in {zone}")
        return self._register(CardObject(self._allocate_object_id(), card, owner, owner, zone))  # type: ignore[return-value]

    def create_permanent(
        self,
        card: CardFact,
        owner: int,
        *,
        controller: int | None = None,
        tapped: bool = False,
        summoning_sick: bool = True,
    ) -> Permanent:
        """Create, register, and authoritatively place a setup battlefield object."""
        permanent = Permanent(
            self._allocate_object_id(),
            card,
            owner,
            owner if controller is None else controller,
            tapped=tapped,
            summoning_sick=summoning_sick,
            entered_battlefield_turn=self.turn,
        )
        self._register(permanent)
        self.players[permanent.controller].battlefield.append(permanent)
        return permanent

    def create_tokens(
        self,
        creator_index: int,
        program: TokenCreationProgram,
        *,
        controller: int | None = None,
        source_card: str,
        oracle_fragment: str,
        source_id: str | None = None,
    ) -> tuple[Permanent, ...]:
        """Atomically create one deterministic batch of Oracle-derived token permanents."""
        if creator_index not in range(2):
            raise ValueError("token creator is invalid")
        destination_controller = creator_index if controller is None else controller
        if destination_controller not in range(2):
            raise ValueError("token controller is invalid")
        if source_id is not None and source_id not in self._objects:
            raise ValueError("token source identity is not authoritative")
        if not isinstance(program, TokenCreationProgram) or not program.executable:
            raise ValueError("token creation program is not executable")
        assert program.definition is not None and program.quantity is not None
        definition = program.definition
        if definition.is_creature and (definition.power is None or definition.toughness is None):
            raise ValueError("creature token definition requires power and toughness")
        if not definition.is_creature and (
            definition.power is not None or definition.toughness is not None
        ):
            raise ValueError("noncreature token definition cannot have power or toughness")

        starting_number = self._next_object_number
        created: list[Permanent] = []
        try:
            for _ in range(program.quantity):
                token = Permanent(
                    self._allocate_object_id(),
                    definition,
                    destination_controller,
                    destination_controller,
                    tapped=program.tapped,
                    summoning_sick=definition.is_creature,
                    entered_battlefield_turn=self.turn,
                    is_token=True,
                )
                self._register(token)
                self.players[destination_controller].battlefield.append(token)
                created.append(token)
        except Exception:
            for token in created:
                if token in self.players[destination_controller].battlefield:
                    self.players[destination_controller].battlefield.remove(token)
                self._objects.pop(token.object_id, None)
            self._next_object_number = starting_number
            raise

        object_ids = tuple(token.object_id for token in created)
        event = self._new_rules_event(
            RulesEventKind.TOKENS_CREATED,
            destination_controller,
            object_ids,
        )
        self.log(
            "tokens_created",
            event_id=event.event_id,
            creator=self.players[creator_index].name,
            controller=self.players[destination_controller].name,
            token=definition.name,
            quantity=program.quantity,
            object_ids=list(object_ids),
            source_card=source_card,
            source_id=source_id,
            oracle_fragment=oracle_fragment,
        )
        creatures = tuple(token for token in created if token.card.is_creature)
        if creatures:
            self._process_creatures_entered_triggers(creatures)
        self.refresh_static_pt_modifiers()
        self.check_state_based_actions()
        return tuple(created)

    def place_on_battlefield(self, permanent: Permanent) -> None:
        """Place a newly registered test/setup object in its authoritative battlefield zone."""
        if self._objects.get(permanent.object_id) is not permanent:
            raise ValueError("unregistered runtime object")
        if self._identity_contains(self.players[permanent.controller].battlefield, permanent):
            return
        if any(self._identity_contains(zone, permanent) for zone in self._all_zone_lists()):
            raise ValueError("runtime object already occupies a zone")
        self.players[permanent.controller].battlefield.append(permanent)

    def set_hand_for_testing(self, owner: int, cards: list[CardFact]) -> list[CardObject]:
        """Replace a hand for deterministic rule-test setup, outside gameplay transitions."""
        player = self.players[owner]
        for obj in player.hand:
            obj.zone = "former"
        player.hand.clear()
        player.hand.extend(self._create_card_object(card, owner, "hand") for card in cards)
        return player.hand

    @staticmethod
    def _identity_contains(zone: list, obj: object) -> bool:
        return any(candidate is obj for candidate in zone)

    def _all_zone_lists(self) -> list[list]:
        return [self.stack] + [
            zone
            for player in self.players
            for zone in (player.library, player.hand, player.battlefield, player.graveyard)
        ]

    def _authoritative_container(
        self,
        obj: CardObject | StackObject | TriggeredAbilityObject | ActivatedAbilityObject | Permanent,
    ) -> list:
        if obj.zone == "stack":
            return self.stack
        holder = obj.controller if obj.zone == "battlefield" else obj.owner
        if obj.zone == "former":
            raise ValueError("former object no longer occupies an authoritative zone")
        return getattr(self.players[holder], obj.zone)

    def is_authoritative(
        self,
        obj: CardObject | StackObject | TriggeredAbilityObject | ActivatedAbilityObject | Permanent,
        zone: Zone,
    ) -> bool:
        if zone == "former" or self._objects.get(obj.object_id) is not obj or obj.zone != zone:
            return False
        return self._identity_contains(self._authoritative_container(obj), obj)

    def _battlefield_authority_snapshot(self) -> tuple[tuple[str, int], ...]:
        return tuple(
            (permanent.object_id, permanent.controller)
            for player in self.players
            for permanent in player.battlefield
        )

    def _battlefield_characteristics_snapshot(self) -> tuple[tuple[str, int, str], ...]:
        """Freeze evaluated type/controller facts for authoritative battlefield permanents."""
        return tuple(
            (permanent.object_id, permanent.controller, permanent.type_line)
            for player in self.players
            for permanent in player.battlefield
        )

    def _permanent_left_trigger_sources(
        self,
    ) -> tuple[tuple[Permanent, str], ...]:
        sources: list[tuple[Permanent, str]] = []
        for player in self.players:
            for permanent in player.battlefield:
                for fragment in self.interpreter.fragments(permanent.card):
                    coverage = self.interpreter.permanent_left_self_counter_semantic_coverage(
                        permanent.card, fragment
                    )
                    if coverage is not None and coverage.fully_supported:
                        sources.append((permanent, fragment))
        return tuple(sources)

    def move_object(
        self,
        obj: CardObject | StackObject | Permanent,
        destination: Literal["library", "hand", "stack", "battlefield", "graveyard"],
        *,
        controller: int | None = None,
        cast_kind: CastKind | None = None,
        target_id: str | None = None,
        summoning_sick: bool = True,
        reason: str | None = None,
        library_position: Literal["top", "bottom"] | None = None,
        _departure_authority: tuple[tuple[str, int], ...] | None = None,
        _departure_sources: tuple[tuple[Permanent, str], ...] | None = None,
    ) -> CardObject | StackObject | Permanent:
        """Validate then atomically create the destination-zone incarnation of ``obj``."""
        if self._objects.get(obj.object_id) is not obj:
            raise ValueError("unregistered runtime object")
        if obj.zone == "former":
            raise ValueError("former object cannot move")
        source = self._authoritative_container(obj)
        if not self._identity_contains(source, obj):
            raise ValueError("object is not in its declared source zone")
        if sum(self._identity_contains(zone, obj) for zone in self._all_zone_lists()) != 1:
            raise ValueError("object must occupy exactly one authoritative zone")
        if destination == obj.zone:
            raise ValueError("same-zone movement is not supported")
        if isinstance(obj, CardObject) and obj.is_token and obj.zone != "battlefield":
            raise ValueError("a nonbattlefield token must cease before it can move again")
        if destination == "stack" and getattr(obj, "is_token", False):
            raise ValueError("a token cannot move to the stack")
        if controller is not None and (
            destination not in {"battlefield", "stack"} or controller not in range(2)
        ):
            raise ValueError("destination controller is invalid")
        if destination == "stack" and (controller is None or cast_kind is None):
            raise ValueError("stack movement requires controller and cast program")
        if destination != "stack" and (cast_kind is not None or target_id is not None):
            raise ValueError("stack metadata is valid only for stack movement")
        if library_position is not None and destination != "library":
            raise ValueError("library position is valid only for library movement")

        source_zone = obj.zone
        departure_authority = None
        departure_sources = None
        departure_last_known = None
        if source_zone == "battlefield" and destination != "battlefield":
            assert isinstance(obj, Permanent)
            departure_authority = (
                self._battlefield_authority_snapshot()
                if _departure_authority is None
                else _departure_authority
            )
            departure_sources = (
                self._permanent_left_trigger_sources()
                if _departure_sources is None
                else _departure_sources
            )
            departure_last_known = (
                obj.object_id,
                obj.controller,
                obj.type_line,
                obj.is_creature,
            )
        new_id = self._allocate_object_id()
        destination_controller = obj.owner if controller is None else controller
        if destination == "battlefield":
            replacement: CardObject | StackObject | Permanent = Permanent(
                new_id,
                obj.card,
                obj.owner,
                destination_controller,
                summoning_sick=summoning_sick,
                entered_battlefield_turn=self.turn,
                is_token=getattr(obj, "is_token", False),
            )
            destination_container = self.players[destination_controller].battlefield
        elif destination == "stack":
            assert controller is not None and cast_kind is not None
            replacement = StackObject(new_id, obj.card, obj.owner, controller, cast_kind, target_id)
            destination_container = self.stack
        else:
            replacement = CardObject(
                new_id,
                obj.card,
                obj.owner,
                obj.owner,
                destination,
                is_token=getattr(obj, "is_token", False),
            )
            destination_container = getattr(self.players[obj.owner], destination)

        # No mutation occurs before every validation and destination construction succeeds.
        source_index = next(index for index, candidate in enumerate(source) if candidate is obj)
        source.pop(source_index)
        if destination == "library" and library_position == "bottom":
            destination_container.insert(0, replacement)
        else:
            destination_container.append(replacement)
        obj.zone = "former"
        self._register(replacement)
        self.log(
            "zone_changed",
            card=obj.card.name,
            owner=self.players[obj.owner].name,
            source_object_id=obj.object_id,
            destination_object_id=replacement.object_id,
            source_zone=source_zone,
            destination_zone=destination,
            reason=reason,
            library_position=library_position,
        )
        if departure_authority is not None:
            assert departure_sources is not None and departure_last_known is not None
            qualifying_sources = tuple(
                (watcher, fragment)
                for watcher, fragment in departure_sources
                if watcher.object_id != obj.object_id
            )
            if qualifying_sources:
                event = self._new_rules_event(
                    RulesEventKind.PERMANENT_LEFT,
                    departure_last_known[1],
                    (obj.object_id,),
                    source_id=obj.object_id,
                    battlefield_authority=departure_authority,
                    last_known_battlefield=(departure_last_known,)
                    + tuple(
                        (
                            watcher.object_id,
                            watcher.controller,
                            watcher.type_line,
                            watcher.is_creature,
                        )
                        for watcher, _fragment in qualifying_sources
                    ),
                )
                for watcher, fragment in qualifying_sources:
                    self._enqueue_trigger(
                        event,
                        watcher,
                        fragment,
                        TriggerEffect.PERMANENT_LEFT_SELF_COUNTER,
                    )
        if source_zone == "battlefield" and destination != "battlefield":
            for occurrence in tuple(self.semantic_occurrences):
                watcher = self._objects.get(occurrence.object_id)
                fragment = occurrence.oracle_fragment
                self_departure = occurrence.object_id == obj.object_id and bool(
                    re.search(r"leaves the battlefield|\bdies\b", fragment)
                )
                controlled_departure = (
                    isinstance(watcher, Permanent)
                    and self.is_authoritative(watcher, "battlefield")
                    and watcher.controller == obj.controller
                    and bool(
                        re.search(
                            r"Whenever (?:a|another) (?:creature|permanent|artifact) you control "
                            r"(?:leaves the battlefield|is put into a graveyard from the "
                            r"battlefield)",
                            fragment,
                        )
                    )
                )
                another_departure = (
                    isinstance(watcher, Permanent)
                    and self.is_authoritative(watcher, "battlefield")
                    and watcher.object_id != obj.object_id
                    and fragment.startswith("Whenever another permanent leaves the battlefield,")
                )
                if self_departure or controlled_departure or another_departure:
                    self._new_opportunity_context(
                        "permanent_departed",
                        controller=occurrence.controller,
                        source_id=occurrence.object_id,
                        subject_ids=(obj.object_id,),
                        facts=(
                            ("destination_zone", destination),
                            ("source_zone", source_zone),
                        ),
                    )
        return replacement

    def change_controller(self, permanent: Permanent, controller: int) -> None:
        """Change control without changing owner or runtime object identity."""
        if controller not in range(2):
            raise ValueError("controller is invalid")
        if not self.is_authoritative(permanent, "battlefield"):
            raise ValueError("permanent is not on the battlefield")
        if controller == permanent.controller:
            return
        source = self.players[permanent.controller].battlefield
        source_index = next(
            index for index, candidate in enumerate(source) if candidate is permanent
        )
        source.pop(source_index)
        self.players[controller].battlefield.append(permanent)
        old_controller = permanent.controller
        permanent.controller = controller
        self.log(
            "controller_changed",
            object_id=permanent.object_id,
            card=permanent.card.name,
            owner=self.players[permanent.owner].name,
            old_controller=self.players[old_controller].name,
            controller=self.players[controller].name,
        )

    def log(self, event: str, **details: object) -> None:
        self.events.append(
            {
                "turn": self.turn,
                "phase": self.phase,
                "step": self.step.value,
                "event": event,
                **details,
            }
        )

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

    def report_unsupported_abilities(
        self,
        player_index: int,
        card: CardFact,
        *,
        source: CardObject | Permanent,
    ) -> None:
        """Report each unresolved Oracle line without interpreting or combining its meaning."""
        grouped: dict[str, list[str]] = {}
        for fragment, reason in self.interpreter.unsupported_fragments(card):
            grouped.setdefault(fragment, []).append(reason)
            self.unsupported(
                card,
                reason,
                player_index=player_index,
                oracle_fragment=fragment,
            )
        for fragment, reasons in grouped.items():
            occurrence = self._register_semantic_occurrence(
                source, player_index, fragment, tuple(sorted(set(reasons)))
            )
            self._witness_from_existing_events(occurrence)

    def _witness_resolved_unsupported_instructions(self, source: CardObject) -> None:
        """Mark the instruction point of an actually resolved unsupported spell."""
        if not self.is_authoritative(source, "graveyard"):
            raise ValueError("resolved-instruction evidence requires its graveyard object")
        for occurrence in tuple(self.semantic_occurrences):
            if occurrence.object_id != source.object_id:
                continue
            instruction_context = self._new_opportunity_context(
                "instruction_reached",
                controller=source.controller,
                source_id=source.object_id,
                subject_ids=(source.object_id,),
                facts=(
                    ("fragment_hash", occurrence.fragment_hash),
                    ("fragment_index", str(occurrence.fragment_index)),
                    ("instruction_source_zone", "graveyard"),
                    ("occurrence_id", occurrence.occurrence_id),
                    ("semantic_key", occurrence.semantic_key),
                ),
            )
            if self._unconstrained_creature_target_shape(occurrence.oracle_fragment):
                candidates = tuple(
                    permanent.object_id
                    for player in self.players
                    for permanent in player.battlefield
                    if permanent.card.is_creature
                )
                if candidates:
                    self._new_opportunity_context(
                        "target_choice_available",
                        controller=source.controller,
                        source_id=source.object_id,
                        subject_ids=candidates,
                        facts=(
                            ("candidate_kind", "battlefield_creature"),
                            ("instruction_context_id", instruction_context.context_id),
                            ("instruction_occurrence_id", occurrence.occurrence_id),
                        ),
                    )

    def _register_semantic_occurrence(
        self,
        source: CardObject | Permanent,
        controller: int,
        fragment: str,
        limitations: tuple[str, ...],
    ) -> SemanticOccurrence:
        if not self.is_authoritative(source, source.zone):
            raise ValueError("semantic presence requires an authoritative runtime object")
        fragments = self._semantic_fragments(source.card)
        try:
            fragment_index = fragments.index(fragment)
        except ValueError as error:
            raise ValueError("semantic presence fragment is not authoritative") from error
        key = semantic_key(source.card.oracle_id, 0, fragment_index, fragment)
        prior = next(
            (
                item
                for item in self.semantic_occurrences
                if item.object_id == source.object_id and item.semantic_key == key
            ),
            None,
        )
        if prior is not None:
            return prior
        occurrence = SemanticOccurrence(
            f"semantic-{self._next_semantic_occurrence_number:06d}",
            key,
            source.card.oracle_id,
            0,
            fragment_index,
            fragment_digest(fragment),
            source.object_id,
            controller,
            source.zone,
            fragment,
            limitations,
            self.turn,
            self.phase,
            self.step.value,
            self._next_event_number - 1,
        )
        self._next_semantic_occurrence_number += 1
        self.semantic_occurrences.append(occurrence)
        self.log(
            "semantic_present",
            occurrence_id=occurrence.occurrence_id,
            semantic_key=key,
            object_id=source.object_id,
            oracle_fragment=fragment,
            limitations=list(limitations),
        )
        return occurrence

    def _semantic_fragments(self, card: CardFact) -> tuple[str, ...]:
        """Authoritative Oracle lines plus normalized keyword facts absent from the text."""
        fragments = self.interpreter.fragments(card)
        return fragments + tuple(keyword for keyword in card.keywords if keyword not in fragments)

    def _new_opportunity_context(
        self,
        context_kind: str,
        *,
        controller: int,
        source_id: str,
        subject_ids: tuple[str, ...],
        facts: tuple[tuple[str, str], ...] = (),
        event_id: str | None = None,
        stack_object_id: str | None = None,
    ) -> AuthoritativeOpportunityContext:
        """Freeze one bounded rules context without executing its unsupported semantic."""
        if controller not in range(2) or source_id not in self._objects:
            raise ValueError("opportunity context source/controller is invalid")
        if any(subject_id not in self._objects for subject_id in subject_ids):
            raise ValueError("opportunity context contains a fabricated subject")
        if tuple(sorted(facts)) != facts or len({key for key, _value in facts}) != len(facts):
            raise ValueError("opportunity context facts must be unique and sorted")
        required_facts = {
            "activation_available": {
                "mana_required",
                "source_tap_required",
                "source_tapped",
                "timing",
            },
            "permanent_departed": {"destination_zone", "source_zone"},
            "artifact_dependency": {
                "affected_object_id",
                "artifact_count",
                "counted_artifact_ids",
                "excluded_source_id",
                "predicate",
            },
            "stack_response": {"response_cost", "target_is_creature"},
            "target_choice_available": {
                "candidate_kind",
                "instruction_context_id",
                "instruction_occurrence_id",
            },
            "replacement_evaluation": {"counter_type", "quantity"},
            "instruction_reached": {
                "fragment_hash",
                "fragment_index",
                "instruction_source_zone",
                "occurrence_id",
                "semantic_key",
            },
        }
        if (
            context_kind not in required_facts
            or {key for key, _value in facts} != required_facts[context_kind]
        ):
            raise ValueError("opportunity context lacks its required reconstructive facts")
        if event_id is not None and event_id not in self._rules_events:
            raise ValueError("opportunity context event is not authoritative")
        if stack_object_id is not None and not any(
            item.object_id == stack_object_id for item in self.stack
        ):
            raise ValueError("opportunity context stack object is not authoritative")
        prior = next(
            (
                item
                for item in self.opportunity_contexts
                if (
                    item.context_kind,
                    item.turn,
                    item.step,
                    item.source_id,
                    item.subject_ids,
                    item.facts,
                    item.event_id,
                    item.stack_object_id,
                )
                == (
                    context_kind,
                    self.turn,
                    self.step.value,
                    source_id,
                    subject_ids,
                    facts,
                    event_id,
                    stack_object_id,
                )
            ),
            None,
        )
        if prior is not None:
            return prior
        context_id = f"context-{self._next_opportunity_context_number:06d}"
        state_fingerprint = self.authoritative_state_fingerprint()
        subject_zones = tuple(self._objects[item].zone for item in subject_ids)
        context = AuthoritativeOpportunityContext(
            context_id=context_id,
            context_key=opportunity_context_key(
                context_id,
                context_kind,
                self.turn,
                self.phase,
                self.step.value,
                self.active_player,
                controller,
                source_id,
                subject_ids,
                subject_zones,
                facts,
                event_id,
                stack_object_id,
                state_fingerprint,
            ),
            context_kind=context_kind,
            turn=self.turn,
            phase=self.phase,
            step=self.step.value,
            active_player=self.active_player,
            controller=controller,
            source_id=source_id,
            subject_ids=subject_ids,
            subject_zones=subject_zones,
            facts=facts,
            event_id=event_id,
            stack_object_id=stack_object_id,
            state_fingerprint=state_fingerprint,
        )
        self._next_opportunity_context_number += 1
        self.opportunity_contexts.append(context)
        bound_occurrence_id = dict(facts).get("instruction_occurrence_id") or dict(facts).get(
            "occurrence_id"
        )
        for occurrence in tuple(self.semantic_occurrences):
            if occurrence.object_id == source_id and (
                bound_occurrence_id is None or occurrence.occurrence_id == bound_occurrence_id
            ):
                self._witness_from_context(occurrence, context)
        return context

    def _witness_from_context(
        self, occurrence: SemanticOccurrence, context: AuthoritativeOpportunityContext
    ) -> None:
        fragment = occurrence.oracle_fragment
        matches = {
            "activation_available": ":" in fragment,
            "permanent_departed": bool(
                re.search(r"leaves the battlefield|\bdies\b|put into a graveyard", fragment)
            ),
            "artifact_dependency": self._artifact_entry_dependency_shape(
                fragment, self._objects[occurrence.object_id].card.name
            ),
            "stack_response": bool(re.match(r"^Counter target (?:noncreature )?spell", fragment)),
            "target_choice_available": self._unconstrained_creature_target_shape(fragment),
            "replacement_evaluation": bool(
                re.search(r"\bwould\b|\binstead\b", fragment, re.IGNORECASE)
            ),
            "instruction_reached": occurrence.object_id in context.subject_ids,
        }
        if matches.get(context.context_kind, False):
            self._record_opportunity(
                occurrence,
                cause_kind="authoritative_context",
                cause_id=context.context_id,
                cause_subject_ids=context.subject_ids,
            )

    @staticmethod
    def _artifact_entry_dependency_shape(fragment: str, source_name: str) -> bool:
        """Return only artifact predicates reconstructed by one controlled artifact entry."""
        return Game._artifact_dependency_mode(fragment, source_name) is not None

    @staticmethod
    def _artifact_dependency_mode(fragment: str, source_name: str) -> str | None:
        if re.match(r"^Whenever an artifact you control enters,", fragment):
            return "artifact_entry_trigger"
        if re.fullmatch(
            re.escape(source_name) + r" gets [^.]+ for each other artifact you control\.",
            fragment,
        ):
            return "self_other_artifact_count"
        return None

    @staticmethod
    def _unconstrained_creature_target_shape(fragment: str) -> bool:
        """Return only one unconstrained battlefield-creature target instruction."""
        lowered = fragment.lower()
        if len(re.findall(r"\btarget\b", lowered)) != 1 or "target creature" not in lowered:
            return False
        incompatible = (
            "when ",
            "whenever ",
            "at the beginning",
            "if ",
            "artifact",
            "enchantment",
            "player",
            "spell",
            "target card",
            "creature card",
            "graveyard",
            "you control",
            "opponent controls",
            "with flying",
            "mana value",
            "power ",
            "toughness",
            "another target",
            "other target",
            "up to",
            "one or more",
            "and/or",
            "two target",
            "target permanent",
            "any target",
            "choose a ",
            ":",
        )
        return not any(marker in lowered for marker in incompatible)

    def _record_opportunity(
        self,
        occurrence: SemanticOccurrence,
        *,
        cause_kind: str,
        cause_id: str,
        cause_subject_ids: tuple[str, ...],
    ) -> OpportunityWitness:
        facts = self._validate_opportunity_applicability(
            occurrence,
            cause_kind=cause_kind,
            cause_id=cause_id,
            cause_subject_ids=cause_subject_ids,
        )
        opportunity_key = fragment_digest(
            "|".join((occurrence.occurrence_id, cause_kind, cause_id))
        )
        prior = next(
            (
                item
                for item in self.opportunity_witnesses
                if item.opportunity_key == opportunity_key
            ),
            None,
        )
        if prior is not None:
            return prior
        witness = OpportunityWitness(
            f"opportunity-{self._next_opportunity_witness_number:06d}",
            opportunity_key,
            occurrence.occurrence_id,
            occurrence.semantic_key,
            occurrence.object_id,
            facts[1],
            occurrence.oracle_fragment,
            self.turn,
            self.phase,
            self.step.value,
            cause_kind,
            cause_id,
            cause_subject_ids,
            facts[0],
            facts[1],
            facts[2],
            facts[3],
        )
        self._next_opportunity_witness_number += 1
        self.opportunity_witnesses.append(witness)
        self.log(
            "unsupported_opportunity_witnessed",
            witness_id=witness.witness_id,
            opportunity_key=opportunity_key,
            occurrence_id=occurrence.occurrence_id,
            semantic_key=occurrence.semantic_key,
            object_id=occurrence.object_id,
            oracle_fragment=occurrence.oracle_fragment,
            cause_kind=cause_kind,
            cause_id=cause_id,
            cause_subject_ids=list(cause_subject_ids),
        )
        return witness

    @staticmethod
    def _event_number(event_id: str) -> int:
        try:
            prefix, number = event_id.split("-", 1)
            if prefix != "event":
                raise ValueError
            return int(number)
        except (TypeError, ValueError) as error:
            raise ValueError("opportunity event identity is malformed") from error

    def _validate_opportunity_applicability(
        self,
        occurrence: SemanticOccurrence,
        *,
        cause_kind: str,
        cause_id: str,
        cause_subject_ids: tuple[str, ...],
        historical: OpportunityWitness | None = None,
    ) -> tuple[str, int, tuple[str, ...], str | None]:
        """Validate source and cause applicability for one supported witness shape."""
        source = self._objects.get(occurrence.object_id)
        if not isinstance(source, (CardObject, Permanent)):
            raise ValueError("opportunity source identity is not registered")
        fragments = self._semantic_fragments(source.card)
        if (
            occurrence.fragment_index >= len(fragments)
            or fragments[occurrence.fragment_index] != occurrence.oracle_fragment
            or fragment_digest(occurrence.oracle_fragment) != occurrence.fragment_hash
        ):
            raise ValueError("opportunity fragment does not match authoritative card data")

        live = historical is None
        if live and occurrence.controller != source.controller:
            raise ValueError("opportunity source controller is not authoritative")
        source_zone = source.zone if live else historical.source_zone
        source_controller = source.controller if live else historical.source_controller
        subject_zones = (
            tuple(self._objects[subject_id].zone for subject_id in cause_subject_ids)
            if live and all(subject_id in self._objects for subject_id in cause_subject_ids)
            else (() if live else historical.cause_subject_zones)
        )
        if len(subject_zones) != len(cause_subject_ids):
            raise ValueError("opportunity references a nonexistent subject")

        fragment = occurrence.oracle_fragment
        event_kind: str | None = None
        if cause_kind == "rules_event":
            event = self._rules_events.get(cause_id)
            if event is None or event.subject_ids != cause_subject_ids:
                raise ValueError("opportunity references a fabricated or mismatched event")
            event_kind = event.kind.value
            if historical is not None and (
                historical.turn != event.turn
                or historical.step != event.step
                or historical.cause_event_kind != event_kind
            ):
                raise ValueError("opportunity event provenance is inconsistent")
            battlefield_authority = dict(event.battlefield_authority)
            if battlefield_authority.get(occurrence.object_id) != source_controller:
                raise ValueError("event does not prove authoritative source presence")
            self_etb = (
                event.kind is RulesEventKind.CREATURE_ENTERED
                and bool(re.match(r"^When .+ enters,", fragment))
                and occurrence.object_id in event.subject_ids
                and self._event_number(event.event_id) == occurrence.registration_event_cursor
            )
            alliance = (
                event.kind is RulesEventKind.CREATURE_ENTERED
                and fragment.startswith("Alliance — Whenever another creature you control enters,")
                and occurrence.object_id not in event.subject_ids
                and event.player_index == source_controller
                and self._event_number(event.event_id) > occurrence.registration_event_cursor
            )
            attacks = (
                event.kind is RulesEventKind.ATTACKERS_DECLARED
                and bool(re.match(r"^Whenever .+ attacks,", fragment))
                and occurrence.object_id in event.subject_ids
                and event.player_index == source_controller
                and event.step == TurnStep.DECLARE_ATTACKERS.value
                and self._event_number(event.event_id) > occurrence.registration_event_cursor
            )
            if not (self_etb or alliance or attacks):
                raise ValueError("event does not establish semantic applicability")
            if source_zone != "battlefield":
                raise ValueError("event opportunity source was not on the battlefield")
        elif cause_kind == "legal_action_context":
            match = re.match(
                r"^During your turn, you may cast creature spells with power or toughness "
                r"(?P<limit>\d+) or less from your graveyard\.",
                fragment,
            )
            step = self.step.value if live else historical.step
            turn = self.turn if live else historical.turn
            expected_id = f"legal-main:{turn}:{step}:{source_controller}:" + ",".join(
                cause_subject_ids
            )
            if (
                match is None
                or source_zone != "battlefield"
                or step not in {TurnStep.PRECOMBAT_MAIN.value, TurnStep.POSTCOMBAT_MAIN.value}
                or cause_id != expected_id
                or any(zone != "graveyard" for zone in subject_zones)
            ):
                raise ValueError("legal-action context does not establish applicability")
            if live:
                limit = int(match.group("limit"))
                if source_controller != self.active_player or any(
                    not isinstance(self._objects.get(subject_id), CardObject)
                    or not self._objects[subject_id].card.is_creature
                    or self._objects[subject_id].card.power is None
                    or self._objects[subject_id].card.toughness is None
                    or (
                        self._objects[subject_id].card.power > limit
                        and self._objects[subject_id].card.toughness > limit
                    )
                    for subject_id in cause_subject_ids
                ):
                    raise ValueError("graveyard subject does not satisfy the permission")
        elif cause_kind == "legal_block_context":
            step = self.step.value if live else historical.step
            expected_id = (
                f"block:{historical.turn if historical else self.turn}:{step}:"
                + ":".join(cause_subject_ids)
            )
            if (
                not fragment.startswith("Menace ")
                or len(cause_subject_ids) != 2
                or cause_subject_ids[0] != occurrence.object_id
                or source_zone != "battlefield"
                or any(zone != "battlefield" for zone in subject_zones)
                or step != TurnStep.DECLARE_BLOCKERS.value
                or cause_id != expected_id
            ):
                raise ValueError("block context does not establish applicability")
            if live and occurrence.object_id not in self._combat_attackers:
                raise ValueError("block context attacker is not in authoritative combat")
        elif cause_kind == "authoritative_context":
            context = next(
                (item for item in self.opportunity_contexts if item.context_id == cause_id), None
            )
            if context is None or context.source_id != occurrence.object_id:
                raise ValueError("opportunity context does not authenticate its source")
            if context.subject_ids != cause_subject_ids:
                raise ValueError("opportunity context subjects are mismatched")
            if historical is not None and (
                historical.turn != context.turn
                or historical.step != context.step
                or historical.controller != context.controller
            ):
                raise ValueError("opportunity context provenance is inconsistent")
            source_zone = occurrence.zone
            source_controller = context.controller
            subject_zones = context.subject_zones
            allowed = {
                "activation_available": ":" in fragment,
                "permanent_departed": bool(
                    re.search(r"leaves the battlefield|\bdies\b|put into a graveyard", fragment)
                ),
                "artifact_dependency": self._artifact_entry_dependency_shape(
                    fragment, source.card.name
                ),
                "stack_response": bool(
                    re.match(r"^Counter target (?:noncreature )?spell", fragment)
                ),
                "target_choice_available": self._unconstrained_creature_target_shape(fragment),
                "replacement_evaluation": bool(
                    re.search(r"\bwould\b|\binstead\b", fragment, re.IGNORECASE)
                ),
                "instruction_reached": occurrence.object_id in context.subject_ids,
            }
            if not allowed.get(context.context_kind, False):
                raise ValueError("opportunity context does not establish fragment applicability")
            if context.event_id is not None and context.event_id not in self._rules_events:
                raise ValueError("opportunity context event provenance is missing")
            if context.stack_object_id is not None and context.stack_object_id not in self._objects:
                raise ValueError("opportunity context stack provenance is missing")
            context_facts = dict(context.facts)
            if context.context_kind == "activation_available" and not (
                context.step in {TurnStep.PRECOMBAT_MAIN.value, TurnStep.POSTCOMBAT_MAIN.value}
                and context.source_id == context.subject_ids[0]
                and context.subject_zones
                and all(zone == "battlefield" for zone in context.subject_zones)
                and context_facts.get("timing") == context.step
                and (
                    context_facts.get("source_tap_required") == "false"
                    or context_facts.get("source_tapped") == "false"
                )
                and context_facts.get("mana_required") == str(len(context.subject_ids) - 1)
            ):
                raise ValueError("activation context facts do not prove availability")
            if context.context_kind == "permanent_departed" and not (
                context_facts.get("source_zone") == "battlefield"
                and context_facts.get("destination_zone") in {"hand", "library", "graveyard"}
                and context.subject_zones == ("former",)
            ):
                raise ValueError("departure context facts do not prove zone movement")
            if context.context_kind == "artifact_dependency":
                event = self._rules_events.get(context.event_id or "")
                mode = self._artifact_dependency_mode(fragment, source.card.name)
                event_artifacts = (
                    ()
                    if event is None
                    else tuple(
                        sorted(
                            object_id
                            for object_id, controller in event.battlefield_authority
                            if controller == context.controller
                            and "Artifact" in self._objects[object_id].card.type_line
                            and not (
                                mode == "self_other_artifact_count"
                                and object_id == context.source_id
                            )
                        )
                    )
                )
                if not (
                    mode in {"artifact_entry_trigger", "self_other_artifact_count"}
                    and context_facts.get("predicate") == mode
                    and (mode != "self_other_artifact_count" or "Artifact" in source.card.type_line)
                    and event is not None
                    and event.kind is RulesEventKind.CREATURE_ENTERED
                    and set(context.subject_ids).issubset(event.subject_ids)
                    and all(
                        "Artifact" in self._objects[subject_id].card.type_line
                        for subject_id in context.subject_ids
                    )
                    and context_facts.get("affected_object_id") == context.source_id
                    and context_facts.get("artifact_count") == str(len(event_artifacts))
                    and context_facts.get("counted_artifact_ids") == ",".join(event_artifacts)
                    and context_facts.get("excluded_source_id")
                    == (context.source_id if mode == "self_other_artifact_count" else "")
                ):
                    raise ValueError("artifact context facts do not prove its predicate")
            if context.context_kind == "stack_response" and not (
                source_zone == "hand"
                and context.stack_object_id in context.subject_ids
                and context.subject_zones == ("stack",)
                and context_facts.get("response_cost") == source.card.mana_cost
                and context_facts.get("target_is_creature") in {"true", "false"}
            ):
                raise ValueError("response context facts do not prove Stack availability")
            if context.context_kind == "target_choice_available" and not (
                context_facts.get("candidate_kind") == "battlefield_creature"
                and source_zone == "graveyard"
                and context.subject_ids
                and all(zone == "battlefield" for zone in context.subject_zones)
                and any(
                    prior.context_id == context_facts.get("instruction_context_id")
                    and prior.context_kind == "instruction_reached"
                    and prior.source_id == context.source_id
                    and prior.turn == context.turn
                    and prior.step == context.step
                    and dict(prior.facts).get("occurrence_id")
                    == context_facts.get("instruction_occurrence_id")
                    == occurrence.occurrence_id
                    for prior in self.opportunity_contexts
                )
            ):
                raise ValueError("target/choice context facts do not prove candidates")
            if context.context_kind == "replacement_evaluation" and not (
                context_facts.get("counter_type")
                and context_facts.get("quantity", "").isdecimal()
                and int(context_facts["quantity"]) > 0
                and context.subject_zones == ("battlefield",)
            ):
                raise ValueError("replacement context facts do not prove evaluation")
            if context.context_kind == "instruction_reached" and not (
                context_facts.get("instruction_source_zone") == "graveyard"
                and context.subject_ids == (context.source_id,)
                and context.subject_zones == ("graveyard",)
                and context_facts.get("occurrence_id") == occurrence.occurrence_id
                and context_facts.get("semantic_key") == occurrence.semantic_key
                and context_facts.get("fragment_hash") == occurrence.fragment_hash
                and context_facts.get("fragment_index") == str(occurrence.fragment_index)
            ):
                raise ValueError("instruction context facts do not prove resolution reach")
        else:
            raise ValueError("opportunity cause kind is unsupported")
        return source_zone, source_controller, subject_zones, event_kind

    def _witness_from_event(self, occurrence: SemanticOccurrence, event: RulesEvent) -> None:
        fragment = occurrence.oracle_fragment
        source_id = occurrence.object_id
        source = self._objects.get(source_id)
        source_is_live = isinstance(source, Permanent) and self.is_authoritative(
            source, "battlefield"
        )
        if event.kind is RulesEventKind.CREATURE_ENTERED:
            self_enters = (
                bool(re.match(r"^When .+ enters,", fragment)) and source_id in event.subject_ids
            )
            alliance = fragment.startswith(
                "Alliance — Whenever another creature you control enters,"
            )
            if self_enters or (
                alliance
                and source_is_live
                and event.player_index == source.controller
                and source_id not in event.subject_ids
            ):
                self._record_opportunity(
                    occurrence,
                    cause_kind="rules_event",
                    cause_id=event.event_id,
                    cause_subject_ids=event.subject_ids,
                )
        elif (
            event.kind is RulesEventKind.ATTACKERS_DECLARED
            and bool(re.match(r"^Whenever .+ attacks,", fragment))
            and source_is_live
            and source_id in event.subject_ids
        ):
            self._record_opportunity(
                occurrence,
                cause_kind="rules_event",
                cause_id=event.event_id,
                cause_subject_ids=event.subject_ids,
            )

    def _witness_from_existing_events(self, occurrence: SemanticOccurrence) -> None:
        """Join only the source's own just-completed ETB; never retroactively infer reach."""
        for event in self._rules_events.values():
            if (
                event.kind is RulesEventKind.CREATURE_ENTERED
                and occurrence.object_id in event.subject_ids
                and bool(re.match(r"^When .+ enters,", occurrence.oracle_fragment))
                and self._event_number(event.event_id) == occurrence.registration_event_cursor
            ):
                self._witness_from_event(occurrence, event)

    def _new_rules_event(
        self,
        kind: RulesEventKind,
        player_index: int,
        subject_ids: tuple[str, ...],
        *,
        source_id: str | None = None,
        target_player: int | None = None,
        amount: int | None = None,
        battlefield_authority: tuple[tuple[str, int], ...] | None = None,
        battlefield_characteristics: tuple[tuple[str, int, str], ...] | None = None,
        last_known_battlefield: tuple[tuple[str, int, str, bool], ...] = (),
    ) -> RulesEvent:
        event = RulesEvent(
            f"event-{self._next_event_number:06d}",
            kind,
            player_index,
            subject_ids,
            source_id,
            target_player,
            amount,
            self.turn,
            self.step.value,
            self.active_player,
            (
                tuple(
                    (permanent.object_id, permanent.controller)
                    for player in self.players
                    for permanent in player.battlefield
                )
                if battlefield_authority is None
                else battlefield_authority
            ),
            (
                self._battlefield_characteristics_snapshot()
                if battlefield_characteristics is None
                else battlefield_characteristics
            ),
            last_known_battlefield,
        )
        self._next_event_number += 1
        self._rules_events[event.event_id] = event
        self._rules_event_evidence.append(
            RulesEventEvidence(
                event.event_id,
                self._event_number(event.event_id),
                event.kind,
                event.player_index,
                event.subject_ids,
                event.source_id,
                event.target_player,
                event.amount,
                event.turn,
                event.step,
                event.active_player,
                event.battlefield_authority,
                event.battlefield_characteristics,
                event.last_known_battlefield,
            )
        )
        self.log(
            "rules_event",
            event_id=event.event_id,
            rules_event=event.kind.value,
            player=self.players[player_index].name,
            subject_ids=list(subject_ids),
            source_id=source_id,
            target_player=target_player,
            amount=amount,
            event_turn=event.turn,
            event_step=event.step,
            event_active_player=event.active_player,
            battlefield_authority=[
                {"object_id": object_id, "controller": controller}
                for object_id, controller in event.battlefield_authority
            ],
            battlefield_characteristics=[
                {
                    "object_id": object_id,
                    "controller": controller,
                    "type_line": type_line,
                }
                for object_id, controller, type_line in event.battlefield_characteristics
            ],
            last_known_battlefield=[
                {
                    "object_id": object_id,
                    "controller": controller,
                    "type_line": type_line,
                    "is_creature": is_creature,
                }
                for object_id, controller, type_line, is_creature in event.last_known_battlefield
            ],
        )
        for occurrence in tuple(self.semantic_occurrences):
            self._witness_from_event(occurrence, event)
        if kind is RulesEventKind.CREATURE_ENTERED:
            event_characteristics = {
                object_id: (controller, type_line)
                for object_id, controller, type_line in event.battlefield_characteristics
            }
            artifact_ids = tuple(
                subject_id
                for subject_id in subject_ids
                if subject_id in event_characteristics
                and "Artifact" in event_characteristics[subject_id][1]
            )
            if artifact_ids:
                for occurrence in tuple(self.semantic_occurrences):
                    source = self._objects.get(occurrence.object_id)
                    mode = (
                        None
                        if source is None
                        else self._artifact_dependency_mode(
                            occurrence.oracle_fragment, source.card.name
                        )
                    )
                    if (
                        mode is not None
                        and isinstance(source, Permanent)
                        and self.is_authoritative(source, "battlefield")
                        and source.controller == player_index
                        and (
                            mode != "self_other_artifact_count"
                            or "Artifact" in event_characteristics[source.object_id][1]
                        )
                    ):
                        counted_ids = tuple(
                            sorted(
                                object_id
                                for object_id, controller in event.battlefield_authority
                                if controller == player_index
                                and object_id in event_characteristics
                                and "Artifact" in event_characteristics[object_id][1]
                                and not (
                                    mode == "self_other_artifact_count"
                                    and object_id == source.object_id
                                )
                            )
                        )
                        self._new_opportunity_context(
                            "artifact_dependency",
                            controller=source.controller,
                            source_id=source.object_id,
                            subject_ids=artifact_ids,
                            facts=(
                                ("affected_object_id", source.object_id),
                                ("artifact_count", str(len(counted_ids))),
                                ("counted_artifact_ids", ",".join(counted_ids)),
                                (
                                    "excluded_source_id",
                                    source.object_id if mode == "self_other_artifact_count" else "",
                                ),
                                ("predicate", mode),
                            ),
                            event_id=event.event_id,
                        )
        return event

    def _authenticate_original_rules_event(self, event: RulesEvent) -> RulesEventEvidence:
        """Join one derived typed event back to its independent creation-time evidence."""
        records = [item for item in self._rules_event_evidence if item.event_id == event.event_id]
        ledger = [
            item
            for item in self.events
            if item.get("event") == "rules_event" and item.get("event_id") == event.event_id
        ]
        if len(records) != 1 or len(ledger) != 1:
            raise ValueError("rules event lacks unique original evidence")
        evidence = records[0]
        expected = (
            evidence.event_id,
            evidence.kind,
            evidence.player_index,
            evidence.subject_ids,
            evidence.source_id,
            evidence.target_player,
            evidence.amount,
            evidence.turn,
            evidence.step,
            evidence.active_player,
            evidence.battlefield_authority,
            evidence.battlefield_characteristics,
            evidence.last_known_battlefield,
        )
        actual = (
            event.event_id,
            event.kind,
            event.player_index,
            event.subject_ids,
            event.source_id,
            event.target_player,
            event.amount,
            event.turn,
            event.step,
            event.active_player,
            event.battlefield_authority,
            event.battlefield_characteristics,
            event.last_known_battlefield,
        )
        log = ledger[0]
        serialized_authority = tuple(
            (item.get("object_id"), item.get("controller"))
            for item in log.get("battlefield_authority", [])
        )
        serialized_characteristics = tuple(
            (
                item.get("object_id"),
                item.get("controller"),
                item.get("type_line"),
            )
            for item in log.get("battlefield_characteristics", [])
        )
        serialized_last_known = tuple(
            (
                item.get("object_id"),
                item.get("controller"),
                item.get("type_line"),
                item.get("is_creature"),
            )
            for item in log.get("last_known_battlefield", [])
        )
        if (
            expected != actual
            or evidence.event_cursor != self._event_number(event.event_id)
            or log.get("rules_event") != evidence.kind.value
            or log.get("subject_ids") != list(evidence.subject_ids)
            or log.get("source_id") != evidence.source_id
            or log.get("target_player") != evidence.target_player
            or log.get("amount") != evidence.amount
            or log.get("event_turn") != evidence.turn
            or log.get("event_step") != evidence.step
            or log.get("event_active_player") != evidence.active_player
            or serialized_authority != evidence.battlefield_authority
            or serialized_characteristics != evidence.battlefield_characteristics
            or serialized_last_known != evidence.last_known_battlefield
        ):
            raise ValueError("rules event disagrees with immutable original evidence")
        return evidence

    def deal_damage(
        self, transaction: DamageTransaction, *, defer_post_damage: bool = False
    ) -> RulesEvent:
        """Validate and atomically apply one bounded noncombat damage transaction."""
        if not isinstance(transaction, DamageTransaction):
            raise ValueError("damage requires a typed transaction")
        if transaction.controller not in range(2):
            raise ValueError("damage controller is invalid")
        if not isinstance(transaction.amount, int) or isinstance(transaction.amount, bool):
            raise ValueError("damage amount must be an integer")
        if transaction.amount <= 0:
            raise ValueError("damage amount must be positive")
        source = transaction.source
        source_authoritative = self.is_authoritative(
            source, "battlefield"
        ) or self.is_authoritative(source, "stack")
        if not source_authoritative:
            raise ValueError("damage source is not authoritative")
        if transaction.controller != source.controller:
            raise ValueError("damage controller does not control its source")

        target: Permanent | None = None
        target_player = transaction.target_player
        if transaction.target_kind is DamageTargetKind.PLAYER:
            if target_player not in range(2) or transaction.target is not None:
                raise ValueError("damage player target is invalid")
        elif transaction.target_kind is DamageTargetKind.CREATURE:
            candidate = transaction.target
            if (
                not isinstance(candidate, Permanent)
                or not self.is_authoritative(candidate, "battlefield")
                or not candidate.card.is_creature
                or target_player is not None
            ):
                raise ValueError("damage creature target is invalid")
            target = candidate
        else:
            raise ValueError("damage target kind is unsupported")

        if target is not None:
            target.damage += transaction.amount
            subject_ids = (target.object_id,)
        else:
            assert target_player is not None
            self.players[target_player].life -= transaction.amount
            subject_ids = ()
        event = self._new_rules_event(
            RulesEventKind.DAMAGE_DEALT,
            transaction.controller,
            subject_ids,
            source_id=source.object_id,
            target_player=target_player,
            amount=transaction.amount,
        )
        self.log(
            "damage_dealt",
            event_id=event.event_id,
            source_id=source.object_id,
            source_card=source.card.name,
            target_id=None if target is None else target.object_id,
            target_player=(None if target_player is None else self.players[target_player].name),
            amount=transaction.amount,
            oracle_fragment=transaction.oracle_fragment,
            combat=False,
        )
        lifelink_applied = self.evaluated_lifelink(source)
        if lifelink_applied:
            self._apply_lifelink_result(
                source,
                transaction.amount,
                combat=False,
                damage_step=None,
                target_ids=subject_ids,
                target_players=(() if target_player is None else (target_player,)),
            )
        if not defer_post_damage:
            self.check_state_based_actions()
            self.check_life()
            if lifelink_applied:
                self._put_pending_triggers_on_stack()
                self._drain_triggered_abilities()
        return event

    def choose_hand_bottom_draw(
        self, player_index: int, program: HandBottomDrawProgram
    ) -> HandBottomDrawPlan:
        """Validate a private optional choice without mutating authoritative state."""
        if player_index not in range(2) or not isinstance(program, HandBottomDrawProgram):
            raise ValueError("hand-bottom Draw program is invalid")
        if not program.executable:
            raise ValueError("hand-bottom Draw program is not executable")
        player = self.players[player_index]
        hand_objects_before = tuple(player.hand)
        library_objects_before = tuple(player.library)
        hand_before = tuple(card.object_id for card in player.hand)
        library_before = tuple(card.object_id for card in player.library)
        view = HandBottomDrawView(
            player_index,
            tuple((card.object_id, card.card.name) for card in player.hand),
        )
        options = (HandBottomDrawOption(None),) + tuple(
            HandBottomDrawOption(card.object_id) for card in player.hand
        )
        try:
            choice = self.hand_bottom_draw_chooser(view, options)
            if not isinstance(choice, HandBottomDrawOption) or choice not in options:
                raise ValueError("hand-bottom Draw chooser must return one listed option")
            if (
                tuple(card.object_id for card in player.hand) != hand_before
                or tuple(card.object_id for card in player.library) != library_before
            ):
                raise ValueError("hand-bottom Draw choice mutated authoritative zones")
        except Exception:
            player.hand[:] = hand_objects_before
            player.library[:] = library_objects_before
            raise
        selected = None
        if choice.card_id is not None:
            selected = next(
                (card for card in player.hand if card.object_id == choice.card_id), None
            )
            if selected is None or not self.is_authoritative(selected, "hand"):
                raise ValueError("hand-bottom Draw selection is stale")
        return HandBottomDrawPlan(
            choice,
            selected,
            tuple(option.card_id for option in options),
            hand_before,
            library_before,
        )

    def commit_hand_bottom_draw(
        self,
        player_index: int,
        program: HandBottomDrawProgram,
        plan: HandBottomDrawPlan,
        *,
        source_id: str,
        oracle_fragment: str,
    ) -> HandBottomDrawEvidence:
        """Commit the selected move, then its conditional draw, in Oracle order."""
        if not isinstance(plan, HandBottomDrawPlan):
            raise ValueError("hand-bottom Draw plan is invalid")
        choice = plan.choice
        selected = plan.selected
        player = self.players[player_index]
        if (
            tuple(card.object_id for card in player.hand) != plan.pre_hand_ids
            or tuple(card.object_id for card in player.library) != plan.pre_library_ids
        ):
            raise ValueError("hand-bottom Draw plan became stale")
        if choice.card_id is None:
            event = self._new_rules_event(RulesEventKind.HAND_BOTTOM_DRAW, player_index, ())
            evidence = HandBottomDrawEvidence(
                event.event_id,
                player_index,
                source_id,
                oracle_fragment,
                plan.offered_choice_ids,
                plan.pre_hand_ids,
                plan.pre_library_ids,
                None,
                None,
                False,
                False,
                None,
                None,
                plan.pre_hand_ids,
                plan.pre_library_ids,
                True,
            )
        else:
            if selected is None or not self.is_authoritative(selected, "hand"):
                raise ValueError("hand-bottom Draw selected card became stale")
            bottom = self.move_object(
                selected,
                "library",
                reason="optional_hand_bottom_filter",
                library_position="bottom",
            )
            assert isinstance(bottom, CardObject)
            draw_source_id = player.library[-1].object_id
            assert program.draw_quantity is not None
            if not self.draw(player, program.draw_quantity):
                raise AssertionError("selected card guarantees a nonempty library")
            drawn = player.hand[-1]
            event = self._new_rules_event(
                RulesEventKind.HAND_BOTTOM_DRAW,
                player_index,
                (bottom.object_id, drawn.object_id),
                source_id=source_id,
            )
            evidence = HandBottomDrawEvidence(
                event.event_id,
                player_index,
                source_id,
                oracle_fragment,
                plan.offered_choice_ids,
                plan.pre_hand_ids,
                plan.pre_library_ids,
                choice.card_id,
                bottom.object_id,
                True,
                True,
                draw_source_id,
                drawn.object_id,
                tuple(card.object_id for card in player.hand),
                tuple(card.object_id for card in player.library),
                False,
            )
        self.hand_bottom_draw_evidence.append(evidence)
        self.log(
            "hand_bottom_draw_committed",
            event_id=evidence.event_id,
            player=player.name,
            source_id=source_id,
            oracle_fragment=oracle_fragment,
            offered_choice_ids=list(evidence.offered_choice_ids),
            pre_hand_ids=list(evidence.pre_hand_ids),
            pre_library_ids=list(evidence.pre_library_ids),
            selected_hand_id=evidence.selected_hand_id,
            library_bottom_id=evidence.library_bottom_id,
            movement_succeeded=evidence.movement_succeeded,
            conditional_draw_performed=evidence.conditional_draw_performed,
            drawn_library_id=evidence.drawn_library_id,
            drawn_hand_id=evidence.drawn_hand_id,
            post_hand_ids=list(evidence.post_hand_ids),
            post_library_ids=list(evidence.post_library_ids),
            declined=evidence.declined,
        )
        return evidence

    def choose_discard_draw(
        self, player_index: int, program: DiscardDrawProgram
    ) -> DiscardDrawPlan:
        """Obtain and validate the optional discard at resolution time."""
        if player_index not in range(2) or not isinstance(program, DiscardDrawProgram):
            raise ValueError("discard/Draw program is invalid")
        if not program.executable:
            raise ValueError("discard/Draw program is not executable")
        player = self.players[player_index]
        hand_objects = tuple(player.hand)
        library_objects = tuple(player.library)
        graveyard_objects = tuple(player.graveyard)
        hand_ids = tuple(card.object_id for card in hand_objects)
        library_ids = tuple(card.object_id for card in library_objects)
        graveyard_ids = tuple(card.object_id for card in graveyard_objects)
        view = DiscardDrawView(
            player_index, tuple((card.object_id, card.card.name) for card in player.hand)
        )
        options = (DiscardDrawOption(None),) + tuple(
            DiscardDrawOption(card.object_id) for card in player.hand
        )
        try:
            choice = self.discard_draw_chooser(view, options)
            if not isinstance(choice, DiscardDrawOption) or choice not in options:
                raise ValueError("discard/Draw chooser must return one listed option")
            if (
                tuple(player.hand) != hand_objects
                or tuple(player.library) != library_objects
                or tuple(player.graveyard) != graveyard_objects
            ):
                raise ValueError("discard/Draw choice mutated authoritative zones")
        except Exception:
            player.hand[:] = hand_objects
            player.library[:] = library_objects
            player.graveyard[:] = graveyard_objects
            raise
        selected = (
            None
            if choice.card_id is None
            else next((card for card in player.hand if card.object_id == choice.card_id), None)
        )
        if choice.card_id is not None and (
            selected is None or not self.is_authoritative(selected, "hand")
        ):
            raise ValueError("discard/Draw selection is stale")
        return DiscardDrawPlan(
            choice,
            selected,
            tuple(option.card_id for option in options),
            hand_ids,
            library_ids,
            graveyard_ids,
        )

    def commit_discard_draw(
        self,
        player_index: int,
        program: DiscardDrawProgram,
        plan: DiscardDrawPlan,
        *,
        trigger: TriggeredAbilityObject,
    ) -> DiscardDrawEvidence:
        """Commit Discard then its dependent Draw in authoritative instruction order."""
        if not isinstance(plan, DiscardDrawPlan) or not program.executable:
            raise ValueError("discard/Draw plan is invalid")
        provenance = self._discard_draw_attack_provenance(trigger)
        if trigger.controller != player_index:
            raise ValueError("discard/Draw trigger controller is mismatched")
        player = self.players[player_index]
        if (
            tuple(card.object_id for card in player.hand) != plan.pre_hand_ids
            or tuple(card.object_id for card in player.library) != plan.pre_library_ids
            or tuple(card.object_id for card in player.graveyard) != plan.pre_graveyard_ids
        ):
            raise ValueError("discard/Draw plan became stale")
        selected = plan.selected
        discarded_id = None
        pre_draw_top = None
        drawn_id = None
        movement_succeeded = False
        draw_performed = False
        if plan.choice.card_id is not None:
            if selected is None or not self.is_authoritative(selected, "hand"):
                raise ValueError("discard/Draw selected card became stale")
            discarded = self.move_object(selected, "graveyard", reason="optional_discard")
            assert isinstance(discarded, CardObject)
            discarded_id = discarded.object_id
            movement_succeeded = True
            pre_draw_top = player.library[-1].object_id if player.library else None
            assert program.draw_quantity is not None
            draw_performed = self.draw(player, program.draw_quantity)
            if draw_performed:
                drawn_id = player.hand[-1].object_id
        event = self._new_rules_event(
            RulesEventKind.DISCARD_DRAW,
            player_index,
            tuple(object_id for object_id in (discarded_id, drawn_id) if object_id is not None),
            source_id=trigger.source_id,
        )
        evidence = DiscardDrawEvidence(
            event.event_id,
            player_index,
            provenance,
            trigger.object_id,
            trigger.source_id,
            trigger.oracle_fragment,
            plan.offered_choice_ids,
            plan.pre_hand_ids,
            plan.pre_library_ids,
            plan.pre_graveyard_ids,
            plan.choice.card_id,
            discarded_id,
            movement_succeeded,
            draw_performed,
            pre_draw_top,
            drawn_id,
            tuple(card.object_id for card in player.hand),
            tuple(card.object_id for card in player.library),
            tuple(card.object_id for card in player.graveyard),
            plan.choice.card_id is None,
        )
        self.discard_draw_evidence.append(evidence)
        self.log(
            "discard_draw_committed",
            event_id=evidence.event_id,
            attack_event_id=provenance.event_id,
            attack_event_kind=provenance.event_kind.value,
            attack_subject_ids=list(provenance.subject_ids),
            attack_turn=provenance.turn,
            attack_step=provenance.step,
            stack_object_id=trigger.object_id,
            source_id=trigger.source_id,
            player=player.name,
            oracle_fragment=trigger.oracle_fragment,
            selected_hand_id=evidence.selected_hand_id,
            discarded_graveyard_id=evidence.discarded_graveyard_id,
            movement_succeeded=evidence.movement_succeeded,
            conditional_draw_performed=evidence.conditional_draw_performed,
            pre_draw_top_id=evidence.pre_draw_top_id,
            drawn_hand_id=evidence.drawn_hand_id,
            declined=evidence.declined,
        )
        return evidence

    def _discard_draw_attack_provenance(
        self, trigger: TriggeredAbilityObject
    ) -> AttackTriggerProvenance:
        """Validate and freeze the attack event carried by one authoritative trigger."""
        if (
            not isinstance(trigger, TriggeredAbilityObject)
            or self._objects.get(trigger.object_id) is not trigger
            or trigger.zone != "former"
            or trigger.effect is not TriggerEffect.DISCARD_DRAW
            or any(
                evidence.stack_object_id == trigger.object_id
                for evidence in self.discard_draw_evidence
            )
        ):
            raise ValueError("discard/Draw provenance requires its resolving trigger object")
        event = trigger.event
        if (
            event.kind is not RulesEventKind.ATTACKERS_DECLARED
            or event.step != TurnStep.DECLARE_ATTACKERS.value
            or event.player_index != trigger.controller
            or event.active_player != trigger.controller
            or event.subject_ids.count(trigger.source_id) != 1
        ):
            raise ValueError("discard/Draw trigger has mismatched attack provenance")
        return AttackTriggerProvenance(
            event.event_id,
            event.kind,
            event.player_index,
            event.subject_ids,
            trigger.source_id,
            trigger.controller,
            event.turn,
            event.step,
            event.active_player,
        )

    @staticmethod
    def legal_scry_options(inspected: tuple[CardObject, ...]) -> tuple[ScryOption, ...]:
        """Enumerate every partition and ordering without exposing authoritative objects."""
        object_ids = tuple(card.object_id for card in inspected)
        options = {
            ScryOption(order[:top_count], order[top_count:])
            for order in permutations(object_ids)
            for top_count in range(len(object_ids) + 1)
        }
        if not object_ids:
            options.add(ScryOption((), ()))
        return tuple(sorted(options, key=lambda option: (option.top_ids, option.bottom_ids)))

    def scry(
        self,
        player_index: int,
        program: ScryProgram,
        *,
        source_card: str,
        oracle_fragment: str,
        source_id: str | None = None,
    ) -> ScryOption:
        """Transactionally perform one fixed-number Scry using authoritative library objects."""
        if player_index not in range(2):
            raise ValueError("Scry player is invalid")
        if not isinstance(program, ScryProgram) or not program.executable:
            raise ValueError("Scry program is not executable")
        assert program.amount is not None
        library = self.players[player_index].library
        inspected = tuple(reversed(library[-min(program.amount, len(library)) :]))
        before = tuple(library)
        view = ScryView(
            player_index,
            program.amount,
            tuple((card.object_id, card.card.name) for card in inspected),
        )
        options = self.legal_scry_options(inspected)
        try:
            choice = self.scry_chooser(view, options)

            if not isinstance(choice, ScryOption) or choice not in options:
                raise ValueError("Scry chooser must return one listed option")
            if tuple(library) != before or any(
                self._objects.get(card.object_id) is not card
                or not self.is_authoritative(card, "library")
                for card in inspected
            ):
                raise ValueError("Scry library or inspected identity became stale")
            selected_ids = choice.top_ids + choice.bottom_ids
            if len(set(selected_ids)) != len(inspected) or set(selected_ids) != {
                card.object_id for card in inspected
            }:
                raise ValueError("Scry choice must contain each inspected card exactly once")
        except Exception:
            library[:] = before
            raise

        by_id = {card.object_id: card for card in inspected}
        inspected_identities = {id(card) for card in inspected}
        uninspected = [card for card in library if id(card) not in inspected_identities]
        replacement = (
            [by_id[object_id] for object_id in choice.bottom_ids]
            + uninspected
            + [by_id[object_id] for object_id in reversed(choice.top_ids)]
        )
        if len(replacement) != len(before) or {id(card) for card in replacement} != {
            id(card) for card in before
        }:
            raise AssertionError("Scry transaction changed library membership")
        library[:] = replacement

        event = self._new_rules_event(
            RulesEventKind.SCRIED,
            player_index,
            tuple(card.object_id for card in inspected),
        )
        evidence = ScryEvidence(
            event.event_id,
            player_index,
            program.amount,
            tuple(card.object_id for card in inspected),
            choice.top_ids,
            choice.bottom_ids,
            source_card,
            oracle_fragment,
            source_id,
        )
        self.scry_evidence.append(evidence)
        self.log(
            "scry_committed",
            event_id=evidence.event_id,
            player=self.players[player_index].name,
            requested=evidence.requested,
            inspected=len(evidence.inspected_ids),
            inspected_ids=list(evidence.inspected_ids),
            top_ids=list(evidence.top_ids),
            bottom_ids=list(evidence.bottom_ids),
            source_card=evidence.source_card,
            source_id=evidence.source_id,
            oracle_fragment=evidence.oracle_fragment,
        )
        return choice

    def _validate_permanent_left_counter_provenance(
        self,
        *,
        controller: int,
        source_id: str,
        source_card: CardFact,
        oracle_fragment: str,
        event: RulesEvent,
        trigger_id: str | None = None,
    ) -> Permanent | None:
        """Authenticate the exact source and departed permanent from frozen leave evidence."""
        source = self._objects.get(source_id)
        coverage = self.interpreter.permanent_left_self_counter_semantic_coverage(
            source_card, oracle_fragment
        )
        last_known = {item[0]: item for item in event.last_known_battlefield}
        departed_id = event.subject_ids[0] if len(event.subject_ids) == 1 else None
        departure_records = [
            item
            for item in self.events
            if item.get("event") == "zone_changed"
            and item.get("source_object_id") == departed_id
            and item.get("source_zone") == "battlefield"
            and item.get("destination_zone") != "battlefield"
        ]
        source_lki = last_known.get(source_id)
        departed_lki = last_known.get(departed_id or "")
        trigger = None if trigger_id is None else self._triggers.get(trigger_id)
        if (
            coverage is None
            or not coverage.fully_supported
            or event.kind is not RulesEventKind.PERMANENT_LEFT
            or self._rules_events.get(event.event_id) is not event
            or event.source_id != departed_id
            or departed_id is None
            or departed_id == source_id
            or len(departure_records) != 1
            or source_lki is None
            or departed_lki is None
            or source_lki[1] != controller
            or not source_lki[2]
            or not departed_lki[2]
            or (source_id, controller) not in event.battlefield_authority
            or (departed_id, departed_lki[1]) not in event.battlefield_authority
            or not isinstance(source, Permanent)
            or source.card is not source_card
            or source.zone not in {"battlefield", "former"}
            or (
                trigger_id is not None
                and (
                    trigger is None
                    or trigger.controller != controller
                    or trigger.source_id != source_id
                    or trigger.source_card is not source_card
                    or trigger.oracle_fragment != oracle_fragment
                    or trigger.effect is not TriggerEffect.PERMANENT_LEFT_SELF_COUNTER
                    or trigger.event is not event
                )
            )
        ):
            raise ValueError("permanent-left counter trigger has mismatched provenance")
        return source if self.is_authoritative(source, "battlefield") else None

    def _enqueue_trigger(
        self,
        event: RulesEvent,
        source: Permanent,
        fragment: str,
        effect: TriggerEffect,
    ) -> None:
        if effect is TriggerEffect.PERMANENT_LEFT_SELF_COUNTER:
            self._validate_permanent_left_counter_provenance(
                controller=source.controller,
                source_id=source.object_id,
                source_card=source.card,
                oracle_fragment=fragment,
                event=event,
            )
        if effect is TriggerEffect.ETB_ARTIFACT_DRAW:
            self._validate_etb_artifact_draw_provenance(
                controller=source.controller,
                source_id=source.object_id,
                source_card=source.card,
                oracle_fragment=fragment,
                event=event,
                require_current_condition=False,
            )
        trigger = TriggerInstance(
            f"trigger-{self._next_trigger_number:06d}",
            source.controller,
            source.object_id,
            source.card,
            fragment,
            effect,
            event,
        )
        self._next_trigger_number += 1
        self._triggers[trigger.trigger_id] = trigger
        self.pending_triggers.append(trigger)
        self.log(
            "trigger_pending",
            trigger_id=trigger.trigger_id,
            event_id=event.event_id,
            source=source.card.name,
            controller=self.players[source.controller].name,
            oracle_fragment=fragment,
        )

    def _put_pending_triggers_on_stack(self, effects: set[TriggerEffect] | None = None) -> bool:
        """Put one detected batch on the stack in deterministic APNAP/source order."""
        batch = [
            trigger
            for trigger in self.pending_triggers
            if effects is None or trigger.effect in effects
        ]
        if not batch:
            return False
        self.pending_triggers[:] = [
            trigger for trigger in self.pending_triggers if trigger not in batch
        ]
        for controller in (self.active_player, 1 - self.active_player):
            controlled = [trigger for trigger in batch if trigger.controller == controller]
            for trigger in reversed(controlled):
                ability = TriggeredAbilityObject(
                    self._allocate_object_id(),
                    trigger.controller,
                    trigger.source_id,
                    trigger.source_card,
                    trigger.oracle_fragment,
                    trigger.effect,
                    trigger.event,
                    trigger.trigger_id,
                )
                self._register(ability)
                self.stack.append(ability)
                self.log(
                    "trigger_stacked",
                    trigger_id=trigger.trigger_id,
                    stack_object_id=ability.object_id,
                    event_id=trigger.event.event_id,
                    source=trigger.source_card.name,
                    controller=self.players[trigger.controller].name,
                )
        return True

    def _resolve_triggered_ability(self, ability: TriggeredAbilityObject) -> None:
        if (
            not self.stack
            or self.stack[-1] is not ability
            or not self.is_authoritative(ability, "stack")
        ):
            raise ValueError("triggered ability must be the authoritative top stack object")
        if ability.effect is TriggerEffect.ETB_DRAIN_GAIN_SCRY:
            self._validate_etb_drain_gain_scry_trigger(ability)
        if ability.effect is TriggerEffect.PERMANENT_LEFT_SELF_COUNTER:
            self._validate_permanent_left_counter_provenance(
                controller=ability.controller,
                source_id=ability.source_id,
                source_card=ability.source_card,
                oracle_fragment=ability.oracle_fragment,
                event=ability.event,
                trigger_id=ability.trigger_id,
            )
        if ability.effect is TriggerEffect.ETB_ARTIFACT_DRAW:
            self._validate_etb_artifact_draw_provenance(
                controller=ability.controller,
                source_id=ability.source_id,
                source_card=ability.source_card,
                oracle_fragment=ability.oracle_fragment,
                event=ability.event,
                trigger_id=ability.trigger_id,
                require_current_condition=False,
            )
        self.stack.pop()
        ability.zone = "former"
        source = self._objects.get(ability.source_id)
        source_permanent = (
            source
            if isinstance(source, Permanent) and self.is_authoritative(source, "battlefield")
            else None
        )
        subjects = [self._objects.get(object_id) for object_id in ability.event.subject_ids]

        if ability.effect is TriggerEffect.CREATE_TOKEN:
            coverage = self.interpreter.token_semantic_coverage(
                ability.source_card, ability.oracle_fragment
            )
            if (
                coverage is None
                or not coverage.payload_executable
                or not coverage.parent_executable
            ):
                raise AssertionError("stacked token trigger no longer has executable semantics")
            self.create_tokens(
                ability.controller,
                coverage.program,
                source_card=ability.source_card.name,
                oracle_fragment=ability.oracle_fragment,
                source_id=ability.source_id,
            )
        elif ability.effect is TriggerEffect.DEAL_DAMAGE:
            semantics = self.interpreter.damage_semantic_coverage(
                ability.source_card, ability.oracle_fragment
            )
            if (
                semantics is None
                or not semantics.coverage.payload_executable
                or not semantics.coverage.parent_executable
            ):
                raise AssertionError("stacked damage trigger no longer has executable semantics")
            program = semantics.program
            assert program.amount is not None and program.target_kind is DamageTargetKind.PLAYER
            if source_permanent is None:
                raise AssertionError("represented damage source must remain authoritative")
            if program.target_scope == "you":
                targets = (ability.controller,)
            else:
                targets = tuple(index for index in range(2) if index != ability.controller)
            for target_player in targets:
                self.deal_damage(
                    DamageTransaction(
                        ability.controller,
                        source_permanent,
                        program.target_kind,
                        program.amount,
                        ability.oracle_fragment,
                        target_player=target_player,
                    )
                )
        elif ability.effect is TriggerEffect.SCRY:
            semantics = self.interpreter.scry_semantic_coverage(
                ability.source_card, ability.oracle_fragment
            )
            if (
                semantics is None
                or not semantics.coverage.payload_executable
                or not semantics.coverage.parent_executable
            ):
                raise AssertionError("stacked Scry trigger no longer has executable semantics")
            self.scry(
                ability.controller,
                semantics.program,
                source_card=ability.source_card.name,
                oracle_fragment=ability.oracle_fragment,
                source_id=ability.source_id,
            )
        elif ability.effect is TriggerEffect.ETB_DRAIN_GAIN_SCRY:
            coverage = self.interpreter.etb_drain_gain_scry_semantic_coverage(
                ability.source_card, ability.oracle_fragment
            )
            if coverage is None or not coverage.fully_supported:
                raise AssertionError("stacked ETB drain/gain/Scry trigger is no longer executable")
            self._validate_etb_drain_gain_scry_trigger(ability)
            opponent = 1 - ability.controller
            opponent_life_before = self.players[opponent].life
            controller_life_before = self.players[ability.controller].life
            self.players[opponent].life -= 1
            self.log(
                "life_lost",
                player=self.players[opponent].name,
                amount=1,
                source=ability.source_card.name,
                source_id=ability.source_id,
                stack_object_id=ability.object_id,
                oracle_fragment=ability.oracle_fragment,
            )
            self.check_life()
            if self.winner is not None:
                evidence = EtbDrainGainScryEvidence(
                    ability.event.event_id,
                    ability.object_id,
                    ability.source_id,
                    ability.source_card.name,
                    ability.controller,
                    opponent,
                    ability.oracle_fragment,
                    ability.event.turn,
                    ability.event.step,
                    opponent_life_before,
                    self.players[opponent].life,
                    controller_life_before,
                    self.players[ability.controller].life,
                    None,
                    True,
                )
                self.etb_drain_gain_scry_evidence.append(evidence)
                self.log(
                    "etb_drain_gain_scry_terminal",
                    event_id=evidence.event_id,
                    stack_object_id=evidence.stack_object_id,
                    source_id=evidence.source_id,
                    oracle_fragment=evidence.oracle_fragment,
                )
                return
            self.gain_life(
                ability.controller,
                1,
                source_card=ability.source_card.name,
                oracle_fragment=ability.oracle_fragment,
                defer_trigger_delivery=True,
            )
            scry_count_before = len(self.scry_evidence)
            self.scry(
                ability.controller,
                ScryProgram(1),
                source_card=ability.source_card.name,
                oracle_fragment=ability.oracle_fragment,
                source_id=ability.source_id,
            )
            if len(self.scry_evidence) != scry_count_before + 1:
                raise AssertionError(
                    "ETB drain/gain/Scry transaction lacks committed Scry evidence"
                )
            scry_event_id = self.scry_evidence[-1].event_id
            self.etb_drain_gain_scry_evidence.append(
                EtbDrainGainScryEvidence(
                    ability.event.event_id,
                    ability.object_id,
                    ability.source_id,
                    ability.source_card.name,
                    ability.controller,
                    opponent,
                    ability.oracle_fragment,
                    ability.event.turn,
                    ability.event.step,
                    opponent_life_before,
                    self.players[opponent].life,
                    controller_life_before,
                    self.players[ability.controller].life,
                    scry_event_id,
                    False,
                )
            )
        elif ability.effect is TriggerEffect.PERMANENT_LEFT_SELF_COUNTER:
            source_before = self._validate_permanent_left_counter_provenance(
                controller=ability.controller,
                source_id=ability.source_id,
                source_card=ability.source_card,
                oracle_fragment=ability.oracle_fragment,
                event=ability.event,
                trigger_id=ability.trigger_id,
            )
            counters_before = (
                None if source_before is None else source_before.counters.get("+1/+1", 0)
            )
            if source_before is not None:
                self.place_counters(
                    source_before,
                    "+1/+1",
                    1,
                    source_card=ability.source_card.name,
                    oracle_fragment=ability.oracle_fragment,
                )
            self.log(
                "permanent_left_self_counter_resolved",
                event_id=ability.event.event_id,
                stack_object_id=ability.object_id,
                source=ability.source_card.name,
                source_id=ability.source_id,
                departed_object_id=ability.event.subject_ids[0],
                controller=ability.controller,
                counter_applied=source_before is not None,
                counters_before=counters_before,
                counters_after=(
                    None if source_before is None else source_before.counters.get("+1/+1", 0)
                ),
                oracle_fragment=ability.oracle_fragment,
            )
        elif ability.effect is TriggerEffect.ETB_ARTIFACT_DRAW:
            condition_met = self._validate_etb_artifact_draw_provenance(
                controller=ability.controller,
                source_id=ability.source_id,
                source_card=ability.source_card,
                oracle_fragment=ability.oracle_fragment,
                event=ability.event,
                trigger_id=ability.trigger_id,
                require_current_condition=True,
                allow_condition_failure=True,
            )
            hand_before = tuple(card.object_id for card in self.players[ability.controller].hand)
            library_before = tuple(
                card.object_id for card in self.players[ability.controller].library
            )
            draw_succeeded = False
            if condition_met:
                draw_succeeded = self.draw(self.players[ability.controller], 1)
            hand_after = tuple(card.object_id for card in self.players[ability.controller].hand)
            library_after = tuple(
                card.object_id for card in self.players[ability.controller].library
            )
            self.log(
                "etb_artifact_draw_resolved",
                event_id=ability.event.event_id,
                stack_object_id=ability.object_id,
                trigger_id=ability.trigger_id,
                source=ability.source_card.name,
                source_id=ability.source_id,
                controller=ability.controller,
                oracle_fragment=ability.oracle_fragment,
                condition_met=condition_met,
                draw_succeeded=draw_succeeded,
                hand_before=list(hand_before),
                hand_after=list(hand_after),
                library_before=list(library_before),
                library_after=list(library_after),
            )
        elif ability.effect is TriggerEffect.DISCARD_DRAW:
            semantics = self.interpreter.discard_draw_semantic_coverage(
                ability.source_card, ability.oracle_fragment
            )
            if semantics is None or not semantics.coverage.fully_supported:
                raise AssertionError("stacked discard/Draw trigger is no longer executable")
            plan = self.choose_discard_draw(ability.controller, semantics.program)
            self.commit_discard_draw(
                ability.controller,
                semantics.program,
                plan,
                trigger=ability,
            )
        elif ability.effect is TriggerEffect.DIES_DRAW:
            coverage = self.interpreter.dies_draw_semantic_coverage(
                ability.source_card, ability.oracle_fragment
            )
            if coverage is None or not coverage.fully_supported:
                raise AssertionError("stacked dies/Draw trigger is no longer executable")
            self._validate_dies_draw_trigger(ability)
            self.draw(self.players[ability.controller], 1)
        elif ability.effect is TriggerEffect.SNEAK_ETB_CONDITION:
            match = self.interpreter.SNEAK_ETB_TEAM_UNTIL_EOT.fullmatch(ability.oracle_fragment)
            assert match is not None
            if ability.event.source_id is None:
                self.log(
                    "pt_effect_condition_not_met",
                    source=ability.source_card.name,
                    condition="sneak_cost_paid",
                    oracle_fragment=ability.oracle_fragment,
                )
            else:
                for permanent in tuple(self.players[ability.controller].battlefield):
                    if permanent.card.is_creature:
                        self.apply_pt_modifier(
                            permanent,
                            int(match.group(1)),
                            int(match.group(2)),
                            duration="until_end_of_turn",
                            source_card=ability.source_card.name,
                            oracle_fragment=ability.oracle_fragment,
                        )
        elif ability.effect is TriggerEffect.ALLIANCE_PT and source_permanent is not None:
            match = self.interpreter.ALLIANCE_THIS_UNTIL_EOT.fullmatch(ability.oracle_fragment)
            assert match is not None
            self.apply_pt_modifier(
                source_permanent,
                int(match.group(1)),
                int(match.group(2)),
                duration="until_end_of_turn",
                source_card=ability.source_card.name,
                oracle_fragment=ability.oracle_fragment,
            )
        elif ability.effect is TriggerEffect.ALLIANCE_COUNTER and source_permanent is not None:
            match = self.interpreter.ALLIANCE_TARGET_PLUS_COUNTER.fullmatch(ability.oracle_fragment)
            assert match is not None
            candidates = tuple(
                permanent
                for permanent in self.players[ability.controller].battlefield
                if permanent.card.is_creature
            )
            target_id = self.counter_target_chooser(
                ability.controller,
                ability.source_id,
                tuple(candidate.object_id for candidate in candidates),
            )
            target = next(
                (candidate for candidate in candidates if candidate.object_id == target_id), None
            )
            if target is None:
                raise ValueError("counter target chooser must return a listed creature")
            self.place_counters(
                target,
                "+1/+1",
                int(match.group(1) or 1),
                source_card=ability.source_card.name,
                oracle_fragment=ability.oracle_fragment,
            )
        elif ability.effect is TriggerEffect.ALLIANCE_MODAL and source_permanent is not None:
            fragments = self.interpreter.fragments(ability.source_card)
            modes = tuple(fragment for fragment in fragments if fragment.startswith("• "))
            chosen = self.alliance_modes_chosen.setdefault(ability.source_id, set())
            available = tuple(mode for mode in modes if mode not in chosen)
            if not available:
                self.log("alliance_no_available_mode", source=ability.source_card.name)
            else:
                mode = self.alliance_mode_chooser(ability.controller, ability.source_id, available)
                if mode not in available:
                    raise ValueError("Alliance mode chooser must return an available mode")
                chosen.add(mode)
                token_coverage = self.interpreter.token_semantic_coverage(ability.source_card, mode)
                if self.interpreter.SELF_PLUS_COUNTER_MODE.fullmatch(mode):
                    self.place_counters(
                        source_permanent,
                        "+1/+1",
                        1,
                        source_card=ability.source_card.name,
                        oracle_fragment=mode,
                    )
                elif (
                    token_coverage is not None
                    and token_coverage.payload_executable
                    and token_coverage.parent_executable
                ):
                    self.create_tokens(
                        ability.controller,
                        token_coverage.program,
                        source_card=ability.source_card.name,
                        oracle_fragment=mode,
                        source_id=ability.source_id,
                    )
                elif (
                    (
                        scry_coverage := self.interpreter.scry_semantic_coverage(
                            ability.source_card, mode
                        )
                    )
                    is not None
                    and scry_coverage.coverage.payload_executable
                    and scry_coverage.coverage.parent_executable
                ):
                    self.scry(
                        ability.controller,
                        scry_coverage.program,
                        source_card=ability.source_card.name,
                        oracle_fragment=mode,
                        source_id=ability.source_id,
                    )
                else:
                    self.log(
                        "alliance_mode_not_executed",
                        source=ability.source_card.name,
                        oracle_fragment=mode,
                        reason="chosen_mode_semantics_not_implemented",
                    )
        elif ability.effect is TriggerEffect.LIFE_GAIN_COUNTER and source_permanent is not None:
            self.place_counters(
                source_permanent,
                "+1/+1",
                1,
                source_card=ability.source_card.name,
                oracle_fragment=ability.oracle_fragment,
            )
        elif ability.effect is TriggerEffect.ATTACK_PT and source_permanent is not None:
            match = self.interpreter.ATTACK_OTHER_ATTACKERS_UNTIL_EOT.fullmatch(
                ability.oracle_fragment
            )
            assert match is not None
            for subject in subjects:
                if (
                    isinstance(subject, Permanent)
                    and subject is not source_permanent
                    and self.is_authoritative(subject, "battlefield")
                ):
                    self.apply_pt_modifier(
                        subject,
                        int(match.group(1)),
                        int(match.group(2)),
                        duration="until_end_of_turn",
                        source_card=ability.source_card.name,
                        oracle_fragment=ability.oracle_fragment,
                    )
        self.log(
            "trigger_resolved",
            stack_object_id=ability.object_id,
            event_id=ability.event.event_id,
            source=ability.source_card.name,
            source_id=ability.source_id,
            oracle_fragment=ability.oracle_fragment,
            effect=ability.effect.value,
            trigger_id=ability.trigger_id,
        )

    def _drain_triggered_abilities(self) -> None:
        """Immediate compatibility drain until Priority owns all-pass resolution."""
        while self.stack and isinstance(self.stack[-1], TriggeredAbilityObject):
            if self.stack[-1].effect in {
                TriggerEffect.DISCARD_DRAW,
                TriggerEffect.DIES_DRAW,
                TriggerEffect.ETB_DRAIN_GAIN_SCRY,
                TriggerEffect.PERMANENT_LEFT_SELF_COUNTER,
                TriggerEffect.ETB_ARTIFACT_DRAW,
            }:
                self._begin_priority_window()
                return
            self._resolve_triggered_ability(self.stack[-1])

    def _validate_dies_draw_trigger(self, ability: TriggeredAbilityObject) -> None:
        """Authenticate one self-death trigger from frozen event and zone-change provenance."""
        event = ability.event
        source = self._objects.get(ability.source_id)
        last_known = event.last_known_battlefield
        departures = [
            item
            for item in self.events
            if item.get("event") == "zone_changed"
            and item.get("source_object_id") == ability.source_id
            and item.get("source_zone") == "battlefield"
            and item.get("destination_zone") == "graveyard"
        ]
        if (
            event.kind is not RulesEventKind.CREATURE_DIED
            or self._rules_events.get(event.event_id) is not event
            or event.source_id != ability.source_id
            or event.subject_ids != (ability.source_id,)
            or event.player_index != ability.controller
            or (ability.source_id, ability.controller) not in event.battlefield_authority
            or len(last_known) != 1
            or last_known[0][0] != ability.source_id
            or last_known[0][1] != ability.controller
            or not last_known[0][2]
            or last_known[0][3] is not True
            or ("Creature" in last_known[0][2]) is not last_known[0][3]
            or len(departures) != 1
            or not isinstance(source, Permanent)
            or source.zone != "former"
            or source.controller != ability.controller
            or source.card is not ability.source_card
        ):
            raise ValueError("dies/Draw trigger has mismatched death provenance")

    def _controlled_artifact_ids(self, controller: int) -> tuple[str, ...]:
        """Return authoritative battlefield artifacts controlled by one player."""
        return tuple(
            sorted(
                permanent.object_id
                for permanent in self.players[controller].battlefield
                if self.is_authoritative(permanent, "battlefield")
                and "Artifact" in permanent.type_line
            )
        )

    def _validate_etb_artifact_draw_provenance(
        self,
        *,
        controller: int,
        source_id: str,
        source_card: CardFact,
        oracle_fragment: str,
        event: RulesEvent,
        trigger_id: str | None = None,
        require_current_condition: bool,
        allow_condition_failure: bool = False,
    ) -> bool:
        """Authenticate the self-ETB event and both intervening-if artifact checks."""
        self._authenticate_original_rules_event(event)
        coverage = self.interpreter.etb_artifact_draw_semantic_coverage(
            source_card, oracle_fragment
        )
        source = self._objects.get(source_id)
        trigger = None if trigger_id is None else self._triggers.get(trigger_id)
        event_characteristics = {
            object_id: (event_controller, type_line)
            for object_id, event_controller, type_line in event.battlefield_characteristics
        }
        event_artifact_ids = tuple(
            sorted(
                object_id
                for object_id, (event_controller, type_line) in event_characteristics.items()
                if event_controller == controller and "Artifact" in type_line
            )
        )
        if (
            coverage is None
            or not coverage.fully_supported
            or event.kind is not RulesEventKind.CREATURE_ENTERED
            or self._rules_events.get(event.event_id) is not event
            or event.subject_ids != (source_id,)
            or event.player_index != controller
            or (source_id, controller) not in event.battlefield_authority
            or event_characteristics.get(source_id, (None, ""))[0] != controller
            or not event_artifact_ids
            or not isinstance(source, Permanent)
            or source.card is not source_card
            or source.zone not in {"battlefield", "former"}
            or (
                trigger_id is not None
                and (
                    trigger is None
                    or trigger.controller != controller
                    or trigger.source_id != source_id
                    or trigger.source_card is not source_card
                    or trigger.oracle_fragment != oracle_fragment
                    or trigger.effect is not TriggerEffect.ETB_ARTIFACT_DRAW
                    or trigger.event is not event
                )
            )
        ):
            raise ValueError("ETB artifact/Draw trigger has mismatched entry provenance")
        current_condition = bool(self._controlled_artifact_ids(controller))
        if require_current_condition and not current_condition and not allow_condition_failure:
            raise ValueError("ETB artifact/Draw resolution condition is false")
        return current_condition if require_current_condition else True

    def _validate_etb_drain_gain_scry_trigger(self, ability: TriggeredAbilityObject) -> None:
        """Authenticate the bounded compound trigger against its exact self-ETB event."""
        event = ability.event
        source = self._objects.get(ability.source_id)
        coverage = self.interpreter.etb_drain_gain_scry_semantic_coverage(
            ability.source_card, ability.oracle_fragment
        )
        if (
            ability.effect is not TriggerEffect.ETB_DRAIN_GAIN_SCRY
            or coverage is None
            or not coverage.fully_supported
            or event.kind is not RulesEventKind.CREATURE_ENTERED
            or self._rules_events.get(event.event_id) is not event
            or event.subject_ids != (ability.source_id,)
            or event.player_index != ability.controller
            or (ability.source_id, ability.controller) not in event.battlefield_authority
            or not isinstance(source, Permanent)
            or source.card is not ability.source_card
            or source.zone not in {"battlefield", "former"}
        ):
            raise ValueError("ETB drain/gain/Scry trigger has mismatched entry provenance")

    def _detect_creature_entered_triggers(
        self,
        entering: Permanent,
        event: RulesEvent,
        enabled: set[TriggerEffect],
    ) -> None:
        """Detect one creature's triggers without prematurely placing or draining the batch."""
        if TriggerEffect.SNEAK_ETB_CONDITION in enabled:
            for fragment in self.interpreter.fragments(entering.card):
                if self.interpreter.SNEAK_ETB_TEAM_UNTIL_EOT.fullmatch(fragment):
                    self._enqueue_trigger(
                        event, entering, fragment, TriggerEffect.SNEAK_ETB_CONDITION
                    )
        if TriggerEffect.CREATE_TOKEN in enabled:
            for fragment in self.interpreter.fragments(entering.card):
                coverage = self.interpreter.token_semantic_coverage(entering.card, fragment)
                if (
                    coverage is not None
                    and coverage.payload_executable
                    and coverage.parent_executable
                    and re.match(r"^(?:When|Whenever) .+ enters(?: or attacks)?,", fragment)
                ):
                    self._enqueue_trigger(event, entering, fragment, TriggerEffect.CREATE_TOKEN)
        if TriggerEffect.SCRY in enabled:
            for fragment in self.interpreter.fragments(entering.card):
                coverage = self.interpreter.scry_semantic_coverage(entering.card, fragment)
                if (
                    coverage is not None
                    and coverage.coverage.payload_executable
                    and coverage.coverage.parent_executable
                    and re.match(r"^When .+ enters, scry\b", fragment, re.I)
                ):
                    self._enqueue_trigger(event, entering, fragment, TriggerEffect.SCRY)
        if TriggerEffect.ETB_DRAIN_GAIN_SCRY in enabled:
            for fragment in self.interpreter.fragments(entering.card):
                coverage = self.interpreter.etb_drain_gain_scry_semantic_coverage(
                    entering.card, fragment
                )
                if coverage is not None and coverage.fully_supported:
                    self._enqueue_trigger(
                        event, entering, fragment, TriggerEffect.ETB_DRAIN_GAIN_SCRY
                    )
        if TriggerEffect.ETB_ARTIFACT_DRAW in enabled:
            for fragment in self.interpreter.fragments(entering.card):
                coverage = self.interpreter.etb_artifact_draw_semantic_coverage(
                    entering.card, fragment
                )
                if (
                    coverage is not None
                    and coverage.fully_supported
                    and self._controlled_artifact_ids(entering.controller)
                ):
                    self._enqueue_trigger(
                        event, entering, fragment, TriggerEffect.ETB_ARTIFACT_DRAW
                    )
        for source in list(self.players[entering.controller].battlefield):
            if source is entering:
                continue
            fragments = self.interpreter.fragments(source.card)
            for fragment in fragments:
                if (
                    TriggerEffect.ALLIANCE_PT in enabled
                    and self.interpreter.ALLIANCE_THIS_UNTIL_EOT.fullmatch(fragment)
                ):
                    self._enqueue_trigger(event, source, fragment, TriggerEffect.ALLIANCE_PT)
                if (
                    TriggerEffect.ALLIANCE_COUNTER in enabled
                    and self.interpreter.ALLIANCE_TARGET_PLUS_COUNTER.fullmatch(fragment)
                ):
                    self._enqueue_trigger(event, source, fragment, TriggerEffect.ALLIANCE_COUNTER)
                if TriggerEffect.DEAL_DAMAGE in enabled:
                    semantics = self.interpreter.damage_semantic_coverage(source.card, fragment)
                    if (
                        semantics is not None
                        and semantics.coverage.payload_executable
                        and semantics.coverage.parent_executable
                        and fragment.startswith("Alliance — ")
                    ):
                        self._enqueue_trigger(event, source, fragment, TriggerEffect.DEAL_DAMAGE)
            if TriggerEffect.ALLIANCE_MODAL in enabled and any(
                self.interpreter.ALLIANCE_MODAL_HEADER.fullmatch(fragment) for fragment in fragments
            ):
                header = next(
                    fragment
                    for fragment in fragments
                    if self.interpreter.ALLIANCE_MODAL_HEADER.fullmatch(fragment)
                )
                self._enqueue_trigger(event, source, header, TriggerEffect.ALLIANCE_MODAL)

    def _process_creatures_entered_triggers(
        self,
        entering: tuple[Permanent, ...],
        effects: set[TriggerEffect] | None = None,
        *,
        source_id: str | None = None,
        defer_triggers: bool = False,
        after_event: Callable[[Permanent, RulesEvent], None] | None = None,
    ) -> None:
        enabled = effects or {
            TriggerEffect.SNEAK_ETB_CONDITION,
            TriggerEffect.ALLIANCE_PT,
            TriggerEffect.ALLIANCE_COUNTER,
            TriggerEffect.ALLIANCE_MODAL,
            TriggerEffect.CREATE_TOKEN,
            TriggerEffect.DEAL_DAMAGE,
            TriggerEffect.SCRY,
            TriggerEffect.ETB_DRAIN_GAIN_SCRY,
            TriggerEffect.ETB_ARTIFACT_DRAW,
        }
        for permanent in entering:
            event = self._new_rules_event(
                RulesEventKind.CREATURE_ENTERED,
                permanent.controller,
                (permanent.object_id,),
                source_id=source_id,
            )
            if after_event is not None:
                after_event(permanent, event)
            self._detect_creature_entered_triggers(permanent, event, enabled)
        self._put_pending_triggers_on_stack()
        if not defer_triggers:
            self._drain_triggered_abilities()

    def _process_creature_entered_triggers(
        self,
        entering: Permanent,
        effects: set[TriggerEffect] | None = None,
        *,
        source_id: str | None = None,
        defer_triggers: bool = False,
        after_event: Callable[[Permanent, RulesEvent], None] | None = None,
    ) -> None:
        self._process_creatures_entered_triggers(
            (entering,),
            effects,
            source_id=source_id,
            defer_triggers=defer_triggers,
            after_event=after_event,
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
        if not self.is_authoritative(target, "battlefield"):
            raise ValueError("counter target must be a battlefield permanent")
        for occurrence in tuple(self.semantic_occurrences):
            source = self._objects.get(occurrence.object_id)
            if (
                isinstance(source, Permanent)
                and self.is_authoritative(source, "battlefield")
                and source.controller == target.controller
                and re.search(
                    r"counters would be put|counters are put on it instead",
                    occurrence.oracle_fragment,
                )
            ):
                self._new_opportunity_context(
                    "replacement_evaluation",
                    controller=source.controller,
                    source_id=source.object_id,
                    subject_ids=(target.object_id,),
                    facts=(
                        ("counter_type", counter_type),
                        ("quantity", str(quantity)),
                    ),
                )
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
        self._process_creature_entered_triggers(
            entering, {TriggerEffect.ALLIANCE_COUNTER, TriggerEffect.ALLIANCE_MODAL}
        )

    def gain_life(
        self,
        player_index: int,
        amount: int,
        *,
        source_card: str,
        oracle_fragment: str,
        defer_trigger_delivery: bool = False,
    ) -> RulesEvent:
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
        event = self._new_rules_event(RulesEventKind.LIFE_GAINED, player_index, ())
        for permanent in list(player.battlefield):
            for fragment in self.interpreter.fragments(permanent.card):
                if self.interpreter.GAIN_LIFE_SELF_PLUS_COUNTER.fullmatch(fragment):
                    self._enqueue_trigger(
                        event, permanent, fragment, TriggerEffect.LIFE_GAIN_COUNTER
                    )
        if not defer_trigger_delivery:
            self._put_pending_triggers_on_stack()
            self._drain_triggered_abilities()
        return event

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
        if not self.is_authoritative(target, "battlefield"):
            raise ValueError("P/T modifier target must be a battlefield permanent")
        target.pt_modifiers.append(
            PowerToughnessModifier(
                power=power,
                toughness=toughness,
                duration=duration,
                source_card=source_card,
                oracle_fragment=oracle_fragment,
                created_turn=self.turn,
                created_order=self._next_effect_number,
                derived_static=derived_static,
            )
        )
        self._next_effect_number += 1
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

    def add_characteristic_effect(self, target: Permanent, effect: CharacteristicEffect) -> None:
        """Register a typed continuous effect for ordered characteristic evaluation."""
        if not self.is_authoritative(target, "battlefield"):
            raise ValueError("characteristic effect target must be on the battlefield")
        if any(
            existing.effect_id == effect.effect_id for existing in target.characteristic_effects
        ):
            raise ValueError("characteristic effect ID must be unique on its target")
        if effect.layer is not CharacteristicLayer.POWER_TOUGHNESS or effect.sublayer is None:
            raise ValueError("only typed power/toughness layer effects are represented")
        valid_operation = {
            PowerToughnessSubLayer.CHARACTERISTIC_DEFINING: CharacteristicOperation.SET,
            PowerToughnessSubLayer.SET_BASE: CharacteristicOperation.SET,
            PowerToughnessSubLayer.MODIFY: CharacteristicOperation.ADD,
            PowerToughnessSubLayer.SWITCH: CharacteristicOperation.SWITCH,
        }[effect.sublayer]
        if effect.operation is not valid_operation:
            raise ValueError("characteristic operation does not match its sublayer")
        existing_ids = {existing.effect_id for existing in target.characteristic_effects}
        if any(dependency not in existing_ids for dependency in effect.depends_on):
            raise ValueError("characteristic effect dependency must already exist")
        target.characteristic_effects.append(effect)
        # Evaluate immediately so cycles and malformed dependencies never enter authoritative state.
        try:
            target.evaluate_power_toughness()
        except Exception:
            target.characteristic_effects.remove(effect)
            raise
        self.log(
            "characteristic_effect_added",
            target=target.card.name,
            effect_id=effect.effect_id,
            layer=effect.layer.value,
            sublayer=effect.sublayer.value,
            operation=effect.operation.value,
            source=effect.source_card,
        )

    def refresh_static_pt_modifiers(self) -> None:
        previous: dict[str, tuple[int, int]] = {}
        for player in self.players:
            for permanent in player.battlefield:
                previous[permanent.object_id] = (
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
                for fragment in self.interpreter.fragments(source.card):
                    match = self.interpreter.STATIC_OTHER_CREATURES.fullmatch(fragment)
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
                        if previous.get(source.object_id, (0, 0)) != current:
                            self.log(
                                "pt_static_modifier_refreshed",
                                target=source.card.name,
                                source=source.card.name,
                                power=current[0],
                                toughness=current[1],
                                oracle_fragment=fragment,
                            )

    def resolve_creature_entered_pt_effects(self, entering: Permanent) -> None:
        self._process_creature_entered_triggers(
            entering, {TriggerEffect.SNEAK_ETB_CONDITION, TriggerEffect.ALLIANCE_PT}
        )

    def resolve_attack_pt_effects(self, attackers: list[Permanent]) -> None:
        if any(
            not isinstance(attacker, Permanent)
            or not self.is_authoritative(attacker, "battlefield")
            or attacker.controller != self.active_player
            for attacker in attackers
        ):
            raise ValueError(
                "attack trigger delivery requires authoritative active-player attackers"
            )
        event = self._new_rules_event(
            RulesEventKind.ATTACKERS_DECLARED,
            self.active_player,
            tuple(attacker.object_id for attacker in attackers),
        )
        for source in attackers:
            for fragment in self.interpreter.fragments(source.card):
                if self.interpreter.ATTACK_OTHER_ATTACKERS_UNTIL_EOT.fullmatch(fragment):
                    self._enqueue_trigger(event, source, fragment, TriggerEffect.ATTACK_PT)
                token_coverage = self.interpreter.token_semantic_coverage(source.card, fragment)
                if (
                    token_coverage is not None
                    and token_coverage.payload_executable
                    and token_coverage.parent_executable
                    and re.match(
                        r"^Whenever .+ (?:attacks|enters or attacks),",
                        fragment,
                    )
                ):
                    self._enqueue_trigger(event, source, fragment, TriggerEffect.CREATE_TOKEN)
                discard_draw = self.interpreter.discard_draw_semantic_coverage(
                    source.card, fragment
                )
                if discard_draw is not None and discard_draw.coverage.fully_supported:
                    self._enqueue_trigger(event, source, fragment, TriggerEffect.DISCARD_DRAW)
        self._put_pending_triggers_on_stack()
        self._drain_triggered_abilities()

    def draw(self, player: PlayerState, count: int = 1, *, setup: bool = False) -> bool:
        for _ in range(count):
            if not player.library:
                player.failed_draw_pending = True
                self.log(
                    "draw_failed",
                    player=player.name,
                    reason="empty_library",
                    state_based_action_pending=True,
                )
                return False
            self.move_object(player.library[-1], "hand", reason="draw")
            self.log("card_drawn", player=player.name, setup=setup)
        return True

    def transition_to(self, step: TurnStep) -> None:
        """Perform the one legal deterministic CR 500-series step transition."""
        if self.stack:
            raise ValueError("cannot advance the turn with an unresolved stack")
        expected = NEXT_STEP[self._step]
        if step is not expected:
            raise ValueError(
                f"illegal turn transition: {self._step.value} -> {step.value}; "
                f"expected {expected.value}"
            )
        if self._step is TurnStep.COMBAT_DAMAGE and not self._combat_damage_resolved:
            raise ValueError("combat damage step must be resolved before it can end")
        if self._step is TurnStep.DECLARE_ATTACKERS and not self._attackers_declared:
            self._attackers_declared = True
            self._combat_attackers = ()
            self.log("attackers_declared", attackers=[])
        if self._step is TurnStep.DECLARE_BLOCKERS and not self._blockers_declared:
            self._blockers_declared = True
            self._combat_blocks = ()
            self.log("blockers_declared", blocks=[])
        previous = self._step
        if previous is TurnStep.CLEANUP:
            self._turn += 1
            self._active_player = (self._turn - 1) % len(self.players)
        elif previous is TurnStep.SETUP:
            self._turn = 1
            self._active_player = 0
        self._step = step
        self.log("step_started", step=step.value, previous_step=previous.value)
        self._on_enter_step(step)

    def advance_step(self) -> None:
        self.transition_to(NEXT_STEP[self._step])

    def advance_to(self, step: TurnStep) -> None:
        """Advance through, never around, each intermediate rules step."""
        visited = 0
        while self._step is not step:
            self.advance_step()
            visited += 1
            if visited > len(TurnStep):
                raise ValueError(f"cannot reach {step.value} from current turn state")

    def _on_enter_step(self, step: TurnStep) -> None:
        player = self.players[self.active_player]
        if step is TurnStep.UNTAP:
            player.lands_played = 0
            for permanent in player.battlefield:
                permanent.tapped = False
                if permanent.entered_battlefield_turn < self.turn:
                    permanent.summoning_sick = False
            self.log("turn_started", player=player.name)
        elif step is TurnStep.DRAW:
            if self.turn == 1 and self.active_player == 0:
                self.log("draw_skipped", player=player.name, reason="starting_player_first_turn")
            else:
                self.draw(player)
                self.check_state_based_actions()
        elif step is TurnStep.BEGINNING_OF_COMBAT:
            self._reset_current_combat_state()
            self.log("combat_state_reset")
        elif step is TurnStep.COMBAT_DAMAGE:
            self._begin_combat_damage_steps()
        elif step is TurnStep.POSTCOMBAT_MAIN:
            # CR 511.3: the combat phase has ended, so no object remains in combat.
            self._reset_current_combat_state()
        elif step is TurnStep.CLEANUP:
            self._perform_cleanup()

    def _reset_current_combat_state(self) -> None:
        """End the semantic lifetime of mutable state for the current combat."""
        self._combat_attackers = ()
        self._combat_blocks = ()
        self._attackers_declared = False
        self._blockers_declared = False
        self._combat_damage_resolved = False
        self._combat_damage_step_kind = CombatDamageStepKind.NONE
        self._combat_damage_step_number = 0
        self._combat_damage_total_steps = 0
        self._first_damage_qualified_ids = ()
        self._first_double_strike_ids = ()
        self._regular_damage_initial_ids = ()

    def _perform_cleanup(self) -> None:
        expired = 0
        for current in self.players:
            for permanent in current.battlefield:
                before = len(permanent.pt_modifiers)
                permanent.pt_modifiers = [
                    modifier
                    for modifier in permanent.pt_modifiers
                    if modifier.duration != "until_end_of_turn"
                ]
                permanent.temporary_keyword_effects = [
                    effect
                    for effect in permanent.temporary_keyword_effects
                    if effect.duration != "until_end_of_turn"
                ]
                expired += before - len(permanent.pt_modifiers)
                permanent.damage = 0
        self._reset_current_combat_state()
        self.refresh_static_pt_modifiers()
        self.alliance_modes_chosen.clear()
        self.log("cleanup_completed", expired_pt_modifiers=expired)
        self.check_state_based_actions()
        self.log("turn_ended", player=self.players[self.active_player].name)

    def begin_turn(self) -> None:
        """Compatibility helper: follow legal transitions to precombat main."""
        if self.step not in {TurnStep.SETUP, TurnStep.CLEANUP}:
            raise ValueError("begin_turn is legal only before a turn starts")
        self.advance_to(TurnStep.PRECOMBAT_MAIN)

    def public_view(self) -> GameView:
        """Return immutable pilot-visible state with no mutable authoritative objects."""
        return GameView(
            turn=self.turn,
            active_player=self.active_player,
            phase=self.phase,
            step=self.step.value,
            life=tuple(player.life for player in self.players),  # type: ignore[arg-type]
            hands=tuple(
                tuple(
                    (card.object_id, card.name, card.mana_value, card.is_creature)
                    for card in player.hand
                )
                for player in self.players
            ),  # type: ignore[arg-type]
            battlefields=tuple(
                tuple(
                    PublicObjectView(
                        permanent.object_id,
                        permanent.card.name,
                        permanent.controller,
                        permanent.power if permanent.card.is_creature else None,
                        permanent.toughness if permanent.card.is_creature else None,
                        permanent.tapped,
                        permanent.damage,
                        permanent.is_token,
                    )
                    for permanent in player.battlefield
                )
                for player in self.players
            ),  # type: ignore[arg-type]
        )

    def legal_main_actions(self, player_index: int) -> tuple[ActionOption, ...]:
        """Generate every currently represented legal main-phase option."""
        if (
            self.priority_state is not None
            or player_index != self.active_player
            or self.step
            not in {
                TurnStep.PRECOMBAT_MAIN,
                TurnStep.POSTCOMBAT_MAIN,
            }
        ):
            return ()
        player = self.players[player_index]
        opponent = self.players[1 - player_index]
        self._witness_graveyard_cast_permissions(player_index)
        self._witness_unsupported_activation_contexts(player_index)
        options: list[ActionOption] = []
        if player.lands_played < 1:
            options.extend(
                ActionOption(ActionKind.PLAY_LAND, player_index, object_id=card.object_id)
                for card in player.hand
                if card.is_land
            )
        for card in player.hand:
            if not self.can_afford(player_index, card):
                continue
            kind = self.interpreter.cast_program(card.card).kind
            if kind is CastKind.CREATURE:
                options.append(
                    ActionOption(ActionKind.CAST, player_index, object_id=card.object_id)
                )
            elif kind in {CastKind.DAMAGE_3_OPPOSING_CREATURE, CastKind.DEAL_DAMAGE}:
                options.extend(
                    ActionOption(
                        ActionKind.CAST,
                        player_index,
                        object_id=card.object_id,
                        target_id=target.object_id,
                    )
                    for target in opponent.battlefield
                    if target.card.is_creature
                )
            elif kind is CastKind.DESTROY_OPPOSING_POWER_4:
                options.extend(
                    ActionOption(
                        ActionKind.CAST,
                        player_index,
                        object_id=card.object_id,
                        target_id=target.object_id,
                    )
                    for target in opponent.battlefield
                    if target.card.is_creature and target.power >= 4
                )
        options.extend(self.legal_activated_ability_actions(player_index))
        options.append(ActionOption(ActionKind.PASS, player_index))
        return tuple(options)

    def _witness_unsupported_activation_contexts(self, player_index: int) -> None:
        """Witness only fixed-cost unsupported activations provably available now."""
        for occurrence in tuple(self.semantic_occurrences):
            source = self._objects.get(occurrence.object_id)
            if (
                not isinstance(source, Permanent)
                or not self.is_authoritative(source, "battlefield")
                or source.controller != player_index
            ):
                continue
            fragment = occurrence.oracle_fragment
            match = re.match(
                r"^(?P<cost>(?:\{[0-9WUBRG]+\})+)(?P<rest>(?:, \{T\})?[^:]*):", fragment
            )
            if match is None:
                continue
            requirement = self.activation_mana_requirement(match.group("cost"))
            needs_tap = "{T}" in match.group("rest")
            if requirement is None or (needs_tap and source.tapped):
                continue
            available = tuple(
                permanent
                for permanent in self.players[player_index].battlefield
                if permanent.card.is_land and not permanent.tapped and permanent is not source
            )
            if len(available) < requirement.total:
                continue
            subjects = (source.object_id,) + tuple(
                permanent.object_id for permanent in available[: requirement.total]
            )
            self._new_opportunity_context(
                "activation_available",
                controller=player_index,
                source_id=source.object_id,
                subject_ids=subjects,
                facts=(
                    ("mana_required", str(requirement.total)),
                    ("source_tap_required", str(needs_tap).lower()),
                    ("source_tapped", str(source.tapped).lower()),
                    ("timing", self.step.value),
                ),
            )

    def _witness_graveyard_cast_permissions(self, player_index: int) -> None:
        """Witness only permissions whose represented P/T and timing predicates are true."""
        pattern = re.compile(
            r"^During your turn, you may cast creature spells with power or toughness "
            r"(?P<limit>\d+) or less from your graveyard\."
        )
        for occurrence in tuple(self.semantic_occurrences):
            source = self._objects.get(occurrence.object_id)
            match = pattern.match(occurrence.oracle_fragment)
            if (
                match is None
                or not isinstance(source, Permanent)
                or not self.is_authoritative(source, "battlefield")
                or source.controller != player_index
            ):
                continue
            limit = int(match.group("limit"))
            candidates = tuple(
                card.object_id
                for card in self.players[player_index].graveyard
                if card.card.is_creature
                and card.card.power is not None
                and card.card.toughness is not None
                and (card.card.power <= limit or card.card.toughness <= limit)
            )
            if candidates:
                self._record_opportunity(
                    occurrence,
                    cause_kind="legal_action_context",
                    cause_id=(
                        f"legal-main:{self.turn}:{self.step.value}:{player_index}:"
                        + ",".join(candidates)
                    ),
                    cause_subject_ids=candidates,
                )

    def legal_priority_actions(self, player_index: int) -> tuple[ActionOption, ...]:
        """Expose only immutable engine-generated choices for the bounded priority window."""
        state = self.priority_state
        if (
            state is None
            or state.resolution_pending
            or player_index != state.player_index
            or not self.stack
        ):
            return ()
        return (
            ActionOption(
                ActionKind.PASS_PRIORITY,
                player_index,
                priority_epoch=state.epoch,
            ),
        )

    def execute_priority_action(self, option: ActionOption) -> bool:
        """Revalidate and apply one pilot-selected bounded priority decision."""
        if option not in self.legal_priority_actions(option.player_index):
            raise ValueError("priority action is not currently legal")
        if option.kind is not ActionKind.PASS_PRIORITY:
            raise ValueError("unsupported priority action kind")
        state = self.priority_state
        assert state is not None
        passes = state.consecutive_passes + (option.player_index,)
        pending = len(passes) == 2
        next_player = option.player_index if pending else 1 - option.player_index
        self.priority_state = PriorityState(state.epoch, next_player, passes, pending)
        if self.stack and isinstance(self.stack[-1], ActivatedAbilityObject):
            stack_object_id = self.stack[-1].object_id
            for index, evidence in enumerate(self.food_activation_evidence):
                if evidence.stack_object_id == stack_object_id:
                    self.food_activation_evidence[index] = replace(
                        evidence,
                        priority_passes=passes,
                        resolution_permitted=pending,
                    )
                    break
        self.log(
            "priority_passed",
            player=self.players[option.player_index].name,
            player_index=option.player_index,
            priority_epoch=state.epoch,
            consecutive_passes=len(passes),
            resolution_pending=pending,
        )
        if not pending:
            self.log(
                "priority_granted",
                player=self.players[next_player].name,
                player_index=next_player,
                priority_epoch=state.epoch,
            )
        else:
            self.log(
                "stack_resolution_permitted",
                stack_object_id=self.stack[-1].object_id,
                priority_epoch=state.epoch,
            )
        return True

    def process_priority_resolution(self) -> bool:
        """Perform an engine-permitted resolution after the represented all-pass sequence."""
        state = self.priority_state
        if state is None or not state.resolution_pending:
            raise ValueError("stack resolution is not permitted")
        if not self.stack:
            raise ValueError("priority state cannot resolve an empty stack")
        self.priority_state = None
        self._priority_resolution_in_progress = True
        try:
            self.resolve_top_of_stack()
        finally:
            self._priority_resolution_in_progress = False
        self.check_state_based_actions()
        if self.winner is None:
            self._put_pending_triggers_on_stack()
        if self.winner is None and self.stack and self.priority_state is None:
            self._begin_priority_window()
        elif (
            self.winner is None
            and self.step is TurnStep.COMBAT_DAMAGE
            and self._combat_damage_resolved
        ):
            self._advance_after_combat_damage()
        elif (
            self.winner is None
            and self.step is TurnStep.DECLARE_ATTACKERS
            and self._attackers_declared
        ):
            self.transition_to(TurnStep.DECLARE_BLOCKERS)
        return True

    def _advance_after_combat_damage(self) -> None:
        """Advance only after damage-created Stack and Priority work is complete."""
        if self.step is not TurnStep.COMBAT_DAMAGE or not self._combat_damage_resolved:
            raise ValueError("combat damage is not ready to advance")
        if self.stack or self.priority_state is not None:
            return
        if (
            self._combat_damage_step_kind is CombatDamageStepKind.FIRST_STRIKE
            and self.winner is None
        ):
            self._start_combat_damage_step(CombatDamageStepKind.REGULAR, 2, 2)
        else:
            self._combat_damage_step_kind = CombatDamageStepKind.COMPLETE
            self.transition_to(TurnStep.END_OF_COMBAT)

    def _record_represented_priority_action(self, player_index: int) -> None:
        """Reset passes after an engine-validated response; no such response exists yet."""
        state = self.priority_state
        if (
            state is None
            or state.resolution_pending
            or state.player_index != player_index
            or not self.stack
        ):
            raise ValueError("represented priority action is not currently legal")
        self.priority_state = PriorityState(state.epoch, player_index)
        self.log(
            "priority_action_taken",
            player=self.players[player_index].name,
            player_index=player_index,
            priority_epoch=state.epoch,
        )

    def _begin_priority_window(self) -> None:
        if not self.stack:
            raise ValueError("priority requires a nonempty stack")
        epoch = self._next_priority_epoch
        self._next_priority_epoch += 1
        self.priority_state = PriorityState(epoch, self.active_player)
        self._witness_unsupported_stack_responses()
        self.log(
            "priority_granted",
            player=self.players[self.active_player].name,
            player_index=self.active_player,
            priority_epoch=epoch,
        )

    def _witness_unsupported_stack_responses(self) -> None:
        """Freeze a counterspell opportunity only when spell, card, and mana all exist."""
        if not self.stack or not isinstance(self.stack[-1], StackObject):
            return
        target = self.stack[-1]
        for player_index, player in enumerate(self.players):
            if player_index == target.controller:
                continue
            for card in tuple(player.hand):
                grouped: dict[str, list[str]] = {}
                for fragment, reason in self.interpreter.unsupported_fragments(card.card):
                    grouped.setdefault(fragment, []).append(reason)
                for fragment, reasons in grouped.items():
                    match = re.match(
                        r"^Counter target (?P<noncreature>noncreature )?spell\.", fragment
                    )
                    if (
                        match is None
                        or not self.can_afford(player_index, card)
                        or (match.group("noncreature") and target.card.is_creature)
                    ):
                        continue
                    self._register_semantic_occurrence(
                        card, player_index, fragment, tuple(sorted(set(reasons)))
                    )
                    self._new_opportunity_context(
                        "stack_response",
                        controller=player_index,
                        source_id=card.object_id,
                        subject_ids=(target.object_id,),
                        facts=(
                            ("response_cost", card.mana_cost),
                            ("target_is_creature", str(target.card.is_creature).lower()),
                        ),
                        stack_object_id=target.object_id,
                    )

    def execute_main_action(self, option: ActionOption) -> bool:
        """Revalidate and execute one engine-issued main-phase option."""
        if option not in self.legal_main_actions(option.player_index):
            raise ValueError("action is not currently legal")
        if option.kind is ActionKind.PASS:
            return True
        obj = self._objects.get(option.object_id or "")
        if option.kind is ActionKind.PLAY_LAND:
            if not isinstance(obj, CardObject):
                raise ValueError("land option does not identify a card object")
            return self.play_land(option.player_index, obj)
        if option.kind is ActionKind.CAST:
            if not isinstance(obj, CardObject):
                raise ValueError("cast option does not identify a card object")
            target = self._objects.get(option.target_id or "")
            if target is not None and not isinstance(target, Permanent):
                raise ValueError("target option does not identify a permanent")
            return self.cast(option.player_index, obj, target)
        if option.kind is ActionKind.ACTIVATE_ABILITY:
            if not isinstance(obj, Permanent):
                raise ValueError("activation option does not identify a permanent")
            if option.oracle_fragment is None:
                raise ValueError("activation option lacks an Oracle fragment")
            target_ids = () if option.target_id is None else (option.target_id,)
            return self.activate_ability(
                option.player_index, obj, option.oracle_fragment, target_ids=target_ids
            )
        raise ValueError("unsupported main action kind")

    def legal_attack_options(self, player_index: int) -> tuple[ActionOption, ...]:
        if player_index != self.active_player or self.step is not TurnStep.DECLARE_ATTACKERS:
            return ()
        attacker_ids = tuple(obj.object_id for obj in self.legal_attackers(player_index))
        options = [ActionOption(ActionKind.DECLARE_ATTACKERS, player_index)]
        if attacker_ids:
            options.append(
                ActionOption(
                    ActionKind.DECLARE_ATTACKERS,
                    player_index,
                    attacker_ids=attacker_ids,
                )
            )
        return tuple(options)

    def legal_block_options(
        self, attack: ActionOption, defender_index: int
    ) -> tuple[ActionOption, ...]:
        if self.step is not TurnStep.DECLARE_BLOCKERS:
            return ()
        if attack.attacker_ids != self._combat_attackers:
            return ()
        attackers = [self._objects[object_id] for object_id in attack.attacker_ids]
        if not all(isinstance(obj, Permanent) for obj in attackers):
            return ()
        generated = self.generate_blocks(attackers, defender_index, log_rejections=False)  # type: ignore[arg-type]
        options = [ActionOption(ActionKind.DECLARE_BLOCKERS, defender_index)]
        if generated:
            options.append(
                ActionOption(
                    ActionKind.DECLARE_BLOCKERS,
                    defender_index,
                    blocks=tuple(
                        (attacker_id, blocker.object_id)
                        for attacker_id, blocker in generated.items()
                    ),
                )
            )
        return tuple(options)

    def _sneak_semantics(self, card: CardObject):
        for fragment in self.interpreter.fragments(card.card):
            semantics = self.interpreter.sneak_semantic_coverage(card.card, fragment)
            if semantics is not None and semantics.coverage.fully_supported:
                return fragment, semantics
        return None

    def _unblocked_attackers(self, player_index: int) -> tuple[Permanent, ...]:
        blocked = {attacker_id for attacker_id, _blocker_id in self._combat_blocks}
        result: list[Permanent] = []
        for object_id in self._combat_attackers:
            attacker = self._objects.get(object_id)
            if (
                object_id not in blocked
                and isinstance(attacker, Permanent)
                and self.is_authoritative(attacker, "battlefield")
                and attacker.controller == player_index
            ):
                result.append(attacker)
        return tuple(result)

    def sneak_payment_plan(
        self, player_index: int, card: CardObject, attacker: Permanent
    ) -> SneakPaymentPlan | None:
        """Build one immutable fixed-cost Sneak plan without mutating game state."""
        if (
            player_index != self.active_player
            or self.step is not TurnStep.DECLARE_BLOCKERS
            or not self._blockers_declared
            or self.priority_state is not None
            or self.stack
            or not self.is_authoritative(card, "hand")
            or card.owner != player_index
            or attacker not in self._unblocked_attackers(player_index)
        ):
            return None
        interpreted = self._sneak_semantics(card)
        if interpreted is None:
            return None
        fragment, semantics = interpreted
        program: SneakProgram = semantics.program
        assert program.mana_cost is not None
        requirement = self.activation_mana_requirement(program.mana_cost)
        if requirement is None:
            return None
        available = [
            permanent
            for permanent in self.players[player_index].battlefield
            if permanent.card.is_land and not permanent.tapped and permanent is not attacker
        ]
        chosen: list[Permanent] = []
        for color in requirement.colored:
            source = next(
                (permanent for permanent in available if self._mana_color(permanent) == color),
                None,
            )
            if source is None:
                return None
            chosen.append(source)
            available.remove(source)
        if len(available) < requirement.generic:
            return None
        chosen.extend(available[: requirement.generic])
        return SneakPaymentPlan(
            player_index,
            card.object_id,
            attacker.object_id,
            requirement,
            tuple(source.object_id for source in chosen),
            1 - player_index,
            fragment,
        )

    def legal_sneak_actions(self, player_index: int) -> tuple[ActionOption, ...]:
        """Generate represented Sneak announcements after blockers are declared."""
        if (
            player_index != self.active_player
            or self.step is not TurnStep.DECLARE_BLOCKERS
            or not self._blockers_declared
            or self.priority_state is not None
            or self.stack
        ):
            return ()
        options: list[ActionOption] = []
        for card in self.players[player_index].hand:
            interpreted = self._sneak_semantics(card)
            if interpreted is None:
                continue
            fragment, _semantics = interpreted
            for attacker in self._unblocked_attackers(player_index):
                if self.sneak_payment_plan(player_index, card, attacker) is not None:
                    options.append(
                        ActionOption(
                            ActionKind.CAST,
                            player_index,
                            object_id=card.object_id,
                            cost_object_id=attacker.object_id,
                            oracle_fragment=fragment,
                        )
                    )
        options.append(ActionOption(ActionKind.PASS, player_index))
        return tuple(options)

    def execute_attack_action(self, attack: ActionOption) -> None:
        """Revalidate and execute the declare-attackers turn-based action."""
        if attack not in self.legal_attack_options(attack.player_index):
            raise ValueError("attack option is not currently legal")
        attackers = [self._objects[object_id] for object_id in attack.attacker_ids]
        if not all(isinstance(obj, Permanent) for obj in attackers):
            raise ValueError("combat option references a nonpermanent")
        for attacker in attackers:
            attacker.tapped = True  # type: ignore[union-attr]
        self._combat_attackers = attack.attacker_ids
        self._attackers_declared = True
        self.log("attackers_declared", attackers=list(attack.attacker_ids))
        self.resolve_attack_pt_effects(attackers)  # type: ignore[arg-type]
        if self.priority_state is None:
            self.transition_to(TurnStep.DECLARE_BLOCKERS)

    def execute_block_action(self, blocks: ActionOption) -> None:
        """Revalidate and execute the declare-blockers turn-based action."""
        attack = ActionOption(
            ActionKind.DECLARE_ATTACKERS,
            self.active_player,
            attacker_ids=self._combat_attackers,
        )
        defender = 1 - self.active_player
        if blocks not in self.legal_block_options(attack, defender):
            raise ValueError("block option is not currently legal")
        if blocks.blocks:
            attackers = [self._objects[object_id] for object_id in self._combat_attackers]
            generated = self.generate_blocks(attackers, defender, log_rejections=True)  # type: ignore[arg-type]
            resolved = tuple(
                (attacker_id, blocker.object_id) for attacker_id, blocker in generated.items()
            )
            if resolved != blocks.blocks:
                raise ValueError("block option became stale or illegal")
        self._combat_blocks = blocks.blocks
        self._blockers_declared = True
        self.log("blockers_declared", blocks=[list(pair) for pair in blocks.blocks])
        if not any(
            option.kind is ActionKind.CAST
            for option in self.legal_sneak_actions(self.active_player)
        ):
            self.transition_to(TurnStep.COMBAT_DAMAGE)

    def execute_sneak_action(self, option: ActionOption) -> bool:
        """Revalidate and execute one engine-generated Sneak action or decline."""
        if option not in self.legal_sneak_actions(option.player_index):
            raise ValueError("Sneak action is not currently legal")
        if option.kind is ActionKind.PASS:
            self.transition_to(TurnStep.COMBAT_DAMAGE)
            return True
        card = self._objects.get(option.object_id or "")
        attacker = self._objects.get(option.cost_object_id or "")
        if not isinstance(card, CardObject) or not isinstance(attacker, Permanent):
            raise ValueError("Sneak option references an invalid runtime object")
        plan = self.sneak_payment_plan(option.player_index, card, attacker)
        if plan is None or plan.oracle_fragment != option.oracle_fragment:
            raise ValueError("Sneak option became stale or illegal")
        self._commit_sneak_announcement(card, attacker, plan)
        return True

    def evaluated_strike_keywords(self, permanent: Permanent) -> frozenset[StrikeKeyword]:
        """Evaluate the represented printed and static combat-step keyword characteristics."""
        if not self.is_authoritative(permanent, "battlefield"):
            return frozenset()
        keywords = {
            keyword
            for keyword in StrikeKeyword
            if keyword.value.replace("_", " ").casefold()
            in {value.casefold() for value in permanent.card.keywords}
        }
        keywords.update(effect.keyword for effect in permanent.temporary_keyword_effects)
        for fragment in self.interpreter.fragments(permanent.card):
            semantics = self.interpreter.strike_semantic_coverage(permanent.card, fragment)
            if semantics is None or not semantics.coverage.fully_supported:
                continue
            if semantics.program.applicability is StrikeApplicability.SELF or (
                semantics.program.applicability is StrikeApplicability.SELF_DURING_CONTROLLER_TURN
                and permanent.controller == self.active_player
            ):
                keywords.add(semantics.program.keyword)
        if permanent.object_id in self._combat_attackers:
            for source in self.players[permanent.controller].battlefield:
                for fragment in self.interpreter.fragments(source.card):
                    semantics = self.interpreter.strike_semantic_coverage(source.card, fragment)
                    if (
                        semantics is not None
                        and semantics.coverage.fully_supported
                        and semantics.program.applicability
                        is StrikeApplicability.ATTACKING_CREATURES_YOU_CONTROL
                    ):
                        keywords.add(semantics.program.keyword)
        return frozenset(keywords)

    def _combat_permanent(self, object_id: str, role: str) -> Permanent:
        obj = self._objects.get(object_id)
        if not isinstance(obj, Permanent):
            raise ValueError(f"combat state references a fabricated or nonpermanent {role}")
        return obj

    def _start_combat_damage_step(
        self, kind: CombatDamageStepKind, sequence: int, total_steps: int
    ) -> None:
        self._combat_damage_step_kind = kind
        self._combat_damage_step_number = sequence
        self._combat_damage_total_steps = total_steps
        self._combat_damage_resolved = False
        self.log(
            "combat_damage_step_started",
            damage_step=kind.value,
            sequence=sequence,
            total_steps=total_steps,
        )

    def _begin_combat_damage_steps(self) -> None:
        """Determine the CR 510.4 one- or two-step combat-damage sequence."""
        combatant_ids = tuple(
            dict.fromkeys(
                self._combat_attackers
                + tuple(blocker_id for _attacker_id, blocker_id in self._combat_blocks)
            )
        )
        combatants = tuple(
            self._combat_permanent(object_id, "combatant") for object_id in combatant_ids
        )
        remaining = tuple(
            permanent for permanent in combatants if self.is_authoritative(permanent, "battlefield")
        )
        evaluated = {
            permanent.object_id: self.evaluated_strike_keywords(permanent)
            for permanent in remaining
        }
        self._first_damage_qualified_ids = tuple(
            permanent.object_id
            for permanent in remaining
            if evaluated[permanent.object_id]
            & {StrikeKeyword.FIRST_STRIKE, StrikeKeyword.DOUBLE_STRIKE}
        )
        self._first_double_strike_ids = tuple(
            permanent.object_id
            for permanent in remaining
            if StrikeKeyword.DOUBLE_STRIKE in evaluated[permanent.object_id]
        )
        self._regular_damage_initial_ids = tuple(
            permanent.object_id
            for permanent in remaining
            if not evaluated[permanent.object_id]
            & {StrikeKeyword.FIRST_STRIKE, StrikeKeyword.DOUBLE_STRIKE}
        )
        if self._first_damage_qualified_ids:
            self._start_combat_damage_step(CombatDamageStepKind.FIRST_STRIKE, 1, 2)
        else:
            self._start_combat_damage_step(CombatDamageStepKind.REGULAR, 1, 1)

    def _damage_step_eligible_ids(self) -> set[str]:
        if self._combat_damage_step_kind is CombatDamageStepKind.FIRST_STRIKE:
            return set(self._first_damage_qualified_ids)
        if self._combat_damage_step_kind is not CombatDamageStepKind.REGULAR:
            raise ValueError("combat damage step is not active")
        current_double = {
            object_id
            for object_id in self._combat_attackers
            + tuple(blocker_id for _attacker_id, blocker_id in self._combat_blocks)
            if isinstance((obj := self._objects.get(object_id)), Permanent)
            and self.is_authoritative(obj, "battlefield")
            and StrikeKeyword.DOUBLE_STRIKE in self.evaluated_strike_keywords(obj)
        }
        return set(self._regular_damage_initial_ids) | current_double

    def _combat_assignment(
        self,
        source: Permanent,
        *,
        target: Permanent | None = None,
        target_player: int | None = None,
        amount: int | None = None,
        trample: bool = False,
        lethal_required: int | None = None,
    ) -> CombatDamageAssignment:
        if self._combat_damage_step_kind is CombatDamageStepKind.FIRST_STRIKE:
            role = (
                "double_strike_first"
                if source.object_id in self._first_double_strike_ids
                else "first_strike"
            )
        else:
            role = (
                "double_strike_second"
                if StrikeKeyword.DOUBLE_STRIKE in self.evaluated_strike_keywords(source)
                else "regular"
            )
        return CombatDamageAssignment(
            source.object_id,
            None if target is None else target.object_id,
            target_player,
            max(0, source.power) if amount is None else amount,
            role,
            trample,
            lethal_required,
        )

    def evaluated_trample(self, permanent: Permanent) -> bool:
        """Evaluate only authoritative, fully supported Trample characteristics."""
        if not self.is_authoritative(permanent, "battlefield"):
            return False
        if isinstance(permanent.card, TokenDefinition) and "trample" in {
            keyword.casefold() for keyword in permanent.card.keywords
        }:
            return True
        return any(
            semantics is not None
            and semantics.coverage.payload_executable
            and semantics.coverage.parent_executable
            for fragment in self.interpreter.fragments(permanent.card)
            if (semantics := self.interpreter.trample_semantic_coverage(permanent.card, fragment))
            is not None
        )

    def evaluated_lifelink(self, source: CardObject | StackObject | Permanent) -> bool:
        """Evaluate only authoritative intrinsic Lifelink on the damage source."""
        if not (
            self.is_authoritative(source, "battlefield") or self.is_authoritative(source, "stack")
        ):
            return False
        if isinstance(source.card, TokenDefinition) and "lifelink" in {
            keyword.casefold() for keyword in source.card.keywords
        }:
            return True
        return any(
            semantics.coverage.fully_supported
            for fragment in self.interpreter.fragments(source.card)
            if (semantics := self.interpreter.lifelink_semantic_coverage(source.card, fragment))
            is not None
        )

    def _apply_lifelink_result(
        self,
        source: CardObject | StackObject | Permanent,
        amount: int,
        *,
        combat: bool,
        damage_step: CombatDamageStepKind | None,
        target_ids: tuple[str, ...],
        target_players: tuple[int, ...],
    ) -> LifelinkEvidence:
        """Apply CR 120.3f once for one authoritative source's damage event."""
        if not self.evaluated_lifelink(source):
            raise ValueError("Lifelink result requires an authoritative source with lifelink")
        if amount <= 0:
            raise ValueError("Lifelink result requires positive damage")
        controller = source.controller
        life_before = self.players[controller].life
        event = self.gain_life(
            controller,
            amount,
            source_card=source.card.name,
            oracle_fragment="Lifelink",
            defer_trigger_delivery=True,
        )
        evidence = LifelinkEvidence(
            event.event_id,
            source.object_id,
            controller,
            amount,
            combat,
            damage_step,
            target_ids,
            target_players,
            life_before,
            self.players[controller].life,
        )
        self.lifelink_evidence.append(evidence)
        self.log(
            "lifelink_result",
            event_id=event.event_id,
            source_id=source.object_id,
            source_card=source.card.name,
            controller=self.players[controller].name,
            amount=amount,
            combat=combat,
            damage_step=None if damage_step is None else damage_step.value,
            target_ids=list(target_ids),
            target_players=[self.players[index].name for index in target_players],
            life_before=evidence.life_before,
            life_after=evidence.life_after,
        )
        return evidence

    def resolve_combat_damage(self) -> CombatDamageStepEvidence:
        """Resolve exactly one authoritative CR 510.4 combat-damage step."""
        if (
            self.step is not TurnStep.COMBAT_DAMAGE
            or self._combat_damage_resolved
            or self._combat_damage_step_kind
            not in {CombatDamageStepKind.FIRST_STRIKE, CombatDamageStepKind.REGULAR}
        ):
            raise ValueError("combat damage step is not ready to resolve")
        if len(set(self._combat_attackers)) != len(self._combat_attackers):
            raise ValueError("combat state contains a duplicate attacker")
        if len({blocker_id for _attacker_id, blocker_id in self._combat_blocks}) != len(
            self._combat_blocks
        ):
            raise ValueError("combat state contains a duplicate blocker")

        defender_index = 1 - self.active_player
        attackers = {
            object_id: self._combat_permanent(object_id, "attacker")
            for object_id in self._combat_attackers
        }
        blocks = {
            attacker_id: self._combat_permanent(blocker_id, "blocker")
            for attacker_id, blocker_id in self._combat_blocks
        }
        if any(attacker_id not in attackers for attacker_id in blocks):
            raise ValueError("combat state assigns a blocker to a nonattacker")
        eligible = self._damage_step_eligible_ids()
        assignments: list[CombatDamageAssignment] = []
        damaged_pairs: list[tuple[Permanent, Permanent]] = []
        trample_inputs: dict[
            str, tuple[str | None, int, int | None, int | None, int, int, int]
        ] = {}
        for attacker_id, attacker in attackers.items():
            attacker_present = self.is_authoritative(attacker, "battlefield")
            blocker = blocks.get(attacker_id)
            blocker_present = blocker is not None and self.is_authoritative(blocker, "battlefield")
            if blocker is None:
                if attacker_present and attacker_id in eligible and attacker.power > 0:
                    assignments.append(
                        self._combat_assignment(attacker, target_player=defender_index)
                    )
                continue
            if attacker_present and blocker_present and attacker_id in eligible:
                power = max(0, attacker.power)
                if self.evaluated_trample(attacker) and power > 0:
                    lethal = max(0, blocker.toughness - blocker.damage)
                    blocker_damage = min(power, lethal)
                    excess = power - blocker_damage
                    trample_inputs[attacker_id] = (
                        blocker.object_id,
                        power,
                        blocker.toughness,
                        blocker.damage,
                        lethal,
                        blocker_damage,
                        excess,
                    )
                    if blocker_damage:
                        assignments.append(
                            self._combat_assignment(
                                attacker,
                                target=blocker,
                                amount=blocker_damage,
                                trample=True,
                                lethal_required=lethal,
                            )
                        )
                    if excess:
                        assignments.append(
                            self._combat_assignment(
                                attacker,
                                target_player=defender_index,
                                amount=excess,
                                trample=True,
                                lethal_required=lethal,
                            )
                        )
                elif power > 0:
                    assignments.append(self._combat_assignment(attacker, target=blocker))
            elif (
                attacker_present
                and blocker is not None
                and not blocker_present
                and attacker_id in eligible
                and self.evaluated_trample(attacker)
                and attacker.power > 0
            ):
                power = attacker.power
                trample_inputs[attacker_id] = (
                    blocker.object_id,
                    power,
                    None,
                    None,
                    0,
                    0,
                    power,
                )
                assignments.append(
                    self._combat_assignment(
                        attacker,
                        target_player=defender_index,
                        trample=True,
                        lethal_required=0,
                    )
                )
            if (
                attacker_present
                and blocker_present
                and blocker.object_id in eligible
                and blocker.power > 0
            ):
                assignments.append(self._combat_assignment(blocker, target=attacker))
            if (
                attacker_present
                and blocker_present
                and any(
                    assignment.source_id in {attacker.object_id, blocker.object_id}
                    for assignment in assignments
                )
            ):
                damaged_pairs.append((attacker, blocker))

        if len(
            {
                (assignment.source_id, assignment.target_id, assignment.target_player)
                for assignment in assignments
            }
        ) != len(assignments):
            raise AssertionError("a combatant repeated one assignment in a damage step")
        for source_id in {assignment.source_id for assignment in assignments}:
            source_assignments = [
                assignment for assignment in assignments if assignment.source_id == source_id
            ]
            if len(source_assignments) <= 1:
                continue
            source = self._combat_permanent(source_id, "damage source")
            if (
                len(source_assignments) != 2
                or not self.evaluated_trample(source)
                or sum(item.target_id is not None for item in source_assignments) != 1
                or sum(item.target_player is not None for item in source_assignments) != 1
            ):
                raise AssertionError("split assignments require bounded authoritative Trample")
        before_remaining = {
            permanent.object_id
            for permanent in tuple(attackers.values()) + tuple(blocks.values())
            if self.is_authoritative(permanent, "battlefield")
        }
        trample_life_before: dict[str, int] = {}
        trample_life_after: dict[str, int] = {}
        lifelink_assignments: dict[str, list[CombatDamageAssignment]] = {}
        for assignment in assignments:
            source = self._combat_permanent(assignment.source_id, "damage source")
            if self.evaluated_lifelink(source):
                lifelink_assignments.setdefault(source.object_id, []).append(assignment)
            if assignment.source_id in trample_inputs:
                trample_life_before.setdefault(
                    assignment.source_id, self.players[defender_index].life
                )
            if assignment.target_player is not None:
                self.players[assignment.target_player].life -= assignment.amount
                self.log(
                    "combat_damage_player",
                    source=source.card.name,
                    damage=assignment.amount,
                    damage_step=self._combat_damage_step_kind.value,
                    role=assignment.role,
                )
            else:
                assert assignment.target_id is not None
                target = self._combat_permanent(assignment.target_id, "damage target")
                target.damage += assignment.amount
                self.log(
                    "combat_damage_assignment",
                    source=source.card.name,
                    source_id=source.object_id,
                    target=target.card.name,
                    target_id=target.object_id,
                    damage=assignment.amount,
                    damage_step=self._combat_damage_step_kind.value,
                    role=assignment.role,
                )
            if assignment.source_id in trample_inputs:
                trample_life_after[assignment.source_id] = self.players[defender_index].life
        for source_id, source_assignments in lifelink_assignments.items():
            source = self._combat_permanent(source_id, "Lifelink damage source")
            self._apply_lifelink_result(
                source,
                sum(assignment.amount for assignment in source_assignments),
                combat=True,
                damage_step=self._combat_damage_step_kind,
                target_ids=tuple(
                    assignment.target_id
                    for assignment in source_assignments
                    if assignment.target_id is not None
                ),
                target_players=tuple(
                    assignment.target_player
                    for assignment in source_assignments
                    if assignment.target_player is not None
                ),
            )
        for attacker, blocker in dict.fromkeys(damaged_pairs):
            self.log(
                "combat_damage_creatures",
                attacker=attacker.card.name,
                blocker=blocker.card.name,
            )

        resolved_kind = self._combat_damage_step_kind
        resolved_sequence = self._combat_damage_step_number
        resolved_total = self._combat_damage_total_steps
        self.check_state_based_actions()
        self.check_life()
        if lifelink_assignments:
            self._put_pending_triggers_on_stack()
            self._drain_triggered_abilities()
        after_remaining = {
            object_id
            for object_id in before_remaining
            if isinstance((obj := self._objects.get(object_id)), Permanent)
            and self.is_authoritative(obj, "battlefield")
        }
        removed = tuple(sorted(before_remaining - after_remaining))
        trample_results: list[TrampleDamageEvidence] = []
        for source_id, (
            blocker_id,
            attacker_power,
            blocker_toughness,
            blocker_damage_before,
            lethal,
            blocker_assigned,
            player_assigned,
        ) in trample_inputs.items():
            blocker_after = self._objects.get(blocker_id) if blocker_id is not None else None
            blocker_survived = isinstance(blocker_after, Permanent) and self.is_authoritative(
                blocker_after, "battlefield"
            )
            trample_results.append(
                TrampleDamageEvidence(
                    source_id,
                    blocker_id,
                    resolved_kind,
                    attacker_power,
                    blocker_toughness,
                    blocker_damage_before,
                    lethal,
                    blocker_assigned,
                    player_assigned,
                    defender_index,
                    trample_life_before[source_id],
                    trample_life_after[source_id],
                    blocker_after.damage if blocker_survived else None,
                    blocker_survived,
                )
            )
        evidence = CombatDamageStepEvidence(
            resolved_kind,
            resolved_sequence,
            resolved_total,
            tuple(assignments),
            removed,
            tuple(trample_results),
        )
        self.combat_damage_evidence.append(evidence)
        self.log(
            "combat_damage_step_resolved",
            damage_step=resolved_kind.value,
            sequence=resolved_sequence,
            total_steps=resolved_total,
            assignments=len(assignments),
            removed_before_next_step=list(removed),
        )
        self._combat_damage_resolved = True
        self._advance_after_combat_damage()
        return evidence

    def play_land(self, player_index: int, card: CardObject) -> bool:
        player = self.players[player_index]
        if player_index != self.active_player or self.step not in {
            TurnStep.PRECOMBAT_MAIN,
            TurnStep.POSTCOMBAT_MAIN,
        }:
            return False
        if (
            not card.is_land
            or not self.is_authoritative(card, "hand")
            or card.owner != player_index
            or player.lands_played >= 1
        ):
            return False
        self.move_object(
            card,
            "battlefield",
            controller=player_index,
            summoning_sick=False,
            reason="land_played",
        )
        self.refresh_static_pt_modifiers()
        player.lands_played += 1
        self.log("land_played", player=player.name, card=card.name)
        return True

    @staticmethod
    def _mana_color(source: Permanent) -> str | None:
        match = re.search(r"Add \{([WUBRG])\}", source.card.oracle_text)
        if match:
            return match.group(1)
        return {
            "Plains": "W",
            "Island": "U",
            "Swamp": "B",
            "Mountain": "R",
            "Forest": "G",
        }.get(source.card.name)

    @staticmethod
    def mana_requirement(card: CardFact | CardObject) -> ManaRequirement | None:
        """Construct the currently represented fixed generic/colored total mana cost."""
        symbols = re.findall(r"\{([^}]+)\}", card.mana_cost)
        generic = 0
        colored: list[str] = []
        for symbol in symbols:
            if symbol.isdecimal():
                generic += int(symbol)
            elif symbol in {"W", "U", "B", "R", "G"}:
                colored.append(symbol)
            else:
                return None
        requirement = ManaRequirement(generic, tuple(colored))
        if requirement.total != card.mana_value:
            return None
        return requirement

    @staticmethod
    def activation_mana_requirement(mana_cost: str) -> ManaRequirement | None:
        """Construct one represented fixed activation mana requirement."""
        symbols = re.findall(r"\{([^}]+)\}", mana_cost)
        if "".join(f"{{{symbol}}}" for symbol in symbols) != mana_cost:
            return None
        generic = 0
        colored: list[str] = []
        for symbol in symbols:
            if symbol.isdecimal():
                generic += int(symbol)
            elif symbol in {"W", "U", "B", "R", "G"}:
                colored.append(symbol)
            else:
                return None
        return ManaRequirement(generic, tuple(colored))

    def activation_payment_plan(
        self, player_index: int, source: Permanent, oracle_fragment: str
    ) -> ActivationPaymentPlan | None:
        """Build a deterministic activation payment without mutating game state."""
        if (
            player_index not in range(2)
            or not self.is_authoritative(source, "battlefield")
            or source.controller != player_index
        ):
            return None
        semantics = self.interpreter.activated_ability_semantics(source.card, oracle_fragment)
        if semantics is None or not semantics.coverage.fully_supported:
            return None
        cost = semantics.program.cost
        requirement = self.activation_mana_requirement(cost.mana_cost)
        if requirement is None:
            return None
        if cost.tap_source and (
            source.tapped
            or (
                source.card.is_creature
                and source.summoning_sick
                and "Haste" not in source.card.keywords
            )
        ):
            return None
        available = [
            permanent
            for permanent in self.players[player_index].battlefield
            if permanent.card.is_land
            and not permanent.tapped
            and (not cost.tap_source or permanent is not source)
        ]
        chosen: list[Permanent] = []
        for color in requirement.colored:
            mana_source = next(
                (permanent for permanent in available if self._mana_color(permanent) == color),
                None,
            )
            if mana_source is None:
                return None
            chosen.append(mana_source)
            available.remove(mana_source)
        if len(available) < requirement.generic:
            return None
        chosen.extend(available[: requirement.generic])
        return ActivationPaymentPlan(
            player_index,
            source.object_id,
            oracle_fragment,
            requirement,
            tuple(permanent.object_id for permanent in chosen),
            cost.tap_source,
            cost.sacrifice_source,
        )

    def legal_activated_ability_actions(self, player_index: int) -> tuple[ActionOption, ...]:
        """Generate bounded engine-owned activation options for the current priority window."""
        if (
            player_index != self.active_player
            or self.step not in {TurnStep.PRECOMBAT_MAIN, TurnStep.POSTCOMBAT_MAIN}
            or self.stack
        ):
            return ()
        options: list[ActionOption] = []
        for source in self.players[player_index].battlefield:
            for fragment in self.interpreter.fragments(source.card):
                plan = self.activation_payment_plan(player_index, source, fragment)
                if plan is None:
                    continue
                semantics = self.interpreter.activated_ability_semantics(source.card, fragment)
                if semantics is None or not semantics.coverage.fully_supported:
                    continue
                if (
                    semantics.program.effect_kind
                    is ActivatedEffectKind.RETURN_ANOTHER_CREATURE_YOU_CONTROL_TO_OWNERS_HAND
                ):
                    for target in self.players[player_index].battlefield:
                        if target is source or not target.card.is_creature:
                            continue
                        options.append(
                            ActionOption(
                                ActionKind.ACTIVATE_ABILITY,
                                player_index,
                                object_id=source.object_id,
                                target_id=target.object_id,
                                oracle_fragment=fragment,
                            )
                        )
                else:
                    options.append(
                        ActionOption(
                            ActionKind.ACTIVATE_ABILITY,
                            player_index,
                            object_id=source.object_id,
                            oracle_fragment=fragment,
                        )
                    )
        return tuple(options)

    def announce_activated_ability(
        self,
        player_index: int,
        source: Permanent,
        oracle_fragment: str,
        *,
        target_ids: tuple[str, ...] = (),
        choice_ids: tuple[str, ...] = (),
    ) -> ActivatedAbilityObject | None:
        """Revalidate, transactionally pay, and put one activated ability on the stack."""
        if (
            player_index != self.active_player
            or self.step not in {TurnStep.PRECOMBAT_MAIN, TurnStep.POSTCOMBAT_MAIN}
            or self.stack
            or not self.is_authoritative(source, "battlefield")
            or source.controller != player_index
        ):
            return None
        semantics = self.interpreter.activated_ability_semantics(source.card, oracle_fragment)
        if semantics is None or not semantics.coverage.fully_supported:
            return None
        targeted_return = (
            semantics.program.effect_kind
            is ActivatedEffectKind.RETURN_ANOTHER_CREATURE_YOU_CONTROL_TO_OWNERS_HAND
        )
        if choice_ids or semantics.program.choices_required:
            return None
        if targeted_return:
            if len(target_ids) != 1:
                return None
            target = self._objects.get(target_ids[0])
            if (
                not isinstance(target, Permanent)
                or not self.is_authoritative(target, "battlefield")
                or target is source
                or target.controller != player_index
                or not target.card.is_creature
            ):
                return None
        elif target_ids or semantics.program.target_count:
            return None
        plan = self.activation_payment_plan(player_index, source, oracle_fragment)
        if plan is None:
            return None
        mana_sources: list[Permanent] = []
        for object_id in plan.mana_source_ids:
            candidate = self._objects.get(object_id)
            if not isinstance(candidate, Permanent) or not self.is_authoritative(
                candidate, "battlefield"
            ):
                raise ValueError("activation mana source is not authoritative")
            mana_sources.append(candidate)
        if len({candidate.object_id for candidate in mana_sources}) != len(mana_sources):
            raise ValueError("activation payment cannot reuse a mana source")
        prior_mana_taps = tuple(candidate.tapped for candidate in mana_sources)
        prior_source_tapped = source.tapped
        starting_object_number = self._next_object_number
        source_index = self.players[source.controller].battlefield.index(source)
        sacrificed: CardObject | None = None
        ability: ActivatedAbilityObject | None = None
        try:
            if plan.sacrifice_source:
                sacrificed = CardObject(
                    self._allocate_object_id(),
                    source.card,
                    source.owner,
                    source.owner,
                    "graveyard",
                    is_token=source.is_token,
                )
            ability = ActivatedAbilityObject(
                object_id=self._allocate_object_id(),
                controller=player_index,
                source_id=source.object_id,
                source_card=source.card,
                oracle_fragment=oracle_fragment,
                program=semantics.program,
                mana_source_ids=plan.mana_source_ids,
                tap_source=plan.tap_source,
                sacrifice_source=plan.sacrifice_source,
                sacrificed_destination_id=(
                    sacrificed.object_id if sacrificed is not None else None
                ),
                target_ids=target_ids,
                choice_ids=choice_ids,
            )
            for mana_source in mana_sources:
                mana_source.tapped = True
            if plan.tap_source:
                source.tapped = True
            if sacrificed is not None:
                self.players[source.controller].battlefield.pop(source_index)
                self.players[source.owner].graveyard.append(sacrificed)
                source.zone = "former"
                self._register(sacrificed)
            self._register(ability)
            self.stack.append(ability)
        except Exception:
            for mana_source, tapped in zip(mana_sources, prior_mana_taps, strict=True):
                mana_source.tapped = tapped
            source.tapped = prior_source_tapped
            if sacrificed is not None:
                self.players[source.owner].graveyard[:] = [
                    item for item in self.players[source.owner].graveyard if item is not sacrificed
                ]
                self._objects.pop(sacrificed.object_id, None)
                if source not in self.players[source.controller].battlefield:
                    self.players[source.controller].battlefield.insert(source_index, source)
                source.zone = "battlefield"
            if ability is not None:
                self.stack[:] = [entry for entry in self.stack if entry is not ability]
                self._objects.pop(ability.object_id, None)
            self._next_object_number = starting_object_number
            raise
        evidence = ActivationEvidence(
            ability.object_id,
            source.object_id,
            player_index,
            oracle_fragment,
            plan.mana_source_ids,
            plan.tap_source,
            False,
        )
        self.activation_evidence.append(evidence)
        if sacrificed is not None:
            self.log(
                "zone_changed",
                card=source.card.name,
                owner=self.players[source.owner].name,
                source_object_id=source.object_id,
                destination_object_id=sacrificed.object_id,
                source_zone="battlefield",
                destination_zone="graveyard",
                reason="activation_sacrifice_cost",
            )
        self.log(
            "activation_announced",
            player=self.players[player_index].name,
            source=source.card.name,
            source_id=source.object_id,
            stack_object_id=ability.object_id,
            oracle_fragment=oracle_fragment,
        )
        self.log(
            "activation_cost_paid",
            player=self.players[player_index].name,
            source_id=source.object_id,
            stack_object_id=ability.object_id,
            generic=plan.requirement.generic,
            colored=list(plan.requirement.colored),
            mana_source_ids=list(plan.mana_source_ids),
            tap_source=plan.tap_source,
            sacrifice_source=plan.sacrifice_source,
            sacrificed_destination_id=(sacrificed.object_id if sacrificed is not None else None),
        )
        self.log(
            "activated_ability_stacked",
            stack_object_id=ability.object_id,
            source_id=source.object_id,
            controller=self.players[player_index].name,
        )
        if sacrificed is not None:
            self.check_state_based_actions()
        self._begin_priority_window()
        if sacrificed is not None:
            assert self.priority_state is not None
            self.food_activation_evidence.append(
                FoodActivationEvidence(
                    source_id=source.object_id,
                    source_name=source.card.name,
                    source_type_line=source.card.type_line,
                    source_owner=source.owner,
                    controller=player_index,
                    source_was_token=source.is_token,
                    oracle_fragment=oracle_fragment,
                    turn=self.turn,
                    step=self.step.value,
                    source_zone_before="battlefield",
                    mana_requirement=plan.requirement,
                    mana_source_ids=plan.mana_source_ids,
                    source_tapped_before=prior_source_tapped,
                    tap_paid=plan.tap_source,
                    sacrifice_paid=True,
                    sacrificed_destination_id=sacrificed.object_id,
                    sacrificed_destination_zone="graveyard",
                    stack_object_id=ability.object_id,
                    priority_epoch=self.priority_state.epoch,
                    resolved=False,
                    final_source_disposition=sacrificed.zone,
                )
            )
        return ability

    def activate_ability(
        self,
        player_index: int,
        source: Permanent,
        oracle_fragment: str,
        *,
        target_ids: tuple[str, ...] = (),
    ) -> bool:
        """Announce one ability and open the bounded engine-owned priority window."""
        ability = self.announce_activated_ability(
            player_index, source, oracle_fragment, target_ids=target_ids
        )
        return ability is not None

    def _resolve_activated_ability(self, ability: ActivatedAbilityObject) -> None:
        if (
            not self.stack
            or self.stack[-1] is not ability
            or not self.is_authoritative(ability, "stack")
        ):
            raise ValueError("activated ability must be the authoritative top stack object")
        if any(item.stack_object_id == ability.object_id for item in self.food_activation_evidence):
            self._validate_food_activation_linkage(ability)
        semantics = self.interpreter.activated_ability_semantics(
            ability.source_card, ability.oracle_fragment
        )
        if (
            semantics is None
            or not semantics.coverage.fully_supported
            or semantics.program != ability.program
        ):
            raise AssertionError("stacked activation no longer has executable semantics")
        self.stack.pop()
        ability.zone = "former"
        source = self._objects.get(ability.source_id)
        source_permanent = (
            source
            if isinstance(source, Permanent) and self.is_authoritative(source, "battlefield")
            else None
        )
        delivered = False
        food_life_before: int | None = None
        food_life_after: int | None = None
        if (
            ability.program.effect_kind is ActivatedEffectKind.GRANT_SELF_FIRST_STRIKE_UNTIL_EOT
            and source_permanent is not None
        ):
            source_permanent.temporary_keyword_effects.append(
                TemporaryKeywordEffect(
                    StrikeKeyword.FIRST_STRIKE,
                    "until_end_of_turn",
                    ability.source_id,
                    ability.oracle_fragment,
                )
            )
            delivered = True
            self.log(
                "temporary_keyword_granted",
                source_id=ability.source_id,
                target_id=source_permanent.object_id,
                keyword=StrikeKeyword.FIRST_STRIKE.value,
                duration="until_end_of_turn",
                oracle_fragment=ability.oracle_fragment,
            )
        elif (
            ability.program.effect_kind
            is ActivatedEffectKind.RETURN_ANOTHER_CREATURE_YOU_CONTROL_TO_OWNERS_HAND
        ):
            target = self._objects.get(ability.target_ids[0])
            if (
                isinstance(target, Permanent)
                and self.is_authoritative(target, "battlefield")
                and target.object_id != ability.source_id
                and target.controller == ability.controller
                and target.card.is_creature
            ):
                replacement = self.move_object(
                    target, "hand", reason="activated_return_to_owners_hand"
                )
                delivered = True
                self.log(
                    "target_returned_to_hand",
                    stack_object_id=ability.object_id,
                    source_id=ability.source_id,
                    target_id=target.object_id,
                    destination_object_id=replacement.object_id,
                    owner=self.players[target.owner].name,
                )
            else:
                self.log(
                    "activated_ability_resolved_no_effect",
                    stack_object_id=ability.object_id,
                    source_id=ability.source_id,
                    reason="target_illegal_at_resolution",
                )
        elif ability.program.effect_kind is ActivatedEffectKind.GAIN_THREE_LIFE:
            food_life_before = self.players[ability.controller].life
            self.gain_life(
                ability.controller,
                3,
                source_card=ability.source_card.name,
                oracle_fragment=ability.oracle_fragment,
                defer_trigger_delivery=True,
            )
            food_life_after = self.players[ability.controller].life
            delivered = True
        else:
            self.log(
                "activated_ability_resolved_no_effect",
                stack_object_id=ability.object_id,
                source_id=ability.source_id,
                reason="source_not_on_battlefield",
            )
        for index, evidence in enumerate(self.activation_evidence):
            if evidence.stack_object_id == ability.object_id:
                self.activation_evidence[index] = ActivationEvidence(
                    evidence.stack_object_id,
                    evidence.source_id,
                    evidence.controller,
                    evidence.oracle_fragment,
                    evidence.mana_source_ids,
                    evidence.tap_source,
                    True,
                )
                break
        if ability.program.effect_kind is ActivatedEffectKind.GAIN_THREE_LIFE:
            for index, evidence in enumerate(self.food_activation_evidence):
                if evidence.stack_object_id == ability.object_id:
                    self.food_activation_evidence[index] = replace(
                        evidence,
                        resolved=True,
                        life_before=food_life_before,
                        life_after=food_life_after,
                        amount_gained=(
                            food_life_after - food_life_before
                            if food_life_before is not None and food_life_after is not None
                            else None
                        ),
                    )
                    break
        self.log(
            "activated_ability_resolved",
            stack_object_id=ability.object_id,
            source_id=ability.source_id,
            controller=self.players[ability.controller].name,
            delivered=delivered,
        )
        if ability.program.effect_kind is ActivatedEffectKind.GAIN_THREE_LIFE:
            self._put_pending_triggers_on_stack()

    def _validate_food_activation_linkage(self, ability: ActivatedAbilityObject) -> None:
        """Authenticate one canonical Food stack object from immutable payment evidence."""
        activations = [
            item for item in self.activation_evidence if item.stack_object_id == ability.object_id
        ]
        foods = [
            item
            for item in self.food_activation_evidence
            if item.stack_object_id == ability.object_id
        ]
        if len(activations) != 1 or len(foods) != 1:
            raise AssertionError("Food stack object lacks unique activation provenance")
        activation = activations[0]
        food = foods[0]
        sacrificed = self._objects.get(food.sacrificed_destination_id)
        if (
            activation.resolved != food.resolved
            or ability.source_id != activation.source_id
            or ability.source_id != food.source_id
            or ability.controller != activation.controller
            or ability.controller != food.controller
            or ability.oracle_fragment != activation.oracle_fragment
            or ability.oracle_fragment != food.oracle_fragment
            or ability.mana_source_ids != activation.mana_source_ids
            or ability.mana_source_ids != food.mana_source_ids
            or ability.tap_source != activation.tap_source
            or ability.tap_source != food.tap_paid
            or not ability.sacrifice_source
            or not food.sacrifice_paid
            or ability.sacrificed_destination_id != food.sacrificed_destination_id
            or ability.source_card.name != food.source_name
            or ability.source_card.type_line != food.source_type_line
            or not isinstance(sacrificed, CardObject)
            or sacrificed.card != ability.source_card
            or sacrificed.owner != food.source_owner
            or sacrificed.is_token != food.source_was_token
            or ability.program.effect_kind is not ActivatedEffectKind.GAIN_THREE_LIFE
        ):
            raise AssertionError("Food stack object disagrees with activation provenance")

    def payment_plan(self, player_index: int, card: CardObject) -> PaymentPlan | None:
        """Build one deterministic legal payment without mutating authoritative state."""
        if not self.is_authoritative(card, "hand") or card.owner != player_index:
            return None
        requirement = self.mana_requirement(card)
        if requirement is None:
            return None
        available = [
            permanent
            for permanent in self.players[player_index].battlefield
            if permanent.card.is_land and not permanent.tapped
        ]
        chosen: list[Permanent] = []
        for color in requirement.colored:
            source = next(
                (permanent for permanent in available if self._mana_color(permanent) == color),
                None,
            )
            if source is None:
                return None
            chosen.append(source)
            available.remove(source)
        if len(available) < requirement.generic:
            return None
        chosen.extend(available[: requirement.generic])
        return PaymentPlan(
            player_index,
            card.object_id,
            requirement,
            tuple(source.object_id for source in chosen),
        )

    def can_afford(self, player_index: int, card: CardFact | CardObject) -> bool:
        if isinstance(card, CardObject):
            return self.payment_plan(player_index, card) is not None
        requirement = self.mana_requirement(card)
        if requirement is None:
            return False
        available = [
            permanent
            for permanent in self.players[player_index].battlefield
            if permanent.card.is_land and not permanent.tapped
        ]
        for color in requirement.colored:
            source = next(
                (permanent for permanent in available if self._mana_color(permanent) == color),
                None,
            )
            if source is None:
                return False
            available.remove(source)
        return len(available) >= requirement.generic

    def _commit_announcement_payment(
        self,
        card: CardObject,
        plan: PaymentPlan,
        *,
        cast_kind: CastKind,
        target_id: str | None,
    ) -> StackObject:
        """Atomically pay a revalidated plan and move the represented card Hand -> Stack."""
        if plan != self.payment_plan(plan.player_index, card):
            raise ValueError("payment plan is no longer legal")
        sources: list[Permanent] = []
        for object_id in plan.source_ids:
            source = self._objects.get(object_id)
            if not isinstance(source, Permanent) or not self.is_authoritative(
                source, "battlefield"
            ):
                raise ValueError("payment source is not authoritative")
            sources.append(source)
        previous_tapped = tuple(source.tapped for source in sources)
        try:
            for source in sources:
                source.tapped = True
            spell = self.move_object(
                card,
                "stack",
                controller=plan.player_index,
                cast_kind=cast_kind,
                target_id=target_id,
                reason="spell_cast",
            )
        except Exception:
            for source, tapped in zip(sources, previous_tapped, strict=True):
                source.tapped = tapped
            raise
        assert isinstance(spell, StackObject)
        self.log(
            "cost_paid",
            player=self.players[plan.player_index].name,
            card=card.name,
            generic=plan.requirement.generic,
            colored=list(plan.requirement.colored),
            source_ids=list(plan.source_ids),
        )
        return spell

    def _commit_sneak_announcement(
        self, card: CardObject, attacker: Permanent, plan: SneakPaymentPlan
    ) -> StackObject:
        """Atomically pay fixed Sneak mana plus the authoritative return cost."""
        if plan != self.sneak_payment_plan(plan.player_index, card, attacker):
            raise ValueError("Sneak payment plan is no longer legal")
        sources: list[Permanent] = []
        for object_id in plan.mana_source_ids:
            source = self._objects.get(object_id)
            if (
                not isinstance(source, Permanent)
                or not self.is_authoritative(source, "battlefield")
                or source.tapped
                or not source.card.is_land
            ):
                raise ValueError("Sneak mana source is not authoritative")
            sources.append(source)
        if len({source.object_id for source in sources}) != len(sources):
            raise ValueError("Sneak payment cannot reuse a mana source")

        # Construct both new zone incarnations before mutating any authoritative container.
        returned = CardObject(
            self._allocate_object_id(),
            attacker.card,
            attacker.owner,
            attacker.owner,
            "hand",
            is_token=attacker.is_token,
        )
        spell = StackObject(
            self._allocate_object_id(),
            card.card,
            card.owner,
            plan.player_index,
            CastKind.CREATURE,
            sneak_returned_attacker_id=attacker.object_id,
            sneak_returned_hand_id=returned.object_id,
            sneak_defending_player=plan.defending_player,
            sneak_oracle_fragment=plan.oracle_fragment,
            sneak_mana_source_ids=plan.mana_source_ids,
        )

        battlefield = self.players[attacker.controller].battlefield
        hand = self.players[card.owner].hand
        if not self._identity_contains(battlefield, attacker) or not self._identity_contains(
            hand, card
        ):
            raise ValueError("Sneak source zones changed before commitment")
        attacker_index = next(i for i, value in enumerate(battlefield) if value is attacker)
        card_index = next(i for i, value in enumerate(hand) if value is card)
        for source in sources:
            source.tapped = True
        battlefield.pop(attacker_index)
        hand.pop(card_index)
        self.players[attacker.owner].hand.append(returned)
        self.stack.append(spell)
        attacker.zone = "former"
        card.zone = "former"
        self._register(returned)
        self._register(spell)
        self._combat_attackers = tuple(
            object_id for object_id in self._combat_attackers if object_id != attacker.object_id
        )
        self._combat_blocks = tuple(
            pair for pair in self._combat_blocks if pair[0] != attacker.object_id
        )
        self.refresh_static_pt_modifiers()

        self.log(
            "zone_changed",
            card=attacker.card.name,
            owner=self.players[attacker.owner].name,
            source_object_id=attacker.object_id,
            destination_object_id=returned.object_id,
            source_zone="battlefield",
            destination_zone="hand",
            reason="sneak_return_cost",
        )
        self.log(
            "zone_changed",
            card=card.card.name,
            owner=self.players[card.owner].name,
            source_object_id=card.object_id,
            destination_object_id=spell.object_id,
            source_zone="hand",
            destination_zone="stack",
            reason="sneak_spell_cast",
        )
        self.log(
            "sneak_cost_paid",
            player=self.players[plan.player_index].name,
            card=card.card.name,
            mana_source_ids=list(plan.mana_source_ids),
            returned_attacker_id=attacker.object_id,
            returned_hand_id=returned.object_id,
        )
        self.log(
            "sneak_announced",
            player=self.players[plan.player_index].name,
            card=spell.name,
            hand_object_id=card.object_id,
            stack_object_id=spell.object_id,
            oracle_fragment=plan.oracle_fragment,
        )
        self.check_state_based_actions()
        self._begin_priority_window()
        assert self.priority_state is not None
        self.sneak_evidence.append(
            SneakEvidence(
                card.card.name,
                card.object_id,
                plan.player_index,
                self.turn,
                self.step.value,
                plan.oracle_fragment,
                plan.requirement,
                plan.mana_source_ids,
                attacker.object_id,
                returned.object_id,
                plan.defending_player,
                spell.object_id,
                self.priority_state.epoch,
            )
        )
        return spell

    def cast(self, player_index: int, card: CardObject, target: Permanent | None = None) -> bool:
        """Compatibility action: announce a represented spell, then resolve it immediately.

        Immediate resolution is an explicit temporary boundary until a priority controller owns
        pass sequencing. Every represented spell still traverses the authoritative stack lifecycle.
        """
        spell = self.announce_spell(player_index, card, target)
        if spell is None:
            return False
        self.resolve_top_of_stack()
        return True

    def announce_spell(
        self, player_index: int, card: CardObject, target: Permanent | None = None
    ) -> StackObject | None:
        """Validate announcement, pay represented mana, and atomically move Hand -> Stack."""
        player = self.players[player_index]
        if (
            player_index != self.active_player
            or self.step not in {TurnStep.PRECOMBAT_MAIN, TurnStep.POSTCOMBAT_MAIN}
            or not self.is_authoritative(card, "hand")
            or card.owner != player_index
        ):
            return None
        program = self.interpreter.cast_program(card.card)
        target_id: str | None = None
        if program.kind in {CastKind.DAMAGE_3_OPPOSING_CREATURE, CastKind.DEAL_DAMAGE}:
            if (
                target is None
                or not self.is_authoritative(target, "battlefield")
                or target.controller == player_index
            ):
                self.log(
                    "dead_interaction", player=player.name, card=card.name, reason="no_legal_target"
                )
                return None
            target_id = target.object_id
        elif program.kind is CastKind.DESTROY_OPPOSING_POWER_4:
            if (
                target is None
                or not self.is_authoritative(target, "battlefield")
                or target.controller == player_index
                or target.power < 4
            ):
                self.log(
                    "dead_interaction", player=player.name, card=card.name, reason="no_legal_target"
                )
                return None
            target_id = target.object_id
        elif program.kind is CastKind.UNSUPPORTED:
            fragments = [line.strip() for line in card.oracle_text.splitlines() if line.strip()]
            for fragment in fragments or [card.type_line]:
                self.unsupported(
                    card.card,
                    "spell_or_permanent_semantics_not_implemented",
                    player_index=player_index,
                    oracle_fragment=fragment,
                )
            return None

        requirement = self.mana_requirement(card)
        if requirement is None:
            self.unsupported(
                card.card,
                "mana_cost_not_implemented",
                player_index=player_index,
                oracle_fragment=card.mana_cost or "zero mana cost",
            )
            return None
        plan = self.payment_plan(player_index, card)
        if plan is None:
            return None
        spell = self._commit_announcement_payment(
            card, plan, cast_kind=program.kind, target_id=target_id
        )
        self.log(
            "spell_cast",
            player=player.name,
            card=spell.name,
            stack_object_id=spell.object_id,
            target_id=target_id,
        )
        return spell

    def resolve_top_of_stack(self) -> CardObject | Permanent | None:
        """Resolve the authoritative top spell or triggered ability."""
        if not self.stack:
            raise ValueError("cannot resolve an empty stack")
        spell = self.stack[-1]
        if not self.is_authoritative(spell, "stack"):
            raise ValueError("top stack object is not authoritative")
        if isinstance(spell, TriggeredAbilityObject):
            if spell.effect in {
                TriggerEffect.DISCARD_DRAW,
                TriggerEffect.DIES_DRAW,
                TriggerEffect.SNEAK_ETB_CONDITION,
                TriggerEffect.ETB_DRAIN_GAIN_SCRY,
                TriggerEffect.PERMANENT_LEFT_SELF_COUNTER,
                TriggerEffect.ETB_ARTIFACT_DRAW,
            } and (
                not self._priority_resolution_in_progress
                and (self.priority_state is None or not self.priority_state.resolution_pending)
            ):
                raise ValueError(
                    "represented triggered ability cannot resolve before all players pass"
                )
            self._resolve_triggered_ability(spell)
            return None
        if isinstance(spell, ActivatedAbilityObject):
            if not self._priority_resolution_in_progress and (
                self.priority_state is None or not self.priority_state.resolution_pending
            ):
                raise ValueError("activated ability cannot resolve before all players pass")
            self._resolve_activated_ability(spell)
            return None
        player = self.players[spell.controller]
        target = self._objects.get(spell.target_id or "")
        sneak_cast = spell.sneak_returned_attacker_id is not None
        if sneak_cast and (
            not self._priority_resolution_in_progress
            and (self.priority_state is None or not self.priority_state.resolution_pending)
        ):
            raise ValueError("Sneak spell cannot resolve before all players pass")

        if spell.cast_kind is CastKind.CREATURE:
            stack_object_id = spell.object_id
            permanent = self.move_object(
                spell,
                "battlefield",
                controller=spell.controller,
                summoning_sick=True if sneak_cast else "Haste" not in spell.card.keywords,
                reason="sneak_creature_resolved" if sneak_cast else "creature_resolved",
            )
            assert isinstance(permanent, Permanent)
            if sneak_cast:
                permanent.tapped = True
                self._combat_attackers = self._combat_attackers + (permanent.object_id,)
                self.log(
                    "sneak_creature_resolved",
                    player=player.name,
                    card=spell.name,
                    stack_object_id=stack_object_id,
                    permanent_object_id=permanent.object_id,
                    defending_player=spell.sneak_defending_player,
                    tapped=True,
                    attacking=True,
                )
                for index, evidence in enumerate(self.sneak_evidence):
                    if evidence.stack_object_id == stack_object_id:
                        self.sneak_evidence[index] = SneakEvidence(
                            evidence.card_name,
                            evidence.hand_object_id,
                            evidence.controller,
                            evidence.turn,
                            evidence.step,
                            evidence.oracle_fragment,
                            evidence.mana_requirement,
                            evidence.mana_source_ids,
                            evidence.returned_attacker_id,
                            evidence.returned_hand_id,
                            evidence.defending_player,
                            evidence.stack_object_id,
                            evidence.priority_epoch,
                            permanent.object_id,
                            True,
                            True,
                        )
                        break
            else:
                self.log("creature_resolved", player=player.name, card=spell.name)
            self.refresh_static_pt_modifiers()
            self._process_creature_entered_triggers(
                permanent,
                source_id=stack_object_id if sneak_cast else None,
                defer_triggers=sneak_cast,
                after_event=lambda source, _event: self.report_unsupported_abilities(
                    spell.controller, spell.card, source=source
                ),
            )
            if not sneak_cast:
                self.check_state_based_actions()
            return permanent

        legal_target = isinstance(target, Permanent) and self.is_authoritative(
            target, "battlefield"
        )
        if spell.cast_kind in {CastKind.DAMAGE_3_OPPOSING_CREATURE, CastKind.DEAL_DAMAGE}:
            legal_target = legal_target and target.controller != spell.controller
        elif spell.cast_kind is CastKind.DESTROY_OPPOSING_POWER_4:
            legal_target = (
                legal_target and target.controller != spell.controller and target.power >= 4
            )
        if not legal_target:
            resolved_card = self.move_object(spell, "graveyard", reason="spell_resolved")
            assert isinstance(resolved_card, CardObject)
            self.log(
                "spell_resolved_no_effect",
                player=player.name,
                card=spell.name,
                reason="all_targets_illegal",
            )
            return resolved_card
        assert isinstance(target, Permanent)
        filter_plan = None
        filter_semantics = None
        if spell.cast_kind in {CastKind.DAMAGE_3_OPPOSING_CREATURE, CastKind.DEAL_DAMAGE}:
            semantics = self.interpreter.damage_semantic_coverage(
                spell.card, spell.card.oracle_text
            )
            if semantics is None or not semantics.coverage.payload_executable:
                raise AssertionError("stacked damage spell no longer has executable semantics")
            assert semantics.program.amount is not None
            filter_semantics = self.interpreter.hand_bottom_draw_semantic_coverage(
                spell.card, spell.card.oracle_text
            )
            filter_executable = (
                filter_semantics is not None and filter_semantics.coverage.fully_supported
            )
            self.deal_damage(
                DamageTransaction(
                    spell.controller,
                    spell,
                    DamageTargetKind.CREATURE,
                    semantics.program.amount,
                    spell.card.oracle_text,
                    target=target,
                ),
                defer_post_damage=filter_executable,
            )
            if filter_executable:
                assert filter_semantics is not None
                filter_plan = self.choose_hand_bottom_draw(
                    spell.controller, filter_semantics.program
                )
                self.commit_hand_bottom_draw(
                    spell.controller,
                    filter_semantics.program,
                    filter_plan,
                    source_id=spell.object_id,
                    oracle_fragment=spell.card.oracle_text,
                )
        elif spell.cast_kind is CastKind.DESTROY_OPPOSING_POWER_4:
            self.destroy(target)
        resolved_card = self.move_object(spell, "graveyard", reason="spell_resolved")
        assert isinstance(resolved_card, CardObject)
        self.report_unsupported_abilities(spell.controller, spell.card, source=resolved_card)
        self._witness_resolved_unsupported_instructions(resolved_card)
        self.log("spell_resolved", player=player.name, card=spell.name, target=target.card.name)
        if filter_plan is not None:
            self.check_state_based_actions()
            self.check_life()
            self._put_pending_triggers_on_stack()
            self._drain_triggered_abilities()
        return resolved_card

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
        for fragment in self.interpreter.fragments(attacker.card):
            match = self.interpreter.CANT_BE_BLOCKED_BY_POWER_OR_GREATER.fullmatch(fragment)
            if match and blocker.power >= int(match.group(1)):
                return fragment, "blocker_power_at_or_above_restriction"
            if (
                self.interpreter.CANT_BE_BLOCKED_BY_GREATER_POWER.fullmatch(fragment)
                and blocker.power > attacker.power
            ):
                return fragment, "blocker_power_greater_than_attacker"
        return None

    def _witness_unsupported_block_context(self, attacker: Permanent, blocker: Permanent) -> None:
        """Record a Menace opportunity only for an authoritative blocker candidate."""
        if not (
            self.step is TurnStep.DECLARE_BLOCKERS
            and self.is_authoritative(attacker, "battlefield")
            and self.is_authoritative(blocker, "battlefield")
            and attacker.object_id in self._combat_attackers
        ):
            return
        for occurrence in self.semantic_occurrences:
            if occurrence.object_id == attacker.object_id and occurrence.oracle_fragment.startswith(
                "Menace "
            ):
                self._record_opportunity(
                    occurrence,
                    cause_kind="legal_block_context",
                    cause_id=(
                        f"block:{self.turn}:{self.step.value}:"
                        f"{attacker.object_id}:{blocker.object_id}"
                    ),
                    cause_subject_ids=(attacker.object_id, blocker.object_id),
                )

    def can_block(self, attacker: Permanent, blocker: Permanent, defender_index: int) -> bool:
        return (
            blocker.controller == defender_index
            and any(candidate is blocker for candidate in self.players[defender_index].battlefield)
            and blocker.card.is_creature
            and not blocker.tapped
            and self.blocking_restriction(attacker, blocker) is None
        )

    def generate_blocks(
        self,
        attackers: list[Permanent],
        defender_index: int,
        *,
        log_rejections: bool = True,
    ) -> dict[str, Permanent]:
        """Generate deterministic one-to-one blocks using the same legality as validation."""
        available = [
            permanent
            for permanent in self.players[defender_index].battlefield
            if permanent.card.is_creature and not permanent.tapped
        ]
        blocks: dict[str, Permanent] = {}
        for attacker in attackers:
            for blocker in available:
                self._witness_unsupported_block_context(attacker, blocker)
                restriction = self.blocking_restriction(attacker, blocker)
                if restriction is not None:
                    fragment, reason = restriction
                    if log_rejections:
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
                blocks[attacker.object_id] = blocker
                available.remove(blocker)
                break
        return blocks

    def combat(
        self,
        attackers: list[Permanent],
        blocks: dict[str, Permanent] | None = None,
        *,
        auto_assign_blockers: bool = False,
    ) -> None:
        """Compatibility adapter over the three authoritative combat actions."""
        if self.step is not TurnStep.DECLARE_ATTACKERS:
            raise ValueError("attackers can be declared only during declare attackers")
        attacker_ids = tuple(attacker.object_id for attacker in attackers)
        attack = next(
            (
                option
                for option in self.legal_attack_options(self.active_player)
                if option.attacker_ids == attacker_ids
                and all(self._objects.get(attacker.object_id) is attacker for attacker in attackers)
            ),
            None,
        )
        if attack is None:
            raise ValueError("illegal attacker")
        defender = 1 - self.active_player
        if not auto_assign_blockers:
            blocks = blocks or {}
            attacker_id_set = set(attacker_ids)
            if any(attacker_id not in attacker_id_set for attacker_id in blocks):
                raise ValueError("block assigned to a nonattacker")
            if len({blocker.object_id for blocker in blocks.values()}) != len(blocks):
                raise ValueError("illegal blocker")
            if any(
                not self.is_authoritative(blocker, "battlefield")
                or not self.can_block(
                    self._objects[attacker_id],
                    blocker,
                    defender,  # type: ignore[arg-type]
                )
                for attacker_id, blocker in blocks.items()
            ):
                raise ValueError("illegal blocker")
        self.execute_attack_action(attack)
        if auto_assign_blockers:
            if blocks is not None:
                raise ValueError("cannot provide blocks when auto-assigning blockers")
            block_option = max(
                self.legal_block_options(attack, defender),
                key=lambda option: len(option.blocks),
            )
        else:
            assert blocks is not None
            block_option = ActionOption(
                ActionKind.DECLARE_BLOCKERS,
                defender,
                blocks=tuple(
                    (attacker_id, blocker.object_id) for attacker_id, blocker in blocks.items()
                ),
            )
        self.execute_block_action(block_option)
        if self.step is TurnStep.DECLARE_BLOCKERS:
            self.execute_sneak_action(ActionOption(ActionKind.PASS, self.active_player))
        while self.step is TurnStep.COMBAT_DAMAGE:
            self.resolve_combat_damage()

    def end_turn(self) -> None:
        """Compatibility helper: follow legal transitions through cleanup."""
        if self.step in {TurnStep.SETUP, TurnStep.CLEANUP}:
            raise ValueError("end_turn is legal only during an active turn")
        while self.step is not TurnStep.POSTCOMBAT_MAIN:
            if self.step is TurnStep.COMBAT_DAMAGE:
                self.resolve_combat_damage()
            else:
                self.advance_step()
        self.advance_to(TurnStep.CLEANUP)

    def put_permanents_into_graveyard(
        self,
        permanents: tuple[Permanent, ...],
        *,
        state_based_action: str | None = None,
    ) -> tuple[CardObject, ...]:
        """Move one simultaneous battlefield batch with a shared last-known trigger snapshot."""
        if len({permanent.object_id for permanent in permanents}) != len(permanents):
            raise ValueError("simultaneous departure batch contains duplicate objects")
        if any(not self.is_authoritative(permanent, "battlefield") for permanent in permanents):
            raise ValueError("simultaneous departure requires authoritative permanents")
        authority = self._battlefield_authority_snapshot()
        sources = self._permanent_left_trigger_sources()
        return tuple(
            self.put_into_graveyard(
                permanent,
                state_based_action=state_based_action,
                _departure_authority=authority,
                _departure_sources=sources,
            )
            for permanent in permanents
        )

    def put_into_graveyard(
        self,
        permanent: Permanent,
        *,
        state_based_action: str | None = None,
        _departure_authority: tuple[tuple[str, int], ...] | None = None,
        _departure_sources: tuple[tuple[Permanent, str], ...] | None = None,
    ) -> CardObject:
        if not self.is_authoritative(permanent, "battlefield"):
            raise ValueError("permanent is not on the battlefield")
        owner = self.players[permanent.owner]
        controller = permanent.controller
        battlefield_authority = (
            self._battlefield_authority_snapshot()
            if _departure_authority is None
            else _departure_authority
        )
        dies_draw_fragments = tuple(
            fragment
            for fragment in self.interpreter.fragments(permanent.card)
            if (coverage := self.interpreter.dies_draw_semantic_coverage(permanent.card, fragment))
            is not None
            and coverage.fully_supported
        )
        last_known_type_line = permanent.type_line
        last_known_is_creature = permanent.is_creature
        self.alliance_modes_chosen.pop(permanent.object_id, None)
        replacement = self.move_object(
            permanent,
            "graveyard",
            reason=state_based_action or "put_into_graveyard",
            _departure_authority=battlefield_authority,
            _departure_sources=_departure_sources,
        )
        assert isinstance(replacement, CardObject)
        self.refresh_static_pt_modifiers()
        self.log(
            "permanent_to_graveyard",
            player=owner.name,
            card=permanent.card.name,
            state_based_action=state_based_action,
        )
        if dies_draw_fragments and last_known_is_creature:
            event = self._new_rules_event(
                RulesEventKind.CREATURE_DIED,
                controller,
                (permanent.object_id,),
                source_id=permanent.object_id,
                battlefield_authority=battlefield_authority,
                last_known_battlefield=(
                    (
                        permanent.object_id,
                        controller,
                        last_known_type_line,
                        last_known_is_creature,
                    ),
                ),
            )
            for fragment in dies_draw_fragments:
                self._enqueue_trigger(event, permanent, fragment, TriggerEffect.DIES_DRAW)
        return replacement

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
        self.check_life()
        if self.winner is None and self._put_pending_triggers_on_stack(
            {TriggerEffect.DIES_DRAW, TriggerEffect.PERMANENT_LEFT_SELF_COUNTER}
        ):
            self._drain_triggered_abilities()
        self.check_invariants()

    def check_invariants(self) -> None:
        combat_ids = self._combat_attackers + tuple(
            blocker_id for _attacker_id, blocker_id in self._combat_blocks
        )
        evidence_ids = [item.event_id for item in self._rules_event_evidence]
        if (
            len(evidence_ids) != len(set(evidence_ids))
            or set(evidence_ids) != set(self._rules_events)
            or [item.event_cursor for item in self._rules_event_evidence]
            != list(range(1, len(self._rules_event_evidence) + 1))
        ):
            raise AssertionError("rules-event evidence ledger is incomplete or duplicated")
        for event in self._rules_events.values():
            try:
                self._authenticate_original_rules_event(event)
            except ValueError as error:
                raise AssertionError(str(error)) from error
        occurrence_by_id = {item.occurrence_id: item for item in self.semantic_occurrences}
        if len(occurrence_by_id) != len(self.semantic_occurrences):
            raise AssertionError("semantic occurrence IDs must be unique")
        if len({item.opportunity_key for item in self.opportunity_witnesses}) != len(
            self.opportunity_witnesses
        ):
            raise AssertionError("opportunity witnesses must be deterministically deduplicated")
        context_by_id = {item.context_id: item for item in self.opportunity_contexts}
        if len(context_by_id) != len(self.opportunity_contexts):
            raise AssertionError("opportunity context IDs must be unique")
        for context in self.opportunity_contexts:
            if (
                context.source_id not in self._objects
                or any(subject_id not in self._objects for subject_id in context.subject_ids)
                or len(context.subject_ids) != len(context.subject_zones)
                or context.controller not in range(2)
                or not re.fullmatch(r"[0-9a-f]{64}", context.state_fingerprint)
                or context.context_key
                != opportunity_context_key(
                    context.context_id,
                    context.context_kind,
                    context.turn,
                    context.phase,
                    context.step,
                    context.active_player,
                    context.controller,
                    context.source_id,
                    context.subject_ids,
                    context.subject_zones,
                    context.facts,
                    context.event_id,
                    context.stack_object_id,
                    context.state_fingerprint,
                )
            ):
                raise AssertionError("opportunity context provenance is malformed")
            if context.event_id is not None and context.event_id not in self._rules_events:
                raise AssertionError("opportunity context event provenance is missing")
            if context.stack_object_id is not None and context.stack_object_id not in self._objects:
                raise AssertionError("opportunity context Stack provenance is missing")
        for occurrence in self.semantic_occurrences:
            source = self._objects.get(occurrence.object_id)
            if not isinstance(source, (CardObject, Permanent)):
                raise AssertionError("semantic occurrence references a nonexistent object")
            fragments = self._semantic_fragments(source.card)
            if (
                occurrence.fragment_index >= len(fragments)
                or fragments[occurrence.fragment_index] != occurrence.oracle_fragment
                or fragment_digest(occurrence.oracle_fragment) != occurrence.fragment_hash
                or semantic_key(
                    getattr(source.card, "oracle_id", ""),
                    occurrence.face_index,
                    occurrence.fragment_index,
                    occurrence.oracle_fragment,
                )
                != occurrence.semantic_key
            ):
                raise AssertionError("semantic occurrence mismatches authoritative Oracle data")
        for witness in self.opportunity_witnesses:
            occurrence = occurrence_by_id.get(witness.occurrence_id)
            if occurrence is None or (
                witness.semantic_key != occurrence.semantic_key
                or witness.object_id != occurrence.object_id
                or witness.oracle_fragment != occurrence.oracle_fragment
            ):
                raise AssertionError("opportunity witness mismatches semantic presence")
            try:
                facts = self._validate_opportunity_applicability(
                    occurrence,
                    cause_kind=witness.cause_kind,
                    cause_id=witness.cause_id,
                    cause_subject_ids=witness.cause_subject_ids,
                    historical=witness,
                )
            except ValueError as error:
                raise AssertionError(str(error)) from error
            if facts != (
                witness.source_zone,
                witness.source_controller,
                witness.cause_subject_zones,
                witness.cause_event_kind,
            ):
                raise AssertionError("opportunity witness applicability facts are inconsistent")
            if (
                witness.cause_kind == "authoritative_context"
                and witness.cause_id not in context_by_id
            ):
                raise AssertionError("opportunity witness context provenance is missing")
        if len(set(self._combat_attackers)) != len(self._combat_attackers):
            raise AssertionError("combat state contains duplicate attackers")
        if len({blocker_id for _attacker_id, blocker_id in self._combat_blocks}) != len(
            self._combat_blocks
        ):
            raise AssertionError("combat state contains duplicate blockers")
        if any(object_id not in combat_ids for object_id in self._first_damage_qualified_ids):
            raise AssertionError("first-strike qualification references a noncombatant")
        if any(object_id not in combat_ids for object_id in self._regular_damage_initial_ids):
            raise AssertionError("regular-step qualification references a noncombatant")
        if any(
            len(
                {
                    (assignment.source_id, assignment.target_id, assignment.target_player)
                    for assignment in evidence.assignments
                }
            )
            != len(evidence.assignments)
            for evidence in self.combat_damage_evidence
        ):
            raise AssertionError("combatant repeated one assignment in a damage step")
        if any(
            assignment.amount <= 0
            for evidence in self.combat_damage_evidence
            for assignment in evidence.assignments
        ):
            raise AssertionError("combat evidence contains a nonpositive damage assignment")
        for evidence in self.combat_damage_evidence:
            for result in evidence.trample_results:
                if result.damage_step is not evidence.kind or result.attacker_power <= 0:
                    raise AssertionError("Trample evidence has invalid step or power")
                if (
                    result.blocker_damage_assigned + result.player_damage_assigned
                    != result.attacker_power
                ):
                    raise AssertionError("Trample evidence does not conserve assigned damage")
                if (
                    result.defending_life_before - result.player_damage_assigned
                    != result.defending_life_after
                ):
                    raise AssertionError("Trample evidence life result is inconsistent")
                if result.blocker_toughness is not None and (
                    result.blocker_marked_damage_before is None
                    or result.lethal_required
                    != max(
                        0,
                        result.blocker_toughness - result.blocker_marked_damage_before,
                    )
                ):
                    raise AssertionError("Trample evidence lethal calculation is inconsistent")
                if result.blocker_survived != (result.blocker_marked_damage_after is not None):
                    raise AssertionError("Trample evidence blocker result is inconsistent")
        if len({item.stack_object_id for item in self.etb_drain_gain_scry_evidence}) != len(
            self.etb_drain_gain_scry_evidence
        ):
            raise AssertionError("ETB drain/gain/Scry evidence stack IDs must be unique")
        for item in self.etb_drain_gain_scry_evidence:
            ability = self._objects.get(item.stack_object_id)
            if not isinstance(ability, TriggeredAbilityObject) or ability.zone != "former":
                raise AssertionError("ETB drain/gain/Scry evidence lacks resolved Stack authority")
            try:
                self._validate_etb_drain_gain_scry_trigger(ability)
            except ValueError as error:
                raise AssertionError(str(error)) from error
            if (
                item.event_id != ability.event.event_id
                or item.source_id != ability.source_id
                or item.source_card != ability.source_card.name
                or item.controller != ability.controller
                or item.opponent != 1 - item.controller
                or item.oracle_fragment != ability.oracle_fragment
                or item.turn != ability.event.turn
                or item.step != ability.event.step
                or item.opponent_life_after != item.opponent_life_before - 1
            ):
                raise AssertionError("ETB drain/gain/Scry evidence provenance is inconsistent")
            if item.terminal_after_life_loss:
                if (
                    item.opponent_life_after > 0
                    or item.controller_life_after != item.controller_life_before
                    or item.scry_event_id is not None
                ):
                    raise AssertionError("terminal ETB drain/gain/Scry evidence is inconsistent")
            else:
                matching_scry = [
                    evidence
                    for evidence in self.scry_evidence
                    if evidence.event_id == item.scry_event_id
                ]
                if (
                    item.opponent_life_after <= 0
                    or item.controller_life_after != item.controller_life_before + 1
                    or len(matching_scry) != 1
                    or matching_scry[0].player_index != item.controller
                    or matching_scry[0].requested != 1
                    or matching_scry[0].source_id != item.source_id
                    or matching_scry[0].oracle_fragment != item.oracle_fragment
                ):
                    raise AssertionError("completed ETB drain/gain/Scry evidence is inconsistent")
        if len({item.stack_object_id for item in self.activation_evidence}) != len(
            self.activation_evidence
        ):
            raise AssertionError("activation evidence stack IDs must be unique")
        for item in self.activation_evidence:
            if item.controller not in range(2) or item.source_id not in self._objects:
                raise AssertionError("activation evidence references invalid authority")
            ability = self._objects.get(item.stack_object_id)
            if not isinstance(ability, ActivatedAbilityObject):
                raise AssertionError("activation evidence lacks its runtime stack object")
            if item.resolved != (ability.zone == "former"):
                raise AssertionError("activation resolution evidence disagrees with stack state")
        if len({item.stack_object_id for item in self.food_activation_evidence}) != len(
            self.food_activation_evidence
        ):
            raise AssertionError("Food activation evidence stack IDs must be unique")
        for item in self.food_activation_evidence:
            ability = self._objects.get(item.stack_object_id)
            sacrificed = self._objects.get(item.sacrificed_destination_id)
            if not isinstance(ability, ActivatedAbilityObject):
                raise AssertionError("Food activation evidence lacks its stack object")
            self._validate_food_activation_linkage(ability)
            if item.source_id not in self._objects or not isinstance(sacrificed, CardObject):
                raise AssertionError("Food activation evidence lacks immutable cost identities")
            if not item.tap_paid or not item.sacrifice_paid:
                raise AssertionError("Food activation evidence lacks complete canonical costs")
            if item.source_was_token and item.final_source_disposition != "former":
                raise AssertionError("sacrificed Food token must cease at the SBA boundary")
            if item.resolved != (ability.zone == "former"):
                raise AssertionError("Food activation resolution evidence disagrees with stack")
            if item.resolved and (
                item.life_before is None
                or item.life_after is None
                or item.amount_gained != 3
                or item.life_after - item.life_before != 3
                or item.priority_passes != (item.controller, 1 - item.controller)
                or not item.resolution_permitted
            ):
                raise AssertionError("Food activation life evidence is inconsistent")
        if len({item.stack_object_id for item in self.sneak_evidence}) != len(self.sneak_evidence):
            raise AssertionError("Sneak evidence stack IDs must be unique")
        for item in self.sneak_evidence:
            spell = self._objects.get(item.stack_object_id)
            if not isinstance(spell, StackObject):
                raise AssertionError("Sneak evidence lacks its runtime stack object")
            if item.controller not in range(2) or item.defending_player != 1 - item.controller:
                raise AssertionError("Sneak evidence has invalid player authority")
            if (
                item.hand_object_id not in self._objects
                or item.returned_attacker_id not in self._objects
            ):
                raise AssertionError("Sneak evidence lacks immutable source identities")
            if item.returned_hand_id not in self._objects:
                raise AssertionError("Sneak evidence lacks returned-object identity")
            resolved = item.resolved_object_id is not None
            if resolved != (spell.zone == "former"):
                raise AssertionError("Sneak evidence resolution disagrees with stack state")
            if resolved and (
                item.resolved_object_id not in self._objects
                or item.entered_tapped is not True
                or item.entered_attacking is not True
            ):
                raise AssertionError("resolved Sneak evidence lacks battlefield result")
        if self.priority_state is not None:
            state = self.priority_state
            if not self.stack:
                raise AssertionError("priority state requires a nonempty stack")
            if state.player_index not in range(2):
                raise AssertionError("priority player is invalid")
            if len(state.consecutive_passes) > 2:
                raise AssertionError("priority pass sequence is too long")
            if state.consecutive_passes not in {(), (0,), (1,), (0, 1), (1, 0)}:
                raise AssertionError("priority passes must alternate between players")
            if state.resolution_pending != (len(state.consecutive_passes) == 2):
                raise AssertionError("priority resolution permission disagrees with passes")
                raise AssertionError("activation evidence resolution state is inconsistent")
        if self.step is TurnStep.COMBAT_DAMAGE and self._combat_damage_step_kind not in {
            CombatDamageStepKind.FIRST_STRIKE,
            CombatDamageStepKind.REGULAR,
        }:
            raise AssertionError("combat damage turn step lacks an active damage-step kind")
        if self.step in {
            TurnStep.POSTCOMBAT_MAIN,
            TurnStep.END_STEP,
            TurnStep.CLEANUP,
            TurnStep.UNTAP,
            TurnStep.UPKEEP,
            TurnStep.DRAW,
            TurnStep.PRECOMBAT_MAIN,
        } and (
            combat_ids
            or self._attackers_declared
            or self._blockers_declared
            or self._combat_damage_resolved
            or self._combat_damage_step_kind is not CombatDamageStepKind.NONE
            or self._combat_damage_step_number
            or self._combat_damage_total_steps
            or self._first_damage_qualified_ids
            or self._first_double_strike_ids
            or self._regular_damage_initial_ids
        ):
            raise AssertionError("completed combat state leaked outside the combat phase")
        if [record.sequence for record in self.rng.records] != list(
            range(1, len(self.rng.records) + 1)
        ):
            raise AssertionError("RNG consumption sequence is not contiguous")
        if any(
            previous.state_after != current.state_before
            for previous, current in zip(self.rng.records, self.rng.records[1:], strict=False)
        ):
            raise AssertionError("RNG state evidence does not form one chain")
        if self.rng.records and self.rng.records[-1].state_after != self.rng.state_digest:
            raise AssertionError("RNG current state does not match its consumption ledger")
        occupied: dict[
            str,
            tuple[
                int | None,
                str,
                CardObject
                | StackObject
                | TriggeredAbilityObject
                | ActivatedAbilityObject
                | Permanent,
            ],
        ] = {}
        for obj in self.stack:
            if not isinstance(obj, (StackObject, TriggeredAbilityObject, ActivatedAbilityObject)):
                raise AssertionError("stack may contain only spell or ability objects")
            if obj.object_id in occupied:
                raise AssertionError("runtime object occupies more than one zone")
            if self._objects.get(obj.object_id) is not obj:
                raise AssertionError("stack contains an unregistered or aliased object")
            if obj.zone != "stack":
                raise AssertionError("stack object zone does not match its container")
            if obj.controller not in range(2):
                raise AssertionError("stack object controller is invalid")
            if isinstance(obj, StackObject):
                if obj.cast_kind is CastKind.UNSUPPORTED:
                    raise AssertionError("unsupported spells cannot become stack objects")
                if obj.target_id is not None and obj.target_id not in self._objects:
                    raise AssertionError("stack target ID was never registered")
            elif isinstance(obj, TriggeredAbilityObject):
                if obj.event.player_index not in range(2):
                    raise AssertionError("trigger event player is invalid")
                if obj.effect is TriggerEffect.DIES_DRAW:
                    try:
                        self._validate_dies_draw_trigger(obj)
                    except ValueError as error:
                        raise AssertionError(str(error)) from error
                if obj.effect is TriggerEffect.ETB_DRAIN_GAIN_SCRY:
                    try:
                        self._validate_etb_drain_gain_scry_trigger(obj)
                    except ValueError as error:
                        raise AssertionError(str(error)) from error
                if obj.effect is TriggerEffect.PERMANENT_LEFT_SELF_COUNTER:
                    try:
                        self._validate_permanent_left_counter_provenance(
                            controller=obj.controller,
                            source_id=obj.source_id,
                            source_card=obj.source_card,
                            oracle_fragment=obj.oracle_fragment,
                            event=obj.event,
                            trigger_id=obj.trigger_id,
                        )
                    except ValueError as error:
                        raise AssertionError(str(error)) from error
                if obj.effect is TriggerEffect.ETB_ARTIFACT_DRAW:
                    try:
                        self._validate_etb_artifact_draw_provenance(
                            controller=obj.controller,
                            source_id=obj.source_id,
                            source_card=obj.source_card,
                            oracle_fragment=obj.oracle_fragment,
                            event=obj.event,
                            trigger_id=obj.trigger_id,
                            require_current_condition=False,
                        )
                    except ValueError as error:
                        raise AssertionError(str(error)) from error
            elif isinstance(obj, ActivatedAbilityObject):
                if obj.source_id not in self._objects:
                    raise AssertionError("activated ability source ID was never registered")
                if any(target_id not in self._objects for target_id in obj.target_ids):
                    raise AssertionError("activated ability target ID was never registered")
            occupied[obj.object_id] = (None, "stack", obj)
        if len({trigger.trigger_id for trigger in self.pending_triggers}) != len(
            self.pending_triggers
        ):
            raise AssertionError("pending trigger IDs must be unique")
        for trigger in self.pending_triggers:
            if trigger.effect is TriggerEffect.PERMANENT_LEFT_SELF_COUNTER:
                try:
                    self._validate_permanent_left_counter_provenance(
                        controller=trigger.controller,
                        source_id=trigger.source_id,
                        source_card=trigger.source_card,
                        oracle_fragment=trigger.oracle_fragment,
                        event=trigger.event,
                        trigger_id=trigger.trigger_id,
                    )
                except ValueError as error:
                    raise AssertionError(str(error)) from error
            if trigger.effect is TriggerEffect.ETB_ARTIFACT_DRAW:
                try:
                    self._validate_etb_artifact_draw_provenance(
                        controller=trigger.controller,
                        source_id=trigger.source_id,
                        source_card=trigger.source_card,
                        oracle_fragment=trigger.oracle_fragment,
                        event=trigger.event,
                        trigger_id=trigger.trigger_id,
                        require_current_condition=False,
                    )
                except ValueError as error:
                    raise AssertionError(str(error)) from error
        for player_index, player in enumerate(self.players):
            for zone_name in ("library", "hand", "battlefield", "graveyard"):
                for obj in getattr(player, zone_name):
                    if not isinstance(obj, (CardObject, Permanent)):
                        raise AssertionError("zones may contain only registered runtime objects")
                    if obj.object_id in occupied:
                        raise AssertionError("runtime object occupies more than one zone")
                    if self._objects.get(obj.object_id) is not obj:
                        raise AssertionError("zone contains an unregistered or aliased object")
                    if obj.zone != zone_name:
                        raise AssertionError("runtime object zone does not match its container")
                    expected_holder = obj.controller if zone_name == "battlefield" else obj.owner
                    if expected_holder != player_index:
                        raise AssertionError("runtime object occupies the wrong player's zone")
                    if zone_name != "battlefield" and obj.controller != obj.owner:
                        raise AssertionError("nonbattlefield object controller must reset to owner")
                    if isinstance(obj, CardObject) and obj.is_token:
                        raise AssertionError(
                            "a nonbattlefield token must cease at the SBA boundary"
                        )
                    occupied[obj.object_id] = (player_index, zone_name, obj)
        for object_id, obj in self._objects.items():
            if obj.zone == "former":
                if object_id in occupied:
                    raise AssertionError("former object still occupies a zone")
            elif object_id not in occupied:
                raise AssertionError("authoritative runtime object occupies no zone")

        for player_index, player in enumerate(self.players):
            legendary_names: set[str] = set()
            for permanent in player.battlefield:
                if permanent.controller != player_index:
                    raise AssertionError("battlefield controller does not match player zone")
                if permanent.entered_battlefield_turn > self.turn:
                    raise AssertionError("permanent entered the battlefield in a future turn")
                if permanent.is_token != isinstance(permanent.card, TokenDefinition):
                    raise AssertionError("token runtime state does not match its token definition")
                if not permanent.type_line:
                    raise AssertionError("permanent type line must remain nonempty")
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
                if any(
                    effect.duration != "until_end_of_turn"
                    or not isinstance(effect.keyword, StrikeKeyword)
                    for effect in permanent.temporary_keyword_effects
                ):
                    raise AssertionError("temporary keyword effect is malformed")
                effect_ids = {effect.effect_id for effect in permanent.characteristic_effects}
                if len(effect_ids) != len(permanent.characteristic_effects):
                    raise AssertionError("characteristic effect IDs must be unique")
                if any(
                    dependency not in effect_ids
                    for effect in permanent.characteristic_effects
                    for dependency in effect.depends_on
                ):
                    raise AssertionError("characteristic effect dependency is missing")
                if permanent.card.is_creature:
                    try:
                        permanent.evaluate_power_toughness()
                    except ValueError as error:
                        raise AssertionError(str(error)) from error
                if "Legendary" in permanent.card.type_line:
                    if permanent.card.name in legendary_names:
                        raise AssertionError("legend rule left duplicate names on battlefield")
                    legendary_names.add(permanent.card.name)

    def check_life(self) -> None:
        for index, player in enumerate(self.players):
            if player.life <= 0 and not player.lost:
                player.lost = True
                player.loss_reason = "life_zero_or_less"
                self.winner = 1 - index
                self.log("player_lost", player=player.name, reason=player.loss_reason)

    def record_conformance_stop(
        self, kind: str, before_fingerprint: str, *, detail: str
    ) -> ConformanceStopRecord:
        """Record an illegal-mutation or unclassified-reach stop deterministically."""
        if kind not in {"illegal_mutation", "unclassified_reach", "silent_approximation"}:
            raise ValueError("conformance stop kind is unsupported")
        after = self.authoritative_state_fingerprint()
        if kind == "illegal_mutation" and before_fingerprint == after:
            raise ValueError("illegal-mutation stop requires an observed state change")
        record = ConformanceStopRecord(
            f"stop-{len(self.conformance_stop_records) + 1:06d}",
            kind,
            self.turn,
            self.phase,
            self.step.value,
            before_fingerprint,
            after,
            detail,
        )
        self.conformance_stop_records.append(record)
        return record

    def authoritative_state_fingerprint(self) -> str:
        """Stable mutation-boundary digest excluding diagnostics and evidence ledgers."""
        return sha256(
            repr(self._authoritative_state_fingerprint_preimage()).encode("utf-8")
        ).hexdigest()

    def _authoritative_state_fingerprint_preimage(self) -> tuple[object, ...]:
        """Return the complete canonical preimage used by the existing state fingerprint."""
        zones = tuple(
            (
                tuple(card.object_id for card in player.library),
                tuple(card.object_id for card in player.hand),
                tuple(permanent.object_id for permanent in player.battlefield),
                tuple(card.object_id for card in player.graveyard),
                player.life,
                player.lost,
                player.failed_draw_pending,
            )
            for player in self.players
        )
        return (
            self.turn,
            self.active_player,
            self.step.value,
            tuple(item.object_id for item in self.stack),
            self._combat_attackers,
            self._combat_blocks,
            zones,
            self.rng.state_digest,
            self.winner,
        )

    def authoritative_state_fingerprint_evidence(self) -> dict[str, object]:
        """Serialize the existing fingerprint preimage without defining a second state model."""
        authority = self._authoritative_state_fingerprint_preimage()
        zones = authority[6]
        return {
            "scheme": "engine07-authoritative-state-fingerprint-preimage-v1",
            "turn": authority[0],
            "active_player_index": authority[1],
            "step": authority[2],
            "stack_object_ids": list(authority[3]),
            "combat_attacker_ids": list(authority[4]),
            "combat_blocks": [list(item) for item in authority[5]],
            "players": [
                {
                    "library_object_ids": list(player[0]),
                    "hand_object_ids": list(player[1]),
                    "battlefield_object_ids": list(player[2]),
                    "graveyard_object_ids": list(player[3]),
                    "life": player[4],
                    "lost": player[5],
                    "failed_draw_pending": player[6],
                }
                for player in zones
            ],
            "rng_state_digest": authority[7],
            "winner_index": authority[8],
        }

    def _executed_conformance_references(self) -> list[dict[str, object]]:
        """Index mature Action evidence without replacing or weakening that evidence."""
        references: list[dict[str, object]] = []

        def add(kind: str, evidence_id: str, source_id: str, fragment: str) -> None:
            source = self._objects.get(source_id)
            if not isinstance(source, (CardObject, StackObject, Permanent)):
                return
            fragments = self._semantic_fragments(source.card)
            if fragment not in fragments:
                return
            index = fragments.index(fragment)
            references.append(
                {
                    "evidence_kind": kind,
                    "evidence_id": evidence_id,
                    "source_id": source_id,
                    "semantic_key": semantic_key(
                        getattr(source.card, "oracle_id", ""), 0, index, fragment
                    ),
                    "oracle_fragment": fragment,
                }
            )

        for item in self.activation_evidence:
            if item.resolved:
                add("activated_ability", item.stack_object_id, item.source_id, item.oracle_fragment)
        for item in self.food_activation_evidence:
            if item.resolved:
                add("food_activation", item.stack_object_id, item.source_id, item.oracle_fragment)
        for item in self.sneak_evidence:
            if item.resolved_object_id is not None:
                add("sneak", item.stack_object_id, item.hand_object_id, item.oracle_fragment)
        for item in self.hand_bottom_draw_evidence:
            add("hand_bottom_draw", item.event_id, item.source_id, item.oracle_fragment)
        for item in self.discard_draw_evidence:
            add("discard_draw", item.event_id, item.source_id, item.oracle_fragment)
        for item in self.lifelink_evidence:
            add("lifelink", item.event_id, item.source_id, "Lifelink")
        for item in self.etb_drain_gain_scry_evidence:
            add(
                "etb_drain_gain_scry",
                item.stack_object_id,
                item.source_id,
                item.oracle_fragment,
            )
        for evidence in self.combat_damage_evidence:
            for assignment in evidence.assignments:
                source = self._objects.get(assignment.source_id)
                if not isinstance(source, Permanent):
                    continue
                if assignment.trample:
                    add(
                        "trample",
                        f"combat:{evidence.sequence}:{assignment.source_id}:trample",
                        assignment.source_id,
                        "Trample",
                    )
                for keyword in ("First strike", "Double strike"):
                    if keyword in self._semantic_fragments(source.card):
                        add(
                            "strike_damage_step",
                            f"combat:{evidence.sequence}:{assignment.source_id}:{keyword}",
                            assignment.source_id,
                            keyword,
                        )
        for event in self.events:
            if event.get("event") in {
                "damage_dealt",
                "scry_committed",
                "tokens_created",
                "trigger_resolved",
            }:
                source_id = event.get("source_id")
                fragment = event.get("oracle_fragment")
                evidence_id = event.get("event_id") or event.get("stack_object_id")
                if all(isinstance(value, str) for value in (source_id, fragment, evidence_id)):
                    add(
                        str(event["event"]),
                        str(evidence_id),
                        str(source_id),
                        str(fragment),
                    )
        unique = {
            (
                str(item["evidence_kind"]),
                str(item["evidence_id"]),
                str(item["source_id"]),
                str(item["semantic_key"]),
            ): item
            for item in references
        }
        return sorted(
            unique.values(),
            key=lambda item: (str(item["evidence_kind"]), str(item["evidence_id"])),
        )

    def snapshot(self) -> dict[str, object]:
        return {
            "engine_version": ENGINE_VERSION,
            "turn": self.turn,
            "active_player": self.players[self.active_player].name,
            "phase": self.phase,
            "step": self.step.value,
            "winner": None if self.winner is None else self.players[self.winner].name,
            "authoritative_state_fingerprint": self.authoritative_state_fingerprint(),
            "authoritative_state_fingerprint_preimage": (
                self.authoritative_state_fingerprint_evidence()
            ),
            "rules_event_evidence": [
                {
                    "event_id": item.event_id,
                    "event_cursor": item.event_cursor,
                    "kind": item.kind.value,
                    "player_index": item.player_index,
                    "subject_ids": list(item.subject_ids),
                    "source_id": item.source_id,
                    "target_player": item.target_player,
                    "amount": item.amount,
                    "turn": item.turn,
                    "step": item.step,
                    "active_player": item.active_player,
                    "battlefield_authority": [
                        {"object_id": object_id, "controller": controller}
                        for object_id, controller in item.battlefield_authority
                    ],
                    "battlefield_characteristics": [
                        {
                            "object_id": object_id,
                            "controller": controller,
                            "type_line": type_line,
                        }
                        for object_id, controller, type_line in item.battlefield_characteristics
                    ],
                    "last_known_battlefield": [
                        {
                            "object_id": object_id,
                            "controller": controller,
                            "type_line": type_line,
                            "is_creature": is_creature,
                        }
                        for object_id, controller, type_line, is_creature in (
                            item.last_known_battlefield
                        )
                    ],
                }
                for item in self._rules_event_evidence
            ],
            "conformance": {
                "semantic_occurrences": [
                    {
                        "occurrence_id": item.occurrence_id,
                        "semantic_key": item.semantic_key,
                        "oracle_id": item.oracle_id,
                        "face_index": item.face_index,
                        "fragment_index": item.fragment_index,
                        "fragment_hash": item.fragment_hash,
                        "object_id": item.object_id,
                        "controller": item.controller,
                        "zone": item.zone,
                        "oracle_fragment": item.oracle_fragment,
                        "limitations": list(item.limitations),
                        "turn": item.turn,
                        "phase": item.phase,
                        "step": item.step,
                        "registration_event_cursor": item.registration_event_cursor,
                        "classification": (
                            "reached_unsupported"
                            if any(
                                witness.occurrence_id == item.occurrence_id
                                for witness in self.opportunity_witnesses
                            )
                            else "present_unreached"
                        ),
                    }
                    for item in self.semantic_occurrences
                ],
                "opportunity_witnesses": [
                    {
                        "witness_id": item.witness_id,
                        "opportunity_key": item.opportunity_key,
                        "occurrence_id": item.occurrence_id,
                        "semantic_key": item.semantic_key,
                        "object_id": item.object_id,
                        "controller": item.controller,
                        "oracle_fragment": item.oracle_fragment,
                        "turn": item.turn,
                        "phase": item.phase,
                        "step": item.step,
                        "cause_kind": item.cause_kind,
                        "cause_id": item.cause_id,
                        "cause_subject_ids": list(item.cause_subject_ids),
                        "source_zone": item.source_zone,
                        "source_controller": item.source_controller,
                        "cause_subject_zones": list(item.cause_subject_zones),
                        "cause_event_kind": item.cause_event_kind,
                        "classification": item.classification.value,
                    }
                    for item in self.opportunity_witnesses
                ],
                "opportunity_contexts": [
                    {
                        "context_id": item.context_id,
                        "context_key": item.context_key,
                        "context_kind": item.context_kind,
                        "turn": item.turn,
                        "phase": item.phase,
                        "step": item.step,
                        "active_player": item.active_player,
                        "controller": item.controller,
                        "source_id": item.source_id,
                        "subject_ids": list(item.subject_ids),
                        "subject_zones": list(item.subject_zones),
                        "facts": {key: value for key, value in item.facts},
                        "event_id": item.event_id,
                        "stack_object_id": item.stack_object_id,
                        "state_fingerprint": item.state_fingerprint,
                    }
                    for item in self.opportunity_contexts
                ],
                "stop_records": [
                    {
                        "stop_id": item.stop_id,
                        "kind": item.kind,
                        "turn": item.turn,
                        "phase": item.phase,
                        "step": item.step,
                        "before_fingerprint": item.before_fingerprint,
                        "after_fingerprint": item.after_fingerprint,
                        "detail": item.detail,
                    }
                    for item in self.conformance_stop_records
                ],
                "executed_references": self._executed_conformance_references(),
            },
            "rng": {
                "seed": self.rng.seed,
                "state_digest": self.rng.state_digest,
                "records": [
                    {
                        "sequence": record.sequence,
                        "domain": record.domain,
                        "operation": record.operation,
                        "result": (
                            list(record.result)
                            if isinstance(record.result, tuple)
                            else record.result
                        ),
                        "state_before": record.state_before,
                        "state_after": record.state_after,
                    }
                    for record in self.rng.records
                ],
            },
            "stack": [
                (
                    {
                        "object_id": entry.object_id,
                        "kind": "spell",
                        "card": entry.card.name,
                        "owner": entry.owner,
                        "controller": entry.controller,
                        "cast_kind": entry.cast_kind.value,
                        "target_id": entry.target_id,
                        "sneak_returned_attacker_id": entry.sneak_returned_attacker_id,
                        "sneak_returned_hand_id": entry.sneak_returned_hand_id,
                        "sneak_defending_player": entry.sneak_defending_player,
                        "sneak_oracle_fragment": entry.sneak_oracle_fragment,
                        "sneak_mana_source_ids": list(entry.sneak_mana_source_ids),
                    }
                    if isinstance(entry, StackObject)
                    else {
                        "object_id": entry.object_id,
                        "kind": "activated_ability",
                        "source": entry.source_card.name,
                        "source_id": entry.source_id,
                        "controller": entry.controller,
                        "oracle_fragment": entry.oracle_fragment,
                        "target_ids": list(entry.target_ids),
                        "choice_ids": list(entry.choice_ids),
                    }
                    if isinstance(entry, ActivatedAbilityObject)
                    else {
                        "object_id": entry.object_id,
                        "kind": "triggered_ability",
                        "source": entry.source_card.name,
                        "source_id": entry.source_id,
                        "controller": entry.controller,
                        "effect": entry.effect.value,
                        "event_id": entry.event.event_id,
                        "trigger_id": entry.trigger_id,
                    }
                )
                for entry in self.stack
            ],
            "priority": (
                None
                if self.priority_state is None
                else {
                    "epoch": self.priority_state.epoch,
                    "player_index": self.priority_state.player_index,
                    "consecutive_passes": list(self.priority_state.consecutive_passes),
                    "resolution_pending": self.priority_state.resolution_pending,
                }
            ),
            "pending_triggers": [trigger.trigger_id for trigger in self.pending_triggers],
            "scry": [
                {
                    "event_id": item.event_id,
                    "player_index": item.player_index,
                    "requested": item.requested,
                    "inspected_ids": list(item.inspected_ids),
                    "top_ids": list(item.top_ids),
                    "bottom_ids": list(item.bottom_ids),
                    "source_card": item.source_card,
                    "source_id": item.source_id,
                    "oracle_fragment": item.oracle_fragment,
                }
                for item in self.scry_evidence
            ],
            "etb_drain_gain_scry": [
                {
                    "event_id": item.event_id,
                    "stack_object_id": item.stack_object_id,
                    "source_id": item.source_id,
                    "source_card": item.source_card,
                    "controller": item.controller,
                    "opponent": item.opponent,
                    "oracle_fragment": item.oracle_fragment,
                    "turn": item.turn,
                    "step": item.step,
                    "opponent_life_before": item.opponent_life_before,
                    "opponent_life_after": item.opponent_life_after,
                    "controller_life_before": item.controller_life_before,
                    "controller_life_after": item.controller_life_after,
                    "scry_event_id": item.scry_event_id,
                    "terminal_after_life_loss": item.terminal_after_life_loss,
                }
                for item in self.etb_drain_gain_scry_evidence
            ],
            "combat_damage": {
                "step_kind": self._combat_damage_step_kind.value,
                "sequence": self._combat_damage_step_number,
                "total_steps": self._combat_damage_total_steps,
                "first_qualified_ids": list(self._first_damage_qualified_ids),
                "regular_initial_ids": list(self._regular_damage_initial_ids),
                "evidence": [
                    {
                        "kind": item.kind.value,
                        "sequence": item.sequence,
                        "total_steps": item.total_steps,
                        "assignments": [
                            {
                                "source_id": assignment.source_id,
                                "target_id": assignment.target_id,
                                "target_player": assignment.target_player,
                                "amount": assignment.amount,
                                "role": assignment.role,
                                "trample": assignment.trample,
                                "lethal_required": assignment.lethal_required,
                            }
                            for assignment in item.assignments
                        ],
                        "removed_before_next_step": list(item.removed_before_next_step),
                        "trample_results": [
                            {
                                "attacker_id": result.attacker_id,
                                "blocker_id": result.blocker_id,
                                "damage_step": result.damage_step.value,
                                "attacker_power": result.attacker_power,
                                "blocker_toughness": result.blocker_toughness,
                                "blocker_marked_damage_before": (
                                    result.blocker_marked_damage_before
                                ),
                                "lethal_required": result.lethal_required,
                                "blocker_damage_assigned": result.blocker_damage_assigned,
                                "player_damage_assigned": result.player_damage_assigned,
                                "defending_player": result.defending_player,
                                "defending_life_before": result.defending_life_before,
                                "defending_life_after": result.defending_life_after,
                                "blocker_marked_damage_after": (result.blocker_marked_damage_after),
                                "blocker_survived": result.blocker_survived,
                            }
                            for result in item.trample_results
                        ],
                    }
                    for item in self.combat_damage_evidence
                ],
            },
            "lifelink": [
                {
                    "event_id": item.event_id,
                    "source_id": item.source_id,
                    "controller": item.controller,
                    "amount": item.amount,
                    "combat": item.combat,
                    "damage_step": (None if item.damage_step is None else item.damage_step.value),
                    "target_ids": list(item.target_ids),
                    "target_players": list(item.target_players),
                    "life_before": item.life_before,
                    "life_after": item.life_after,
                }
                for item in self.lifelink_evidence
            ],
            "hand_bottom_draw": [
                {
                    "event_id": item.event_id,
                    "player_index": item.player_index,
                    "source_id": item.source_id,
                    "oracle_fragment": item.oracle_fragment,
                    "offered_choice_ids": list(item.offered_choice_ids),
                    "pre_hand_ids": list(item.pre_hand_ids),
                    "pre_library_ids": list(item.pre_library_ids),
                    "selected_hand_id": item.selected_hand_id,
                    "library_bottom_id": item.library_bottom_id,
                    "movement_succeeded": item.movement_succeeded,
                    "conditional_draw_performed": item.conditional_draw_performed,
                    "drawn_library_id": item.drawn_library_id,
                    "drawn_hand_id": item.drawn_hand_id,
                    "post_hand_ids": list(item.post_hand_ids),
                    "post_library_ids": list(item.post_library_ids),
                    "declined": item.declined,
                }
                for item in self.hand_bottom_draw_evidence
            ],
            "discard_draw": [
                {
                    "event_id": item.event_id,
                    "player_index": item.player_index,
                    "attack_provenance": {
                        "event_id": item.attack_provenance.event_id,
                        "event_kind": item.attack_provenance.event_kind.value,
                        "event_player_index": item.attack_provenance.event_player_index,
                        "subject_ids": list(item.attack_provenance.subject_ids),
                        "attacker_id": item.attack_provenance.attacker_id,
                        "controller": item.attack_provenance.controller,
                        "turn": item.attack_provenance.turn,
                        "step": item.attack_provenance.step,
                        "active_player": item.attack_provenance.active_player,
                    },
                    "stack_object_id": item.stack_object_id,
                    "source_id": item.source_id,
                    "oracle_fragment": item.oracle_fragment,
                    "offered_choice_ids": list(item.offered_choice_ids),
                    "pre_hand_ids": list(item.pre_hand_ids),
                    "pre_library_ids": list(item.pre_library_ids),
                    "pre_graveyard_ids": list(item.pre_graveyard_ids),
                    "selected_hand_id": item.selected_hand_id,
                    "discarded_graveyard_id": item.discarded_graveyard_id,
                    "movement_succeeded": item.movement_succeeded,
                    "conditional_draw_performed": item.conditional_draw_performed,
                    "pre_draw_top_id": item.pre_draw_top_id,
                    "drawn_hand_id": item.drawn_hand_id,
                    "post_hand_ids": list(item.post_hand_ids),
                    "post_library_ids": list(item.post_library_ids),
                    "post_graveyard_ids": list(item.post_graveyard_ids),
                    "declined": item.declined,
                }
                for item in self.discard_draw_evidence
            ],
            "activated_abilities": [
                {
                    "stack_object_id": item.stack_object_id,
                    "source_id": item.source_id,
                    "controller": item.controller,
                    "oracle_fragment": item.oracle_fragment,
                    "mana_source_ids": list(item.mana_source_ids),
                    "tap_source": item.tap_source,
                    "resolved": item.resolved,
                }
                for item in self.activation_evidence
            ],
            "food_activations": [
                {
                    "source_id": item.source_id,
                    "source_name": item.source_name,
                    "source_type_line": item.source_type_line,
                    "source_owner": item.source_owner,
                    "controller": item.controller,
                    "source_was_token": item.source_was_token,
                    "oracle_fragment": item.oracle_fragment,
                    "turn": item.turn,
                    "step": item.step,
                    "source_zone_before": item.source_zone_before,
                    "mana_requirement": {
                        "generic": item.mana_requirement.generic,
                        "colored": list(item.mana_requirement.colored),
                    },
                    "mana_source_ids": list(item.mana_source_ids),
                    "source_tapped_before": item.source_tapped_before,
                    "tap_paid": item.tap_paid,
                    "sacrifice_paid": item.sacrifice_paid,
                    "sacrificed_destination_id": item.sacrificed_destination_id,
                    "sacrificed_destination_zone": item.sacrificed_destination_zone,
                    "stack_object_id": item.stack_object_id,
                    "priority_epoch": item.priority_epoch,
                    "priority_passes": list(item.priority_passes),
                    "resolution_permitted": item.resolution_permitted,
                    "resolved": item.resolved,
                    "life_before": item.life_before,
                    "life_after": item.life_after,
                    "amount_gained": item.amount_gained,
                    "final_source_disposition": item.final_source_disposition,
                }
                for item in self.food_activation_evidence
            ],
            "sneak": [
                {
                    "card": item.card_name,
                    "hand_object_id": item.hand_object_id,
                    "controller": item.controller,
                    "turn": item.turn,
                    "step": item.step,
                    "oracle_fragment": item.oracle_fragment,
                    "mana_requirement": {
                        "generic": item.mana_requirement.generic,
                        "colored": list(item.mana_requirement.colored),
                    },
                    "mana_source_ids": list(item.mana_source_ids),
                    "returned_attacker_id": item.returned_attacker_id,
                    "returned_hand_id": item.returned_hand_id,
                    "defending_player": item.defending_player,
                    "stack_object_id": item.stack_object_id,
                    "priority_epoch": item.priority_epoch,
                    "resolved_object_id": item.resolved_object_id,
                    "entered_tapped": item.entered_tapped,
                    "entered_attacking": item.entered_attacking,
                }
                for item in self.sneak_evidence
            ],
            "players": [
                {
                    "name": p.name,
                    "life": p.life,
                    "library": len(p.library),
                    "library_object_ids": [card.object_id for card in p.library],
                    "hand": [c.name for c in p.hand],
                    "hand_object_ids": [card.object_id for card in p.hand],
                    "battlefield": [
                        {
                            "object_id": x.object_id,
                            "card": {
                                "name": x.card.name,
                                "mana_cost": x.card.mana_cost,
                                "mana_value": x.card.mana_value,
                                "type_line": x.card.type_line,
                                "oracle_text": x.card.oracle_text,
                                "power": x.card.power,
                                "toughness": x.card.toughness,
                                "keywords": list(x.card.keywords),
                            },
                            "owner": x.owner,
                            "controller": x.controller,
                            "zone": x.zone,
                            "is_token": x.is_token,
                            "evaluated_type_line": x.type_line,
                            "colors": (
                                list(x.card.colors) if isinstance(x.card, TokenDefinition) else []
                            ),
                            "tapped": x.tapped,
                            "summoning_sick": x.summoning_sick,
                            "entered_battlefield_turn": x.entered_battlefield_turn,
                            "damage": x.damage,
                            "counters": dict(x.counters),
                            "pt_modifiers": [
                                {
                                    "power": modifier.power,
                                    "toughness": modifier.toughness,
                                    "duration": modifier.duration,
                                    "source_card": modifier.source_card,
                                    "oracle_fragment": modifier.oracle_fragment,
                                    "created_turn": modifier.created_turn,
                                    "created_order": modifier.created_order,
                                    "derived_static": modifier.derived_static,
                                }
                                for modifier in x.pt_modifiers
                            ],
                            "characteristic_effects": [
                                {
                                    "effect_id": effect.effect_id,
                                    "layer": effect.layer.value,
                                    "sublayer": (
                                        None if effect.sublayer is None else effect.sublayer.value
                                    ),
                                    "operation": effect.operation.value,
                                    "power": effect.power,
                                    "toughness": effect.toughness,
                                    "timestamp": list(effect.timestamp),
                                    "depends_on": list(effect.depends_on),
                                    "source_card": effect.source_card,
                                }
                                for effect in x.characteristic_effects
                            ],
                            "temporary_keyword_effects": [
                                {
                                    "keyword": effect.keyword.value,
                                    "duration": effect.duration,
                                    "source_id": effect.source_id,
                                    "oracle_fragment": effect.oracle_fragment,
                                }
                                for effect in x.temporary_keyword_effects
                            ],
                        }
                        for x in p.battlefield
                    ],
                    "graveyard": [c.name for c in p.graveyard],
                    "graveyard_object_ids": [card.object_id for card in p.graveyard],
                    "lost": p.lost,
                    "loss_reason": p.loss_reason,
                    "failed_draw_pending": p.failed_draw_pending,
                }
                for p in self.players
            ],
            "limitations": sorted(self.limitations),
            "events": self.events,
        }


def _integer_characteristic(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def load_facts(catalog: CardDataCatalog, names: set[str]) -> dict[str, CardFact]:
    facts = {}
    for name in sorted(names):
        row = catalog.resolve_name(name)
        mana_value = int(row.mana_value)
        if mana_value != row.mana_value:
            raise ValueError(f"Engine 0.7 cannot represent nonintegral mana value for {name}")
        facts[name] = CardFact(
            name=row.name,
            mana_cost=row.mana_cost,
            mana_value=mana_value,
            type_line=row.type_line,
            oracle_text=row.oracle_text,
            power=_integer_characteristic(row.power),
            toughness=_integer_characteristic(row.toughness),
            keywords=row.keywords,
            oracle_id=row.oracle_id,
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
