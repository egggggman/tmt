YªçŠx-®éÜj×¢ëiºÚ+Š§j[h‘éÜ¢éíÛÝýß}vï^zo+^²‰¢¶×"""Small, deterministic, rules-grounded Cardcade Engine 0.7 foundation.

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
from itertools import combinations, permutations
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
    TopCardSelectionViewV2,
    TopCreatureSelectionViewV2,
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
    choice_ids: tuple[str, ...] = ()

    @property
    def x_value(self) -> int | None:
        """An X announcement encoded in the existing immutable choice channel."""
        if (
            self.kind is ActionKind.CAST
            and len(self.choice_ids) == 1
            and self.choice_ids[0].isdecimal()
        ):
            return int(self.choice_ids[0])
        return None


@dataclass(frozen=True)
class TopCardSelectionOption:
    card_id: str | None


@dataclass(frozen=True)
class TopCreatureSelectionOption:
    card_ids: tuple[str, ...]


@dataclass(frozen=True)
class PriorityState:
    """Authoritative bounded 1v1 priority state for a nonempty stack."""

    epoch: int
    player_index: int
    consecutive_passes: tuple[int, ...] = ()
    resolution_pending: bool = False


@dataclass
class LinkedPlayGrant:
    """One until-end-of-turn permission to play any one card linked to a source object."""

    grant_id: str
    source_id: str
    controller: int
    expires_turn: int
    remaining_plays: int = 1


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
    floating_event_ids: tuple[str, ...] = ()
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
    floating_event_ids: tuple[str, ...] = ()
    source_zone: str = "hand"
    permission_source_id: str | None = None


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
    source_zone: str = "hand"
    permission_source_id: str | None = None


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
    floating_event_ids: tuple[str, ...] = ()
    other_sacrifice_id: str | None = None
    reduction_source_ids: tuple[str, ...] = ()


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
    END_STEP_BEGAN = "end_step_began"
    DAMAGE_DEALT = "damage_dealt"
    COMBAT_DAMAGE_TO_PLAYER = "combat_damage_to_player"
    COMBAT_DAMAGE_TO_CREATURE = "combat_damage_to_creature"
    SCRIED = "scried"
    HAND_BOTTOM_DRAW = "hand_bottom_draw"
    DISCARD_DRAW = "discard_draw"
    VIGILANTE_UPKEEP = "vigilante_upkeep"
    PERMANENT_LEFT = "permanent_left"
    SPELL_CAST = "spell_cast"
    CLASS_LEVEL_ADVANCED = "class_level_advanced"
    BEGINNING_OF_COMBAT = "beginning_of_combat"
    CARD_DISCARDED = "card_discarded"


class TriggerEffect(Enum):
    ALLIANCE_PT = "alliance_pt"
    ALLIANCE_COUNTER = "alliance_counter"
    ALLIANCE_MODAL = "alliance_modal"
    LIFE_GAIN_COUNTER = "life_gain_counter"
    ATTACK_PT = "attack_pt"
    ATTACK_TARGET_COUNTER = "attack_target_counter"
    SNEAK_ETB_CONDITION = "sneak_etb_condition"
    CREATE_TOKEN = "create_token"
    CONDITIONAL_ENTRY_TOKEN = "conditional_entry_token"
    DEAL_DAMAGE = "deal_damage"
    ETB_ANY_TARGET_DAMAGE = "etb_any_target_damage"
    SCRY = "scry"
    DISCARD_DRAW = "discard_draw"
    ETB_KRANG_REFILL = "etb_krang_refill"
    ETB_MILL_THREE = "etb_mill_three"
    ETB_JURY_RIG = "etb_jury_rig"
    ETB_VIGILANTE = "etb_vigilante"
    VIGILANTE_DISCARD = "vigilante_discard"
    ETB_FOOD_SEARCH = "etb_food_search"
    ETB_DRAW_DISCARD = "etb_draw_discard"
    COMBAT_DAMAGE_DRAW_DISCARD = "combat_damage_draw_discard"
    COMBAT_DAMAGE_DRAW_LOSE_LIFE = "combat_damage_draw_lose_life"
    COMBAT_DAMAGE_GRAVEYARD_ATTACKER = "combat_damage_graveyard_attacker"
    COMBAT_DAMAGE_ARTIFACT_COPY = "combat_damage_artifact_copy"
    GRANTED_COMBAT_UNTAP_GAIN = "granted_combat_untap_gain"
    EQUIPMENT_SUBTYPE_ENTRY_ATTACH = "equipment_subtype_entry_attach"
    UTILITY_TARGET = "utility_target"
    ETB_MILL_DRAW_DISCARD = "etb_mill_draw_discard"
    CLASS_LEVEL_TWO_RECOVERY = "class_level_two_recovery"
    CLASS_DISCARD_DAMAGE = "class_discard_damage"
    CLASS_LEVEL_THREE_SEARCH = "class_level_three_search"
    CLASS_SPELL_CAST_TEAM_COUNTER = "class_spell_cast_team_counter"
    CLASS_COMBAT_ARTIFACT_ANIMATION = "class_combat_artifact_animation"
    LTB_MUTAGEN = "ltb_mutagen"
    DIES_DRAW = "dies_draw"
    GRANTED_DIES_RETURN = "granted_dies_return"
    ETB_DRAIN_GAIN_SCRY = "etb_drain_gain_scry"
    ETB_SELF_LIFE_GAIN = "etb_self_life_gain"
    PERMANENT_LEFT_SELF_COUNTER = "permanent_left_self_counter"
    CONTROLLED_CREATURE_LEFT_OPPONENT_LOSS = "controlled_creature_left_opponent_loss"
    CONTROLLED_COUNTERED_CREATURE_LEFT_LIFE = "controlled_countered_creature_left_life"
    CONTROLLED_ARTIFACT_COUNTER_TRANSFER = "controlled_artifact_counter_transfer"
    DAMAGE_TO_SELF_MANA = "damage_to_self_mana"
    ETB_ARTIFACT_DRAW = "etb_artifact_draw"
    ETB_TAP_STUN = "etb_tap_stun"
    ETB_ATTACH_EQUIPMENT = "etb_attach_equipment"
    ALLIANCE_TEMPORARY_KEYWORD_CHOICE = "alliance_temporary_keyword_choice"
    ROCK_SOLDIERS_ETB_DESTROY = "rock_soldiers_etb_destroy"
    ETB_DESTROY_TARGET_CREATURE = "etb_destroy_target_creature"
    ETB_TARGET_CREATURE_PUMP_UNTAP = "etb_target_creature_pump_untap"
    ARTIFACT_ENTRY_SELF_COUNTER = "artifact_entry_self_counter"
    SHREDDER_DEATHTOUCH = "shredder_deathtouch"
    PARAMECIA_EXILE_CHOICE = "paramecia_exile_choice"
    PARAMECIA_REFLEXIVE_RETURN = "paramecia_reflexive_return"
    RAPHAEL_ALLIANCE_EXILE = "raphael_alliance_exile"
    RAPHAEL_ATTACK_PLAY = "raphael_attack_play"
    COMBAT_DISCARD_OR_SACRIFICE = "combat_discard_or_sacrifice"
    END_STEP_SPELL_TYPES_DRAW = "end_step_spell_types_draw"
    DISAPPEAR_END_STEP = "disappear_end_step"


class TemporaryKeyword(Enum):
    FLYING = "flying"
    MENACE = "menace"
    HASTE = "haste"
    DEATHTOUCH = "deathtouch"
    REACH = "reach"
    TRAMPLE = "trample"
    HEXPROOF = "hexproof"
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
    source_event: RulesEvent | None = None


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
    source_deathtouch: bool = False


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
class TemporaryDeathReturnEffect:
    """A bounded triggered ability granted to a creature by a resolving spell."""

    duration: Literal["until_end_of_turn"]
    source_id: str
    oracle_fragment: str
    timestamp: tuple[int, int]


@dataclass(frozen=True)
class TemporaryTypeEffect:
    """A layer-four addition to a permanent's card types for its stated duration."""

    added_types: tuple[str, ...]
    duration: Literal["persistent", "until_end_of_turn"]
    source_id: str
    oracle_fragment: str
    timestamp: tuple[int, int]
    added_subtypes: tuple[str, ...] = ()


@dataclass(frozen=True)
class TriggerInstance:
    trigger_id: str
    controller: int
    source_id: str
    source_card: CardFact
    oracle_fragment: str
    effect: TriggerEffect
    event: RulesEvent
    grant_source_id: str | None = None


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
    duration: Literal["persistent", "until_end_of_turn"] = "persistent"


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
    target_ids: tuple[str, ...] = ()
    source_target_id: str | None = None
    mode_fragment: str | None = None
    kicker_sacrifice_id: str | None = None
    sneak_returned_attacker_id: str | None = None
    sneak_returned_hand_id: str | None = None
    sneak_defending_player: int | None = None
    sneak_oracle_fragment: str | None = None
    cast_from_graveyard: bool = False
    finality_on_entry: bool = False
    cast_from_raphael: bool = False
    sneak_mana_source_ids: tuple[str, ...] = ()
    zone: Zone = "stack"
    x_value: int | None = None

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
    departure_event_id: str | None = None
    discarded_destination_id: str | None = None
    other_sacrifice_id: str | None = None
    other_sacrifice_destination_id: str | None = None
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
    entered_under_controller: int = -1
    damage: int = 0
    deathtouch_damage: bool = False
    counters: dict[str, int] = field(default_factory=dict)
    pt_modifiers: list[PowerToughnessModifier] = field(default_factory=list)
    characteristic_effects: list[CharacteristicEffect] = field(default_factory=list)
    temporary_keyword_effects: list[TemporaryKeywordEffect] = field(default_factory=list)
    temporary_death_return_effects: list[TemporaryDeathReturnEffect] = field(default_factory=list)
    temporary_type_effects: list[TemporaryTypeEffect] = field(default_factory=list)
    is_token: bool = False
    type_line_override: str | None = None
    class_level: int | None = None
    class_level_timestamp: tuple[int, int] = (0, 0)
    attached_to: str | None = None
    attachment_timestamp: tuple[int, int] = (0, 0)
    entered_timestamp: tuple[int, int] = (0, 0)
    ability_loss_timestamp: tuple[int, int] | None = None
    aura_creature_type: str | None = None
    aura_effect_ids: tuple[str, ...] = ()
    aura_attack_restrictions: tuple[tuple[str, str], ...] = ()
    once_per_turn_activations: dict[str, int] = field(default_factory=dict)
    x_value: int | None = None

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
            types, _, subtypes = current.partition(" â€” ")
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
            current = types + " â€” " + " ".join([*retained, self.aura_creature_type])
        if self.temporary_type_effects:
            card_types, separator, subtypes = current.partition(" â€” ")
            tokens = card_types.split()
            subtype_tokens = subtypes.split()
            for effect in sorted(self.temporary_type_effects, key=lambda item: item.timestamp):
                for added in effect.added_types:
                    if added not in tokens:
                        if added == "Artifact" and "Creature" in tokens:
                            tokens.insert(tokens.index("Creature"), added)
                        else:
                            tokens.append(added)
                for added in effect.added_subtypes:
                    if added not in subtype_tokens:
                        subtype_tokens.append(added)
            current = " ".join(tokens) + (
                " â€” " + " ".join(subtype_tokens) if subtype_tokens else ""
            )
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
    def has_represented_power_toughness(self) -> bool:
        """Return whether the current creature has a represented P/T starting point."""
        return (self.card.power is not None and self.card.toughness is not None) or any(
            effect.sublayer is PowerToughnessSubLayer.SET_BASE
            and effect.operation is CharacteristicOperation.SET
            for effect in self.characteristic_effects
        )

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
        if self.card.power is None or self.card.toughness is None:
            if not any(
                effect.sublayer is PowerToughnessSubLayer.SET_BASE
                and effect.operation is CharacteristicOperation.SET
                for effect in effects
            ):
                raise ValueError("animated noncreature lacks a represented base P/T effect")
            power, toughness = 0, 0
        else:
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
            if permanent.is_creature
            and permanent.has_represented_power_toughness
            and (
                permanent.toughness <= 0
                or (
                    permanent.damage > 0
                    and (permanent.damage >= permanent.toughness or permanent.deathtouch_damage)
                    and not game._has_keyword(permanent, "Indestructible")
                )
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
        newly_lost = []
        for index, player in enumerate(game.players):
            if not player.failed_draw_pending:
                continue
            player.failed_draw_pending = False
            if not player.lost:
                player.lost = True
                player.loss_reason = "draw_from_empty_library"
                newly_lost.append(index)
                game.log(
                    "player_lost",
                    player=player.name,
                    reason=player.loss_reason,
                    state_based_action=self.name,
                )
        if len(newly_lost) == 2:
            game.winner = None
            game.terminal_draw = True
            game.log("game_draw", reason="simultaneous_failed_draw")
        elif newly_lost:
            game.winner = 1 - newly_lost[0]
        return bool(newly_lost)


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
        alliance_mode_chooser=None,
        temporary_keyword_chooser=None,
        stun_target_chooser=None,
        scry_chooser=None,
        top_card_chooser=None,
        top_creature_selection_chooser=None,
        library_search_chooser=None,
        hand_reset_chooser=None,
        hand_bottom_draw_chooser=None,
        library_position_chooser=None,
        discard_draw_chooser=None,
        draw_discard_chooser=None,
        class_recovery_chooser=None,
        food_search_chooser=None,
        jury_rig_chooser=None,
        paramecia_exile_chooser=None,
        paramecia_target_chooser=None,
        raphael_exile_chooser=None,
        damage_target_chooser=None,
        equipment_attach_chooser=None,
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
        self.terminal_draw = False
        self.damage_target_chooser = damage_target_chooser
        self.events: list[dict[str, object]] = []
        self.floating_mana = FloatingManaLedger()
        self.scry_evidence: list[ScryEvidence] = []
        self.etb_drain_gain_scry_evidence: list[EtbDrainGainScryEvidence] = []
        self._stun_selections: dict[str, StunTargetSelection] = {}
        self._rock_soldiers_targets: dict[str, str | None] = {}
        self._etb_creature_destroy_targets: dict[str, tuple[Permanent, tuple[str, ...]]] = {}
        self._etb_pump_targets: dict[str, tuple[Permanent, tuple[str, ...]]] = {}
        self._attack_counter_targets: dict[str, tuple[str, str]] = {}
        self._countered_departure_anchors: dict[str, tuple[object, ...]] = {}
        self._artifact_counter_departures: dict[str, tuple[object, ...]] = {}
        self._artifact_counter_targets: dict[str, tuple[Permanent | None, tuple[str, ...]]] = {}
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
        self._linked_play_grants: dict[str, list[LinkedPlayGrant]] = {}
        self.discard_or_sacrifice_chooser = lambda _controller, _source, discards, sacrifices: (
            ("discard", discards[-1]) if discards else ("sacrifice", sacrifices[0])
        )
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
        self._combat_draw_discard_anchors = {}
        self._combat_draw_discard_consumed: set[str] = set()
        self._combat_artifact_copy_targets: dict[str, tuple[str | None, tuple[str, ...]]] = {}
        self._utility_trigger_anchors = {}
        self._utility_trigger_consumed: set[str] = set()
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
        self.top_card_chooser = top_card_chooser or (
            lambda _view, options: next(
                (option for option in options if option.card_id is not None), options[0]
            )
        )
        self.top_creature_selection_chooser = (
            top_creature_selection_chooser or self._default_top_creature_selection_choice
        )
        self._top_creature_selection_choice_active = False
        self.library_search_chooser = library_search_chooser or self._default_library_search_choice
        self._library_search_choice_active = False
        self.hand_reset_chooser = hand_reset_chooser or (
            lambda _player, cards, _context: len(cards) < 7
        )
        self._hand_reset_choice_active = False
        self.hand_bottom_draw_chooser = hand_bottom_draw_chooser or (
            lambda _view, options: next(option for option in options if option.card_id is None)
        )
        self.library_position_chooser = library_position_chooser or (
            lambda _owner, _source_id, _target_id, options: options[0]
        )
        self._library_position_choice_active = False
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
        self.equipment_attach_chooser = equipment_attach_chooser or (
            lambda _controller, _source_id, _recipient_id: True
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
            entered_under_controller=owner if controller is None else controller,
            x_value=0 if "{X}" in card.mana_cost else None,
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
        defer_post_creation: bool = False,
        defer_triggers: bool = False,
        attacking_defender: int | None = None,
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
        if attacking_defender is not None and (
            not definition.is_creature
            or not program.tapped
            or destination_controller != self.active_player
            or attacking_defender != 1 - destination_controller
            or self.step is not TurnStep.DECLARE_BLOCKERS
            or not self._blockers_declared
        ):
            raise ValueError("attacking tokens require a legal defending player and combat")
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
                    entered_under_controller=destination_controller,
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
        if attacking_defender is not None:
            self._combat_attackers += object_ids
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
            attacking_defender=attacking_defender,
            tapped=program.tapped,
        )
        if created:
            self._process_creatures_entered_triggers(tuple(created), defer_triggers=defer_triggers)
        self.refresh_static_pt_modifiers()
        if not defer_post_creation:
            self.check_state_based_actions()
        return tuple(created)

    def create_copy_token(
        self,
        source: Permanent,
        controller: int,
        *,
        source_card: str,
        oracle_fragment: str,
        source_id: str | None = None,
        stack_object_id: str | None = None,
    ) -> Permanent:
        """Create one independent token with the source's copiable characteristics."""
        if (
            not isinstance(source, Permanent)
            or not self.is_authoritative(source, "battlefield")
            or controller not in range(2)
            or source.controller != controller
            or "Artifact" not in source.type_line.split(" â€” ", 1)[0].split()
        ):
            raise ValueError("copy source is not an authoritative controlled artifact")
        if source_id is not None and source_id != source.object_id:
            raise ValueError("copy source identity mismatch")
        card = source.card
        definition = TokenDefinition(
            name=card.name,
            type_line=card.type_line,
            power=card.power,
            toughness=card.toughness,
            oracle_text=card.oracle_text,
            keywords=card.keywords,
            mana_cost=card.mana_cost,
            mana_value=card.mana_value,
            oracle_id=getattr(card, "oracle_id", ""),
        )
        created = self.create_tokens(
            controller,
            TokenCreationProgram(definition, 1),
            controller=controller,
            source_card=source_card,
            oracle_fragment=oracle_fragment,
            source_id=source.object_id,
            defer_post_creation=True,
        )[0]
        self.log(
            "copied_artifact_token_created",
            stack_object_id=stack_object_id,
            source_id=source.object_id,
            token_id=created.object_id,
            source_card=source_card,
            oracle_fragment=oracle_fragment,
            copied_name=definition.name,
            copied_type_line=definition.type_line,
            copied_oracle_text=definition.oracle_text,
            attached_to=None,
        )
        return created

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
                    loss = self.interpreter.CONTROLLED_CREATURE_LEFT_OPPONENT_LOSS.fullmatch(
                        fragment
                    )
                    countered_life = self.interpreter.countered_creature_left_life(
                        permanent.card, fragment
                    )
                    counter_transfer = self.interpreter.controlled_artifact_counter_transfer(
                        permanent.card, fragment
                    )
                    if (
                        (coverage is not None and coverage.fully_supported)
                        or loss is not None
                        or counter_transfer
                        or (
                            countered_life is not None
                            and (permanent.class_level is None or permanent.class_level >= 2)
                        )
                    ):
                        sources.append((permanent, fragment))
        return tuple(sources)

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
        if self._library_position_choice_active:
            raise ValueError("library-position chooser cannot move authoritative objects")
        if self._library_search_choice_active:
            raise ValueError("library-search chooser cannot move authoritative objects")
        if self._top_creature_selection_choice_active:
            raise ValueError("top-creature chooser cannot move authoritative objects")
        if self._hand_reset_choice_active:
            raise ValueError("hand-reset chooser cannot move authoritative objects")
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
            or target_id is not None
            or cast_from_graveyard
            or finality_on_entry
        ):
            raise ValueError("stack metadata is valid only for stack movement")
        if library_position is not None and destination != "library":
            raise ValueError("library position is valid only for library movement")

        source_zone = obj.zone
        departure_authority = None
        departure_sources = None
        departure_last_known = None
        departure_counters: tuple[tuple[str, int], ...] = ()
        ltb_mutagen_fragments = ()
        ltb_utility_fragments = ()
        ltb_token_fragments = ()
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
            departure_counters = tuple(
                sorted((kind, count) for kind, count in obj.counters.items() if count > 0)
            )
            ltb_mutagen_fragments = tuple(
                fragment
                for fragment in self.interpreter.fragments(obj.rules_card)
                if self.interpreter.ltb_mutagen_semantic_coverage(obj.card, fragment) is not None
            )
            ltb_utility_fragments = tuple(
                fragment
                for fragment in self.interpreter.fragments(obj.rules_card)
                if (semantics := self.interpreter.utility_trigger_semantics(obj.card, fragment))
                is not None
                and semantics[0] == "entry_or_leave"
            )
            ltb_token_fragments = tuple(
                fragment
                for fragment in self.interpreter.fragments(obj.rules_card)
                if self.interpreter.entry_leave_or_artifact_cast_token_context(obj.card, fragment)
                == "entry_or_leave"
                and (coverage := self.interpreter.token_semantic_coverage(obj.card, fragment))
                is not None
                and coverage.fully_supported
            )
            for fragment in ltb_mutagen_fragments:
                coverage = self.interpreter.ltb_mutagen_semantic_coverage(obj.card, fragment)
                assert coverage is not None
                self._register_semantic_occurrence(
                    obj, obj.controller, fragment, coverage.limitations
                )
        new_id = self._allocate_object_id()
        destination_controller = obj.owner if controller is None else controller
        if destination == "battlefield":
            replacement: CardObject | StackObject | Permanent = Permanent(
                new_id,
                obj.card,
                obj.owner,
                destination_controller,
                tapped=self.interpreter.enters_tapped_semantics(obj.card),
                summoning_sick=summoning_sick,
                entered_battlefield_turn=self.turn,
                entered_under_controller=destination_controller,
                is_token=getattr(obj, "is_token", False),
                x_value=(
                    obj.x_value
                    if isinstance(obj, StackObject)
                    else 0
                    if "{X}" in obj.card.mana_cost
                    else None
                ),
            )
            if replacement.is_creature and self._left_under_control_this_turn(
                destination_controller
            ):
                for fragment in self.interpreter.fragments(replacement.rules_card):
                    match = self.interpreter.DISAPPEAR_ENTRY_COUNTERS.fullmatch(fragment)
                    if match is not None:
                        quantity = {"one": 1, "two": 2, "three": 3}.get(match["quantity"])
                        replacement.counters["+1/+1"] = (
                            quantity if quantity is not None else int(match["quantity"])
                        )
            destination_container = self.players[destination_controller].battlefield
        elif destination == "stack":
            assert controller is not None and cast_kind is not None
            replacement = StackObject(
                new_id,
                obj.card,
                obj.owner,
                controller,
                cast_kind,
                target_id,
                cast_from_graveyard=cast_from_graveyard,
                finality_on_entry=finality_on_entry,
                cast_from_raphael=cast_from_raphael,
            )
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
        if departure_last_known is not None:
            self.log(
                "permanent_departed",
                source_object_id=obj.object_id,
                destination_object_id=replacement.object_id,
                controller=departure_last_known[1],
                type_line=departure_last_known[2],
                counter_snapshot=[list(counter) for counter in departure_counters],
            )
            if destination == "graveyard" and departure_last_known[3]:
                grants = tuple(
                    effect
                    for effect in obj.temporary_death_return_effects
                    if obj.ability_loss_timestamp is None
                    or effect.timestamp > obj.ability_loss_timestamp
                )
                if grants:
                    assert departure_authority is not None
                    death = self._new_rules_event(
                        RulesEventKind.CREATURE_DIED,
                        obj.controller,
                        (obj.object_id,),
                        source_id=obj.object_id,
                        battlefield_authority=departure_authority,
                        last_known_battlefield=(departure_last_known,),
                    )
                    for grant in grants:
                        self._enqueue_trigger(
                            death,
                            obj,
                            grant.oracle_fragment,
                            TriggerEffect.GRANTED_DIES_RETURN,
                        )
        if destination == "battlefield" and isinstance(replacement, Permanent):
            for fragment in self.interpreter.fragments(replacement.rules_card):
                if self.interpreter.DISAPPEAR_ENTRY_COUNTERS.fullmatch(fragment):
                    self.log(
                        "conditional_entry_counters",
                        source_id=replacement.object_id,
                        oracle_fragment=fragment,
                        quantity=replacement.counters.get("+1/+1", 0),
                    )
        if source_zone == "hand" and destination == "graveyard" and reason and "discard" in reason:
            watchers = tuple(
                (watcher, fragment)
                for watcher in self.players[obj.owner].battlefield
                if watcher.class_level is not None and watcher.class_level >= 2
                for fragment in self.interpreter.fragments(watcher.rules_card)
                if self.interpreter.CLASS_DISCARD_DAMAGE.fullmatch(fragment)
            )
            if watchers:
                event = self._new_rules_event(
                    RulesEventKind.CARD_DISCARDED,
                    obj.owner,
                    (obj.object_id,),
                    source_id=obj.object_id,
                )
                for watcher, fragment in watchers:
                    self._enqueue_trigger(
                        event, watcher, fragment, TriggerEffect.CLASS_DISCARD_DAMAGE
                    )
        if departure_authority is not None:
            assert departure_sources is not None and departure_last_known is not None
            qualifying_sources = tuple(
                (watcher, fragment)
                for watcher, fragment in departure_sources
                if (
                    watcher.object_id != obj.object_id
                    and self.interpreter.permanent_left_self_counter_semantic_coverage(
                        watcher.card, fragment
                    )
                    is not None
                )
                or (
                    departure_last_known[3]
                    and watcher.controller == departure_last_known[1]
                    and self.interpreter.CONTROLLED_CREATURE_LEFT_OPPONENT_LOSS.fullmatch(fragment)
                )
                or (
                    departure_last_known[3]
                    and bool(departure_counters)
                    and watcher.controller == departure_last_known[1]
                    and self.interpreter.countered_creature_left_life(watcher.card, fragment)
                    is not None
                    and (watcher.class_level is None or watcher.class_level >= 2)
                )
                or (
                    destination == "graveyard"
                    and "Artifact" in departure_last_known[2].split(" â€” ", 1)[0].split()
                    and bool(departure_counters)
                    and watcher.controller == departure_last_known[1]
                    and self.interpreter.controlled_artifact_counter_transfer(
                        watcher.card, fragment
                    )
                )
            )
            if (
                qualifying_sources
                or ltb_mutagen_fragments
                or ltb_utility_fragments
                or ltb_token_fragments
            ):
                departure_record = tuple(self.events[-2].items())
                departure_log_record = tuple(self.events[-1].items())
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
                        if watcher.object_id != obj.object_id
                    ),
                )
                countered_watchers = tuple(
                    (watcher.object_id, watcher.controller, watcher.class_level, fragment)
                    for watcher, fragment in qualifying_sources
                    if self.interpreter.countered_creature_left_life(watcher.card, fragment)
                    is not None
                )
                if countered_watchers:
                    self._countered_departure_anchors[event.event_id] = (
                        obj,
                        departure_counters,
                        departure_log_record,
                        countered_watchers,
                    )
                artifact_watchers = tuple(
                    (watcher.object_id, watcher.controller, fragment)
                    for watcher, fragment in qualifying_sources
                    if self.interpreter.controlled_artifact_counter_transfer(watcher.card, fragment)
                )
                if artifact_watchers:
                    self._artifact_counter_departures[event.event_id] = (
                        obj,
                        departure_counters,
                        departure_log_record,
                        artifact_watchers,
                    )
                for fragment in ltb_mutagen_fragments:
                    key = (obj.object_id, event.event_id, fragment)
                    self._ltb_mutagen_departures[key] = (
                        obj,
                        obj.card,
                        event,
                        replacement,
                        departure_record,
                    )
                    self._enqueue_trigger(event, obj, fragment, TriggerEffect.LTB_MUTAGEN)
                for fragment in ltb_utility_fragments:
                    self._enqueue_trigger(event, obj, fragment, TriggerEffect.UTILITY_TARGET)
                for fragment in ltb_token_fragments:
                    self._enqueue_trigger(event, obj, fragment, TriggerEffect.CREATE_TOKEN)
                for watcher, fragment in qualifying_sources:
                    effect = (
                        TriggerEffect.CONTROLLED_CREATURE_LEFT_OPPONENT_LOSS
                        if self.interpreter.CONTROLLED_CREATURE_LEFT_OPPONENT_LOSS.fullmatch(
                            fragment
                        )
                        else TriggerEffect.CONTROLLED_COUNTERED_CREATURE_LEFT_LIFE
                        if self.interpreter.countered_creature_left_life(watcher.card, fragment)
                        is not None
                        else TriggerEffect.CONTROLLED_ARTIFACT_COUNTER_TRANSFER
                        if self.interpreter.controlled_artifact_counter_transfer(
                            watcher.card, fragment
                        )
                        else TriggerEffect.PERMANENT_LEFT_SELF_COUNTER
                    )
                    self._enqueue_trigger(
                        event,
                        watcher,
                        fragment,
                        effect,
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
        if source_zone == "battlefield" or destination == "battlefield":
            self.refresh_static_pt_modifiers()
        return replacement

    def _left_under_control_this_turn(self, controller: int) -> bool:
        """Use departure-time control, including before the source entered this turn."""
        return any(
            record["turn"] == self.turn and record["controller"] == controller
            for record in self.events
            if record["event"] == "permanent_departed"
        )

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
        self.refresh_static_pt_modifiers()

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
                    if permanent.is_creature
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
                and fragment.startswith("Alliance â€” Whenever another creature you control enters,")
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
                and context_facts.get("destination_zone")
                in {
                    "hand",
                    "library",
                    "graveyard",
                    "exile",
                }
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
                "Alliance â€” Whenever another creature you control enters,"
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
        if transaction.source_event is not None:
            event = transaction.source_event
            self._authenticate_original_rules_event(event)
            source_authoritative = source_authoritative or (
                isinstance(source, Permanent)
                and self._rules_events.get(event.event_id) is event
                and event.kind
                in {
                    RulesEventKind.PERMANENT_ENTERED,
                    RulesEventKind.CREATURE_ENTERED,
                    RulesEventKind.CARD_DISCARDED,
                    RulesEventKind.PERMANENT_LEFT,
                }
                and (
                    event.subject_ids == (source.object_id,)
                    or (event.kind is RulesEventKind.CARD_DISCARDED and event.subject_ids)
                )
                and event.player_index == transaction.controller
                and (source.object_id, source.controller) in event.battlefield_authority
            )
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
            if self.evaluated_deathtouch(source):
                target.deathtouch_damage = True
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
        if target is not None:
            self._enqueue_damage_to_self_mana(event, target)
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
        view = HandBottomDrawViewV2(
            player_index,
            tuple((card.object_id, card.card.name) for card in player.hand),
            decision_context(self, player_index),
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
        view = DiscardDrawViewV2(
            player_index,
            tuple((card.object_id, card.card.name) for card in player.hand),
            decision_context(self, player_index),
        )
        options = tuple(DiscardDrawOption(card.object_id) for card in player.hand)
        if program.optional or not options:
            options = (DiscardDrawOption(None),) + options
        chooser = self.draw_discard_chooser if program.draw_first else self.discard_draw_chooser
        anchors = [
            (obj, dict(vars(obj))) for obj in (*hand_objects, *library_objects, *graveyard_objects)
        ]
        registry = dict(self._objects)

        self._mandatory_discard_choice_active = program.draw_first
        try:
            choice = chooser(view, options)
            if not isinstance(choice, DiscardDrawOption) or choice not in options:
                raise ValueError("discard/Draw chooser must return one listed option")
            if (
                tuple(player.hand) != hand_objects
                or tuple(player.library) != library_objects
                or tuple(player.graveyard) != graveyard_objects
            ):
                raise ValueError("discard/Draw choice mutated authoritative zones")
            if program.draw_first and (
                self._objects != registry
                or any(
                    vars(obj) != state or obj.card is not state["card"] for obj, state in anchors
                )
                or any(not self.is_authoritative(obj, "hand") for obj in hand_objects)
            ):
                raise ValueError("discard/Draw choice changed authoritative identity")
        except Exception:
            player.hand[:] = hand_objects
            player.library[:] = library_objects
            player.graveyard[:] = graveyard_objects
            if program.draw_first:
                self._objects.clear()
                self._objects.update(registry)
                for obj, state in anchors:
                    vars(obj).clear()
                    vars(obj).update(state)
            raise
        finally:
            self._mandatory_discard_choice_active = False
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
        if not isinstance(plan, DiscardDrawPlan) or not program.executable or program.draw_first:
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

    def _validate_etb_draw_discard_trigger(self, ability: TriggeredAbilityObject) -> None:
        if not self._priority_resolution_in_progress and (
            self.priority_state is None or not self.priority_state.resolution_pending
        ):
            raise ValueError("ETB Draw/discard requires Priority resolution")
        anchor = self._draw_discard_anchors.get(ability.object_id)
        if anchor is None:
            raise ValueError("ETB Draw/discard lacks Stack provenance")
        original, trigger, source, card = anchor
        self._authenticate_original_rules_event(ability.event)
        if (
            ability is not original
            or self._objects.get(ability.object_id) is not ability
            or self._triggers.get(ability.trigger_id) is not trigger
            or self._objects.get(trigger.source_id) is not source
            or source.card is not card
            or source.object_id != trigger.source_id
            or source.zone not in {"battlefield", "former"}
            or ability.source_card is not card
            or ability.source_id != trigger.source_id
            or ability.controller != trigger.controller
            or ability.oracle_fragment != trigger.oracle_fragment
            or ability.effect is not TriggerEffect.ETB_DRAW_DISCARD
            or ability.event is not trigger.event
            or self._rules_events.get(trigger.event.event_id) is not trigger.event
            or ability.trigger_id in self._draw_discard_consumed
            or self.interpreter.etb_draw_discard_semantic_coverage(card, ability.oracle_fragment)
            is None
        ):
            raise ValueError("ETB Draw/discard trigger provenance is invalid or consumed")

    def _resolve_etb_draw_discard(self, ability: TriggeredAbilityObject) -> None:
        self._validate_etb_draw_discard_trigger(ability)
        if ability.zone != "former":
            raise ValueError("ETB Draw/discard requires Priority resolution")
        self._draw_discard_consumed.add(ability.trigger_id)
        semantics = self.interpreter.etb_draw_discard_semantic_coverage(
            ability.source_card, ability.oracle_fragment
        )
        assert semantics is not None
        player = self.players[ability.controller]
        hand_before = tuple(obj.object_id for obj in player.hand)
        library_before = tuple(obj.object_id for obj in player.library)
        graveyard_before = tuple(obj.object_id for obj in player.graveyard)
        start_cursor = len(self.events)
        draw_succeeded = self.draw(player, 1)
        drawn_id = player.hand[-1].object_id if draw_succeeded else None
        plan = self.choose_discard_draw(ability.controller, semantics.program)
        discarded_id = None
        if plan.selected is not None:
            discarded = self.move_object(plan.selected, "graveyard", reason="mandatory_discard")
            discarded_id = discarded.object_id
        self.log(
            "etb_draw_discard_committed",
            event_id=ability.event.event_id,
            trigger_id=ability.trigger_id,
            stack_object_id=ability.object_id,
            source_id=ability.source_id,
            controller=ability.controller,
            oracle_fragment=ability.oracle_fragment,
            start_event_cursor=start_cursor,
            pre_hand_ids=list(hand_before),
            pre_library_ids=list(library_before),
            pre_graveyard_ids=list(graveyard_before),
            draw_succeeded=draw_succeeded,
            drawn_library_id=library_before[-1] if library_before else None,
            drawn_hand_id=drawn_id,
            post_draw_hand_ids=list(plan.pre_hand_ids),
            offered_choice_ids=list(plan.offered_choice_ids),
            selected_hand_id=plan.choice.card_id,
            discarded_graveyard_id=discarded_id,
            post_hand_ids=[obj.object_id for obj in player.hand],
            post_library_ids=[obj.object_id for obj in player.library],
            post_graveyard_ids=[obj.object_id for obj in player.graveyard],
            failed_draw_pending=player.failed_draw_pending,
        )

    def _validate_combat_draw_discard_trigger(self, ability: TriggeredAbilityObject) -> None:
        if not self._priority_resolution_in_progress and (
            self.priority_state is None or not self.priority_state.resolution_pending
        ):
            raise ValueError("combat Draw/discard requires Priority resolution")
        anchor = self._combat_draw_discard_anchors.get(ability.object_id)
        if anchor is None:
            raise ValueError("combat Draw/discard lacks Stack provenance")
        original, trigger, source, card = anchor
        event = ability.event
        self._authenticate_original_rules_event(event)
        if (
            ability is not original
            or self._objects.get(ability.object_id) is not ability
            or self._triggers.get(ability.trigger_id) is not trigger
            or self._objects.get(trigger.source_id) is not source
            or source.card is not card
            or source.zone not in {"battlefield", "former"}
            or ability.source_card is not card
            or ability.source_id != source.object_id
            or ability.controller != trigger.controller
            or ability.oracle_fragment != trigger.oracle_fragment
            or ability.effect is not TriggerEffect.COMBAT_DAMAGE_DRAW_DISCARD
            or event is not trigger.event
            or self._rules_events.get(event.event_id) is not event
            or event.kind is not RulesEventKind.COMBAT_DAMAGE_TO_PLAYER
            or event.source_id != source.object_id
            or event.subject_ids != (source.object_id,)
            or event.player_index != ability.controller
            or event.target_player != 1 - ability.controller
            or event.amount is None
            or event.amount <= 0
            or ability.trigger_id in self._combat_draw_discard_consumed
            or self.interpreter.combat_damage_draw_discard_semantic_coverage(
                card, ability.oracle_fragment
            )
            is None
        ):
            raise ValueError("combat Draw/discard trigger provenance is invalid or consumed")

    def _resolve_combat_draw_discard(self, ability: TriggeredAbilityObject) -> None:
        self._validate_combat_draw_discard_trigger(ability)
        if ability.zone != "former":
            raise ValueError("combat Draw/discard requires Priority resolution")
        self._combat_draw_discard_consumed.add(ability.trigger_id)
        amount = ability.event.amount
        assert amount is not None and amount > 0
        player = self.players[ability.controller]
        hand_before = tuple(card.object_id for card in player.hand)
        library_before = tuple(card.object_id for card in player.library)
        graveyard_before = tuple(card.object_id for card in player.graveyard)
        cursor = len(self.events)
        draw_succeeded = self.draw(player, amount)
        plan = self.choose_discard_draw(
            ability.controller, DiscardDrawProgram(1, amount, False, False, draw_first=True)
        )
        discarded_id = None
        if plan.selected is not None:
            discarded_id = self.move_object(
                plan.selected, "graveyard", reason="mandatory_discard"
            ).object_id
        self.log(
            "combat_draw_discard_committed",
            event_id=ability.event.event_id,
            trigger_id=ability.trigger_id,
            stack_object_id=ability.object_id,
            source_id=ability.source_id,
            controller=ability.controller,
            target_player=ability.event.target_player,
            damage=amount,
            oracle_fragment=ability.oracle_fragment,
            start_event_cursor=cursor,
            pre_hand_ids=list(hand_before),
            pre_library_ids=list(library_before),
            pre_graveyard_ids=list(graveyard_before),
            draw_succeeded=draw_succeeded,
            drawn_count=len(library_before) - len(player.library),
            post_draw_hand_ids=list(plan.pre_hand_ids),
            offered_choice_ids=list(plan.offered_choice_ids),
            selected_hand_id=plan.choice.card_id,
            discarded_graveyard_id=discarded_id,
            post_hand_ids=[card.object_id for card in player.hand],
            post_library_ids=[card.object_id for card in player.library],
            post_graveyard_ids=[card.object_id for card in player.graveyard],
            failed_draw_pending=player.failed_draw_pending,
        )

    def _resolve_etb_mill_draw_discard(self, ability: TriggeredAbilityObject) -> None:
        anchor = self._mill_draw_discard_anchors.get(ability.object_id)
        semantics = self.interpreter.etb_mill_draw_discard_semantic_coverage(
            ability.source_card, ability.oracle_fragment
        )
        if (
            anchor is None
            or ability.zone != "former"
            or ability.trigger_id in self._mill_draw_discard_consumed
            or semantics is None
            or not semantics.coverage.fully_supported
        ):
            raise ValueError("ETB mill/draw/discard trigger provenance is invalid or consumed")
        source, trigger = anchor
        if source.card is not ability.source_card or trigger.event is not ability.event:
            raise ValueError("ETB mill/draw/discard source was relinked")
        self._mill_draw_discard_consumed.add(ability.trigger_id)
        player = self.players[ability.controller]
        library_before = tuple(card.object_id for card in player.library)
        hand_before = tuple(card.object_id for card in player.hand)
        graveyard_before = tuple(card.object_id for card in player.graveyard)
        milled = []
        for _ in range(min(semantics.program.mill_quantity, len(player.library))):
            moved = self.move_object(player.library[-1], "graveyard", reason="etb_mill")
            milled.append(moved.object_id)
        draw_count = semantics.program.draw_quantity or 0
        draw_succeeded = self.draw(player, draw_count)
        discard_count = min(semantics.program.discard_quantity or 0, len(player.hand))
        discarded = []
        for card in tuple(player.hand[:discard_count]):
            moved = self.move_object(card, "graveyard", reason="etb_mandatory_discard")
            discarded.append(moved.object_id)
        self.log(
            "etb_mill_draw_discard_committed",
            event_id=ability.event.event_id,
            trigger_id=ability.trigger_id,
            stack_object_id=ability.object_id,
            source_id=ability.source_id,
            controller=ability.controller,
            oracle_fragment=ability.oracle_fragment,
            library_before=list(library_before),
            hand_before=list(hand_before),
            graveyard_before=list(graveyard_before),
            milled_ids=milled,
            draw_count=draw_count,
            draw_succeeded=draw_succeeded,
            discarded_ids=discarded,
            library_after=[card.object_id for card in player.library],
            hand_after=[card.object_id for card in player.hand],
            graveyard_after=[card.object_id for card in player.graveyard],
        )

    @staticmethod
    def validate_draw_discard_snapshot_evidence(snapshot: dict[str, object]) -> None:
        """Reconstruct the bounded ETB transaction from independent event records."""
        events = snapshot.get("events", [])
        committed = [
            (i, e) for i, e in enumerate(events) if e.get("event") == "etb_draw_discard_committed"
        ]
        resolutions = [
            e
            for e in events
            if e.get("event") == "trigger_resolved" and e.get("effect") == "etb_draw_discard"
        ]
        if len(committed) != len(resolutions):
            raise ValueError("ETB Draw/discard evidence lacks a unique resolution")
        seen = set()
        for cursor, item in committed:
            try:
                stack_id = item["stack_object_id"]
                assert stack_id not in seen
                seen.add(stack_id)
                source_id, event_id = item["source_id"], item["event_id"]
                controller = item["controller"]
                assert controller in (0, 1)
                entry = [
                    (i, e)
                    for i, e in enumerate(events[:cursor])
                    if e.get("event") == "rules_event" and e.get("event_id") == event_id
                ]
                assert len(entry) == 1
                entry_cursor, entry_event = entry[0]
                assert entry_event["rules_event"] == "creature_entered"
                assert entry_event["subject_ids"] == [source_id]
                assert {"object_id": source_id, "controller": controller} in entry_event[
                    "battlefield_authority"
                ]
                pending = [
                    (i, e)
                    for i, e in enumerate(events[:cursor])
                    if e.get("event") == "trigger_pending"
                    and e.get("trigger_id") == item["trigger_id"]
                ]
                stacked = [
                    (i, e)
                    for i, e in enumerate(events[:cursor])
                    if e.get("event") == "trigger_stacked" and e.get("stack_object_id") == stack_id
                ]
                permitted = [
                    (i, e)
                    for i, e in enumerate(events[:cursor])
                    if e.get("event") == "stack_resolution_permitted"
                    and e.get("stack_object_id") == stack_id
                ]
                resolved = [
                    (i, e)
                    for i, e in enumerate(events)
                    if e.get("event") == "trigger_resolved" and e.get("stack_object_id") == stack_id
                ]
                assert len(pending) == len(stacked) == len(permitted) == len(resolved) == 1
                pending_cursor, pending_event = pending[0]
                stacked_cursor, stacked_event = stacked[0]
                permitted_cursor, permission = permitted[0]
                resolved_cursor, resolution = resolved[0]
                assert pending_event["event_id"] == stacked_event["event_id"] == event_id
                assert stacked_event["trigger_id"] == item["trigger_id"]
                assert pending_event["oracle_fragment"] == item["oracle_fragment"]
                assert (
                    pending_event["controller"]
                    == stacked_event["controller"]
                    == entry_event["player"]
                )
                assert resolution["event_id"] == event_id and resolution["source_id"] == source_id
                assert resolution["trigger_id"] == item["trigger_id"]
                assert resolution["oracle_fragment"] == item["oracle_fragment"]
                assert resolution["effect"] == "etb_draw_discard"
                start = item["start_event_cursor"]
                assert (
                    entry_cursor
                    < pending_cursor
                    < stacked_cursor
                    < permitted_cursor
                    < start
                    <= cursor
                    < resolved_cursor
                )
                passes = [
                    e
                    for e in events[stacked_cursor:permitted_cursor]
                    if e.get("event") == "priority_passed"
                    and e.get("priority_epoch") == permission["priority_epoch"]
                ]
                assert len(passes) >= 2 and passes[-1]["resolution_pending"] is True
                assert {passes[-1]["player_index"], passes[-2]["player_index"]} == {0, 1}
                steps = events[start:cursor]
                before_hand = item["pre_hand_ids"]
                before_library = item["pre_library_ids"]
                before_graveyard = item["pre_graveyard_ids"]
                assert len(set(before_hand + before_library + before_graveyard)) == len(
                    before_hand + before_library + before_graveyard
                )
                if before_library:
                    assert item["draw_succeeded"] is True
                    assert item["drawn_library_id"] == before_library[-1]
                    drawn = item["drawn_hand_id"]
                    assert drawn and drawn not in before_hand + before_library + before_graveyard
                    assert steps[0]["event"] == "zone_changed" and steps[0]["reason"] == "draw"
                    assert steps[0]["source_object_id"] == before_library[-1]
                    assert steps[0]["destination_object_id"] == drawn
                    assert (
                        steps[0]["source_zone"] == "library"
                        and steps[0]["destination_zone"] == "hand"
                    )
                    assert steps[1]["event"] == "card_drawn"
                    assert steps[1]["player"] == entry_event["player"]
                    post_draw = before_hand + [drawn]
                    assert item["post_library_ids"] == before_library[:-1]
                    draw_end = 2
                else:
                    assert item["draw_succeeded"] is False
                    assert item["drawn_library_id"] is None and item["drawn_hand_id"] is None
                    assert steps[0]["event"] == "draw_failed"
                    assert steps[0]["player"] == entry_event["player"]
                    assert steps[0]["state_based_action_pending"] is True
                    assert item["failed_draw_pending"] is True
                    assert item["post_library_ids"] == []
                    post_draw = before_hand
                    draw_end = 1
                assert item["post_draw_hand_ids"] == post_draw
                selected, discarded = item["selected_hand_id"], item["discarded_graveyard_id"]
                if post_draw:
                    assert item["offered_choice_ids"] == post_draw and selected in post_draw
                    assert (
                        discarded
                        and discarded
                        not in before_hand + before_library + before_graveyard + post_draw
                    )
                    movement = steps[draw_end]
                    assert (
                        movement["event"] == "zone_changed"
                        and movement["reason"] == "mandatory_discard"
                    )
                    assert (
                        movement["source_zone"] == "hand"
                        and movement["destination_zone"] == "graveyard"
                    )
                    assert (
                        movement["source_object_id"] == selected
                        and movement["destination_object_id"] == discarded
                    )
                    assert item["post_hand_ids"] == [x for x in post_draw if x != selected]
                    assert item["post_graveyard_ids"] == before_graveyard + [discarded]
                    assert len(steps) == draw_end + 1
                else:
                    assert selected is None and discarded is None
                    assert item["offered_choice_ids"] == [None]
                    assert item["post_hand_ids"] == []
                    assert item["post_graveyard_ids"] == before_graveyard
                    assert len(steps) == draw_end
            except (AssertionError, KeyError, IndexError, TypeError) as error:
                raise ValueError("ETB Draw/discard evidence does not reconstruct") from error

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
            or (
                event.subject_ids.count(trigger.source_id) != 1
                and not (
                    "Class" in trigger.source_card.type_line
                    and event.subject_ids
                    and trigger.oracle_fragment.startswith("Whenever you attack,")
                )
            )
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
        view = ScryViewV2(
            player_index,
            program.amount,
            tuple((card.object_id, card.card.name) for card in inspected),
            decision_context(self, player_index),
            tuple(describe_card(card.object_id, card.card) for card in inspected),
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

    def _validate_controlled_creature_departure_loss(
        self,
        *,
        controller: int,
        source_id: str,
        source_card: CardFact,
        oracle_fragment: str,
        event: RulesEvent,
        trigger_id: str | None = None,
    ) -> int:
        """Join a controlled creature's exit and a pre-exit watching permanent."""
        self._authenticate_original_rules_event(event)
        match = self.interpreter.CONTROLLED_CREATURE_LEFT_OPPONENT_LOSS.fullmatch(oracle_fragment)
        departed_id = event.subject_ids[0] if len(event.subject_ids) == 1 else None
        source = self._objects.get(source_id)
        last_known = {item[0]: item for item in event.last_known_battlefield}
        departed = last_known.get(departed_id or "")
        watcher = last_known.get(source_id)
        records = [
            item
            for item in self.events
            if item.get("event") == "permanent_departed"
            and item.get("source_object_id") == departed_id
        ]
        trigger = None if trigger_id is None else self._triggers.get(trigger_id)
        if (
            match is None
            or event.kind is not RulesEventKind.PERMANENT_LEFT
            or self._rules_events.get(event.event_id) is not event
            or event.source_id != departed_id
            or departed is None
            or not departed[3]
            or departed[1] != controller
            or watcher is None
            or watcher[1] != controller
            or event.player_index != controller
            or (source_id, controller) not in event.battlefield_authority
            or len(records) != 1
            or records[0]["controller"] != controller
            or records[0]["turn"] != event.turn
            or not isinstance(source, Permanent)
            or source.card is not source_card
            or source.zone not in {"battlefield", "former"}
            or oracle_fragment not in self.interpreter.fragments(source.card)
            or (
                trigger_id is not None
                and (
                    trigger is None
                    or trigger.controller != controller
                    or trigger.source_id != source_id
                    or trigger.source_card is not source_card
                    or trigger.oracle_fragment != oracle_fragment
                    or trigger.effect is not TriggerEffect.CONTROLLED_CREATURE_LEFT_OPPONENT_LOSS
                    or trigger.event is not event
                )
            )
        ):
            raise ValueError("controlled creature departure trigger provenance is invalid")
        return int(match["amount"])

    def _validate_countered_creature_departure_life(
        self,
        event: RulesEvent,
        source_id: str,
        source_card: CardFact,
        fragment: str,
        controller: int,
        *,
        trigger_id: str | None = None,
    ) -> int:
        """Bind a countered creature's last-known state to its watcher and exit."""
        self._authenticate_original_rules_event(event)
        amount = self.interpreter.countered_creature_left_life(source_card, fragment)
        anchor = self._countered_departure_anchors.get(event.event_id)
        departed_id = event.subject_ids[0] if len(event.subject_ids) == 1 else None
        departed_lki = next(
            (record for record in event.last_known_battlefield if record[0] == departed_id),
            None,
        )
        source_lki = next(
            (record for record in event.last_known_battlefield if record[0] == source_id),
            None,
        )
        source = self._objects.get(source_id)
        trigger = self._triggers.get(trigger_id) if trigger_id is not None else None
        if anchor is None:
            raise ValueError("countered departure lacks frozen leave history")
        departed, counters, original_departure, watchers = anchor
        matches = [
            record
            for record in self.events
            if record.get("event") == "permanent_departed"
            and record.get("source_object_id") == departed_id
        ]
        if (
            amount is None
            or event.kind is not RulesEventKind.PERMANENT_LEFT
            or event.source_id != departed_id
            or event.player_index != controller
            or departed_id is None
            or departed is not self._objects.get(departed_id)
            or not isinstance(departed, Permanent)
            or departed.zone != "former"
            or not counters
            or tuple(sorted((kind, n) for kind, n in departed.counters.items() if n > 0))
            != counters
            or departed_lki is None
            or not departed_lki[3]
            or departed_lki[1] != controller
            or source_lki is None
            or source_lki[1] != controller
            or (departed_id, controller) not in event.battlefield_authority
            or (source_id, controller) not in event.battlefield_authority
            or not isinstance(source, Permanent)
            or source.card is not source_card
            or source.zone not in {"battlefield", "former"}
            or not any(
                watcher_id == source_id
                and watcher_controller == controller
                and watcher_fragment == fragment
                and (level is None or level >= 2)
                for watcher_id, watcher_controller, level, watcher_fragment in watchers
            )
            or len(matches) != 1
            or tuple(matches[0].items()) != original_departure
            or matches[0].get("counter_snapshot") != [list(counter) for counter in counters]
            or (
                trigger_id is not None
                and (
                    trigger is None
                    or trigger.effect is not TriggerEffect.CONTROLLED_COUNTERED_CREATURE_LEFT_LIFE
                    or trigger.source_id != source_id
                    or trigger.source_card is not source_card
                    or trigger.controller != controller
                    or trigger.oracle_fragment != fragment
                    or trigger.event is not event
                )
            )
        ):
            raise ValueError("countered creature departure has invalid event provenance")
        return amount

    def _validate_artifact_counter_transfer(
        self,
        event: RulesEvent,
        source_id: str,
        source_card: CardFact,
        fragment: str,
        controller: int,
        *,
        trigger_id: str | None = None,
    ) -> tuple[tuple[str, int], ...]:
        """Authenticate a countered artifact's departure-time state and watcher."""
        self._authenticate_original_rules_event(event)
        anchor = self._artifact_counter_departures.get(event.event_id)
        if anchor is None:
            raise ValueError("artifact counter transfer lacks departure snapshot")
        departed, counters, original_departure, watchers = anchor
        departed_id = event.subject_ids[0] if len(event.subject_ids) == 1 else None
        source = self._objects.get(source_id)
        departure_records = [
            record
            for record in self.events
            if record.get("event") == "permanent_departed"
            and record.get("source_object_id") == departed_id
        ]
        trigger = self._triggers.get(trigger_id) if trigger_id is not None else None
        if (
            not self.interpreter.controlled_artifact_counter_transfer(source_card, fragment)
            or event.kind is not RulesEventKind.PERMANENT_LEFT
            or event.source_id != departed_id
            or event.player_index != controller
            or departed_id is None
            or departed is not self._objects.get(departed_id)
            or not isinstance(departed, Permanent)
            or departed.zone != "former"
            or not counters
            or tuple(sorted((kind, n) for kind, n in departed.counters.items() if n > 0))
            != counters
            or not any(
                item[0] == departed_id
                and item[1] == controller
                and "Artifact" in item[2].split(" â€” ", 1)[0].split()
                for item in event.last_known_battlefield
            )
            or (departed_id, controller) not in event.battlefield_authority
            or (source_id, controller) not in event.battlefield_authority
            or not isinstance(source, Permanent)
            or source.card is not source_card
            or source.zone not in {"battlefield", "former"}
            or (source_id, controller, fragment) not in watchers
            or len(departure_records) != 1
            or tuple(departure_records[0].items()) != original_departure
            or departure_records[0].get("counter_snapshot")
            != [list(counter) for counter in counters]
            or (
                trigger_id is not None
                and (
                    trigger is None
                    or trigger.effect is not TriggerEffect.CONTROLLED_ARTIFACT_COUNTER_TRANSFER
                    or trigger.source_id != source_id
                    or trigger.source_card is not source_card
                    or trigger.controller != controller
                    or trigger.oracle_fragment != fragment
                    or trigger.event is not event
                )
            )
        ):
            raise ValueError("artifact counter transfer has invalid event provenance")
        return counters

    def _paramecia_fragment(self, card: CardFact) -> str | None:
        target = (
            "When this creature dies, you may exile it. When you do, put target creature card "
            "from your graveyard on top of your library."
        )
        return next(
            (fragment for fragment in self.interpreter.fragments(card) if fragment == target), None
        )

    def _validate_artifact_token_trigger(
        self, event: RulesEvent, source: Permanent, fragment: str, controller: int
    ) -> None:
        """Bind a parsed token effect to an actual cast or self-zone event."""
        self._authenticate_original_rules_event(event)
        context = self.interpreter.entry_leave_or_artifact_cast_token_context(source.card, fragment)
        coverage = self.interpreter.token_semantic_coverage(source.card, fragment)
        if (
            context is None
            or coverage is None
            or not coverage.fully_supported
            or self._objects.get(source.object_id) is not source
            or fragment not in self.interpreter.fragments(source.rules_card)
            or (source.object_id, controller) not in event.battlefield_authority
            or event.player_index != controller
        ):
            raise ValueError("artifact token trigger lacks source or Oracle provenance")
        if context == "entry_or_leave":
            if event.kind in {RulesEventKind.CREATURE_ENTERED, RulesEventKind.PERMANENT_ENTERED}:
                valid = event.subject_ids == (source.object_id,)
            else:
                valid = (
                    event.kind is RulesEventKind.PERMANENT_LEFT
                    and event.subject_ids == (source.object_id,)
                    and event.source_id == source.object_id
                    and any(
                        item[0] == source.object_id and item[1] == controller
                        for item in event.last_known_battlefield
                    )
                )
        else:
            spell = self._objects.get(event.source_id)
            valid = (
                event.kind is RulesEventKind.SPELL_CAST
                and event.subject_ids == (event.source_id,)
                and isinstance(spell, StackObject)
                and "Artifact" in spell.card.type_line.split(" â€” ", 1)[0].split()
                and any(
                    record["event"] == "spell_cast"
                    and record.get("stack_object_id") == spell.object_id
                    and record.get("player") == self.players[controller].name
                    for record in self.events
                )
            )
        if not valid:
            raise ValueError("artifact token trigger has invalid cast or zone provenance")

    def _enqueue_spell_cast_triggers(self, spell: StackObject) -> None:
        """Deliver spell-cast triggers after complete announcement, before priority."""
        if not self.is_authoritative(spell, "stack"):
            raise ValueError("cast event requires an authoritative spell")
        event = self._new_rules_event(
            RulesEventKind.SPELL_CAST,
            spell.controller,
            (spell.object_id,),
            source_id=spell.object_id,
        )
        for source in tuple(self.players[spell.controller].battlefield):
            for fragment in self.interpreter.fragments(source.rules_card):
                if (
                    "Artifact" in spell.card.type_line.split(" â€” ", 1)[0].split()
                    and self.interpreter.entry_leave_or_artifact_cast_token_context(
                        source.card, fragment
                    )
                    == "artifact_cast"
                    and (
                        coverage := self.interpreter.token_semantic_coverage(source.card, fragment)
                    )
                    is not None
                    and coverage.fully_supported
                ):
                    self._enqueue_trigger(event, source, fragment, TriggerEffect.CREATE_TOKEN)
                if (
                    source.class_level is not None
                    and source.class_level >= 3
                    and (
                        source.ability_loss_timestamp is None
                        or source.class_level_timestamp > source.ability_loss_timestamp
                    )
                    and self.interpreter.class_spell_cast_team_counter(source.card, fragment)
                ):
                    self._enqueue_trigger(
                        event, source, fragment, TriggerEffect.CLASS_SPELL_CAST_TEAM_COUNTER
                    )
        self._put_pending_triggers_on_stack()

    def _validate_class_spell_cast_team_counter(
        self,
        ability: TriggeredAbilityObject | None,
        event: RulesEvent,
        source: Permanent,
        fragment: str,
        controller: int,
    ) -> None:
        self._authenticate_original_rules_event(event)
        spell = self._objects.get(event.source_id or "")
        if (
            event.kind is not RulesEventKind.SPELL_CAST
            or event.subject_ids != (event.source_id,)
            or event.player_index != controller
            or not isinstance(spell, StackObject)
            or spell.controller != controller
            or (ability is None and source.controller != controller)
            or (source.object_id, controller) not in event.battlefield_authority
            or (ability is None and (source.class_level is None or source.class_level < 3))
            or (
                ability is None
                and source.ability_loss_timestamp is not None
                and source.class_level_timestamp <= source.ability_loss_timestamp
            )
            or not self.interpreter.class_spell_cast_team_counter(source.card, fragment)
            or source.zone not in {"battlefield", "former"}
            or self._objects.get(source.object_id) is not source
            or not any(
                record["event"] == "spell_cast"
                and record.get("stack_object_id") == spell.object_id
                and record.get("player_index") == controller
                for record in self.events
            )
            or (
                ability is not None
                and (
                    (trigger := self._triggers.get(ability.trigger_id)) is None
                    or trigger.event is not event
                    or trigger.effect is not TriggerEffect.CLASS_SPELL_CAST_TEAM_COUNTER
                    or trigger.source_id != source.object_id
                    or trigger.source_card is not source.card
                    or trigger.controller != controller
                    or trigger.oracle_fragment != fragment
                    or ability.source_id != source.object_id
                    or ability.source_card is not source.card
                    or ability.controller != controller
                    or ability.oracle_fragment != fragment
                )
            )
        ):
            raise ValueError("Class spell-cast trigger has invalid provenance")

    def _validate_damage_to_self_mana(
        self,
        event: RulesEvent,
        source_id: str,
        source_card: CardFact,
        fragment: str,
        controller: int,
        *,
        trigger_id: str | None = None,
    ) -> tuple[str, int]:
        """Bind dealt damage to its original recipient and printed retained-mana trigger."""
        self._authenticate_original_rules_event(event)
        recipient_id = (
            event.subject_ids[0]
            if event.kind is RulesEventKind.DAMAGE_DEALT and len(event.subject_ids) == 1
            else event.subject_ids[1]
            if event.kind is RulesEventKind.COMBAT_DAMAGE_TO_CREATURE
            and len(event.subject_ids) == 2
            else None
        )
        source = self._objects.get(source_id)
        trigger = self._triggers.get(trigger_id) if trigger_id is not None else None
        color = self.interpreter.damage_to_self_mana(source_card, fragment)
        if (
            color is None
            or recipient_id != source_id
            or event.source_id is None
            or event.source_id not in self._objects
            or event.target_player is not None
            or not isinstance(event.amount, int)
            or isinstance(event.amount, bool)
            or event.amount <= 0
            or (source_id, controller) not in event.battlefield_authority
            or not isinstance(source, Permanent)
            or source.card is not source_card
            or source.zone not in {"battlefield", "former"}
            or (
                trigger_id is not None
                and (
                    trigger is None
                    or trigger.effect is not TriggerEffect.DAMAGE_TO_SELF_MANA
                    or trigger.event is not event
                    or trigger.source_id != source_id
                    or trigger.source_card is not source_card
                    or trigger.controller != controller
                    or trigger.oracle_fragment != fragment
                )
            )
        ):
            raise ValueError("damage-to-self mana trigger has invalid event provenance")
        return color, event.amount

    def _enqueue_damage_to_self_mana(self, event: RulesEvent, recipient: Permanent) -> None:
        """Detect printed self-damage abilities before state-based departures."""
        for fragment in self.interpreter.fragments(recipient.rules_card):
            if self.interpreter.damage_to_self_mana(recipient.card, fragment) is not None:
                self._enqueue_trigger(event, recipient, fragment, TriggerEffect.DAMAGE_TO_SELF_MANA)

    def _validate_granted_death_return(
        self,
        event: RulesEvent,
        source: Permanent,
        fragment: str,
        controller: int,
        *,
        trigger_id: str | None = None,
    ) -> CardObject:
        """Bind a granted death ability to the exact battlefield-to-graveyard move."""
        self._authenticate_original_rules_event(event)
        grants = tuple(
            grant
            for grant in source.temporary_death_return_effects
            if grant.oracle_fragment == fragment
            and (
                source.ability_loss_timestamp is None
                or grant.timestamp > source.ability_loss_timestamp
            )
            and isinstance(self._objects.get(grant.source_id), StackObject)
            and self.interpreter.temporary_death_return_grant_program(
                self._objects[grant.source_id].card
            )
            is not None
            and any(
                record.get("event") == "temporary_death_return_granted"
                and record.get("stack_object_id") == grant.source_id
                and record.get("target_id") == source.object_id
                and record.get("oracle_fragment") == fragment
                for record in self.events
            )
        )
        moves = tuple(
            record
            for record in self.events
            if record.get("event") == "zone_changed"
            and record.get("source_object_id") == source.object_id
            and record.get("source_zone") == "battlefield"
            and record.get("destination_zone") == "graveyard"
        )
        destination = (
            self._objects.get(moves[0]["destination_object_id"]) if len(moves) == 1 else None
        )
        trigger = self._triggers.get(trigger_id) if trigger_id is not None else None
        if (
            event.kind is not RulesEventKind.CREATURE_DIED
            or self._rules_events.get(event.event_id) is not event
            or event.source_id != source.object_id
            or event.subject_ids != (source.object_id,)
            or event.player_index != controller
            or (source.object_id, controller) not in event.battlefield_authority
            or len(event.last_known_battlefield) != 1
            or event.last_known_battlefield[0][:2] != (source.object_id, controller)
            or event.last_known_battlefield[0][3] is not True
            or source.zone != "former"
            or source.controller != controller
            or not grants
            or not isinstance(destination, CardObject)
            or destination.card is not source.card
            or (
                trigger_id is not None
                and (
                    trigger is None
                    or trigger.effect is not TriggerEffect.GRANTED_DIES_RETURN
                    or trigger.event is not event
                    or trigger.source_id != source.object_id
                    or trigger.source_card is not source.card
                    or trigger.controller != controller
                    or trigger.oracle_fragment != fragment
                )
            )
        ):
            raise ValueError("granted death return lacks authenticated departure provenance")
        return destination

    def _enqueue_trigger(
        self,
        event: RulesEvent,
        source: Permanent,
        fragment: str,
        effect: TriggerEffect,
        *,
        grant_source: Permanent | None = None,
    ) -> None:
        if effect is TriggerEffect.GRANTED_DIES_RETURN:
            self._validate_granted_death_return(event, source, fragment, source.controller)
        if effect is TriggerEffect.ATTACK_TARGET_COUNTER:
            self._authenticate_original_rules_event(event)
            if (
                event.kind is not RulesEventKind.ATTACKERS_DECLARED
                or event.player_index != source.controller
                or not event.subject_ids
                or event.subject_ids != self._combat_attackers
                or (source.object_id, source.controller) not in event.battlefield_authority
                or not self.is_authoritative(source, "battlefield")
                or fragment not in self.interpreter.fragments(source.rules_card)
                or not self.interpreter.attack_target_counter(source.card, fragment)
            ):
                raise ValueError("attack counter trigger lacks attack provenance")
        if effect is TriggerEffect.COMBAT_DAMAGE_ARTIFACT_COPY:
            self._authenticate_original_rules_event(event)
            if (
                event.kind is not RulesEventKind.COMBAT_DAMAGE_TO_PLAYER
                or event.source_id != source.object_id
                or event.subject_ids != (source.object_id,)
                or event.player_index != source.controller
                or event.target_player != 1 - source.controller
                or event.amount is None
                or event.amount <= 0
                or not self.is_authoritative(source, "battlefield")
                or (source.object_id, source.controller) not in event.battlefield_authority
                or fragment not in self.interpreter.fragments(source.rules_card)
                or not self.interpreter.combat_damage_artifact_copy(source.card, fragment)
            ):
                raise ValueError("artifact copy trigger lacks combat-damage provenance")
        if (
            effect is TriggerEffect.CREATE_TOKEN
            and self.interpreter.entry_leave_or_artifact_cast_token_context(source.card, fragment)
            is not None
        ):
            self._validate_artifact_token_trigger(event, source, fragment, source.controller)
        if effect is TriggerEffect.GRANTED_COMBAT_UNTAP_GAIN:
            self._authenticate_original_rules_event(event)
            if (
                grant_source is None
                or not self.is_authoritative(source, "battlefield")
                or not self.is_authoritative(grant_source, "battlefield")
                or grant_source.attached_to != source.object_id
                or "Equipment" not in grant_source.type_line
                or (
                    source.ability_loss_timestamp is not None
                    and grant_source.attachment_timestamp <= source.ability_loss_timestamp
                )
                or event.kind
                not in {
                    RulesEventKind.COMBAT_DAMAGE_TO_PLAYER,
                    RulesEventKind.COMBAT_DAMAGE_TO_CREATURE,
                }
                or not event.subject_ids
                or event.subject_ids[0] != source.object_id
                or event.source_id != source.object_id
                or event.player_index != source.controller
                or (
                    event.target_player != 1 - source.controller
                    if event.kind is RulesEventKind.COMBAT_DAMAGE_TO_PLAYER
                    else event.target_player is not None or len(event.subject_ids) != 2
                )
                or (source.object_id, source.controller) not in event.battlefield_authority
                or (grant_source.object_id, grant_source.controller)
                not in event.battlefield_authority
                or event.amount is None
                or event.amount <= 0
                or fragment not in self.interpreter.fragments(grant_source.rules_card)
                or self.interpreter.equipment_granted_combat_semantics(grant_source.card, fragment)
                is None
            ):
                raise ValueError("granted combat trigger lacks damage and attachment provenance")
        elif grant_source is not None:
            raise ValueError("grant source is valid only for a granted combat trigger")
        if effect is TriggerEffect.EQUIPMENT_SUBTYPE_ENTRY_ATTACH:
            self._authenticate_original_rules_event(event)
            subtype = self.interpreter.equipment_subtype_entry_attach(source.card, fragment)
            entering = (
                self._objects.get(event.subject_ids[0]) if len(event.subject_ids) == 1 else None
            )
            if (
                subtype is None
                or not self.is_authoritative(source, "battlefield")
                or event.kind is not RulesEventKind.CREATURE_ENTERED
                or (source.object_id, source.controller) not in event.battlefield_authority
                or event.player_index != source.controller
                or not isinstance(entering, Permanent)
                or not self.is_authoritative(entering, "battlefield")
                or entering.controller != source.controller
                or subtype not in entering.type_line.partition(" â€” ")[2].split()
            ):
                raise ValueError("Equipment subtype entry lacks creature-entry provenance")
        if effect in {
            TriggerEffect.COMBAT_DISCARD_OR_SACRIFICE,
            TriggerEffect.END_STEP_SPELL_TYPES_DRAW,
            TriggerEffect.DISAPPEAR_END_STEP,
            TriggerEffect.RAPHAEL_ALLIANCE_EXILE,
            TriggerEffect.RAPHAEL_ATTACK_PLAY,
        }:
            self._authenticate_original_rules_event(event)
            valid = {
                TriggerEffect.COMBAT_DISCARD_OR_SACRIFICE: (
                    event.kind
                    in {RulesEventKind.ATTACKERS_DECLARED, RulesEventKind.BLOCKERS_DECLARED}
                    and source.object_id in event.subject_ids
                    and self.interpreter.combat_discard_or_sacrifice(source.card, fragment)
                ),
                TriggerEffect.END_STEP_SPELL_TYPES_DRAW: (
                    event.kind is RulesEventKind.END_STEP_BEGAN
                    and event.player_index == source.controller
                    and self.interpreter.end_step_spell_types_draw(fragment)
                ),
                TriggerEffect.DISAPPEAR_END_STEP: (
                    event.kind is RulesEventKind.END_STEP_BEGAN
                    and event.player_index == source.controller
                    and self.interpreter.disappear_end_step(source.rules_card, fragment) is not None
                    and self._left_under_control_this_turn(source.controller)
                ),
                TriggerEffect.RAPHAEL_ALLIANCE_EXILE: (
                    event.kind
                    in {RulesEventKind.CREATURE_ENTERED, RulesEventKind.PERMANENT_ENTERED}
                    and self.interpreter.linked_top_exile(source.card, fragment)
                ),
                TriggerEffect.RAPHAEL_ATTACK_PLAY: (
                    event.kind is RulesEventKind.ATTACKERS_DECLARED
                    and source.object_id in event.subject_ids
                    and self.interpreter.linked_attack_play(source.card, fragment)
                ),
            }[effect]
            if (
                not valid
                or (source.object_id, source.controller) not in event.battlefield_authority
                or not self.is_authoritative(source, "battlefield")
                or fragment not in self.interpreter.fragments(source.rules_card)
            ):
                raise ValueError("combat or end-step trigger has invalid event provenance")
        if effect is TriggerEffect.ETB_ATTACH_EQUIPMENT:
            self._authenticate_original_rules_event(event)
            if (
                event.kind is not RulesEventKind.PERMANENT_ENTERED
                or event.subject_ids != (source.object_id,)
                or (source.object_id, source.controller) not in event.battlefield_authority
                or not self.interpreter.equipment_etb_attach(source.card, fragment)
            ):
                raise ValueError("equipment entry trigger lacks event provenance")
        if effect is TriggerEffect.ETB_ANY_TARGET_DAMAGE:
            self._authenticate_original_rules_event(event)
            if (
                self._rules_events.get(event.event_id) is not event
                or event.kind
                not in {RulesEventKind.PERMANENT_ENTERED, RulesEventKind.CREATURE_ENTERED}
                or event.subject_ids != (source.object_id,)
                or event.player_index != source.controller
                or (source.object_id, source.controller) not in event.battlefield_authority
                or not self.is_authoritative(source, "battlefield")
                or fragment not in self.interpreter.fragments(source.card)
                or self.interpreter.entry_any_target_damage_program(source.card, fragment) is None
            ):
                raise ValueError("entry damage trigger has invalid original event")
        if effect is TriggerEffect.ETB_KRANG_REFILL:
            self._enqueue_krang_refill(event, source, fragment)
            return
        if effect is TriggerEffect.UTILITY_TARGET:
            semantics = self.interpreter.utility_trigger_semantics(source.card, fragment)
            self._authenticate_original_rules_event(event)
            if (
                semantics is None
                or self._rules_events.get(event.event_id) is not event
                or event.subject_ids != (source.object_id,)
                or event.player_index != source.controller
                or (source.object_id, source.controller) not in event.battlefield_authority
                or fragment not in self.interpreter.fragments(source.card)
                or not (
                    event.kind
                    in {RulesEventKind.CREATURE_ENTERED, RulesEventKind.PERMANENT_ENTERED}
                    and semantics[0] in {"entry", "entry_or_leave"}
                    and self.is_authoritative(source, "battlefield")
                    or event.kind is RulesEventKind.PERMANENT_LEFT
                    and semantics[0] == "entry_or_leave"
                    and source.zone == "former"
                    and event.source_id == source.object_id
                )
            ):
                raise ValueError("utility trigger event provenance is invalid")
        if effect is TriggerEffect.ETB_MILL_THREE:
            self._enqueue_mill_three(event, source, fragment)
            return
        if effect is TriggerEffect.ETB_JURY_RIG:
            self._enqueue_jury_rig(event, source, fragment)
            return
        if effect is TriggerEffect.ETB_VIGILANTE:
            self._enqueue_vigilante(event, source, fragment)
            return
        if effect is TriggerEffect.VIGILANTE_DISCARD:
            raise ValueError("Vigilante delayed delivery requires a scheduling record")
        if effect is TriggerEffect.ETB_TAP_STUN and not self.is_authoritative(
            source, "battlefield"
        ):
            raise ValueError("stun source must be an authoritative battlefield incarnation")
        if effect is TriggerEffect.PERMANENT_LEFT_SELF_COUNTER:
            self._validate_permanent_left_counter_provenance(
                controller=source.controller,
                source_id=source.object_id,
                source_card=source.card,
                oracle_fragment=fragment,
                event=event,
            )
        if effect is TriggerEffect.CONTROLLED_CREATURE_LEFT_OPPONENT_LOSS:
            self._validate_controlled_creature_departure_loss(
                controller=source.controller,
                source_id=source.object_id,
                source_card=source.card,
                oracle_fragment=fragment,
                event=event,
            )
        if effect is TriggerEffect.CONTROLLED_COUNTERED_CREATURE_LEFT_LIFE:
            self._validate_countered_creature_departure_life(
                event, source.object_id, source.card, fragment, source.controller
            )
        if effect is TriggerEffect.CONTROLLED_ARTIFACT_COUNTER_TRANSFER:
            self._validate_artifact_counter_transfer(
                event, source.object_id, source.card, fragment, source.controller
            )
        if effect is TriggerEffect.DAMAGE_TO_SELF_MANA:
            self._validate_damage_to_self_mana(
                event, source.object_id, source.card, fragment, source.controller
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
        if effect is TriggerEffect.CONDITIONAL_ENTRY_TOKEN:
            self._authenticate_original_rules_event(event)
            if (
                event.kind is not RulesEventKind.CREATURE_ENTERED
                or event.subject_ids != (source.object_id,)
                or (source.object_id, source.controller) not in event.battlefield_authority
                or not self.is_authoritative(source, "battlefield")
                or not self.interpreter.DISAPPEAR_ETB_TOKEN.fullmatch(fragment)
                or not self._left_under_control_this_turn(source.controller)
            ):
                raise ValueError("conditional entry trigger condition or provenance invalid")
        if effect is TriggerEffect.ETB_FOOD_SEARCH:
            self._authenticate_original_rules_event(event)
            if (
                not self.is_authoritative(source, "battlefield")
                or self._rules_events.get(event.event_id) is not event
                or event.kind is not RulesEventKind.CREATURE_ENTERED
                or event.subject_ids != (source.object_id,)
                or event.player_index != source.controller
                or (source.object_id, source.controller) not in event.battlefield_authority
                or fragment not in self.interpreter.fragments(source.rules_card)
                or self.interpreter.etb_food_search_semantic_coverage(source.card, fragment) is None
            ):
                raise ValueError("ETB Food search entry provenance is invalid")
            key = (source.object_id, fragment)
            if key in self._food_search_sources:
                original_source, original_card = self._food_search_sources[key]
                if original_source is not source or original_card is not source.card:
                    raise ValueError("ETB Food search source was relinked")
                return
            occurrence = self._register_semantic_occurrence(source, source.controller, fragment, ())
            self._witness_from_existing_events(occurrence)
            self._food_search_sources[key] = (source, source.card)
        if effect is TriggerEffect.ETB_DRAW_DISCARD:
            self._authenticate_original_rules_event(event)
            if (
                not self.is_authoritative(source, "battlefield")
                or self._rules_events.get(event.event_id) is not event
                or event.kind is not RulesEventKind.CREATURE_ENTERED
                or event.subject_ids != (source.object_id,)
                or event.player_index != source.controller
                or (source.object_id, source.controller) not in event.battlefield_authority
                or fragment not in self.interpreter.fragments(source.rules_card)
                or self.interpreter.etb_draw_discard_semantic_coverage(source.card, fragment)
                is None
            ):
                raise ValueError("ETB Draw/discard entry provenance is invalid")
            key = (source.object_id, fragment)
            if key in self._draw_discard_sources:
                original_source, original_card = self._draw_discard_sources[key]
                if original_source is not source or original_card is not source.card:
                    raise ValueError("ETB Draw/discard source was relinked")
                return
            occurrence = self._register_semantic_occurrence(source, source.controller, fragment, ())
            self._witness_from_existing_events(occurrence)
            self._draw_discard_sources[key] = (source, source.card)
        if effect is TriggerEffect.COMBAT_DAMAGE_DRAW_DISCARD:
            self._authenticate_original_rules_event(event)
            if (
                not self.is_authoritative(source, "battlefield")
                or self._rules_events.get(event.event_id) is not event
                or event.kind is not RulesEventKind.COMBAT_DAMAGE_TO_PLAYER
                or event.source_id != source.object_id
                or event.subject_ids != (source.object_id,)
                or event.player_index != source.controller
                or event.target_player != 1 - source.controller
                or event.amount is None
                or event.amount <= 0
                or (source.object_id, source.controller) not in event.battlefield_authority
                or fragment not in self.interpreter.fragments(source.rules_card)
                or self.interpreter.combat_damage_draw_discard_semantic_coverage(
                    source.card, fragment
                )
                is None
            ):
                raise ValueError("combat Draw/discard damage provenance is invalid")
        if effect is TriggerEffect.COMBAT_DAMAGE_DRAW_LOSE_LIFE:
            self._validate_combat_draw_life_event(event, source, fragment)
        if effect is TriggerEffect.ETB_DESTROY_TARGET_CREATURE:
            self._authenticate_original_rules_event(event)
            if (
                not self.is_authoritative(source, "battlefield")
                or event.kind
                is not (
                    RulesEventKind.CREATURE_ENTERED
                    if source.card.is_creature
                    else RulesEventKind.PERMANENT_ENTERED
                )
                or event.subject_ids != (source.object_id,)
                or event.player_index != source.controller
                or (source.object_id, source.controller) not in event.battlefield_authority
                or fragment not in self.interpreter.fragments(source.rules_card)
                or not self.interpreter.etb_destroy_target_creature(source.card, fragment)
            ):
                raise ValueError("entry destruction lacks source event provenance")
        if effect is TriggerEffect.ETB_TARGET_CREATURE_PUMP_UNTAP:
            self._authenticate_original_rules_event(event)
            if (
                event.kind
                is not (
                    RulesEventKind.CREATURE_ENTERED
                    if source.card.is_creature
                    else RulesEventKind.PERMANENT_ENTERED
                )
                or event.subject_ids != (source.object_id,)
                or event.player_index != source.controller
                or (source.object_id, source.controller) not in event.battlefield_authority
                or fragment not in self.interpreter.fragments(source.rules_card)
                or self.interpreter.etb_target_creature_pump_untap(source.card, fragment) is None
            ):
                raise ValueError("entry modifier lacks source event provenance")
        if effect is TriggerEffect.ETB_MILL_DRAW_DISCARD:
       ×]µçkh‘éì¶»§q«^u‰¥±¥Ñä¹½¹ÑÉ½±±•Ét(€€€€€€€€€€€µ…Ñ¡•Ì€ôÍ½ÉÑ• (€€€€€€€€€€€€€€€€ (€€€€€€€€€€€€€€€€€€€…É(€€€€€€€€€€€€€€€€€€€™½È…É¥¸Á±…å•È¹±¥‰É…Éä(€€€€€€€€€€€€€€€€€€€¥˜É”¹Í•…É ¡É˜‰q‰í±…¹‘}ÑåÁ”¹É½ÕÀ ±…¹œ¥õqˆˆ°…É¹…É¹ÑåÁ•}±¥¹”¤(€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€­•äõ±…µ‰‘„…Éè…É¹½‰©•Ñ}¥°(€€€€€€€€€€€€¤(€€€€€€€€€€€™½Õ¹€ôµ…Ñ¡•ÍlÁt¥˜µ…Ñ¡•Ì•±Í”9½¹”(€€€€€€€€€€€¥˜™½Õ¹¥Ì¹½Ð9½¹”è(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰±…¹‘å±¥¹}É•Ù•…±•ˆ°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€…Éõ™½Õ¹¹¹…µ”°(€€€€€€€€€€€€€€€€€€€±¥‰É…Éå}½‰©•Ñ}¥õ™½Õ¹¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€¥¹}¡…¹€ôÍ•±˜¹µ½Ù•}½‰©•Ð¡™½Õ¹°€‰¡…¹ˆ°É•…Í½¸ô‰±…¹‘å±¥¹}Í•…É ˆ¤(€€€€€€€€€€€€€€€‘•±¥Ù•É•€ôQÉÕ”(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰±…¹‘å±¥¹}™½Õ¹ˆ°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€…Éõ¥¹}¡…¹¹¹…µ”°(€€€€€€€€€€€€€€€€€€€¡…¹‘}½‰©•Ñ}¥õ¥¹}¡…¹¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€Á±…å•È¹±¥‰É…Éålét€ôÍ•±˜¹É¹œ¹Í¡Õ™™±• (€€€€€€€€€€€€€€€Á±…å•È¹±¥‰É…Éä°‘½µ…¥¸õ˜‰±…¹‘å±¥¹œéí…‰¥±¥Ñä¹½‰©•Ñ}¥‘ôˆ(€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰±…¹‘å±¥¹}Í¡Õ™™±•ˆ°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€™½Õ¹õ‘•±¥Ù•É•°(€€€€€€€€€€€€€€€±¥‰É…Éå}Í¥é”õ±•¸¡Á±…å•È¹±¥‰É…Éä¤°(€€€€€€€€€€€€¤(€€€€€€€¥˜€ (€€€€€€€€€€€…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥ÌÑ¥Ù…Ñ•‘™™•Ñ-¥¹¹Y9}1MM}1Y0(€€€€€€€€€€€…¹Í½ÕÉ•}Á•Éµ…¹•¹Ð¥Ì¹½Ð9½¹”(€€€€€€€€€€€…¹€‰±…ÍÌˆ¥¸Í½ÕÉ•}Á•Éµ…¹•¹Ð¹…É¹ÑåÁ•}±¥¹”(€€€€€€€€¤è(€€€€€€€€€€€±•Ù•±}µ…Ñ €ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹1MM}1Y1}U@¹™Õ±±µ…Ñ ¡…‰¥±¥Ñä¹½É…±•}™É…µ•¹Ð¤(€€€€€€€€€€€¥˜±•Ù•±}µ…Ñ ¥Ì9½¹”½ÈÍ½ÕÉ•}Á•Éµ…¹•¹Ð¹±…ÍÍ}±•Ù•°€„ô¥¹Ð¡±•Ù•±}µ…Ñ¡l‰±•Ù•°‰t¤€´€Äè(€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰±…ÍÌ±•Ù•°…‘Ù…¹•µ•¹Ð¹¼±½¹•È¡…ÌÙ…±¥ÁÉ½É•ÍÍ¥½¸ˆ¤(€€€€€€€€€€€¹•áÑ}±•Ù•°€ô¥¹Ð¡±•Ù•±}µ…Ñ¡l‰±•Ù•°‰t¤(€€€€€€€€€€€Í½ÕÉ•}Á•Éµ…¹•¹Ð¹±…ÍÍ}±•Ù•°€ô¹•áÑ}±•Ù•°(€€€€€€€€€€€¥˜¹•áÑ}±•Ù•°€ôô€Èè(€€€€€€€€€€€€€€€Í½ÕÉ•}Á•Éµ…¹•¹Ð¹±…ÍÍ}±•Ù•±}Ñ¥µ•ÍÑ…µÀ€ôÍ•±˜¹}•™™•Ñ}Ñ¥µ•ÍÑ…µÀ ¤(€€€€€€€€€€€Í•±˜¹É•™É•Í¡}ÍÑ…Ñ¥}ÁÑ}µ½‘¥™¥•ÉÌ ¤(€€€€€€€€€€€•Ù•¹Ð€ôÍ•±˜¹}¹•Ý}ÉÕ±•Í}•Ù•¹Ð (€€€€€€€€€€€€€€€IÕ±•ÍÙ•¹Ñ-¥¹¹1MM}1Y1}Y9°(€€€€€€€€€€€€€€€…‰¥±¥Ñä¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€¡Í½ÕÉ•}Á•Éµ…¹•¹Ð¹½‰©•Ñ}¥°¤°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍ½ÕÉ•}Á•Éµ…¹•¹Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€¤(€€€€€€€€€€€¡¥±€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹±…ÍÍ}±•Ù•±}¡¥±¡Í½ÕÉ•}Á•Éµ…¹•¹Ð¹…É°¹•áÑ}±•Ù•°¤(€€€€€€€€€€€¥˜¡¥±¥Ì¹½Ð9½¹”è(€€€€€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€€€€€Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹±…ÍÍ}±•Ù•±}É•½Ù•Éå}Í•µ…¹Ñ¥}½Ù•É…” (€€€€€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}Á•Éµ…¹•¹Ð¹…É°¡¥±(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€¥Ì¹½Ð9½¹”(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€Í•±˜¹}•¹ÅÕ•Õ•}ÑÉ¥•È (€€€€€€€€€€€€€€€€€€€€€€€•Ù•¹Ð°Í½ÕÉ•}Á•Éµ…¹•¹Ð°¡¥±°QÉ¥•É™™•Ð¹1MM}1Y1}Q]=}I=YId(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€•±¥˜Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹1MM}1Y1}Q!I}MI ¹™Õ±±µ…Ñ ¡¡¥±¤è(€€€€€€€€€€€€€€€€€€€Í•±˜¹}•¹ÅÕ•Õ•}ÑÉ¥•È (€€€€€€€€€€€€€€€€€€€€€€€•Ù•¹Ð°Í½ÕÉ•}Á•Éµ…¹•¹Ð°¡¥±°QÉ¥•É™™•Ð¹1MM}1Y1}Q!I}MI (€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰±…ÍÍ}±•Ù•±}…‘Ù…¹•ˆ°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍ½ÕÉ•}Á•Éµ…¹•¹Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€™É½µ}±•Ù•°õ¹•áÑ}±•Ù•°€´€Ä°(€€€€€€€€€€€€€€€Ñ½}±•Ù•°õ¹•áÑ}±•Ù•°°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹Ðõ…‰¥±¥Ñä¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€¤(€€€€€€€€€€€‘•±¥Ù•É•€ôQÉÕ”(€€€€€€€¥˜€ (€€€€€€€€€€€…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥ÌÑ¥Ù…Ñ•‘™™•Ñ-¥¹¹I9Q}I!}U9Q%1}=P(€€€€€€€€€€€…¹¥Í¥¹ÍÑ…¹”¡Í½ÕÉ•}Á•Éµ…¹•¹Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€…¹Í•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Í½ÕÉ•}Á•Éµ…¹•¹Ð°€‰‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€€¤è(€€€€€€€€€€€Í½ÕÉ•}Á•Éµ…¹•¹Ð¹Ñ•µÁ½É…Éå}­•åÝ½É‘}•™™•ÑÌ¹…ÁÁ•¹ (€€€€€€€€€€€€€€€Q•µÁ½É…Éå-•åÝ½É‘™™•Ð (€€€€€€€€€€€€€€€€€€€Q•µÁ½É…Éå-•åÝ½É¹I °(€€€€€€€€€€€€€€€€€€€€‰Õ¹Ñ¥±}•¹‘}½™}ÑÕÉ¸ˆ°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}Á•Éµ…¹•¹Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€…‰¥±¥Ñä¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€Ñ¥µ•ÍÑ…µÀõÍ•±˜¹}•™™•Ñ}Ñ¥µ•ÍÑ…µÀ ¤°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰™É½}‰ÕÑ±•É}É•…¡}É…¹Ñ•ˆ°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍ½ÕÉ•}Á•Éµ…¹•¹Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€¤(€€€€€€€€€€€‘•±¥Ù•É•€ôQÉÕ”(€€€€€€€¥˜€ (€€€€€€€€€€€…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥ÌÑ¥Ù…Ñ•‘™™•Ñ-¥¹¹IQUI9}M1}I=5}IYeI}QAA(€€€€€€€€€€€…¹¥Í¥¹ÍÑ…¹”¡Í½ÕÉ”°…É‘=‰©•Ð¤(€€€€€€€€¤è(€€€€€€€€€€€É•ÑÕÉ¹•€ôÍ•±˜¹É•…Ñ•}Á•Éµ…¹•¹Ð (€€€€€€€€€€€€€€€Í½ÕÉ”¹…É°…‰¥±¥Ñä¹½¹ÑÉ½±±•È°Ñ…ÁÁ•õQÉÕ”°ÍÕµµ½¹¥¹}Í¥¬õ…±Í”(€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰ÑÕ¹¹•±}É…ÑÍ}É•ÑÕÉ¹•ˆ°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍ½ÕÉ”¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Á•Éµ…¹•¹Ñ}¥õÉ•ÑÕÉ¹•¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Ñ…ÁÁ•õQÉÕ”°(€€€€€€€€€€€€¤(€€€€€€€€€€€‘•±¥Ù•É•€ôQÉÕ”(€€€€€€€™½½‘}±¥™•}…™Ñ•Èè¥¹Ðð9½¹”€ô9½¹”(€€€€€€€¥˜…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥ÌÑ¥Ù…Ñ•‘™™•Ñ-¥¹¹I]}Iè(€€€€€€€€€€€‰•™½É”€ô±•¸¡Í•±˜¹Á±…å•ÉÍm…‰¥±¥Ñä¹½¹ÑÉ½±±•Ét¹¡…¹¤(€€€€€€€€€€€‘É•Ü€ôÍ•±˜¹‘É…Ü¡Í•±˜¹Á±…å•ÉÍm…‰¥±¥Ñä¹½¹ÑÉ½±±•Ét°€Ä¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰É…å}™¥±±•ÑÍ}‘É…Ý}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€½ÍÑ}Ñ…É•Ñ}¥õ…‰¥±¥Ñä¹½ÍÑ}Ñ…É•Ñ}¥°(€€€€€€€€€€€€€€€…É‘Í}‘É…Ý¸ôÄ¥˜‘É•Ü•±Í”€À°(€€€€€€€€€€€€€€€¡…¹‘}Í¥é•}‰•™½É”õ‰•™½É”°(€€€€€€€€€€€€€€€¡…¹‘}Í¥é•}…™Ñ•Èõ±•¸¡Í•±˜¹Á±…å•ÉÍm…‰¥±¥Ñä¹½¹ÑÉ½±±•Ét¹¡…¹¤°(€€€€€€€€€€€€¤(€€€€€€€€€€€‘•±¥Ù•É•€ô‘É•Ü(€€€€€€€•±¥˜…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥ÌÑ¥Ù…Ñ•‘™™•Ñ-¥¹¹I]}ILè(€€€€€€€€€€€µ…Ñ €ôÉ”¹Í•…É  (€€€€€€€€€€€€€€€È‰yÉ…Ü€ ý@ñ½Õ¹Ðù…ñ½¹•ñÑÝ½ñÑ¡É••ñ™½ÕÉñ™¥Ù•ñlÄ´åuq¨¤…É‘Ìýp¸ˆ(€€€€€€€€€€€€€€€Èˆ üèÑ¥Ù…Ñ”½¹±ä…Ì„Í½É•Éåp¸¤üˆ°(€€€€€€€€€€€€€€€…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}Ñ•áÐ°(€€€€€€€€€€€€€€€É”¹$°(€€€€€€€€€€€€¤(€€€€€€€€€€€…ÍÍ•ÉÐµ…Ñ ¥Ì¹½Ð9½¹”(€€€€€€€€€€€ÅÕ…¹Ñ¥Ñä€ôì‰„ˆè€Ä°€‰½¹”ˆè€Ä°€‰ÑÝ¼ˆè€È°€‰Ñ¡É•”ˆè€Ì°€‰™½ÕÈˆè€Ð°€‰™¥Ù”ˆè€Õô¹•Ð (€€€€€€€€€€€€€€€µ…Ñ ¹É½ÕÀ ‰½Õ¹Ðˆ¤¹…Í•™½± ¤(€€€€€€€€€€€€¤½È¥¹Ð¡µ…Ñ ¹É½ÕÀ ‰½Õ¹Ðˆ¤¤(€€€€€€€€€€€‰•™½É”€ô±•¸¡Í•±˜¹Á±…å•ÉÍm…‰¥±¥Ñä¹½¹ÑÉ½±±•Ét¹±¥‰É…Éä¤(€€€€€€€€€€€‘•±¥Ù•É•€ôÍ•±˜¹‘É…Ü¡Í•±˜¹Á±…å•ÉÍm…‰¥±¥Ñä¹½¹ÑÉ½±±•Ét°ÅÕ…¹Ñ¥Ñä¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰…Ñ¥Ù…Ñ•‘}‘É…Ý}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€É•ÅÕ•ÍÑ•õÅÕ…¹Ñ¥Ñä°(€€€€€€€€€€€€€€€…É‘Í}‘É…Ý¸õ‰•™½É”€´±•¸¡Í•±˜¹Á±…å•ÉÍm…‰¥±¥Ñä¹½¹ÑÉ½±±•Ét¹±¥‰É…Éä¤°(€€€€€€€€€€€€€€€‘É…Ý}ÍÕ••‘•õ‘•±¥Ù•É•°(€€€€€€€€€€€€¤(€€€€€€€•±¥˜…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥ÌÑ¥Ù…Ñ•‘™™•Ñ-¥¹¹I9Q}Q=-9}!MQ}U9Q%1}=Pè(€€€€€€€€€€€É•¥Á¥•¹ÑÌ€ôl(€€€€€€€€€€€€€€€À(€€€€€€€€€€€€€€€™½ÈÁ±…å•È¥¸Í•±˜¹Á±…å•ÉÌ(€€€€€€€€€€€€€€€™½ÈÀ¥¸Á±…å•È¹‰…ÑÑ±•™¥•±(€€€€€€€€€€€€€€€¥˜À¹½¹ÑÉ½±±•È€ôô…‰¥±¥Ñä¹½¹ÑÉ½±±•È…¹À¹¥Í}Ñ½­•¸…¹À¹¥Í}É•…ÑÕÉ”(€€€€€€€€€€€t(€€€€€€€€€€€™½ÈÉ•¥Á¥•¹Ð¥¸É•¥Á¥•¹ÑÌè(€€€€€€€€€€€€€€€¥˜¹½Ð…¹ä (€€€€€€€€€€€€€€€€€€€”¹­•åÝ½É¥ÌQ•µÁ½É…Éå-•åÝ½É¹!MQ(€€€€€€€€€€€€€€€€€€€…¹”¹Í½ÕÉ•}¥€ôô…‰¥±¥Ñä¹Í½ÕÉ•}¥(€€€€€€€€€€€€€€€€€€€…¹”¹½É…±•}™É…µ•¹Ð€ôô…‰¥±¥Ñä¹½É…±•}™É…µ•¹Ð(€€€€€€€€€€€€€€€€€€€™½È”¥¸É•¥Á¥•¹Ð¹Ñ•µÁ½É…Éå}­•åÝ½É‘}•™™•ÑÌ(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€É•¥Á¥•¹Ð¹Ñ•µÁ½É…Éå}­•åÝ½É‘}•™™•ÑÌ¹…ÁÁ•¹ (€€€€€€€€€€€€€€€€€€€€€€€Q•µÁ½É…Éå-•åÝ½É‘™™•Ð (€€€€€€€€€€€€€€€€€€€€€€€€€€€Q•µÁ½É…Éå-•åÝ½É¹!MQ°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Õ¹Ñ¥±}•¹‘}½™}ÑÕÉ¸ˆ°(€€€€€€€€€€€€€€€€€€€€€€€€€€€…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€…‰¥±¥Ñä¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€Ñ¥µ•ÍÑ…µÀõÍ•±˜¹}•™™•Ñ}Ñ¥µ•ÍÑ…µÀ ¤°(€€€€€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰Ñ½­•¹}¡…ÍÑ•}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€É•¥Á¥•¹Ñ}¥‘ÌõmÀ¹½‰©•Ñ}¥™½ÈÀ¥¸É•¥Á¥•¹ÑÍt°(€€€€€€€€€€€€€€€ÅÕ…¹Ñ¥Ñäõ±•¸¡É•¥Á¥•¹ÑÌ¤°(€€€€€€€€€€€€¤(€€€€€€€•±¥˜…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥ÌÑ¥Ù…Ñ•‘™™•Ñ-¥¹¹5UQ9}=U9QHè(€€€€€€€€€€€Ñ…É•Ð€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘ÍlÁt¤¥˜…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘Ì•±Í”9½¹”(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€…¹Í•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Ñ…É•Ð°€‰‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€€€€€€€€€…¹Ñ…É•Ð¹¥Í}É•…ÑÕÉ”(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€Í•±˜¹Á±…•}½Õ¹Ñ•ÉÌ (€€€€€€€€€€€€€€€€€€€Ñ…É•Ð°(€€€€€€€€€€€€€€€€€€€€ˆ¬Ä¼¬Äˆ°(€€€€€€€€€€€€€€€€€€€€Ä°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}…Éõ…‰¥±¥Ñä¹Í½ÕÉ•}…É¹¹…µ”°(€€€€€€€€€€€€€€€€€€€½É…±•}™É…µ•¹Ðõ…‰¥±¥Ñä¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰µÕÑ…•¹}½Õ¹Ñ•É}Á±…•ˆ°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÑ…É•Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€‘•±¥Ù•É•€ôQÉÕ”(€€€€€€€€€€€•±Í”è(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰µÕÑ…•¹}½Õ¹Ñ•É}™…¥±•‘}±½Í•ˆ°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õ…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘ÍlÁt¥˜…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘Ì•±Í”9½¹”°(€€€€€€€€€€€€€€€€¤(€€€€€€€•±¥˜€ (€€€€€€€€€€€…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥ÌÑ¥Ù…Ñ•‘™™•Ñ-¥¹¹1}%a}5}Q=}QIQ}IQUI(€€€€€€€€¤è(€€€€€€€€€€€Ñ…É•Ð€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘ÍlÁt¤¥˜…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘Ì•±Í”9½¹”(€€€€€€€€€€€¥˜Í•±˜¹}±•…±}…Ñ¥Ù…Ñ•‘}‘…µ…•}Ñ…É•Ð¡Ñ…É•Ð°…‰¥±¥Ñä¹½¹ÑÉ½±±•È¤è(€€€€€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Í½ÕÉ”°A•Éµ…¹•¹Ð¤…¹‘…µ…•}‘•Á…ÉÑÕÉ•}•Ù•¹Ð¥Ì¹½Ð9½¹”(€€€€€€€€€€€€€€€ÁÉ½É…´€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹‘…µ…•}ÁÉ½É…´¡…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}Ñ•áÐ¤(€€€€€€€€€€€€€€€…ÍÍ•ÉÐÁÉ½É…´¥Ì¹½Ð9½¹”…¹ÁÉ½É…´¹…µ½Õ¹Ð¥Ì¹½Ð9½¹”(€€€€€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€‘…µ…•}•Ù•¹Ð€ôÍ•±˜¹‘•…±}‘…µ…” (€€€€€€€€€€€€€€€€€€€…µ…•QÉ…¹Í…Ñ¥½¸ (€€€€€€€€€€€€€€€€€€€€€€€…‰¥±¥Ñä¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€Í½ÕÉ”°(€€€€€€€€€€€€€€€€€€€€€€€…µ…•Q…É•Ñ-¥¹¹IQUI°(€€€€€€€€€€€€€€€€€€€€€€€ÁÉ½É…´¹…µ½Õ¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€…‰¥±¥Ñä¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€Ñ…É•Ð°(€€€€€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}•Ù•¹Ðõ‘…µ…•}‘•Á…ÉÑÕÉ•}•Ù•¹Ð°(€€€€€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€€€€€‘•™•É}Á½ÍÑ}‘…µ…”õQÉÕ”°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€‘•±¥Ù•É•€ôQÉÕ”(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰…Ñ¥Ù…Ñ•‘}‘…µ…•}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÑ…É•Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€‘…µ…•}•Ù•¹Ñ}¥õ‘…µ…•}•Ù•¹Ð¹•Ù•¹Ñ}¥°(€€€€€€€€€€€€€€€€€€€…µ½Õ¹ÐõÁÉ½É…´¹…µ½Õ¹Ð°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€•±Í”è(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰…Ñ¥Ù…Ñ•‘}…‰¥±¥Ñå}É•Í½±Ù•‘}¹½}•™™•Ðˆ°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õ…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘ÍlÁt¥˜…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘Ì•±Í”9½¹”°(€€€€€€€€€€€€€€€€€€€É•…Í½¸ô‰Ñ…É•Ñ}¥±±•…±}…Ñ}É•Í½±ÕÑ¥½¸ˆ°(€€€€€€€€€€€€€€€€¤(€€€€€€€•±¥˜…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥ÌÑ¥Ù…Ñ•‘™™•Ñ-¥¹¹=U9QI}QIQ}MA10è(€€€€€€€€€€€Ñ…É•Ð€ô€ (€€€€€€€€€€€€€€€Í•±˜¹}½‰©•ÑÌ¹•Ð¡…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘ÍlÁt¤¥˜±•¸¡…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘Ì¤€ôô€Ä•±Í”9½¹”(€€€€€€€€€€€€¤(€€€€€€€€€€€±•…°€ôÍ•±˜¹}¥Í}±•…±}½Õ¹Ñ•É}Ñ…É•Ð¡Ñ…É•Ð°…‰¥±¥Ñä¹½¹ÑÉ½±±•È¤(€€€€€€€€€€€¥˜±•…°è(€€€€€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°MÑ…­=‰©•Ð¤(€€€€€€€€€€€€€€€Ñ…É•Ñ}…É€ôÍ•±˜¹µ½Ù•}½‰©•Ð¡Ñ…É•Ð°€‰É…Ù•å…Éˆ°É•…Í½¸ô‰ÍÁ•±±}½Õ¹Ñ•É•ˆ¤(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰ÍÁ•±±}½Õ¹Ñ•É•ˆ°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€…‰¥±¥Ñå}Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}ÍÁ•±±}¥õÑ…É•Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}½‰©•Ñ}¥õÑ…É•Ð¹Ñ…É•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}…ÉõÑ…É•Ð¹…É¹¹…µ”°(€€€€€€€€€€€€€€€€€€€½¹ÑÉ½±±•Èõ…‰¥±¥Ñä¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€½É…±•}™É…µ•¹Ðõ…‰¥±¥Ñä¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}É•±…Ñ¥½¹Í¡¥Àô‰Ñ…É•ÑÍ}…ÉÑ¥™…Ñ}½É}É•…ÑÕÉ•}å½Õ}½¹ÑÉ½°ˆ°(€€€€€€€€€€€€€€€€€€€½Õ¹Ñ•É•‘}½‰©•Ñ}¥õÑ…É•Ñ}…É¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€‘•±¥Ù•É•€ôQÉÕ”(€€€€€€€€€€€•±Í”è(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰…Ñ¥Ù…Ñ•‘}…‰¥±¥Ñå}É•Í½±Ù•‘}¹½}•™™•Ðˆ°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}ÍÁ•±±}¥ô¡…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘ÍlÁt¥˜…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘Ì•±Í”9½¹”¤°(€€€€€€€€€€€€€€€€€€€É•…Í½¸ô‰½Õ¹Ñ•É}Ñ…É•Ñ}¥±±•…±}…Ñ}É•Í½±ÕÑ¥½¸ˆ°(€€€€€€€€€€€€€€€€¤(€€€€€€€•±¥˜…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥ÌÑ¥Ù…Ñ•‘™™•Ñ-¥¹¹=U9QI}9}9%5Q}IQ%Pè(€€€€€€€€€€€ÁÉ½É…´€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹½Õ¹Ñ•É}…¹‘}…¹¥µ…Ñ•}…ÉÑ¥™…Ñ}ÁÉ½É…´¡…‰¥±¥Ñä¹½É…±•}™É…µ•¹Ð¤(€€€€€€€€€€€…ÍÍ•ÉÐÁÉ½É…´¥Ì¹½Ð9½¹”(€€€€€€€€€€€Ñ…É•Ð€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘ÍlÁt¤¥˜…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘Ì•±Í”9½¹”(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€…¹Í•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Ñ…É•Ð°€‰‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€€€€€€€€€…¹Ñ…É•Ð¹½¹ÑÉ½±±•È€ôô…‰¥±¥Ñä¹½¹ÑÉ½±±•È(€€€€€€€€€€€€€€€…¹€‰ÉÑ¥™…Ðˆ¥¸Ñ…É•Ð¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€€€€€€€€€…¹Í•±˜¹}±•…±}Ñ…É•Ñ¥¹}ÁÉ½Ñ•Ñ¥½¸¡Ñ…É•Ð°…‰¥±¥Ñä¹½¹ÑÉ½±±•È¤(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€½Õ¹Ð°Á½Ý•È°Ñ½Õ¡¹•ÍÌ°ÍÕ‰ÑåÁ”€ôÁÉ½É…´(€€€€€€€€€€€€€€€Ý…Í}É•…ÑÕÉ”€ôÑ…É•Ð¹¥Í}É•…ÑÕÉ”(€€€€€€€€€€€€€€€Í•±˜¹Á±…•}½Õ¹Ñ•ÉÌ (€€€€€€€€€€€€€€€€€€€Ñ…É•Ð°(€€€€€€€€€€€€€€€€€€€€ˆ¬Ä¼¬Äˆ°(€€€€€€€€€€€€€€€€€€€½Õ¹Ð°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}…Éõ…‰¥±¥Ñä¹Í½ÕÉ•}…É¹¹…µ”°(€€€€€€€€€€€€€€€€€€€½É…±•}™É…µ•¹Ðõ…‰¥±¥Ñä¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€‘•™•É}Á½ÍÑ}Á±…•µ•¹ÐõQÉÕ”°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€¥˜¹½ÐÝ…Í}É•…ÑÕÉ”è(€€€€€€€€€€€€€€€€€€€Í•±˜¹…ÁÁ±å}Ñ•µÁ½É…Éå}ÑåÁ•}…¹‘}‰…Í•}ÁÐ (€€€€€€€€€€€€€€€€€€€€€€€Ñ…É•Ð°(€€€€€€€€€€€€€€€€€€€€€€€…‘‘•‘}ÑåÁ•Ìô ‰É•…ÑÕÉ”ˆ°¤°(€€€€€€€€€€€€€€€€€€€€€€€…‘‘•‘}ÍÕ‰ÑåÁ•Ìô¡ÍÕ‰ÑåÁ”°¤°(€€€€€€€€€€€€€€€€€€€€€€€Á½Ý•ÈõÁ½Ý•È°(€€€€€€€€€€€€€€€€€€€€€€€Ñ½Õ¡¹•ÍÌõÑ½Õ¡¹•ÍÌ°(€€€€€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}…Éõ…‰¥±¥Ñä¹Í½ÕÉ•}…É¹¹…µ”°(€€€€€€€€€€€€€€€€€€€€€€€½É…±•}™É…µ•¹Ðõ…‰¥±¥Ñä¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€‘ÕÉ…Ñ¥½¸ô‰Á•ÉÍ¥ÍÑ•¹Ðˆ°(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€Í•±˜¹É•™É•Í¡}ÍÑ…Ñ¥}ÁÑ}µ½‘¥™¥•ÉÌ ¤(€€€€€€€€€€€€€€€‘•±¥Ù•É•€ôQÉÕ”(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰…Ñ¥Ù…Ñ•‘}½Õ¹Ñ•É}…ÉÑ¥™…Ñ}…¹¥µ…Ñ¥½¹}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÑ…É•Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€½Õ¹Ñ•ÉÌõ½Õ¹Ð°(€€€€€€€€€€€€€€€€€€€…¹¥µ…Ñ•õ¹½ÐÝ…Í}É•…ÑÕÉ”°(€€€€€€€€€€€€€€€€€€€É•ÍÕ±Ñ¥¹}ÑåÁ•}±¥¹”õÑ…É•Ð¹ÑåÁ•}±¥¹”°(€€€€€€€€€€€€€€€€€€€É•ÍÕ±Ñ¥¹}Á½Ý•ÈõÑ…É•Ð¹Á½Ý•È°(€€€€€€€€€€€€€€€€€€€É•ÍÕ±Ñ¥¹}Ñ½Õ¡¹•ÍÌõÑ…É•Ð¹Ñ½Õ¡¹•ÍÌ°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€•±Í”è(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰…Ñ¥Ù…Ñ•‘}…‰¥±¥Ñå}É•Í½±Ù•‘}¹½}•™™•Ðˆ°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õ…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘ÍlÁt¥˜…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘Ì•±Í”9½¹”°(€€€€€€€€€€€€€€€€€€€É•…Í½¸ô‰Ñ…É•Ñ}¥±±•…±}…Ñ}É•Í½±ÕÑ¥½¸ˆ°(€€€€€€€€€€€€€€€€¤(€€€€€€€•±¥˜€ (€€€€€€€€€€€…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥ÌÑ¥Ù…Ñ•‘™™•Ñ-¥¹¹I9Q}M1}%IMQ}MQI%-}U9Q%1}=P(€€€€€€€€€€€…¹Í½ÕÉ•}Á•Éµ…¹•¹Ð¥Ì¹½Ð9½¹”(€€€€€€€€¤è(€€€€€€€€€€€Í½ÕÉ•}Á•Éµ…¹•¹Ð¹Ñ•µÁ½É…Éå}­•åÝ½É‘}•™™•ÑÌ¹…ÁÁ•¹ (€€€€€€€€€€€€€€€Q•µÁ½É…Éå-•åÝ½É‘™™•Ð (€€€€€€€€€€€€€€€€€€€MÑÉ¥­•-•åÝ½É¹%IMQ}MQI%-°(€€€€€€€€€€€€€€€€€€€€‰Õ¹Ñ¥±}•¹‘}½™}ÑÕÉ¸ˆ°(€€€€€€€€€€€€€€€€€€€…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€…‰¥±¥Ñä¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€Ñ¥µ•ÍÑ…µÀõÍ•±˜¹}•™™•Ñ}Ñ¥µ•ÍÑ…µÀ ¤°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€¤(€€€€€€€€€€€‘•±¥Ù•É•€ôQÉÕ”(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰Ñ•µÁ½É…Éå}­•åÝ½É‘}É…¹Ñ•ˆ°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÍ½ÕÉ•}Á•Éµ…¹•¹Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€­•åÝ½ÉõMÑÉ¥­•-•åÝ½É¹%IMQ}MQI%-¹Ù…±Õ”°(€€€€€€€€€€€€€€€‘ÕÉ…Ñ¥½¸ô‰Õ¹Ñ¥±}•¹‘}½™}ÑÕÉ¸ˆ°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹Ðõ…‰¥±¥Ñä¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€¤(€€€€€€€•±¥˜€ (€€€€€€€€€€€…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹(€€€€€€€€€€€¥ÌÑ¥Ù…Ñ•‘™™•Ñ-¥¹¹IQUI9}9=Q!I}IQUI}e=U}=9QI=1}Q=}=]9IM}!9(€€€€€€€€¤è(€€€€€€€€€€€Ñ…É•Ð€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘ÍlÁt¤(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€…¹Í•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Ñ…É•Ð°€‰‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€€€€€€€€€…¹Ñ…É•Ð¹½‰©•Ñ}¥€„ô…‰¥±¥Ñä¹Í½ÕÉ•}¥(€€€€€€€€€€€€€€€…¹Ñ…É•Ð¹½¹ÑÉ½±±•È€ôô…‰¥±¥Ñä¹½¹ÑÉ½±±•È(€€€€€€€€€€€€€€€…¹Ñ…É•Ð¹¥Í}É•…ÑÕÉ”(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É•Á±…•µ•¹Ð€ôÍ•±˜¹µ½Ù•}½‰©•Ð (€€€€€€€€€€€€€€€€€€€Ñ…É•Ð°€‰¡…¹ˆ°É•…Í½¸ô‰…Ñ¥Ù…Ñ•‘}É•ÑÕÉ¹}Ñ½}½Ý¹•ÉÍ}¡…¹ˆ(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€‘•±¥Ù•É•€ôQÉÕ”(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰Ñ…É•Ñ}É•ÑÕÉ¹•‘}Ñ½}¡…¹ˆ°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÑ…É•Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€‘•ÍÑ¥¹…Ñ¥½¹}½‰©•Ñ}¥õÉ•Á±…•µ•¹Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€½Ý¹•ÈõÍ•±˜¹Á±…å•ÉÍmÑ…É•Ð¹½Ý¹•Ét¹¹…µ”°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€•±Í”è(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰…Ñ¥Ù…Ñ•‘}…‰¥±¥Ñå}É•Í½±Ù•‘}¹½}•™™•Ðˆ°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€É•…Í½¸ô‰Ñ…É•Ñ}¥±±•…±}…Ñ}É•Í½±ÕÑ¥½¸ˆ°(€€€€€€€€€€€€€€€€¤(€€€€€€€•±¥˜…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥ÌÑ¥Ù…Ñ•‘™™•Ñ-¥¹¹QQ!}EU%A59Pè(€€€€€€€€€€€Ñ…É•Ð€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘ÍlÁt¤¥˜…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘Ì•±Í”9½¹”(€€€€€€€€€€€±•…°€ô€ (€€€€€€€€€€€€€€€¥Í¥¹ÍÑ…¹”¡Í½ÕÉ•}Á•Éµ…¹•¹Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€…¹Í•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Í½ÕÉ•}Á•Éµ…¹•¹Ð°€‰‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€€€€€€€€€…¹€‰ÅÕ¥Áµ•¹Ðˆ¥¸Í½ÕÉ•}Á•Éµ…¹•¹Ð¹ÑåÁ•}±¥¹”(€€€€€€€€€€€€€€€…¹¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€…¹Í•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Ñ…É•Ð°€‰‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€€€€€€€€€…¹Ñ…É•Ð¹½¹ÑÉ½±±•È€ôô…‰¥±¥Ñä¹½¹ÑÉ½±±•È(€€€€€€€€€€€€€€€…¹Ñ…É•Ð¹¥Í}É•…ÑÕÉ”(€€€€€€€€€€€€€€€…¹Í•±˜¹}±•…±}Ñ…É•Ñ¥¹}ÁÉ½Ñ•Ñ¥½¸¡Ñ…É•Ð°…‰¥±¥Ñä¹½¹ÑÉ½±±•È¤(€€€€€€€€€€€€¤(€€€€€€€€€€€¥˜±•…°è(€€€€€€€€€€€€€€€Í½ÕÉ•}Á•Éµ…¹•¹Ð¹…ÑÑ…¡•‘}Ñ¼€ôÑ…É•Ð¹½‰©•Ñ}¥(€€€€€€€€€€€€€€€Í½ÕÉ•}Á•Éµ…¹•¹Ð¹…ÑÑ…¡µ•¹Ñ}Ñ¥µ•ÍÑ…µÀ€ôÍ•±˜¹}•™™•Ñ}Ñ¥µ•ÍÑ…µÀ ¤(€€€€€€€€€€€€€€€Í•±˜¹É•™É•Í¡}ÍÑ…Ñ¥}ÁÑ}µ½‘¥™¥•ÉÌ ¤(€€€€€€€€€€€€€€€‘•±¥Ù•É•€ôQÉÕ”(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰•ÅÕ¥Áµ•¹Ñ}…ÑÑ…¡•ˆ°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍ½ÕÉ•}Á•Éµ…¹•¹Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€…ÉõÍ½ÕÉ•}Á•Éµ…¹•¹Ð¹…É¹¹…µ”°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÑ…É•Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Á±…å•ÈõÍ•±˜¹Á±…å•ÉÍm…‰¥±¥Ñä¹½¹ÑÉ½±±•Ét¹¹…µ”°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€•±Í”è(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰•ÅÕ¥Áµ•¹Ñ}…ÑÑ…¡}™…¥±•‘}±½Í•ˆ°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õ…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘ÍlÁt¥˜…‰¥±¥Ñä¹Ñ…É•Ñ}¥‘Ì•±Í”9½¹”°(€€€€€€€€€€€€€€€€¤(€€€€€€€•±¥˜…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥ÌÑ¥Ù…Ñ•‘™™•Ñ-¥¹¹%9}Q!I}1%è(€€€€€€€€€€€™½½‘}±¥™•}‰•™½É”€ôÍ•±˜¹Á±…å•ÉÍm…‰¥±¥Ñä¹½¹ÑÉ½±±•Ét¹±¥™”(€€€€€€€€€€€Í•±˜¹…¥¹}±¥™” (€€€€€€€€€€€€€€€…‰¥±¥Ñä¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€Ì°(€€€€€€€€€€€€€€€Í½ÕÉ•}…Éõ…‰¥±¥Ñä¹Í½ÕÉ•}…É¹¹…µ”°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹Ðõ…‰¥±¥Ñä¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€‘•™•É}ÑÉ¥•É}‘•±¥Ù•ÉäõQÉÕ”°(€€€€€€€€€€€€¤(€€€€€€€€€€€™½½‘}±¥™•}…™Ñ•È€ôÍ•±˜¹Á±…å•ÉÍm…‰¥±¥Ñä¹½¹ÑÉ½±±•Ét¹±¥™”(€€€€€€€€€€€‘•±¥Ù•É•€ôQÉÕ”(€€€€€€€•±¥˜…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥ÌÑ¥Ù…Ñ•‘™™•Ñ-¥¹¹Y9}1MM}1Y0è(€€€€€€€€€€€Á…ÍÌ(€€€€€€€•±Í”è(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰…Ñ¥Ù…Ñ•‘}…‰¥±¥Ñå}É•Í½±Ù•‘}¹½}•™™•Ðˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€É•…Í½¸ô‰Í½ÕÉ•}¹½Ñ}½¹}‰…ÑÑ±•™¥•±ˆ°(€€€€€€€€€€€€¤(€€€€€€€™½È¥¹‘•à°•Ù¥‘•¹”¥¸•¹Õµ•É…Ñ”¡Í•±˜¹…Ñ¥Ù…Ñ¥½¹}•Ù¥‘•¹”¤è(€€€€€€€€€€€¥˜•Ù¥‘•¹”¹ÍÑ…­}½‰©•Ñ}¥€ôô…‰¥±¥Ñä¹½‰©•Ñ}¥è(€€€€€€€€€€€€€€€Í•±˜¹…Ñ¥Ù…Ñ¥½¹}•Ù¥‘•¹•m¥¹‘•át€ôÑ¥Ù…Ñ¥½¹Ù¥‘•¹” (€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹ÍÑ…­}½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹µ…¹…}Í½ÕÉ•}¥‘Ì°(€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹Ñ…Á}Í½ÕÉ”°(€€€€€€€€€€€€€€€€€€€QÉÕ”°(€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹½ÍÑ}Ñ…É•Ñ}¥°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€‰É•…¬(€€€€€€€¥˜…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥ÌÑ¥Ù…Ñ•‘™™•Ñ-¥¹¹%9}Q!I}1%è(€€€€€€€€€€€™½È¥¹‘•à°•Ù¥‘•¹”¥¸•¹Õµ•É…Ñ”¡Í•±˜¹™½½‘}…Ñ¥Ù…Ñ¥½¹}•Ù¥‘•¹”¤è(€€€€€€€€€€€€€€€¥˜•Ù¥‘•¹”¹ÍÑ…­}½‰©•Ñ}¥€ôô…‰¥±¥Ñä¹½‰©•Ñ}¥è(€€€€€€€€€€€€€€€€€€€Í•±˜¹™½½‘}…Ñ¥Ù…Ñ¥½¹}•Ù¥‘•¹•m¥¹‘•át€ôÉ•Á±…” (€€€€€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”°(€€€€€€€€€€€€€€€€€€€€€€€É•Í½±Ù•õQÉÕ”°(€€€€€€€€€€€€€€€€€€€€€€€±¥™•}‰•™½É”õ™½½‘}±¥™•}‰•™½É”°(€€€€€€€€€€€€€€€€€€€€€€€±¥™•}…™Ñ•Èõ™½½‘}±¥™•}…™Ñ•È°(€€€€€€€€€€€€€€€€€€€€€€€…µ½Õ¹Ñ}…¥¹•ô (€€€€€€€€€€€€€€€€€€€€€€€€€€€™½½‘}±¥™•}…™Ñ•È€´™½½‘}±¥™•}‰•™½É”(€€€€€€€€€€€€€€€€€€€€€€€€€€€¥˜™½½‘}±¥™•}‰•™½É”¥Ì¹½Ð9½¹”…¹™½½‘}±¥™•}…™Ñ•È¥Ì¹½Ð9½¹”(€€€€€€€€€€€€€€€€€€€€€€€€€€€•±Í”9½¹”(€€€€€€€€€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€‰É•…¬(€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€‰…Ñ¥Ù…Ñ•‘}…‰¥±¥Ñå}É•Í½±Ù•ˆ°(€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õ…‰¥±¥Ñä¹½‰©•Ñ}¥°(€€€€€€€€€€€Í½ÕÉ•}¥õ…‰¥±¥Ñä¹Í½ÕÉ•}¥°(€€€€€€€€€€€…Éõ…‰¥±¥Ñä¹Í½ÕÉ•}…É¹¹…µ”°(€€€€€€€€€€€½¹ÑÉ½±±•ÈõÍ•±˜¹Á±…å•ÉÍm…‰¥±¥Ñä¹½¹ÑÉ½±±•Ét¹¹…µ”°(€€€€€€€€€€€‘•±¥Ù•É•õ‘•±¥Ù•É•°(€€€€€€€€¤(€€€€€€€¥˜…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥ÌÑ¥Ù…Ñ•‘™™•Ñ-¥¹¹1}%a}5}Q=}QIQ}IQUIè(€€€€€€€€€€€Í•±˜¹¡•­}ÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¹Ì ¤(€€€€€€€€€€€Í•±˜¹¡•­}±¥™” ¤(€€€€€€€€€€€¥˜‘•±¥Ù•É•è(€€€€€€€€€€€€€€€Í•±˜¹}ÁÕÑ}Á•¹‘¥¹}ÑÉ¥•ÉÍ}½¹}ÍÑ…¬ ¤(€€€€€€€¥˜…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥¸ì(€€€€€€€€€€€Ñ¥Ù…Ñ•‘™™•Ñ-¥¹¹%9}Q!I}1%°(€€€€€€€€€€€Ñ¥Ù…Ñ•‘™™•Ñ-¥¹¹Y9}1MM}1Y0°(€€€€€€€€€€€Ñ¥Ù…Ñ•‘™™•Ñ-¥¹¹=U9QI}9}9%5Q}IQ%P°(€€€€€€€€€€€Ñ¥Ù…Ñ•‘™™•Ñ-¥¹¹=Ae}Q!%M}EU%A59P°(€€€€€€€ôè(€€€€€€€€€€€¥˜…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥¸ì(€€€€€€€€€€€€€€€Ñ¥Ù…Ñ•‘™™•Ñ-¥¹¹=U9QI}9}9%5Q}IQ%P°(€€€€€€€€€€€€€€€Ñ¥Ù…Ñ•‘™™•Ñ-¥¹¹=Ae}Q!%M}EU%A59P°(€€€€€€€€€€€ôè(€€€€€€€€€€€€€€€Í•±˜¹¡•­}ÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¹Ì ¤(€€€€€€€€€€€Í•±˜¹}ÁÕÑ}Á•¹‘¥¹}ÑÉ¥•ÉÍ}½¹}ÍÑ…¬ ¤((€€€‘•˜}Ù…±¥‘…Ñ•}™½½‘}…Ñ¥Ù…Ñ¥½¹}±¥¹­…”¡Í•±˜°…‰¥±¥ÑäèÑ¥Ù…Ñ•‘‰¥±¥Ñå=‰©•Ð¤€´ø9½¹”è(€€€€€€€€ˆˆ‰ÕÑ¡•¹Ñ¥…Ñ”½¹”…¹½¹¥…°½½ÍÑ…¬½‰©•Ð™É½´¥µµÕÑ…‰±”Á…åµ•¹Ð•Ù¥‘•¹”¸ˆˆˆ(€€€€€€€…Ñ¥Ù…Ñ¥½¹Ì€ôl(€€€€€€€€€€€¥Ñ•´™½È¥Ñ•´¥¸Í•±˜¹…Ñ¥Ù…Ñ¥½¹}•Ù¥‘•¹”¥˜¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥€ôô…‰¥±¥Ñä¹½‰©•Ñ}¥(€€€€€€€t(€€€€€€€™½½‘Ì€ôl(€€€€€€€€€€€¥Ñ•´(€€€€€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹™½½‘}…Ñ¥Ù…Ñ¥½¹}•Ù¥‘•¹”(€€€€€€€€€€€¥˜¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥€ôô…‰¥±¥Ñä¹½‰©•Ñ}¥(€€€€€€€t(€€€€€€€¥˜±•¸¡…Ñ¥Ù…Ñ¥½¹Ì¤€„ô€Ä½È±•¸¡™½½‘Ì¤€„ô€Äè(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½½ÍÑ…¬½‰©•Ð±…­ÌÕ¹¥ÅÕ”…Ñ¥Ù…Ñ¥½¸ÁÉ½Ù•¹…¹”ˆ¤(€€€€€€€…Ñ¥Ù…Ñ¥½¸€ô…Ñ¥Ù…Ñ¥½¹ÍlÁt(€€€€€€€™½½€ô™½½‘ÍlÁt(€€€€€€€Í…É¥™¥•€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡™½½¹Í…É¥™¥•‘}‘•ÍÑ¥¹…Ñ¥½¹}¥¤(€€€€€€€¥˜€ (€€€€€€€€€€€…Ñ¥Ù…Ñ¥½¸¹É•Í½±Ù•€„ô™½½¹É•Í½±Ù•(€€€€€€€€€€€½È…‰¥±¥Ñä¹Í½ÕÉ•}¥€„ô…Ñ¥Ù…Ñ¥½¸¹Í½ÕÉ•}¥(€€€€€€€€€€€½È…‰¥±¥Ñä¹Í½ÕÉ•}¥€„ô™½½¹Í½ÕÉ•}¥(€€€€€€€€€€€½È…‰¥±¥Ñä¹½¹ÑÉ½±±•È€„ô…Ñ¥Ù…Ñ¥½¸¹½¹ÑÉ½±±•È(€€€€€€€€€€€½È…‰¥±¥Ñä¹½¹ÑÉ½±±•È€„ô™½½¹½¹ÑÉ½±±•È(€€€€€€€€€€€½È…‰¥±¥Ñä¹½É…±•}™É…µ•¹Ð€„ô…Ñ¥Ù…Ñ¥½¸¹½É…±•}™É…µ•¹Ð(€€€€€€€€€€€½È…‰¥±¥Ñä¹½É…±•}™É…µ•¹Ð€„ô™½½¹½É…±•}™É…µ•¹Ð(€€€€€€€€€€€½È…‰¥±¥Ñä¹µ…¹…}Í½ÕÉ•}¥‘Ì€„ô…Ñ¥Ù…Ñ¥½¸¹µ…¹…}Í½ÕÉ•}¥‘Ì(€€€€€€€€€€€½È…‰¥±¥Ñä¹µ…¹…}Í½ÕÉ•}¥‘Ì€„ô™½½¹µ…¹…}Í½ÕÉ•}¥‘Ì(€€€€€€€€€€€½È…‰¥±¥Ñä¹Ñ…Á}Í½ÕÉ”€„ô…Ñ¥Ù…Ñ¥½¸¹Ñ…Á}Í½ÕÉ”(€€€€€€€€€€€½È…‰¥±¥Ñä¹Ñ…Á}Í½ÕÉ”€„ô™½½¹Ñ…Á}Á…¥(€€€€€€€€€€€½È¹½Ð…‰¥±¥Ñä¹Í…É¥™¥•}Í½ÕÉ”(€€€€€€€€€€€½È¹½Ð™½½¹Í…É¥™¥•}Á…¥(€€€€€€€€€€€½È…‰¥±¥Ñä¹Í…É¥™¥•‘}‘•ÍÑ¥¹…Ñ¥½¹}¥€„ô™½½¹Í…É¥™¥•‘}‘•ÍÑ¥¹…Ñ¥½¹}¥(€€€€€€€€€€€½È…‰¥±¥Ñä¹Í½ÕÉ•}…É¹¹…µ”€„ô™½½¹Í½ÕÉ•}¹…µ”(€€€€€€€€€€€½È…‰¥±¥Ñä¹Í½ÕÉ•}…É¹ÑåÁ•}±¥¹”€„ô™½½¹Í½ÕÉ•}ÑåÁ•}±¥¹”(€€€€€€€€€€€½È¹½Ð¥Í¥¹ÍÑ…¹”¡Í…É¥™¥•°…É‘=‰©•Ð¤(€€€€€€€€€€€½ÈÍ…É¥™¥•¹…É€„ô…‰¥±¥Ñä¹Í½ÕÉ•}…É(€€€€€€€€€€€½ÈÍ…É¥™¥•¹½Ý¹•È€„ô™½½¹Í½ÕÉ•}½Ý¹•È(€€€€€€€€€€€½ÈÍ…É¥™¥•¹¥Í}Ñ½­•¸€„ô™½½¹Í½ÕÉ•}Ý…Í}Ñ½­•¸(€€€€€€€€€€€½È…‰¥±¥Ñä¹ÁÉ½É…´¹•™™•Ñ}­¥¹¥Ì¹½ÐÑ¥Ù…Ñ•‘™™•Ñ-¥¹¹%9}Q!I}1%(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½½ÍÑ…¬½‰©•Ð‘¥Í…É••ÌÝ¥Ñ …Ñ¥Ù…Ñ¥½¸ÁÉ½Ù•¹…¹”ˆ¤((€€€‘•˜Á…åµ•¹Ñ}Á±…¸ (€€€€€€€Í•±˜°(€€€€€€€Á±…å•É}¥¹‘•àè¥¹Ð°(€€€€€€€…Éè…É‘=‰©•Ð°(€€€€€€€€¨°(€€€€€€€…±±½Ý}É…Ù•å…Éè‰½½°€ô…±Í”°(€€€€€€€…±±½Ý}•á¥±”è‰½½°€ô…±Í”°(€€€€€€€á}Ù…±Õ”è¥¹Ðð9½¹”€ô9½¹”°(€€€€¤€´øA…åµ•¹ÑA±…¸ð9½¹”è(€€€€€€€Í½ÕÉ•}é½¹”€ô€‰É…Ù•å…Éˆ¥˜…±±½Ý}É…Ù•å…É•±Í”€ ‰•á¥±”ˆ¥˜…±±½Ý}•á¥±”•±Í”€‰¡…¹ˆ¤(€€€€€€€¥˜€ (€€€€€€€€€€€¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡…É°Í½ÕÉ•}é½¹”¤(€€€€€€€€€€€½È€¡…±±½Ý}•á¥±”…¹Í•±˜¹}±¥¹­•‘}Á±…å}É…¹Ñ}™½È¡Á±…å•É}¥¹‘•à°…É¤¥Ì9½¹”¤(€€€€€€€€€€€½È€¡…É¹½Ý¹•È€„ôÁ±…å•É}¥¹‘•à…¹¹½Ð…±±½Ý}•á¥±”¤(€€€€€€€€¤è(€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€É•ÅÕ¥É•µ•¹Ð€ôÍ•±˜¹…ÍÑ¥¹}É•ÅÕ¥É•µ•¹Ð¡Á±…å•É}¥¹‘•à°…É°á}Ù…±Õ”õá}Ù…±Õ”¤(€€€€€€€¥˜É•ÅÕ¥É•µ•¹Ð¥Ì9½¹”è(€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€…Ù…¥±…‰±”€ôl(€€€€€€€€€€€À™½ÈÀ¥¸Í•±˜¹Á±…å•ÉÍmÁ±…å•É}¥¹‘•át¹‰…ÑÑ±•™¥•±¥˜À¹…É¹¥Í}±…¹…¹¹½ÐÀ¹Ñ…ÁÁ•(€€€€€€€t(€€€€€€€ÍÁ•±±}ÑåÁ•Ì€ô…É¹…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€½¹Ñ•áÐ€ô€‰…ÉÑ¥™…Ñ}ÍÁ•±°ˆ¥˜€‰ÉÑ¥™…Ðˆ¥¸ÍÁ•±±}ÑåÁ•Ì•±Í”€‰½Ñ¡•É}ÍÁ•±°ˆ(€€€€€€€Í•±•Ñ•€ôÍ•±˜¹}Á±…¹}µ…¹…}Ý¥Ñ¡}™±½…Ñ¥¹œ¡Á±…å•É}¥¹‘•à°É•ÅÕ¥É•µ•¹Ð°…Ù…¥±…‰±”°½¹Ñ•áÐ¤(€€€€€€€¥˜Í•±•Ñ•¥Ì9½¹”è(€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€™±½…Ñ¥¹œ°•Ù•¹Ñ}¥‘Ì°¡½Í•¸€ôÍ•±•Ñ•(€€€€€€€É•ÑÕÉ¸A…åµ•¹ÑA±…¸ (€€€€€€€€€€€Á±…å•É}¥¹‘•à°(€€€€€€€€€€€…É¹½‰©•Ñ}¥°(€€€€€€€€€€€É•ÅÕ¥É•µ•¹Ð°(€€€€€€€€€€€ÑÕÁ±”¡À¹½‰©•Ñ}¥™½ÈÀ¥¸¡½Í•¸¤°(€€€€€€€€€€€™±½…Ñ¥¹œ°(€€€€€€€€€€€•Ù•¹Ñ}¥‘Ì°(€€€€€€€€€€€á}Ù…±Õ”°(€€€€€€€€¤((€€€‘•˜…¹}…™™½É¡Í•±˜°Á±…å•É}¥¹‘•àè¥¹Ð°…Éè…É‘…Ðð…É‘=‰©•Ð¤€´ø‰½½°è(€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡…É°…É‘=‰©•Ð¤è(€€€€€€€€€€€É•ÑÕÉ¸Í•±˜¹Á…åµ•¹Ñ}Á±…¸¡Á±…å•É}¥¹‘•à°…É¤¥Ì¹½Ð9½¹”(€€€€€€€É•ÅÕ¥É•µ•¹Ð€ôÍ•±˜¹…ÍÑ¥¹}É•ÅÕ¥É•µ•¹Ð¡Á±…å•É}¥¹‘•à°…É¤(€€€€€€€¥˜É•ÅÕ¥É•µ•¹Ð¥Ì9½¹”è(€€€€€€€€€€€É•ÑÕÉ¸…±Í”(€€€€€€€…Ù…¥±…‰±”€ôl(€€€€€€€€€€€Á•Éµ…¹•¹Ð(€€€€€€€€€€€™½ÈÁ•Éµ…¹•¹Ð¥¸Í•±˜¹Á±…å•ÉÍmÁ±…å•É}¥¹‘•át¹‰…ÑÑ±•™¥•±(€€€€€€€€€€€¥˜Á•Éµ…¹•¹Ð¹…É¹¥Í}±…¹…¹¹½ÐÁ•Éµ…¹•¹Ð¹Ñ…ÁÁ•(€€€€€€€t(€€€€€€€É•ÑÕÉ¸€ (€€€€€€€€€€€Í•±˜¹}Á±…¹}µ…¹…}Ý¥Ñ¡}™±½…Ñ¥¹œ (€€€€€€€€€€€€€€€Á±…å•É}¥¹‘•à°(€€€€€€€€€€€€€€€É•ÅÕ¥É•µ•¹Ð°(€€€€€€€€€€€€€€€…Ù…¥±…‰±”°(€€€€€€€€€€€€€€€€‰…ÉÑ¥™…Ñ}ÍÁ•±°ˆ(€€€€€€€€€€€€€€€¥˜€‰ÉÑ¥™…Ðˆ¥¸…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€€€€€€€€€•±Í”€‰½Ñ¡•É}ÍÁ•±°ˆ°(€€€€€€€€€€€€¤(€€€€€€€€€€€¥Ì¹½Ð9½¹”(€€€€€€€€¤((€€€‘•˜}½µµ¥Ñ}…¹¹½Õ¹•µ•¹Ñ}Á…åµ•¹Ð (€€€€€€€Í•±˜°(€€€€€€€…Éè…É‘=‰©•Ð°(€€€€€€€Á±…¸èA…åµ•¹ÑA±…¸°(€€€€€€€€¨°(€€€€€€€…ÍÑ}­¥¹è…ÍÑ-¥¹°(€€€€€€€Ñ…É•Ñ}¥èÍÑÈð9½¹”°(€€€€€€€…ÍÑ}™É½µ}É…Ù•å…Éè‰½½°€ô…±Í”°(€€€€€€€™¥¹…±¥Ñå}½¹}•¹ÑÉäè‰½½°€ô…±Í”°(€€€€€€€…ÍÑ}™É½µ}É…Á¡…•°è‰½½°€ô…±Í”°(€€€€¤€´øMÑ…­=‰©•Ðè(€€€€€€€€ˆˆ‰Ñ½µ¥…±±äÁ…ä„É•Ù…±¥‘…Ñ•Á±…¸…¹µ½Ù”Ñ¡”É•ÁÉ•Í•¹Ñ•…É!…¹€´øMÑ…¬¸ˆˆˆ(€€€€€€€¥˜Á±…¸€„ôÍ•±˜¹Á…åµ•¹Ñ}Á±…¸ (€€€€€€€€€€€Á±…¸¹Á±…å•É}¥¹‘•à°(€€€€€€€€€€€…É°(€€€€€€€€€€€…±±½Ý}É…Ù•å…Éõ…ÍÑ}™É½µ}É…Ù•å…É°(€€€€€€€€€€€…±±½Ý}•á¥±”õ…ÍÑ}™É½µ}É…Á¡…•°°(€€€€€€€€€€€á}Ù…±Õ”õÁ±…¸¹á}Ù…±Õ”°(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰Á…åµ•¹ÐÁ±…¸¥Ì¹¼±½¹•È±•…°ˆ¤(€€€€€€€Í½ÕÉ•Ìè±¥ÍÑmA•Éµ…¹•¹Ñt€ômt(€€€€€€€™½È½‰©•Ñ}¥¥¸Á±…¸¹Í½ÕÉ•}¥‘Ìè(€€€€€€€€€€€Í½ÕÉ”€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡½‰©•Ñ}¥¤(€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡Í½ÕÉ”°A•Éµ…¹•¹Ð¤½È¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù” (€€€€€€€€€€€€€€€Í½ÕÉ”°€‰‰…ÑÑ±•™¥•±ˆ(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰Á…åµ•¹ÐÍ½ÕÉ”¥Ì¹½Ð…ÕÑ¡½É¥Ñ…Ñ¥Ù”ˆ¤(€€€€€€€€€€€Í½ÕÉ•Ì¹…ÁÁ•¹¡Í½ÕÉ”¤(€€€€€€€ÁÉ•Ù¥½ÕÍ}Ñ…ÁÁ•€ôÑÕÁ±”¡Í½ÕÉ”¹Ñ…ÁÁ•™½ÈÍ½ÕÉ”¥¸Í½ÕÉ•Ì¤(€€€€€€€ÑÉäè(€€€€€€€€€€€™½ÈÍ½ÕÉ”¥¸Í½ÕÉ•Ìè(€€€€€€€€€€€€€€€Í½ÕÉ”¹Ñ…ÁÁ•€ôQÉÕ”(€€€€€€€€€€€ÍÁ•±°€ôÍ•±˜¹µ½Ù•}½‰©•Ð (€€€€€€€€€€€€€€€…É°(€€€€€€€€€€€€€€€€‰ÍÑ…¬ˆ°(€€€€€€€€€€€€€€€½¹ÑÉ½±±•ÈõÁ±…¸¹Á±…å•É}¥¹‘•à°(€€€€€€€€€€€€€€€…ÍÑ}­¥¹õ…ÍÑ}­¥¹°(€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÑ…É•Ñ}¥°(€€€€€€€€€€€€€€€…ÍÑ}™É½µ}É…Ù•å…Éõ…ÍÑ}™É½µ}É…Ù•å…É°(€€€€€€€€€€€€€€€™¥¹…±¥Ñå}½¹}•¹ÑÉäõ™¥¹…±¥Ñå}½¹}•¹ÑÉä°(€€€€€€€€€€€€€€€…ÍÑ}™É½µ}É…Á¡…•°õ…ÍÑ}™É½µ}É…Á¡…•°°(€€€€€€€€€€€€€€€É•…Í½¸ô‰ÍÁ•±±}…ÍÑ}™É½µ}É…Ù•å…Éˆ¥˜…ÍÑ}™É½µ}É…Ù•å…É•±Í”€‰ÍÁ•±±}…ÍÐˆ°(€€€€€€€€€€€€¤(€€€€€€€•á•ÁÐá•ÁÑ¥½¸è(€€€€€€€€€€€™½ÈÍ½ÕÉ”°Ñ…ÁÁ•¥¸é¥À¡Í½ÕÉ•Ì°ÁÉ•Ù¥½ÕÍ}Ñ…ÁÁ•°ÍÑÉ¥ÐõQÉÕ”¤è(€€€€€€€€€€€€€€€Í½ÕÉ”¹Ñ…ÁÁ•€ôÑ…ÁÁ•(€€€€€€€€€€€É…¥Í”(€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡ÍÁ•±°°MÑ…­=‰©•Ð¤(€€€€€€€ÍÁ•±°¹á}Ù…±Õ”€ôÁ±…¸¹á}Ù…±Õ”(€€€€€€€Í•±˜¹™±½…Ñ¥¹}µ…¹„¹½¹ÍÕµ•}•Ù•¹ÑÌ (€€€€€€€€€€€Á±…¸¹Á±…å•É}¥¹‘•à°(€€€€€€€€€€€Á±…¸¹™±½…Ñ¥¹}•Ù•¹Ñ}¥‘Ì°(€€€€€€€€€€€…É¹½‰©•Ñ}¥°(€€€€€€€€€€€€‰…ÉÑ¥™…Ñ}ÍÁ•±°ˆ(€€€€€€€€€€€¥˜€‰ÉÑ¥™…Ðˆ¥¸…É¹…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€€€€€•±Í”€‰½Ñ¡•É}ÍÁ•±°ˆ°(€€€€€€€€¤(€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€‰½ÍÑ}Á…¥ˆ°(€€€€€€€€€€€Á±…å•ÈõÍ•±˜¹Á±…å•ÉÍmÁ±…¸¹Á±…å•É}¥¹‘•át¹¹…µ”°(€€€€€€€€€€€…Éõ…É¹¹…µ”°(€€€€€€€€€€€•¹•É¥ŒõÁ±…¸¹É•ÅÕ¥É•µ•¹Ð¹•¹•É¥Œ°(€€€€€€€€€€€½±½É•õ±¥ÍÐ¡Á±…¸¹É•ÅÕ¥É•µ•¹Ð¹½±½É•¤°(€€€€€€€€€€€Í½ÕÉ•}¥‘Ìõ±¥ÍÐ¡Á±…¸¹Í½ÕÉ•}¥‘Ì¤°(€€€€€€€€€€€™±½…Ñ¥¹}•Ù•¹Ñ}¥‘Ìõ±¥ÍÐ¡Á±…¸¹™±½…Ñ¥¹}•Ù•¹Ñ}¥‘Ì¤°(€€€€€€€€€€€á}Ù…±Õ”õÁ±…¸¹á}Ù…±Õ”°(€€€€€€€€¤(€€€€€€€ÁÉ¥¹Ñ•€ôÍ•±˜¹µ…¹…}É•ÅÕ¥É•µ•¹Ð¡…É¤(€€€€€€€¥˜ÁÉ¥¹Ñ•¥Ì¹½Ð9½¹”…¹Á±…¸¹É•ÅÕ¥É•µ•¹Ð¹•¹•É¥Œ€ðÁÉ¥¹Ñ•¹•¹•É¥Œè(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰…ÍÑ¥¹}½ÍÑ}É•‘Õ•ˆ°(€€€€€€€€€€€€€€€Á±…å•ÈõÍ•±˜¹Á±…å•ÉÍmÁ±…¸¹Á±…å•É}¥¹‘•át¹¹…µ”°(€€€€€€€€€€€€€€€…Éõ…É¹¹…µ”°(€€€€€€€€€€€€€€€ÁÉ¥¹Ñ•‘}•¹•É¥ŒõÁÉ¥¹Ñ•¹•¹•É¥Œ°(€€€€€€€€€€€€€€€Á…¥‘}•¹•É¥ŒõÁ±…¸¹É•ÅÕ¥É•µ•¹Ð¹•¹•É¥Œ°(€€€€€€€€€€€€€€€É•‘ÕÑ¥½¹Ìõl(€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€‰½É…±•}™É…µ•¹ÐˆèÁÉ½É…´¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€‰…µ½Õ¹ÐˆèÁÉ½É…´¹…µ½Õ¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€‰Á•É}Á•Éµ…¹•¹ÐˆèÁÉ½É…´¹Á•É}Á•Éµ…¹•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÅÕ…±¥™å¥¹}Í½ÕÉ•}¥‘Ìˆè±¥ÍÐ¡Í½ÕÉ•Ì¤°(€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€™½ÈÁÉ½É…´°Í½ÕÉ•Ì¥¸Í•±˜¹}…ÍÑ¥¹}É•‘ÕÑ¥½¹Ì¡Á±…¸¹Á±…å•É}¥¹‘•à°…É¤(€€€€€€€€€€€€€€€€€€€¥˜Í½ÕÉ•Ì(€€€€€€€€€€€€€€€t°(€€€€€€€€€€€€¤(€€€€€€€É•ÑÕÉ¸ÍÁ•±°((€€€‘•˜}½µµ¥Ñ}Í¹•…­}…¹¹½Õ¹•µ•¹Ð (€€€€€€€Í•±˜°(€€€€€€€…Éè…É‘=‰©•Ð°(€€€€€€€…ÑÑ…­•ÈèA•Éµ…¹•¹Ð°(€€€€€€€Á±…¸èM¹•…­A…åµ•¹ÑA±…¸°(€€€€€€€€¨°(€€€€€€€Ñ…É•Ðõ9½¹”°(€€€€€€€É•ÕÉÍ¥½¹}Ñ…É•ÑÌèÑÕÁ±•m½‰©•Ð°€¸¸¹t€ô€ ¤°(€€€€¤€´øMÑ…­=‰©•Ðè(€€€€€€€€ˆˆ‰Ñ½µ¥…±±äÁ…ä™¥á•M¹•…¬µ…¹„Á±ÕÌÑ¡”…ÕÑ¡½É¥Ñ…Ñ¥Ù”É•ÑÕÉ¸½ÍÐ¸ˆˆˆ(€€€€€€€¥˜Á±…¸€„ôÍ•±˜¹Í¹•…­}Á…åµ•¹Ñ}Á±…¸ (€€€€€€€€€€€Á±…¸¹Á±…å•É}¥¹‘•à°…É°…ÑÑ…­•È°½É…±•}™É…µ•¹ÐõÁ±…¸¹½É…±•}™É…µ•¹Ð(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰M¹•…¬Á…åµ•¹ÐÁ±…¸¥Ì¹¼±½¹•È±•…°ˆ¤(€€€€€€€É•µ½Ù…°€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹Ñ…É•Ñ•‘}É•µ½Ù…±}ÁÉ½É…´¡…É¹…É¤(€€€€€€€¥˜É•µ½Ù…°¥Ì¹½Ð9½¹”…¹¹½ÐÍ•±˜¹}±•…±}Ñ…É•Ñ•‘}É•µ½Ù…±}Ñ…É•Ð (€€€€€€€€€€€Ñ…É•Ð°Á±…¸¹Á±…å•É}¥¹‘•à°É•µ½Ù…°(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰M¹•…¬Ñ…É•Ð¥Ì¹¼±½¹•È±•…°ˆ¤(€€€€€€€¥˜É•µ½Ù…°¥Ì9½¹”…¹Ñ…É•Ð¥Ì¹½Ð9½¹”è(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰Õ¹Ñ…É•Ñ•M¹•…¬ÍÁ•±°…¹¹½Ð…¹¹½Õ¹”„Ñ…É•Ðˆ¤(€€€€€€€É•ÕÉÍ¥½¸€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹É…Ù•å…É‘}É•ÕÉÍ¥½¹}ÁÉ½É…´¡…É¹…É¤(€€€€€€€¥˜É•ÕÉÍ¥½¸¥Ì¹½Ð9½¹”è(€€€€€€€€€€€¥˜¹½ÐÍ•±˜¹}Ù…±¥‘}É…Ù•å…É‘}É•ÕÉÍ¥½¹}Ñ…É•ÑÌ (€€€€€€€€€€€€€€€É•ÕÉÍ¥½¹}Ñ…É•ÑÌ°Á±…¸¹Á±…å•É}¥¹‘•à°É•ÕÉÍ¥½¸¹µ…¹…}Ù…±Õ•}±¥µ¥Ð(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰M¹•…¬É•ÕÉÍ¥½¸Ñ…É•ÑÌ…É”¹¼±½¹•È±•…°ˆ¤(€€€€€€€•±¥˜É•ÕÉÍ¥½¹}Ñ…É•ÑÌè(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰¹½¹É•ÕÉÍ¥½¸M¹•…¬ÍÁ•±°…¹¹½Ð…¹¹½Õ¹”É…Ù•å…ÉÑ…É•ÑÌˆ¤(€€€€€€€Í½ÕÉ•Ìè±¥ÍÑmA•Éµ…¹•¹Ñt€ômt(€€€€€€€™½È½‰©•Ñ}¥¥¸Á±…¸¹µ…¹…}Í½ÕÉ•}¥‘Ìè(€€€€€€€€€€€Í½ÕÉ”€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡½‰©•Ñ}¥¤(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€¹½Ð¥Í¥¹ÍÑ…¹”¡Í½ÕÉ”°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€½È¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Í½ÕÉ”°€‰‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€€€€€€€€€½ÈÍ½ÕÉ”¹Ñ…ÁÁ•(€€€€€€€€€€€€€€€½È¹½ÐÍ½ÕÉ”¹…É¹¥Í}±…¹(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰M¹•…¬µ…¹„Í½ÕÉ”¥Ì¹½Ð…ÕÑ¡½É¥Ñ…Ñ¥Ù”ˆ¤(€€€€€€€€€€€Í½ÕÉ•Ì¹…ÁÁ•¹¡Í½ÕÉ”¤(€€€€€€€¥˜±•¸¡íÍ½ÕÉ”¹½‰©•Ñ}¥™½ÈÍ½ÕÉ”¥¸Í½ÕÉ•Íô¤€„ô±•¸¡Í½ÕÉ•Ì¤è(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰M¹•…¬Á…åµ•¹Ð…¹¹½ÐÉ•ÕÍ”„µ…¹„Í½ÕÉ”ˆ¤((€€€€€€€€Œ½¹ÍÑÉÕÐ‰½Ñ ¹•Üé½¹”¥¹…É¹…Ñ¥½¹Ì‰•™½É”µÕÑ…Ñ¥¹œ…¹ä…ÕÑ¡½É¥Ñ…Ñ¥Ù”½¹Ñ…¥¹•È¸(€€€€€€€É•ÑÕÉ¹•€ô…É‘=‰©•Ð (€€€€€€€€€€€Í•±˜¹}…±±½…Ñ•}½‰©•Ñ}¥ ¤°(€€€€€€€€€€€…ÑÑ…­•È¹…É°(€€€€€€€€€€€…ÑÑ…­•È¹½Ý¹•È°(€€€€€€€€€€€…ÑÑ…­•È¹½Ý¹•È°(€€€€€€€€€€€€‰¡…¹ˆ°(€€€€€€€€€€€¥Í}Ñ½­•¸õ…ÑÑ…­•È¹¥Í}Ñ½­•¸°(€€€€€€€€¤(€€€€€€€ÍÁ•±°€ôMÑ…­=‰©•Ð (€€€€€€€€€€€Í•±˜¹}…±±½…Ñ•}½‰©•Ñ}¥ ¤°(€€€€€€€€€€€…É¹…É°(€€€€€€€€€€€…É¹½Ý¹•È°(€€€€€€€€€€€Á±…¸¹Á±…å•É}¥¹‘•à°(€€€€€€€€€€€Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹…ÍÑ}ÁÉ½É…´¡…É¹…É¤¹­¥¹°(€€€€€€€€€€€Ñ…É•Ñ}¥õÑ…É•Ð¹½‰©•Ñ}¥¥˜Ñ…É•Ð¥Ì¹½Ð9½¹”•±Í”9½¹”°(€€€€€€€€€€€Ñ…É•Ñ}¥‘ÌõÑÕÁ±”¡¥Ñ•´¹½‰©•Ñ}¥™½È¥Ñ•´¥¸É•ÕÉÍ¥½¹}Ñ…É•ÑÌ¤°(€€€€€€€€€€€Í¹•…­}É•ÑÕÉ¹•‘}…ÑÑ…­•É}¥õ…ÑÑ…­•È¹½‰©•Ñ}¥°(€€€€€€€€€€€Í¹•…­}É•ÑÕÉ¹•‘}¡…¹‘}¥õÉ•ÑÕÉ¹•¹½‰©•Ñ}¥°(€€€€€€€€€€€Í¹•…­}‘•™•¹‘¥¹}Á±…å•ÈõÁ±…¸¹‘•™•¹‘¥¹}Á±…å•È°(€€€€€€€€€€€Í¹•…­}½É…±•}™É…µ•¹ÐõÁ±…¸¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€Í¹•…­}µ…¹…}Í½ÕÉ•}¥‘ÌõÁ±…¸¹µ…¹…}Í½ÕÉ•}¥‘Ì°(€€€€€€€€€€€…ÍÑ}™É½µ}É…Ù•å…ÉõÁ±…¸¹Í½ÕÉ•}é½¹”€ôô€‰É…Ù•å…Éˆ°(€€€€€€€€¤((€€€€€€€‰…ÑÑ±•™¥•±€ôÍ•±˜¹Á±…å•ÉÍm…ÑÑ…­•È¹½¹ÑÉ½±±•Ét¹‰…ÑÑ±•™¥•±(€€€€€€€Í½ÕÉ•}é½¹”€ô…É¹é½¹”(€€€€€€€É…¹Ð€ô€ (€€€€€€€€€€€Í•±˜¹}±¥¹­•‘}Á±…å}É…¹Ñ}™½È¡Á±…¸¹Á±…å•É}¥¹‘•à°…É¤¥˜Í½ÕÉ•}é½¹”€ôô€‰•á¥±”ˆ•±Í”9½¹”(€€€€€€€€¤(€€€€€€€Í½ÕÉ•}…É‘Ì€ôì(€€€€€€€€€€€€‰¡…¹ˆèÍ•±˜¹Á±…å•ÉÍm…É¹½Ý¹•Ét¹¡…¹°(€€€€€€€€€€€€‰•á¥±”ˆèÍ•±˜¹Á±…å•ÉÍm…É¹½Ý¹•Ét¹•á¥±”°(€€€€€€€€€€€€‰É…Ù•å…ÉˆèÍ•±˜¹Á±…å•ÉÍm…É¹½Ý¹•Ét¹É…Ù•å…É°(€€€€€€€õmÍ½ÕÉ•}é½¹•t(€€€€€€€¥˜¹½ÐÍ•±˜¹}¥‘•¹Ñ¥Ñå}½¹Ñ…¥¹Ì¡‰…ÑÑ±•™¥•±°…ÑÑ…­•È¤½È¹½ÐÍ•±˜¹}¥‘•¹Ñ¥Ñå}½¹Ñ…¥¹Ì (€€€€€€€€€€€Í½ÕÉ•}…É‘Ì°…É(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰M¹•…¬Í½ÕÉ”é½¹•Ì¡…¹•‰•™½É”½µµ¥Ñµ•¹Ðˆ¤(€€€€€€€…ÑÑ…­•É}¥¹‘•à€ô¹•áÐ¡¤™½È¤°Ù…±Õ”¥¸•¹Õµ•É…Ñ”¡‰…ÑÑ±•™¥•±¤¥˜Ù…±Õ”¥Ì…ÑÑ…­•È¤(€€€€€€€…É‘}¥¹‘•à€ô¹•áÐ¡¤™½È¤°Ù…±Õ”¥¸•¹Õµ•É…Ñ”¡Í½ÕÉ•}…É‘Ì¤¥˜Ù…±Õ”¥Ì…É¤(€€€€€€€™½ÈÍ½ÕÉ”¥¸Í½ÕÉ•Ìè(€€€€€€€€€€€Í½ÕÉ”¹Ñ…ÁÁ•€ôQÉÕ”(€€€€€€€‰…ÑÑ±•™¥•±¹Á½À¡…ÑÑ…­•É}¥¹‘•à¤(€€€€€€€Í½ÕÉ•}…É‘Ì¹Á½À¡…É‘}¥¹‘•à¤(€€€€€€€Í•±˜¹Á±…å•ÉÍm…ÑÑ…­•È¹½Ý¹•Ét¹¡…¹¹…ÁÁ•¹¡É•ÑÕÉ¹•¤(€€€€€€€Í•±˜¹ÍÑ…¬¹…ÁÁ•¹¡ÍÁ•±°¤(€€€€€€€…ÑÑ…­•È¹é½¹”€ô€‰™½Éµ•Èˆ(€€€€€€€…É¹é½¹”€ô€‰™½Éµ•Èˆ(€€€€€€€Í•±˜¹}É•¥ÍÑ•È¡É•ÑÕÉ¹•¤(€€€€€€€Í•±˜¹}É•¥ÍÑ•È¡ÍÁ•±°¤(€€€€€€€¥˜É…¹Ð¥Ì¹½Ð9½¹”è(€€€€€€€€€€€ÍÁ•±°¹…ÍÑ}™É½µ}É…Á¡…•°€ôQÉÕ”(€€€€€€€€€€€Í•±˜¹}½¹ÍÕµ•}±¥¹­•‘}Á±…å}É…¹Ð¡É…¹Ð°…É¹½‰©•Ñ}¥¤(€€€€€€€Í•±˜¹}½µ‰…Ñ}…ÑÑ…­•ÉÌ€ôÑÕÁ±” (€€€€€€€€€€€½‰©•Ñ}¥™½È½‰©•Ñ}¥¥¸Í•±˜¹}½µ‰…Ñ}…ÑÑ…­•ÉÌ¥˜½‰©•Ñ}¥€„ô…ÑÑ…­•È¹½‰©•Ñ}¥(€€€€€€€€¤(€€€€€€€Í•±˜¹}½µ‰…Ñ}‰±½­Ì€ôÑÕÁ±” (€€€€€€€€€€€Á…¥È™½ÈÁ…¥È¥¸Í•±˜¹}½µ‰…Ñ}‰±½­Ì¥˜Á…¥ÉlÁt€„ô…ÑÑ…­•È¹½‰©•Ñ}¥(€€€€€€€€¤(€€€€€€€Í•±˜¹É•™É•Í¡}ÍÑ…Ñ¥}ÁÑ}µ½‘¥™¥•ÉÌ ¤((€€€€€€€Í•±˜¹™±½…Ñ¥¹}µ…¹„¹½¹ÍÕµ•}•Ù•¹ÑÌ (€€€€€€€€€€€Á±…¸¹Á±…å•É}¥¹‘•à°(€€€€€€€€€€€Á±…¸¹™±½…Ñ¥¹}•Ù•¹Ñ}¥‘Ì°(€€€€€€€€€€€…É¹½‰©•Ñ}¥°(€€€€€€€€€€€€‰…ÉÑ¥™…Ñ}ÍÁ•±°ˆ(€€€€€€€€€€€¥˜€‰ÉÑ¥™…Ðˆ¥¸…É¹…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€€€€€•±Í”€‰½Ñ¡•É}ÍÁ•±°ˆ°(€€€€€€€€¤(€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€‰é½¹•}¡…¹•ˆ°(€€€€€€€€€€€…Éõ…ÑÑ…­•È¹…É¹¹…µ”°(€€€€€€€€€€€½Ý¹•ÈõÍ•±˜¹Á±…å•ÉÍm…ÑÑ…­•È¹½Ý¹•Ét¹¹…µ”°(€€€€€€€€€€€Í½ÕÉ•}½‰©•Ñ}¥õ…ÑÑ…­•È¹½‰©•Ñ}¥°(€€€€€€€€€€€‘•ÍÑ¥¹…Ñ¥½¹}½‰©•Ñ}¥õÉ•ÑÕÉ¹•¹½‰©•Ñ}¥°(€€€€€€€€€€€Í½ÕÉ•}é½¹”ô‰‰…ÑÑ±•™¥•±ˆ°(€€€€€€€€€€€‘•ÍÑ¥¹…Ñ¥½¹}é½¹”ô‰¡…¹ˆ°(€€€€€€€€€€€É•…Í½¸ô‰Í¹•…­}É•ÑÕÉ¹}½ÍÐˆ°(€€€€€€€€¤(€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€‰é½¹•}¡…¹•ˆ°(€€€€€€€€€€€…Éõ…É¹…É¹¹…µ”°(€€€€€€€€€€€½Ý¹•ÈõÍ•±˜¹Á±…å•ÉÍm…É¹½Ý¹•Ét¹¹…µ”°(€€€€€€€€€€€Í½ÕÉ•}½‰©•Ñ}¥õ…É¹½‰©•Ñ}¥°(€€€€€€€€€€€‘•ÍÑ¥¹…Ñ¥½¹}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€Í½ÕÉ•}é½¹”õÍ½ÕÉ•}é½¹”°(€€€€€€€€€€€‘•ÍÑ¥¹…Ñ¥½¹}é½¹”ô‰ÍÑ…¬ˆ°(€€€€€€€€€€€É•…Í½¸ô‰Í¹•…­}ÍÁ•±±}…ÍÐˆ°(€€€€€€€€¤(€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€‰Í¹•…­}½ÍÑ}Á…¥ˆ°(€€€€€€€€€€€Á±…å•ÈõÍ•±˜¹Á±…å•ÉÍmÁ±…¸¹Á±…å•É}¥¹‘•át¹¹…µ”°(€€€€€€€€€€€…Éõ…É¹…É¹¹…µ”°(€€€€€€€€€€€µ…¹…}Í½ÕÉ•}¥‘Ìõ±¥ÍÐ¡Á±…¸¹µ…¹…}Í½ÕÉ•}¥‘Ì¤°(€€€€€€€€€€€™±½…Ñ¥¹}•Ù•¹Ñ}¥‘Ìõ±¥ÍÐ¡Á±…¸¹™±½…Ñ¥¹}•Ù•¹Ñ}¥‘Ì¤°(€€€€€€€€€€€É•ÑÕÉ¹•‘}…ÑÑ…­•É}¥õ…ÑÑ…­•È¹½‰©•Ñ}¥°(€€€€€€€€€€€É•ÑÕÉ¹•‘}¡…¹‘}¥õÉ•ÑÕÉ¹•¹½‰©•Ñ}¥°(€€€€€€€€¤(€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€‰Í¹•…­}…¹¹½Õ¹•ˆ°(€€€€€€€€€€€Á±…å•ÈõÍ•±˜¹Á±…å•ÉÍmÁ±…¸¹Á±…å•É}¥¹‘•át¹¹…µ”°(€€€€€€€€€€€…ÉõÍÁ•±°¹¹…µ”°(€€€€€€€€€€€¡…¹‘}½‰©•Ñ}¥õ…É¹½‰©•Ñ}¥°(€€€€€€€€€€€Í½ÕÉ•}é½¹”õÍ½ÕÉ•}é½¹”°(€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÁ±…¸¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€Á•Éµ¥ÍÍ¥½¹}Í½ÕÉ•}¥õÁ±…¸¹Á•Éµ¥ÍÍ¥½¹}Í½ÕÉ•}¥°(€€€€€€€€¤(€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€‰ÍÁ•±±}…ÍÐˆ°(€€€€€€€€€€€Á±…å•ÈõÍ•±˜¹Á±…å•ÉÍmÁ±…¸¹Á±…å•É}¥¹‘•át¹¹…µ”°(€€€€€€€€€€€Á±…å•É}¥¹‘•àõÁ±…¸¹Á±…å•É}¥¹‘•à°(€€€€€€€€€€€…ÉõÍÁ•±°¹¹…µ”°(€€€€€€€€€€€…É‘}ÑåÁ•ÌõÑÕÁ±” (€€€€€€€€€€€€€€€­¥¹(€€€€€€€€€€€€€€€™½È­¥¹¥¸€ (€€€€€€€€€€€€€€€€€€€€‰ÉÑ¥™…Ðˆ°(€€€€€€€€€€€€€€€€€€€€‰	…ÑÑ±”ˆ°(€€€€€€€€€€€€€€€€€€€€‰É•…ÑÕÉ”ˆ°(€€€€€€€€€€€€€€€€€€€€‰¹¡…¹Ñµ•¹Ðˆ°(€€€€€€€€€€€€€€€€€€€€‰%¹ÍÑ…¹Ðˆ°(€€€€€€€€€€€€€€€€€€€€‰A±…¹•ÍÝ…±­•Èˆ°(€€€€€€€€€€€€€€€€€€€€‰M½É•Éäˆ°(€€€€€€€€€€€€€€€€€€€€‰QÉ¥‰…°ˆ°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€¥˜­¥¹¥¸ÍÁ•±°¹…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€€€€€€¤°(€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€Í½ÕÉ•}é½¹”õÍ½ÕÉ•}é½¹”°(€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÁ±…¸¹½É…±•}™É…µ•¹Ð°(€€€€€€€€¤(€€€€€€€Í•±˜¹}•¹ÅÕ•Õ•}ÍÁ•±±}…ÍÑ}ÑÉ¥•ÉÌ¡ÍÁ•±°¤(€€€€€€€Í•±˜¹¡•­}ÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¹Ì ¤(€€€€€€€Í•±˜¹}‰•¥¹}ÁÉ¥½É¥Ñå}Ý¥¹‘½Ü ¤(€€€€€€€…ÍÍ•ÉÐÍ•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¥Ì¹½Ð9½¹”(€€€€€€€Í•±˜¹Í¹•…­}•Ù¥‘•¹”¹…ÁÁ•¹ (€€€€€€€€€€€M¹•…­Ù¥‘•¹” (€€€€€€€€€€€€€€€…É¹…É¹¹…µ”°(€€€€€€€€€€€€€€€…É¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Á±…¸¹Á±…å•É}¥¹‘•à°(€€€€€€€€€€€€€€€Í•±˜¹ÑÕÉ¸°(€€€€€€€€€€€€€€€Í•±˜¹ÍÑ•À¹Ù…±Õ”°(€€€€€€€€€€€€€€€Á±…¸¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€Á±…¸¹É•ÅÕ¥É•µ•¹Ð°(€€€€€€€€€€€€€€€Á±…¸¹µ…¹…}Í½ÕÉ•}¥‘Ì°(€€€€€€€€€€€€€€€…ÑÑ…­•È¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€É•ÑÕÉ¹•¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Á±…¸¹‘•™•¹‘¥¹}Á±…å•È°(€€€€€€€€€€€€€€€ÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Í•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¹•Á½ °(€€€€€€€€€€€€€€€Í½ÕÉ•}é½¹”õÍ½ÕÉ•}é½¹”°(€€€€€€€€€€€€€€€Á•Éµ¥ÍÍ¥½¹}Í½ÕÉ•}¥õÁ±…¸¹Á•Éµ¥ÍÍ¥½¹}Í½ÕÉ•}¥°(€€€€€€€€€€€€¤(€€€€€€€€¤(€€€€€€€É•ÑÕÉ¸ÍÁ•±°((€€€‘•˜…ÍÐ (€€€€€€€Í•±˜°(€€€€€€€Á±…å•É}¥¹‘•àè¥¹Ð°(€€€€€€€…Éè…É‘=‰©•Ð°(€€€€€€€Ñ…É•ÐèA•Éµ…¹•¹Ðð9½¹”€ô9½¹”°(€€€€€€€€¨°(€€€€€€€…ÍÑ}™É½µ}É…Ù•å…Éè‰½½°€ô…±Í”°(€€€€€€€Í…É¥™¥•}½ÍÐèA•Éµ…¹•¹Ðð9½¹”€ô9½¹”°(€€€€€€€Í½ÕÉ•}Ñ…É•ÐèA•Éµ…¹•¹Ðð9½¹”€ô9½¹”°(€€€€€€€µ½‘•}™É…µ•¹ÐèÍÑÈð9½¹”€ô9½¹”°(€€€€€€€É•ÕÉÍ¥½¹}Ñ…É•ÑÌèÑÕÁ±•m…É‘=‰©•Ð°€¸¸¹t€ô€ ¤°(€€€€€€€á}Ù…±Õ”è¥¹Ðð9½¹”€ô9½¹”°(€€€€¤€´ø‰½½°è(€€€€€€€€ˆˆ‰½µÁ…Ñ¥‰¥±¥Ñä…Ñ¥½¸è…¹¹½Õ¹”„É•ÁÉ•Í•¹Ñ•ÍÁ•±°°Ñ¡•¸É•Í½±Ù”¥Ð¥µµ•‘¥…Ñ•±ä¸((€€€€€€€%µµ•‘¥…Ñ”É•Í½±ÕÑ¥½¸¥Ì…¸•áÁ±¥¥ÐÑ•µÁ½É…Éä‰½Õ¹‘…ÉäÕ¹Ñ¥°„ÁÉ¥½É¥Ñä½¹ÑÉ½±±•È½Ý¹Ì(€€€€€€€Á…ÍÌÍ•ÅÕ•¹¥¹œ¸Ù•ÉäÉ•ÁÉ•Í•¹Ñ•ÍÁ•±°ÍÑ¥±°ÑÉ…Ù•ÉÍ•ÌÑ¡”…ÕÑ¡½É¥Ñ…Ñ¥Ù”ÍÑ…¬±¥™•å±”¸(€€€€€€€€ˆˆˆ(€€€€€€€ÍÁ•±°€ôÍ•±˜¹…¹¹½Õ¹•}ÍÁ•±° (€€€€€€€€€€€Á±…å•É}¥¹‘•à°(€€€€€€€€€€€…É°(€€€€€€€€€€€Ñ…É•Ð°(€€€€€€€€€€€…ÍÑ}™É½µ}É…Ù•å…Éõ…ÍÑ}™É½µ}É…Ù•å…É°(€€€€€€€€€€€Í…É¥™¥•}½ÍÐõÍ…É¥™¥•}½ÍÐ°(€€€€€€€€€€€Í½ÕÉ•}Ñ…É•ÐõÍ½ÕÉ•}Ñ…É•Ð°(€€€€€€€€€€€µ½‘•}™É…µ•¹Ðõµ½‘•}™É…µ•¹Ð°(€€€€€€€€€€€É•ÕÉÍ¥½¹}Ñ…É•ÑÌõÉ•ÕÉÍ¥½¹}Ñ…É•ÑÌ°(€€€€€€€€€€€á}Ù…±Õ”õá}Ù…±Õ”°(€€€€€€€€¤(€€€€€€€¥˜ÍÁ•±°¥Ì9½¹”è(€€€€€€€€€€€É•ÑÕÉ¸…±Í”(€€€€€€€¥˜Í•±˜¹ÍÑ…­l´Åt¥Ì¹½ÐÍÁ•±°è(€€€€€€€€€€€€Œ…ÍÐÑÉ¥•ÈÍ¥ÑÌ…‰½Ù”Ñ¡”ÍÁ•±°ì½É‘¥¹…ÉäÁÉ¥½É¥Ñä½Ý¹ÌÑ¡…ÐÍÑ…¬¸(€€€€€€€€€€€Í•±˜¹}‰•¥¹}ÁÉ¥½É¥Ñå}Ý¥¹‘½Ü¡ÁÉ¥½É¥Ñå}Á±…å•ÈõÁ±…å•É}¥¹‘•à¤(€€€€€€€€€€€É•ÑÕÉ¸QÉÕ”(€€€€€€€Í•±˜¹É•Í½±Ù•}Ñ½Á}½™}ÍÑ…¬ ¤(€€€€€€€É•ÑÕÉ¸QÉÕ”((€€€‘•˜…¹¹½Õ¹•}ÍÁ•±° (€€€€€€€Í•±˜°(€€€€€€€Á±…å•É}¥¹‘•àè¥¹Ð°(€€€€€€€…Éè…É‘=‰©•Ð°(€€€€€€€Ñ…É•ÐèA•Éµ…¹•¹ÐðMÑ…­=‰©•Ðð9½¹”€ô9½¹”°(€€€€€€€€¨°(€€€€€€€…ÍÑ}™É½µ}É…Ù•å…Éè‰½½°€ô…±Í”°(€€€€€€€…ÍÑ}™É½µ}•á¥±”è‰½½°€ô…±Í”°(€€€€€€€Í…É¥™¥•}½ÍÐèA•Éµ…¹•¹Ðð9½¹”€ô9½¹”°(€€€€€€€Í½ÕÉ•}Ñ…É•ÐèA•Éµ…¹•¹Ðð9½¹”€ô9½¹”°(€€€€€€€µ½‘•}™É…µ•¹ÐèÍÑÈð9½¹”€ô9½¹”°(€€€€€€€É•ÕÉÍ¥½¹}Ñ…É•ÑÌèÑÕÁ±•m½‰©•Ð°€¸¸¹t€ô€ ¤°(€€€€€€€á}Ù…±Õ”è¥¹Ðð9½¹”€ô9½¹”°(€€€€¤€´øMÑ…­=‰©•Ðð9½¹”è(€€€€€€€€ˆˆ‰Y…±¥‘…Ñ”…¹¹½Õ¹•µ•¹Ð°Á…äÉ•ÁÉ•Í•¹Ñ•µ…¹„°…¹…Ñ½µ¥…±±äµ½Ù”!…¹€´øMÑ…¬¸ˆˆˆ(€€€€€€€Á±…å•È€ôÍ•±˜¹Á±…å•ÉÍmÁ±…å•É}¥¹‘•át(€€€€€€€™±…Í¡}ÁÉ¥½É¥Ñä€ô€ (€€€€€€€€€€€Í•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¥Ì¹½Ð9½¹”(€€€€€€€€€€€…¹¹½ÐÍ•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¹É•Í½±ÕÑ¥½¹}Á•¹‘¥¹œ(€€€€€€€€€€€…¹Í•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¹Á±…å•É}¥¹‘•à€ôôÁ±…å•É}¥¹‘•à(€€€€€€€€€€€…¹€‰±…Í ˆ¥¸Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹™É…µ•¹ÑÌ¡…É¹…É¤(€€€€€€€€€€€…¹Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹…ÍÑ}ÁÉ½É…´¡…É¹…É¤¹­¥¹¥¸í…ÍÑ-¥¹¹UI°…ÍÑ-¥¹¹AI599Qô(€€€€€€€€¤(€€€€€€€¥¹ÍÑ…¹Ñ}ÁÉ¥½É¥Ñä€ô€ (€€€€€€€€€€€Í•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¥Ì¹½Ð9½¹”(€€€€€€€€€€€…¹¹½ÐÍ•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¹É•Í½±ÕÑ¥½¹}Á•¹‘¥¹œ(€€€€€€€€€€€…¹Í•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¹Á±…å•É}¥¹‘•à€ôôÁ±…å•É}¥¹‘•à(€€€€€€€€€€€…¹€ (€€€€€€€€€€€€€€€Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹­¥­•‘}É•…ÑÕÉ•}ÁÑ}ÁÉ½É…´¡…É¹…É¤¥Ì¹½Ð9½¹”(€€€€€€€€€€€€€€€½È€ (€€€€€€€€€€€€€€€€€€€…ÍÑ}™É½µ}•á¥±”(€€€€€€€€€€€€€€€€€€€…¹€‰%¹ÍÑ…¹Ðˆ¥¸…É¹…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€€€€€€€€€€€€€…¹Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹…ÍÑ}ÁÉ½É…´¡…É¹…É¤¹­¥¹(€€€€€€€€€€€€€€€€€€€¥¸ì(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹I]}IL°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹Q=A}I}M1Q%=8°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹Q=A}IQUI}M1Q%=8°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹1%	IIe}MI!}Q=}!9°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹=AQ%=91}!9}IMP°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹=9%Q%=91}M9-}Q=-9L°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹=AQ%=91}MQI=e}9}IQ°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹=9%Q%=91}MQI=e}9}IQ°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹5|Í}=AA=M%9}IQUI°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹1}5°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹IQUI}A=]I}5°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹MQI=e}IQ%Q}9!9Q59Q}=I}A=]I|Ñ}IQUI°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹==i}MA%10°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹=U9QI}QIQ}MA10°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹QIQ}I5=Y0°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹5=1}Q=-9}=I}IQUI}AU5@°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹QIQ}=U9QI}-e]=I}I9P°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹Q5A=IIe}Q!}IQUI9}I9P°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹Q5A=IIe}QeA}	M}AQ}I\°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÑ-¥¹¹QIQ}1%	IIe}IQUI9}9}Q=-8°(€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€½È€ (€€€€€€€€€€€€€€€€€€€¹½Ð…ÍÑ}™É½µ}•á¥±”(€€€€€€€€€€€€€€€€€€€…¹Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹…ÍÑ}ÁÉ½É…´¡…É¹…É¤¹­¥¹¥Ì…ÍÑ-¥¹¹QIQ}I5=Y0(€€€€€€€€€€€€€€€€€€€…¹€‰%¹ÍÑ…¹Ðˆ¥¸…É¹…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€½È€ (€€€€€€€€€€€€€€€€€€€¹½Ð…ÍÑ}™É½µ}•á¥±”(€€€€€€€€€€€€€€€€€€€…¹Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹…ÍÑ}ÁÉ½É…´¡…É¹…É¤¹­¥¹(€€€€€€€€€€€€€€€€€€€¥Ì…ÍÑ-¥¹¹IQUI}A=]I}5(€€€€€€€€€€€€€€€€€€€…¹€‰%¹ÍÑ…¹Ðˆ¥¸…É¹…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€½È€ (€€€€€€€€€€€€€€€€€€€¹½Ð…ÍÑ}™É½µ}•á¥±”(€€€€€€€€€€€€€€€€€€€…¹Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹…ÍÑ}ÁÉ½É…´¡…É¹…É¤¹­¥¹(€€€€€€€€€€€€€€€€€€€¥Ì…ÍÑ-¥¹¹5=1}Q=-9}=I}IQUI}AU5@(€€€€€€€€€€€€€€€€€€€…¹€‰%¹ÍÑ…¹Ðˆ¥¸…É¹…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€½È€ (€€€€€€€€€€€€€€€€€€€¹½Ð…ÍÑ}™É½µ}•á¥±”(€€€€€€€€€€€€€€€€€€€…¹Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹…ÍÑ}ÁÉ½É…´¡…É¹…É¤¹­¥¹(€€€€€€€€€€€€€€€€€€€¥Ì…ÍÑ-¥¹¹QIQ}=U9QI}-e]=I}I9P(€€€€€€€€€€€€€€€€€€€…¹€‰%¹ÍÑ…¹Ðˆ¥¸…É¹…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€½È€ (€€€€€€€€€€€€€€€€€€€¹½Ð…ÍÑ}™É½µ}•á¥±”(€€€€€€€€€€€€€€€€€€€…¹Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹…ÍÑ}ÁÉ½É…´¡…É¹…É¤¹­¥¹(€€€€€€€€€€€€€€€€€€€¥Ì…ÍÑ-¥¹¹Q5A=IIe}Q!}IQUI9}I9P(€€€€€€€€€€€€€€€€€€€…¹€‰%¹ÍÑ…¹Ðˆ¥¸…É¹…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€½È€ (€€€€€€€€€€€€€€€€€€€¹½Ð…ÍÑ}™É½µ}•á¥±”(€€€€€€€€€€€€€€€€€€€…¹Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹…ÍÑ}ÁÉ½É…´¡…É¹…É¤¹­¥¹(€€€€€€€€€€€€€€€€€€€¥Ì…ÍÑ-¥¹¹Q5A=IIe}QeA}	M}AQ}I\(€€€€€€€€€€€€€€€€€€€…¹€‰%¹ÍÑ…¹Ðˆ¥¸…É¹…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€½È€ (€€€€€€€€€€€€€€€€€€€¹½Ð…ÍÑ}™É½µ}•á¥±”(€€€€€€€€€€€€€€€€€€€…¹Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹…ÍÑ}ÁÉ½É…´¡…É¹…É¤¹­¥¹(€€€€€€€€€€€€€€€€€€€¥Ì…ÍÑ-¥¹¹QIQ}1%	IIe}IQUI9}9}Q=-8(€€€€€€€€€€€€€€€€€€€…¹€‰%¹ÍÑ…¹Ðˆ¥¸…É¹…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€½È€ (€€€€€€€€€€€€€€€€€€€¹½Ð…ÍÑ}™É½µ}•á¥±”(€€€€€€€€€€€€€€€€€€€…¹Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹…ÍÑ}ÁÉ½É…´¡…É¹…É¤¹­¥¹(€€€€€€€€€€€€€€€€€€€¥Ì…ÍÑ-¥¹¹=AQ%=91}!9}IMP(€€€€€€€€€€€€€€€€€€€…¹€‰%¹ÍÑ…¹Ðˆ¥¸…É¹…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€½È€ (€€€€€€€€€€€€€€€€€€€¹½Ð…ÍÑ}™É½µ}•á¥±”(€€€€€€€€€€€€€€€€€€€…¹Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹…ÍÑ}ÁÉ½É…´¡…É¹…É¤¹­¥¹(€€€€€€€€€€€€€€€€€€€¥Ì…ÍÑ-¥¹¹=9%Q%=91}M9-}Q=-9L(€€€€€€€€€€€€€€€€€€€…¹€‰%¹ÍÑ…¹Ðˆ¥¸…É¹…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€¤(€€€€€€€€¤(€€€€€€€¥˜€ (€€€€€€€€€€€€ (€€€€€€€€€€€€€€€¹½Ð€¡™±…Í¡}ÁÉ¥½É¥Ñä½È¥¹ÍÑ…¹Ñ}ÁÉ¥½É¥Ñä¤(€€€€€€€€€€€€€€€…¹€ (€€€€€€€€€€€€€€€€€€€Á±…å•É}¥¹‘•à€„ôÍ•±˜¹…Ñ¥Ù•}Á±…å•È(€€€€€€€€€€€€€€€€€€€½ÈÍ•±˜¹ÍÑ•À¹½Ð¥¸íQÕÉ¹MÑ•À¹AI=5	Q}5%8°QÕÉ¹MÑ•À¹A=MQ=5	Q}5%9ô(€€€€€€€€€€€€€€€€€€€½È€ (€€€€€€€€€€€€€€€€€€€€€€€€¡Í•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¥Ì¹½Ð9½¹”½ÈÍ•±˜¹ÍÑ…¬¤(€€€€€€€€€€€€€€€€€€€€€€€…¹Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹…ÕÉ…}ÁÉ½É…´¡…É¹…É¤¥Ì¹½Ð9½¹”(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€¤(€€€€€€€€€€€½È¹½Ð€ (€€€€€€€€€€€€€€€Í•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡…É°€‰É…Ù•å…Éˆ¤(€€€€€€€€€€€€€€€¥˜…ÍÑ}™É½µ}É…Ù•å…É(€€€€€€€€€€€€€€€•±Í”€ (€€€€€€€€€€€€€€€€€€€Í•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡…É°€‰•á¥±”ˆ¤(€€€€€€€€€€€€€€€€€€€¥˜…ÍÑ}™É½µ}•á¥±”(€€€€€€€€€€€€€€€€€€€•±Í”Í•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡…É°€‰¡…¹ˆ¤(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€¤(€€€€€€€€€€€½È€ (€€€€€€€€€€€€€€€…É¹½Ý¹•È€„ôÁ±…å•É}¥¹‘•à(€€€€€€€€€€€€€€€…¹¹½Ð€¡…ÍÑ}™É½µ}•á¥±”…¹Í•±˜¹}±¥¹­•‘}Á±…å}É…¹Ñ}™½È¡Á±…å•É}¥¹‘•à°…É¤¤(€€€€€€€€€€€€¤(€€€€€€€€¤è(€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€±¥¹­•‘}É…¹Ð€ôÍ•±˜¹}±¥¹­•‘}Á±…å}É…¹Ñ}™½È¡Á±…å•É}¥¹‘•à°…É¤¥˜…ÍÑ}™É½µ}•á¥±”•±Í”9½¹”(€€€€€€€Á•Éµ¥ÍÍ¥½¸€ô9½¹”(€€€€€€€¥˜…ÍÑ}™É½µ}•á¥±”…¹±¥¹­•‘}É…¹Ð¥Ì9½¹”è(€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€¥˜…ÍÑ}™É½µ}É…Ù•å…Éè(€€€€€€€€€€€Á•Éµ¥ÍÍ¥½¸€ô¹•áÐ (€€€€€€€€€€€€€€€€ (€€€€€€€€€€€€€€€€€€€Í•±˜¹}É…Ù•å…É‘}…ÍÑ}Á•Éµ¥ÍÍ¥½¸¡Í½ÕÉ”¤(€€€€€€€€€€€€€€€€€€€™½ÈÍ½ÕÉ”¥¸Á±…å•È¹‰…ÑÑ±•™¥•±(€€€€€€€€€€€€€€€€€€€¥˜Í•±˜¹}É…Ù•å…É‘}…ÍÑ}Á•Éµ¥ÍÍ¥½¸¡Í½ÕÉ”¤¥Ì¹½Ð9½¹”(€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€9½¹”°(€€€€€€€€€€€€¤(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€Á•Éµ¥ÍÍ¥½¸¥Ì9½¹”(€€€€€€€€€€€€€€€½È¹½Ð…É¹…É¹¥Í}É•…ÑÕÉ”(€€€€€€€€€€€€€€€½È¹½ÐÍ•±˜¹}É…Ù•å…É‘}…É‘}ÅÕ…±¥™¥•Ì¡…É¹…É°Á•Éµ¥ÍÍ¥½¹lÁt¤(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€ÁÉ½É…´€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹…ÍÑ}ÁÉ½É…´¡…É¹…É¤(€€€€€€€¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹5=1}Q=-9}=I}IQUI}AU5@è(€€€€€€€€€€€µ½‘…°€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹µ½‘…±}Ñ½­•¹}½É}É•…ÑÕÉ•}ÁÕµÁ}ÁÉ½É…´¡…É¹…É¤(€€€€€€€€€€€¥˜µ½‘…°¥Ì9½¹”½Èµ½‘•}™É…µ•¹Ð¹½Ð¥¸ì(€€€€€€€€€€€€€€€µ½‘…°¹Ñ½­•¹}™É…µ•¹Ð°(€€€€€€€€€€€€€€€µ½‘…°¹ÁÕµÁ}™É…µ•¹Ð°(€€€€€€€€€€€ôè(€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€•±¥˜µ½‘•}™É…µ•¹Ð¥Ì¹½Ð9½¹”è(€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€¥˜Í…É¥™¥•}½ÍÐ¥Ì¹½Ð9½¹”…¹€ (€€€€€€€€€€€ÁÉ½É…´¹­¥¹¥Ì¹½Ð…ÍÑ-¥¹¹-%-}IQUI}AP(€€€€€€€€€€€½È¹½Ð¥Í¥¹ÍÑ…¹”¡Í…É¥™¥•}½ÍÐ°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€½È¹½ÐÍ•±˜¹}±•…±}­¥­•É}Í…É¥™¥” (€€€€€€€€€€€€€€€Á±…å•É}¥¹‘•à°(€€€€€€€€€€€€€€€Í…É¥™¥•}½ÍÐ°(€€€€€€€€€€€€€€€Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹­¥­•‘}É•…ÑÕÉ•}ÁÑ}ÁÉ½É…´¡…É¹…É¤¹Í…É¥™¥•}ÑåÁ•Ì°(€€€€€€€€€€€€¤(€€€€€€€€¤è(€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€Ñ…É•Ñ}¥èÍÑÈð9½¹”€ô9½¹”(€€€€€€€¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹UIè(€€€€€€€€€€€¥˜¹½ÐÍ•±˜¹±•…±}…ÕÉ…}Ñ…É•Ð¡…É¹…É°Ñ…É•Ð°Á±…å•É}¥¹‘•à¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€€€€€Ñ…É•Ñ}¥€ôÑ…É•Ð¹½‰©•Ñ}¥(€€€€€€€•±¥˜ÁÉ½É…´¹­¥¹¥¸í…ÍÑ-¥¹¹5|Í}=AA=M%9}IQUI°…ÍÑ-¥¹¹1}5ôè(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€Ñ…É•Ð¥Ì9½¹”(€€€€€€€€€€€€€€€½È¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Ñ…É•Ð°€‰‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€€€€€€€€€½ÈÑ…É•Ð¹½¹ÑÉ½±±•È€ôôÁ±…å•É}¥¹‘•à(€€€€€€€€€€€€€€€½È¹½ÐÍ•±˜¹}±•…±}‘…µ…•}Ñ…É•Ð¡Ñ…É•Ð°Á±…å•É}¥¹‘•à¤(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰‘•…‘}¥¹Ñ•É…Ñ¥½¸ˆ°Á±…å•ÈõÁ±…å•È¹¹…µ”°…Éõ…É¹¹…µ”°É•…Í½¸ô‰¹½}±•…±}Ñ…É•Ðˆ(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€€€€€Ñ…É•Ñ}¥€ôÑ…É•Ð¹½‰©•Ñ}¥(€€€€€€€•±¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹IQUI}A=]I}5è(€€€€€€€€€€€¥˜¹½ÐÍ•±˜¹}±•…±}É•…ÑÕÉ•}Á½Ý•É}Í½ÕÉ” (€€€€€€€€€€€€€€€Í½ÕÉ•}Ñ…É•Ð°Á±…å•É}¥¹‘•à(€€€€€€€€€€€€¤½È¹½ÐÍ•±˜¹}±•…±}É•…ÑÕÉ•}Á½Ý•É}É•¥Á¥•¹Ð¡Ñ…É•Ð°Á±…å•É}¥¹‘•à¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€Ñ…É•Ñ}¥€ôÑ…É•Ð¹½‰©•Ñ}¥(€€€€€€€•±¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹==i}MA%10è(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€Ñ…É•Ð¥Ì9½¹”(€€€€€€€€€€€€€€€½È¹½Ð¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°MÑ…­=‰©•Ð¤(€€€€€€€€€€€€€€€½È¹½ÐÍ•±˜¹}¥Í}±•…±}½½é•}Ñ…É•Ð¡Ñ…É•Ð°Á±…å•É}¥¹‘•à¤(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€€€€€Ñ…É•Ñ}¥€ôÑ…É•Ð¹½‰©•Ñ}¥(€€€€€€€•±¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹=U9QI}QIQ}MA10è(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€Í•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¥Ì9½¹”(€€€€€€€€€€€€€€€½ÈÍ•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¹É•Í½±ÕÑ¥½¹}Á•¹‘¥¹œ(€€€€€€€€€€€€€€€½ÈÍ•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¹Á±…å•É}¥¹‘•à€„ôÁ±…å•É}¥¹‘•à(€€€€€€€€€€€€€€€½È¹½ÐÍ•±˜¹}¥Í}±•…±}¡…¹‘}½Õ¹Ñ•É}Ñ…É•Ð¡…É¹…É°Ñ…É•Ð¤(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°MÑ…­=‰©•Ð¤(€€€€€€€€€€€Ñ…É•Ñ}¥€ôÑ…É•Ð¹½‰©•Ñ}¥(€€€€€€€•±¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹MQI=e}IQ%Q}9!9Q59Q}=I}A=]I|Ñ}IQUIè(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€Ñ…É•Ð¥Ì9½¹”(€€€€€€€€€€€€€€€½È¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Ñ…É•Ð°€‰‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€€€€€€€€€½È¹½ÐÍ•±˜¹}¥Í}‘•ÍÑÉ½å}…ÉÑ¥™…Ñ}•¹¡…¹Ñµ•¹Ñ}½É}Á½Ý•É|Ñ}É•…ÑÕÉ•}Ñ…É•Ð¡Ñ…É•Ð¤(€€€€€€€€€€€€€€€½È¹½ÐÍ•±˜¹}±•…±}Ñ…É•Ñ¥¹}ÁÉ½Ñ•Ñ¥½¸¡Ñ…É•Ð°Á±…å•É}¥¹‘•à¤(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰‘•…‘}¥¹Ñ•É…Ñ¥½¸ˆ°Á±…å•ÈõÁ±…å•È¹¹…µ”°…Éõ…É¹¹…µ”°É•…Í½¸ô‰¹½}±•…±}Ñ…É•Ðˆ(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€€€€€Ñ…É•Ñ}¥€ôÑ…É•Ð¹½‰©•Ñ}¥(€€€€€€€•±¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹=AQ%=91}MQI=e}9}IQè(€€€€€€€€€€€¥˜Ñ…É•Ð¥Ì¹½Ð9½¹”è(€€€€€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤½È¹½ÐÍ•±˜¹}±•…±}½ÁÑ¥½¹…±}‘•ÍÑÉ½å}Ñ…É•Ð (€€€€€€€€€€€€€€€€€€€Ñ…É•Ð°Á±…å•É}¥¹‘•à(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€€€€€€€€€Ñ…É•Ñ}¥€ôÑ…É•Ð¹½‰©•Ñ}¥(€€€€€€€•±¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹=9%Q%=91}MQI=e}9}IQè(€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤½È¹½ÐÍ•±˜¹}±•…±}½¹‘¥Ñ¥½¹…±}‘•ÍÑÉ½å}Ñ…É•Ð (€€€€€€€€€€€€€€€Ñ…É•Ð°Á±…å•É}¥¹‘•à(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€€€€€Ñ…É•Ñ}¥€ôÑ…É•Ð¹½‰©•Ñ}¥(€€€€€€€•±¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹QIQ}I5=Y0è(€€€€€€€€€€€É•µ½Ù…°€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹Ñ…É•Ñ•‘}É•µ½Ù…±}ÁÉ½É…´¡…É¹…É¤(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€É•µ½Ù…°¥Ì9½¹”(€€€€€€€€€€€€€€€½È¹½Ð¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€½È¹½ÐÍ•±˜¹}±•…±}Ñ…É•Ñ•‘}É•µ½Ù…±}Ñ…É•Ð¡Ñ…É•Ð°Á±…å•É}¥¹‘•à°É•µ½Ù…°¤(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€€€€€Ñ…É•Ñ}¥€ôÑ…É•Ð¹½‰©•Ñ}¥(€€€€€€€•±¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹-%-}IQUI}APè(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€¹½Ð¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€½È¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Ñ…É•Ð°€‰‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€€€€€€€€€½È¹½ÐÑ…É•Ð¹¥Í}É•…ÑÕÉ”(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€€€€€Ñ…É•Ñ}¥€ôÑ…É•Ð¹½‰©•Ñ}¥(€€€€€€€•±¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹QIQ}=U9QI}-e]=I}I9Pè(€€€€€€€€€€€¥˜¹½ÐÍ•±˜¹}±•…±}½Õ¹Ñ•É}­•åÝ½É‘}É…¹Ñ}Ñ…É•Ð¡Ñ…É•Ð°Á±…å•É}¥¹‘•à¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€Ñ…É•Ñ}¥€ôÑ…É•Ð¹½‰©•Ñ}¥(€€€€€€€•±¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹Q5A=IIe}Q!}IQUI9}I9Pè(€€€€€€€€€€€¥˜¹½ÐÍ•±˜¹}±•…±}‘•…Ñ¡}É•ÑÕÉ¹}É…¹Ñ}Ñ…É•Ð¡Ñ…É•Ð°Á±…å•É}¥¹‘•à¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€Ñ…É•Ñ}¥€ôÑ…É•Ð¹½‰©•Ñ}¥(€€€€€€€•±¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹Q5A=IIe}QeA}	M}AQ}I\è(€€€€€€€€€€€…¹¥µ…Ñ¥½¸€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹Ñ•µÁ½É…Éå}ÑåÁ•}‰…Í•}ÁÑ}‘É…Ý}ÁÉ½É…´¡…É¹…É¤(€€€€€€€€€€€¥˜…¹¥µ…Ñ¥½¸¥Ì9½¹”½È¹½ÐÍ•±˜¹}±•…±}Ñ•µÁ½É…Éå}ÑåÁ•}‰…Í•}ÁÑ}Ñ…É•Ð (€€€€€€€€€€€€€€€Ñ…É•Ð°Á±…å•É}¥¹‘•à°…¹¥µ…Ñ¥½¸¹Ñ…É•Ñ}ÑåÁ•Ì(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€Ñ…É•Ñ}¥€ôÑ…É•Ð¹½‰©•Ñ}¥(€€€€€€€•±¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹QIQ}1%	IIe}IQUI9}9}Q=-8è(€€€€€€€€€€€¥˜¹½ÐÍ•±˜¹}±•…±}Ñ…É•Ñ•‘}±¥‰É…Éå}É•ÑÕÉ¸¡Ñ…É•Ð°Á±…å•É}¥¹‘•à¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€Ñ…É•Ñ}¥€ôÑ…É•Ð¹½‰©•Ñ}¥(€€€€€€€•±¥˜€ (€€€€€€€€€€€ÁÉ½É…´¹­¥¹(€€€€€€€€€€€¥¸ì(€€€€€€€€€€€€€€€…ÍÑ-¥¹¹1%	IIe}MI!}Q=}!9°(€€€€€€€€€€€€€€€…ÍÑ-¥¹¹=AQ%=91}!9}IMP°(€€€€€€€€€€€€€€€…ÍÑ-¥¹¹=9%Q%=91}M9-}Q=-9L°(€€€€€€€€€€€€€€€…ÍÑ-¥¹¹Q=A}IQUI}M1Q%=8°(€€€€€€€€€€€ô(€€€€€€€€€€€…¹Ñ…É•Ð¥Ì¹½Ð9½¹”(€€€€€€€€¤è(€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€•±¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹IYeI}IUIM%=8è(€€€€€€€€€€€É•ÕÉÍ¥½¸€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹É…Ù•å…É‘}É•ÕÉÍ¥½¹}ÁÉ½É…´¡…É¹…É¤(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€Ñ…É•Ð¥Ì¹½Ð9½¹”(€€€€€€€€€€€€€€€½ÈÉ•ÕÉÍ¥½¸¥Ì9½¹”(€€€€€€€€€€€€€€€½È¹½ÐÍ•±˜¹}Ù…±¥‘}É…Ù•å…É‘}É•ÕÉÍ¥½¹}Ñ…É•ÑÌ (€€€€€€€€€€€€€€€€€€€É•ÕÉÍ¥½¹}Ñ…É•ÑÌ°Á±…å•É}¥¹‘•à°É•ÕÉÍ¥½¸¹µ…¹…}Ù…±Õ•}±¥µ¥Ð(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€•±¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹5=1}Q=-9}=I}IQUI}AU5@è(€€€€€€€€€€€¥˜µ½‘•}™É…µ•¹Ð€ôôµ½‘…°¹Ñ½­•¹}™É…µ•¹Ðè(€€€€€€€€€€€€€€€¥˜Ñ…É•Ð¥Ì¹½Ð9½¹”è(€€€€€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€€€€€•±Í”è(€€€€€€€€€€€€€€€¥˜¹½ÐÍ•±˜¹}±•…±}µ½‘…±}É•…ÑÕÉ•}Ñ…É•Ð¡Ñ…É•Ð°Á±…å•É}¥¹‘•à¤è(€€€€€€€€€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€Ñ…É•Ñ}¥€ôÑ…É•Ð¹½‰©•Ñ}¥(€€€€€€€•±¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹U9MUAA=IQè(€€€€€€€€€€€™É…µ•¹ÑÌ€ôm±¥¹”¹ÍÑÉ¥À ¤™½È±¥¹”¥¸…É¹½É…±•}Ñ•áÐ¹ÍÁ±¥Ñ±¥¹•Ì ¤¥˜±¥¹”¹ÍÑÉ¥À ¥t(€€€€€€€€€€€™½È™É…µ•¹Ð¥¸™É…µ•¹ÑÌ½Èm…É¹ÑåÁ•}±¥¹•tè(€€€€€€€€€€€€€€€Í•±˜¹Õ¹ÍÕÁÁ½ÉÑ• (€€€€€€€€€€€€€€€€€€€…É¹…É°(€€€€€€€€€€€€€€€€€€€€‰ÍÁ•±±}½É}Á•Éµ…¹•¹Ñ}Í•µ…¹Ñ¥Í}¹½Ñ}¥µÁ±•µ•¹Ñ•ˆ°(€€€€€€€€€€€€€€€€€€€Á±…å•É}¥¹‘•àõÁ±…å•É}¥¹‘•à°(€€€€€€€€€€€€€€€€€€€½É…±•}™É…µ•¹Ðõ™É…µ•¹Ð°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€É•ÑÕÉ¸9½¹”((€€€€€€€É•ÅÕ¥É•µ•¹Ð€ôÍ•±˜¹µ…¹…}É•ÅÕ¥É•µ•¹Ð¡…É°á}Ù…±Õ”õá}Ù…±Õ”¤(€€€€€€€¥˜É•ÅÕ¥É•µ•¹Ð¥Ì9½¹”è(€€€€€€€€€€€Í•±˜¹Õ¹ÍÕÁÁ½ÉÑ• (€€€€€€€€€€€€€€€…É¹…É°(€€€€€€€€€€€€€€€€‰µ…¹…}½ÍÑ}¹½Ñ}¥µÁ±•µ•¹Ñ•ˆ°(€€€€€€€€€€€€€€€Á±…å•É}¥¹‘•àõÁ±…å•É}¥¹‘•à°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹Ðõ…É¹µ…¹…}½ÍÐ½È€‰é•É¼µ…¹„½ÍÐˆ°(€€€€€€€€€€€€¤(€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€Á±…¸€ôÍ•±˜¹Á…åµ•¹Ñ}Á±…¸ (€€€€€€€€€€€Á±…å•É}¥¹‘•à°(€€€€€€€€€€€…É°(€€€€€€€€€€€…±±½Ý}É…Ù•å…Éõ…ÍÑ}™É½µ}É…Ù•å…É°(€€€€€€€€€€€…±±½Ý}•á¥±”õ…ÍÑ}™É½µ}•á¥±”°(€€€€€€€€€€€á}Ù…±Õ”õá}Ù…±Õ”°(€€€€€€€€¤(€€€€€€€¥˜Á±…¸¥Ì9½¹”è(€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€ÍÁ•±°€ôÍ•±˜¹}½µµ¥Ñ}…¹¹½Õ¹•µ•¹Ñ}Á…åµ•¹Ð (€€€€€€€€€€€…É°(€€€€€€€€€€€Á±…¸°(€€€€€€€€€€€…ÍÑ}­¥¹õÁÉ½É…´¹­¥¹°(€€€€€€€€€€€Ñ…É•Ñ}¥õÑ…É•Ñ}¥°(€€€€€€€€€€€…ÍÑ}™É½µ}É…Ù•å…Éõ…ÍÑ}™É½µ}É…Ù•å…É°(€€€€€€€€€€€™¥¹…±¥Ñå}½¹}•¹ÑÉäõ…ÍÑ}™É½µ}É…Ù•å…É°(€€€€€€€€€€€…ÍÑ}™É½µ}É…Á¡…•°õ…ÍÑ}™É½µ}•á¥±”°(€€€€€€€€¤(€€€€€€€¥˜±¥¹­•‘}É…¹Ð¥Ì¹½Ð9½¹”è(€€€€€€€€€€€Í•±˜¹}½¹ÍÕµ•}±¥¹­•‘}Á±…å}É…¹Ð¡±¥¹­•‘}É…¹Ð°…É¹½‰©•Ñ}¥¤(€€€€€€€¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹IYeI}IUIM%=8è(€€€€€€€€€€€ÍÁ•±°¹Ñ…É•Ñ}¥‘Ì€ôÑÕÁ±”¡¥Ñ•´¹½‰©•Ñ}¥™½È¥Ñ•´¥¸É•ÕÉÍ¥½¹}Ñ…É•ÑÌ¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰É…Ù•å…É‘}É•ÕÉÍ¥½¹}Ñ…É•ÑÍ}…¹¹½Õ¹•ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Ñ…É•Ñ}¥‘Ìõ±¥ÍÐ¡ÍÁ•±°¹Ñ…É•Ñ}¥‘Ì¤°(€€€€€€€€€€€€€€€½¹ÑÉ½±±•ÈõÁ±…å•É}¥¹‘•à°(€€€€€€€€€€€€¤(€€€€€€€¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹5=1}Q=-9}=I}IQUI}AU5@è(€€€€€€€€€€€ÍÁ•±°¹µ½‘•}™É…µ•¹Ð€ôµ½‘•}™É…µ•¹Ð(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰µ½‘…±}µ½‘•}¡½Í•¸ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€µ½‘•}™É…µ•¹Ðõµ½‘•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÑ…É•Ñ}¥°(€€€€€€€€€€€€€€€½¹ÑÉ½±±•ÈõÁ±…å•É}¥¹‘•à°(€€€€€€€€€€€€¤(€€€€€€€¥˜ÁÉ½É…´¹­¥¹¥Ì…ÍÑ-¥¹¹IQUI}A=]I}5è(€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Í½ÕÉ•}Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€ÍÁ•±°¹Í½ÕÉ•}Ñ…É•Ñ}¥€ôÍ½ÕÉ•}Ñ…É•Ð¹½‰©•Ñ}¥(€€€€€€€¥˜Í…É¥™¥•}½ÍÐ¥Ì¹½Ð9½¹”è(€€€€€€€€€€€ÍÁ•±°¹­¥­•É}Í…É¥™¥•}¥€ôÍ…É¥™¥•}½ÍÐ¹½‰©•Ñ}¥(€€€€€€€€€€€Í•±˜¹µ½Ù•}½‰©•Ð¡Í…É¥™¥•}½ÍÐ°€‰É…Ù•å…Éˆ°É•…Í½¸ô‰­¥­•É}Í…É¥™¥•}½ÍÐˆ¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰­¥­•É}½ÍÑ}Á…¥ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Í…É¥™¥•‘}¥õÍ…É¥™¥•}½ÍÐ¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€…ÉõÍÁ•±°¹¹…µ”°(€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹¡•­}ÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¹Ì ¤(€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€‰ÍÁ•±±}…ÍÐˆ°(€€€€€€€€€€€Á±…å•ÈõÁ±…å•È¹¹…µ”°(€€€€€€€€€€€Á±…å•É}¥¹‘•àõÁ±…å•É}¥¹‘•à°(€€€€€€€€€€€…ÉõÍÁ•±°¹¹…µ”°(€€€€€€€€€€€…É‘}ÑåÁ•ÌõÑÕÁ±” (€€€€€€€€€€€€€€€­¥¹(€€€€€€€€€€€€€€€™½È­¥¹¥¸€ (€€€€€€€€€€€€€€€€€€€€‰ÉÑ¥™…Ðˆ°(€€€€€€€€€€€€€€€€€€€€‰	…ÑÑ±”ˆ°(€€€€€€€€€€€€€€€€€€€€‰É•…ÑÕÉ”ˆ°(€€€€€€€€€€€€€€€€€€€€‰¹¡…¹Ñµ•¹Ðˆ°(€€€€€€€€€€€€€€€€€€€€‰%¹ÍÑ…¹Ðˆ°(€€€€€€€€€€€€€€€€€€€€‰A±…¹•ÍÝ…±­•Èˆ°(€€€€€€€€€€€€€€€€€€€€‰M½É•Éäˆ°(€€€€€€€€€€€€€€€€€€€€‰QÉ¥‰…°ˆ°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€¥˜­¥¹¥¸ÍÁ•±°¹…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€€€€€€¤°(€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€Ñ…É•Ñ}¥õÑ…É•Ñ}¥°(€€€€€€€€€€€Í½ÕÉ•}Ñ…É•Ñ}¥õÍÁ•±°¹Í½ÕÉ•}Ñ…É•Ñ}¥°(€€€€€€€€€€€µ½‘•}™É…µ•¹ÐõÍÁ•±°¹µ½‘•}™É…µ•¹Ð°(€€€€€€€€€€€á}Ù…±Õ”õÍÁ•±°¹á}Ù…±Õ”°(€€€€€€€€¤(€€€€€€€Í•±˜¹}•¹ÅÕ•Õ•}ÍÁ•±±}…ÍÑ}ÑÉ¥•ÉÌ¡ÍÁ•±°¤(€€€€€€€É•ÑÕÉ¸ÍÁ•±°((€€€‘•˜É•Í½±Ù•}Ñ½Á}½™}ÍÑ…¬¡Í•±˜¤€´ø…É‘=‰©•ÐðA•Éµ…¹•¹Ðð9½¹”è(€€€€€€€€ˆˆ‰I•Í½±Ù”Ñ¡”…ÕÑ¡½É¥Ñ…Ñ¥Ù”Ñ½ÀÍÁ•±°½ÈÑÉ¥•É•…‰¥±¥Ñä¸ˆˆˆ(€€€€€€€¥˜¹½ÐÍ•±˜¹ÍÑ…¬è(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰…¹¹½ÐÉ•Í½±Ù”…¸•µÁÑäÍÑ…¬ˆ¤(€€€€€€€ÍÁ•±°€ôÍ•±˜¹ÍÑ…­l´Åt(€€€€€€€ÍÑ…­}½‰©•Ñ}¥€ôÍÁ•±°¹½‰©•Ñ}¥(€€€€€€€¥˜¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡ÍÁ•±°°€‰ÍÑ…¬ˆ¤è(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰Ñ½ÀÍÑ…¬½‰©•Ð¥Ì¹½Ð…ÕÑ¡½É¥Ñ…Ñ¥Ù”ˆ¤(€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡ÍÁ•±°°QÉ¥•É•‘‰¥±¥Ñå=‰©•Ð¤è(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€€ (€€€€€€€€€€€€€€€€€€€€ (€€€€€€€€€€€€€€€€€€€€€€€ÍÁ•±°¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹IQ}Q=-8(€€€€€€€€€€€€€€€€€€€€€€€…¹Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹•¹ÑÉå}±•…Ù•}½É}…ÉÑ¥™…Ñ}…ÍÑ}Ñ½­•¹}½¹Ñ•áÐ (€€€€€€€€€€€€€€€€€€€€€€€€€€€ÍÁ•±°¹Í½ÕÉ•}…É°ÍÁ•±°¹½É…±•}™É…µ•¹Ð(€€€€€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€€€€€¥Ì¹½Ð9½¹”(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€½ÈÍÁ•±°¹•™™•Ð(€€€€€€€€€€€€€€€€€€€¥¸ì(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹1Q	}5UQ8°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹QQ-}QIQ}=U9QH°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹AI5%}a%1}!=%°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹AI5%}I1a%Y}IQUI8°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹IA!1}11%9}a%1°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹IA!1}QQ-}A1d°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹=5	Q}%MI}=I}MI%%°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹9}MQA}MA11}QeAM}I\°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹%MAAI}9}MQ@°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹Q	}Y%%19Q°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹Y%%19Q}%MI°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹Q	}-I9}I%10°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹Q	}5%11}Q!I°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹Q	})UIe}I%°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹Q	}==}MI °(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹Q	}I]}%MI°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹=5	Q}5}I]}%MI°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹=5	Q}5}I]}1=M}1%°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹=5	Q}5}IYeI}QQ-H°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹UQ%1%Qe}QIP°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹Q	}5%11}I]}%MI°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹1MM}1Y1}Q]=}I=YId°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹%MI}I\°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹%M}I\°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹M9-}Q	}=9%Q%=8°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹Q	}I%9}%9}MId°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹Q	}M1}1%}%8°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹=9%Q%=91}9QIe}Q=-8°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹AI599Q}1Q}M1}=U9QH°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹=9QI=11}IQUI}1Q}=AA=99Q}1=ML°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹=9QI=11}=U9QI}IQUI}1Q}1%°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹=9QI=11}IQ%Q}=U9QI}QI9MH°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹5}Q=}M1}59°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹1MM}MA11}MQ}Q5}=U9QH°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹Q	}IQ%Q}I\°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹Q	}QA}MQU8°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹Q	}9e}QIQ}5°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹Q	}MQI=e}QIQ}IQUI°(€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹Q	}QIQ}IQUI}AU5A}U9Q@°(€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€…¹¹½ÐÍ•±˜¹}ÁÉ¥½É¥Ñå}É•Í½±ÕÑ¥½¹}¥¹}ÁÉ½É•ÍÌ(€€€€€€€€€€€€€€€…¹€¡Í•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¥Ì9½¹”½È¹½ÐÍ•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¹É•Í½±ÕÑ¥½¹}Á•¹‘¥¹œ¤(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È (€€€€€€€€€€€€€€€€€€€€‰É•ÁÉ•Í•¹Ñ•ÑÉ¥•É•…‰¥±¥Ñä…¹¹½ÐÉ•Í½±Ù”‰•™½É”…±°Á±…å•ÉÌÁ…ÍÌˆ(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹}É•Í½±Ù•}ÑÉ¥•É•‘}…‰¥±¥Ñä¡ÍÁ•±°¤(€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡ÍÁ•±°°Ñ¥Ù…Ñ•‘‰¥±¥Ñå=‰©•Ð¤è(€€€€€€€€€€€¥˜¹½ÐÍ•±˜¹}ÁÉ¥½É¥Ñå}É•Í½±ÕÑ¥½¹}¥¹}ÁÉ½É•ÍÌ…¹€ (€€€€€€€€€€€€€€€Í•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¥Ì9½¹”½È¹½ÐÍ•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¹É•Í½±ÕÑ¥½¹}Á•¹‘¥¹œ(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰…Ñ¥Ù…Ñ•…‰¥±¥Ñä…¹¹½ÐÉ•Í½±Ù”‰•™½É”…±°Á±…å•ÉÌÁ…ÍÌˆ¤(€€€€€€€€€€€Í•±˜¹}É•Í½±Ù•}…Ñ¥Ù…Ñ•‘}…‰¥±¥Ñä¡ÍÁ•±°¤(€€€€€€€€€€€É•ÑÕÉ¸9½¹”(€€€€€€€Á±…å•È€ôÍ•±˜¹Á±…å•ÉÍmÍÁ•±°¹½¹ÑÉ½±±•Ét(€€€€€€€Ñ…É•Ð€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡ÍÁ•±°¹Ñ…É•Ñ}¥½È€ˆˆ¤(€€€€€€€Í¹•…­}…ÍÐ€ôÍÁ•±°¹Í¹•…­}É•ÑÕÉ¹•‘}…ÑÑ…­•É}¥¥Ì¹½Ð9½¹”(€€€€€€€¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹-%-}IQUI}AP…¹ÍÁ•±°¹­¥­•É}Í…É¥™¥•}¥¥Ì¹½Ð9½¹”è(€€€€€€€€€€€Á…¥€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡ÍÁ•±°¹­¥­•É}Í…É¥™¥•}¥¤(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€¹½Ð¥Í¥¹ÍÑ…¹”¡Á…¥°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€½ÈÁ…¥¹é½¹”€„ô€‰™½Éµ•Èˆ(€€€€€€€€€€€€€€€½È¹½Ð…¹ä (€€€€€€€€€€€€€€€€€€€•Ù•¹Ñl‰•Ù•¹Ð‰t€ôô€‰­¥­•É}½ÍÑ}Á…¥ˆ(€€€€€€€€€€€€€€€€€€€…¹•Ù•¹Ð¹•Ð ‰ÍÑ…­}½‰©•Ñ}¥ˆ¤€ôôÍÁ•±°¹½‰©•Ñ}¥(€€€€€€€€€€€€€€€€€€€…¹•Ù•¹Ð¹•Ð ‰Í…É¥™¥•‘}¥ˆ¤€ôôÁ…¥¹½‰©•Ñ}¥(€€€€€€€€€€€€€€€€€€€™½È•Ù•¹Ð¥¸Í•±˜¹•Ù•¹ÑÌ(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰­¥­•È¡½¥”±…­Ì„Á…¥Í…É¥™¥”ˆ¤(€€€€€€€¥˜Í¹•…­}…ÍÐ…¹€ (€€€€€€€€€€€¹½ÐÍ•±˜¹}ÁÉ¥½É¥Ñå}É•Í½±ÕÑ¥½¹}¥¹}ÁÉ½É•ÍÌ(€€€€€€€€€€€…¹€¡Í•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¥Ì9½¹”½È¹½ÐÍ•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¹É•Í½±ÕÑ¥½¹}Á•¹‘¥¹œ¤(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰M¹•…¬ÍÁ•±°…¹¹½ÐÉ•Í½±Ù”‰•™½É”…±°Á±…å•ÉÌÁ…ÍÌˆ¤((€€€€€€€¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹UI…¹¹½ÐÍ•±˜¹±•…±}…ÕÉ…}Ñ…É•Ð (€€€€€€€€€€€ÍÁ•±°¹…É°Ñ…É•Ð°ÍÁ•±°¹½¹ÑÉ½±±•È(€€€€€€€€¤è(€€€€€€€€€€€É•Í½±Ù•€ôÍ•±˜¹µ½Ù•}½‰©•Ð¡ÍÁ•±°°€‰É…Ù•å…Éˆ°É•…Í½¸ô‰…ÕÉ…}…±±}Ñ…É•ÑÍ}¥±±•…°ˆ¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰…ÕÉ…}™…¥±•ˆ°(€€€€€€€€€€€€€€€…ÉõÍÁ•±°¹¹…µ”°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍÑ…­}½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÍÁ•±°¹Ñ…É•Ñ}¥°(€€€€€€€€€€€€€€€É•…Í½¸ô‰…±±}Ñ…É•ÑÍ}¥±±•…°ˆ°(€€€€€€€€€€€€¤(€€€€€€€€€€€É•ÑÕÉ¸É•Í½±Ù•(€€€€€€€¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥¸í…ÍÑ-¥¹¹IQUI°…ÍÑ-¥¹¹AI599P°…ÍÑ-¥¹¹UIôè(€€€€€€€€€€€Á•Éµ…¹•¹Ð€ôÍ•±˜¹µ½Ù•}½‰©•Ð (€€€€€€€€€€€€€€€ÍÁ•±°°(€€€€€€€€€€€€€€€€‰‰…ÑÑ±•™¥•±ˆ°(€€€€€€€€€€€€€€€½¹ÑÉ½±±•ÈõÍÁ•±°¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€ÍÕµµ½¹¥¹}Í¥¬õQÉÕ”°(€€€€€€€€€€€€€€€É•…Í½¸ô (€€€€€€€€€€€€€€€€€€€€‰Í¹•…­}É•…ÑÕÉ•}É•Í½±Ù•ˆ(€€€€€€€€€€€€€€€€€€€¥˜Í¹•…­}…ÍÐ(€€€€€€€€€€€€€€€€€€€•±Í”€ (€€€€€€€€€€€€€€€€€€€€€€€€‰É•…ÑÕÉ•}É•Í½±Ù•ˆ(€€€€€€€€€€€€€€€€€€€€€€€¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹IQUI(€€€€€€€€€€€€€€€€€€€€€€€•±Í”€‰Á•Éµ…¹•¹Ñ}É•Í½±Ù•ˆ(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€¤(€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Á•Éµ…¹•¹Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹UIè(€€€€€€€€€€€€€€€Í•±˜¹…ÑÑ…¡}…ÕÉ„¡Á•Éµ…¹•¹Ð°Ñ…É•Ð¤(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰…ÕÉ…}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€€€€€…ÉõÍÁ•±°¹¹…µ”°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÑ…­}½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÁ•Éµ…¹•¹Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÑ…É•Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Ñ…É•ÐõÑ…É•Ð¹…É¹¹…µ”°(€€€€€€€€€€€€€€€€€€€½¹ÑÉ½±±•ÈõÍÁ•±°¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€Á½Ý•ÈõÑ…É•Ð¹Á½Ý•È°(€€€€€€€€€€€€€€€€€€€Ñ½Õ¡¹•ÍÌõÑ…É•Ð¹Ñ½Õ¡¹•ÍÌ°(€€€€€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹…ÕÉ…}ÁÉ½É…´¡ÍÁ•±°¹…É¤¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€¥˜ÍÁ•±°¹™¥¹…±¥Ñå}½¹}•¹ÑÉäè(€€€€€€€€€€€€€€€Á•Éµ…¹•¹Ð¹½Õ¹Ñ•ÉÍl‰™¥¹…±¥Ñä‰t€ôÁ•Éµ…¹•¹Ð¹½Õ¹Ñ•ÉÌ¹•Ð ‰™¥¹…±¥Ñäˆ°€À¤€¬€Ä(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰™¥¹…±¥Ñå}½Õ¹Ñ•É}Á±…•ˆ°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÁ•Éµ…¹•¹Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€…ÉõÁ•Éµ…¹•¹Ð¹…É¹¹…µ”°(€€€€€€€€€€€€€€€€€€€½Õ¹Ñ•É}ÑåÁ”ô‰™¥¹…±¥Ñäˆ°(€€€€€€€€€€€€€€€€€€€Ñ½Ñ…°õÁ•Éµ…¹•¹Ð¹½Õ¹Ñ•ÉÍl‰™¥¹…±¥Ñä‰t°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€¥˜Í¹•…­}…ÍÐè(€€€€€€€€€€€€€€€Á•Éµ…¹•¹Ð¹Ñ…ÁÁ•€ôQÉÕ”(€€€€€€€€€€€€€€€Í•±˜¹}½µ‰…Ñ}…ÑÑ…­•ÉÌ€ôÍ•±˜¹}½µ‰…Ñ}…ÑÑ…­•ÉÌ€¬€¡Á•Éµ…¹•¹Ð¹½‰©•Ñ}¥°¤(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰Í¹•…­}É•…ÑÕÉ•}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€€€€€Á±…å•ÈõÁ±…å•È¹¹…µ”°(€€€€€€€€€€€€€€€€€€€…ÉõÍÁ•±°¹¹…µ”°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÑ…­}½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Á•Éµ…¹•¹Ñ}½‰©•Ñ}¥õÁ•Éµ…¹•¹Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€‘•™•¹‘¥¹}Á±…å•ÈõÍÁ•±°¹Í¹•…­}‘•™•¹‘¥¹}Á±…å•È°(€€€€€€€€€€€€€€€€€€€Ñ…ÁÁ•õQÉÕ”°(€€€€€€€€€€€€€€€€€€€…ÑÑ…­¥¹œõQÉÕ”°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€™½È¥¹‘•à°•Ù¥‘•¹”¥¸•¹Õµ•É…Ñ”¡Í•±˜¹Í¹•…­}•Ù¥‘•¹”¤è(€€€€€€€€€€€€€€€€€€€¥˜•Ù¥‘•¹”¹ÍÑ…­}½‰©•Ñ}¥€ôôÍÑ…­}½‰©•Ñ}¥è(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹Í¹•…­}•Ù¥‘•¹•m¥¹‘•át€ôM¹•…­Ù¥‘•¹” (€€€€€€€€€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹…É‘}¹…µ”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹¡…¹‘}½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹ÑÕÉ¸°(€€€€€€€€€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹ÍÑ•À°(€€€€€€€€€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹µ…¹…}É•ÅÕ¥É•µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹µ…¹…}Í½ÕÉ•}¥‘Ì°(€€€€€€€€€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹É•ÑÕÉ¹•‘}…ÑÑ…­•É}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹É•ÑÕÉ¹•‘}¡…¹‘}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹‘•™•¹‘¥¹}Á±…å•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹ÍÑ…­}½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹ÁÉ¥½É¥Ñå}•Á½ °(€€€€€€€€€€€€€€€€€€€€€€€€€€€Á•Éµ…¹•¹Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€QÉÕ”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€QÉÕ”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹Í½ÕÉ•}é½¹”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”¹Á•Éµ¥ÍÍ¥½¹}Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€€€€€‰É•…¬(€€€€€€€€€€€•±Í”è(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰É•…ÑÕÉ•}É•Í½±Ù•ˆ(€€€€€€€€€€€€€€€€€€€¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹IQUI(€€€€€€€€€€€€€€€€€€€•±Í”€‰Á•Éµ…¹•¹Ñ}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€€€€€Á±…å•ÈõÁ±…å•È¹¹…µ”°(€€€€€€€€€€€€€€€€€€€…ÉõÍÁ•±°¹¹…µ”°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹É•™É•Í¡}ÍÑ…Ñ¥}ÁÑ}µ½‘¥™¥•ÉÌ ¤(€€€€€€€€€€€Í•±˜¹}ÁÉ½•ÍÍ}É•…ÑÕÉ•Í}•¹Ñ•É•‘}ÑÉ¥•ÉÌ (€€€€€€€€€€€€€€€€¡Á•Éµ…¹•¹Ð°¤°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍÑ…­}½‰©•Ñ}¥¥˜Í¹•…­}…ÍÐ•±Í”9½¹”°(€€€€€€€€€€€€€€€‘•™•É}ÑÉ¥•ÉÌõÍ¹•…­}…ÍÐ°(€€€€€€€€€€€€€€€…™Ñ•É}•Ù•¹Ðõ±…µ‰‘„Í½ÕÉ”°}•Ù•¹ÐèÍ•±˜¹É•Á½ÉÑ}Õ¹ÍÕÁÁ½ÉÑ•‘}…‰¥±¥Ñ¥•Ì (€€€€€€€€€€€€€€€€€€€ÍÁ•±°¹½¹ÑÉ½±±•È°ÍÁ•±°¹…É°Í½ÕÉ”õÍ½ÕÉ”(€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€¤(€€€€€€€€€€€¥˜¹½ÐÍ¹•…­}…ÍÐè(€€€€€€€€€€€€€€€Í•±˜¹¡•­}ÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¹Ì ¤(€€€€€€€€€€€É•ÑÕÉ¸Á•Éµ…¹•¹Ð((€€€€€€€±•…±}Ñ…É•Ð€ôÍÁ•±°¹…ÍÑ}­¥¹¥¸ì(€€€€€€€€€€€…ÍÑ-¥¹¹I]}IL°(€€€€€€€€€€€…ÍÑ-¥¹¹Q=A}I}M1Q%=8°(€€€€€€€€€€€…ÍÑ-¥¹¹Q=A}IQUI}M1Q%=8°(€€€€€€€€€€€…ÍÑ-¥¹¹1%	IIe}MI!}Q=}!9°(€€€€€€€€€€€…ÍÑ-¥¹¹=AQ%=91}!9}IMP°(€€€€€€€€€€€…ÍÑ-¥¹¹=9%Q%=91}M9-}Q=-9L°(€€€€€€€ô½È€¡¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤…¹Í•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Ñ…É•Ð°€‰‰…ÑÑ±•™¥•±ˆ¤¤(€€€€€€€¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹IYeI}IUIM%=8è(€€€€€€€€€€€É•ÕÉÍ¥½¸€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹É…Ù•å…É‘}É•ÕÉÍ¥½¹}ÁÉ½É…´¡ÍÁ•±°¹…É¤(€€€€€€€€€€€…ÍÍ•ÉÐÉ•ÕÉÍ¥½¸¥Ì¹½Ð9½¹”…¹ÍÁ•±°¹Ñ…É•Ñ}¥‘Ì(€€€€€€€€€€€±•…±}Ñ…É•Ð€ô…¹ä (€€€€€€€€€€€€€€€Í•±˜¹}±•…±}É…Ù•å…É‘}É•ÕÉÍ¥½¹}Ñ…É•Ð (€€€€€€€€€€€€€€€€€€€Í•±˜¹}½‰©•ÑÌ¹•Ð¡½‰©•Ñ}¥¤°ÍÁ•±°¹½¹ÑÉ½±±•È°É•ÕÉÍ¥½¸¹µ…¹…}Ù…±Õ•}±¥µ¥Ð(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€™½È½‰©•Ñ}¥¥¸ÍÁ•±°¹Ñ…É•Ñ}¥‘Ì(€€€€€€€€€€€€¤(€€€€€€€¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹=AQ%=91}MQI=e}9}IQè(€€€€€€€€€€€±•…±}Ñ…É•Ð€ôÍÁ•±°¹Ñ…É•Ñ}¥¥Ì9½¹”½È€ (€€€€€€€€€€€€€€€¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€…¹Í•±˜¹}±•…±}½ÁÑ¥½¹…±}‘•ÍÑÉ½å}Ñ…É•Ð¡Ñ…É•Ð°ÍÁ•±°¹½¹ÑÉ½±±•È¤(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹=9%Q%=91}MQI=e}9}IQè(€€€€€€€€€€€±•…±}Ñ…É•Ð€ô¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤…¹Í•±˜¹}±•…±}½¹‘¥Ñ¥½¹…±}‘•ÍÑÉ½å}Ñ…É•Ð (€€€€€€€€€€€€€€€Ñ…É•Ð°ÍÁ•±°¹½¹ÑÉ½±±•È(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹QIQ}I5=Y0è(€€€€€€€€€€€É•µ½Ù…°€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹Ñ…É•Ñ•‘}É•µ½Ù…±}ÁÉ½É…´¡ÍÁ•±°¹…É¤(€€€€€€€€€€€±•…±}Ñ…É•Ð€ô€ (€€€€€€€€€€€€€€€É•µ½Ù…°¥Ì¹½Ð9½¹”(€€€€€€€€€€€€€€€…¹¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€…¹Í•±˜¹}±•…±}Ñ…É•Ñ•‘}É•µ½Ù…±}Ñ…É•Ð¡Ñ…É•Ð°ÍÁ•±°¹½¹ÑÉ½±±•È°É•µ½Ù…°¤(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹IQUI}A=]I}5è(€€€€€€€€€€€‘…µ…•}Í½ÕÉ”€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡ÍÁ•±°¹Í½ÕÉ•}Ñ…É•Ñ}¥½È€ˆˆ¤(€€€€€€€€€€€±•…±}Ñ…É•Ð€ôÍ•±˜¹}±•…±}É•…ÑÕÉ•}Á½Ý•É}Í½ÕÉ” (€€€€€€€€€€€€€€€‘…µ…•}Í½ÕÉ”°ÍÁ•±°¹½¹ÑÉ½±±•È(€€€€€€€€€€€€¤½ÈÍ•±˜¹}±•…±}É•…ÑÕÉ•}Á½Ý•É}É•¥Á¥•¹Ð¡Ñ…É•Ð°ÍÁ•±°¹½¹ÑÉ½±±•È¤(€€€€€€€¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥¸í…ÍÑ-¥¹¹5|Í}=AA=M%9}IQUI°…ÍÑ-¥¹¹1}5ôè(€€€€€€€€€€€±•…±}Ñ…É•Ð€ô€ (€€€€€€€€€€€€€€€±•…±}Ñ…É•Ð(€€€€€€€€€€€€€€€…¹Ñ…É•Ð¹½¹ÑÉ½±±•È€„ôÍÁ•±°¹½¹ÑÉ½±±•È(€€€€€€€€€€€€€€€…¹Í•±˜¹}±•…±}‘…µ…•}Ñ…É•Ð¡Ñ…É•Ð°ÍÁ•±°¹½¹ÑÉ½±±•È¤(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹==i}MA%10è(€€€€€€€€€€€±•…±}Ñ…É•Ð€ôÍ•±˜¹}¥Í}±•…±}½½é•}Ñ…É•Ð¡Ñ…É•Ð°ÍÁ•±°¹½¹ÑÉ½±±•È¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹=U9QI}QIQ}MA10è(€€€€€€€€€€€±•…±}Ñ…É•Ð€ôÍ•±˜¹}¥Í}±•…±}¡…¹‘}½Õ¹Ñ•É}Ñ…É•Ð¡ÍÁ•±°¹…É°Ñ…É•Ð¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹MQI=e}IQ%Q}9!9Q59Q}=I}A=]I|Ñ}IQUIè(€€€€€€€€€€€±•…±}Ñ…É•Ð€ô€ (€€€€€€€€€€€€€€€±•…±}Ñ…É•Ð(€€€€€€€€€€€€€€€…¹¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€…¹Í•±˜¹}¥Í}‘•ÍÑÉ½å}…ÉÑ¥™…Ñ}•¹¡…¹Ñµ•¹Ñ}½É}Á½Ý•É|Ñ}É•…ÑÕÉ•}Ñ…É•Ð¡Ñ…É•Ð¤(€€€€€€€€€€€€€€€…¹Í•±˜¹}±•…±}Ñ…É•Ñ¥¹}ÁÉ½Ñ•Ñ¥½¸¡Ñ…É•Ð°ÍÁ•±°¹½¹ÑÉ½±±•È¤(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹-%-}IQUI}APè(€€€€€€€€€€€±•…±}Ñ…É•Ð€ô±•…±}Ñ…É•Ð…¹¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤…¹Ñ…É•Ð¹¥Í}É•…ÑÕÉ”(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹QIQ}=U9QI}-e]=I}I9Pè(€€€€€€€€€€€±•…±}Ñ…É•Ð€ôÍ•±˜¹}±•…±}½Õ¹Ñ•É}­•åÝ½É‘}É…¹Ñ}Ñ…É•Ð¡Ñ…É•Ð°ÍÁ•±°¹½¹ÑÉ½±±•È¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹Q5A=IIe}Q!}IQUI9}I9Pè(€€€€€€€€€€€±•…±}Ñ…É•Ð€ôÍ•±˜¹}±•…±}‘•…Ñ¡}É•ÑÕÉ¹}É…¹Ñ}Ñ…É•Ð¡Ñ…É•Ð°ÍÁ•±°¹½¹ÑÉ½±±•È¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹Q5A=IIe}QeA}	M}AQ}I\è(€€€€€€€€€€€…¹¥µ…Ñ¥½¸€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹Ñ•µÁ½É…Éå}ÑåÁ•}‰…Í•}ÁÑ}‘É…Ý}ÁÉ½É…´¡ÍÁ•±°¹…É¤(€€€€€€€€€€€±•…±}Ñ…É•Ð€ô…¹¥µ…Ñ¥½¸¥Ì¹½Ð9½¹”…¹Í•±˜¹}±•…±}Ñ•µÁ½É…Éå}ÑåÁ•}‰…Í•}ÁÑ}Ñ…É•Ð (€€€€€€€€€€€€€€€Ñ…É•Ð°ÍÁ•±°¹½¹ÑÉ½±±•È°…¹¥µ…Ñ¥½¸¹Ñ…É•Ñ}ÑåÁ•Ì(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹QIQ}1%	IIe}IQUI9}9}Q=-8è(€€€€€€€€€€€±•…±}Ñ…É•Ð€ôÍ•±˜¹}±•…±}Ñ…É•Ñ•‘}±¥‰É…Éå}É•ÑÕÉ¸¡Ñ…É•Ð°ÍÁ•±°¹½¹ÑÉ½±±•È¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹5=1}Q=-9}=I}IQUI}AU5@è(€€€€€€€€€€€µ½‘…°€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹µ½‘…±}Ñ½­•¹}½É}É•…ÑÕÉ•}ÁÕµÁ}ÁÉ½É…´¡ÍÁ•±°¹…É¤(€€€€€€€€€€€¥˜µ½‘…°¥Ì9½¹”½ÈÍÁ•±°¹µ½‘•}™É…µ•¹Ð¹½Ð¥¸ì(€€€€€€€€€€€€€€€µ½‘…°¹Ñ½­•¹}™É…µ•¹Ð°(€€€€€€€€€€€€€€€µ½‘…°¹ÁÕµÁ}™É…µ•¹Ð°(€€€€€€€€€€€ôè(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…­•µ½‘…°ÍÁ•±°±½ÍÐ¥ÑÌ½µÁ±•Ñ”Í•µ…¹Ñ¥Ìˆ¤(€€€€€€€€€€€±•…±}Ñ…É•Ð€ô€ (€€€€€€€€€€€€€€€ÍÁ•±°¹Ñ…É•Ñ}¥¥Ì9½¹”(€€€€€€€€€€€€€€€¥˜ÍÁ•±°¹µ½‘•}™É…µ•¹Ð€ôôµ½‘…°¹Ñ½­•¹}™É…µ•¹Ð(€€€€€€€€€€€€€€€•±Í”Í•±˜¹}±•…±}µ½‘…±}É•…ÑÕÉ•}Ñ…É•Ð¡Ñ…É•Ð°ÍÁ•±°¹½¹ÑÉ½±±•È¤(€€€€€€€€€€€€¤(€€€€€€€¥˜¹½Ð±•…±}Ñ…É•Ðè(€€€€€€€€€€€É•Í½±Ù•‘}…É€ôÍ•±˜¹µ½Ù•}½‰©•Ð¡ÍÁ•±°°€‰É…Ù•å…Éˆ°É•…Í½¸ô‰ÍÁ•±±}É•Í½±Ù•ˆ¤(€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡É•Í½±Ù•‘}…É°…É‘=‰©•Ð¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰ÍÁ•±±}É•Í½±Ù•‘}¹½}•™™•Ðˆ°(€€€€€€€€€€€€€€€•Ù•¹Ñ}¥õ˜‰ÍÁ•±°éíÍÑ…­}½‰©•Ñ}¥‘ôéÉ•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€Á±…å•ÈõÁ±…å•È¹¹…µ”°(€€€€€€€€€€€€€€€…ÉõÍÁ•±°¹¹…µ”°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÉ•Í½±Ù•‘}…É¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÍÁ•±°¹…É¹½É…±•}Ñ•áÐ°(€€€€€€€€€€€€€€€Ñ…É•Ñ}Í½ÕÉ•}¥õÍÁ•±°¹Ñ…É•Ñ}¥°(€€€€€€€€€€€€€€€Ñ…É•Ñ}Í½ÕÉ•}¥‘Ìô (€€€€€€€€€€€€€€€€€€€±¥ÍÐ¡ÍÁ•±°¹Ñ…É•Ñ}¥‘Ì¤(€€€€€€€€€€€€€€€€€€€¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹IYeI}IUIM%=8(€€€€€€€€€€€€€€€€€€€•±Í”9½¹”(€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€É•…Í½¸ô‰…±±}Ñ…É•ÑÍ}¥±±•…°ˆ°(€€€€€€€€€€€€¤(€€€€€€€€€€€É•ÑÕÉ¸É•Í½±Ù•‘}…É(€€€€€€€¥˜ÍÁ•±°¹…ÍÑ}­¥¹¹½Ð¥¸ì(€€€€€€€€€€€…ÍÑ-¥¹¹==i}MA%10°(€€€€€€€€€€€…ÍÑ-¥¹¹=U9QI}QIQ}MA10°(€€€€€€€€€€€…ÍÑ-¥¹¹I]}IL°(€€€€€€€€€€€…ÍÑ-¥¹¹Q=A}I}M1Q%=8°(€€€€€€€€€€€…ÍÑ-¥¹¹Q=A}IQUI}M1Q%=8°(€€€€€€€€€€€…ÍÑ-¥¹¹1%	IIe}MI!}Q=}!9°(€€€€€€€€€€€…ÍÑ-¥¹¹=AQ%=91}!9}IMP°(€€€€€€€€€€€…ÍÑ-¥¹¹IYeI}IUIM%=8°(€€€€€€€€€€€…ÍÑ-¥¹¹=9%Q%=91}M9-}Q=-9L°(€€€€€€€€€€€…ÍÑ-¥¹¹=AQ%=91}MQI=e}9}IQ°(€€€€€€€€€€€…ÍÑ-¥¹¹=9%Q%=91}MQI=e}9}IQ°(€€€€€€€€€€€…ÍÑ-¥¹¹IQUI}A=]I}5°(€€€€€€€€€€€…ÍÑ-¥¹¹5=1}Q=-9}=I}IQUI}AU5@°(€€€€€€€ôè(€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€™¥±Ñ•É}Á±…¸€ô9½¹”(€€€€€€€™¥±Ñ•É}Í•µ…¹Ñ¥Ì€ô9½¹”(€€€€€€€¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹==i}MA%10è(€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°MÑ…­=‰©•Ð¤(€€€€€€€€€€€½Õ¹Ñ•É•€ôÍ•±˜¹µ½Ù•}½‰©•Ð¡Ñ…É•Ð°€‰É…Ù•å…Éˆ°É•…Í½¸ô‰½½é•}ÍÁ¥±±}½Õ¹Ñ•É•ˆ¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰ÍÁ•±±}½Õ¹Ñ•É•ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Ñ…É•Ñ}ÍÁ•±±}¥õÑ…É•Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Ñ…É•Ñ}½‰©•Ñ}¥õÑ…É•Ð¹Ñ…É•Ñ}¥°(€€€€€€€€€€€€€€€Ñ…É•Ñ}…ÉõÑ…É•Ð¹…É¹¹…µ”°(€€€€€€€€€€€€€€€½¹ÑÉ½±±•ÈõÍÁ•±°¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÍÁ•±°¹…É¹½É…±•}Ñ•áÐ°(€€€€€€€€€€€€€€€Ñ…É•Ñ}É•±…Ñ¥½¹Í¡¥Àô‰½Õ¹Ñ•É}Ñ…É•Ñ}ÍÁ•±°ˆ°(€€€€€€€€€€€€€€€½Õ¹Ñ•É•‘}½‰©•Ñ}¥õ½Õ¹Ñ•É•¹½‰©•Ñ}¥°(€€€€€€€€€€€€¤(€€€€€€€€€€€µÕÑ…•¸€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹AI%9}Q=-9Ml‰µÕÑ…•¸‰t(€€€€€€€€€€€ÁÉ½É…´€ôQ½­•¹É•…Ñ¥½¹AÉ½É…´¡µÕÑ…•¸°€Ä¤(€€€€€€€€€€€É•…Ñ•€ôÍ•±˜¹É•…Ñ•}Ñ½­•¹Ì (€€€€€€€€€€€€€€€ÍÁ•±°¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€ÁÉ½É…´°(€€€€€€€€€€€€€€€Í½ÕÉ•}…ÉõÍÁ•±°¹…É¹¹…µ”°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÍÁ•±°¹…É¹½É…±•}Ñ•áÐ°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰½½é•}ÍÁ¥±±}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Ñ…É•Ñ}ÍÁ•±±}¥õÑ…É•Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€½Õ¹Ñ•É•‘}½‰©•Ñ}¥õ½Õ¹Ñ•É•¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€µÕÑ…•¹}Ñ½­•¹}¥õÉ•…Ñ•‘lÁt¹½‰©•Ñ}¥°(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹=U9QI}QIQ}MA10è(€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°MÑ…­=‰©•Ð¤(€€€€€€€€€€€½Õ¹Ñ•É•€ôÍ•±˜¹µ½Ù•}½‰©•Ð¡Ñ…É•Ð°€‰É…Ù•å…Éˆ°É•…Í½¸ô‰ÍÁ•±±}½Õ¹Ñ•É•ˆ¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰ÍÁ•±±}½Õ¹Ñ•É•ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Ñ…É•Ñ}ÍÁ•±±}¥õÑ…É•Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Ñ…É•Ñ}…ÉõÑ…É•Ð¹…É¹¹…µ”°(€€€€€€€€€€€€€€€½¹ÑÉ½±±•ÈõÍÁ•±°¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÍÁ•±°¹…É¹½É…±•}Ñ•áÐ°(€€€€€€€€€€€€€€€Ñ…É•Ñ}É•±…Ñ¥½¹Í¡¥Àô‰½Õ¹Ñ•É}Ñ…É•Ñ}¹½¹É•…ÑÕÉ•}ÍÁ•±°ˆ(€€€€€€€€€€€€€€€¥˜€‰¹½¹É•…ÑÕÉ”ˆ¥¸ÍÁ•±°¹…É¹½É…±•}Ñ•áÐ(€€€€€€€€€€€€€€€•±Í”€‰½Õ¹Ñ•É}Ñ…É•Ñ}ÍÁ•±°ˆ°(€€€€€€€€€€€€€€€½Õ¹Ñ•É•‘}½‰©•Ñ}¥õ½Õ¹Ñ•É•¹½‰©•Ñ}¥°(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹I]}ILè(€€€€€€€€€€€‘É…Ý}Í•µ…¹Ñ¥Ì€ô¹•áÐ (€€€€€€€€€€€€€€€€ (€€€€€€€€€€€€€€€€€€€Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹‘É…Ý}…É‘Í}Í•µ…¹Ñ¥}½Ù•É…”¡ÍÁ•±°¹…É°™É…µ•¹Ð¤(€€€€€€€€€€€€€€€€€€€™½È™É…µ•¹Ð¥¸Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹™É…µ•¹ÑÌ¡ÍÁ•±°¹…É¤(€€€€€€€€€€€€€€€€€€€¥˜Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹‘É…Ý}…É‘Í}Í•µ…¹Ñ¥}½Ù•É…”¡ÍÁ•±°¹…É°™É…µ•¹Ð¤(€€€€€€€€€€€€€€€€€€€¥Ì¹½Ð9½¹”(€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€9½¹”°(€€€€€€€€€€€€¤(€€€€€€€€€€€¥˜‘É…Ý}Í•µ…¹Ñ¥Ì¥Ì9½¹”½È¹½Ð‘É…Ý}Í•µ…¹Ñ¥Ì¹½Ù•É…”¹™Õ±±å}ÍÕÁÁ½ÉÑ•è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…­•‘É…ÜÍÁ•±°¹¼±½¹•È¡…Ì•á•ÕÑ…‰±”Í•µ…¹Ñ¥Ìˆ¤(€€€€€€€€€€€‘É…Ý}ÍÕ••‘•€ôÍ•±˜¹‘É…Ü¡Á±…å•È°‘É…Ý}Í•µ…¹Ñ¥Ì¹ÁÉ½É…´¹ÅÕ…¹Ñ¥Ñä¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰‘É…Ý}ÍÁ•±±}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Á±…å•ÈõÁ±…å•È¹¹…µ”°(€€€€€€€€€€€€€€€…ÉõÍÁ•±°¹¹…µ”°(€€€€€€€€€€€€€€€ÅÕ…¹Ñ¥Ñäõ‘É…Ý}Í•µ…¹Ñ¥Ì¹ÁÉ½É…´¹ÅÕ…¹Ñ¥Ñä°(€€€€€€€€€€€€€€€‘É…Ý}ÍÕ••‘•õ‘É…Ý}ÍÕ••‘•°(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹Q=A}I}M1Q%=8è(€€€€€€€€€€€ÁÉ½É…´€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹Ñ½Á}…É‘}Í•±•Ñ¥½¹}ÁÉ½É…´¡ÍÁ•±°¹…É¤(€€€€€€€€€€€¥˜ÁÉ½É…´¥Ì9½¹”è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…­•…ÉÍ•±•Ñ¥½¸¥Ì¹¼±½¹•È•á•ÕÑ…‰±”ˆ¤(€€€€€€€€€€€Í•±˜¹É•Í½±Ù•}Ñ½Á}…É‘}Í•±•Ñ¥½¸¡ÍÁ•±°¹½¹ÑÉ½±±•È°ÁÉ½É…´°Í½ÕÉ•}¥õÍÁ•±°¹½‰©•Ñ}¥¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹Q=A}IQUI}M1Q%=8è(€€€€€€€€€€€ÁÉ½É…´€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹Ñ½Á}É•…ÑÕÉ•}Í•±•Ñ¥½¹}ÁÉ½É…´¡ÍÁ•±°¹…É¤(€€€€€€€€€€€¥˜ÁÉ½É…´¥Ì9½¹”è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…­•Ñ½ÀµÉ•…ÑÕÉ”ÍÁ•±°±½ÍÐ¥ÑÌ½µÁ±•Ñ”Í•µ…¹Ñ¥Ìˆ¤(€€€€€€€€€€€Í•±˜¹É•Í½±Ù•}Ñ½Á}É•…ÑÕÉ•}Í•±•Ñ¥½¸ (€€€€€€€€€€€€€€€ÍÁ•±°¹½¹ÑÉ½±±•È°ÁÉ½É…´°Í½ÕÉ•}¥õÍÁ•±°¹½‰©•Ñ}¥(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹1%	IIe}MI!}Q=}!9è(€€€€€€€€€€€ÁÉ½É…´€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹±¥‰É…Éå}Í•…É¡}Ñ½}¡…¹‘}ÁÉ½É…´¡ÍÁ•±°¹…É¤(€€€€€€€€€€€¥˜ÁÉ½É…´¥Ì9½¹”è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…­•±¥‰É…ÉäÍ•…É ±½ÍÐ¥ÑÌ½µÁ±•Ñ”Í•µ…¹Ñ¥Ìˆ¤(€€€€€€€€€€€Í•±˜¹É•Í½±Ù•}±¥‰É…Éå}Í•…É¡}Ñ½}¡…¹ (€€€€€€€€€€€€€€€ÍÁ•±°¹½¹ÑÉ½±±•È°ÁÉ½É…´¹Í•…É¡}™É…µ•¹Ð°Í½ÕÉ•}¥õÍÁ•±°¹½‰©•Ñ}¥(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹=AQ%=91}!9}IMPè(€€€€€€€€€€€ÁÉ½É…´€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹½ÁÑ¥½¹…±}¡…¹‘}É•Í•Ñ}ÁÉ½É…´¡ÍÁ•±°¹…É¤(€€€€€€€€€€€¥˜ÁÉ½É…´¥Ì9½¹”è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…­•¡…¹É•Í•Ð±½ÍÐ¥ÑÌ½µÁ±•Ñ”Í•µ…¹Ñ¥Ìˆ¤(€€€€€€€€€€€Í•±˜¹É•Í½±Ù•}½ÁÑ¥½¹…±}¡…¹‘}É•Í•Ð (€€€€€€€€€€€€€€€ÁÉ½É…´¹‘É…Ý}ÅÕ…¹Ñ¥Ñä°ÁÉ½É…´¹•™™•Ñ}™É…µ•¹Ð°Í½ÕÉ•}¥õÍÁ•±°¹½‰©•Ñ}¥(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹IYeI}IUIM%=8è(€€€€€€€€€€€ÁÉ½É…´€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹É…Ù•å…É‘}É•ÕÉÍ¥½¹}ÁÉ½É…´¡ÍÁ•±°¹…É¤(€€€€€€€€€€€¥˜ÁÉ½É…´¥Ì9½¹”è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…­•É…Ù•å…ÉÉ•ÕÉÍ¥½¸±½ÍÐ¥ÑÌ½µÁ±•Ñ”Í•µ…¹Ñ¥Ìˆ¤(€€€€€€€€€€€•¹Ñ•É•€ômt(€€€€€€€€€€€¥¹Ù…±¥€ômt(€€€€€€€€€€€™½È½‰©•Ñ}¥¥¸ÍÁ•±°¹Ñ…É•Ñ}¥‘Ìè(€€€€€€€€€€€€€€€…¹‘¥‘…Ñ”€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡½‰©•Ñ}¥¤(€€€€€€€€€€€€€€€¥˜¹½ÐÍ•±˜¹}±•…±}É…Ù•å…É‘}É•ÕÉÍ¥½¹}Ñ…É•Ð (€€€€€€€€€€€€€€€€€€€…¹‘¥‘…Ñ”°ÍÁ•±°¹½¹ÑÉ½±±•È°ÁÉ½É…´¹µ…¹…}Ù…±Õ•}±¥µ¥Ð(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€¥¹Ù…±¥¹…ÁÁ•¹¡½‰©•Ñ}¥¤(€€€€€€€€€€€€€€€€€€€½¹Ñ¥¹Õ”(€€€€€€€€€€€€€€€Á•Éµ…¹•¹Ð€ôÍ•±˜¹µ½Ù•}½‰©•Ð (€€€€€€€€€€€€€€€€€€€…¹‘¥‘…Ñ”°(€€€€€€€€€€€€€€€€€€€€‰‰…ÑÑ±•™¥•±ˆ°(€€€€€€€€€€€€€€€€€€€½¹ÑÉ½±±•ÈõÍÁ•±°¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€É•…Í½¸ô‰É…Ù•å…É‘}É•ÕÉÍ¥½¹}É•ÑÕÉ¸ˆ°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Á•Éµ…¹•¹Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€•¹Ñ•É•¹…ÁÁ•¹ ¡½‰©•Ñ}¥°Á•Éµ…¹•¹Ð¤¤(€€€€€€€€€€€Í•±˜¹É•™É•Í¡}ÍÑ…Ñ¥}ÁÑ}µ½‘¥™¥•ÉÌ ¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰É…Ù•å…É‘}É•ÕÉÍ¥½¹}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€½¹ÑÉ½±±•ÈõÍÁ•±°¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÁÉ½É…´¹•™™•Ñ}™É…µ•¹Ð°(€€€€€€€€€€€€€€€Ñ…É•Ñ}¥‘Ìõ±¥ÍÐ¡ÍÁ•±°¹Ñ…É•Ñ}¥‘Ì¤°(€€€€€€€€€€€€€€€•¹Ñ•É•õl(€€€€€€€€€€€€€€€€€€€ì‰É…Ù•å…É‘}¥ˆèÍ½ÕÉ”°€‰‰…ÑÑ±•™¥•±‘}¥ˆè¥Ñ•´¹½‰©•Ñ}¥‘ô(€€€€€€€€€€€€€€€€€€€™½ÈÍ½ÕÉ”°¥Ñ•´¥¸•¹Ñ•É•(€€€€€€€€€€€€€€€t°(€€€€€€€€€€€€€€€¥¹Ù…±¥‘}Ñ…É•Ñ}¥‘Ìõ¥¹Ù…±¥°(€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹}ÁÉ½•ÍÍ}É•…ÑÕÉ•Í}•¹Ñ•É•‘}ÑÉ¥•ÉÌ (€€€€€€€€€€€€€€€ÑÕÁ±”¡¥Ñ•´™½È|°¥Ñ•´¥¸•¹Ñ•É•¤°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€‘•™•É}ÑÉ¥•ÉÌõQÉÕ”°(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹=9%Q%=91}M9-}Q=-9Lè(€€€€€€€€€€€ÁÉ½É…´€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹½¹‘¥Ñ¥½¹…±}Í¹•…­}Ñ½­•¹Í}ÁÉ½É…´¡ÍÁ•±°¹…É¤(€€€€€€€€€€€¥˜ÁÉ½É…´¥Ì9½¹”è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…­•½¹‘¥Ñ¥½¹…°Ñ½­•¸ÍÁ•±°±½ÍÐ¥ÑÌÍ•µ…¹Ñ¥Ìˆ¤(€€€€€€€€€€€É•…Ñ•€ôÍ•±˜¹É•…Ñ•}Ñ½­•¹Ì (€€€€€€€€€€€€€€€ÍÁ•±°¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€É•Á±…”¡ÁÉ½É…´¹Ñ½­•¸°Ñ…ÁÁ•õÍ¹•…­}…ÍÐ¤°(€€€€€€€€€€€€€€€Í½ÕÉ•}…ÉõÍÁ•±°¹¹…µ”°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÁÉ½É…´¹•™™•Ñ}™É…µ•¹Ð°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€‘•™•É}Á½ÍÑ}É•…Ñ¥½¸õQÉÕ”°(€€€€€€€€€€€€€€€‘•™•É}ÑÉ¥•ÉÌõQÉÕ”°(€€€€€€€€€€€€€€€…ÑÑ…­¥¹}‘•™•¹‘•ÈõÍÁ•±°¹Í¹•…­}‘•™•¹‘¥¹}Á±…å•È¥˜Í¹•…­}…ÍÐ•±Í”9½¹”°(€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰½¹‘¥Ñ¥½¹…±}Ñ½­•¹Í}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Ñ½­•¹}¥‘ÌõmÑ½­•¸¹½‰©•Ñ}¥™½ÈÑ½­•¸¥¸É•…Ñ•‘t°(€€€€€€€€€€€€€€€Í¹•…­}½ÍÑ}Á…¥õÍ¹•…­}…ÍÐ°(€€€€€€€€€€€€€€€Ñ…ÁÁ•õÍ¹•…­}…ÍÐ°(€€€€€€€€€€€€€€€…ÑÑ…­¥¹}‘•™•¹‘•ÈõÍÁ•±°¹Í¹•…­}‘•™•¹‘¥¹}Á±…å•È¥˜Í¹•…­}…ÍÐ•±Í”9½¹”°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÁÉ½É…´¹•™™•Ñ}™É…µ•¹Ð°(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹=AQ%=91}MQI=e}9}IQè(€€€€€€€€€€€ÁÉ½É…´€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹½ÁÑ¥½¹…±}‘•ÍÑÉ½å}…¹‘}É•…Ñ•}ÁÉ½É…´¡ÍÁ•±°¹…É¤(€€€€€€€€€€€¥˜ÁÉ½É…´¥Ì9½¹”è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…­•½ÁÑ¥½¹…°É•µ½Ù…°±½ÍÐ¥ÑÌÍ•µ…¹Ñ¥Ìˆ¤(€€€€€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤è(€€€€€€€€€€€€€€€Í•±˜¹‘•ÍÑÉ½ä¡Ñ…É•Ð¤(€€€€€€€€€€€É•…Ñ•€ôÍ•±˜¹É•…Ñ•}Ñ½­•¹Ì (€€€€€€€€€€€€€€€ÍÁ•±°¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€ÁÉ½É…´¹Ñ½­•¸°(€€€€€€€€€€€€€€€Í½ÕÉ•}…ÉõÍÁ•±°¹…É¹¹…µ”°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÍÁ•±°¹…É¹½É…±•}Ñ•áÐ°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€‘•™•É}Á½ÍÑ}É•…Ñ¥½¸õQÉÕ”°(€€€€€€€€€€€€€€€‘•™•É}ÑÉ¥•ÉÌõQÉÕ”°(€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰½ÁÑ¥½¹…±}É•µ½Ù…±}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÍÁ•±°¹Ñ…É•Ñ}¥°(€€€€€€€€€€€€€€€Ñ½­•¹}¥‘Ìõm¥Ñ•´¹½‰©•Ñ}¥™½È¥Ñ•´¥¸É•…Ñ•‘t°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÍÁ•±°¹…É¹½É…±•}Ñ•áÐ°(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹=9%Q%=91}MQI=e}9}IQè(€€€€€€€€€€€ÁÉ½É…´€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹½¹‘¥Ñ¥½¹…±}‘•ÍÑÉ½å}…¹‘}É•…Ñ•}ÁÉ½É…´¡ÍÁ•±°¹…É¤(€€€€€€€€€€€¥˜ÁÉ½É…´¥Ì9½¹”è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…­•½¹‘¥Ñ¥½¹…°É•µ½Ù…°±½ÍÐ¥ÑÌÍ•µ…¹Ñ¥Ìˆ¤(€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€±…ÍÑ}­¹½Ý¹}µ…¹…}Ù…±Õ”€ôÑ…É•Ð¹…É¹µ…¹…}Ù…±Õ”(€€€€€€€€€€€Í•±˜¹‘•ÍÑÉ½ä¡Ñ…É•Ð¤(€€€€€€€€€€€É•…Ñ•€ô€ (€€€€€€€€€€€€€€€Í•±˜¹É•…Ñ•}Ñ½­•¹Ì (€€€€€€€€€€€€€€€€€€€ÍÁ•±°¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€ÁÉ½É…´¹Ñ½­•¸°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}…ÉõÍÁ•±°¹…É¹¹…µ”°(€€€€€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÍÁ•±°¹…É¹½É…±•}Ñ•áÐ°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€‘•™•É}Á½ÍÑ}É•…Ñ¥½¸õQÉÕ”°(€€€€€€€€€€€€€€€€€€€‘•™•É}ÑÉ¥•ÉÌõQÉÕ”°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€¥˜±…ÍÑ}­¹½Ý¹}µ…¹…}Ù…±Õ”€ðôÁÉ½É…´¹µ…á¥µÕµ}µ…¹…}Ù…±Õ”(€€€€€€€€€€€€€€€•±Í”€ ¤(€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰½¹‘¥Ñ¥½¹…±}É•µ½Ù…±}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÍÁ•±°¹Ñ…É•Ñ}¥°(€€€€€€€€€€€€€€€±…ÍÑ}­¹½Ý¹}µ…¹…}Ù…±Õ”õ±…ÍÑ}­¹½Ý¹}µ…¹…}Ù…±Õ”°(€€€€€€€€€€€€€€€Ñ½­•¹}¥‘Ìõm¥Ñ•´¹½‰©•Ñ}¥™½È¥Ñ•´¥¸É•…Ñ•‘t°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÍÁ•±°¹…É¹½É…±•}Ñ•áÐ°(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹-%-}IQUI}APè(€€€€€€€€€€€ÁÉ½É…´€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹­¥­•‘}É•…ÑÕÉ•}ÁÑ}ÁÉ½É…´¡ÍÁ•±°¹…É¤(€€€€€€€€€€€¥˜ÁÉ½É…´¥Ì9½¹”è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…­•­¥­•µ½‘¥™¥•È¥Ì¹¼±½¹•È•á•ÕÑ…‰±”ˆ¤(€€€€€€€€€€€µ½‘¥™¥•È€ôÁÉ½É…´¹­¥­•¥˜ÍÁ•±°¹­¥­•É}Í…É¥™¥•}¥¥Ì¹½Ð9½¹”•±Í”ÁÉ½É…´¹½É‘¥¹…Éä(€€€€€€€€€€€Í•±˜¹…ÁÁ±å}ÁÑ}µ½‘¥™¥•È (€€€€€€€€€€€€€€€Ñ…É•Ð°(€€€€€€€€€€€€€€€€©µ½‘¥™¥•È°(€€€€€€€€€€€€€€€‘ÕÉ…Ñ¥½¸ô‰Õ¹Ñ¥±}•¹‘}½™}ÑÕÉ¸ˆ°(€€€€€€€€€€€€€€€Í½ÕÉ•}…ÉõÍÁ•±°¹¹…µ”°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÍÁ•±°¹…É¹½É…±•}Ñ•áÐ°(€€€€€€€€€€€€€€€Í½ÕÉ•}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰­¥­•‘}É•…ÑÕÉ•}ÁÑ}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÑ…É•Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€­¥­•É}Í…É¥™¥•}¥õÍÁ•±°¹­¥­•É}Í…É¥™¥•}¥°(€€€€€€€€€€€€€€€Á½Ý•Èõµ½‘¥™¥•ÉlÁt°(€€€€€€€€€€€€€€€Ñ½Õ¡¹•ÍÌõµ½‘¥™¥•ÉlÅt°(€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹¡•­}ÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¹Ì ¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹QIQ}=U9QI}-e]=I}I9Pè(€€€€€€€€€€€ÁÉ½É…´€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹Ñ…É•Ñ•‘}½Õ¹Ñ•É}­•åÝ½É‘}É…¹Ñ}ÁÉ½É…´¡ÍÁ•±°¹…É¤(€€€€€€€€€€€¥˜ÁÉ½É…´¥Ì9½¹”è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…­•½Õ¹Ñ•Èµ…¹µ­•åÝ½ÉÍÁ•±°±½ÍÐ¥ÑÌÍ•µ…¹Ñ¥Ìˆ¤(€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€Í•±˜¹Á±…•}½Õ¹Ñ•ÉÌ (€€€€€€€€€€€€€€€Ñ…É•Ð°(€€€€€€€€€€€€€€€ÁÉ½É…´¹½Õ¹Ñ•É}ÑåÁ”°(€€€€€€€€€€€€€€€ÁÉ½É…´¹ÅÕ…¹Ñ¥Ñä°(€€€€€€€€€€€€€€€Í½ÕÉ•}…ÉõÍÁ•±°¹¹…µ”°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÁÉ½É…´¹•™™•Ñ}™É…µ•¹Ð°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€‘•™•É}Á½ÍÑ}Á±…•µ•¹ÐõQÉÕ”°(€€€€€€€€€€€€¤(€€€€€€€€€€€™½È­•åÝ½É¥¸ÁÉ½É…´¹­•åÝ½É‘Ìè(€€€€€€€€€€€€€€€Ñ…É•Ð¹Ñ•µÁ½É…Éå}­•åÝ½É‘}•™™•ÑÌ¹…ÁÁ•¹ (€€€€€€€€€€€€€€€€€€€Q•µÁ½É…Éå-•åÝ½É‘™™•Ð (€€€€€€€€€€€€€€€€€€€€€€€Q•µÁ½É…Éå-•åÝ½É¡­•åÝ½É¤°(€€€€€€€€€€€€€€€€€€€€€€€€‰Õ¹Ñ¥±}•¹‘}½™}ÑÕÉ¸ˆ°(€€€€€€€€€€€€€€€€€€€€€€€ÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€ÁÉ½É…´¹•™™•Ñ}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€Ñ¥µ•ÍÑ…µÀõÍ•±˜¹}•™™•Ñ}Ñ¥µ•ÍÑ…µÀ ¤°(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰½Õ¹Ñ•É}­•åÝ½É‘}É…¹Ñ}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÑ…É•Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€½Õ¹Ñ•É}ÑåÁ”õÁÉ½É…´¹½Õ¹Ñ•É}ÑåÁ”°(€€€€€€€€€€€€€€€ÅÕ…¹Ñ¥ÑäõÁÉ½É…´¹ÅÕ…¹Ñ¥Ñä°(€€€€€€€€€€€€€€€­•åÝ½É‘Ìõ±¥ÍÐ¡ÁÉ½É…´¹­•åÝ½É‘Ì¤°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÁÉ½É…´¹•™™•Ñ}™É…µ•¹Ð°(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹Q5A=IIe}Q!}IQUI9}I9Pè(€€€€€€€€€€€ÁÉ½É…´€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹Ñ•µÁ½É…Éå}‘•…Ñ¡}É•ÑÕÉ¹}É…¹Ñ}ÁÉ½É…´¡ÍÁ•±°¹…É¤(€€€€€€€€€€€¥˜ÁÉ½É…´¥Ì9½¹”è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…­•Ñ•µÁ½É…Éä‘•…Ñ É•ÑÕÉ¸±½ÍÐ½µÁ±•Ñ”Í•µ…¹Ñ¥Ìˆ¤(€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€Ñ¥µ•ÍÑ…µÀ€ôÍ•±˜¹}•™™•Ñ}Ñ¥µ•ÍÑ…µÀ ¤(€€€€€€€€€€€Ñ…É•Ð¹Ñ•µÁ½É…Éå}­•åÝ½É‘}•™™•ÑÌ¹…ÁÁ•¹ (€€€€€€€€€€€€€€€Q•µÁ½É…Éå-•åÝ½É‘™™•Ð (€€€€€€€€€€€€€€€€€€€Q•µÁ½É…Éå-•åÝ½É¡ÁÉ½É…´¹­•åÝ½É¤°(€€€€€€€€€€€€€€€€€€€€‰Õ¹Ñ¥±}•¹‘}½™}ÑÕÉ¸ˆ°(€€€€€€€€€€€€€€€€€€€ÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€ÁÉ½É…´¹•™™•Ñ}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€Ñ¥µ•ÍÑ…µÀõÑ¥µ•ÍÑ…µÀ°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€¤(€€€€€€€€€€€Ñ…É•Ð¹Ñ•µÁ½É…Éå}‘•…Ñ¡}É•ÑÕÉ¹}•™™•ÑÌ¹…ÁÁ•¹ (€€€€€€€€€€€€€€€Q•µÁ½É…Éå•…Ñ¡I•ÑÕÉ¹™™•Ð (€€€€€€€€€€€€€€€€€€€€‰Õ¹Ñ¥±}•¹‘}½™}ÑÕÉ¸ˆ°ÍÁ•±°¹½‰©•Ñ}¥°ÁÉ½É…´¹•™™•Ñ}™É…µ•¹Ð°Ñ¥µ•ÍÑ…µÀ(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰Ñ•µÁ½É…Éå}‘•…Ñ¡}É•ÑÕÉ¹}É…¹Ñ•ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÑ…É•Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€­•åÝ½ÉõÁÉ½É…´¹­•åÝ½É°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÁÉ½É…´¹•™™•Ñ}™É…µ•¹Ð°(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹Q5A=IIe}QeA}	M}AQ}I\è(€€€€€€€€€€€ÁÉ½É…´€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹Ñ•µÁ½É…Éå}ÑåÁ•}‰…Í•}ÁÑ}‘É…Ý}ÁÉ½É…´¡ÍÁ•±°¹…É¤(€€€€€€€€€€€¥˜ÁÉ½É…´¥Ì9½¹”è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…­•…¹¥µ…Ñ¥½¸µ…¹µ‘É…ÜÍÁ•±°±½ÍÐ¥ÑÌÍ•µ…¹Ñ¥Ìˆ¤(€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€Í•±˜¹…ÁÁ±å}Ñ•µÁ½É…Éå}ÑåÁ•}…¹‘}‰…Í•}ÁÐ (€€€€€€€€€€€€€€€Ñ…É•Ð°(€€€€€€€€€€€€€€€…‘‘•‘}ÑåÁ•ÌõÁÉ½É…´¹…‘‘•‘}ÑåÁ•Ì°(€€€€€€€€€€€€€€€Á½Ý•ÈõÁÉ½É…´¹Á½Ý•È°(€€€€€€€€€€€€€€€Ñ½Õ¡¹•ÍÌõÁÉ½É…´¹Ñ½Õ¡¹•ÍÌ°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Í½ÕÉ•}…ÉõÍÁ•±°¹¹…µ”°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÁÉ½É…´¹•™™•Ñ}™É…µ•¹Ð°(€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹É•™É•Í¡}ÍÑ…Ñ¥}ÁÑ}µ½‘¥™¥•ÉÌ ¤(€€€€€€€€€€€‘É…Ý}ÍÕ••‘•€ôÍ•±˜¹‘É…Ü¡Á±…å•È°ÁÉ½É…´¹‘É…Ý}ÅÕ…¹Ñ¥Ñä¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰Ñ•µÁ½É…Éå}…¹¥µ…Ñ¥½¹}‘É…Ý}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÑ…É•Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€ÑåÁ•}±¥¹”õÑ…É•Ð¹ÑåÁ•}±¥¹”°(€€€€€€€€€€€€€€€Á½Ý•ÈõÑ…É•Ð¹Á½Ý•È°(€€€€€€€€€€€€€€€Ñ½Õ¡¹•ÍÌõÑ…É•Ð¹Ñ½Õ¡¹•ÍÌ°(€€€€€€€€€€€€€€€‘É…Ý}ÅÕ…¹Ñ¥ÑäõÁÉ½É…´¹‘É…Ý}ÅÕ…¹Ñ¥Ñä°(€€€€€€€€€€€€€€€‘É…Ý}ÍÕ••‘•õ‘É…Ý}ÍÕ••‘•°(€€€€€€€€€€€€€€€‘É…Ý¹}™É…µ•¹ÐõÁÉ½É…´¹‘É…Ý}™É…µ•¹Ð°(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹QIQ}1%	IIe}IQUI9}9}Q=-8è(€€€€€€€€€€€ÁÉ½É…´€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹Ñ…É•Ñ•‘}±¥‰É…Éå}É•ÑÕÉ¹}…¹‘}Ñ½­•¹}ÁÉ½É…´¡ÍÁ•±°¹…É¤(€€€€€€€€€€€¥˜ÁÉ½É…´¥Ì9½¹”è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…­•±¥‰É…ÉäÉ•ÑÕÉ¸±½ÍÐ¥ÑÌ½µÁ±•Ñ”Í•µ…¹Ñ¥Ìˆ¤(€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€½Ý¹•É}¥¹‘•à€ôÑ…É•Ð¹½Ý¹•È(€€€€€€€€€€€½ÁÑ¥½¹Ì€ô€ ‰Ñ½Àˆ°€‰‰½ÑÑ½´ˆ¤(€€€€€€€€€€€Í•±˜¹}±¥‰É…Éå}Á½Í¥Ñ¥½¹}¡½¥•}…Ñ¥Ù”€ôQÉÕ”(€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€Á½Í¥Ñ¥½¸€ôÍ•±˜¹±¥‰É…Éå}Á½Í¥Ñ¥½¹}¡½½Í•È (€€€€€€€€€€€€€€€€€€€½Ý¹•É}¥¹‘•à°ÍÁ•±°¹½‰©•Ñ}¥°Ñ…É•Ð¹½‰©•Ñ}¥°½ÁÑ¥½¹Ì(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€™¥¹…±±äè(€€€€€€€€€€€€€€€Í•±˜¹}±¥‰É…Éå}Á½Í¥Ñ¥½¹}¡½¥•}…Ñ¥Ù”€ô…±Í”(€€€€€€€€€€€¥˜Á½Í¥Ñ¥½¸¹½Ð¥¸½ÁÑ¥½¹Ìè(€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰Ñ…É•Ð½Ý¹•ÈµÕÍÐÍ•±•Ð„±•…°±¥‰É…ÉäÁ½Í¥Ñ¥½¸ˆ¤(€€€€€€€€€€€µ½Ù•€ôÍ•±˜¹µ½Ù•}½‰©•Ð (€€€€€€€€€€€€€€€Ñ…É•Ð°(€€€€€€€€€€€€€€€€‰±¥‰É…Éäˆ°(€€€€€€€€€€€€€€€±¥‰É…Éå}Á½Í¥Ñ¥½¸õÁ½Í¥Ñ¥½¸°(€€€€€€€€€€€€€€€É•…Í½¸ô‰Ñ…É•Ñ•‘}±¥‰É…Éå}É•ÑÕÉ¸ˆ°(€€€€€€€€€€€€¤(€€€€€€€€€€€É•…Ñ•€ôÍ•±˜¹É•…Ñ•}Ñ½­•¹Ì (€€€€€€€€€€€€€€€ÍÁ•±°¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€ÁÉ½É…´¹Ñ½­•¸°(€€€€€€€€€€€€€€€Í½ÕÉ•}…ÉõÍÁ•±°¹…É¹¹…µ”°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÁÉ½É…´¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€‘•™•É}Á½ÍÑ}É•…Ñ¥½¸õQÉÕ”°(€€€€€€€€€€€€€€€‘•™•É}ÑÉ¥•ÉÌõQÉÕ”°(€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰Ñ…É•Ñ•‘}±¥‰É…Éå}É•ÑÕÉ¹}Ñ½­•¹}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÑ…É•Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Ñ…É•Ñ}½Ý¹•Èõ½Ý¹•É}¥¹‘•à°(€€€€€€€€€€€€€€€¡½Í•¹}Á½Í¥Ñ¥½¸õÁ½Í¥Ñ¥½¸°(€€€€€€€€€€€€€€€‘•ÍÑ¥¹…Ñ¥½¹}¥õµ½Ù•¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€Ñ½­•¹}¥‘Ìõm¥Ñ•´¹½‰©•Ñ}¥™½È¥Ñ•´¥¸É•…Ñ•‘t°(€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÁÉ½É…´¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹5=1}Q=-9}=I}IQUI}AU5@è(€€€€€€€€€€€¥˜ÍÁ•±°¹µ½‘•}™É…µ•¹Ð€ôôµ½‘…°¹Ñ½­•¹}™É…µ•¹Ðè(€€€€€€€€€€€€€€€É•…Ñ•€ôÍ•±˜¹É•…Ñ•}Ñ½­•¹Ì (€€€€€€€€€€€€€€€€€€€ÍÁ•±°¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€µ½‘…°¹Ñ½­•¸°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}…ÉõÍÁ•±°¹¹…µ”°(€€€€€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÍÁ•±°¹µ½‘•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€‘•™•É}Á½ÍÑ}É•…Ñ¥½¸õQÉÕ”°(€€€€€€€€€€€€€€€€€€€‘•™•É}ÑÉ¥•ÉÌõQÉÕ”°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰µ½‘…±}ÍÁ•±±}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€µ½‘•}™É…µ•¹ÐõÍÁ•±°¹µ½‘•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€Ñ½­•¹}¥‘ÌõmÑ½­•¸¹½‰©•Ñ}¥™½ÈÑ½­•¸¥¸É•…Ñ•‘t°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õ9½¹”°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€•±Í”è(€€€€€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€Í•±˜¹…ÁÁ±å}ÁÑ}µ½‘¥™¥•È (€€€€€€€€€€€€€€€€€€€Ñ…É•Ð°(€€€€€€€€€€€€€€€€€€€µ½‘…°¹Á½Ý•È°(€€€€€€€€€€€€€€€€€€€µ½‘…°¹Ñ½Õ¡¹•ÍÌ°(€€€€€€€€€€€€€€€€€€€‘ÕÉ…Ñ¥½¸ô‰Õ¹Ñ¥±}•¹‘}½™}ÑÕÉ¸ˆ°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}…ÉõÍÁ•±°¹¹…µ”°(€€€€€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÍÁ•±°¹µ½‘•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€Ñ…É•Ð¹Ñ•µÁ½É…Éå}­•åÝ½É‘}•™™•ÑÌ¹…ÁÁ•¹ (€€€€€€€€€€€€€€€€€€€Q•µÁ½É…Éå-•åÝ½É‘™™•Ð (€€€€€€€€€€€€€€€€€€€€€€€µ½‘…°¹ÍÑÉ¥­•}­•åÝ½É°(€€€€€€€€€€€€€€€€€€€€€€€€‰Õ¹Ñ¥±}•¹‘}½™}ÑÕÉ¸ˆ°(€€€€€€€€€€€€€€€€€€€€€€€ÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€ÍÁ•±°¹µ½‘•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€Ñ¥µ•ÍÑ…µÀõÍ•±˜¹}•™™•Ñ}Ñ¥µ•ÍÑ…µÀ ¤°(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰µ½‘…±}ÍÁ•±±}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€µ½‘•}™É…µ•¹ÐõÍÁ•±°¹µ½‘•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€Ñ½­•¹}¥‘Ìõmt°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÑ…É•Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€­•åÝ½Éõµ½‘…°¹ÍÑÉ¥­•}­•åÝ½É¹Ù…±Õ”°(€€€€€€€€€€€€€€€€€€€Á½Ý•Èõµ½‘…°¹Á½Ý•È°(€€€€€€€€€€€€€€€€€€€Ñ½Õ¡¹•ÍÌõµ½‘…°¹Ñ½Õ¡¹•ÍÌ°(€€€€€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥¸í…ÍÑ-¥¹¹5|Í}=AA=M%9}IQUI°…ÍÑ-¥¹¹1}5ôè(€€€€€€€€€€€Í•µ…¹Ñ¥Ì€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹‘…µ…•}Í•µ…¹Ñ¥}½Ù•É…” (€€€€€€€€€€€€€€€ÍÁ•±°¹…É°ÍÁ•±°¹…É¹½É…±•}Ñ•áÐ(€€€€€€€€€€€€¤(€€€€€€€€€€€¥˜Í•µ…¹Ñ¥Ì¥Ì9½¹”½È¹½ÐÍ•µ…¹Ñ¥Ì¹½Ù•É…”¹Á…å±½…‘}•á•ÕÑ…‰±”è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…­•‘…µ…”ÍÁ•±°¹¼±½¹•È¡…Ì•á•ÕÑ…‰±”Í•µ…¹Ñ¥Ìˆ¤(€€€€€€€€€€€…ÍÍ•ÉÐÍ•µ…¹Ñ¥Ì¹ÁÉ½É…´¹…µ½Õ¹Ð¥Ì¹½Ð9½¹”(€€€€€€€€€€€™¥±Ñ•É}Í•µ…¹Ñ¥Ì€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹¡…¹‘}‰½ÑÑ½µ}‘É…Ý}Í•µ…¹Ñ¥}½Ù•É…” (€€€€€€€€€€€€€€€ÍÁ•±°¹…É°ÍÁ•±°¹…É¹½É…±•}Ñ•áÐ(€€€€€€€€€€€€¤(€€€€€€€€€€€™¥±Ñ•É}•á•ÕÑ…‰±”€ô€ (€€€€€€€€€€€€€€€™¥±Ñ•É}Í•µ…¹Ñ¥Ì¥Ì¹½Ð9½¹”…¹™¥±Ñ•É}Í•µ…¹Ñ¥Ì¹½Ù•É…”¹™Õ±±å}ÍÕÁÁ½ÉÑ•(€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹‘•…±}‘…µ…” (€€€€€€€€€€€€€€€…µ…•QÉ…¹Í…Ñ¥½¸ (€€€€€€€€€€€€€€€€€€€ÍÁ•±°¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€ÍÁ•±°°(€€€€€€€€€€€€€€€€€€€…µ…•Q…É•Ñ-¥¹¹IQUI°(€€€€€€€€€€€€€€€€€€€Í•µ…¹Ñ¥Ì¹ÁÉ½É…´¹…µ½Õ¹Ð°(€€€€€€€€€€€€€€€€€€€ÍÁ•±°¹…É¹½É…±•}Ñ•áÐ°(€€€€€€€€€€€€€€€€€€€Ñ…É•ÐõÑ…É•Ð°(€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€‘•™•É}Á½ÍÑ}‘…µ…”õ™¥±Ñ•É}•á•ÕÑ…‰±”°(€€€€€€€€€€€€¤(€€€€€€€€€€€¥˜™¥±Ñ•É}•á•ÕÑ…‰±”è(€€€€€€€€€€€€€€€…ÍÍ•ÉÐ™¥±Ñ•É}Í•µ…¹Ñ¥Ì¥Ì¹½Ð9½¹”(€€€€€€€€€€€€€€€™¥±Ñ•É}Á±…¸€ôÍ•±˜¹¡½½Í•}¡…¹‘}‰½ÑÑ½µ}‘É…Ü (€€€€€€€€€€€€€€€€€€€ÍÁ•±°¹½¹ÑÉ½±±•È°™¥±Ñ•É}Í•µ…¹Ñ¥Ì¹ÁÉ½É…´(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€Í•±˜¹½µµ¥Ñ}¡…¹‘}‰½ÑÑ½µ}‘É…Ü (€€€€€€€€€€€€€€€€€€€ÍÁ•±°¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€™¥±Ñ•É}Í•µ…¹Ñ¥Ì¹ÁÉ½É…´°(€€€€€€€€€€€€€€€€€€€™¥±Ñ•É}Á±…¸°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÍÁ•±°¹…É¹½É…±•}Ñ•áÐ°(€€€€€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹IQUI}A=]I}5è(€€€€€€€€€€€ÁÉ½É…´€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹É•…ÑÕÉ•}Á½Ý•É}‘…µ…•}ÁÉ½É…´ (€€€€€€€€€€€€€€€ÍÁ•±°¹…É°ÍÁ•±°¹…É¹½É…±•}Ñ•áÐ(€€€€€€€€€€€€¤(€€€€€€€€€€€¥˜ÁÉ½É…´¥Ì9½¹”è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…­•É•…ÑÕÉ”µÁ½Ý•È‘…µ…”±½ÍÐ¥ÑÌÍ•µ…¹Ñ¥Ìˆ¤(€€€€€€€€€€€Í½ÕÉ”€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡ÍÁ•±°¹Í½ÕÉ•}Ñ…É•Ñ}¥½È€ˆˆ¤(€€€€€€€€€€€Í½ÕÉ•}±•…°€ôÍ•±˜¹}±•…±}É•…ÑÕÉ•}Á½Ý•É}Í½ÕÉ”¡Í½ÕÉ”°ÍÁ•±°¹½¹ÑÉ½±±•È¤(€€€€€€€€€€€Ñ…É•Ñ}±•…°€ôÍ•±˜¹}±•…±}É•…ÑÕÉ•}Á½Ý•É}É•¥Á¥•¹Ð¡Ñ…É•Ð°ÍÁ•±°¹½¹ÑÉ½±±•È¤(€€€€€€€€€€€…µ½Õ¹Ð€ôµ…à À°Í½ÕÉ”¹Á½Ý•È¤¥˜Í½ÕÉ•}±•…°•±Í”€À(€€€€€€€€€€€¥˜Í½ÕÉ•}±•…°…¹Ñ…É•Ñ}±•…°…¹…µ½Õ¹Ð€ø€Àè(€€€€€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Í½ÕÉ”°A•Éµ…¹•¹Ð¤…¹¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€•Ù•¹Ð€ôÍ•±˜¹‘•…±}‘…µ…” (€€€€€€€€€€€€€€€€€€€…µ…•QÉ…¹Í…Ñ¥½¸ (€€€€€€€€€€€€€€€€€€€€€€€ÍÁ•±°¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€Í½ÕÉ”°(€€€€€€€€€€€€€€€€€€€€€€€…µ…•Q…É•Ñ-¥¹¹IQUI°(€€€€€€€€€€€€€€€€€€€€€€€…µ½Õ¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€ÍÁ•±°¹…É¹½É…±•}Ñ•áÐ°(€€€€€€€€€€€€€€€€€€€€€€€Ñ…É•ÐõÑ…É•Ð°(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰É•…ÑÕÉ•}Á½Ý•É}‘…µ…•}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}Ñ…É•Ñ}¥õÍ½ÕÉ”¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÑ…É•Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€‘…µ…•}•Ù•¹Ñ}¥õ•Ù•¹Ð¹•Ù•¹Ñ}¥°(€€€€€€€€€€€€€€€€€€€…µ½Õ¹Ðõ…µ½Õ¹Ð°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€•±Í”è(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰É•…ÑÕÉ•}Á½Ý•É}‘…µ…•}É•Í½±Ù•‘}¹½}‘…µ…”ˆ°(€€€€€€€€€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍÁ•±°¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}Ñ…É•Ñ}¥õÍÁ•±°¹Í½ÕÉ•}Ñ…É•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}¥õÍÁ•±°¹Ñ…É•Ñ}¥°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}±•…°õÍ½ÕÉ•}±•…°°(€€€€€€€€€€€€€€€€€€€Ñ…É•Ñ}±•…°õÑ…É•Ñ}±•…°°(€€€€€€€€€€€€€€€€€€€…µ½Õ¹Ðõ…µ½Õ¹Ð°(€€€€€€€€€€€€€€€€¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹MQI=e}IQ%Q}9!9Q59Q}=I}A=]I|Ñ}IQUIè(€€€€€€€€€€€Í•±˜¹‘•ÍÑÉ½ä¡Ñ…É•Ð¤(€€€€€€€•±¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹QIQ}I5=Y0è(€€€€€€€€€€€É•µ½Ù…°€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹Ñ…É•Ñ•‘}É•µ½Ù…±}ÁÉ½É…´¡ÍÁ•±°¹…É¤(€€€€€€€€€€€…ÍÍ•ÉÐÉ•µ½Ù…°¥Ì¹½Ð9½¹”(€€€€€€€€€€€Ý…Í}•¹¡…¹Ñµ•¹Ð€ô€‰¹¡…¹Ñµ•¹Ðˆ¥¸Ñ…É•Ð¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€€€€€¥˜É•µ½Ù…°¹‘•ÍÑ¥¹…Ñ¥½¸€ôô€‰•á¥±”ˆè(€€€€€€€€€€€€€€€Í•±˜¹µ½Ù•}½‰©•Ð¡Ñ…É•Ð°€‰•á¥±”ˆ°É•…Í½¸ô‰Ñ…É•Ñ•‘}É•µ½Ù…±}•á¥±”ˆ¤(€€€€€€€€€€€•±Í”è(€€€€€€€€€€€€€€€Í•±˜¹‘•ÍÑÉ½ä¡Ñ…É•Ð¤(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€Ý…Í}•¹¡…¹Ñµ•¹Ð(€€€€€€€€€€€€€€€…¹¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Ñ…É•Ð°€‰‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€€€€€€€€€…¹É•µ½Ù…°¹•¹¡…¹Ñµ•¹Ñ}±¥™•}±½ÍÌ(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€Í•±˜¹Á±…å•ÉÍmÍÁ•±°¹½¹ÑÉ½±±•Ét¹±¥™”€´ôÉ•µ½Ù…°¹•¹¡…¹Ñµ•¹Ñ}±¥™•}±½ÍÌ(€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€‰±¥™•}±½ÍÐˆ°(€€€€€€€€€€€€€€€€€€€Á±…å•ÈõÍ•±˜¹Á±…å•ÉÍmÍÁ•±°¹½¹ÑÉ½±±•Ét¹¹…µ”°(€€€€€€€€€€€€€€€€€€€…µ½Õ¹ÐõÉ•µ½Ù…°¹•¹¡…¹Ñµ•¹Ñ}±¥™•}±½ÍÌ°(€€€€€€€€€€€€€€€€€€€Í½ÕÉ”õÍÁ•±°¹¹…µ”°(€€€€€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÍÁ•±°¹…É¹½É…±•}Ñ•áÐ°(€€€€€€€€€€€€€€€€¤(€€€€€€€É•Í½±Ù•‘}…É€ôÍ•±˜¹µ½Ù•}½‰©•Ð¡ÍÁ•±°°€‰É…Ù•å…Éˆ°É•…Í½¸ô‰ÍÁ•±±}É•Í½±Ù•ˆ¤(€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡É•Í½±Ù•‘}…É°…É‘=‰©•Ð¤(€€€€€€€Í•±˜¹É•Á½ÉÑ}Õ¹ÍÕÁÁ½ÉÑ•‘}…‰¥±¥Ñ¥•Ì¡ÍÁ•±°¹½¹ÑÉ½±±•È°ÍÁ•±°¹…É°Í½ÕÉ”õÉ•Í½±Ù•‘}…É¤(€€€€€€€Í•±˜¹}Ý¥Ñ¹•ÍÍ}É•Í½±Ù•‘}Õ¹ÍÕÁÁ½ÉÑ•‘}¥¹ÍÑÉÕÑ¥½¹Ì¡É•Í½±Ù•‘}…É¤(€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€‰ÍÁ•±±}É•Í½±Ù•ˆ°(€€€€€€€€€€€•Ù•¹Ñ}¥õ˜‰ÍÁ•±°éíÍÑ…­}½‰©•Ñ}¥‘ôéÉ•Í½±Ù•ˆ°(€€€€€€€€€€€Á±…å•ÈõÁ±…å•È¹¹…µ”°(€€€€€€€€€€€…ÉõÍÁ•±°¹¹…µ”°(€€€€€€€€€€€Í½ÕÉ•}¥õÉ•Í½±Ù•‘}…É¹½‰©•Ñ}¥°(€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÍÁ•±°¹…É¹½É…±•}Ñ•áÐ°(€€€€€€€€€€€Ñ…É•Ðô¡Ñ…É•Ð¹…É¹¹…µ”¥˜¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤•±Í”9½¹”¤°(€€€€€€€€€€€Ñ…É•Ñ}Í½ÕÉ•}¥ô¡Ñ…É•Ð¹½‰©•Ñ}¥¥˜¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤•±Í”9½¹”¤°(€€€€€€€€¤(€€€€€€€¥˜™¥±Ñ•É}Á±…¸¥Ì¹½Ð9½¹”è(€€€€€€€€€€€Í•±˜¹¡•­}ÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¹Ì ¤(€€€€€€€€€€€Í•±˜¹¡•­}±¥™” ¤(€€€€€€€€€€€Í•±˜¹}ÁÕÑ}Á•¹‘¥¹}ÑÉ¥•ÉÍ}½¹}ÍÑ…¬ ¤(€€€€€€€€€€€Í•±˜¹}‘É…¥¹}ÑÉ¥•É•‘}…‰¥±¥Ñ¥•Ì ¤(€€€€€€€¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥¸ì(€€€€€€€€€€€…ÍÑ-¥¹¹=AQ%=91}MQI=e}9}IQ°(€€€€€€€€€€€…ÍÑ-¥¹¹=9%Q%=91}MQI=e}9}IQ°(€€€€€€€€€€€…ÍÑ-¥¹¹QIQ}I5=Y0°(€€€€€€€€€€€…ÍÑ-¥¹¹5=1}Q=-9}=I}IQUI}AU5@°(€€€€€€€€€€€…ÍÑ-¥¹¹QIQ}=U9QI}-e]=I}I9P°(€€€€€€€€€€€…ÍÑ-¥¹¹Q5A=IIe}Q!}IQUI9}I9P°(€€€€€€€€€€€…ÍÑ-¥¹¹Q5A=IIe}QeA}	M}AQ}I\°(€€€€€€€€€€€…ÍÑ-¥¹¹1%	IIe}MI!}Q=}!9°(€€€€€€€€€€€…ÍÑ-¥¹¹=AQ%=91}!9}IMP°(€€€€€€€€€€€…ÍÑ-¥¹¹IYeI}IUIM%=8°(€€€€€€€€€€€…ÍÑ-¥¹¹=9%Q%=91}M9-}Q=-9L°(€€€€€€€€€€€…ÍÑ-¥¹¹Q=A}IQUI}M1Q%=8°(€€€€€€€€€€€…ÍÑ-¥¹¹QIQ}1%	IIe}IQUI9}9}Q=-8°(€€€€€€€ôè(€€€€€€€€€€€Í•±˜¹¡•­}ÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¹Ì ¤(€€€€€€€€€€€Í•±˜¹}ÁÕÑ}Á•¹‘¥¹}ÑÉ¥•ÉÍ}½¹}ÍÑ…¬ ¤(€€€€€€€€€€€Í•±˜¹}‘É…¥¹}ÑÉ¥•É•‘}…‰¥±¥Ñ¥•Ì ¤(€€€€€€€É•ÑÕÉ¸É•Í½±Ù•‘}…É((€€€ÍÑ…Ñ¥µ•Ñ¡½(€€€‘•˜}‘•™…Õ±Ñ}Ñ½Á}É•…ÑÕÉ•}Í•±•Ñ¥½¹}¡½¥”¡Ù¥•Ü°½ÁÑ¥½¹Ì¤è(€€€€€€€€ˆˆ‰AÉ•™•ÈÕÍ•™Õ°‰½…ÉÙ…±Õ”ÕÍ¥¹œ½¹±äÑ¡”¥¹ÍÁ•Ñ•ÁÉ¥Ù…Ñ”…É‘•ÍÉ¥ÁÑ¥½¹Ì¸ˆˆˆ(€€€€€€€™…ÑÌ€ôí…É¹½‰©•Ñ}¥è…É™½È…É¥¸Ù¥•Ü¹…É‘Íô(€€€€€€€É•ÑÕÉ¸µ…à (€€€€€€€€€€€½ÁÑ¥½¹Ì°(€€€€€€€€€€€­•äõ±…µ‰‘„½ÁÑ¥½¸è€ (€€€€€€€€€€€€€€€ÍÕ´¡™…ÑÍm½‰©•Ñ}¥‘t¹µ…¹…}Ù…±Õ”™½È½‰©•Ñ}¥¥¸½ÁÑ¥½¸¹…É‘}¥‘Ì¤°(€€€€€€€€€€€€€€€±•¸¡½ÁÑ¥½¸¹…É‘}¥‘Ì¤°(€€€€€€€€€€€€€€€ÍÕ´ ¡™…ÑÍm½‰©•Ñ}¥‘t¹Á½Ý•È½È€À¤™½È½‰©•Ñ}¥¥¸½ÁÑ¥½¸¹…É‘}¥‘Ì¤°(€€€€€€€€€€€€¤°(€€€€€€€€¤((€€€‘•˜É•Í½±Ù•}Ñ½Á}É•…ÑÕÉ•}Í•±•Ñ¥½¸¡Í•±˜°Á±…å•É}¥¹‘•à°ÁÉ½É…´°€¨°Í½ÕÉ•}¥èÍÑÈ¤€´ø9½¹”è(€€€€€€€€ˆˆ‰¡½½Í”ÕÀÑ¼8É•…ÑÕÉ•ÌÁÉ¥Ù…Ñ•±ä°•¹Ñ•È…Ì„‰…Ñ °Ñ¡•¸É…¹‘½µ¥é”Ñ¡”É•ÍÐ¸ˆˆˆ(€€€€€€€Á±…å•È€ôÍ•±˜¹Á±…å•ÉÍmÁ±…å•É}¥¹‘•át(€€€€€€€±¥‰É…Éä€ôÁ±…å•È¹±¥‰É…Éä(€€€€€€€¥¹ÍÁ•Ñ•€ôÑÕÁ±”¡É•Ù•ÉÍ•¡±¥‰É…ÉålµÁÉ½É…´¹½Õ¹Ð€ét¤¤(€€€€€€€•±¥¥‰±”€ôÑÕÁ±”¡…É™½È…É¥¸¥¹ÍÁ•Ñ•¥˜…É¹…É¹¥Í}É•…ÑÕÉ”¤(€€€€€€€¡½¥•Ì€ô€¡Q½ÁÉ•…ÑÕÉ•M•±•Ñ¥½¹=ÁÑ¥½¸  ¤¤°¤€¬ÑÕÁ±” (€€€€€€€€€€€Q½ÁÉ•…ÑÕÉ•M•±•Ñ¥½¹=ÁÑ¥½¸¡ÑÕÁ±”¡…É¹½‰©•Ñ}¥™½È…É¥¸É½ÕÀ¤¤(€€€€€€€€€€€™½ÈÅÕ…¹Ñ¥Ñä¥¸É…¹” Ä°µ¥¸¡ÁÉ½É…´¹µ…á¥µÕµ}É•…ÑÕÉ•Ì°±•¸¡•±¥¥‰±”¤¤€¬€Ä¤(€€€€€€€€€€€™½ÈÉ½ÕÀ¥¸½µ‰¥¹…Ñ¥½¹Ì¡•±¥¥‰±”°ÅÕ…¹Ñ¥Ñä¤(€€€€€€€€€€€¥˜ÍÕ´¡…É¹µ…¹…}Ù…±Õ”™½È…É¥¸É½ÕÀ¤€ðôÁÉ½É…´¹µ…á¥µÕµ}Ñ½Ñ…±}µ…¹…}Ù…±Õ”(€€€€€€€€¤(€€€€€€€Ù¥•Ü€ôQ½ÁÉ•…ÑÕÉ•M•±•Ñ¥½¹Y¥•ÝXÈ (€€€€€€€€€€€Á±…å•É}¥¹‘•à°(€€€€€€€€€€€ÑÕÁ±”¡‘•ÍÉ¥‰•}…É¡…É¹½‰©•Ñ}¥°…É¹…É¤™½È…É¥¸¥¹ÍÁ•Ñ•¤°(€€€€€€€€€€€ÁÉ½É…´¹µ…á¥µÕµ}É•…ÑÕÉ•Ì°(€€€€€€€€€€€ÁÉ½É…´¹µ…á¥µÕµ}Ñ½Ñ…±}µ…¹…}Ù…±Õ”°(€€€€€€€€€€€‘•¥Í¥½¹}½¹Ñ•áÐ¡Í•±˜°Á±…å•É}¥¹‘•à¤°(€€€€€€€€¤(€€€€€€€é½¹•Ì€ôÍ•±˜¹}…±±}é½¹•}±¥ÍÑÌ ¤(€€€€€€€‰•™½É•}é½¹•Ì€ôÑÕÁ±”¡ÑÕÁ±”¡é½¹”¤™½Èé½¹”¥¸é½¹•Ì¤(€€€€€€€É¹}‰•™½É”€ôÍ•±˜¹É¹œ¹ÍÑ…Ñ•}‘¥•ÍÐ(€€€€€€€Í•±˜¹}Ñ½Á}É•…ÑÕÉ•}Í•±•Ñ¥½¹}¡½¥•}…Ñ¥Ù”€ôQÉÕ”(€€€€€€€ÑÉäè(€€€€€€€€€€€¡½¥”€ôÍ•±˜¹Ñ½Á}É•…ÑÕÉ•}Í•±•Ñ¥½¹}¡½½Í•È¡Ù¥•Ü°¡½¥•Ì¤(€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡¡½¥”°Q½ÁÉ•…ÑÕÉ•M•±•Ñ¥½¹=ÁÑ¥½¸¤½È¡½¥”¹½Ð¥¸¡½¥•Ìè(€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰Ñ½ÀµÉ•…ÑÕÉ”¡½½Í•ÈµÕÍÐÉ•ÑÕÉ¸½¹”±•…°½µ‰¥¹•µÙ…±Õ”¡½¥”ˆ¤(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€…¹ä¡ÑÕÁ±”¡é½¹”¤€„ô‰•™½É”™½Èé½¹”°‰•™½É”¥¸é¥À¡é½¹•Ì°‰•™½É•}é½¹•Ì°ÍÑÉ¥ÐõQÉÕ”¤¤(€€€€€€€€€€€€€€€½ÈÍ•±˜¹É¹œ¹ÍÑ…Ñ•}‘¥•ÍÐ€„ôÉ¹}‰•™½É”(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰Ñ½ÀµÉ•…ÑÕÉ”¡½½Í•ÈµÕÑ…Ñ•…ÕÑ¡½É¥Ñ…Ñ¥Ù”ÍÑ…Ñ”ˆ¤(€€€€€€€™¥¹…±±äè(€€€€€€€€€€€Í•±˜¹}Ñ½Á}É•…ÑÕÉ•}Í•±•Ñ¥½¹}¡½¥•}…Ñ¥Ù”€ô…±Í”((€€€€€€€Í•±•Ñ•€ôÑÕÁ±” (€€€€€€€€€€€¹•áÐ¡…É™½È…É¥¸¥¹ÍÁ•Ñ•¥˜…É¹½‰©•Ñ}¥€ôô½‰©•Ñ}¥¤(€€€€€€€€€€€™½È½‰©•Ñ}¥¥¸¡½¥”¹…É‘}¥‘Ì(€€€€€€€€¤(€€€€€€€É•µ…¥¹‘•È€ôm…É™½È…É¥¸¥¹ÍÁ•Ñ•¥˜…É¹½Ð¥¸Í•±•Ñ•‘t(€€€€€€€‰½ÑÑ½´€ôÍ•±˜¹É¹œ¹Í¡Õ™™±•¡É•µ…¥¹‘•È°‘½µ…¥¸õ˜‰Ñ½Á}É•…ÑÕÉ•}Í•±•Ñ¥½¹}‰½ÑÑ½´éíÍ½ÕÉ•}¥‘ôˆ¤(€€€€€€€±¥‰É…Éålét€ô‰½ÑÑ½´€¬m…É™½È…É¥¸±¥‰É…Éä¥˜…É¹½Ð¥¸¥¹ÍÁ•Ñ•‘t(€€€€€€€•¹Ñ•É•€ômt(€€€€€€€™½È…É¥¸Í•±•Ñ•è(€€€€€€€€€€€€ŒQ¡”Í•±•Ñ•…É‘Ì¡…Ù”…±É•…‘ä‰••¸É•µ½Ù•™É½´Ñ¡”±¥‰É…Éä½É‘•É¥¹œì(€€€€€€€€€€€€ŒÉ•Ñ…¥¸Ñ¡•¥È…ÕÑ¡½É¥Ñ…Ñ¥Ù”Í½ÕÉ”é½¹”Õ¹Ñ¥°•… é½¹”ÑÉ…¹Í¥Ñ¥½¸¸(€€€€€€€€€€€±¥‰É…Éä¹…ÁÁ•¹¡…É¤(€€€€€€€€€€€Á•Éµ…¹•¹Ð€ôÍ•±˜¹µ½Ù•}½‰©•Ð (€€€€€€€€€€€€€€€…É°€‰‰…ÑÑ±•™¥•±ˆ°½¹ÑÉ½±±•ÈõÁ±…å•É}¥¹‘•à°É•…Í½¸ô‰Ñ½Á}É•…ÑÕÉ•}Í•±•Ñ¥½¹}•¹ÑÉäˆ(€€€€€€€€€€€€¤(€€€€€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡Á•Éµ…¹•¹Ð°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€•¹Ñ•É•¹…ÁÁ•¹ ¡…É¹½‰©•Ñ}¥°Á•Éµ…¹•¹Ð¤¤(€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€‰Ñ½Á}É•…ÑÕÉ•}Í•±•Ñ¥½¹}É•Í½±Ù•ˆ°(€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍ½ÕÉ•}¥°(€€€€€€€€€€€½¹ÑÉ½±±•ÈõÁ±…å•É}¥¹‘•à°(€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÁÉ½É…´¹•™™•Ñ}™É…µ•¹Ð°(€€€€€€€€€€€¥¹ÍÁ•Ñ•‘}¥‘Ìõm…É¹½‰©•Ñ}¥™½È…É¥¸¥¹ÍÁ•Ñ•‘t°(€€€€€€€€€€€Í•±•Ñ•õmì‰±¥‰É…Éå}¥ˆè½±°€‰‰…ÑÑ±•™¥•±‘}¥ˆè¹•Ü¹½‰©•Ñ}¥‘ô™½È½±°¹•Ü¥¸•¹Ñ•É•‘t°(€€€€€€€€€€€‰½ÑÑ½µ}¥‘Ìõm…É¹½‰©•Ñ}¥™½È…É¥¸‰½ÑÑ½µt°(€€€€€€€€€€€µ…á¥µÕµ}É•…ÑÕÉ•ÌõÁÉ½É…´¹µ…á¥µÕµ}É•…ÑÕÉ•Ì°(€€€€€€€€€€€µ…á¥µÕµ}Ñ½Ñ…±}µ…¹…}Ù…±Õ”õÁÉ½É…´¹µ…á¥µÕµ}Ñ½Ñ…±}µ…¹…}Ù…±Õ”°(€€€€€€€€¤(€€€€€€€Í•±˜¹É•™É•Í¡}ÍÑ…Ñ¥}ÁÑ}µ½‘¥™¥•ÉÌ ¤(€€€€€€€Í•±˜¹}ÁÉ½•ÍÍ}É•…ÑÕÉ•Í}•¹Ñ•É•‘}ÑÉ¥•ÉÌ (€€€€€€€€€€€ÑÕÁ±”¡¹•Ü™½È|°¹•Ü¥¸•¹Ñ•É•¤°Í½ÕÉ•}¥õÍ½ÕÉ•}¥°‘•™•É}ÑÉ¥•ÉÌõQÉÕ”(€€€€€€€€¤((€€€‘•˜É•Í½±Ù•}Ñ½Á}…É‘}Í•±•Ñ¥½¸¡Í•±˜°Á±…å•É}¥¹‘•à°ÁÉ½É…´°€¨°Í½ÕÉ•}¥èÍÑÈ¤€´ø9½¹”è(€€€€€€€€ˆˆ‰¡½½Í”ÁÉ¥Ù…Ñ•±ä™É½´Ñ¡”¥¹ÍÁ•Ñ•Ñ½À…É‘Ì°Ñ¡•¸É…¹‘½µ¥é”½¹±äÑ¡”É•µ…¥¹‘•È¸ˆˆˆ(€€€€€€€Á±…å•È€ôÍ•±˜¹Á±…å•ÉÍmÁ±…å•É}¥¹‘•át(€€€€€€€±¥‰É…Éä€ôÁ±…å•È¹±¥‰É…Éä(€€€€€€€¥¹ÍÁ•Ñ•€ôÑÕÁ±”¡É•Ù•ÉÍ•¡±¥‰É…ÉålµÁÉ½É…´¹½Õ¹Ð€ét¤¤(€€€€€€€•±¥¥‰±”€ôÑÕÁ±” (€€€€€€€€€€€…É(€€€€€€€€€€€™½È…É¥¸¥¹ÍÁ•Ñ•(€€€€€€€€€€€¥˜€¡ÁÉ½É…´¹¥¹±Õ‘•}±…¹…¹…É¹¥Í}±…¹¤(€€€€€€€€€€€½È‰½½°¡Í•Ð¡…É¹ÑåÁ•}±¥¹”¹Á…ÉÑ¥Ñ¥½¸ ˆƒŠP€ˆ¥lÉt¹ÍÁ±¥Ð ¤¤€˜Í•Ð¡ÁÉ½É…´¹ÍÕ‰ÑåÁ•Ì¤¤(€€€€€€€€¤(€€€€€€€½ÁÑ¥½¹Ì€ô€¡Q½Á…É‘M•±•Ñ¥½¹=ÁÑ¥½¸¡9½¹”¤°¤€¬ÑÕÁ±” (€€€€€€€€€€€Q½Á…É‘M•±•Ñ¥½¹=ÁÑ¥½¸¡…É¹½‰©•Ñ}¥¤™½È…É¥¸•±¥¥‰±”(€€€€€€€€¤(€€€€€€€Ù¥•Ü€ôQ½Á…É‘M•±•Ñ¥½¹Y¥•ÝXÈ (€€€€€€€€€€€Á±…å•É}¥¹‘•à°(€€€€€€€€€€€ÑÕÁ±”¡‘•ÍÉ¥‰•}…É¡…É¹½‰©•Ñ}¥°…É¹…É¤™½È…É¥¸¥¹ÍÁ•Ñ•¤°(€€€€€€€€€€€‘•¥Í¥½¹}½¹Ñ•áÐ¡Í•±˜°Á±…å•É}¥¹‘•à¤°(€€€€€€€€¤(€€€€€€€‰•™½É•}±¥‰É…Éä€ôÑÕÁ±”¡±¥‰É…Éä¤(€€€€€€€‰•™½É•}¡…¹€ôÑÕÁ±”¡Á±…å•È¹¡…¹¤(€€€€€€€ÑÉäè(€€€€€€€€€€€¡½¥”€ôÍ•±˜¹Ñ½Á}…É‘}¡½½Í•È¡Ù¥•Ü°½ÁÑ¥½¹Ì¤(€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡¡½¥”°Q½Á…É‘M•±•Ñ¥½¹=ÁÑ¥½¸¤½È¡½¥”¹½Ð¥¸½ÁÑ¥½¹Ìè(€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰Ñ½À…É¡½½Í•ÈµÕÍÐÉ•ÑÕÉ¸½¹”•±¥¥‰±”½ÁÑ¥½¸ˆ¤(€€€€€€€€€€€¥˜ÑÕÁ±”¡±¥‰É…Éä¤€„ô‰•™½É•}±¥‰É…Éä½ÈÑÕÁ±”¡Á±…å•È¹¡…¹¤€„ô‰•™½É•}¡…¹è(€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰Ñ½À…É¡½½Í•ÈµÕÑ…Ñ•…ÕÑ¡½É¥Ñ…Ñ¥Ù”é½¹•Ìˆ¤(€€€€€€€•á•ÁÐá•ÁÑ¥½¸è(€€€€€€€€€€€±¥‰É…Éålét€ô‰•™½É•}±¥‰É…Éä(€€€€€€€€€€€Á±…å•È¹¡…¹‘lét€ô‰•™½É•}¡…¹(€€€€€€€€€€€É…¥Í”(€€€€€€€Í•±•Ñ•€ô¹•áÐ ¡…É™½È…É¥¸•±¥¥‰±”¥˜…É¹½‰©•Ñ}¥€ôô¡½¥”¹…É‘}¥¤°9½¹”¤(€€€€€€€¥˜Í•±•Ñ•¥Ì¹½Ð9½¹”è(€€€€€€€€€€€É•Ù•…±•‘}¥€ôÍ•±•Ñ•¹½‰©•Ñ}¥(€€€€€€€€€€€Í•±˜¹µ½Ù•}½‰©•Ð¡Í•±•Ñ•°€‰¡…¹ˆ°É•…Í½¸ô‰Ñ½Á}…É‘}É•Ù•…±•‘}Ñ½}¡…¹ˆ¤(€€€€€€€•±Í”è(€€€€€€€€€€€É•Ù•…±•‘}¥€ô9½¹”(€€€€€€€É•µ…¥¹‘•È€ôm…É™½È…É¥¸¥¹ÍÁ•Ñ•¥˜…É¥Ì¹½ÐÍ•±•Ñ•‘t(€€€€€€€É…¹‘½µ¥é•€ôÍ•±˜¹É¹œ¹Í¡Õ™™±•¡É•µ…¥¹‘•È°‘½µ…¥¸ô‰Ñ½Á}…É‘}Í•±•Ñ¥½¹}‰½ÑÑ½´ˆ¤(€€€€€€€¥¹ÍÁ•Ñ•‘}¥‘•¹Ñ¥Ñ¥•Ì€ôí¥¡…É¤™½È…É¥¸É•µ…¥¹‘•Éô(€€€€€€€±¥‰É…Éålét€ôÉ…¹‘½µ¥é•€¬m…É™½È…É¥¸±¥‰É…Éä¥˜¥¡…É¤¹½Ð¥¸¥¹ÍÁ•Ñ•‘}¥‘•¹Ñ¥Ñ¥•Ít(€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€‰Ñ½Á}…É‘}Í•±•Ñ¥½¹}É•Í½±Ù•ˆ°(€€€€€€€€€€€Í½ÕÉ•}¥õÍ½ÕÉ•}¥°(€€€€€€€€€€€Á±…å•ÈõÁ±…å•È¹¹…µ”°(€€€€€€€€€€€¥¹ÍÁ•Ñ•‘}¥‘Ìõm…É¹½‰©•Ñ}¥™½È…É¥¸¥¹ÍÁ•Ñ•‘t°(€€€€€€€€€€€É•Ù•…±•‘}¥õÉ•Ù•…±•‘}¥°(€€€€€€€€€€€‰½ÑÑ½µ}¥‘Ìõm…É¹½‰©•Ñ}¥™½È…É¥¸É…¹‘½µ¥é•‘t°(€€€€€€€€€€€¡…¹‘}¥õÁ±…å•È¹¡…¹‘l´Åt¹½‰©•Ñ}¥¥˜Í•±•Ñ•¥Ì¹½Ð9½¹”•±Í”9½¹”°(€€€€€€€€¤((€€€ÍÑ…Ñ¥µ•Ñ¡½(€€€‘•˜}‘•™…Õ±Ñ}±¥‰É…Éå}Í•…É¡}¡½¥”¡Ù¥•Ü°½ÁÑ¥½¹Ì¤è(€€€€€€€€ˆˆ‰¡½½Í”„¹••‘•±…¹½È„¹•…ÈµÑ•É´…ÍÑ…‰±”ÍÁ•±°™É½´ÁÉ¥Ù…Ñ”…É™…ÑÌ¸ˆˆˆ(€€€€€€€½Ý¸€ôÙ¥•Ü¹½¹Ñ•áÐ¹‰…ÑÑ±•™¥•±‘ÍmÙ¥•Ü¹Á±…å•É}¥¹‘•át(€€€€€€€±…¹‘Ì€ôÍÕ´ ‰1…¹ˆ¥¸¥Ñ•´¹…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤™½È¥Ñ•´¥¸½Ý¸¤(€€€€€€€±…¹‘}¥¹}¡…¹€ô…¹ä (€€€€€€€€€€€€‰1…¹ˆ¥¸…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤™½È…É¥¸Ù¥•Ü¹½¹Ñ•áÐ¹½Ý¹}¡…¹(€€€€€€€€¤(€€€€€€€™…ÑÌ€ôí…É¹½‰©•Ñ}¥è…É™½È…É¥¸Ù¥•Ü¹…É‘Íô((€€€€€€€‘•˜Í½É”¡½ÁÑ¥½¸¤è(€€€€€€€€€€€…É€ô™…ÑÍm½ÁÑ¥½¸¹…É‘}¥‘t(€€€€€€€€€€€±…¹€ô€‰1…¹ˆ¥¸…É¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤(€€€€€€€€€€€¥˜±…¹…¹±…¹‘Ì€ð€Ð…¹¹½Ð±…¹‘}¥¹}¡…¹è(€€€€€€€€€€€€€€€É•ÑÕÉ¸€ Ì°€À°…É¹½‰©•Ñ}¥¤(€€€€€€€€€€€¥˜¹½Ð±…¹…¹…É¹µ…¹…}Ù…±Õ”€ðô±…¹‘Ì€¬€Äè(€€€€€€€€€€€€€€€É•ÑÕÉ¸€ È°…É¹µ…¹…}Ù…±Õ”°…É¹½‰©•Ñ}¥¤(€€€€€€€€€€€¥˜¹½Ð±…¹è(€€€€€€€€€€€€€€€É•ÑÕÉ¸€ Ä°€µ…É¹µ…¹…}Ù…±Õ”°…É¹½‰©•Ñ}¥¤(€€€€€€€€€€€É•ÑÕÉ¸€ À°€À°…É¹½‰©•Ñ}¥¤((€€€€€€€É•ÑÕÉ¸µ…à¡½ÁÑ¥½¹Ì°­•äõÍ½É”¤((€€€‘•˜É•Í½±Ù•}½ÁÑ¥½¹…±}¡…¹‘}É•Í•Ð (€€€€€€€Í•±˜°ÅÕ…¹Ñ¥Ñäè¥¹Ð°½É…±•}™É…µ•¹ÐèÍÑÈ°€¨°Í½ÕÉ•}¥èÍÑÈ(€€€€¤€´ø9½¹”è(€€€€€€€€ˆˆ‰½±±•ÐA9@¡½¥•Ì°Ñ¡•¸‘¥Í…É¡½Í•¸¡…¹‘Ì‰•™½É”…¹äÁ±…å•È‘É…ÝÌ¸ˆˆˆ(€€€€€€€½É‘•È€ô€¡Í•±˜¹…Ñ¥Ù•}Á±…å•È°€Ä€´Í•±˜¹…Ñ¥Ù•}Á±…å•È¤(€€€€€€€¡½¥•Ìè‘¥Ñm¥¹Ð°‰½½±t€ôíô(€€€€€€€Í¹…ÁÍ¡½ÑÌ€ôÑÕÁ±”¡ÑÕÁ±”¡é½¹”¤™½Èé½¹”¥¸Í•±˜¹}…±±}é½¹•}±¥ÍÑÌ ¤¤(€€€€€€€™½È¥¹‘•à¥¸½É‘•Èè(€€€€€€€€€€€Á±…å•È€ôÍ•±˜¹Á±…å•ÉÍm¥¹‘•át(€€€€€€€€€€€¡…¹€ôÑÕÁ±”¡Á±…å•È¹¡…¹¤(€€€€€€€€€€€Í•±˜¹}¡…¹‘}É•Í•Ñ}¡½¥•}…Ñ¥Ù”€ôQÉÕ”(€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€‘•¥Í¥½¸€ôÍ•±˜¹¡…¹‘}É•Í•Ñ}¡½½Í•È (€€€€€€€€€€€€€€€€€€€¥¹‘•à°(€€€€€€€€€€€€€€€€€€€ÑÕÁ±”¡‘•ÍÉ¥‰•}…É¡…É¹½‰©•Ñ}¥°…É¹…É¤™½È…É¥¸¡…¹¤°(€€€€€€€€€€€€€€€€€€€‘•¥Í¥½¹}½¹Ñ•áÐ¡Í•±˜°¥¹‘•à¤°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€¥˜ÑåÁ”¡‘•¥Í¥½¸¤¥Ì¹½Ð‰½½°è(€€€€€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰¡…¹É•Í•Ð¡½¥”µÕÍÐ‰”„‰½½±•…¸ˆ¤(€€€€€€€€€€€€€€€¥˜…¹ä (€€€€€€€€€€€€€€€€€€€ÑÕÁ±”¡é½¹”¤€„ô‰•™½É”(€€€€€€€€€€€€€€€€€€€™½Èé½¹”°‰•™½É”¥¸é¥À¡Í•±˜¹}…±±}é½¹•}±¥ÍÑÌ ¤°Í¹…ÁÍ¡½ÑÌ°ÍÑÉ¥ÐõQÉÕ”¤(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰¡…¹É•Í•Ð¡½½Í•ÈµÕÑ…Ñ•…ÕÑ¡½É¥Ñ…Ñ¥Ù”é½¹•Ìˆ¤(€€€€€€€€€€€•á•ÁÐá•ÁÑ¥½¸è(€€€€€€€€€€€€€€€™½Èé½¹”°‰•™½É”¥¸é¥À¡Í•±˜¹}…±±}é½¹•}±¥ÍÑÌ ¤°Í¹…ÁÍ¡½ÑÌ°ÍÑÉ¥ÐõQÉÕ”¤è(€€€€€€€€€€€€€€€€€€€é½¹•lét€ô‰•™½É”(€€€€€€€€€€€€€€€É…¥Í”(€€€€€€€€€€€™¥¹…±±äè(€€€€€€€€€€€€€€€Í•±˜¹}¡…¹‘}É•Í•Ñ}¡½¥•}…Ñ¥Ù”€ô…±Í”(€€€€€€€€€€€¡½¥•Ím¥¹‘•át€ô‘•¥Í¥½¸(€€€€€€€‘¥Í…É‘•è‘¥Ñm¥¹Ð°±¥ÍÑmÑÕÁ±•mÍÑÈ°ÍÑÉuut€ôí¥¹‘•àèmt™½È¥¹‘•à¥¸½É‘•Éô(€€€€€€€™½È¥¹‘•à¥¸½É‘•Èè(€€€€€€€€€€€¥˜¡½¥•Ím¥¹‘•átè(€€€€€€€€€€€€€€€™½È…É¥¸ÑÕÁ±”¡Í•±˜¹Á±…å•ÉÍm¥¹‘•át¹¡…¹¤è(€€€€€€€€€€€€€€€€€€€µ½Ù•€ôÍ•±˜¹µ½Ù•}½‰©•Ð (€€€€€€€€€€€€€€€€€€€€€€€…É°€‰É…Ù•å…Éˆ°É•…Í½¸ô‰½ÁÑ¥½¹…±}¡…¹‘}É•Í•Ñ}‘¥Í…Éˆ(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€‘¥Í…É‘•‘m¥¹‘•át¹…ÁÁ•¹ ¡…É¹½‰©•Ñ}¥°µ½Ù•¹½‰©•Ñ}¥¤¤(€€€€€€€‘É…Ý¸è‘¥Ñm¥¹Ð°±¥ÍÑmÍÑÉut€ôí¥¹‘•àèmt™½È¥¹‘•à¥¸½É‘•Éô(€€€€€€€ÍÕ••‘•è‘¥Ñm¥¹Ð°‰½½±t€ôíô(€€€€€€€™½È¥¹‘•à¥¸½É‘•Èè(€€€€€€€€€€€¥˜¡½¥•Ím¥¹‘•átè(€€€€€€€€€€€€€€€Á±…å•È€ôÍ•±˜¹Á±…å•ÉÍm¥¹‘•át(€€€€€€€€€€€€€€€‰•™½É”€ô±•¸¡Á±…å•È¹¡…¹¤(€€€€€€€€€€€€€€€ÍÕ••‘•‘m¥¹‘•át€ôÍ•±˜¹‘É…Ü¡Á±…å•È°ÅÕ…¹Ñ¥Ñä¤(€€€€€€€€€€€€€€€‘É…Ý¹m¥¹‘•át€ôm…É¹½‰©•Ñ}¥™½È…É¥¸Á±…å•È¹¡…¹‘m‰•™½É”éut(€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€‰½ÁÑ¥½¹…±}¡…¹‘}É•Í•Ñ}É•Í½±Ù•ˆ°(€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍ½ÕÉ•}¥°(€€€€€€€€€€€½É…±•}™É…µ•¹Ðõ½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€…Á¹…Á}½É‘•Èõ±¥ÍÐ¡½É‘•È¤°(€€€€€€€€€€€¡½¥•Ìõmì‰Á±…å•Èˆè¥¹‘•à°€‰‘¥Í…É‘}…¹‘}‘É…Üˆè¡½¥•Ím¥¹‘•áuô™½È¥¹‘•à¥¸½É‘•Ét°(€€€€€€€€€€€‘¥Í…É‘•õmì‰Á±…å•Èˆè¥¹‘•à°€‰é½¹•}¥‘Ìˆè‘¥Í…É‘•‘m¥¹‘•áuô™½È¥¹‘•à¥¸½É‘•Ét°(€€€€€€€€€€€‘É…Ý¸õmì‰Á±…å•Èˆè¥¹‘•à°€‰¡…¹‘}¥‘Ìˆè‘É…Ý¹m¥¹‘•áuô™½È¥¹‘•à¥¸½É‘•Ét°(€€€€€€€€€€€‘É…Ý}ÅÕ…¹Ñ¥ÑäõÅÕ…¹Ñ¥Ñä°(€€€€€€€€€€€‘É…Ý}ÍÕ••‘•õmì‰Á±…å•Èˆè¥¹‘•à°€‰ÍÕ•ÍÌˆèÍÕ••‘•¹•Ð¡¥¹‘•à¥ô™½È¥¹‘•à¥¸½É‘•Ét°(€€€€€€€€¤((€€€‘•˜É•Í½±Ù•}±¥‰É…Éå}Í•…É¡}Ñ½}¡…¹ (€€€€€€€Í•±˜°Á±…å•É}¥¹‘•àè¥¹Ð°½É…±•}™É…µ•¹ÐèÍÑÈ°€¨°Í½ÕÉ•}¥èÍÑÈ(€€€€¤€´ø9½¹”è(€€€€€€€€ˆˆ‰¥Ù”Ñ¡”Í•…É¡¥¹œÁ±…å•È„ÁÉ¥Ù…Ñ”±•…°¡½¥”°µ½Ù”¥Ð°Ñ¡•¸Í¡Õ™™±”¸ˆˆˆ(€€€€€€€Á±…å•È€ôÍ•±˜¹Á±…å•ÉÍmÁ±…å•É}¥¹‘•át(€€€€€€€‰•™½É•}±¥‰É…Éä€ôÑÕÁ±”¡Á±…å•È¹±¥‰É…Éä¤(€€€€€€€‰•™½É•}¡…¹€ôÑÕÁ±”¡Á±…å•È¹¡…¹¤(€€€€€€€Í•±•Ñ•€ô9½¹”(€€€€€€€¥˜‰•™½É•}±¥‰É…Éäè(€€€€€€€€€€€½ÁÑ¥½¹Ì€ôÑÕÁ±”¡Q½Á…É‘M•±•Ñ¥½¹=ÁÑ¥½¸¡…É¹½‰©•Ñ}¥¤™½È…É¥¸‰•™½É•}±¥‰É…Éä¤(€€€€€€€€€€€Ù¥•Ü€ôQ½Á…É‘M•±•Ñ¥½¹Y¥•ÝXÈ (€€€€€€€€€€€€€€€Á±…å•É}¥¹‘•à°(€€€€€€€€€€€€€€€ÑÕÁ±”¡‘•ÍÉ¥‰•}…É¡…É¹½‰©•Ñ}¥°…É¹…É¤™½È…É¥¸‰•™½É•}±¥‰É…Éä¤°(€€€€€€€€€€€€€€€‘•¥Í¥½¹}½¹Ñ•áÐ¡Í•±˜°Á±…å•É}¥¹‘•à¤°(€€€€€€€€€€€€¤(€€€€€€€€€€€Í•±˜¹}±¥‰É…Éå}Í•…É¡}¡½¥•}…Ñ¥Ù”€ôQÉÕ”(€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€¡½¥”€ôÍ•±˜¹±¥‰É…Éå}Í•…É¡}¡½½Í•È¡Ù¥•Ü°½ÁÑ¥½¹Ì¤(€€€€€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡¡½¥”°Q½Á…É‘M•±•Ñ¥½¹=ÁÑ¥½¸¤½È¡½¥”¹½Ð¥¸½ÁÑ¥½¹Ìè(€€€€€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰±¥‰É…ÉäÍ•…É µÕÍÐÍ•±•Ð½¹”½™™•É•…Éˆ¤(€€€€€€€€€€€€€€€¥˜ÑÕÁ±”¡Á±…å•È¹±¥‰É…Éä¤€„ô‰•™½É•}±¥‰É…Éä½ÈÑÕÁ±”¡Á±…å•È¹¡…¹¤€„ô‰•™½É•}¡…¹è(€€€€€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰±¥‰É…ÉäÍ•…É ¡½½Í•ÈµÕÑ…Ñ•…ÕÑ¡½É¥Ñ…Ñ¥Ù”é½¹•Ìˆ¤(€€€€€€€€€€€•á•ÁÐá•ÁÑ¥½¸è(€€€€€€€€€€€€€€€Á±…å•È¹±¥‰É…Éålét€ô‰•™½É•}±¥‰É…Éä(€€€€€€€€€€€€€€€Á±…å•È¹¡…¹‘lét€ô‰•™½É•}¡…¹(€€€€€€€€€€€€€€€É…¥Í”(€€€€€€€€€€€™¥¹…±±äè(€€€€€€€€€€€€€€€Í•±˜¹}±¥‰É…Éå}Í•…É¡}¡½¥•}…Ñ¥Ù”€ô…±Í”(€€€€€€€€€€€Í•±•Ñ•€ô¹•áÐ¡…É™½È…É¥¸‰•™½É•}±¥‰É…Éä¥˜…É¹½‰©•Ñ}¥€ôô¡½¥”¹…É‘}¥¤(€€€€€€€µ½Ù•€ô€ (€€€€€€€€€€€Í•±˜¹µ½Ù•}½‰©•Ð¡Í•±•Ñ•°€‰¡…¹ˆ°É•…Í½¸ô‰±¥‰É…Éå}Í•…É¡}Ñ½}¡…¹ˆ¤(€€€€€€€€€€€¥˜Í•±•Ñ•¥Ì¹½Ð9½¹”(€€€€€€€€€€€•±Í”9½¹”(€€€€€€€€¤(€€€€€€€‘½µ…¥¸€ô˜‰±¥‰É…Éå}Í•…É éíÍ½ÕÉ•}¥‘ôˆ(€€€€€€€ÁÉ•}Í¡Õ™™±•}¥‘Ì€ôm…É¹½‰©•Ñ}¥™½È…É¥¸Á±…å•È¹±¥‰É…Éåt(€€€€€€€Á±…å•È¹±¥‰É…Éålét€ôÍ•±˜¹É¹œ¹Í¡Õ™™±•¡Á±…å•È¹±¥‰É…Éä°‘½µ…¥¸õ‘½µ…¥¸¤(€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€‰±¥‰É…Éå}Í•…É¡}Ñ½}¡…¹‘}É•Í½±Ù•ˆ°(€€€€€€€€€€€ÍÑ…­}½‰©•Ñ}¥õÍ½ÕÉ•}¥°(€€€€€€€€€€€½É…±•}™É…µ•¹Ðõ½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€Í•…É¡¥¹}Á±…å•ÈõÁ±…å•É}¥¹‘•à°(€€€€€€€€€€€Í•±•Ñ•‘}¥õ9½¹”¥˜Í•±•Ñ•¥Ì9½¹”•±Í”Í•±•Ñ•¹½‰©•Ñ}¥°(€€€€€€€€€€€¡…¹‘}¥õ9½¹”¥˜µ½Ù•¥Ì9½¹”•±Í”µ½Ù•¹½‰©•Ñ}¥°(€€€€€€€€€€€ÁÉ•}Í¡Õ™™±•}¥‘ÌõÁÉ•}Í¡Õ™™±•}¥‘Ì°(€€€€€€€€€€€Á½ÍÑ}Í¡Õ™™±•}¥‘Ìõm…É¹½‰©•Ñ}¥™½È…É¥¸Á±…å•È¹±¥‰É…Éåt°(€€€€€€€€€€€Í¡Õ™™±•}‘½µ…¥¸õ‘½µ…¥¸°(€€€€€€€€¤((€€€ÍÑ…Ñ¥µ•Ñ¡½(€€€‘•˜}¥Í}‘•ÍÑÉ½å}…ÉÑ¥™…Ñ}•¹¡…¹Ñµ•¹Ñ}½É}Á½Ý•É|Ñ}É•…ÑÕÉ•}Ñ…É•Ð (€€€€€€€Ñ…É•ÐèA•Éµ…¹•¹Ð°(€€€€¤€´ø‰½½°è(€€€€€€€€ˆˆ‰Ù…±Õ…Ñ”Ñ¡”‰½Õ¹‘•Ñ…É•ÐÁÉ•‘¥…Ñ”™É½´ÕÉÉ•¹Ð‰…ÑÑ±•™¥•±¡…É…Ñ•É¥ÍÑ¥Ì¸ˆˆˆ(€€€€€€€…É‘}ÑåÁ•Ì€ôÍ•Ð¡Ñ…É•Ð¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤¤(€€€€€€€É•ÑÕÉ¸€ (€€€€€€€€€€€€‰ÉÑ¥™…Ðˆ¥¸…É‘}ÑåÁ•Ì(€€€€€€€€€€€½È€‰¹¡…¹Ñµ•¹Ðˆ¥¸…É‘}ÑåÁ•Ì(€€€€€€€€€€€½È€ ‰É•…ÑÕÉ”ˆ¥¸…É‘}ÑåÁ•Ì…¹Ñ…É•Ð¹Á½Ý•È€øô€Ð¤(€€€€€€€€¤((€€€‘•˜}±•…±}½ÁÑ¥½¹…±}‘•ÍÑÉ½å}Ñ…É•Ð¡Í•±˜°Ñ…É•ÐèA•Éµ…¹•¹Ð°½¹ÑÉ½±±•Èè¥¹Ð¤€´ø‰½½°è(€€€€€€€¥˜¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Ñ…É•Ð°€‰‰…ÑÑ±•™¥•±ˆ¤è(€€€€€€€€€€€É•ÑÕÉ¸…±Í”(€€€€€€€…É‘}ÑåÁ•Ì€ôÍ•Ð¡Ñ…É•Ð¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤¤(€€€€€€€•±¥¥‰±”€ô€ (€€€€€€€€€€€€‰ÉÑ¥™…Ðˆ¥¸…É‘}ÑåÁ•Ì(€€€€€€€€€€€½È€‰¹¡…¹Ñµ•¹Ðˆ¥¸…É‘}ÑåÁ•Ì(€€€€€€€€€€€½È€¡Ñ…É•Ð¹¥Í}É•…ÑÕÉ”…¹Í•±˜¹}¡…Í}­•åÝ½É¡Ñ…É•Ð°€‰±å¥¹œˆ¤¤(€€€€€€€€¤(€€€€€€€¥˜¹½Ð•±¥¥‰±”è(€€€€€€€€€€€É•ÑÕÉ¸…±Í”(€€€€€€€É•ÑÕÉ¸Í•±˜¹}±•…±}Ñ…É•Ñ¥¹}ÁÉ½Ñ•Ñ¥½¸¡Ñ…É•Ð°½¹ÑÉ½±±•È¤((€€€‘•˜}±•…±}½¹‘¥Ñ¥½¹…±}‘•ÍÑÉ½å}Ñ…É•Ð¡Í•±˜°Ñ…É•ÐèA•Éµ…¹•¹Ð°½¹ÑÉ½±±•Èè¥¹Ð¤€´ø‰½½°è(€€€€€€€¥˜¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Ñ…É•Ð°€‰‰…ÑÑ±•™¥•±ˆ¤è(€€€€€€€€€€€É•ÑÕÉ¸…±Í”(€€€€€€€ÑåÁ•Ì€ôÍ•Ð¡Ñ…É•Ð¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤¤(€€€€€€€¥˜¹½ÐÑåÁ•Ì¹¥¹Ñ•ÉÍ•Ñ¥½¸¡ì‰ÉÑ¥™…Ðˆ°€‰É•…ÑÕÉ”‰ô¤è(€€€€€€€€€€€É•ÑÕÉ¸…±Í”(€€€€€€€É•ÑÕÉ¸Í•±˜¹}±•…±}Ñ…É•Ñ¥¹}ÁÉ½Ñ•Ñ¥½¸¡Ñ…É•Ð°½¹ÑÉ½±±•È¤((€€€‘•˜}±•…±}Ñ…É•Ñ•‘}É•µ½Ù…±}Ñ…É•Ð¡Í•±˜°Ñ…É•Ð°½¹ÑÉ½±±•Èè¥¹Ð°ÁÉ½É…´¤€´ø‰½½°è(€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡Ñ…É•Ð°A•Éµ…¹•¹Ð¤½È¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Ñ…É•Ð°€‰‰…ÑÑ±•™¥•±ˆ¤è(€€€€€€€€€€€É•ÑÕÉ¸…±Í”(€€€€€€€ÑåÁ•Ì€ôÍ•Ð¡Ñ…É•Ð¹ÑåÁ•}±¥¹”¹ÍÁ±¥Ð ˆƒŠP€ˆ°€Ä¥lÁt¹ÍÁ±¥Ð ¤¤(€€€€€€€É•ÑÕÉ¸€ (€€€€€€€€€€€‰½½°¡ÑåÁ•Ì¹¥¹Ñ•ÉÍ•Ñ¥½¸¡ÁÉ½É…´¹Ñ…É•Ñ}ÑåÁ•Ì¤¤(€€€€€€€€€€€…¹€ (€€€€€€€€€€€€€€€ÁÉ½É…´¹µ…á¥µÕµ}µ…¹…}Ù…±Õ”¥Ì9½¹”(€€€€€€€€€€€€€€€½ÈÑ…É•Ð¹…É¹µ…¹…}Ù…±Õ”€ðôÁÉ½É…´¹µ…á¥µÕµ}µ…¹…}Ù…±Õ”(€€€€€€€€€€€€¤(€€€€€€€€€€€…¹Í•±˜¹}±•…±}Ñ…É•Ñ¥¹}ÁÉ½Ñ•Ñ¥½¸¡Ñ…É•Ð°½¹ÑÉ½±±•È¤(€€€€€€€€¤((€€€‘•˜}±•…±}Ñ…É•Ñ¥¹}ÁÉ½Ñ•Ñ¥½¸¡Í•±˜°Ñ…É•ÐèA•Éµ…¹•¹Ð°½¹ÑÉ½±±•Èè¥¹Ð¤€´ø‰½½°è(€€€€€€€Ñ•áÐ€ô€ˆ€ˆ¹©½¥¸  ©Ñ…É•Ð¹ÉÕ±•Í}…É¹­•åÝ½É‘Ì°Ñ…É•Ð¹ÉÕ±•Í}…É¹½É…±•}Ñ•áÐ¤¤(€€€€€€€¥˜É”¹Í•…É ¡È‰q‰Í¡É½Õ‘q‰ñq‰Ý…É‘q‰ñq‰ÁÉ½Ñ•Ñ¥½¹q‰ñ…¸Ð‰”€ üéÑ¡”€¤ýÑ…É•Ðˆ°Ñ•áÐ°É”¹$¤è(€€€€€€€€€€€É•ÑÕÉ¸…±Í”(€€€€€€€É•ÑÕÉ¸¹½Ð€ (€€€€€€€€€€€Ñ…É•Ð¹½¹ÑÉ½±±•È€„ô½¹ÑÉ½±±•È(€€€€€€€€€€€…¹€¡Í•±˜¹}¡…Í}­•åÝ½É¡Ñ…É•Ð°€‰!•áÁÉ½½˜ˆ¤½ÈÉ”¹Í•…É ¡È‰q‰¡•áÁÉ½½™qˆˆ°Ñ•áÐ°É”¹$¤¤(€€€€€€€€¤((€€€‘•˜±•…±}…ÑÑ…­•ÉÌ¡Í•±˜°Á±…å•É}¥¹‘•àè¥¹Ð¤€´ø±¥ÍÑmA•Éµ…¹•¹Ñtè(€€€€€€€É•ÑÕÉ¸l(€€€€€€€€€€€À(€€€€€€€€€€€™½ÈÀ¥¸Í•±˜¹Á±…å•ÉÍmÁ±…å•É}¥¹‘•át¹‰…ÑÑ±•™¥•±(€€€€€€€€€€€¥˜À¹¥Í}É•…ÑÕÉ”(€€€€€€€€€€€…¹¹½ÐÀ¹Ñ…ÁÁ•(€€€€€€€€€€€…¹€ (€€€€€€€€€€€€€€€¹½ÐÀ¹ÍÕµµ½¹¥¹}Í¥¬(€€€€€€€€€€€€€€€½ÈÍ•±˜¹}¡…Í}­•åÝ½É¡À°€‰!…ÍÑ”ˆ¤(€€€€€€€€€€€€€€€½ÈÍ•±˜¹¡…Í}Ñ•µÁ½É…Éå}­•åÝ½É¡À°Q•µÁ½É…Éå-•åÝ½É¹!MQ¤(€€€€€€€€€€€€¤(€€€€€€€€€€€…¹Í•±˜¹…ÑÑ…­¥¹}É•ÍÑÉ¥Ñ¥½¸¡À¤¥Ì9½¹”(€€€€€€€t((€€€‘•˜…ÑÑ…­¥¹}É•ÍÑÉ¥Ñ¥½¸¡Í•±˜°…ÑÑ…­•ÈèA•Éµ…¹•¹Ð¤€´øÑÕÁ±•mÍÑÈ°ÍÑÉtð9½¹”è(€€€€€€€€ˆˆ‰I•ÑÕÉ¸Ñ¡”™¥ÉÍÐ=É…±”µ‘•É¥Ù•É•ÍÑÉ¥Ñ¥½¸Ñ¡…Ðµ…­•Ì…¸…ÑÑ…¬¥±±•…°¸ˆˆˆ(€€€€€€€¥˜…ÑÑ…­•È¹…ÕÉ…}…ÑÑ…­}É•ÍÑÉ¥Ñ¥½¹Ìè(€€€€€€€€€€€É•ÑÕÉ¸…ÑÑ…­•È¹…ÕÉ…}…ÑÑ…­}É•ÍÑÉ¥Ñ¥½¹ÍlÁulÅt°€‰…ÕÉ…}…¹Ñ}…ÑÑ…¬ˆ(€€€€€€€™½È™É…µ•¹Ð¥¸Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹™É…µ•¹ÑÌ¡…ÑÑ…­•È¹ÉÕ±•Í}…É¤è(€€€€€€€€€€€¥˜¹½ÐÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹9Q}QQ-}U91MM}9=Q!I}IQ%P¹™Õ±±µ…Ñ ¡™É…µ•¹Ð¤è(€€€€€€€€€€€€€€€½¹Ñ¥¹Õ”(€€€€€€€€€€€¡…Í}½Ñ¡•É}…ÉÑ¥™…Ð€ô…¹ä (€€€€€€€€€€€€€€€Á•Éµ…¹•¹Ð¥Ì¹½Ð…ÑÑ…­•È(€€€€€€€€€€€€€€€…¹Á•Éµ…¹•¹Ð¹½¹ÑÉ½±±•È€ôô…ÑÑ…­•È¹½¹ÑÉ½±±•È(€€€€€€€€€€€€€€€…¹Í•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Á•Éµ…¹•¹Ð°€‰‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€€€€€€€€€…¹€‰ÉÑ¥™…Ðˆ¥¸Á•Éµ…¹•¹Ð¹…É¹ÑåÁ•}±¥¹”(€€€€€€€€€€€€€€€™½ÈÁ•Éµ…¹•¹Ð¥¸Í•±˜¹Á±…å•ÉÍm…ÑÑ…­•È¹½¹ÑÉ½±±•Ét¹‰…ÑÑ±•™¥•±(€€€€€€€€€€€€¤(€€€€€€€€€€€¥˜¹½Ð¡…Í}½Ñ¡•É}…ÉÑ¥™…Ðè(€€€€€€€€€€€€€€€É•ÑÕÉ¸™É…µ•¹Ð°€‰…ÑÑ…­}É•ÅÕ¥É•Í}…¹½Ñ¡•É}½¹ÑÉ½±±•‘}…ÉÑ¥™…Ðˆ(€€€€€€€É•ÑÕÉ¸9½¹”((€€€‘•˜¡…Í}Ñ•µÁ½É…Éå}­•åÝ½É¡Í•±˜°Á•Éµ…¹•¹ÐèA•Éµ…¹•¹Ð°­•åÝ½ÉèQ•µÁ½É…Éå-•åÝ½É¤€´ø‰½½°è(€€€€€€€€ˆˆ‰I•…„ÕÉÉ•¹Ð‰½Õ¹‘•Ñ•µÁ½É…Éä­•åÝ½É™É½´…ÕÑ¡½É¥Ñ…Ñ¥Ù”¥¹…É¹…Ñ¥½¸ÍÑ…Ñ”¸ˆˆˆ(€€€€€€€É•ÑÕÉ¸Í•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Á•Éµ…¹•¹Ð°€‰‰…ÑÑ±•™¥•±ˆ¤…¹…¹ä (€€€€€€€€€€€•™™•Ð¹­•åÝ½É¥Ì­•åÝ½É™½È•™™•Ð¥¸Á•Éµ…¹•¹Ð¹…Ñ¥Ù•}Ñ•µÁ½É…Éå}­•åÝ½É‘}•™™•ÑÌ(€€€€€€€€¤((€€€‘•˜‰±½­¥¹}É•ÍÑÉ¥Ñ¥½¸ (€€€€€€€Í•±˜°…ÑÑ…­•ÈèA•Éµ…¹•¹Ð°‰±½­•ÈèA•Éµ…¹•¹Ð(€€€€¤€´øÑÕÁ±•mÍÑÈ°ÍÑÉtð9½¹”è(€€€€€€€€ˆˆ‰I•ÑÕÉ¸Ñ¡”™¥ÉÍÐ=É…±”µ‘•É¥Ù•É•ÍÑÉ¥Ñ¥½¸Ñ¡…Ðµ…­•ÌÑ¡¥Ì‰±½¬¥±±•…°¸ˆˆˆ(€€€€€€€¥˜Í•±˜¹}¡…Í}™±å¥¹œ¡…ÑÑ…­•È¤…¹¹½Ð€ (€€€€€€€€€€€Í•±˜¹}¡…Í}™±å¥¹œ¡‰±½­•È¤½ÈÍ•±˜¹}¡…Í}É•… ¡‰±½­•È¤(€€€€€€€€¤è(€€€€€€€€€€€É•ÑÕÉ¸€‰±å¥¹œˆ°€‰™±å¥¹}É•ÅÕ¥É•Í}™±å¥¹}½É}É•… ˆ(€€€€€€€™½È™É…µ•¹Ð¥¸Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹™É…µ•¹ÑÌ¡…ÑÑ…­•È¹ÉÕ±•Í}…É¤è(€€€€€€€€€€€¥˜Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹9Q}	}	1=-}QI}IQ%Q}9QId¹™Õ±±µ…Ñ ¡™É…µ•¹Ð¤…¹…¹ä (€€€€€€€€€€€€€€€¥Í¥¹ÍÑ…¹”¡•¹Ñ•É•°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€…¹•¹Ñ•É•¹•¹Ñ•É•‘}‰…ÑÑ±•™¥•±‘}ÑÕÉ¸€ôôÍ•±˜¹ÑÕÉ¸(€€€€€€€€€€€€€€€…¹•¹Ñ•É•¹•¹Ñ•É•‘}Õ¹‘•É}½¹ÑÉ½±±•È€ôô…ÑÑ…­•È¹½¹ÑÉ½±±•È(€€€€€€€€€€€€€€€…¹€‰ÉÑ¥™…Ðˆ¥¸•¹Ñ•É•¹…É¹ÑåÁ•}±¥¹”(€€€€€€€€€€€€€€€™½È•¹Ñ•É•¥¸Í•±˜¹}½‰©•ÑÌ¹Ù…±Õ•Ì ¤(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸™É…µ•¹Ð°€‰…ÉÑ¥™…Ñ}•¹Ñ•É•‘}Õ¹‘•É}…ÑÑ…­•É}½¹ÑÉ½±±•É}Ñ¡¥Í}ÑÕÉ¸ˆ(€€€€€€€€€€€µ…Ñ €ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹9Q}	}	1=-}	e}A=]I}=I}IQH¹™Õ±±µ…Ñ ¡™É…µ•¹Ð¤(€€€€€€€€€€€¥˜µ…Ñ …¹‰±½­•È¹Á½Ý•È€øô¥¹Ð¡µ…Ñ ¹É½ÕÀ Ä¤¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸™É…µ•¹Ð°€‰‰±½­•É}Á½Ý•É}…Ñ}½É}…‰½Ù•}É•ÍÑÉ¥Ñ¥½¸ˆ(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹9Q}	}	1=-}	e}IQI}A=]H¹™Õ±±µ…Ñ ¡™É…µ•¹Ð¤(€€€€€€€€€€€€€€€…¹‰±½­•È¹Á½Ý•È€ø…ÑÑ…­•È¹Á½Ý•È(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸™É…µ•¹Ð°€‰‰±½­•É}Á½Ý•É}É•…Ñ•É}Ñ¡…¹}…ÑÑ…­•Èˆ(€€€€€€€É•ÑÕÉ¸9½¹”((€€€‘•˜}•ÅÕ¥Áµ•¹Ñ}­•åÝ½É‘Ì¡Í•±˜°Á•Éµ…¹•¹ÐèA•Éµ…¹•¹Ð¤€´ø™É½é•¹Í•ÑmÍÑÉtè(€€€€€€€¥˜¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Á•Éµ…¹•¹Ð°€‰‰…ÑÑ±•™¥•±ˆ¤è(€€€€€€€€€€€É•ÑÕÉ¸™É½é•¹Í•Ð ¤(€€€€€€€É•ÑÕÉ¸™É½é•¹Í•Ð (€€€€€€€€€€€Í•µ…¹Ñ¥ÍlÉt(€€€€€€€€€€€™½ÈÁ±…å•È¥¸Í•±˜¹Á±…å•ÉÌ(€€€€€€€€€€€™½ÈÍ½ÕÉ”¥¸Á±…å•È¹‰…ÑÑ±•™¥•±(€€€€€€€€€€€¥˜Í½ÕÉ”¹…ÑÑ…¡•‘}Ñ¼€ôôÁ•Éµ…¹•¹Ð¹½‰©•Ñ}¥(€€€€€€€€€€€…¹Í•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Í½ÕÉ”°€‰‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€€€€€…¹€‰ÅÕ¥Áµ•¹Ðˆ¥¸Í½ÕÉ”¹ÑåÁ•}±¥¹”(€€€€€€€€€€€…¹€ (€€€€€€€€€€€€€€€Á•Éµ…¹•¹Ð¹…‰¥±¥Ñå}±½ÍÍ}Ñ¥µ•ÍÑ…µÀ¥Ì9½¹”(€€€€€€€€€€€€€€€½ÈÍ½ÕÉ”¹…ÑÑ…¡µ•¹Ñ}Ñ¥µ•ÍÑ…µÀ€øÁ•Éµ…¹•¹Ð¹…‰¥±¥Ñå}±½ÍÍ}Ñ¥µ•ÍÑ…µÀ(€€€€€€€€€€€€¤(€€€€€€€€€€€™½È™É…µ•¹Ð¥¸Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹™É…µ•¹ÑÌ¡Í½ÕÉ”¹ÉÕ±•Í}…É¤(€€€€€€€€€€€¥˜€¡Í•µ…¹Ñ¥Ì€èôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹•ÅÕ¥Áµ•¹Ñ}ÍÑ…Ñ¥}Í•µ…¹Ñ¥Ì¡Í½ÕÉ”¹…É°™É…µ•¹Ð¤¤(€€€€€€€€€€€¥Ì¹½Ð9½¹”(€€€€€€€€€€€…¹Í•µ…¹Ñ¥ÍlÉt¥Ì¹½Ð9½¹”(€€€€€€€€¤((€€€‘•˜}¡…Í}­•åÝ½É¡Í•±˜°Á•Éµ…¹•¹ÐèA•Éµ…¹•¹Ð°­•åÝ½ÉèÍÑÈ¤€´ø‰½½°è(€€€€€€€±…ÍÍ}­•åÝ½É‘Ì€ô€ (€€€€€€€€€€€Í•µ…¹Ñ¥ÍlÉt(€€€€€€€€€€€™½ÈÍ½ÕÉ”¥¸Í•±˜¹Á±…å•ÉÍmÁ•Éµ…¹•¹Ð¹½¹ÑÉ½±±•Ét¹‰…ÑÑ±•™¥•±(€€€€€€€€€€€¥˜Á•Éµ…¹•¹Ð¹¥Í}É•…ÑÕÉ”(€€€€€€€€€€€…¹Í½ÕÉ”¹±…ÍÍ}±•Ù•°¥Ì¹½Ð9½¹”(€€€€€€€€€€€…¹Í½ÕÉ”¹±…ÍÍ}±•Ù•°€øô€È(€€€€€€€€€€€…¹Í•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Í½ÕÉ”°€‰‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€€€€€…¹€ (€€€€€€€€€€€€€€€Á•Éµ…¹•¹Ð¹…‰¥±¥Ñå}±½ÍÍ}Ñ¥µ•ÍÑ…µÀ¥Ì9½¹”(€€€€€€€€€€€€€€€½ÈÍ½ÕÉ”¹±…ÍÍ}±•Ù•±}Ñ¥µ•ÍÑ…µÀ€øÁ•Éµ…¹•¹Ð¹…‰¥±¥Ñå}±½ÍÍ}Ñ¥µ•ÍÑ…µÀ(€€€€€€€€€€€€¤(€€€€€€€€€€€™½È™É…µ•¹Ð¥¸Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹™É…µ•¹ÑÌ¡Í½ÕÉ”¹ÉÕ±•Í}…É¤(€€€€€€€€€€€¥˜Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹±…ÍÍ}±•Ù•±}¡¥±¡Í½ÕÉ”¹…É°€È¤€ôô™É…µ•¹Ð(€€€€€€€€€€€¥˜€¡Í•µ…¹Ñ¥Ì€èôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹±…ÍÍ}É•…ÑÕÉ•}…¹Ñ¡•´¡Í½ÕÉ”¹…É°™É…µ•¹Ð¤¤(€€€€€€€€€€€¥Ì¹½Ð9½¹”(€€€€€€€€¤(€€€€€€€É•ÑÕÉ¸­•åÝ½É¹…Í•™½± ¤¥¸ì(€€€€€€€€€€€€¨¡Ù…±Õ”¹…Í•™½± ¤™½ÈÙ…±Õ”¥¸Á•Éµ…¹•¹Ð¹ÉÕ±•Í}…É¹­•åÝ½É‘Ì¤°(€€€€€€€€€€€€©Í•±˜¹}•ÅÕ¥Áµ•¹Ñ}­•åÝ½É‘Ì¡Á•Éµ…¹•¹Ð¤°(€€€€€€€€€€€€¨¡•™™•Ð¹­•åÝ½É¹Ù…±Õ”™½È•™™•Ð¥¸Á•Éµ…¹•¹Ð¹…Ñ¥Ù•}Ñ•µÁ½É…Éå}­•åÝ½É‘}•™™•ÑÌ¤°(€€€€€€€€€€€€©±…ÍÍ}­•åÝ½É‘Ì°(€€€€€€€€€€€€¨ (€€€€€€€€€€€€€€€­•åÝ½É¹…Í•™½± ¤(€€€€€€€€€€€€€€€™½È}Í½ÕÉ•}¥°}™É…µ•¹Ð¥¸Í•±˜¹}ÍÑ…Ñ¥}ÍÕ‰ÑåÁ•}­•åÝ½É‘}Í½ÕÉ•Ì (€€€€€€€€€€€€€€€€€€€Á•Éµ…¹•¹Ð°­•åÝ½É(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€¤°(€€€€€€€ô((€€€‘•˜}ÍÑ…Ñ¥}ÍÕ‰ÑåÁ•}­•åÝ½É‘}Í½ÕÉ•Ì (€€€€€€€Í•±˜°Á•Éµ…¹•¹ÐèA•Éµ…¹•¹Ð°­•åÝ½ÉèÍÑÈ(€€€€¤€´øÑÕÁ±•mÑÕÁ±•mÍÑÈ°ÍÑÉt°€¸¸¹tè(€€€€€€€€ˆˆ‰Ù…±Õ…Ñ”½¹ÑÉ½±±•ÍÕ‰ÑåÁ”É…¹ÑÌ¥¸±…å•ÈÍ¥à……¥¹ÍÐÕÉÉ•¹ÐÍÑ…Ñ”¸ˆˆˆ(€€€€€€€¥˜¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Á•Éµ…¹•¹Ð°€‰‰…ÑÑ±•™¥•±ˆ¤½È¹½ÐÁ•Éµ…¹•¹Ð¹¥Í}É•…ÑÕÉ”è(€€€€€€€€€€€É•ÑÕÉ¸€ ¤(€€€€€€€ÍÕ‰ÑåÁ•Ì€ôÍ•Ð¡Á•Éµ…¹•¹Ð¹ÑåÁ•}±¥¹”¹Á…ÉÑ¥Ñ¥½¸ ˆƒŠP€ˆ¥lÉt¹ÍÁ±¥Ð ¤¤(€€€€€€€Í½ÕÉ•Ìè±¥ÍÑmÑÕÁ±•mÍÑÈ°ÍÑÉut€ômt(€€€€€€€™½ÈÍ½ÕÉ”¥¸Í•±˜¹Á±…å•ÉÍmÁ•Éµ…¹•¹Ð¹½¹ÑÉ½±±•Ét¹‰…ÑÑ±•™¥•±è(€€€€€€€€€€€¥˜¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Í½ÕÉ”°€‰‰…ÑÑ±•™¥•±ˆ¤è(€€€€€€€€€€€€€€€½¹Ñ¥¹Õ”(€€€€€€€€€€€™½È™É…µ•¹Ð¥¸Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹™É…µ•¹ÑÌ¡Í½ÕÉ”¹ÉÕ±•Í}…É¤è(€€€€€€€€€€€€€€€ÁÉ½É…´€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹ÍÑ…Ñ¥}ÍÕ‰ÑåÁ•}­•åÝ½É‘}É…¹Ð¡Í½ÕÉ”¹…É°™É…µ•¹Ð¤(€€€€€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€€€€€ÁÉ½É…´¥Ì¹½Ð9½¹”(€€€€€€€€€€€€€€€€€€€…¹ÁÉ½É…´¹­•åÝ½É€ôô­•åÝ½É¹…Í•™½± ¤(€€€€€€€€€€€€€€€€€€€…¹ÁÉ½É…´¹É•…ÑÕÉ•}ÍÕ‰ÑåÁ”¥¸ÍÕ‰ÑåÁ•Ì(€€€€€€€€€€€€€€€€€€€…¹€ (€€€€€€€€€€€€€€€€€€€€€€€Á•Éµ…¹•¹Ð¹…‰¥±¥Ñå}±½ÍÍ}Ñ¥µ•ÍÑ…µÀ¥Ì9½¹”(€€€€€€€€€€€€€€€€€€€€€€€½ÈÍ½ÕÉ”¹•¹Ñ•É•‘}Ñ¥µ•ÍÑ…µÀ€øÁ•Éµ…¹•¹Ð¹…‰¥±¥Ñå}±½ÍÍ}Ñ¥µ•ÍÑ…µÀ(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•Ì¹…ÁÁ•¹ ¡Í½ÕÉ”¹½‰©•Ñ}¥°™É…µ•¹Ð¤¤(€€€€€€€É•ÑÕÉ¸ÑÕÁ±”¡Í½ÕÉ•Ì¤((€€€‘•˜}¡…Í}™±å¥¹œ¡Í•±˜°Á•Éµ…¹•¹ÐèA•Éµ…¹•¹Ð¤€´ø‰½½°è(€€€€€€€É•ÑÕÉ¸Í•±˜¹}¡…Í}­•åÝ½É¡Á•Éµ…¹•¹Ð°€‰±å¥¹œˆ¤½È…¹ä (€€€€€€€€€€€•™™•Ð¹­•åÝ½É¥ÌQ•µÁ½É…Éå-•åÝ½É¹1e%9(€€€€€€€€€€€™½È•™™•Ð¥¸Á•Éµ…¹•¹Ð¹…Ñ¥Ù•}Ñ•µÁ½É…Éå}­•åÝ½É‘}•™™•ÑÌ(€€€€€€€€¤((€€€‘•˜}¡…Í}É•… ¡Í•±˜°Á•Éµ…¹•¹ÐèA•Éµ…¹•¹Ð¤€´ø‰½½°è(€€€€€€€É•ÑÕÉ¸Í•±˜¹}¡…Í}­•åÝ½É¡Á•Éµ…¹•¹Ð°€‰I•… ˆ¤½È…¹ä (€€€€€€€€€€€•™™•Ð¹­•åÝ½É¥ÌQ•µÁ½É…Éå-•åÝ½É¹I (€€€€€€€€€€€™½È•™™•Ð¥¸Á•Éµ…¹•¹Ð¹…Ñ¥Ù•}Ñ•µÁ½É…Éå}­•åÝ½É‘}•™™•ÑÌ(€€€€€€€€¤((€€€‘•˜}¡…Í}µ•¹…”¡Í•±˜°…ÑÑ…­•ÈèA•Éµ…¹•¹Ð¤€´ø‰½½°è(€€€€€€€É•ÑÕÉ¸Í•±˜¹}¡…Í}­•åÝ½É¡…ÑÑ…­•È°€‰5•¹…”ˆ¤½È…¹ä (€€€€€€€€€€€™É…µ•¹Ð¹…Í•™½± ¤¹ÍÑ…ÉÑÍÝ¥Ñ  ‰µ•¹…”ˆ¤(€€€€€€€€€€€™½È™É…µ•¹Ð¥¸Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹™É…µ•¹ÑÌ¡…ÑÑ…­•È¹ÉÕ±•Í}…É¤(€€€€€€€€¤((€€€‘•˜}Í¥¹±•}‰±½­}±¥µ¥Ñ}Í½ÕÉ•Ì¡Í•±˜°…ÑÑ…­•ÈèA•Éµ…¹•¹Ð¤€´øÑÕÁ±•mÑÕÁ±•mÍÑÈ°ÍÑÉt°€¸¸¹tè(€€€€€€€€ˆˆ‰Ù…±Õ…Ñ”ÕÉÉ•¹ÐÍ•±˜…¹½¹ÑÉ½±±•µÍÕ‰ÑåÁ”ÍÑ…Ñ¥ŒÉ•ÍÑÉ¥Ñ¥½¹Ì¸ˆˆˆ(€€€€€€€¥˜¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡…ÑÑ…­•È°€‰‰…ÑÑ±•™¥•±ˆ¤½È¹½Ð…ÑÑ…­•È¹¥Í}É•…ÑÕÉ”è(€€€€€€€€€€€É•ÑÕÉ¸€ ¤(€€€€€€€ÍÕ‰ÑåÁ”€ôÍ•Ð¡…ÑÑ…­•È¹ÑåÁ•}±¥¹”¹Á…ÉÑ¥Ñ¥½¸ ˆƒŠP€ˆ¥lÉt¹ÍÁ±¥Ð ¤¤(€€€€€€€Í½ÕÉ•Ì€ômt(€€€€€€€™½ÈÍ½ÕÉ”¥¸Í•±˜¹Á±…å•ÉÍm…ÑÑ…­•È¹½¹ÑÉ½±±•Ét¹‰…ÑÑ±•™¥•±è(€€€€€€€€€€€¥˜¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Í½ÕÉ”°€‰‰…ÑÑ±•™¥•±ˆ¤è(€€€€€€€€€€€€€€€½¹Ñ¥¹Õ”(€€€€€€€€€€€™½È™É…µ•¹Ð¥¸Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹™É…µ•¹ÑÌ¡Í½ÕÉ”¹ÉÕ±•Í}…É¤è(€€€€€€€€€€€€€€€…™™•Ñ•€ôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹Í¥¹±•}‰±½­}±¥µ¥Ð¡Í½ÕÉ”¹…É°™É…µ•¹Ð¤(€€€€€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€€€€€€¡…™™•Ñ•€ôô€‰Í•±˜ˆ…¹Í½ÕÉ”¥Ì…ÑÑ…­•È¤(€€€€€€€€€€€€€€€€€€€½È€ (€€€€€€€€€€€€€€€€€€€€€€€…™™•Ñ•€ôô€‰½¹ÑÉ½±±•‘}Ý¥Ñ¡}½Õ¹Ñ•Èˆ(€€€€€€€€€€€€€€€€€€€€€€€…¹…¹ä¡½Õ¹Ð€ø€À™½È½Õ¹Ð¥¸…ÑÑ…­•È¹½Õ¹Ñ•ÉÌ¹Ù…±Õ•Ì ¤¤(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€½È€ (€€€€€€€€€€€€€€€€€€€€€€€…™™•Ñ•¥Ì¹½Ð9½¹”(€€€€€€€€€€€€€€€€€€€€€€€…¹…™™•Ñ•¹½Ð¥¸ì‰Í•±˜ˆ°€‰½¹ÑÉ½±±•‘}Ý¥Ñ¡}½Õ¹Ñ•È‰ô(€€€€€€€€€€€€€€€€€€€€€€€…¹…™™•Ñ•¥¸ÍÕ‰ÑåÁ”(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€Í½ÕÉ•Ì¹…ÁÁ•¹ ¡Í½ÕÉ”¹½‰©•Ñ}¥°™É…µ•¹Ð¤¤(€€€€€€€É•ÑÕÉ¸ÑÕÁ±”¡Í½ÕÉ•Ì¤((€€€‘•˜}Ù…±¥‘}‰±½­}…ÍÍ¥¹µ•¹Ð (€€€€€€€Í•±˜°(€€€€€€€…ÑÑ…­•ÉÌè±¥ÍÑmA•Éµ…¹•¹Ñt°(€€€€€€€…ÍÍ¥¹µ•¹ÐèÑÕÁ±•mÑÕÁ±•mÍÑÈ°ÍÑÉt°€¸¸¹t°(€€€€€€€‘•™•¹‘•É}¥¹‘•àè¥¹Ð°(€€€€¤€´ø‰½½°è(€€€€€€€‰å}…ÑÑ…­•Èè‘¥ÑmÍÑÈ°±¥ÍÑmÍÑÉut€ôíô(€€€€€€€™½È…ÑÑ…­•É}¥°‰±½­•É}¥¥¸…ÍÍ¥¹µ•¹Ðè(€€€€€€€€€€€‰å}…ÑÑ…­•È¹Í•Ñ‘•™…Õ±Ð¡…ÑÑ…­•É}¥°mt¤¹…ÁÁ•¹¡‰±½­•É}¥¤(€€€€€€€¥˜±•¸¡í‰±½­•É}¥™½È|°‰±½­•É}¥¥¸…ÍÍ¥¹µ•¹Ñô¤€„ô±•¸¡…ÍÍ¥¹µ•¹Ð¤è(€€€€€€€€€€€É•ÑÕÉ¸…±Í”(€€€€€€€…ÑÑ…­•É}µ…À€ôí…ÑÑ…­•È¹½‰©•Ñ}¥è…ÑÑ…­•È™½È…ÑÑ…­•È¥¸…ÑÑ…­•ÉÍô(€€€€€€€¥˜Í•Ð¡‰å}…ÑÑ…­•È¤€´Í•Ð¡…ÑÑ…­•É}µ…À¤è(€€€€€€€€€€€É•ÑÕÉ¸…±Í”(€€€€€€€™½È…ÑÑ…­•È¥¸…ÑÑ…­•ÉÌè(€€€€€€€€€€€‰±½­•É}¥‘Ì€ô‰å}…ÑÑ…­•È¹•Ð¡…ÑÑ…­•È¹½‰©•Ñ}¥°mt¤(€€€€€€€€€€€¥˜Í•±˜¹}¡…Í}µ•¹…”¡…ÑÑ…­•È¤…¹‰±½­•É}¥‘Ì…¹±•¸¡‰±½­•É}¥‘Ì¤€ð€Èè(€€€€€€€€€€€€€€€É•ÑÕÉ¸…±Í”(€€€€€€€€€€€¥˜±•¸¡‰±½­•É}¥‘Ì¤€ø€Ä…¹Í•±˜¹}Í¥¹±•}‰±½­}±¥µ¥Ñ}Í½ÕÉ•Ì¡…ÑÑ…­•È¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸…±Í”(€€€€€€€€€€€™½È‰±½­•É}¥¥¸‰±½­•É}¥‘Ìè(€€€€€€€€€€€€€€€‰±½­•È€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡‰±½­•É}¥¤(€€€€€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡‰±½­•È°A•Éµ…¹•¹Ð¤½È¹½ÐÍ•±˜¹…¹}‰±½¬ (€€€€€€€€€€€€€€€€€€€…ÑÑ…­•È°‰±½­•È°‘•™•¹‘•É}¥¹‘•à(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€É•ÑÕÉ¸…±Í”(€€€€€€€É•ÑÕÉ¸QÉÕ”((€€€‘•˜}Ý¥Ñ¹•ÍÍ}Õ¹ÍÕÁÁ½ÉÑ•‘}‰±½­}½¹Ñ•áÐ¡Í•±˜°…ÑÑ…­•ÈèA•Éµ…¹•¹Ð°‰±½­•ÈèA•Éµ…¹•¹Ð¤€´ø9½¹”è(€€€€€€€€ˆˆ‰I•½É„5•¹…”½ÁÁ½ÉÑÕ¹¥Ñä½¹±ä™½È…¸…ÕÑ¡½É¥Ñ…Ñ¥Ù”‰±½­•È…¹‘¥‘…Ñ”¸ˆˆˆ(€€€€€€€¥˜¹½Ð€ (€€€€€€€€€€€Í•±˜¹ÍÑ•À¥ÌQÕÉ¹MÑ•À¹1I}	1=-IL(€€€€€€€€€€€…¹Í•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡…ÑÑ…­•È°€‰‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€€€€€…¹Í•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡‰±½­•È°€‰‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€€€€€…¹…ÑÑ…­•È¹½‰©•Ñ}¥¥¸Í•±˜¹}½µ‰…Ñ}…ÑÑ…­•ÉÌ(€€€€€€€€¤è(€€€€€€€€€€€É•ÑÕÉ¸(€€€€€€€™½È½ÕÉÉ•¹”¥¸Í•±˜¹Í•µ…¹Ñ¥}½ÕÉÉ•¹•Ìè(€€€€€€€€€€€¥˜½ÕÉÉ•¹”¹½‰©•Ñ}¥€ôô…ÑÑ…­•È¹½‰©•Ñ}¥…¹½ÕÉÉ•¹”¹½É…±•}™É…µ•¹Ð¹ÍÑ…ÉÑÍÝ¥Ñ  (€€€€€€€€€€€€€€€€‰5•¹…”€ˆ(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€Í•±˜¹}É•½É‘}½ÁÁ½ÉÑÕ¹¥Ñä (€€€€€€€€€€€€€€€€€€€½ÕÉÉ•¹”°(€€€€€€€€€€€€€€€€€€€…ÕÍ•}­¥¹ô‰±•…±}‰±½­}½¹Ñ•áÐˆ°(€€€€€€€€€€€€€€€€€€€…ÕÍ•}¥ô (€€€€€€€€€€€€€€€€€€€€€€€˜‰‰±½¬éíÍ•±˜¹ÑÕÉ¹ôéíÍ•±˜¹ÍÑ•À¹Ù…±Õ•ôèˆ(€€€€€€€€€€€€€€€€€€€€€€€˜‰í…ÑÑ…­•È¹½‰©•Ñ}¥‘ôéí‰±½­•È¹½‰©•Ñ}¥‘ôˆ(€€€€€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€€€€€…ÕÍ•}ÍÕ‰©•Ñ}¥‘Ìô¡…ÑÑ…­•È¹½‰©•Ñ}¥°‰±½­•È¹½‰©•Ñ}¥¤°(€€€€€€€€€€€€€€€€¤((€€€‘•˜…¹}‰±½¬¡Í•±˜°…ÑÑ…­•ÈèA•Éµ…¹•¹Ð°‰±½­•ÈèA•Éµ…¹•¹Ð°‘•™•¹‘•É}¥¹‘•àè¥¹Ð¤€´ø‰½½°è(€€€€€€€É•ÑÕÉ¸€ (€€€€€€€€€€€‰±½­•È¹½¹ÑÉ½±±•È€ôô‘•™•¹‘•É}¥¹‘•à(€€€€€€€€€€€…¹…¹ä¡…¹‘¥‘…Ñ”¥Ì‰±½­•È™½È…¹‘¥‘…Ñ”¥¸Í•±˜¹Á±…å•ÉÍm‘•™•¹‘•É}¥¹‘•át¹‰…ÑÑ±•™¥•±¤(€€€€€€€€€€€…¹‰±½­•È¹¥Í}É•…ÑÕÉ”(€€€€€€€€€€€…¹¹½Ð‰±½­•È¹Ñ…ÁÁ•(€€€€€€€€€€€…¹Í•±˜¹‰±½­¥¹}É•ÍÑÉ¥Ñ¥½¸¡…ÑÑ…­•È°‰±½­•È¤¥Ì9½¹”(€€€€€€€€¤((€€€‘•˜•¹•É…Ñ•}‰±½­Ì (€€€€€€€Í•±˜°(€€€€€€€…ÑÑ…­•ÉÌè±¥ÍÑmA•Éµ…¹•¹Ñt°(€€€€€€€‘•™•¹‘•É}¥¹‘•àè¥¹Ð°(€€€€€€€€¨°(€€€€€€€±½}É•©•Ñ¥½¹Ìè‰½½°€ôQÉÕ”°(€€€€¤€´ø‘¥ÑmÍÑÈ°A•Éµ…¹•¹Ñtè(€€€€€€€€ˆˆ‰•¹•É…Ñ”‘•Ñ•Éµ¥¹¥ÍÑ¥Œ½¹”µÑ¼µ½¹”‰±½­ÌÕÍ¥¹œÑ¡”Í…µ”±•…±¥Ñä…ÌÙ…±¥‘…Ñ¥½¸¸ˆˆˆ(€€€€€€€…Ù…¥±…‰±”€ôl(€€€€€€€€€€€Á•Éµ…¹•¹Ð(€€€€€€€€€€€™½ÈÁ•Éµ…¹•¹Ð¥¸Í•±˜¹Á±…å•ÉÍm‘•™•¹‘•É}¥¹‘•át¹‰…ÑÑ±•™¥•±(€€€€€€€€€€€¥˜Á•Éµ…¹•¹Ð¹¥Í}É•…ÑÕÉ”…¹¹½ÐÁ•Éµ…¹•¹Ð¹Ñ…ÁÁ•(€€€€€€€t(€€€€€€€‰±½­Ìè‘¥ÑmÍÑÈ°A•Éµ…¹•¹Ñt€ôíô(€€€€€€€™½È…ÑÑ…­•È¥¸…ÑÑ…­•ÉÌè(€€€€€€€€€€€™½È‰±½­•È¥¸…Ù…¥±…‰±”è(€€€€€€€€€€€€€€€Í•±˜¹}Ý¥Ñ¹•ÍÍ}Õ¹ÍÕÁÁ½ÉÑ•‘}‰±½­}½¹Ñ•áÐ¡…ÑÑ…­•È°‰±½­•È¤(€€€€€€€€€€€€€€€É•ÍÑÉ¥Ñ¥½¸€ôÍ•±˜¹‰±½­¥¹}É•ÍÑÉ¥Ñ¥½¸¡…ÑÑ…­•È°‰±½­•È¤(€€€€€€€€€€€€€€€¥˜É•ÍÑÉ¥Ñ¥½¸¥Ì¹½Ð9½¹”è(€€€€€€€€€€€€€€€€€€€™É…µ•¹Ð°É•…Í½¸€ôÉ•ÍÑÉ¥Ñ¥½¸(€€€€€€€€€€€€€€€€€€€¥˜±½}É•©•Ñ¥½¹Ìè(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‰±½­}…¹‘¥‘…Ñ•}É•©•Ñ•ˆ°(€€€€€€€€€€€€€€€€€€€€€€€€€€€…ÑÑ…­•Èõ…ÑÑ…­•È¹…É¹¹…µ”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€‰±½­•Èõ‰±½­•È¹…É¹¹…µ”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€½É…±•}™É…µ•¹Ðõ™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€É•…Í½¸õÉ•…Í½¸°(€€€€€€€€€€€€€€€€€€€€€€€€€€€…ÑÑ…­•É}Á½Ý•Èõ…ÑÑ…­•È¹Á½Ý•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€‰±½­•É}Á½Ý•Èõ‰±½­•È¹Á½Ý•È°(€€€€€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€½¹Ñ¥¹Õ”(€€€€€€€€€€€€€€€‰±½­Ím…ÑÑ…­•È¹½‰©•Ñ}¥‘t€ô‰±½­•È(€€€€€€€€€€€€€€€…Ù…¥±…‰±”¹É•µ½Ù”¡‰±½­•È¤(€€€€€€€€€€€€€€€‰É•…¬(€€€€€€€É•ÑÕÉ¸‰±½­Ì((€€€‘•˜½µ‰…Ð (€€€€€€€Í•±˜°(€€€€€€€…ÑÑ…­•ÉÌè±¥ÍÑmA•Éµ…¹•¹Ñt°(€€€€€€€‰±½­Ìè‘¥ÑmÍÑÈ°A•Éµ…¹•¹Ñtð9½¹”€ô9½¹”°(€€€€€€€€¨°(€€€€€€€…ÕÑ½}…ÍÍ¥¹}‰±½­•ÉÌè‰½½°€ô…±Í”°(€€€€¤€´ø9½¹”è(€€€€€€€€ˆˆ‰½µÁ…Ñ¥‰¥±¥Ñä…‘…ÁÑ•È½Ù•ÈÑ¡”Ñ¡É•”…ÕÑ¡½É¥Ñ…Ñ¥Ù”½µ‰…Ð…Ñ¥½¹Ì¸ˆˆˆ(€€€€€€€¥˜Í•±˜¹ÍÑ•À¥Ì¹½ÐQÕÉ¹MÑ•À¹1I}QQ-ILè(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰…ÑÑ…­•ÉÌ…¸‰”‘•±…É•½¹±ä‘ÕÉ¥¹œ‘•±…É”…ÑÑ…­•ÉÌˆ¤(€€€€€€€…ÑÑ…­•É}¥‘Ì€ôÑÕÁ±”¡…ÑÑ…­•È¹½‰©•Ñ}¥™½È…ÑÑ…­•È¥¸…ÑÑ…­•ÉÌ¤(€€€€€€€…ÑÑ…¬€ô¹•áÐ (€€€€€€€€€€€€ (€€€€€€€€€€€€€€€½ÁÑ¥½¸(€€€€€€€€€€€€€€€™½È½ÁÑ¥½¸¥¸Í•±˜¹±•…±}…ÑÑ…­}½ÁÑ¥½¹Ì¡Í•±˜¹…Ñ¥Ù•}Á±…å•È¤(€€€€€€€€€€€€€€€¥˜½ÁÑ¥½¸¹…ÑÑ…­•É}¥‘Ì€ôô…ÑÑ…­•É}¥‘Ì(€€€€€€€€€€€€€€€…¹…±°¡Í•±˜¹}½‰©•ÑÌ¹•Ð¡…ÑÑ…­•È¹½‰©•Ñ}¥¤¥Ì…ÑÑ…­•È™½È…ÑÑ…­•È¥¸…ÑÑ…­•ÉÌ¤(€€€€€€€€€€€€¤°(€€€€€€€€€€€9½¹”°(€€€€€€€€¤(€€€€€€€¥˜…ÑÑ…¬¥Ì9½¹”è(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰¥±±•…°…ÑÑ…­•Èˆ¤(€€€€€€€‘•™•¹‘•È€ô€Ä€´Í•±˜¹…Ñ¥Ù•}Á±…å•È(€€€€€€€¥˜¹½Ð…ÕÑ½}…ÍÍ¥¹}‰±½­•ÉÌè(€€€€€€€€€€€‰±½­Ì€ô‰±½­Ì½Èíô(€€€€€€€€€€€…ÑÑ…­•É}¥‘}Í•Ð€ôÍ•Ð¡…ÑÑ…­•É}¥‘Ì¤(€€€€€€€€€€€¥˜…¹ä¡…ÑÑ…­•É}¥¹½Ð¥¸…ÑÑ…­•É}¥‘}Í•Ð™½È…ÑÑ…­•É}¥¥¸‰±½­Ì¤è(€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰‰±½¬…ÍÍ¥¹•Ñ¼„¹½¹…ÑÑ…­•Èˆ¤(€€€€€€€€€€€¥˜±•¸¡í‰±½­•È¹½‰©•Ñ}¥™½È‰±½­•È¥¸‰±½­Ì¹Ù…±Õ•Ì ¥ô¤€„ô±•¸¡‰±½­Ì¤è(€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰¥±±•…°‰±½­•Èˆ¤(€€€€€€€€€€€¥˜…¹ä (€€€€€€€€€€€€€€€¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡‰±½­•È°€‰‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€€€€€€€€€½È¹½ÐÍ•±˜¹…¹}‰±½¬ (€€€€€€€€€€€€€€€€€€€Í•±˜¹}½‰©•ÑÍm…ÑÑ…­•É}¥‘t°(€€€€€€€€€€€€€€€€€€€‰±½­•È°(€€€€€€€€€€€€€€€€€€€‘•™•¹‘•È°€€ŒÑåÁ”è¥¹½É•m…ÉœµÑåÁ•t(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€™½È…ÑÑ…­•É}¥°‰±½­•È¥¸‰±½­Ì¹¥Ñ•µÌ ¤(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰¥±±•…°‰±½­•Èˆ¤(€€€€€€€Í•±˜¹•á•ÕÑ•}…ÑÑ…­}…Ñ¥½¸¡…ÑÑ…¬¤(€€€€€€€¥˜…ÕÑ½}…ÍÍ¥¹}‰±½­•ÉÌè(€€€€€€€€€€€¥˜‰±½­Ì¥Ì¹½Ð9½¹”è(€€€€€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰…¹¹½ÐÁÉ½Ù¥‘”‰±½­ÌÝ¡•¸…ÕÑ¼µ…ÍÍ¥¹¥¹œ‰±½­•ÉÌˆ¤(€€€€€€€€€€€‰±½­}½ÁÑ¥½¹Ì€ôÍ•±˜¹±•…±}‰±½­}½ÁÑ¥½¹Ì¡…ÑÑ…¬°‘•™•¹‘•È¤(€€€€€€€€€€€µ…á}‰±½­Ì€ôµ…à¡±•¸¡½ÁÑ¥½¸¹‰±½­Ì¤™½È½ÁÑ¥½¸¥¸‰±½­}½ÁÑ¥½¹Ì¤(€€€€€€€€€€€‰±½­}½ÁÑ¥½¸€ôµ…à (€€€€€€€€€€€€€€€€¡½ÁÑ¥½¸™½È½ÁÑ¥½¸¥¸‰±½­}½ÁÑ¥½¹Ì¥˜±•¸¡½ÁÑ¥½¸¹‰±½­Ì¤€ôôµ…á}‰±½­Ì¤°(€€€€€€€€€€€€€€€­•äõ±…µ‰‘„½ÁÑ¥½¸èÑÕÁ±” (€€€€€€€€€€€€€€€€€€€€µ…ÑÑ…¬¹…ÑÑ…­•É}¥‘Ì¹¥¹‘•à¡…ÑÑ…­•É}¥¤™½È…ÑÑ…­•É}¥°|¥¸½ÁÑ¥½¸¹‰±½­Ì(€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€¤(€€€€€€€•±Í”è(€€€€€€€€€€€…ÍÍ•ÉÐ‰±½­Ì¥Ì¹½Ð9½¹”(€€€€€€€€€€€‰±½­}½ÁÑ¥½¸€ôÑ¥½¹=ÁÑ¥½¸ (€€€€€€€€€€€€€€€Ñ¥½¹-¥¹¹1I}	1=-IL°(€€€€€€€€€€€€€€€‘•™•¹‘•È°(€€€€€€€€€€€€€€€‰±½­ÌõÑÕÁ±” (€€€€€€€€€€€€€€€€€€€€¡…ÑÑ…­•É}¥°‰±½­•È¹½‰©•Ñ}¥¤™½È…ÑÑ…­•É}¥°‰±½­•È¥¸‰±½­Ì¹¥Ñ•µÌ ¤(€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€¤(€€€€€€€Í•±˜¹•á•ÕÑ•}‰±½­}…Ñ¥½¸¡‰±½­}½ÁÑ¥½¸¤(€€€€€€€¥˜Í•±˜¹ÍÑ•À¥ÌQÕÉ¹MÑ•À¹1I}	1=-ILè(€€€€€€€€€€€Í•±˜¹•á•ÕÑ•}Í¹•…­}…Ñ¥½¸¡Ñ¥½¹=ÁÑ¥½¸¡Ñ¥½¹-¥¹¹AML°Í•±˜¹…Ñ¥Ù•}Á±…å•È¤¤(€€€€€€€Ý¡¥±”Í•±˜¹ÍÑ•À¥ÌQÕÉ¹MÑ•À¹=5	Q}5è(€€€€€€€€€€€Í•±˜¹É•Í½±Ù•}½µ‰…Ñ}‘…µ…” ¤((€€€‘•˜•¹‘}ÑÕÉ¸¡Í•±˜¤€´ø9½¹”è(€€€€€€€€ˆˆ‰½µÁ…Ñ¥‰¥±¥Ñä¡•±Á•Èè™½±±½Ü±•…°ÑÉ…¹Í¥Ñ¥½¹ÌÑ¡É½Õ ±•…¹ÕÀ¸ˆˆˆ(€€€€€€€¥˜Í•±˜¹ÍÑ•À¥¸íQÕÉ¹MÑ•À¹MQU@°QÕÉ¹MÑ•À¹19UAôè(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰•¹‘}ÑÕÉ¸¥Ì±•…°½¹±ä‘ÕÉ¥¹œ…¸…Ñ¥Ù”ÑÕÉ¸ˆ¤(€€€€€€€Ý¡¥±”Í•±˜¹ÍÑ•À¹½Ð¥¸íQÕÉ¹MÑ•À¹A=MQ=5	Q}5%8°QÕÉ¹MÑ•À¹9}MQAôè(€€€€€€€€€€€¥˜Í•±˜¹ÍÑ•À¥ÌQÕÉ¹MÑ•À¹=5	Q}5è(€€€€€€€€€€€€€€€Í•±˜¹É•Í½±Ù•}½µ‰…Ñ}‘…µ…” ¤(€€€€€€€€€€€•±Í”è(€€€€€€€€€€€€€€€Í•±˜¹…‘Ù…¹•}ÍÑ•À ¤(€€€€€€€¥˜Í•±˜¹ÍÑ•À¥ÌQÕÉ¹MÑ•À¹A=MQ=5	Q}5%8è(€€€€€€€€€€€Í•±˜¹…‘Ù…¹•}ÍÑ•À ¤(€€€€€€€Í•±˜¹…‘Ù…¹•}Ñ¼¡QÕÉ¹MÑ•À¹19U@¤((€€€‘•˜ÁÕÑ}Á•Éµ…¹•¹ÑÍ}¥¹Ñ½}É…Ù•å…É (€€€€€€€Í•±˜°(€€€€€€€Á•Éµ…¹•¹ÑÌèÑÕÁ±•mA•Éµ…¹•¹Ð°€¸¸¹t°(€€€€€€€€¨°(€€€€€€€ÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¸èÍÑÈð9½¹”€ô9½¹”°(€€€€¤€´øÑÕÁ±•m…É‘=‰©•Ð°€¸¸¹tè(€€€€€€€€ˆˆ‰5½Ù”½¹”Í¥µÕ±Ñ…¹•½ÕÌ‰…ÑÑ±•™¥•±‰…Ñ Ý¥Ñ „Í¡…É•±…ÍÐµ­¹½Ý¸ÑÉ¥•ÈÍ¹…ÁÍ¡½Ð¸ˆˆˆ(€€€€€€€¥˜±•¸¡íÁ•Éµ…¹•¹Ð¹½‰©•Ñ}¥™½ÈÁ•Éµ…¹•¹Ð¥¸Á•Éµ…¹•¹ÑÍô¤€„ô±•¸¡Á•Éµ…¹•¹ÑÌ¤è(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰Í¥µÕ±Ñ…¹•½ÕÌ‘•Á…ÉÑÕÉ”‰…Ñ ½¹Ñ…¥¹Ì‘ÕÁ±¥…Ñ”½‰©•ÑÌˆ¤(€€€€€€€¥˜…¹ä¡¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Á•Éµ…¹•¹Ð°€‰‰…ÑÑ±•™¥•±ˆ¤™½ÈÁ•Éµ…¹•¹Ð¥¸Á•Éµ…¹•¹ÑÌ¤è(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰Í¥µÕ±Ñ…¹•½ÕÌ‘•Á…ÉÑÕÉ”É•ÅÕ¥É•Ì…ÕÑ¡½É¥Ñ…Ñ¥Ù”Á•Éµ…¹•¹ÑÌˆ¤(€€€€€€€…ÕÑ¡½É¥Ñä€ôÍ•±˜¹}‰…ÑÑ±•™¥•±‘}…ÕÑ¡½É¥Ñå}Í¹…ÁÍ¡½Ð ¤(€€€€€€€Í½ÕÉ•Ì€ôÍ•±˜¹}Á•Éµ…¹•¹Ñ}±•™Ñ}ÑÉ¥•É}Í½ÕÉ•Ì ¤(€€€€€€€€Œ±°‘•Á…ÉÑ¥¹œ½‰©•ÑÌÕÍ”ÁÉ”µ•Ù•¹Ð…‰¥±¥Ñ¥•Ì°¥¹±Õ‘¥¹œÍÕÁÁÉ•ÍÍ•‘¥•Ì½1QÑ•áÐ¸(€€€€€€€‘•™•ÉÉ•€ô•Ñ…ÑÑÈ¡Í•±˜°€‰}½¹Ñ¥¹Õ½ÕÍ}É•™É•Í¡}‘•™•ÉÉ•ˆ°…±Í”¤(€€€€€€€Í•±˜¹}½¹Ñ¥¹Õ½ÕÍ}É•™É•Í¡}‘•™•ÉÉ•€ôQÉÕ”(€€€€€€€ÑÉäè(€€€€€€€€€€€É•ÑÕÉ¸ÑÕÁ±” (€€€€€€€€€€€€€€€Í•±˜¹ÁÕÑ}¥¹Ñ½}É…Ù•å…É (€€€€€€€€€€€€€€€€€€€Á•Éµ…¹•¹Ð°(€€€€€€€€€€€€€€€€€€€ÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¸õÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¸°(€€€€€€€€€€€€€€€€€€€}‘•Á…ÉÑÕÉ•}…ÕÑ¡½É¥Ñäõ…ÕÑ¡½É¥Ñä°(€€€€€€€€€€€€€€€€€€€}‘•Á…ÉÑÕÉ•}Í½ÕÉ•ÌõÍ½ÕÉ•Ì°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€™½ÈÁ•Éµ…¹•¹Ð¥¸Á•Éµ…¹•¹ÑÌ(€€€€€€€€€€€€¤(€€€€€€€™¥¹…±±äè(€€€€€€€€€€€Í•±˜¹}½¹Ñ¥¹Õ½ÕÍ}É•™É•Í¡}‘•™•ÉÉ•€ô‘•™•ÉÉ•(€€€€€€€€€€€Í•±˜¹É•™É•Í¡}ÍÑ…Ñ¥}ÁÑ}µ½‘¥™¥•ÉÌ ¤((€€€‘•˜ÁÕÑ}¥¹Ñ½}É…Ù•å…É (€€€€€€€Í•±˜°(€€€€€€€Á•Éµ…¹•¹ÐèA•Éµ…¹•¹Ð°(€€€€€€€€¨°(€€€€€€€ÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¸èÍÑÈð9½¹”€ô9½¹”°(€€€€€€€}‘•Á…ÉÑÕÉ•}…ÕÑ¡½É¥ÑäèÑÕÁ±•mÑÕÁ±•mÍÑÈ°¥¹Ñt°€¸¸¹tð9½¹”€ô9½¹”°(€€€€€€€}‘•Á…ÉÑÕÉ•}Í½ÕÉ•ÌèÑÕÁ±•mÑÕÁ±•mA•Éµ…¹•¹Ð°ÍÑÉt°€¸¸¹tð9½¹”€ô9½¹”°(€€€€¤€´ø…É‘=‰©•Ðè(€€€€€€€¥˜¹½ÐÍ•±˜¹¥Í}…ÕÑ¡½É¥Ñ…Ñ¥Ù”¡Á•Éµ…¹•¹Ð°€‰‰…ÑÑ±•™¥•±ˆ¤è(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰Á•Éµ…¹•¹Ð¥Ì¹½Ð½¸Ñ¡”‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€½Ý¹•È€ôÍ•±˜¹Á±…å•ÉÍmÁ•Éµ…¹•¹Ð¹½Ý¹•Ét(€€€€€€€½¹ÑÉ½±±•È€ôÁ•Éµ…¹•¹Ð¹½¹ÑÉ½±±•È(€€€€€€€‰…ÑÑ±•™¥•±‘}…ÕÑ¡½É¥Ñä€ô€ (€€€€€€€€€€€Í•±˜¹}‰…ÑÑ±•™¥•±‘}…ÕÑ¡½É¥Ñå}Í¹…ÁÍ¡½Ð ¤(€€€€€€€€€€€¥˜}‘•Á…ÉÑÕÉ•}…ÕÑ¡½É¥Ñä¥Ì9½¹”(€€€€€€€€€€€•±Í”}‘•Á…ÉÑÕÉ•}…ÕÑ¡½É¥Ñä(€€€€€€€€¤(€€€€€€€Á…É…µ•¥…}™É…µ•¹Ð€ôÍ•±˜¹}Á…É…µ•¥…}™É…µ•¹Ð¡Á•Éµ…¹•¹Ð¹ÉÕ±•Í}…É¤(€€€€€€€‘¥•Í}‘É…Ý}™É…µ•¹ÑÌ€ôÑÕÁ±” (€€€€€€€€€€€™É…µ•¹Ð(€€€€€€€€€€€™½È™É…µ•¹Ð¥¸Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹™É…µ•¹ÑÌ¡Á•Éµ…¹•¹Ð¹ÉÕ±•Í}…É¤(€€€€€€€€€€€¥˜€¡½Ù•É…”€èôÍ•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹‘¥•Í}‘É…Ý}Í•µ…¹Ñ¥}½Ù•É…”¡Á•Éµ…¹•¹Ð¹…É°™É…µ•¹Ð¤¤(€€€€€€€€€€€¥Ì¹½Ð9½¹”(€€€€€€€€€€€…¹½Ù•É…”¹™Õ±±å}ÍÕÁÁ½ÉÑ•(€€€€€€€€¤(€€€€€€€±…ÍÑ}­¹½Ý¹}ÑåÁ•}±¥¹”€ôÁ•Éµ…¹•¹Ð¹ÑåÁ•}±¥¹”(€€€€€€€±…ÍÑ}­¹½Ý¹}¥Í}É•…ÑÕÉ”€ôÁ•Éµ…¹•¹Ð¹¥Í}É•…ÑÕÉ”(€€€€€€€Í•±˜¹…±±¥…¹•}µ½‘•Í}¡½Í•¸¹Á½À¡Á•Éµ…¹•¹Ð¹½‰©•Ñ}¥°9½¹”¤(€€€€€€€™¥¹…±¥Ñä€ôÁ•Éµ…¹•¹Ð¹½Õ¹Ñ•ÉÌ¹•Ð ‰™¥¹…±¥Ñäˆ°€À¤€ø€À(€€€€€€€‘•ÍÑ¥¹…Ñ¥½¸€ô€‰•á¥±”ˆ¥˜™¥¹…±¥Ñä•±Í”€‰É…Ù•å…Éˆ(€€€€€€€É•Á±…•µ•¹Ð€ôÍ•±˜¹µ½Ù•}½‰©•Ð (€€€€€€€€€€€Á•Éµ…¹•¹Ð°(€€€€€€€€€€€‘•ÍÑ¥¹…Ñ¥½¸°(€€€€€€€€€€€É•…Í½¸ô ‰™¥¹…±¥Ñå}•á¥±”ˆ¥˜™¥¹…±¥Ñä•±Í”€¡ÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¸½È€‰ÁÕÑ}¥¹Ñ½}É…Ù•å…Éˆ¤¤°(€€€€€€€€€€€}‘•Á…ÉÑÕÉ•}…ÕÑ¡½É¥Ñäõ‰…ÑÑ±•™¥•±‘}…ÕÑ¡½É¥Ñä°(€€€€€€€€€€€}‘•Á…ÉÑÕÉ•}Í½ÕÉ•Ìõ}‘•Á…ÉÑÕÉ•}Í½ÕÉ•Ì°(€€€€€€€€¤(€€€€€€€…ÍÍ•ÉÐ¥Í¥¹ÍÑ…¹”¡É•Á±…•µ•¹Ð°…É‘=‰©•Ð¤(€€€€€€€Í•±˜¹É•™É•Í¡}ÍÑ…Ñ¥}ÁÑ}µ½‘¥™¥•ÉÌ ¤(€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€‰Á•Éµ…¹•¹Ñ}Ñ½}•á¥±”ˆ¥˜™¥¹…±¥Ñä•±Í”€‰Á•Éµ…¹•¹Ñ}Ñ½}É…Ù•å…Éˆ°(€€€€€€€€€€€Á±…å•Èõ½Ý¹•È¹¹…µ”°(€€€€€€€€€€€…ÉõÁ•Éµ…¹•¹Ð¹…É¹¹…µ”°(€€€€€€€€€€€ÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¸õÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¸°(€€€€€€€€¤(€€€€€€€¥˜€¡‘¥•Í}‘É…Ý}™É…µ•¹ÑÌ½ÈÁ…É…µ•¥…}™É…µ•¹Ð¤…¹±…ÍÑ}­¹½Ý¹}¥Í}É•…ÑÕÉ”…¹¹½Ð™¥¹…±¥Ñäè(€€€€€€€€€€€•Ù•¹Ð€ôÍ•±˜¹}¹•Ý}ÉÕ±•Í}•Ù•¹Ð (€€€€€€€€€€€€€€€IÕ±•ÍÙ•¹Ñ-¥¹¹IQUI}%°(€€€€€€€€€€€€€€€½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€¡Á•Éµ…¹•¹Ð¹½‰©•Ñ}¥°¤°(€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÁ•Éµ…¹•¹Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€‰…ÑÑ±•™¥•±‘}…ÕÑ¡½É¥Ñäõ‰…ÑÑ±•™¥•±‘}…ÕÑ¡½É¥Ñä°(€€€€€€€€€€€€€€€±…ÍÑ}­¹½Ý¹}‰…ÑÑ±•™¥•±ô (€€€€€€€€€€€€€€€€€€€€ (€€€€€€€€€€€€€€€€€€€€€€€Á•Éµ…¹•¹Ð¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€±…ÍÑ}­¹½Ý¹}ÑåÁ•}±¥¹”°(€€€€€€€€€€€€€€€€€€€€€€€±…ÍÑ}­¹½Ý¹}¥Í}É•…ÑÕÉ”°(€€€€€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€¤(€€€€€€€€€€€¥˜Á…É…µ•¥…}™É…µ•¹Ðè(€€€€€€€€€€€€€€€Í•±˜¹}Á…É…µ•¥…}‘•Á…ÉÑÕÉ•ÍmÁ•Éµ…¹•¹Ð¹½‰©•Ñ}¥‘t€ô€ (€€€€€€€€€€€€€€€€€€€Á•Éµ…¹•¹Ð°(€€€€€€€€€€€€€€€€€€€É•Á±…•µ•¹Ð°(€€€€€€€€€€€€€€€€€€€•Ù•¹Ð°(€€€€€€€€€€€€€€€€€€€Á…É…µ•¥…}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€Í•±˜¹}•¹ÅÕ•Õ•}ÑÉ¥•È (€€€€€€€€€€€€€€€€€€€•Ù•¹Ð°Á•Éµ…¹•¹Ð°Á…É…µ•¥…}™É…µ•¹Ð°QÉ¥•É™™•Ð¹AI5%}a%1}!=%(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€™½È™É…µ•¹Ð¥¸‘¥•Í}‘É…Ý}™É…µ•¹ÑÌè(€€€€€€€€€€€€€€€Í•±˜¹}•¹ÅÕ•Õ•}ÑÉ¥•È¡•Ù•¹Ð°Á•Éµ…¹•¹Ð°™É…µ•¹Ð°QÉ¥•É™™•Ð¹%M}I\¤(€€€€€€€É•ÑÕÉ¸É•Á±…•µ•¹Ð((€€€‘•˜‘•ÍÑÉ½ä¡Í•±˜°Á•Éµ…¹•¹ÐèA•Éµ…¹•¹Ð°€¨°ÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¸èÍÑÈð9½¹”€ô9½¹”¤€´ø9½¹”è(€€€€€€€¥˜Í•±˜¹}¡…Í}­•åÝ½É¡Á•Éµ…¹•¹Ð°€‰%¹‘•ÍÑÉÕÑ¥‰±”ˆ¤è(€€€€€€€€€€€Í•±˜¹±½œ (€€€€€€€€€€€€€€€€‰‘•ÍÑÉÕÑ¥½¹}ÁÉ•Ù•¹Ñ•ˆ°Ñ…É•Ñ}¥õÁ•Éµ…¹•¹Ð¹½‰©•Ñ}¥°É•…Í½¸ô‰¥¹‘•ÍÑÉÕÑ¥‰±”ˆ(€€€€€€€€€€€€¤(€€€€€€€€€€€É•ÑÕÉ¸(€€€€€€€Í•±˜¹ÁÕÑ}¥¹Ñ½}É…Ù•å…É¡Á•Éµ…¹•¹Ð°ÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¸õÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¸¤((€€€‘•˜¡•­}ÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¹Ì¡Í•±˜¤€´ø9½¹”è(€€€€€€€Í•±˜¹É•™É•Í¡}ÍÑ…Ñ¥}ÁÑ}µ½‘¥™¥•ÉÌ ¤(€€€€€€€Ý¡¥±”QÉÕ”è(€€€€€€€€€€€¡…¹•€ôÍ•±˜¹…ÕÉ…}ÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¹Ì ¤(€€€€€€€€€€€™½È…Ñ¥½¸¥¸Í•±˜¹ÍÑ…Ñ•}‰…Í•‘}…Ñ¥½¹Ìè(€€€€€€€€€€€€€€€¥˜…Ñ¥½¸¹…ÁÁ±ä¡Í•±˜¤è(€€€€€€€€€€€€€€€€€€€¡…¹•€ôQÉÕ”(€€€€€€€€€€€€€€€€€€€Í•±˜¹É•™É•Í¡}ÍÑ…Ñ¥}ÁÑ}µ½‘¥™¥•ÉÌ ¤(€€€€€€€€€€€¥˜¹½Ð¡…¹•è(€€€€€€€€€€€€€€€‰É•…¬(€€€€€€€Í•±˜¹¡•­}±¥™” ¤(€€€€€€€¥˜¹½ÐÍ•±˜¹¥Í}Ñ•Éµ¥¹…°…¹Í•±˜¹}ÁÕÑ}Á•¹‘¥¹}ÑÉ¥•ÉÍ}½¹}ÍÑ…¬ (€€€€€€€€€€€ì(€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹%M}I\°(€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹I9Q}%M}IQUI8°(€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹AI599Q}1Q}M1}=U9QH°(€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹=9QI=11}IQUI}1Q}=AA=99Q}1=ML°(€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹=9QI=11}=U9QI}IQUI}1Q}1%°(€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹=9QI=11}IQ%Q}=U9QI}QI9MH°(€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹5}Q=}M1}59°(€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹1Q	}5UQ8°(€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹AI5%}a%1}!=%°(€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹UQ%1%Qe}QIP°(€€€€€€€€€€€ô(€€€€€€€€¤è(€€€€€€€€€€€Í•±˜¹}‘É…¥¹}ÑÉ¥•É•‘}…‰¥±¥Ñ¥•Ì ¤(€€€€€€€Í•±˜¹¡•­}¥¹Ù…É¥…¹ÑÌ ¤((€€€‘•˜¡•­}¥¹Ù…É¥…¹ÑÌ¡Í•±˜¤€´ø9½¹”è(€€€€€€€É•Ñ…¥¹•‘}½É¥¥¹Ì€ôì(€€€€€€€€€€€•Ù•¹Ð¹•Ð ‰ÍÑ…­}½‰©•Ñ}¥ˆ¤è•Ù•¹Ð(€€€€€€€€€€€™½È•Ù•¹Ð¥¸Í•±˜¹•Ù•¹ÑÌ(€€€€€€€€€€€¥˜•Ù•¹Ñl‰•Ù•¹Ð‰t€ôô€‰‘…µ…•}Ñ½}Í•±™}µ…¹…}É•Í½±Ù•ˆ(€€€€€€€ô(€€€€€€€™½ÈÁ±…å•É}¥¹‘•à¥¸É…¹”¡±•¸¡Í•±˜¹Á±…å•ÉÌ¤¤è(€€€€€€€€€€€ÁÉ½‘ÕÑ¥½¹Ì€ôÍ•±˜¹™±½…Ñ¥¹}µ…¹„¹ÁÉ½‘ÕÑ¥½¹Ì¡Á±…å•É}¥¹‘•à¤(€€€€€€€€€€€½¹ÍÕµÁÑ¥½¹Ì€ôÍ•±˜¹™±½…Ñ¥¹}µ…¹„¹½¹ÍÕµÁÑ¥½¹Ì¡Á±…å•É}¥¹‘•à¤(€€€€€€€€€€€¥˜±•¸¡íÕ¹¥Ð¹•Ù•¹Ñ}¥™½ÈÕ¹¥Ð¥¸ÁÉ½‘ÕÑ¥½¹Íô¤€„ô±•¸¡ÁÉ½‘ÕÑ¥½¹Ì¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰™±½…Ñ¥¹œµ…¹„ÁÉ½‘ÕÑ¥½¸%Ì…É”¹½ÐÕ¹¥ÅÕ”ˆ¤(€€€€€€€€€€€ÕÍ•‘}‰å}¥è‘¥ÑmÍÑÈ°¥¹Ñt€ôíô(€€€€€€€€€€€™½È¥Ñ•´¥¸½¹ÍÕµÁÑ¥½¹Ìè(€€€€€€€€€€€€€€€ÕÍ•‘}‰å}¥‘m¥Ñ•´¹Í½ÕÉ•}•Ù•¹Ñ}¥‘t€ô€ (€€€€€€€€€€€€€€€€€€€ÕÍ•‘}‰å}¥¹•Ð¡¥Ñ•´¹Í½ÕÉ•}•Ù•¹Ñ}¥°€À¤€¬¥Ñ•´¹ÅÕ…¹Ñ¥Ñä(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€¥˜Í•Ð¡ÕÍ•‘}‰å}¥¤€´íÕ¹¥Ð¹•Ù•¹Ñ}¥™½ÈÕ¹¥Ð¥¸ÁÉ½‘ÕÑ¥½¹Íôè(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰™±½…Ñ¥¹œµ…¹„½¹ÍÕµÁÑ¥½¸±…­Ì„ÁÉ½‘ÕÑ¥½¸ˆ¤(€€€€€€€€€€€‰…±…¹”è‘¥ÑmÍÑÈ°¥¹Ñt€ôíô(€€€€€€€€€€€™½ÈÕ¹¥Ð¥¸ÁÉ½‘ÕÑ¥½¹Ìè(€€€€€€€€€€€€€€€ÕÍ•€ôÕÍ•‘}‰å}¥¹•Ð¡Õ¹¥Ð¹•Ù•¹Ñ}¥°€À¤(€€€€€€€€€€€€€€€¥˜ÕÍ•€øÕ¹¥Ð¹ÅÕ…¹Ñ¥Ñä½ÈÕÍ•€ð€Àè(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰™±½…Ñ¥¹œµ…¹„½¹ÍÕµÁÑ¥½¸•á••‘ÌÁÉ½‘ÕÑ¥½¸ˆ¤(€€€€€€€€€€€€€€€¥˜Õ¹¥Ð¹ÅÕ…¹Ñ¥Ñä€øÕÍ•è(€€€€€€€€€€€€€€€€€€€‰…±…¹•mÕ¹¥Ð¹½±½Ét€ô‰…±…¹”¹•Ð¡Õ¹¥Ð¹½±½È°€À¤€¬Õ¹¥Ð¹ÅÕ…¹Ñ¥Ñä€´ÕÍ•(€€€€€€€€€€€€€€€¥˜Õ¹¥Ð¹Á•ÉÍ¥ÍÑÍ}Õ¹Ñ¥±}ÑÕÉ¹}•¹è(€€€€€€€€€€€€€€€€€€€½É¥¥¸€ôÉ•Ñ…¥¹•‘}½É¥¥¹Ì¹•Ð¡Õ¹¥Ð¹•Ù•¹Ñ}¥¤(€€€€€€€€€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€€€€€€€€€½É¥¥¸¥Ì9½¹”(€€€€€€€€€€€€€€€€€€€€€€€½È½É¥¥¸¹•Ð ‰Í½ÕÉ•}¥ˆ¤€„ôÕ¹¥Ð¹Í½ÕÉ•}¥(€€€€€€€€€€€€€€€€€€€€€€€½È½É¥¥¸¹•Ð ‰½¹ÑÉ½±±•Èˆ¤€„ôÁ±…å•É}¥¹‘•à(€€€€€€€€€€€€€€€€€€€€€€€½È½É¥¥¸¹•Ð ‰ÅÕ…¹Ñ¥Ñäˆ¤€„ôÕ¹¥Ð¹ÅÕ…¹Ñ¥Ñä(€€€€€€€€€€€€€€€€€€€€€€€½È½É¥¥¸¹•Ð ‰½±½Èˆ¤€„ôÕ¹¥Ð¹½±½È(€€€€€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰É•Ñ…¥¹•µ…¹„±…­ÌÍ½ÕÉ”ÑÉ¥•ÈÁÉ½Ù•¹…¹”ˆ¤(€€€€€€€€€€€¥˜Í•±˜¹™±½…Ñ¥¹}µ…¹„¹Í¹…ÁÍ¡½Ð¡Á±…å•É}¥¹‘•à¤€„ô‘¥Ð¡Í½ÉÑ•¡‰…±…¹”¹¥Ñ•µÌ ¤¤¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰™±½…Ñ¥¹œµ…¹„Á½½°‘¥™™•ÉÌ™É½´¥¹‘¥Ù¥‘Õ…°Õ¹¥ÑÌˆ¤(€€€€€€€‘•Á…ÉÑÕÉ•Ì€ôl(€€€€€€€€€€€€¡¥¹‘•à°¥Ñ•´¤(€€€€€€€€€€€™½È¥¹‘•à°¥Ñ•´¥¸•¹Õµ•É…Ñ”¡Í•±˜¹•Ù•¹ÑÌ¤(€€€€€€€€€€€¥˜¥Ñ•µl‰•Ù•¹Ð‰t€ôô€‰Á•Éµ…¹•¹Ñ}‘•Á…ÉÑ•ˆ(€€€€€€€t(€€€€€€€™½È¥¹‘•à°¥Ñ•´¥¸‘•Á…ÉÑÕÉ•Ìè(€€€€€€€€€€€Í½ÕÉ”€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡¥Ñ•µl‰Í½ÕÉ•}½‰©•Ñ}¥‰t¤(€€€€€€€€€€€ÁÉ••‘¥¹œ€ôÍ•±˜¹•Ù•¹ÑÍm¥¹‘•à€´€Åt¥˜¥¹‘•à•±Í”íô(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€¹½Ð¥Í¥¹ÍÑ…¹”¡Í½ÕÉ”°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€½ÈÍ½ÕÉ”¹é½¹”€„ô€‰™½Éµ•Èˆ(€€€€€€€€€€€€€€€½ÈÍ½ÕÉ”¹½¹ÑÉ½±±•È€„ô¥Ñ•µl‰½¹ÑÉ½±±•È‰t(€€€€€€€€€€€€€€€½ÈÍ½ÕÉ”¹ÑåÁ•}±¥¹”€„ô¥Ñ•µl‰ÑåÁ•}±¥¹”‰t(€€€€€€€€€€€€€€€½ÈÁÉ••‘¥¹œ¹•Ð ‰•Ù•¹Ðˆ¤€„ô€‰é½¹•}¡…¹•ˆ(€€€€€€€€€€€€€€€½ÈÁÉ••‘¥¹œ¹•Ð ‰Í½ÕÉ•}½‰©•Ñ}¥ˆ¤€„ô¥Ñ•µl‰Í½ÕÉ•}½‰©•Ñ}¥‰t(€€€€€€€€€€€€€€€½ÈÁÉ••‘¥¹œ¹•Ð ‰‘•ÍÑ¥¹…Ñ¥½¹}½‰©•Ñ}¥ˆ¤€„ô¥Ñ•µl‰‘•ÍÑ¥¹…Ñ¥½¹}½‰©•Ñ}¥‰t(€€€€€€€€€€€€€€€½ÈÁÉ••‘¥¹œ¹•Ð ‰Í½ÕÉ•}é½¹”ˆ¤€„ô€‰‰…ÑÑ±•™¥•±ˆ(€€€€€€€€€€€€€€€½ÈÁÉ••‘¥¹œ¹•Ð ‰‘•ÍÑ¥¹…Ñ¥½¹}é½¹”ˆ¤€ôô€‰‰…ÑÑ±•™¥•±ˆ(€€€€€€€€€€€€€€€½ÈÁÉ••‘¥¹œ¹•Ð ‰ÑÕÉ¸ˆ¤€„ô¥Ñ•µl‰ÑÕÉ¸‰t(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰‘•Á…ÉÑÕÉ”¡¥ÍÑ½Éä±…­Ìé½¹”…¹½¹ÑÉ½±±•ÈÁÉ½Ù•¹…¹”ˆ¤(€€€€€€€±¥¹­•‘}É…¹ÑÌ€ômÉ…¹Ð™½ÈÉ…¹ÑÌ¥¸Í•±˜¹}±¥¹­•‘}Á±…å}É…¹ÑÌ¹Ù…±Õ•Ì ¤™½ÈÉ…¹Ð¥¸É…¹ÑÍt(€€€€€€€¥˜±•¸¡íÉ…¹Ð¹É…¹Ñ}¥™½ÈÉ…¹Ð¥¸±¥¹­•‘}É…¹ÑÍô¤€„ô±•¸¡±¥¹­•‘}É…¹ÑÌ¤½È…¹ä (€€€€€€€€€€€É…¹Ð¹Í½ÕÉ•}¥€„ôÍ½ÕÉ•}¥(€€€€€€€€€€€½ÈÍ½ÕÉ•}¥¹½Ð¥¸Í•±˜¹}½‰©•ÑÌ(€€€€€€€€€€€½ÈÉ…¹Ð¹½¹ÑÉ½±±•È¹½Ð¥¸É…¹” È¤(€€€€€€€€€€€½ÈÉ…¹Ð¹•áÁ¥É•Í}ÑÕÉ¸€øÍ•±˜¹ÑÕÉ¸(€€€€€€€€€€€½ÈÉ…¹Ð¹É•µ…¥¹¥¹}Á±…åÌ¹½Ð¥¸ìÀ°€Åô(€€€€€€€€€€€™½ÈÍ½ÕÉ•}¥°É…¹ÑÌ¥¸Í•±˜¹}±¥¹­•‘}Á±…å}É…¹ÑÌ¹¥Ñ•µÌ ¤(€€€€€€€€€€€™½ÈÉ…¹Ð¥¸É…¹ÑÌ(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰±¥¹­•Á±…äÉ…¹ÐÁÉ½Ù•¹…¹”½È½¹ÍÕµÁÑ¥½¸¥Ìµ…±™½Éµ•ˆ¤(€€€€€€€ÑÉäè(€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}ÍÑÕ¹}¡¥ÍÑ½Éä ¤(€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€½µ‰…Ñ}¥‘Ì€ôÍ•±˜¹}½µ‰…Ñ}…ÑÑ…­•ÉÌ€¬ÑÕÁ±” (€€€€€€€€€€€‰±½­•É}¥™½È}…ÑÑ…­•É}¥°‰±½­•É}¥¥¸Í•±˜¹}½µ‰…Ñ}‰±½­Ì(€€€€€€€€¤(€€€€€€€•Ù¥‘•¹•}¥‘Ì€ôm¥Ñ•´¹•Ù•¹Ñ}¥™½È¥Ñ•´¥¸Í•±˜¹}ÉÕ±•Í}•Ù•¹Ñ}•Ù¥‘•¹•t(€€€€€€€¥˜€ (€€€€€€€€€€€±•¸¡•Ù¥‘•¹•}¥‘Ì¤€„ô±•¸¡Í•Ð¡•Ù¥‘•¹•}¥‘Ì¤¤(€€€€€€€€€€€½ÈÍ•Ð¡•Ù¥‘•¹•}¥‘Ì¤€„ôÍ•Ð¡Í•±˜¹}ÉÕ±•Í}•Ù•¹ÑÌ¤(€€€€€€€€€€€½Èm¥Ñ•´¹•Ù•¹Ñ}ÕÉÍ½È™½È¥Ñ•´¥¸Í•±˜¹}ÉÕ±•Í}•Ù•¹Ñ}•Ù¥‘•¹•t(€€€€€€€€€€€€„ô±¥ÍÐ¡É…¹” Ä°±•¸¡Í•±˜¹}ÉÕ±•Í}•Ù•¹Ñ}•Ù¥‘•¹”¤€¬€Ä¤¤(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÉÕ±•Ìµ•Ù•¹Ð•Ù¥‘•¹”±•‘•È¥Ì¥¹½µÁ±•Ñ”½È‘ÕÁ±¥…Ñ•ˆ¤(€€€€€€€™½È•Ù•¹Ð¥¸Í•±˜¹}ÉÕ±•Í}•Ù•¹ÑÌ¹Ù…±Õ•Ì ¤è(€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€Í•±˜¹}…ÕÑ¡•¹Ñ¥…Ñ•}½É¥¥¹…±}ÉÕ±•Í}•Ù•¹Ð¡•Ù•¹Ð¤(€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€½ÕÉÉ•¹•}‰å}¥€ôí¥Ñ•´¹½ÕÉÉ•¹•}¥è¥Ñ•´™½È¥Ñ•´¥¸Í•±˜¹Í•µ…¹Ñ¥}½ÕÉÉ•¹•Íô(€€€€€€€¥˜±•¸¡½ÕÉÉ•¹•}‰å}¥¤€„ô±•¸¡Í•±˜¹Í•µ…¹Ñ¥}½ÕÉÉ•¹•Ì¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰Í•µ…¹Ñ¥Œ½ÕÉÉ•¹”%ÌµÕÍÐ‰”Õ¹¥ÅÕ”ˆ¤(€€€€€€€¥˜±•¸¡í¥Ñ•´¹½ÁÁ½ÉÑÕ¹¥Ñå}­•ä™½È¥Ñ•´¥¸Í•±˜¹½ÁÁ½ÉÑÕ¹¥Ñå}Ý¥Ñ¹•ÍÍ•Íô¤€„ô±•¸ (€€€€€€€€€€€Í•±˜¹½ÁÁ½ÉÑÕ¹¥Ñå}Ý¥Ñ¹•ÍÍ•Ì(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½ÁÁ½ÉÑÕ¹¥ÑäÝ¥Ñ¹•ÍÍ•ÌµÕÍÐ‰”‘•Ñ•Éµ¥¹¥ÍÑ¥…±±ä‘•‘ÕÁ±¥…Ñ•ˆ¤(€€€€€€€½¹Ñ•áÑ}‰å}¥€ôí¥Ñ•´¹½¹Ñ•áÑ}¥è¥Ñ•´™½È¥Ñ•´¥¸Í•±˜¹½ÁÁ½ÉÑÕ¹¥Ñå}½¹Ñ•áÑÍô(€€€€€€€¥˜±•¸¡½¹Ñ•áÑ}‰å}¥¤€„ô±•¸¡Í•±˜¹½ÁÁ½ÉÑÕ¹¥Ñå}½¹Ñ•áÑÌ¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½ÁÁ½ÉÑÕ¹¥Ñä½¹Ñ•áÐ%ÌµÕÍÐ‰”Õ¹¥ÅÕ”ˆ¤(€€€€€€€™½È½¹Ñ•áÐ¥¸Í•±˜¹½ÁÁ½ÉÑÕ¹¥Ñå}½¹Ñ•áÑÌè(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€½¹Ñ•áÐ¹Í½ÕÉ•}¥¹½Ð¥¸Í•±˜¹}½‰©•ÑÌ(€€€€€€€€€€€€€€€½È…¹ä¡ÍÕ‰©•Ñ}¥¹½Ð¥¸Í•±˜¹}½‰©•ÑÌ™½ÈÍÕ‰©•Ñ}¥¥¸½¹Ñ•áÐ¹ÍÕ‰©•Ñ}¥‘Ì¤(€€€€€€€€€€€€€€€½È±•¸¡½¹Ñ•áÐ¹ÍÕ‰©•Ñ}¥‘Ì¤€„ô±•¸¡½¹Ñ•áÐ¹ÍÕ‰©•Ñ}é½¹•Ì¤(€€€€€€€€€€€€€€€½È½¹Ñ•áÐ¹½¹ÑÉ½±±•È¹½Ð¥¸É…¹” È¤(€€€€€€€€€€€€€€€½È¹½ÐÉ”¹™Õ±±µ…Ñ ¡È‰lÀ´å„µ™uìØÑôˆ°½¹Ñ•áÐ¹ÍÑ…Ñ•}™¥¹•ÉÁÉ¥¹Ð¤(€€€€€€€€€€€€€€€½È½¹Ñ•áÐ¹½¹Ñ•áÑ}­•ä(€€€€€€€€€€€€€€€€„ô½ÁÁ½ÉÑÕ¹¥Ñå}½¹Ñ•áÑ}­•ä (€€€€€€€€€€€€€€€€€€€½¹Ñ•áÐ¹½¹Ñ•áÑ}¥°(€€€€€€€€€€€€€€€€€€€½¹Ñ•áÐ¹½¹Ñ•áÑ}­¥¹°(€€€€€€€€€€€€€€€€€€€½¹Ñ•áÐ¹ÑÕÉ¸°(€€€€€€€€€€€€€€€€€€€½¹Ñ•áÐ¹Á¡…Í”°(€€€€€€€€€€€€€€€€€€€½¹Ñ•áÐ¹ÍÑ•À°(€€€€€€€€€€€€€€€€€€€½¹Ñ•áÐ¹…Ñ¥Ù•}Á±…å•È°(€€€€€€€€€€€€€€€€€€€½¹Ñ•áÐ¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€½¹Ñ•áÐ¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€½¹Ñ•áÐ¹ÍÕ‰©•Ñ}¥‘Ì°(€€€€€€€€€€€€€€€€€€€½¹Ñ•áÐ¹ÍÕ‰©•Ñ}é½¹•Ì°(€€€€€€€€€€€€€€€€€€€½¹Ñ•áÐ¹™…ÑÌ°(€€€€€€€€€€€€€€€€€€€½¹Ñ•áÐ¹•Ù•¹Ñ}¥°(€€€€€€€€€€€€€€€€€€€½¹Ñ•áÐ¹ÍÑ…­}½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€½¹Ñ•áÐ¹ÍÑ…Ñ•}™¥¹•ÉÁÉ¥¹Ð°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½ÁÁ½ÉÑÕ¹¥Ñä½¹Ñ•áÐÁÉ½Ù•¹…¹”¥Ìµ…±™½Éµ•ˆ¤(€€€€€€€€€€€¥˜½¹Ñ•áÐ¹•Ù•¹Ñ}¥¥Ì¹½Ð9½¹”…¹½¹Ñ•áÐ¹•Ù•¹Ñ}¥¹½Ð¥¸Í•±˜¹}ÉÕ±•Í}•Ù•¹ÑÌè(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½ÁÁ½ÉÑÕ¹¥Ñä½¹Ñ•áÐ•Ù•¹ÐÁÉ½Ù•¹…¹”¥Ìµ¥ÍÍ¥¹œˆ¤(€€€€€€€€€€€¥˜½¹Ñ•áÐ¹ÍÑ…­}½‰©•Ñ}¥¥Ì¹½Ð9½¹”…¹½¹Ñ•áÐ¹ÍÑ…­}½‰©•Ñ}¥¹½Ð¥¸Í•±˜¹}½‰©•ÑÌè(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½ÁÁ½ÉÑÕ¹¥Ñä½¹Ñ•áÐMÑ…¬ÁÉ½Ù•¹…¹”¥Ìµ¥ÍÍ¥¹œˆ¤(€€€€€€€™½È½ÕÉÉ•¹”¥¸Í•±˜¹Í•µ…¹Ñ¥}½ÕÉÉ•¹•Ìè(€€€€€€€€€€€Í½ÕÉ”€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡½ÕÉÉ•¹”¹½‰©•Ñ}¥¤(€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡Í½ÕÉ”°€¡…É‘=‰©•Ð°A•Éµ…¹•¹Ð¤¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰Í•µ…¹Ñ¥Œ½ÕÉÉ•¹”É•™•É•¹•Ì„¹½¹•á¥ÍÑ•¹Ð½‰©•Ðˆ¤(€€€€€€€€€€€™É…µ•¹ÑÌ€ôÍ•±˜¹}Í•µ…¹Ñ¥}™É…µ•¹ÑÌ¡Í½ÕÉ”¹…É¤(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€½ÕÉÉ•¹”¹™É…µ•¹Ñ}¥¹‘•à€øô±•¸¡™É…µ•¹ÑÌ¤(€€€€€€€€€€€€€€€½È™É…µ•¹ÑÍm½ÕÉÉ•¹”¹™É…µ•¹Ñ}¥¹‘•át€„ô½ÕÉÉ•¹”¹½É…±•}™É…µ•¹Ð(€€€€€€€€€€€€€€€½È™É…µ•¹Ñ}‘¥•ÍÐ¡½ÕÉÉ•¹”¹½É…±•}™É…µ•¹Ð¤€„ô½ÕÉÉ•¹”¹™É…µ•¹Ñ}¡…Í (€€€€€€€€€€€€€€€½ÈÍ•µ…¹Ñ¥}­•ä (€€€€€€€€€€€€€€€€€€€•Ñ…ÑÑÈ¡Í½ÕÉ”¹…É°€‰½É…±•}¥ˆ°€ˆˆ¤°(€€€€€€€€€€€€€€€€€€€½ÕÉÉ•¹”¹™…•}¥¹‘•à°(€€€€€€€€€€€€€€€€€€€½ÕÉÉ•¹”¹™É…µ•¹Ñ}¥¹‘•à°(€€€€€€€€€€€€€€€€€€€½ÕÉÉ•¹”¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€„ô½ÕÉÉ•¹”¹Í•µ…¹Ñ¥}­•ä(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰Í•µ…¹Ñ¥Œ½ÕÉÉ•¹”µ¥Íµ…Ñ¡•Ì…ÕÑ¡½É¥Ñ…Ñ¥Ù”=É…±”‘…Ñ„ˆ¤(€€€€€€€™½ÈÝ¥Ñ¹•ÍÌ¥¸Í•±˜¹½ÁÁ½ÉÑÕ¹¥Ñå}Ý¥Ñ¹•ÍÍ•Ìè(€€€€€€€€€€€½ÕÉÉ•¹”€ô½ÕÉÉ•¹•}‰å}¥¹•Ð¡Ý¥Ñ¹•ÍÌ¹½ÕÉÉ•¹•}¥¤(€€€€€€€€€€€¥˜½ÕÉÉ•¹”¥Ì9½¹”½È€ (€€€€€€€€€€€€€€€Ý¥Ñ¹•ÍÌ¹Í•µ…¹Ñ¥}­•ä€„ô½ÕÉÉ•¹”¹Í•µ…¹Ñ¥}­•ä(€€€€€€€€€€€€€€€½ÈÝ¥Ñ¹•ÍÌ¹½‰©•Ñ}¥€„ô½ÕÉÉ•¹”¹½‰©•Ñ}¥(€€€€€€€€€€€€€€€½ÈÝ¥Ñ¹•ÍÌ¹½É…±•}™É…µ•¹Ð€„ô½ÕÉÉ•¹”¹½É…±•}™É…µ•¹Ð(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½ÁÁ½ÉÑÕ¹¥ÑäÝ¥Ñ¹•ÍÌµ¥Íµ…Ñ¡•ÌÍ•µ…¹Ñ¥ŒÁÉ•Í•¹”ˆ¤(€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€™…ÑÌ€ôÍ•±˜¹}Ù…±¥‘…Ñ•}½ÁÁ½ÉÑÕ¹¥Ñå}…ÁÁ±¥…‰¥±¥Ñä (€€€€€€€€€€€€€€€€€€€½ÕÉÉ•¹”°(€€€€€€€€€€€€€€€€€€€…ÕÍ•}­¥¹õÝ¥Ñ¹•ÍÌ¹…ÕÍ•}­¥¹°(€€€€€€€€€€€€€€€€€€€…ÕÍ•}¥õÝ¥Ñ¹•ÍÌ¹…ÕÍ•}¥°(€€€€€€€€€€€€€€€€€€€…ÕÍ•}ÍÕ‰©•Ñ}¥‘ÌõÝ¥Ñ¹•ÍÌ¹…ÕÍ•}ÍÕ‰©•Ñ}¥‘Ì°(€€€€€€€€€€€€€€€€€€€¡¥ÍÑ½É¥…°õÝ¥Ñ¹•ÍÌ°(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€¥˜™…ÑÌ€„ô€ (€€€€€€€€€€€€€€€Ý¥Ñ¹•ÍÌ¹Í½ÕÉ•}é½¹”°(€€€€€€€€€€€€€€€Ý¥Ñ¹•ÍÌ¹Í½ÕÉ•}½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€Ý¥Ñ¹•ÍÌ¹…ÕÍ•}ÍÕ‰©•Ñ}é½¹•Ì°(€€€€€€€€€€€€€€€Ý¥Ñ¹•ÍÌ¹…ÕÍ•}•Ù•¹Ñ}­¥¹°(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½ÁÁ½ÉÑÕ¹¥ÑäÝ¥Ñ¹•ÍÌ…ÁÁ±¥…‰¥±¥Ñä™…ÑÌ…É”¥¹½¹Í¥ÍÑ•¹Ðˆ¤(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€Ý¥Ñ¹•ÍÌ¹…ÕÍ•}­¥¹€ôô€‰…ÕÑ¡½É¥Ñ…Ñ¥Ù•}½¹Ñ•áÐˆ(€€€€€€€€€€€€€€€…¹Ý¥Ñ¹•ÍÌ¹…ÕÍ•}¥¹½Ð¥¸½¹Ñ•áÑ}‰å}¥(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½ÁÁ½ÉÑÕ¹¥ÑäÝ¥Ñ¹•ÍÌ½¹Ñ•áÐÁÉ½Ù•¹…¹”¥Ìµ¥ÍÍ¥¹œˆ¤(€€€€€€€¥˜±•¸¡Í•Ð¡Í•±˜¹}½µ‰…Ñ}…ÑÑ…­•ÉÌ¤¤€„ô±•¸¡Í•±˜¹}½µ‰…Ñ}…ÑÑ…­•ÉÌ¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½µ‰…ÐÍÑ…Ñ”½¹Ñ…¥¹Ì‘ÕÁ±¥…Ñ”…ÑÑ…­•ÉÌˆ¤(€€€€€€€¥˜±•¸¡í‰±½­•É}¥™½È}…ÑÑ…­•É}¥°‰±½­•É}¥¥¸Í•±˜¹}½µ‰…Ñ}‰±½­Íô¤€„ô±•¸ (€€€€€€€€€€€Í•±˜¹}½µ‰…Ñ}‰±½­Ì(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½µ‰…ÐÍÑ…Ñ”½¹Ñ…¥¹Ì‘ÕÁ±¥…Ñ”‰±½­•ÉÌˆ¤(€€€€€€€¥˜…¹ä¡½‰©•Ñ}¥¹½Ð¥¸½µ‰…Ñ}¥‘Ì™½È½‰©•Ñ}¥¥¸Í•±˜¹}™¥ÉÍÑ}‘…µ…•}ÅÕ…±¥™¥•‘}¥‘Ì¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰™¥ÉÍÐµÍÑÉ¥­”ÅÕ…±¥™¥…Ñ¥½¸É•™•É•¹•Ì„¹½¹½µ‰…Ñ…¹Ðˆ¤(€€€€€€€¥˜…¹ä¡½‰©•Ñ}¥¹½Ð¥¸½µ‰…Ñ}¥‘Ì™½È½‰©•Ñ}¥¥¸Í•±˜¹}É•Õ±…É}‘…µ…•}¥¹¥Ñ¥…±}¥‘Ì¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰É•Õ±…ÈµÍÑ•ÀÅÕ…±¥™¥…Ñ¥½¸É•™•É•¹•Ì„¹½¹½µ‰…Ñ…¹Ðˆ¤(€€€€€€€¥˜…¹ä (€€€€€€€€€€€±•¸ (€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€¡…ÍÍ¥¹µ•¹Ð¹Í½ÕÉ•}¥°…ÍÍ¥¹µ•¹Ð¹Ñ…É•Ñ}¥°…ÍÍ¥¹µ•¹Ð¹Ñ…É•Ñ}Á±…å•È¤(€€€€€€€€€€€€€€€€€€€™½È…ÍÍ¥¹µ•¹Ð¥¸•Ù¥‘•¹”¹…ÍÍ¥¹µ•¹ÑÌ(€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€¤(€€€€€€€€€€€€„ô±•¸¡•Ù¥‘•¹”¹…ÍÍ¥¹µ•¹ÑÌ¤(€€€€€€€€€€€™½È•Ù¥‘•¹”¥¸Í•±˜¹½µ‰…Ñ}‘…µ…•}•Ù¥‘•¹”(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½µ‰…Ñ…¹ÐÉ•Á•…Ñ•½¹”…ÍÍ¥¹µ•¹Ð¥¸„‘…µ…”ÍÑ•Àˆ¤(€€€€€€€¥˜…¹ä (€€€€€€€€€€€…ÍÍ¥¹µ•¹Ð¹…µ½Õ¹Ð€ðô€À(€€€€€€€€€€€™½È•Ù¥‘•¹”¥¸Í•±˜¹½µ‰…Ñ}‘…µ…•}•Ù¥‘•¹”(€€€€€€€€€€€™½È…ÍÍ¥¹µ•¹Ð¥¸•Ù¥‘•¹”¹…ÍÍ¥¹µ•¹ÑÌ(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½µ‰…Ð•Ù¥‘•¹”½¹Ñ…¥¹Ì„¹½¹Á½Í¥Ñ¥Ù”‘…µ…”…ÍÍ¥¹µ•¹Ðˆ¤(€€€€€€€™½È•Ù¥‘•¹”¥¸Í•±˜¹½µ‰…Ñ}‘…µ…•}•Ù¥‘•¹”è(€€€€€€€€€€€™½ÈÉ•ÍÕ±Ð¥¸•Ù¥‘•¹”¹ÑÉ…µÁ±•}É•ÍÕ±ÑÌè(€€€€€€€€€€€€€€€¥˜É•ÍÕ±Ð¹‘…µ…•}ÍÑ•À¥Ì¹½Ð•Ù¥‘•¹”¹­¥¹½ÈÉ•ÍÕ±Ð¹…ÑÑ…­•É}Á½Ý•È€ðô€Àè(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰QÉ…µÁ±”•Ù¥‘•¹”¡…Ì¥¹Ù…±¥ÍÑ•À½ÈÁ½Ý•Èˆ¤(€€€€€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€€€€€É•ÍÕ±Ð¹‰±½­•É}‘…µ…•}…ÍÍ¥¹•€¬É•ÍÕ±Ð¹Á±…å•É}‘…µ…•}…ÍÍ¥¹•(€€€€€€€€€€€€€€€€€€€€„ôÉ•ÍÕ±Ð¹…ÑÑ…­•É}Á½Ý•È(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰QÉ…µÁ±”•Ù¥‘•¹”‘½•Ì¹½Ð½¹Í•ÉÙ”…ÍÍ¥¹•‘…µ…”ˆ¤(€€€€€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€€€€€É•ÍÕ±Ð¹‘•™•¹‘¥¹}±¥™•}‰•™½É”€´É•ÍÕ±Ð¹Á±…å•É}‘…µ…•}…ÍÍ¥¹•(€€€€€€€€€€€€€€€€€€€€„ôÉ•ÍÕ±Ð¹‘•™•¹‘¥¹}±¥™•}…™Ñ•È(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰QÉ…µÁ±”•Ù¥‘•¹”±¥™”É•ÍÕ±Ð¥Ì¥¹½¹Í¥ÍÑ•¹Ðˆ¤(€€€€€€€€€€€€€€€¥˜É•ÍÕ±Ð¹‰±½­•É}Ñ½Õ¡¹•ÍÌ¥Ì¹½Ð9½¹”…¹€ (€€€€€€€€€€€€€€€€€€€É•ÍÕ±Ð¹‰±½­•É}µ…É­•‘}‘…µ…•}‰•™½É”¥Ì9½¹”(€€€€€€€€€€€€€€€€€€€½ÈÉ•ÍÕ±Ð¹±•Ñ¡…±}É•ÅÕ¥É•(€€€€€€€€€€€€€€€€€€€€„ôµ¥¸ (€€€€€€€€€€€€€€€€€€€€€€€µ…à À°É•ÍÕ±Ð¹‰±½­•É}Ñ½Õ¡¹•ÍÌ€´É•ÍÕ±Ð¹‰±½­•É}µ…É­•‘}‘…µ…•}‰•™½É”¤°(€€€€€€€€€€€€€€€€€€€€€€€€Ä¥˜É•ÍÕ±Ð¹Í½ÕÉ•}‘•…Ñ¡Ñ½Õ •±Í”É•ÍÕ±Ð¹‰±½­•É}Ñ½Õ¡¹•ÍÌ°(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰QÉ…µÁ±”•Ù¥‘•¹”±•Ñ¡…°…±Õ±…Ñ¥½¸¥Ì¥¹½¹Í¥ÍÑ•¹Ðˆ¤(€€€€€€€€€€€€€€€¥˜É•ÍÕ±Ð¹‰±½­•É}ÍÕÉÙ¥Ù•€„ô€¡É•ÍÕ±Ð¹‰±½­•É}µ…É­•‘}‘…µ…•}…™Ñ•È¥Ì¹½Ð9½¹”¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰QÉ…µÁ±”•Ù¥‘•¹”‰±½­•ÈÉ•ÍÕ±Ð¥Ì¥¹½¹Í¥ÍÑ•¹Ðˆ¤(€€€€€€€¥˜…¹ä (€€€€€€€€€€€Á•Éµ…¹•¹Ð¹‘•…Ñ¡Ñ½Õ¡}‘…µ…”…¹Á•Éµ…¹•¹Ð¹‘…µ…”€ðô€À(€€€€€€€€€€€™½ÈÁ±…å•È¥¸Í•±˜¹Á±…å•ÉÌ(€€€€€€€€€€€™½ÈÁ•Éµ…¹•¹Ð¥¸Á±…å•È¹‰…ÑÑ±•™¥•±(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰•…Ñ¡Ñ½Õ µ…É­•ÈÉ•ÅÕ¥É•ÌÁ½Í¥Ñ¥Ù”‘…µ…”ˆ¤(€€€€€€€¥˜±•¸¡í¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥™½È¥Ñ•´¥¸Í•±˜¹•Ñ‰}‘É…¥¹}…¥¹}ÍÉå}•Ù¥‘•¹•ô¤€„ô±•¸ (€€€€€€€€€€€Í•±˜¹•Ñ‰}‘É…¥¹}…¥¹}ÍÉå}•Ù¥‘•¹”(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰Q‘É…¥¸½…¥¸½MÉä•Ù¥‘•¹”ÍÑ…¬%ÌµÕÍÐ‰”Õ¹¥ÅÕ”ˆ¤(€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹•Ñ‰}‘É…¥¹}…¥¹}ÍÉå}•Ù¥‘•¹”è(€€€€€€€€€€€…‰¥±¥Ñä€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥¤(€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡…‰¥±¥Ñä°QÉ¥•É•‘‰¥±¥Ñå=‰©•Ð¤½È…‰¥±¥Ñä¹é½¹”€„ô€‰™½Éµ•Èˆè(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰Q‘É…¥¸½…¥¸½MÉä•Ù¥‘•¹”±…­ÌÉ•Í½±Ù•MÑ…¬…ÕÑ¡½É¥Ñäˆ¤(€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}•Ñ‰}‘É…¥¹}…¥¹}ÍÉå}ÑÉ¥•È¡…‰¥±¥Ñä¤(€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€¥Ñ•´¹•Ù•¹Ñ}¥€„ô…‰¥±¥Ñä¹•Ù•¹Ð¹•Ù•¹Ñ}¥(€€€€€€€€€€€€€€€½È¥Ñ•´¹Í½ÕÉ•}¥€„ô…‰¥±¥Ñä¹Í½ÕÉ•}¥(€€€€€€€€€€€€€€€½È¥Ñ•´¹Í½ÕÉ•}…É€„ô…‰¥±¥Ñä¹Í½ÕÉ•}…É¹¹…µ”(€€€€€€€€€€€€€€€½È¥Ñ•´¹½¹ÑÉ½±±•È€„ô…‰¥±¥Ñä¹½¹ÑÉ½±±•È(€€€€€€€€€€€€€€€½È¥Ñ•´¹½ÁÁ½¹•¹Ð€„ô€Ä€´¥Ñ•´¹½¹ÑÉ½±±•È(€€€€€€€€€€€€€€€½È¥Ñ•´¹½É…±•}™É…µ•¹Ð€„ô…‰¥±¥Ñä¹½É…±•}™É…µ•¹Ð(€€€€€€€€€€€€€€€½È¥Ñ•´¹ÑÕÉ¸€„ô…‰¥±¥Ñä¹•Ù•¹Ð¹ÑÕÉ¸(€€€€€€€€€€€€€€€½È¥Ñ•´¹ÍÑ•À€„ô…‰¥±¥Ñä¹•Ù•¹Ð¹ÍÑ•À(€€€€€€€€€€€€€€€½È¥Ñ•´¹½ÁÁ½¹•¹Ñ}±¥™•}…™Ñ•È€„ô¥Ñ•´¹½ÁÁ½¹•¹Ñ}±¥™•}‰•™½É”€´€Ä(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰Q‘É…¥¸½…¥¸½MÉä•Ù¥‘•¹”ÁÉ½Ù•¹…¹”¥Ì¥¹½¹Í¥ÍÑ•¹Ðˆ¤(€€€€€€€€€€€¥˜¥Ñ•´¹Ñ•Éµ¥¹…±}…™Ñ•É}±¥™•}±½ÍÌè(€€€€€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€€€€€¥Ñ•´¹½ÁÁ½¹•¹Ñ}±¥™•}…™Ñ•È€ø€À(€€€€€€€€€€€€€€€€€€€½È¥Ñ•´¹½¹ÑÉ½±±•É}±¥™•}…™Ñ•È€„ô¥Ñ•´¹½¹ÑÉ½±±•É}±¥™•}‰•™½É”(€€€€€€€€€€€€€€€€€€€½È¥Ñ•´¹ÍÉå}•Ù•¹Ñ}¥¥Ì¹½Ð9½¹”(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰Ñ•Éµ¥¹…°Q‘É…¥¸½…¥¸½MÉä•Ù¥‘•¹”¥Ì¥¹½¹Í¥ÍÑ•¹Ðˆ¤(€€€€€€€€€€€•±Í”è(€€€€€€€€€€€€€€€µ…Ñ¡¥¹}ÍÉä€ôl(€€€€€€€€€€€€€€€€€€€•Ù¥‘•¹”(€€€€€€€€€€€€€€€€€€€™½È•Ù¥‘•¹”¥¸Í•±˜¹ÍÉå}•Ù¥‘•¹”(€€€€€€€€€€€€€€€€€€€¥˜•Ù¥‘•¹”¹•Ù•¹Ñ}¥€ôô¥Ñ•´¹ÍÉå}•Ù•¹Ñ}¥(€€€€€€€€€€€€€€€t(€€€€€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€€€€€¥Ñ•´¹½ÁÁ½¹•¹Ñ}±¥™•}…™Ñ•È€ðô€À(€€€€€€€€€€€€€€€€€€€½È¥Ñ•´¹½¹ÑÉ½±±•É}±¥™•}…™Ñ•È€„ô¥Ñ•´¹½¹ÑÉ½±±•É}±¥™•}‰•™½É”€¬€Ä(€€€€€€€€€€€€€€€€€€€½È±•¸¡µ…Ñ¡¥¹}ÍÉä¤€„ô€Ä(€€€€€€€€€€€€€€€€€€€½Èµ…Ñ¡¥¹}ÍÉålÁt¹Á±…å•É}¥¹‘•à€„ô¥Ñ•´¹½¹ÑÉ½±±•È(€€€€€€€€€€€€€€€€€€€½Èµ…Ñ¡¥¹}ÍÉålÁt¹É•ÅÕ•ÍÑ•€„ô€Ä(€€€€€€€€€€€€€€€€€€€½Èµ…Ñ¡¥¹}ÍÉålÁt¹Í½ÕÉ•}¥€„ô¥Ñ•´¹Í½ÕÉ•}¥(€€€€€€€€€€€€€€€€€€€½Èµ…Ñ¡¥¹}ÍÉålÁt¹½É…±•}™É…µ•¹Ð€„ô¥Ñ•´¹½É…±•}™É…µ•¹Ð(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½µÁ±•Ñ•Q‘É…¥¸½…¥¸½MÉä•Ù¥‘•¹”¥Ì¥¹½¹Í¥ÍÑ•¹Ðˆ¤(€€€€€€€¥˜±•¸¡í¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥™½È¥Ñ•´¥¸Í•±˜¹…Ñ¥Ù…Ñ¥½¹}•Ù¥‘•¹•ô¤€„ô±•¸ (€€€€€€€€€€€Í•±˜¹…Ñ¥Ù…Ñ¥½¹}•Ù¥‘•¹”(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰…Ñ¥Ù…Ñ¥½¸•Ù¥‘•¹”ÍÑ…¬%ÌµÕÍÐ‰”Õ¹¥ÅÕ”ˆ¤(€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹…Ñ¥Ù…Ñ¥½¹}•Ù¥‘•¹”è(€€€€€€€€€€€¥˜¥Ñ•´¹½¹ÑÉ½±±•È¹½Ð¥¸É…¹” È¤½È¥Ñ•´¹Í½ÕÉ•}¥¹½Ð¥¸Í•±˜¹}½‰©•ÑÌè(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰…Ñ¥Ù…Ñ¥½¸•Ù¥‘•¹”É•™•É•¹•Ì¥¹Ù…±¥…ÕÑ¡½É¥Ñäˆ¤(€€€€€€€€€€€…‰¥±¥Ñä€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥¤(€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡…‰¥±¥Ñä°Ñ¥Ù…Ñ•‘‰¥±¥Ñå=‰©•Ð¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰…Ñ¥Ù…Ñ¥½¸•Ù¥‘•¹”±…­Ì¥ÑÌÉÕ¹Ñ¥µ”ÍÑ…¬½‰©•Ðˆ¤(€€€€€€€€€€€¥˜¥Ñ•´¹É•Í½±Ù•€„ô€¡…‰¥±¥Ñä¹é½¹”€ôô€‰™½Éµ•Èˆ¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰…Ñ¥Ù…Ñ¥½¸É•Í½±ÕÑ¥½¸•Ù¥‘•¹”‘¥Í…É••ÌÝ¥Ñ ÍÑ…¬ÍÑ…Ñ”ˆ¤(€€€€€€€¥˜±•¸¡í¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥™½È¥Ñ•´¥¸Í•±˜¹™½½‘}…Ñ¥Ù…Ñ¥½¹}•Ù¥‘•¹•ô¤€„ô±•¸ (€€€€€€€€€€€Í•±˜¹™½½‘}…Ñ¥Ù…Ñ¥½¹}•Ù¥‘•¹”(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½½…Ñ¥Ù…Ñ¥½¸•Ù¥‘•¹”ÍÑ…¬%ÌµÕÍÐ‰”Õ¹¥ÅÕ”ˆ¤(€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹™½½‘}…Ñ¥Ù…Ñ¥½¹}•Ù¥‘•¹”è(€€€€€€€€€€€…‰¥±¥Ñä€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥¤(€€€€€€€€€€€Í…É¥™¥•€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡¥Ñ•´¹Í…É¥™¥•‘}‘•ÍÑ¥¹…Ñ¥½¹}¥¤(€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡…‰¥±¥Ñä°Ñ¥Ù…Ñ•‘‰¥±¥Ñå=‰©•Ð¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½½…Ñ¥Ù…Ñ¥½¸•Ù¥‘•¹”±…­Ì¥ÑÌÍÑ…¬½‰©•Ðˆ¤(€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}™½½‘}…Ñ¥Ù…Ñ¥½¹}±¥¹­…”¡…‰¥±¥Ñä¤(€€€€€€€€€€€¥˜¥Ñ•´¹Í½ÕÉ•}¥¹½Ð¥¸Í•±˜¹}½‰©•ÑÌ½È¹½Ð¥Í¥¹ÍÑ…¹”¡Í…É¥™¥•°…É‘=‰©•Ð¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½½…Ñ¥Ù…Ñ¥½¸•Ù¥‘•¹”±…­Ì¥µµÕÑ…‰±”½ÍÐ¥‘•¹Ñ¥Ñ¥•Ìˆ¤(€€€€€€€€€€€¥˜¹½Ð¥Ñ•´¹Ñ…Á}Á…¥½È¹½Ð¥Ñ•´¹Í…É¥™¥•}Á…¥è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½½…Ñ¥Ù…Ñ¥½¸•Ù¥‘•¹”±…­Ì½µÁ±•Ñ”…¹½¹¥…°½ÍÑÌˆ¤(€€€€€€€€€€€¥˜¥Ñ•´¹Í½ÕÉ•}Ý…Í}Ñ½­•¸…¹¥Ñ•´¹™¥¹…±}Í½ÕÉ•}‘¥ÍÁ½Í¥Ñ¥½¸€„ô€‰™½Éµ•Èˆè(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰Í…É¥™¥•½½Ñ½­•¸µÕÍÐ•…Í”…ÐÑ¡”M	‰½Õ¹‘…Éäˆ¤(€€€€€€€€€€€¥˜¥Ñ•´¹É•Í½±Ù•€„ô€¡…‰¥±¥Ñä¹é½¹”€ôô€‰™½Éµ•Èˆ¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½½…Ñ¥Ù…Ñ¥½¸É•Í½±ÕÑ¥½¸•Ù¥‘•¹”‘¥Í…É••ÌÝ¥Ñ ÍÑ…¬ˆ¤(€€€€€€€€€€€¥˜¥Ñ•´¹É•Í½±Ù•…¹€ (€€€€€€€€€€€€€€€¥Ñ•´¹±¥™•}‰•™½É”¥Ì9½¹”(€€€€€€€€€€€€€€€½È¥Ñ•´¹±¥™•}…™Ñ•È¥Ì9½¹”(€€€€€€€€€€€€€€€½È¥Ñ•´¹…µ½Õ¹Ñ}…¥¹•€„ô€Ì(€€€€€€€€€€€€€€€½È¥Ñ•´¹±¥™•}…™Ñ•È€´¥Ñ•´¹±¥™•}‰•™½É”€„ô€Ì(€€€€€€€€€€€€€€€½È¥Ñ•´¹ÁÉ¥½É¥Ñå}Á…ÍÍ•Ì€„ô€¡¥Ñ•´¹½¹ÑÉ½±±•È°€Ä€´¥Ñ•´¹½¹ÑÉ½±±•È¤(€€€€€€€€€€€€€€€½È¹½Ð¥Ñ•´¹É•Í½±ÕÑ¥½¹}Á•Éµ¥ÑÑ•(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½½…Ñ¥Ù…Ñ¥½¸±¥™”•Ù¥‘•¹”¥Ì¥¹½¹Í¥ÍÑ•¹Ðˆ¤(€€€€€€€¥˜±•¸¡í¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥™½È¥Ñ•´¥¸Í•±˜¹Í¹•…­}•Ù¥‘•¹•ô¤€„ô±•¸¡Í•±˜¹Í¹•…­}•Ù¥‘•¹”¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰M¹•…¬•Ù¥‘•¹”ÍÑ…¬%ÌµÕÍÐ‰”Õ¹¥ÅÕ”ˆ¤(€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹Í¹•…­}•Ù¥‘•¹”è(€€€€€€€€€€€ÍÁ•±°€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥¤(€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡ÍÁ•±°°MÑ…­=‰©•Ð¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰M¹•…¬•Ù¥‘•¹”±…­Ì¥ÑÌÉÕ¹Ñ¥µ”ÍÑ…¬½‰©•Ðˆ¤(€€€€€€€€€€€¥˜¥Ñ•´¹Í½ÕÉ•}é½¹”¹½Ð¥¸ì‰¡…¹ˆ°€‰•á¥±”ˆ°€‰É…Ù•å…É‰ôè(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰M¹•…¬•Ù¥‘•¹”¡…Ì…¸¥¹Ù…±¥…ÍÐ½É¥¥¸ˆ¤(€€€€€€€€€€€¥˜¥Ñ•´¹Í½ÕÉ•}é½¹”€ôô€‰É…Ù•å…Éˆè(€€€€€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€€€€€¥Ñ•´¹Á•Éµ¥ÍÍ¥½¹}Í½ÕÉ•}¥¥Ì9½¹”(€€€€€€€€€€€€€€€€€€€½È¹½Ð¥Í¥¹ÍÑ…¹”¡Í•±˜¹}½‰©•ÑÌ¹•Ð¡¥Ñ•´¹Á•Éµ¥ÍÍ¥½¹}Í½ÕÉ•}¥¤°A•Éµ…¹•¹Ð¤(€€€€€€€€€€€€€€€€€€€½È¹½ÐÍÁ•±°¹…ÍÑ}™É½µ}É…Ù•å…É(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰É…Ù•å…ÉM¹•…¬±…­Ì±¥¹­•Á•Éµ¥ÍÍ¥½¸ÁÉ½Ù•¹…¹”ˆ¤(€€€€€€€€€€€•±¥˜¥Ñ•´¹Á•Éµ¥ÍÍ¥½¹}Í½ÕÉ•}¥¥Ì¹½Ð9½¹”è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰M¹•…¬•Ù¥‘•¹”¡…ÌÕ¹•áÁ•Ñ•Á•Éµ¥ÍÍ¥½¸ÁÉ½Ù•¹…¹”ˆ¤(€€€€€€€€€€€¥˜¥Ñ•´¹½¹ÑÉ½±±•È¹½Ð¥¸É…¹” È¤½È¥Ñ•´¹‘•™•¹‘¥¹}Á±…å•È€„ô€Ä€´¥Ñ•´¹½¹ÑÉ½±±•Èè(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰M¹•…¬•Ù¥‘•¹”¡…Ì¥¹Ù…±¥Á±…å•È…ÕÑ¡½É¥Ñäˆ¤(€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€¥Ñ•´¹¡…¹‘}½‰©•Ñ}¥¹½Ð¥¸Í•±˜¹}½‰©•ÑÌ(€€€€€€€€€€€€€€€½È¥Ñ•´¹É•ÑÕÉ¹•‘}…ÑÑ…­•É}¥¹½Ð¥¸Í•±˜¹}½‰©•ÑÌ(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰M¹•…¬•Ù¥‘•¹”±…­Ì¥µµÕÑ…‰±”Í½ÕÉ”¥‘•¹Ñ¥Ñ¥•Ìˆ¤(€€€€€€€€€€€¥˜¥Ñ•´¹É•ÑÕÉ¹•‘}¡…¹‘}¥¹½Ð¥¸Í•±˜¹}½‰©•ÑÌè(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰M¹•…¬•Ù¥‘•¹”±…­ÌÉ•ÑÕÉ¹•µ½‰©•Ð¥‘•¹Ñ¥Ñäˆ¤(€€€€€€€€€€€É•Í½±Ù•€ô¥Ñ•´¹É•Í½±Ù•‘}½‰©•Ñ}¥¥Ì¹½Ð9½¹”(€€€€€€€€€€€½Õ¹Ñ•É•€ô…¹ä (€€€€€€€€€€€€€€€•Ù•¹Ð¹•Ð ‰•Ù•¹Ðˆ¤€ôô€‰ÍÁ•±±}½Õ¹Ñ•É•ˆ(€€€€€€€€€€€€€€€…¹•Ù•¹Ð¹•Ð ‰Ñ…É•Ñ}ÍÁ•±±}¥ˆ¤€ôôÍÁ•±°¹½‰©•Ñ}¥(€€€€€€€€€€€€€€€™½È•Ù•¹Ð¥¸Í•±˜¹•Ù•¹ÑÌ(€€€€€€€€€€€€¤(€€€€€€€€€€€¥˜ÍÁ•±°¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹IQUIè(€€€€€€€€€€€€€€€¥˜É•Í½±Ù•…¹ÍÁ•±°¹é½¹”€„ô€‰™½Éµ•Èˆè(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰M¹•…¬•Ù¥‘•¹”É•Í½±ÕÑ¥½¸‘¥Í…É••ÌÝ¥Ñ ÍÑ…¬ÍÑ…Ñ”ˆ¤(€€€€€€€€€€€€€€€¥˜¹½ÐÉ•Í½±Ù•…¹ÍÁ•±°¹é½¹”€ôô€‰™½Éµ•Èˆ…¹¹½Ð½Õ¹Ñ•É•è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰M¹•…¬•Ù¥‘•¹”É•Í½±ÕÑ¥½¸‘¥Í…É••ÌÝ¥Ñ ÍÑ…¬ÍÑ…Ñ”ˆ¤(€€€€€€€€€€€€€€€¥˜É•Í½±Ù•…¹€ (€€€€€€€€€€€€€€€€€€€¥Ñ•´¹É•Í½±Ù•‘}½‰©•Ñ}¥¹½Ð¥¸Í•±˜¹}½‰©•ÑÌ(€€€€€€€€€€€€€€€€€€€½È¥Ñ•´¹•¹Ñ•É•‘}Ñ…ÁÁ•¥Ì¹½ÐQÉÕ”(€€€€€€€€€€€€€€€€€€€½È¥Ñ•´¹•¹Ñ•É•‘}…ÑÑ…­¥¹œ¥Ì¹½ÐQÉÕ”(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰É•Í½±Ù•M¹•…¬•Ù¥‘•¹”±…­Ì‰…ÑÑ±•™¥•±É•ÍÕ±Ðˆ¤(€€€€€€€€€€€•±¥˜É•Í½±Ù•è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰¹½¹É•…ÑÕÉ”M¹•…¬•Ù¥‘•¹”¡…Ì„‰…ÑÑ±•™¥•±É•ÍÕ±Ðˆ¤(€€€€€€€¥˜Í•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¥Ì¹½Ð9½¹”è(€€€€€€€€€€€ÍÑ…Ñ”€ôÍ•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”(€€€€€€€€€€€¥˜¹½ÐÍ•±˜¹ÍÑ…¬…¹¹½Ð€ (€€€€€€€€€€€€€€€Í•±˜¹ÍÑ•À¥ÌQÕÉ¹MÑ•À¹1I}	1=-IL…¹Í•±˜¹}‰±½­•ÉÍ}‘•±…É•(€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÁÉ¥½É¥ÑäÍÑ…Ñ”É•ÅÕ¥É•Ì„¹½¹•µÁÑäÍÑ…¬ˆ¤(€€€€€€€€€€€¥˜ÍÑ…Ñ”¹Á±…å•É}¥¹‘•à¹½Ð¥¸É…¹” È¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÁÉ¥½É¥ÑäÁ±…å•È¥Ì¥¹Ù…±¥ˆ¤(€€€€€€€€€€€¥˜±•¸¡ÍÑ…Ñ”¹½¹Í•ÕÑ¥Ù•}Á…ÍÍ•Ì¤€ø€Èè(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÁÉ¥½É¥ÑäÁ…ÍÌÍ•ÅÕ•¹”¥ÌÑ½¼±½¹œˆ¤(€€€€€€€€€€€¥˜ÍÑ…Ñ”¹½¹Í•ÕÑ¥Ù•}Á…ÍÍ•Ì¹½Ð¥¸ì ¤°€ À°¤°€ Ä°¤°€ À°€Ä¤°€ Ä°€À¥ôè(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÁÉ¥½É¥ÑäÁ…ÍÍ•ÌµÕÍÐ…±Ñ•É¹…Ñ”‰•ÑÝ••¸Á±…å•ÉÌˆ¤(€€€€€€€€€€€¥˜ÍÑ…Ñ”¹É•Í½±ÕÑ¥½¹}Á•¹‘¥¹œ€„ô€¡±•¸¡ÍÑ…Ñ”¹½¹Í•ÕÑ¥Ù•}Á…ÍÍ•Ì¤€ôô€È¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÁÉ¥½É¥ÑäÉ•Í½±ÕÑ¥½¸Á•Éµ¥ÍÍ¥½¸‘¥Í…É••ÌÝ¥Ñ Á…ÍÍ•Ìˆ¤(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰…Ñ¥Ù…Ñ¥½¸•Ù¥‘•¹”É•Í½±ÕÑ¥½¸ÍÑ…Ñ”¥Ì¥¹½¹Í¥ÍÑ•¹Ðˆ¤(€€€€€€€¥˜Í•±˜¹ÍÑ•À¥ÌQÕÉ¹MÑ•À¹=5	Q}5…¹Í•±˜¹}½µ‰…Ñ}‘…µ…•}ÍÑ•Á}­¥¹¹½Ð¥¸ì(€€€€€€€€€€€½µ‰…Ñ…µ…•MÑ•Á-¥¹¹%IMQ}MQI%-°(€€€€€€€€€€€½µ‰…Ñ…µ…•MÑ•Á-¥¹¹IU1H°(€€€€€€€ôè(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½µ‰…Ð‘…µ…”ÑÕÉ¸ÍÑ•À±…­Ì…¸…Ñ¥Ù”‘…µ…”µÍÑ•À­¥¹ˆ¤(€€€€€€€¥˜Í•±˜¹ÍÑ•À¥¸ì(€€€€€€€€€€€QÕÉ¹MÑ•À¹A=MQ=5	Q}5%8°(€€€€€€€€€€€QÕÉ¹MÑ•À¹9}MQ@°(€€€€€€€€€€€QÕÉ¹MÑ•À¹19U@°(€€€€€€€€€€€QÕÉ¹MÑ•À¹U9Q@°(€€€€€€€€€€€QÕÉ¹MÑ•À¹UA-@°(€€€€€€€€€€€QÕÉ¹MÑ•À¹I\°(€€€€€€€€€€€QÕÉ¹MÑ•À¹AI=5	Q}5%8°(€€€€€€€ô…¹€ (€€€€€€€€€€€½µ‰…Ñ}¥‘Ì(€€€€€€€€€€€½ÈÍ•±˜¹}…ÑÑ…­•ÉÍ}‘•±…É•(€€€€€€€€€€€½ÈÍ•±˜¹}‰±½­•ÉÍ}‘•±…É•(€€€€€€€€€€€½ÈÍ•±˜¹}½µ‰…Ñ}‘…µ…•}É•Í½±Ù•(€€€€€€€€€€€½ÈÍ•±˜¹}½µ‰…Ñ}‘…µ…•}ÍÑ•Á}­¥¹¥Ì¹½Ð½µ‰…Ñ…µ…•MÑ•Á-¥¹¹9=9(€€€€€€€€€€€½ÈÍ•±˜¹}½µ‰…Ñ}‘…µ…•}ÍÑ•Á}¹Õµ‰•È(€€€€€€€€€€€½ÈÍ•±˜¹}½µ‰…Ñ}‘…µ…•}Ñ½Ñ…±}ÍÑ•ÁÌ(€€€€€€€€€€€½ÈÍ•±˜¹}™¥ÉÍÑ}‘…µ…•}ÅÕ…±¥™¥•‘}¥‘Ì(€€€€€€€€€€€½ÈÍ•±˜¹}™¥ÉÍÑ}‘½Õ‰±•}ÍÑÉ¥­•}¥‘Ì(€€€€€€€€€€€½ÈÍ•±˜¹}É•Õ±…É}‘…µ…•}¥¹¥Ñ¥…±}¥‘Ì(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½µÁ±•Ñ•½µ‰…ÐÍÑ…Ñ”±•…­•½ÕÑÍ¥‘”Ñ¡”½µ‰…ÐÁ¡…Í”ˆ¤(€€€€€€€¥˜mÉ•½É¹Í•ÅÕ•¹”™½ÈÉ•½É¥¸Í•±˜¹É¹œ¹É•½É‘Ít€„ô±¥ÍÐ (€€€€€€€€€€€É…¹” Ä°±•¸¡Í•±˜¹É¹œ¹É•½É‘Ì¤€¬€Ä¤(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰I9½¹ÍÕµÁÑ¥½¸Í•ÅÕ•¹”¥Ì¹½Ð½¹Ñ¥Õ½ÕÌˆ¤(€€€€€€€¥˜…¹ä (€€€€€€€€€€€ÁÉ•Ù¥½ÕÌ¹ÍÑ…Ñ•}…™Ñ•È€„ôÕÉÉ•¹Ð¹ÍÑ…Ñ•}‰•™½É”(€€€€€€€€€€€™½ÈÁÉ•Ù¥½ÕÌ°ÕÉÉ•¹Ð¥¸é¥À¡Í•±˜¹É¹œ¹É•½É‘Ì°Í•±˜¹É¹œ¹É•½É‘ÍlÄét°ÍÑÉ¥Ðõ…±Í”¤(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰I9ÍÑ…Ñ”•Ù¥‘•¹”‘½•Ì¹½Ð™½É´½¹”¡…¥¸ˆ¤(€€€€€€€¥˜Í•±˜¹É¹œ¹É•½É‘Ì…¹Í•±˜¹É¹œ¹É•½É‘Íl´Åt¹ÍÑ…Ñ•}…™Ñ•È€„ôÍ•±˜¹É¹œ¹ÍÑ…Ñ•}‘¥•ÍÐè(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰I9ÕÉÉ•¹ÐÍÑ…Ñ”‘½•Ì¹½Ðµ…Ñ ¥ÑÌ½¹ÍÕµÁÑ¥½¸±•‘•Èˆ¤(€€€€€€€½ÕÁ¥•è‘¥Ñl(€€€€€€€€€€€ÍÑÈ°(€€€€€€€€€€€ÑÕÁ±•l(€€€€€€€€€€€€€€€¥¹Ðð9½¹”°(€€€€€€€€€€€€€€€ÍÑÈ°(€€€€€€€€€€€€€€€…É‘=‰©•Ð(€€€€€€€€€€€€€€€ðMÑ…­=‰©•Ð(€€€€€€€€€€€€€€€ðQÉ¥•É•‘‰¥±¥Ñå=‰©•Ð(€€€€€€€€€€€€€€€ðÑ¥Ù…Ñ•‘‰¥±¥Ñå=‰©•Ð(€€€€€€€€€€€€€€€ðA•Éµ…¹•¹Ð°(€€€€€€€€€€€t°(€€€€€€€t€ôíô(€€€€€€€™½È½‰¨¥¸Í•±˜¹ÍÑ…¬è(€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡½‰¨°€¡MÑ…­=‰©•Ð°QÉ¥•É•‘‰¥±¥Ñå=‰©•Ð°Ñ¥Ù…Ñ•‘‰¥±¥Ñå=‰©•Ð¤¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…¬µ…ä½¹Ñ…¥¸½¹±äÍÁ•±°½È…‰¥±¥Ñä½‰©•ÑÌˆ¤(€€€€€€€€€€€¥˜½‰¨¹½‰©•Ñ}¥¥¸½ÕÁ¥•è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÉÕ¹Ñ¥µ”½‰©•Ð½ÕÁ¥•Ìµ½É”Ñ¡…¸½¹”é½¹”ˆ¤(€€€€€€€€€€€¥˜Í•±˜¹}½‰©•ÑÌ¹•Ð¡½‰¨¹½‰©•Ñ}¥¤¥Ì¹½Ð½‰¨è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…¬½¹Ñ…¥¹Ì…¸Õ¹É•¥ÍÑ•É•½È…±¥…Í•½‰©•Ðˆ¤(€€€€€€€€€€€¥˜½‰¨¹é½¹”€„ô€‰ÍÑ…¬ˆè(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…¬½‰©•Ðé½¹”‘½•Ì¹½Ðµ…Ñ ¥ÑÌ½¹Ñ…¥¹•Èˆ¤(€€€€€€€€€€€¥˜½‰¨¹½¹ÑÉ½±±•È¹½Ð¥¸É…¹” È¤è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…¬½‰©•Ð½¹ÑÉ½±±•È¥Ì¥¹Ù…±¥ˆ¤(€€€€€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡½‰¨°MÑ…­=‰©•Ð¤è(€€€€€€€€€€€€€€€¥˜½‰¨¹…ÍÑ}­¥¹¥Ì…ÍÑ-¥¹¹U9MUAA=IQè(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰Õ¹ÍÕÁÁ½ÉÑ•ÍÁ•±±Ì…¹¹½Ð‰•½µ”ÍÑ…¬½‰©•ÑÌˆ¤(€€€€€€€€€€€€€€€¥˜½‰¨¹Ñ…É•Ñ}¥¥Ì¹½Ð9½¹”…¹½‰¨¹Ñ…É•Ñ}¥¹½Ð¥¸Í•±˜¹}½‰©•ÑÌè(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÑ…¬Ñ…É•Ð%Ý…Ì¹•Ù•ÈÉ•¥ÍÑ•É•ˆ¤(€€€€€€€€€€€€€€€¥˜…¹ä¡Ñ…É•Ñ}¥¹½Ð¥¸Í•±˜¹}½‰©•ÑÌ™½ÈÑ…É•Ñ}¥¥¸½‰¨¹Ñ…É•Ñ}¥‘Ì¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÁ•±°Ñ…É•Ð%Ý…Ì¹•Ù•ÈÉ•¥ÍÑ•É•ˆ¤(€€€€€€€€€€€€€€€¥˜±•¸¡Í•Ð¡½‰¨¹Ñ…É•Ñ}¥‘Ì¤¤€„ô±•¸¡½‰¨¹Ñ…É•Ñ}¥‘Ì¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÍÁ•±°Ñ…É•ÑÌ…É”¹½Ð‘¥ÍÑ¥¹Ðˆ¤(€€€€€€€€€€€•±¥˜¥Í¥¹ÍÑ…¹”¡½‰¨°QÉ¥•É•‘‰¥±¥Ñå=‰©•Ð¤è(€€€€€€€€€€€€€€€¥˜½‰¨¹•Ù•¹Ð¹Á±…å•É}¥¹‘•à¹½Ð¥¸É…¹” È¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÑÉ¥•È•Ù•¹ÐÁ±…å•È¥Ì¥¹Ù…±¥ˆ¤(€€€€€€€€€€€€€€€¥˜½‰¨¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹%M}I\è(€€€€€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}‘¥•Í}‘É…Ý}ÑÉ¥•È¡½‰¨¤(€€€€€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€€€€€¥˜½‰¨¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹I9Q}%M}IQUI8è(€€€€€€€€€€€€€€€€€€€Í½ÕÉ”€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡½‰¨¹Í½ÕÉ•}¥¤(€€€€€€€€€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡Í½ÕÉ”°A•Éµ…¹•¹Ð¤è(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰É…¹Ñ•‘•…Ñ ÑÉ¥•ÈÍ½ÕÉ”¥Ì¥¹Ù…±¥ˆ¤(€€€€€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}É…¹Ñ•‘}‘•…Ñ¡}É•ÑÕÉ¸ (€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨¹•Ù•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€Í½ÕÉ”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•É}¥õ½‰¨¹ÑÉ¥•É}¥°(€€€€€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€€€€€¥˜½‰¨¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹Q	}I%9}%9}MIdè(€€€€€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}•Ñ‰}‘É…¥¹}…¥¹}ÍÉå}ÑÉ¥•È¡½‰¨¤(€€€€€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€€€€€¥˜½‰¨¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹Q	}M1}1%}%8è(€€€€€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}•Ñ‰}Í•±™}±¥™•}…¥¹}ÑÉ¥•È¡½‰¨¤(€€€€€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€€€€€¥˜½‰¨¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹AI599Q}1Q}M1}=U9QHè(€€€€€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}Á•Éµ…¹•¹Ñ}±•™Ñ}½Õ¹Ñ•É}ÁÉ½Ù•¹…¹” (€€€€€€€€€€€€€€€€€€€€€€€€€€€½¹ÑÉ½±±•Èõ½‰¨¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ½‰¨¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}…Éõ½‰¨¹Í½ÕÉ•}…É°(€€€€€€€€€€€€€€€€€€€€€€€€€€€½É…±•}™É…µ•¹Ðõ½‰¨¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€•Ù•¹Ðõ½‰¨¹•Ù•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•É}¥õ½‰¨¹ÑÉ¥•É}¥°(€€€€€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€€€€€¥˜½‰¨¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹=9QI=11}IQUI}1Q}=AA=99Q}1=MLè(€€€€€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}½¹ÑÉ½±±•‘}É•…ÑÕÉ•}‘•Á…ÉÑÕÉ•}±½ÍÌ (€€€€€€€€€€€€€€€€€€€€€€€€€€€½¹ÑÉ½±±•Èõ½‰¨¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ½‰¨¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}…Éõ½‰¨¹Í½ÕÉ•}…É°(€€€€€€€€€€€€€€€€€€€€€€€€€€€½É…±•}™É…µ•¹Ðõ½‰¨¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€•Ù•¹Ðõ½‰¨¹•Ù•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•É}¥õ½‰¨¹ÑÉ¥•É}¥°(€€€€€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€€€€€¥˜½‰¨¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹=9QI=11}=U9QI}IQUI}1Q}1%è(€€€€€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}½Õ¹Ñ•É•‘}É•…ÑÕÉ•}‘•Á…ÉÑÕÉ•}±¥™” (€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨¹•Ù•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨¹Í½ÕÉ•}…É°(€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•É}¥õ½‰¨¹ÑÉ¥•É}¥°(€€€€€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€€€€€¥˜½‰¨¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹=9QI=11}IQ%Q}=U9QI}QI9MHè(€€€€€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}…ÉÑ¥™…Ñ}½Õ¹Ñ•É}ÑÉ…¹Í™•È (€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨¹•Ù•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨¹Í½ÕÉ•}…É°(€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•É}¥õ½‰¨¹ÑÉ¥•É}¥°(€€€€€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€€€€€¥˜½‰¨¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹5}Q=}M1}59è(€€€€€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}‘…µ…•}Ñ½}Í•±™}µ…¹„ (€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨¹•Ù•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨¹Í½ÕÉ•}…É°(€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•É}¥õ½‰¨¹ÑÉ¥•É}¥°(€€€€€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€€€€€¥˜½‰¨¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹1MM}MA11}MQ}Q5}=U9QHè(€€€€€€€€€€€€€€€€€€€Í½ÕÉ”€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡½‰¨¹Í½ÕÉ•}¥¤(€€€€€€€€€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡Í½ÕÉ”°A•Éµ…¹•¹Ð¤è(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰±…ÍÌÍÁ•±°µ…ÍÐÍ½ÕÉ”¥Ì¥¹Ù…±¥ˆ¤(€€€€€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}±…ÍÍ}ÍÁ•±±}…ÍÑ}Ñ•…µ}½Õ¹Ñ•È (€€€€€€€€€€€€€€€€€€€€€€€€€€€½‰¨°½‰¨¹•Ù•¹Ð°Í½ÕÉ”°½‰¨¹½É…±•}™É…µ•¹Ð°½‰¨¹½¹ÑÉ½±±•È(€€€€€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€€€€€¥˜½‰¨¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹Q	}IQ%Q}I\è(€€€€€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}•Ñ‰}…ÉÑ¥™…Ñ}‘É…Ý}ÁÉ½Ù•¹…¹” (€€€€€€€€€€€€€€€€€€€€€€€€€€€½¹ÑÉ½±±•Èõ½‰¨¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õ½‰¨¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}…Éõ½‰¨¹Í½ÕÉ•}…É°(€€€€€€€€€€€€€€€€€€€€€€€€€€€½É…±•}™É…µ•¹Ðõ½‰¨¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€•Ù•¹Ðõ½‰¨¹•Ù•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•É}¥õ½‰¨¹ÑÉ¥•É}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€É•ÅÕ¥É•}ÕÉÉ•¹Ñ}½¹‘¥Ñ¥½¸õ…±Í”°(€€€€€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€€€€€¥˜½‰¨¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹11%9}Q5A=IIe}-e]=I}!=%è(€€€€€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}…±±¥…¹•}Ñ•µÁ½É…Éå}­•åÝ½É‘}¡½¥•}ÑÉ¥•È¡½‰¨¤(€€€€€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€€€€€¥˜½‰¨¹•™™•Ð¥¸ì(€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹I9Q}=5	Q}U9QA}%8°(€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹EU%A59Q}MU	QeA}9QIe}QQ °(€€€€€€€€€€€€€€€ôè(€€€€€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}•ÅÕ¥Áµ•¹Ñ}É…¹Ñ•‘}ÑÉ¥•È¡½‰¨¤(€€€€€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€€€€€¥˜½‰¨¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹=5	Q}5}I]}1=M}1%è(€€€€€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}½µ‰…Ñ}‘É…Ý}±¥™•}ÑÉ¥•È¡½‰¨¤(€€€€€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€€€€€¥˜½‰¨¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹=5	Q}5}IYeI}QQ-Hè(€€€€€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}½µ‰…Ñ}É…Ù•å…É‘}ÑÉ¥•È¡½‰¨¤(€€€€€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€€€€€¥˜½‰¨¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹Q	}MQI=e}QIQ}IQUIè(€€€€€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}•Ñ‰}É•…ÑÕÉ•}‘•ÍÑÉ½å}ÑÉ¥•È¡½‰¨¤(€€€€€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€€€€€¥˜½‰¨¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹Q	}QIQ}IQUI}AU5A}U9Q@è(€€€€€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}•Ñ‰}ÁÕµÁ}ÑÉ¥•È¡½‰¨¤(€€€€€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€•±¥˜¥Í¥¹ÍÑ…¹”¡½‰¨°Ñ¥Ù…Ñ•‘‰¥±¥Ñå=‰©•Ð¤è(€€€€€€€€€€€€€€€¥˜½‰¨¹Í½ÕÉ•}¥¹½Ð¥¸Í•±˜¹}½‰©•ÑÌè(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰…Ñ¥Ù…Ñ•…‰¥±¥ÑäÍ½ÕÉ”%Ý…Ì¹•Ù•ÈÉ•¥ÍÑ•É•ˆ¤(€€€€€€€€€€€€€€€¥˜…¹ä¡Ñ…É•Ñ}¥¹½Ð¥¸Í•±˜¹}½‰©•ÑÌ™½ÈÑ…É•Ñ}¥¥¸½‰¨¹Ñ…É•Ñ}¥‘Ì¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰…Ñ¥Ù…Ñ•…‰¥±¥ÑäÑ…É•Ð%Ý…Ì¹•Ù•ÈÉ•¥ÍÑ•É•ˆ¤(€€€€€€€€€€€½ÕÁ¥•‘m½‰¨¹½‰©•Ñ}¥‘t€ô€¡9½¹”°€‰ÍÑ…¬ˆ°½‰¨¤(€€€€€€€¥˜±•¸¡íÑÉ¥•È¹ÑÉ¥•É}¥™½ÈÑÉ¥•È¥¸Í•±˜¹Á•¹‘¥¹}ÑÉ¥•ÉÍô¤€„ô±•¸ (€€€€€€€€€€€Í•±˜¹Á•¹‘¥¹}ÑÉ¥•ÉÌ(€€€€€€€€¤è(€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰Á•¹‘¥¹œÑÉ¥•È%ÌµÕÍÐ‰”Õ¹¥ÅÕ”ˆ¤(€€€€€€€™½ÈÑÉ¥•È¥¸Í•±˜¹Á•¹‘¥¹}ÑÉ¥•ÉÌè(€€€€€€€€€€€¥˜ÑÉ¥•È¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹5}Q=}M1}59è(€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}‘…µ…•}Ñ½}Í•±™}µ…¹„ (€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•È¹•Ù•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•È¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•È¹Í½ÕÉ•}…É°(€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•È¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•È¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•É}¥õÑÉ¥•È¹ÑÉ¥•É}¥°(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€¥˜ÑÉ¥•È¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹=9QI=11}IQ%Q}=U9QI}QI9MHè(€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}…ÉÑ¥™…Ñ}½Õ¹Ñ•É}ÑÉ…¹Í™•È (€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•È¹•Ù•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•È¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•È¹Í½ÕÉ•}…É°(€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•È¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•È¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•É}¥õÑÉ¥•È¹ÑÉ¥•É}¥°(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€¥˜ÑÉ¥•È¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹AI599Q}1Q}M1}=U9QHè(€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}Á•Éµ…¹•¹Ñ}±•™Ñ}½Õ¹Ñ•É}ÁÉ½Ù•¹…¹” (€€€€€€€€€€€€€€€€€€€€€€€½¹ÑÉ½±±•ÈõÑÉ¥•È¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÑÉ¥•È¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}…ÉõÑÉ¥•È¹Í½ÕÉ•}…É°(€€€€€€€€€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÑÉ¥•È¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€•Ù•¹ÐõÑÉ¥•È¹•Ù•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•É}¥õÑÉ¥•È¹ÑÉ¥•É}¥°(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€¥˜ÑÉ¥•È¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹Q	}IQ%Q}I\è(€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}•Ñ‰}…ÉÑ¥™…Ñ}‘É…Ý}ÁÉ½Ù•¹…¹” (€€€€€€€€€€€€€€€€€€€€€€€½¹ÑÉ½±±•ÈõÑÉ¥•È¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}¥õÑÉ¥•È¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€Í½ÕÉ•}…ÉõÑÉ¥•È¹Í½ÕÉ•}…É°(€€€€€€€€€€€€€€€€€€€€€€€½É…±•}™É…µ•¹ÐõÑÉ¥•È¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€•Ù•¹ÐõÑÉ¥•È¹•Ù•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€ÑÉ¥•É}¥õÑÉ¥•È¹ÑÉ¥•É}¥°(€€€€€€€€€€€€€€€€€€€€€€€É•ÅÕ¥É•}ÕÉÉ•¹Ñ}½¹‘¥Ñ¥½¸õ…±Í”°(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€™½ÈÁ±…å•É}¥¹‘•à°Á±…å•È¥¸•¹Õµ•É…Ñ”¡Í•±˜¹Á±…å•ÉÌ¤è(€€€€€€€€€€€™½Èé½¹•}¹…µ”¥¸€ ‰±¥‰É…Éäˆ°€‰¡…¹ˆ°€‰‰…ÑÑ±•™¥•±ˆ°€‰É…Ù•å…Éˆ°€‰•á¥±”ˆ¤è(€€€€€€€€€€€€€€€™½È½‰¨¥¸•Ñ…ÑÑÈ¡Á±…å•È°é½¹•}¹…µ”¤è(€€€€€€€€€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡½‰¨°€¡…É‘=‰©•Ð°A•Éµ…¹•¹Ð¤¤è(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰é½¹•Ìµ…ä½¹Ñ…¥¸½¹±äÉ•¥ÍÑ•É•ÉÕ¹Ñ¥µ”½‰©•ÑÌˆ¤(€€€€€€€€€€€€€€€€€€€¥˜½‰¨¹½‰©•Ñ}¥¥¸½ÕÁ¥•è(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÉÕ¹Ñ¥µ”½‰©•Ð½ÕÁ¥•Ìµ½É”Ñ¡…¸½¹”é½¹”ˆ¤(€€€€€€€€€€€€€€€€€€€¥˜Í•±˜¹}½‰©•ÑÌ¹•Ð¡½‰¨¹½‰©•Ñ}¥¤¥Ì¹½Ð½‰¨è(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰é½¹”½¹Ñ…¥¹Ì…¸Õ¹É•¥ÍÑ•É•½È…±¥…Í•½‰©•Ðˆ¤(€€€€€€€€€€€€€€€€€€€¥˜½‰¨¹é½¹”€„ôé½¹•}¹…µ”è(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÉÕ¹Ñ¥µ”½‰©•Ðé½¹”‘½•Ì¹½Ðµ…Ñ ¥ÑÌ½¹Ñ…¥¹•Èˆ¤(€€€€€€€€€€€€€€€€€€€•áÁ•Ñ•‘}¡½±‘•È€ô½‰¨¹½¹ÑÉ½±±•È¥˜é½¹•}¹…µ”€ôô€‰‰…ÑÑ±•™¥•±ˆ•±Í”½‰¨¹½Ý¹•È(€€€€€€€€€€€€€€€€€€€¥˜•áÁ•Ñ•‘}¡½±‘•È€„ôÁ±…å•É}¥¹‘•àè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰ÉÕ¹Ñ¥µ”½‰©•Ð½ÕÁ¥•ÌÑ¡”ÝÉ½¹œÁ±…å•ÈÌé½¹”ˆ¤(€€€€€€€€€€€€€€€€€€€¥˜é½¹•}¹…µ”€„ô€‰‰…ÑÑ±•™¥•±ˆ…¹½‰¨¹½¹ÑÉ½±±•È€„ô½‰¨¹½Ý¹•Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰¹½¹‰…ÑÑ±•™¥•±½‰©•Ð½¹ÑÉ½±±•ÈµÕÍÐÉ•Í•ÐÑ¼½Ý¹•Èˆ¤(€€€€€€€€€€€€€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡½‰¨°…É‘=‰©•Ð¤…¹½‰¨¹¥Í}Ñ½­•¸è(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È (€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰„¹½¹‰…ÑÑ±•™¥•±Ñ½­•¸µÕÍÐ•…Í”…ÐÑ¡”M	‰½Õ¹‘…Éäˆ(€€€€€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€½ÕÁ¥•‘m½‰¨¹½‰©•Ñ}¥‘t€ô€¡Á±…å•É}¥¹‘•à°é½¹•}¹…µ”°½‰¨¤(€€€€€€€™½È½‰©•Ñ}¥°½‰¨¥¸Í•±˜¹}½‰©•ÑÌ¹¥Ñ•µÌ ¤è(€€€€€€€€€€€¥˜½‰¨¹é½¹”€ôô€‰™½Éµ•Èˆè(€€€€€€€€€€€€€€€¥˜½‰©•Ñ}¥¥¸½ÕÁ¥•è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰™½Éµ•È½‰©•ÐÍÑ¥±°½ÕÁ¥•Ì„é½¹”ˆ¤(€€€€€€€€€€€•±¥˜½‰©•Ñ}¥¹½Ð¥¸½ÕÁ¥•è(€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰…ÕÑ¡½É¥Ñ…Ñ¥Ù”ÉÕ¹Ñ¥µ”½‰©•Ð½ÕÁ¥•Ì¹¼é½¹”ˆ¤((€€€€€€€™½ÈÁ±…å•É}¥¹‘•à°Á±…å•È¥¸•¹Õµ•É…Ñ”¡Í•±˜¹Á±…å•ÉÌ¤è(€€€€€€€€€€€±••¹‘…Éå}¹…µ•ÌèÍ•ÑmÍÑÉt€ôÍ•Ð ¤(€€€€€€€€€€€™½ÈÁ•Éµ…¹•¹Ð¥¸Á±…å•È¹‰…ÑÑ±•™¥•±è(€€€€€€€€€€€€€€€¥˜Á•Éµ…¹•¹Ð¹½¹ÑÉ½±±•È€„ôÁ±…å•É}¥¹‘•àè(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰‰…ÑÑ±•™¥•±½¹ÑÉ½±±•È‘½•Ì¹½Ðµ…Ñ Á±…å•Èé½¹”ˆ¤(€€€€€€€€€€€€€€€¥˜Á•Éµ…¹•¹Ð¹•¹Ñ•É•‘}‰…ÑÑ±•™¥•±‘}ÑÕÉ¸€øÍ•±˜¹ÑÕÉ¸è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰Á•Éµ…¹•¹Ð•¹Ñ•É•Ñ¡”‰…ÑÑ±•™¥•±¥¸„™ÕÑÕÉ”ÑÕÉ¸ˆ¤(€€€€€€€€€€€€€€€¥˜Á•Éµ…¹•¹Ð¹•¹Ñ•É•‘}Õ¹‘•É}½¹ÑÉ½±±•È¹½Ð¥¸É…¹” È¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰Á•Éµ…¹•¹Ð±…­Ì¥ÑÌ•¹ÑÉä½¹ÑÉ½±±•ÈÁÉ½Ù•¹…¹”ˆ¤(€€€€€€€€€€€€€€€¥˜Á•Éµ…¹•¹Ð¹¥Í}Ñ½­•¸€„ô¥Í¥¹ÍÑ…¹”¡Á•Éµ…¹•¹Ð¹…É°Q½­•¹•™¥¹¥Ñ¥½¸¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰Ñ½­•¸ÉÕ¹Ñ¥µ”ÍÑ…Ñ”‘½•Ì¹½Ðµ…Ñ ¥ÑÌÑ½­•¸‘•™¥¹¥Ñ¥½¸ˆ¤(€€€€€€€€€€€€€€€¥˜¹½ÐÁ•Éµ…¹•¹Ð¹ÑåÁ•}±¥¹”è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰Á•Éµ…¹•¹ÐÑåÁ”±¥¹”µÕÍÐÉ•µ…¥¸¹½¹•µÁÑäˆ¤(€€€€€€€€€€€€€€€¥˜Á•Éµ…¹•¹Ð¹…É¹¥Í}É•…ÑÕÉ”…¹€ (€€€€€€€€€€€€€€€€€€€Á•Éµ…¹•¹Ð¹…É¹Á½Ý•È¥Ì9½¹”½ÈÁ•Éµ…¹•¹Ð¹…É¹Ñ½Õ¡¹•ÍÌ¥Ì9½¹”(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰É•…ÑÕÉ”Á•Éµ…¹•¹Ð±…­ÌÁÉ¥¹Ñ•Á½Ý•È½Ñ½Õ¡¹•ÍÌˆ¤(€€€€€€€€€€€€€€€¥˜€ (€€€€€€€€€€€€€€€€€€€Á•Éµ…¹•¹Ð¹¥Í}É•…ÑÕÉ”(€€€€€€€€€€€€€€€€€€€…¹Á•Éµ…¹•¹Ð¹¡…Í}É•ÁÉ•Í•¹Ñ•‘}Á½Ý•É}Ñ½Õ¡¹•ÍÌ(€€€€€€€€€€€€€€€€€€€…¹Á•Éµ…¹•¹Ð¹Ñ½Õ¡¹•ÍÌ€ðô€À(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰¹½¹Á½Í¥Ñ¥Ù”Ñ½Õ¡¹•ÍÌµÕÍÐ‰”¡…¹‘±•‰ä…¸M	ˆ¤(€€€€€€€€€€€€€€€¥¹Ù…±¥‘}½Õ¹Ñ•ÉÌ€ô…¹ä (€€€€€€€€€€€€€€€€€€€¹½Ð¥Í¥¹ÍÑ…¹”¡½Õ¹Ñ•É}ÑåÁ”°ÍÑÈ¤(€€€€€€€€€€€€€€€€€€€½È¹½Ð½Õ¹Ñ•É}ÑåÁ”(€€€€€€€€€€€€€€€€€€€½È¹½Ð¥Í¥¹ÍÑ…¹”¡Ù…±Õ”°¥¹Ð¤(€€€€€€€€€€€€€€€€€€€½È¥Í¥¹ÍÑ…¹”¡Ù…±Õ”°‰½½°¤(€€€€€€€€€€€€€€€€€€€½ÈÙ…±Õ”€ðô€À(€€€€€€€€€€€€€€€€€€€™½È½Õ¹Ñ•É}ÑåÁ”°Ù…±Õ”¥¸Á•Éµ…¹•¹Ð¹½Õ¹Ñ•ÉÌ¹¥Ñ•µÌ ¤(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€¥˜¥¹Ù…±¥‘}½Õ¹Ñ•ÉÌè(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½Õ¹Ñ•ÈÅÕ…¹Ñ¥Ñ¥•ÌµÕÍÐ‰”¹½¹¹•…Ñ¥Ù”¥¹Ñ••ÉÌˆ¤(€€€€€€€€€€€€€€€¥˜…¹ä (€€€€€€€€€€€€€€€€€€€™É…µ•¹Ð¹½Ð¥¸Í•±˜¹¥¹Ñ•ÉÁÉ•Ñ•È¹™É…µ•¹ÑÌ¡Á•Éµ…¹•¹Ð¹…É¤(€€€€€€€€€€€€€€€€€€€½ÈÑÕÉ¸€øÍ•±˜¹ÑÕÉ¸(€€€€€€€€€€€€€€€€€€€½ÈÑÕÉ¸€ð€Ä(€€€€€€€€€€€€€€€€€€€™½È™É…µ•¹Ð°ÑÕÉ¸¥¸Á•Éµ…¹•¹Ð¹½¹•}Á•É}ÑÕÉ¹}…Ñ¥Ù…Ñ¥½¹Ì¹¥Ñ•µÌ ¤(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰½¹”µÁ•ÈµÑÕÉ¸…Ñ¥Ù…Ñ¥½¸µ…É­•È¥Ì¥¹Ù…±¥ˆ¤(€€€€€€€€€€€€€€€™½Èµ½‘¥™¥•È¥¸Á•Éµ…¹•¹Ð¹ÁÑ}µ½‘¥™¥•ÉÌè(€€€€€€€€€€€€€€€€€€€¥˜µ½‘¥™¥•È¹‘ÕÉ…Ñ¥½¸¹½Ð¥¸ì‰Á•ÉÍ¥ÍÑ•¹Ðˆ°€‰Õ¹Ñ¥±}•¹‘}½™}ÑÕÉ¸‰ôè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰Õ¹­¹½Ý¸@½Pµ½‘¥™¥•È‘ÕÉ…Ñ¥½¸ˆ¤(€€€€€€€€€€€€€€€€€€€¥˜µ½‘¥™¥•È¹É•…Ñ•‘}ÑÕÉ¸€øÍ•±˜¹ÑÕÉ¸è(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰@½Pµ½‘¥™¥•È½É¥¥¹…Ñ•Ì¥¸„™ÕÑÕÉ”ÑÕÉ¸ˆ¤(€€€€€€€€€€€€€€€¥˜…¹ä (€€€€€€€€€€€€€€€€€€€•™™•Ð¹‘ÕÉ…Ñ¥½¸€„ô€‰Õ¹Ñ¥±}•¹‘}½™}ÑÕÉ¸ˆ(€€€€€€€€€€€€€€€€€€€½È¹½Ð¥Í¥¹ÍÑ…¹”¡•™™•Ð¹­•åÝ½É°€¡MÑÉ¥­•-•åÝ½É°Q•µÁ½É…Éå-•åÝ½É¤¤(€€€€€€€€€€€€€€€€€€€™½È•™™•Ð¥¸Á•Éµ…¹•¹Ð¹Ñ•µÁ½É…Éå}­•åÝ½É‘}•™™•ÑÌ(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰Ñ•µÁ½É…Éä­•åÝ½É•™™•Ð¥Ìµ…±™½Éµ•ˆ¤(€€€€€€€€€€€€€€€¥˜…¹ä (€€€€€€€€€€€€€€€€€€€•™™•Ð¹‘ÕÉ…Ñ¥½¸¹½Ð¥¸ì‰Á•ÉÍ¥ÍÑ•¹Ðˆ°€‰Õ¹Ñ¥±}•¹‘}½™}ÑÕÉ¸‰ô(€€€€€€€€€€€€€€€€€€€½È¹½Ð•™™•Ð¹…‘‘•‘}ÑåÁ•Ì(€€€€€€€€€€€€€€€€€€€½È…¹ä¡¹½Ð¥Ñ•´™½È¥Ñ•´¥¸•™™•Ð¹…‘‘•‘}ÑåÁ•Ì¤(€€€€€€€€€€€€€€€€€€€½È…¹ä¡¹½Ð¥Ñ•´™½È¥Ñ•´¥¸•™™•Ð¹…‘‘•‘}ÍÕ‰ÑåÁ•Ì¤(€€€€€€€€€€€€€€€€€€€™½È•™™•Ð¥¸Á•Éµ…¹•¹Ð¹Ñ•µÁ½É…Éå}ÑåÁ•}•™™•ÑÌ(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰Ñ•µÁ½É…ÉäÑåÁ”•™™•Ð¥Ìµ…±™½Éµ•ˆ¤(€€€€€€€€€€€€€€€•™™•Ñ}¥‘Ì€ôí•™™•Ð¹•™™•Ñ}¥™½È•™™•Ð¥¸Á•Éµ…¹•¹Ð¹¡…É…Ñ•É¥ÍÑ¥}•™™•ÑÍô(€€€€€€€€€€€€€€€¥˜±•¸¡•™™•Ñ}¥‘Ì¤€„ô±•¸¡Á•Éµ…¹•¹Ð¹¡…É…Ñ•É¥ÍÑ¥}•™™•ÑÌ¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰¡…É…Ñ•É¥ÍÑ¥Œ•™™•Ð%ÌµÕÍÐ‰”Õ¹¥ÅÕ”ˆ¤(€€€€€€€€€€€€€€€¥˜…¹ä (€€€€€€€€€€€€€€€€€€€•™™•Ð¹‘ÕÉ…Ñ¥½¸¹½Ð¥¸ì‰Á•ÉÍ¥ÍÑ•¹Ðˆ°€‰Õ¹Ñ¥±}•¹‘}½™}ÑÕÉ¸‰ô(€€€€€€€€€€€€€€€€€€€™½È•™™•Ð¥¸Á•Éµ…¹•¹Ð¹¡…É…Ñ•É¥ÍÑ¥}•™™•ÑÌ(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰¡…É…Ñ•É¥ÍÑ¥Œ•™™•Ð‘ÕÉ…Ñ¥½¸¥Ìµ…±™½Éµ•ˆ¤(€€€€€€€€€€€€€€€¥˜…¹ä (€€€€€€€€€€€€€€€€€€€‘•Á•¹‘•¹ä¹½Ð¥¸•™™•Ñ}¥‘Ì(€€€€€€€€€€€€€€€€€€€™½È•™™•Ð¥¸Á•Éµ…¹•¹Ð¹¡…É…Ñ•É¥ÍÑ¥}•™™•ÑÌ(€€€€€€€€€€€€€€€€€€€™½È‘•Á•¹‘•¹ä¥¸•™™•Ð¹‘•Á•¹‘Í}½¸(€€€€€€€€€€€€€€€€¤è(€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰¡…É…Ñ•É¥ÍÑ¥Œ•™™•Ð‘•Á•¹‘•¹ä¥Ìµ¥ÍÍ¥¹œˆ¤(€€€€€€€€€€€€€€€¥˜Á•Éµ…¹•¹Ð¹¥Í}É•…ÑÕÉ”…¹Á•Éµ…¹•¹Ð¹¡…Í}É•ÁÉ•Í•¹Ñ•‘}Á½Ý•É}Ñ½Õ¡¹•ÍÌè(€€€€€€€€€€€€€€€€€€€ÑÉäè(€€€€€€€€€€€€€€€€€€€€€€€Á•Éµ…¹•¹Ð¹•Ù…±Õ…Ñ•}Á½Ý•É}Ñ½Õ¡¹•ÍÌ ¤(€€€€€€€€€€€€€€€€€€€•á•ÁÐY…±Õ•ÉÉ½È…Ì•ÉÉ½Èè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È¡ÍÑÈ¡•ÉÉ½È¤¤™É½´•ÉÉ½È(€€€€€€€€€€€€€€€¥˜€‰1••¹‘…Éäˆ¥¸Á•Éµ…¹•¹Ð¹…É¹ÑåÁ•}±¥¹”è(€€€€€€€€€€€€€€€€€€€¥˜Á•Éµ…¹•¹Ð¹…É¹¹…µ”¥¸±••¹‘…Éå}¹…µ•Ìè(€€€€€€€€€€€€€€€€€€€€€€€É…¥Í”ÍÍ•ÉÑ¥½¹ÉÉ½È ‰±••¹ÉÕ±”±•™Ð‘ÕÁ±¥…Ñ”¹…µ•Ì½¸‰…ÑÑ±•™¥•±ˆ¤(€€€€€€€€€€€€€€€€€€€±••¹‘…Éå}¹…µ•Ì¹…‘¡Á•Éµ…¹•¹Ð¹…É¹¹…µ”¤((€€€‘•˜¡•­}±¥™”¡Í•±˜¤€´ø9½¹”è(€€€€€€€¹•Ý±å}±½ÍÐ€ômt(€€€€€€€™½È¥¹‘•à°Á±…å•È¥¸•¹Õµ•É…Ñ”¡Í•±˜¹Á±…å•ÉÌ¤è(€€€€€€€€€€€¥˜Á±…å•È¹±¥™”€ðô€À…¹¹½ÐÁ±…å•È¹±½ÍÐè(€€€€€€€€€€€€€€€Á±…å•È¹±½ÍÐ€ôQÉÕ”(€€€€€€€€€€€€€€€Á±…å•È¹±½ÍÍ}É•…Í½¸€ô€‰±¥™•}é•É½}½É}±•ÍÌˆ(€€€€€€€€€€€€€€€¹•Ý±å}±½ÍÐ¹…ÁÁ•¹¡¥¹‘•à¤(€€€€€€€€€€€€€€€Í•±˜¹±½œ ‰Á±…å•É}±½ÍÐˆ°Á±…å•ÈõÁ±…å•È¹¹…µ”°É•…Í½¸õÁ±…å•È¹±½ÍÍ}É•…Í½¸¤(€€€€€€€¥˜±•¸¡¹•Ý±å}±½ÍÐ¤€ôô€Èè(€€€€€€€€€€€Í•±˜¹Ý¥¹¹•È€ô9½¹”(€€€€€€€€€€€Í•±˜¹Ñ•Éµ¥¹…±}‘É…Ü€ôQÉÕ”(€€€€€€€€€€€Í•±˜¹±½œ ‰…µ•}‘É…Üˆ°É•…Í½¸ô‰Í¥µÕ±Ñ…¹•½ÕÍ}Á±…å•É}±½ÍÌˆ¤(€€€€€€€•±¥˜¹•Ý±å}±½ÍÐè(€€€€€€€€€€€Í•±˜¹Ý¥¹¹•È€ô€Ä€´¹•Ý±å}±½ÍÑlÁt((€€€ÁÉ½Á•ÉÑä(€€€‘•˜¥Í}Ñ•Éµ¥¹…°¡Í•±˜¤€´ø‰½½°è(€€€€€€€É•ÑÕÉ¸Í•±˜¹Ý¥¹¹•È¥Ì¹½Ð9½¹”½ÈÍ•±˜¹Ñ•Éµ¥¹…±}‘É…Ü((€€€‘•˜É•½É‘}½¹™½Éµ…¹•}ÍÑ½À (€€€€€€€Í•±˜°­¥¹èÍÑÈ°‰•™½É•}™¥¹•ÉÁÉ¥¹ÐèÍÑÈ°€¨°‘•Ñ…¥°èÍÑÈ(€€€€¤€´ø½¹™½Éµ…¹•MÑ½ÁI•½Éè(€€€€€€€€ˆˆ‰I•½É…¸¥±±•…°µµÕÑ…Ñ¥½¸½ÈÕ¹±…ÍÍ¥™¥•µÉ•… ÍÑ½À‘•Ñ•Éµ¥¹¥ÍÑ¥…±±ä¸ˆˆˆ(€€€€€€€¥˜­¥¹¹½Ð¥¸ì‰¥±±•…±}µÕÑ…Ñ¥½¸ˆ°€‰Õ¹±…ÍÍ¥™¥•‘}É•… ˆ°€‰Í¥±•¹Ñ}…ÁÁÉ½á¥µ…Ñ¥½¸‰ôè(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰½¹™½Éµ…¹”ÍÑ½À­¥¹¥ÌÕ¹ÍÕÁÁ½ÉÑ•ˆ¤(€€€€€€€…™Ñ•È€ôÍ•±˜¹…ÕÑ¡½É¥Ñ…Ñ¥Ù•}ÍÑ…Ñ•}™¥¹•ÉÁÉ¥¹Ð ¤(€€€€€€€¥˜­¥¹€ôô€‰¥±±•…±}µÕÑ…Ñ¥½¸ˆ…¹‰•™½É•}™¥¹•ÉÁÉ¥¹Ð€ôô…™Ñ•Èè(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È ‰¥±±•…°µµÕÑ…Ñ¥½¸ÍÑ½ÀÉ•ÅÕ¥É•Ì…¸½‰Í•ÉÙ•ÍÑ…Ñ”¡…¹”ˆ¤(€€€€€€€É•½É€ô½¹™½Éµ…¹•MÑ½ÁI•½É (€€€€€€€€€€€˜‰ÍÑ½Àµí±•¸¡Í•±˜¹½¹™½Éµ…¹•}ÍÑ½Á}É•½É‘Ì¤€¬€ÄèÀÙ‘ôˆ°(€€€€€€€€€€€­¥¹°(€€€€€€€€€€€Í•±˜¹ÑÕÉ¸°(€€€€€€€€€€€Í•±˜¹Á¡…Í”°(€€€€€€€€€€€Í•±˜¹ÍÑ•À¹Ù…±Õ”°(€€€€€€€€€€€‰•™½É•}™¥¹•ÉÁÉ¥¹Ð°(€€€€€€€€€€€…™Ñ•È°(€€€€€€€€€€€‘•Ñ…¥°°(€€€€€€€€¤(€€€€€€€Í•±˜¹½¹™½Éµ…¹•}ÍÑ½Á}É•½É‘Ì¹…ÁÁ•¹¡É•½É¤(€€€€€€€É•ÑÕÉ¸É•½É((€€€‘•˜…ÕÑ¡½É¥Ñ…Ñ¥Ù•}ÍÑ…Ñ•}™¥¹•ÉÁÉ¥¹Ð¡Í•±˜¤€´øÍÑÈè(€€€€€€€€ˆˆ‰MÑ…‰±”µÕÑ…Ñ¥½¸µ‰½Õ¹‘…Éä‘¥•ÍÐ•á±Õ‘¥¹œ‘¥…¹½ÍÑ¥Ì…¹•Ù¥‘•¹”±•‘•ÉÌ¸ˆˆˆ(€€€€€€€É•ÑÕÉ¸Í¡„ÈÔØ (€€€€€€€€€€€É•ÁÈ¡Í•±˜¹}…ÕÑ¡½É¥Ñ…Ñ¥Ù•}ÍÑ…Ñ•}™¥¹•ÉÁÉ¥¹Ñ}ÁÉ•¥µ…” ¤¤¹•¹½‘” ‰ÕÑ˜´àˆ¤(€€€€€€€€¤¹¡•á‘¥•ÍÐ ¤((€€€‘•˜}…ÕÑ¡½É¥Ñ…Ñ¥Ù•}ÍÑ…Ñ•}™¥¹•ÉÁÉ¥¹Ñ}ÁÉ•¥µ…”¡Í•±˜¤€´øÑÕÁ±•m½‰©•Ð°€¸¸¹tè(€€€€€€€€ˆˆ‰I•ÑÕÉ¸Ñ¡”½µÁ±•Ñ”…¹½¹¥…°ÁÉ•¥µ…”ÕÍ•‰äÑ¡”•á¥ÍÑ¥¹œÍÑ…Ñ”™¥¹•ÉÁÉ¥¹Ð¸ˆˆˆ(€€€€€€€é½¹•Ì€ôÑÕÁ±” (€€€€€€€€€€€€ (€€€€€€€€€€€€€€€ÑÕÁ±”¡…É¹½‰©•Ñ}¥™½È…É¥¸Á±…å•È¹±¥‰É…Éä¤°(€€€€€€€€€€€€€€€ÑÕÁ±”¡…É¹½‰©•Ñ}¥™½È…É¥¸Á±…å•È¹¡…¹¤°(€€€€€€€€€€€€€€€ÑÕÁ±”¡Á•Éµ…¹•¹Ð¹½‰©•Ñ}¥™½ÈÁ•Éµ…¹•¹Ð¥¸Á±…å•È¹‰…ÑÑ±•™¥•±¤°(€€€€€€€€€€€€€€€ÑÕÁ±”¡…É¹½‰©•Ñ}¥™½È…É¥¸Á±…å•È¹É…Ù•å…É¤°(€€€€€€€€€€€€€€€ÑÕÁ±”¡…É¹½‰©•Ñ}¥™½È…É¥¸Á±…å•È¹•á¥±”¤°(€€€€€€€€€€€€€€€Á±…å•È¹±¥™”°(€€€€€€€€€€€€€€€Á±…å•È¹±½ÍÐ°(€€€€€€€€€€€€€€€Á±…å•È¹™…¥±•‘}‘É…Ý}Á•¹‘¥¹œ°(€€€€€€€€€€€€¤(€€€€€€€€€€€™½ÈÁ±…å•È¥¸Í•±˜¹Á±…å•ÉÌ(€€€€€€€€¤(€€€€€€€½É¥¥¹…°€ô€ (€€€€€€€€€€€Í•±˜¹ÑÕÉ¸°(€€€€€€€€€€€Í•±˜¹…Ñ¥Ù•}Á±…å•È°(€€€€€€€€€€€Í•±˜¹ÍÑ•À¹Ù…±Õ”°(€€€€€€€€€€€ÑÕÁ±”¡¥Ñ•´¹½‰©•Ñ}¥™½È¥Ñ•´¥¸Í•±˜¹ÍÑ…¬¤°(€€€€€€€€€€€Í•±˜¹}½µ‰…Ñ}…ÑÑ…­•ÉÌ°(€€€€€€€€€€€Í•±˜¹}½µ‰…Ñ}‰±½­Ì°(€€€€€€€€€€€é½¹•Ì°(€€€€€€€€€€€Í•±˜¹É¹œ¹ÍÑ…Ñ•}‘¥•ÍÐ°(€€€€€€€€€€€Í•±˜¹Ý¥¹¹•È°(€€€€€€€€¤(€€€€€€€É•ÑÕÉ¸½É¥¥¹…°€¬€¡QÉÕ”°¤¥˜Í•±˜¹Ñ•Éµ¥¹…±}‘É…Ü•±Í”½É¥¥¹…°((€€€‘•˜…ÕÑ¡½É¥Ñ…Ñ¥Ù•}ÍÑ…Ñ•}™¥¹•ÉÁÉ¥¹Ñ}•Ù¥‘•¹”¡Í•±˜¤€´ø‘¥ÑmÍÑÈ°½‰©•Ñtè(€€€€€€€€ˆˆ‰M•É¥…±¥é”Ñ¡”•á¥ÍÑ¥¹œ™¥¹•ÉÁÉ¥¹ÐÁÉ•¥µ…”Ý¥Ñ¡½ÕÐ‘•™¥¹¥¹œ„Í•½¹ÍÑ…Ñ”µ½‘•°¸ˆˆˆ(€€€€€€€…ÕÑ¡½É¥Ñä€ôÍ•±˜¹}…ÕÑ¡½É¥Ñ…Ñ¥Ù•}ÍÑ…Ñ•}™¥¹•ÉÁÉ¥¹Ñ}ÁÉ•¥µ…” ¤(€€€€€€€é½¹•Ì€ô…ÕÑ¡½É¥ÑålÙt(€€€€€€€É•ÑÕÉ¸ì(€€€€€€€€€€€€‰Í¡•µ”ˆè€‰•¹¥¹”ÀÜµ…ÕÑ¡½É¥Ñ…Ñ¥Ù”µÍÑ…Ñ”µ™¥¹•ÉÁÉ¥¹ÐµÁÉ•¥µ…”µØÄˆ°(€€€€€€€€€€€€‰ÑÕÉ¸ˆè…ÕÑ¡½É¥ÑålÁt°(€€€€€€€€€€€€‰…Ñ¥Ù•}Á±…å•É}¥¹‘•àˆè…ÕÑ¡½É¥ÑålÅt°(€€€€€€€€€€€€‰ÍÑ•Àˆè…ÕÑ¡½É¥ÑålÉt°(€€€€€€€€€€€€‰ÍÑ…­}½‰©•Ñ}¥‘Ìˆè±¥ÍÐ¡…ÕÑ¡½É¥ÑålÍt¤°(€€€€€€€€€€€€‰½µ‰…Ñ}…ÑÑ…­•É}¥‘Ìˆè±¥ÍÐ¡…ÕÑ¡½É¥ÑålÑt¤°(€€€€€€€€€€€€‰½µ‰…Ñ}‰±½­Ìˆèm±¥ÍÐ¡¥Ñ•´¤™½È¥Ñ•´¥¸…ÕÑ¡½É¥ÑålÕut°(€€€€€€€€€€€€‰Á±…å•ÉÌˆèl(€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€‰±¥‰É…Éå}½‰©•Ñ}¥‘Ìˆè±¥ÍÐ¡Á±…å•ÉlÁt¤°(€€€€€€€€€€€€€€€€€€€€‰¡…¹‘}½‰©•Ñ}¥‘Ìˆè±¥ÍÐ¡Á±…å•ÉlÅt¤°(€€€€€€€€€€€€€€€€€€€€‰‰…ÑÑ±•™¥•±‘}½‰©•Ñ}¥‘Ìˆè±¥ÍÐ¡Á±…å•ÉlÉt¤°(€€€€€€€€€€€€€€€€€€€€‰É…Ù•å…É‘}½‰©•Ñ}¥‘Ìˆè±¥ÍÐ¡Á±…å•ÉlÍt¤°(€€€€€€€€€€€€€€€€€€€€‰•á¥±•}½‰©•Ñ}¥‘Ìˆè±¥ÍÐ¡Á±…å•ÉlÑt¤°(€€€€€€€€€€€€€€€€€€€€‰±¥™”ˆèÁ±…å•ÉlÕt°(€€€€€€€€€€€€€€€€€€€€‰±½ÍÐˆèÁ±…å•ÉlÙt°(€€€€€€€€€€€€€€€€€€€€‰™…¥±•‘}‘É…Ý}Á•¹‘¥¹œˆèÁ±…å•ÉlÝt°(€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€™½ÈÁ±…å•È¥¸é½¹•Ì(€€€€€€€€€€€t°(€€€€€€€€€€€€‰É¹}ÍÑ…Ñ•}‘¥•ÍÐˆè…ÕÑ¡½É¥ÑålÝt°(€€€€€€€€€€€€‰Ý¥¹¹•É}¥¹‘•àˆè…ÕÑ¡½É¥Ñålát°(€€€€€€€€€€€€¨¨¡ì‰Ñ•Éµ¥¹…±}‘É…ÜˆèQÉÕ•ô¥˜Í•±˜¹Ñ•Éµ¥¹…±}‘É…Ü•±Í”íô¤°(€€€€€€€ô((€€€‘•˜}•á•ÕÑ•‘}½¹™½Éµ…¹•}É•™•É•¹•Ì¡Í•±˜¤€´ø±¥ÍÑm‘¥ÑmÍÑÈ°½‰©•Ñutè(€€€€€€€€ˆˆ‰%¹‘•àµ…ÑÕÉ”Ñ¥½¸•Ù¥‘•¹”Ý¥Ñ¡½ÕÐÉ•Á±…¥¹œ½ÈÝ•…­•¹¥¹œÑ¡…Ð•Ù¥‘•¹”¸ˆˆˆ(€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}ÍÑÕ¹}¡¥ÍÑ½Éä ¤(€€€€€€€Í•±˜¹}¡•­}µ¥±±}Ñ¡É••}¡¥ÍÑ½Éä ¤(€€€€€€€Í•±˜¹}Ù…±¥‘…Ñ•}­É…¹}É•™¥±±}±¥Ù” ¤(€€€€€€€Í•±˜¹}¡•­}©ÕÉå}É¥}¡¥ÍÑ½Éä ¤(€€€€€€€Í•±˜¹}¡•­}Ù¥¥±…¹Ñ•}±¥Ù” ¤(€€€€€€€Í•±˜¹Ù…±¥‘…Ñ•}™½½‘}Í•…É¡}Í¹…ÁÍ¡½Ñ}•Ù¥‘•¹” (€€€€€€€€€€€ì‰•Ù•¹ÑÌˆèÍ•±˜¹•Ù•¹ÑÌ°€‰™½½‘}Í•…É¡}•Ù¥‘•¹”ˆèÍ•±˜¹™½½‘}Í•…É¡}Í¹…ÁÍ¡½Ñ}•Ù¥‘•¹” ¥ô(€€€€€€€€¤(€€€€€€€Í•±˜¹Ù…±¥‘…Ñ•}‘É…Ý}‘¥Í…É‘}Í¹…ÁÍ¡½Ñ}•Ù¥‘•¹”¡ì‰•Ù•¹ÑÌˆèÍ•±˜¹•Ù•¹ÑÍô¤(€€€€€€€É•™•É•¹•Ìè±¥ÍÑm‘¥ÑmÍÑÈ°½‰©•Ñut€ômt((€€€€€€€‘•˜…‘¡­¥¹èÍÑÈ°•Ù¥‘•¹•}¥èÍÑÈ°Í½ÕÉ•}¥èÍÑÈ°™É…µ•¹ÐèÍÑÈ¤€´ø9½¹”è(€€€€€€€€€€€Í½ÕÉ”€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡Í½ÕÉ•}¥¤(€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡Í½ÕÉ”°€¡…É‘=‰©•Ð°MÑ…­=‰©•Ð°A•Éµ…¹•¹Ð¤¤è(€€€€€€€€€€€€€€€É•ÑÕÉ¸(€€€€€€€€€€€™É…µ•¹ÑÌ€ôÍ•±˜¹}Í•µ…¹Ñ¥}™É…µ•¹ÑÌ¡Í½ÕÉ”¹…É¤(€€€€€€€€€€€¥˜™É…µ•¹Ð¹½Ð¥¸™É…µ•¹ÑÌè(€€€€€€€€€€€€€€€É•ÑÕÉ¸(€€€€€€€€€€€¥¹‘•à€ô™É…µ•¹ÑÌ¹¥¹‘•à¡™É…µ•¹Ð¤(€€€€€€€€€€€É•™•É•¹•Ì¹…ÁÁ•¹ (€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€‰•Ù¥‘•¹•}­¥¹ˆè­¥¹°(€€€€€€€€€€€€€€€€€€€€‰•Ù¥‘•¹•}¥ˆè•Ù¥‘•¹•}¥°(€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}¥ˆèÍ½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€‰Í•µ…¹Ñ¥}­•äˆèÍ•µ…¹Ñ¥}­•ä (€€€€€€€€€€€€€€€€€€€€€€€•Ñ…ÑÑÈ¡Í½ÕÉ”¹…É°€‰½É…±•}¥ˆ°€ˆˆ¤°€À°¥¹‘•à°™É…µ•¹Ð(€€€€€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€€€€€€‰½É…±•}™É…µ•¹Ðˆè™É…µ•¹Ð°(€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€¤((€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹…Ñ¥Ù…Ñ¥½¹}•Ù¥‘•¹”è(€€€€€€€€€€€¥˜¥Ñ•´¹É•Í½±Ù•è(€€€€€€€€€€€€€€€…‘ ‰…Ñ¥Ù…Ñ•‘}…‰¥±¥Ñäˆ°¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥°¥Ñ•´¹Í½ÕÉ•}¥°¥Ñ•´¹½É…±•}™É…µ•¹Ð¤(€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹™½½‘}…Ñ¥Ù…Ñ¥½¹}•Ù¥‘•¹”è(€€€€€€€€€€€¥˜¥Ñ•´¹É•Í½±Ù•è(€€€€€€€€€€€€€€€…‘ ‰™½½‘}…Ñ¥Ù…Ñ¥½¸ˆ°¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥°¥Ñ•´¹Í½ÕÉ•}¥°¥Ñ•´¹½É…±•}™É…µ•¹Ð¤(€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹Í¹•…­}•Ù¥‘•¹”è(€€€€€€€€€€€¥˜¥Ñ•´¹É•Í½±Ù•‘}½‰©•Ñ}¥¥Ì¹½Ð9½¹”è(€€€€€€€€€€€€€€€…‘ ‰Í¹•…¬ˆ°¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥°¥Ñ•´¹¡…¹‘}½‰©•Ñ}¥°¥Ñ•´¹½É…±•}™É…µ•¹Ð¤(€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹¡…¹‘}‰½ÑÑ½µ}‘É…Ý}•Ù¥‘•¹”è(€€€€€€€€€€€…‘ ‰¡…¹‘}‰½ÑÑ½µ}‘É…Üˆ°¥Ñ•´¹•Ù•¹Ñ}¥°¥Ñ•´¹Í½ÕÉ•}¥°¥Ñ•´¹½É…±•}™É…µ•¹Ð¤(€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹‘¥Í…É‘}‘É…Ý}•Ù¥‘•¹”è(€€€€€€€€€€€…‘ ‰‘¥Í…É‘}‘É…Üˆ°¥Ñ•´¹•Ù•¹Ñ}¥°¥Ñ•´¹Í½ÕÉ•}¥°¥Ñ•´¹½É…±•}™É…µ•¹Ð¤(€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹±¥™•±¥¹­}•Ù¥‘•¹”è(€€€€€€€€€€€…‘ ‰±¥™•±¥¹¬ˆ°¥Ñ•´¹•Ù•¹Ñ}¥°¥Ñ•´¹Í½ÕÉ•}¥°€‰1¥™•±¥¹¬ˆ¤(€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹•Ñ‰}‘É…¥¹}…¥¹}ÍÉå}•Ù¥‘•¹”è(€€€€€€€€€€€…‘ (€€€€€€€€€€€€€€€€‰•Ñ‰}‘É…¥¹}…¥¹}ÍÉäˆ°(€€€€€€€€€€€€€€€¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥°(€€€€€€€€€€€€€€€¥Ñ•´¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€¥Ñ•´¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€¤(€€€€€€€™½È•Ù¥‘•¹”¥¸Í•±˜¹½µ‰…Ñ}‘…µ…•}•Ù¥‘•¹”è(€€€€€€€€€€€™½È…ÍÍ¥¹µ•¹Ð¥¸•Ù¥‘•¹”¹…ÍÍ¥¹µ•¹ÑÌè(€€€€€€€€€€€€€€€Í½ÕÉ”€ôÍ•±˜¹}½‰©•ÑÌ¹•Ð¡…ÍÍ¥¹µ•¹Ð¹Í½ÕÉ•}¥¤(€€€€€€€€€€€€€€€¥˜¹½Ð¥Í¥¹ÍÑ…¹”¡Í½ÕÉ”°A•Éµ…¹•¹Ð¤è(€€€€€€€€€€€€€€€€€€€½¹Ñ¥¹Õ”(€€€€€€€€€€€€€€€¥˜…ÍÍ¥¹µ•¹Ð¹ÑÉ…µÁ±”è(€€€€€€€€€€€€€€€€€€€…‘ (€€€€€€€€€€€€€€€€€€€€€€€€‰ÑÉ…µÁ±”ˆ°(€€€€€€€€€€€€€€€€€€€€€€€˜‰½µ‰…Ðéí•Ù¥‘•¹”¹Í•ÅÕ•¹•ôéí…ÍÍ¥¹µ•¹Ð¹Í½ÕÉ•}¥‘ôéÑÉ…µÁ±”ˆ°(€€€€€€€€€€€€€€€€€€€€€€€…ÍÍ¥¹µ•¹Ð¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰QÉ…µÁ±”ˆ°(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€™½È­•åÝ½É¥¸€ ‰¥ÉÍÐÍÑÉ¥­”ˆ°€‰½Õ‰±”ÍÑÉ¥­”ˆ¤è(€€€€€€€€€€€€€€€€€€€¥˜­•åÝ½É¥¸Í•±˜¹}Í•µ…¹Ñ¥}™É…µ•¹ÑÌ¡Í½ÕÉ”¹…É¤è(€€€€€€€€€€€€€€€€€€€€€€€…‘ (€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰ÍÑÉ¥­•}‘…µ…•}ÍÑ•Àˆ°(€€€€€€€€€€€€€€€€€€€€€€€€€€€˜‰½µ‰…Ðéí•Ù¥‘•¹”¹Í•ÅÕ•¹•ôéí…ÍÍ¥¹µ•¹Ð¹Í½ÕÉ•}¥‘ôéí­•åÝ½É‘ôˆ°(€€€€€€€€€€€€€€€€€€€€€€€€€€€…ÍÍ¥¹µ•¹Ð¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€­•åÝ½É°(€€€€€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€™½È•Ù•¹Ð¥¸Í•±˜¹•Ù•¹ÑÌè(€€€€€€€€€€€¥˜…É‘%¹Ñ•ÉÁÉ•Ñ•È¹¥Í}­É…¹}É•™¥±±}™É…µ•¹Ð¡•Ù•¹Ð¹•Ð ‰½É…±•}™É…µ•¹Ðˆ¤¤è(€€€€€€€€€€€€€€€¥˜•Ù•¹Ð¹•Ð ‰•Ù•¹Ðˆ¤€ôô€‰­É…¹}É•™¥±±}½µµ¥ÑÑ•ˆ…¹•Ù•¹Ñl‰É•ÅÕ•ÍÑ•‰t€ø€Àè(€€€€€€€€€€€€€€€€€€€…‘ (€€€€€€€€€€€€€€€€€€€€€€€€‰­É…¹}É•™¥±°ˆ°(€€€€€€€€€€€€€€€€€€€€€€€•Ù•¹Ñl‰ÍÑ…­}½‰©•Ñ}¥‰t°(€€€€€€€€€€€€€€€€€€€€€€€•Ù•¹Ñl‰Í½ÕÉ•}¥‰t°(€€€€€€€€€€€€€€€€€€€€€€€•Ù•¹Ñl‰½É…±•}™É…µ•¹Ð‰t°(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€½¹Ñ¥¹Õ”(€€€€€€€€€€€¥˜•Ù•¹Ð¹•Ð ‰½É…±•}™É…µ•¹Ðˆ¤€ôô…É‘%¹Ñ•ÉÁÉ•Ñ•È¹5%11}Q!I}I59Pè(€€€€€€€€€€€€€€€¥˜•Ù•¹Ð¹•Ð ‰•Ù•¹Ðˆ¤€ôô€‰µ¥±±}Ñ¡É••}½µµ¥ÑÑ•ˆè(€€€€€€€€€€€€€€€€€€€…‘ (€€€€€€€€€€€€€€€€€€€€€€€€‰µ¥±±}Ñ¡É•”ˆ°(€€€€€€€€€€€€€€€€€€€€€€€•Ù•¹Ñl‰ÍÑ…­}½‰©•Ñ}¥‰t°(€€€€€€€€€€€€€€€€€€€€€€€•Ù•¹Ñl‰Í½ÕÉ•}¥‰t°(€€€€€€€€€€€€€€€€€€€€€€€•Ù•¹Ñl‰½É…±•}™É…µ•¹Ð‰t°(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€½¹Ñ¥¹Õ”(€€€€€€€€€€€¥˜•Ù•¹Ð¹•Ð ‰½É…±•}™É…µ•¹Ðˆ¤€ôô…É‘%¹Ñ•ÉÁÉ•Ñ•È¹)UIe}I%}I59Pè(€€€€€€€€€€€€€€€¥˜•Ù•¹Ð¹•Ð ‰•Ù•¹Ðˆ¤€ôô€‰©ÕÉå}É¥}½µµ¥ÑÑ•ˆè(€€€€€€€€€€€€€€€€€€€…‘ (€€€€€€€€€€€€€€€€€€€€€€€€‰©ÕÉå}É¥œˆ°(€€€€€€€€€€€€€€€€€€€€€€€•Ù•¹Ñl‰ÍÑ…­}½‰©•Ñ}¥‰t°(€€€€€€€€€€€€€€€€€€€€€€€•Ù•¹Ñl‰Í½ÕÉ•}¥‰t°(€€€€€€€€€€€€€€€€€€€€€€€•Ù•¹Ñl‰½É…±•}™É…µ•¹Ð‰t°(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€½¹Ñ¥¹Õ”(€€€€€€€€€€€¥˜•Ù•¹Ð¹•Ð ‰•™™•Ðˆ¤€ôô€‰•Ñ‰}Ù¥¥±…¹Ñ”ˆè(€€€€€€€€€€€€€€€½¹Ñ¥¹Õ”(€€€€€€€€€€€¥˜•Ù•¹Ð¹•Ð ‰•Ù•¹Ðˆ¤¥¸ì(€€€€€€€€€€€€€€€€‰‘…µ…•}‘•…±Ðˆ°(€€€€€€€€€€€€€€€€‰ÍÉå}½µµ¥ÑÑ•ˆ°(€€€€€€€€€€€€€€€€‰Ñ½­•¹Í}É•…Ñ•ˆ°(€€€€€€€€€€€€€€€€‰ÑÉ¥•É}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€€‰ÍÁ•±±}É•Í½±Ù•ˆ°(€€€€€€€€€€€€€€€€‰ÍÁ•±±}É•Í½±Ù•‘}¹½}•™™•Ðˆ°(€€€€€€€€€€€€€€€€‰…ÕÉ…}É•Í½±Ù•ˆ°(€€€€€€€€€€€ôè(€€€€€€€€€€€€€€€Í½ÕÉ•}¥€ô•Ù•¹Ð¹•Ð ‰Í½ÕÉ•}¥ˆ¤(€€€€€€€€€€€€€€€™É…µ•¹Ð€ô•Ù•¹Ð¹•Ð ‰½É…±•}™É…µ•¹Ðˆ¤(€€€€€€€€€€€€€€€•Ù¥‘•¹•}¥€ô•Ù•¹Ð¹•Ð ‰•Ù•¹Ñ}¥ˆ¤½È•Ù•¹Ð¹•Ð ‰ÍÑ…­}½‰©•Ñ}¥ˆ¤(€€€€€€€€€€€€€€€¥˜…±°¡¥Í¥¹ÍÑ…¹”¡Ù…±Õ”°ÍÑÈ¤™½ÈÙ…±Õ”¥¸€¡Í½ÕÉ•}¥°™É…µ•¹Ð°•Ù¥‘•¹•}¥¤¤è(€€€€€€€€€€€€€€€€€€€…‘ (€€€€€€€€€€€€€€€€€€€€€€€ÍÑÈ¡•Ù•¹Ñl‰•Ù•¹Ð‰t¤°(€€€€€€€€€€€€€€€€€€€€€€€ÍÑÈ¡•Ù¥‘•¹•}¥¤°(€€€€€€€€€€€€€€€€€€€€€€€ÍÑÈ¡Í½ÕÉ•}¥¤°(€€€€€€€€€€€€€€€€€€€€€€€ÍÑÈ¡™É…µ•¹Ð¤°(€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€Õ¹¥ÅÕ”€ôì(€€€€€€€€€€€€ (€€€€€€€€€€€€€€€ÍÑÈ¡¥Ñ•µl‰•Ù¥‘•¹•}­¥¹‰t¤°(€€€€€€€€€€€€€€€ÍÑÈ¡¥Ñ•µl‰•Ù¥‘•¹•}¥‰t¤°(€€€€€€€€€€€€€€€ÍÑÈ¡¥Ñ•µl‰Í½ÕÉ•}¥‰t¤°(€€€€€€€€€€€€€€€ÍÑÈ¡¥Ñ•µl‰Í•µ…¹Ñ¥}­•ä‰t¤°(€€€€€€€€€€€€¤è¥Ñ•´(€€€€€€€€€€€™½È¥Ñ•´¥¸É•™•É•¹•Ì(€€€€€€€ô(€€€€€€€É•ÑÕÉ¸Í½ÉÑ• (€€€€€€€€€€€Õ¹¥ÅÕ”¹Ù…±Õ•Ì ¤°(€€€€€€€€€€€­•äõ±…µ‰‘„¥Ñ•´è€¡ÍÑÈ¡¥Ñ•µl‰•Ù¥‘•¹•}­¥¹‰t¤°ÍÑÈ¡¥Ñ•µl‰•Ù¥‘•¹•}¥‰t¤¤°(€€€€€€€€¤((€€€‘•˜Í¹…ÁÍ¡½Ð¡Í•±˜¤€´ø‘¥ÑmÍÑÈ°½‰©•Ñtè(€€€€€€€É•ÑÕÉ¸ì(€€€€€€€€€€€€‰•¹¥¹•}Ù•ÉÍ¥½¸ˆè9%9}YIM%=8°(€€€€€€€€€€€€‰ÑÕÉ¸ˆèÍ•±˜¹ÑÕÉ¸°(€€€€€€€€€€€€‰ÑÕÉ¹Í}ÍÑ…ÉÑ•ˆèÍ•±˜¹ÑÕÉ¸°(€€€€€€€€€€€€‰Ñ•Éµ¥¹…°ˆèÍ•±˜¹¥Í}Ñ•Éµ¥¹…°°(€€€€€€€€€€€€‰Ñ•Éµ¥¹…±}‘É…ÜˆèÍ•±˜¹Ñ•Éµ¥¹…±}‘É…Ü°(€€€€€€€€€€€€‰…Ñ¥Ù•}Á±…å•ÈˆèÍ•±˜¹Á±…å•ÉÍmÍ•±˜¹…Ñ¥Ù•}Á±…å•Ét¹¹…µ”°(€€€€€€€€€€€€‰Á¡…Í”ˆèÍ•±˜¹Á¡…Í”°(€€€€€€€€€€€€‰ÍÑ•ÀˆèÍ•±˜¹ÍÑ•À¹Ù…±Õ”°(€€€€€€€€€€€€‰Ý¥¹¹•Èˆè9½¹”¥˜Í•±˜¹Ý¥¹¹•È¥Ì9½¹”•±Í”Í•±˜¹Á±…å•ÉÍmÍ•±˜¹Ý¥¹¹•Ét¹¹…µ”°(€€€€€€€€€€€€‰…ÕÑ¡½É¥Ñ…Ñ¥Ù•}ÍÑ…Ñ•}™¥¹•ÉÁÉ¥¹ÐˆèÍ•±˜¹…ÕÑ¡½É¥Ñ…Ñ¥Ù•}ÍÑ…Ñ•}™¥¹•ÉÁÉ¥¹Ð ¤°(€€€€€€€€€€€€‰…ÕÑ¡½É¥Ñ…Ñ¥Ù•}ÍÑ…Ñ•}™¥¹•ÉÁÉ¥¹Ñ}ÁÉ•¥µ…”ˆè€ (€€€€€€€€€€€€€€€Í•±˜¹…ÕÑ¡½É¥Ñ…Ñ¥Ù•}ÍÑ…Ñ•}™¥¹•ÉÁÉ¥¹Ñ}•Ù¥‘•¹” ¤(€€€€€€€€€€€€¤°(€€€€€€€€€€€€‰ÉÕ±•Í}•Ù•¹Ñ}•Ù¥‘•¹”ˆèl(€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€‰•Ù•¹Ñ}¥ˆè¥Ñ•´¹•Ù•¹Ñ}¥°(€€€€€€€€€€€€€€€€€€€€‰•Ù•¹Ñ}ÕÉÍ½Èˆè¥Ñ•´¹•Ù•¹Ñ}ÕÉÍ½È°(€€€€€€€€€€€€€€€€€€€€‰­¥¹ˆè¥Ñ•´¹­¥¹¹Ù…±Õ”°(€€€€€€€€€€€€€€€€€€€€‰Á±…å•É}¥¹‘•àˆè¥Ñ•´¹Á±…å•É}¥¹‘•à°(€€€€€€€€€€€€€€€€€€€€‰ÍÕ‰©•Ñ}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹ÍÕ‰©•Ñ}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}¥ˆè¥Ñ•´¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€‰Ñ…É•Ñ}Á±…å•Èˆè¥Ñ•´¹Ñ…É•Ñ}Á±…å•È°(€€€€€€€€€€€€€€€€€€€€‰…µ½Õ¹Ðˆè¥Ñ•´¹…µ½Õ¹Ð°(€€€€€€€€€€€€€€€€€€€€‰ÑÕÉ¸ˆè¥Ñ•´¹ÑÕÉ¸°(€€€€€€€€€€€€€€€€€€€€‰ÍÑ•Àˆè¥Ñ•´¹ÍÑ•À°(€€€€€€€€€€€€€€€€€€€€‰…Ñ¥Ù•}Á±…å•Èˆè¥Ñ•´¹…Ñ¥Ù•}Á±…å•È°(€€€€€€€€€€€€€€€€€€€€‰‰…ÑÑ±•™¥•±‘}…ÕÑ¡½É¥Ñäˆèl(€€€€€€€€€€€€€€€€€€€€€€€ì‰½‰©•Ñ}¥ˆè½‰©•Ñ}¥°€‰½¹ÑÉ½±±•Èˆè½¹ÑÉ½±±•Éô(€€€€€€€€€€€€€€€€€€€€€€€™½È½‰©•Ñ}¥°½¹ÑÉ½±±•È¥¸¥Ñ•´¹‰…ÑÑ±•™¥•±‘}…ÕÑ¡½É¥Ñä(€€€€€€€€€€€€€€€€€€€t°(€€€€€€€€€€€€€€€€€€€€‰‰…ÑÑ±•™¥•±‘}¡…É…Ñ•É¥ÍÑ¥Ìˆèl(€€€€€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰½‰©•Ñ}¥ˆè½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰½¹ÑÉ½±±•Èˆè½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰ÑåÁ•}±¥¹”ˆèÑåÁ•}±¥¹”°(€€€€€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€€€€€™½È½‰©•Ñ}¥°½¹ÑÉ½±±•È°ÑåÁ•}±¥¹”¥¸¥Ñ•´¹‰…ÑÑ±•™¥•±‘}¡…É…Ñ•É¥ÍÑ¥Ì(€€€€€€€€€€€€€€€€€€€t°(€€€€€€€€€€€€€€€€€€€€‰±…ÍÑ}­¹½Ý¹}‰…ÑÑ±•™¥•±ˆèl(€€€€€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰½‰©•Ñ}¥ˆè½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰½¹ÑÉ½±±•Èˆè½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰ÑåÁ•}±¥¹”ˆèÑåÁ•}±¥¹”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰¥Í}É•…ÑÕÉ”ˆè¥Í}É•…ÑÕÉ”°(€€€€€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€€€€€™½È½‰©•Ñ}¥°½¹ÑÉ½±±•È°ÑåÁ•}±¥¹”°¥Í}É•…ÑÕÉ”¥¸€ (€€€€€€€€€€€€€€€€€€€€€€€€€€€¥Ñ•´¹±…ÍÑ}­¹½Ý¹}‰…ÑÑ±•™¥•±(€€€€€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€t°(€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹}ÉÕ±•Í}•Ù•¹Ñ}•Ù¥‘•¹”(€€€€€€€€€€€t°(€€€€€€€€€€€€‰½¹™½Éµ…¹”ˆèì(€€€€€€€€€€€€€€€€‰Í•µ…¹Ñ¥}½ÕÉÉ•¹•Ìˆèl(€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€‰½ÕÉÉ•¹•}¥ˆè¥Ñ•´¹½ÕÉÉ•¹•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰Í•µ…¹Ñ¥}­•äˆè¥Ñ•´¹Í•µ…¹Ñ¥}­•ä°(€€€€€€€€€€€€€€€€€€€€€€€€‰½É…±•}¥ˆè¥Ñ•´¹½É…±•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰™…•}¥¹‘•àˆè¥Ñ•´¹™…•}¥¹‘•à°(€€€€€€€€€€€€€€€€€€€€€€€€‰™É…µ•¹Ñ}¥¹‘•àˆè¥Ñ•´¹™É…µ•¹Ñ}¥¹‘•à°(€€€€€€€€€€€€€€€€€€€€€€€€‰™É…µ•¹Ñ}¡…Í ˆè¥Ñ•´¹™É…µ•¹Ñ}¡…Í °(€€€€€€€€€€€€€€€€€€€€€€€€‰½‰©•Ñ}¥ˆè¥Ñ•´¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰½¹ÑÉ½±±•Èˆè¥Ñ•´¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€‰é½¹”ˆè¥Ñ•´¹é½¹”°(€€€€€€€€€€€€€€€€€€€€€€€€‰½É…±•}™É…µ•¹Ðˆè¥Ñ•´¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€‰±¥µ¥Ñ…Ñ¥½¹Ìˆè±¥ÍÐ¡¥Ñ•´¹±¥µ¥Ñ…Ñ¥½¹Ì¤°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÑÕÉ¸ˆè¥Ñ•´¹ÑÕÉ¸°(€€€€€€€€€€€€€€€€€€€€€€€€‰Á¡…Í”ˆè¥Ñ•´¹Á¡…Í”°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÍÑ•Àˆè¥Ñ•´¹ÍÑ•À°(€€€€€€€€€€€€€€€€€€€€€€€€‰É•¥ÍÑÉ…Ñ¥½¹}•Ù•¹Ñ}ÕÉÍ½Èˆè¥Ñ•´¹É•¥ÍÑÉ…Ñ¥½¹}•Ù•¹Ñ}ÕÉÍ½È°(€€€€€€€€€€€€€€€€€€€€€€€€‰±…ÍÍ¥™¥…Ñ¥½¸ˆè€ (€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰É•…¡•‘}Õ¹ÍÕÁÁ½ÉÑ•ˆ(€€€€€€€€€€€€€€€€€€€€€€€€€€€¥˜…¹ä (€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€Ý¥Ñ¹•ÍÌ¹½ÕÉÉ•¹•}¥€ôô¥Ñ•´¹½ÕÉÉ•¹•}¥(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€™½ÈÝ¥Ñ¹•ÍÌ¥¸Í•±˜¹½ÁÁ½ÉÑÕ¹¥Ñå}Ý¥Ñ¹•ÍÍ•Ì(€€€€€€€€€€€€€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€€€€€€€€€€€€€•±Í”€‰ÁÉ•Í•¹Ñ}Õ¹É•…¡•ˆ(€€€€€€€€€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹Í•µ…¹Ñ¥}½ÕÉÉ•¹•Ì(€€€€€€€€€€€€€€€t°(€€€€€€€€€€€€€€€€‰½ÁÁ½ÉÑÕ¹¥Ñå}Ý¥Ñ¹•ÍÍ•Ìˆèl(€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€‰Ý¥Ñ¹•ÍÍ}¥ˆè¥Ñ•´¹Ý¥Ñ¹•ÍÍ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰½ÁÁ½ÉÑÕ¹¥Ñå}­•äˆè¥Ñ•´¹½ÁÁ½ÉÑÕ¹¥Ñå}­•ä°(€€€€€€€€€€€€€€€€€€€€€€€€‰½ÕÉÉ•¹•}¥ˆè¥Ñ•´¹½ÕÉÉ•¹•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰Í•µ…¹Ñ¥}­•äˆè¥Ñ•´¹Í•µ…¹Ñ¥}­•ä°(€€€€€€€€€€€€€€€€€€€€€€€€‰½‰©•Ñ}¥ˆè¥Ñ•´¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰½¹ÑÉ½±±•Èˆè¥Ñ•´¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€‰½É…±•}™É…µ•¹Ðˆè¥Ñ•´¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÑÕÉ¸ˆè¥Ñ•´¹ÑÕÉ¸°(€€€€€€€€€€€€€€€€€€€€€€€€‰Á¡…Í”ˆè¥Ñ•´¹Á¡…Í”°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÍÑ•Àˆè¥Ñ•´¹ÍÑ•À°(€€€€€€€€€€€€€€€€€€€€€€€€‰…ÕÍ•}­¥¹ˆè¥Ñ•´¹…ÕÍ•}­¥¹°(€€€€€€€€€€€€€€€€€€€€€€€€‰…ÕÍ•}¥ˆè¥Ñ•´¹…ÕÍ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰…ÕÍ•}ÍÕ‰©•Ñ}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹…ÕÍ•}ÍÕ‰©•Ñ}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}é½¹”ˆè¥Ñ•´¹Í½ÕÉ•}é½¹”°(€€€€€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}½¹ÑÉ½±±•Èˆè¥Ñ•´¹Í½ÕÉ•}½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€‰…ÕÍ•}ÍÕ‰©•Ñ}é½¹•Ìˆè±¥ÍÐ¡¥Ñ•´¹…ÕÍ•}ÍÕ‰©•Ñ}é½¹•Ì¤°(€€€€€€€€€€€€€€€€€€€€€€€€‰…ÕÍ•}•Ù•¹Ñ}­¥¹ˆè¥Ñ•´¹…ÕÍ•}•Ù•¹Ñ}­¥¹°(€€€€€€€€€€€€€€€€€€€€€€€€‰±…ÍÍ¥™¥…Ñ¥½¸ˆè¥Ñ•´¹±…ÍÍ¥™¥…Ñ¥½¸¹Ù…±Õ”°(€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹½ÁÁ½ÉÑÕ¹¥Ñå}Ý¥Ñ¹•ÍÍ•Ì(€€€€€€€€€€€€€€€t°(€€€€€€€€€€€€€€€€‰½ÁÁ½ÉÑÕ¹¥Ñå}½¹Ñ•áÑÌˆèl(€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€‰½¹Ñ•áÑ}¥ˆè¥Ñ•´¹½¹Ñ•áÑ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰½¹Ñ•áÑ}­•äˆè¥Ñ•´¹½¹Ñ•áÑ}­•ä°(€€€€€€€€€€€€€€€€€€€€€€€€‰½¹Ñ•áÑ}­¥¹ˆè¥Ñ•´¹½¹Ñ•áÑ}­¥¹°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÑÕÉ¸ˆè¥Ñ•´¹ÑÕÉ¸°(€€€€€€€€€€€€€€€€€€€€€€€€‰Á¡…Í”ˆè¥Ñ•´¹Á¡…Í”°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÍÑ•Àˆè¥Ñ•´¹ÍÑ•À°(€€€€€€€€€€€€€€€€€€€€€€€€‰…Ñ¥Ù•}Á±…å•Èˆè¥Ñ•´¹…Ñ¥Ù•}Á±…å•È°(€€€€€€€€€€€€€€€€€€€€€€€€‰½¹ÑÉ½±±•Èˆè¥Ñ•´¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}¥ˆè¥Ñ•´¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÍÕ‰©•Ñ}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹ÍÕ‰©•Ñ}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÍÕ‰©•Ñ}é½¹•Ìˆè±¥ÍÐ¡¥Ñ•´¹ÍÕ‰©•Ñ}é½¹•Ì¤°(€€€€€€€€€€€€€€€€€€€€€€€€‰™…ÑÌˆèí­•äèÙ…±Õ”™½È­•ä°Ù…±Õ”¥¸¥Ñ•´¹™…ÑÍô°(€€€€€€€€€€€€€€€€€€€€€€€€‰•Ù•¹Ñ}¥ˆè¥Ñ•´¹•Ù•¹Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÍÑ…­}½‰©•Ñ}¥ˆè¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÍÑ…Ñ•}™¥¹•ÉÁÉ¥¹Ðˆè¥Ñ•´¹ÍÑ…Ñ•}™¥¹•ÉÁÉ¥¹Ð°(€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹½ÁÁ½ÉÑÕ¹¥Ñå}½¹Ñ•áÑÌ(€€€€€€€€€€€€€€€t°(€€€€€€€€€€€€€€€€‰ÍÑ½Á}É•½É‘Ìˆèl(€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€‰ÍÑ½Á}¥ˆè¥Ñ•´¹ÍÑ½Á}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰­¥¹ˆè¥Ñ•´¹­¥¹°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÑÕÉ¸ˆè¥Ñ•´¹ÑÕÉ¸°(€€€€€€€€€€€€€€€€€€€€€€€€‰Á¡…Í”ˆè¥Ñ•´¹Á¡…Í”°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÍÑ•Àˆè¥Ñ•´¹ÍÑ•À°(€€€€€€€€€€€€€€€€€€€€€€€€‰‰•™½É•}™¥¹•ÉÁÉ¥¹Ðˆè¥Ñ•´¹‰•™½É•}™¥¹•ÉÁÉ¥¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€‰…™Ñ•É}™¥¹•ÉÁÉ¥¹Ðˆè¥Ñ•´¹…™Ñ•É}™¥¹•ÉÁÉ¥¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€‰‘•Ñ…¥°ˆè¥Ñ•´¹‘•Ñ…¥°°(€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹½¹™½Éµ…¹•}ÍÑ½Á}É•½É‘Ì(€€€€€€€€€€€€€€€t°(€€€€€€€€€€€€€€€€‰•á•ÕÑ•‘}É•™•É•¹•ÌˆèÍ•±˜¹}•á•ÕÑ•‘}½¹™½Éµ…¹•}É•™•É•¹•Ì ¤°(€€€€€€€€€€€ô°(€€€€€€€€€€€€‰µ¥±±}Ñ¡É••}•Ù¥‘•¹”ˆèÍ•±˜¹µ¥±±}Ñ¡É••}Í¹…ÁÍ¡½Ñ}•Ù¥‘•¹” ¤°(€€€€€€€€€€€€‰­É…¹}É•™¥±±}•Ù¥‘•¹”ˆèÍ•±˜¹­É…¹}É•™¥±±}Í¹…ÁÍ¡½Ñ}•Ù¥‘•¹” ¤°(€€€€€€€€€€€€‰©ÕÉå}É¥}•Ù¥‘•¹”ˆèÍ•±˜¹©ÕÉå}É¥}Í¹…ÁÍ¡½Ñ}•Ù¥‘•¹” ¤°(€€€€€€€€€€€€‰Ù¥¥±…¹Ñ•}•Ù¥‘•¹”ˆèÍ•±˜¹Ù¥¥±…¹Ñ•}Í¹…ÁÍ¡½Ñ}•Ù¥‘•¹” ¤°(€€€€€€€€€€€€‰™½½‘}Í•…É¡}•Ù¥‘•¹”ˆèÍ•±˜¹™½½‘}Í•…É¡}Í¹…ÁÍ¡½Ñ}•Ù¥‘•¹” ¤°(€€€€€€€€€€€€‰É¹œˆèì(€€€€€€€€€€€€€€€€‰Í••ˆèÍ•±˜¹É¹œ¹Í••°(€€€€€€€€€€€€€€€€‰ÍÑ…Ñ•}‘¥•ÍÐˆèÍ•±˜¹É¹œ¹ÍÑ…Ñ•}‘¥•ÍÐ°(€€€€€€€€€€€€€€€€‰É•½É‘Ìˆèl(€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€‰Í•ÅÕ•¹”ˆèÉ•½É¹Í•ÅÕ•¹”°(€€€€€€€€€€€€€€€€€€€€€€€€‰‘½µ…¥¸ˆèÉ•½É¹‘½µ…¥¸°(€€€€€€€€€€€€€€€€€€€€€€€€‰½Á•É…Ñ¥½¸ˆèÉ•½É¹½Á•É…Ñ¥½¸°(€€€€€€€€€€€€€€€€€€€€€€€€‰É•ÍÕ±Ðˆè€ (€€€€€€€€€€€€€€€€€€€€€€€€€€€±¥ÍÐ¡É•½É¹É•ÍÕ±Ð¤(€€€€€€€€€€€€€€€€€€€€€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡É•½É¹É•ÍÕ±Ð°ÑÕÁ±”¤(€€€€€€€€€€€€€€€€€€€€€€€€€€€•±Í”É•½É¹É•ÍÕ±Ð(€€€€€€€€€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÍÑ…Ñ•}‰•™½É”ˆèÉ•½É¹ÍÑ…Ñ•}‰•™½É”°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÍÑ…Ñ•}…™Ñ•ÈˆèÉ•½É¹ÍÑ…Ñ•}…™Ñ•È°(€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€™½ÈÉ•½É¥¸Í•±˜¹É¹œ¹É•½É‘Ì(€€€€€€€€€€€€€€€t°(€€€€€€€€€€€ô°(€€€€€€€€€€€€‰ÍÑ…¬ˆèl(€€€€€€€€€€€€€€€€ (€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€‰½‰©•Ñ}¥ˆè•¹ÑÉä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰­¥¹ˆè€‰ÍÁ•±°ˆ°(€€€€€€€€€€€€€€€€€€€€€€€€‰…Éˆè•¹ÑÉä¹…É¹¹…µ”°(€€€€€€€€€€€€€€€€€€€€€€€€‰½Ý¹•Èˆè•¹ÑÉä¹½Ý¹•È°(€€€€€€€€€€€€€€€€€€€€€€€€‰½¹ÑÉ½±±•Èˆè•¹ÑÉä¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€‰…ÍÑ}­¥¹ˆè•¹ÑÉä¹…ÍÑ}­¥¹¹Ù…±Õ”°(€€€€€€€€€€€€€€€€€€€€€€€€‰Ñ…É•Ñ}¥ˆè•¹ÑÉä¹Ñ…É•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€¨¨¡ì‰Ñ…É•Ñ}¥‘Ìˆè±¥ÍÐ¡•¹ÑÉä¹Ñ…É•Ñ}¥‘Ì¥ô¥˜•¹ÑÉä¹Ñ…É•Ñ}¥‘Ì•±Í”íô¤°(€€€€€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}Ñ…É•Ñ}¥ˆè•¹ÑÉä¹Í½ÕÉ•}Ñ…É•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰µ½‘•}™É…µ•¹Ðˆè•¹ÑÉä¹µ½‘•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€‰­¥­•É}Í…É¥™¥•}¥ˆè•¹ÑÉä¹­¥­•É}Í…É¥™¥•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰Í¹•…­}É•ÑÕÉ¹•‘}…ÑÑ…­•É}¥ˆè•¹ÑÉä¹Í¹•…­}É•ÑÕÉ¹•‘}…ÑÑ…­•É}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰Í¹•…­}É•ÑÕÉ¹•‘}¡…¹‘}¥ˆè•¹ÑÉä¹Í¹•…­}É•ÑÕÉ¹•‘}¡…¹‘}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰Í¹•…­}‘•™•¹‘¥¹}Á±…å•Èˆè•¹ÑÉä¹Í¹•…­}‘•™•¹‘¥¹}Á±…å•È°(€€€€€€€€€€€€€€€€€€€€€€€€‰Í¹•…­}½É…±•}™É…µ•¹Ðˆè•¹ÑÉä¹Í¹•…­}½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€‰Í¹•…­}µ…¹…}Í½ÕÉ•}¥‘Ìˆè±¥ÍÐ¡•¹ÑÉä¹Í¹•…­}µ…¹…}Í½ÕÉ•}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡•¹ÑÉä°MÑ…­=‰©•Ð¤(€€€€€€€€€€€€€€€€€€€•±Í”ì(€€€€€€€€€€€€€€€€€€€€€€€€‰½‰©•Ñ}¥ˆè•¹ÑÉä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰­¥¹ˆè€‰…Ñ¥Ù…Ñ•‘}…‰¥±¥Ñäˆ°(€€€€€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ”ˆè•¹ÑÉä¹Í½ÕÉ•}…É¹¹…µ”°(€€€€€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}¥ˆè•¹ÑÉä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰½¹ÑÉ½±±•Èˆè•¹ÑÉä¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€‰½É…±•}™É…µ•¹Ðˆè•¹ÑÉä¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€‰Ñ…É•Ñ}¥‘Ìˆè±¥ÍÐ¡•¹ÑÉä¹Ñ…É•Ñ}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€€€€€‰¡½¥•}¥‘Ìˆè±¥ÍÐ¡•¹ÑÉä¹¡½¥•}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€¥˜¥Í¥¹ÍÑ…¹”¡•¹ÑÉä°Ñ¥Ù…Ñ•‘‰¥±¥Ñå=‰©•Ð¤(€€€€€€€€€€€€€€€€€€€•±Í”ì(€€€€€€€€€€€€€€€€€€€€€€€€‰½‰©•Ñ}¥ˆè•¹ÑÉä¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰­¥¹ˆè€‰ÑÉ¥•É•‘}…‰¥±¥Ñäˆ°(€€€€€€€€€€€€€€€€€€€€€€€€¨¨ (€€€€€€€€€€€€€€€€€€€€€€€€€€€ì‰Ñ…É•Ñ}¥ˆè•¹ÑÉä¹Ñ…É•Ñ}¥‘ô(€€€€€€€€€€€€€€€€€€€€€€€€€€€¥˜•¹ÑÉä¹•™™•Ð(€€€€€€€€€€€€€€€€€€€€€€€€€€€¥¸ì(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹Q	}QA}MQU8°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹I9Q}=5	Q}U9QA}%8°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€QÉ¥•É™™•Ð¹EU%A59Q}MU	QeA}9QIe}QQ °(€€€€€€€€€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€€€€€€€€€•±Í”íô(€€€€€€€€€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€€€€€€€€€€¨¨ (€€€€€€€€€€€€€€€€€€€€€€€€€€€ì‰É…¹Ñ}Í½ÕÉ•}¥ˆèÍ•±˜¹}ÑÉ¥•ÉÍm•¹ÑÉä¹ÑÉ¥•É}¥‘t¹É…¹Ñ}Í½ÕÉ•}¥‘ô(€€€€€€€€€€€€€€€€€€€€€€€€€€€¥˜•¹ÑÉä¹•™™•Ð¥ÌQÉ¥•É™™•Ð¹I9Q}=5	Q}U9QA}%8(€€€€€€€€€€€€€€€€€€€€€€€€€€€•±Í”íô(€€€€€€€€€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ”ˆè•¹ÑÉä¹Í½ÕÉ•}…É¹¹…µ”°(€€€€€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}¥ˆè•¹ÑÉä¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰½¹ÑÉ½±±•Èˆè•¹ÑÉä¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€‰•™™•Ðˆè•¹ÑÉä¹•™™•Ð¹Ù…±Õ”°(€€€€€€€€€€€€€€€€€€€€€€€€‰•Ù•¹Ñ}¥ˆè•¹ÑÉä¹•Ù•¹Ð¹•Ù•¹Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÑÉ¥•É}¥ˆè•¹ÑÉä¹ÑÉ¥•É}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰Ñ…É•Ñ}¥‘Ìˆè±¥ÍÐ¡•¹ÑÉä¹Ñ…É•Ñ}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€¤(€€€€€€€€€€€€€€€™½È•¹ÑÉä¥¸Í•±˜¹ÍÑ…¬(€€€€€€€€€€€t°(€€€€€€€€€€€€‰ÁÉ¥½É¥Ñäˆè€ (€€€€€€€€€€€€€€€9½¹”(€€€€€€€€€€€€€€€¥˜Í•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¥Ì9½¹”(€€€€€€€€€€€€€€€•±Í”ì(€€€€€€€€€€€€€€€€€€€€‰•Á½ ˆèÍ•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¹•Á½ °(€€€€€€€€€€€€€€€€€€€€‰Á±…å•É}¥¹‘•àˆèÍ•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¹Á±…å•É}¥¹‘•à°(€€€€€€€€€€€€€€€€€€€€‰½¹Í•ÕÑ¥Ù•}Á…ÍÍ•Ìˆè±¥ÍÐ¡Í•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¹½¹Í•ÕÑ¥Ù•}Á…ÍÍ•Ì¤°(€€€€€€€€€€€€€€€€€€€€‰É•Í½±ÕÑ¥½¹}Á•¹‘¥¹œˆèÍ•±˜¹ÁÉ¥½É¥Ñå}ÍÑ…Ñ”¹É•Í½±ÕÑ¥½¹}Á•¹‘¥¹œ°(€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€¤°(€€€€€€€€€€€€‰Á•¹‘¥¹}ÑÉ¥•ÉÌˆèmÑÉ¥•È¹ÑÉ¥•É}¥™½ÈÑÉ¥•È¥¸Í•±˜¹Á•¹‘¥¹}ÑÉ¥•ÉÍt°(€€€€€€€€€€€€‰ÍÑÕ¹}¡¥ÍÑ½Éäˆèl(€€€€€€€€€€€€€€€ì‰•Ù•¹Ñ}ÕÉÍ½ÈˆèÕÉÍ½È°€‰É•½Éˆè‘¥Ð¡É•½É¥ô(€€€€€€€€€€€€€€€™½ÈÕÉÍ½È°É•½É¥¸Í•±˜¹}ÍÑÕ¹}¡¥ÍÑ½Éä(€€€€€€€€€€€t°(€€€€€€€€€€€€‰ÍÉäˆèl(€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€‰•Ù•¹Ñ}¥ˆè¥Ñ•´¹•Ù•¹Ñ}¥°(€€€€€€€€€€€€€€€€€€€€‰Á±…å•É}¥¹‘•àˆè¥Ñ•´¹Á±…å•É}¥¹‘•à°(€€€€€€€€€€€€€€€€€€€€‰É•ÅÕ•ÍÑ•ˆè¥Ñ•´¹É•ÅÕ•ÍÑ•°(€€€€€€€€€€€€€€€€€€€€‰¥¹ÍÁ•Ñ•‘}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹¥¹ÍÁ•Ñ•‘}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰Ñ½Á}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹Ñ½Á}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰‰½ÑÑ½µ}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹‰½ÑÑ½µ}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}…Éˆè¥Ñ•´¹Í½ÕÉ•}…É°(€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}¥ˆè¥Ñ•´¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€‰½É…±•}™É…µ•¹Ðˆè¥Ñ•´¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹ÍÉå}•Ù¥‘•¹”(€€€€€€€€€€€t°(€€€€€€€€€€€€‰•Ñ‰}‘É…¥¹}…¥¹}ÍÉäˆèl(€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€‰•Ù•¹Ñ}¥ˆè¥Ñ•´¹•Ù•¹Ñ}¥°(€€€€€€€€€€€€€€€€€€€€‰ÍÑ…­}½‰©•Ñ}¥ˆè¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}¥ˆè¥Ñ•´¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}…Éˆè¥Ñ•´¹Í½ÕÉ•}…É°(€€€€€€€€€€€€€€€€€€€€‰½¹ÑÉ½±±•Èˆè¥Ñ•´¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€‰½ÁÁ½¹•¹Ðˆè¥Ñ•´¹½ÁÁ½¹•¹Ð°(€€€€€€€€€€€€€€€€€€€€‰½É…±•}™É…µ•¹Ðˆè¥Ñ•´¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€‰ÑÕÉ¸ˆè¥Ñ•´¹ÑÕÉ¸°(€€€€€€€€€€€€€€€€€€€€‰ÍÑ•Àˆè¥Ñ•´¹ÍÑ•À°(€€€€€€€€€€€€€€€€€€€€‰½ÁÁ½¹•¹Ñ}±¥™•}‰•™½É”ˆè¥Ñ•´¹½ÁÁ½¹•¹Ñ}±¥™•}‰•™½É”°(€€€€€€€€€€€€€€€€€€€€‰½ÁÁ½¹•¹Ñ}±¥™•}…™Ñ•Èˆè¥Ñ•´¹½ÁÁ½¹•¹Ñ}±¥™•}…™Ñ•È°(€€€€€€€€€€€€€€€€€€€€‰½¹ÑÉ½±±•É}±¥™•}‰•™½É”ˆè¥Ñ•´¹½¹ÑÉ½±±•É}±¥™•}‰•™½É”°(€€€€€€€€€€€€€€€€€€€€‰½¹ÑÉ½±±•É}±¥™•}…™Ñ•Èˆè¥Ñ•´¹½¹ÑÉ½±±•É}±¥™•}…™Ñ•È°(€€€€€€€€€€€€€€€€€€€€‰ÍÉå}•Ù•¹Ñ}¥ˆè¥Ñ•´¹ÍÉå}•Ù•¹Ñ}¥°(€€€€€€€€€€€€€€€€€€€€‰Ñ•Éµ¥¹…±}…™Ñ•É}±¥™•}±½ÍÌˆè¥Ñ•´¹Ñ•Éµ¥¹…±}…™Ñ•É}±¥™•}±½ÍÌ°(€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹•Ñ‰}‘É…¥¹}…¥¹}ÍÉå}•Ù¥‘•¹”(€€€€€€€€€€€t°(€€€€€€€€€€€€‰½µ‰…Ñ}‘…µ…”ˆèì(€€€€€€€€€€€€€€€€‰ÍÑ•Á}­¥¹ˆèÍ•±˜¹}½µ‰…Ñ}‘…µ…•}ÍÑ•Á}­¥¹¹Ù…±Õ”°(€€€€€€€€€€€€€€€€‰Í•ÅÕ•¹”ˆèÍ•±˜¹}½µ‰…Ñ}‘…µ…•}ÍÑ•Á}¹Õµ‰•È°(€€€€€€€€€€€€€€€€‰Ñ½Ñ…±}ÍÑ•ÁÌˆèÍ•±˜¹}½µ‰…Ñ}‘…µ…•}Ñ½Ñ…±}ÍÑ•ÁÌ°(€€€€€€€€€€€€€€€€‰™¥ÉÍÑ}ÅÕ…±¥™¥•‘}¥‘Ìˆè±¥ÍÐ¡Í•±˜¹}™¥ÉÍÑ}‘…µ…•}ÅÕ…±¥™¥•‘}¥‘Ì¤°(€€€€€€€€€€€€€€€€‰É•Õ±…É}¥¹¥Ñ¥…±}¥‘Ìˆè±¥ÍÐ¡Í•±˜¹}É•Õ±…É}‘…µ…•}¥¹¥Ñ¥…±}¥‘Ì¤°(€€€€€€€€€€€€€€€€‰•Ù¥‘•¹”ˆèl(€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€‰­¥¹ˆè¥Ñ•´¹­¥¹¹Ù…±Õ”°(€€€€€€€€€€€€€€€€€€€€€€€€‰Í•ÅÕ•¹”ˆè¥Ñ•´¹Í•ÅÕ•¹”°(€€€€€€€€€€€€€€€€€€€€€€€€‰Ñ½Ñ…±}ÍÑ•ÁÌˆè¥Ñ•´¹Ñ½Ñ…±}ÍÑ•ÁÌ°(€€€€€€€€€€€€€€€€€€€€€€€€‰…ÍÍ¥¹µ•¹ÑÌˆèl(€€€€€€€€€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}¥ˆè…ÍÍ¥¹µ•¹Ð¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Ñ…É•Ñ}¥ˆè…ÍÍ¥¹µ•¹Ð¹Ñ…É•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Ñ…É•Ñ}Á±…å•Èˆè…ÍÍ¥¹µ•¹Ð¹Ñ…É•Ñ}Á±…å•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰…µ½Õ¹Ðˆè…ÍÍ¥¹µ•¹Ð¹…µ½Õ¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰É½±”ˆè…ÍÍ¥¹µ•¹Ð¹É½±”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰ÑÉ…µÁ±”ˆè…ÍÍ¥¹µ•¹Ð¹ÑÉ…µÁ±”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰±•Ñ¡…±}É•ÅÕ¥É•ˆè…ÍÍ¥¹µ•¹Ð¹±•Ñ¡…±}É•ÅÕ¥É•°(€€€€€€€€€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€€€€€€€€€™½È…ÍÍ¥¹µ•¹Ð¥¸¥Ñ•´¹…ÍÍ¥¹µ•¹ÑÌ(€€€€€€€€€€€€€€€€€€€€€€€t°(€€€€€€€€€€€€€€€€€€€€€€€€‰É•µ½Ù•‘}‰•™½É•}¹•áÑ}ÍÑ•Àˆè±¥ÍÐ¡¥Ñ•´¹É•µ½Ù•‘}‰•™½É•}¹•áÑ}ÍÑ•À¤°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÑÉ…µÁ±•}É•ÍÕ±ÑÌˆèl(€€€€€€€€€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰…ÑÑ…­•É}¥ˆèÉ•ÍÕ±Ð¹…ÑÑ…­•É}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‰±½­•É}¥ˆèÉ•ÍÕ±Ð¹‰±½­•É}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‘…µ…•}ÍÑ•ÀˆèÉ•ÍÕ±Ð¹‘…µ…•}ÍÑ•À¹Ù…±Õ”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰…ÑÑ…­•É}Á½Ý•ÈˆèÉ•ÍÕ±Ð¹…ÑÑ…­•É}Á½Ý•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‰±½­•É}Ñ½Õ¡¹•ÍÌˆèÉ•ÍÕ±Ð¹‰±½­•É}Ñ½Õ¡¹•ÍÌ°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‰±½­•É}µ…É­•‘}‘…µ…•}‰•™½É”ˆè€ (€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€É•ÍÕ±Ð¹‰±½­•É}µ…É­•‘}‘…µ…•}‰•™½É”(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰±•Ñ¡…±}É•ÅÕ¥É•ˆèÉ•ÍÕ±Ð¹±•Ñ¡…±}É•ÅÕ¥É•°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‰±½­•É}‘…µ…•}…ÍÍ¥¹•ˆèÉ•ÍÕ±Ð¹‰±½­•É}‘…µ…•}…ÍÍ¥¹•°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Á±…å•É}‘…µ…•}…ÍÍ¥¹•ˆèÉ•ÍÕ±Ð¹Á±…å•É}‘…µ…•}…ÍÍ¥¹•°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‘•™•¹‘¥¹}Á±…å•ÈˆèÉ•ÍÕ±Ð¹‘•™•¹‘¥¹}Á±…å•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‘•™•¹‘¥¹}±¥™•}‰•™½É”ˆèÉ•ÍÕ±Ð¹‘•™•¹‘¥¹}±¥™•}‰•™½É”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‘•™•¹‘¥¹}±¥™•}…™Ñ•ÈˆèÉ•ÍÕ±Ð¹‘•™•¹‘¥¹}±¥™•}…™Ñ•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‰±½­•É}µ…É­•‘}‘…µ…•}…™Ñ•Èˆè€¡É•ÍÕ±Ð¹‰±½­•É}µ…É­•‘}‘…µ…•}…™Ñ•È¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‰±½­•É}ÍÕÉÙ¥Ù•ˆèÉ•ÍÕ±Ð¹‰±½­•É}ÍÕÉÙ¥Ù•°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}‘•…Ñ¡Ñ½Õ ˆèÉ•ÍÕ±Ð¹Í½ÕÉ•}‘•…Ñ¡Ñ½Õ °(€€€€€€€€€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€€€€€€€€€™½ÈÉ•ÍÕ±Ð¥¸¥Ñ•´¹ÑÉ…µÁ±•}É•ÍÕ±ÑÌ(€€€€€€€€€€€€€€€€€€€€€€€t°(€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹½µ‰…Ñ}‘…µ…•}•Ù¥‘•¹”(€€€€€€€€€€€€€€€t°(€€€€€€€€€€€ô°(€€€€€€€€€€€€‰±¥™•±¥¹¬ˆèl(€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€‰•Ù•¹Ñ}¥ˆè¥Ñ•´¹•Ù•¹Ñ}¥°(€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}¥ˆè¥Ñ•´¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€‰½¹ÑÉ½±±•Èˆè¥Ñ•´¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€‰…µ½Õ¹Ðˆè¥Ñ•´¹…µ½Õ¹Ð°(€€€€€€€€€€€€€€€€€€€€‰½µ‰…Ðˆè¥Ñ•´¹½µ‰…Ð°(€€€€€€€€€€€€€€€€€€€€‰‘…µ…•}ÍÑ•Àˆè€¡9½¹”¥˜¥Ñ•´¹‘…µ…•}ÍÑ•À¥Ì9½¹”•±Í”¥Ñ•´¹‘…µ…•}ÍÑ•À¹Ù…±Õ”¤°(€€€€€€€€€€€€€€€€€€€€‰Ñ…É•Ñ}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹Ñ…É•Ñ}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰Ñ…É•Ñ}Á±…å•ÉÌˆè±¥ÍÐ¡¥Ñ•´¹Ñ…É•Ñ}Á±…å•ÉÌ¤°(€€€€€€€€€€€€€€€€€€€€‰±¥™•}‰•™½É”ˆè¥Ñ•´¹±¥™•}‰•™½É”°(€€€€€€€€€€€€€€€€€€€€‰±¥™•}…™Ñ•Èˆè¥Ñ•´¹±¥™•}…™Ñ•È°(€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹±¥™•±¥¹­}•Ù¥‘•¹”(€€€€€€€€€€€t°(€€€€€€€€€€€€‰¡…¹‘}‰½ÑÑ½µ}‘É…Üˆèl(€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€‰•Ù•¹Ñ}¥ˆè¥Ñ•´¹•Ù•¹Ñ}¥°(€€€€€€€€€€€€€€€€€€€€‰Á±…å•É}¥¹‘•àˆè¥Ñ•´¹Á±…å•É}¥¹‘•à°(€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}¥ˆè¥Ñ•´¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€‰½É…±•}™É…µ•¹Ðˆè¥Ñ•´¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€‰½™™•É•‘}¡½¥•}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹½™™•É•‘}¡½¥•}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰ÁÉ•}¡…¹‘}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹ÁÉ•}¡…¹‘}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰ÁÉ•}±¥‰É…Éå}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹ÁÉ•}±¥‰É…Éå}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰Í•±•Ñ•‘}¡…¹‘}¥ˆè¥Ñ•´¹Í•±•Ñ•‘}¡…¹‘}¥°(€€€€€€€€€€€€€€€€€€€€‰±¥‰É…Éå}‰½ÑÑ½µ}¥ˆè¥Ñ•´¹±¥‰É…Éå}‰½ÑÑ½µ}¥°(€€€€€€€€€€€€€€€€€€€€‰µ½Ù•µ•¹Ñ}ÍÕ••‘•ˆè¥Ñ•´¹µ½Ù•µ•¹Ñ}ÍÕ••‘•°(€€€€€€€€€€€€€€€€€€€€‰½¹‘¥Ñ¥½¹…±}‘É…Ý}Á•É™½Éµ•ˆè¥Ñ•´¹½¹‘¥Ñ¥½¹…±}‘É…Ý}Á•É™½Éµ•°(€€€€€€€€€€€€€€€€€€€€‰‘É…Ý¹}±¥‰É…Éå}¥ˆè¥Ñ•´¹‘É…Ý¹}±¥‰É…Éå}¥°(€€€€€€€€€€€€€€€€€€€€‰‘É…Ý¹}¡…¹‘}¥ˆè¥Ñ•´¹‘É…Ý¹}¡…¹‘}¥°(€€€€€€€€€€€€€€€€€€€€‰Á½ÍÑ}¡…¹‘}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹Á½ÍÑ}¡…¹‘}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰Á½ÍÑ}±¥‰É…Éå}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹Á½ÍÑ}±¥‰É…Éå}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰‘•±¥¹•ˆè¥Ñ•´¹‘•±¥¹•°(€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹¡…¹‘}‰½ÑÑ½µ}‘É…Ý}•Ù¥‘•¹”(€€€€€€€€€€€t°(€€€€€€€€€€€€‰‘¥Í…É‘}‘É…Üˆèl(€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€‰•Ù•¹Ñ}¥ˆè¥Ñ•´¹•Ù•¹Ñ}¥°(€€€€€€€€€€€€€€€€€€€€‰Á±…å•É}¥¹‘•àˆè¥Ñ•´¹Á±…å•É}¥¹‘•à°(€€€€€€€€€€€€€€€€€€€€‰…ÑÑ…­}ÁÉ½Ù•¹…¹”ˆèì(€€€€€€€€€€€€€€€€€€€€€€€€‰•Ù•¹Ñ}¥ˆè¥Ñ•´¹…ÑÑ…­}ÁÉ½Ù•¹…¹”¹•Ù•¹Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰•Ù•¹Ñ}­¥¹ˆè¥Ñ•´¹…ÑÑ…­}ÁÉ½Ù•¹…¹”¹•Ù•¹Ñ}­¥¹¹Ù…±Õ”°(€€€€€€€€€€€€€€€€€€€€€€€€‰•Ù•¹Ñ}Á±…å•É}¥¹‘•àˆè¥Ñ•´¹…ÑÑ…­}ÁÉ½Ù•¹…¹”¹•Ù•¹Ñ}Á±…å•É}¥¹‘•à°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÍÕ‰©•Ñ}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹…ÑÑ…­}ÁÉ½Ù•¹…¹”¹ÍÕ‰©•Ñ}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€€€€€‰…ÑÑ…­•É}¥ˆè¥Ñ•´¹…ÑÑ…­}ÁÉ½Ù•¹…¹”¹…ÑÑ…­•É}¥°(€€€€€€€€€€€€€€€€€€€€€€€€‰½¹ÑÉ½±±•Èˆè¥Ñ•´¹…ÑÑ…­}ÁÉ½Ù•¹…¹”¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÑÕÉ¸ˆè¥Ñ•´¹…ÑÑ…­}ÁÉ½Ù•¹…¹”¹ÑÕÉ¸°(€€€€€€€€€€€€€€€€€€€€€€€€‰ÍÑ•Àˆè¥Ñ•´¹…ÑÑ…­}ÁÉ½Ù•¹…¹”¹ÍÑ•À°(€€€€€€€€€€€€€€€€€€€€€€€€‰…Ñ¥Ù•}Á±…å•Èˆè¥Ñ•´¹…ÑÑ…­}ÁÉ½Ù•¹…¹”¹…Ñ¥Ù•}Á±…å•È°(€€€€€€€€€€€€€€€€€€€ô°(€€€€€€€€€€€€€€€€€€€€‰ÍÑ…­}½‰©•Ñ}¥ˆè¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}¥ˆè¥Ñ•´¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€‰½É…±•}™É…µ•¹Ðˆè¥Ñ•´¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€‰½™™•É•‘}¡½¥•}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹½™™•É•‘}¡½¥•}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰ÁÉ•}¡…¹‘}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹ÁÉ•}¡…¹‘}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰ÁÉ•}±¥‰É…Éå}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹ÁÉ•}±¥‰É…Éå}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰ÁÉ•}É…Ù•å…É‘}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹ÁÉ•}É…Ù•å…É‘}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰Í•±•Ñ•‘}¡…¹‘}¥ˆè¥Ñ•´¹Í•±•Ñ•‘}¡…¹‘}¥°(€€€€€€€€€€€€€€€€€€€€‰‘¥Í…É‘•‘}É…Ù•å…É‘}¥ˆè¥Ñ•´¹‘¥Í…É‘•‘}É…Ù•å…É‘}¥°(€€€€€€€€€€€€€€€€€€€€‰µ½Ù•µ•¹Ñ}ÍÕ••‘•ˆè¥Ñ•´¹µ½Ù•µ•¹Ñ}ÍÕ••‘•°(€€€€€€€€€€€€€€€€€€€€‰½¹‘¥Ñ¥½¹…±}‘É…Ý}Á•É™½Éµ•ˆè¥Ñ•´¹½¹‘¥Ñ¥½¹…±}‘É…Ý}Á•É™½Éµ•°(€€€€€€€€€€€€€€€€€€€€‰ÁÉ•}‘É…Ý}Ñ½Á}¥ˆè¥Ñ•´¹ÁÉ•}‘É…Ý}Ñ½Á}¥°(€€€€€€€€€€€€€€€€€€€€‰‘É…Ý¹}¡…¹‘}¥ˆè¥Ñ•´¹‘É…Ý¹}¡…¹‘}¥°(€€€€€€€€€€€€€€€€€€€€‰Á½ÍÑ}¡…¹‘}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹Á½ÍÑ}¡…¹‘}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰Á½ÍÑ}±¥‰É…Éå}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹Á½ÍÑ}±¥‰É…Éå}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰Á½ÍÑ}É…Ù•å…É‘}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹Á½ÍÑ}É…Ù•å…É‘}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰‘•±¥¹•ˆè¥Ñ•´¹‘•±¥¹•°(€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹‘¥Í…É‘}‘É…Ý}•Ù¥‘•¹”(€€€€€€€€€€€t°(€€€€€€€€€€€€‰…Ñ¥Ù…Ñ•‘}…‰¥±¥Ñ¥•Ìˆèl(€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€‰ÍÑ…­}½‰©•Ñ}¥ˆè¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}¥ˆè¥Ñ•´¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€‰½¹ÑÉ½±±•Èˆè¥Ñ•´¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€‰½É…±•}™É…µ•¹Ðˆè¥Ñ•´¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€‰µ…¹…}Í½ÕÉ•}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹µ…¹…}Í½ÕÉ•}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰Ñ…Á}Í½ÕÉ”ˆè¥Ñ•´¹Ñ…Á}Í½ÕÉ”°(€€€€€€€€€€€€€€€€€€€€‰É•Í½±Ù•ˆè¥Ñ•´¹É•Í½±Ù•°(€€€€€€€€€€€€€€€€€€€€‰½ÍÑ}Ñ…É•Ñ}¥ˆè¥Ñ•´¹½ÍÑ}Ñ…É•Ñ}¥°(€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹…Ñ¥Ù…Ñ¥½¹}•Ù¥‘•¹”(€€€€€€€€€€€t°(€€€€€€€€€€€€‰™½½‘}…Ñ¥Ù…Ñ¥½¹Ìˆèl(€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}¥ˆè¥Ñ•´¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}¹…µ”ˆè¥Ñ•´¹Í½ÕÉ•}¹…µ”°(€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}ÑåÁ•}±¥¹”ˆè¥Ñ•´¹Í½ÕÉ•}ÑåÁ•}±¥¹”°(€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}½Ý¹•Èˆè¥Ñ•´¹Í½ÕÉ•}½Ý¹•È°(€€€€€€€€€€€€€€€€€€€€‰½¹ÑÉ½±±•Èˆè¥Ñ•´¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}Ý…Í}Ñ½­•¸ˆè¥Ñ•´¹Í½ÕÉ•}Ý…Í}Ñ½­•¸°(€€€€€€€€€€€€€€€€€€€€‰½É…±•}™É…µ•¹Ðˆè¥Ñ•´¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€‰ÑÕÉ¸ˆè¥Ñ•´¹ÑÕÉ¸°(€€€€€€€€€€€€€€€€€€€€‰ÍÑ•Àˆè¥Ñ•´¹ÍÑ•À°(€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}é½¹•}‰•™½É”ˆè¥Ñ•´¹Í½ÕÉ•}é½¹•}‰•™½É”°(€€€€€€€€€€€€€€€€€€€€‰µ…¹…}É•ÅÕ¥É•µ•¹Ðˆèì(€€€€€€€€€€€€€€€€€€€€€€€€‰•¹•É¥Œˆè¥Ñ•´¹µ…¹…}É•ÅÕ¥É•µ•¹Ð¹•¹•É¥Œ°(€€€€€€€€€€€€€€€€€€€€€€€€‰½±½É•ˆè±¥ÍÐ¡¥Ñ•´¹µ…¹…}É•ÅÕ¥É•µ•¹Ð¹½±½É•¤°(€€€€€€€€€€€€€€€€€€€ô°(€€€€€€€€€€€€€€€€€€€€‰µ…¹…}Í½ÕÉ•}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹µ…¹…}Í½ÕÉ•}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}Ñ…ÁÁ•‘}‰•™½É”ˆè¥Ñ•´¹Í½ÕÉ•}Ñ…ÁÁ•‘}‰•™½É”°(€€€€€€€€€€€€€€€€€€€€‰Ñ…Á}Á…¥ˆè¥Ñ•´¹Ñ…Á}Á…¥°(€€€€€€€€€€€€€€€€€€€€‰Í…É¥™¥•}Á…¥ˆè¥Ñ•´¹Í…É¥™¥•}Á…¥°(€€€€€€€€€€€€€€€€€€€€‰Í…É¥™¥•‘}‘•ÍÑ¥¹…Ñ¥½¹}¥ˆè¥Ñ•´¹Í…É¥™¥•‘}‘•ÍÑ¥¹…Ñ¥½¹}¥°(€€€€€€€€€€€€€€€€€€€€‰Í…É¥™¥•‘}‘•ÍÑ¥¹…Ñ¥½¹}é½¹”ˆè¥Ñ•´¹Í…É¥™¥•‘}‘•ÍÑ¥¹…Ñ¥½¹}é½¹”°(€€€€€€€€€€€€€€€€€€€€‰ÍÑ…­}½‰©•Ñ}¥ˆè¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€‰ÁÉ¥½É¥Ñå}•Á½ ˆè¥Ñ•´¹ÁÉ¥½É¥Ñå}•Á½ °(€€€€€€€€€€€€€€€€€€€€‰ÁÉ¥½É¥Ñå}Á…ÍÍ•Ìˆè±¥ÍÐ¡¥Ñ•´¹ÁÉ¥½É¥Ñå}Á…ÍÍ•Ì¤°(€€€€€€€€€€€€€€€€€€€€‰É•Í½±ÕÑ¥½¹}Á•Éµ¥ÑÑ•ˆè¥Ñ•´¹É•Í½±ÕÑ¥½¹}Á•Éµ¥ÑÑ•°(€€€€€€€€€€€€€€€€€€€€‰É•Í½±Ù•ˆè¥Ñ•´¹É•Í½±Ù•°(€€€€€€€€€€€€€€€€€€€€‰±¥™•}‰•™½É”ˆè¥Ñ•´¹±¥™•}‰•™½É”°(€€€€€€€€€€€€€€€€€€€€‰±¥™•}…™Ñ•Èˆè¥Ñ•´¹±¥™•}…™Ñ•È°(€€€€€€€€€€€€€€€€€€€€‰…µ½Õ¹Ñ}…¥¹•ˆè¥Ñ•´¹…µ½Õ¹Ñ}…¥¹•°(€€€€€€€€€€€€€€€€€€€€‰™¥¹…±}Í½ÕÉ•}‘¥ÍÁ½Í¥Ñ¥½¸ˆè¥Ñ•´¹™¥¹…±}Í½ÕÉ•}‘¥ÍÁ½Í¥Ñ¥½¸°(€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹™½½‘}…Ñ¥Ù…Ñ¥½¹}•Ù¥‘•¹”(€€€€€€€€€€€t°(€€€€€€€€€€€€‰Í¹•…¬ˆèl(€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€‰…Éˆè¥Ñ•´¹…É‘}¹…µ”°(€€€€€€€€€€€€€€€€€€€€‰¡…¹‘}½‰©•Ñ}¥ˆè¥Ñ•´¹¡…¹‘}½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€‰½¹ÑÉ½±±•Èˆè¥Ñ•´¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€‰ÑÕÉ¸ˆè¥Ñ•´¹ÑÕÉ¸°(€€€€€€€€€€€€€€€€€€€€‰ÍÑ•Àˆè¥Ñ•´¹ÍÑ•À°(€€€€€€€€€€€€€€€€€€€€‰½É…±•}™É…µ•¹Ðˆè¥Ñ•´¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€‰µ…¹…}É•ÅÕ¥É•µ•¹Ðˆèì(€€€€€€€€€€€€€€€€€€€€€€€€‰•¹•É¥Œˆè¥Ñ•´¹µ…¹…}É•ÅÕ¥É•µ•¹Ð¹•¹•É¥Œ°(€€€€€€€€€€€€€€€€€€€€€€€€‰½±½É•ˆè±¥ÍÐ¡¥Ñ•´¹µ…¹…}É•ÅÕ¥É•µ•¹Ð¹½±½É•¤°(€€€€€€€€€€€€€€€€€€€ô°(€€€€€€€€€€€€€€€€€€€€‰µ…¹…}Í½ÕÉ•}¥‘Ìˆè±¥ÍÐ¡¥Ñ•´¹µ…¹…}Í½ÕÉ•}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€‰É•ÑÕÉ¹•‘}…ÑÑ…­•É}¥ˆè¥Ñ•´¹É•ÑÕÉ¹•‘}…ÑÑ…­•É}¥°(€€€€€€€€€€€€€€€€€€€€‰É•ÑÕÉ¹•‘}¡…¹‘}¥ˆè¥Ñ•´¹É•ÑÕÉ¹•‘}¡…¹‘}¥°(€€€€€€€€€€€€€€€€€€€€‰‘•™•¹‘¥¹}Á±…å•Èˆè¥Ñ•´¹‘•™•¹‘¥¹}Á±…å•È°(€€€€€€€€€€€€€€€€€€€€‰ÍÑ…­}½‰©•Ñ}¥ˆè¥Ñ•´¹ÍÑ…­}½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€‰ÁÉ¥½É¥Ñå}•Á½ ˆè¥Ñ•´¹ÁÉ¥½É¥Ñå}•Á½ °(€€€€€€€€€€€€€€€€€€€€‰É•Í½±Ù•‘}½‰©•Ñ}¥ˆè¥Ñ•´¹É•Í½±Ù•‘}½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€‰•¹Ñ•É•‘}Ñ…ÁÁ•ˆè¥Ñ•´¹•¹Ñ•É•‘}Ñ…ÁÁ•°(€€€€€€€€€€€€€€€€€€€€‰•¹Ñ•É•‘}…ÑÑ…­¥¹œˆè¥Ñ•´¹•¹Ñ•É•‘}…ÑÑ…­¥¹œ°(€€€€€€€€€€€€€€€€€€€€¨¨ (€€€€€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}é½¹”ˆè¥Ñ•´¹Í½ÕÉ•}é½¹”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Á•Éµ¥ÍÍ¥½¹}Í½ÕÉ•}¥ˆè¥Ñ•´¹Á•Éµ¥ÍÍ¥½¹}Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€€€€€¥˜¥Ñ•´¹Í½ÕÉ•}é½¹”€ôô€‰É…Ù•å…Éˆ(€€€€€€€€€€€€€€€€€€€€€€€•±Í”íô(€€€€€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€™½È¥Ñ•´¥¸Í•±˜¹Í¹•…­}•Ù¥‘•¹”(€€€€€€€€€€€t°(€€€€€€€€€€€€‰Á±…å•ÉÌˆèl(€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€‰¹…µ”ˆèÀ¹¹…µ”°(€€€€€€€€€€€€€€€€€€€€‰±¥™”ˆèÀ¹±¥™”°(€€€€€€€€€€€€€€€€€€€€‰±¥‰É…Éäˆè±•¸¡À¹±¥‰É…Éä¤°(€€€€€€€€€€€€€€€€€€€€‰±¥‰É…Éå}½‰©•Ñ}¥‘Ìˆèm…É¹½‰©•Ñ}¥™½È…É¥¸À¹±¥‰É…Éåt°(€€€€€€€€€€€€€€€€€€€€‰¡…¹ˆèmŒ¹¹…µ”™½ÈŒ¥¸À¹¡…¹‘t°(€€€€€€€€€€€€€€€€€€€€‰¡…¹‘}½‰©•Ñ}¥‘Ìˆèm…É¹½‰©•Ñ}¥™½È…É¥¸À¹¡…¹‘t°(€€€€€€€€€€€€€€€€€€€€‰‰…ÑÑ±•™¥•±ˆèl(€€€€€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰½‰©•Ñ}¥ˆèà¹½‰©•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰…Éˆèì(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰¹…µ”ˆèà¹…É¹¹…µ”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰µ…¹…}½ÍÐˆèà¹…É¹µ…¹…}½ÍÐ°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰µ…¹…}Ù…±Õ”ˆèà¹…É¹µ…¹…}Ù…±Õ”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰ÑåÁ•}±¥¹”ˆèà¹…É¹ÑåÁ•}±¥¹”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰½É…±•}Ñ•áÐˆèà¹…É¹½É…±•}Ñ•áÐ°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Á½Ý•Èˆèà¹…É¹Á½Ý•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Ñ½Õ¡¹•ÍÌˆèà¹…É¹Ñ½Õ¡¹•ÍÌ°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰­•åÝ½É‘Ìˆè±¥ÍÐ¡à¹…É¹­•åÝ½É‘Ì¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€ô°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰½Ý¹•Èˆèà¹½Ý¹•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰½¹ÑÉ½±±•Èˆèà¹½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰é½¹”ˆèà¹é½¹”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰¥Í}Ñ½­•¸ˆèà¹¥Í}Ñ½­•¸°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰•Ù…±Õ…Ñ•‘}ÑåÁ•}±¥¹”ˆèà¹ÑåÁ•}±¥¹”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰½±½ÉÌˆè€ (€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€±¥ÍÐ¡à¹…É¹½±½ÉÌ¤¥˜¥Í¥¹ÍÑ…¹”¡à¹…É°Q½­•¹•™¥¹¥Ñ¥½¸¤•±Í”mt(€€€€€€€€€€€€€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Ñ…ÁÁ•ˆèà¹Ñ…ÁÁ•°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰ÍÕµµ½¹¥¹}Í¥¬ˆèà¹ÍÕµµ½¹¥¹}Í¥¬°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰•¹Ñ•É•‘}‰…ÑÑ±•™¥•±‘}ÑÕÉ¸ˆèà¹•¹Ñ•É•‘}‰…ÑÑ±•™¥•±‘}ÑÕÉ¸°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰•¹Ñ•É•‘}Õ¹‘•É}½¹ÑÉ½±±•Èˆèà¹•¹Ñ•É•‘}Õ¹‘•É}½¹ÑÉ½±±•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€¨¨¡ì‰±…ÍÍ}±•Ù•°ˆèà¹±…ÍÍ}±•Ù•±ô¥˜à¹±…ÍÍ}±•Ù•°¥Ì¹½Ð9½¹”•±Í”íô¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€¨¨¡ì‰…ÑÑ…¡•‘}Ñ¼ˆèà¹…ÑÑ…¡•‘}Ñ½ô¥˜à¹…ÑÑ…¡•‘}Ñ¼¥Ì¹½Ð9½¹”•±Í”íô¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰•¹Ñ•É•‘}Ñ¥µ•ÍÑ…µÀˆè±¥ÍÐ¡à¹•¹Ñ•É•‘}Ñ¥µ•ÍÑ…µÀ¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰…ÑÑ…¡µ•¹Ñ}Ñ¥µ•ÍÑ…µÀˆè±¥ÍÐ¡à¹…ÑÑ…¡µ•¹Ñ}Ñ¥µ•ÍÑ…µÀ¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰…‰¥±¥Ñå}±½ÍÍ}Ñ¥µ•ÍÑ…µÀˆèà¹…‰¥±¥Ñå}±½ÍÍ}Ñ¥µ•ÍÑ…µÀ°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰…ÕÉ…}É•…ÑÕÉ•}ÑåÁ”ˆèà¹…ÕÉ…}É•…ÑÕÉ•}ÑåÁ”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰…ÕÉ…}•™™•Ñ}¥‘Ìˆè±¥ÍÐ¡à¹…ÕÉ…}•™™•Ñ}¥‘Ì¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰…ÕÉ…}…ÑÑ…­}É•ÍÑÉ¥Ñ¥½¹Ìˆè±¥ÍÐ¡à¹…ÕÉ…}…ÑÑ…­}É•ÍÑÉ¥Ñ¥½¹Ì¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‘…µ…”ˆèà¹‘…µ…”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‘•…Ñ¡Ñ½Õ¡}‘…µ…”ˆèà¹‘•…Ñ¡Ñ½Õ¡}‘…µ…”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰½Õ¹Ñ•ÉÌˆè‘¥Ð¡à¹½Õ¹Ñ•ÉÌ¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰½¹•}Á•É}ÑÕÉ¹}…Ñ¥Ù…Ñ¥½¹Ìˆè‘¥Ð¡à¹½¹•}Á•É}ÑÕÉ¹}…Ñ¥Ù…Ñ¥½¹Ì¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰ÁÑ}µ½‘¥™¥•ÉÌˆèl(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Á½Ý•Èˆèµ½‘¥™¥•È¹Á½Ý•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Ñ½Õ¡¹•ÍÌˆèµ½‘¥™¥•È¹Ñ½Õ¡¹•ÍÌ°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‘ÕÉ…Ñ¥½¸ˆèµ½‘¥™¥•È¹‘ÕÉ…Ñ¥½¸°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}…Éˆèµ½‘¥™¥•È¹Í½ÕÉ•}…É°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰½É…±•}™É…µ•¹Ðˆèµ½‘¥™¥•È¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰É•…Ñ•‘}ÑÕÉ¸ˆèµ½‘¥™¥•È¹É•…Ñ•‘}ÑÕÉ¸°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰É•…Ñ•‘}½É‘•Èˆèµ½‘¥™¥•È¹É•…Ñ•‘}½É‘•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‘•É¥Ù•‘}ÍÑ…Ñ¥Œˆèµ½‘¥™¥•È¹‘•É¥Ù•‘}ÍÑ…Ñ¥Œ°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€¨¨ (€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€ì‰Í½ÕÉ•}½‰©•Ñ}¥ˆèµ½‘¥™¥•È¹Í½ÕÉ•}½‰©•Ñ}¥‘ô(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€¥˜µ½‘¥™¥•È¹Í½ÕÉ•}½‰©•Ñ}¥¥Ì¹½Ð9½¹”(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€•±Í”íô(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€™½Èµ½‘¥™¥•È¥¸à¹ÁÑ}µ½‘¥™¥•ÉÌ(€€€€€€€€€€€€€€€€€€€€€€€€€€€t°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰¡…É…Ñ•É¥ÍÑ¥}•™™•ÑÌˆèl(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰•™™•Ñ}¥ˆè•™™•Ð¹•™™•Ñ}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰±…å•Èˆè•™™•Ð¹±…å•È¹Ù…±Õ”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰ÍÕ‰±…å•Èˆè€ (€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€9½¹”¥˜•™™•Ð¹ÍÕ‰±…å•È¥Ì9½¹”•±Í”•™™•Ð¹ÍÕ‰±…å•È¹Ù…±Õ”(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰½Á•É…Ñ¥½¸ˆè•™™•Ð¹½Á•É…Ñ¥½¸¹Ù…±Õ”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Á½Ý•Èˆè•™™•Ð¹Á½Ý•È°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Ñ½Õ¡¹•ÍÌˆè•™™•Ð¹Ñ½Õ¡¹•ÍÌ°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Ñ¥µ•ÍÑ…µÀˆè±¥ÍÐ¡•™™•Ð¹Ñ¥µ•ÍÑ…µÀ¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‘•Á•¹‘Í}½¸ˆè±¥ÍÐ¡•™™•Ð¹‘•Á•¹‘Í}½¸¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}…Éˆè•™™•Ð¹Í½ÕÉ•}…É°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€¨¨ (€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€ì‰‘ÕÉ…Ñ¥½¸ˆè•™™•Ð¹‘ÕÉ…Ñ¥½¹ô(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€¥˜•™™•Ð¹‘ÕÉ…Ñ¥½¸€„ô€‰Á•ÉÍ¥ÍÑ•¹Ðˆ(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€•±Í”íô(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€™½È•™™•Ð¥¸à¹¡…É…Ñ•É¥ÍÑ¥}•™™•ÑÌ(€€€€€€€€€€€€€€€€€€€€€€€€€€€t°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€¨¨ (€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Ñ•µÁ½É…Éå}ÑåÁ•}•™™•ÑÌˆèl(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰…‘‘•‘}ÑåÁ•Ìˆè±¥ÍÐ¡•™™•Ð¹…‘‘•‘}ÑåÁ•Ì¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‘ÕÉ…Ñ¥½¸ˆè•™™•Ð¹‘ÕÉ…Ñ¥½¸°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}¥ˆè•™™•Ð¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰½É…±•}™É…µ•¹Ðˆè•™™•Ð¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Ñ¥µ•ÍÑ…µÀˆè±¥ÍÐ¡•™™•Ð¹Ñ¥µ•ÍÑ…µÀ¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€¨¨ (€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€ì‰…‘‘•‘}ÍÕ‰ÑåÁ•Ìˆè±¥ÍÐ¡•™™•Ð¹…‘‘•‘}ÍÕ‰ÑåÁ•Ì¥ô(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€¥˜•™™•Ð¹…‘‘•‘}ÍÕ‰ÑåÁ•Ì(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€•±Í”íô(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€™½È•™™•Ð¥¸à¹Ñ•µÁ½É…Éå}ÑåÁ•}•™™•ÑÌ(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€t(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€¥˜à¹Ñ•µÁ½É…Éå}ÑåÁ•}•™™•ÑÌ(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€•±Í”íô(€€€€€€€€€€€€€€€€€€€€€€€€€€€€¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Ñ•µÁ½É…Éå}­•åÝ½É‘}•™™•ÑÌˆèl(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰­•åÝ½Éˆè•™™•Ð¹­•åÝ½É¹Ù…±Õ”°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Ñ¥µ•ÍÑ…µÀˆè±¥ÍÐ¡•™™•Ð¹Ñ¥µ•ÍÑ…µÀ¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‘ÕÉ…Ñ¥½¸ˆè•™™•Ð¹‘ÕÉ…Ñ¥½¸°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}¥ˆè•™™•Ð¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰½É…±•}™É…µ•¹Ðˆè•™™•Ð¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€™½È•™™•Ð¥¸à¹Ñ•µÁ½É…Éå}­•åÝ½É‘}•™™•ÑÌ(€€€€€€€€€€€€€€€€€€€€€€€€€€€t°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Ñ•µÁ½É…Éå}‘•…Ñ¡}É•ÑÕÉ¹}•™™•ÑÌˆèl(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€ì(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Ñ¥µ•ÍÑ…µÀˆè±¥ÍÐ¡•™™•Ð¹Ñ¥µ•ÍÑ…µÀ¤°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰‘ÕÉ…Ñ¥½¸ˆè•™™•Ð¹‘ÕÉ…Ñ¥½¸°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰Í½ÕÉ•}¥ˆè•™™•Ð¹Í½ÕÉ•}¥°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€‰½É…±•}™É…µ•¹Ðˆè•™™•Ð¹½É…±•}™É…µ•¹Ð°(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€€™½È•™™•Ð¥¸à¹Ñ•µÁ½É…Éå}‘•…Ñ¡}É•ÑÕÉ¹}•™™•ÑÌ(€€€€€€€€€€€€€€€€€€€€€€€€€€€t°(€€€€€€€€€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€€€€€€€€€™½Èà¥¸À¹‰…ÑÑ±•™¥•±(€€€€€€€€€€€€€€€€€€€t°(€€€€€€€€€€€€€€€€€€€€‰É…Ù•å…ÉˆèmŒ¹¹…µ”™½ÈŒ¥¸À¹É…Ù•å…É‘t°(€€€€€€€€€€€€€€€€€€€€‰É…Ù•å…É‘}½‰©•Ñ}¥‘Ìˆèm…É¹½‰©•Ñ}¥™½È…É¥¸À¹É…Ù•å…É‘t°(€€€€€€€€€€€€€€€€€€€€‰±½ÍÐˆèÀ¹±½ÍÐ°(€€€€€€€€€€€€€€€€€€€€‰±½ÍÍ}É•…Í½¸ˆèÀ¹±½ÍÍ}É•…Í½¸°(€€€€€€€€€€€€€€€€€€€€‰™…¥±•‘}‘É…Ý}Á•¹‘¥¹œˆèÀ¹™…¥±•‘}‘É…Ý}Á•¹‘¥¹œ°(€€€€€€€€€€€€€€€ô(€€€€€€€€€€€€€€€™½ÈÀ¥¸Í•±˜¹Á±…å•ÉÌ(€€€€€€€€€€€t°(€€€€€€€€€€€€‰±¥µ¥Ñ…Ñ¥½¹ÌˆèÍ½ÉÑ•¡Í•±˜¹±¥µ¥Ñ…Ñ¥½¹Ì¤°(€€€€€€€€€€€€‰•Ù•¹ÑÌˆèÍ•±˜¹•Ù•¹ÑÌ°(€€€€€€€ô(()‘•˜}¥¹Ñ••É}¡…É…Ñ•É¥ÍÑ¥Œ¡Ù…±Õ”èÍÑÈð9½¹”¤€´ø¥¹Ðð9½¹”è(€€€¥˜Ù…±Õ”¥Ì9½¹”è(€€€€€€€É•ÑÕÉ¸9½¹”(€€€ÑÉäè(€€€€€€€É•ÑÕÉ¸¥¹Ð¡Ù…±Õ”¤(€€€•á•ÁÐY…±Õ•ÉÉ½Èè(€€€€€€€É•ÑÕÉ¸9½¹”(()‘•˜±½…‘}™…ÑÌ¡…Ñ…±½œè…É‘…Ñ……Ñ…±½œ°¹…µ•ÌèÍ•ÑmÍÑÉt¤€´ø‘¥ÑmÍÑÈ°…É‘…Ñtè(€€€™…ÑÌ€ôíô(€€€™½È¹…µ”¥¸Í½ÉÑ•¡¹…µ•Ì¤è(€€€€€€€É½Ü€ô…Ñ…±½œ¹É•Í½±Ù•}¹…µ”¡¹…µ”¤(€€€€€€€µ…¹…}Ù…±Õ”€ô¥¹Ð¡É½Ü¹µ…¹…}Ù…±Õ”¤(€€€€€€€¥˜µ…¹…}Ù…±Õ”€„ôÉ½Ü¹µ…¹…}Ù…±Õ”è(€€€€€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È¡˜‰¹¥¹”€À¸Ü…¹¹½ÐÉ•ÁÉ•Í•¹Ð¹½¹¥¹Ñ•É…°µ…¹„Ù…±Õ”™½Èí¹…µ•ôˆ¤(€€€€€€€™…ÑÍm¹…µ•t€ô…É‘…Ð (€€€€€€€€€€€¹…µ”õÉ½Ü¹¹…µ”°(€€€€€€€€€€€µ…¹…}½ÍÐõÉ½Ü¹µ…¹…}½ÍÐ°(€€€€€€€€€€€µ…¹…}Ù…±Õ”õµ…¹…}Ù…±Õ”°(€€€€€€€€€€€ÑåÁ•}±¥¹”õÉ½Ü¹ÑåÁ•}±¥¹”°(€€€€€€€€€€€½É…±•}Ñ•áÐõÉ½Ü¹½É…±•}Ñ•áÐ°(€€€€€€€€€€€Á½Ý•Èõ}¥¹Ñ••É}¡…É…Ñ•É¥ÍÑ¥Œ¡É½Ü¹Á½Ý•È¤°(€€€€€€€€€€€Ñ½Õ¡¹•ÍÌõ}¥¹Ñ••É}¡…É…Ñ•É¥ÍÑ¥Œ¡É½Ü¹Ñ½Õ¡¹•ÍÌ¤°(€€€€€€€€€€€­•åÝ½É‘ÌõÉ½Ü¹­•åÝ½É‘Ì°(€€€€€€€€€€€½É…±•}¥õÉ½Ü¹½É…±•}¥°(€€€€€€€€¤(€€€É•ÑÕÉ¸™…ÑÌ(()‘•˜±½…‘}‘•¬¡Á…Ñ èA…Ñ °™…ÑÌè‘¥ÑmÍÑÈ°…É‘…Ñt¤€´ø±¥ÍÑm…É‘…Ñtè(€€€…É‘Ìè±¥ÍÑm…É‘…Ñt€ômt(€€€™½È±¥¹”¥¸Á…Ñ ¹É•…‘}Ñ•áÐ¡•¹½‘¥¹œô‰ÕÑ˜´àˆ¤¹ÍÁ±¥Ñ±¥¹•Ì ¤è(€€€€€€€¥˜¹½Ð±¥¹”½È±¥¹”€ôô€‰•¬ˆè(€€€€€€€€€€€½¹Ñ¥¹Õ”(€€€€€€€ÅÕ…¹Ñ¥Ñä°¹…µ”€ô±¥¹”¹ÍÁ±¥Ð ˆ€ˆ°€Ä¤(€€€€€€€…É‘Ì¹•áÑ•¹¡m™…ÑÍm¹…µ•ut€¨¥¹Ð¡ÅÕ…¹Ñ¥Ñä¤¤(€€€¥˜±•¸¡…É‘Ì¤€„ô€ØÀè(€€€€€€€É…¥Í”Y…±Õ•ÉÉ½È¡˜‰íÁ…Ñ¡ôè•áÁ•Ñ•€ØÀ…É‘Ì°™½Õ¹í±•¸¡…É‘Ì¥ôˆ¤(€€€É•ÑÕÉ¸…É‘Ì(