Warning: truncated output (original token count: 135052)
Total output lines: 12164

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
    sneak_returned_attacker_id: str | None = None
    sneak_returned_hand_id: str | None = None
    sneak_defending_player: int | None = None
    sneak_oracle_fragment: str | None = None
    cast_from_graveyard: bool = False
    finality_on_entry: bool = False
    cast_from_raphael: bool = False
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
    AuraMixin, FoodSearchMixin, VigilanteMixin, JuryRigMixin, MillThreeMixin, KrangRefillMixin
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
        draw_discard_chooser=None,
        class_recovery_chooser=None,
        food_search_chooser=None,
        jury_rig_chooser=None,
        paramecia_exile_chooser=None,
        paramecia_target_chooser=None,
        raphael_exile_chooser=None,
        raphael_play_chooser=None,
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
        self._response_exposure_keys: set[tuple[int, str, str]] = set()
        self.pending_triggers: list[TriggerInstance] = []
        self._triggers: dict[str, TriggerInstance] = {}
        self._next_event_number = 1
        self._rules_events: dict[str, RulesEvent] = {}
        self._permanent_left_history: list[RulesEvent] = []
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
        self._static_team_contributions: dict[tuple[str, str, str], tuple[int, int, str, str]] = {}
        self._init_mill_three()
        self._init_krang_refill()
        self.players = [PlayerState(names[i], []) for i in range(2)]
        self._krang_refill_zones = tuple((p, p.library, p.hand) for p in self.players)
        self._mill_three_zones = tuple((p, p.library, p.graveyard) for p in self.players)
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
        self.floating_mana = FloatingManaLedger()
        self.scry_evidence: list[ScryEvidence] = []
        self.etb_drain_gain_scry_evidence: list[EtbDrainGainScryEvidence] = []
        self._stun_selections: dict[str, StunTargetSelection] = {}
        self._rock_soldiers_targets: dict[str, str | None] = {}
        self._shredder_targets: dict[
            str, tuple[Permanent | None, CardFact | None, tuple[str, ...]]
        ] = {}
        self._stun_history: list[tuple[int, tuple[tuple[str, object], ...]]] = []
        self.hand_bottom_draw_evidence: list[HandBottomDrawEvidence] = []
        self.discard_draw_evidence: list[DiscardDrawEvidence] = []
        self._ltb_mutagen_departures = {}
        self._ltb_mutagen_enqueued: set[tuple[str, str, str]] = set()
        self._ltb_mutagen_anchors = {}
        self._ltb_mutagen_consumed: set[str] = set()
        self._paramecia_departures = {}
        self._raphael_linked_exile = {}
        self._raphael_permissions = {}
        self._init_vigilante()
        self._init_jury_rig(jury_rig_chooser)
        self._food_search_history = []
        self._food_search_anchors = {}
        self._food_search_sources = {}
        self._food_search_consumed = set()
        self._food_search_choice_active = False
        self.food_search_chooser = food_search_chooser or (lambda _view, options: options[0])
        self._draw_discard_anchors = {}
        self._draw_discard_sources = {}
        self._draw_discard_consumed: set[str] = set()
        self._mill_draw_discard_anchors = {}
        self._mill_draw_discard_sources = {}
        self._mill_draw_discard_consumed: set[str] = set()
        self._class_recovery_targets = {}
        self.class_recovery_chooser = class_recovery_chooser or (
            lambda _player_index, _source_id, offered: tuple(offered[:2])
        )
        self._mandatory_discard_choice_active = False
        self.draw_discard_chooser = draw_discard_chooser or (lambda _view, options: options[0])
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
        self.attack_target_chooser = attack_target_chooser or (
            lambda _player_index, _source_id, object_ids: object_ids[0] if object_ids else None
        )
        self.counter_spell_target_chooser = lambda _player_index, _source_id, object_ids: (
            object_ids[0]
        )
        self.alliance_mode_chooser = alliance_mode_chooser or (
            lambda _player_index, _source_id, modes: modes[0]
        )
        self.temporary_keyword_chooser = temporary_keyword_chooser or (
            lambda _player_index, _source_id, choices: choices[0]
        )
        self.stun_target_chooser = stun_target_chooser or (
            lambda _controller, _source_id, options: options[0]
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
        self.paramecia_exile_chooser = paramecia_exile_chooser or (
            lambda _controller, _source_id: True
        )
        self.paramecia_target_chooser = paramecia_target_chooser or (
            lambda _controller, _source_id, options: options[0] if options else None
        )
        self.raphael_exile_chooser = raphael_exile_chooser or (lambda _controller, _source_id: True)
        self.raphael_play_chooser = raphael_play_chooser or (
            lambda _controller, _source_id, options: options[0] if options else None
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
        if getattr(self, "_jury_rig_choice_active", False):
            raise ValueError("Jury-Rig chooser cannot register authoritative objects")
        if getattr(self, "_food_search_choice_active", False):
            raise ValueError("Food search chooser cannot register authoritative objects")
        if obj.object_id in self._objects:
            raise ValueError(f"duplicate runtime object ID: {obj.object_id}")
        self._objects[obj.object_id] = obj
        if isinstance(obj, Permanent):
            obj.entered_timestamp = self._effect_timestamp()
        self._mill_three_register(obj)
        self._krang_refill_register(obj)
        return obj

    def _create_card_object(self, card: CardFact, owner: int, zone: Zone) -> CardObject:
        if zone not in {"library", "hand", "graveyard", "exile"}:
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
            for zone in (
                player.library,
                player.hand,
                player.battlefield,
                player.graveyard,
                player.exile,
            )
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
                for fragment in self.interpreter.fragments(permanent.rules_card):
                    coverage = self.interpreter.permanent_left_self_counter_semantic_coverage(
                        permanent.card, fragment
                    )
                    if coverage is not None and coverage.fully_supported:
                        sources.append((permanent, fragment))
        return tuple(sources)

    def _permanent_left_this_turn(self, controller: int) -> bool:
        return any(
            event.turn == self.turn
            and event.player_index == controller
            and event.kind is RulesEventKind.PERMANENT_LEFT
            and bool(event.subject_ids)
            for event in self._permanent_left_history
        )

    def move_object(
        self,
        obj: CardObject | StackObject | Permanent,
        destination: Literal["library", "hand", "stack", "battlefield", "graveyard", "exile"],
        *,
        controller: int | None = None,
        cast_kind: CastKind | None = None,
        target_id: str | None = None,
        summoning_sick: bool = True,
        cast_from_graveyard: bool = False,
        finality_on_entry: bool = False,
        cast_from_raphael: bool = False,
        reason: str | None = None,
        library_position: Literal["top", "bottom"] | None = None,
        _departure_authority: tuple[tuple[str, int], ...] | None = None,
        _departure_sources: tuple[tuple[Permanent, str], ...] | None = None,
    ) -> CardObject | StackObject | Permanent:
        """Validate then atomically create the destination-zone incarnation of ``obj``."""
        if self._jury_rig_choice_active:
            raise ValueError("Jury-Rig chooser cannot move authoritative objects")
        if self._food_search_choice_active:
            raise ValueError("Food search chooser cannot move authoritative objects")
        if self._mandatory_discard_choice_active:
            raise ValueError("discard/Draw chooser cannot move authoritative objects")
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
        if destination != "stack" and (
            cast_kind is not None
            or …105052 tokens truncated…         if item.terminal_after_life_loss:
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
            countered = any(
                event.get("event") == "spell_countered"
                and event.get("target_spell_id") == spell.object_id
                for event in self.events
            )
            if spell.cast_kind is CastKind.CREATURE:
                if resolved and spell.zone != "former":
                    raise AssertionError("Sneak evidence resolution disagrees with stack state")
                if not resolved and spell.zone == "former" and not countered:
                    raise AssertionError("Sneak evidence resolution disagrees with stack state")
                if resolved and (
                    item.resolved_object_id not in self._objects
                    or item.entered_tapped is not True
                    or item.entered_attacking is not True
                ):
                    raise AssertionError("resolved Sneak evidence lacks battlefield result")
            elif resolved:
                raise AssertionError("noncreature Sneak evidence has a battlefield result")
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
                if obj.effect is TriggerEffect.ETB_SELF_LIFE_GAIN:
                    try:
                        self._validate_etb_self_life_gain_trigger(obj)
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
                if obj.effect is TriggerEffect.ALLIANCE_TEMPORARY_KEYWORD_CHOICE:
                    try:
                        self._validate_alliance_temporary_keyword_choice_trigger(obj)
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
            for zone_name in ("library", "hand", "battlefield", "graveyard", "exile"):
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
                    or not isinstance(effect.keyword, (StrikeKeyword, TemporaryKeyword))
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
                tuple(card.object_id for card in player.exile),
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
                    "exile_object_ids": list(player[4]),
                    "life": player[5],
                    "lost": player[6],
                    "failed_draw_pending": player[7],
                }
                for player in zones
            ],
            "rng_state_digest": authority[7],
            "winner_index": authority[8],
        }

    def _executed_conformance_references(self) -> list[dict[str, object]]:
        """Index mature Action evidence without replacing or weakening that evidence."""
        self._validate_stun_history()
        self._check_mill_three_history()
        self._validate_krang_refill_live()
        self._check_jury_rig_history()
        self._check_vigilante_live()
        self.validate_food_search_snapshot_evidence(
            {"events": self.events, "food_search_evidence": self.food_search_snapshot_evidence()}
        )
        self.validate_draw_discard_snapshot_evidence({"events": self.events})
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
            if CardInterpreter.is_krang_refill_fragment(event.get("oracle_fragment")):
                if event.get("event") == "krang_refill_committed" and event["requested"] > 0:
                    add(
                        "krang_refill",
                        event["stack_object_id"],
                        event["source_id"],
                        event["oracle_fragment"],
                    )
                continue
            if event.get("oracle_fragment") == CardInterpreter.MILL_THREE_FRAGMENT:
                if event.get("event") == "mill_three_committed":
                    add(
                        "mill_three",
                        event["stack_object_id"],
                        event["source_id"],
                        event["oracle_fragment"],
                    )
                continue
            if event.get("oracle_fragment") == CardInterpreter.JURY_RIG_FRAGMENT:
                if event.get("event") == "jury_rig_committed":
                    add(
                        "jury_rig",
                        event["stack_object_id"],
                        event["source_id"],
                        event["oracle_fragment"],
                    )
                continue
            if event.get("effect") == "etb_vigilante":
                continue
            if event.get("event") in {
                "damage_dealt",
                "scry_committed",
                "tokens_created",
                "trigger_resolved",
                "spell_resolved",
                "spell_resolved_no_effect",
                "aura_resolved",
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
            "turns_started": self.turn,
            "terminal": self.winner is not None,
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
            "mill_three_evidence": self.mill_three_snapshot_evidence(),
            "krang_refill_evidence": self.krang_refill_snapshot_evidence(),
            "jury_rig_evidence": self.jury_rig_snapshot_evidence(),
            "vigilante_evidence": self.vigilante_snapshot_evidence(),
            "food_search_evidence": self.food_search_snapshot_evidence(),
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
                        **(
                            {"target_id": entry.target_id}
                            if entry.effect is TriggerEffect.ETB_TAP_STUN
                            else {}
                        ),
                        "source": entry.source_card.name,
                        "source_id": entry.source_id,
                        "controller": entry.controller,
                        "effect": entry.effect.value,
                        "event_id": entry.event.event_id,
                        "trigger_id": entry.trigger_id,
                        "target_ids": list(entry.target_ids),
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
            "stun_history": [
                {"event_cursor": cursor, "record": dict(record)}
                for cursor, record in self._stun_history
            ],
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
                    "cost_target_id": item.cost_target_id,
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
                            **({"class_level": x.class_level} if x.class_level is not None else {}),
                            **({"attached_to": x.attached_to} if x.attached_to is not None else {}),
                            "entered_timestamp": list(x.entered_timestamp),
                            "attachment_timestamp": list(x.attachment_timestamp),
                            "ability_loss_timestamp": x.ability_loss_timestamp,
                            "aura_creature_type": x.aura_creature_type,
                            "aura_effect_ids": list(x.aura_effect_ids),
                            "aura_attack_restrictions": list(x.aura_attack_restrictions),
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
                                    **(
                                        {"source_object_id": modifier.source_object_id}
                                        if modifier.source_object_id is not None
                                        else {}
                                    ),
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
                                    "timestamp": list(effect.timestamp),
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
