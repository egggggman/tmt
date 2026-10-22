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

from tmnt_design_studio.aura07 import AuraMixin
from tmnt_design_studio.card_data import CardDataCatalog
from tmnt_design_studio.card_interpreter07 import (
    ActivatedAbilityProgram,
    ActivatedEffectKind,
    CardInterpreter,
    CastKind,
    CompoundRemovalTokenProgram,
    ConditionalRemovalTokenProgram,
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
from tmnt_design_studio.food_search07 import FoodSearchMixin
from tmnt_design_studio.jury_rig07 import JuryRigMixin
from tmnt_design_studio.krang_refill07 import KrangRefillMixin
from tmnt_design_studio.mana_ledger07 import FloatingManaLedger
from tmnt_design_studio.mill_three07 import MillThreeMixin
from tmnt_design_studio.pilot_input_v2 import (
    DiscardDrawViewV2,
    GameViewV2,
    HandBottomDrawViewV2,
    PriorityViewV2,
    ScryViewV2,
    decision_context,
    describe_card,
    pilot_view,
    priority_view,
)
from tmnt_design_studio.top_library_selection07 import TopLibrarySelectionMixin
from tmnt_design_studio.vigilante07 import VigilanteMixin

ENGINE_VERSION = "cardcade-0.9.0-alpha.1"

Zone = Literal["library", "hand", "stack", "battlefield", "graveyard", "exile", "former"]


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
    floating_colors: tuple[str, ...] = ()
    x_value: int | None = None


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
    counter_target_id: str | None = None


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
    cost_target_id: str | None = None


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
    PERMANENT_ENTERED = "permanent_entered"
    CREATURE_DIED = "creature_died"
    TOKENS_CREATED = "tokens_created"
    LIFE_GAINED = "life_gained"
    ATTACKERS_DECLARED = "attackers_declared"
    BLOCKERS_DECLARED = "blockers_declared"
    DAMAGE_DEALT = "damage_dealt"
    SCRIED = "scried"
    HAND_BOTTOM_DRAW = "hand_bottom_draw"
    DISCARD_DRAW = "discard_draw"
    VIGILANTE_UPKEEP = "vigilante_upkeep"
    PERMANENT_LEFT = "permanent_left"
    CLASS_LEVEL_ADVANCED = "class_level_advanced"


class TriggerEffect(Enum):
    ALLIANCE_PT = "alliance_pt"
    ALLIANCE_COUNTER = "alliance_counter"
    ALLIANCE_MODAL = "alliance_modal"
    LIFE_GAIN_COUNTER = "life_gain_counter"
    ATTACK_PT = "attack_pt"
    ATTACK_TARGET_PT = "attack_target_pt"
    ETB_CONDITIONAL_TOKEN = "etb_conditional_token"
    SNEAK_ETB_CONDITION = "sneak_etb_condition"
    CREATE_TOKEN = "create_token"
    DEAL_DAMAGE = "deal_damage"
    SCRY = "scry"
    DISCARD_DRAW = "discard_draw"
    ETB_KRANG_REFILL = "etb_krang_refill"
    ETB_MILL_THREE = "etb_mill_three"
    ETB_JURY_RIG = "etb_jury_rig"
    TOP_LIBRARY_SELECTION = "top_library_selection"
    ETB_VIGILANTE = "etb_vigilante"
    VIGILANTE_DISCARD = "vigilante_discard"
    ETB_FOOD_SEARCH = "etb_food_search"
    ETB_DRAW_DISCARD = "etb_draw_discard"
    ETB_MILL_DRAW_DISCARD = "etb_mill_draw_discard"
    CLASS_LEVEL_TWO_RECOVERY = "class_level_two_recovery"
    LTB_MUTAGEN = "ltb_mutagen"
    DIES_DRAW = "dies_draw"
    ETB_DRAIN_GAIN_SCRY = "etb_drain_gain_scry"
    ETB_SELF_LIFE_GAIN = "etb_self_life_gain"
    PERMANENT_LEFT_SELF_COUNTER = "permanent_left_self_counter"
    ETB_ARTIFACT_DRAW = "etb_artifact_draw"
    ETB_TAP_STUN = "etb_tap_stun"
    ALLIANCE_TEMPORARY_KEYWORD_CHOICE = "alliance_temporary_keyword_choice"
    ROCK_SOLDIERS_ETB_DESTROY = "rock_soldiers_etb_destroy"
    ARTIFACT_ENTRY_SELF_COUNTER = "artifact_entry_self_counter"
    SHREDDER_DEATHTOUCH = "shredder_deathtouch"
    PARAMECIA_EXILE_CHOICE = "paramecia_exile_choice"
    PARAMECIA_REFLEXIVE_RETURN = "paramecia_reflexive_return"
    RAPHAEL_ALLIANCE_EXILE = "raphael_alliance_exile"
    RAPHAEL_ATTACK_PLAY = "raphael_attack_play"
    COMBAT_SACRIFICE_OR_DISCARD = "combat_sacrifice_or_discard"


class TemporaryKeyword(Enum):
    FLYING = "flying"
    MENACE = "menace"
    HASTE = "haste"
    DEATHTOUCH = "deathtouch"
    REACH = "reach"
    INDESTRUCTIBLE = "indestructible"


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
    keyword: StrikeKeyword | TemporaryKeyword
    duration: Literal["until_end_of_turn"]
    source_id: str
    oracle_fragment: str
    timestamp: tuple[int, int] = (0, 0)


@dataclass(frozen=True)
class TriggerInstance:
    trigger_id: str
    controller: int
    source_id: str
    source_card: CardFact
    oracle_fragment: str
    effect: TriggerEffect
    event: RulesEvent
    x_value: int | None = None


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
    source_object_id: str | None = None


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
    def rules_card(self):
        return self.card

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
    kicker_sacrifice_id: str | None = None
    sneak_returned_attacker_id: str | None = None
    sneak_returned_hand_id: str | None = None
    sneak_defending_player: int | None = None
    sneak_oracle_fragment: str | None = None
    cast_from_graveyard: bool = False
    finality_on_entry: bool = False
    cast_from_raphael: bool = False
    x_value: int | None = None
    sneak_mana_source_ids: tuple[str, ...] = ()
    zone: Zone = "stack"

    @property
    def rules_card(self):
        return self.card

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
    target_id: str | None = None
    target_ids: tuple[str, ...] = ()
    x_value: int | None = None

    @property
    def owner(self) -> int:
        return self.controller


@dataclass(frozen=True)
class StunTargetSelection:
    """Frozen trigger, source, and target incarnation anchors at stack placement."""

    ability: TriggeredAbilityObject
    trigger: TriggerInstance
    source: Permanent
    target: Permanent | None
    target_id: str | None
    offered_ids: tuple[str, ...]
    target_card: CardFact | TokenDefinition | None
    event_cursor: int


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
    discarded_destination_id: str | None = None
    target_ids: tuple[str, ...] = ()
    choice_ids: tuple[str, ...] = ()
    cost_target_id: str | None = None
    cost_target_card: CardFact | TokenDefinition | None = None
    cost_target_object: Permanent | None = None
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
    class_level: int | None = None
    attached_to: str | None = None
    attachment_timestamp: tuple[int, int] = (0, 0)
    entered_timestamp: tuple[int, int] = (0, 0)
    ability_loss_timestamp: tuple[int, int] | None = None
    aura_creature_type: str | None = None
    aura_effect_ids: tuple[str, ...] = ()
    aura_attack_restrictions: tuple[tuple[str, str], ...] = ()
    cast_x_value: int | None = None

    @property
    def rules_card(self):
        """Evaluated intrinsic abilities; printed card facts remain immutable for history."""
        if self.ability_loss_timestamp is None:
            return self.card
        return replace(self.card, oracle_text="", keywords=())

    @property
    def active_temporary_keyword_effects(self):
        return tuple(
            effect
            for effect in self.temporary_keyword_effects
            if self.ability_loss_timestamp is None or effect.timestamp > self.ability_loss_timestamp
        )

    def __post_init__(self) -> None:
        if self.class_level is None and "Class" in self.card.type_line:
            self.class_level = 1

    @property
    def type_line(self) -> str:
        """The permanent's current authoritative type line on the battlefield."""
        current = (
            self.card.type_line if self.type_line_override is None else self.type_line_override
        )
        if self.aura_creature_type is not None and "Creature" in current:
            types, _, subtypes = current.partition(" — ")
            # Preserve represented noncreature subtypes on multi-type permanents.
            retained = [
                s
                for s in subtypes.split()
                if s
                in {
                    "Equipment",
                    "Vehicle",
                    "Fortification",
                    "Food",
                    "Clue",
                    "Treasure",
                    "Mutagen",
                    "Blood",
                    "Map",
                    "Powerstone",
                }
            ]
            return types + " — " + " ".join([*retained, self.aura_creature_type])
        return current

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
    exile: list[CardObject] = field(default_factory=list)
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
            if (
                permanent.card.is_creature
                and permanent.damage >= permanent.toughness
                and not game._has_indestructible(permanent)
            )
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
            for zone_name in ("library", "hand", "graveyard", "exile"):
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


class Game(
    AuraMixin,
    FoodSearchMixin,
    VigilanteMixin,
    JuryRigMixin,
    TopLibrarySelectionMixin,
    MillThreeMixin,
    KrangRefillMixin,
):
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
        attack_target_chooser=None,
        alliance_mode_chooser=None,
        temporary_keyword_chooser=None,
        stun_target_chooser=None,
        scry_chooser=None,
        hand_bottom_draw_chooser=None,
        discard_draw_chooser=None,
        combat_obligation_chooser=None,
        draw_discard_chooser=None,
        class_recovery_chooser=None,
        food_search_chooser=None,
        jury_rig_chooser=None,
        top_library_selection_chooser=None,
        paramecia_exile_chooser=None,
        paramecia_target_chooser=N