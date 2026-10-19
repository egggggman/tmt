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
    COMBAT_DAMAGE_HAND_BATTLEFIELD = "combat_damage_hand_battlefield"
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
class HandBattlefieldEntryOption:
    """One legal optional creature/land pair selected from a private hand."""

    creature_id: str | None
    land_id: str | None


@dataclass(frozen=True)
class HandBattlefieldEntryView:
    player_index: int
    cards: tuple[tuple[str, str], ...]


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
        hand_battlefield_entry_chooser=None,
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
        self.hand_battlefield_entry_chooser = hand_battlefield_entry_chooser or (
            lambda _view, options: options[0]
        )
        self._hand_battlefield_entry_choice_active = False
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
        if self._hand_battlefield_entry_choice_active:
            raise ValueError("hand-entry chooser cannot move authoritative objects")
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
                or not candidate.is_creature
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

    def choose_hand_battlefield_entry(self, player_index: int) -> HandBattlefieldEntryOption:
        """Choose zero, one, or one creature plus one land from a private hand."""
        if player_index not in range(2):
            raise ValueError("hand-entry player is invalid")
        player = self.players[player_index]
        creatures = tuple(card for card in player.hand if card.card.is_creature)
        lands = tuple(card for card in player.hand if card.card.is_land)
        options = [HandBattlefieldEntryOption(None, None)]
        options.extend(HandBattlefieldEntryOption(card.object_id, None) for card in creatures)
        options.extend(HandBattlefieldEntryOption(None, card.object_id) for card in lands)
        options.extend(
            HandBattlefieldEntryOption(creature.object_id, land.object_id)
            for creature in creatures
            for land in lands
        )
        view = HandBattlefieldEntryView(
            player_index,
            tuple((card.object_id, card.card.name) for card in player.hand),
        )
        before = tuple(player.hand)
        self._hand_battlefield_entry_choice_active = True
        try:
            choice = self.hand_battlefield_entry_chooser(view, tuple(options))
        finally:
            self._hand_battlefield_entry_choice_active = False
        if not isinstance(choice, HandBattlefieldEntryOption) or choice not in options:
            raise ValueError("hand-entry chooser must return one listed option")
        if tuple(player.hand) != before:
            raise ValueError("hand-entry chooser mutated authoritative hand")
        return choice

    def commit_hand_battlefield_entry(
        self,
        player_index: int,
        choice: HandBattlefieldEntryOption,
        *,
        source_id: str,
        oracle_fragment: str,
    ) -> tuple[Permanent, ...]:
        if not isinstance(choice, HandBattlefieldEntryOption):
            raise ValueError("hand-entry choice is invalid")
        ids = tuple(x for x in (choice.creature_id, choice.land_id) if x is not None)
        if len(set(ids)) != len(ids):
            raise ValueError("hand-entry choice cannot select one card twice")
        selected = []
        for object_id in ids:
            card = self._objects.get(object_id)
            if (
                not isinstance(card, CardObject)
                or not self.is_authoritative(card, "hand")
                or card.owner != player_index
            ):
                raise ValueError("hand-entry choice selected an unavailable card")
            if choice.creature_id == object_id and not card.card.is_creature:
                raise ValueError("hand-entry creature choice is not a creature")
            if choice.land_id == object_id and not card.card.is_land:
                raise ValueError("hand-entry land choice is not a land")
            selected.append(card)
        entered = []
        for card in selected:
            permanent = self.move_object(
                card, "battlefield", controller=player_index, reason="combat_hand_entry"
            )
            assert isinstance(permanent, Permanent)
            entered.append(permanent)
            if permanent.is_creature:
                self._process_creature_entered_triggers(permanent, defer_triggers=True)
        self.check_state_based_actions()
        self._put_pending_triggers_on_stack()
        self._drain_triggered_abilities()
        self.log(
            "combat_hand_battlefield_entry_resolved",
            source_id=source_id,
            controller=player_index,
            selected_ids=ids,
            entered_ids=[item.object_id for item in entered],
            oracle_fragment=oracle_fragment,
        )
        return tuple(entered)

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
        if effect is TriggerEffect.COMBAT_DAMAGE_HAND_BATTLEFIELD:
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
                or not self.interpreter.combat_damage_hand_battlefield(source.card, fragment)
            ):
                raise ValueError("hand-entry trigger lacks combat-damage provenance")
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
            self._authenticate_original_rules_event(event)
            if (
                not self.is_authoritative(source, "battlefield")
                or self._rules_events.get(event.event_id) is not event
                or event.kind
                not in {RulesEventKind.CREATURE_ENTERED, RulesEventKind.PERMANENT_ENTERED}
                or event.subject_ids != (source.object_id,)
                or event.player_index != source.controller
                or fragment not in self.interpreter.fragments(source.rules_card)
                or self.interpreter.etb_mill_draw_discard_semantic_coverage(source.card, fragment)
                is None
            ):
                raise ValueError("ETB mill/draw/discard entry provenance is invalid")
            key = (source.object_id, fragment)
            if key in self._mill_draw_discard_sources:
                return
            self._mill_draw_discard_sources[key] = (source, None)
        if effect is TriggerEffect.CLASS_LEVEL_TWO_RECOVERY:
            self._authenticate_original_rules_event(event)
            if (
                not self.is_authoritative(source, "battlefield")
                or source.class_level != 2
                or self._rules_events.get(event.event_id) is not event
                or event.kind is not RulesEventKind.CLASS_LEVEL_ADVANCED
                or event.subject_ids != (source.object_id,)
                or event.player_index != source.controller
                or fragment not in self.interpreter.fragments(source.rules_card)
                or self.interpreter.class_level_recovery_semantic_coverage(source.card, fragment)
                is None
            ):
                raise ValueError("Class level recovery entry provenance is invalid")
        if effect is TriggerEffect.CLASS_SPELL_CAST_TEAM_COUNTER:
            self._validate_class_spell_cast_team_counter(
                None, event, source, fragment, source.controller
            )
        if effect is TriggerEffect.CLASS_DISCARD_DAMAGE:
            self._authenticate_original_rules_event(event)
            if (
                not self.is_authoritative(source, "battlefield")
                or source.class_level is None
                or source.class_level < 2
                or event.kind is not RulesEventKind.CARD_DISCARDED
                or event.player_index != source.controller
                or self.interpreter.CLASS_DISCARD_DAMAGE.fullmatch(fragment) is None
                or fragment not in self.interpreter.fragments(source.rules_card)
            ):
                raise ValueError("Class discard trigger provenance is invalid")
        if effect is TriggerEffect.CLASS_LEVEL_THREE_SEARCH:
            self._authenticate_original_rules_event(event)
            if (
                not self.is_authoritative(source, "battlefield")
                or source.class_level != 3
                or event.kind is not RulesEventKind.CLASS_LEVEL_ADVANCED
                or event.subject_ids != (source.object_id,)
                or event.player_index != source.controller
                or self.interpreter.CLASS_LEVEL_THREE_SEARCH.fullmatch(fragment) is None
                or fragment not in self.interpreter.fragments(source.rules_card)
            ):
                raise ValueError("Class level-three trigger provenance is invalid")
        if effect is TriggerEffect.CLASS_COMBAT_ARTIFACT_ANIMATION:
            self._authenticate_original_rules_event(event)
            if (
                not self.is_authoritative(source, "battlefield")
                or source.class_level is None
                or source.class_level < 3
                or event.kind is not RulesEventKind.BEGINNING_OF_COMBAT
                or event.player_index != source.controller
                or event.player_index != self.active_player
                or (source.object_id, source.controller) not in event.battlefield_authority
                or fragment not in self.interpreter.fragments(source.rules_card)
                or self.interpreter.class_combat_artifact_animation(source.card, fragment) is None
            ):
                raise ValueError("Class combat trigger provenance is invalid")
        if effect is TriggerEffect.LTB_MUTAGEN:
            self._validate_ltb_mutagen_departure(source, fragment, event, source.controller)
            key = (source.object_id, event.event_id, fragment)
            if key in self._ltb_mutagen_enqueued:
                return
            self._ltb_mutagen_enqueued.add(key)
        if effect is TriggerEffect.PARAMECIA_EXILE_CHOICE and (
            event.kind is not RulesEventKind.CREATURE_DIED
            or event.subject_ids != (source.object_id,)
            or source.zone != "former"
            or fragment != self._paramecia_fragment(source.card)
        ):
            raise ValueError("Paramecia death provenance is invalid")
        trigger = TriggerInstance(
            f"trigger-{self._next_trigger_number:06d}",
            source.controller,
            source.object_id,
            source.card,
            fragment,
            effect,
            event,
            grant_source.object_id if grant_source is not None else None,
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
            **({"grant_source_id": grant_source.object_id} if grant_source is not None else {}),
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
                if ability.effect is TriggerEffect.ETB_TAP_STUN:
                    self._select_stun_target(ability, trigger)
                if ability.effect is TriggerEffect.ATTACK_TARGET_COUNTER:
                    offered = tuple(
                        sorted(
                            attacker.object_id
                            for attacker in self.players[trigger.controller].battlefield
                            if attacker.object_id in trigger.event.subject_ids
                            and self.is_authoritative(attacker, "battlefield")
                            and self._legal_targeting_protection(attacker, trigger.controller)
                        )
                    )
                    if not offered:
                        self.log(
                            "attack_counter_no_legal_target",
                            event_id=trigger.event.event_id,
                            source_id=trigger.source_id,
                        )
                        continue
                    selected = self.counter_target_chooser(
                        trigger.controller, trigger.source_id, offered
                    )
                    if selected not in offered:
                        raise ValueError("attack counter chooser must return an attacking creature")
                    ability.target_id = selected
                    self._attack_counter_targets[ability.object_id] = (
                        selected,
                        trigger.trigger_id,
                    )
                    self.log(
                        "attack_counter_target_selected",
                        event_id=trigger.event.event_id,
                        stack_object_id=ability.object_id,
                        source_id=trigger.source_id,
                        target_id=selected,
                        offered_ids=list(offered),
                    )
                if ability.effect is TriggerEffect.CONTROLLED_ARTIFACT_COUNTER_TRANSFER:
                    self._validate_artifact_counter_transfer(
                        trigger.event,
                        trigger.source_id,
                        trigger.source_card,
                        trigger.oracle_fragment,
                        trigger.controller,
                        trigger_id=trigger.trigger_id,
                    )
                    offered = tuple(
                        sorted(
                            permanent.object_id
                            for permanent in self.players[trigger.controller].battlefield
                            if self.is_authoritative(permanent, "battlefield")
                            and (
                                {"Artifact", "Creature"}
                                & set(permanent.type_line.split(" â€” ", 1)[0].split())
                            )
                            and self._legal_targeting_protection(permanent, trigger.controller)
                        )
                    )
                    selected = (
                        self.counter_target_chooser(trigger.controller, trigger.source_id, offered)
                        if offered
                        else None
                    )
                    if selected is not None and selected not in offered:
                        raise ValueError("counter transfer chooser returned an illegal target")
                    ability.target_id = selected
                    target = self._objects.get(selected) if selected is not None else None
                    self._artifact_counter_targets[ability.object_id] = (target, offered)
                    self.log(
                        "artifact_counter_transfer_target_selected",
                        event_id=trigger.event.event_id,
                        stack_object_id=ability.object_id,
                        source_id=trigger.source_id,
                        target_id=selected,
                        offered_ids=list(offered),
                    )
                if ability.effect is TriggerEffect.ETB_ANY_TARGET_DAMAGE:
                    self._select_entry_damage_target(ability, trigger)
                if ability.effect is TriggerEffect.ETB_ATTACH_EQUIPMENT:
                    eligible = tuple(
                        sorted(
                            permanent.object_id
                            for permanent in self.players[trigger.controller].battlefield
                            if self.is_authoritative(permanent, "battlefield")
                            and permanent.is_creature
                            and self._legal_targeting_protection(permanent, trigger.controller)
                        )
                    )
                    if not eligible:
                        self.log("equipment_entry_no_legal_target", source_id=trigger.source_id)
                        continue
                    ability.target_id = eligible[0]
                    self.log(
                        "equipment_entry_target_selected",
                        stack_object_id=ability.object_id,
                        event_id=trigger.event.event_id,
                        target_id=ability.target_id,
                        offered_ids=list(eligible),
                    )
                if ability.effect is TriggerEffect.GRANTED_COMBAT_UNTAP_GAIN:
                    ability.target_id = trigger.event.source_id  # recipient, not a target
                if ability.effect is TriggerEffect.EQUIPMENT_SUBTYPE_ENTRY_ATTACH:
                    ability.target_id = trigger.event.subject_ids[0]  # "it", not a target
                if ability.effect is TriggerEffect.ROCK_SOLDIERS_ETB_DESTROY:
                    self._select_rock_soldiers_target(ability, trigger)
                if (
                    ability.effect is TriggerEffect.ETB_DESTROY_TARGET_CREATURE
                    and not self._select_etb_creature_destroy_target(ability, trigger)
                ):
                    continue
                if (
                    ability.effect is TriggerEffect.ETB_TARGET_CREATURE_PUMP_UNTAP
                    and not self._select_etb_pump_target(ability, trigger)
                ):
                    continue
                if (
                    ability.effect is TriggerEffect.SHREDDER_DEATHTOUCH
                    and not self._select_shredder_target(ability, trigger)
                ):
                    continue
                if ability.effect is TriggerEffect.ETB_FOOD_SEARCH:
                    source, card = self._food_search_sources[
                        (trigger.source_id, trigger.oracle_fragment)
                    ]
                    self._food_search_anchors[ability.object_id] = (ability, trigger, source, card)
                if ability.effect is TriggerEffect.ETB_DRAW_DISCARD:
                    source, card = self._draw_discard_sources[
                        (trigger.source_id, trigger.oracle_fragment)
                    ]
                    self._draw_discard_anchors[ability.object_id] = (ability, trigger, source, card)
                if ability.effect is TriggerEffect.COMBAT_DAMAGE_DRAW_DISCARD:
                    source = self._objects[trigger.source_id]
                    assert isinstance(source, Permanent)
                    self._combat_draw_discard_anchors[ability.object_id] = (
                        ability,
                        trigger,
                        source,
                        source.card,
                    )
                if ability.effect is TriggerEffect.COMBAT_DAMAGE_GRAVEYARD_ATTACKER:
                    self._validate_combat_graveyard_event(
                        trigger.event,
                        trigger.source_id,
                        trigger.source_card,
                        trigger.controller,
                        trigger.oracle_fragment,
                    )
                    defender = trigger.event.target_player
                    assert defender is not None
                    choices = sorted(
                        (
                            card
                            for card in self.players[defender].graveyard
                            if card.card.is_creature and self.is_authoritative(card, "graveyard")
                        ),
                        key=lambda card: (-(card.card.power or 0), card.object_id),
                    )
                    if choices:
                        ability.target_id = choices[0].object_id
                    self.log(
                        "combat_graveyard_target_selected",
                        event_id=trigger.event.event_id,
                        stack_object_id=ability.object_id,
                        target_id=ability.target_id,
                        offered_ids=[card.object_id for card in choices],
                        defending_player=defender,
                    )
                if ability.effect is TriggerEffect.COMBAT_DAMAGE_ARTIFACT_COPY:
                    self._authenticate_original_rules_event(trigger.event)
                    source = self._objects.get(trigger.source_id)
                    if (
                        not isinstance(source, Permanent)
                        or source.card is not trigger.source_card
                        or trigger.event.kind is not RulesEventKind.COMBAT_DAMAGE_TO_PLAYER
                        or trigger.event.source_id != trigger.source_id
                        or trigger.event.target_player != 1 - trigger.controller
                    ):
                        raise ValueError("artifact copy trigger lost combat provenance")
                    offered = tuple(
                        sorted(
                            permanent.object_id
                            for permanent in self.players[trigger.controller].battlefield
                            if self.is_authoritative(permanent, "battlefield")
                            and "Artifact" in permanent.type_line.split(" â€” ", 1)[0].split()
                            and self._legal_targeting_protection(permanent, trigger.controller)
                        )
                    )
                    if not offered:
                        self.log(
                            "combat_artifact_copy_no_legal_target",
                            event_id=trigger.event.event_id,
                            source_id=trigger.source_id,
                            offered_ids=[],
                        )
                        continue
                    selected = self.counter_target_chooser(
                        trigger.controller, trigger.source_id, offered
                    )
                    if selected not in offered:
                        raise ValueError("artifact copy chooser returned an illegal target")
                    ability.target_id = selected
                    self._combat_artifact_copy_targets[ability.object_id] = (selected, offered)
                    self.log(
                        "combat_artifact_copy_target_selected",
                        event_id=trigger.event.event_id,
                        stack_object_id=ability.object_id,
                        source_id=trigger.source_id,
                        target_id=selected,
                        offered_ids=list(offered),
                    )
                if ability.effect is TriggerEffect.COMBAT_DAMAGE_HAND_BATTLEFIELD:
                    self._authenticate_original_rules_event(trigger.event)
                    source = self._objects.get(trigger.source_id)
                    if (
                        not isinstance(source, (Permanent, CardObject))
                        or source.card is not trigger.source_card
                        or trigger.event.kind is not RulesEventKind.COMBAT_DAMAGE_TO_PLAYER
                        or trigger.event.source_id != trigger.source_id
                        or trigger.event.target_player != 1 - trigger.controller
                    ):
                        raise ValueError("hand-entry trigger lost combat provenance")
                    # The choice is made on resolution, but the ability carries the
                    # authenticated event and source identity independently of source departure.
                if (
                    ability.effect is TriggerEffect.UTILITY_TARGET
                    and not self._select_utility_target(ability, trigger)
                ):
                    continue
                if ability.effect is TriggerEffect.ETB_MILL_DRAW_DISCARD:
                    source, _card = self._mill_draw_discard_sources[
                        (trigger.source_id, trigger.oracle_fragment)
                    ]
                    self._mill_draw_discard_anchors[ability.object_id] = (source, trigger)
                if ability.effect is TriggerEffect.CLASS_LEVEL_TWO_RECOVERY:
                    self._select_class_recovery_targets(ability, trigger)
                if ability.effect is TriggerEffect.CLASS_COMBAT_ARTIFACT_ANIMATION:
                    candidates = sorted(
                        (
                            permanent
                            for permanent in self.players[trigger.controller].battlefield
                            if "Artifact" in permanent.type_line.split(" â€” ", 1)[0].split()
                            and self._legal_targeting_protection(permanent, trigger.controller)
                        ),
                        key=lambda permanent: (permanent.is_creature, permanent.object_id),
                    )
                    if not candidates:
                        self.log(
                            "class_combat_no_legal_target",
                            event_id=trigger.event.event_id,
                            source_id=trigger.source_id,
                        )
                        continue
                    ability.target_id = candidates[0].object_id
                    self.log(
                        "class_combat_target_selected",
                        event_id=trigger.event.event_id,
                        stack_object_id=ability.object_id,
                        source_id=trigger.source_id,
                        target_id=ability.target_id,
                        offered_ids=[permanent.object_id for permanent in candidates],
                    )
                if ability.effect is TriggerEffect.LTB_MUTAGEN:
                    self._ltb_mutagen_anchors[ability.object_id] = (ability, trigger)
                self._anchor_mill_three(ability, trigger)
                self._anchor_krang_refill(ability, trigger)
                self._anchor_jury_rig(ability, trigger)
                self._anchor_vigilante(ability, trigger)
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

    def _legal_damage_target(self, target: Permanent, controller: int) -> bool:
        if not self.is_authoritative(target, "battlefield") or not target.is_creature:
            return False
        return self._legal_targeting_protection(target, controller)

    def _select_entry_damage_target(
        self, ability: TriggeredAbilityObject, trigger: TriggerInstance
    ) -> None:
        program = self.interpreter.entry_any_target_damage_program(
            trigger.source_card, trigger.oracle_fragment
        )
        if program is None:
            raise ValueError("entry damage program is absent")
        candidates = tuple(
            target
            for player in self.players
            for target in player.battlefield
            if self._legal_damage_target(target, trigger.controller)
        )
        offered = ("player:0", "player:1") + tuple(target.object_id for target in candidates)
        hostile = [
            target
            for target in candidates
            if target.controller != trigger.controller
            and target.toughness is not None
            and target.toughness - target.damage <= program.target_damage
        ]
        selected = (
            self.damage_target_chooser(trigger.controller, offered)
            if self.damage_target_chooser is not None
            else (
                min(hostile, key=lambda target: (target.toughness, target.object_id)).object_id
                if hostile
                else f"player:{1 - trigger.controller}"
            )
        )
        if selected not in offered:
            raise ValueError("entry damage target choice is not legal")
        ability.target_id = selected
        self.log(
            "entry_damage_target_selected",
            stack_object_id=ability.object_id,
            event_id=trigger.event.event_id,
            target_id=selected,
            offered_ids=list(offered),
            oracle_fragment=trigger.oracle_fragment,
        )

    def _select_utility_target(
        self, ability: TriggeredAbilityObject, trigger: TriggerInstance
    ) -> bool:
        semantics = self.interpreter.utility_trigger_semantics(
            trigger.source_card, trigger.oracle_fragment
        )
        assert semantics is not None
        _event, effect, optional = semantics
        targets = [
            target
            for player in self.players
            for target in player.battlefield
            if self.is_authoritative(target, "battlefield")
            and (
                target.is_creature
                if effect == "tap_or_untap_creature"
                else (
                    not target.card.is_land and target.object_id != trigger.source_id
                    if effect == "bounce_other_nonland"
                    else True
                )
            )
        ]
        targets = [
            target
            for target in targets
            if self._legal_targeting_protection(target, trigger.controller)
        ]
        hostile = [target for target in targets if target.controller != trigger.controller]
        if effect == "bounce_other_nonland":
            chosen = max(
                hostile,
                key=lambda target: (
                    target.power if target.is_creature else 0,
                    target.object_id,
                ),
                default=None,
            )
        elif effect == "tap_or_untap_creature":
            chosen = next((target for target in hostile if not target.tapped), None)
            chosen = chosen or next(
                (
                    target
                    for target in targets
                    if target.controller == trigger.controller and target.tapped
                ),
                None,
            )
            chosen = chosen or (targets[0] if targets else None)
        else:
            chosen = next((target for target in hostile if not target.tapped), None)
            chosen = chosen or (hostile[0] if hostile else targets[0] if targets else None)
        if chosen is None and not optional:
            self.log("utility_trigger_no_target", trigger_id=trigger.trigger_id)
            return False
        ability.target_id = chosen.object_id if chosen is not None else None
        source = self._objects[trigger.source_id]
        assert isinstance(source, Permanent)
        self._utility_trigger_anchors[ability.object_id] = (
            ability,
            trigger,
            source,
            chosen,
            semantics,
        )
        self.log(
            "utility_target_selected",
            stack_object_id=ability.object_id,
            trigger_id=trigger.trigger_id,
            source_id=trigger.source_id,
            target_id=ability.target_id,
            offered_ids=[target.object_id for target in targets],
            effect=effect,
        )
        return True

    def _validate_utility_trigger(self, ability: TriggeredAbilityObject) -> None:
        anchor = self._utility_trigger_anchors.get(ability.object_id)
        if anchor is None:
            raise ValueError("utility trigger lacks targeting provenance")
        original, trigger, source, target, semantics = anchor
        event = ability.event
        self._authenticate_original_rules_event(event)
        if (
            ability is not original
            or self._objects.get(ability.object_id) is not ability
            or self._triggers.get(ability.trigger_id) is not trigger
            or trigger.event is not event
            or trigger.source_id != source.object_id
            or self._objects.get(source.object_id) is not source
            or source.card is not ability.source_card
            or source.zone not in {"battlefield", "former"}
            or trigger.controller != ability.controller
            or trigger.oracle_fragment != ability.oracle_fragment
            or ability.effect is not TriggerEffect.UTILITY_TARGET
            or self.interpreter.utility_trigger_semantics(source.card, ability.oracle_fragment)
            != semantics
            or ability.target_id != (target.object_id if target is not None else None)
            or ability.trigger_id in self._utility_trigger_consumed
        ):
            raise ValueError("utility trigger provenance is invalid or consumed")

    def _resolve_utility_trigger(self, ability: TriggeredAbilityObject) -> None:
        self._validate_utility_trigger(ability)
        if ability.zone != "former":
            raise ValueError("utility trigger requires Priority resolution")
        self._utility_trigger_consumed.add(ability.trigger_id)
        _original, _trigger, _source, target, semantics = self._utility_trigger_anchors[
            ability.object_id
        ]
        _event, effect, _optional = semantics
        legal = isinstance(target, Permanent) and self.is_authoritative(target, "battlefield")
        if legal and effect == "bounce_other_nonland":
            legal = not target.card.is_land and target.object_id != ability.source_id
        elif legal and effect == "tap_or_untap_creature":
            legal = target.is_creature
        result = "no_legal_target"
        destination_id = None
        if legal and target is not None:
            if effect == "bounce_other_nonland":
                destination_id = self.move_object(target, "hand", reason="utility_bounce").object_id
                result = "returned"
            elif effect == "tap_or_untap_creature":
                if target.controller != ability.controller and not target.tapped:
                    target.tapped = True
                    result = "tapped"
                elif target.controller == ability.controller and target.tapped:
                    self.untap_permanent(target)
                    result = "untapped" if not target.tapped else "stun_removed"
                else:
                    result = "declined"
            else:
                target.tapped = True
                result = "tapped"
        self.log(
            "utility_trigger_resolved",
            event_id=ability.event.event_id,
            stack_object_id=ability.object_id,
            trigger_id=ability.trigger_id,
            source_id=ability.source_id,
            target_id=ability.target_id,
            destination_id=destination_id,
            effect=effect,
            result=result,
        )

    def _select_class_recovery_targets(
        self, ability: TriggeredAbilityObject, trigger: TriggerInstance
    ) -> None:
        source = self._objects.get(trigger.source_id)
        if (
            not isinstance(source, Permanent)
            or not self.is_authoritative(source, "battlefield")
            or source.card is not trigger.source_card
            or source.class_level != 2
            or trigger.event.kind is not RulesEventKind.CLASS_LEVEL_ADVANCED
            or self.interpreter.class_level_recovery_semantic_coverage(
                source.card, trigger.oracle_fragment
            )
            is None
        ):
            raise ValueError("Class level recovery trigger has invalid provenance")
        candidates = tuple(
            card
            for card in self.players[trigger.controller].graveyard
            if self.is_authoritative(card, "graveyard")
            and card.card.type_line.startswith("Artifact")
        )
        offered = tuple(sorted(card.object_id for card in candidates))
        selected = self.class_recovery_chooser(trigger.controller, trigger.source_id, offered)
        if not isinstance(selected, (tuple, list)) or len(selected) > 2:
            raise ValueError("Class recovery chooser must select up to two listed artifacts")
        selected = tuple(selected)
        if len(set(selected)) != len(selected) or any(item not in offered for item in selected):
            raise ValueError("Class recovery chooser selected an illegal artifact")
        self._class_recovery_targets[ability.object_id] = (selected, offered)
        ability.target_ids = selected
        self.log(
            "class_level_recovery_targets_selected",
            stack_object_id=ability.object_id,
            trigger_id=trigger.trigger_id,
            source_id=trigger.source_id,
            controller=trigger.controller,
            offered_ids=list(offered),
            selected_ids=list(selected),
            oracle_fragment=trigger.oracle_fragment,
        )

    def _select_rock_soldiers_target(
        self, ability: TriggeredAbilityObject, trigger: TriggerInstance
    ) -> None:
        self._authenticate_original_rules_event(trigger.event)
        source = self._objects.get(trigger.source_id)
        if (
            not isinstance(source, Permanent)
            or source.card is not trigger.source_card
            or trigger.event.kind is not RulesEventKind.CREATURE_ENTERED
            or trigger.event.subject_ids != (trigger.source_id,)
            or trigger.event.player_index != trigger.controller
            or (trigger.source_id, trigger.controller) not in trigger.event.battlefield_authority
            or trigger.oracle_fragment not in self.interpreter.fragments(trigger.source_card)
            or not self.interpreter.rock_soldiers_etb_semantic_coverage(
                trigger.source_card, trigger.oracle_fragment
            ).fully_supported
        ):
            raise ValueError("Rock Soldiers trigger has invalid entry provenance")
        candidates = tuple(
            permanent
            for player in self.players
            for permanent in player.battlefield
            if self.is_authoritative(permanent, "battlefield")
            and "Artifact" in permanent.type_line
            and "Creature" not in permanent.type_line
        )
        offered = tuple(sorted(target.object_id for target in candidates))
        choice = self.stun_target_chooser(trigger.controller, trigger.source_id, (*offered, None))
        if choice is not None and (not isinstance(choice, str) or choice not in offered):
            raise ValueError("Rock Soldiers target chooser must return a listed artifact or None")
        self._rock_soldiers_targets[ability.object_id] = choice
        self.log(
            "rock_soldiers_target_selected",
            stack_object_id=ability.object_id,
            trigger_id=trigger.trigger_id,
            event_id=trigger.event.event_id,
            source_id=trigger.source_id,
            target_id=choice,
            offered_ids=offered,
            controller=trigger.controller,
            oracle_fragment=trigger.oracle_fragment,
        )

    def _select_etb_creature_destroy_target(
        self, ability: TriggeredAbilityObject, trigger: TriggerInstance
    ) -> bool:
        """Choose a mandatory legal creature target as this trigger goes on the stack."""
        self._authenticate_original_rules_event(trigger.event)
        source = self._objects.get(trigger.source_id)
        if (
            not isinstance(source, Permanent)
            or not self.is_authoritative(source, "battlefield")
            or source.card is not trigger.source_card
            or trigger.event.kind
            is not (
                RulesEventKind.CREATURE_ENTERED
                if trigger.source_card.is_creature
                else RulesEventKind.PERMANENT_ENTERED
            )
            or trigger.event.subject_ids != (trigger.source_id,)
            or trigger.event.player_index != trigger.controller
            or (trigger.source_id, trigger.controller) not in trigger.event.battlefield_authority
            or trigger.oracle_fragment not in self.interpreter.fragments(trigger.source_card)
            or not self.interpreter.etb_destroy_target_creature(
                trigger.source_card, trigger.oracle_fragment
            )
        ):
            raise ValueError("entry destruction target lacks event provenance")
        candidates = tuple(
            permanent
            for player in self.players
            for permanent in player.battlefield
            if self.is_authoritative(permanent, "battlefield")
            and permanent.is_creature
            and self._legal_targeting_protection(permanent, trigger.controller)
        )
        offered = tuple(sorted(permanent.object_id for permanent in candidates))
        if not offered:
            self.log(
                "etb_creature_destroy_no_legal_target",
                source_id=trigger.source_id,
                event_id=trigger.event.event_id,
            )
            return False
        chosen = self.counter_target_chooser(trigger.controller, trigger.source_id, offered)
        if not isinstance(chosen, str) or chosen not in offered:
            raise ValueError("entry destruction chooser must return a listed creature")
        target = next(permanent for permanent in candidates if permanent.object_id == chosen)
        ability.target_id = chosen
        self._etb_creature_destroy_targets[ability.object_id] = (target, offered)
        self.log(
            "etb_creature_destroy_target_selected",
            stack_object_id=ability.object_id,
            trigger_id=trigger.trigger_id,
            event_id=trigger.event.event_id,
            source_id=trigger.source_id,
            target_id=chosen,
            offered_ids=list(offered),
            controller=trigger.controller,
            oracle_fragment=trigger.oracle_fragment,
        )
        return True

    def _select_etb_pump_target(
        self, ability: TriggeredAbilityObject, trigger: TriggerInstance
    ) -> bool:
        """Announce one legal creature target for the complete entry modifier."""
        self._authenticate_original_rules_event(trigger.event)
        source = self._objects.get(trigger.source_id)
        if (
            not isinstance(source, Permanent)
            or source.card is not trigger.source_card
            or source.zone not in {"battlefield", "former"}
            or trigger.effect is not TriggerEffect.ETB_TARGET_CREATURE_PUMP_UNTAP
            or trigger.event.kind
            is not (
                RulesEventKind.CREATURE_ENTERED
                if source.card.is_creature
                else RulesEventKind.PERMANENT_ENTERED
            )
            or trigger.event.subject_ids != (source.object_id,)
            or trigger.event.player_index != trigger.controller
            or (source.object_id, trigger.controller) not in trigger.event.battlefield_authority
            or trigger.oracle_fragment not in self.interpreter.fragments(source.card)
            or self.interpreter.etb_target_creature_pump_untap(source.card, trigger.oracle_fragment)
            is None
        ):
            raise ValueError("entry modifier target lacks event provenance")
        candidates = tuple(
            permanent
            for player in self.players
            for permanent in player.battlefield
            if self.is_authoritative(permanent, "battlefield")
            and permanent.is_creature
            and self._legal_targeting_protection(permanent, trigger.controller)
        )
        offered = tuple(sorted(permanent.object_id for permanent in candidates))
        if not offered:
            self.log(
                "etb_pump_no_legal_target",
                source_id=trigger.source_id,
                event_id=trigger.event.event_id,
            )
            return False
        chosen = self.counter_target_chooser(trigger.controller, trigger.source_id, offered)
        if not isinstance(chosen, str) or chosen not in offered:
            raise ValueError("entry modifier chooser must return a listed creature")
        target = next(permanent for permanent in candidates if permanent.object_id == chosen)
        ability.target_id = chosen
        self._etb_pump_targets[ability.object_id] = (target, offered)
        self.log(
            "etb_pump_target_selected",
            stack_object_id=ability.object_id,
            trigger_id=trigger.trigger_id,
            event_id=trigger.event.event_id,
            source_id=trigger.source_id,
            target_id=chosen,
            offered_ids=list(offered),
            controller=trigger.controller,
            oracle_fragment=trigger.oracle_fragment,
        )
        return True

    def _validate_etb_pump_trigger(self, ability: TriggeredAbilityObject) -> tuple[int, int]:
        """Authenticate the entry event and original mandatory target selection."""
        trigger = self._triggers.get(ability.trigger_id or "")
        event = ability.event
        source = self._objects.get(ability.source_id)
        target, offered = self._etb_pump_targets.get(ability.object_id, (None, ()))
        self._authenticate_original_rules_event(event)
        numbers = self.interpreter.etb_target_creature_pump_untap(
            ability.source_card, ability.oracle_fragment
        )
        if (
            numbers is None
            or trigger is None
            or trigger.event is not event
            or trigger.effect is not TriggerEffect.ETB_TARGET_CREATURE_PUMP_UNTAP
            or trigger.source_id != ability.source_id
            or trigger.source_card is not ability.source_card
            or trigger.oracle_fragment != ability.oracle_fragment
            or trigger.controller != ability.controller
            or not isinstance(source, Permanent)
            or source.card is not ability.source_card
            or source.zone not in {"battlefield", "former"}
            or event.kind
            is not (
                RulesEventKind.CREATURE_ENTERED
                if ability.source_card.is_creature
                else RulesEventKind.PERMANENT_ENTERED
            )
            or event.subject_ids != (source.object_id,)
            or event.player_index != ability.controller
            or (source.object_id, ability.controller) not in event.battlefield_authority
            or not isinstance(target, Permanent)
            or self._objects.get(target.object_id) is not target
            or not offered
            or ability.target_id != target.object_id
            or ability.target_id not in offered
        ):
            raise ValueError("entry modifier trigger has invalid target provenance")
        return numbers

    def _select_shredder_target(
        self, ability: TriggeredAbilityObject, trigger: TriggerInstance
    ) -> bool:
        self._authenticate_original_rules_event(trigger.event)
        source = self._objects.get(trigger.source_id)
        coverage = self.interpreter.shredder_deathtouch_semantic_coverage(
            trigger.source_card, trigger.oracle_fragment
        )
        if (
            not isinstance(source, Permanent)
            or source.card is not trigger.source_card
            or not self.is_authoritative(source, "battlefield")
            or trigger.event.kind
            not in {
                RulesEventKind.CREATURE_ENTERED,
                RulesEventKind.ATTACKERS_DECLARED,
            }
            or trigger.oracle_fragment not in self.interpreter.fragments(trigger.source_card)
            or coverage is None
            or not coverage.fully_supported
        ):
            raise ValueError("Shredder trigger has invalid source provenance")
        candidates = tuple(
            permanent
            for permanent in self.players[trigger.controller].battlefield
            if self.is_authoritative(permanent, "battlefield")
            and permanent is not source
            and permanent.is_creature
        )
        offered = tuple(sorted(permanent.object_id for permanent in candidates))
        if not offered:
            return False
        choice = self.counter_target_chooser(trigger.controller, trigger.source_id, offered)
        if not isinstance(choice, str) or choice not in offered:
            raise ValueError("Shredder target chooser must return a listed creature")
        target = next(permanent for permanent in candidates if permanent.object_id == choice)
        ability.target_id = choice
        self._shredder_targets[ability.object_id] = (target, target.card, offered)
        self.log(
            "shredder_target_selected",
            stack_object_id=ability.object_id,
            trigger_id=trigger.trigger_id,
            event_id=trigger.event.event_id,
            source_id=trigger.source_id,
            target_id=choice,
            offered_ids=offered,
            controller=trigger.controller,
            oracle_fragment=trigger.oracle_fragment,
        )
        return True

    def _validate_shredder_trigger(self, ability: TriggeredAbilityObject) -> None:
        trigger = self._triggers.get(ability.trigger_id)
        source = self._objects.get(ability.source_id)
        target, target_card, offered = self._shredder_targets.get(
            ability.object_id, (None, None, ())
        )
        self._authenticate_original_rules_event(ability.event)
        if (
            trigger is None
            or trigger.event is not ability.event
            or trigger.effect is not TriggerEffect.SHREDDER_DEATHTOUCH
            or trigger.source_id != ability.source_id
            or trigger.source_card is not ability.source_card
            or trigger.oracle_fragment != ability.oracle_fragment
            or trigger.controller != ability.controller
            or (
                source is not None
                and (
                    not isinstance(source, Permanent)
                    or source.card is not ability.source_card
                    or source.zone not in {"battlefield", "former"}
                )
            )
            or (
                offered
                and (
                    ability.target_id not in offered
                    or target is None
                    or target.object_id != ability.target_id
                    or self._objects.get(target.object_id) is not target
                    or target.card is not target_card
                )
            )
        ):
            raise ValueError("Shredder trigger has invalid target provenance")

    def _validate_rock_soldiers_trigger(self, ability: TriggeredAbilityObject) -> None:
        trigger = self._triggers.get(ability.trigger_id)
        source = self._objects.get(ability.source_id)
        self._authenticate_original_rules_event(ability.event)
        if (
            trigger is None
            or trigger.event is not ability.event
            or trigger.source_id != ability.source_id
            or trigger.source_card is not ability.source_card
            or trigger.oracle_fragment != ability.oracle_fragment
            or trigger.controller != ability.controller
            or not isinstance(source, Permanent)
            or source.card is not ability.source_card
            or source.zone not in {"battlefield", "former"}
        ):
            raise ValueError("Rock Soldiers trigger has invalid source provenance")

    def _validate_etb_creature_destroy_trigger(self, ability: TriggeredAbilityObject) -> None:
        trigger = self._triggers.get(ability.trigger_id or "")
        event = ability.event
        source = self._objects.get(ability.source_id)
        target, offered = self._etb_creature_destroy_targets.get(ability.object_id, (None, ()))
        self._authenticate_original_rules_event(event)
        if (
            trigger is None
            or trigger.event is not event
            or trigger.effect is not TriggerEffect.ETB_DESTROY_TARGET_CREATURE
            or trigger.source_id != ability.source_id
            or trigger.source_card is not ability.source_card
            or trigger.oracle_fragment != ability.oracle_fragment
            or trigger.controller != ability.controller
            or not isinstance(source, Permanent)
            or source.card is not ability.source_card
            or source.zone not in {"battlefield", "former"}
            or self._rules_events.get(event.event_id) is not event
            or event.kind
            is not (
                RulesEventKind.CREATURE_ENTERED
                if ability.source_card.is_creature
                else RulesEventKind.PERMANENT_ENTERED
            )
            or event.subject_ids != (source.object_id,)
            or event.player_index != ability.controller
            or (source.object_id, ability.controller) not in event.battlefield_authority
            or not self.interpreter.etb_destroy_target_creature(
                ability.source_card, ability.oracle_fragment
            )
            or not isinstance(target, Permanent)
            or self._objects.get(target.object_id) is not target
            or not offered
            or ability.target_id != target.object_id
            or ability.target_id not in offered
        ):
            raise ValueError("entry destruction trigger has invalid target provenance")

    def _validate_equipment_granted_trigger(self, ability: TriggeredAbilityObject) -> None:
        trigger = self._triggers.get(ability.trigger_id or "")
        event = ability.event
        self._authenticate_original_rules_event(event)
        if (
            trigger is None
            or trigger.event is not event
            or trigger.effect is not ability.effect
            or trigger.source_id != ability.source_id
            or trigger.source_card is not ability.source_card
            or trigger.oracle_fragment != ability.oracle_fragment
            or trigger.controller != ability.controller
            or self._rules_events.get(event.event_id) is not event
        ):
            raise ValueError("Equipment trigger identity is invalid")
        source = self._objects.get(ability.source_id)
        if ability.effect is TriggerEffect.GRANTED_COMBAT_UNTAP_GAIN:
            grant = self._objects.get(trigger.grant_source_id or "")
            if (
                not isinstance(source, Permanent)
                or source.card is not ability.source_card
                or source.zone not in {"battlefield", "former"}
                or not isinstance(grant, Permanent)
                or grant.zone not in {"battlefield", "former"}
                or self.interpreter.equipment_granted_combat_semantics(
                    grant.card, ability.oracle_fragment
                )
                is None
                or event.kind
                not in {
                    RulesEventKind.COMBAT_DAMAGE_TO_PLAYER,
                    RulesEventKind.COMBAT_DAMAGE_TO_CREATURE,
                }
                or event.source_id != source.object_id
                or not event.subject_ids
                or event.subject_ids[0] != source.object_id
                or event.player_index != ability.controller
                or (
                    event.target_player != 1 - ability.controller
                    if event.kind is RulesEventKind.COMBAT_DAMAGE_TO_PLAYER
                    else event.target_player is not None or len(event.subject_ids) != 2
                )
                or event.amount is None
                or event.amount <= 0
                or (grant.object_id, grant.controller) not in event.battlefield_authority
                or (source.object_id, ability.controller) not in event.battlefield_authority
                or ability.target_id != source.object_id
            ):
                raise ValueError("granted combat trigger provenance is invalid")
        elif ability.effect is TriggerEffect.EQUIPMENT_SUBTYPE_ENTRY_ATTACH:
            subtype = self.interpreter.equipment_subtype_entry_attach(
                ability.source_card, ability.oracle_fragment
            )
            if (
                subtype is None
                or not isinstance(source, Permanent)
                or source.card is not ability.source_card
                or source.zone not in {"battlefield", "former"}
                or event.kind is not RulesEventKind.CREATURE_ENTERED
                or len(event.subject_ids) != 1
                or ability.target_id != event.subject_ids[0]
                or (source.object_id, ability.controller) not in event.battlefield_authority
                or event.player_index != ability.controller
                or not any(
                    object_id == ability.target_id
                    and controller == ability.controller
                    and subtype in type_line.partition(" â€” ")[2].split()
                    for object_id, controller, type_line in event.battlefield_characteristics
                )
            ):
                raise ValueError("Equipment subtype-entry trigger provenance is invalid")

    def _validate_combat_draw_life_event(
        self, event: RulesEvent, source: Permanent, fragment: str
    ) -> None:
        self._authenticate_original_rules_event(event)
        if (
            event.kind is not RulesEventKind.COMBAT_DAMAGE_TO_PLAYER
            or event.source_id != source.object_id
            or event.subject_ids != (source.object_id,)
            or event.player_index != source.controller
            or event.target_player != 1 - source.controller
            or event.amount is None
            or event.amount <= 0
            or (source.object_id, source.controller) not in event.battlefield_authority
            or fragment not in self.interpreter.fragments(source.rules_card)
            or self.interpreter.combat_damage_draw_lose_life(source.card, fragment) is None
        ):
            raise ValueError("combat draw/life event provenance is invalid")

    def _validate_combat_draw_life_trigger(self, ability: TriggeredAbilityObject) -> None:
        trigger = self._triggers.get(ability.trigger_id or "")
        event = ability.event
        source = self._objects.get(ability.source_id)
        self._authenticate_original_rules_event(event)
        if (
            trigger is None
            or trigger.event is not event
            or trigger.effect is not TriggerEffect.COMBAT_DAMAGE_DRAW_LOSE_LIFE
            or trigger.source_id != ability.source_id
            or trigger.source_card is not ability.source_card
            or trigger.oracle_fragment != ability.oracle_fragment
            or trigger.controller != ability.controller
            or not isinstance(source, Permanent)
            or source.card is not ability.source_card
            or source.zone not in {"battlefield", "former"}
            or self._rules_events.get(event.event_id) is not event
            or event.kind is not RulesEventKind.COMBAT_DAMAGE_TO_PLAYER
            or event.source_id != source.object_id
            or event.subject_ids != (source.object_id,)
            or event.player_index != ability.controller
            or event.target_player != 1 - ability.controller
            or event.amount is None
            or event.amount <= 0
            or (source.object_id, ability.controller) not in event.battlefield_authority
            or self.interpreter.combat_damage_draw_lose_life(
                ability.source_card, ability.oracle_fragment
            )
            is None
        ):
            raise ValueError("combat draw/life trigger provenance is invalid")

    def _validate_combat_graveyard_event(
        self,
        event: RulesEvent,
        source_id: str,
        source_card: CardFact,
        controller: int,
        fragment: str,
    ) -> None:
        self._authenticate_original_rules_event(event)
        source = self._objects.get(source_id)
        if (
            not isinstance(source, Permanent)
            or source.card is not source_card
            or source.controller != controller
            or event.kind is not RulesEventKind.COMBAT_DAMAGE_TO_PLAYER
            or event.source_id != source_id
            or event.subject_ids != (source_id,)
            or event.player_index != controller
            or event.target_player != 1 - controller
            or event.amount is None
            or event.amount <= 0
            or (source_id, controller) not in event.battlefield_authority
            or fragment not in self.interpreter.fragments(source_card)
            or not self.interpreter.combat_damage_graveyard_attacker(source_card, fragment)
        ):
            raise ValueError("combat graveyard return lacks damage provenance")

    def _validate_combat_graveyard_trigger(self, ability: TriggeredAbilityObject) -> None:
        trigger = self._triggers.get(ability.trigger_id or "")
        if (
            trigger is None
            or trigger.effect is not TriggerEffect.COMBAT_DAMAGE_GRAVEYARD_ATTACKER
            or trigger.event is not ability.event
            or trigger.source_id != ability.source_id
            or trigger.source_card is not ability.source_card
            or trigger.oracle_fragment != ability.oracle_fragment
            or trigger.controller != ability.controller
        ):
            raise ValueError("combat graveyard trigger identity is invalid")
        self._validate_combat_graveyard_event(
            ability.event,
            ability.source_id,
            ability.source_card,
            ability.controller,
            ability.oracle_fragment,
        )
        if ability.target_id is not None:
            target = self._objects.get(ability.target_id)
            if (
                not isinstance(target, CardObject)
                or target.owner != ability.event.target_player
                or not target.card.is_creature
            ):
                raise ValueError("combat graveyard target identity is invalid")
        selections = [
            record
            for record in self.events
            if record.get("event") == "combat_graveyard_target_selected"
            and record.get("stack_object_id") == ability.object_id
        ]
        if (
            len(selections) != 1
            or selections[0]["event_id"] != ability.event.event_id
            or selections[0]["target_id"] != ability.target_id
            or (
                ability.target_id is not None
                and ability.target_id not in selections[0]["offered_ids"]
            )
        ):
            raise ValueError("combat graveyard target lacks selection provenance")

    def _validate_combat_artifact_copy_trigger(self, ability: TriggeredAbilityObject) -> None:
        trigger = self._triggers.get(ability.trigger_id or "")
        source = self._objects.get(ability.source_id)
        self._authenticate_original_rules_event(ability.event)
        if (
            trigger is None
            or trigger.effect is not TriggerEffect.COMBAT_DAMAGE_ARTIFACT_COPY
            or trigger.event is not ability.event
            or trigger.source_id != ability.source_id
            or trigger.source_card is not ability.source_card
            or trigger.oracle_fragment != ability.oracle_fragment
            or trigger.controller != ability.controller
            or not isinstance(source, Permanent)
            or source.card is not ability.source_card
            or source.zone not in {"battlefield", "former"}
            or ability.event.kind is not RulesEventKind.COMBAT_DAMAGE_TO_PLAYER
            or ability.event.source_id != ability.source_id
            or ability.event.subject_ids != (ability.source_id,)
            or ability.event.player_index != ability.controller
            or ability.event.target_player != 1 - ability.controller
            or ability.event.amount is None
            or ability.event.amount <= 0
            or (ability.source_id, ability.controller) not in ability.event.battlefield_authority
            or not self.interpreter.combat_damage_artifact_copy(
                ability.source_card, ability.oracle_fragment
            )
            or ability.target_id is None
            or self._combat_artifact_copy_targets.get(ability.object_id, (None, ()))[0]
            != ability.target_id
        ):
            raise ValueError("combat artifact copy trigger provenance is invalid")

    def _validate_combat_hand_battlefield_trigger(self, ability: TriggeredAbilityObject) -> None:
        trigger = self._triggers.get(ability.trigger_id or "")
        source = self._objects.get(ability.source_id)
        self._authenticate_original_rules_event(ability.event)
        if (
            trigger is None
            or trigger.effect is not TriggerEffect.COMBAT_DAMAGE_HAND_BATTLEFIELD
            or trigger.event is not ability.event
            or trigger.source_id != ability.source_id
            or trigger.source_card is not ability.source_card
            or trigger.oracle_fragment != ability.oracle_fragment
            or trigger.controller != ability.controller
            or not isinstance(source, Permanent)
            or source.card is not ability.source_card
            or source.zone not in {"battlefield", "former"}
            or ability.event.kind is not RulesEventKind.COMBAT_DAMAGE_TO_PLAYER
            or ability.event.source_id != ability.source_id
            or ability.event.subject_ids != (ability.source_id,)
            or ability.event.player_index != ability.controller
            or ability.event.target_player != 1 - ability.controller
            or ability.event.amount is None
            or ability.event.amount <= 0
            or (ability.source_id, ability.controller) not in ability.event.battlefield_authority
            or not self.interpreter.combat_damage_hand_battlefield(
                ability.source_card, ability.oracle_fragment
            )
        ):
            raise ValueError("combat hand-entry trigger provenance is invalid")

    def _validate_artifact_entry_self_counter_trigger(
        self, ability: TriggeredAbilityObject
    ) -> None:
        """Authenticate the entry snapshot, not the entering object's later zone."""
        event = ability.event
        self._authenticate_original_rules_event(event)
        trigger = self._triggers.get(ability.trigger_id)
        source = self._objects.get(ability.source_id)
        if (
            self._rules_events.get(event.event_id) is not event
            or event.kind not in {RulesEventKind.PERMANENT_ENTERED, RulesEventKind.CREATURE_ENTERED}
            or len(event.subject_ids) != 1
            or event.player_index != ability.controller
            or not any(
                object_id == event.subject_ids[0]
                and controller == event.player_index
                and "Artifact" in type_line
                for object_id, controller, type_line in event.battlefield_characteristics
            )
            or (ability.source_id, ability.controller) not in event.battlefield_authority
            or ability.source_id == event.subject_ids[0]
            or not isinstance(source, Permanent)
            or source.card is not ability.source_card
            or ability.oracle_fragment not in self.interpreter.fragments(source.card)
            or not (
                (
                    coverage := self.interpreter.artifact_entry_self_counter_semantic_coverage(
                        source.card, ability.oracle_fragment
                    )
                )
                and coverage.fully_supported
            )
            or trigger is None
            or trigger.event is not event
            or trigger.effect is not ability.effect
            or trigger.source_id != ability.source_id
            or trigger.source_card is not ability.source_card
            or trigger.controller != ability.controller
            or trigger.oracle_fragment != ability.oracle_fragment
            or ability.target_id is not None
            or ability.target_ids
        ):
            raise ValueError("artifact entry counter trigger lacks original event provenance")

    def _resolve_triggered_ability(self, ability: TriggeredAbilityObject) -> None:
        if (
            not self.stack
            or self.stack[-1] is not ability
            or not self.is_authoritative(ability, "stack")
        ):
            raise ValueError("triggered ability must be the authoritative top stack object")
        if (
            ability.effect is TriggerEffect.ETB_TAP_STUN
            or ability.object_id in self._stun_selections
        ):
            self._validate_stun_trigger(ability)
            if any(
                dict(record).get("event") == "stun_etb_resolved"
                and dict(record).get("stack_object_id") == ability.object_id
                for _cursor, record in self._stun_history
            ):
                raise ValueError("stun trigger has already resolved")
            selected = self._stun_selections[ability.object_id].target
            if selected is not None and self.is_authoritative(selected, "battlefield"):
                self._validate_stun_targeting_dependencies(selected)
        if ability.effect is TriggerEffect.ROCK_SOLDIERS_ETB_DESTROY:
            self._validate_rock_soldiers_trigger(ability)
        if ability.effect is TriggerEffect.ATTACK_TARGET_COUNTER:
            self._authenticate_original_rules_event(ability.event)
            if (
                ability.event.kind is not RulesEventKind.ATTACKERS_DECLARED
                or ability.event.player_index != ability.controller
                or (ability.source_id, ability.controller)
                not in ability.event.battlefield_authority
                or not self.interpreter.attack_target_counter(
                    ability.source_card, ability.oracle_fragment
                )
                or ability.target_id not in ability.event.subject_ids
                or self._attack_counter_targets.get(ability.object_id)
                != (ability.target_id, ability.trigger_id)
                or self._triggers.get(ability.trigger_id) is None
                or self._triggers[ability.trigger_id].event is not ability.event
            ):
                raise ValueError("attack counter resolution lacks original provenance")
        if ability.effect is TriggerEffect.ETB_DESTROY_TARGET_CREATURE:
            self._validate_etb_creature_destroy_trigger(ability)
        if ability.effect is TriggerEffect.ETB_TARGET_CREATURE_PUMP_UNTAP:
            self._validate_etb_pump_trigger(ability)
        if ability.effect is TriggerEffect.COMBAT_DAMAGE_DRAW_LOSE_LIFE:
            self._validate_combat_draw_life_trigger(ability)
        if ability.effect is TriggerEffect.COMBAT_DAMAGE_GRAVEYARD_ATTACKER:
            self._validate_combat_graveyard_trigger(ability)
        if ability.effect is TriggerEffect.COMBAT_DAMAGE_ARTIFACT_COPY:
            self._validate_combat_artifact_copy_trigger(ability)
        if ability.effect is TriggerEffect.COMBAT_DAMAGE_HAND_BATTLEFIELD:
            self._validate_combat_hand_battlefield_trigger(ability)
        if ability.effect in {
            TriggerEffect.GRANTED_COMBAT_UNTAP_GAIN,
            TriggerEffect.EQUIPMENT_SUBTYPE_ENTRY_ATTACH,
        }:
            self._validate_equipment_granted_trigger(ability)
        if ability.effect is TriggerEffect.ETB_ATTACH_EQUIPMENT:
            self._authenticate_original_rules_event(ability.event)
            if (
                ability.event.kind is not RulesEventKind.PERMANENT_ENTERED
                or ability.event.subject_ids != (ability.source_id,)
                or (ability.source_id, ability.controller)
                not in ability.event.battlefield_authority
                or not self.interpreter.equipment_etb_attach(
                    ability.source_card, ability.oracle_fragment
                )
            ):
                raise ValueError("equipment entry resolution lacks event provenance")
        if ability.effect is TriggerEffect.SHREDDER_DEATHTOUCH:
            self._validate_shredder_trigger(ability)
        if ability.effect is TriggerEffect.PARAMECIA_EXILE_CHOICE and (
            ability.event.kind is not RulesEventKind.CREATURE_DIED
            or ability.source_id not in self._paramecia_departures
        ):
            raise ValueError("Paramecia trigger has invalid provenance")
        if ability.effect is TriggerEffect.ETB_DRAIN_GAIN_SCRY:
            self._validate_etb_drain_gain_scry_trigger(ability)
        if ability.effect is TriggerEffect.ETB_ANY_TARGET_DAMAGE:
            self._authenticate_original_rules_event(ability.event)
            if (
                ability.event.subject_ids != (ability.source_id,)
                or ability.event.kind
                not in {RulesEventKind.PERMANENT_ENTERED, RulesEventKind.CREATURE_ENTERED}
                or ability.event.player_index != ability.controller
                or (ability.source_id, ability.controller)
                not in ability.event.battlefield_authority
                or self.interpreter.entry_any_target_damage_program(
                    ability.source_card, ability.oracle_fragment
                )
                is None
            ):
                raise ValueError("entry damage resolution provenance is invalid")
        if ability.effect is TriggerEffect.ETB_SELF_LIFE_GAIN:
            self._validate_etb_self_life_gain_trigger(ability)
        if ability.effect is TriggerEffect.PERMANENT_LEFT_SELF_COUNTER:
            self._validate_permanent_left_counter_provenance(
                controller=ability.controller,
                source_id=ability.source_id,
                source_card=ability.source_card,
                oracle_fragment=ability.oracle_fragment,
                event=ability.event,
                trigger_id=ability.trigger_id,
            )
        if ability.effect is TriggerEffect.CONTROLLED_CREATURE_LEFT_OPPONENT_LOSS:
            self._validate_controlled_creature_departure_loss(
                controller=ability.controller,
                source_id=ability.source_id,
                source_card=ability.source_card,
                oracle_fragment=ability.oracle_fragment,
                event=ability.event,
                trigger_id=ability.trigger_id,
            )
        if ability.effect is TriggerEffect.CONTROLLED_COUNTERED_CREATURE_LEFT_LIFE:
            self._validate_countered_creature_departure_life(
                ability.event,
                ability.source_id,
                ability.source_card,
                ability.oracle_fragment,
                ability.controller,
                trigger_id=ability.trigger_id,
            )
        if ability.effect is TriggerEffect.CONTROLLED_ARTIFACT_COUNTER_TRANSFER:
            self._validate_artifact_counter_transfer(
                ability.event,
                ability.source_id,
                ability.source_card,
                ability.oracle_fragment,
                ability.controller,
                trigger_id=ability.trigger_id,
            )
            selection = self._artifact_counter_targets.get(ability.object_id)
            if (
                selection is None
                or (selection[0] is None and ability.target_id is not None)
                or (
                    selection[0] is not None
                    and (
                        selection[0].object_id != ability.target_id
                        or ability.target_id not in selection[1]
                    )
                )
            ):
                raise ValueError("counter transfer target selection is unauthenticated")
        if ability.effect is TriggerEffect.DAMAGE_TO_SELF_MANA:
            self._validate_damage_to_self_mana(
                ability.event,
                ability.source_id,
                ability.source_card,
                ability.oracle_fragment,
                ability.controller,
                trigger_id=ability.trigger_id,
            )
        if ability.effect is TriggerEffect.CLASS_SPELL_CAST_TEAM_COUNTER:
            source = self._objects.get(ability.source_id)
            if not isinstance(source, Permanent):
                raise ValueError("Class spell-cast source is invalid")
            self._validate_class_spell_cast_team_counter(
                ability, ability.event, source, ability.oracle_fragment, ability.controller
            )
        if ability.effect is TriggerEffect.ARTIFACT_ENTRY_SELF_COUNTER:
            self._validate_artifact_entry_self_counter_trigger(ability)
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
        if ability.effect is TriggerEffect.ALLIANCE_TEMPORARY_KEYWORD_CHOICE:
            self._validate_alliance_temporary_keyword_choice_trigger(ability)
        if (
            ability.effect is TriggerEffect.ETB_FOOD_SEARCH
            or ability.object_id in self._food_search_anchors
        ):
            self._validate_etb_food_search_trigger(ability)
        if (
            ability.effect is TriggerEffect.ETB_DRAW_DISCARD
            or ability.object_id in self._draw_discard_anchors
        ):
            self._validate_etb_draw_discard_trigger(ability)
        if (
            ability.effect is TriggerEffect.COMBAT_DAMAGE_DRAW_DISCARD
            or ability.object_id in self._combat_draw_discard_anchors
        ):
            self._validate_combat_draw_discard_trigger(ability)
        if (
            ability.effect is TriggerEffect.UTILITY_TARGET
            or ability.object_id in self._utility_trigger_anchors
        ):
            self._validate_utility_trigger(ability)
        if (
            ability.effect is TriggerEffect.LTB_MUTAGEN
            or ability.object_id in self._ltb_mutagen_anchors
        ):
            self._validate_ltb_mutagen_trigger(ability)
        if (
            ability.effect in {TriggerEffect.ETB_VIGILANTE, TriggerEffect.VIGILANTE_DISCARD}
            or ability.object_id in self._vigilante_stack
        ):
            self._validate_vigilante_trigger(ability)
        if (
            ability.effect is TriggerEffect.ETB_JURY_RIG
            or ability.object_id in self._jury_rig_anchors
        ):
            self._validate_jury_rig_trigger(ability)
        if (
            ability.effect is TriggerEffect.ETB_KRANG_REFILL
            or ability.object_id in self._krang_refill_anchors
        ):
            self._preflight_krang_refill(ability)
        if (
            ability.effect is TriggerEffect.ETB_MILL_THREE
            or ability.object_id in self._mill_three_anchors
        ):
            self._preflight_mill_three(ability)
        self.stack.pop()
        ability.zone = "former"
        for index, evidence in enumerate(self.activation_evidence):
            if evidence.stack_object_id == ability.object_id:
                self.activation_evidence[index] = replace(evidence, resolved=True)
                break
        source = self._objects.get(ability.source_id)
        source_permanent = (
            source
            if isinstance(source, Permanent) and self.is_authoritative(source, "battlefield")
            else None
        )
        subjects = [self._objects.get(object_id) for object_id in ability.event.subject_ids]

        if ability.effect is TriggerEffect.SHREDDER_DEATHTOUCH:
            target, target_card, _offered = self._shredder_targets.get(
                ability.object_id, (None, None, ())
            )
            legal = (
                target is not None
                and self._objects.get(target.object_id) is target
                and self.is_authoritative(target, "battlefield")
                and target.controller == ability.controller
                and target.card is target_card
                and target.is_creature
                and target.object_id != ability.source_id
            )
            if legal:
                target.temporary_keyword_effects.append(
                    TemporaryKeywordEffect(
                        TemporaryKeyword.DEATHTOUCH,
                        "until_end_of_turn",
                        ability.source_id,
                        ability.oracle_fragment,
                        timestamp=self._effect_timestamp(),
                    )
                )
                self.log(
                    "shredder_deathtouch_granted",
                    stack_object_id=ability.object_id,
                    trigger_id=ability.trigger_id,
                    event_id=ability.event.event_id,
                    source_id=ability.source_id,
                    target_id=target.object_id,
                    duration="until_end_of_turn",
                )
            else:
                self.log(
                    "shredder_deathtouch_failed_closed",
                    stack_object_id=ability.object_id,
                    trigger_id=ability.trigger_id,
                    source_id=ability.source_id,
                    target_id=target.object_id if target is not None else None,
                )
        elif ability.effect is TriggerEffect.GRANTED_COMBAT_UNTAP_GAIN:
            recipient = self._objects.get(ability.target_id or "")
            untapped = isinstance(recipient, Permanent) and self.is_authoritative(
                recipient, "battlefield"
            )
            if untapped:
                recipient.tapped = False
            grant = self._triggers[ability.trigger_id].grant_source_id
            assert grant is not None
            gain = self.interpreter.equipment_granted_combat_semantics(
                self._objects[grant].card, ability.oracle_fragment
            )
            assert gain is not None
            self.gain_life(
                ability.controller,
                gain[2],
                source_card=self._objects[grant].card.name,
                oracle_fragment=ability.oracle_fragment,
                defer_trigger_delivery=True,
            )
            self.log(
                "equipment_granted_combat_resolved",
                stack_object_id=ability.object_id,
                event_id=ability.event.event_id,
                grant_source_id=grant,
                recipient_id=ability.target_id,
                untapped=untapped,
                life_gained=gain[2],
                damage_recipient_id=(
                    ability.event.subject_ids[1]
                    if ability.event.kind is RulesEventKind.COMBAT_DAMAGE_TO_CREATURE
                    else None
                ),
            )
        elif ability.effect is TriggerEffect.EQUIPMENT_SUBTYPE_ENTRY_ATTACH:
            recipient = self._objects.get(ability.target_id or "")
            chosen = self.equipment_attach_chooser(
                ability.controller, ability.source_id, ability.target_id
            )
            if not isinstance(chosen, bool):
                raise ValueError("optional Equipment attachment chooser must return a boolean")
            legal = (
                chosen
                and source_permanent is not None
                and "Equipment" in source_permanent.type_line
                and isinstance(recipient, Permanent)
                and self.is_authoritative(recipient, "battlefield")
                and recipient.is_creature
            )
            if legal:
                source_permanent.attached_to = recipient.object_id
                source_permanent.attachment_timestamp = self._effect_timestamp()
                self.refresh_static_pt_modifiers()
            self.log(
                "equipment_subtype_entry_attach_resolved",
                stack_object_id=ability.object_id,
                event_id=ability.event.event_id,
                source_id=ability.source_id,
                recipient_id=ability.target_id,
                chosen=chosen,
                attached=legal,
            )
        elif ability.effect is TriggerEffect.ETB_ATTACH_EQUIPMENT:
            equipment = self._objects.get(ability.source_id)
            target = self._objects.get(ability.target_id or "")
            legal = (
                isinstance(equipment, Permanent)
                and self.is_authoritative(equipment, "battlefield")
                and "Equipment" in equipment.type_line
                and isinstance(target, Permanent)
                and self.is_authoritative(target, "battlefield")
                and target.is_creature
                and target.controller == ability.controller
                and self._legal_targeting_protection(target, ability.controller)
            )
            if legal:
                equipment.attached_to = target.object_id
                equipment.attachment_timestamp = self._effect_timestamp()
                self.refresh_static_pt_modifiers()
            self.log(
                "equipment_entry_attach_resolved",
                stack_object_id=ability.object_id,
                source_id=ability.source_id,
                target_id=ability.target_id,
                attached=legal,
            )
        elif ability.effect is TriggerEffect.ROCK_SOLDIERS_ETB_DESTROY:
            target_id = self._rock_soldiers_targets.get(ability.object_id)
            target = self._objects.get(target_id) if target_id else None
            legal = (
                isinstance(target, Permanent)
                and self.is_authoritative(target, "battlefield")
                and "Artifact" in target.type_line
                and "Creature" not in target.type_line
            )
            if legal:
                self.destroy(target)
                self.log(
                    "rock_soldiers_destroyed",
                    stack_object_id=ability.object_id,
                    source_id=ability.source_id,
                    target_id=target.object_id,
                )
            else:
                self.log(
                    "rock_soldiers_no_target",
                    stack_object_id=ability.object_id,
                    source_id=ability.source_id,
                )
        elif ability.effect is TriggerEffect.ETB_DESTROY_TARGET_CREATURE:
            target = self._etb_creature_destroy_targets[ability.object_id][0]
            legal = (
                self.is_authoritative(target, "battlefield")
                and target.is_creature
                and self._legal_targeting_protection(target, ability.controller)
            )
            if legal:
                self.destroy(target)
            self.log(
                "etb_creature_destroy_resolved",
                stack_object_id=ability.object_id,
                trigger_id=ability.trigger_id,
                event_id=ability.event.event_id,
                source_id=ability.source_id,
                target_id=ability.target_id,
                legal_target=legal,
                destroyed=legal and not self.is_authoritative(target, "battlefield"),
            )
        elif ability.effect is TriggerEffect.ETB_TARGET_CREATURE_PUMP_UNTAP:
            power, toughness = self._validate_etb_pump_trigger(ability)
            target = self._etb_pump_targets[ability.object_id][0]
            legal = (
                self.is_authoritative(target, "battlefield")
                and target.is_creature
                and self._legal_targeting_protection(target, ability.controller)
            )
            was_tapped = target.tapped if legal else None
            if legal:
                self.apply_pt_modifier(
                    target,
                    power,
                    toughness,
                    duration="until_end_of_turn",
                    source_card=ability.source_card.name,
                    oracle_fragment=ability.oracle_fragment,
                    source_object_id=ability.source_id,
                )
                target.tapped = False
            self.log(
                "etb_pump_untap_resolved",
                stack_object_id=ability.object_id,
                trigger_id=ability.trigger_id,
                event_id=ability.event.event_id,
                source_id=ability.source_id,
                target_id=ability.target_id,
                legal_target=legal,
                power=power if legal else 0,
                toughness=toughness if legal else 0,
                was_tapped=was_tapped,
                untapped=bool(legal and was_tapped),
            )
        if ability.effect is TriggerEffect.ETB_TAP_STUN:
            selection = self._stun_selections[ability.object_id]
            target = selection.target
            legal = target is not None and self.is_authoritative(target, "battlefield")
            legal = (
                legal
                and "Creature" in target.type_line
                and not (
                    target.controller != ability.controller
                    and self.has_temporary_keyword(target, TemporaryKeyword.HEXPROOF)
                )
            )
            before = target.counters.get("stun", 0) if legal else None
            tapped_before = target.tapped if legal else None
            placement_cursor = None
            if legal:
                target.tapped = True
                self._record_stun_event(
                    "stun_target_tapped",
                    target_id=target.object_id,
                    source_id=ability.source_id,
                    stack_object_id=ability.object_id,
                    tapped_before=tapped_before,
                    tapped_after=True,
                )
                placement_cursor = len(self.events)
                self.place_counters(
                    target,
                    "stun",
                    1,
                    source_card=ability.source_card.name,
                    oracle_fragment=ability.oracle_fragment,
                    source_id=ability.source_id,
                    stack_object_id=ability.object_id,
                )
                # Counter replacement opportunity records may precede placement.
                placement_cursor = next(
                    index
                    for index in range(placement_cursor, len(self.events))
                    if self.events[index]["event"] == "counters_placed"
                )
            self._record_stun_event(
                "stun_etb_resolved",
                stack_object_id=ability.object_id,
                trigger_id=ability.trigger_id,
                event_id=ability.event.event_id,
                source_id=ability.source_id,
                target_id=selection.target_id,
                controller=ability.controller,
                oracle_fragment=ability.oracle_fragment,
                applied=bool(legal),
                tapped_before=tapped_before,
                tapped_after=True if legal else None,
                counters_before=before,
                counters_after=before + 1 if legal else None,
                placement_cursor=placement_cursor,
            )
        elif ability.effect is TriggerEffect.PARAMECIA_EXILE_CHOICE:
            departure = self._paramecia_departures.get(ability.source_id)
            if departure is None:
                raise ValueError("Paramecia departure is missing")
            _original, grave, _event, fragment = departure
            chosen = bool(self.paramecia_exile_chooser(ability.controller, ability.source_id))
            if (
                chosen
                and not self.is_terminal
                and self._objects.get(grave.object_id) is grave
                and self.is_authoritative(grave, "graveyard")
            ):
                exiled = self.move_object(grave, "exile", reason="paramecia_optional_exile")
                options = tuple(
                    card.object_id
                    for card in self.players[ability.controller].graveyard
                    if card.card.is_creature
                )
                target_id = self.paramecia_target_chooser(
                    ability.controller, ability.source_id, options
                )
                reflexive = TriggeredAbilityObject(
                    self._allocate_object_id(),
                    ability.controller,
                    ability.source_id,
                    ability.source_card,
                    fragment,
                    TriggerEffect.PARAMECIA_REFLEXIVE_RETURN,
                    ability.event,
                    ability.trigger_id,
                    target_id=target_id,
                )
                self._register(reflexive)
                self.stack.append(reflexive)
                self.log(
                    "paramecia_reflexive_trigger_created",
                    stack_object_id=reflexive.object_id,
                    source_id=ability.source_id,
                    event_id=ability.event.event_id,
                    exiled_object_id=exiled.object_id,
                    target_id=target_id,
                )
            else:
                self.log(
                    "paramecia_exile_declined" if not chosen else "paramecia_terminal_or_invalid",
                    source_id=ability.source_id,
                    event_id=ability.event.event_id,
                )
        elif ability.effect is TriggerEffect.PARAMECIA_REFLEXIVE_RETURN:
            target = self._objects.get(ability.target_id or "")
            legal = (
                isinstance(target, CardObject)
                and target.zone == "graveyard"
                and target.owner == ability.controller
                and target.card.is_creature
                and self.is_authoritative(target, "graveyard")
            )
            if legal:
                moved = self.move_object(
                    target, "library", library_position="top", reason="paramecia_reflexive_return"
                )
                self.log(
                    "paramecia_reflexive_return",
                    source_id=ability.source_id,
                    target_id=target.object_id,
                    destination_object_id=moved.object_id,
                    event_id=ability.event.event_id,
                )
            else:
                self.log(
                    "paramecia_target_invalidated",
                    source_id=ability.source_id,
                    target_id=ability.target_id,
                    event_id=ability.event.event_id,
                )
        elif ability.effect is TriggerEffect.LTB_MUTAGEN:
            self._resolve_ltb_mutagen(ability)
        elif ability.effect in {
            TriggerEffect.CREATE_TOKEN,
            TriggerEffect.CONDITIONAL_ENTRY_TOKEN,
        }:
            coverage = self.interpreter.token_semantic_coverage(
                ability.source_card, ability.oracle_fragment
            )
            if (
                coverage is None
                or not coverage.payload_executable
                or not coverage.parent_executable
            ):
                raise AssertionError("stacked token trigger no longer has executable semantics")
            if (
                self.interpreter.entry_leave_or_artifact_cast_token_context(
                    ability.source_card, ability.oracle_fragment
                )
                is not None
            ):
                trigger = self._triggers.get(ability.trigger_id)
                source = self._objects.get(ability.source_id)
                if (
                    not isinstance(source, Permanent)
                    or source.card is not ability.source_card
                    or trigger is None
                    or trigger.event is not ability.event
                    or trigger.source_id != ability.source_id
                    or trigger.source_card is not ability.source_card
                    or trigger.controller != ability.controller
                    or trigger.effect is not ability.effect
                    or trigger.oracle_fragment != ability.oracle_fragment
                    or source.zone not in {"battlefield", "former"}
                ):
                    raise ValueError("artifact token trigger was relinked")
                self._validate_artifact_token_trigger(
                    ability.event, source, ability.oracle_fragment, ability.controller
                )
            conditional = ability.effect is TriggerEffect.CONDITIONAL_ENTRY_TOKEN
            if conditional:
                self._authenticate_original_rules_event(ability.event)
                trigger = self._triggers.get(ability.trigger_id)
                if (
                    ability.event.kind is not RulesEventKind.CREATURE_ENTERED
                    or ability.event.subject_ids != (ability.source_id,)
                    or (ability.source_id, ability.controller)
                    not in ability.event.battlefield_authority
                    or trigger is None
                    or trigger.event is not ability.event
                    or trigger.source_id != ability.source_id
                    or trigger.effect is not ability.effect
                ):
                    raise ValueError("conditional entry trigger provenance is invalid")
            if not conditional or self._left_under_control_this_turn(ability.controller):
                x_entry = self.interpreter.x_entry_token_program(
                    ability.source_card, ability.oracle_fragment
                )
                program = coverage.program
                if x_entry is not None:
                    self._authenticate_original_rules_event(ability.event)
                    trigger = self._triggers.get(ability.trigger_id)
                    source = self._objects.get(ability.source_id)
                    if (
                        trigger is None
                        or trigger.event is not ability.event
                        or trigger.source_id != ability.source_id
                        or trigger.controller != ability.controller
                        or ability.event.kind is not RulesEventKind.CREATURE_ENTERED
                        or ability.event.subject_ids != (ability.source_id,)
                        or not isinstance(source, Permanent)
                        or source.card is not ability.source_card
                        or source.zone not in {"battlefield", "former"}
                        or source.x_value is None
                        or source.x_value < 0
                    ):
                        raise ValueError("variable X entry trigger lost source provenance")
                    program = replace(x_entry, quantity=source.x_value)
                    self.log(
                        "variable_x_entry_resolved",
                        source_id=ability.source_id,
                        stack_object_id=ability.object_id,
                        event_id=ability.event.event_id,
                        controller=ability.controller,
                        x_value=source.x_value,
                    )
                if program.quantity:
                    self.create_tokens(
                        ability.controller,
                        program,
                        source_card=ability.source_card.name,
                        oracle_fragment=ability.oracle_fragment,
                        source_id=ability.source_id,
                    )
            else:
                self.log("conditional_entry_trigger_condition_false", source_id=ability.source_id)
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
        elif ability.effect is TriggerEffect.ETB_ANY_TARGET_DAMAGE:
            program = self.interpreter.entry_any_target_damage_program(
                ability.source_card, ability.oracle_fragment
            )
            assert program is not None
            target_id = ability.target_id
            player_target = target_id in {"player:0", "player:1"}
            target = self._objects.get(target_id or "")
            legal = player_target or (
                isinstance(target, Permanent)
                and self._legal_damage_target(target, ability.controller)
            )
            if legal:
                source = self._objects[ability.source_id]
                assert isinstance(source, Permanent)
                self.deal_damage(
                    DamageTransaction(
                        ability.controller,
                        source,
                        DamageTargetKind.PLAYER if player_target else DamageTargetKind.CREATURE,
                        program.target_damage,
                        ability.oracle_fragment,
                        target=None if player_target else target,
                        target_player=int(target_id[-1]) if player_target else None,
                        source_event=ability.event,
                    ),
                    defer_post_damage=True,
                )
                self.deal_damage(
                    DamageTransaction(
                        ability.controller,
                        source,
                        DamageTargetKind.PLAYER,
                        program.self_damage,
                        ability.oracle_fragment,
                        target_player=ability.controller,
                        source_event=ability.event,
                    ),
                    defer_post_damage=True,
                )
                self.check_state_based_actions()
            self.log(
                "entry_damage_resolved",
                stack_object_id=ability.object_id,
                event_id=ability.event.event_id,
                source_id=ability.source_id,
                target_id=target_id,
                target_damage=program.target_damage if legal else 0,
                self_damage=program.self_damage if legal else 0,
                result="resolved" if legal else "all_targets_illegal",
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
            if self.is_terminal:
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
        elif ability.effect is TriggerEffect.ETB_SELF_LIFE_GAIN:
            amount = self._validate_etb_self_life_gain_trigger(ability)
            life_before = self.players[ability.controller].life
            event = self.gain_life(
                ability.controller,
                amount,
                source_card=ability.source_card.name,
                oracle_fragment=ability.oracle_fragment,
                defer_trigger_delivery=True,
            )
            self.log(
                "etb_life_gain_resolved",
                event_id=ability.event.event_id,
                life_gain_event_id=event.event_id,
                stack_object_id=ability.object_id,
                source_id=ability.source_id,
                source_card=ability.source_card.name,
                controller=self.players[ability.controller].name,
                amount=amount,
                life_before=life_before,
                life_after=self.players[ability.controller].life,
                oracle_fragment=ability.oracle_fragment,
            )
        elif ability.effect is TriggerEffect.CONTROLLED_CREATURE_LEFT_OPPONENT_LOSS:
            amount = self._validate_controlled_creature_departure_loss(
                controller=ability.controller,
                source_id=ability.source_id,
                source_card=ability.source_card,
                oracle_fragment=ability.oracle_fragment,
                event=ability.event,
                trigger_id=ability.trigger_id,
            )
            for opponent in range(len(self.players)):
                if opponent == ability.controller:
                    continue
                before = self.players[opponent].life
                self.players[opponent].life -= amount
                self.log(
                    "controlled_creature_departure_life_loss",
                    source_id=ability.source_id,
                    departed_id=ability.event.source_id,
                    event_id=ability.event.event_id,
                    stack_object_id=ability.object_id,
                    controller=ability.controller,
                    opponent=opponent,
                    amount=amount,
                    life_before=before,
                    life_after=self.players[opponent].life,
                )
            self.check_life()
        elif ability.effect is TriggerEffect.CLASS_SPELL_CAST_TEAM_COUNTER:
            recipients = tuple(
                permanent
                for permanent in self.players[ability.controller].battlefield
                if permanent.is_creature and self.is_authoritative(permanent, "battlefield")
            )
            for permanent in recipients:
                self.place_counters(
                    permanent,
                    "+1/+1",
                    1,
                    source_card=ability.source_card.name,
                    oracle_fragment=ability.oracle_fragment,
                )
            self.log(
                "class_spell_cast_team_counters_resolved",
                event_id=ability.event.event_id,
                stack_object_id=ability.object_id,
                source_id=ability.source_id,
                spell_id=ability.event.source_id,
                controller=ability.controller,
                recipient_ids=[permanent.object_id for permanent in recipients],
            )
        elif ability.effect is TriggerEffect.CONTROLLED_COUNTERED_CREATURE_LEFT_LIFE:
            amount = self._validate_countered_creature_departure_life(
                ability.event,
                ability.source_id,
                ability.source_card,
                ability.oracle_fragment,
                ability.controller,
                trigger_id=ability.trigger_id,
            )
            before = self.players[ability.controller].life
            life_event = self.gain_life(
                ability.controller,
                amount,
                source_card=ability.source_card.name,
                oracle_fragment=ability.oracle_fragment,
                defer_trigger_delivery=True,
            )
            self.log(
                "countered_creature_departure_life_resolved",
                event_id=ability.event.event_id,
                life_gain_event_id=life_event.event_id,
                stack_object_id=ability.object_id,
                source_id=ability.source_id,
                departed_id=ability.event.source_id,
                controller=ability.controller,
                amount=amount,
                life_before=before,
                life_after=self.players[ability.controller].life,
            )
        elif ability.effect is TriggerEffect.CONTROLLED_ARTIFACT_COUNTER_TRANSFER:
            counters = self._validate_artifact_counter_transfer(
                ability.event,
                ability.source_id,
                ability.source_card,
                ability.oracle_fragment,
                ability.controller,
                trigger_id=ability.trigger_id,
            )
            target, _offered = self._artifact_counter_targets[ability.object_id]
            legal = (
                isinstance(target, Permanent)
                and self._objects.get(target.object_id) is target
                and self.is_authoritative(target, "battlefield")
                and target.controller == ability.controller
                and bool(
                    {"Artifact", "Creature"} & set(target.type_line.split(" â€” ", 1)[0].split())
                )
                and self._legal_targeting_protection(target, ability.controller)
            )
            if legal:
                for kind, count in counters:
                    self.place_counters(
                        target,
                        kind,
                        count,
                        source_card=ability.source_card.name,
                        oracle_fragment=ability.oracle_fragment,
                        source_id=ability.source_id,
                        stack_object_id=ability.object_id,
                        defer_post_placement=True,
                    )
            self.log(
                "artifact_counter_transfer_resolved",
                event_id=ability.event.event_id,
                stack_object_id=ability.object_id,
                source_id=ability.source_id,
                departed_id=ability.event.source_id,
                controller=ability.controller,
                target_id=target.object_id if target is not None else None,
                target_legal=bool(legal),
                counter_snapshot=[list(item) for item in counters],
            )
        elif ability.effect is TriggerEffect.DAMAGE_TO_SELF_MANA:
            color, quantity = self._validate_damage_to_self_mana(
                ability.event,
                ability.source_id,
                ability.source_card,
                ability.oracle_fragment,
                ability.controller,
                trigger_id=ability.trigger_id,
            )
            self.floating_mana.add(
                ability.controller,
                ability.source_id,
                color,
                quantity,
                ability.object_id,
                persists_until_turn_end=True,
            )
            self.log(
                "damage_to_self_mana_resolved",
                event_id=ability.event.event_id,
                stack_object_id=ability.object_id,
                source_id=ability.source_id,
                controller=ability.controller,
                color=color,
                quantity=quantity,
                persists_until_turn_end=True,
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
        elif ability.effect is TriggerEffect.ETB_KRANG_REFILL:
            self._resolve_krang_refill(ability)
        elif ability.effect is TriggerEffect.ETB_MILL_THREE:
            self._resolve_mill_three(ability)
        elif ability.effect is TriggerEffect.ETB_JURY_RIG:
            self._resolve_jury_rig(ability)
        elif ability.effect in {TriggerEffect.ETB_VIGILANTE, TriggerEffect.VIGILANTE_DISCARD}:
            self._resolve_vigilante(ability)
        elif ability.effect is TriggerEffect.ETB_FOOD_SEARCH:
            self._resolve_etb_food_search(ability)
        elif ability.effect is TriggerEffect.ETB_DRAW_DISCARD:
            self._resolve_etb_draw_discard(ability)
        elif ability.effect is TriggerEffect.COMBAT_DAMAGE_DRAW_DISCARD:
            self._resolve_combat_draw_discard(ability)
        elif ability.effect is TriggerEffect.COMBAT_DAMAGE_DRAW_LOSE_LIFE:
            semantics = self.interpreter.combat_damage_draw_lose_life(
                ability.source_card, ability.oracle_fragment
            )
            assert semantics is not None
            draw_count, life_loss = semantics
            player = self.players[ability.controller]
            library_before = len(player.library)
            life_before = player.life
            self.draw(player, draw_count)
            player.life -= life_loss
            self.log(
                "life_lost",
                player=player.name,
                amount=life_loss,
                source=ability.source_card.name,
                source_id=ability.source_id,
                stack_object_id=ability.object_id,
                oracle_fragment=ability.oracle_fragment,
            )
            self.log(
                "combat_draw_life_resolved",
                event_id=ability.event.event_id,
                trigger_id=ability.trigger_id,
                stack_object_id=ability.object_id,
                source_id=ability.source_id,
                controller=ability.controller,
                damage=ability.event.amount,
                draw_count=draw_count,
                drawn_count=min(library_before, draw_count),
                failed_draw_pending=player.failed_draw_pending,
                life_before=life_before,
                life_after=player.life,
                life_lost=life_loss,
            )
        elif ability.effect is TriggerEffect.COMBAT_DAMAGE_ARTIFACT_COPY:
            target = self._objects.get(ability.target_id or "")
            legal = (
                isinstance(target, Permanent)
                and self.is_authoritative(target, "battlefield")
                and target.controller == ability.controller
                and "Artifact" in target.type_line.split(" â€” ", 1)[0].split()
            )
            token = None
            if legal:
                token = self.create_copy_token(
                    target,
                    ability.controller,
                    source_card=ability.source_card.name,
                    oracle_fragment=ability.oracle_fragment,
                    source_id=target.object_id,
                    stack_object_id=ability.object_id,
                )
            self.log(
                "combat_artifact_copy_resolved",
                event_id=ability.event.event_id,
                trigger_id=ability.trigger_id,
                stack_object_id=ability.object_id,
                source_id=ability.source_id,
                target_id=ability.target_id,
                controller=ability.controller,
                legal_target=legal,
                token_id=None if token is None else token.object_id,
            )
        elif ability.effect is TriggerEffect.COMBAT_DAMAGE_HAND_BATTLEFIELD:
            self._validate_combat_hand_battlefield_trigger(ability)
            choice = self.choose_hand_battlefield_entry(ability.controller)
            self.log(
                "combat_hand_battlefield_entry_choice",
                event_id=ability.event.event_id,
                trigger_id=ability.trigger_id,
                stack_object_id=ability.object_id,
                source_id=ability.source_id,
                controller=ability.controller,
                creature_id=choice.creature_id,
                land_id=choice.land_id,
                oracle_fragment=ability.oracle_fragment,
            )
            entered = self.commit_hand_battlefield_entry(
                ability.controller,
                choice,
                source_id=ability.source_id,
                oracle_fragment=ability.oracle_fragment,
            )
            self.log(
                "combat_hand_battlefield_entry_resolved",
                event_id=ability.event.event_id,
                trigger_id=ability.trigger_id,
                stack_object_id=ability.object_id,
                source_id=ability.source_id,
                controller=ability.controller,
                creature_id=choice.creature_id,
                land_id=choice.land_id,
                entered_ids=[item.object_id for item in entered],
                oracle_fragment=ability.oracle_fragment,
            )
        elif ability.effect is TriggerEffect.COMBAT_DAMAGE_GRAVEYARD_ATTACKER:
            target = self._objects.get(ability.target_id or "")
            valid = isinstance(target, CardObject) and self.is_authoritative(target, "graveyard")
            entering = None
            if valid:
                assert isinstance(target, CardObject)
                entering = self.move_object(
                    target,
                    "battlefield",
                    controller=ability.controller,
                    reason="combat_graveyard_return",
                )
                assert isinstance(entering, Permanent)
                entering.tapped = True
                self._combat_attackers += (entering.object_id,)
                self._process_creature_entered_triggers(entering, defer_triggers=True)
                self.check_state_based_actions()
            self.log(
                "combat_graveyard_attacker_resolved",
                event_id=ability.event.event_id,
                trigger_id=ability.trigger_id,
                stack_object_id=ability.object_id,
                source_id=ability.source_id,
                target_id=ability.target_id,
                permanent_id=entering.object_id if entering is not None else None,
                defending_player=ability.event.target_player,
                legal_target=valid,
                attacking=entering is not None,
            )
        elif ability.effect is TriggerEffect.UTILITY_TARGET:
            self._resolve_utility_trigger(ability)
        elif ability.effect is TriggerEffect.ETB_MILL_DRAW_DISCARD:
            self._resolve_etb_mill_draw_discard(ability)
        elif ability.effect is TriggerEffect.CLASS_LEVEL_TWO_RECOVERY:
            selected = self._class_recovery_targets.get(ability.object_id, ((), ()))[0]
            recovered = []
            for object_id in selected:
                card = self._objects.get(object_id)
                if (
                    isinstance(card, CardObject)
                    and self.is_authoritative(card, "graveyard")
                    and card.owner == ability.controller
                    and card.card.type_line.startswith("Artifact")
                ):
                    moved = self.move_object(card, "hand", reason="class_level_artifact_recovery")
                    recovered.append(moved.object_id)
            self.log(
                "class_level_artifact_recovery_resolved",
                stack_object_id=ability.object_id,
                trigger_id=ability.trigger_id,
                source_id=ability.source_id,
                controller=ability.controller,
                selected_ids=list(selected),
                recovered_ids=recovered,
                oracle_fragment=ability.oracle_fragment,
            )
        elif ability.effect is TriggerEffect.CLASS_COMBAT_ARTIFACT_ANIMATION:
            self._authenticate_original_rules_event(ability.event)
            program = self.interpreter.class_combat_artifact_animation(
                ability.source_card, ability.oracle_fragment
            )
            if (
                program is None
                or ability.event.kind is not RulesEventKind.BEGINNING_OF_COMBAT
                or ability.event.player_index != ability.controller
                or (ability.source_id, ability.controller)
                not in ability.event.battlefield_authority
            ):
                raise ValueError("Class combat resolution lacks original event provenance")
            target = self._objects.get(ability.target_id)
            if (
                not isinstance(target, Permanent)
                or not self.is_authoritative(target, "battlefield")
                or target.controller != ability.controller
                or "Artifact" not in target.type_line.split(" â€” ", 1)[0].split()
                or not self._legal_targeting_protection(target, ability.controller)
            ):
                self.log(
                    "class_combat_target_invalid",
                    stack_object_id=ability.object_id,
                    target_id=ability.target_id,
                )
            else:
                was_creature = target.is_creature
                self.place_counters(
                    target,
                    "+1/+1",
                    program.counter_quantity,
                    source_card=ability.source_card.name,
                    oracle_fragment=ability.oracle_fragment,
                    source_id=ability.source_id,
                    stack_object_id=ability.object_id,
                    defer_post_placement=True,
                )
                if not was_creature:
                    self.apply_temporary_type_and_base_pt(
                        target,
                        added_types=("Creature",),
                        added_subtypes=(program.creature_subtype,),
                        power=program.base_power,
                        toughness=program.base_toughness,
                        source_id=ability.object_id,
                        source_card=ability.source_card.name,
                        oracle_fragment=ability.oracle_fragment,
                        duration="persistent",
                    )
                    self.refresh_static_pt_modifiers()
                self.log(
                    "class_combat_artifact_resolved",
                    event_id=ability.event.event_id,
                    stack_object_id=ability.object_id,
                    source_id=ability.source_id,
                    target_id=target.object_id,
                    counter_quantity=program.counter_quantity,
                    animated=not was_creature,
                    resulting_type_line=target.type_line,
                    resulting_power=target.power,
                    resulting_toughness=target.toughness,
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
        elif ability.effect is TriggerEffect.CLASS_DISCARD_DAMAGE:
            match = self.interpreter.CLASS_DISCARD_DAMAGE.fullmatch(ability.oracle_fragment)
            assert match is not None
            self._authenticate_original_rules_event(ability.event)
            if ability.event.kind is not RulesEventKind.CARD_DISCARDED:
                raise ValueError("Class damage requires a discarded-card event")
            amount = int(match["amount"])
            source = self._objects.get(ability.source_id)
            if not isinstance(source, Permanent):
                raise ValueError("Class damage source has no permanent incarnation")
            for opponent in range(2):
                if opponent != ability.controller:
                    self.deal_damage(
                        DamageTransaction(
                            ability.controller,
                            source,
                            DamageTargetKind.PLAYER,
                            amount,
                            ability.oracle_fragment,
                            target_player=opponent,
                            source_event=ability.event,
                        )
                    )
            self.log(
                "class_discard_damage_resolved",
                trigger_id=ability.trigger_id,
                source_id=ability.source_id,
                amount=amount,
                discarded_id=ability.event.subject_ids[0],
            )
        elif ability.effect is TriggerEffect.CLASS_LEVEL_THREE_SEARCH:
            if self.interpreter.CLASS_LEVEL_THREE_SEARCH.fullmatch(ability.oracle_fragment) is None:
                raise AssertionError("Class search semantics changed while stacked")
            player = self.players[ability.controller]
            selected = max(
                player.library, key=lambda card: (card.mana_value, card.name), default=None
            )
            if selected is not None:
                fetched = self.move_object(selected, "hand", reason="class_search")
                self.log(
                    "class_card_searched",
                    source_id=ability.source_id,
                    searched_id=selected.object_id,
                    hand_id=fetched.object_id,
                )
            player.library[:] = self.rng.shuffled(
                player.library, domain=f"class_search:{ability.object_id}"
            )
            self.log(
                "class_library_shuffled",
                source_id=ability.source_id,
                stack_object_id=ability.object_id,
            )
            if player.hand:
                discard = player.hand[
                    self.rng.randrange(
                        len(player.hand), domain=f"class_random_discard:{ability.object_id}"
                    )
                ]
                moved = self.move_object(discard, "graveyard", reason="class_random_discard")
                self.log(
                    "class_random_card_discarded",
                    source_id=ability.source_id,
                    hand_id=discard.object_id,
                    graveyard_id=moved.object_id,
                )
        elif ability.effect is TriggerEffect.DIES_DRAW:
            coverage = self.interpreter.dies_draw_semantic_coverage(
                ability.source_card, ability.oracle_fragment
            )
            if coverage is None or not coverage.fully_supported:
                raise AssertionError("stacked dies/Draw trigger is no longer executable")
            self._validate_dies_draw_trigger(ability)
            self.draw(self.players[ability.controller], 1)
        elif ability.effect is TriggerEffect.GRANTED_DIES_RETURN:
            source = self._objects.get(ability.source_id)
            if not isinstance(source, Permanent):
                raise ValueError("granted death trigger source is invalid")
            destination = self._validate_granted_death_return(
                ability.event,
                source,
                ability.oracle_fragment,
                ability.controller,
                trigger_id=ability.trigger_id,
            )
            if self.is_authoritative(destination, "graveyard"):
                entering = self.move_object(
                    destination,
                    "battlefield",
                    controller=destination.owner,
                    reason="granted_death_return",
                )
                assert isinstance(entering, Permanent)
                entering.tapped = True
                self.log(
                    "granted_death_return_resolved",
                    stack_object_id=ability.object_id,
                    death_event_id=ability.event.event_id,
                    departed_id=source.object_id,
                    graveyard_id=destination.object_id,
                    entering_id=entering.object_id,
                    owner=entering.owner,
                    controller=entering.controller,
                )
                self._process_creature_entered_triggers(entering, defer_triggers=True)
                self.check_state_based_actions()
            else:
                self.log(
                    "granted_death_return_no_effect",
                    stack_object_id=ability.object_id,
                    death_event_id=ability.event.event_id,
                    departed_id=source.object_id,
                    graveyard_id=destination.object_id,
                )
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
                    if permanent.is_creature:
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
        elif ability.effect is TriggerEffect.ALLIANCE_TEMPORARY_KEYWORD_CHOICE:
            semantics = self.interpreter.temporary_keyword_choice_semantic_coverage(
                ability.source_card, ability.oracle_fragment
            )
            if semantics is None or not semantics.coverage.fully_supported:
                raise AssertionError("stacked temporary-keyword choice is no longer executable")
            self._validate_alliance_temporary_keyword_choice_trigger(ability)
            choices = semantics.program.choices
            selected = self.temporary_keyword_chooser(
                ability.controller, ability.source_id, choices
            )
            if selected not in choices:
                raise ValueError("temporary keyword chooser must return an available keyword")
            applied = source_permanent is not None
            if source_permanent is not None:
                source_permanent.temporary_keyword_effects.append(
                    TemporaryKeywordEffect(
                        TemporaryKeyword(selected),
                        "until_end_of_turn",
                        ability.source_id,
                        ability.oracle_fragment,
                        timestamp=self._effect_timestamp(),
                    )
                )
            self.log(
                "temporary_keyword_choice_resolved",
                stack_object_id=ability.object_id,
                trigger_id=ability.trigger_id,
                event_id=ability.event.event_id,
                source_id=ability.source_id,
                target_id=ability.source_id,
                controller=ability.controller,
                choices=list(choices),
                selected_keyword=selected,
                duration="until_end_of_turn",
                oracle_fragment=ability.oracle_fragment,
                applied=applied,
            )
        elif ability.effect is TriggerEffect.ARTIFACT_ENTRY_SELF_COUNTER:
            if source_permanent is not None:
                self.place_counters(
                    source_permanent,
                    "+1/+1",
                    1,
                    source_card=ability.source_card.name,
                    oracle_fragment=ability.oracle_fragment,
                )
                self.log(
                    "artifact_entry_counter_resolved",
                    stack_object_id=ability.object_id,
                    trigger_id=ability.trigger_id,
                    event_id=ability.event.event_id,
                    source_id=ability.source_id,
                    entered_id=ability.event.subject_ids[0],
                    quantity=1,
                    counter_type="+1/+1",
                )
            else:
                self.log(
                    "artifact_entry_counter_source_absent",
                    stack_object_id=ability.object_id,
                    trigger_id=ability.trigger_id,
                    event_id=ability.event.event_id,
                    source_id=ability.source_id,
                    entered_id=ability.event.subject_ids[0],
                )
        elif ability.effect is TriggerEffect.RAPHAEL_ALLIANCE_EXILE:
            if not self.raphael_exile_chooser(ability.controller, ability.source_id):
                self.log("raphael_alliance_exile_declined", source_id=ability.source_id)
            elif self.players[ability.controller].library:
                top = self.players[ability.controller].library[-1]
                moved = self.move_object(top, "exile", reason="raphael_alliance_exile")
                self._raphael_linked_exile.setdefault(ability.source_id, []).append(
                    (moved.object_id, moved.card, ability.source_id)
                )
                self.log(
                    "raphael_linked_exile",
                    source_id=ability.source_id,
                    exiled_object_id=moved.object_id,
                    card=moved.card.name,
                    event_id=ability.event.event_id,
                )
            else:
                self.log("raphael_alliance_exile_empty", source_id=ability.source_id)
        elif ability.effect is TriggerEffect.RAPHAEL_ATTACK_PLAY:
            grant = LinkedPlayGrant(
                ability.object_id, ability.source_id, ability.controller, self.turn
            )
            self._linked_play_grants.setdefault(ability.source_id, []).append(grant)
            self.log(
                "raphael_play_permission_created",
                source_id=ability.source_id,
                grant_id=grant.grant_id,
                controller=grant.controller,
                remaining_plays=grant.remaining_plays,
                expires_turn=self.turn,
                event_id=ability.event.event_id,
            )
        elif ability.effect is TriggerEffect.COMBAT_DISCARD_OR_SACRIFICE:
            discards = tuple(card.object_id for card in self.players[ability.controller].hand)
            sacrifices = tuple(
                permanent.object_id for permanent in self.players[ability.controller].battlefield
            )
            choice = self.discard_or_sacrifice_chooser(
                ability.controller, ability.source_id, discards, sacrifices
            )
            if choice[0] == "discard" and choice[1] in discards:
                selected = self._objects[choice[1]]
                self.move_object(selected, "graveyard", reason="combat_trigger_discard")
            elif choice[0] == "sacrifice" and choice[1] in sacrifices:
                selected = self._objects[choice[1]]
                self.move_object(selected, "graveyard", reason="combat_trigger_sacrifice")
            elif sacrifices and not discards:
                raise ValueError("mandatory sacrifice requires a legal permanent choice")
            elif discards or sacrifices:
                raise ValueError("combat trigger chooser returned an illegal choice")
            else:
                selected = None
            self.log(
                "combat_discard_or_sacrifice_resolved",
                event_id=ability.event.event_id,
                source_id=ability.source_id,
                choice=choice[0] if selected is not None else "none",
                chosen_id=selected.object_id if selected is not None else None,
            )
            self.check_state_based_actions()
        elif ability.effect is TriggerEffect.END_STEP_SPELL_TYPES_DRAW:
            types = sorted(
                {
                    card_type
                    for record in self.events
                    if record["event"] == "spell_cast"
                    and record["turn"] == ability.event.turn
                    and record["player_index"] == ability.controller
                    for card_type in record["card_types"]
                }
            )
            self.log(
                "end_step_spell_types_draw_resolved",
                event_id=ability.event.event_id,
                source_id=ability.source_id,
                card_types=types,
                count=len(types),
            )
            self.draw(self.players[ability.controller], len(types))
        elif ability.effect is TriggerEffect.DISAPPEAR_END_STEP:
            program = self.interpreter.disappear_end_step(
                ability.source_card, ability.oracle_fragment
            )
            if program is None:
                raise ValueError("incomplete conditional end-step effect")
            condition = self._left_under_control_this_turn(ability.controller)
            self.log(
                "disappear_end_step_condition_checked",
                event_id=ability.event.event_id,
                trigger_id=ability.trigger_id,
                source_id=ability.source_id,
                controller=ability.controller,
                satisfied=condition,
            )
            if condition and program[0] == "scry":
                self.scry(
                    ability.controller,
                    ScryProgram(program[1]),
                    source_card=ability.source_card.name,
                    oracle_fragment=ability.oracle_fragment,
                    source_id=ability.source_id,
                )
            elif condition and program[0] == "self_counter" and source_permanent is not None:
                self.place_counters(
                    source_permanent,
                    "+1/+1",
                    program[1],
                    source_card=ability.source_card.name,
                    oracle_fragment=ability.oracle_fragment,
                    source_id=ability.source_id,
                    stack_object_id=ability.object_id,
                )
        elif ability.effect is TriggerEffect.ALLIANCE_COUNTER and source_permanent is not None:
            match = self.interpreter.ALLIANCE_TARGET_PLUS_COUNTER.fullmatch(ability.oracle_fragment)
            assert match is not None
            candidates = tuple(
                permanent
                for permanent in self.players[ability.controller].battlefield
                if permanent.is_creature
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
            modes = tuple(fragment for fragment in fragments if fragment.startswith("â€¢ "))
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
        elif ability.effect is TriggerEffect.ATTACK_TARGET_COUNTER:
            target = self._objects.get(ability.target_id or "")
            valid = (
                isinstance(target, Permanent)
                and self.is_authoritative(target, "battlefield")
                and target.object_id in self._combat_attackers
                and target.controller == ability.controller
                and self._legal_targeting_protection(target, ability.controller)
            )
            if valid:
                self.place_counters(
                    target,
                    "+1/+1",
                    1,
                    source_card=ability.source_card.name,
                    oracle_fragment=ability.oracle_fragment,
                )
            self.log(
                "attack_counter_resolved",
                event_id=ability.event.event_id,
                stack_object_id=ability.object_id,
                source_id=ability.source_id,
                target_id=ability.target_id,
                applied=valid,
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
        record_resolution = (
            self._record_stun_event if ability.effect is TriggerEffect.ETB_TAP_STUN else self.log
        )
        record_resolution(
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
            if (
                self.stack[-1].effect is TriggerEffect.CREATE_TOKEN
                and self.interpreter.entry_leave_or_artifact_cast_token_context(
                    self.stack[-1].source_card, self.stack[-1].oracle_fragment
                )
                is not None
            ) or self.stack[-1].effect in {
                TriggerEffect.LTB_MUTAGEN,
                TriggerEffect.ATTACK_TARGET_COUNTER,
                TriggerEffect.PARAMECIA_EXILE_CHOICE,
                TriggerEffect.PARAMECIA_REFLEXIVE_RETURN,
                TriggerEffect.RAPHAEL_ALLIANCE_EXILE,
                TriggerEffect.RAPHAEL_ATTACK_PLAY,
                TriggerEffect.COMBAT_DISCARD_OR_SACRIFICE,
                TriggerEffect.END_STEP_SPELL_TYPES_DRAW,
                TriggerEffect.DISAPPEAR_END_STEP,
                TriggerEffect.ETB_VIGILANTE,
                TriggerEffect.VIGILANTE_DISCARD,
                TriggerEffect.ETB_KRANG_REFILL,
                TriggerEffect.ETB_MILL_THREE,
                TriggerEffect.ETB_JURY_RIG,
                TriggerEffect.ETB_FOOD_SEARCH,
                TriggerEffect.ETB_DRAW_DISCARD,
                TriggerEffect.COMBAT_DAMAGE_DRAW_DISCARD,
                TriggerEffect.COMBAT_DAMAGE_DRAW_LOSE_LIFE,
                TriggerEffect.COMBAT_DAMAGE_GRAVEYARD_ATTACKER,
                TriggerEffect.COMBAT_DAMAGE_ARTIFACT_COPY,
                TriggerEffect.COMBAT_DAMAGE_HAND_BATTLEFIELD,
                TriggerEffect.UTILITY_TARGET,
                TriggerEffect.ETB_MILL_DRAW_DISCARD,
                TriggerEffect.CLASS_LEVEL_TWO_RECOVERY,
                TriggerEffect.CLASS_COMBAT_ARTIFACT_ANIMATION,
                TriggerEffect.DISCARD_DRAW,
                TriggerEffect.DIES_DRAW,
                TriggerEffect.GRANTED_DIES_RETURN,
                TriggerEffect.ETB_DRAIN_GAIN_SCRY,
                TriggerEffect.ETB_SELF_LIFE_GAIN,
                TriggerEffect.CONDITIONAL_ENTRY_TOKEN,
                TriggerEffect.PERMANENT_LEFT_SELF_COUNTER,
                TriggerEffect.CONTROLLED_CREATURE_LEFT_OPPONENT_LOSS,
                TriggerEffect.CONTROLLED_COUNTERED_CREATURE_LEFT_LIFE,
                TriggerEffect.CONTROLLED_ARTIFACT_COUNTER_TRANSFER,
                TriggerEffect.DAMAGE_TO_SELF_MANA,
                TriggerEffect.CLASS_SPELL_CAST_TEAM_COUNTER,
                TriggerEffect.ETB_ARTIFACT_DRAW,
                TriggerEffect.ETB_TAP_STUN,
                TriggerEffect.ETB_ANY_TARGET_DAMAGE,
                TriggerEffect.ETB_ATTACH_EQUIPMENT,
                TriggerEffect.GRANTED_COMBAT_UNTAP_GAIN,
                TriggerEffect.EQUIPMENT_SUBTYPE_ENTRY_ATTACH,
                TriggerEffect.ROCK_SOLDIERS_ETB_DESTROY,
                TriggerEffect.ETB_DESTROY_TARGET_CREATURE,
                TriggerEffect.ETB_TARGET_CREATURE_PUMP_UNTAP,
                TriggerEffect.SHREDDER_DEATHTOUCH,
                TriggerEffect.ALLIANCE_TEMPORARY_KEYWORD_CHOICE,
            }:
                self._begin_priority_window()
                return
            self._resolve_triggered_ability(self.stack[-1])

    def _validate_ltb_mutagen_departure(
        self, source: Permanent, fragment: str, event: RulesEvent, controller: int
    ) -> None:
        key = (source.object_id, event.event_id, fragment)
        anchor = self._ltb_mutagen_departures.get(key)
        self._authenticate_original_rules_event(event)
        if anchor is None:
            raise ValueError("LTB Mutagen lacks original departure provenance")
        original, card, original_event, replacement, departure = anchor
        records = [
            item
            for item in self.events
            if item.get("event") == "zone_changed"
            and item.get("source_object_id") == source.object_id
        ]
        if (
            source is not original
            or self._objects.get(source.object_id) is not source
            or source.card is not card
            or source.zone != "former"
            or source.controller != controller
            or self._objects.get(replacement.object_id) is not replacement
            or replacement.card is not card
            or event is not original_event
            or self._rules_events.get(event.event_id) is not event
            or event.kind is not RulesEventKind.PERMANENT_LEFT
            or event.source_id != source.object_id
            or event.subject_ids != (source.object_id,)
            or event.player_index != controller
            or (source.object_id, controller) not in event.battlefield_authority
            or (source.object_id, controller, source.type_line, True)
            not in event.last_known_battlefield
            or len(records) != 1
            or tuple(records[0].items()) != departure
            or records[0]["source_zone"] != "battlefield"
            or records[0]["destination_zone"] == "battlefield"
            or records[0]["destination_object_id"] != replacement.object_id
            or fragment not in self.interpreter.fragments(card)
            or self.interpreter.ltb_mutagen_semantic_coverage(card, fragment) is None
        ):
            raise ValueError("LTB Mutagen departure provenance is stale or relinked")

    def _validate_ltb_mutagen_trigger(self, ability: TriggeredAbilityObject) -> None:
        if not self._priority_resolution_in_progress and (
            self.priority_state is None or not self.priority_state.resolution_pending
        ):
            raise ValueError("LTB Mutagen requires Priority resolution")
        anchor = self._ltb_mutagen_anchors.get(ability.object_id)
        if anchor is None:
            raise ValueError("LTB Mutagen lacks original Stack provenance")
        original, trigger = anchor
        source = self._objects.get(trigger.source_id)
        if (
            ability is not original
            or self._objects.get(ability.object_id) is not ability
            or self._triggers.get(ability.trigger_id) is not trigger
            or ability.event is not trigger.event
            or ability.controller != trigger.controller
            or ability.source_id != trigger.source_id
            or ability.source_card is not trigger.source_card
            or ability.oracle_fragment != trigger.oracle_fragment
            or ability.effect is not TriggerEffect.LTB_MUTAGEN
            or ability.trigger_id in self._ltb_mutagen_consumed
            or not isinstance(source, Permanent)
        ):
            raise ValueError("LTB Mutagen trigger provenance is stale, relinked or consumed")
        self._validate_ltb_mutagen_departure(
            source, ability.oracle_fragment, ability.event, ability.controller
        )

    def _resolve_ltb_mutagen(self, ability: TriggeredAbilityObject) -> None:
        self._validate_ltb_mutagen_trigger(ability)
        if ability.zone != "former":
            raise ValueError("LTB Mutagen requires its resolving Stack object")
        self._ltb_mutagen_consumed.add(ability.trigger_id)
        coverage = self.interpreter.ltb_mutagen_semantic_coverage(
            ability.source_card, ability.oracle_fragment
        )
        assert coverage is not None
        tokens = self.create_tokens(
            ability.controller,
            coverage.program,
            source_card=ability.source_card.name,
            source_id=ability.source_id,
            oracle_fragment=ability.oracle_fragment,
        )
        if len(tokens) != 1 or any(
            not self.is_authoritative(token, "battlefield")
            or not token.is_token
            or token.card is not coverage.program.definition
            or token.owner != ability.controller
            or token.controller != ability.controller
            for token in tokens
        ):
            raise ValueError("LTB Mutagen token creation is not authoritative")
        creation = [
            e
            for e in self.events
            if e.get("event") == "tokens_created" and e.get("object_ids") == [tokens[0].object_id]
        ]
        if len(creation) != 1:
            raise ValueError("LTB Mutagen lacks unique token creation evidence")
        self.log(
            "ltb_mutagen_resolved",
            event_id=ability.event.event_id,
            trigger_id=ability.trigger_id,
            stack_object_id=ability.object_id,
            source_id=ability.source_id,
            controller=ability.controller,
            oracle_fragment=ability.oracle_fragment,
            creation_event_id=creation[0]["event_id"],
            token_id=tokens[0].object_id,
            token_owner=tokens[0].owner,
            token_controller=tokens[0].controller,
            token_type_line=tokens[0].type_line,
            token_oracle_text=tokens[0].card.oracle_text,
            activation_supported=False,
        )

    @staticmethod
    def validate_ltb_mutagen_snapshot_evidence(snapshot: dict[str, object]) -> None:
        """Reconstruct only the bounded leave/Mutagen creation chain, not activation."""
        events = snapshot.get("events", [])
        deliveries = [
            (i, e) for i, e in enumerate(events) if e.get("event") == "ltb_mutagen_resolved"
        ]
        resolutions = [
            e
            for e in events
            if e.get("event") == "trigger_resolved" and e.get("effect") == "ltb_mutagen"
        ]
        if len(deliveries) != len(resolutions):
            raise ValueError("LTB Mutagen evidence lacks unique resolution")
        seen_leaves, seen_tokens = set(), set()
        definition = CardInterpreter.PREDEFINED_TOKENS["mutagen"]
        for delivery_cursor, item in deliveries:
            try:
                source, leave_id, token = item["source_id"], item["event_id"], item["token_id"]
                controller = item["controller"]
                assert controller in (0, 1)
                assert (source, leave_id) not in seen_leaves and token not in seen_tokens
                seen_leaves.add((source, leave_id))
                seen_tokens.add(token)
                assert item["oracle_fragment"] == CardInterpreter.LTB_MUTAGEN_FRAGMENT
                assert item["token_owner"] == item["token_controller"] == controller
                assert item["token_type_line"] == definition.type_line
                assert item["token_oracle_text"] == definition.oracle_text
                assert item["activation_supported"] is False

                def unique(kind, key, value):
                    matches = [
                        (i, e)
                        for i, e in enumerate(events)
                        if e.get("event") == kind and e.get(key) == value
                    ]
                    assert len(matches) == 1
                    return matches[0]

                departure_cursor, departure = unique("zone_changed", "source_object_id", source)
                leave_cursor, leave = unique("rules_event", "event_id", leave_id)
                pending_cursor, pending = unique(
                    "trigger_pending", "trigger_id", item["trigger_id"]
                )
                stack_cursor, stacked = unique(
                    "trigger_stacked", "stack_object_id", item["stack_object_id"]
                )
                permit_cursor, permit = unique(
                    "stack_resolution_permitted", "stack_object_id", item["stack_object_id"]
                )
                creation_cursor, creation = unique(
                    "rules_event", "event_id", item["creation_event_id"]
                )
                payload_cursor, payload = unique(
                    "tokens_created", "event_id", item["creation_event_id"]
                )
                resolved_cursor, resolved = unique(
                    "trigger_resolved", "stack_object_id", item["stack_object_id"]
                )
                assert (
                    departure_cursor
                    < leave_cursor
                    < pending_cursor
                    < stack_cursor
                    < permit_cursor
                    < creation_cursor
                    < payload_cursor
                    < delivery_cursor
                    < resolved_cursor
                )
                assert (
                    departure["source_zone"] == "battlefield"
                    and departure["destination_zone"] != "battlefield"
                )
                assert departure["destination_object_id"] != source
                assert leave["rules_event"] == "permanent_left"
                assert leave["source_id"] == source and leave["subject_ids"] == [source]
                assert {"object_id": source, "controller": controller} in leave[
                    "battlefield_authority"
                ]
                assert any(
                    x["object_id"] == source
                    and x["controller"] == controller
                    and x["is_creature"] is True
                    for x in leave["last_known_battlefield"]
                )
                assert (
                    pending["event_id"] == stacked["event_id"] == resolved["event_id"] == leave_id
                )
                assert stacked["trigger_id"] == resolved["trigger_id"] == item["trigger_id"]
                assert (
                    pending["oracle_fragment"]
                    == resolved["oracle_fragment"]
                    == item["oracle_fragment"]
                )
                assert resolved["source_id"] == source and resolved["effect"] == "ltb_mutagen"
                passes = [
                    e
                    for e in events[stack_cursor:permit_cursor]
                    if e.get("event") == "priority_passed"
                    and e.get("priority_epoch") == permit["priority_epoch"]
                ]
                assert len(passes) >= 2 and passes[-1]["resolution_pending"] is True
                assert {passes[-1]["player_index"], passes[-2]["player_index"]} == {0, 1}
                assert creation["rules_event"] == "tokens_created" and creation["subject_ids"] == [
                   ×Žz×¦òµë(š+my×G2À¢f7G3Ò€¢‚&Öæ÷&WV—&VB"Â7G"‡&WV—&VÖVçBçF÷FÂ’’À¢‚'6÷W&6U÷F÷&WV—&VB"Â7G"†æVVG5÷F’æÆ÷vW"‚’’À¢‚'6÷W&6U÷FVB"Â7G"‡6÷W&6RçFVB’æÆ÷vW"‚’’À¢‚'F–Ö–ær"Â6VÆbç7FWçfÇVR’À¢’À¢ ¢FVböw&fW–&Eö67E÷W&Ö—76–öâ‡6VÆbÂ6÷W&6S¢W&ÖæVçB’ÓâGWÆU¶–çBÂ7G%ÒÂæöæS ¢–bæ÷B6VÆbæ—5öWF†÷&—FF—fR‡6÷W&6RÂ&&GFÆVf–VÆB"“ ¢&WGW&âæöæP¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡6÷W&6Rç'VÆW5ö6&B“ ¢ÖF6‚Ò&RæÖF6‚€¢"%äGW&–ær–÷W"GW&âÂ–÷RÖ’67B7&VGW&R7VÆÇ2v—F‚÷vW"÷"F÷Vv†æW72 ¢""ƒõÆÆ–Ö—CåÆB²’÷"ÆW72g&öÒ–÷W"w&fW–&EÂâ"À¢g&vÖVçBÀ¢¢–bÖF6‚—2æ÷BæöæS ¢&WGW&â–çB†ÖF6‚æw&÷W‚&Æ–Ö—B"’’Âg&vÖVç@¢&WGW&âæöæP ¢7FF–6ÖWF†ö@¢FVböw&fW–&Eö6&E÷VÆ–f–W2†6&C¢6&Df7BÂÆ–Ö—C¢–çB’Óâ&ööÃ ¢&WGW&â€¢6&Bæ—5ö7&VGW&P¢æB6&Bç÷vW"—2æ÷BæöæP¢æB6&BçF÷Vv†æW72—2æ÷BæöæP¢æB†6&Bç÷vW"ÃÒÆ–Ö—B÷"6&BçF÷Vv†æW72ÃÒÆ–Ö—B¢ ¢FVb÷v—FæW75öw&fW–&Eö67E÷W&Ö—76–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâæöæS ¢""%v—FæW72öæÇ’W&Ö—76–öç2v†÷6R&W&W6VçFVBõBæBF–Ö–ær&VF–6FW2&RG'VRâ"" ¢GFW&âÒ&Ræ6ö×–ÆR€¢"%äGW&–ær–÷W"GW&âÂ–÷RÖ’67B7&VGW&R7VÆÇ2v—F‚÷vW"÷"F÷Vv†æW72 ¢""ƒõÆÆ–Ö—CåÆB²’÷"ÆW72g&öÒ–÷W"w&fW–&EÂâ ¢¢f÷"ö67W'&Væ6R–âGWÆR‡6VÆbç6VÖçF–5öö67W'&Væ6W2“ ¢6÷W&6RÒ6VÆbåöö&¦V7G2ævWB†ö67W'&Væ6Ræö&¦V7Eö–B¢ÖF6‚ÒGFW&âæÖF6‚†ö67W'&Væ6Ræ÷&6ÆUög&vÖVçB¢–b€¢ÖF6‚—2æöæP¢÷"æ÷B—6–ç7Fæ6R‡6÷W&6RÂW&ÖæVçB¢÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR‡6÷W&6RÂ&&GFÆVf–VÆB"¢÷"6÷W&6Ræ6öçG&öÆÆW"ÒÆ–W%ö–æFW€¢“ ¢6öçF–çVP¢Æ–Ö—BÒ–çB†ÖF6‚æw&÷W‚&Æ–Ö—B"’¢6æF–FFW2ÒGWÆR€¢6&Bæö&¦V7Eö–@¢f÷"6&B–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæw&fW–&@¢–b6&Bæ6&Bæ—5ö7&VGW&P¢æB6&Bæ6&Bç÷vW"—2æ÷BæöæP¢æB6&Bæ6&BçF÷Vv†æW72—2æ÷BæöæP¢æB†6&Bæ6&Bç÷vW"ÃÒÆ–Ö—B÷"6&Bæ6&BçF÷Vv†æW72ÃÒÆ–Ö—B¢¢–b6æF–FFW3 ¢6VÆbå÷&V6÷&Eö÷÷'GVæ—G’€¢ö67W'&Væ6RÀ¢6W6Uö¶–æCÒ&ÆVvÅö7F–öåö6öçFW‡B"À¢6W6Uö–CÒ€¢b&ÆVvÂÖÖ–ã§·6VÆbçGW&çÓ§·6VÆbç7FWçfÇVWÓ§·Æ–W%ö–æFW‡Ó¢ ¢²"Â"æ¦ö–â†6æF–FFW2¢’À¢6W6U÷7V&¦V7Eö–G3Ö6æF–FFW2À¢ ¢FVbö—5öÆVvÅö6÷VçFW%÷F&vWB‡6VÆbÂF&vWC¢ö&¦V7BÂ6öçG&öÆÆW#¢–çB’Óâ&ööÃ ¢–bæ÷B—6–ç7Fæ6R‡F&vWBÂ7F6´ö&¦V7B’÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ'7F6²"“ ¢&WGW&âfÇ6P¢–bF&vWBçF&vWEö–B—2æöæS ¢&WGW&âfÇ6P¢&÷FV7FVBÒ6VÆbåöö&¦V7G2ævWB‡F&vWBçF&vWEö–B¢&WGW&â€¢—6–ç7Fæ6R‡&÷FV7FVBÂW&ÖæVçB¢æB6VÆbæ—5öWF†÷&—FF—fR‡&÷FV7FVBÂ&&GFÆVf–VÆB"¢æB&÷FV7FVBæ6öçG&öÆÆW"ÓÒ6öçG&öÆÆW ¢æB&÷FV7FVBæ6&Bæ—5ö7&VGW&P¢÷"€¢—6–ç7Fæ6R‡&÷FV7FVBÂW&ÖæVçB¢æB6VÆbæ—5öWF†÷&—FF—fR‡&÷FV7FVBÂ&&GFÆVf–VÆB"¢æB&÷FV7FVBæ6öçG&öÆÆW"ÓÒ6öçG&öÆÆW ¢æB$'F–f7B"–â&÷FV7FVBçG—UöÆ–æP¢¢ ¢FVbö—5öÆVvÅöö÷¦U÷F&vWB‡6VÆbÂF&vWC¢ö&¦V7BÂ6öçG&öÆÆW#¢–çB’Óâ&ööÃ ¢&WGW&â€¢—6–ç7Fæ6R‡F&vWBÂ7F6´ö&¦V7B¢æB6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ'7F6²"¢æBF&vWBæ6öçG&öÆÆW"Ò6öçG&öÆÆW ¢ ¢FVbö—5öÆVvÅö†æEö6÷VçFW%÷F&vWB‡6VÆbÂ6&C¢6&Df7BÂF&vWC¢ö&¦V7B’Óâ&ööÃ ¢¶–æBÒ6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&B’æ¶–æ@¢&WGW&â€¢—6–ç7Fæ6R‡F&vWBÂ7F6´ö&¦V7B¢æB6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ'7F6²"¢æB€¢¶–æB—267D¶–æBäôõ¤Uõ5”ÄÀ¢÷"€¢¶–æB—267D¶–æBä4õTåDU%õD$tUEõ5TÄÀ¢æB‚&æöæ7&VGW&R"æ÷B–â6&Bæ÷&6ÆU÷FW‡B÷"æ÷BF&vWBæ6&Bæ—5ö7&VGW&R¢¢¢ ¢FVböÆVvÅö6÷VçFW%÷F&vWEö–G2‡6VÆbÂ6öçG&öÆÆW#¢–çB’ÓâGWÆU·7G"ÂââåÓ ¢&WGW&âGWÆR€¢7VÆÂæö&¦V7Eö–@¢f÷"7VÆÂ–â6VÆbç7F6°¢–b—6–ç7Fæ6R‡7VÆÂÂ7F6´ö&¦V7B¢æB7VÆÂæ6öçG&öÆÆW"Ò6öçG&öÆÆW ¢æB6VÆbåö—5öÆVvÅö6÷VçFW%÷F&vWB‡7VÆÂÂ6öçG&öÆÆW"¢ ¢FVbö†æE÷&W7öç6Uö÷F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢""$W‡÷6R–&ÆR†æB6÷VçFW'2v–ç7B÷÷6–ær7VÆÇ2ç—v†W&RöâF†R7F6²â"" ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b€¢7FFR—2æöæP¢÷"7FFRç&W6öÇWF–öå÷VæF–æp¢÷"7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFW€¢÷"æ÷B6VÆbç7F6°¢“ ¢&WGW&â‚¢÷F–öç2ÒµÐ¢f÷"6&B–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ†æC ¢–b€¢$–ç7FçB"æ÷B–â6&Bæ6&BçG—UöÆ–æP¢÷"6VÆbç–ÖVçE÷Æâ‡Æ–W%ö–æFW‚Â6&B’—2æöæP¢“ ¢6öçF–çVP¢f÷"F&vWB–â&WfW'6VB‡6VÆbç7F6²“ ¢–b€¢æ÷B—6–ç7Fæ6R‡F&vWBÂ7F6´ö&¦V7B¢÷"F&vWBæ6öçG&öÆÆW"ÓÒÆ–W%ö–æFW€¢÷"æ÷B6VÆbåö—5öÆVvÅö†æEö6÷VçFW%÷F&vWB†6&Bæ6&BÂF&vWB¢“ ¢6öçF–çVP¢÷F–öç2æVæB€¢7F–öä÷F–öâ€¢7F–öä¶–æBä45BÀ¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–CÖ6&Bæö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçCÖ6&Bæ6&Bæ÷&6ÆU÷FW‡BÀ¢&–÷&—G•öWö6ƒ×7FFRæWö6‚À¢¢¢&WGW&âGWÆR†÷F–öç2 ¢FVböææ÷Væ6Uö†æE÷&W7öç6R€¢6VÆbÂÆ–W%ö–æFWƒ¢–çBÂ6&C¢6&Dö&¦V7BÂF&vWC¢7F6´ö&¦V7@¢’Óâ7F6´ö&¦V7BÂæöæS ¢""$ææ÷Væ6RöæR7W÷'FVB†æB–ç7FçBv–ç7Bâ÷÷6–ær7F6²7VÆÂâ"" ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b€¢7FFR—2æöæP¢÷"7FFRç&W6öÇWF–öå÷VæF–æp¢÷"7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFW€¢÷"æ÷B6VÆbç7F6°¢÷"F&vWBæ÷B–â6VÆbç7F6°¢÷"F&vWBæ6öçG&öÆÆW"ÓÒÆ–W%ö–æFW€¢÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR†6&BÂ&†æB"¢÷"6&Bæ÷væW"ÒÆ–W%ö–æFW€¢÷"$–ç7FçB"æ÷B–â6&Bæ6&BçG—UöÆ–æP¢÷"æ÷B6VÆbåö—5öÆVvÅö†æEö6÷VçFW%÷F&vWB†6&Bæ6&BÂF&vWB¢“ ¢&WGW&âæöæP¢ÆâÒ6VÆbç–ÖVçE÷Æâ‡Æ–W%ö–æFW‚Â6&B¢–bÆâ—2æöæS ¢&WGW&âæöæP¢7VÆÂÒ6VÆbåö6öÖÖ—Eöææ÷Væ6VÖVçE÷–ÖVçB€¢6&BÀ¢ÆâÀ¢67Eö¶–æC×6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æBÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢¢6VÆbæÆör€¢'7VÆÅö67B"À¢Æ–W#×6VÆbçÆ–W'5·Æ–W%ö–æFW…ÒææÖRÀ¢6&C×7VÆÂææÖRÀ¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢&W7öç6SÕG'VRÀ¢¢6VÆbåöVçVWVU÷7VÆÅö67E÷G&–vvW'2‡7VÆÂ¢6VÆbæÆör€¢'&W7öç6U÷6VÆV7FVB"À¢Æ–W#×6VÆbçÆ–W'5·Æ–W%ö–æFW…ÒææÖRÀ¢Æ–W%ö–æFWƒ×Æ–W%ö–æFW‚À¢&W7öç6Uö6&C×7VÆÂææÖRÀ¢&W7öç6Uöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢F&vWE÷7VÆÅö–C×F&vWBæö&¦V7Eö–BÀ¢&–÷&—G•öWö6ƒ×7FFRæWö6‚À¢¢6VÆbæÆör€¢'&W7öç6U÷F&vWE÷6VÆV7FVB"À¢&W7öç6Uöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢F&vWE÷7VÆÅö–C×F&vWBæö&¦V7Eö–BÀ¢F&vWEö6&C×F&vWBæ6&BææÖRÀ¢¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‡&–÷&—G•÷Æ–W#×Æ–W%ö–æFW‚¢&WGW&â7VÆÀ ¢FVböÆöu÷7W÷'FVEö†æE÷&W7öç6W2‡6VÆb’ÓâæöæS ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b7FFR—2æöæS ¢&WGW&à¢f÷"÷F–öâ–â6VÆbåö†æE÷&W7öç6Uö÷F–öç2‡7FFRçÆ–W%ö–æFW‚“ ¢¶W’Ò‡7FFRæWö6‚Â÷F–öâæö&¦V7Eö–B÷"""Â÷F–öâçF&vWEö–B÷"""¢–b¶W’–â6VÆbå÷&W7öç6UöW‡÷7W&Uö¶W—3 ¢6öçF–çVP¢6VÆbå÷&W7öç6UöW‡÷7W&Uö¶W—2æFB†¶W’¢6VÆbæÆör€¢&ÆVvÅ÷&W7öç6UöW‡÷6VB"À¢Æ–W#×6VÆbçÆ–W'5·7FFRçÆ–W%ö–æFW…ÒææÖRÀ¢Æ–W%ö–æFWƒ×7FFRçÆ–W%ö–æFW‚À¢&W7öç6Uöö&¦V7Eö–CÖ÷F–öâæö&¦V7Eö–BÀ¢F&vWE÷7VÆÅö–CÖ÷F–öâçF&vWEö–BÀ¢&–÷&—G•öWö6ƒ×7FFRæWö6‚À¢ ¢FVbö6÷VçFW%ö7F—fF–öåö÷F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b€¢7FFR—2æöæP¢÷"7FFRç&W6öÇWF–öå÷VæF–æp¢÷"7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFW€¢÷"æ÷B6VÆbç7F6°¢“ ¢&WGW&â‚¢F&vWEö–G2Ò6VÆbåöÆVvÅö6÷VçFW%÷F&vWEö–G2‡Æ–W%ö–æFW‚¢–bæ÷BF&vWEö–G3 ¢&WGW&â‚¢÷F–öç2ÒµÐ¢f÷"6÷W&6R–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆC ¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡6÷W&6Rç'VÆW5ö6&B“ ¢6VÖçF–72Ò6VÆbæ–çFW'&WFW"æ7F—fFVEö&–Æ—G•÷6VÖçF–72‡6÷W&6Ræ6&BÂg&vÖVçB¢–b€¢6VÖçF–72—2æöæP¢÷"æ÷B6VÖçF–72æ6÷fW&vRægVÆÇ•÷7W÷'FV@¢÷"6VÖçF–72ç&öw&ÒæVffV7Eö¶–æB—2æ÷B7F—fFVDVffV7D¶–æBä4õTåDU%õD$tUEõ5TÄÀ¢÷"6VÆbæ7F—fF–öå÷–ÖVçE÷Æâ‡Æ–W%ö–æFW‚Â6÷W&6RÂg&vÖVçB’—2æöæP¢“ ¢6öçF–çVP¢f÷"F&vWEö–B–âF&vWEö–G3 ¢÷F–öç2æVæB€¢7F–öä÷F–öâ€¢7F–öä¶–æBä5D•dDUô$”Ä•E’À¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–C×6÷W&6Ræö&¦V7Eö–BÀ¢F&vWEö–C×F&vWEö–BÀ¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢&–÷&—G•öWö6ƒ×7FFRæWö6‚À¢¢¢&WGW&âGWÆR†÷F–öç2 ¢FVbÆVvÅ÷&–÷&—G•ö7F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢""$W‡÷6RöæÇ’–Ö×WF&ÆRVæv–æRÖvVæW&FVB6†ö–6W2f÷"F†R&÷VæFVB&–÷&—G’v–æF÷râ"" ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b7FFR—2æöæR÷"7FFRç&W6öÇWF–öå÷VæF–ær÷"Æ–W%ö–æFW‚Ò7FFRçÆ–W%ö–æFWƒ ¢&WGW&â‚¢&WGW&â€¢7F–öä÷F–öâ€¢7F–öä¶–æBå55õ$”õ$•E’À¢Æ–W%ö–æFW‚À¢&–÷&—G•öWö6ƒ×7FFRæWö6‚À¢’À¢§6VÆbåö†æE÷&W7öç6Uö÷F–öç2‡Æ–W%ö–æFW‚’À¢¢€¢÷F–öà¢f÷"6&B–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ†æ@¢–b6VÆbæ–çFW'&WFW"æ¶–6¶VEö7&VGW&U÷E÷&öw&Ò†6&Bæ6&B’—2æ÷BæöæP¢f÷"÷F–öâ–â6VÆbåö¶–6¶VEö7&VGW&U÷Eö÷F–öç2€¢Æ–W%ö–æFW‚Â6&BÂ&–÷&—G•öWö6ƒ×7FFRæWö6€¢¢’À¢§6VÆbåöW&ö67Eö÷F–öç2‡Æ–W%ö–æFW‚Â&–÷&—G“ÕG'VR’À¢§6VÆbåöfÆ6…÷W&ÖæVçEö67Eö÷F–öç2‡Æ–W%ö–æFW‚’À¢§6VÆbåö†æE÷F&vWFVE÷&VÖ÷fÅö÷F–öç2‡Æ–W%ö–æFW‚’À¢§6VÆbåö†æEö÷F–öæÅ÷&W6WEö÷F–öç2‡Æ–W%ö–æFW‚’À¢§6VÆbåö†æEö6öæF—F–öæÅ÷Fö¶Våö÷F–öç2‡Æ–W%ö–æFW‚’À¢§6VÆbåö†æEö7&VGW&U÷÷vW%öFÖvUö÷F–öç2‡Æ–W%ö–æFW‚’À¢§6VÆbåö†æEöÖöFÅ÷7VÆÅö÷F–öç2‡Æ–W%ö–æFW‚’À¢§6VÆbåö†æEö6÷VçFW%ö¶W—v÷&Eöw&çEö÷F–öç2‡Æ–W%ö–æFW‚’À¢§6VÆbåö†æEöFVF…÷&WGW&åöw&çEö÷F–öç2‡Æ–W%ö–æFW‚’À¢§6VÆbåö†æE÷FV×÷&'•÷G—Uö&6U÷EöG&uö÷F–öç2‡Æ–W%ö–æFW‚’À¢§6VÆbåö†æE÷F&vWFVEöÆ–'&'•÷&WGW&åö÷F–öç2‡Æ–W%ö–æFW‚’À¢§6VÆbåöÆ–æ¶VEöW†–ÆUö–ç7FçEö÷F–öç2‡Æ–W%ö–æFW‚’À¢¢€¢÷F–öà¢f÷"÷F–öâ–â6VÆbæÆVvÅ÷6æVµö7F–öç2‡Æ–W%ö–æFW‚¢–b÷F–öâæ¶–æB—27F–öä¶–æBä45@¢’À¢§6VÆbæÆVvÅö†æEö7F—fFVEö&–Æ—G•ö7F–öç2‡Æ–W%ö–æFW‚’À¢§6VÆbæÆVvÅöÖæö&–Æ—G•ö7F–öç2‡Æ–W%ö–æFW‚Â&–÷&—G“ÕG'VR’À¢§6VÆbåö6÷VçFW%ö7F—fF–öåö÷F–öç2‡Æ–W%ö–æFW‚’À¢§6VÆbåöFÖvUö7F—fF–öå÷&–÷&—G•ö÷F–öç2‡Æ–W%ö–æFW‚’À¢§6VÆbåöæöå÷F&vWEö7F—fF–öå÷&–÷&—G•ö÷F–öç2‡Æ–W%ö–æFW‚’À¢ ¢FVböæöå÷F&vWEö7F—fF–öå÷&–÷&—G•ö÷F–öç2€¢6VÆbÂÆ–W%ö–æFWƒ¢–ç@¢’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢""$W‡÷6R6ö×ÆWFR–ç7FçB×7VVBÂVçF&vWFVB&W6÷W&6R7F—fF–öç2â"" ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b7FFR—2æöæR÷"7FFRç&W6öÇWF–öå÷VæF–ær÷"7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFWƒ ¢&WGW&â‚¢&WGW&âGWÆR€¢7F–öä÷F–öâ€¢7F–öä¶–æBä5D•dDUô$”Ä•E’À¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–C×6÷W&6Ræö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢&–÷&—G•öWö6ƒ×7FFRæWö6‚À¢¢f÷"6÷W&6R–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡6÷W&6Rç'VÆW5ö6&B¢f÷"6VÖçF–72–â‡6VÆbæ–çFW'&WFW"æ7F—fFVEö&–Æ—G•÷6VÖçF–72‡6÷W&6Ræ6&BÂg&vÖVçB’Â¢–b6VÖçF–72—2æ÷BæöæP¢æB6VÖçF–72æ6÷fW&vRægVÆÇ•÷7W÷'FV@¢æB6VÖçF–72ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBät”åõD…$TUôÄ”dP¢æB6VÖçF–72ç&öw&Òæ7F—fF–öåö–ç7G'V7F–öç2—2æöæP¢æB6VÆbæ7F—fF–öå÷–ÖVçE÷Æâ‡Æ–W%ö–æFW‚Â6÷W&6RÂg&vÖVçB’—2æ÷BæöæP¢ ¢FVböÆVvÅö7&VGW&U÷÷vW%÷6÷W&6R‡6VÆbÂ6÷W&6S¢ö&¦V7BÂ6öçG&öÆÆW#¢–çB’Óâ&ööÃ ¢&WGW&â€¢—6–ç7Fæ6R‡6÷W&6RÂW&ÖæVçB¢æB6÷W&6Ræ6öçG&öÆÆW"ÓÒ6öçG&öÆÆW ¢æB6VÆbåöÆVvÅöFÖvU÷F&vWB‡6÷W&6RÂ6öçG&öÆÆW"¢ ¢FVböÆVvÅö7&VGW&U÷÷vW%÷&V6—–VçB‡6VÆbÂF&vWC¢ö&¦V7BÂ6öçG&öÆÆW#¢–çB’Óâ&ööÃ ¢&WGW&â€¢—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢æBF&vWBæ6öçG&öÆÆW"Ò6öçG&öÆÆW ¢æB6VÆbåöÆVvÅöFÖvU÷F&vWB‡F&vWBÂ6öçG&öÆÆW"¢ ¢FVbö†æEö7&VGW&U÷÷vW%öFÖvUö÷F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b7FFR—2æöæR÷"7FFRç&W6öÇWF–öå÷VæF–ær÷"7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFWƒ ¢&WGW&â‚¢&WGW&âGWÆR€¢7F–öä÷F–öâ€¢7F–öä¶–æBä45BÀ¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–CÖ6&Bæö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢6†ö–6Uö–G3Ò‡6÷W&6Ræö&¦V7Eö–BÂ’À¢÷&6ÆUög&vÖVçCÖ6&Bæ6&Bæ÷&6ÆU÷FW‡BÀ¢&–÷&—G•öWö6ƒ×7FFRæWö6‚À¢¢f÷"6&B–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ†æ@¢–b6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æB—267D¶–æBä5$TEU$UõõtU%ôDÔtP¢æB$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢æB6VÆbç–ÖVçE÷Æâ‡Æ–W%ö–æFW‚Â6&B’—2æ÷BæöæP¢f÷"6÷W&6R–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢–b6VÆbåöÆVvÅö7&VGW&U÷÷vW%÷6÷W&6R‡6÷W&6RÂÆ–W%ö–æFW‚¢f÷"F&vWB–â6VÆbçÆ–W'5³ÒÆ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢–b6VÆbåöÆVvÅö7&VGW&U÷÷vW%÷&V6—–VçB‡F&vWBÂÆ–W%ö–æFW‚¢ ¢FVbö†æEöÖöFÅ÷7VÆÅö÷F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b7FFR—2æöæR÷"7FFRç&W6öÇWF–öå÷VæF–ær÷"7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFWƒ ¢&WGW&â‚¢&WGW&âGWÆR€¢÷F–öà¢f÷"6&B–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ†æ@¢–b6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æ@¢—267D¶–æBäÔôDÅõDô´Tåôõ%ô5$TEU$UõTÕ ¢æB$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢f÷"÷F–öâ–â6VÆbåöÖöFÅ÷7VÆÅö÷F–öç2‡Æ–W%ö–æFW‚Â6&BÂ&–÷&—G•öWö6ƒ×7FFRæWö6‚¢ ¢FVbö†æEö6÷VçFW%ö¶W—v÷&Eöw&çEö÷F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b7FFR—2æöæR÷"7FFRç&W6öÇWF–öå÷VæF–ær÷"7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFWƒ ¢&WGW&â‚¢&WGW&âGWÆR€¢÷F–öà¢f÷"6&B–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ†æ@¢–b6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æ@¢—267D¶–æBåD$tUDTEô4õTåDU%ô´U•tõ$Eôu$å@¢æB$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢f÷"÷F–öâ–â6VÆbåö6÷VçFW%ö¶W—v÷&Eöw&çEö÷F–öç2€¢Æ–W%ö–æFW‚Â6&BÂ&–÷&—G•öWö6ƒ×7FFRæWö6€¢¢ ¢FVbö†æEöFVF…÷&WGW&åöw&çEö÷F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b7FFR—2æöæR÷"7FFRç&W6öÇWF–öå÷VæF–ær÷"7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFWƒ ¢&WGW&â‚¢&WGW&âGWÆR€¢÷F–öà¢f÷"6&B–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ†æ@¢–b6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æ@¢—267D¶–æBåDTÕõ$%•ôDTD…õ$UEU$åôu$å@¢æB$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢f÷"÷F–öâ–â6VÆbåöFVF…÷&WGW&åöw&çEö÷F–öç2€¢Æ–W%ö–æFW‚Â6&BÂ&–÷&—G•öWö6ƒ×7FFRæWö6€¢¢ ¢FVbö†æE÷FV×÷&'•÷G—Uö&6U÷EöG&uö÷F–öç2€¢6VÆbÂÆ–W%ö–æFWƒ¢–ç@¢’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b7FFR—2æöæR÷"7FFRç&W6öÇWF–öå÷VæF–ær÷"7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFWƒ ¢&WGW&â‚¢&WGW&âGWÆR€¢÷F–öà¢f÷"6&B–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ†æ@¢–b6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æB—267D¶–æBåDTÕõ$%•õE•Uô$4UõEôE$p¢æB$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢f÷"÷F–öâ–â6VÆbå÷FV×÷&'•÷G—Uö&6U÷EöG&uö÷F–öç2€¢Æ–W%ö–æFW‚Â6&BÂ&–÷&—G•öWö6ƒ×7FFRæWö6€¢¢ ¢FVbö†æE÷F&vWFVEöÆ–'&'•÷&WGW&åö÷F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b7FFR—2æöæR÷"7FFRç&W6öÇWF–öå÷VæF–ær÷"7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFWƒ ¢&WGW&â‚¢&WGW&âGWÆR€¢÷F–öà¢f÷"6&B–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ†æ@¢–b6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æ@¢—267D¶–æBåD$tUDTEôÄ”%$%•õ$UEU$åôäEõDô´Tà¢æB$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢f÷"÷F–öâ–â6VÆbå÷F&vWFVEöÆ–'&'•÷&WGW&åö÷F–öç2€¢Æ–W%ö–æFW‚Â6&BÂ&–÷&—G•öWö6ƒ×7FFRæWö6€¢¢ ¢FVböFÖvUö7F—fF–öå÷&–÷&—G•ö÷F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b7FFR—2æöæR÷"7FFRç&W6öÇWF–öå÷VæF–ær÷"7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFWƒ ¢&WGW&â‚¢&WGW&âGWÆR€¢7F–öä÷F–öâ€¢7F–öä¶–æBä5D•dDUô$”Ä•E’À¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–C×6÷W&6Ræö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢&–÷&—G•öWö6ƒ×7FFRæWö6‚À¢¢f÷"6÷W&6R–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡6÷W&6Rç'VÆW5ö6&B¢f÷"6VÖçF–72–â‡6VÆbæ–çFW'&WFW"æ7F—fFVEö&–Æ—G•÷6VÖçF–72‡6÷W&6Ræ6&BÂg&vÖVçB’Â¢–b6VÖçF–72—2æ÷BæöæP¢æB6VÖçF–72æ6÷fW&vRægVÆÇ•÷7W÷'FV@¢æB6VÖçF–72ç&öw&ÒæVffV7Eö¶–æ@¢—27F—fFVDVffV7D¶–æBäDTÅôd•„TEôDÔtUõDõõD$tUEô5$TEU$P¢æB6VÆbæ7F—fF–öå÷–ÖVçE÷Æâ‡Æ–W%ö–æFW‚Â6÷W&6RÂg&vÖVçB’—2æ÷BæöæP¢f÷"Æ–W"–â6VÆbçÆ–W'0¢f÷"F&vWB–âÆ–W"æ&GFÆVf–VÆ@¢–b6VÆbåöÆVvÅö7F—fFVEöFÖvU÷F&vWB‡F&vWBÂÆ–W%ö–æFW‚¢ ¢FVbö†æE÷F&vWFVE÷&VÖ÷fÅö÷F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b7FFR—2æöæR÷"7FFRç&W6öÇWF–öå÷VæF–ær÷"7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFWƒ ¢&WGW&â‚¢&WGW&âGWÆR€¢7F–öä÷F–öâ€¢7F–öä¶–æBä45BÀ¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–CÖ6&Bæö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçCÖ6&Bæ6&Bæ÷&6ÆU÷FW‡BÀ¢&–÷&—G•öWö6ƒ×7FFRæWö6‚À¢¢f÷"6&B–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ†æ@¢–b$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢f÷"&öw&Ò–â‡6VÆbæ–çFW'&WFW"çF&vWFVE÷&VÖ÷fÅ÷&öw&Ò†6&Bæ6&B’Â¢–b&öw&Ò—2æ÷BæöæRæB6VÆbç–ÖVçE÷Æâ‡Æ–W%ö–æFW‚Â6&B’—2æ÷BæöæP¢f÷"6–FR–â6VÆbçÆ–W'0¢f÷"F&vWB–â6–FRæ&GFÆVf–VÆ@¢–b6VÆbåöÆVvÅ÷F&vWFVE÷&VÖ÷fÅ÷F&vWB‡F&vWBÂÆ–W%ö–æFW‚Â&öw&Ò¢ ¢FVbö†æEö÷F–öæÅ÷&W6WEö÷F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b7FFR—2æöæR÷"7FFRç&W6öÇWF–öå÷VæF–ær÷"7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFWƒ ¢&WGW&â‚¢&WGW&âGWÆR€¢7F–öä÷F–öâ€¢7F–öä¶–æBä45BÀ¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–CÖ6&Bæö&¦V7Eö–BÀ¢&–÷&—G•öWö6ƒ×7FFRæWö6‚À¢¢f÷"6&B–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ†æ@¢–b$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢æB6VÆbæ–çFW'&WFW"æ÷F–öæÅö†æE÷&W6WE÷&öw&Ò†6&Bæ6&B’—2æ÷BæöæP¢æB6VÆbç–ÖVçE÷Æâ‡Æ–W%ö–æFW‚Â6&B’—2æ÷BæöæP¢ ¢FVbö†æEö6öæF—F–öæÅ÷Fö¶Våö÷F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b7FFR—2æöæR÷"7FFRç&W6öÇWF–öå÷VæF–ær÷"7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFWƒ ¢&WGW&â‚¢&WGW&âGWÆR€¢7F–öä÷F–öâ€¢7F–öä¶–æBä45BÂÆ–W%ö–æFW‚Âö&¦V7Eö–CÖ6&Bæö&¦V7Eö–BÂ&–÷&—G•öWö6ƒ×7FFRæWö6€¢¢f÷"6&B–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ†æ@¢–b$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢æB6VÆbæ–çFW'&WFW"æ6öæF—F–öæÅ÷6æVµ÷Fö¶Vç5÷&öw&Ò†6&Bæ6&B’—2æ÷BæöæP¢æB6VÆbç–ÖVçE÷Æâ‡Æ–W%ö–æFW‚Â6&B’—2æ÷BæöæP¢ ¢FVböfÆ6…÷W&ÖæVçEö67Eö÷F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b7FFR—2æöæR÷"7FFRç&W6öÇWF–öå÷VæF–ær÷"7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFWƒ ¢&WGW&â‚¢&WGW&âGWÆR€¢7F–öä÷F–öâ€¢7F–öä¶–æBä45BÀ¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–CÖ6&Bæö&¦V7Eö–BÀ¢&–÷&—G•öWö6ƒ×7FFRæWö6‚À¢¢f÷"6&B–â€¢§6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ†æBÀ¢¢€¢6æF–FFP¢f÷"÷væW"–â6VÆbçÆ–W'0¢f÷"6æF–FFR–â÷væW"æW†–ÆP¢–b6VÆbå÷&†VÅ÷W&Ö—76–öåöf÷"‡Æ–W%ö–æFW‚Â6æF–FFR’—2æ÷BæöæP¢’À¢¢–b$fÆ6‚"–â6VÆbæ–çFW'&WFW"æg&vÖVçG2†6&Bæ6&B¢æB6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æB—267D¶–æBåU$ÔäTå@¢æB6VÆbç–ÖVçE÷Æâ€¢Æ–W%ö–æFW‚Â6&BÂÆÆ÷uöW†–ÆS×6VÆbæ—5öWF†÷&—FF—fR†6&BÂ&W†–ÆR"¢¢—2æ÷BæöæP¢ ¢FVböÆ–æ¶VEöW†–ÆUö–ç7FçEö÷F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢""$öffW"–BÂ÷&6ÆRÖ–çFW'&WFVB–ç7FçB7VÆÇ2w&çFVB'’Æ–æ¶VBÆ’W&Ö—76–öââ"" ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b7FFR—2æöæR÷"7FFRç&W6öÇWF–öå÷VæF–ær÷"7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFWƒ ¢&WGW&â‚¢÷F–öç3¢Æ—7E´7F–öä÷F–öåÒÒµÐ¢f÷"6&B–â†—FVÒf÷"÷væW"–â6VÆbçÆ–W'2f÷"—FVÒ–â÷væW"æW†–ÆR“ ¢–b€¢6VÆbå÷&†VÅ÷W&Ö—76–öåöf÷"‡Æ–W%ö–æFW‚Â6&B’—2æöæP¢÷"$–ç7FçB"æ÷B–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢÷"6VÆbç–ÖVçE÷Æâ‡Æ–W%ö–æFW‚Â6&BÂÆÆ÷uöW†–ÆSÕG'VR’—2æöæP¢“ ¢6öçF–çVP¢¶–æBÒ6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æ@¢–b¶–æB—267D¶–æBä5$TEU$UõõtU%ôDÔtS ¢÷F–öç2æW‡FVæB€¢7F–öä÷F–öâ€¢7F–öä¶–æBä45BÀ¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–CÖ6&Bæö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢6†ö–6Uö–G3Ò‡6÷W&6Ræö&¦V7Eö–BÂ’À¢÷&6ÆUög&vÖVçCÖ6&Bæ6&Bæ÷&6ÆU÷FW‡BÀ¢&–÷&—G•öWö6ƒ×7FFRæWö6‚À¢¢f÷"6÷W&6R–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢–b6VÆbåöÆVvÅö7&VGW&U÷÷vW%÷6÷W&6R‡6÷W&6RÂÆ–W%ö–æFW‚¢f÷"F&vWB–â6VÆbçÆ–W'5³ÒÆ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢–b6VÆbåöÆVvÅö7&VGW&U÷÷vW%÷&V6—–VçB‡F&vWBÂÆ–W%ö–æFW‚¢¢6öçF–çVP¢–b¶–æB—267D¶–æBä´”4´TEô5$TEU$UõC ¢÷F–öç2æW‡FVæB€¢6VÆbåö¶–6¶VEö7&VGW&U÷Eö÷F–öç2‡Æ–W%ö–æFW‚Â6&BÂ&–÷&—G•öWö6ƒ×7FFRæWö6‚¢¢6öçF–çVP¢–b¶–æB—267D¶–æBäÔôDÅõDô´Tåôõ%ô5$TEU$UõTÕ ¢÷F–öç2æW‡FVæB€¢6VÆbåöÖöFÅ÷7VÆÅö÷F–öç2‡Æ–W%ö–æFW‚Â6&BÂ&–÷&—G•öWö6ƒ×7FFRæWö6‚¢¢6öçF–çVP¢–b¶–æB—267D¶–æBåD$tUDTEô4õTåDU%ô´U•tõ$Eôu$åC ¢÷F–öç2æW‡FVæB€¢6VÆbåö6÷VçFW%ö¶W—v÷&Eöw&çEö÷F–öç2€¢Æ–W%ö–æFW‚Â6&BÂ&–÷&—G•öWö6ƒ×7FFRæWö6€¢¢¢6öçF–çVP¢–b¶–æB—267D¶–æBåDTÕõ$%•ôDTD…õ$UEU$åôu$åC ¢÷F–öç2æW‡FVæB€¢6VÆbåöFVF…÷&WGW&åöw&çEö÷F–öç2‡Æ–W%ö–æFW‚Â6&BÂ&–÷&—G•öWö6ƒ×7FFRæWö6‚¢¢6öçF–çVP¢–b¶–æB—267D¶–æBåDTÕõ$%•õE•Uô$4UõEôE$s ¢÷F–öç2æW‡FVæB€¢6VÆbå÷FV×÷&'•÷G—Uö&6U÷EöG&uö÷F–öç2€¢Æ–W%ö–æFW‚Â6&BÂ&–÷&—G•öWö6ƒ×7FFRæWö6€¢¢¢6öçF–çVP¢–b¶–æB—267D¶–æBåD$tUDTEôÄ”%$%•õ$UEU$åôäEõDô´Tã ¢÷F–öç2æW‡FVæB€¢6VÆbå÷F&vWFVEöÆ–'&'•÷&WGW&åö÷F–öç2€¢Æ–W%ö–æFW‚Â6&BÂ&–÷&—G•öWö6ƒ×7FFRæWö6€¢¢¢6öçF–çVP¢–b¶–æB–â°¢67D¶–æBäE$uô4$E2À¢67D¶–æBåDõô4$Eõ4TÄT5D”ôâÀ¢67D¶–æBåDõô5$TEU$Uõ4TÄT5D”ôâÀ¢67D¶–æBäÄ”%$%•õ4T$4…õDõô„äBÀ¢67D¶–æBäõD”ôäÅô„äEõ$U4UBÀ¢Ó ¢F&vWG2Ò„æöæRÂ¢VÆ–b¶–æB—267D¶–æBäõD”ôäÅôDU5E$õ•ôäEô5$TDS ¢F&vWG2Ò„æöæRÂ’²GWÆR€¢F&vW@¢f÷"6–FR–â6VÆbçÆ–W'0¢f÷"F&vWB–â6–FRæ&GFÆVf–VÆ@¢–b6VÆbåöÆVvÅö÷F–öæÅöFW7G&÷•÷F&vWB‡F&vWBÂÆ–W%ö–æFW‚¢¢VÆ–b¶–æB—267D¶–æBä4ôäD•D”ôäÅôDU5E$õ•ôäEô5$TDS ¢F&vWG2ÒGWÆR€¢F&vW@¢f÷"6–FR–â6VÆbçÆ–W'0¢f÷"F&vWB–â6–FRæ&GFÆVf–VÆ@¢–b6VÆbåöÆVvÅö6öæF—F–öæÅöFW7G&÷•÷F&vWB‡F&vWBÂÆ–W%ö–æFW‚¢¢VÆ–b¶–æB—267D¶–æBåD$tUDTEõ$TÔõdÃ ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"çF&vWFVE÷&VÖ÷fÅ÷&öw&Ò†6&Bæ6&B¢76W'B&öw&Ò—2æ÷BæöæP¢F&vWG2ÒGWÆR€¢F&vW@¢f÷"6–FR–â6VÆbçÆ–W'0¢f÷"F&vWB–â6–FRæ&GFÆVf–VÆ@¢–b6VÆbåöÆVvÅ÷F&vWFVE÷&VÖ÷fÅ÷F&vWB‡F&vWBÂÆ–W%ö–æFW‚Â&öw&Ò¢¢VÆ–b¶–æB—267D¶–æBäDU5E$õ•ô%D”d5EôTä4„åDÔTåEôõ%õõtU%óEô5$TEU$S ¢F&vWG2ÒGWÆR€¢F&vW@¢f÷"6–FR–â6VÆbçÆ–W'0¢f÷"F&vWB–â6–FRæ&GFÆVf–VÆ@¢–b6VÆbåö—5öFW7G&÷•ö'F–f7EöVæ6†çFÖVçEö÷%÷÷vW%óEö7&VGW&U÷F&vWB‡F&vWB¢æB6VÆbåöÆVvÅ÷F&vWF–æu÷&÷FV7F–öâ‡F&vWBÂÆ–W%ö–æFW‚¢¢VÆ–b¶–æB–â´67D¶–æBäDÔtUó5ôõõ4”äuô5$TEU$RÂ67D¶–æBäDTÅôDÔtWÓ ¢F&vWG2ÒGWÆR€¢F&vW@¢f÷"F&vWB–â6VÆbçÆ–W'5³ÒÆ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢–b6VÆbåöÆVvÅöFÖvU÷F&vWB‡F&vWBÂÆ–W%ö–æFW‚¢¢VÆ–b¶–æB—267D¶–æBäôõ¤Uõ5”ÄÃ ¢F&vWG2ÒGWÆR€¢F&vW@¢f÷"F&vWB–â6VÆbç7F6°¢–b—6–ç7Fæ6R‡F&vWBÂ7F6´ö&¦V7B¢æB6VÆbåö—5öÆVvÅöö÷¦U÷F&vWB‡F&vWBÂÆ–W%ö–æFW‚¢¢VÆ–b¶–æB—267D¶–æBä4õTåDU%õD$tUEõ5TÄÃ ¢F&vWG2ÒGWÆR€¢F&vW@¢f÷"F&vWB–â6VÆbç7F6°¢–b—6–ç7Fæ6R‡F&vWBÂ7F6´ö&¦V7B¢æB6VÆbåö—5öÆVvÅö†æEö6÷VçFW%÷F&vWB†6&Bæ6&BÂF&vWB¢¢VÇ6S ¢6öçF–çVP¢÷F–öç2æW‡FVæB€¢7F–öä÷F–öâ€¢7F–öä¶–æBä45BÀ¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–CÖ6&Bæö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–B–bF&vWB—2æ÷BæöæRVÇ6RæöæRÀ¢÷&6ÆUög&vÖVçCÖ6&Bæ6&Bæ÷&6ÆU÷FW‡BÀ¢&–÷&—G•öWö6ƒ×7FFRæWö6‚À¢¢f÷"F&vWB–âF&vWG0¢¢&WGW&âGWÆR†÷F–öç2 ¢FVbW†V7WFU÷&–÷&—G•ö7F–öâ‡6VÆbÂ÷F–öã¢7F–öä÷F–öâ’Óâ&ööÃ ¢""%&WfÆ–FFRæBÇ’öæR–Æ÷B×6VÆV7FVB&÷VæFVB&–÷&—G’FV6—6–öââ"" ¢–b÷F–öâæ÷B–â6VÆbæÆVvÅ÷&–÷&—G•ö7F–öç2†÷F–öâçÆ–W%ö–æFW‚“ ¢&—6RfÇVTW'&÷"‚'&–÷&—G’7F–öâ—2æ÷B7W'&VçFÇ’ÆVvÂ"¢–b÷F–öâæ¶–æB—27F–öä¶–æBä45BæB÷F–öâ–â6VÆbæÆVvÅ÷6æVµö7F–öç2€¢÷F–öâçÆ–W%ö–æFW€¢“ ¢&WGW&â6VÆbæW†V7WFU÷6æVµö7F–öâ†÷F–öâ¢–b÷F–öâæ¶–æB—27F–öä¶–æBä5D•dDUô$”Ä•E“ ¢6÷W&6RÒ6VÆbåöö&¦V7G2ævWB†÷F–öâæö&¦V7Eö–B÷"""¢–b—6–ç7Fæ6R‡6÷W&6RÂ6&Dö&¦V7B’æB÷F–öâæ÷&6ÆUög&vÖVçB—2æ÷BæöæS ¢&WGW&â€¢6VÆbæææ÷Væ6Uö†æEö7F—fFVEö&–Æ—G’€¢÷F–öâçÆ–W%ö–æFW‚Â6÷W&6RÂ÷F–öâæ÷&6ÆUög&vÖVç@¢¢—2æ÷BæöæP¢¢–bæ÷B—6–ç7Fæ6R‡6÷W&6RÂW&ÖæVçB’÷"÷F–öâæ÷&6ÆUög&vÖVçB—2æöæS ¢&—6RfÇVTW'&÷"‚&6÷VçFW"7F—fF–öâ÷F–öâ—2ÖÆf÷&ÖVB"¢F&vWEö–G2Ò‚’–b÷F–öâçF&vWEö–B—2æöæRVÇ6R†÷F–öâçF&vWEö–BÂ¢&–Æ—G’Ò6VÆbæææ÷Væ6Uö7F—fFVEö&–Æ—G’€¢÷F–öâçÆ–W%ö–æFW‚À¢6÷W&6RÀ¢÷F–öâæ÷&6ÆUög&vÖVçBÀ¢F&vWEö–G3×F&vWEö–G2À¢6†ö–6Uö–G3Ö÷F–öâæ6†ö–6Uö–G2À¢¢–b&–Æ—G’—2æöæS ¢&—6RfÇVTW'&÷"‚&6÷VçFW"7F—fF–öâ÷F–öâ&V6ÖR–ÆÆVvÂ"¢–b&–Æ—G’ç¦öæRÓÒ'7F6²# ¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‡&–÷&—G•÷Æ–W#Ö÷F–öâçÆ–W%ö–æFW‚¢&WGW&âG'VP¢–b÷F–öâæ¶–æB—27F–öä¶–æBä45C ¢6&BÒ6VÆbåöö&¦V7G2ævWB†÷F–öâæö&¦V7Eö–B÷"""¢F&vWBÒ6VÆbåöö&¦V7G2ævWB†÷F–öâçF&vWEö–B÷"""¢6÷W&6U÷F&vWBÒ6VÆbåöö&¦V7G2ævWB†÷F–öâæ6†ö–6Uö–G5³Ò’–b÷F–öâæ6†ö–6Uö–G2VÇ6RæöæP¢–b—6–ç7Fæ6R†6&BÂ6&Dö&¦V7B’æB6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æB—2€¢67D¶–æBåD$tUDTEôÄ”%$%•õ$UEU$åôäEõDô´Tà¢“ ¢7VÆÂÒ6VÆbæææ÷Væ6U÷7VÆÂ€¢÷F–öâçÆ–W%ö–æFW‚À¢6&BÀ¢F&vWB–b—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB’VÇ6RæöæRÀ¢67Eög&öÕöW†–ÆS×6VÆbæ—5öWF†÷&—FF—fR†6&BÂ&W†–ÆR"’À¢¢–b7VÆÂ—2æöæS ¢&—6RfÇVTW'&÷"‚'F&vWFVBÆ–'&'’&WGW&â&W7öç6R&V6ÖR–ÆÆVvÂ"¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‡&–÷&—G•÷Æ–W#Ö÷F–öâçÆ–W%ö–æFW‚¢&WGW&âG'VP¢–b—6–ç7Fæ6R†6&BÂ6&Dö&¦V7B’æB6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æB—2€¢67D¶–æBåDTÕõ$%•õE•Uô$4UõEôE$p¢“ ¢7VÆÂÒ6VÆbæææ÷Væ6U÷7VÆÂ€¢÷F–öâçÆ–W%ö–æFW‚À¢6&BÀ¢F&vWB–b—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB’VÇ6RæöæRÀ¢67Eög&öÕöW†–ÆS×6VÆbæ—5öWF†÷&—FF—fR†6&BÂ&W†–ÆR"’À¢¢–b7VÆÂ—2æöæS ¢&—6RfÇVTW'&÷"‚'FV×÷&'’æ–ÖF–öâ&W7öç6R&V6ÖR–ÆÆVvÂ"¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‡&–÷&—G•÷Æ–W#Ö÷F–öâçÆ–W%ö–æFW‚¢&WGW&âG'VP¢–b—6–ç7Fæ6R†6&BÂ6&Dö&¦V7B’æB6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æB—2€¢67D¶–æBåD$tUDTEô4õTåDU%ô´U•tõ$Eôu$å@¢“ ¢7VÆÂÒ6VÆbæææ÷Væ6U÷7VÆÂ€¢÷F–öâçÆ–W%ö–æFW‚À¢6&BÀ¢F&vWB–b—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB’VÇ6RæöæRÀ¢67Eög&öÕöW†–ÆS×6VÆbæ—5öWF†÷&—FF—fR†6&BÂ&W†–ÆR"’À¢¢–b7VÆÂ—2æöæS ¢&—6RfÇVTW'&÷"‚&6÷VçFW"ÖæBÖ¶W—v÷&B&W7öç6R&V6ÖR–ÆÆVvÂ"¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‡&–÷&—G•÷Æ–W#Ö÷F–öâçÆ–W%ö–æFW‚¢&WGW&âG'VP¢–b—6–ç7Fæ6R†6&BÂ6&Dö&¦V7B’æB6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æB—2€¢67D¶–æBåDTÕõ$%•ôDTD…õ$UEU$åôu$å@¢“ ¢7VÆÂÒ6VÆbæææ÷Væ6U÷7VÆÂ€¢÷F–öâçÆ–W%ö–æFW‚À¢6&BÀ¢F&vWB–b—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB’VÇ6RæöæRÀ¢67Eög&öÕöW†–ÆS×6VÆbæ—5öWF†÷&—FF—fR†6&BÂ&W†–ÆR"’À¢¢–b7VÆÂ—2æöæS ¢&—6RfÇVTW'&÷"‚&FVF‚×&WGW&âw&çB&V6ÖR–ÆÆVvÂ"¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‡&–÷&—G•÷Æ–W#Ö÷F–öâçÆ–W%ö–æFW‚¢&WGW&âG'VP¢–b—6–ç7Fæ6R†6&BÂ6&Dö&¦V7B’æB6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æB—2€¢67D¶–æBäÔôDÅõDô´Tåôõ%ô5$TEU$UõTÕ ¢“ ¢7VÆÂÒ6VÆbæææ÷Væ6U÷7VÆÂ€¢÷F–öâçÆ–W%ö–æFW‚À¢6&BÀ¢F&vWB–b—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB’VÇ6RæöæRÀ¢67Eög&öÕöW†–ÆS×6VÆbæ—5öWF†÷&—FF—fR†6&BÂ&W†–ÆR"’À¢ÖöFUög&vÖVçCÖ÷F–öâæ÷&6ÆUög&vÖVçBÀ¢¢–b7VÆÂ—2æöæS ¢&—6RfÇVTW'&÷"‚&ÖöFÂ&W7öç6R&V6ÖR–ÆÆVvÂ"¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‡&–÷&—G•÷Æ–W#Ö÷F–öâçÆ–W%ö–æFW‚¢&WGW&âG'VP¢–b—6–ç7Fæ6R†6&BÂ6&Dö&¦V7B’æB÷F–öâ–â6VÆbåö†æEö7&VGW&U÷÷vW%öFÖvUö÷F–öç2€¢÷F–öâçÆ–W%ö–æFW€¢“ ¢7VÆÂÒ6VÆbæææ÷Væ6U÷7VÆÂ€¢÷F–öâçÆ–W%ö–æFW‚À¢6&BÀ¢F&vWBÀ¢6÷W&6U÷F&vWC×6÷W&6U÷F&vWB–b—6–ç7Fæ6R‡6÷W&6U÷F&vWBÂW&ÖæVçB’VÇ6RæöæRÀ¢¢–b7VÆÂ—2æöæS ¢&—6RfÇVTW'&÷"‚&7&VGW&R×÷vW"FÖvR&W7öç6R&V6ÖR–ÆÆVvÂ"¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‡&–÷&—G•÷Æ–W#Ö÷F–öâçÆ–W%ö–æFW‚¢&WGW&âG'VP¢–b—6–ç7Fæ6R†6&BÂ6&Dö&¦V7B’æB÷F–öâ–â6VÆbåö†æE÷F&vWFVE÷&VÖ÷fÅö÷F–öç2€¢÷F–öâçÆ–W%ö–æFW€¢“ ¢7VÆÂÒ6VÆbæææ÷Væ6U÷7VÆÂ†÷F–öâçÆ–W%ö–æFW‚Â6&BÂF&vWB¢–b7VÆÂ—2æöæS ¢&—6RfÇVTW'&÷"‚'F&vWFVB&VÖ÷fÂ&W7öç6R&V6ÖR–ÆÆVvÂ"¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‡&–÷&—G•÷Æ–W#Ö÷F–öâçÆ–W%ö–æFW‚¢&WGW&âG'VP¢–b—6–ç7Fæ6R†6&BÂ6&Dö&¦V7B’æB÷F–öâ–â6VÆbåö†æEö÷F–öæÅ÷&W6WEö÷F–öç2€¢÷F–öâçÆ–W%ö–æFW€¢“ ¢7VÆÂÒ6VÆbæææ÷Væ6U÷7VÆÂ†÷F–öâçÆ–W%ö–æFW‚Â6&B¢–b7VÆÂ—2æöæS ¢&—6RfÇVTW'&÷"‚&†æB&W6WB&W7öç6R&V6ÖR–ÆÆVvÂ"¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‡&–÷&—G•÷Æ–W#Ö÷F–öâçÆ–W%ö–æFW‚¢&WGW&âG'VP¢–b—6–ç7Fæ6R†6&BÂ6&Dö&¦V7B’æB÷F–öâ–â6VÆbåö†æEö6öæF—F–öæÅ÷Fö¶Våö÷F–öç2€¢÷F–öâçÆ–W%ö–æFW€¢“ ¢7VÆÂÒ6VÆbæææ÷Væ6U÷7VÆÂ†÷F–öâçÆ–W%ö–æFW‚Â6&B¢–b7VÆÂ—2æöæS ¢&—6RfÇVTW'&÷"‚'Fö¶Vâ7VÆÂ&W7öç6R&V6ÖR–ÆÆVvÂ"¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‡&–÷&—G•÷Æ–W#Ö÷F–öâçÆ–W%ö–æFW‚¢&WGW&âG'VP¢–b—6–ç7Fæ6R†6&BÂ6&Dö&¦V7B’æB÷F–öâ–â6VÆbåöÆ–æ¶VEöW†–ÆUö–ç7FçEö÷F–öç2€¢÷F–öâçÆ–W%ö–æFW€¢“ ¢6÷7BÒ6VÆbåöö&¦V7G2ævWB†÷F–öâæ6÷7Eöö&¦V7Eö–B÷"""¢7VÆÂÒ6VÆbæææ÷Væ6U÷7VÆÂ€¢÷F–öâçÆ–W%ö–æFW‚À¢6&BÀ¢F&vWBÀ¢67Eög&öÕöW†–ÆSÕG'VRÀ¢67&–f–6Uö6÷7CÖ6÷7B–b—6–ç7Fæ6R†6÷7BÂW&ÖæVçB’VÇ6RæöæRÀ¢6÷W&6U÷F&vWC×6÷W&6U÷F&vWB–b—6–ç7Fæ6R‡6÷W&6U÷F&vWBÂW&ÖæVçB’VÇ6RæöæRÀ¢ÖöFUög&vÖVçCÒ€¢÷F–öâæ÷&6ÆUög&vÖVç@¢–b6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æ@¢—267D¶–æBäÔôDÅõDô´Tåôõ%ô5$TEU$UõTÕ ¢VÇ6RæöæP¢’À¢¢–b7VÆÂ—2æöæS ¢&—6RfÇVTW'&÷"‚&Æ–æ¶VB–ç7FçB&V6ÖR–ÆÆVvÂBææ÷Væ6VÖVçB"¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‡&–÷&—G•÷Æ–W#Ö÷F–öâçÆ–W%ö–æFW‚¢&WGW&âG'VP¢–b—6–ç7Fæ6R†6&BÂ6&Dö&¦V7B’æB÷F–öâ–â6VÆbåöfÆ6…÷W&ÖæVçEö67Eö÷F–öç2€¢÷F–öâçÆ–W%ö–æFW€¢“ ¢7VÆÂÒ6VÆbæææ÷Væ6U÷7VÆÂ€¢÷F–öâçÆ–W%ö–æFW‚À¢6&BÀ¢67Eög&öÕöW†–ÆS×6VÆbæ—5öWF†÷&—FF—fR†6&BÂ&W†–ÆR"’À¢¢–b7VÆÂ—2æöæS ¢&—6RfÇVTW'&÷"‚$fÆ6‚W&ÖæVçB&W7öç6R&V6ÖR–ÆÆVvÂ"¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‡&–÷&—G•÷Æ–W#Ö÷F–öâçÆ–W%ö–æFW‚¢&WGW&âG'VP¢–b—6–ç7Fæ6R†6&BÂ6&Dö&¦V7B’æB6VÆbæ–çFW'&WFW"æW&÷&öw&Ò†6&Bæ6&B“ ¢7VÆÂÒ6VÆbæææ÷Væ6U÷7VÆÂ€¢÷F–öâçÆ–W%ö–æFW‚À¢6&BÀ¢F&vWBÀ¢67Eög&öÕöW†–ÆS×6VÆbæ—5öWF†÷&—FF—fR†6&BÂ&W†–ÆR"’À¢¢–b7VÆÂ—2æöæS ¢&—6RfÇVTW'&÷"‚$W&&W7öç6R&V6ÖR–ÆÆVvÂ"¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‡&–÷&—G•÷Æ–W#Ö÷F–öâçÆ–W%ö–æFW‚¢&WGW&âG'VP¢–b—6–ç7Fæ6R†6&BÂ6&Dö&¦V7B’æB6VÆbæ–çFW'&WFW"æ¶–6¶VEö7&VGW&U÷E÷&öw&Ò€¢6&Bæ6&@¢“ ¢–bæ÷B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB“ ¢&—6RfÇVTW'&÷"‚&7&VGW&RÖöF–f–W"F&vWB—2–çfÆ–B"¢6÷7BÒ6VÆbåöö&¦V7G2ævWB†÷F–öâæ6÷7Eöö&¦V7Eö–B÷"""¢7VÆÂÒ6VÆbæææ÷Væ6U÷7VÆÂ€¢÷F–öâçÆ–W%ö–æFW‚À¢6&BÀ¢F&vWBÀ¢67&–f–6Uö6÷7CÖ6÷7B–b—6–ç7Fæ6R†6÷7BÂW&ÖæVçB’VÇ6RæöæRÀ¢¢–b7VÆÂ—2æöæS ¢&—6RfÇVTW'&÷"‚&–ç7FçB&W7öç6R&V6ÖR–ÆÆVvÂ"¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‡&–÷&—G•÷Æ–W#Ö÷F–öâçÆ–W%ö–æFW‚¢&WGW&âG'VP¢–bæ÷B—6–ç7Fæ6R†6&BÂ6&Dö&¦V7B’÷"æ÷B—6–ç7Fæ6R‡F&vWBÂ7F6´ö&¦V7B“ ¢&—6RfÇVTW'&÷"‚&†æB&W7öç6R÷F–öâ—2ÖÆf÷&ÖVB"¢7VÆÂÒ6VÆbåöææ÷Væ6Uö†æE÷&W7öç6R†÷F–öâçÆ–W%ö–æFW‚Â6&BÂF&vWB¢–b7VÆÂ—2æöæS ¢&—6RfÇVTW'&÷"‚&†æB&W7öç6R÷F–öâ&V6ÖR–ÆÆVvÂ"¢&WGW&âG'VP¢–b÷F–öâæ¶–æB—2æ÷B7F–öä¶–æBå55õ$”õ$•E“ ¢&—6RfÇVTW'&÷"‚'Vç7W÷'FVB&–÷&—G’7F–öâ¶–æB"¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢76W'B7FFR—2æ÷BæöæP¢76W2Ò7FFRæ6öç6V7WF—fU÷76W2²†÷F–öâçÆ–W%ö–æFW‚Â¢VæF–ærÒÆVâ‡76W2’ÓÒ ¢æW‡E÷Æ–W"Ò÷F–öâçÆ–W%ö–æFW‚–bVæF–ærVÇ6RÒ÷F–öâçÆ–W%ö–æFW€¢6VÆbç&–÷&—G•÷7FFRÒ&–÷&—G•7FFR‡7FFRæWö6‚ÂæW‡E÷Æ–W"Â76W2ÂVæF–ær¢–b6VÆbç7F6²æB—6–ç7Fæ6R‡6VÆbç7F6µ²ÓÒÂ7F—fFVD&–Æ—G”ö&¦V7B“ ¢7F6µöö&¦V7Eö–BÒ6VÆbç7F6µ²ÓÒæö&¦V7Eö–@¢f÷"–æFW‚ÂWf–FVæ6R–âVçVÖW&FR‡6VÆbæfööEö7F—fF–öåöWf–FVæ6R“ ¢–bWf–FVæ6Rç7F6µöö&¦V7Eö–BÓÒ7F6µöö&¦V7Eö–C ¢6VÆbæfööEö7F—fF–öåöWf–FVæ6U¶–æFW…ÒÒ&WÆ6R€¢Wf–FVæ6RÀ¢&–÷&—G•÷76W3×76W2À¢&W6öÇWF–öå÷W&Ö—GFVC×VæF–ærÀ¢¢'&V°¢6VÆbæÆör€¢'&–÷&—G•÷76VB"À¢Æ–W#×6VÆbçÆ–W'5¶÷F–öâçÆ–W%ö–æFW…ÒææÖRÀ¢Æ–W%ö–æFWƒÖ÷F–öâçÆ–W%ö–æFW‚À¢&–÷&—G•öWö6ƒ×7FFRæWö6‚À¢6öç6V7WF—fU÷76W3ÖÆVâ‡76W2’À¢&W6öÇWF–öå÷VæF–æs×VæF–ærÀ¢¢–bæ÷BVæF–æs ¢6VÆbæÆör€¢'&–÷&—G•öw&çFVB"À¢Æ–W#×6VÆbçÆ–W'5¶æW‡E÷Æ–W%ÒææÖRÀ¢Æ–W%ö–æFWƒÖæW‡E÷Æ–W"À¢&–÷&—G•öWö6ƒ×7FFRæWö6‚À¢¢VÇ6S ¢6VÆbæÆör€¢'7F6µ÷&W6öÇWF–öå÷W&Ö—GFVB"–b6VÆbç7F6²VÇ6R'&–÷&—G•÷v–æF÷u÷76VB"À¢7F6µöö&¦V7Eö–C×6VÆbç7F6µ²ÓÒæö&¦V7Eö–B–b6VÆbç7F6²VÇ6RæöæRÀ¢&–÷&—G•öWö6ƒ×7FFRæWö6‚À¢¢&WGW&âG'VP ¢FVb&ö6W75÷&–÷&—G•÷&W6öÇWF–öâ‡6VÆb’Óâ&ööÃ ¢""%W&f÷&ÒâVæv–æR×W&Ö—GFVB&W6öÇWF–öâgFW"F†R&W&W6VçFVBÆÂ×726WVVæ6Râ"" ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b7FFR—2æöæR÷"æ÷B7FFRç&W6öÇWF–öå÷VæF–æs ¢&—6RfÇVTW'&÷"‚'7F6²&W6öÇWF–öâ—2æ÷BW&Ö—GFVB"¢–bæ÷B6VÆbç7F6³ ¢6VÆbç&–÷&—G•÷7FFRÒæöæP¢&WGW&âG'VP¢6VÆbç&–÷&—G•÷7FFRÒæöæP¢6VÆbå÷&–÷&—G•÷&W6öÇWF–öåö–å÷&öw&W72ÒG'VP¢G'“ ¢6VÆbç&W6öÇfU÷F÷ööe÷7F6²‚¢f–æÆÇ“ ¢6VÆbå÷&–÷&—G•÷&W6öÇWF–öåö–å÷&öw&W72ÒfÇ6P¢6VÆbæ6†V6µ÷7FFUö&6VEö7F–öç2‚¢–bæ÷B6VÆbæ—5÷FW&Ö–æÃ ¢6VÆbå÷WE÷VæF–æu÷G&–vvW'5ööå÷7F6²‚¢–bæ÷B6VÆbæ—5÷FW&Ö–æÂæB6VÆbç7F6²æB6VÆbç&–÷&—G•÷7FFR—2æöæS ¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‚¢VÆ–b€¢æ÷B6VÆbæ—5÷FW&Ö–æÀ¢æB6VÆbç7FW—2GW&å7FWä4ôÔ$EôDÔtP¢æB6VÆbåö6öÖ&EöFÖvU÷&W6öÇfV@¢“ ¢6VÆbåöGfæ6UögFW%ö6öÖ&EöFÖvR‚¢VÆ–b€¢æ÷B6VÆbæ—5÷FW&Ö–æÀ¢æB6VÆbç7FW—2GW&å7FWäDT4Ä$UôED4´U%0¢æB6VÆbåöGF6¶W'5öFV6Æ&V@¢“ ¢6VÆbçG&ç6—F–öå÷Fò…GW&å7FWäDT4Ä$Uô$Äô4´U%2¢&WGW&âG'VP ¢FVböGfæ6UögFW%ö6öÖ&EöFÖvR‡6VÆb’ÓâæöæS ¢""$Gfæ6RöæÇ’gFW"FÖvRÖ7&VFVB7F6²æB&–÷&—G’v÷&²—26ö×ÆWFRâ"" ¢–b6VÆbç7FW—2æ÷BGW&å7FWä4ôÔ$EôDÔtR÷"æ÷B6VÆbåö6öÖ&EöFÖvU÷&W6öÇfVC ¢&—6RfÇVTW'&÷"‚&6öÖ&BFÖvR—2æ÷B&VG’FòGfæ6R"¢–b6VÆbç7F6²÷"6VÆbç&–÷&—G•÷7FFR—2æ÷BæöæS ¢&WGW&à¢–b€¢6VÆbåö6öÖ&EöFÖvU÷7FWö¶–æB—26öÖ&DFÖvU7FW¶–æBäd•%5Eõ5E$”´P¢æBæ÷B6VÆbæ—5÷FW&Ö–æÀ¢“ ¢6VÆbåö6ÆV%öÖæöEö&÷VæF'’‚'&VwVÆ%ö6öÖ&EöFÖvR"¢6VÆbå÷7F'Eö6öÖ&EöFÖvU÷7FW„6öÖ&DFÖvU7FW¶–æBå$TuTÄ"Â"Â"¢VÇ6S ¢6VÆbåö6öÖ&EöFÖvU÷7FWö¶–æBÒ6öÖ&DFÖvU7FW¶–æBä4ôÕÄUDP¢6VÆbçG&ç6—F–öå÷Fò…GW&å7FWäTäEôôeô4ôÔ$B ¢FVb÷&V6÷&E÷&W&W6VçFVE÷&–÷&—G•ö7F–öâ‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâæöæS ¢""%&W6WB76W2gFW"âVæv–æR×fÆ–FFVB&W7öç6S²æò7V6‚&W7öç6RW†—7G2–WBâ"" ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–b€¢7FFR—2æöæP¢÷"7FFRç&W6öÇWF–öå÷VæF–æp¢÷"7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFW€¢÷"æ÷B6VÆbç7F6°¢“ ¢&—6RfÇVTW'&÷"‚'&W&W6VçFVB&–÷&—G’7F–öâ—2æ÷B7W'&VçFÇ’ÆVvÂ"¢6VÆbç&–÷&—G•÷7FFRÒ&–÷&—G•7FFR‡7FFRæWö6‚ÂÆ–W%ö–æFW‚¢6VÆbæÆör€¢'&–÷&—G•ö7F–öå÷F¶Vâ"À¢Æ–W#×6VÆbçÆ–W'5·Æ–W%ö–æFW…ÒææÖRÀ¢Æ–W%ö–æFWƒ×Æ–W%ö–æFW‚À¢&–÷&—G•öWö6ƒ×7FFRæWö6‚À¢ ¢FVbö&Vv–å÷&–÷&—G•÷v–æF÷r€¢6VÆbÂ¢ÂÆÆ÷uöV×G“¢&ööÂÒfÇ6RÂ&–÷&—G•÷Æ–W#¢–çBÂæöæRÒæöæP¢’ÓâæöæS ¢–bæ÷B6VÆbç7F6²æBæ÷BÆÆ÷uöV×G“ ¢&—6RfÇVTW'&÷"‚'&–÷&—G’&WV—&W2æöæV×G’7F6²"¢–bÆÆ÷uöV×G’æB6VÆbç7FW–âµGW&å7FWå4UEUÂGW&å7FWåTåDÂGW&å7FWä4ÄTåUÓ ¢&—6RfÇVTW'&÷"‚'F†—27FW†2æò÷&F–æ'’&–÷&—G’v–æF÷r"¢Wö6‚Ò6VÆbåöæW‡E÷&–÷&—G•öWö6€¢6VÆbåöæW‡E÷&–÷&—G•öWö6‚³Ò¢†öÆFW"Ò6VÆbæ7F—fU÷Æ–W"–b&–÷&—G•÷Æ–W"—2æöæRVÇ6R&–÷&—G•÷Æ–W ¢6VÆbç&–÷&—G•÷7FFRÒ&–÷&—G•7FFR†Wö6‚Â†öÆFW"¢F÷Ò6VÆbç7F6µ²ÓÒ–b6VÆbç7F6²VÇ6RæöæP¢6VÆbæÆör€¢'&W7öç6U÷v–æF÷uö÷VæVB"À¢7F6µöö&¦V7Eö–C×F÷æö&¦V7Eö–B–bF÷—2æ÷BæöæRVÇ6RæöæRÀ¢7F6µö6&C×F÷ææÖR–b—6–ç7Fæ6R‡F÷Â7F6´ö&¦V7B’VÇ6RæöæRÀ¢&–÷&—G•öWö6ƒÖWö6‚À¢¢6VÆbå÷v—FæW75÷Vç7W÷'FVE÷7F6µ÷&W7öç6W2‚¢6VÆbåöÆöu÷7W÷'FVEö†æE÷&W7öç6W2‚¢6VÆbæÆör€¢'&–÷&—G•öw&çFVB"À¢Æ–W#×6VÆbçÆ–W'5¶†öÆFW%ÒææÖRÀ¢Æ–W%ö–æFWƒÖ†öÆFW"À¢&–÷&—G•öWö6ƒÖWö6‚À¢ ¢FVb÷v—FæW75÷Vç7W÷'FVE÷7F6µ÷&W7öç6W2‡6VÆb’ÓâæöæS ¢""$g&VW¦R6÷VçFW'7VÆÂ÷÷'GVæ—G’öæÇ’v†Vâ7VÆÂÂ6&BÂæBÖæÆÂW†—7Bâ"" ¢–bæ÷B6VÆbç7F6²÷"æ÷B—6–ç7Fæ6R‡6VÆbç7F6µ²ÓÒÂ7F6´ö&¦V7B“ ¢&WGW&à¢F&vWBÒ6VÆbç7F6µ²ÓÐ¢f÷"Æ–W%ö–æFW‚ÂÆ–W"–âVçVÖW&FR‡6VÆbçÆ–W'2“ ¢–bÆ–W%ö–æFW‚ÓÒF&vWBæ6öçG&öÆÆW# ¢6öçF–çVP¢f÷"6&B–âGWÆR‡Æ–W"æ†æB“ ¢w&÷WVC¢F–7E·7G"ÂÆ—7E·7G%ÕÒÒ·Ð¢f÷"g&vÖVçBÂ&V6öâ–â6VÆbæ–çFW'&WFW"çVç7W÷'FVEög&vÖVçG2†6&Bæ6&B“ ¢w&÷WVBç6WFFVfVÇB†g&vÖVçBÂµÒ’æVæB‡&V6öâ¢f÷"g&vÖVçBÂ&V6öç2–âw&÷WVBæ—FV×2‚“ ¢ÖF6‚Ò&RæÖF6‚€¢"%ä6÷VçFW"F&vWBƒõÆæöæ7&VGW&Sææöæ7&VGW&R“÷7VÆÅÂâ"Âg&vÖVç@¢¢–b€¢ÖF6‚—2æöæP¢÷"æ÷B6VÆbæ6åöff÷&B‡Æ–W%ö–æFW‚Â6&B¢÷"†ÖF6‚æw&÷W‚&æöæ7&VGW&R"’æBF&vWBæ6&Bæ—5ö7&VGW&R¢“ ¢6öçF–çVP¢6VÆbå÷&Vv—7FW%÷6VÖçF–5öö67W'&Væ6R€¢6&BÂÆ–W%ö–æFW‚Âg&vÖVçBÂGWÆR‡6÷'FVB‡6WB‡&V6öç2’’¢¢6VÆbåöæWuö÷÷'GVæ—G•ö6öçFW‡B€¢'7F6µ÷&W7öç6R"À¢6öçG&öÆÆW#×Æ–W%ö–æFW‚À¢6÷W&6Uö–CÖ6&Bæö&¦V7Eö–BÀ¢7V&¦V7Eö–G3Ò‡F&vWBæö&¦V7Eö–BÂ’À¢f7G3Ò€¢‚'&W7öç6Uö6÷7B"Â6&BæÖæö6÷7B’À¢‚'F&vWEö—5ö7&VGW&R"Â7G"‡F&vWBæ6&Bæ—5ö7&VGW&R’æÆ÷vW"‚’’À¢’À¢7F6µöö&¦V7Eö–C×F&vWBæö&¦V7Eö–BÀ¢ ¢FVbW†V7WFUöÖ–åö7F–öâ‡6VÆbÂ÷F–öã¢7F–öä÷F–öâ’Óâ&ööÃ ¢""%&WfÆ–FFRæBW†V7WFRöæRVæv–æRÖ—77VVBÖ–â×†6R÷F–öââ"" ¢–b÷F–öâæ÷B–â6VÆbæÆVvÅöÖ–åö7F–öç2†÷F–öâçÆ–W%ö–æFW‚“ ¢&—6RfÇVTW'&÷"‚&7F–öâ—2æ÷B7W'&VçFÇ’ÆVvÂ"¢–b÷F–öâæ¶–æB—27F–öä¶–æBå53 ¢&WGW&âG'VP¢ö&¢Ò6VÆbåöö&¦V7G2ævWB†÷F–öâæö&¦V7Eö–B÷"""¢–b÷F–öâæ¶–æB—27F–öä¶–æBåÄ•ôÄäC ¢–bæ÷B—6–ç7Fæ6R†ö&¢Â6&Dö&¦V7B“ ¢&—6RfÇVTW'&÷"‚&ÆæB÷F–öâFöW2æ÷B–FVçF–g’6&Bö&¦V7B"¢&WGW&â6VÆbçÆ•öÆæB€¢÷F–öâçÆ–W%ö–æFW‚Âö&¢Âg&öÕ÷&†VÃ×6VÆbæ—5öWF†÷&—FF—fR†ö&¢Â&W†–ÆR"¢¢–b÷F–öâæ¶–æB—27F–öä¶–æBä45C ¢–bæ÷B—6–ç7Fæ6R†ö&¢Â6&Dö&¦V7B“ ¢&—6RfÇVTW'&÷"‚&67B÷F–öâFöW2æ÷B–FVçF–g’6&Bö&¦V7B"¢F&vWBÒ6VÆbåöö&¦V7G2ævWB†÷F–öâçF&vWEö–B÷"""¢6÷W&6U÷F&vWBÒ6VÆbåöö&¦V7G2ævWB†÷F–öâæ6†ö–6Uö–G5³Ò’–b÷F–öâæ6†ö–6Uö–G2VÇ6RæöæP¢&V7W'6–öå÷F&vWG2ÒGWÆR‡6VÆbåöö&¦V7G2ævWB†—FVÒ’f÷"—FVÒ–â÷F–öâæ6†ö–6Uö–G2¢–bF&vWB—2æ÷BæöæRæBæ÷B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB“ ¢&—6RfÇVTW'&÷"‚'F&vWB÷F–öâFöW2æ÷B–FVçF–g’W&ÖæVçB"¢–bö&¢ææÖR–â²%6¶FV&ö&B"Â%7–7’öFÖVÂ—§¦'Ó ¢6VÆbæÆör€¢'WF–Æ—G•ö'F–f7Eö7F–öå÷6VÆV7FVB"À¢Æ–W#×6VÆbçÆ–W'5¶÷F–öâçÆ–W%ö–æFW…ÒææÖRÀ¢6&CÖö&¢ææÖRÀ¢ö&¦V7Eö–CÖö&¢æö&¦V7Eö–BÀ¢¢–b6VÆbæ—5öWF†÷&—FF—fR†ö&¢Â&W†–ÆR"“ ¢7VÆÂÒ6VÆbæææ÷Væ6U÷7VÆÂ€¢÷F–öâçÆ–W%ö–æFW‚À¢ö&¢À¢F&vWBÀ¢67Eög&öÕöW†–ÆSÕG'VRÀ¢…÷fÇVSÖ÷F–öâç…÷fÇVRÀ¢67&–f–6Uö6÷7CÒ€¢6VÆbåöö&¦V7G2ævWB†÷F–öâæ6÷7Eöö&¦V7Eö–B÷"""¢–b÷F–öâæ6÷7Eöö&¦V7Eö–B—2æ÷BæöæP¢VÇ6RæöæP¢’À¢6÷W&6U÷F&vWC×6÷W&6U÷F&vWB–b—6–ç7Fæ6R‡6÷W&6U÷F&vWBÂW&ÖæVçB’VÇ6RæöæRÀ¢&V7W'6–öå÷F&vWG3×&V7W'6–öå÷F&vWG2À¢ÖöFUög&vÖVçCÒ€¢÷F–öâæ÷&6ÆUög&vÖVç@¢–b6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†ö&¢æ6&B’æ¶–æ@¢—267D¶–æBäÔôDÅõDô´Tåôõ%ô5$TEU$UõTÕ ¢VÇ6RæöæP¢’À¢¢–b7VÆÂ—2æöæS ¢&—6RfÇVTW'&÷"‚&Æ–æ¶VBW†–ÆR7VÆÂ&V6ÖR–ÆÆVvÂ"¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‡&–÷&—G•÷Æ–W#Ö÷F–öâçÆ–W%ö–æFW‚¢&WGW&âG'VP¢–b6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†ö&¢æ6&B’æ¶–æB–â°¢67D¶–æBä´”4´TEô5$TEU$UõBÀ¢67D¶–æBåDõô4$Eõ4TÄT5D”ôâÀ¢67D¶–æBåDõô5$TEU$Uõ4TÄT5D”ôâÀ¢67D¶–æBäÄ”%$%•õ4T$4…õDõô„äBÀ¢67D¶–æBäõD”ôäÅô„äEõ$U4UBÀ¢67D¶–æBäu$dU”$Eõ$T5U%4”ôâÀ¢67D¶–æBä4ôäD•D”ôäÅõ4äTµõDô´Tå2À¢67D¶–æBäõD”ôäÅôDU5E$õ•ôäEô5$TDRÀ¢67D¶–æBä4ôäD•D”ôäÅôDU5E$õ•ôäEô5$TDRÀ¢67D¶–æBä5$TEU$UõõtU%ôDÔtRÀ¢67D¶–æBäÔôDÅõDô´Tåôõ%ô5$TEU$UõTÕÀ¢67D¶–æBåD$tUDTEô4õTåDU%ô´U•tõ$Eôu$åBÀ¢67D¶–æBåDTÕõ$%•ôDTD…õ$UEU$åôu$åBÀ¢67D¶–æBåDTÕõ$%•õE•Uô$4UõEôE$rÀ¢67D¶–æBåD$tUDTEôÄ”%$%•õ$UEU$åôäEõDô´TâÀ¢Ó ¢6÷7BÒ6VÆbåöö&¦V7G2ævWB†÷F–öâæ6÷7Eöö&¦V7Eö–B÷"""¢7VÆÂÒ6VÆbæææ÷Væ6U÷7VÆÂ€¢÷F–öâçÆ–W%ö–æFW‚À¢ö&¢À¢F&vWBÀ¢67&–f–6Uö6÷7CÖ6÷7B–b—6–ç7Fæ6R†6÷7BÂW&ÖæVçB’VÇ6RæöæRÀ¢6÷W&6U÷F&vWC×6÷W&6U÷F&vWB–b—6–ç7Fæ6R‡6÷W&6U÷F&vWBÂW&ÖæVçB’VÇ6RæöæRÀ¢&V7W'6–öå÷F&vWG3×&V7W'6–öå÷F&vWG2À¢ÖöFUög&vÖVçCÒ€¢÷F–öâæ÷&6ÆUög&vÖVç@¢–b6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†ö&¢æ6&B’æ¶–æ@¢—267D¶–æBäÔôDÅõDô´Tåôõ%ô5$TEU$UõTÕ ¢VÇ6RæöæP¢’À¢¢–b7VÆÂ—2æöæS ¢&—6RfÇVTW'&÷"‚'6†&VB7VÆÂ&V6ÖR–ÆÆVvÂBææ÷Væ6VÖVçB"¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‡&–÷&—G•÷Æ–W#Ö÷F–öâçÆ–W%ö–æFW‚¢&WGW&âG'VP¢&WGW&â6VÆbæ67B€¢÷F–öâçÆ–W%ö–æFW‚À¢ö&¢À¢F&vWBÀ¢67&–f–6Uö6÷7CÒ€¢6VÆbåöö&¦V7G2ævWB†÷F–öâæ6÷7Eöö&¦V7Eö–B÷"""¢–b÷F–öâæ6÷7Eöö&¦V7Eö–B—2æ÷BæöæP¢VÇ6RæöæP¢’À¢67Eög&öÕöw&fW–&CÒ€¢—6–ç7Fæ6R†ö&¢Â6&Dö&¦V7B¢æB÷F–öâæ÷&6ÆUög&vÖVçB—2æ÷BæöæP¢æB6VÆbæ—5öWF†÷&—FF—fR†ö&¢Â&w&fW–&B"¢’À¢…÷fÇVSÖ÷F–öâç…÷fÇVRÀ¢¢–b÷F–öâæ¶–æB—27F–öä¶–æBä5D•dDUô$”Ä•E“ ¢–b—6–ç7Fæ6R†ö&¢Â6&Dö&¦V7B’æB÷F–öâæ÷&6ÆUög&vÖVçB—2æ÷BæöæS ¢&WGW&â€¢6VÆbæææ÷Væ6Uö†æEö7F—fFVEö&–Æ—G’€¢÷F–öâçÆ–W%ö–æFW‚Âö&¢Â÷F–öâæ÷&6ÆUög&vÖVç@¢¢—2æ÷BæöæP¢¢–bæ÷B—6–ç7Fæ6R†ö&¢ÂW&ÖæVçB“ ¢&—6RfÇVTW'&÷"‚&7F—fF–öâ÷F–öâFöW2æ÷B–FVçF–g’W&ÖæVçB"¢–b÷F–öâæ÷&6ÆUög&vÖVçB—2æöæS ¢&—6RfÇVTW'&÷"‚&7F—fF–öâ÷F–öâÆ6·2â÷&6ÆRg&vÖVçB"¢F&vWEö–G2Ò‚’–b÷F–öâçF&vWEö–B—2æöæRVÇ6R†÷F–öâçF&vWEö–BÂ¢&WGW&â€¢6VÆbæææ÷Væ6Uö7F—fFVEö&–Æ—G’€¢÷F–öâçÆ–W%ö–æFW‚À¢ö&¢À¢÷F–öâæ÷&6ÆUög&vÖVçBÀ¢F&vWEö–G3×F&vWEö–G2À¢6†ö–6Uö–G3Ö÷F–öâæ6†ö–6Uö–G2À¢÷F†W%÷67&–f–6Uö–CÖ÷F–öâæ6÷7Eöö&¦V7Eö–BÀ¢¢—2æ÷BæöæP¢¢&—6RfÇVTW'&÷"‚'Vç7W÷'FVBÖ–â7F–öâ¶–æB" ¢FVbÆVvÅöGF6µö÷F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢–bÆ–W%ö–æFW‚Ò6VÆbæ7F—fU÷Æ–W"÷"6VÆbç7FW—2æ÷BGW&å7FWäDT4Ä$UôED4´U%3 ¢&WGW&â‚¢GF6¶W%ö–G2ÒGWÆR†ö&¢æö&¦V7Eö–Bf÷"ö&¢–â6VÆbæÆVvÅöGF6¶W'2‡Æ–W%ö–æFW‚’¢÷F–öç2Ò´7F–öä÷F–öâ„7F–öä¶–æBäDT4Ä$UôED4´U%2ÂÆ–W%ö–æFW‚•Ð¢–bGF6¶W%ö–G3 ¢÷F–öç2æVæB€¢7F–öä÷F–öâ€¢7F–öä¶–æBäDT4Ä$UôED4´U%2À¢Æ–W%ö–æFW‚À¢GF6¶W%ö–G3ÖGF6¶W%ö–G2À¢¢¢&WGW&âGWÆR†÷F–öç2 ¢FVbÆVvÅö&Æö6µö÷F–öç2€¢6VÆbÂGF6³¢7F–öä÷F–öâÂFVfVæFW%ö–æFWƒ¢–ç@¢’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢–b6VÆbç7FW—2æ÷BGW&å7FWäDT4Ä$Uô$Äô4´U%3 ¢&WGW&â‚¢–bGF6²æGF6¶W%ö–G2Ò6VÆbåö6öÖ&EöGF6¶W'3 ¢&WGW&â‚¢GF6¶W'2Ò·6VÆbåöö&¦V7G5¶ö&¦V7Eö–EÒf÷"ö&¦V7Eö–B–âGF6²æGF6¶W%ö–G5Ð¢–bæ÷BÆÂ†—6–ç7Fæ6R†ö&¢ÂW&ÖæVçB’f÷"ö&¢–âGF6¶W'2“ ¢&WGW&â‚¢f–Æ&ÆRÒ°¢f÷"–â6VÆbçÆ–W'5¶FVfVæFW%ö–æFW…Òæ&GFÆVf–VÆB–bæ—5ö7&VGW&RæBæ÷BçFV@¢Ð¢÷F–öç2Ò´7F–öä÷F–öâ„7F–öä¶–æBäDT4Ä$Uô$Äô4´U%2ÂFVfVæFW%ö–æFW‚•Ð ¢FVbf—6—B†–æFW‚Â&VÖ–æ–ærÂ76–væÖVçB“ ¢–b–æFW‚ÓÒÆVâ†GF6¶W'2“ ¢–b76–væÖVçC ¢÷F–öç2æVæB€¢7F–öä÷F–öâ„7F–öä¶–æBäDT4Ä$Uô$Äô4´U%2ÂFVfVæFW%ö–æFW‚Â&Æö6·3Ö76–væÖVçB¢¢&WGW&à¢GF6¶W"ÒGF6¶W'5¶–æFW…Ð¢f÷"6÷VçB–â&ævR†ÆVâ‡&VÖ–æ–ær’²“ ¢f÷"w&÷W–âW&×WFF–öç2‡&VÖ–æ–ærÂ6÷VçB“ ¢&Æö6·2ÒGWÆR‚†GF6¶W"æö&¦V7Eö–BÂ&Æö6¶W"æö&¦V7Eö–B’f÷"&Æö6¶W"–âw&÷W¢–bæ÷B6VÆbå÷fÆ–Eö&Æö6µö76–væÖVçB…¶GF6¶W%ÒÂ&Æö6·2ÂFVfVæFW%ö–æFW‚“ ¢6öçF–çVP¢W6VBÒ¶&Æö6¶W"æö&¦V7Eö–Bf÷"&Æö6¶W"–âw&÷WÐ¢f—6—B€¢–æFW‚²À¢GWÆR†&Æö6¶W"f÷"&Æö6¶W"–â&VÖ–æ–ær–b&Æö6¶W"æö&¦V7Eö–Bæ÷B–âW6VB’À¢76–væÖVçB²&Æö6·2À¢ ¢2F†RöÆB6'FW6–â&öGV7BfÆ–FFVBöæÇ’BF†RÆVfW2â&VÖ÷f–ærW6V@¢2&Æö6¶W'2æB–ÆÆVvÂW"ÖGF6¶W"w&÷W2V&Ç’&W6W'fW2—G2W†7@¢27W'f—f–ær÷F–öâ÷&FW"Â–æ6ÇVF–ærF†R–Æ÷Bw2f—'7BÖÖ‚F–R'&V²à¢f—6—BƒÂGWÆR†f–Æ&ÆR’Â‚’¢&WV—&VBÒ°¢GF6¶W"æö&¦V7Eö–@¢f÷"GF6¶W"–âGF6¶W'0¢–bç’€¢6VÆbæ–çFW'&WFW"æ×W7Eö&Uö&Æö6¶VB†GF6¶W"æ6&BÂg&vÖVçB¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2†GF6¶W"ç'VÆW5ö6&B¢¢Ð¢–b&WV—&VC  ¢FVb66÷&R†÷F–öã¢7F–öä÷F–öâ’Óâ–çC ¢&WGW&âÆVâ‡&WV—&VBb¶GF6¶W%ö–Bf÷"GF6¶W%ö–BÂò–â÷F–öâæ&Æö6·7Ò ¢Ö†–×VÒÒÖ‚†Ö‡66÷&RÂ÷F–öç2’¢÷F–öç2Ò¶÷F–öâf÷"÷F–öâ–â÷F–öç2–b66÷&R†÷F–öâ’ÓÒÖ†–×VÕÐ¢&WGW&âGWÆR†÷F–öç2 ¢FVbö6Æ75öw&fW–&E÷6æVµ÷6÷W&6W2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB“ ¢""$7W'&VçFÇ’6öçG&öÆÆVBÂÆWfVÂ×F‡&VR6Æ72w&çG2v—F‚&÷F‚7FF–26ÆW6W2â"" ¢&WGW&âGWÆR€¢‡6÷W&6RÂw&çB¢f÷"6÷W&6R–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢–b6VÆbæ—5öWF†÷&—FF—fR‡6÷W&6RÂ&&GFÆVf–VÆB"¢æB6÷W&6Ræ6Æ75öÆWfVÂ—2æ÷BæöæP¢æB6÷W&6Ræ6Æ75öÆWfVÂãÒ0¢æB†w&çB£Ò6VÆbæ–çFW'&WFW"æ6Æ75öw&fW–&E÷6æV²‡6÷W&6Rç'VÆW5ö6&B’’—2æ÷BæöæP¢ ¢FVb÷6æVµ÷6VÖçF–72‡6VÆbÂ6&C¢6&Dö&¦V7BÂÆ–W%ö–æFWƒ¢–çB“ ¢–b6&Bç¦öæRÓÒ&w&fW–&B# ¢6÷W&6W2Ò6VÆbåö6Æ75öw&fW–&E÷6æVµ÷6÷W&6W2‡Æ–W%ö–æFW‚¢–bæ÷B6÷W&6W2÷"6&Bæ÷væW"ÒÆ–W%ö–æFW‚÷"æ÷B6&Bæ6&Bæ—5ö7&VGW&S ¢&WGW&â‚¢6÷W&6RÂw&çBÒ6÷W&6W5³Ð¢w&çFVBÒ6VÆbæ–çFW'&WFW"ç6æVµ÷6VÖçF–5ö6÷fW&vR‡6÷W&6Rç'VÆW5ö6&BÂw&çE³Ò¢76W'B€¢w&çFVB—2æ÷BæöæP¢æBw&çFVBæ6÷fW&vRægVÆÇ•÷7W÷'FV@¢æBw&çFVBç&öw&Òæw&çFVEö¶W—v÷&Eö&–Æ—G¢¢÷F–öç2Ò²†w&çE³ÒÂw&çFVBÂ6÷W&6Ræö&¦V7Eö–B•Ð¢÷F–öç2æW‡FVæB€¢†g&vÖVçBÂ6VÖçF–72Â6÷W&6Ræö&¦V7Eö–B¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2†6&Bæ6&B¢–b‡6VÖçF–72£Ò6VÆbæ–çFW'&WFW"ç6æVµ÷6VÖçF–5ö6÷fW&vR†6&Bæ6&BÂg&vÖVçB’¢—2æ÷BæöæP¢æB6VÖçF–72æ6÷fW&vRægVÆÇ•÷7W÷'FV@¢æB6VÖçF–72ç&öw&ÒæF—&V7Eö¶W—v÷&Eö&–Æ—G¢¢&WGW&âGWÆR†÷F–öç2¢&WGW&âGWÆR€¢†g&vÖVçBÂ6VÖçF–72ÂæöæR¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2†6&Bæ6&B¢–b‡6VÖçF–72£Ò6VÆbæ–çFW'&WFW"ç6æVµ÷6VÖçF–5ö6÷fW&vR†6&Bæ6&BÂg&vÖVçB’¢—2æ÷BæöæP¢æB6VÖçF–72æ6÷fW&vRægVÆÇ•÷7W÷'FV@¢æB6VÖçF–72ç&öw&ÒæF—&V7Eö¶W—v÷&Eö&–Æ—G¢ ¢FVb÷Væ&Æö6¶VEöGF6¶W'2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆUµW&ÖæVçBÂââåÓ ¢&Æö6¶VBÒ¶GF6¶W%ö–Bf÷"GF6¶W%ö–BÂö&Æö6¶W%ö–B–â6VÆbåö6öÖ&Eö&Æö6·7Ð¢&W7VÇC¢Æ—7EµW&ÖæVçEÒÒµÐ¢f÷"ö&¦V7Eö–B–â6VÆbåö6öÖ&EöGF6¶W'3 ¢GF6¶W"Ò6VÆbåöö&¦V7G2ævWB†ö&¦V7Eö–B¢–b€¢ö&¦V7Eö–Bæ÷B–â&Æö6¶V@¢æB—6–ç7Fæ6R†GF6¶W"ÂW&ÖæVçB¢æB6VÆbæ—5öWF†÷&—FF—fR†GF6¶W"Â&&GFÆVf–VÆB"¢æBGF6¶W"æ6öçG&öÆÆW"ÓÒÆ–W%ö–æFW€¢“ ¢&W7VÇBæVæB†GF6¶W"¢&WGW&âGWÆR‡&W7VÇB ¢FVb6æVµ÷–ÖVçE÷Æâ€¢6VÆbÀ¢Æ–W%ö–æFWƒ¢–çBÀ¢6&C¢6&Dö&¦V7BÀ¢GF6¶W#¢W&ÖæVçBÀ¢¢À¢÷&6ÆUög&vÖVçC¢7G"ÂæöæRÒæöæRÀ¢’Óâ6æVµ–ÖVçEÆâÂæöæS ¢""$'V–ÆBöæR–Ö×WF&ÆRf—†VBÖ6÷7B6æV²Æâv—F†÷WB×WFF–ærvÖR7FFRâ"" ¢–b€¢Æ–W%ö–æFW‚Ò6VÆbæ7F—fU÷Æ–W ¢÷"6VÆbç7FW—2æ÷BGW&å7FWäDT4Ä$Uô$Äô4´U%0¢÷"æ÷B6VÆbåö&Æö6¶W'5öFV6Æ&V@¢÷"€¢6VÆbç&–÷&—G•÷7FFR—2æ÷BæöæP¢æB€¢6VÆbç&–÷&—G•÷7FFRç&W6öÇWF–öå÷VæF–æp¢÷"6VÆbç&–÷&—G•÷7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFW€¢¢¢÷"‡6VÆbç7F6²æB6VÆbç&–÷&—G•÷7FFR—2æöæR¢÷"æ÷B€¢‡6VÆbæ—5öWF†÷&—FF—fR†6&BÂ&†æB"’æB6&Bæ÷væW"ÓÒÆ–W%ö–æFW‚¢÷"6VÆbåöÆ–æ¶VE÷Æ•öw&çEöf÷"‡Æ–W%ö–æFW‚Â6&B’—2æ÷BæöæP¢÷"‡6VÆbæ—5öWF†÷&—FF—fR†6&BÂ&w&fW–&B"’æB6&Bæ÷væW"ÓÒÆ–W%ö–æFW‚¢¢÷"GF6¶W"æ÷B–â6VÆbå÷Væ&Æö6¶VEöGF6¶W'2‡Æ–W%ö–æFW‚¢“ ¢&WGW&âæöæP¢÷F–öç2Ò6VÆbå÷6æVµ÷6VÖçF–72†6&BÂÆ–W%ö–æFW‚¢6VÆV7FVE÷6VÖçF–72Ò€¢æW‡B‚†÷F–öâf÷"÷F–öâ–â÷F–öç2–b÷F–öå³ÒÓÒ÷&6ÆUög&vÖVçB’ÂæöæR¢–b÷&6ÆUög&vÖVçB—2æ÷BæöæP¢VÇ6R†÷F–öç5³Ò–b÷F–öç2VÇ6RæöæR¢¢–b6VÆV7FVE÷6VÖçF–72—2æöæS ¢&WGW&âæöæP¢g&vÖVçBÂ6VÖçF–72ÂW&Ö—76–öå÷6÷W&6Uö–BÒ6VÆV7FVE÷6VÖçF–70¢&öw&Ó¢6æVµ&öw&ÒÒ6VÖçF–72ç&öw&Ð¢76W'B&öw&ÒæÖæö6÷7B—2æ÷BæöæP¢&WV—&VÖVçBÒ6VÆbæ67F–æu÷&WV—&VÖVçB‡Æ–W%ö–æFW‚Â6&BÂÇFW&æF—fS×&öw&ÒæÖæö6÷7B¢–b&WV—&VÖVçB—2æöæS ¢&WGW&âæöæP¢f–Æ&ÆRÒ°¢W&ÖæVç@¢f÷"W&ÖæVçB–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢–bW&ÖæVçBæ6&Bæ—5öÆæBæBæ÷BW&ÖæVçBçFVBæBW&ÖæVçB—2æ÷BGF6¶W ¢Ð¢6VÆV7FVBÒ6VÆbå÷ÆåöÖæ÷v—F…öfÆöF–ær€¢Æ–W%ö–æFW‚À¢&WV—&VÖVçBÀ¢f–Æ&ÆRÀ¢&'F–f7E÷7VÆÂ ¢–b$'F–f7B"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢VÇ6R&÷F†W%÷7VÆÂ"À¢¢–b6VÆV7FVB—2æöæS ¢&WGW&âæöæP¢öfÆöF–æuö6öÆ÷'2ÂfÆöF–æuöWfVçEö–G2Â6†÷6VâÒ6VÆV7FV@¢&WGW&â6æVµ–ÖVçEÆâ€¢Æ–W%ö–æFW‚À¢6&Bæö&¦V7Eö–BÀ¢GF6¶W"æö&¦V7Eö–BÀ¢&WV—&VÖVçBÀ¢GWÆR‡6÷W&6Ræö&¦V7Eö–Bf÷"6÷W&6R–â6†÷6Vâ’À¢ÒÆ–W%ö–æFW‚À¢g&vÖVçBÀ¢fÆöF–æuöWfVçEö–G2À¢6&Bç¦öæRÀ¢W&Ö—76–öå÷6÷W&6Uö–BÀ¢ ¢FVbÆVvÅ÷6æVµö7F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢""$vVæW&FR&W&W6VçFVB6æV²ææ÷Væ6VÖVçG2gFW"&Æö6¶W'2&RFV6Æ&VBâ"" ¢–b€¢Æ–W%ö–æFW‚Ò6VÆbæ7F—fU÷Æ–W ¢÷"6VÆbç7FW—2æ÷BGW&å7FWäDT4Ä$Uô$Äô4´U%0¢÷"æ÷B6VÆbåö&Æö6¶W'5öFV6Æ&V@¢÷"€¢6VÆbç&–÷&—G•÷7FFR—2æ÷BæöæP¢æB€¢6VÆbç&–÷&—G•÷7FFRç&W6öÇWF–öå÷VæF–æp¢÷"6VÆbç&–÷&—G•÷7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFW€¢¢¢÷"‡6VÆbç7F6²æB6VÆbç&–÷&—G•÷7FFR—2æöæR¢“ ¢&WGW&â‚¢÷F–öç3¢Æ—7E´7F–öä÷F–öåÒÒµÐ¢Æ–&ÆUöW†–ÆRÒGWÆR€¢6&@¢f÷"÷væW"–â6VÆbçÆ–W'0¢f÷"6&B–â÷væW"æW†–ÆP¢–b6VÆbåöÆ–æ¶VE÷Æ•öw&çEöf÷"‡Æ–W%ö–æFW‚Â6&B’—2æ÷BæöæP¢¢Æ–&ÆUöw&fW–&BÒ€¢GWÆR‡6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæw&fW–&B¢–b6VÆbåö6Æ75öw&fW–&E÷6æVµ÷6÷W&6W2‡Æ–W%ö–æFW‚¢VÇ6R‚¢¢f÷"6&B–â‚§6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ†æBÂ§Æ–&ÆUöW†–ÆRÂ§Æ–&ÆUöw&fW–&B“ ¢f÷"g&vÖVçBÂ÷6VÖçF–72Â÷6÷W&6Uö–B–â6VÆbå÷6æVµ÷6VÖçF–72†6&BÂÆ–W%ö–æFW‚“ ¢f÷"GF6¶W"–â6VÆbå÷Væ&Æö6¶VEöGF6¶W'2‡Æ–W%ö–æFW‚“ ¢–b€¢6VÆbç6æVµ÷–ÖVçE÷Æâ€¢Æ–W%ö–æFW‚Â6&BÂGF6¶W"Â÷&6ÆUög&vÖVçCÖg&vÖVç@¢¢—2æöæP¢“ ¢6öçF–çVP¢&V7W'6–öâÒ6VÆbæ–çFW'&WFW"æw&fW–&E÷&V7W'6–öå÷&öw&Ò†6&Bæ6&B¢–b&V7W'6–öâ—2æ÷BæöæS ¢÷F–öç2æW‡FVæB€¢7F–öä÷F–öâ€¢7F–öä¶–æBä45BÀ¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–CÖ6&Bæö&¦V7Eö–BÀ¢6÷7Eöö&¦V7Eö–CÖGF6¶W"æö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢6†ö–6Uö–G3×GWÆR‡F&vWBæö&¦V7Eö–Bf÷"F&vWB–âF&vWG2’À¢&–÷&—G•öWö6ƒÒ€¢6VÆbç&–÷&—G•÷7FFRæWö6‚–b6VÆbç&–÷&—G•÷7FFRVÇ6RæöæP¢’À¢¢f÷"F&vWG2–â6VÆbåöw&fW–&E÷&V7W'6–öå÷F&vWG2‡Æ–W%ö–æFW‚Â6&B¢¢6öçF–çVP¢&VÖ÷fÂÒ6VÆbæ–çFW'&WFW"çF&vWFVE÷&VÖ÷fÅ÷&öw&Ò†6&Bæ6&B¢F&vWG2Ò€¢GWÆR€¢F&vW@¢f÷"6–FR–â6VÆbçÆ–W'0¢f÷"F&vWB–â6–FRæ&GFÆVf–VÆ@¢–b6VÆbåöÆVvÅ÷F&vWFVE÷&VÖ÷fÅ÷F&vWB‡F&vWBÂÆ–W%ö–æFW‚Â&VÖ÷fÂ¢¢–b&VÖ÷fÂ—2æ÷BæöæP¢VÇ6R„æöæRÂ¢¢÷F–öç2æW‡FVæB€¢7F–öä÷F–öâ€¢7F–öä¶–æBä45BÀ¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–CÖ6&Bæö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–B–bF&vWB—2æ÷BæöæRVÇ6RæöæRÀ¢6÷7Eöö&¦V7Eö–CÖGF6¶W"æö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢&–÷&—G•öWö6ƒÒ€¢6VÆbç&–÷&—G•÷7FFRæWö6‚–b6VÆbç&–÷&—G•÷7FFRVÇ6RæöæP¢’À¢¢f÷"F&vWB–âF&vWG0¢¢–b6VÆbç&–÷&—G•÷7FFR—2æöæS ¢÷F–öç2æVæB„7F–öä÷F–öâ„7F–öä¶–æBå52ÂÆ–W%ö–æFW‚’¢&WGW&âGWÆR†÷F–öç2 ¢FVbW†V7WFUöGF6µö7F–öâ‡6VÆbÂGF6³¢7F–öä÷F–öâ’ÓâæöæS ¢""%&WfÆ–FFRæBW†V7WFRF†RFV6Æ&RÖGF6¶W'2GW&âÖ&6VB7F–öââ"" ¢–bGF6²æ÷B–â6VÆbæÆVvÅöGF6µö÷F–öç2†GF6²çÆ–W%ö–æFW‚“ ¢&—6RfÇVTW'&÷"‚&GF6²÷F–öâ—2æ÷B7W'&VçFÇ’ÆVvÂ"¢GF6¶W'2Ò·6VÆbåöö&¦V7G5¶ö&¦V7Eö–EÒf÷"ö&¦V7Eö–B–âGF6²æGF6¶W%ö–G5Ð¢–bæ÷BÆÂ†—6–ç7Fæ6R†ö&¢ÂW&ÖæVçB’f÷"ö&¢–âGF6¶W'2“ ¢&—6RfÇVTW'&÷"‚&6öÖ&B÷F–öâ&VfW&Væ6W2æöçW&ÖæVçB"¢f÷"GF6¶W"–âGF6¶W'3 ¢–bæ÷B6VÆbåö†5ö¶W—v÷&B†GF6¶W"Â%f–v–Ææ6R"“ ¢GF6¶W"çFVBÒG'VR2G—S¢–væ÷&U·Væ–öâÖGG%Ð¢6VÆbåö6öÖ&EöGF6¶W'2ÒGF6²æGF6¶W%ö–G0¢6VÆbåöGF6¶W'5öFV6Æ&VBÒG'VP¢6VÆbæÆör‚&GF6¶W'5öFV6Æ&VB"ÂGF6¶W'3ÖÆ—7B†GF6²æGF6¶W%ö–G2’¢f÷"GF6¶W"–âGF6¶W'3 ¢f÷"6÷W&6Uö–BÂg&vÖVçB–â6VÆbå÷7FF–5÷7V'G—Uö¶W—v÷&E÷6÷W&6W2†GF6¶W"Â&ÖVæ6R"“ ¢6VÆbæÆör€¢'7FF–5÷7V'G—Uö¶W—v÷&E÷W6VB"À¢GF6¶W%ö–CÖGF6¶W"æö&¦V7Eö–BÀ¢6÷W&6Uö–C×6÷W&6Uö–BÀ¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢¶W—v÷&CÒ&ÖVæ6R"À¢GF6¶W%ö6öçG&öÆÆW#ÖGF6¶W"æ6öçG&öÆÆW"À¢¢6VÆbç&W6öÇfUöGF6µ÷EöVffV7G2†GF6¶W'2’2G—S¢–væ÷&U¶&r×G—UÐ¢–b6VÆbç&–÷&—G•÷7FFR—2æöæS ¢6VÆbçG&ç6—F–öå÷Fò…GW&å7FWäDT4Ä$Uô$Äô4´U%2 ¢FVbW†V7WFUö&Æö6µö7F–öâ‡6VÆbÂ&Æö6·3¢7F–öä÷F–öâ’ÓâæöæS ¢""%&WfÆ–FFRæBW†V7WFRF†RFV6Æ&RÖ&Æö6¶W'2GW&âÖ&6VB7F–öââ"" ¢GF6²Ò7F–öä÷F–öâ€¢7F–öä¶–æBäDT4Ä$UôED4´U%2À¢6VÆbæ7F—fU÷Æ–W"À¢GF6¶W%ö–G3×6VÆbåö6öÖ&EöGF6¶W'2À¢¢FVfVæFW"ÒÒ6VÆbæ7F—fU÷Æ–W ¢–b&Æö6·2æ÷B–â6VÆbæÆVvÅö&Æö6µö÷F–öç2†GF6²ÂFVfVæFW"“ ¢&—6RfÇVTW'&÷"‚&&Æö6²÷F–öâ—2æ÷B7W'&VçFÇ’ÆVvÂ"¢GF6¶W'2Ò·6VÆbåöö&¦V7G5¶ö&¦V7Eö–EÒf÷"ö&¦V7Eö–B–â6VÆbåö6öÖ&EöGF6¶W'5Ð¢–bæ÷BÆÂ†—6–ç7Fæ6R†ö&¢ÂW&ÖæVçB’f÷"ö&¢–âGF6¶W'2“ ¢&—6RfÇVTW'&÷"‚&6öÖ&B7FFR&VfW&Væ6W2æöçW&ÖæVçBGF6¶W""¢–b&Æö6·2æ&Æö6·2æBæ÷B6VÆbå÷fÆ–Eö&Æö6µö76–væÖVçB†GF6¶W'2Â&Æö6·2æ&Æö6·2ÂFVfVæFW"“ ¢&—6RfÇVTW'&÷"‚&&Æö6²÷F–öâ&V6ÖR7FÆR÷"–ÆÆVvÂ"¢6VÆbåö6öÖ&Eö&Æö6·2Ò&Æö6·2æ&Æö6·0¢6VÆbåö&Æö6¶W'5öFV6Æ&VBÒG'VP¢6VÆbæÆör‚&&Æö6¶W'5öFV6Æ&VB"Â&Æö6·3Õ¶Æ—7B‡—"’f÷"—"–â&Æö6·2æ&Æö6·5Ò¢f÷"GF6¶W"–âGF6¶W'3 ¢f÷"6÷W&6Uö–BÂg&vÖVçB–â6VÆbå÷6–ævÆUö&Æö6µöÆ–Ö—E÷6÷W&6W2†GF6¶W"“ ¢6VÆbæÆör€¢'6–ævÆUö&Æö6µöÆ–Ö—EöÆ–VB"À¢GF6¶W%ö–CÖGF6¶W"æö&¦V7Eö–BÀ¢6÷W&6Uö–C×6÷W&6Uö–BÀ¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢&Æö6¶W'3×7VÒ†–BÓÒGF6¶W"æö&¦V7Eö–Bf÷"–BÂö&–B–â&Æö6·2æ&Æö6·2’À¢GF6¶W%ö6öçG&öÆÆW#ÖGF6¶W"æ6öçG&öÆÆW"À¢¢–b&Æö6·2æ&Æö6·3 ¢WfVçBÒ6VÆbåöæWu÷'VÆW5öWfVçB€¢'VÆW4WfVçD¶–æBä$Äô4´U%5ôDT4Ä$TBÀ¢FVfVæFW"À¢GWÆR†&Æö6¶W%ö–Bf÷"òÂ&Æö6¶W%ö–B–â&Æö6·2æ&Æö6·2’À¢¢f÷"&Æö6¶W%ö–B–âWfVçBç7V&¦V7Eö–G3 ¢6÷W&6RÒ6VÆbåöö&¦V7G5¶&Æö6¶W%ö–EÐ¢76W'B—6–ç7Fæ6R‡6÷W&6RÂW&ÖæVçB¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡6÷W&6Rç'VÆW5ö6&B“ ¢–b6VÆbæ–çFW'&WFW"æ6öÖ&EöF—66&Eö÷%÷67&–f–6R‡6÷W&6Ræ6&BÂg&vÖVçB“ ¢6VÆbåöVçVWVU÷G&–vvW"€¢WfVçBÂ6÷W&6RÂg&vÖVçBÂG&–vvW$VffV7Bä4ôÔ$EôD•44$Eôõ%õ45$”d”4P¢¢6VÆbå÷WE÷VæF–æu÷G&–vvW'5ööå÷7F6²‚¢6VÆbåöG&–å÷G&–vvW&VEö&–Æ—F–W2‚¢–b6VÆbç7F6²÷"6VÆbç&–÷&—G•÷7FFR—2æ÷BæöæS ¢&WGW&à¢–bç’€¢6VÆbæ–çFW'&WFW"æ¶–6¶VEö7&VGW&U÷E÷&öw&Ò†6&Bæ6&B’—2æ÷BæöæP¢æB6VÆbåö¶–6¶VEö7&VGW&U÷Eö÷F–öç2‡Æ–W%ö–æFW‚Â6&B¢f÷"Æ–W%ö–æFW‚ÂÆ–W"–âVçVÖW&FR‡6VÆbçÆ–W'2¢f÷"6&B–âÆ–W"æ†æ@¢“ ¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r†ÆÆ÷uöV×G“ÕG'VR¢&WGW&à¢–bæ÷Bç’€¢÷F–öâæ¶–æB—27F–öä¶–æBä45@¢f÷"÷F–öâ–â6VÆbæÆVvÅ÷6æVµö7F–öç2‡6VÆbæ7F—fU÷Æ–W"¢“ ¢6VÆbçG&ç6—F–öå÷Fò…GW&å7FWä4ôÔ$EôDÔtR ¢FVbW†V7WFU÷6æVµö7F–öâ‡6VÆbÂ÷F–öã¢7F–öä÷F–öâ’Óâ&ööÃ ¢""%&WfÆ–FFRæBW†V7WFRöæRVæv–æRÖvVæW&FVB6æV²7F–öâ÷"FV6Æ–æRâ"" ¢–b÷F–öâæ÷B–â6VÆbæÆVvÅ÷6æVµö7F–öç2†÷F–öâçÆ–W%ö–æFW‚“ ¢&—6RfÇVTW'&÷"‚%6æV²7F–öâ—2æ÷B7W'&VçFÇ’ÆVvÂ"¢–b÷F–öâæ¶–æB—27F–öä¶–æBå53 ¢6VÆbçG&ç6—F–öå÷Fò…GW&å7FWä4ôÔ$EôDÔtR¢&WGW&âG'VP¢6&BÒ6VÆbåöö&¦V7G2ævWB†÷F–öâæö&¦V7Eö–B÷"""¢GF6¶W"Ò6VÆbåöö&¦V7G2ævWB†÷F–öâæ6÷7Eöö&¦V7Eö–B÷"""¢–bæ÷B—6–ç7Fæ6R†6&BÂ6&Dö&¦V7B’÷"æ÷B—6–ç7Fæ6R†GF6¶W"ÂW&ÖæVçB“ ¢&—6RfÇVTW'&÷"‚%6æV²÷F–öâ&VfW&Væ6W2â–çfÆ–B'VçF–ÖRö&¦V7B"¢ÆâÒ6VÆbç6æVµ÷–ÖVçE÷Æâ€¢÷F–öâçÆ–W%ö–æFW‚Â6&BÂGF6¶W"Â÷&6ÆUög&vÖVçCÖ÷F–öâæ÷&6ÆUög&vÖVç@¢¢–bÆâ—2æöæR÷"Æâæ÷&6ÆUög&vÖVçBÒ÷F–öâæ÷&6ÆUög&vÖVçC ¢&—6RfÇVTW'&÷"‚%6æV²÷F–öâ&V6ÖR7FÆR÷"–ÆÆVvÂ"¢F&vWBÒ6VÆbåöö&¦V7G2ævWB†÷F–öâçF&vWEö–B÷"""¢&V7W'6–öå÷F&vWG2ÒGWÆR‡6VÆbåöö&¦V7G2ævWB†ö&¦V7Eö–B’f÷"ö&¦V7Eö–B–â÷F–öâæ6†ö–6Uö–G2¢6VÆbåö6öÖÖ—E÷6æVµöææ÷Væ6VÖVçB€¢6&BÂGF6¶W"ÂÆâÂF&vWC×F&vWBÂ&V7W'6–öå÷F&vWG3×&V7W'6–öå÷F&vWG0¢¢&WGW&âG'VP ¢FVbWfÇVFVE÷7G&–¶Uö¶W—v÷&G2‡6VÆbÂW&ÖæVçC¢W&ÖæVçB’Óâg&÷¦Vç6WEµ7G&–¶T¶W—v÷&EÓ ¢""$WfÇVFRF†R&W&W6VçFVB&–çFVBæB7FF–26öÖ&B×7FW¶W—v÷&B6†&7FW&—7F–72â"" ¢–bæ÷B6VÆbæ—5öWF†÷&—FF—fR‡W&ÖæVçBÂ&&GFÆVf–VÆB"“ ¢&WGW&âg&÷¦Vç6WB‚¢¶W—v÷&G2Ò°¢¶W—v÷&@¢f÷"¶W—v÷&B–â7G&–¶T¶W—v÷&@¢–b¶W—v÷&BçfÇVRç&WÆ6R‚%ò"Â""’æ66VföÆB‚¢–â·fÇVRæ66VföÆB‚’f÷"fÇVR–âW&ÖæVçBç'VÆW5ö6&Bæ¶W—v÷&G7Ð¢Ð¢¶W—v÷&G2çWFFR€¢VffV7Bæ¶W—v÷&@¢f÷"VffV7B–âW&ÖæVçBæ7F—fU÷FV×÷&'•ö¶W—v÷&EöVffV7G0¢–b—6–ç7Fæ6R†VffV7Bæ¶W—v÷&BÂ7G&–¶T¶W—v÷&B¢¢¶W—v÷&G2çWFFR€¢¶W—v÷&@¢f÷"¶W—v÷&B–â7G&–¶T¶W—v÷&@¢–b¶W—v÷&BçfÇVRç&WÆ6R‚%ò"Â""’–â6VÆbåöWV—ÖVçEö¶W—v÷&G2‡W&ÖæVçB¢¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡W&ÖæVçBç'VÆW5ö6&B“ ¢6VÖçF–72Ò6VÆbæ–çFW'&WFW"ç7G&–¶U÷6VÖçF–5ö6÷fW&vR‡W&ÖæVçBæ6&BÂg&vÖVçB¢–b6VÖçF–72—2æöæR÷"æ÷B6VÖçF–72æ6÷fW&vRægVÆÇ•÷7W÷'FVC ¢6öçF–çVP¢–b6VÖçF–72ç&öw&ÒæÆ–6&–Æ—G’—27G&–¶TÆ–6&–Æ—G’å4TÄb÷"€¢6VÖçF–72ç&öw&ÒæÆ–6&–Æ—G’—27G&–¶TÆ–6&–Æ—G’å4TÄeôEU$”äuô4ôåE$ôÄÄU%õEU$à¢æBW&ÖæVçBæ6öçG&öÆÆW"ÓÒ6VÆbæ7F—fU÷Æ–W ¢“ ¢¶W—v÷&G2æFB‡6VÖçF–72ç&öw&Òæ¶W—v÷&B¢–bW&ÖæVçBæö&¦V7Eö–B–â6VÆbåö6öÖ&EöGF6¶W'3 ¢f÷"6÷W&6R–â6VÆbçÆ–W'5·W&ÖæVçBæ6öçG&öÆÆW%Òæ&GFÆVf–VÆC ¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡6÷W&6Rç'VÆW5ö6&B“ ¢6VÖçF–72Ò6VÆbæ–çFW'&WFW"ç7G&–¶U÷6VÖçF–5ö6÷fW&vR‡6÷W&6Ræ6&BÂg&vÖVçB¢–b€¢6VÖçF–72—2æ÷BæöæP¢æB6VÖçF–72æ6÷fW&vRægVÆÇ•÷7W÷'FV@¢æB6VÖçF–72ç&öw&ÒæÆ–6&–Æ—G¢—27G&–¶TÆ–6&–Æ—G’äED4´”äuô5$TEU$U5õ”õUô4ôåE$ôÀ¢æB€¢W&ÖæVçBæ&–Æ—G•öÆ÷75÷F–ÖW7F×—2æöæP¢÷"6÷W&6RæVçFW&VE÷F–ÖW7F×âW&ÖæVçBæ&–Æ—G•öÆ÷75÷F–ÖW7F× ¢¢“ ¢¶W—v÷&G2æFB‡6VÖçF–72ç&öw&Òæ¶W—v÷&B¢&WGW&âg&÷¦Vç6WB†¶W—v÷&G2 ¢FVbö6öÖ&E÷W&ÖæVçB‡6VÆbÂö&¦V7Eö–C¢7G"Â&öÆS¢7G"’ÓâW&ÖæVçC ¢ö&¢Ò6VÆbåöö&¦V7G2ævWB†ö&¦V7Eö–B¢–bæ÷B—6–ç7Fæ6R†ö&¢ÂW&ÖæVçB“ ¢&—6RfÇVTW'&÷"†b&6öÖ&B7FFR&VfW&Væ6W2f'&–6FVB÷"æöçW&ÖæVçB·&öÆWÒ"¢&WGW&âö&  ¢FVb÷7F'Eö6öÖ&EöFÖvU÷7FW€¢6VÆbÂ¶–æC¢6öÖ&DFÖvU7FW¶–æBÂ6WVVæ6S¢–çBÂF÷FÅ÷7FW3¢–ç@¢’ÓâæöæS ¢6VÆbåö6öÖ&EöFÖvU÷7FWö¶–æBÒ¶–æ@¢6VÆbåö6öÖ&EöFÖvU÷7FWöçVÖ&W"Ò6WVVæ6P¢6VÆbåö6öÖ&EöFÖvU÷F÷FÅ÷7FW2ÒF÷FÅ÷7FW0¢6VÆbåö6öÖ&EöFÖvU÷&W6öÇfVBÒfÇ6P¢6VÆbæÆör€¢&6öÖ&EöFÖvU÷7FW÷7F'FVB"À¢FÖvU÷7FWÖ¶–æBçfÇVRÀ¢6WVVæ6S×6WVVæ6RÀ¢F÷FÅ÷7FW3×F÷FÅ÷7FW2À¢ ¢FVbö&Vv–åö6öÖ&EöFÖvU÷7FW2‡6VÆb’ÓâæöæS ¢""$FWFW&Ö–æRF†R5"SãBöæRÒ÷"Gvò×7FW6öÖ&BÖFÖvR6WVVæ6Râ"" ¢6öÖ&FçEö–G2ÒGWÆR€¢F–7Bæg&öÖ¶W—2€¢6VÆbåö6öÖ&EöGF6¶W'0¢²GWÆR†&Æö6¶W%ö–Bf÷"öGF6¶W%ö–BÂ&Æö6¶W%ö–B–â6VÆbåö6öÖ&Eö&Æö6·2¢¢¢6öÖ&FçG2ÒGWÆR€¢6VÆbåö6öÖ&E÷W&ÖæVçB†ö&¦V7Eö–BÂ&6öÖ&FçB"’f÷"ö&¦V7Eö–B–â6öÖ&FçEö–G0¢¢&VÖ–æ–ærÒGWÆR€¢W&ÖæVçBf÷"W&ÖæVçB–â6öÖ&FçG2–b6VÆbæ—5öWF†÷&—FF—fR‡W&ÖæVçBÂ&&GFÆVf–VÆB"¢¢WfÇVFVBÒ°¢W&ÖæVçBæö&¦V7Eö–C¢6VÆbæWfÇVFVE÷7G&–¶Uö¶W—v÷&G2‡W&ÖæVçB¢f÷"W&ÖæVçB–â&VÖ–æ–æp¢Ð¢6VÆbåöf—'7EöFÖvU÷VÆ–f–VEö–G2ÒGWÆR€¢W&ÖæVçBæö&¦V7Eö–@¢f÷"W&ÖæVçB–â&VÖ–æ–æp¢–bWfÇVFVE·W&ÖæVçBæö&¦V7Eö–EÐ¢bµ7G&–¶T¶W—v÷&Bäd•%5Eõ5E$”´RÂ7G&–¶T¶W—v÷&BäDõT$ÄUõ5E$”´WÐ¢¢6VÆbåöf—'7EöF÷V&ÆU÷7G&–¶Uö–G2ÒGWÆR€¢W&ÖæVçBæö&¦V7Eö–@¢f÷"W&ÖæVçB–â&VÖ–æ–æp¢–b7G&–¶T¶W—v÷&BäDõT$ÄUõ5E$”´R–âWfÇVFVE·W&ÖæVçBæö&¦V7Eö–EÐ¢¢6VÆbå÷&VwVÆ%öFÖvUö–æ—F–Åö–G2ÒGWÆR€¢W&ÖæVçBæö&¦V7Eö–@¢f÷"W&ÖæVçB–â&VÖ–æ–æp¢–bæ÷BWfÇVFVE·W&ÖæVçBæö&¦V7Eö–EÐ¢bµ7G&–¶T¶W—v÷&Bäd•%5Eõ5E$”´RÂ7G&–¶T¶W—v÷&BäDõT$ÄUõ5E$”´WÐ¢¢–b6VÆbåöf—'7EöFÖvU÷VÆ–f–VEö–G3 ¢6VÆbå÷7F'Eö6öÖ&EöFÖvU÷7FW„6öÖ&DFÖvU7FW¶–æBäd•%5Eõ5E$”´RÂÂ"¢VÇ6S ¢6VÆbå÷7F'Eö6öÖ&EöFÖvU÷7FW„6öÖ&DFÖvU7FW¶–æBå$TuTÄ"ÂÂ ¢FVböFÖvU÷7FWöVÆ–v–&ÆUö–G2‡6VÆb’Óâ6WE·7G%Ó ¢–b6VÆbåö6öÖ&EöFÖvU÷7FWö¶–æB—26öÖ&DFÖvU7FW¶–æBäd•%5Eõ5E$”´S ¢&WGW&â6WB‡6VÆbåöf—'7EöFÖvU÷VÆ–f–VEö–G2¢–b6VÆbåö6öÖ&EöFÖvU÷7FWö¶–æB—2æ÷B6öÖ&DFÖvU7FW¶–æBå$TuTÄ# ¢&—6RfÇVTW'&÷"‚&6öÖ&BFÖvR7FW—2æ÷B7F—fR"¢7W'&VçEöF÷V&ÆRÒ°¢ö&¦V7Eö–@¢f÷"ö&¦V7Eö–B–â6VÆbåö6öÖ&EöGF6¶W'0¢²GWÆR†&Æö6¶W%ö–Bf÷"öGF6¶W%ö–BÂ&Æö6¶W%ö–B–â6VÆbåö6öÖ&Eö&Æö6·2¢–b—6–ç7Fæ6R‚†ö&¢£Ò6VÆbåöö&¦V7G2ævWB†ö&¦V7Eö–B’’ÂW&ÖæVçB¢æB6VÆbæ—5öWF†÷&—FF—fR†ö&¢Â&&GFÆVf–VÆB"¢æB7G&–¶T¶W—v÷&BäDõT$ÄUõ5E$”´R–â6VÆbæWfÇVFVE÷7G&–¶Uö¶W—v÷&G2†ö&¢¢Ð¢26öÖ&FçBWB–çFò6öÖ&BgFW"F†Rf—'7BFÖvR7FW&VvâF–Bæ÷@¢2FVÂf—'7B×7G&–¶RFÖvS²WfVâöæRv—F‚f—'7B7G&–¶R6âFVÂ†W&Rà¢–æ—F–ÂÒ6WB‡6VÆbåöf—'7EöFÖvU÷VÆ–f–VEö–G2’Â6WB‡6VÆbå÷&VwVÆ%öFÖvUö–æ—F–Åö–G2¢ÆFRÒ6WB‡6VÆbåö6öÖ&EöGF6¶W'2’Ò–æ—F–À¢&WGW&â6WB‡6VÆbå÷&VwVÆ%öFÖvUö–æ—F–Åö–G2’Â7W'&VçEöF÷V&ÆRÂÆFP ¢FVbö6öÖ&Eö76–væÖVçB€¢6VÆbÀ¢6÷W&6S¢W&ÖæVçBÀ¢¢À¢F&vWC¢W&ÖæVçBÂæöæRÒæöæRÀ¢F&vWE÷Æ–W#¢–çBÂæöæRÒæöæRÀ¢Ö÷VçC¢–çBÂæöæRÒæöæRÀ¢G&×ÆS¢&ööÂÒfÇ6RÀ¢ÆWF†Å÷&WV—&VC¢–çBÂæöæRÒæöæRÀ¢’Óâ6öÖ&DFÖvT76–væÖVçC ¢–b6VÆbåö6öÖ&EöFÖvU÷7FWö¶–æB—26öÖ&DFÖvU7FW¶–æBäd•%5Eõ5E$”´S ¢&öÆRÒ€¢&F÷V&ÆU÷7G&–¶Uöf—'7B ¢–b6÷W&6Ræö&¦V7Eö–B–â6VÆbåöf—'7EöF÷V&ÆU÷7G&–¶Uö–G0¢VÇ6R&f—'7E÷7G&–¶R ¢¢VÇ6S ¢&öÆRÒ€¢&F÷V&ÆU÷7G&–¶U÷6V6öæB ¢–b7G&–¶T¶W—v÷&BäDõT$ÄUõ5E$”´R–â6VÆbæWfÇVFVE÷7G&–¶Uö¶W—v÷&G2‡6÷W&6R¢VÇ6R'&VwVÆ" ¢¢&WGW&â6öÖ&DFÖvT76–væÖVçB€¢6÷W&6Ræö&¦V7Eö–BÀ¢æöæR–bF&vWB—2æöæRVÇ6RF&vWBæö&¦V7Eö–BÀ¢F&vWE÷Æ–W"À¢Ö‚ƒÂ6÷W&6Rç÷vW"’–bÖ÷VçB—2æöæRVÇ6RÖ÷VçBÀ¢&öÆRÀ¢G&×ÆRÀ¢ÆWF†Å÷&WV—&VBÀ¢ ¢FVbWfÇVFVE÷G&×ÆR‡6VÆbÂW&ÖæVçC¢W&ÖæVçB’Óâ&ööÃ ¢""$WfÇVFRöæÇ’WF†÷&—FF—fRÂgVÆÇ’7W÷'FVBG&×ÆR6†&7FW&—7F–72â"" ¢–bæ÷B6VÆbæ—5öWF†÷&—FF—fR‡W&ÖæVçBÂ&&GFÆVf–VÆB"“ ¢&WGW&âfÇ6P¢–b6VÆbåö†5ö¶W—v÷&B‡W&ÖæVçBÂ%G&×ÆR"“ ¢&WGW&âG'VP¢–b—6–ç7Fæ6R‡W&ÖæVçBæ6&BÂFö¶VäFVf–æ—F–öâ’æB'G&×ÆR"–â°¢¶W—v÷&Bæ66VföÆB‚’f÷"¶W—v÷&B–âW&ÖæVçBç'VÆW5ö6&Bæ¶W—v÷&G0¢Ó ¢&WGW&âG'VP¢&WGW&âç’€¢6VÖçF–72—2æ÷BæöæP¢æB6VÖçF–72æ6÷fW&vRç–ÆöEöW†V7WF&ÆP¢æB6VÖçF–72æ6÷fW&vRç&VçEöW†V7WF&ÆP¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡W&ÖæVçBç'VÆW5ö6&B¢–b‡6VÖçF–72£Ò6VÆbæ–çFW'&WFW"çG&×ÆU÷6VÖçF–5ö6÷fW&vR‡W&ÖæVçBæ6&BÂg&vÖVçB’¢—2æ÷BæöæP¢ ¢FVbWfÇVFVEöÆ–fVÆ–æ²‡6VÆbÂ6÷W&6S¢6&Dö&¦V7BÂ7F6´ö&¦V7BÂW&ÖæVçB’Óâ&ööÃ ¢""$WfÇVFRöæÇ’WF†÷&—FF—fR–çG&–ç6–2Æ–fVÆ–æ²öâF†RFÖvR6÷W&6Râ"" ¢–bæ÷B€¢6VÆbæ—5öWF†÷&—FF—fR‡6÷W&6RÂ&&GFÆVf–VÆB"’÷"6VÆbæ—5öWF†÷&—FF—fR‡6÷W&6RÂ'7F6²"¢“ ¢&WGW&âfÇ6P¢–b—6–ç7Fæ6R‡6÷W&6Ræ6&BÂFö¶VäFVf–æ—F–öâ’æB&Æ–fVÆ–æ²"–â°¢¶W—v÷&Bæ66VföÆB‚’f÷"¶W—v÷&B–â6÷W&6Rç'VÆW5ö6&Bæ¶W—v÷&G0¢Ó ¢&WGW&âG'VP¢&WGW&âç’€¢6VÖçF–72æ6÷fW&vRægVÆÇ•÷7W÷'FV@¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡6÷W&6Rç'VÆW5ö6&B¢–b‡6VÖçF–72£Ò6VÆbæ–çFW'&WFW"æÆ–fVÆ–æµ÷6VÖçF–5ö6÷fW&vR‡6÷W&6Ræ6&BÂg&vÖVçB’¢—2æ÷BæöæP¢ ¢FVbWfÇVFVEöFVF‡F÷V6‚‡6VÆbÂ6÷W&6S¢6&Dö&¦V7BÂ7F6´ö&¦V7BÂW&ÖæVçB’Óâ&ööÃ ¢""%&VBFVF‡F÷V6‚g&öÒF†RFÖvR6÷W&6RBFÖvRF–ÖRâ"" ¢–bæ÷B6VÆbæ—5öWF†÷&—FF—fR‡6÷W&6RÂ&&GFÆVf–VÆB"“ ¢&WGW&âfÇ6P¢–b—6–ç7Fæ6R‡6÷W&6RÂW&ÖæVçB“ ¢&WGW&â6VÆbåö†5ö¶W—v÷&B‡6÷W&6RÂ$FVF‡F÷V6‚"’÷"6VÆbæ†5÷FV×÷&'•ö¶W—v÷&B€¢6÷W&6RÂFV×÷&'”¶W—v÷&BäDTD…DõT4€¢¢&WGW&âfÇ6P ¢FVböÇ•öÆ–fVÆ–æµ÷&W7VÇB€¢6VÆbÀ¢6÷W&6S¢6&Dö&¦V7BÂ7F6´ö&¦V7BÂW&ÖæVçBÀ¢Ö÷VçC¢–çBÀ¢¢À¢6öÖ&C¢&ööÂÀ¢FÖvU÷7FW¢6öÖ&DFÖvU7FW¶–æBÂæöæRÀ¢F&vWEö–G3¢GWÆU·7G"ÂââåÒÀ¢F&vWE÷Æ–W'3¢GWÆU¶–çBÂââåÒÀ¢’ÓâÆ–fVÆ–æ´Wf–FVæ6S ¢""$Ç’5"#ã6böæ6Rf÷"öæRWF†÷&—FF—fR6÷W&6Rw2FÖvRWfVçBâ"" ¢–bæ÷B6VÆbæWfÇVFVEöÆ–fVÆ–æ²‡6÷W&6R“ ¢&—6RfÇVTW'&÷"‚$Æ–fVÆ–æ²&W7VÇB&WV—&W2âWF†÷&—FF—fR6÷W&6Rv—F‚Æ–fVÆ–æ²"¢–bÖ÷VçBÃÒ ¢&—6RfÇVTW'&÷"‚$Æ–fVÆ–æ²&W7VÇB&WV—&W2÷6—F—fRFÖvR"¢6öçG&öÆÆW"Ò6÷W&6Ræ6öçG&öÆÆW ¢Æ–fUö&Vf÷&RÒ6VÆbçÆ–W'5¶6öçG&öÆÆW%ÒæÆ–fP¢WfVçBÒ6VÆbæv–åöÆ–fR€¢6öçG&öÆÆW"À¢Ö÷VçBÀ¢6÷W&6Uö6&C×6÷W&6Ræ6&BææÖRÀ¢÷&6ÆUög&vÖVçCÒ$Æ–fVÆ–æ²"À¢FVfW%÷G&–vvW%öFVÆ—fW'“ÕG'VRÀ¢¢Wf–FVæ6RÒÆ–fVÆ–æ´Wf–FVæ6R€¢WfVçBæWfVçEö–BÀ¢6÷W&6Ræö&¦V7Eö–BÀ¢6öçG&öÆÆW"À¢Ö÷VçBÀ¢6öÖ&BÀ¢FÖvU÷7FWÀ¢F&vWEö–G2À¢F&vWE÷Æ–W'2À¢Æ–fUö&Vf÷&RÀ¢6VÆbçÆ–W'5¶6öçG&öÆÆW%ÒæÆ–fRÀ¢¢6VÆbæÆ–fVÆ–æµöWf–FVæ6RæVæB†Wf–FVæ6R¢6VÆbæÆör€¢&Æ–fVÆ–æµ÷&W7VÇB"À¢WfVçEö–CÖWfVçBæWfVçEö–BÀ¢6÷W&6Uö–C×6÷W&6Ræö&¦V7Eö–BÀ¢6÷W&6Uö6&C×6÷W&6Ræ6&BææÖRÀ¢6öçG&öÆÆW#×6VÆbçÆ–W'5¶6öçG&öÆÆW%ÒææÖRÀ¢Ö÷VçCÖÖ÷VçBÀ¢6öÖ&CÖ6öÖ&BÀ¢FÖvU÷7FWÔæöæR–bFÖvU÷7FW—2æöæRVÇ6RFÖvU÷7FWçfÇVRÀ¢F&vWEö–G3ÖÆ—7B‡F&vWEö–G2’À¢F&vWE÷Æ–W'3Õ·6VÆbçÆ–W'5¶–æFW…ÒææÖRf÷"–æFW‚–âF&vWE÷Æ–W'5ÒÀ¢Æ–fUö&Vf÷&SÖWf–FVæ6RæÆ–fUö&Vf÷&RÀ¢Æ–fUögFW#ÖWf–FVæ6RæÆ–fUögFW"À¢¢&WGW&âWf–FVæ6P ¢FVböVçVWVUöWV—ÖVçEö6öÖ&E÷G&–vvW'2‡6VÆbÂWfVçC¢'VÆW4WfVçBÂ&V6—–VçC¢W&ÖæVçB’ÓâæöæS ¢""$w&çB6öÖ&BG&–vvW'2g&öÒWV—ÖVçBGF6†VBBF†RFÖvRWfVçBâ"" ¢f÷"Æ–W"–â6VÆbçÆ–W'3 ¢f÷"WV—ÖVçB–âÆ–W"æ&GFÆVf–VÆC ¢–bWV—ÖVçBæGF6†VE÷FòÒ&V6—–VçBæö&¦V7Eö–C ¢6öçF–çVP¢–b€¢&V6—–VçBæ&–Æ—G•öÆ÷75÷F–ÖW7F×—2æ÷BæöæP¢æBWV—ÖVçBæGF6†ÖVçE÷F–ÖW7F×ÃÒ&V6—–VçBæ&–Æ—G•öÆ÷75÷F–ÖW7F× ¢“ ¢6öçF–çVP¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2†WV—ÖVçBç'VÆW5ö6&B“ ¢–b€¢6VÆbæ–çFW'&WFW"æWV—ÖVçEöw&çFVEö6öÖ&E÷6VÖçF–72€¢WV—ÖVçBæ6&BÂg&vÖVç@¢¢—2æ÷BæöæP¢“ ¢6VÆbåöVçVWVU÷G&–vvW"€¢WfVçBÀ¢&V6—–VçBÀ¢g&vÖVçBÀ¢G&–vvW$VffV7Bäu$åDTEô4ôÔ$EõTåDôt”âÀ¢w&çE÷6÷W&6SÖWV—ÖVçBÀ¢ ¢FVb&W6öÇfUö6öÖ&EöFÖvR‡6VÆb’Óâ6öÖ&DFÖvU7FWWf–FVæ6S ¢""%&W6öÇfRW†7FÇ’öæRWF†÷&—FF—fR5"SãB6öÖ&BÖFÖvR7FWâ"" ¢–b€¢6VÆbç7FW—2æ÷BGW&å7FWä4ôÔ$EôDÔtP¢÷"6VÆbåö6öÖ&EöFÖvU÷&W6öÇfV@¢÷"6VÆbåö6öÖ&EöFÖvU÷7FWö¶–æ@¢æ÷B–â´6öÖ&DFÖvU7FW¶–æBäd•%5Eõ5E$”´RÂ6öÖ&DFÖvU7FW¶–æBå$TuTÄ'Ð¢“ ¢&—6RfÇVTW'&÷"‚&6öÖ&BFÖvR7FW—2æ÷B&VG’Fò&W6öÇfR"¢–bÆVâ‡6WB‡6VÆbåö6öÖ&EöGF6¶W'2’’ÒÆVâ‡6VÆbåö6öÖ&EöGF6¶W'2“ ¢&—6RfÇVTW'&÷"‚&6öÖ&B7FFR6öçF–ç2GWÆ–6FRGF6¶W""¢–bÆVâ‡¶&Æö6¶W%ö–Bf÷"öGF6¶W%ö–BÂ&Æö6¶W%ö–B–â6VÆbåö6öÖ&Eö&Æö6·7Ò’ÒÆVâ€¢6VÆbåö6öÖ&Eö&Æö6·0¢“ ¢&—6RfÇVTW'&÷"‚&6öÖ&B7FFR6öçF–ç2GWÆ–6FR&Æö6¶W"" ¢FVfVæFW%ö–æFW‚ÒÒ6VÆbæ7F—fU÷Æ–W ¢GF6¶W'2Ò°¢ö&¦V7Eö–C¢6VÆbåö6öÖ&E÷W&ÖæVçB†ö&¦V7Eö–BÂ&GF6¶W""¢f÷"ö&¦V7Eö–B–â6VÆbåö6öÖ&EöGF6¶W'0¢Ð¢&Æö6·3¢F–7E·7G"ÂGWÆUµW&ÖæVçBÂââåÕÒÒ·Ð¢f÷"GF6¶W%ö–BÂ&Æö6¶W%ö–B–â6VÆbåö6öÖ&Eö&Æö6·3 ¢&Æö6¶W"Ò6VÆbåö6öÖ&E÷W&ÖæVçB†&Æö6¶W%ö–BÂ&&Æö6¶W""¢&Æö6·5¶GF6¶W%ö–EÒÒ&Æö6·2ævWB†GF6¶W%ö–BÂ‚’’²†&Æö6¶W"Â¢–bç’†GF6¶W%ö–Bæ÷B–âGF6¶W'2f÷"GF6¶W%ö–B–â&Æö6·2“ ¢&—6RfÇVTW'&÷"‚&6öÖ&B7FFR76–vç2&Æö6¶W"FòæöæGF6¶W""¢VÆ–v–&ÆRÒ6VÆbåöFÖvU÷7FWöVÆ–v–&ÆUö–G2‚¢76–væÖVçG3¢Æ—7E´6öÖ&DFÖvT76–væÖVçEÒÒµÐ¢FÖvVE÷—'3¢Æ—7E·GWÆUµW&ÖæVçBÂW&ÖæVçEÕÒÒµÐ¢G&×ÆUö–çWG3¢F–7E°¢7G"ÂGWÆU·7G"ÂæöæRÂ–çBÂ–çBÂæöæRÂ–çBÂæöæRÂ–çBÂ–çBÂ–çBÂ&ööÅÐ¢ÒÒ·Ð¢f÷"GF6¶W%ö–BÂGF6¶W"–âGF6¶W'2æ—FV×2‚“ ¢GF6¶W%÷&W6VçBÒ6VÆbæ—5öWF†÷&—FF—fR†GF6¶W"Â&&GFÆVf–VÆB"¢&Æö6¶W'2Ò&Æö6·2ævWB†GF6¶W%ö–BÂ‚’¢&W6VçBÒGWÆR€¢&Æö6¶W"f÷"&Æö6¶W"–â&Æö6¶W'2–b6VÆbæ—5öWF†÷&—FF—fR†&Æö6¶W"Â&&GFÆVf–VÆB"¢¢–bæ÷B&Æö6¶W'3 ¢–bGF6¶W%÷&W6VçBæBGF6¶W%ö–B–âVÆ–v–&ÆRæBGF6¶W"ç÷vW"â ¢76–væÖVçG2æVæB€¢6VÆbåö6öÖ&Eö76–væÖVçB†GF6¶W"ÂF&vWE÷Æ–W#ÖFVfVæFW%ö–æFW‚¢¢6öçF–çVP¢–bGF6¶W%÷&W6VçBæBGF6¶W%ö–B–âVÆ–v–&ÆRæBGF6¶W"ç÷vW"â ¢÷vW"ÒÖ‚ƒÂGF6¶W"ç÷vW"¢&VÖ–æ–ærÒ÷vW ¢f—'7BÒ&W6VçE³Ò–b&W6VçBVÇ6RæöæP¢f—'7Eöç’Ò&Æö6¶W'5³Ò–b&Æö6¶W'2VÇ6RæöæP¢f÷"–æFW‚Â&Æö6¶W"–âVçVÖW&FR‡&W6VçB“ ¢–b&VÖ–æ–ærÃÒ ¢'&V°¢ÆWF†ÂÒÖ–â€¢Ö‚ƒÂ&Æö6¶W"çF÷Vv†æW72Ò&Æö6¶W"æFÖvR’À¢–b6VÆbæWfÇVFVEöFVF‡F÷V6‚†GF6¶W"’VÇ6R&Æö6¶W"çF÷Vv†æW72À¢¢—5öÆ7BÒ–æFW‚ÓÒÆVâ‡&W6VçB’Ò¢Ö÷VçBÒ€¢Ö–â‡&VÖ–æ–ærÂÆWF†Â¢–b6VÆbæWfÇVFVE÷G&×ÆR†GF6¶W"’÷"æ÷B—5öÆ7@¢VÇ6R&VÖ–æ–æp¢¢76–væÖVçG2æVæB€¢6VÆbåö6öÖ&Eö76–væÖVçB€¢GF6¶W"À¢F&vWCÖ&Æö6¶W"À¢Ö÷VçCÖÖ÷VçBÀ¢G&×ÆS×6VÆbæWfÇVFVE÷G&×ÆR†GF6¶W"’À¢ÆWF†Å÷&WV—&VCÖÆWF†Â–b6VÆbæWfÇVFVE÷G&×ÆR†GF6¶W"’VÇ6RæöæRÀ¢¢¢&VÖ–æ–ærÓÒÖ÷Vç@¢FÖvVE÷—'2æVæB‚†GF6¶W"Â&Æö6¶W"’¢–b6VÆbæWfÇVFVE÷G&×ÆR†GF6¶W"“ ¢G&×ÆUö–çWG5¶GF6¶W%ö–EÒÒ€¢f—'7Eöç’æö&¦V7Eö–B–bf—'7Eöç’VÇ6RæöæRÀ¢÷vW"À¢f—'7BçF÷Vv†æW72–bf—'7BVÇ6RæöæRÀ¢f—'7BæFÖvR–bf—'7BVÇ6RæöæRÀ¢€¢Ö–â€¢Ö‚ƒÂf—'7BçF÷Vv†æW72Òf—'7BæFÖvR’À¢–b6VÆbæWfÇVFVEöFVF‡F÷V6‚†GF6¶W"’VÇ6Rf—'7BçF÷Vv†æW72À¢¢–bf—'7@¢VÇ6R ¢’À¢÷vW"Ò&VÖ–æ–ærÀ¢&VÖ–æ–ærÀ¢6VÆbæWfÇVFVEöFVF‡F÷V6‚†GF6¶W"’À¢¢–b&VÖ–æ–æs ¢76–væÖVçG2æVæB€¢6VÆbåö6öÖ&Eö76–væÖVçB€¢GF6¶W"À¢F&vWE÷Æ–W#ÖFVfVæFW%ö–æFW‚À¢Ö÷VçC×&VÖ–æ–ærÀ¢G&×ÆSÕG'VRÀ¢ÆWF†Å÷&WV—&VCÓÀ¢¢¢f÷"&Æö6¶W"–â&W6VçC ¢–b&Æö6¶W"æö&¦V7Eö–B–âVÆ–v–&ÆRæB&Æö6¶W"ç÷vW"â ¢76–væÖVçG2æVæB‡6VÆbåö6öÖ&Eö76–væÖVçB†&Æö6¶W"ÂF&vWCÖGF6¶W"’ ¢–bÆVâ€¢°¢†76–væÖVçBç6÷W&6Uö–BÂ76–væÖVçBçF&vWEö–BÂ76–væÖVçBçF&vWE÷Æ–W"¢f÷"76–væÖVçB–â76–væÖVçG0¢Ð¢’ÒÆVâ†76–væÖVçG2“ ¢&—6R76W'F–öäW'&÷"‚&6öÖ&FçB&WVFVBöæR76–væÖVçB–âFÖvR7FW"¢f÷"6÷W&6Uö–B–â¶76–væÖVçBç6÷W&6Uö–Bf÷"76–væÖVçB–â76–væÖVçG7Ó ¢6÷W&6Uö76–væÖVçG2Ò°¢76–væÖVçBf÷"76–væÖVçB–â76–væÖVçG2–b76–væÖVçBç6÷W&6Uö–BÓÒ6÷W&6Uö–@¢Ð¢–bÆVâ‡6÷W&6Uö76–væÖVçG2’ÃÒ ¢6öçF–çVP¢6÷W&6RÒ6VÆbåö6öÖ&E÷W&ÖæVçB‡6÷W&6Uö–BÂ&FÖvR6÷W&6R"¢—5ö×VÇF•ö&Æö6µöGF6¶W"Ò6÷W&6Uö–B–âGF6¶W'2æBÆVâ†&Æö6·2ævWB‡6÷W&6Uö–BÂ‚’’’â¢–b†æ÷B6VÆbæWfÇVFVE÷G&×ÆR‡6÷W&6R’æBæ÷B—5ö×VÇF•ö&Æö6µöGF6¶W"’÷"7VÒ€¢—FVÒçF&vWE÷Æ–W"—2æ÷BæöæRf÷"—FVÒ–â6÷W&6Uö76–væÖVçG0¢’â ¢&—6R76W'F–öäW'&÷"‚'7Æ—B76–væÖVçG2&WV—&R&÷VæFVB6öÖ&B76–væÖVçB"¢&Vf÷&U÷&VÖ–æ–ærÒ°¢W&ÖæVçBæö&¦V7Eö–@¢f÷"W&ÖæVçB–âGWÆR†GF6¶W'2çfÇVW2‚’¢²GWÆR€¢&Æö6¶W ¢f÷"w&÷W–â&Æö6·2çfÇVW2‚¢f÷"&Æö6¶W"–â†w&÷W–b—6–ç7Fæ6R†w&÷WÂGWÆR’VÇ6R†w&÷WÂ’¢¢–b6VÆbæ—5öWF†÷&—FF—fR‡W&ÖæVçBÂ&&GFÆVf–VÆB"¢Ð¢G&×ÆUöÆ–fUö&Vf÷&S¢F–7E·7G"Â–çEÒÒ·Ð¢G&×ÆUöÆ–fUögFW#¢F–7E·7G"Â–çEÒÒ·Ð¢Æ–fVÆ–æµö76–væÖVçG3¢F–7E·7G"ÂÆ—7E´6öÖ&DFÖvT76–væÖVçEÕÒÒ·Ð¢f÷"76–væÖVçB–â76–væÖVçG3 ¢6÷W&6RÒ6VÆbåö6öÖ&E÷W&ÖæVçB†76–væÖVçBç6÷W&6Uö–BÂ&FÖvR6÷W&6R"¢–b6VÆbæWfÇVFVEöÆ–fVÆ–æ²‡6÷W&6R“ ¢Æ–fVÆ–æµö76–væÖVçG2ç6WFFVfVÇB‡6÷W&6Ræö&¦V7Eö–BÂµÒ’æVæB†76–væÖVçB¢–b76–væÖVçBç6÷W&6Uö–B–âG&×ÆUö–çWG3 ¢G&×ÆUöÆ–fUö&Vf÷&Rç6WFFVfVÇB€¢76–væÖVçBç6÷W&6Uö–BÂ6VÆbçÆ–W'5¶FVfVæFW%ö–æFW…ÒæÆ–fP¢¢–b76–væÖVçBçF&vWE÷Æ–W"—2æ÷BæöæS ¢6VÆbçÆ–W'5¶76–væÖVçBçF&vWE÷Æ–W%ÒæÆ–fRÓÒ76–væÖVçBæÖ÷Vç@¢6VÆbæÆör€¢&6öÖ&EöFÖvU÷Æ–W""À¢6÷W&6S×6÷W&6Ræ6&BææÖRÀ¢6÷W&6Uö–C×6÷W&6Ræö&¦V7Eö–BÀ¢F&vWE÷Æ–W#Ö76–væÖVçBçF&vWE÷Æ–W"À¢FÖvSÖ76–væÖVçBæÖ÷VçBÀ¢FÖvU÷7FW×6VÆbåö6öÖ&EöFÖvU÷7FWö¶–æBçfÇVRÀ¢&öÆSÖ76–væÖVçBç&öÆRÀ¢¢–b76–væÖVçBæÖ÷VçBâ ¢WfVçBÒ6VÆbåöæWu÷'VÆW5öWfVçB€¢'VÆW4WfVçD¶–æBä4ôÔ$EôDÔtUõDõõÄ”U"À¢6÷W&6Ræ6öçG&öÆÆW"À¢‡6÷W&6Ræö&¦V7Eö–BÂ’À¢6÷W&6Uö–C×6÷W&6Ræö&¦V7Eö–BÀ¢F&vWE÷Æ–W#Ö76–væÖVçBçF&vWE÷Æ–W"À¢Ö÷VçCÖ76–væÖVçBæÖ÷VçBÀ¢¢6VÆbåöVçVWVUöWV—ÖVçEö6öÖ&E÷G&–vvW'2†WfVçBÂ6÷W&6R¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡6÷W&6Rç'VÆW5ö6&B“ ¢6VÖçF–72Ò6VÆbæ–çFW'&WFW"æ6öÖ&EöFÖvUöG&uöF—66&E÷6VÖçF–5ö6÷fW&vR€¢6÷W&6Ræ6&BÂg&vÖVç@¢¢–b6VÖçF–72—2æ÷BæöæRæB6VÖçF–72æ6÷fW&vRægVÆÇ•÷7W÷'FVC ¢6VÆbåöVçVWVU÷G&–vvW"€¢WfVçBÂ6÷W&6RÂg&vÖVçBÂG&–vvW$VffV7Bä4ôÔ$EôDÔtUôE$uôD•44$@¢¢–b6VÆbæ–çFW'&WFW"æ6öÖ&EöFÖvUöG&uöÆ÷6UöÆ–fR‡6÷W&6Ræ6&BÂg&vÖVçB“ ¢6VÆbåöVçVWVU÷G&–vvW"€¢WfVçBÂ6÷W&6RÂg&vÖVçBÂG&–vvW$VffV7Bä4ôÔ$EôDÔtUôE$uôÄõ4UôÄ”dP¢¢–b€¢6÷W&6Ræ&–Æ—G•öÆ÷75÷F–ÖW7F×—2æöæP¢æB6VÆbæ–çFW'&WFW"æ6öÖ&EöFÖvUöw&fW–&EöGF6¶W"€¢6÷W&6Ræ6&BÂg&vÖVç@¢¢“ ¢6VÆbåöVçVWVU÷G&–vvW"€¢WfVçBÀ¢6÷W&6RÀ¢g&vÖVçBÀ¢G&–vvW$VffV7Bä4ôÔ$EôDÔtUôu$dU”$EôED4´U"À¢¢–b€¢6÷W&6Ræ&–Æ—G•öÆ÷75÷F–ÖW7F×—2æöæP¢æB6VÆbæ–çFW'&WFW"æ6öÖ&EöFÖvUö'F–f7Eö6÷’‡6÷W&6Ræ6&BÂg&vÖVçB¢“ ¢6VÆbåöVçVWVU÷G&–vvW"€¢WfVçBÀ¢6÷W&6RÀ¢g&vÖVçBÀ¢G&–vvW$VffV7Bä4ôÔ$EôDÔtUô%D”d5Eô4õ’À¢¢–b€¢6÷W&6Ræ&–Æ—G•öÆ÷75÷F–ÖW7F×—2æöæP¢æB6VÆbæ–çFW'&WFW"æ6öÖ&EöFÖvUö†æEö&GFÆVf–VÆB€¢6÷W&6Ræ6&BÂg&vÖVç@¢¢“ ¢6VÆbåöVçVWVU÷G&–vvW"€¢WfVçBÀ¢6÷W&6RÀ¢g&vÖVçBÀ¢G&–vvW$VffV7Bä4ôÔ$EôDÔtUô„äEô$EDÄTd”TÄBÀ¢¢VÇ6S ¢76W'B76–væÖVçBçF&vWEö–B—2æ÷BæöæP¢F&vWBÒ6VÆbåö6öÖ&E÷W&ÖæVçB†76–væÖVçBçF&vWEö–BÂ&FÖvRF&vWB"¢26öÖ&B76–væÖVçG2&R'V–ÇB&Vf÷&RF†RFÖvR7FW&W6öÇfW2â¢2F&vWB6â6V6RFòö67W’F†RWF†÷&—FF—fR&GFÆVf–VÆB&WGvVVà¢27FW2†÷"&R&WF–æVB'’7FÆR6öÖ&B7FFR“²æWfW"ÖçVf7GW&R¢2FÖvRWfVçBf÷"F†BFW'FVBö&¦V7BâF†—2&W6W'fW2F†P¢2&÷fVææ6R–çf&–çB–ç7FVBöbvV¶Væ–ær—BBG&–vvW"fÆ–FF–öâà¢–bæ÷B6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"“ ¢6öçF–çVP¢F&vWBæFÖvR³Ò76–væÖVçBæÖ÷Vç@¢–b76–væÖVçBæÖ÷VçBâæB6VÆbæWfÇVFVEöFVF‡F÷V6‚‡6÷W&6R“ ¢F&vWBæFVF‡F÷V6…öFÖvRÒG'VP¢–b76–væÖVçBæÖ÷VçBâ ¢WfVçBÒ6VÆbåöæWu÷'VÆW5öWfVçB€¢'VÆW4WfVçD¶–æBä4ôÔ$EôDÔtUõDõô5$TEU$RÀ¢6÷W&6Ræ6öçG&öÆÆW"À¢‡6÷W&6Ræö&¦V7Eö–BÂF&vWBæö&¦V7Eö–B’À¢6÷W&6Uö–C×6÷W&6Ræö&¦V7Eö–BÀ¢Ö÷VçCÖ76–væÖVçBæÖ÷VçBÀ¢¢6VÆbåöVçVWVUöWV—ÖVçEö6öÖ&E÷G&–vvW'2†WfVçBÂ6÷W&6R¢6VÆbåöVçVWVUöFÖvU÷Fõ÷6VÆeöÖæ†WfVçBÂF&vWB¢6VÆbæÆör€¢&6öÖ&EöFÖvUö76–væÖVçB"À¢6÷W&6S×6÷W&6Ræ6&BææÖRÀ¢6÷W&6Uö–C×6÷W&6Ræö&¦V7Eö–BÀ¢F&vWC×F&vWBæ6&BææÖRÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢FÖvSÖ76–væÖVçBæÖ÷VçBÀ¢FÖvU÷7FW×6VÆbåö6öÖ&EöFÖvU÷7FWö¶–æBçfÇVRÀ¢&öÆSÖ76–væÖVçBç&öÆRÀ¢¢–b76–væÖVçBç6÷W&6Uö–B–âG&×ÆUö–çWG3 ¢G&×ÆUöÆ–fUögFW%¶76–væÖVçBç6÷W&6Uö–EÒÒ6VÆbçÆ–W'5¶FVfVæFW%ö–æFW…ÒæÆ–fP¢f÷"6÷W&6Uö–BÂ6÷W&6Uö76–væÖVçG2–âÆ–fVÆ–æµö76–væÖVçG2æ—FV×2‚“ ¢6÷W&6RÒ6VÆbåö6öÖ&E÷W&ÖæVçB‡6÷W&6Uö–BÂ$Æ–fVÆ–æ²FÖvR6÷W&6R"¢6VÆbåöÇ•öÆ–fVÆ–æµ÷&W7VÇB€¢6÷W&6RÀ¢7VÒ†76–væÖVçBæÖ÷VçBf÷"76–væÖVçB–â6÷W&6Uö76–væÖVçG2’À¢6öÖ&CÕG'VRÀ¢FÖvU÷7FW×6VÆbåö6öÖ&EöFÖvU÷7FWö¶–æBÀ¢F&vWEö–G3×GWÆR€¢76–væÖVçBçF&vWEö–@¢f÷"76–væÖVçB–â6÷W&6Uö76–væÖVçG0¢–b76–væÖVçBçF&vWEö–B—2æ÷BæöæP¢’À¢F&vWE÷Æ–W'3×GWÆR€¢76–væÖVçBçF&vWE÷Æ–W ¢f÷"76–væÖVçB–â6÷W&6Uö76–væÖVçG0¢–b76–væÖVçBçF&vWE÷Æ–W"—2æ÷BæöæP¢’À¢¢f÷"GF6¶W"Â&Æö6¶W"–âF–7Bæg&öÖ¶W—2†FÖvVE÷—'2“ ¢6VÆbæÆör€¢&6öÖ&EöFÖvUö7&VGW&W2"À¢GF6¶W#ÖGF6¶W"æ6&BææÖRÀ¢&Æö6¶W#Ö&Æö6¶W"æ6&BææÖRÀ¢ ¢&W6öÇfVEö¶–æBÒ6VÆbåö6öÖ&EöFÖvU÷7FWö¶–æ@¢&W6öÇfVE÷6WVVæ6RÒ6VÆbåö6öÖ&EöFÖvU÷7FWöçVÖ&W ¢&W6öÇfVE÷F÷FÂÒ6VÆbåö6öÖ&EöFÖvU÷F÷FÅ÷7FW0¢6VÆbæ6†V6µ÷7FFUö&6VEö7F–öç2‚¢6VÆbæ6†V6µöÆ–fR‚¢–bæ÷B6VÆbæ—5÷FW&Ö–æÂæB6VÆbçVæF–æu÷G&–vvW'3 ¢6VÆbå÷WE÷VæF–æu÷G&–vvW'5ööå÷7F6²‚¢6VÆbåöG&–å÷G&–vvW&VEö&–Æ—F–W2‚¢gFW%÷&VÖ–æ–ærÒ°¢ö&¦V7Eö–@¢f÷"ö&¦V7Eö–B–â&Vf÷&U÷&VÖ–æ–æp¢–b—6–ç7Fæ6R‚†ö&¢£Ò6VÆbåöö&¦V7G2ævWB†ö&¦V7Eö–B’’ÂW&ÖæVçB¢æB6VÆbæ—5öWF†÷&—FF—fR†ö&¢Â&&GFÆVf–VÆB"¢Ð¢&VÖ÷fVBÒGWÆR‡6÷'FVB†&Vf÷&U÷&VÖ–æ–ærÒgFW%÷&VÖ–æ–ær’¢G&×ÆU÷&W7VÇG3¢Æ—7EµG&×ÆTFÖvTWf–FVæ6UÒÒµÐ¢f÷"6÷W&6Uö–BÂ€¢&Æö6¶W%ö–BÀ¢GF6¶W%÷÷vW"À¢&Æö6¶W%÷F÷Vv†æW72À¢&Æö6¶W%öFÖvUö&Vf÷&RÀ¢ÆWF†ÂÀ¢&Æö6¶W%ö76–væVBÀ¢Æ–W%ö76–væVBÀ¢6÷W&6UöFVF‡F÷V6‚À¢’–âG&×ÆUö–çWG2æ—FV×2‚“ ¢&Æö6¶W%ögFW"Ò6VÆbåöö&¦V7G2ævWB†&Æö6¶W%ö–B’–b&Æö6¶W%ö–B—2æ÷BæöæRVÇ6RæöæP¢&Æö6¶W%÷7W'f—fVBÒ—6–ç7Fæ6R†&Æö6¶W%ögFW"ÂW&ÖæVçB’æB6VÆbæ—5öWF†÷&—FF—fR€¢&Æö6¶W%ögFW"Â&&GFÆVf–VÆB ¢¢G&×ÆU÷&W7VÇG2æVæB€¢G&×ÆTFÖvTWf–FVæ6R€¢6÷W&6Uö–BÀ¢&Æö6¶W%ö–BÀ¢&W6öÇfVEö¶–æBÀ¢GF6¶W%÷÷vW"À¢&Æö6¶W%÷F÷Vv†æW72À¢&Æö6¶W%öFÖvUö&Vf÷&RÀ¢ÆWF†ÂÀ¢&Æö6¶W%ö76–væVBÀ¢Æ–W%ö76–væVBÀ¢FVfVæFW%ö–æFW‚À¢G&×ÆUöÆ–fUö&Vf÷&U·6÷W&6Uö–EÒÀ¢G&×ÆUöÆ–fUögFW%·6÷W&6Uö–EÒÀ¢&Æö6¶W%ögFW"æFÖvR–b&Æö6¶W%÷7W'f—fVBVÇ6RæöæRÀ¢&Æö6¶W%÷7W'f—fVBÀ¢6÷W&6UöFVF‡F÷V6‚À¢¢¢Wf–FVæ6RÒ6öÖ&DFÖvU7FWWf–FVæ6R€¢&W6öÇfVEö¶–æBÀ¢&W6öÇfVE÷6WVVæ6RÀ¢&W6öÇfVE÷F÷FÂÀ¢GWÆR†76–væÖVçG2’À¢&VÖ÷fVBÀ¢GWÆR‡G&×ÆU÷&W7VÇG2’À¢¢6VÆbæ6öÖ&EöFÖvUöWf–FVæ6RæVæB†Wf–FVæ6R¢6VÆbæÆör€¢&6öÖ&EöFÖvU÷7FW÷&W6öÇfVB"À¢FÖvU÷7FW×&W6öÇfVEö¶–æBçfÇVRÀ¢6WVVæ6S×&W6öÇfVE÷6WVVæ6RÀ¢F÷FÅ÷7FW3×&W6öÇfVE÷F÷FÂÀ¢76–væÖVçG3ÖÆVâ†76–væÖVçG2’À¢&VÖ÷fVEö&Vf÷&UöæW‡E÷7FWÖÆ—7B‡&VÖ÷fVB’À¢¢6VÆbåö6öÖ&EöFÖvU÷&W6öÇfVBÒG'VP¢6VÆbåöGfæ6UögFW%ö6öÖ&EöFÖvR‚¢&WGW&âWf–FVæ6P ¢FVböÆ–æ¶VE÷Æ•öw&çEöf÷"‡6VÆbÂÆ–W%ö–æFWƒ¢–çBÂ6&C¢6&Dö&¦V7B’ÓâÆ–æ¶VEÆ”w&çBÂæöæS ¢""$f–æBF†RöÆFW7BVçW6VBw&çBÆ–æ¶VBFòF†—2W†7BW†–ÆR–æ6&æF–öââ"" ¢–bæ÷B6VÆbæ—5öWF†÷&—FF—fR†6&BÂ&W†–ÆR"“ ¢&WGW&âæöæP¢f÷"6÷W&6Uö–BÂw&çG2–â6VÆbåöÆ–æ¶VE÷Æ•öw&çG2æ—FV×2‚“ ¢–bæ÷Bç’€¢Æ–æ¶VEö–BÓÒ6&Bæö&¦V7Eö–BæB÷væW%ö–BÓÒ6÷W&6Uö–@¢f÷"Æ–æ¶VEö–BÂöÆ–æ¶VEö6&BÂ÷væW%ö–B–â6VÆbå÷&†VÅöÆ–æ¶VEöW†–ÆRævWB€¢6÷W&6Uö–BÂ‚¢¢“ ¢6öçF–çVP¢f÷"w&çB–âw&çG3 ¢–b€¢w&çBæ6öçG&öÆÆW"ÓÒÆ–W%ö–æFW€¢æBw&çBæW‡—&W5÷GW&âÓÒ6VÆbçGW&à¢æBw&çBç&VÖ–æ–æu÷Æ—2â ¢“ ¢&WGW&âw&ç@¢&WGW&âæöæP ¢FVb÷&†VÅ÷W&Ö—76–öåöf÷"‡6VÆbÂÆ–W%ö–æFWƒ¢–çBÂ6&C¢6&Dö&¦V7B’Óâ7G"ÂæöæS ¢w&çBÒ6VÆbåöÆ–æ¶VE÷Æ•öw&çEöf÷"‡Æ–W%ö–æFW‚Â6&B¢&WGW&âæöæR–bw&çB—2æöæRVÇ6Rw&çBç6÷W&6Uö–@ ¢FVbö6öç7VÖUöÆ–æ¶VE÷Æ•öw&çB‡6VÆbÂw&çC¢Æ–æ¶VEÆ”w&çBÂ6&Eö–C¢7G"’ÓâæöæS ¢–bw&çBç&VÖ–æ–æu÷Æ—2Ò ¢&—6RfÇVTW'&÷"‚&Æ–æ¶VBÆ’w&çBv2Ç&VG’6öç7VÖVB"¢w&çBç&VÖ–æ–æu÷Æ—2Ò ¢6VÆbæÆör€¢&Æ–æ¶VE÷Æ•öw&çE÷W6VB"À¢w&çEö–CÖw&çBæw&çEö–BÀ¢6÷W&6Uö–CÖw&çBç6÷W&6Uö–BÀ¢6öçG&öÆÆW#Öw&çBæ6öçG&öÆÆW"À¢W†–ÆVEöö&¦V7Eö–CÖ6&Eö–BÀ¢ ¢FVbÆ•öÆæB‡6VÆbÂÆ–W%ö–æFWƒ¢–çBÂ6&C¢6&Dö&¦V7BÂ¢Âg&öÕ÷&†VÃ¢&ööÂÒfÇ6R’Óâ&ööÃ ¢Æ–W"Ò6VÆbçÆ–W'5·Æ–W%ö–æFW…Ð¢w&çBÒ6VÆbåöÆ–æ¶VE÷Æ•öw&çEöf÷"‡Æ–W%ö–æFW‚Â6&B’–bg&öÕ÷&†VÂVÇ6RæöæP¢–b6VÆbç&–÷&—G•÷7FFR—2æ÷BæöæR÷"6VÆbç7F6³ ¢&WGW&âfÇ6P¢–bÆ–W%ö–æFW‚Ò6VÆbæ7F—fU÷Æ–W"÷"6VÆbç7FWæ÷B–â°¢GW&å7FWå$T4ôÔ$EôÔ”âÀ¢GW&å7FWåõ5D4ôÔ$EôÔ”âÀ¢Ó ¢&WGW&âfÇ6P¢–b€¢æ÷B6&Bæ—5öÆæ@¢÷"æ÷B€¢6VÆbæ—5öWF†÷&—FF—fR†6&BÂ&W†–ÆR"¢–bg&öÕ÷&†VÀ¢VÇ6R6VÆbæ—5öWF†÷&—FF—fR†6&BÂ&†æB"¢¢÷"†æ÷Bg&öÕ÷&†VÂæB6&Bæ÷væW"ÒÆ–W%ö–æFW‚¢÷"Æ–W"æÆæG5÷Æ–VBãÒ¢÷"†g&öÕ÷&†VÂæBw&çB—2æöæR¢“ ¢&WGW&âfÇ6P¢VçFW&–ærÒ6VÆbæÖ÷fUöö&¦V7B€¢6&BÀ¢&&GFÆVf–VÆB"À¢6öçG&öÆÆW#×Æ–W%ö–æFW‚À¢7VÖÖöæ–æu÷6–6³ÔfÇ6RÀ¢&V6öãÒ'&†VÅöÆæE÷Æ–VB"–bg&öÕ÷&†VÂVÇ6R&ÆæE÷Æ–VB"À¢¢76W'B—6–ç7Fæ6R†VçFW&–ærÂW&ÖæVçB¢–bw&çB—2æ÷BæöæS ¢6VÆbåö6öç7VÖUöÆ–æ¶VE÷Æ•öw&çB†w&çBÂ6&Bæö&¦V7Eö–B¢6VÆbç&Vg&W6…÷7FF–5÷EöÖöF–f–W'2‚¢Æ–W"æÆæG5÷Æ–VB³Ò¢6VÆbæÆör‚&ÆæE÷Æ–VB"ÂÆ–W#×Æ–W"ææÖRÂ6&CÖ6&BææÖR¢–bç’€¢6VÖçF–72—2æ÷BæöæRæB6VÖçF–75³ÒægVÆÇ•÷7W÷'FV@¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2†VçFW&–ærç'VÆW5ö6&B¢–b‡6VÖçF–72£Ò6VÆbæ–çFW'&WFW"æWF%÷6VÆeöÆ–fUöv–å÷6VÖçF–72†6&Bæ6&BÂg&vÖVçB’¢“ ¢6VÆbå÷&ö6W75ö7&VGW&UöVçFW&VE÷G&–vvW'2€¢VçFW&–ærÂVffV7G3×µG&–vvW$VffV7BäUD%õ4TÄeôÄ”dUôt”çÐ¢¢&WGW&âG'VP ¢7FF–6ÖWF†ö@¢FVböÖæö6öÆ÷'2‡6÷W&6S¢W&ÖæVçB’ÓâGWÆU·7G"ÂââåÓ ¢""$f–Æ&ÆRöæRÖÖæ÷WGWG2&–çFVBöââVçFVBÆæBâ"" ¢f÷"g&vÖVçB–â6&D–çFW'&WFW"æg&vÖVçG2‡6÷W&6Rç'VÆW5ö6&B“ ¢6öÆ÷'2Ò6&D–çFW'&WFW"æÆæEöÖæö÷WGWG2‡6÷W&6Rç'VÆW5ö6&BÂg&vÖVçB¢–b6öÆ÷'2—2æ÷BæöæS ¢&WGW&â6öÆ÷'0¢–bæ÷B6÷W&6Ræ6&BçG—UöÆ–æRç7F'G7v—F‚‚$&6–2ÆæB"“ ¢&WGW&â‚¢&6–2Ò°¢%Æ–ç2#¢%r"À¢$—6ÆæB#¢%R"À¢%7v×#¢$""À¢$Ö÷VçF–â#¢%""À¢$f÷&W7B#¢$r"À¢ÒævWB‡6÷W&6Ræ6&BææÖR¢&WGW&â†&6–2Â’–b&6–2VÇ6R‚ ¢7FF–6ÖWF†ö@¢FVböÖæö6öÆ÷"‡6÷W&6S¢W&ÖæVçB’Óâ7G"ÂæöæS ¢""$ÆVv7’6–ævÆRÖ÷WGWB&ö¦V7F–öã²–ÖVçBW6W2ÆÂÆVvÂ6öÆ÷'2â"" ¢&WGW&âæW‡B†—FW"„vÖRåöÖæö6öÆ÷'2‡6÷W&6R’’ÂæöæR ¢7FF–6ÖWF†ö@¢FVböÖæ÷7–Ö&öÅö÷F–öç2‡7–Ö&öÃ¢7G"’ÓâGWÆU·7G"ÂââåÒÂæöæS ¢""%&WGW&âF†R6öÆ÷'2F†B6â’öæRf—†VB÷"‡–'&–B7–Ö&öÂâ"" ¢–b7–Ö&öÂ–â²%r"Â%R"Â$""Â%""Â$r'Ó ¢&WGW&â‡7–Ö&öÂÂ¢÷F–öç2ÒGWÆR‡7–Ö&öÂç7Æ—B‚"ò"’¢–bÆVâ†÷F–öç2’ÓÒ"æB6WB†÷F–öç2’ÓÒ²%R"Â%"'Ó ¢&WGW&â÷F–öç0¢&WGW&âæöæP ¢FVb÷6VÆV7EöÖæ÷6÷W&6W2€¢6VÆbÀ¢&WV—&VÖVçC¢Öæ&WV—&VÖVçBÀ¢f–Æ&ÆS¢Æ—7EµW&ÖæVçEÒÀ¢fÆöF–æs¢F–7E·7G"Â–çEÒÂæöæRÒæöæRÀ¢’ÓâGWÆU¶Æ—7E·7G%ÒÂÆ—7EµW&ÖæVçEÕÒÂæöæS ¢""%6VÆV7B6öÆ÷&VBæBvVæW&–2–ÖVçB6÷W&6W2FWFW&Ö–æ—7F–6ÆÇ’â"" ¢ööÂÒ·Ò–bfÆöF–ær—2æöæRVÇ6RF–7B†fÆöF–ær¢6÷W&6W2Ò¶ÆæBf÷"ÆæB–âf–Æ&ÆR–b6VÆbåöÖæö6öÆ÷'2†ÆæB•Ð ¢FVb76–vâ€¢–æFWƒ¢–çBÀ¢&VÖ–æ–æs¢Æ—7EµW&ÖæVçEÒÀ¢Öæ÷ööÃ¢F–7E·7G"Â–çEÒÀ¢–EöfÆöF–æs¢Æ—7E·7G%ÒÀ¢6†÷6Vã¢Æ—7EµW&ÖæVçEÒÀ¢’ÓâGWÆU¶Æ—7E·7G%ÒÂÆ—7EµW&ÖæVçEÕÒÂæöæS ¢–b–æFW‚ÓÒÆVâ‡&WV—&VÖVçBæ6öÆ÷&VB“ ¢vVæW&–2Ò&WV—&VÖVçBævVæW&–0¢fÆöF–æuövVæW&–2ÒµÐ¢f÷"6öÆ÷"–â6÷'FVB†Öæ÷ööÂ“ ¢F¶RÒÖ–â†Öæ÷ööÅ¶6öÆ÷%ÒÂvVæW&–2¢fÆöF–æuövVæW&–2æW‡FVæB…¶6öÆ÷%Ò¢F¶R¢vVæW&–2ÓÒF¶P¢–bÆVâ‡&VÖ–æ–ær’ÂvVæW&–3 ¢&WGW&âæöæP¢&WGW&â–EöfÆöF–ær²fÆöF–æuövVæW&–2Â6†÷6Vâ²&VÖ–æ–æu³¦vVæW&–5Ð¢÷F–öç2Ò6VÆbåöÖæ÷7–Ö&öÅö÷F–öç2‡&WV—&VÖVçBæ6öÆ÷&VE¶–æFW…Ò¢–b÷F–öç2—2æöæS ¢&WGW&âæöæP¢f÷"6öÆ÷"–â÷F–öç3 ¢–bÖæ÷ööÂævWB†6öÆ÷"Â“ ¢æW‡E÷ööÂÒF–7B†Öæ÷ööÂ¢æW‡E÷ööÅ¶6öÆ÷%ÒÓÒ¢f÷VæBÒ76–vâ†–æFW‚²Â&VÖ–æ–ærÂæW‡E÷ööÂÂ–EöfÆöF–ær²¶6öÆ÷%ÒÂ6†÷6Vâ¢–bf÷VæB—2æ÷BæöæS ¢&WGW&âf÷Væ@¢f÷"÷6—F–öâÂÆæB–âVçVÖW&FR‡&VÖ–æ–ær“ ¢–bç’†6öÆ÷"–â6VÆbåöÖæö6öÆ÷'2†ÆæB’f÷"6öÆ÷"–â÷F–öç2“ ¢f÷VæBÒ76–vâ€¢–æFW‚²À¢&VÖ–æ–æu³§÷6—F–öåÒ²&VÖ–æ–æu·÷6—F–öâ²¥ÒÀ¢Öæ÷ööÂÀ¢–EöfÆöF–ærÀ¢6†÷6Vâ²¶ÆæEÒÀ¢¢–bf÷VæB—2æ÷BæöæS ¢&WGW&âf÷Væ@¢&WGW&âæöæP ¢&WGW&â76–vâƒÂ6÷W&6W2ÂööÂÂµÒÂµÒ ¢FVb÷ÆåöÖæ÷v—F…öfÆöF–ær€¢6VÆbÀ¢Æ–W%ö–æFWƒ¢–çBÀ¢&WV—&VÖVçC¢Öæ&WV—&VÖVçBÀ¢f–Æ&ÆS¢Æ—7EµW&ÖæVçEÒÀ¢6öçFW‡C¢7G"À¢’ÓâGWÆU·GWÆU·7G"ÂââåÒÂGWÆU·7G"ÂââåÒÂÆ—7EµW&ÖæVçEÕÒÂæöæS ¢""%6VÆV7BöæÇ’VÆ–v–&ÆRfÆöF–ærVæ—G2æB&W6W'fRW†7B&öGV7F–öâÆ–æVvRâ"" ¢Væ—G2Ò6VÆbæfÆöF–æuöÖææVÆ–v–&ÆR‡Æ–W%ö–æFW‚Â6öçFW‡B¢ööÃ¢F–7E·7G"Â–çEÒÒ·Ð¢f÷"Væ—B–âVæ—G3 ¢ööÅ·Væ—Bæ6öÆ÷%ÒÒööÂævWB‡Væ—Bæ6öÆ÷"Â’²¢6VÆV7F–öâÒ6VÆbå÷6VÆV7EöÖæ÷6÷W&6W2‡&WV—&VÖVçBÂf–Æ&ÆRÂööÂ¢–b6VÆV7F–öâ—2æöæS ¢&WGW&âæöæP¢6öÆ÷'2ÂÆæG2Ò6VÆV7F–öà¢&VÖ–æ–ærÒÆ—7B‡Væ—G2¢WfVçEö–G2ÒµÐ¢f÷"6öÆ÷"–â6öÆ÷'3 ¢Væ—BÒæW‡B†—FVÒf÷"—FVÒ–â&VÖ–æ–ær–b—FVÒæ6öÆ÷"ÓÒ6öÆ÷"¢&VÖ–æ–ærç&VÖ÷fR‡Væ—B¢WfVçEö–G2æVæB‡Væ—BæWfVçEö–B¢&WGW&âGWÆR†6öÆ÷'2’ÂGWÆR†WfVçEö–G2’ÂÆæG0 ¢7FF–6ÖWF†ö@¢FVbÖæ÷&WV—&VÖVçB€¢6&C¢6&Df7BÂ6&Dö&¦V7BÂ…÷fÇVS¢–çBÂæöæRÒæöæP¢’ÓâÖæ&WV—&VÖVçBÂæöæS ¢""$6öç7G'V7B6÷7Bv—F‚ÆVvÆÇ’ææ÷Væ6VBæöææVvF—fR‚Â–æ6ÇVF–ær‡–'&–Bâ"" ¢7–Ö&öÇ2Ò&Ræf–æFÆÂ‡"%Ç²…µçÕÒ²•ÇÒ"Â6&BæÖæö6÷7B¢–b""æ¦ö–â†b'···7–Ö&öÇ××Ò"f÷"7–Ö&öÂ–â7–Ö&öÇ2’Ò6&BæÖæö6÷7C ¢&WGW&âæöæP¢–b…÷fÇVR—2æ÷BæöæRæB%‚"æ÷B–â7–Ö&öÇ3 ¢&WGW&âæöæP¢vVæW&–2Ò ¢6öÆ÷&VC¢Æ—7E·7G%ÒÒµÐ¢f÷"7–Ö&öÂ–â7–Ö&öÇ3 ¢–b7–Ö&öÂæ—6FV6–ÖÂ‚“ ¢vVæW&–2³Ò–çB‡7–Ö&öÂ¢VÆ–b€¢7–Ö&öÂÓÒ%‚ ¢æB—6–ç7Fæ6R‡…÷fÇVRÂ–çB¢æBæ÷B—6–ç7Fæ6R‡…÷fÇVRÂ&ööÂ¢æB…÷fÇVRãÒ ¢“ ¢vVæW&–2³Ò…÷fÇVP¢VÆ–bvÖRåöÖæ÷7–Ö&öÅö÷F–öç2‡7–Ö&öÂ’—2æ÷BæöæS ¢6öÆ÷&VBæVæB‡7–Ö&öÂ¢VÇ6S ¢&WGW&âæöæP¢&WV—&VÖVçBÒÖæ&WV—&VÖVçB†vVæW&–2ÂGWÆR†6öÆ÷&VB’¢f&–&ÆU÷F÷FÂÒ7VÒ‡…÷fÇVRf÷"7–Ö&öÂ–â7–Ö&öÇ2–b7–Ö&öÂÓÒ%‚"¢–b&WV—&VÖVçBçF÷FÂÒ6&BæÖæ÷fÇVR²f&–&ÆU÷F÷FÃ ¢&WGW&âæöæP¢&WGW&â&WV—&VÖVç@ ¢FVb67F–æu÷&WV—&VÖVçB€¢6VÆbÀ¢Æ–W%ö–æFWƒ¢–çBÀ¢6&C¢6&Df7BÂ6&Dö&¦V7BÀ¢¢À¢ÇFW&æF—fS¢7G"ÂæöæRÒæöæRÀ¢…÷fÇVS¢–çBÂæöæRÒæöæRÀ¢’ÓâÖæ&WV—&VÖVçBÂæöæS ¢""$Ç’÷&6ÆRÖFW&—fVBvVæW&–2F—66÷VçG2FòF†R6†÷6Vâ7VÆÂ6÷7Bâ"" ¢&6RÒ€¢6VÆbæÖæ÷&WV—&VÖVçB†6&BÂ…÷fÇVS×…÷fÇVR¢–bÇFW&æF—fR—2æöæP¢VÇ6R6VÆbæ7F—fF–öåöÖæ÷&WV—&VÖVçB†ÇFW&æF—fR¢¢–b&6R—2æöæS ¢&WGW&âæöæP¢&VGV7F–öâÒ7VÒ€¢&öw&ÒæÖ÷VçB¢†ÆVâ‡6÷W&6W2’–b&öw&ÒçW%÷W&ÖæVçBVÇ6R&ööÂ‡6÷W&6W2’¢f÷"&öw&ÒÂ6÷W&6W2–â6VÆbåö67F–æu÷&VGV7F–öç2‡Æ–W%ö–æFW‚Â6&B¢¢&WGW&âÖæ&WV—&VÖVçB†Ö‚ƒÂ&6RævVæW&–2Ò&VGV7F–öâ’Â&6Ræ6öÆ÷&VB ¢FVbö67F–æu÷&VGV7F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çBÂ6&C¢6&Df7BÂ6&Dö&¦V7B“ ¢""%&WGW&âF—66÷VçBv—FæW76W2g&öÒ7W'&VçB6öçG&öÆÆVBW&ÖæVçG2â"" ¢–bÆ–W%ö–æFW‚æ÷B–â&ævRƒ"“ ¢&WGW&â‚¢f7G2Ò6&Bæ6&B–b—6–ç7Fæ6R†6&BÂ6&Dö&¦V7B’VÇ6R6&@¢&W7VÇBÒµÐ¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2†f7G2“ ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"ævVæW&–5ö6÷7E÷&VGV7F–öå÷&öw&Ò†f7G2Âg&vÖVçB¢–b&öw&Ò—2æöæS ¢6öçF–çVP¢6÷W&6W2ÒGWÆR€¢6÷W&6Ræö&¦V7Eö–@¢f÷"6÷W&6R–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢–b6VÆbæ—5öWF†÷&—FF—fR‡6÷W&6RÂ&&GFÆVf–VÆB"¢æB€¢&öw&ÒçVÆ—G’–â6÷W&6RçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢–b&öw&ÒçW%÷W&ÖæVç@¢VÇ6R&öw&ÒçVÆ—G’–â6÷W&6RçG—UöÆ–æRç'F—F–öâ‚"(	B"•³%Òç7Æ—B‚¢¢¢&W7VÇBæVæB‚‡&öw&ÒÂ6÷W&6W2’¢&WGW&âGWÆR‡&W7VÇB ¢7FF–6ÖWF†ö@¢FVb7F—fF–öåöÖæ÷&WV—&VÖVçB†Öæö6÷7C¢7G"’ÓâÖæ&WV—&VÖVçBÂæöæS ¢""$6öç7G'V7BöæR&W&W6VçFVBf—†VB7F—fF–öâÖæ&WV—&VÖVçBâ"" ¢7–Ö&öÇ2Ò&Ræf–æFÆÂ‡"%Ç²…µçÕÒ²•ÇÒ"ÂÖæö6÷7B¢–b""æ¦ö–â†b'···7–Ö&öÇ××Ò"f÷"7–Ö&öÂ–â7–Ö&öÇ2’ÒÖæö6÷7C ¢&WGW&âæöæP¢vVæW&–2Ò ¢6öÆ÷&VC¢Æ—7E·7G%ÒÒµÐ¢f÷"7–Ö&öÂ–â7–Ö&öÇ3 ¢–b7–Ö&öÂæ—6FV6–ÖÂ‚“ ¢vVæW&–2³Ò–çB‡7–Ö&öÂ¢VÆ–bvÖRåöÖæ÷7–Ö&öÅö÷F–öç2‡7–Ö&öÂ’—2æ÷BæöæS ¢6öÆ÷&VBæVæB‡7–Ö&öÂ¢VÇ6S ¢&WGW&âæöæP¢&WGW&âÖæ&WV—&VÖVçB†vVæW&–2ÂGWÆR†6öÆ÷&VB’ ¢FVbö7F—fF–öå÷Fö¶Våö6÷7E÷&VGV6W'2€¢6VÆbÂÆ–W%ö–æFWƒ¢–çBÂ6÷W&6S¢W&ÖæVç@¢’ÓâGWÆU·GWÆUµW&ÖæVçBÂ–çBÂ7G%ÒÂââåÓ ¢""$Æ—fR7FF–2VffV7G2Ç––ærFòF†—26öçG&öÆÆVBFö¶Vâw27F—fFVB&–Æ—G’â"" ¢–bæ÷B6÷W&6Ræ—5÷Fö¶Vâ÷"6÷W&6Ræ6öçG&öÆÆW"ÒÆ–W%ö–æFWƒ ¢&WGW&â‚¢G—W2Ò6÷W&6RçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢&WGW&âGWÆR€¢‡&VGV6W"Â&öw&ÒæÖ÷VçBÂ&öw&Òæ÷&6ÆUög&vÖVçB¢f÷"&VGV6W"–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢–b6VÆbæ—5öWF†÷&—FF—fR‡&VGV6W"Â&&GFÆVf–VÆB"¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡&VGV6W"ç'VÆW5ö6&B¢–b€¢&öw&Ò£Ò6VÆbæ–çFW'&WFW"æ7F—fFVE÷Fö¶Våö6÷7E÷&VGV7F–öå÷&öw&Ò€¢&VGV6W"æ6&BÂg&vÖVç@¢¢¢—2æ÷BæöæP¢æB&öw&ÒçW&ÖæVçE÷G—R–âG—W0¢ ¢FVb7F—fF–öå÷–ÖVçE÷Æâ€¢6VÆbÀ¢Æ–W%ö–æFWƒ¢–çBÀ¢6÷W&6S¢W&ÖæVçBÀ¢÷&6ÆUög&vÖVçC¢7G"À¢¢À¢÷F†W%÷67&–f–6Uö–C¢7G"ÂæöæRÒæöæRÀ¢’Óâ7F—fF–öå–ÖVçEÆâÂæöæS ¢""$'V–ÆBFWFW&Ö–æ—7F–27F—fF–öâ–ÖVçBv—F†÷WB×WFF–ærvÖR7FFRâ"" ¢–b€¢Æ–W%ö–æFW‚æ÷B–â&ævRƒ"¢÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR‡6÷W&6RÂ&&GFÆVf–VÆB"¢÷"6÷W&6Ræ6öçG&öÆÆW"ÒÆ–W%ö–æFW€¢“ ¢&WGW&âæöæP¢–b÷&6ÆUög&vÖVçBæ÷B–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡6÷W&6Rç'VÆW5ö6&B“ ¢&WGW&âæöæP¢6VÖçF–72Ò6VÆbæ–çFW'&WFW"æ7F—fFVEö&–Æ—G•÷6VÖçF–72‡6÷W&6Ræ6&BÂ÷&6ÆUög&vÖVçB¢–b6VÖçF–72—2æöæR÷"æ÷B6VÖçF–72æ6÷fW&vRægVÆÇ•÷7W÷'FVC ¢&WGW&âæöæP¢–b6VÖçF–72ç&öw&Òæ6÷7BæF—66&E÷6÷W&6S ¢&WGW&âæöæP¢–b6VÖçF–72ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäEdä4Uô4Ä55ôÄUdTÂæB€¢†ÖF6‚£Ò6VÆbæ–çFW'&WFW"ä4Ä55ôÄUdTÅõUægVÆÆÖF6‚†÷&6ÆUög&vÖVçB’’—2æöæP¢÷"6÷W&6Ræ6Æ75öÆWfVÂÒ–çB†ÖF6…²&ÆWfVÂ%Ò’Ò¢“ ¢&WGW&âæöæP¢6÷7BÒ6VÖçF–72ç&öw&Òæ6÷7@¢–b6÷7Bç67&–f–6Uö÷F†W%öæöæÆæB÷"6÷7Bç67&–f–6Uö÷F†W%ö7&VGW&Uö÷%÷Fö¶Vã ¢–b€¢6÷7Bç67&–f–6Uö÷F†W%öæöæÆæ@¢æB6÷W&6Ræöæ6U÷W%÷GW&åö7F—fF–öç2ævWB†÷&6ÆUög&vÖVçB’ÓÒ6VÆbçGW&à¢“ ¢&WGW&âæöæP¢VÆ–v–&ÆRÒGWÆR€¢W&ÖæVçBæö&¦V7Eö–@¢f÷"W&ÖæVçB–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢–bW&ÖæVçB—2æ÷B6÷W&6P¢æB6VÆbæ—5öWF†÷&—FF—fR‡W&ÖæVçBÂ&&GFÆVf–VÆB"¢æB€¢$ÆæB"æ÷B–âW&ÖæVçBçG—UöÆ–æRç7Æ—B‚"(	B"•³Òç7Æ—B‚¢–b6÷7Bç67&–f–6Uö÷F†W%öæöæÆæ@¢VÇ6RW&ÖæVçBæ—5ö7&VGW&R÷"W&ÖæVçBæ—5÷Fö¶Và¢¢¢–b÷F†W%÷67&–f–6Uö–Bæ÷B–âVÆ–v–&ÆS ¢&WGW&âæöæP¢VÆ–b÷F†W%÷67&–f–6Uö–B—2æ÷BæöæS ¢&WGW&âæöæP¢&WV—&VÖVçBÒ6VÆbæ7F—fF–öåöÖæ÷&WV—&VÖVçB†6÷7BæÖæö6÷7B¢–b&WV—&VÖVçB—2æöæS ¢&WGW&âæöæP¢&VGV6W'2Ò6VÆbåö7F—fF–öå÷Fö¶Våö6÷7E÷&VGV6W'2‡Æ–W%ö–æFW‚Â6÷W&6R¢&WV—&VÖVçBÒÖæ&WV—&VÖVçB€¢Ö‚ƒÂ&WV—&VÖVçBævVæW&–2Ò7VÒ†Ö÷VçBf÷"÷6÷W&6RÂÖ÷VçBÂ÷FW‡B–â&VGV6W'2’’À¢&WV—&VÖVçBæ6öÆ÷&VBÀ¢¢–b6÷7BçF÷6÷W&6RæB€¢6÷W&6RçFV@¢÷"€¢6÷W&6Ræ6&Bæ—5ö7&VGW&P¢æB6÷W&6Rç7VÖÖöæ–æu÷6–6°¢æBæ÷B6VÆbåö†5ö¶W—v÷&B‡6÷W&6RÂ$†7FR"¢æBæ÷B6VÆbæ†5÷FV×÷&'•ö¶W—v÷&B‡6÷W&6RÂFV×÷&'”¶W—v÷&Bä„5DR¢¢“ ¢&WGW&âæöæP¢f–Æ&ÆRÒ°¢W&ÖæVç@¢f÷"W&ÖæVçB–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢–bW&ÖæVçBæ6&Bæ—5öÆæ@¢æBæ÷BW&ÖæVçBçFV@¢æB†æ÷B6÷7BçF÷6÷W&6R÷"W&ÖæVçB—2æ÷B6÷W&6R¢Ð¢6VÆV7FVBÒ6VÆbå÷ÆåöÖæ÷v—F…öfÆöF–ær€¢Æ–W%ö–æFW‚Â&WV—&VÖVçBÂf–Æ&ÆRÂ&7F—fFUö&–Æ—G’ ¢¢–b6VÆV7FVB—2æöæS ¢&WGW&âæöæP¢öfÆöF–æuö6öÆ÷'2ÂfÆöF–æuöWfVçEö–G2Â6†÷6VâÒ6VÆV7FV@¢6÷VçFW%÷F&vWEö–BÒæöæP¢–b6÷7Bç&VÖ÷fUö6÷VçFW%÷F&vWC ¢VÆ–v–&ÆRÒGWÆR€¢W&ÖæVç@¢f÷"W&ÖæVçB–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢–b6VÆbæ—5öWF†÷&—FF—fR‡W&ÖæVçBÂ&&GFÆVf–VÆB"¢æBW&ÖæVçBæ—5ö7&VGW&P¢æBW&ÖæVçBæ6÷VçFW'2ævWB‚"³ò³"Â’â ¢¢öffW&VBÒGWÆR‡6÷'FVB‡W&ÖæVçBæö&¦V7Eö–Bf÷"W&ÖæVçB–âVÆ–v–&ÆR’¢–bæ÷BöffW&VC ¢&WGW&âæöæP¢6÷VçFW%÷F&vWEö–BÒ6VÆbæ6÷VçFW%÷F&vWEö6†ö÷6W"‡Æ–W%ö–æFW‚Â6÷W&6Ræö&¦V7Eö–BÂöffW&VB¢–b6÷VçFW%÷F&vWEö–Bæ÷B–âöffW&VC ¢&—6RfÇVTW'&÷"‚&6÷VçFW"Ö6÷7BF&vWB6†ö÷6W"×W7B&WGW&ââVÆ–v–&ÆR7&VGW&R"¢&WGW&â7F—fF–öå–ÖVçEÆâ€¢Æ–W%ö–æFW‚À¢6÷W&6Ræö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçBÀ¢&WV—&VÖVçBÀ¢GWÆR‡W&ÖæVçBæö&¦V7Eö–Bf÷"W&ÖæVçB–â6†÷6Vâ’À¢6÷7BçF÷6÷W&6RÀ¢6÷7Bç67&–f–6U÷6÷W&6RÀ¢6÷VçFW%÷F&vWEö–BÀ¢fÆöF–æuöWfVçEö–G2À¢÷F†W%÷67&–f–6Uö–BÀ¢GWÆR‡&VGV6W"æö&¦V7Eö–Bf÷"&VGV6W"ÂöÖ÷VçBÂ÷FW‡B–â&VGV6W'2’À¢ ¢FVbÆVvÅö7F—fFVEö&–Æ—G•ö7F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢""$vVæW&FR&÷VæFVBVæv–æRÖ÷væVB7F—fF–öâ÷F–öç2f÷"F†R7W'&VçB&–÷&—G’v–æF÷râ"" ¢–b€¢Æ–W%ö–æFW‚Ò6VÆbæ7F—fU÷Æ–W ¢÷"6VÆbç7FWæ÷B–âµGW&å7FWå$T4ôÔ$EôÔ”âÂGW&å7FWåõ5D4ôÔ$EôÔ”çÐ¢÷"6VÆbç7F6°¢“ ¢&WGW&â‚¢÷F–öç3¢Æ—7E´7F–öä÷F–öåÒÒµÐ¢f÷"6÷W&6R–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆC ¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡6÷W&6Rç'VÆW5ö6&B“ ¢6VÖçF–72Ò6VÆbæ–çFW'&WFW"æ7F—fFVEö&–Æ—G•÷6VÖçF–72‡6÷W&6Ræ6&BÂg&vÖVçB¢–b6VÖçF–72—2æöæR÷"æ÷B6VÖçF–72æ6÷fW&vRægVÆÇ•÷7W÷'FVC ¢6öçF–çVP¢6÷7Eö÷F–öç2Ò€¢GWÆR€¢W&ÖæVçBæö&¦V7Eö–@¢f÷"W&ÖæVçB–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢–bW&ÖæVçB—2æ÷B6÷W&6P¢æB€¢$ÆæB"æ÷B–âW&ÖæVçBçG—UöÆ–æRç7Æ—B‚"(	B"•³Òç7Æ—B‚¢–b6VÖçF–72ç&öw&Òæ6÷7Bç67&–f–6Uö÷F†W%öæöæÆæ@¢VÇ6RW&ÖæVçBæ—5ö7&VGW&R÷"W&ÖæVçBæ—5÷Fö¶Và¢¢¢–b6VÖçF–72ç&öw&Òæ6÷7Bç67&–f–6Uö÷F†W%öæöæÆæ@¢÷"6VÖçF–72ç&öw&Òæ6÷7Bç67&–f–6Uö÷F†W%ö7&VGW&Uö÷%÷Fö¶Và¢VÇ6R„æöæRÂ¢¢f—'7Eö6÷7BÒ6÷7Eö÷F–öç5³Ò–b6÷7Eö÷F–öç2VÇ6RæöæP¢ÆâÒ6VÆbæ7F—fF–öå÷–ÖVçE÷Æâ€¢Æ–W%ö–æFW‚Â6÷W&6RÂg&vÖVçBÂ÷F†W%÷67&–f–6Uö–CÖf—'7Eö6÷7@¢¢–bÆâ—2æöæS ¢6öçF–çVP¢f—'7Eö÷F–öåö–æFW‚ÒÆVâ†÷F–öç2¢ÖæÒ6VÆbæ–çFW'&WFW"æÖæö&–Æ—G•÷&öw&Ò†g&vÖVçB¢–b€¢Öæ—2æ÷BæöæP¢æB6VÖçF–72ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäDEôÔä¢“ ¢–b6÷W&6Ræ6&Bæ—5öÆæC ¢6öçF–çVR2F†RÆæB–ÖVçBÆææW"Ç&VG’6VÆV7G2æBF2ÆæG0¢÷F–öç2æW‡FVæB€¢7F–öä÷F–öâ€¢7F–öä¶–æBä5D•dDUô$”Ä•E’À¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–C×6÷W&6Ræö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢6†ö–6Uö–G3Ò†6öÆ÷"Â’À¢¢f÷"6öÆ÷"–âÖææ6öÆ÷'0¢¢6öçF–çVP¢–b6VÖçF–72ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäÕUDtTåô4õTåDU# ¢f÷"F&vWB–â6VÆbçÆ–W'5³Òæ&GFÆVf–VÆB²6VÆbçÆ–W'5³Òæ&GFÆVf–VÆC ¢–b6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"’æBF&vWBæ—5ö7&VGW&S ¢÷F–öç2æVæB€¢7F–öä÷F–öâ€¢7F–öä¶–æBä5D•dDUô$”Ä•E’À¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–C×6÷W&6Ræö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢¢¢VÆ–b€¢6VÖçF–72ç&öw&ÒæVffV7Eö¶–æ@¢—27F—fFVDVffV7D¶–æBä4õTåDU%ôäEôä”ÔDUô%D”d5@¢“ ¢f÷"F&vWB–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆC ¢–b€¢6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"¢æB$'F–f7B"–âF&vWBçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢æB6VÆbåöÆVvÅ÷F&vWF–æu÷&÷FV7F–öâ‡F&vWBÂÆ–W%ö–æFW‚¢“ ¢÷F–öç2æVæB€¢7F–öä÷F–öâ€¢7F–öä¶–æBä5D•dDUô$”Ä•E’À¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–C×6÷W&6Ræö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢¢¢VÆ–b€¢6VÖçF–72ç&öw&ÒæVffV7Eö¶–æ@¢—27F—fFVDVffV7D¶–æBäDTÅôd•„TEôDÔtUõDõõD$tUEô5$TEU$P¢“ ¢f÷"Æ–W"–â6VÆbçÆ–W'3 ¢f÷"F&vWB–âÆ–W"æ&GFÆVf–VÆC ¢–b6VÆbåöÆVvÅö7F—fFVEöFÖvU÷F&vWB‡F&vWBÂÆ–W%ö–æFW‚“ ¢÷F–öç2æVæB€¢7F–öä÷F–öâ€¢7F–öä¶–æBä5D•dDUô$”Ä•E’À¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–C×6÷W&6Ræö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢¢¢VÆ–b€¢6VÖçF–72ç&öw&ÒæVffV7Eö¶–æ@¢—27F—fFVDVffV7D¶–æBå$UEU$åôäõD„U%ô5$TEU$Uõ”õUô4ôåE$ôÅõDõôõtäU%5ô„ä@¢“ ¢f÷"F&vWB–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆC ¢–bF&vWB—26÷W&6R÷"æ÷BF&vWBæ—5ö7&VGW&S ¢6öçF–çVP¢÷F–öç2æVæB€¢7F–öä÷F–öâ€¢7F–öä¶–æBä5D•dDUô$”Ä•E’À¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–C×6÷W&6Ræö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢¢¢VÆ–b6VÖçF–72ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäED4…ôUT•ÔTåC ¢f÷"F&vWB–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆC ¢–b€¢F&vWBæ—5ö7&VGW&P¢æBF&vWBæ6öçG&öÆÆW"ÓÒÆ–W%ö–æFW€¢æB6VÆbåöÆVvÅ÷F&vWF–æu÷&÷FV7F–öâ‡F&vWBÂÆ–W%ö–æFW‚¢“ ¢÷F–öç2æVæB€¢7F–öä÷F–öâ€¢7F–öä¶–æBä5D•dDUô$”Ä•E’À¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–C×6÷W&6Ræö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢6÷7Eöö&¦V7Eö–CÖf—'7Eö6÷7BÀ¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢¢¢VÇ6S ¢÷F–öç2æVæB€¢7F–öä÷F–öâ€¢7F–öä¶–æBä5D•dDUô$”Ä•E’À¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–C×6÷W&6Ræö&¦V7Eö–BÀ¢6÷7Eöö&¦V7Eö–CÖf—'7Eö6÷7BÀ¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢¢¢–b€¢6VÖçF–72ç&öw&Òæ6÷7Bç67&–f–6Uö÷F†W%öæöæÆæ@¢÷"6VÖçF–72ç&öw&Òæ6÷7Bç67&–f–6Uö÷F†W%ö7&VGW&Uö÷%÷Fö¶Và¢“ ¢6†÷6VâÒGWÆR†÷F–öç5¶f—'7Eö÷F–öåö–æFWƒ¥Ò¢f÷"FF—F–öæÅö6÷7B–â6÷7Eö÷F–öç5³¥Ó ¢÷F–öç2æW‡FVæB€¢&WÆ6R†÷F–öâÂ6÷7Eöö&¦V7Eö–CÖFF—F–öæÅö6÷7B’f÷"÷F–öâ–â6†÷6Và¢¢&WGW&âGWÆR†÷F–öç2 ¢FVböÆVvÅö7F—fFVEöFÖvU÷F&vWB‡6VÆbÂF&vWC¢ö&¦V7BÂ6öçG&öÆÆW#¢–çB’Óâ&ööÃ ¢&WGW&â€¢—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢æB6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"¢æBF&vWBæ—5ö7&VGW&P¢æB6VÆbåöÆVvÅ÷F&vWF–æu÷&÷FV7F–öâ‡F&vWBÂ6öçG&öÆÆW"¢ ¢FVbÆVvÅöÖæö&–Æ—G•ö7F–öç2€¢6VÆbÂÆ–W%ö–æFWƒ¢–çBÂ¢Â&–÷&—G“¢&ööÂÒfÇ6P¢’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢""$Öæ&–Æ—F–W2&RÆVvÂGW&–ærâ÷&F–æ'’&–÷&—G’v–æF÷rv—F†÷WBF†R7F6²â"" ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–bæ÷B&–÷&—G’÷"7FFR—2æöæR÷"7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFWƒ ¢&WGW&â‚¢&WGW&âGWÆR€¢7F–öä÷F–öâ€¢7F–öä¶–æBä5D•dDUô$”Ä•E’À¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–C×6÷W&6Ræö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢&–÷&—G•öWö6ƒ×7FFRæWö6‚À¢6†ö–6Uö–G3Ò†6öÆ÷"Â’À¢¢f÷"6÷W&6R–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡6÷W&6Rç'VÆW5ö6&B¢f÷"Öæ–â‡6VÆbæ–çFW'&WFW"æÖæö&–Æ—G•÷&öw&Ò†g&vÖVçB’Â¢–bÖæ—2æ÷BæöæP¢æBæ÷B6÷W&6Ræ6&Bæ—5öÆæ@¢æB6VÆbæ7F—fF–öå÷–ÖVçE÷Æâ‡Æ–W%ö–æFW‚Â6÷W&6RÂg&vÖVçB’—2æ÷BæöæP¢f÷"6öÆ÷"–âÖææ6öÆ÷'0¢ ¢FVbÆVvÅö†æEö7F—fFVEö&–Æ—G•ö7F–öç2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâGWÆU´7F–öä÷F–öâÂââåÓ ¢""$öffW"÷&6ÆRÖFW&—fVBÆæF7–6Æ–ærg&öÒ†æBB—G2÷&F–æ'’–ç7FçBF–Ö–ærâ"" ¢&WGW&âGWÆR€¢7F–öä÷F–öâ€¢7F–öä¶–æBä5D•dDUô$”Ä•E’À¢Æ–W%ö–æFW‚À¢ö&¦V7Eö–CÖ6&Bæö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢&–÷&—G•öWö6ƒ×6VÆbç&–÷&—G•÷7FFRæWö6‚–b6VÆbç&–÷&—G•÷7FFRVÇ6RæöæRÀ¢¢f÷"6&B–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ†æ@¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2†6&Bæ6&B¢–b6VÆbåö†æEö7F—fF–öåöÖæ÷6÷W&6W2‡Æ–W%ö–æFW‚Â6&BÂg&vÖVçB’—2æ÷BæöæP¢ ¢FVbö†æEö7F—fF–öåöÖæ÷6÷W&6W2€¢6VÆbÂÆ–W%ö–æFWƒ¢–çBÂ6&C¢6&Dö&¦V7BÂg&vÖVçC¢7G ¢’ÓâGWÆU·GWÆUµW&ÖæVçBÂââåÒÂGWÆU·7G"ÂââåÕÒÂæöæS ¢–b€¢æ÷B6VÆbæ—5öWF†÷&—FF—fR†6&BÂ&†æB"¢÷"6&Bæ÷væW"ÒÆ–W%ö–æFW€¢÷"Æ–W%ö–æFW‚æ÷B–â&ævRƒ"¢“ ¢&WGW&âæöæP¢6VÖçF–72Ò6VÆbæ–çFW'&WFW"æ7F—fFVEö&–Æ—G•÷6VÖçF–72†6&Bæ6&BÂg&vÖVçB¢–b€¢g&vÖVçBæ÷B–â6VÆbæ–çFW'&WFW"æg&vÖVçG2†6&Bæ6&B¢÷"6VÖçF–72—2æöæP¢÷"æ÷B6VÖçF–72æ6÷fW&vRægVÆÇ•÷7W÷'FV@¢÷"6VÖçF–72ç&öw&ÒæVffV7Eö¶–æB—2æ÷B7F—fFVDVffV7D¶–æBå4T$4…ôÄäEõE•P¢÷"æ÷B6VÖçF–72ç&öw&Òæ6÷7BæF—66&E÷6÷W&6P¢“ ¢&WGW&âæöæP¢&WV—&VÖVçBÒ6VÆbæ7F—fF–öåöÖæ÷&WV—&VÖVçB‡6VÖçF–72ç&öw&Òæ6÷7BæÖæö6÷7B¢–b&WV—&VÖVçB—2æöæS ¢&WGW&âæöæP¢f–Æ&ÆRÒ°¢Ææ@¢f÷"ÆæB–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢–bÆæBæ6&Bæ—5öÆæBæBæ÷BÆæBçFVBæB6VÆbæ—5öWF†÷&—FF—fR†ÆæBÂ&&GFÆVf–VÆB"¢Ð¢6VÆV7FVBÒ6VÆbå÷ÆåöÖæ÷v—F…öfÆöF–ær€¢Æ–W%ö–æFW‚Â&WV—&VÖVçBÂf–Æ&ÆRÂ&7F—fFUö&–Æ—G’ ¢¢–b6VÆV7FVB—2æöæS ¢&WGW&âæöæP¢öfÆöF–ærÂWfVçEö–G2Â6†÷6VâÒ6VÆV7FV@¢&WGW&âGWÆR†6†÷6Vâ’ÂWfVçEö–G0 ¢FVbææ÷Væ6Uö†æEö7F—fFVEö&–Æ—G’€¢6VÆbÂÆ–W%ö–æFWƒ¢–çBÂ6&C¢6&Dö&¦V7BÂg&vÖVçC¢7G ¢’Óâ7F—fFVD&–Æ—G”ö&¦V7BÂæöæS ¢""%’ÖææBF—66&B2öæRWF†÷&—FF—fR†æB7F—fF–öâG&ç67F–öââ"" ¢–b€¢6VÆbç&–÷&—G•÷7FFR—2æöæP¢æB€¢Æ–W%ö–æFW‚Ò6VÆbæ7F—fU÷Æ–W ¢÷"6VÆbç7FWæ÷B–âµGW&å7FWå$T4ôÔ$EôÔ”âÂGW&å7FWåõ5D4ôÔ$EôÔ”çÐ¢÷"6VÆbç7F6°¢¢’÷"€¢6VÆbç&–÷&—G•÷7FFR—2æ÷BæöæP¢æB€¢6VÆbç&–÷&—G•÷7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFW€¢÷"6VÆbç&–÷&—G•÷7FFRç&W6öÇWF–öå÷VæF–æp¢¢“ ¢&WGW&âæöæP¢–ÖVçBÒ6VÆbåö†æEö7F—fF–öåöÖæ÷6÷W&6W2‡Æ–W%ö–æFW‚Â6&BÂg&vÖVçB¢–b–ÖVçB—2æöæS ¢&WGW&âæöæP¢ÆæG2ÂfÆöF–æuöWfVçEö–G2Ò–ÖVç@¢6VÖçF–72Ò6VÆbæ–çFW'&WFW"æ7F—fFVEö&–Æ—G•÷6VÖçF–72†6&Bæ6&BÂg&vÖVçB¢76W'B6VÖçF–72—2æ÷BæöæP¢÷væW"Ò6VÆbçÆ–W'5¶6&Bæ÷væW%Ð¢†æEö–æFW‚Ò÷væW"æ†æBæ–æFW‚†6&B¢&Wf–÷W5öçVÖ&W"Ò6VÆbåöæW‡Eöö&¦V7EöçVÖ&W ¢&Wf–÷W5÷F2ÒGWÆR†ÆæBçFVBf÷"ÆæB–âÆæG2¢F—66&FVBÒæöæP¢&–Æ—G’ÒæöæP¢G'“ ¢F—66&FVBÒ6&Dö&¦V7B€¢6VÆbåöÆÆö6FUöö&¦V7Eö–B‚’Â6&Bæ6&BÂ6&Bæ÷væW"Â6&Bæ÷væW"Â&w&fW–&B ¢¢&–Æ—G’Ò7F—fFVD&–Æ—G”ö&¦V7B€¢6VÆbåöÆÆö6FUöö&¦V7Eö–B‚’À¢Æ–W%ö–æFW‚À¢6&Bæö&¦V7Eö–BÀ¢6&Bæ6&BÀ¢g&vÖVçBÀ¢6VÖçF–72ç&öw&ÒÀ¢GWÆR†ÆæBæö&¦V7Eö–Bf÷"ÆæB–âÆæG2’À¢fÇ6RÀ¢F—66&FVEöFW7F–æF–öåö–CÖF—66&FVBæö&¦V7Eö–BÀ¢¢f÷"ÆæB–âÆæG3 ¢ÆæBçFVBÒG'VP¢÷væW"æ†æBç÷††æEö–æFW‚¢÷væW"æw&fW–&BæVæB†F—66&FVB¢6&Bç¦öæRÒ&f÷&ÖW" ¢6VÆbå÷&Vv—7FW"†F—66&FVB¢6VÆbå÷&Vv—7FW"†&–Æ—G’¢6VÆbç7F6²æVæB†&–Æ—G’¢W†6WBW†6WF–öã ¢f÷"ÆæBÂFVB–â¦—†ÆæG2Â&Wf–÷W5÷F2Â7G&–7CÕG'VR“ ¢ÆæBçFVBÒFV@¢–bF—66&FVB—2æ÷BæöæS ¢÷væW"æw&fW–&E³¥ÒÒ¶—FVÒf÷"—FVÒ–â÷væW"æw&fW–&B–b—FVÒ—2æ÷BF—66&FVEÐ¢6VÆbåöö&¦V7G2ç÷†F—66&FVBæö&¦V7Eö–BÂæöæR¢–b6&Bæ÷B–â÷væW"æ†æC ¢÷væW"æ†æBæ–ç6W'B††æEö–æFW‚Â6&B¢6&Bç¦öæRÒ&†æB ¢–b&–Æ—G’—2æ÷BæöæS ¢6VÆbç7F6µ³¥ÒÒ¶—FVÒf÷"—FVÒ–â6VÆbç7F6²–b—FVÒ—2æ÷B&–Æ—G•Ð¢6VÆbåöö&¦V7G2ç÷†&–Æ—G’æö&¦V7Eö–BÂæöæR¢6VÆbåöæW‡Eöö&¦V7EöçVÖ&W"Ò&Wf–÷W5öçVÖ&W ¢&—6P¢6VÆbæfÆöF–æuöÖææ6öç7VÖUöWfVçG2€¢Æ–W%ö–æFW‚ÂfÆöF–æuöWfVçEö–G2Â&–Æ—G’æö&¦V7Eö–BÂ&7F—fFUö&–Æ—G’ ¢¢6VÆbæ7F—fF–öåöWf–FVæ6RæVæB€¢7F—fF–öäWf–FVæ6R€¢&–Æ—G’æö&¦V7Eö–BÀ¢6&Bæö&¦V7Eö–BÀ¢Æ–W%ö–æFW‚À¢g&vÖVçBÀ¢&–Æ—G’æÖæ÷6÷W&6Uö–G2À¢fÇ6RÀ¢fÇ6RÀ¢¢¢6VÆbæÆör€¢'¦öæUö6†ævVB"À¢6&CÖ6&BææÖRÀ¢÷væW#Ö÷væW"ææÖRÀ¢6÷W&6Uöö&¦V7Eö–CÖ6&Bæö&¦V7Eö–BÀ¢FW7F–æF–öåöö&¦V7Eö–CÖF—66&FVBæö&¦V7Eö–BÀ¢6÷W&6U÷¦öæSÒ&†æB"À¢FW7F–æF–öå÷¦öæSÒ&w&fW–&B"À¢&V6öãÒ&ÆæF7–6Æ–æuöF—66&Eö6÷7B"À¢¢6VÆbæÆör€¢&7F—fF–öåö6÷7E÷–B"À¢Æ–W#Ö÷væW"ææÖRÀ¢6÷W&6Uö–CÖ6&Bæö&¦V7Eö–BÀ¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢vVæW&–3×6VÖçF–72ç&öw&Òæ6÷7BæÖæö6÷7BÀ¢Öæ÷6÷W&6Uö–G3ÖÆ—7B†&–Æ—G’æÖæ÷6÷W&6Uö–G2’À¢fÆöF–æuöWfVçEö–G3ÖÆ—7B†fÆöF–æuöWfVçEö–G2’À¢F—66&E÷6÷W&6SÕG'VRÀ¢F—66&FVEöFW7F–æF–öåö–CÖF—66&FVBæö&¦V7Eö–BÀ¢¢6VÆbæÆör€¢&7F—fF–öåöææ÷Væ6VB"À¢Æ–W#Ö÷væW"ææÖRÀ¢6÷W&6SÖ6&BææÖRÀ¢6÷W&6Uö–CÖ6&Bæö&¦V7Eö–BÀ¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‚¢&WGW&â&–Æ—G ¢FVbææ÷Væ6Uöw&fW–&Eö7F—fFVEö&–Æ—G’€¢6VÆbÂÆ–W%ö–æFWƒ¢–çBÂ6÷W&6S¢6&Dö&¦V7BÂ÷&6ÆUög&vÖVçC¢7G ¢’Óâ7F—fFVD&–Æ—G”ö&¦V7BÂæöæS ¢–b€¢Æ–W%ö–æFW‚æ÷B–â&ævRƒ"¢÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR‡6÷W&6RÂ&w&fW–&B"¢÷"6÷W&6Ræ÷væW"ÒÆ–W%ö–æFW€¢÷"6VÆbç7FWæ÷B–âµGW&å7FWå$T4ôÔ$EôÔ”âÂGW&å7FWåõ5D4ôÔ$EôÔ”çÐ¢“ ¢&WGW&âæöæP¢6VÖçF–72Ò6VÆbæ–çFW'&WFW"æ7F—fFVEö&–Æ—G•÷6VÖçF–72‡6÷W&6Ræ6&BÂ÷&6ÆUög&vÖVçB¢–b€¢6VÖçF–72—2æöæP¢÷"æ÷B6VÖçF–72æ6÷fW&vRægVÆÇ•÷7W÷'FV@¢÷"6VÖçF–72ç&öw&ÒæVffV7Eö¶–æ@¢—2æ÷B7F—fFVDVffV7D¶–æBå$UEU$åõ4TÄeôe$ôÕôu$dU”$EõDT@¢“ ¢&WGW&âæöæP¢f–Æ&ÆRÒ°¢f÷"–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆB–bæ6&Bæ—5öÆæBæBæ÷BçFV@¢Ð¢&Æ6²ÒæW‡B‚‡f÷"–âf–Æ&ÆR–b$""–â6VÆbåöÖæö6öÆ÷'2‡’’ÂæöæR¢–b&Æ6²—2æöæR÷"ÆVâ†f–Æ&ÆR’ÂS ¢&WGW&âæöæP¢6†÷6VâÒ¶&Æ6µÒ²·f÷"–âf–Æ&ÆR–b—2æ÷B&Æ6µÕ³£EÐ¢f÷"–â6†÷6Vã ¢çFVBÒG'VP¢&–Æ—G’Ò7F—fFVD&–Æ—G”ö&¦V7B€¢6VÆbåöÆÆö6FUöö&¦V7Eö–B‚’À¢Æ–W%ö–æFW‚À¢6÷W&6Ræö&¦V7Eö–BÀ¢6÷W&6Ræ6&BÀ¢÷&6ÆUög&vÖVçBÀ¢6VÖçF–72ç&öw&ÒÀ¢GWÆR‡æö&¦V7Eö–Bf÷"–â6†÷6Vâ’À¢fÇ6RÀ¢fÇ6RÀ¢¢6VÆbå÷&Vv—7FW"†&–Æ—G’¢6VÆbç7F6²æVæB†&–Æ—G’¢6÷W&6Rç¦öæRÒ&f÷&ÖW" ¢6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæw&fW–&Bç&VÖ÷fR‡6÷W&6R¢6VÆbæ7F—fF–öåöWf–FVæ6RæVæB€¢7F—fF–öäWf–FVæ6R€¢&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Ræö&¦V7Eö–BÀ¢Æ–W%ö–æFW‚À¢÷&6ÆUög&vÖVçBÀ¢&–Æ—G’æÖæ÷6÷W&6Uö–G2À¢fÇ6RÀ¢fÇ6RÀ¢¢¢6VÆbæÆör€¢&w&fW–&Eö&–Æ—G•öææ÷Væ6VB"À¢6÷W&6Uö–C×6÷W&6Ræö&¦V7Eö–BÀ¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢&V6öãÒ'GVææVÅ÷&G5÷&WGW&â"À¢¢&WGW&â&–Æ—G ¢FVbææ÷Væ6Uö7F—fFVEö&–Æ—G’€¢6VÆbÀ¢Æ–W%ö–æFWƒ¢–çBÀ¢6÷W&6S¢W&ÖæVçBÀ¢÷&6ÆUög&vÖVçC¢7G"À¢¢À¢F&vWEö–G3¢GWÆU·7G"ÂââåÒÒ‚’À¢6†ö–6Uö–G3¢GWÆU·7G"ÂââåÒÒ‚’À¢÷F†W%÷67&–f–6Uö–C¢7G"ÂæöæRÒæöæRÀ¢’Óâ7F—fFVD&–Æ—G”ö&¦V7BÂæöæS ¢""%&WfÆ–FFRÂG&ç67F–öæÆÇ’’ÂæBWBöæR7F—fFVB&–Æ—G’öâF†R7F6²â"" ¢–b€¢æ÷B6VÆbæ—5öWF†÷&—FF—fR‡6÷W&6RÂ&&GFÆVf–VÆB"¢÷"‡6VÆbç&–÷&—G•÷7FFR—2æ÷BæöæRæB6VÆbç&–÷&—G•÷7FFRç&W6öÇWF–öå÷VæF–ær¢÷"€¢Æ–W%ö–æFW‚Ò6VÆbæ7F—fU÷Æ–W ¢æBæ÷B€¢6VÆbç&–÷&—G•÷7FFR—2æ÷BæöæP¢æB6VÆbç&–÷&—G•÷7FFRçÆ–W%ö–æFW‚ÓÒÆ–W%ö–æFW€¢¢¢÷"€¢6VÆbç7F6°¢æBæ÷B€¢6VÆbç&–÷&—G•÷7FFR—2æ÷BæöæP¢æB6VÆbç&–÷&—G•÷7FFRçÆ–W%ö–æFW‚ÓÒÆ–W%ö–æFW€¢¢¢÷"6÷W&6Ræ6öçG&öÆÆW"ÒÆ–W%ö–æFW€¢“ ¢&WGW&âæöæP¢–b÷&6ÆUög&vÖVçBæ÷B–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡6÷W&6Rç'VÆW5ö6&B“ ¢&WGW&âæöæP¢6VÖçF–72Ò6VÆbæ–çFW'&WFW"æ7F—fFVEö&–Æ—G•÷6VÖçF–72‡6÷W&6Ræ6&BÂ÷&6ÆUög&vÖVçB¢–b6VÖçF–72—2æöæR÷"æ÷B6VÖçF–72æ6÷fW&vRægVÆÇ•÷7W÷'FVC ¢&WGW&âæöæP¢–b6VÖçF–72ç&öw&Òæ6÷7BæF—66&E÷6÷W&6S ¢&WGW&âæöæP¢–b6VÖçF–72ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäEdä4Uô4Ä55ôÄUdTÂæB€¢6VÆbç&–÷&—G•÷7FFR—2æ÷BæöæP¢÷"6VÆbç7FWæ÷B–âµGW&å7FWå$T4ôÔ$EôÔ”âÂGW&å7FWåõ5D4ôÔ$EôÔ”çÐ¢“ ¢&WGW&âæöæP¢–b6VÖçF–72ç&öw&Òæ7F—fF–öåö–ç7G'V7F–öç2ÓÒ$7F—fFRöæÇ’26÷&6W'’â"æB€¢Æ–W%ö–æFW‚Ò6VÆbæ7F—fU÷Æ–W ¢÷"6VÆbç7FWæ÷B–âµGW&å7FWå$T4ôÔ$EôÔ”âÂGW&å7FWåõ5D4ôÔ$EôÔ”çÐ¢÷"6VÆbç7F6°¢÷"6VÆbç&–÷&—G•÷7FFR—2æ÷BæöæP¢“ ¢&WGW&âæöæP¢–b6VÖçF–72ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäED4…ôUT•ÔTåBæB€¢Æ–W%ö–æFW‚Ò6VÆbæ7F—fU÷Æ–W ¢÷"6VÆbç7FWæ÷B–âµGW&å7FWå$T4ôÔ$EôÔ”âÂGW&å7FWåõ5D4ôÔ$EôÔ”çÐ¢÷"6VÆbç7F6°¢÷"6VÆbç&–÷&—G•÷7FFR—2æ÷BæöæP¢“ ¢&WGW&âæöæP¢6÷VçFW%÷F&vWBÒ6VÖçF–72ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBä4õTåDU%õD$tUEõ5TÄÀ¢×WFvVåö6÷VçFW"Ò6VÖçF–72ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäÕUDtTåô4õTåDU ¢6÷VçFW%öæEöæ–ÖFRÒ€¢6VÖçF–72ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBä4õTåDU%ôäEôä”ÔDUô%D”d5@¢¢F&vWFVE÷&WGW&âÒ€¢6VÖçF–72ç&öw&ÒæVffV7Eö¶–æ@¢—27F—fFVDVffV7D¶–æBå$UEU$åôäõD„U%ô5$TEU$Uõ”õUô4ôåE$ôÅõDõôõtäU%5ô„ä@¢¢F&vWFVEöWV—ÖVçBÒ6VÖçF–72ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäED4…ôUT•ÔTå@¢F&vWFVEöFÖvRÒ€¢6VÖçF–72ç&öw&ÒæVffV7Eö¶–æ@¢—27F—fFVDVffV7D¶–æBäDTÅôd•„TEôDÔtUõDõõD$tUEô5$TEU$P¢¢Öæö&–Æ—G’Ò6VÆbæ–çFW'&WFW"æÖæö&–Æ—G•÷&öw&Ò†÷&6ÆUög&vÖVçB¢–bÖæö&–Æ—G’—2æöæRæB†6†ö–6Uö–G2÷"6VÖçF–72ç&öw&Òæ6†ö–6W5÷&WV—&VB“ ¢&WGW&âæöæP¢–bÖæö&–Æ—G’—2æ÷BæöæRæB6†ö–6Uö–G2æ÷B–â°¢†6öÆ÷"Â’f÷"6öÆ÷"–âÖæö&–Æ—G’æ6öÆ÷'0¢Ó ¢&WGW&âæöæP¢–b6÷VçFW%÷F&vWC ¢–bÆVâ‡F&vWEö–G2’Ò÷"æ÷B6VÆbåö—5öÆVvÅö6÷VçFW%÷F&vWB€¢6VÆbåöö&¦V7G2ævWB‡F&vWEö–G5³Ò’ÂÆ–W%ö–æFW€¢“ ¢&WGW&âæöæP¢VÆ–b×WFvVåö6÷VçFW# ¢–bÆVâ‡F&vWEö–G2’Ò ¢&WGW&âæöæP¢F&vWBÒ6VÆbåöö&¦V7G2ævWB‡F&vWEö–G5³Ò¢–b€¢æ÷B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"¢÷"æ÷BF&vWBæ—5ö7&VGW&P¢“ ¢&WGW&âæöæP¢VÆ–b6÷VçFW%öæEöæ–ÖFS ¢–bÆVâ‡F&vWEö–G2’Ò ¢&WGW&âæöæP¢F&vWBÒ6VÆbåöö&¦V7G2ævWB‡F&vWEö–G5³Ò¢–b€¢æ÷B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"¢÷"F&vWBæ6öçG&öÆÆW"ÒÆ–W%ö–æFW€¢÷"$'F–f7B"æ÷B–âF&vWBçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢÷"æ÷B6VÆbåöÆVvÅ÷F&vWF–æu÷&÷FV7F–öâ‡F&vWBÂÆ–W%ö–æFW‚¢“ ¢&WGW&âæöæP¢VÆ–bF&vWFVE÷&WGW&ã ¢–bÆVâ‡F&vWEö–G2’Ò ¢&WGW&âæöæP¢F&vWBÒ6VÆbåöö&¦V7G2ævWB‡F&vWEö–G5³Ò¢–b€¢æ÷B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"¢÷"F&vWB—26÷W&6P¢÷"F&vWBæ6öçG&öÆÆW"ÒÆ–W%ö–æFW€¢÷"æ÷BF&vWBæ—5ö7&VGW&P¢“ ¢&WGW&âæöæP¢VÆ–bF&vWFVEöWV—ÖVçC ¢–bÆVâ‡F&vWEö–G2’Ò ¢&WGW&âæöæP¢F&vWBÒ6VÆbåöö&¦V7G2ævWB‡F&vWEö–G5³Ò¢–b€¢æ÷B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"¢÷"F&vWBæ6öçG&öÆÆW"ÒÆ–W%ö–æFW€¢÷"æ÷BF&vWBæ—5ö7&VGW&P¢÷"æ÷B6VÆbåöÆVvÅ÷F&vWF–æu÷&÷FV7F–öâ‡F&vWBÂÆ–W%ö–æFW‚¢“ ¢&WGW&âæöæP¢VÆ–bF&vWFVEöFÖvS ¢–bÆVâ‡F&vWEö–G2’Ò÷"æ÷B6VÆbåöÆVvÅö7F—fFVEöFÖvU÷F&vWB€¢6VÆbåöö&¦V7G2ævWB‡F&vWEö–G5³Ò’ÂÆ–W%ö–æFW€¢“ ¢&WGW&âæöæP¢VÆ–bF&vWEö–G2÷"6VÖçF–72ç&öw&ÒçF&vWEö6÷VçC ¢&WGW&âæöæP¢ÆâÒ6VÆbæ7F—fF–öå÷–ÖVçE÷Æâ€¢Æ–W%ö–æFW‚Â6÷W&6RÂ÷&6ÆUög&vÖVçBÂ÷F†W%÷67&–f–6Uö–CÖ÷F†W%÷67&–f–6Uö–@¢¢–bÆâ—2æöæS ¢&WGW&âæöæP¢÷F†W%÷67&–f–6RÒ6VÆbåöö&¦V7G2ævWB‡Æâæ÷F†W%÷67&–f–6Uö–B÷"""¢–bÆâæ÷F†W%÷67&–f–6Uö–B—2æ÷BæöæRæBæ÷B—6–ç7Fæ6R†÷F†W%÷67&–f–6RÂW&ÖæVçB“ ¢&WGW&âæöæP¢Öæ÷6÷W&6W3¢Æ—7EµW&ÖæVçEÒÒµÐ¢f÷"ö&¦V7Eö–B–âÆâæÖæ÷6÷W&6Uö–G3 ¢6æF–FFRÒ6VÆbåöö&¦V7G2ævWB†ö&¦V7Eö–B¢–bæ÷B—6–ç7Fæ6R†6æF–FFRÂW&ÖæVçB’÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR€¢6æF–FFRÂ&&GFÆVf–VÆB ¢“ ¢&—6RfÇVTW'&÷"‚&7F—fF–öâÖæ6÷W&6R—2æ÷BWF†÷&—FF—fR"¢Öæ÷6÷W&6W2æVæB†6æF–FFR¢–bÆVâ‡¶6æF–FFRæö&¦V7Eö–Bf÷"6æF–FFR–âÖæ÷6÷W&6W7Ò’ÒÆVâ†Öæ÷6÷W&6W2“ ¢&—6RfÇVTW'&÷"‚&7F—fF–öâ–ÖVçB6ææ÷B&WW6RÖæ6÷W&6R"¢&–÷%öÖæ÷F2ÒGWÆR†6æF–FFRçFVBf÷"6æF–FFR–âÖæ÷6÷W&6W2¢&–÷%÷6÷W&6U÷FVBÒ6÷W&6RçFV@¢6÷VçFW%÷F&vWBÒ€¢6VÆbåöö&¦V7G2ævWB‡Æâæ6÷VçFW%÷F&vWEö–B’–bÆâæ6÷VçFW%÷F&vWEö–BVÇ6RæöæP¢¢&–÷%ö6÷VçFW%ö6÷VçBÒ€¢6÷VçFW%÷F&vWBæ6÷VçFW'2ævWB‚"³ò³"Â¢–b—6–ç7Fæ6R†6÷VçFW%÷F&vWBÂW&ÖæVçB¢VÇ6RæöæP¢¢7F'F–æuöö&¦V7EöçVÖ&W"Ò6VÆbåöæW‡Eöö&¦V7EöçVÖ&W ¢6÷W&6Uö–æFW‚Ò6VÆbçÆ–W'5·6÷W&6Ræ6öçG&öÆÆW%Òæ&GFÆVf–VÆBæ–æFW‚‡6÷W&6R¢WF–Æ—G•öÆVfW2Ò€¢GWÆR€¢g&vÖVç@¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡6÷W&6Rç'VÆW5ö6&B¢–b‡WF–Æ—G’£Ò6VÆbæ–çFW'&WFW"çWF–Æ—G•÷G&–vvW%÷6VÖçF–72‡6÷W&6Ræ6&BÂg&vÖVçB’¢—2æ÷BæöæP¢æBWF–Æ—G•³ÒÓÒ&VçG'•ö÷%öÆVfR ¢¢–bÆâç67&–f–6U÷6÷W&6P¢VÇ6R‚¢¢FW'GW&UöWF†÷&—G’Ò€¢6VÆbåö&GFÆVf–VÆEöWF†÷&—G•÷6æ6†÷B‚’–bÆâç67&–f–6U÷6÷W&6RVÇ6R‚¢¢67&–f–6VC¢6&Dö&¦V7BÂæöæRÒæöæP¢&–Æ—G“¢7F—fFVD&–Æ—G”ö&¦V7BÂæöæRÒæöæP¢G'“ ¢–bÆâç67&–f–6U÷6÷W&6S ¢67&–f–6VBÒ6&Dö&¦V7B€¢6VÆbåöÆÆö6FUöö&¦V7Eö–B‚’À¢6÷W&6Ræ6&BÀ¢6÷W&6Ræ÷væW"À¢6÷W&6Ræ÷væW"À¢&w&fW–&B"À¢—5÷Fö¶Vã×6÷W&6Ræ—5÷Fö¶VâÀ¢¢&–Æ—G’Ò7F—fFVD&–Æ—G”ö&¦V7B€¢ö&¦V7Eö–C×6VÆbåöÆÆö6FUöö&¦V7Eö–B‚’À¢6öçG&öÆÆW#×Æ–W%ö–æFW‚À¢6÷W&6Uö–C×6÷W&6Ræö&¦V7Eö–BÀ¢6÷W&6Uö6&C×6÷W&6Ræ6&BÀ¢÷&6ÆUög&vÖVçCÖ÷&6ÆUög&vÖVçBÀ¢&öw&Ó×6VÖçF–72ç&öw&ÒÀ¢Öæ÷6÷W&6Uö–G3×ÆâæÖæ÷6÷W&6Uö–G2À¢F÷6÷W&6S×ÆâçF÷6÷W&6RÀ¢67&–f–6U÷6÷W&6S×Æâç67&–f–6U÷6÷W&6RÀ¢67&–f–6VEöFW7F–æF–öåö–CÒ€¢67&–f–6VBæö&¦V7Eö–B–b67&–f–6VB—2æ÷BæöæRVÇ6RæöæP¢’À¢F&vWEö–G3×F&vWEö–G2À¢6†ö–6Uö–G3Ö6†ö–6Uö–G2À¢6÷7E÷F&vWEö–C×Æâæ6÷VçFW%÷F&vWEö–BÀ¢6÷7E÷F&vWEö6&CÒ€¢6÷VçFW%÷F&vWBæ6&B–b—6–ç7Fæ6R†6÷VçFW%÷F&vWBÂW&ÖæVçB’VÇ6RæöæP¢’À¢6÷7E÷F&vWEöö&¦V7CÖ6÷VçFW%÷F&vW@¢–b—6–ç7Fæ6R†6÷VçFW%÷F&vWBÂW&ÖæVçB¢VÇ6RæöæRÀ¢¢f÷"Öæ÷6÷W&6R–âÖæ÷6÷W&6W3 ¢Öæ÷6÷W&6RçFVBÒG'VP¢–bÆâçF÷6÷W&6S ¢6÷W&6RçFVBÒG'VP¢–bÆâæ6÷VçFW%÷F&vWEö–B—2æ÷BæöæS ¢–b€¢æ÷B—6–ç7Fæ6R†6÷VçFW%÷F&vWBÂW&ÖæVçB¢÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR†6÷VçFW%÷F&vWBÂ&&GFÆVf–VÆB"¢÷"6÷VçFW%÷F&vWBæ6öçG&öÆÆW"ÒÆ–W%ö–æFW€¢÷"æ÷B6÷VçFW%÷F&vWBæ—5ö7&VGW&P¢÷"6÷VçFW%÷F&vWBæ6÷VçFW'2ævWB‚"³ò³"Â’ÃÒ ¢“ ¢&—6RfÇVTW'&÷"‚&6÷VçFW"Ö6÷7BF&vWB&V6ÖR–ÆÆVvÂ"¢6÷VçFW%÷F&vWBæ6÷VçFW'5²"³ò³%ÒÓÒ¢–b6÷VçFW%÷F&vWBæ6÷VçFW'5²"³ò³%ÒÓÒ ¢FVÂ6÷VçFW%÷F&vWBæ6÷VçFW'5²"³ò³%Ð¢6VÆbæÆör€¢&6÷VçFW%÷&VÖ÷fVEö5ö7F—fF–öåö6÷7B"À¢6÷W&6Uö–C×6÷W&6Ræö&¦V7Eö–BÀ¢6÷7E÷F&vWEö–CÖ6÷VçFW%÷F&vWBæö&¦V7Eö–BÀ¢6÷VçFW%÷G—SÒ"³ò³"À¢6÷VçFW'5ö&Vf÷&S×&–÷%ö6÷VçFW%ö6÷VçBÀ¢6÷VçFW'5ögFW#Ö6÷VçFW%÷F&vWBæ6÷VçFW'2ævWB‚"³ò³"Â’À¢¢–b67&–f–6VB—2æ÷BæöæS ¢6VÆbçÆ–W'5·6÷W&6Ræ6öçG&öÆÆW%Òæ&GFÆVf–VÆBç÷‡6÷W&6Uö–æFW‚¢6VÆbçÆ–W'5·6÷W&6Ræ÷væW%Òæw&fW–&BæVæB‡67&–f–6VB¢6÷W&6Rç¦öæRÒ&f÷&ÖW" ¢6VÆbå÷&Vv—7FW"‡67&–f–6VB¢6VÆbå÷&Vv—7FW"†&–Æ—G’¢6VÆbç7F6²æVæB†&–Æ—G’¢W†6WBW†6WF–öã ¢f÷"Öæ÷6÷W&6RÂFVB–â¦—†Öæ÷6÷W&6W2Â&–÷%öÖæ÷F2Â7G&–7CÕG'VR“ ¢Öæ÷6÷W&6RçFVBÒFV@¢6÷W&6RçFVBÒ&–÷%÷6÷W&6U÷FV@¢–b—6–ç7Fæ6R†6÷VçFW%÷F&vWBÂW&ÖæVçB’æB&–÷%ö6÷VçFW%ö6÷VçB—2æ÷BæöæS ¢6÷VçFW%÷F&vWBæ6÷VçFW'5²"³ò³%ÒÒ&–÷%ö6÷VçFW%ö6÷Vç@¢–b67&–f–6VB—2æ÷BæöæS ¢6VÆbçÆ–W'5·6÷W&6Ræ÷væW%Òæw&fW–&E³¥ÒÒ°¢—FVÒf÷"—FVÒ–â6VÆbçÆ–W'5·6÷W&6Ræ÷væW%Òæw&fW–&B–b—FVÒ—2æ÷B67&–f–6V@¢Ð¢6VÆbåöö&¦V7G2ç÷‡67&–f–6VBæö&¦V7Eö–BÂæöæR¢–b6÷W&6Ræ÷B–â6VÆbçÆ–W'5·6÷W&6Ræ6öçG&öÆÆW%Òæ&GFÆVf–VÆC ¢6VÆbçÆ–W'5·6÷W&6Ræ6öçG&öÆÆW%Òæ&GFÆVf–VÆBæ–ç6W'B‡6÷W&6Uö–æFW‚Â6÷W&6R¢6÷W&6Rç¦öæRÒ&&GFÆVf–VÆB ¢–b&–Æ—G’—2æ÷BæöæS ¢6VÆbç7F6µ³¥ÒÒ¶VçG'’f÷"VçG'’–â6VÆbç7F6²–bVçG'’—2æ÷B&–Æ—G•Ð¢6VÆbåöö&¦V7G2ç÷†&–Æ—G’æö&¦V7Eö–BÂæöæR¢6VÆbåöæW‡Eöö&¦V7EöçVÖ&W"Ò7F'F–æuöö&¦V7EöçVÖ&W ¢&—6P¢Wf–FVæ6RÒ7F—fF–öäWf–FVæ6R€¢&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Ræö&¦V7Eö–BÀ¢Æ–W%ö–æFW‚À¢÷&6ÆUög&vÖVçBÀ¢ÆâæÖæ÷6÷W&6Uö–G2À¢ÆâçF÷6÷W&6RÀ¢fÇ6RÀ¢Æâæ6÷VçFW%÷F&vWEö–BÀ¢¢6VÆbæ7F—fF–öåöWf–FVæ6RæVæB†Wf–FVæ6R¢–b—6–ç7Fæ6R†÷F†W%÷67&–f–6RÂW&ÖæVçB“ ¢FW7F–æF–öâÒ6VÆbæÖ÷fUöö&¦V7B€¢÷F†W%÷67&–f–6RÀ¢&w&fW–&B"À¢&V6öãÒ€¢&WV—ÖVçEö7F—fF–öå÷67&–f–6Uö6÷7B ¢–b6VÖçF–72ç&öw&Òæ6÷7Bç67&–f–6Uö÷F†W%öæöæÆæ@¢VÇ6R&7F—fF–öåö÷F†W%÷67&–f–6Uö6÷7B ¢’À¢¢&–Æ—G’æ÷F†W%÷67&–f–6Uö–BÒ÷F†W%÷67&–f–6Ræö&¦V7Eö–@¢&–Æ—G’æ÷F†W%÷67&–f–6UöFW7F–æF–öåö–BÒFW7F–æF–öâæö&¦V7Eö–@¢–b6VÖçF–72ç&öw&Òæ6÷7Bç67&–f–6Uö÷F†W%öæöæÆæC ¢6÷W&6Ræöæ6U÷W%÷GW&åö7F—fF–öç5¶÷&6ÆUög&vÖVçEÒÒ6VÆbçGW&à¢6VÆbæÆör€¢&7F—fF–öåö÷F†W%÷67&–f–6U÷–B"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Uö–C×6÷W&6Ræö&¦V7Eö–BÀ¢6÷7Eöö&¦V7Eö–CÖ÷F†W%÷67&–f–6Ræö&¦V7Eö–BÀ¢FW7F–æF–öåöö&¦V7Eö–CÖFW7F–æF–öâæö&¦V7Eö–BÀ¢¢–b67&–f–6VB—2æ÷BæöæS ¢6VÆbæÆör€¢'¦öæUö6†ævVB"À¢6&C×6÷W&6Ræ6&BææÖRÀ¢÷væW#×6VÆbçÆ–W'5·6÷W&6Ræ÷væW%ÒææÖRÀ¢6÷W&6Uöö&¦V7Eö–C×6÷W&6Ræö&¦V7Eö–BÀ¢FW7F–æF–öåöö&¦V7Eö–C×67&–f–6VBæö&¦V7Eö–BÀ¢6÷W&6U÷¦öæSÒ&&GFÆVf–VÆB"À¢FW7F–æF–öå÷¦öæSÒ&w&fW–&B"À¢&V6öãÒ&7F—fF–öå÷67&–f–6Uö6÷7B"À¢¢WfVçBÒ6VÆbåöæWu÷'VÆW5öWfVçB€¢'VÆW4WfVçD¶–æBåU$ÔäTåEôÄTeBÀ¢Æ–W%ö–æFW‚À¢‡6÷W&6Ræö&¦V7Eö–BÂ’À¢6÷W&6Uö–C×6÷W&6Ræö&¦V7Eö–BÀ¢&GFÆVf–VÆEöWF†÷&—G“ÖFW'GW&UöWF†÷&—G’À¢Æ7Eö¶æ÷våö&GFÆVf–VÆCÒ€¢‡6÷W&6Ræö&¦V7Eö–BÂÆ–W%ö–æFW‚Â6÷W&6RçG—UöÆ–æRÂ6÷W&6Ræ—5ö7&VGW&R’À¢’À¢¢&–Æ—G’æFW'GW&UöWfVçEö–BÒWfVçBæWfVçEö–@¢f÷"g&vÖVçB–âWF–Æ—G•öÆVfW3 ¢6VÆbåöVçVWVU÷G&–vvW"†WfVçBÂ6÷W&6RÂg&vÖVçBÂG&–vvW$VffV7BåUD”Ä•E•õD$tUB¢6VÆbæÆör€¢&7F—fF–öåöææ÷Væ6VB"À¢Æ–W#×6VÆbçÆ–W'5·Æ–W%ö–æFW…ÒææÖRÀ¢6÷W&6S×6÷W&6Ræ6&BææÖRÀ¢6÷W&6Uö–C×6÷W&6Ræö&¦V7Eö–BÀ¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçCÖ÷&6ÆUög&vÖVçBÀ¢¢6VÆbæÆör€¢&7F—fF–öåö6÷7E÷–B"À¢Æ–W#×6VÆbçÆ–W'5·Æ–W%ö–æFW…ÒææÖRÀ¢6÷W&6Uö–C×6÷W&6Ræö&¦V7Eö–BÀ¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢vVæW&–3×Æâç&WV—&VÖVçBævVæW&–2À¢6öÆ÷&VCÖÆ—7B‡Æâç&WV—&VÖVçBæ6öÆ÷&VB’À¢Öæ÷6÷W&6Uö–G3ÖÆ—7B‡ÆâæÖæ÷6÷W&6Uö–G2’À¢fÆöF–æuöWfVçEö–G3ÖÆ—7B‡ÆâæfÆöF–æuöWfVçEö–G2’À¢F÷6÷W&6S×ÆâçF÷6÷W&6RÀ¢67&–f–6U÷6÷W&6S×Æâç67&–f–6U÷6÷W&6RÀ¢67&–f–6VEöFW7F–æF–öåö–CÒ‡67&–f–6VBæö&¦V7Eö–B–b67&–f–6VB—2æ÷BæöæRVÇ6RæöæR’À¢÷F†W%÷67&–f–6Uö–C×Æâæ÷F†W%÷67&–f–6Uö–BÀ¢¢&–çFVE÷&WV—&VÖVçBÒ6VÆbæ7F—fF–öåöÖæ÷&WV—&VÖVçB‡6VÖçF–72ç&öw&Òæ6÷7BæÖæö6÷7B¢76W'B&–çFVE÷&WV—&VÖVçB—2æ÷BæöæP¢–bÆâç&WV—&VÖVçBævVæW&–2Â&–çFVE÷&WV—&VÖVçBævVæW&–3 ¢6VÆbæÆör€¢&7F—fF–öåö6÷7E÷&VGV6VB"À¢6÷W&6Uö–C×6÷W&6Ræö&¦V7Eö–BÀ¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6öçG&öÆÆW#×Æ–W%ö–æFW‚À¢&–çFVEövVæW&–3×&–çFVE÷&WV—&VÖVçBævVæW&–2À¢–EövVæW&–3×Æâç&WV—&VÖVçBævVæW&–2À¢&VGV7F–öå÷6÷W&6Uö–G3ÖÆ—7B‡Æâç&VGV7F–öå÷6÷W&6Uö–G2’À¢÷&6ÆUög&vÖVçCÖ÷&6ÆUög&vÖVçBÀ¢¢6VÆbæfÆöF–æuöÖææ6öç7VÖUöWfVçG2€¢Æ–W%ö–æFW‚ÂÆâæfÆöF–æuöWfVçEö–G2Â&–Æ—G’æö&¦V7Eö–BÂ&7F—fFUö&–Æ—G’ ¢¢–bÖæö&–Æ—G’—2æ÷BæöæS ¢6VÆbç7F6²ç÷‚¢&–Æ—G’ç¦öæRÒ&f÷&ÖW" ¢6VÆbæ7F—fF–öåöWf–FVæ6U²ÓÒÒ&WÆ6R†Wf–FVæ6RÂ&W6öÇfVCÕG'VR¢6VÆbæfÆöF–æuöÖææFB€¢Æ–W%ö–æFW‚À¢6÷W&6Ræö&¦V7Eö–BÀ¢6†ö–6Uö–G5³ÒÀ¢À¢&–Æ—G’æö&¦V7Eö–BÀ¢Öæö&–Æ—G’æÆÆ÷vVE÷7VæF–ærÀ¢¢6VÆbæÆör€¢&fÆöF–æuöÖæ÷&öGV6VB"À¢6÷W&6Uö–C×6÷W&6Ræö&¦V7Eö–BÀ¢WfVçEö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6öÆ÷#Ö6†ö–6Uö–G5³ÒÀ¢VçF—G“ÓÀ¢ÆÆ÷vVE÷7VæF–æsÖÆ—7B†Öæö&–Æ—G’æÆÆ÷vVE÷7VæF–ær’À¢¢6VÆbæÆör€¢&Öæö&–Æ—G•÷&W6öÇfVB"Â6÷W&6Uö–C×6÷W&6Ræö&¦V7Eö–BÂWfVçEö–CÖ&–Æ—G’æö&¦V7Eö–@¢¢&WGW&â&–Æ—G¢6VÆbæÆör€¢&7F—fFVEö&–Æ—G•÷7F6¶VB"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Uö–C×6÷W&6Ræö&¦V7Eö–BÀ¢6öçG&öÆÆW#×6VÆbçÆ–W'5·Æ–W%ö–æFW…ÒææÖRÀ¢¢–b67&–f–6VB—2æ÷BæöæR÷"—6–ç7Fæ6R†÷F†W%÷67&–f–6RÂW&ÖæVçB“ ¢6VÆbæ6†V6µ÷7FFUö&6VEö7F–öç2‚¢–b6VÆbç&–÷&—G•÷7FFR—2æöæS ¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‚¢–b€¢67&–f–6VB—2æ÷BæöæP¢æB6VÖçF–72ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBät”åõD…$TUôÄ”dP¢“ ¢76W'B6VÆbç&–÷&—G•÷7FFR—2æ÷BæöæP¢6VÆbæfööEö7F—fF–öåöWf–FVæ6RæVæB€¢fööD7F—fF–öäWf–FVæ6R€¢6÷W&6Uö–C×6÷W&6Ræö&¦V7Eö–BÀ¢6÷W&6UöæÖS×6÷W&6Ræ6&BææÖRÀ¢6÷W&6U÷G—UöÆ–æS×6÷W&6Ræ6&BçG—UöÆ–æRÀ¢6÷W&6Uö÷væW#×6÷W&6Ræ÷væW"À¢6öçG&öÆÆW#×Æ–W%ö–æFW‚À¢6÷W&6U÷v5÷Fö¶Vã×6÷W&6Ræ—5÷Fö¶VâÀ¢÷&6ÆUög&vÖVçCÖ÷&6ÆUög&vÖVçBÀ¢GW&ã×6VÆbçGW&âÀ¢7FW×6VÆbç7FWçfÇVRÀ¢6÷W&6U÷¦öæUö&Vf÷&SÒ&&GFÆVf–VÆB"À¢Öæ÷&WV—&VÖVçC×Æâç&WV—&VÖVçBÀ¢Öæ÷6÷W&6Uö–G3×ÆâæÖæ÷6÷W&6Uö–G2À¢6÷W&6U÷FVEö&Vf÷&S×&–÷%÷6÷W&6U÷FVBÀ¢F÷–C×ÆâçF÷6÷W&6RÀ¢67&–f–6U÷–CÕG'VRÀ¢67&–f–6VEöFW7F–æF–öåö–C×67&–f–6VBæö&¦V7Eö–BÀ¢67&–f–6VEöFW7F–æF–öå÷¦öæSÒ&w&fW–&B"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢&–÷&—G•öWö6ƒ×6VÆbç&–÷&—G•÷7FFRæWö6‚À¢&W6öÇfVCÔfÇ6RÀ¢f–æÅ÷6÷W&6UöF—7÷6—F–öã×67&–f–6VBç¦öæRÀ¢¢¢&WGW&â&–Æ—G ¢FVb7F—fFUö&–Æ—G’€¢6VÆbÀ¢Æ–W%ö–æFWƒ¢–çBÀ¢6÷W&6S¢W&ÖæVçBÀ¢÷&6ÆUög&vÖVçC¢7G"À¢¢À¢F&vWEö–G3¢GWÆU·7G"ÂââåÒÒ‚’À¢’Óâ&ööÃ ¢""$ææ÷Væ6RöæR&–Æ—G’æB÷VâF†R&÷VæFVBVæv–æRÖ÷væVB&–÷&—G’v–æF÷râ"" ¢&–Æ—G’Ò6VÆbæææ÷Væ6Uö7F—fFVEö&–Æ—G’€¢Æ–W%ö–æFW‚Â6÷W&6RÂ÷&6ÆUög&vÖVçBÂF&vWEö–G3×F&vWEö–G0¢¢&WGW&â&–Æ—G’—2æ÷BæöæP ¢FVb÷fÆ–FFUö6÷VçFW'7VÆÅ÷&÷fVææ6R‡6VÆbÂ&–Æ—G“¢7F—fFVD&–Æ—G”ö&¦V7B’ÓâæöæS ¢–b&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—2æ÷B7F—fFVDVffV7D¶–æBä4õTåDU%õD$tUEõ5TÄÃ ¢&WGW&à¢6VÖçF–72Ò6VÆbæ–çFW'&WFW"æ7F—fFVEö&–Æ—G•÷6VÖçF–72€¢&–Æ—G’ç6÷W&6Uö6&BÂ&–Æ—G’æ÷&6ÆUög&vÖVç@¢¢6÷W&6RÒ6VÆbåöö&¦V7G2ævWB†&–Æ—G’ç6÷W&6Uö–B¢7F—fF–öâÒæW‡B€¢€¢—FVÐ¢f÷"—FVÒ–â6VÆbæ7F—fF–öåöWf–FVæ6P¢–b—FVÒç7F6µöö&¦V7Eö–BÓÒ&–Æ—G’æö&¦V7Eö–@¢’À¢æöæRÀ¢¢67&–f–6VBÒ6VÆbåöö&¦V7G2ævWB†&–Æ—G’ç67&–f–6VEöFW7F–æF–öåö–B÷"""¢–b€¢6VÖçF–72—2æöæP¢÷"æ÷B6VÖçF–72æ6÷fW&vRægVÆÇ•÷7W÷'FV@¢÷"6VÖçF–72ç&öw&ÒÒ&–Æ—G’ç&öw&Ð¢÷"7F—fF–öâ—2æöæP¢÷"7F—fF–öâç&W6öÇfVB—2æ÷BfÇ6P¢÷"7F—fF–öâç6÷W&6Uö–BÒ&–Æ—G’ç6÷W&6Uö–@¢÷"7F—fF–öâæ6öçG&öÆÆW"Ò&–Æ—G’æ6öçG&öÆÆW ¢÷"7F—fF–öâæ÷&6ÆUög&vÖVçBÒ&–Æ—G’æ÷&6ÆUög&vÖVç@¢÷"7F—fF–öâæÖæ÷6÷W&6Uö–G2Ò&–Æ—G’æÖæ÷6÷W&6Uö–G0¢÷"æ÷B&–Æ—G’ç67&–f–6U÷6÷W&6P¢÷"æ÷B—6–ç7Fæ6R‡6÷W&6RÂW&ÖæVçB¢÷"6÷W&6Ræ6&B—2æ÷B&–Æ—G’ç6÷W&6Uö6&@¢÷"6÷W&6Rç¦öæRÒ&f÷&ÖW" ¢÷"æ÷B—6–ç7Fæ6R‡67&–f–6VBÂ6&Dö&¦V7B¢÷"67&–f–6VBæ6&B—2æ÷B&–Æ—G’ç6÷W&6Uö6&@¢÷"67&–f–6VBç¦öæRÒ&w&fW–&B ¢÷"ÆVâ†&–Æ—G’çF&vWEö–G2’Ò¢÷"æ÷B—6–ç7Fæ6R‡6VÆbåöö&¦V7G2ævWB†&–Æ—G’çF&vWEö–G5³Ò’Â7F6´ö&¦V7B¢÷"6VÆbåöö&¦V7G2ævWB†&–Æ—G’çF&vWEö–G5³Ò’æö&¦V7Eö–BÒ&–Æ—G’çF&vWEö–G5³Ð¢“ ¢&—6RfÇVTW'&÷"‚&6÷VçFW"7F—fF–öâ&÷fVææ6R—2–çfÆ–B" ¢FVb÷fÆ–FFUö6÷VçFW%ö6÷7E÷&÷fVææ6R‡6VÆbÂ&–Æ—G“¢7F—fFVD&–Æ—G”ö&¦V7B’ÓâæöæS ¢–bæ÷B&–Æ—G’ç&öw&Òæ6÷7Bç&VÖ÷fUö6÷VçFW%÷F&vWC ¢&WGW&à¢F&vWBÒ6VÆbåöö&¦V7G2ævWB†&–Æ—G’æ6÷7E÷F&vWEö–B÷"""¢–b€¢&–Æ—G’æ6÷7E÷F&vWEö–B—2æöæP¢÷"&–Æ—G’æ6÷7E÷F&vWEöö&¦V7B—2æöæP¢÷"&–Æ—G’æ6÷7E÷F&vWEöö&¦V7Bæö&¦V7Eö–BÒ&–Æ—G’æ6÷7E÷F&vWEö–@¢÷"&–Æ—G’æ6÷7E÷F&vWEöö&¦V7Bæ6&B—2æ÷B&–Æ—G’æ6÷7E÷F&vWEö6&@¢÷"‡F&vWB—2æ÷BæöæRæBF&vWB—2æ÷B&–Æ—G’æ6÷7E÷F&vWEöö&¦V7B¢“ ¢&—6RfÇVTW'&÷"‚&6÷VçFW"Ö6÷7BF&vWB&÷fVææ6R—2–çfÆ–B" ¢FVb÷fÆ–FFUö÷F†W%÷67&–f–6U÷&÷fVææ6R‡6VÆbÂ&–Æ—G“¢7F—fFVD&–Æ—G”ö&¦V7B’ÓâæöæS ¢""%F†R–B7&VGW&R÷Fö¶Vâ6÷7B7W'f—fW2–æFWVæFVçFÇ’öb—G26÷W&6Râ"" ¢–bæ÷B&–Æ—G’ç&öw&Òæ6÷7Bç67&–f–6Uö÷F†W%ö7&VGW&Uö÷%÷Fö¶Vã ¢&WGW&à¢6÷W&6RÒ6VÆbåöö&¦V7G2ævWB†&–Æ—G’ç6÷W&6Uö–B¢–BÒ6VÆbåöö&¦V7G2ævWB†&–Æ—G’æ÷F†W%÷67&–f–6Uö–B÷"""¢FW7F–æF–öâÒ6VÆbåöö&¦V7G2ævWB†&–Æ—G’æ÷F†W%÷67&–f–6UöFW7F–æF–öåö–B÷"""¢7F—fF–öç2Ò°¢—FVÒf÷"—FVÒ–â6VÆbæ7F—fF–öåöWf–FVæ6R–b—FVÒç7F6µöö&¦V7Eö–BÓÒ&–Æ—G’æö&¦V7Eö–@¢Ð¢v—FæW76W2Ò°¢WfVç@¢f÷"WfVçB–â6VÆbæWfVçG0¢–bWfVçE²&WfVçB%ÒÓÒ&7F—fF–öåö÷F†W%÷67&–f–6U÷–B ¢æBWfVçE²'7F6µöö&¦V7Eö–B%ÒÓÒ&–Æ—G’æö&¦V7Eö–@¢Ð¢–b€¢ÆVâ†7F—fF–öç2’Ò¢÷"7F—fF–öç5³Òç&W6öÇfV@¢÷"7F—fF–öç5³Òç6÷W&6Uö–BÒ&–Æ—G’ç6÷W&6Uö–@¢÷"7F—fF–öç5³Òæ6öçG&öÆÆW"Ò&–Æ—G’æ6öçG&öÆÆW ¢÷"7F—fF–öç5³Òæ÷&6ÆUög&vÖVçBÒ&–Æ—G’æ÷&6ÆUög&vÖVç@¢÷"7F—fF–öç5³ÒæÖæ÷6÷W&6Uö–G2Ò&–Æ—G’æÖæ÷6÷W&6Uö–G0¢÷"æ÷B—6–ç7Fæ6R‡6÷W&6RÂW&ÖæVçB¢÷"6÷W&6Ræ6&B—2æ÷B&–Æ—G’ç6÷W&6Uö6&@¢÷"æ÷B—6–ç7Fæ6R‡–BÂW&ÖæVçB¢÷"–B—26÷W&6P¢÷"–Bç¦öæRÒ&f÷&ÖW" ¢÷"–Bæ6öçG&öÆÆW"Ò&–Æ—G’æ6öçG&öÆÆW ¢÷"æ÷B‡–Bæ—5ö7&VGW&R÷"–Bæ—5÷Fö¶Vâ¢÷"æ÷B—6–ç7Fæ6R†FW7F–æF–öâÂ6&Dö&¦V7B¢÷"FW7F–æF–öâæ6&B—2æ÷B–Bæ6&@¢÷"FW7F–æF–öâæ÷væW"Ò–Bæ÷væW ¢÷"ÆVâ‡v—FæW76W2’Ò¢÷"v—FæW76W5³Õ²&6÷7Eöö&¦V7Eö–B%ÒÒ–Bæö&¦V7Eö–@¢÷"v—FæW76W5³Õ²&FW7F–æF–öåöö&¦V7Eö–B%ÒÒFW7F–æF–öâæö&¦V7Eö–@¢“ ¢&—6RfÇVTW'&÷"‚&÷F†W"×67&–f–6R7F—fF–öâ&÷fVææ6R—2–çfÆ–B" ¢FVb÷&W6öÇfUö7F—fFVEö&–Æ—G’‡6VÆbÂ&–Æ—G“¢7F—fFVD&–Æ—G”ö&¦V7B’ÓâæöæS ¢–b€¢æ÷B6VÆbç7F6°¢÷"6VÆbç7F6µ²ÓÒ—2æ÷B&–Æ—G¢÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR†&–Æ—G’Â'7F6²"¢“ ¢&—6RfÇVTW'&÷"‚&7F—fFVB&–Æ—G’×W7B&RF†RWF†÷&—FF—fRF÷7F6²ö&¦V7B"¢–bç’†—FVÒç7F6µöö&¦V7Eö–BÓÒ&–Æ—G’æö&¦V7Eö–Bf÷"—FVÒ–â6VÆbæfööEö7F—fF–öåöWf–FVæ6R“ ¢6VÆbå÷fÆ–FFUöfööEö7F—fF–öåöÆ–æ¶vR†&–Æ—G’¢6VÆbå÷fÆ–FFUö6÷VçFW'7VÆÅ÷&÷fVææ6R†&–Æ—G’¢6VÆbå÷fÆ–FFUö6÷VçFW%ö6÷7E÷&÷fVææ6R†&–Æ—G’¢6VÆbå÷fÆ–FFUö÷F†W%÷67&–f–6U÷&÷fVææ6R†&–Æ—G’¢6VÖçF–72Ò6VÆbæ–çFW'&WFW"æ7F—fFVEö&–Æ—G•÷6VÖçF–72€¢&–Æ—G’ç6÷W&6Uö6&BÂ&–Æ—G’æ÷&6ÆUög&vÖVç@¢¢–b€¢6VÖçF–72—2æöæP¢÷"æ÷B6VÖçF–72æ6÷fW&vRægVÆÇ•÷7W÷'FV@¢÷"6VÖçF–72ç&öw&ÒÒ&–Æ—G’ç&öw&Ð¢“ ¢&—6R76W'F–öäW'&÷"‚'7F6¶VB7F—fF–öâæòÆöævW"†2W†V7WF&ÆR6VÖçF–72"¢FÖvUöFW'GW&UöWfVçC¢'VÆW4WfVçBÂæöæRÒæöæP¢–b&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäDTÅôd•„TEôDÔtUõDõõD$tUEô5$TEU$S ¢6÷W&6Uöö&¦V7BÒ6VÆbåöö&¦V7G2ævWB†&–Æ—G’ç6÷W&6Uö–B¢Wf–FVæ6RÒGWÆR€¢—FVÐ¢f÷"—FVÒ–â6VÆbæ7F—fF–öåöWf–FVæ6P¢–b—FVÒç7F6µöö&¦V7Eö–BÓÒ&–Æ—G’æö&¦V7Eö–@¢¢FÖvUöFW'GW&UöWfVçBÒ6VÆbå÷'VÆW5öWfVçG2ævWB†&–Æ—G’æFW'GW&UöWfVçEö–B÷"""¢–b€¢ÆVâ†Wf–FVæ6R’Ò¢÷"Wf–FVæ6U³Òç&W6öÇfV@¢÷"Wf–FVæ6U³Òç6÷W&6Uö–BÒ&–Æ—G’ç6÷W&6Uö–@¢÷"Wf–FVæ6U³Òæ6öçG&öÆÆW"Ò&–Æ—G’æ6öçG&öÆÆW ¢÷"Wf–FVæ6U³Òæ÷&6ÆUög&vÖVçBÒ&–Æ—G’æ÷&6ÆUög&vÖVç@¢÷"Wf–FVæ6U³ÒæÖæ÷6÷W&6Uö–G2Ò&–Æ—G’æÖæ÷6÷W&6Uö–G0¢÷"æ÷B&–Æ—G’ç67&–f–6U÷6÷W&6P¢÷"æ÷B—6–ç7Fæ6R‡6÷W&6Uöö&¦V7BÂW&ÖæVçB¢÷"6÷W&6Uöö&¦V7Bç¦öæRÒ&f÷&ÖW" ¢÷"6÷W&6Uöö&¦V7Bæ6&B—2æ÷B&–Æ—G’ç6÷W&6Uö6&@¢÷"FÖvUöFW'GW&UöWfVçB—2æöæP¢÷"FÖvUöFW'GW&UöWfVçBæ¶–æB—2æ÷B'VÆW4WfVçD¶–æBåU$ÔäTåEôÄTe@¢÷"FÖvUöFW'GW&UöWfVçBç7V&¦V7Eö–G2Ò†&–Æ—G’ç6÷W&6Uö–BÂ¢÷"FÖvUöFW'GW&UöWfVçBçÆ–W%ö–æFW‚Ò&–Æ—G’æ6öçG&öÆÆW ¢“ ¢&—6RfÇVTW'&÷"‚&7F—fFVBFÖvR6÷W&6R&÷fVææ6R—2–çfÆ–B"¢6VÆbåöWF†VçF–6FUö÷&–v–æÅ÷'VÆW5öWfVçB†FÖvUöFW'GW&UöWfVçB¢–b&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBå4T$4…ôÄäEõE•S ¢6÷W&6RÒ6VÆbåöö&¦V7G2ævWB†&–Æ—G’ç6÷W&6Uö–B¢F—66&FVBÒ6VÆbåöö&¦V7G2ævWB†&–Æ—G’æF—66&FVEöFW7F–æF–öåö–B÷"""¢–b€¢æ÷B—6–ç7Fæ6R‡6÷W&6RÂ6&Dö&¦V7B¢÷"6÷W&6Rç¦öæRÒ&f÷&ÖW" ¢÷"6÷W&6Ræ6&B—2æ÷B&–Æ—G’ç6÷W&6Uö6&@¢÷"æ÷B—6–ç7Fæ6R†F—66&FVBÂ6&Dö&¦V7B¢÷"F—66&FVBæ6&B—2æ÷B&–Æ—G’ç6÷W&6Uö6&@¢÷"F—66&FVBæ÷væW"Ò&–Æ—G’æ6öçG&öÆÆW ¢÷"&–Æ—G’æF—66&FVEöFW7F–æF–öåö–BÒF—66&FVBæö&¦V7Eö–@¢÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR†F—66&FVBÂ&w&fW–&B"¢“ ¢&—6RfÇVTW'&÷"‚&ÆæF7–6Æ–ærF—66&B&÷fVææ6R—2–çfÆ–B"¢6VÆbç7F6²ç÷‚¢&–Æ—G’ç¦öæRÒ&f÷&ÖW" ¢6÷W&6RÒ6VÆbåöö&¦V7G2ævWB†&–Æ—G’ç6÷W&6Uö–B¢6÷W&6U÷W&ÖæVçBÒ€¢6÷W&6P¢–b—6–ç7Fæ6R‡6÷W&6RÂW&ÖæVçB’æB6VÆbæ—5öWF†÷&—FF—fR‡6÷W&6RÂ&&GFÆVf–VÆB"¢VÇ6RæöæP¢¢FVÆ—fW&VBÒfÇ6P¢fööEöÆ–fUö&Vf÷&S¢–çBÂæöæRÒæöæP¢–b&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBä4õ•õD„•5ôUT•ÔTåC ¢–b6÷W&6U÷W&ÖæVçB—2æ÷BæöæS ¢6VÆbæ7&VFUö6÷•÷Fö¶Vâ€¢6÷W&6U÷W&ÖæVçBÀ¢&–Æ—G’æ6öçG&öÆÆW"À¢6÷W&6Uö6&CÖ&–Æ—G’ç6÷W&6Uö6&BææÖRÀ¢÷&6ÆUög&vÖVçCÖ&–Æ—G’æ÷&6ÆUög&vÖVçBÀ¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢¢FVÆ—fW&VBÒG'VP¢VÇ6S ¢6VÆbæÆör€¢&7F—fFVEö&–Æ—G•÷&W6öÇfVEöæõöVffV7B"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢&V6öãÒ&6÷•÷6÷W&6UöÆVgEö&GFÆVf–VÆB"À¢¢VÆ–b&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBå4T$4…ôÄäEõE•S ¢ÆæE÷G—RÒ6VÆbæ–çFW'&WFW"äÄäD5”4Ä”ärægVÆÆÖF6‚†&–Æ—G’æ÷&6ÆUög&vÖVçB¢76W'BÆæE÷G—R—2æ÷BæöæP¢Æ–W"Ò6VÆbçÆ–W'5¶&–Æ—G’æ6öçG&öÆÆW%Ð¢ÖF6†W2Ò6÷'FVB€¢€¢6&@¢f÷"6&B–âÆ–W"æÆ–'&'¢–b&Rç6V&6‚‡&b%Æ'¶ÆæE÷G—Ræw&÷W‚vÆæBr—ÕÆ""Â6&Bæ6&BçG—UöÆ–æR¢’À¢¶W“ÖÆÖ&F6&C¢6&Bæö&¦V7Eö–BÀ¢¢f÷VæBÒÖF6†W5³Ò–bÖF6†W2VÇ6RæöæP¢–bf÷VæB—2æ÷BæöæS ¢6VÆbæÆör€¢&ÆæF7–6Æ–æu÷&WfVÆVB"À¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6&CÖf÷VæBææÖRÀ¢Æ–'&'•öö&¦V7Eö–CÖf÷VæBæö&¦V7Eö–BÀ¢¢–åö†æBÒ6VÆbæÖ÷fUöö&¦V7B†f÷VæBÂ&†æB"Â&V6öãÒ&ÆæF7–6Æ–æu÷6V&6‚"¢FVÆ—fW&VBÒG'VP¢6VÆbæÆör€¢&ÆæF7–6Æ–æuöf÷VæB"À¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6&CÖ–åö†æBææÖRÀ¢†æEöö&¦V7Eö–CÖ–åö†æBæö&¦V7Eö–BÀ¢¢Æ–W"æÆ–'&'•³¥ÒÒ6VÆbç&ærç6‡VffÆVB€¢Æ–W"æÆ–'&'’ÂFöÖ–ãÖb&ÆæF7–6Æ–æs§¶&–Æ—G’æö&¦V7Eö–GÒ ¢¢6VÆbæÆör€¢&ÆæF7–6Æ–æu÷6‡VffÆVB"À¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢f÷VæCÖFVÆ—fW&VBÀ¢Æ–'&'•÷6—¦SÖÆVâ‡Æ–W"æÆ–'&'’’À¢¢–b€¢&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäEdä4Uô4Ä55ôÄUdTÀ¢æB6÷W&6U÷W&ÖæVçB—2æ÷BæöæP¢æB$6Æ72"–â6÷W&6U÷W&ÖæVçBæ6&BçG—UöÆ–æP¢“ ¢ÆWfVÅöÖF6‚Ò6VÆbæ–çFW'&WFW"ä4Ä55ôÄUdTÅõUægVÆÆÖF6‚†&–Æ—G’æ÷&6ÆUög&vÖVçB¢–bÆWfVÅöÖF6‚—2æöæR÷"6÷W&6U÷W&ÖæVçBæ6Æ75öÆWfVÂÒ–çB†ÆWfVÅöÖF6…²&ÆWfVÂ%Ò’Ò ¢&—6RfÇVTW'&÷"‚$6Æ72ÆWfVÂGfæ6VÖVçBæòÆöævW"†2fÆ–B&öw&W76–öâ"¢æW‡EöÆWfVÂÒ–çB†ÆWfVÅöÖF6…²&ÆWfVÂ%Ò¢6÷W&6U÷W&ÖæVçBæ6Æ75öÆWfVÂÒæW‡EöÆWfVÀ¢–bæW‡EöÆWfVÂÓÒ# ¢6÷W&6U÷W&ÖæVçBæ6Æ75öÆWfVÅ÷F–ÖW7F×Ò6VÆbåöVffV7E÷F–ÖW7F×‚¢6VÆbç&Vg&W6…÷7FF–5÷EöÖöF–f–W'2‚¢WfVçBÒ6VÆbåöæWu÷'VÆW5öWfVçB€¢'VÆW4WfVçD¶–æBä4Ä55ôÄUdTÅôEdä4TBÀ¢&–Æ—G’æ6öçG&öÆÆW"À¢‡6÷W&6U÷W&ÖæVçBæö&¦V7Eö–BÂ’À¢6÷W&6Uö–C×6÷W&6U÷W&ÖæVçBæö&¦V7Eö–BÀ¢¢6†–ÆBÒ6VÆbæ–çFW'&WFW"æ6Æ75öÆWfVÅö6†–ÆB‡6÷W&6U÷W&ÖæVçBæ6&BÂæW‡EöÆWfVÂ¢–b6†–ÆB—2æ÷BæöæS ¢–b€¢6VÆbæ–çFW'&WFW"æ6Æ75öÆWfVÅ÷&V6÷fW'•÷6VÖçF–5ö6÷fW&vR€¢6÷W&6U÷W&ÖæVçBæ6&BÂ6†–Æ@¢¢—2æ÷BæöæP¢“ ¢6VÆbåöVçVWVU÷G&–vvW"€¢WfVçBÂ6÷W&6U÷W&ÖæVçBÂ6†–ÆBÂG&–vvW$VffV7Bä4Ä55ôÄUdTÅõEtõõ$T4õdU%¢¢VÆ–b6VÆbæ–çFW'&WFW"ä4Ä55ôÄUdTÅõD…$TUõ4T$4‚ægVÆÆÖF6‚†6†–ÆB“ ¢6VÆbåöVçVWVU÷G&–vvW"€¢WfVçBÂ6÷W&6U÷W&ÖæVçBÂ6†–ÆBÂG&–vvW$VffV7Bä4Ä55ôÄUdTÅõD…$TUõ4T$4€¢¢6VÆbæÆör€¢&6Æ75öÆWfVÅöGfæ6VB"À¢6÷W&6Uö–C×6÷W&6U÷W&ÖæVçBæö&¦V7Eö–BÀ¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢g&öÕöÆWfVÃÖæW‡EöÆWfVÂÒÀ¢FõöÆWfVÃÖæW‡EöÆWfVÂÀ¢÷&6ÆUög&vÖVçCÖ&–Æ—G’æ÷&6ÆUög&vÖVçBÀ¢¢FVÆ—fW&VBÒG'VP¢–b€¢&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäu$åEõ$T4…õTåD”ÅôTõ@¢æB—6–ç7Fæ6R‡6÷W&6U÷W&ÖæVçBÂW&ÖæVçB¢æB6VÆbæ—5öWF†÷&—FF—fR‡6÷W&6U÷W&ÖæVçBÂ&&GFÆVf–VÆB"¢“ ¢6÷W&6U÷W&ÖæVçBçFV×÷&'•ö¶W—v÷&EöVffV7G2æVæB€¢FV×÷&'”¶W—v÷&DVffV7B€¢FV×÷&'”¶W—v÷&Bå$T4‚À¢'VçF–ÅöVæEööe÷GW&â"À¢6÷W&6U÷W&ÖæVçBæö&¦V7Eö–BÀ¢&–Æ—G’æ÷&6ÆUög&vÖVçBÀ¢F–ÖW7F××6VÆbåöVffV7E÷F–ÖW7F×‚’À¢¢¢6VÆbæÆör€¢&g&öuö'WFÆW%÷&V6…öw&çFVB"À¢6÷W&6Uö–C×6÷W&6U÷W&ÖæVçBæö&¦V7Eö–BÀ¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢¢FVÆ—fW&VBÒG'VP¢–b€¢&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBå$UEU$åõ4TÄeôe$ôÕôu$dU”$EõDT@¢æB—6–ç7Fæ6R‡6÷W&6RÂ6&Dö&¦V7B¢“ ¢&WGW&æVBÒ6VÆbæ7&VFU÷W&ÖæVçB€¢6÷W&6Ræ6&BÂ&–Æ—G’æ6öçG&öÆÆW"ÂFVCÕG'VRÂ7VÖÖöæ–æu÷6–6³ÔfÇ6P¢¢6VÆbæÆör€¢'GVææVÅ÷&G5÷&WGW&æVB"À¢6÷W&6Uö–C×6÷W&6Ræö&¦V7Eö–BÀ¢W&ÖæVçEö–C×&WGW&æVBæö&¦V7Eö–BÀ¢FVCÕG'VRÀ¢¢FVÆ—fW&VBÒG'VP¢fööEöÆ–fUögFW#¢–çBÂæöæRÒæöæP¢–b&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäE$uô4$C ¢&Vf÷&RÒÆVâ‡6VÆbçÆ–W'5¶&–Æ—G’æ6öçG&öÆÆW%Òæ†æB¢G&WrÒ6VÆbæG&r‡6VÆbçÆ–W'5¶&–Æ—G’æ6öçG&öÆÆW%ÒÂ¢6VÆbæÆör€¢'&•öf–ÆÆWG5öG&u÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢6÷7E÷F&vWEö–CÖ&–Æ—G’æ6÷7E÷F&vWEö–BÀ¢6&G5öG&vãÓ–bG&WrVÇ6RÀ¢†æE÷6—¦Uö&Vf÷&SÖ&Vf÷&RÀ¢†æE÷6—¦UögFW#ÖÆVâ‡6VÆbçÆ–W'5¶&–Æ—G’æ6öçG&öÆÆW%Òæ†æB’À¢¢FVÆ—fW&VBÒG&Wp¢VÆ–b&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäE$uô4$E3 ¢ÖF6‚Ò&Rç6V&6‚€¢"%äG&rƒõÆ6÷VçCæÆöæWÇGv÷ÇF‡&VWÆf÷W'Æf—fWÅ³Ó•ÕÆB¢’6&G3õÂâ ¢""ƒó¢7F—fFRöæÇ’26÷&6W'•Ââ“òB"À¢&–Æ—G’ç&öw&ÒæVffV7E÷FW‡BÀ¢&Rä’À¢¢76W'BÖF6‚—2æ÷BæöæP¢VçF—G’Ò²&#¢Â&öæR#¢Â'Gvò#¢"Â'F‡&VR#¢2Â&f÷W"#¢BÂ&f—fR#¢WÒævWB€¢ÖF6‚æw&÷W‚&6÷VçB"’æ66VföÆB‚¢’÷"–çB†ÖF6‚æw&÷W‚&6÷VçB"’¢&Vf÷&RÒÆVâ‡6VÆbçÆ–W'5¶&–Æ—G’æ6öçG&öÆÆW%ÒæÆ–'&'’¢FVÆ—fW&VBÒ6VÆbæG&r‡6VÆbçÆ–W'5¶&–Æ—G’æ6öçG&öÆÆW%ÒÂVçF—G’¢6VÆbæÆör€¢&7F—fFVEöG&u÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢&WVW7FVC×VçF—G’À¢6&G5öG&vãÖ&Vf÷&RÒÆVâ‡6VÆbçÆ–W'5¶&–Æ—G’æ6öçG&öÆÆW%ÒæÆ–'&'’’À¢G&u÷7V66VVFVCÖFVÆ—fW&VBÀ¢¢VÆ–b&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäu$åEõDô´Tåô„5DUõTåD”ÅôTõC ¢&V6—–VçG2Ò°¢ ¢f÷"Æ–W"–â6VÆbçÆ–W'0¢f÷"–âÆ–W"æ&GFÆVf–VÆ@¢–bæ6öçG&öÆÆW"ÓÒ&–Æ—G’æ6öçG&öÆÆW"æBæ—5÷Fö¶VâæBæ—5ö7&VGW&P¢Ð¢f÷"&V6—–VçB–â&V6—–VçG3 ¢–bæ÷Bç’€¢Ræ¶W—v÷&B—2FV×÷&'”¶W—v÷&Bä„5DP¢æBRç6÷W&6Uö–BÓÒ&–Æ—G’ç6÷W&6Uö–@¢æBRæ÷&6ÆUög&vÖVçBÓÒ&–Æ—G’æ÷&6ÆUög&vÖVç@¢f÷"R–â&V6—–VçBçFV×÷&'•ö¶W—v÷&EöVffV7G0¢“ ¢&V6—–VçBçFV×÷&'•ö¶W—v÷&EöVffV7G2æVæB€¢FV×÷&'”¶W—v÷&DVffV7B€¢FV×÷&'”¶W—v÷&Bä„5DRÀ¢'VçF–ÅöVæEööe÷GW&â"À¢&–Æ—G’ç6÷W&6Uö–BÀ¢&–Æ—G’æ÷&6ÆUög&vÖVçBÀ¢F–ÖW7F××6VÆbåöVffV7E÷F–ÖW7F×‚’À¢¢¢6VÆbæÆör€¢'Fö¶Våö†7FU÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢&V6—–VçEö–G3Õ·æö&¦V7Eö–Bf÷"–â&V6—–VçG5ÒÀ¢VçF—G“ÖÆVâ‡&V6—–VçG2’À¢¢VÆ–b&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäÕUDtTåô4õTåDU# ¢F&vWBÒ6VÆbåöö&¦V7G2ævWB†&–Æ—G’çF&vWEö–G5³Ò’–b&–Æ—G’çF&vWEö–G2VÇ6RæöæP¢–b€¢—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢æB6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"¢æBF&vWBæ—5ö7&VGW&P¢“ ¢6VÆbçÆ6Uö6÷VçFW'2€¢F&vWBÀ¢"³ò³"À¢À¢6÷W&6Uö6&CÖ&–Æ—G’ç6÷W&6Uö6&BææÖRÀ¢÷&6ÆUög&vÖVçCÖ&–Æ—G’æ÷&6ÆUög&vÖVçBÀ¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢¢6VÆbæÆör€¢&×WFvVåö6÷VçFW%÷Æ6VB"À¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢¢FVÆ—fW&VBÒG'VP¢VÇ6S ¢6VÆbæÆör€¢&×WFvVåö6÷VçFW%öf–ÆVEö6Æ÷6VB"À¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢F&vWEö–CÖ&–Æ—G’çF&vWEö–G5³Ò–b&–Æ—G’çF&vWEö–G2VÇ6RæöæRÀ¢¢VÆ–b€¢&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäDTÅôd•„TEôDÔtUõDõõD$tUEô5$TEU$P¢“ ¢F&vWBÒ6VÆbåöö&¦V7G2ævWB†&–Æ—G’çF&vWEö–G5³Ò’–b&–Æ—G’çF&vWEö–G2VÇ6RæöæP¢–b6VÆbåöÆVvÅö7F—fFVEöFÖvU÷F&vWB‡F&vWBÂ&–Æ—G’æ6öçG&öÆÆW"“ ¢76W'B—6–ç7Fæ6R‡6÷W&6RÂW&ÖæVçB’æBFÖvUöFW'GW&UöWfVçB—2æ÷BæöæP¢&öw&ÒÒ6VÆbæ–çFW'&WFW"æFÖvU÷&öw&Ò†&–Æ—G’ç&öw&ÒæVffV7E÷FW‡B¢76W'B&öw&Ò—2æ÷BæöæRæB&öw&ÒæÖ÷VçB—2æ÷BæöæP¢76W'B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢FÖvUöWfVçBÒ6VÆbæFVÅöFÖvR€¢FÖvUG&ç67F–öâ€¢&–Æ—G’æ6öçG&öÆÆW"À¢6÷W&6RÀ¢FÖvUF&vWD¶–æBä5$TEU$RÀ¢&öw&ÒæÖ÷VçBÀ¢&–Æ—G’æ÷&6ÆUög&vÖVçBÀ¢F&vWBÀ¢6÷W&6UöWfVçCÖFÖvUöFW'GW&UöWfVçBÀ¢’À¢FVfW%÷÷7EöFÖvSÕG'VRÀ¢¢FVÆ—fW&VBÒG'VP¢6VÆbæÆör€¢&7F—fFVEöFÖvU÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢FÖvUöWfVçEö–CÖFÖvUöWfVçBæWfVçEö–BÀ¢Ö÷VçC×&öw&ÒæÖ÷VçBÀ¢¢VÇ6S ¢6VÆbæÆör€¢&7F—fFVEö&–Æ—G•÷&W6öÇfVEöæõöVffV7B"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢F&vWEö–CÖ&–Æ—G’çF&vWEö–G5³Ò–b&–Æ—G’çF&vWEö–G2VÇ6RæöæRÀ¢&V6öãÒ'F&vWEö–ÆÆVvÅöE÷&W6öÇWF–öâ"À¢¢VÆ–b&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBä4õTåDU%õD$tUEõ5TÄÃ ¢F&vWBÒ€¢6VÆbåöö&¦V7G2ævWB†&–Æ—G’çF&vWEö–G5³Ò’–bÆVâ†&–Æ—G’çF&vWEö–G2’ÓÒVÇ6RæöæP¢¢ÆVvÂÒ6VÆbåö—5öÆVvÅö6÷VçFW%÷F&vWB‡F&vWBÂ&–Æ—G’æ6öçG&öÆÆW"¢–bÆVvÃ ¢76W'B—6–ç7Fæ6R‡F&vWBÂ7F6´ö&¦V7B¢F&vWEö6&BÒ6VÆbæÖ÷fUöö&¦V7B‡F&vWBÂ&w&fW–&B"Â&V6öãÒ'7VÆÅö6÷VçFW&VB"¢6VÆbæÆör€¢'7VÆÅö6÷VçFW&VB"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢&–Æ—G•÷6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢F&vWE÷7VÆÅö–C×F&vWBæö&¦V7Eö–BÀ¢F&vWEöö&¦V7Eö–C×F&vWBçF&vWEö–BÀ¢F&vWEö6&C×F&vWBæ6&BææÖRÀ¢6öçG&öÆÆW#Ö&–Æ—G’æ6öçG&öÆÆW"À¢÷&6ÆUög&vÖVçCÖ&–Æ—G’æ÷&6ÆUög&vÖVçBÀ¢F&vWE÷&VÆF–öç6†—Ò'F&vWG5ö'F–f7Eö÷%ö7&VGW&U÷–÷Uö6öçG&öÂ"À¢6÷VçFW&VEöö&¦V7Eö–C×F&vWEö6&Bæö&¦V7Eö–BÀ¢¢FVÆ—fW&VBÒG'VP¢VÇ6S ¢6VÆbæÆör€¢&7F—fFVEö&–Æ—G•÷&W6öÇfVEöæõöVffV7B"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢F&vWE÷7VÆÅö–CÒ†&–Æ—G’çF&vWEö–G5³Ò–b&–Æ—G’çF&vWEö–G2VÇ6RæöæR’À¢&V6öãÒ&6÷VçFW%÷F&vWEö–ÆÆVvÅöE÷&W6öÇWF–öâ"À¢¢VÆ–b&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBä4õTåDU%ôäEôä”ÔDUô%D”d5C ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"æ6÷VçFW%öæEöæ–ÖFUö'F–f7E÷&öw&Ò†&–Æ—G’æ÷&6ÆUög&vÖVçB¢76W'B&öw&Ò—2æ÷BæöæP¢F&vWBÒ6VÆbåöö&¦V7G2ævWB†&–Æ—G’çF&vWEö–G5³Ò’–b&–Æ—G’çF&vWEö–G2VÇ6RæöæP¢–b€¢—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢æB6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"¢æBF&vWBæ6öçG&öÆÆW"ÓÒ&–Æ—G’æ6öçG&öÆÆW ¢æB$'F–f7B"–âF&vWBçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢æB6VÆbåöÆVvÅ÷F&vWF–æu÷&÷FV7F–öâ‡F&vWBÂ&–Æ—G’æ6öçG&öÆÆW"¢“ ¢6÷VçBÂ÷vW"ÂF÷Vv†æW72Â7V'G—RÒ&öw&Ð¢v5ö7&VGW&RÒF&vWBæ—5ö7&VGW&P¢6VÆbçÆ6Uö6÷VçFW'2€¢F&vWBÀ¢"³ò³"À¢6÷VçBÀ¢6÷W&6Uö6&CÖ&–Æ—G’ç6÷W&6Uö6&BææÖRÀ¢÷&6ÆUög&vÖVçCÖ&–Æ—G’æ÷&6ÆUög&vÖVçBÀ¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢FVfW%÷÷7E÷Æ6VÖVçCÕG'VRÀ¢¢–bæ÷Bv5ö7&VGW&S ¢6VÆbæÇ•÷FV×÷&'•÷G—UöæEö&6U÷B€¢F&vWBÀ¢FFVE÷G—W3Ò‚$7&VGW&R"Â’À¢FFVE÷7V'G—W3Ò‡7V'G—RÂ’À¢÷vW#×÷vW"À¢F÷Vv†æW73×F÷Vv†æW72À¢6÷W&6Uö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Uö6&CÖ&–Æ—G’ç6÷W&6Uö6&BææÖRÀ¢÷&6ÆUög&vÖVçCÖ&–Æ—G’æ÷&6ÆUög&vÖVçBÀ¢GW&F–öãÒ'W'6—7FVçB"À¢¢6VÆbç&Vg&W6…÷7FF–5÷EöÖöF–f–W'2‚¢FVÆ—fW&VBÒG'VP¢6VÆbæÆör€¢&7F—fFVEö6÷VçFW%ö'F–f7Eöæ–ÖF–öå÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢6÷VçFW'3Ö6÷VçBÀ¢æ–ÖFVCÖæ÷Bv5ö7&VGW&RÀ¢&W7VÇF–æu÷G—UöÆ–æS×F&vWBçG—UöÆ–æRÀ¢&W7VÇF–æu÷÷vW#×F&vWBç÷vW"À¢&W7VÇF–æu÷F÷Vv†æW73×F&vWBçF÷Vv†æW72À¢¢VÇ6S ¢6VÆbæÆör€¢&7F—fFVEö&–Æ—G•÷&W6öÇfVEöæõöVffV7B"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢F&vWEö–CÖ&–Æ—G’çF&vWEö–G5³Ò–b&–Æ—G’çF&vWEö–G2VÇ6RæöæRÀ¢&V6öãÒ'F&vWEö–ÆÆVvÅöE÷&W6öÇWF–öâ"À¢¢VÆ–b€¢&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäu$åEõ4TÄeôd•%5Eõ5E$”´UõTåD”ÅôTõ@¢æB6÷W&6U÷W&ÖæVçB—2æ÷BæöæP¢“ ¢6÷W&6U÷W&ÖæVçBçFV×÷&'•ö¶W—v÷&EöVffV7G2æVæB€¢FV×÷&'”¶W—v÷&DVffV7B€¢7G&–¶T¶W—v÷&Bäd•%5Eõ5E$”´RÀ¢'VçF–ÅöVæEööe÷GW&â"À¢&–Æ—G’ç6÷W&6Uö–BÀ¢&–Æ—G’æ÷&6ÆUög&vÖVçBÀ¢F–ÖW7F××6VÆbåöVffV7E÷F–ÖW7F×‚’À¢¢¢FVÆ—fW&VBÒG'VP¢6VÆbæÆör€¢'FV×÷&'•ö¶W—v÷&Eöw&çFVB"À¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢F&vWEö–C×6÷W&6U÷W&ÖæVçBæö&¦V7Eö–BÀ¢¶W—v÷&CÕ7G&–¶T¶W—v÷&Bäd•%5Eõ5E$”´RçfÇVRÀ¢GW&F–öãÒ'VçF–ÅöVæEööe÷GW&â"À¢÷&6ÆUög&vÖVçCÖ&–Æ—G’æ÷&6ÆUög&vÖVçBÀ¢¢VÆ–b€¢&–Æ—G’ç&öw&ÒæVffV7Eö¶–æ@¢—27F—fFVDVffV7D¶–æBå$UEU$åôäõD„U%ô5$TEU$Uõ”õUô4ôåE$ôÅõDõôõtäU%5ô„ä@¢“ ¢F&vWBÒ6VÆbåöö&¦V7G2ævWB†&–Æ—G’çF&vWEö–G5³Ò¢–b€¢—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢æB6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"¢æBF&vWBæö&¦V7Eö–BÒ&–Æ—G’ç6÷W&6Uö–@¢æBF&vWBæ6öçG&öÆÆW"ÓÒ&–Æ—G’æ6öçG&öÆÆW ¢æBF&vWBæ—5ö7&VGW&P¢“ ¢&WÆ6VÖVçBÒ6VÆbæÖ÷fUöö&¦V7B€¢F&vWBÂ&†æB"Â&V6öãÒ&7F—fFVE÷&WGW&å÷Fõö÷væW'5ö†æB ¢¢FVÆ—fW&VBÒG'VP¢6VÆbæÆör€¢'F&vWE÷&WGW&æVE÷Fõö†æB"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢FW7F–æF–öåöö&¦V7Eö–C×&WÆ6VÖVçBæö&¦V7Eö–BÀ¢÷væW#×6VÆbçÆ–W'5·F&vWBæ÷væW%ÒææÖRÀ¢¢VÇ6S ¢6VÆbæÆör€¢&7F—fFVEö&–Æ—G•÷&W6öÇfVEöæõöVffV7B"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢&V6öãÒ'F&vWEö–ÆÆVvÅöE÷&W6öÇWF–öâ"À¢¢VÆ–b&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäED4…ôUT•ÔTåC ¢F&vWBÒ6VÆbåöö&¦V7G2ævWB†&–Æ—G’çF&vWEö–G5³Ò’–b&–Æ—G’çF&vWEö–G2VÇ6RæöæP¢ÆVvÂÒ€¢—6–ç7Fæ6R‡6÷W&6U÷W&ÖæVçBÂW&ÖæVçB¢æB6VÆbæ—5öWF†÷&—FF—fR‡6÷W&6U÷W&ÖæVçBÂ&&GFÆVf–VÆB"¢æB$WV—ÖVçB"–â6÷W&6U÷W&ÖæVçBçG—UöÆ–æP¢æB—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢æB6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"¢æBF&vWBæ6öçG&öÆÆW"ÓÒ&–Æ—G’æ6öçG&öÆÆW ¢æBF&vWBæ—5ö7&VGW&P¢æB6VÆbåöÆVvÅ÷F&vWF–æu÷&÷FV7F–öâ‡F&vWBÂ&–Æ—G’æ6öçG&öÆÆW"¢¢–bÆVvÃ ¢6÷W&6U÷W&ÖæVçBæGF6†VE÷FòÒF&vWBæö&¦V7Eö–@¢6÷W&6U÷W&ÖæVçBæGF6†ÖVçE÷F–ÖW7F×Ò6VÆbåöVffV7E÷F–ÖW7F×‚¢6VÆbç&Vg&W6…÷7FF–5÷EöÖöF–f–W'2‚¢FVÆ—fW&VBÒG'VP¢6VÆbæÆör€¢&WV—ÖVçEöGF6†VB"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Uö–C×6÷W&6U÷W&ÖæVçBæö&¦V7Eö–BÀ¢6&C×6÷W&6U÷W&ÖæVçBæ6&BææÖRÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢Æ–W#×6VÆbçÆ–W'5¶&–Æ—G’æ6öçG&öÆÆW%ÒææÖRÀ¢¢VÇ6S ¢6VÆbæÆör€¢&WV—ÖVçEöGF6…öf–ÆVEö6Æ÷6VB"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢F&vWEö–CÖ&–Æ—G’çF&vWEö–G5³Ò–b&–Æ—G’çF&vWEö–G2VÇ6RæöæRÀ¢¢VÆ–b&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBät”åõD…$TUôÄ”dS ¢fööEöÆ–fUö&Vf÷&RÒ6VÆbçÆ–W'5¶&–Æ—G’æ6öçG&öÆÆW%ÒæÆ–fP¢6VÆbæv–åöÆ–fR€¢&–Æ—G’æ6öçG&öÆÆW"À¢2À¢6÷W&6Uö6&CÖ&–Æ—G’ç6÷W&6Uö6&BææÖRÀ¢÷&6ÆUög&vÖVçCÖ&–Æ—G’æ÷&6ÆUög&vÖVçBÀ¢FVfW%÷G&–vvW%öFVÆ—fW'“ÕG'VRÀ¢¢fööEöÆ–fUögFW"Ò6VÆbçÆ–W'5¶&–Æ—G’æ6öçG&öÆÆW%ÒæÆ–fP¢FVÆ—fW&VBÒG'VP¢VÆ–b&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäEdä4Uô4Ä55ôÄUdTÃ ¢70¢VÇ6S ¢6VÆbæÆör€¢&7F—fFVEö&–Æ—G•÷&W6öÇfVEöæõöVffV7B"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢&V6öãÒ'6÷W&6Uöæ÷Eööåö&GFÆVf–VÆB"À¢¢f÷"–æFW‚ÂWf–FVæ6R–âVçVÖW&FR‡6VÆbæ7F—fF–öåöWf–FVæ6R“ ¢–bWf–FVæ6Rç7F6µöö&¦V7Eö–BÓÒ&–Æ—G’æö&¦V7Eö–C ¢6VÆbæ7F—fF–öåöWf–FVæ6U¶–æFW…ÒÒ7F—fF–öäWf–FVæ6R€¢Wf–FVæ6Rç7F6µöö&¦V7Eö–BÀ¢Wf–FVæ6Rç6÷W&6Uö–BÀ¢Wf–FVæ6Ræ6öçG&öÆÆW"À¢Wf–FVæ6Ræ÷&6ÆUög&vÖVçBÀ¢Wf–FVæ6RæÖæ÷6÷W&6Uö–G2À¢Wf–FVæ6RçF÷6÷W&6RÀ¢G'VRÀ¢Wf–FVæ6Ræ6÷7E÷F&vWEö–BÀ¢¢'&V°¢–b&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBät”åõD…$TUôÄ”dS ¢f÷"–æFW‚ÂWf–FVæ6R–âVçVÖW&FR‡6VÆbæfööEö7F—fF–öåöWf–FVæ6R“ ¢–bWf–FVæ6Rç7F6µöö&¦V7Eö–BÓÒ&–Æ—G’æö&¦V7Eö–C ¢6VÆbæfööEö7F—fF–öåöWf–FVæ6U¶–æFW…ÒÒ&WÆ6R€¢Wf–FVæ6RÀ¢&W6öÇfVCÕG'VRÀ¢Æ–fUö&Vf÷&SÖfööEöÆ–fUö&Vf÷&RÀ¢Æ–fUögFW#ÖfööEöÆ–fUögFW"À¢Ö÷VçEöv–æVCÒ€¢fööEöÆ–fUögFW"ÒfööEöÆ–fUö&Vf÷&P¢–bfööEöÆ–fUö&Vf÷&R—2æ÷BæöæRæBfööEöÆ–fUögFW"—2æ÷BæöæP¢VÇ6RæöæP¢’À¢¢'&V°¢6VÆbæÆör€¢&7F—fFVEö&–Æ—G•÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–CÖ&–Æ—G’æö&¦V7Eö–BÀ¢6÷W&6Uö–CÖ&–Æ—G’ç6÷W&6Uö–BÀ¢6&CÖ&–Æ—G’ç6÷W&6Uö6&BææÖRÀ¢6öçG&öÆÆW#×6VÆbçÆ–W'5¶&–Æ—G’æ6öçG&öÆÆW%ÒææÖRÀ¢FVÆ—fW&VCÖFVÆ—fW&VBÀ¢¢–b&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—27F—fFVDVffV7D¶–æBäDTÅôd•„TEôDÔtUõDõõD$tUEô5$TEU$S ¢6VÆbæ6†V6µ÷7FFUö&6VEö7F–öç2‚¢6VÆbæ6†V6µöÆ–fR‚¢–bFVÆ—fW&VC ¢6VÆbå÷WE÷VæF–æu÷G&–vvW'5ööå÷7F6²‚¢–b&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB–â°¢7F—fFVDVffV7D¶–æBät”åõD…$TUôÄ”dRÀ¢7F—fFVDVffV7D¶–æBäEdä4Uô4Ä55ôÄUdTÂÀ¢7F—fFVDVffV7D¶–æBä4õTåDU%ôäEôä”ÔDUô%D”d5BÀ¢7F—fFVDVffV7D¶–æBä4õ•õD„•5ôUT•ÔTåBÀ¢Ó ¢–b&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB–â°¢7F—fFVDVffV7D¶–æBä4õTåDU%ôäEôä”ÔDUô%D”d5BÀ¢7F—fFVDVffV7D¶–æBä4õ•õD„•5ôUT•ÔTåBÀ¢Ó ¢6VÆbæ6†V6µ÷7FFUö&6VEö7F–öç2‚¢6VÆbå÷WE÷VæF–æu÷G&–vvW'5ööå÷7F6²‚ ¢FVb÷fÆ–FFUöfööEö7F—fF–öåöÆ–æ¶vR‡6VÆbÂ&–Æ—G“¢7F—fFVD&–Æ—G”ö&¦V7B’ÓâæöæS ¢""$WF†VçF–6FRöæR6æöæ–6ÂfööB7F6²ö&¦V7Bg&öÒ–Ö×WF&ÆR–ÖVçBWf–FVæ6Râ"" ¢7F—fF–öç2Ò°¢—FVÒf÷"—FVÒ–â6VÆbæ7F—fF–öåöWf–FVæ6R–b—FVÒç7F6µöö&¦V7Eö–BÓÒ&–Æ—G’æö&¦V7Eö–@¢Ð¢fööG2Ò°¢—FVÐ¢f÷"—FVÒ–â6VÆbæfööEö7F—fF–öåöWf–FVæ6P¢–b—FVÒç7F6µöö&¦V7Eö–BÓÒ&–Æ—G’æö&¦V7Eö–@¢Ð¢–bÆVâ†7F—fF–öç2’Ò÷"ÆVâ†fööG2’Ò ¢&—6R76W'F–öäW'&÷"‚$fööB7F6²ö&¦V7BÆ6·2Væ—VR7F—fF–öâ&÷fVææ6R"¢7F—fF–öâÒ7F—fF–öç5³Ð¢fööBÒfööG5³Ð¢67&–f–6VBÒ6VÆbåöö&¦V7G2ævWB†fööBç67&–f–6VEöFW7F–æF–öåö–B¢–b€¢7F—fF–öâç&W6öÇfVBÒfööBç&W6öÇfV@¢÷"&–Æ—G’ç6÷W&6Uö–BÒ7F—fF–öâç6÷W&6Uö–@¢÷"&–Æ—G’ç6÷W&6Uö–BÒfööBç6÷W&6Uö–@¢÷"&–Æ—G’æ6öçG&öÆÆW"Ò7F—fF–öâæ6öçG&öÆÆW ¢÷"&–Æ—G’æ6öçG&öÆÆW"ÒfööBæ6öçG&öÆÆW ¢÷"&–Æ—G’æ÷&6ÆUög&vÖVçBÒ7F—fF–öâæ÷&6ÆUög&vÖVç@¢÷"&–Æ—G’æ÷&6ÆUög&vÖVçBÒfööBæ÷&6ÆUög&vÖVç@¢÷"&–Æ—G’æÖæ÷6÷W&6Uö–G2Ò7F—fF–öâæÖæ÷6÷W&6Uö–G0¢÷"&–Æ—G’æÖæ÷6÷W&6Uö–G2ÒfööBæÖæ÷6÷W&6Uö–G0¢÷"&–Æ—G’çF÷6÷W&6RÒ7F—fF–öâçF÷6÷W&6P¢÷"&–Æ—G’çF÷6÷W&6RÒfööBçF÷–@¢÷"æ÷B&–Æ—G’ç67&–f–6U÷6÷W&6P¢÷"æ÷BfööBç67&–f–6U÷–@¢÷"&–Æ—G’ç67&–f–6VEöFW7F–æF–öåö–BÒfööBç67&–f–6VEöFW7F–æF–öåö–@¢÷"&–Æ—G’ç6÷W&6Uö6&BææÖRÒfööBç6÷W&6UöæÖP¢÷"&–Æ—G’ç6÷W&6Uö6&BçG—UöÆ–æRÒfööBç6÷W&6U÷G—UöÆ–æP¢÷"æ÷B—6–ç7Fæ6R‡67&–f–6VBÂ6&Dö&¦V7B¢÷"67&–f–6VBæ6&BÒ&–Æ—G’ç6÷W&6Uö6&@¢÷"67&–f–6VBæ÷væW"ÒfööBç6÷W&6Uö÷væW ¢÷"67&–f–6VBæ—5÷Fö¶VâÒfööBç6÷W&6U÷v5÷Fö¶Và¢÷"&–Æ—G’ç&öw&ÒæVffV7Eö¶–æB—2æ÷B7F—fFVDVffV7D¶–æBät”åõD…$TUôÄ”dP¢“ ¢&—6R76W'F–öäW'&÷"‚$fööB7F6²ö&¦V7BF—6w&VW2v—F‚7F—fF–öâ&÷fVææ6R" ¢FVb–ÖVçE÷Æâ€¢6VÆbÀ¢Æ–W%ö–æFWƒ¢–çBÀ¢6&C¢6&Dö&¦V7BÀ¢¢À¢ÆÆ÷uöw&fW–&C¢&ööÂÒfÇ6RÀ¢ÆÆ÷uöW†–ÆS¢&ööÂÒfÇ6RÀ¢…÷fÇVS¢–çBÂæöæRÒæöæRÀ¢’Óâ–ÖVçEÆâÂæöæS ¢6÷W&6U÷¦öæRÒ&w&fW–&B"–bÆÆ÷uöw&fW–&BVÇ6R‚&W†–ÆR"–bÆÆ÷uöW†–ÆRVÇ6R&†æB"¢–b€¢æ÷B6VÆbæ—5öWF†÷&—FF—fR†6&BÂ6÷W&6U÷¦öæR¢÷"†ÆÆ÷uöW†–ÆRæB6VÆbåöÆ–æ¶VE÷Æ•öw&çEöf÷"‡Æ–W%ö–æFW‚Â6&B’—2æöæR¢÷"†6&Bæ÷væW"ÒÆ–W%ö–æFW‚æBæ÷BÆÆ÷uöW†–ÆR¢“ ¢&WGW&âæöæP¢&WV—&VÖVçBÒ6VÆbæ67F–æu÷&WV—&VÖVçB‡Æ–W%ö–æFW‚Â6&BÂ…÷fÇVS×…÷fÇVR¢–b&WV—&VÖVçB—2æöæS ¢&WGW&âæöæP¢f–Æ&ÆRÒ°¢f÷"–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆB–bæ6&Bæ—5öÆæBæBæ÷BçFV@¢Ð¢7VÆÅ÷G—W2Ò6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢6öçFW‡BÒ&'F–f7E÷7VÆÂ"–b$'F–f7B"–â7VÆÅ÷G—W2VÇ6R&÷F†W%÷7VÆÂ ¢6VÆV7FVBÒ6VÆbå÷ÆåöÖæ÷v—F…öfÆöF–ær‡Æ–W%ö–æFW‚Â&WV—&VÖVçBÂf–Æ&ÆRÂ6öçFW‡B¢–b6VÆV7FVB—2æöæS ¢&WGW&âæöæP¢fÆöF–ærÂWfVçEö–G2Â6†÷6VâÒ6VÆV7FV@¢&WGW&â–ÖVçEÆâ€¢Æ–W%ö–æFW‚À¢6&Bæö&¦V7Eö–BÀ¢&WV—&VÖVçBÀ¢GWÆR‡æö&¦V7Eö–Bf÷"–â6†÷6Vâ’À¢fÆöF–ærÀ¢WfVçEö–G2À¢…÷fÇVRÀ¢ ¢FVb6åöff÷&B‡6VÆbÂÆ–W%ö–æFWƒ¢–çBÂ6&C¢6&Df7BÂ6&Dö&¦V7B’Óâ&ööÃ ¢–b—6–ç7Fæ6R†6&BÂ6&Dö&¦V7B“ ¢&WGW&â6VÆbç–ÖVçE÷Æâ‡Æ–W%ö–æFW‚Â6&B’—2æ÷BæöæP¢&WV—&VÖVçBÒ6VÆbæ67F–æu÷&WV—&VÖVçB‡Æ–W%ö–æFW‚Â6&B¢–b&WV—&VÖVçB—2æöæS ¢&WGW&âfÇ6P¢f–Æ&ÆRÒ°¢W&ÖæVç@¢f÷"W&ÖæVçB–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢–bW&ÖæVçBæ6&Bæ—5öÆæBæBæ÷BW&ÖæVçBçFV@¢Ð¢&WGW&â€¢6VÆbå÷ÆåöÖæ÷v—F…öfÆöF–ær€¢Æ–W%ö–æFW‚À¢&WV—&VÖVçBÀ¢f–Æ&ÆRÀ¢&'F–f7E÷7VÆÂ ¢–b$'F–f7B"–â6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢VÇ6R&÷F†W%÷7VÆÂ"À¢¢—2æ÷BæöæP¢ ¢FVbö6öÖÖ—Eöææ÷Væ6VÖVçE÷–ÖVçB€¢6VÆbÀ¢6&C¢6&Dö&¦V7BÀ¢Æã¢–ÖVçEÆâÀ¢¢À¢67Eö¶–æC¢67D¶–æBÀ¢F&vWEö–C¢7G"ÂæöæRÀ¢67Eög&öÕöw&fW–&C¢&ööÂÒfÇ6RÀ¢f–æÆ—G•ööåöVçG'“¢&ööÂÒfÇ6RÀ¢67Eög&öÕ÷&†VÃ¢&ööÂÒfÇ6RÀ¢’Óâ7F6´ö&¦V7C ¢""$FöÖ–6ÆÇ’’&WfÆ–FFVBÆâæBÖ÷fRF†R&W&W6VçFVB6&B†æBÓâ7F6²â"" ¢–bÆâÒ6VÆbç–ÖVçE÷Æâ€¢ÆâçÆ–W%ö–æFW‚À¢6&BÀ¢ÆÆ÷uöw&fW–&CÖ67Eög&öÕöw&fW–&BÀ¢ÆÆ÷uöW†–ÆSÖ67Eög&öÕ÷&†VÂÀ¢…÷fÇVS×Æâç…÷fÇVRÀ¢“ ¢&—6RfÇVTW'&÷"‚'–ÖVçBÆâ—2æòÆöævW"ÆVvÂ"¢6÷W&6W3¢Æ—7EµW&ÖæVçEÒÒµÐ¢f÷"ö&¦V7Eö–B–âÆâç6÷W&6Uö–G3 ¢6÷W&6RÒ6VÆbåöö&¦V7G2ævWB†ö&¦V7Eö–B¢–bæ÷B—6–ç7Fæ6R‡6÷W&6RÂW&ÖæVçB’÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR€¢6÷W&6RÂ&&GFÆVf–VÆB ¢“ ¢&—6RfÇVTW'&÷"‚'–ÖVçB6÷W&6R—2æ÷BWF†÷&—FF—fR"¢6÷W&6W2æVæB‡6÷W&6R¢&Wf–÷W5÷FVBÒGWÆR‡6÷W&6RçFVBf÷"6÷W&6R–â6÷W&6W2¢G'“ ¢f÷"6÷W&6R–â6÷W&6W3 ¢6÷W&6RçFVBÒG'VP¢7VÆÂÒ6VÆbæÖ÷fUöö&¦V7B€¢6&BÀ¢'7F6²"À¢6öçG&öÆÆW#×ÆâçÆ–W%ö–æFW‚À¢67Eö¶–æCÖ67Eö¶–æBÀ¢F&vWEö–C×F&vWEö–BÀ¢67Eög&öÕöw&fW–&CÖ67Eög&öÕöw&fW–&BÀ¢f–æÆ—G•ööåöVçG'“Öf–æÆ—G•ööåöVçG'’À¢67Eög&öÕ÷&†VÃÖ67Eög&öÕ÷&†VÂÀ¢&V6öãÒ'7VÆÅö67Eög&öÕöw&fW–&B"–b67Eög&öÕöw&fW–&BVÇ6R'7VÆÅö67B"À¢¢W†6WBW†6WF–öã ¢f÷"6÷W&6RÂFVB–â¦—‡6÷W&6W2Â&Wf–÷W5÷FVBÂ7G&–7CÕG'VR“ ¢6÷W&6RçFVBÒFV@¢&—6P¢76W'B—6–ç7Fæ6R‡7VÆÂÂ7F6´ö&¦V7B¢7VÆÂç…÷fÇVRÒÆâç…÷fÇVP¢6VÆbæfÆöF–æuöÖææ6öç7VÖUöWfVçG2€¢ÆâçÆ–W%ö–æFW‚À¢ÆâæfÆöF–æuöWfVçEö–G2À¢6&Bæö&¦V7Eö–BÀ¢&'F–f7E÷7VÆÂ ¢–b$'F–f7B"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢VÇ6R&÷F†W%÷7VÆÂ"À¢¢6VÆbæÆör€¢&6÷7E÷–B"À¢Æ–W#×6VÆbçÆ–W'5·ÆâçÆ–W%ö–æFW…ÒææÖRÀ¢6&CÖ6&BææÖRÀ¢vVæW&–3×Æâç&WV—&VÖVçBævVæW&–2À¢6öÆ÷&VCÖÆ—7B‡Æâç&WV—&VÖVçBæ6öÆ÷&VB’À¢6÷W&6Uö–G3ÖÆ—7B‡Æâç6÷W&6Uö–G2’À¢fÆöF–æuöWfVçEö–G3ÖÆ—7B‡ÆâæfÆöF–æuöWfVçEö–G2’À¢…÷fÇVS×Æâç…÷fÇVRÀ¢¢&–çFVBÒ6VÆbæÖæ÷&WV—&VÖVçB†6&B¢–b&–çFVB—2æ÷BæöæRæBÆâç&WV—&VÖVçBævVæW&–2Â&–çFVBævVæW&–3 ¢6VÆbæÆör€¢&67F–æuö6÷7E÷&VGV6VB"À¢Æ–W#×6VÆbçÆ–W'5·ÆâçÆ–W%ö–æFW…ÒææÖRÀ¢6&CÖ6&BææÖRÀ¢&–çFVEövVæW&–3×&–çFVBævVæW&–2À¢–EövVæW&–3×Æâç&WV—&VÖVçBævVæW&–2À¢&VGV7F–öç3Õ°¢°¢&÷&6ÆUög&vÖVçB#¢&öw&Òæ÷&6ÆUög&vÖVçBÀ¢&Ö÷VçB#¢&öw&ÒæÖ÷VçBÀ¢'W%÷W&ÖæVçB#¢&öw&ÒçW%÷W&ÖæVçBÀ¢'VÆ–g––æu÷6÷W&6Uö–G2#¢Æ—7B‡6÷W&6W2’À¢Ð¢f÷"&öw&ÒÂ6÷W&6W2–â6VÆbåö67F–æu÷&VGV7F–öç2‡ÆâçÆ–W%ö–æFW‚Â6&B¢–b6÷W&6W0¢ÒÀ¢¢&WGW&â7VÆÀ ¢FVbö6öÖÖ—E÷6æVµöææ÷Væ6VÖVçB€¢6VÆbÀ¢6&C¢6&Dö&¦V7BÀ¢GF6¶W#¢W&ÖæVçBÀ¢Æã¢6æVµ–ÖVçEÆâÀ¢¢À¢F&vWCÔæöæRÀ¢&V7W'6–öå÷F&vWG3¢GWÆU¶ö&¦V7BÂââåÒÒ‚’À¢’Óâ7F6´ö&¦V7C ¢""$FöÖ–6ÆÇ’’f—†VB6æV²ÖæÇW2F†RWF†÷&—FF—fR&WGW&â6÷7Bâ"" ¢–bÆâÒ6VÆbç6æVµ÷–ÖVçE÷Æâ€¢ÆâçÆ–W%ö–æFW‚Â6&BÂGF6¶W"Â÷&6ÆUög&vÖVçC×Æâæ÷&6ÆUög&vÖVç@¢“ ¢&—6RfÇVTW'&÷"‚%6æV²–ÖVçBÆâ—2æòÆöævW"ÆVvÂ"¢&VÖ÷fÂÒ6VÆbæ–çFW'&WFW"çF&vWFVE÷&VÖ÷fÅ÷&öw&Ò†6&Bæ6&B¢–b&VÖ÷fÂ—2æ÷BæöæRæBæ÷B6VÆbåöÆVvÅ÷F&vWFVE÷&VÖ÷fÅ÷F&vWB€¢F&vWBÂÆâçÆ–W%ö–æFW‚Â&VÖ÷fÀ¢“ ¢&—6RfÇVTW'&÷"‚%6æV²F&vWB—2æòÆöævW"ÆVvÂ"¢–b&VÖ÷fÂ—2æöæRæBF&vWB—2æ÷BæöæS ¢&—6RfÇVTW'&÷"‚'VçF&vWFVB6æV²7VÆÂ6ææ÷Bææ÷Væ6RF&vWB"¢&V7W'6–öâÒ6VÆbæ–çFW'&WFW"æw&fW–&E÷&V7W'6–öå÷&öw&Ò†6&Bæ6&B¢–b&V7W'6–öâ—2æ÷BæöæS ¢–bæ÷B6VÆbå÷fÆ–Eöw&fW–&E÷&V7W'6–öå÷F&vWG2€¢&V7W'6–öå÷F&vWG2ÂÆâçÆ–W%ö–æFW‚Â&V7W'6–öâæÖæ÷fÇVUöÆ–Ö—@¢“ ¢&—6RfÇVTW'&÷"‚%6æV²&V7W'6–öâF&vWG2&RæòÆöævW"ÆVvÂ"¢VÆ–b&V7W'6–öå÷F&vWG3 ¢&—6RfÇVTW'&÷"‚&æöç&V7W'6–öâ6æV²7VÆÂ6ææ÷Bææ÷Væ6Rw&fW–&BF&vWG2"¢6÷W&6W3¢Æ—7EµW&ÖæVçEÒÒµÐ¢f÷"ö&¦V7Eö–B–âÆâæÖæ÷6÷W&6Uö–G3 ¢6÷W&6RÒ6VÆbåöö&¦V7G2ævWB†ö&¦V7Eö–B¢–b€¢æ÷B—6–ç7Fæ6R‡6÷W&6RÂW&ÖæVçB¢÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR‡6÷W&6RÂ&&GFÆVf–VÆB"¢÷"6÷W&6RçFV@¢÷"æ÷B6÷W&6Ræ6&Bæ—5öÆæ@¢“ ¢&—6RfÇVTW'&÷"‚%6æV²Öæ6÷W&6R—2æ÷BWF†÷&—FF—fR"¢6÷W&6W2æVæB‡6÷W&6R¢–bÆVâ‡·6÷W&6Ræö&¦V7Eö–Bf÷"6÷W&6R–â6÷W&6W7Ò’ÒÆVâ‡6÷W&6W2“ ¢&—6RfÇVTW'&÷"‚%6æV²–ÖVçB6ææ÷B&WW6RÖæ6÷W&6R" ¢26öç7G'V7B&÷F‚æWr¦öæR–æ6&æF–öç2&Vf÷&R×WFF–ærç’WF†÷&—FF—fR6öçF–æW"à¢&WGW&æVBÒ6&Dö&¦V7B€¢6VÆbåöÆÆö6FUöö&¦V7Eö–B‚’À¢GF6¶W"æ6&BÀ¢GF6¶W"æ÷væW"À¢GF6¶W"æ÷væW"À¢&†æB"À¢—5÷Fö¶VãÖGF6¶W"æ—5÷Fö¶VâÀ¢¢7VÆÂÒ7F6´ö&¦V7B€¢6VÆbåöÆÆö6FUöö&¦V7Eö–B‚’À¢6&Bæ6&BÀ¢6&Bæ÷væW"À¢ÆâçÆ–W%ö–æFW‚À¢6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æBÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–B–bF&vWB—2æ÷BæöæRVÇ6RæöæRÀ¢F&vWEö–G3×GWÆR†—FVÒæö&¦V7Eö–Bf÷"—FVÒ–â&V7W'6–öå÷F&vWG2’À¢6æVµ÷&WGW&æVEöGF6¶W%ö–CÖGF6¶W"æö&¦V7Eö–BÀ¢6æVµ÷&WGW&æVEö†æEö–C×&WGW&æVBæö&¦V7Eö–BÀ¢6æVµöFVfVæF–æu÷Æ–W#×ÆâæFVfVæF–æu÷Æ–W"À¢6æVµö÷&6ÆUög&vÖVçC×Æâæ÷&6ÆUög&vÖVçBÀ¢6æVµöÖæ÷6÷W&6Uö–G3×ÆâæÖæ÷6÷W&6Uö–G2À¢67Eög&öÕöw&fW–&C×Æâç6÷W&6U÷¦öæRÓÒ&w&fW–&B"À¢ ¢&GFÆVf–VÆBÒ6VÆbçÆ–W'5¶GF6¶W"æ6öçG&öÆÆW%Òæ&GFÆVf–VÆ@¢6÷W&6U÷¦öæRÒ6&Bç¦öæP¢w&çBÒ€¢6VÆbåöÆ–æ¶VE÷Æ•öw&çEöf÷"‡ÆâçÆ–W%ö–æFW‚Â6&B’–b6÷W&6U÷¦öæRÓÒ&W†–ÆR"VÇ6RæöæP¢¢6÷W&6Uö6&G2Ò°¢&†æB#¢6VÆbçÆ–W'5¶6&Bæ÷væW%Òæ†æBÀ¢&W†–ÆR#¢6VÆbçÆ–W'5¶6&Bæ÷væW%ÒæW†–ÆRÀ¢&w&fW–&B#¢6VÆbçÆ–W'5¶6&Bæ÷væW%Òæw&fW–&BÀ¢Õ·6÷W&6U÷¦öæUÐ¢–bæ÷B6VÆbåö–FVçF—G•ö6öçF–ç2†&GFÆVf–VÆBÂGF6¶W"’÷"æ÷B6VÆbåö–FVçF—G•ö6öçF–ç2€¢6÷W&6Uö6&G2Â6&@¢“ ¢&—6RfÇVTW'&÷"‚%6æV²6÷W&6R¦öæW26†ævVB&Vf÷&R6öÖÖ—FÖVçB"¢GF6¶W%ö–æFW‚ÒæW‡B†’f÷"’ÂfÇVR–âVçVÖW&FR†&GFÆVf–VÆB’–bfÇVR—2GF6¶W"¢6&Eö–æFW‚ÒæW‡B†’f÷"’ÂfÇVR–âVçVÖW&FR‡6÷W&6Uö6&G2’–bfÇVR—26&B¢f÷"6÷W&6R–â6÷W&6W3 ¢6÷W&6RçFVBÒG'VP¢&GFÆVf–VÆBç÷†GF6¶W%ö–æFW‚¢6÷W&6Uö6&G2ç÷†6&Eö–æFW‚¢6VÆbçÆ–W'5¶GF6¶W"æ÷væW%Òæ†æBæVæB‡&WGW&æVB¢6VÆbç7F6²æVæB‡7VÆÂ¢GF6¶W"ç¦öæRÒ&f÷&ÖW" ¢6&Bç¦öæRÒ&f÷&ÖW" ¢6VÆbå÷&Vv—7FW"‡&WGW&æVB¢6VÆbå÷&Vv—7FW"‡7VÆÂ¢–bw&çB—2æ÷BæöæS ¢7VÆÂæ67Eög&öÕ÷&†VÂÒG'VP¢6VÆbåö6öç7VÖUöÆ–æ¶VE÷Æ•öw&çB†w&çBÂ6&Bæö&¦V7Eö–B¢6VÆbåö6öÖ&EöGF6¶W'2ÒGWÆR€¢ö&¦V7Eö–Bf÷"ö&¦V7Eö–B–â6VÆbåö6öÖ&EöGF6¶W'2–bö&¦V7Eö–BÒGF6¶W"æö&¦V7Eö–@¢¢6VÆbåö6öÖ&Eö&Æö6·2ÒGWÆR€¢—"f÷"—"–â6VÆbåö6öÖ&Eö&Æö6·2–b—%³ÒÒGF6¶W"æö&¦V7Eö–@¢¢6VÆbç&Vg&W6…÷7FF–5÷EöÖöF–f–W'2‚ ¢6VÆbæfÆöF–æuöÖææ6öç7VÖUöWfVçG2€¢ÆâçÆ–W%ö–æFW‚À¢ÆâæfÆöF–æuöWfVçEö–G2À¢6&Bæö&¦V7Eö–BÀ¢&'F–f7E÷7VÆÂ ¢–b$'F–f7B"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢VÇ6R&÷F†W%÷7VÆÂ"À¢¢6VÆbæÆör€¢'¦öæUö6†ævVB"À¢6&CÖGF6¶W"æ6&BææÖRÀ¢÷væW#×6VÆbçÆ–W'5¶GF6¶W"æ÷væW%ÒææÖRÀ¢6÷W&6Uöö&¦V7Eö–CÖGF6¶W"æö&¦V7Eö–BÀ¢FW7F–æF–öåöö&¦V7Eö–C×&WGW&æVBæö&¦V7Eö–BÀ¢6÷W&6U÷¦öæSÒ&&GFÆVf–VÆB"À¢FW7F–æF–öå÷¦öæSÒ&†æB"À¢&V6öãÒ'6æVµ÷&WGW&åö6÷7B"À¢¢6VÆbæÆör€¢'¦öæUö6†ævVB"À¢6&CÖ6&Bæ6&BææÖRÀ¢÷væW#×6VÆbçÆ–W'5¶6&Bæ÷væW%ÒææÖRÀ¢6÷W&6Uöö&¦V7Eö–CÖ6&Bæö&¦V7Eö–BÀ¢FW7F–æF–öåöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢6÷W&6U÷¦öæS×6÷W&6U÷¦öæRÀ¢FW7F–æF–öå÷¦öæSÒ'7F6²"À¢&V6öãÒ'6æVµ÷7VÆÅö67B"À¢¢6VÆbæÆör€¢'6æVµö6÷7E÷–B"À¢Æ–W#×6VÆbçÆ–W'5·ÆâçÆ–W%ö–æFW…ÒææÖRÀ¢6&CÖ6&Bæ6&BææÖRÀ¢Öæ÷6÷W&6Uö–G3ÖÆ—7B‡ÆâæÖæ÷6÷W&6Uö–G2’À¢fÆöF–æuöWfVçEö–G3ÖÆ—7B‡ÆâæfÆöF–æuöWfVçEö–G2’À¢&WGW&æVEöGF6¶W%ö–CÖGF6¶W"æö&¦V7Eö–BÀ¢&WGW&æVEö†æEö–C×&WGW&æVBæö&¦V7Eö–BÀ¢¢6VÆbæÆör€¢'6æVµöææ÷Væ6VB"À¢Æ–W#×6VÆbçÆ–W'5·ÆâçÆ–W%ö–æFW…ÒææÖRÀ¢6&C×7VÆÂææÖRÀ¢†æEöö&¦V7Eö–CÖ6&Bæö&¦V7Eö–BÀ¢6÷W&6U÷¦öæS×6÷W&6U÷¦öæRÀ¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçC×Æâæ÷&6ÆUög&vÖVçBÀ¢W&Ö—76–öå÷6÷W&6Uö–C×ÆâçW&Ö—76–öå÷6÷W&6Uö–BÀ¢¢6VÆbæÆör€¢'7VÆÅö67B"À¢Æ–W#×6VÆbçÆ–W'5·ÆâçÆ–W%ö–æFW…ÒææÖRÀ¢Æ–W%ö–æFWƒ×ÆâçÆ–W%ö–æFW‚À¢6&C×7VÆÂææÖRÀ¢6&E÷G—W3×GWÆR€¢¶–æ@¢f÷"¶–æB–â€¢$'F–f7B"À¢$&GFÆR"À¢$7&VGW&R"À¢$Væ6†çFÖVçB"À¢$–ç7FçB"À¢%ÆæW7vÆ¶W""À¢%6÷&6W'’"À¢%G&–&Â"À¢¢–b¶–æB–â7VÆÂæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢’À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢6÷W&6U÷¦öæS×6÷W&6U÷¦öæRÀ¢÷&6ÆUög&vÖVçC×Æâæ÷&6ÆUög&vÖVçBÀ¢¢6VÆbåöVçVWVU÷7VÆÅö67E÷G&–vvW'2‡7VÆÂ¢6VÆbæ6†V6µ÷7FFUö&6VEö7F–öç2‚¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‚¢76W'B6VÆbç&–÷&—G•÷7FFR—2æ÷BæöæP¢6VÆbç6æVµöWf–FVæ6RæVæB€¢6æV´Wf–FVæ6R€¢6&Bæ6&BææÖRÀ¢6&Bæö&¦V7Eö–BÀ¢ÆâçÆ–W%ö–æFW‚À¢6VÆbçGW&âÀ¢6VÆbç7FWçfÇVRÀ¢Æâæ÷&6ÆUög&vÖVçBÀ¢Æâç&WV—&VÖVçBÀ¢ÆâæÖæ÷6÷W&6Uö–G2À¢GF6¶W"æö&¦V7Eö–BÀ¢&WGW&æVBæö&¦V7Eö–BÀ¢ÆâæFVfVæF–æu÷Æ–W"À¢7VÆÂæö&¦V7Eö–BÀ¢6VÆbç&–÷&—G•÷7FFRæWö6‚À¢6÷W&6U÷¦öæS×6÷W&6U÷¦öæRÀ¢W&Ö—76–öå÷6÷W&6Uö–C×ÆâçW&Ö—76–öå÷6÷W&6Uö–BÀ¢¢¢&WGW&â7VÆÀ ¢FVb67B€¢6VÆbÀ¢Æ–W%ö–æFWƒ¢–çBÀ¢6&C¢6&Dö&¦V7BÀ¢F&vWC¢W&ÖæVçBÂæöæRÒæöæRÀ¢¢À¢67Eög&öÕöw&fW–&C¢&ööÂÒfÇ6RÀ¢67&–f–6Uö6÷7C¢W&ÖæVçBÂæöæRÒæöæRÀ¢6÷W&6U÷F&vWC¢W&ÖæVçBÂæöæRÒæöæRÀ¢ÖöFUög&vÖVçC¢7G"ÂæöæRÒæöæRÀ¢&V7W'6–öå÷F&vWG3¢GWÆU´6&Dö&¦V7BÂââåÒÒ‚’À¢…÷fÇVS¢–çBÂæöæRÒæöæRÀ¢’Óâ&ööÃ ¢""$6ö×F–&–Æ—G’7F–öã¢ææ÷Væ6R&W&W6VçFVB7VÆÂÂF†Vâ&W6öÇfR—B–ÖÖVF–FVÇ’à ¢–ÖÖVF–FR&W6öÇWF–öâ—2âW‡Æ–6—BFV×÷&'’&÷VæF'’VçF–Â&–÷&—G’6öçG&öÆÆW"÷vç0¢726WVVæ6–ærâWfW'’&W&W6VçFVB7VÆÂ7F–ÆÂG&fW'6W2F†RWF†÷&—FF—fR7F6²Æ–fV7–6ÆRà¢"" ¢7VÆÂÒ6VÆbæææ÷Væ6U÷7VÆÂ€¢Æ–W%ö–æFW‚À¢6&BÀ¢F&vWBÀ¢67Eög&öÕöw&fW–&CÖ67Eög&öÕöw&fW–&BÀ¢67&–f–6Uö6÷7C×67&–f–6Uö6÷7BÀ¢6÷W&6U÷F&vWC×6÷W&6U÷F&vWBÀ¢ÖöFUög&vÖVçCÖÖöFUög&vÖVçBÀ¢&V7W'6–öå÷F&vWG3×&V7W'6–öå÷F&vWG2À¢…÷fÇVS×…÷fÇVRÀ¢¢–b7VÆÂ—2æöæS ¢&WGW&âfÇ6P¢–b6VÆbç7F6µ²ÓÒ—2æ÷B7VÆÃ ¢267BG&–vvW"6—G2&÷fRF†R7VÆÃ²÷&F–æ'’&–÷&—G’÷vç2F†B7F6²à¢6VÆbåö&Vv–å÷&–÷&—G•÷v–æF÷r‡&–÷&—G•÷Æ–W#×Æ–W%ö–æFW‚¢&WGW&âG'VP¢6VÆbç&W6öÇfU÷F÷ööe÷7F6²‚¢&WGW&âG'VP ¢FVbææ÷Væ6U÷7VÆÂ€¢6VÆbÀ¢Æ–W%ö–æFWƒ¢–çBÀ¢6&C¢6&Dö&¦V7BÀ¢F&vWC¢W&ÖæVçBÂ7F6´ö&¦V7BÂæöæRÒæöæRÀ¢¢À¢67Eög&öÕöw&fW–&C¢&ööÂÒfÇ6RÀ¢67Eög&öÕöW†–ÆS¢&ööÂÒfÇ6RÀ¢67&–f–6Uö6÷7C¢W&ÖæVçBÂæöæRÒæöæRÀ¢6÷W&6U÷F&vWC¢W&ÖæVçBÂæöæRÒæöæRÀ¢ÖöFUög&vÖVçC¢7G"ÂæöæRÒæöæRÀ¢&V7W'6–öå÷F&vWG3¢GWÆU¶ö&¦V7BÂââåÒÒ‚’À¢…÷fÇVS¢–çBÂæöæRÒæöæRÀ¢’Óâ7F6´ö&¦V7BÂæöæS ¢""%fÆ–FFRææ÷Væ6VÖVçBÂ’&W&W6VçFVBÖæÂæBFöÖ–6ÆÇ’Ö÷fR†æBÓâ7F6²â"" ¢Æ–W"Ò6VÆbçÆ–W'5·Æ–W%ö–æFW…Ð¢fÆ6…÷&–÷&—G’Ò€¢6VÆbç&–÷&—G•÷7FFR—2æ÷BæöæP¢æBæ÷B6VÆbç&–÷&—G•÷7FFRç&W6öÇWF–öå÷VæF–æp¢æB6VÆbç&–÷&—G•÷7FFRçÆ–W%ö–æFW‚ÓÒÆ–W%ö–æFW€¢æB$fÆ6‚"–â6VÆbæ–çFW'&WFW"æg&vÖVçG2†6&Bæ6&B¢æB6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æB–â´67D¶–æBäU$Â67D¶–æBåU$ÔäTåGÐ¢¢–ç7FçE÷&–÷&—G’Ò€¢6VÆbç&–÷&—G•÷7FFR—2æ÷BæöæP¢æBæ÷B6VÆbç&–÷&—G•÷7FFRç&W6öÇWF–öå÷VæF–æp¢æB6VÆbç&–÷&—G•÷7FFRçÆ–W%ö–æFW‚ÓÒÆ–W%ö–æFW€¢æB€¢6VÆbæ–çFW'&WFW"æ¶–6¶VEö7&VGW&U÷E÷&öw&Ò†6&Bæ6&B’—2æ÷BæöæP¢÷"€¢67Eög&öÕöW†–ÆP¢æB$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢æB6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æ@¢–â°¢67D¶–æBäE$uô4$E2À¢67D¶–æBåDõô4$Eõ4TÄT5D”ôâÀ¢67D¶–æBåDõô5$TEU$Uõ4TÄT5D”ôâÀ¢67D¶–æBäÄ”%$%•õ4T$4…õDõô„äBÀ¢67D¶–æBäõD”ôäÅô„äEõ$U4UBÀ¢67D¶–æBä4ôäD•D”ôäÅõ4äTµõDô´Tå2À¢67D¶–æBäõD”ôäÅôDU5E$õ•ôäEô5$TDRÀ¢67D¶–æBä4ôäD•D”ôäÅôDU5E$õ•ôäEô5$TDRÀ¢67D¶–æBäDÔtUó5ôõõ4”äuô5$TEU$RÀ¢67D¶–æBäDTÅôDÔtRÀ¢67D¶–æBä5$TEU$UõõtU%ôDÔtRÀ¢67D¶–æBäDU5E$õ•ô%D”d5EôTä4„åDÔTåEôõ%õõtU%óEô5$TEU$RÀ¢67D¶–æBäôõ¤Uõ5”ÄÂÀ¢67D¶–æBä4õTåDU%õD$tUEõ5TÄÂÀ¢67D¶–æBåD$tUDTEõ$TÔõdÂÀ¢67D¶–æBäÔôDÅõDô´Tåôõ%ô5$TEU$UõTÕÀ¢67D¶–æBåD$tUDTEô4õTåDU%ô´U•tõ$Eôu$åBÀ¢67D¶–æBåDTÕõ$%•ôDTD…õ$UEU$åôu$åBÀ¢67D¶–æBåDTÕõ$%•õE•Uô$4UõEôE$rÀ¢67D¶–æBåD$tUDTEôÄ”%$%•õ$UEU$åôäEõDô´TâÀ¢Ð¢¢÷"€¢æ÷B67Eög&öÕöW†–ÆP¢æB6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æB—267D¶–æBåD$tUDTEõ$TÔõdÀ¢æB$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢¢÷"€¢æ÷B67Eög&öÕöW†–ÆP¢æB6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æ@¢—267D¶–æBä5$TEU$UõõtU%ôDÔtP¢æB$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢¢÷"€¢æ÷B67Eög&öÕöW†–ÆP¢æB6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æ@¢—267D¶–æBäÔôDÅõDô´Tåôõ%ô5$TEU$UõTÕ ¢æB$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢¢÷"€¢æ÷B67Eög&öÕöW†–ÆP¢æB6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æ@¢—267D¶–æBåD$tUDTEô4õTåDU%ô´U•tõ$Eôu$å@¢æB$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢¢÷"€¢æ÷B67Eög&öÕöW†–ÆP¢æB6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æ@¢—267D¶–æBåDTÕõ$%•ôDTD…õ$UEU$åôu$å@¢æB$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢¢÷"€¢æ÷B67Eög&öÕöW†–ÆP¢æB6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æ@¢—267D¶–æBåDTÕõ$%•õE•Uô$4UõEôE$p¢æB$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢¢÷"€¢æ÷B67Eög&öÕöW†–ÆP¢æB6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æ@¢—267D¶–æBåD$tUDTEôÄ”%$%•õ$UEU$åôäEõDô´Tà¢æB$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢¢÷"€¢æ÷B67Eög&öÕöW†–ÆP¢æB6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æ@¢—267D¶–æBäõD”ôäÅô„äEõ$U4U@¢æB$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢¢÷"€¢æ÷B67Eög&öÕöW†–ÆP¢æB6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B’æ¶–æ@¢—267D¶–æBä4ôäD•D”ôäÅõ4äTµõDô´Tå0¢æB$–ç7FçB"–â6&Bæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢¢¢¢–b€¢€¢æ÷B†fÆ6…÷&–÷&—G’÷"–ç7FçE÷&–÷&—G’¢æB€¢Æ–W%ö–æFW‚Ò6VÆbæ7F—fU÷Æ–W ¢÷"6VÆbç7FWæ÷B–âµGW&å7FWå$T4ôÔ$EôÔ”âÂGW&å7FWåõ5D4ôÔ$EôÔ”çÐ¢÷"€¢‡6VÆbç&–÷&—G•÷7FFR—2æ÷BæöæR÷"6VÆbç7F6²¢æB6VÆbæ–çFW'&WFW"æW&÷&öw&Ò†6&Bæ6&B’—2æ÷BæöæP¢¢¢¢÷"æ÷B€¢6VÆbæ—5öWF†÷&—FF—fR†6&BÂ&w&fW–&B"¢–b67Eög&öÕöw&fW–&@¢VÇ6R€¢6VÆbæ—5öWF†÷&—FF—fR†6&BÂ&W†–ÆR"¢–b67Eög&öÕöW†–ÆP¢VÇ6R6VÆbæ—5öWF†÷&—FF—fR†6&BÂ&†æB"¢¢¢÷"€¢6&Bæ÷væW"ÒÆ–W%ö–æFW€¢æBæ÷B†67Eög&öÕöW†–ÆRæB6VÆbåöÆ–æ¶VE÷Æ•öw&çEöf÷"‡Æ–W%ö–æFW‚Â6&B’¢¢“ ¢&WGW&âæöæP¢Æ–æ¶VEöw&çBÒ6VÆbåöÆ–æ¶VE÷Æ•öw&çEöf÷"‡Æ–W%ö–æFW‚Â6&B’–b67Eög&öÕöW†–ÆRVÇ6RæöæP¢W&Ö—76–öâÒæöæP¢–b67Eög&öÕöW†–ÆRæBÆ–æ¶VEöw&çB—2æöæS ¢&WGW&âæöæP¢–b67Eög&öÕöw&fW–&C ¢W&Ö—76–öâÒæW‡B€¢€¢6VÆbåöw&fW–&Eö67E÷W&Ö—76–öâ‡6÷W&6R¢f÷"6÷W&6R–âÆ–W"æ&GFÆVf–VÆ@¢–b6VÆbåöw&fW–&Eö67E÷W&Ö—76–öâ‡6÷W&6R’—2æ÷BæöæP¢’À¢æöæRÀ¢¢–b€¢W&Ö—76–öâ—2æöæP¢÷"æ÷B6&Bæ6&Bæ—5ö7&VGW&P¢÷"æ÷B6VÆbåöw&fW–&Eö6&E÷VÆ–f–W2†6&Bæ6&BÂW&Ö—76–öå³Ò¢“ ¢&WGW&âæöæP¢&öw&ÒÒ6VÆbæ–çFW'&WFW"æ67E÷&öw&Ò†6&Bæ6&B¢–b&öw&Òæ¶–æB—267D¶–æBäÔôDÅõDô´Tåôõ%ô5$TEU$UõTÕ ¢ÖöFÂÒ6VÆbæ–çFW'&WFW"æÖöFÅ÷Fö¶Våö÷%ö7&VGW&U÷V×÷&öw&Ò†6&Bæ6&B¢–bÖöFÂ—2æöæR÷"ÖöFUög&vÖVçBæ÷B–â°¢ÖöFÂçFö¶Våög&vÖVçBÀ¢ÖöFÂçV×ög&vÖVçBÀ¢Ó ¢&WGW&âæöæP¢VÆ–bÖöFUög&vÖVçB—2æ÷BæöæS ¢&WGW&âæöæP¢–b67&–f–6Uö6÷7B—2æ÷BæöæRæB€¢&öw&Òæ¶–æB—2æ÷B67D¶–æBä´”4´TEô5$TEU$Uõ@¢÷"æ÷B—6–ç7Fæ6R‡67&–f–6Uö6÷7BÂW&ÖæVçB¢÷"æ÷B6VÆbåöÆVvÅö¶–6¶W%÷67&–f–6R€¢Æ–W%ö–æFW‚À¢67&–f–6Uö6÷7BÀ¢6VÆbæ–çFW'&WFW"æ¶–6¶VEö7&VGW&U÷E÷&öw&Ò†6&Bæ6&B’ç67&–f–6U÷G—W2À¢¢“ ¢&WGW&âæöæP¢F&vWEö–C¢7G"ÂæöæRÒæöæP¢–b&öw&Òæ¶–æB—267D¶–æBäU$ ¢–bæ÷B6VÆbæÆVvÅöW&÷F&vWB†6&Bæ6&BÂF&vWBÂÆ–W%ö–æFW‚“ ¢&WGW&âæöæP¢F&vWEö–BÒF&vWBæö&¦V7Eö–@¢VÆ–b&öw&Òæ¶–æB–â´67D¶–æBäDÔtUó5ôõõ4”äuô5$TEU$RÂ67D¶–æBäDTÅôDÔtWÓ ¢–b€¢F&vWB—2æöæP¢÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"¢÷"F&vWBæ6öçG&öÆÆW"ÓÒÆ–W%ö–æFW€¢÷"æ÷B6VÆbåöÆVvÅöFÖvU÷F&vWB‡F&vWBÂÆ–W%ö–æFW‚¢“ ¢6VÆbæÆör€¢&FVEö–çFW&7F–öâ"ÂÆ–W#×Æ–W"ææÖRÂ6&CÖ6&BææÖRÂ&V6öãÒ&æõöÆVvÅ÷F&vWB ¢¢&WGW&âæöæP¢F&vWEö–BÒF&vWBæö&¦V7Eö–@¢VÆ–b&öw&Òæ¶–æB—267D¶–æBä5$TEU$UõõtU%ôDÔtS ¢–bæ÷B6VÆbåöÆVvÅö7&VGW&U÷÷vW%÷6÷W&6R€¢6÷W&6U÷F&vWBÂÆ–W%ö–æFW€¢’÷"æ÷B6VÆbåöÆVvÅö7&VGW&U÷÷vW%÷&V6—–VçB‡F&vWBÂÆ–W%ö–æFW‚“ ¢&WGW&âæöæP¢76W'B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢F&vWEö–BÒF&vWBæö&¦V7Eö–@¢VÆ–b&öw&Òæ¶–æB—267D¶–æBäôõ¤Uõ5”ÄÃ ¢–b€¢F&vWB—2æöæP¢÷"æ÷B—6–ç7Fæ6R‡F&vWBÂ7F6´ö&¦V7B¢÷"æ÷B6VÆbåö—5öÆVvÅöö÷¦U÷F&vWB‡F&vWBÂÆ–W%ö–æFW‚¢“ ¢&WGW&âæöæP¢F&vWEö–BÒF&vWBæö&¦V7Eö–@¢VÆ–b&öw&Òæ¶–æB—267D¶–æBä4õTåDU%õD$tUEõ5TÄÃ ¢–b€¢6VÆbç&–÷&—G•÷7FFR—2æöæP¢÷"6VÆbç&–÷&—G•÷7FFRç&W6öÇWF–öå÷VæF–æp¢÷"6VÆbç&–÷&—G•÷7FFRçÆ–W%ö–æFW‚ÒÆ–W%ö–æFW€¢÷"æ÷B6VÆbåö—5öÆVvÅö†æEö6÷VçFW%÷F&vWB†6&Bæ6&BÂF&vWB¢“ ¢&WGW&âæöæP¢76W'B—6–ç7Fæ6R‡F&vWBÂ7F6´ö&¦V7B¢F&vWEö–BÒF&vWBæö&¦V7Eö–@¢VÆ–b&öw&Òæ¶–æB—267D¶–æBäDU5E$õ•ô%D”d5EôTä4„åDÔTåEôõ%õõtU%óEô5$TEU$S ¢–b€¢F&vWB—2æöæP¢÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"¢÷"æ÷B6VÆbåö—5öFW7G&÷•ö'F–f7EöVæ6†çFÖVçEö÷%÷÷vW%óEö7&VGW&U÷F&vWB‡F&vWB¢÷"æ÷B6VÆbåöÆVvÅ÷F&vWF–æu÷&÷FV7F–öâ‡F&vWBÂÆ–W%ö–æFW‚¢“ ¢6VÆbæÆör€¢&FVEö–çFW&7F–öâ"ÂÆ–W#×Æ–W"ææÖRÂ6&CÖ6&BææÖRÂ&V6öãÒ&æõöÆVvÅ÷F&vWB ¢¢&WGW&âæöæP¢F&vWEö–BÒF&vWBæö&¦V7Eö–@¢VÆ–b&öw&Òæ¶–æB—267D¶–æBäõD”ôäÅôDU5E$õ•ôäEô5$TDS ¢–bF&vWB—2æ÷BæöæS ¢–bæ÷B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB’÷"æ÷B6VÆbåöÆVvÅö÷F–öæÅöFW7G&÷•÷F&vWB€¢F&vWBÂÆ–W%ö–æFW€¢“ ¢&WGW&âæöæP¢F&vWEö–BÒF&vWBæö&¦V7Eö–@¢VÆ–b&öw&Òæ¶–æB—267D¶–æBä4ôäD•D”ôäÅôDU5E$õ•ôäEô5$TDS ¢–bæ÷B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB’÷"æ÷B6VÆbåöÆVvÅö6öæF—F–öæÅöFW7G&÷•÷F&vWB€¢F&vWBÂÆ–W%ö–æFW€¢“ ¢&WGW&âæöæP¢F&vWEö–BÒF&vWBæö&¦V7Eö–@¢VÆ–b&öw&Òæ¶–æB—267D¶–æBåD$tUDTEõ$TÔõdÃ ¢&VÖ÷fÂÒ6VÆbæ–çFW'&WFW"çF&vWFVE÷&VÖ÷fÅ÷&öw&Ò†6&Bæ6&B¢–b€¢&VÖ÷fÂ—2æöæP¢÷"æ÷B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢÷"æ÷B6VÆbåöÆVvÅ÷F&vWFVE÷&VÖ÷fÅ÷F&vWB‡F&vWBÂÆ–W%ö–æFW‚Â&VÖ÷fÂ¢“ ¢&WGW&âæöæP¢F&vWEö–BÒF&vWBæö&¦V7Eö–@¢VÆ–b&öw&Òæ¶–æB—267D¶–æBä´”4´TEô5$TEU$UõC ¢–b€¢æ÷B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"¢÷"æ÷BF&vWBæ—5ö7&VGW&P¢“ ¢&WGW&âæöæP¢F&vWEö–BÒF&vWBæö&¦V7Eö–@¢VÆ–b&öw&Òæ¶–æB—267D¶–æBåD$tUDTEô4õTåDU%ô´U•tõ$Eôu$åC ¢–bæ÷B6VÆbåöÆVvÅö6÷VçFW%ö¶W—v÷&Eöw&çE÷F&vWB‡F&vWBÂÆ–W%ö–æFW‚“ ¢&WGW&âæöæP¢76W'B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢F&vWEö–BÒF&vWBæö&¦V7Eö–@¢VÆ–b&öw&Òæ¶–æB—267D¶–æBåDTÕõ$%•ôDTD…õ$UEU$åôu$åC ¢–bæ÷B6VÆbåöÆVvÅöFVF…÷&WGW&åöw&çE÷F&vWB‡F&vWBÂÆ–W%ö–æFW‚“ ¢&WGW&âæöæP¢76W'B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢F&vWEö–BÒF&vWBæö&¦V7Eö–@¢VÆ–b&öw&Òæ¶–æB—267D¶–æBåDTÕõ$%•õE•Uô$4UõEôE$s ¢æ–ÖF–öâÒ6VÆbæ–çFW'&WFW"çFV×÷&'•÷G—Uö&6U÷EöG&u÷&öw&Ò†6&Bæ6&B¢–bæ–ÖF–öâ—2æöæR÷"æ÷B6VÆbåöÆVvÅ÷FV×÷&'•÷G—Uö&6U÷E÷F&vWB€¢F&vWBÂÆ–W%ö–æFW‚Âæ–ÖF–öâçF&vWE÷G—W0¢“ ¢&WGW&âæöæP¢76W'B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢F&vWEö–BÒF&vWBæö&¦V7Eö–@¢VÆ–b&öw&Òæ¶–æB—267D¶–æBåD$tUDTEõTÕôdÅ””äuõ45%“ ¢7Fæ6RÒ6VÆbæ–çFW'&WFW"çF&vWFVE÷V×öfÇ––æu÷67'•÷&öw&Ò†6&Bæ6&B¢–b7Fæ6R—2æöæR÷"æ÷B6VÆbåöÆVvÅöÖöFÅö7&VGW&U÷F&vWB‡F&vWBÂÆ–W%ö–æFW‚“ ¢&WGW&âæöæP¢76W'B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢F&vWEö–BÒF&vWBæö&¦V7Eö–@¢VÆ–b&öw&Òæ¶–æB—267D¶–æBåD$tUDTEôÄ”%$%•õ$UEU$åôäEõDô´Tã ¢–bæ÷B6VÆbåöÆVvÅ÷F&vWFVEöÆ–'&'•÷&WGW&â‡F&vWBÂÆ–W%ö–æFW‚“ ¢&WGW&âæöæP¢76W'B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢F&vWEö–BÒF&vWBæö&¦V7Eö–@¢VÆ–b€¢&öw&Òæ¶–æ@¢–â°¢67D¶–æBäÄ”%$%•õ4T$4…õDõô„äBÀ¢67D¶–æBäõD”ôäÅô„äEõ$U4UBÀ¢67D¶–æBä4ôäD•D”ôäÅõ4äTµõDô´Tå2À¢67D¶–æBåDõô5$TEU$Uõ4TÄT5D”ôâÀ¢Ð¢æBF&vWB—2æ÷BæöæP¢“ ¢&WGW&âæöæP¢VÆ–b&öw&Òæ¶–æB—267D¶–æBäu$dU”$Eõ$T5U%4”ôã ¢&V7W'6–öâÒ6VÆbæ–çFW'&WFW"æw&fW–&E÷&V7W'6–öå÷&öw&Ò†6&Bæ6&B¢–b€¢F&vWB—2æ÷BæöæP¢÷"&V7W'6–öâ—2æöæP¢÷"æ÷B6VÆbå÷fÆ–Eöw&fW–&E÷&V7W'6–öå÷F&vWG2€¢&V7W'6–öå÷F&vWG2ÂÆ–W%ö–æFW‚Â&V7W'6–öâæÖæ÷fÇVUöÆ–Ö—@¢¢“ ¢&WGW&âæöæP¢VÆ–b&öw&Òæ¶–æB—267D¶–æBäÔôDÅõDô´Tåôõ%ô5$TEU$UõTÕ ¢–bÖöFUög&vÖVçBÓÒÖöFÂçFö¶Våög&vÖVçC ¢–bF&vWB—2æ÷BæöæS ¢&WGW&âæöæP¢VÇ6S ¢–bæ÷B6VÆbåöÆVvÅöÖöFÅö7&VGW&U÷F&vWB‡F&vWBÂÆ–W%ö–æFW‚“ ¢&WGW&âæöæP¢76W'B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢F&vWEö–BÒF&vWBæö&¦V7Eö–@¢VÆ–b&öw&Òæ¶–æB—267D¶–æBåTå5Uõ%DTC ¢g&vÖVçG2Ò¶Æ–æRç7G&—‚’f÷"Æ–æR–â6&Bæ÷&6ÆU÷FW‡Bç7Æ—FÆ–æW2‚’–bÆ–æRç7G&—‚•Ð¢f÷"g&vÖVçB–âg&vÖVçG2÷"¶6&BçG—UöÆ–æUÓ ¢6VÆbçVç7W÷'FVB€¢6&Bæ6&BÀ¢'7VÆÅö÷%÷W&ÖæVçE÷6VÖçF–75öæ÷Eö–×ÆVÖVçFVB"À¢Æ–W%ö–æFWƒ×Æ–W%ö–æFW‚À¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢¢&WGW&âæöæP ¢&WV—&VÖVçBÒ6VÆbæÖæ÷&WV—&VÖVçB†6&BÂ…÷fÇVS×…÷fÇVR¢–b&WV—&VÖVçB—2æöæS ¢6VÆbçVç7W÷'FVB€¢6&Bæ6&BÀ¢&Öæö6÷7Eöæ÷Eö–×ÆVÖVçFVB"À¢Æ–W%ö–æFWƒ×Æ–W%ö–æFW‚À¢÷&6ÆUög&vÖVçCÖ6&BæÖæö6÷7B÷"'¦W&òÖæ6÷7B"À¢¢&WGW&âæöæP¢ÆâÒ6VÆbç–ÖVçE÷Æâ€¢Æ–W%ö–æFW‚À¢6&BÀ¢ÆÆ÷uöw&fW–&CÖ67Eög&öÕöw&fW–&BÀ¢ÆÆ÷uöW†–ÆSÖ67Eög&öÕöW†–ÆRÀ¢…÷fÇVS×…÷fÇVRÀ¢¢–bÆâ—2æöæS ¢&WGW&âæöæP¢7VÆÂÒ6VÆbåö6öÖÖ—Eöææ÷Væ6VÖVçE÷–ÖVçB€¢6&BÀ¢ÆâÀ¢67Eö¶–æC×&öw&Òæ¶–æBÀ¢F&vWEö–C×F&vWEö–BÀ¢67Eög&öÕöw&fW–&CÖ67Eög&öÕöw&fW–&BÀ¢f–æÆ—G•ööåöVçG'“Ö67Eög&öÕöw&fW–&BÀ¢67Eög&öÕ÷&†VÃÖ67Eög&öÕöW†–ÆRÀ¢¢–bÆ–æ¶VEöw&çB—2æ÷BæöæS ¢6VÆbåö6öç7VÖUöÆ–æ¶VE÷Æ•öw&çB†Æ–æ¶VEöw&çBÂ6&Bæö&¦V7Eö–B¢–b&öw&Òæ¶–æB—267D¶–æBäu$dU”$Eõ$T5U%4”ôã ¢7VÆÂçF&vWEö–G2ÒGWÆR†—FVÒæö&¦V7Eö–Bf÷"—FVÒ–â&V7W'6–öå÷F&vWG2¢6VÆbæÆör€¢&w&fW–&E÷&V7W'6–öå÷F&vWG5öææ÷Væ6VB"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢F&vWEö–G3ÖÆ—7B‡7VÆÂçF&vWEö–G2’À¢6öçG&öÆÆW#×Æ–W%ö–æFW‚À¢¢–b&öw&Òæ¶–æB—267D¶–æBäÔôDÅõDô´Tåôõ%ô5$TEU$UõTÕ ¢7VÆÂæÖöFUög&vÖVçBÒÖöFUög&vÖVç@¢6VÆbæÆör€¢&ÖöFÅöÖöFUö6†÷6Vâ"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢ÖöFUög&vÖVçCÖÖöFUög&vÖVçBÀ¢F&vWEö–C×F&vWEö–BÀ¢6öçG&öÆÆW#×Æ–W%ö–æFW‚À¢¢–b&öw&Òæ¶–æB—267D¶–æBä5$TEU$UõõtU%ôDÔtS ¢76W'B—6–ç7Fæ6R‡6÷W&6U÷F&vWBÂW&ÖæVçB¢7VÆÂç6÷W&6U÷F&vWEö–BÒ6÷W&6U÷F&vWBæö&¦V7Eö–@¢–b67&–f–6Uö6÷7B—2æ÷BæöæS ¢7VÆÂæ¶–6¶W%÷67&–f–6Uö–BÒ67&–f–6Uö6÷7Bæö&¦V7Eö–@¢6VÆbæÖ÷fUöö&¦V7B‡67&–f–6Uö6÷7BÂ&w&fW–&B"Â&V6öãÒ&¶–6¶W%÷67&–f–6Uö6÷7B"¢6VÆbæÆör€¢&¶–6¶W%ö6÷7E÷–B"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢67&–f–6VEö–C×67&–f–6Uö6÷7Bæö&¦V7Eö–BÀ¢6&C×7VÆÂææÖRÀ¢¢6VÆbæ6†V6µ÷7FFUö&6VEö7F–öç2‚¢6VÆbæÆör€¢'7VÆÅö67B"À¢Æ–W#×Æ–W"ææÖRÀ¢Æ–W%ö–æFWƒ×Æ–W%ö–æFW‚À¢6&C×7VÆÂææÖRÀ¢6&E÷G—W3×GWÆR€¢¶–æ@¢f÷"¶–æB–â€¢$'F–f7B"À¢$&GFÆR"À¢$7&VGW&R"À¢$Væ6†çFÖVçB"À¢$–ç7FçB"À¢%ÆæW7vÆ¶W""À¢%6÷&6W'’"À¢%G&–&Â"À¢¢–b¶–æB–â7VÆÂæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢’À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢F&vWEö–C×F&vWEö–BÀ¢6÷W&6U÷F&vWEö–C×7VÆÂç6÷W&6U÷F&vWEö–BÀ¢ÖöFUög&vÖVçC×7VÆÂæÖöFUög&vÖVçBÀ¢…÷fÇVS×7VÆÂç…÷fÇVRÀ¢¢6VÆbåöVçVWVU÷7VÆÅö67E÷G&–vvW'2‡7VÆÂ¢&WGW&â7VÆÀ ¢FVb&W6öÇfU÷F÷ööe÷7F6²‡6VÆb’Óâ6&Dö&¦V7BÂW&ÖæVçBÂæöæS ¢""%&W6öÇfRF†RWF†÷&—FF—fRF÷7VÆÂ÷"G&–vvW&VB&–Æ—G’â"" ¢–bæ÷B6VÆbç7F6³ ¢&—6RfÇVTW'&÷"‚&6ææ÷B&W6öÇfRâV×G’7F6²"¢7VÆÂÒ6VÆbç7F6µ²ÓÐ¢7F6µöö&¦V7Eö–BÒ7VÆÂæö&¦V7Eö–@¢–bæ÷B6VÆbæ—5öWF†÷&—FF—fR‡7VÆÂÂ'7F6²"“ ¢&—6RfÇVTW'&÷"‚'F÷7F6²ö&¦V7B—2æ÷BWF†÷&—FF—fR"¢–b—6–ç7Fæ6R‡7VÆÂÂG&–vvW&VD&–Æ—G”ö&¦V7B“ ¢–b€¢€¢€¢7VÆÂæVffV7B—2G&–vvW$VffV7Bä5$TDUõDô´Tà¢æB6VÆbæ–çFW'&WFW"æVçG'•öÆVfUö÷%ö'F–f7Eö67E÷Fö¶Våö6öçFW‡B€¢7VÆÂç6÷W&6Uö6&BÂ7VÆÂæ÷&6ÆUög&vÖVç@¢¢—2æ÷BæöæP¢¢÷"7VÆÂæVffV7@¢–â°¢G&–vvW$VffV7BäÅD%ôÕUDtTâÀ¢G&–vvW$VffV7BäED4µõD$tUEô4õTåDU"À¢G&–vvW$VffV7Bå$ÔT4”ôU„”ÄUô4„ô”4RÀ¢G&–vvW$VffV7Bå$ÔT4”õ$TdÄU„•dUõ$UEU$âÀ¢G&–vvW$VffV7Bå$„TÅôÄÄ”ä4UôU„”ÄRÀ¢G&–vvW$VffV7Bå$„TÅôED4µõÄ’À¢G&–vvW$VffV7Bä4ôÔ$EôD•44$Eôõ%õ45$”d”4RÀ¢G&–vvW$VffV7BäTäEõ5DUõ5TÄÅõE•U5ôE$rÀ¢G&–vvW$VffV7BäD•4T%ôTäEõ5DUÀ¢G&–vvW$VffV7BäUD%õd”t”ÄåDRÀ¢G&–vvW$VffV7Båd”t”ÄåDUôD•44$BÀ¢G&–vvW$VffV7BäUD%ôµ$äuõ$Td”ÄÂÀ¢G&–vvW$VffV7BäUD%ôÔ”ÄÅõD…$TRÀ¢G&–vvW$VffV7BäUD%ô¥U%•õ$”rÀ¢G&–vvW$VffV7BäUD%ôdôôEõ4T$4‚À¢G&–vvW$VffV7BäUD%ôE$uôD•44$BÀ¢G&–vvW$VffV7Bä4ôÔ$EôDÔtUôE$uôD•44$BÀ¢G&–vvW$VffV7Bä4ôÔ$EôDÔtUôE$uôÄõ4UôÄ”dRÀ¢G&–vvW$VffV7Bä4ôÔ$EôDÔtUôu$dU”$EôED4´U"À¢G&–vvW$VffV7BåUD”Ä•E•õD$tUBÀ¢G&–vvW$VffV7BäUD%ôÔ”ÄÅôE$uôD•44$BÀ¢G&–vvW$VffV7Bä4Ä55ôÄUdTÅõEtõõ$T4õdU%’À¢G&–vvW$VffV7BäD•44$EôE$rÀ¢G&–vvW$VffV7BäD”U5ôE$rÀ¢G&–vvW$VffV7Bå4äTµôUD%ô4ôäD•D”ôâÀ¢G&–vvW$VffV7BäUD%ôE$”åôt”åõ45%’À¢G&–vvW$VffV7BäUD%õ4TÄeôÄ”dUôt”âÀ¢G&–vvW$VffV7Bä4ôäD•D”ôäÅôTåE%•õDô´TâÀ¢G&–vvW$VffV7BåU$ÔäTåEôÄTeEõ4TÄeô4õTåDU"À¢G&–vvW$VffV7Bä4ôåE$ôÄÄTEô5$TEU$UôÄTeEôõôäTåEôÄõ52À¢G&–vvW$VffV7Bä4ôåE$ôÄÄTEô4õTåDU$TEô5$TEU$UôÄTeEôÄ”dRÀ¢G&–vvW$VffV7Bä4ôåE$ôÄÄTEô%D”d5Eô4õTåDU%õE$å4dU"À¢G&–vvW$VffV7BäDÔtUõDõõ4TÄeôÔäÀ¢G&–vvW$VffV7Bä4Ä55õ5TÄÅô45EõDTÕô4õTåDU"À¢G&–vvW$VffV7BäUD%ô%D”d5EôE$rÀ¢G&–vvW$VffV7BäUD%õDõ5ETâÀ¢G&–vvW$VffV7BäUD%ôå•õD$tUEôDÔtRÀ¢G&–vvW$VffV7BäUD%ôDU5E$õ•õD$tUEô5$TEU$RÀ¢G&–vvW$VffV7BäUD%õD$tUEô5$TEU$UõTÕõTåDÀ¢Ð¢¢æBæ÷B6VÆbå÷&–÷&—G•÷&W6öÇWF–öåö–å÷&öw&W70¢æB‡6VÆbç&–÷&—G•÷7FFR—2æöæR÷"æ÷B6VÆbç&–÷&—G•÷7FFRç&W6öÇWF–öå÷VæF–ær¢“ ¢&—6RfÇVTW'&÷"€¢'&W&W6VçFVBG&–vvW&VB&–Æ—G’6ææ÷B&W6öÇfR&Vf÷&RÆÂÆ–W'272 ¢¢6VÆbå÷&W6öÇfU÷G&–vvW&VEö&–Æ—G’‡7VÆÂ¢&WGW&âæöæP¢–b—6–ç7Fæ6R‡7VÆÂÂ7F—fFVD&–Æ—G”ö&¦V7B“ ¢–bæ÷B6VÆbå÷&–÷&—G•÷&W6öÇWF–öåö–å÷&öw&W72æB€¢6VÆbç&–÷&—G•÷7FFR—2æöæR÷"æ÷B6VÆbç&–÷&—G•÷7FFRç&W6öÇWF–öå÷VæF–æp¢“ ¢&—6RfÇVTW'&÷"‚&7F—fFVB&–Æ—G’6ææ÷B&W6öÇfR&Vf÷&RÆÂÆ–W'272"¢6VÆbå÷&W6öÇfUö7F—fFVEö&–Æ—G’‡7VÆÂ¢&WGW&âæöæP¢Æ–W"Ò6VÆbçÆ–W'5·7VÆÂæ6öçG&öÆÆW%Ð¢F&vWBÒ6VÆbåöö&¦V7G2ævWB‡7VÆÂçF&vWEö–B÷"""¢6æVµö67BÒ7VÆÂç6æVµ÷&WGW&æVEöGF6¶W%ö–B—2æ÷BæöæP¢–b7VÆÂæ67Eö¶–æB—267D¶–æBä´”4´TEô5$TEU$UõBæB7VÆÂæ¶–6¶W%÷67&–f–6Uö–B—2æ÷BæöæS ¢–BÒ6VÆbåöö&¦V7G2ævWB‡7VÆÂæ¶–6¶W%÷67&–f–6Uö–B¢–b€¢æ÷B—6–ç7Fæ6R‡–BÂW&ÖæVçB¢÷"–Bç¦öæRÒ&f÷&ÖW" ¢÷"æ÷Bç’€¢WfVçE²&WfVçB%ÒÓÒ&¶–6¶W%ö6÷7E÷–B ¢æBWfVçBævWB‚'7F6µöö&¦V7Eö–B"’ÓÒ7VÆÂæö&¦V7Eö–@¢æBWfVçBævWB‚'67&–f–6VEö–B"’ÓÒ–Bæö&¦V7Eö–@¢f÷"WfVçB–â6VÆbæWfVçG0¢¢“ ¢&—6R76W'F–öäW'&÷"‚&¶–6¶W"6†ö–6RÆ6·2–B67&–f–6R"¢–b6æVµö67BæB€¢æ÷B6VÆbå÷&–÷&—G•÷&W6öÇWF–öåö–å÷&öw&W70¢æB‡6VÆbç&–÷&—G•÷7FFR—2æöæR÷"æ÷B6VÆbç&–÷&—G•÷7FFRç&W6öÇWF–öå÷VæF–ær¢“ ¢&—6RfÇVTW'&÷"‚%6æV²7VÆÂ6ææ÷B&W6öÇfR&Vf÷&RÆÂÆ–W'272" ¢–b7VÆÂæ67Eö¶–æB—267D¶–æBäU$æBæ÷B6VÆbæÆVvÅöW&÷F&vWB€¢7VÆÂæ6&BÂF&vWBÂ7VÆÂæ6öçG&öÆÆW ¢“ ¢&W6öÇfVBÒ6VÆbæÖ÷fUöö&¦V7B‡7VÆÂÂ&w&fW–&B"Â&V6öãÒ&W&öÆÅ÷F&vWG5ö–ÆÆVvÂ"¢6VÆbæÆör€¢&W&öf–ÆVB"À¢6&C×7VÆÂææÖRÀ¢6÷W&6Uö–C×7F6µöö&¦V7Eö–BÀ¢F&vWEö–C×7VÆÂçF&vWEö–BÀ¢&V6öãÒ&ÆÅ÷F&vWG5ö–ÆÆVvÂ"À¢¢&WGW&â&W6öÇfV@¢–b7VÆÂæ67Eö¶–æB–â´67D¶–æBä5$TEU$RÂ67D¶–æBåU$ÔäTåBÂ67D¶–æBäU$Ó ¢W&ÖæVçBÒ6VÆbæÖ÷fUöö&¦V7B€¢7VÆÂÀ¢&&GFÆVf–VÆB"À¢6öçG&öÆÆW#×7VÆÂæ6öçG&öÆÆW"À¢7VÖÖöæ–æu÷6–6³ÕG'VRÀ¢&V6öãÒ€¢'6æVµö7&VGW&U÷&W6öÇfVB ¢–b6æVµö67@¢VÇ6R€¢&7&VGW&U÷&W6öÇfVB ¢–b7VÆÂæ67Eö¶–æB—267D¶–æBä5$TEU$P¢VÇ6R'W&ÖæVçE÷&W6öÇfVB ¢¢’À¢¢76W'B—6–ç7Fæ6R‡W&ÖæVçBÂW&ÖæVçB¢–b7VÆÂæ67Eö¶–æB—267D¶–æBäU$ ¢6VÆbæGF6…öW&‡W&ÖæVçBÂF&vWB¢6VÆbæÆör€¢&W&÷&W6öÇfVB"À¢6&C×7VÆÂææÖRÀ¢7F6µöö&¦V7Eö–C×7F6µöö&¦V7Eö–BÀ¢6÷W&6Uö–C×W&ÖæVçBæö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢F&vWC×F&vWBæ6&BææÖRÀ¢6öçG&öÆÆW#×7VÆÂæ6öçG&öÆÆW"À¢÷vW#×F&vWBç÷vW"À¢F÷Vv†æW73×F&vWBçF÷Vv†æW72À¢÷&6ÆUög&vÖVçC×6VÆbæ–çFW'&WFW"æW&÷&öw&Ò‡7VÆÂæ6&B’æ÷&6ÆUög&vÖVçBÀ¢¢–b7VÆÂæf–æÆ—G•ööåöVçG'“ ¢W&ÖæVçBæ6÷VçFW'5²&f–æÆ—G’%ÒÒW&ÖæVçBæ6÷VçFW'2ævWB‚&f–æÆ—G’"Â’²¢6VÆbæÆör€¢&f–æÆ—G•ö6÷VçFW%÷Æ6VB"À¢6÷W&6Uö–C×7VÆÂæö&¦V7Eö–BÀ¢F&vWEö–C×W&ÖæVçBæö&¦V7Eö–BÀ¢6&C×W&ÖæVçBæ6&BææÖRÀ¢6÷VçFW%÷G—SÒ&f–æÆ—G’"À¢F÷FÃ×W&ÖæVçBæ6÷VçFW'5²&f–æÆ—G’%ÒÀ¢¢–b6æVµö67C ¢W&ÖæVçBçFVBÒG'VP¢6VÆbåö6öÖ&EöGF6¶W'2Ò6VÆbåö6öÖ&EöGF6¶W'2²‡W&ÖæVçBæö&¦V7Eö–BÂ¢6VÆbæÆör€¢'6æVµö7&VGW&U÷&W6öÇfVB"À¢Æ–W#×Æ–W"ææÖRÀ¢6&C×7VÆÂææÖRÀ¢7F6µöö&¦V7Eö–C×7F6µöö&¦V7Eö–BÀ¢W&ÖæVçEöö&¦V7Eö–C×W&ÖæVçBæö&¦V7Eö–BÀ¢FVfVæF–æu÷Æ–W#×7VÆÂç6æVµöFVfVæF–æu÷Æ–W"À¢FVCÕG'VRÀ¢GF6¶–æsÕG'VRÀ¢¢f÷"–æFW‚ÂWf–FVæ6R–âVçVÖW&FR‡6VÆbç6æVµöWf–FVæ6R“ ¢–bWf–FVæ6Rç7F6µöö&¦V7Eö–BÓÒ7F6µöö&¦V7Eö–C ¢6VÆbç6æVµöWf–FVæ6U¶–æFW…ÒÒ6æV´Wf–FVæ6R€¢Wf–FVæ6Ræ6&EöæÖRÀ¢Wf–FVæ6Ræ†æEöö&¦V7Eö–BÀ¢Wf–FVæ6Ræ6öçG&öÆÆW"À¢Wf–FVæ6RçGW&âÀ¢Wf–FVæ6Rç7FWÀ¢Wf–FVæ6Ræ÷&6ÆUög&vÖVçBÀ¢Wf–FVæ6RæÖæ÷&WV—&VÖVçBÀ¢Wf–FVæ6RæÖæ÷6÷W&6Uö–G2À¢Wf–FVæ6Rç&WGW&æVEöGF6¶W%ö–BÀ¢Wf–FVæ6Rç&WGW&æVEö†æEö–BÀ¢Wf–FVæ6RæFVfVæF–æu÷Æ–W"À¢Wf–FVæ6Rç7F6µöö&¦V7Eö–BÀ¢Wf–FVæ6Rç&–÷&—G•öWö6‚À¢W&ÖæVçBæö&¦V7Eö–BÀ¢G'VRÀ¢G'VRÀ¢Wf–FVæ6Rç6÷W&6U÷¦öæRÀ¢Wf–FVæ6RçW&Ö—76–öå÷6÷W&6Uö–BÀ¢¢'&V°¢VÇ6S ¢6VÆbæÆör€¢&7&VGW&U÷&W6öÇfVB ¢–b7VÆÂæ67Eö¶–æB—267D¶–æBä5$TEU$P¢VÇ6R'W&ÖæVçE÷&W6öÇfVB"À¢Æ–W#×Æ–W"ææÖRÀ¢6&C×7VÆÂææÖRÀ¢¢6VÆbç&Vg&W6…÷7FF–5÷EöÖöF–f–W'2‚¢6VÆbå÷&ö6W75ö7&VGW&W5öVçFW&VE÷G&–vvW'2€¢‡W&ÖæVçBÂ’À¢6÷W&6Uö–C×7F6µöö&¦V7Eö–B–b6æVµö67BVÇ6RæöæRÀ¢FVfW%÷G&–vvW'3×6æVµö67BÀ¢gFW%öWfVçCÖÆÖ&F6÷W&6RÂöWfVçC¢6VÆbç&W÷'E÷Vç7W÷'FVEö&–Æ—F–W2€¢7VÆÂæ6öçG&öÆÆW"Â7VÆÂæ6&BÂ6÷W&6S×6÷W&6P¢’À¢¢–bæ÷B6æVµö67C ¢6VÆbæ6†V6µ÷7FFUö&6VEö7F–öç2‚¢&WGW&âW&ÖæVç@ ¢ÆVvÅ÷F&vWBÒ7VÆÂæ67Eö¶–æB–â°¢67D¶–æBäE$uô4$E2À¢67D¶–æBåDõô4$Eõ4TÄT5D”ôâÀ¢67D¶–æBåDõô5$TEU$Uõ4TÄT5D”ôâÀ¢67D¶–æBäÄ”%$%•õ4T$4…õDõô„äBÀ¢67D¶–æBäõD”ôäÅô„äEõ$U4UBÀ¢67D¶–æBä4ôäD•D”ôäÅõ4äTµõDô´Tå2À¢Ò÷"†—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB’æB6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"’¢–b7VÆÂæ67Eö¶–æB—267D¶–æBäu$dU”$Eõ$T5U%4”ôã ¢&V7W'6–öâÒ6VÆbæ–çFW'&WFW"æw&fW–&E÷&V7W'6–öå÷&öw&Ò‡7VÆÂæ6&B¢76W'B&V7W'6–öâ—2æ÷BæöæRæB7VÆÂçF&vWEö–G0¢ÆVvÅ÷F&vWBÒç’€¢6VÆbåöÆVvÅöw&fW–&E÷&V7W'6–öå÷F&vWB€¢6VÆbåöö&¦V7G2ævWB†ö&¦V7Eö–B’Â7VÆÂæ6öçG&öÆÆW"Â&V7W'6–öâæÖæ÷fÇVUöÆ–Ö—@¢¢f÷"ö&¦V7Eö–B–â7VÆÂçF&vWEö–G0¢¢–b7VÆÂæ67Eö¶–æB—267D¶–æBäõD”ôäÅôDU5E$õ•ôäEô5$TDS ¢ÆVvÅ÷F&vWBÒ7VÆÂçF&vWEö–B—2æöæR÷"€¢—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢æB6VÆbåöÆVvÅö÷F–öæÅöFW7G&÷•÷F&vWB‡F&vWBÂ7VÆÂæ6öçG&öÆÆW"¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBä4ôäD•D”ôäÅôDU5E$õ•ôäEô5$TDS ¢ÆVvÅ÷F&vWBÒ—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB’æB6VÆbåöÆVvÅö6öæF—F–öæÅöFW7G&÷•÷F&vWB€¢F&vWBÂ7VÆÂæ6öçG&öÆÆW ¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBåD$tUDTEõ$TÔõdÃ ¢&VÖ÷fÂÒ6VÆbæ–çFW'&WFW"çF&vWFVE÷&VÖ÷fÅ÷&öw&Ò‡7VÆÂæ6&B¢ÆVvÅ÷F&vWBÒ€¢&VÖ÷fÂ—2æ÷BæöæP¢æB—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢æB6VÆbåöÆVvÅ÷F&vWFVE÷&VÖ÷fÅ÷F&vWB‡F&vWBÂ7VÆÂæ6öçG&öÆÆW"Â&VÖ÷fÂ¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBä5$TEU$UõõtU%ôDÔtS ¢FÖvU÷6÷W&6RÒ6VÆbåöö&¦V7G2ævWB‡7VÆÂç6÷W&6U÷F&vWEö–B÷"""¢ÆVvÅ÷F&vWBÒ6VÆbåöÆVvÅö7&VGW&U÷÷vW%÷6÷W&6R€¢FÖvU÷6÷W&6RÂ7VÆÂæ6öçG&öÆÆW ¢’÷"6VÆbåöÆVvÅö7&VGW&U÷÷vW%÷&V6—–VçB‡F&vWBÂ7VÆÂæ6öçG&öÆÆW"¢–b7VÆÂæ67Eö¶–æB–â´67D¶–æBäDÔtUó5ôõõ4”äuô5$TEU$RÂ67D¶–æBäDTÅôDÔtWÓ ¢ÆVvÅ÷F&vWBÒ€¢ÆVvÅ÷F&vW@¢æBF&vWBæ6öçG&öÆÆW"Ò7VÆÂæ6öçG&öÆÆW ¢æB6VÆbåöÆVvÅöFÖvU÷F&vWB‡F&vWBÂ7VÆÂæ6öçG&öÆÆW"¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBäôõ¤Uõ5”ÄÃ ¢ÆVvÅ÷F&vWBÒ6VÆbåö—5öÆVvÅöö÷¦U÷F&vWB‡F&vWBÂ7VÆÂæ6öçG&öÆÆW"¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBä4õTåDU%õD$tUEõ5TÄÃ ¢ÆVvÅ÷F&vWBÒ6VÆbåö—5öÆVvÅö†æEö6÷VçFW%÷F&vWB‡7VÆÂæ6&BÂF&vWB¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBäDU5E$õ•ô%D”d5EôTä4„åDÔTåEôõ%õõtU%óEô5$TEU$S ¢ÆVvÅ÷F&vWBÒ€¢ÆVvÅ÷F&vW@¢æB—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢æB6VÆbåö—5öFW7G&÷•ö'F–f7EöVæ6†çFÖVçEö÷%÷÷vW%óEö7&VGW&U÷F&vWB‡F&vWB¢æB6VÆbåöÆVvÅ÷F&vWF–æu÷&÷FV7F–öâ‡F&vWBÂ7VÆÂæ6öçG&öÆÆW"¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBä´”4´TEô5$TEU$UõC ¢ÆVvÅ÷F&vWBÒÆVvÅ÷F&vWBæB—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB’æBF&vWBæ—5ö7&VGW&P¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBåD$tUDTEô4õTåDU%ô´U•tõ$Eôu$åC ¢ÆVvÅ÷F&vWBÒ6VÆbåöÆVvÅö6÷VçFW%ö¶W—v÷&Eöw&çE÷F&vWB‡F&vWBÂ7VÆÂæ6öçG&öÆÆW"¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBåDTÕõ$%•ôDTD…õ$UEU$åôu$åC ¢ÆVvÅ÷F&vWBÒ6VÆbåöÆVvÅöFVF…÷&WGW&åöw&çE÷F&vWB‡F&vWBÂ7VÆÂæ6öçG&öÆÆW"¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBåDTÕõ$%•õE•Uô$4UõEôE$s ¢æ–ÖF–öâÒ6VÆbæ–çFW'&WFW"çFV×÷&'•÷G—Uö&6U÷EöG&u÷&öw&Ò‡7VÆÂæ6&B¢ÆVvÅ÷F&vWBÒæ–ÖF–öâ—2æ÷BæöæRæB6VÆbåöÆVvÅ÷FV×÷&'•÷G—Uö&6U÷E÷F&vWB€¢F&vWBÂ7VÆÂæ6öçG&öÆÆW"Âæ–ÖF–öâçF&vWE÷G—W0¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBåD$tUDTEõTÕôdÅ””äuõ45%“ ¢ÆVvÅ÷F&vWBÒ6VÆbåöÆVvÅöÖöFÅö7&VGW&U÷F&vWB‡F&vWBÂ7VÆÂæ6öçG&öÆÆW"¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBåD$tUDTEôÄ”%$%•õ$UEU$åôäEõDô´Tã ¢ÆVvÅ÷F&vWBÒ6VÆbåöÆVvÅ÷F&vWFVEöÆ–'&'•÷&WGW&â‡F&vWBÂ7VÆÂæ6öçG&öÆÆW"¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBäÔôDÅõDô´Tåôõ%ô5$TEU$UõTÕ ¢ÖöFÂÒ6VÆbæ–çFW'&WFW"æÖöFÅ÷Fö¶Våö÷%ö7&VGW&U÷V×÷&öw&Ò‡7VÆÂæ6&B¢–bÖöFÂ—2æöæR÷"7VÆÂæÖöFUög&vÖVçBæ÷B–â°¢ÖöFÂçFö¶Våög&vÖVçBÀ¢ÖöFÂçV×ög&vÖVçBÀ¢Ó ¢&—6R76W'F–öäW'&÷"‚'7F6¶VBÖöFÂ7VÆÂÆ÷7B—G26ö×ÆWFR6VÖçF–72"¢ÆVvÅ÷F&vWBÒ€¢7VÆÂçF&vWEö–B—2æöæP¢–b7VÆÂæÖöFUög&vÖVçBÓÒÖöFÂçFö¶Våög&vÖVç@¢VÇ6R6VÆbåöÆVvÅöÖöFÅö7&VGW&U÷F&vWB‡F&vWBÂ7VÆÂæ6öçG&öÆÆW"¢¢–bæ÷BÆVvÅ÷F&vWC ¢&W6öÇfVEö6&BÒ6VÆbæÖ÷fUöö&¦V7B‡7VÆÂÂ&w&fW–&B"Â&V6öãÒ'7VÆÅ÷&W6öÇfVB"¢76W'B—6–ç7Fæ6R‡&W6öÇfVEö6&BÂ6&Dö&¦V7B¢6VÆbæÆör€¢'7VÆÅ÷&W6öÇfVEöæõöVffV7B"À¢WfVçEö–CÖb'7VÆÃ§·7F6µöö&¦V7Eö–GÓ§&W6öÇfVB"À¢Æ–W#×Æ–W"ææÖRÀ¢6&C×7VÆÂææÖRÀ¢6÷W&6Uö–C×&W6öÇfVEö6&Bæö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçC×7VÆÂæ6&Bæ÷&6ÆU÷FW‡BÀ¢F&vWE÷6÷W&6Uö–C×7VÆÂçF&vWEö–BÀ¢F&vWE÷6÷W&6Uö–G3Ò€¢Æ—7B‡7VÆÂçF&vWEö–G2¢–b7VÆÂæ67Eö¶–æB—267D¶–æBäu$dU”$Eõ$T5U%4”ôà¢VÇ6RæöæP¢’À¢&V6öãÒ&ÆÅ÷F&vWG5ö–ÆÆVvÂ"À¢¢&WGW&â&W6öÇfVEö6&@¢–b7VÆÂæ67Eö¶–æBæ÷B–â°¢67D¶–æBäôõ¤Uõ5”ÄÂÀ¢67D¶–æBä4õTåDU%õD$tUEõ5TÄÂÀ¢67D¶–æBäE$uô4$E2À¢67D¶–æBåDõô4$Eõ4TÄT5D”ôâÀ¢67D¶–æBåDõô5$TEU$Uõ4TÄT5D”ôâÀ¢67D¶–æBäÄ”%$%•õ4T$4…õDõô„äBÀ¢67D¶–æBäõD”ôäÅô„äEõ$U4UBÀ¢67D¶–æBäu$dU”$Eõ$T5U%4”ôâÀ¢67D¶–æBä4ôäD•D”ôäÅõ4äTµõDô´Tå2À¢67D¶–æBäõD”ôäÅôDU5E$õ•ôäEô5$TDRÀ¢67D¶–æBä4ôäD•D”ôäÅôDU5E$õ•ôäEô5$TDRÀ¢67D¶–æBä5$TEU$UõõtU%ôDÔtRÀ¢67D¶–æBäÔôDÅõDô´Tåôõ%ô5$TEU$UõTÕÀ¢Ó ¢76W'B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢f–ÇFW%÷ÆâÒæöæP¢f–ÇFW%÷6VÖçF–72ÒæöæP¢–b7VÆÂæ67Eö¶–æB—267D¶–æBäôõ¤Uõ5”ÄÃ ¢76W'B—6–ç7Fæ6R‡F&vWBÂ7F6´ö&¦V7B¢6÷VçFW&VBÒ6VÆbæÖ÷fUöö&¦V7B‡F&vWBÂ&w&fW–&B"Â&V6öãÒ&ö÷¦U÷7–ÆÅö6÷VçFW&VB"¢6VÆbæÆör€¢'7VÆÅö6÷VçFW&VB"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢F&vWE÷7VÆÅö–C×F&vWBæö&¦V7Eö–BÀ¢F&vWEöö&¦V7Eö–C×F&vWBçF&vWEö–BÀ¢F&vWEö6&C×F&vWBæ6&BææÖRÀ¢6öçG&öÆÆW#×7VÆÂæ6öçG&öÆÆW"À¢÷&6ÆUög&vÖVçC×7VÆÂæ6&Bæ÷&6ÆU÷FW‡BÀ¢F&vWE÷&VÆF–öç6†—Ò&6÷VçFW%÷F&vWE÷7VÆÂ"À¢6÷VçFW&VEöö&¦V7Eö–CÖ6÷VçFW&VBæö&¦V7Eö–BÀ¢¢×WFvVâÒ6VÆbæ–çFW'&WFW"å$TDTd”äTEõDô´Tå5²&×WFvVâ%Ð¢&öw&ÒÒFö¶Vä7&VF–öå&öw&Ò†×WFvVâÂ¢7&VFVBÒ6VÆbæ7&VFU÷Fö¶Vç2€¢7VÆÂæ6öçG&öÆÆW"À¢&öw&ÒÀ¢6÷W&6Uö6&C×7VÆÂæ6&BææÖRÀ¢÷&6ÆUög&vÖVçC×7VÆÂæ6&Bæ÷&6ÆU÷FW‡BÀ¢6÷W&6Uö–C×7VÆÂæö&¦V7Eö–BÀ¢¢6VÆbæÆör€¢&ö÷¦U÷7–ÆÅ÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢F&vWE÷7VÆÅö–C×F&vWBæö&¦V7Eö–BÀ¢6÷VçFW&VEöö&¦V7Eö–CÖ6÷VçFW&VBæö&¦V7Eö–BÀ¢×WFvVå÷Fö¶Våö–CÖ7&VFVE³Òæö&¦V7Eö–BÀ¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBä4õTåDU%õD$tUEõ5TÄÃ ¢76W'B—6–ç7Fæ6R‡F&vWBÂ7F6´ö&¦V7B¢6÷VçFW&VBÒ6VÆbæÖ÷fUöö&¦V7B‡F&vWBÂ&w&fW–&B"Â&V6öãÒ'7VÆÅö6÷VçFW&VB"¢6VÆbæÆör€¢'7VÆÅö6÷VçFW&VB"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢F&vWE÷7VÆÅö–C×F&vWBæö&¦V7Eö–BÀ¢F&vWEö6&C×F&vWBæ6&BææÖRÀ¢6öçG&öÆÆW#×7VÆÂæ6öçG&öÆÆW"À¢÷&6ÆUög&vÖVçC×7VÆÂæ6&Bæ÷&6ÆU÷FW‡BÀ¢F&vWE÷&VÆF–öç6†—Ò&6÷VçFW%÷F&vWEöæöæ7&VGW&U÷7VÆÂ ¢–b&æöæ7&VGW&R"–â7VÆÂæ6&Bæ÷&6ÆU÷FW‡@¢VÇ6R&6÷VçFW%÷F&vWE÷7VÆÂ"À¢6÷VçFW&VEöö&¦V7Eö–CÖ6÷VçFW&VBæö&¦V7Eö–BÀ¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBäE$uô4$E3 ¢G&u÷6VÖçF–72ÒæW‡B€¢€¢6VÆbæ–çFW'&WFW"æG&uö6&G5÷6VÖçF–5ö6÷fW&vR‡7VÆÂæ6&BÂg&vÖVçB¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡7VÆÂæ6&B¢–b6VÆbæ–çFW'&WFW"æG&uö6&G5÷6VÖçF–5ö6÷fW&vR‡7VÆÂæ6&BÂg&vÖVçB¢—2æ÷BæöæP¢’À¢æöæRÀ¢¢–bG&u÷6VÖçF–72—2æöæR÷"æ÷BG&u÷6VÖçF–72æ6÷fW&vRægVÆÇ•÷7W÷'FVC ¢&—6R76W'F–öäW'&÷"‚'7F6¶VBG&r7VÆÂæòÆöævW"†2W†V7WF&ÆR6VÖçF–72"¢G&u÷7V66VVFVBÒ6VÆbæG&r‡Æ–W"ÂG&u÷6VÖçF–72ç&öw&ÒçVçF—G’¢6VÆbæÆör€¢&G&u÷7VÆÅ÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢Æ–W#×Æ–W"ææÖRÀ¢6&C×7VÆÂææÖRÀ¢VçF—G“ÖG&u÷6VÖçF–72ç&öw&ÒçVçF—G’À¢G&u÷7V66VVFVCÖG&u÷7V66VVFVBÀ¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBåDõô4$Eõ4TÄT5D”ôã ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"çF÷ö6&E÷6VÆV7F–öå÷&öw&Ò‡7VÆÂæ6&B¢–b&öw&Ò—2æöæS ¢&—6R76W'F–öäW'&÷"‚'7F6¶VB6&B6VÆV7F–öâ—2æòÆöævW"W†V7WF&ÆR"¢6VÆbç&W6öÇfU÷F÷ö6&E÷6VÆV7F–öâ‡7VÆÂæ6öçG&öÆÆW"Â&öw&ÒÂ6÷W&6Uö–C×7VÆÂæö&¦V7Eö–B¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBåDõô5$TEU$Uõ4TÄT5D”ôã ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"çF÷ö7&VGW&U÷6VÆV7F–öå÷&öw&Ò‡7VÆÂæ6&B¢–b&öw&Ò—2æöæS ¢&—6R76W'F–öäW'&÷"‚'7F6¶VBF÷Ö7&VGW&R7VÆÂÆ÷7B—G26ö×ÆWFR6VÖçF–72"¢6VÆbç&W6öÇfU÷F÷ö7&VGW&U÷6VÆV7F–öâ€¢7VÆÂæ6öçG&öÆÆW"Â&öw&ÒÂ6÷W&6Uö–C×7VÆÂæö&¦V7Eö–@¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBäÄ”%$%•õ4T$4…õDõô„äC ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"æÆ–'&'•÷6V&6…÷Fõö†æE÷&öw&Ò‡7VÆÂæ6&B¢–b&öw&Ò—2æöæS ¢&—6R76W'F–öäW'&÷"‚'7F6¶VBÆ–'&'’6V&6‚Æ÷7B—G26ö×ÆWFR6VÖçF–72"¢6VÆbç&W6öÇfUöÆ–'&'•÷6V&6…÷Fõö†æB€¢7VÆÂæ6öçG&öÆÆW"Â&öw&Òç6V&6…ög&vÖVçBÂ6÷W&6Uö–C×7VÆÂæö&¦V7Eö–@¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBäõD”ôäÅô„äEõ$U4UC ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"æ÷F–öæÅö†æE÷&W6WE÷&öw&Ò‡7VÆÂæ6&B¢–b&öw&Ò—2æöæS ¢&—6R76W'F–öäW'&÷"‚'7F6¶VB†æB&W6WBÆ÷7B—G26ö×ÆWFR6VÖçF–72"¢6VÆbç&W6öÇfUö÷F–öæÅö†æE÷&W6WB€¢&öw&ÒæG&u÷VçF—G’Â&öw&ÒæVffV7Eög&vÖVçBÂ6÷W&6Uö–C×7VÆÂæö&¦V7Eö–@¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBäu$dU”$Eõ$T5U%4”ôã ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"æw&fW–&E÷&V7W'6–öå÷&öw&Ò‡7VÆÂæ6&B¢–b&öw&Ò—2æöæS ¢&—6R76W'F–öäW'&÷"‚'7F6¶VBw&fW–&B&V7W'6–öâÆ÷7B—G26ö×ÆWFR6VÖçF–72"¢VçFW&VBÒµÐ¢–çfÆ–BÒµÐ¢f÷"ö&¦V7Eö–B–â7VÆÂçF&vWEö–G3 ¢6æF–FFRÒ6VÆbåöö&¦V7G2ævWB†ö&¦V7Eö–B¢–bæ÷B6VÆbåöÆVvÅöw&fW–&E÷&V7W'6–öå÷F&vWB€¢6æF–FFRÂ7VÆÂæ6öçG&öÆÆW"Â&öw&ÒæÖæ÷fÇVUöÆ–Ö—@¢“ ¢–çfÆ–BæVæB†ö&¦V7Eö–B¢6öçF–çVP¢W&ÖæVçBÒ6VÆbæÖ÷fUöö&¦V7B€¢6æF–FFRÀ¢&&GFÆVf–VÆB"À¢6öçG&öÆÆW#×7VÆÂæ6öçG&öÆÆW"À¢&V6öãÒ&w&fW–&E÷&V7W'6–öå÷&WGW&â"À¢¢76W'B—6–ç7Fæ6R‡W&ÖæVçBÂW&ÖæVçB¢VçFW&VBæVæB‚†ö&¦V7Eö–BÂW&ÖæVçB’¢6VÆbç&Vg&W6…÷7FF–5÷EöÖöF–f–W'2‚¢6VÆbæÆör€¢&w&fW–&E÷&V7W'6–öå÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢6öçG&öÆÆW#×7VÆÂæ6öçG&öÆÆW"À¢÷&6ÆUög&vÖVçC×&öw&ÒæVffV7Eög&vÖVçBÀ¢F&vWEö–G3ÖÆ—7B‡7VÆÂçF&vWEö–G2’À¢VçFW&VCÕ°¢²&w&fW–&Eö–B#¢6÷W&6RÂ&&GFÆVf–VÆEö–B#¢—FVÒæö&¦V7Eö–GÐ¢f÷"6÷W&6RÂ—FVÒ–âVçFW&V@¢ÒÀ¢–çfÆ–E÷F&vWEö–G3Ö–çfÆ–BÀ¢¢6VÆbå÷&ö6W75ö7&VGW&W5öVçFW&VE÷G&–vvW'2€¢GWÆR†—FVÒf÷"òÂ—FVÒ–âVçFW&VB’À¢6÷W&6Uö–C×7VÆÂæö&¦V7Eö–BÀ¢FVfW%÷G&–vvW'3ÕG'VRÀ¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBä4ôäD•D”ôäÅõ4äTµõDô´Tå3 ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"æ6öæF—F–öæÅ÷6æVµ÷Fö¶Vç5÷&öw&Ò‡7VÆÂæ6&B¢–b&öw&Ò—2æöæS ¢&—6R76W'F–öäW'&÷"‚'7F6¶VB6öæF—F–öæÂFö¶Vâ7VÆÂÆ÷7B—G26VÖçF–72"¢7&VFVBÒ6VÆbæ7&VFU÷Fö¶Vç2€¢7VÆÂæ6öçG&öÆÆW"À¢&WÆ6R‡&öw&ÒçFö¶VâÂFVC×6æVµö67B’À¢6÷W&6Uö6&C×7VÆÂææÖRÀ¢÷&6ÆUög&vÖVçC×&öw&ÒæVffV7Eög&vÖVçBÀ¢6÷W&6Uö–C×7VÆÂæö&¦V7Eö–BÀ¢FVfW%÷÷7Eö7&VF–öãÕG'VRÀ¢FVfW%÷G&–vvW'3ÕG'VRÀ¢GF6¶–æuöFVfVæFW#×7VÆÂç6æVµöFVfVæF–æu÷Æ–W"–b6æVµö67BVÇ6RæöæRÀ¢¢6VÆbæÆör€¢&6öæF—F–öæÅ÷Fö¶Vç5÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢Fö¶Våö–G3Õ·Fö¶Vâæö&¦V7Eö–Bf÷"Fö¶Vâ–â7&VFVEÒÀ¢6æVµö6÷7E÷–C×6æVµö67BÀ¢FVC×6æVµö67BÀ¢GF6¶–æuöFVfVæFW#×7VÆÂç6æVµöFVfVæF–æu÷Æ–W"–b6æVµö67BVÇ6RæöæRÀ¢÷&6ÆUög&vÖVçC×&öw&ÒæVffV7Eög&vÖVçBÀ¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBäõD”ôäÅôDU5E$õ•ôäEô5$TDS ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"æ÷F–öæÅöFW7G&÷•öæEö7&VFU÷&öw&Ò‡7VÆÂæ6&B¢–b&öw&Ò—2æöæS ¢&—6R76W'F–öäW'&÷"‚'7F6¶VB÷F–öæÂ&VÖ÷fÂÆ÷7B—G26VÖçF–72"¢–b—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB“ ¢6VÆbæFW7G&÷’‡F&vWB¢7&VFVBÒ6VÆbæ7&VFU÷Fö¶Vç2€¢7VÆÂæ6öçG&öÆÆW"À¢&öw&ÒçFö¶VâÀ¢6÷W&6Uö6&C×7VÆÂæ6&BææÖRÀ¢÷&6ÆUög&vÖVçC×7VÆÂæ6&Bæ÷&6ÆU÷FW‡BÀ¢6÷W&6Uö–C×7VÆÂæö&¦V7Eö–BÀ¢FVfW%÷÷7Eö7&VF–öãÕG'VRÀ¢FVfW%÷G&–vvW'3ÕG'VRÀ¢¢6VÆbæÆör€¢&÷F–öæÅ÷&VÖ÷fÅ÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢F&vWEö–C×7VÆÂçF&vWEö–BÀ¢Fö¶Våö–G3Õ¶—FVÒæö&¦V7Eö–Bf÷"—FVÒ–â7&VFVEÒÀ¢÷&6ÆUög&vÖVçC×7VÆÂæ6&Bæ÷&6ÆU÷FW‡BÀ¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBä4ôäD•D”ôäÅôDU5E$õ•ôäEô5$TDS ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"æ6öæF—F–öæÅöFW7G&÷•öæEö7&VFU÷&öw&Ò‡7VÆÂæ6&B¢–b&öw&Ò—2æöæS ¢&—6R76W'F–öäW'&÷"‚'7F6¶VB6öæF—F–öæÂ&VÖ÷fÂÆ÷7B—G26VÖçF–72"¢76W'B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢Æ7Eö¶æ÷våöÖæ÷fÇVRÒF&vWBæ6&BæÖæ÷fÇVP¢6VÆbæFW7G&÷’‡F&vWB¢7&VFVBÒ€¢6VÆbæ7&VFU÷Fö¶Vç2€¢7VÆÂæ6öçG&öÆÆW"À¢&öw&ÒçFö¶VâÀ¢6÷W&6Uö6&C×7VÆÂæ6&BææÖRÀ¢÷&6ÆUög&vÖVçC×7VÆÂæ6&Bæ÷&6ÆU÷FW‡BÀ¢6÷W&6Uö–C×7VÆÂæö&¦V7Eö–BÀ¢FVfW%÷÷7Eö7&VF–öãÕG'VRÀ¢FVfW%÷G&–vvW'3ÕG'VRÀ¢¢–bÆ7Eö¶æ÷våöÖæ÷fÇVRÃÒ&öw&ÒæÖ†–×VÕöÖæ÷fÇVP¢VÇ6R‚¢¢6VÆbæÆör€¢&6öæF—F–öæÅ÷&VÖ÷fÅ÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢F&vWEö–C×7VÆÂçF&vWEö–BÀ¢Æ7Eö¶æ÷våöÖæ÷fÇVSÖÆ7Eö¶æ÷våöÖæ÷fÇVRÀ¢Fö¶Våö–G3Õ¶—FVÒæö&¦V7Eö–Bf÷"—FVÒ–â7&VFVEÒÀ¢÷&6ÆUög&vÖVçC×7VÆÂæ6&Bæ÷&6ÆU÷FW‡BÀ¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBä´”4´TEô5$TEU$UõC ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"æ¶–6¶VEö7&VGW&U÷E÷&öw&Ò‡7VÆÂæ6&B¢–b&öw&Ò—2æöæS ¢&—6R76W'F–öäW'&÷"‚'7F6¶VB¶–6¶VBÖöF–f–W"—2æòÆöævW"W†V7WF&ÆR"¢ÖöF–f–W"Ò&öw&Òæ¶–6¶VB–b7VÆÂæ¶–6¶W%÷67&–f–6Uö–B—2æ÷BæöæRVÇ6R&öw&Òæ÷&F–æ'¢6VÆbæÇ•÷EöÖöF–f–W"€¢F&vWBÀ¢¦ÖöF–f–W"À¢GW&F–öãÒ'VçF–ÅöVæEööe÷GW&â"À¢6÷W&6Uö6&C×7VÆÂææÖRÀ¢÷&6ÆUög&vÖVçC×7VÆÂæ6&Bæ÷&6ÆU÷FW‡BÀ¢6÷W&6Uöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢¢6VÆbæÆör€¢&¶–6¶VEö7&VGW&U÷E÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢¶–6¶W%÷67&–f–6Uö–C×7VÆÂæ¶–6¶W%÷67&–f–6Uö–BÀ¢÷vW#ÖÖöF–f–W%³ÒÀ¢F÷Vv†æW73ÖÖöF–f–W%³ÒÀ¢¢6VÆbæ6†V6µ÷7FFUö&6VEö7F–öç2‚¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBåD$tUDTEô4õTåDU%ô´U•tõ$Eôu$åC ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"çF&vWFVEö6÷VçFW%ö¶W—v÷&Eöw&çE÷&öw&Ò‡7VÆÂæ6&B¢–b&öw&Ò—2æöæS ¢&—6R76W'F–öäW'&÷"‚'7F6¶VB6÷VçFW"ÖæBÖ¶W—v÷&B7VÆÂÆ÷7B—G26VÖçF–72"¢76W'B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢6VÆbçÆ6Uö6÷VçFW'2€¢F&vWBÀ¢&öw&Òæ6÷VçFW%÷G—RÀ¢&öw&ÒçVçF—G’À¢6÷W&6Uö6&C×7VÆÂææÖRÀ¢÷&6ÆUög&vÖVçC×&öw&ÒæVffV7Eög&vÖVçBÀ¢6÷W&6Uö–C×7VÆÂæö&¦V7Eö–BÀ¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢FVfW%÷÷7E÷Æ6VÖVçCÕG'VRÀ¢¢f÷"¶W—v÷&B–â&öw&Òæ¶W—v÷&G3 ¢F&vWBçFV×÷&'•ö¶W—v÷&EöVffV7G2æVæB€¢FV×÷&'”¶W—v÷&DVffV7B€¢FV×÷&'”¶W—v÷&B†¶W—v÷&B’À¢'VçF–ÅöVæEööe÷GW&â"À¢7VÆÂæö&¦V7Eö–BÀ¢&öw&ÒæVffV7Eög&vÖVçBÀ¢F–ÖW7F××6VÆbåöVffV7E÷F–ÖW7F×‚’À¢¢¢6VÆbæÆör€¢&6÷VçFW%ö¶W—v÷&Eöw&çE÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢6÷W&6Uö–C×7VÆÂæö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢6÷VçFW%÷G—S×&öw&Òæ6÷VçFW%÷G—RÀ¢VçF—G“×&öw&ÒçVçF—G’À¢¶W—v÷&G3ÖÆ—7B‡&öw&Òæ¶W—v÷&G2’À¢÷&6ÆUög&vÖVçC×&öw&ÒæVffV7Eög&vÖVçBÀ¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBåDTÕõ$%•ôDTD…õ$UEU$åôu$åC ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"çFV×÷&'•öFVF…÷&WGW&åöw&çE÷&öw&Ò‡7VÆÂæ6&B¢–b&öw&Ò—2æöæS ¢&—6R76W'F–öäW'&÷"‚'7F6¶VBFV×÷&'’FVF‚&WGW&âÆ÷7B6ö×ÆWFR6VÖçF–72"¢76W'B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢F–ÖW7F×Ò6VÆbåöVffV7E÷F–ÖW7F×‚¢F&vWBçFV×÷&'•ö¶W—v÷&EöVffV7G2æVæB€¢FV×÷&'”¶W—v÷&DVffV7B€¢FV×÷&'”¶W—v÷&B‡&öw&Òæ¶W—v÷&B’À¢'VçF–ÅöVæEööe÷GW&â"À¢7VÆÂæö&¦V7Eö–BÀ¢&öw&ÒæVffV7Eög&vÖVçBÀ¢F–ÖW7F××F–ÖW7F×À¢¢¢F&vWBçFV×÷&'•öFVF…÷&WGW&åöVffV7G2æVæB€¢FV×÷&'”FVF…&WGW&äVffV7B€¢'VçF–ÅöVæEööe÷GW&â"Â7VÆÂæö&¦V7Eö–BÂ&öw&ÒæVffV7Eög&vÖVçBÂF–ÖW7F× ¢¢¢6VÆbæÆör€¢'FV×÷&'•öFVF…÷&WGW&åöw&çFVB"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢¶W—v÷&C×&öw&Òæ¶W—v÷&BÀ¢÷&6ÆUög&vÖVçC×&öw&ÒæVffV7Eög&vÖVçBÀ¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBåDTÕõ$%•õE•Uô$4UõEôE$s ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"çFV×÷&'•÷G—Uö&6U÷EöG&u÷&öw&Ò‡7VÆÂæ6&B¢–b&öw&Ò—2æöæS ¢&—6R76W'F–öäW'&÷"‚'7F6¶VBæ–ÖF–öâÖæBÖG&r7VÆÂÆ÷7B—G26VÖçF–72"¢76W'B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢6VÆbæÇ•÷FV×÷&'•÷G—UöæEö&6U÷B€¢F&vWBÀ¢FFVE÷G—W3×&öw&ÒæFFVE÷G—W2À¢÷vW#×&öw&Òç÷vW"À¢F÷Vv†æW73×&öw&ÒçF÷Vv†æW72À¢6÷W&6Uö–C×7VÆÂæö&¦V7Eö–BÀ¢6÷W&6Uö6&C×7VÆÂææÖRÀ¢÷&6ÆUög&vÖVçC×&öw&ÒæVffV7Eög&vÖVçBÀ¢¢6VÆbç&Vg&W6…÷7FF–5÷EöÖöF–f–W'2‚¢G&u÷7V66VVFVBÒ6VÆbæG&r‡Æ–W"Â&öw&ÒæG&u÷VçF—G’¢6VÆbæÆör€¢'FV×÷&'•öæ–ÖF–öåöG&u÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢6÷W&6Uö–C×7VÆÂæö&¦V7Eö–BÀ¢G—UöÆ–æS×F&vWBçG—UöÆ–æRÀ¢÷vW#×F&vWBç÷vW"À¢F÷Vv†æW73×F&vWBçF÷Vv†æW72À¢G&u÷VçF—G“×&öw&ÒæG&u÷VçF—G’À¢G&u÷7V66VVFVCÖG&u÷7V66VVFVBÀ¢G&våög&vÖVçC×&öw&ÒæG&uög&vÖVçBÀ¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBåD$tUDTEõTÕôdÅ””äuõ45%“ ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"çF&vWFVE÷V×öfÇ––æu÷67'•÷&öw&Ò‡7VÆÂæ6&B¢–b&öw&Ò—2æöæS ¢&—6R76W'F–öäW'&÷"‚'7F6¶VBV×öfÇ––ærõ67'’7VÆÂÆ÷7B—G26VÖçF–72"¢76W'B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢6VÆbæÇ•÷EöÖöF–f–W"€¢F&vWBÀ¢&öw&Òç÷vW"À¢&öw&ÒçF÷Vv†æW72À¢GW&F–öãÒ'VçF–ÅöVæEööe÷GW&â"À¢6÷W&6Uö6&C×7VÆÂææÖRÀ¢÷&6ÆUög&vÖVçC×&öw&ÒæVffV7Eög&vÖVçBÀ¢6÷W&6Uöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢¢F&vWBçFV×÷&'•ö¶W—v÷&EöVffV7G2æVæB€¢FV×÷&'”¶W—v÷&DVffV7B€¢FV×÷&'”¶W—v÷&B‡&öw&Òæ¶W—v÷&B’À¢'VçF–ÅöVæEööe÷GW&â"À¢7VÆÂæö&¦V7Eö–BÀ¢&öw&ÒæVffV7Eög&vÖVçBÀ¢F–ÖW7F××6VÆbåöVffV7E÷F–ÖW7F×‚’À¢¢¢6VÆbç&Vg&W6…÷7FF–5÷EöÖöF–f–W'2‚¢6†ö–6RÒ6VÆbç67'’€¢7VÆÂæ6öçG&öÆÆW"À¢&öw&Òç67'’À¢6÷W&6Uö6&C×7VÆÂææÖRÀ¢÷&6ÆUög&vÖVçC×&öw&ÒæVffV7Eög&vÖVçBÀ¢¢6VÆbæÆör€¢'F&vWFVE÷V×öfÇ––æu÷67'•÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢÷vW#×&öw&Òç÷vW"À¢F÷Vv†æW73×&öw&ÒçF÷Vv†æW72À¢¶W—v÷&C×&öw&Òæ¶W—v÷&BÀ¢67'“×&öw&Òç67'’æÖ÷VçBÀ¢F÷ö–G3ÖÆ—7B†6†ö–6RçF÷ö–G2’À¢&÷GFöÕö–G3ÖÆ—7B†6†ö–6Ræ&÷GFöÕö–G2’À¢¢6VÆbæ6†V6µ÷7FFUö&6VEö7F–öç2‚¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBåD$tUDTEôÄ”%$%•õ$UEU$åôäEõDô´Tã ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"çF&vWFVEöÆ–'&'•÷&WGW&åöæE÷Fö¶Vå÷&öw&Ò‡7VÆÂæ6&B¢–b&öw&Ò—2æöæS ¢&—6R76W'F–öäW'&÷"‚'7F6¶VBÆ–'&'’&WGW&âÆ÷7B—G26ö×ÆWFR6VÖçF–72"¢76W'B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢÷væW%ö–æFW‚ÒF&vWBæ÷væW ¢÷F–öç2Ò‚'F÷"Â&&÷GFöÒ"¢6VÆbåöÆ–'&'•÷÷6—F–öåö6†ö–6Uö7F—fRÒG'VP¢G'“ ¢÷6—F–öâÒ6VÆbæÆ–'&'•÷÷6—F–öåö6†ö÷6W"€¢÷væW%ö–æFW‚Â7VÆÂæö&¦V7Eö–BÂF&vWBæö&¦V7Eö–BÂ÷F–öç0¢¢f–æÆÇ“ ¢6VÆbåöÆ–'&'•÷÷6—F–öåö6†ö–6Uö7F—fRÒfÇ6P¢–b÷6—F–öâæ÷B–â÷F–öç3 ¢&—6RfÇVTW'&÷"‚'F&vWB÷væW"×W7B6VÆV7BÆVvÂÆ–'&'’÷6—F–öâ"¢Ö÷fVBÒ6VÆbæÖ÷fUöö&¦V7B€¢F&vWBÀ¢&Æ–'&'’"À¢Æ–'&'•÷÷6—F–öã×÷6—F–öâÀ¢&V6öãÒ'F&vWFVEöÆ–'&'•÷&WGW&â"À¢¢7&VFVBÒ6VÆbæ7&VFU÷Fö¶Vç2€¢7VÆÂæ6öçG&öÆÆW"À¢&öw&ÒçFö¶VâÀ¢6÷W&6Uö6&C×7VÆÂæ6&BææÖRÀ¢÷&6ÆUög&vÖVçC×&öw&Òæ÷&6ÆUög&vÖVçBÀ¢6÷W&6Uö–C×7VÆÂæö&¦V7Eö–BÀ¢FVfW%÷÷7Eö7&VF–öãÕG'VRÀ¢FVfW%÷G&–vvW'3ÕG'VRÀ¢¢6VÆbæÆör€¢'F&vWFVEöÆ–'&'•÷&WGW&å÷Fö¶Vå÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢F&vWEö÷væW#Ö÷væW%ö–æFW‚À¢6†÷6Vå÷÷6—F–öã×÷6—F–öâÀ¢FW7F–æF–öåö–CÖÖ÷fVBæö&¦V7Eö–BÀ¢Fö¶Våö–G3Õ¶—FVÒæö&¦V7Eö–Bf÷"—FVÒ–â7&VFVEÒÀ¢÷&6ÆUög&vÖVçC×&öw&Òæ÷&6ÆUög&vÖVçBÀ¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBäÔôDÅõDô´Tåôõ%ô5$TEU$UõTÕ ¢–b7VÆÂæÖöFUög&vÖVçBÓÒÖöFÂçFö¶Våög&vÖVçC ¢7&VFVBÒ6VÆbæ7&VFU÷Fö¶Vç2€¢7VÆÂæ6öçG&öÆÆW"À¢ÖöFÂçFö¶VâÀ¢6÷W&6Uö6&C×7VÆÂææÖRÀ¢÷&6ÆUög&vÖVçC×7VÆÂæÖöFUög&vÖVçBÀ¢6÷W&6Uö–C×7VÆÂæö&¦V7Eö–BÀ¢FVfW%÷÷7Eö7&VF–öãÕG'VRÀ¢FVfW%÷G&–vvW'3ÕG'VRÀ¢¢6VÆbæÆör€¢&ÖöFÅ÷7VÆÅ÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢ÖöFUög&vÖVçC×7VÆÂæÖöFUög&vÖVçBÀ¢Fö¶Våö–G3Õ·Fö¶Vâæö&¦V7Eö–Bf÷"Fö¶Vâ–â7&VFVEÒÀ¢F&vWEö–CÔæöæRÀ¢¢VÇ6S ¢76W'B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢6VÆbæÇ•÷EöÖöF–f–W"€¢F&vWBÀ¢ÖöFÂç÷vW"À¢ÖöFÂçF÷Vv†æW72À¢GW&F–öãÒ'VçF–ÅöVæEööe÷GW&â"À¢6÷W&6Uö6&C×7VÆÂææÖRÀ¢÷&6ÆUög&vÖVçC×7VÆÂæÖöFUög&vÖVçBÀ¢6÷W&6Uöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢¢F&vWBçFV×÷&'•ö¶W—v÷&EöVffV7G2æVæB€¢FV×÷&'”¶W—v÷&DVffV7B€¢ÖöFÂç7G&–¶Uö¶W—v÷&BÀ¢'VçF–ÅöVæEööe÷GW&â"À¢7VÆÂæö&¦V7Eö–BÀ¢7VÆÂæÖöFUög&vÖVçBÀ¢F–ÖW7F××6VÆbåöVffV7E÷F–ÖW7F×‚’À¢¢¢6VÆbæÆör€¢&ÖöFÅ÷7VÆÅ÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢ÖöFUög&vÖVçC×7VÆÂæÖöFUög&vÖVçBÀ¢Fö¶Våö–G3ÕµÒÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢¶W—v÷&CÖÖöFÂç7G&–¶Uö¶W—v÷&BçfÇVRÀ¢÷vW#ÖÖöFÂç÷vW"À¢F÷Vv†æW73ÖÖöFÂçF÷Vv†æW72À¢¢VÆ–b7VÆÂæ67Eö¶–æB–â´67D¶–æBäDÔtUó5ôõõ4”äuô5$TEU$RÂ67D¶–æBäDTÅôDÔtWÓ ¢6VÖçF–72Ò6VÆbæ–çFW'&WFW"æFÖvU÷6VÖçF–5ö6÷fW&vR€¢7VÆÂæ6&BÂ7VÆÂæ6&Bæ÷&6ÆU÷FW‡@¢¢–b6VÖçF–72—2æöæR÷"æ÷B6VÖçF–72æ6÷fW&vRç–ÆöEöW†V7WF&ÆS ¢&—6R76W'F–öäW'&÷"‚'7F6¶VBFÖvR7VÆÂæòÆöævW"†2W†V7WF&ÆR6VÖçF–72"¢76W'B6VÖçF–72ç&öw&ÒæÖ÷VçB—2æ÷BæöæP¢f–ÇFW%÷6VÖçF–72Ò6VÆbæ–çFW'&WFW"æ†æEö&÷GFöÕöG&u÷6VÖçF–5ö6÷fW&vR€¢7VÆÂæ6&BÂ7VÆÂæ6&Bæ÷&6ÆU÷FW‡@¢¢f–ÇFW%öW†V7WF&ÆRÒ€¢f–ÇFW%÷6VÖçF–72—2æ÷BæöæRæBf–ÇFW%÷6VÖçF–72æ6÷fW&vRægVÆÇ•÷7W÷'FV@¢¢6VÆbæFVÅöFÖvR€¢FÖvUG&ç67F–öâ€¢7VÆÂæ6öçG&öÆÆW"À¢7VÆÂÀ¢FÖvUF&vWD¶–æBä5$TEU$RÀ¢6VÖçF–72ç&öw&ÒæÖ÷VçBÀ¢7VÆÂæ6&Bæ÷&6ÆU÷FW‡BÀ¢F&vWC×F&vWBÀ¢’À¢FVfW%÷÷7EöFÖvSÖf–ÇFW%öW†V7WF&ÆRÀ¢¢–bf–ÇFW%öW†V7WF&ÆS ¢76W'Bf–ÇFW%÷6VÖçF–72—2æ÷BæöæP¢f–ÇFW%÷ÆâÒ6VÆbæ6†ö÷6Uö†æEö&÷GFöÕöG&r€¢7VÆÂæ6öçG&öÆÆW"Âf–ÇFW%÷6VÖçF–72ç&öw&Ð¢¢6VÆbæ6öÖÖ—Eö†æEö&÷GFöÕöG&r€¢7VÆÂæ6öçG&öÆÆW"À¢f–ÇFW%÷6VÖçF–72ç&öw&ÒÀ¢f–ÇFW%÷ÆâÀ¢6÷W&6Uö–C×7VÆÂæö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçC×7VÆÂæ6&Bæ÷&6ÆU÷FW‡BÀ¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBä5$TEU$UõõtU%ôDÔtS ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"æ7&VGW&U÷÷vW%öFÖvU÷&öw&Ò€¢7VÆÂæ6&BÂ7VÆÂæ6&Bæ÷&6ÆU÷FW‡@¢¢–b&öw&Ò—2æöæS ¢&—6R76W'F–öäW'&÷"‚'7F6¶VB7&VGW&R×÷vW"FÖvRÆ÷7B—G26VÖçF–72"¢6÷W&6RÒ6VÆbåöö&¦V7G2ævWB‡7VÆÂç6÷W&6U÷F&vWEö–B÷"""¢6÷W&6UöÆVvÂÒ6VÆbåöÆVvÅö7&VGW&U÷÷vW%÷6÷W&6R‡6÷W&6RÂ7VÆÂæ6öçG&öÆÆW"¢F&vWEöÆVvÂÒ6VÆbåöÆVvÅö7&VGW&U÷÷vW%÷&V6—–VçB‡F&vWBÂ7VÆÂæ6öçG&öÆÆW"¢Ö÷VçBÒÖ‚ƒÂ6÷W&6Rç÷vW"’–b6÷W&6UöÆVvÂVÇ6R ¢–b6÷W&6UöÆVvÂæBF&vWEöÆVvÂæBÖ÷VçBâ ¢76W'B—6–ç7Fæ6R‡6÷W&6RÂW&ÖæVçB’æB—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB¢WfVçBÒ6VÆbæFVÅöFÖvR€¢FÖvUG&ç67F–öâ€¢7VÆÂæ6öçG&öÆÆW"À¢6÷W&6RÀ¢FÖvUF&vWD¶–æBä5$TEU$RÀ¢Ö÷VçBÀ¢7VÆÂæ6&Bæ÷&6ÆU÷FW‡BÀ¢F&vWC×F&vWBÀ¢¢¢6VÆbæÆör€¢&7&VGW&U÷÷vW%öFÖvU÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢6÷W&6U÷F&vWEö–C×6÷W&6Ræö&¦V7Eö–BÀ¢F&vWEö–C×F&vWBæö&¦V7Eö–BÀ¢FÖvUöWfVçEö–CÖWfVçBæWfVçEö–BÀ¢Ö÷VçCÖÖ÷VçBÀ¢¢VÇ6S ¢6VÆbæÆör€¢&7&VGW&U÷÷vW%öFÖvU÷&W6öÇfVEöæõöFÖvR"À¢7F6µöö&¦V7Eö–C×7VÆÂæö&¦V7Eö–BÀ¢6÷W&6U÷F&vWEö–C×7VÆÂç6÷W&6U÷F&vWEö–BÀ¢F&vWEö–C×7VÆÂçF&vWEö–BÀ¢6÷W&6UöÆVvÃ×6÷W&6UöÆVvÂÀ¢F&vWEöÆVvÃ×F&vWEöÆVvÂÀ¢Ö÷VçCÖÖ÷VçBÀ¢¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBäDU5E$õ•ô%D”d5EôTä4„åDÔTåEôõ%õõtU%óEô5$TEU$S ¢6VÆbæFW7G&÷’‡F&vWB¢VÆ–b7VÆÂæ67Eö¶–æB—267D¶–æBåD$tUDTEõ$TÔõdÃ ¢&VÖ÷fÂÒ6VÆbæ–çFW'&WFW"çF&vWFVE÷&VÖ÷fÅ÷&öw&Ò‡7VÆÂæ6&B¢76W'B&VÖ÷fÂ—2æ÷BæöæP¢v5öVæ6†çFÖVçBÒ$Væ6†çFÖVçB"–âF&vWBçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢–b&VÖ÷fÂæFW7F–æF–öâÓÒ&W†–ÆR# ¢6VÆbæÖ÷fUöö&¦V7B‡F&vWBÂ&W†–ÆR"Â&V6öãÒ'F&vWFVE÷&VÖ÷fÅöW†–ÆR"¢VÇ6S ¢6VÆbæFW7G&÷’‡F&vWB¢–b€¢v5öVæ6†çFÖVç@¢æBæ÷B6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"¢æB&VÖ÷fÂæVæ6†çFÖVçEöÆ–fUöÆ÷70¢“ ¢6VÆbçÆ–W'5·7VÆÂæ6öçG&öÆÆW%ÒæÆ–fRÓÒ&VÖ÷fÂæVæ6†çFÖVçEöÆ–fUöÆ÷70¢6VÆbæÆör€¢&Æ–fUöÆ÷7B"À¢Æ–W#×6VÆbçÆ–W'5·7VÆÂæ6öçG&öÆÆW%ÒææÖRÀ¢Ö÷VçC×&VÖ÷fÂæVæ6†çFÖVçEöÆ–fUöÆ÷72À¢6÷W&6S×7VÆÂææÖRÀ¢÷&6ÆUög&vÖVçC×7VÆÂæ6&Bæ÷&6ÆU÷FW‡BÀ¢¢&W6öÇfVEö6&BÒ6VÆbæÖ÷fUöö&¦V7B‡7VÆÂÂ&w&fW–&B"Â&V6öãÒ'7VÆÅ÷&W6öÇfVB"¢76W'B—6–ç7Fæ6R‡&W6öÇfVEö6&BÂ6&Dö&¦V7B¢6VÆbç&W÷'E÷Vç7W÷'FVEö&–Æ—F–W2‡7VÆÂæ6öçG&öÆÆW"Â7VÆÂæ6&BÂ6÷W&6S×&W6öÇfVEö6&B¢6VÆbå÷v—FæW75÷&W6öÇfVE÷Vç7W÷'FVEö–ç7G'V7F–öç2‡&W6öÇfVEö6&B¢6VÆbæÆör€¢'7VÆÅ÷&W6öÇfVB"À¢WfVçEö–CÖb'7VÆÃ§·7F6µöö&¦V7Eö–GÓ§&W6öÇfVB"À¢Æ–W#×Æ–W"ææÖRÀ¢6&C×7VÆÂææÖRÀ¢6÷W&6Uö–C×&W6öÇfVEö6&Bæö&¦V7Eö–BÀ¢÷&6ÆUög&vÖVçC×7VÆÂæ6&Bæ÷&6ÆU÷FW‡BÀ¢F&vWCÒ‡F&vWBæ6&BææÖR–b—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB’VÇ6RæöæR’À¢F&vWE÷6÷W&6Uö–CÒ‡F&vWBæö&¦V7Eö–B–b—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB’VÇ6RæöæR’À¢¢–bf–ÇFW%÷Æâ—2æ÷BæöæS ¢6VÆbæ6†V6µ÷7FFUö&6VEö7F–öç2‚¢6VÆbæ6†V6µöÆ–fR‚¢6VÆbå÷WE÷VæF–æu÷G&–vvW'5ööå÷7F6²‚¢6VÆbåöG&–å÷G&–vvW&VEö&–Æ—F–W2‚¢–b7VÆÂæ67Eö¶–æB–â°¢67D¶–æBäõD”ôäÅôDU5E$õ•ôäEô5$TDRÀ¢67D¶–æBä4ôäD•D”ôäÅôDU5E$õ•ôäEô5$TDRÀ¢67D¶–æBåD$tUDTEõ$TÔõdÂÀ¢67D¶–æBäÔôDÅõDô´Tåôõ%ô5$TEU$UõTÕÀ¢67D¶–æBåD$tUDTEô4õTåDU%ô´U•tõ$Eôu$åBÀ¢67D¶–æBåDTÕõ$%•ôDTD…õ$UEU$åôu$åBÀ¢67D¶–æBåDTÕõ$%•õE•Uô$4UõEôE$rÀ¢67D¶–æBäÄ”%$%•õ4T$4…õDõô„äBÀ¢67D¶–æBäõD”ôäÅô„äEõ$U4UBÀ¢67D¶–æBäu$dU”$Eõ$T5U%4”ôâÀ¢67D¶–æBä4ôäD•D”ôäÅõ4äTµõDô´Tå2À¢67D¶–æBåDõô5$TEU$Uõ4TÄT5D”ôâÀ¢67D¶–æBåD$tUDTEôÄ”%$%•õ$UEU$åôäEõDô´TâÀ¢Ó ¢6VÆbæ6†V6µ÷7FFUö&6VEö7F–öç2‚¢6VÆbå÷WE÷VæF–æu÷G&–vvW'5ööå÷7F6²‚¢6VÆbåöG&–å÷G&–vvW&VEö&–Æ—F–W2‚¢&WGW&â&W6öÇfVEö6&@ ¢7FF–6ÖWF†ö@¢FVböFVfVÇE÷F÷ö7&VGW&U÷6VÆV7F–öåö6†ö–6R‡f–WrÂ÷F–öç2“ ¢""%&VfW"W6VgVÂ&ö&BfÇVRW6–æröæÇ’F†R–ç7V7FVB&—fFR6&BFW67&—F–öç2â"" ¢f7G2Ò¶6&Bæö&¦V7Eö–C¢6&Bf÷"6&B–âf–Wræ6&G7Ð¢&WGW&âÖ‚€¢÷F–öç2À¢¶W“ÖÆÖ&F÷F–öã¢€¢7VÒ†f7G5¶ö&¦V7Eö–EÒæÖæ÷fÇVRf÷"ö&¦V7Eö–B–â÷F–öâæ6&Eö–G2’À¢ÆVâ†÷F–öâæ6&Eö–G2’À¢7VÒ‚†f7G5¶ö&¦V7Eö–EÒç÷vW"÷"’f÷"ö&¦V7Eö–B–â÷F–öâæ6&Eö–G2’À¢’À¢ ¢FVb&W6öÇfU÷F÷ö7&VGW&U÷6VÆV7F–öâ‡6VÆbÂÆ–W%ö–æFW‚Â&öw&ÒÂ¢Â6÷W&6Uö–C¢7G"’ÓâæöæS ¢""$6†ö÷6RWFòâ7&VGW&W2&—fFVÇ’ÂVçFW"2&F6‚ÂF†Vâ&æFöÖ—¦RF†R&W7Bâ"" ¢Æ–W"Ò6VÆbçÆ–W'5·Æ–W%ö–æFW…Ð¢Æ–'&'’ÒÆ–W"æÆ–'&'¢–ç7V7FVBÒGWÆR‡&WfW'6VB†Æ–'&'•²×&öw&Òæ6÷VçB¥Ò’¢VÆ–v–&ÆRÒGWÆR†6&Bf÷"6&B–â–ç7V7FVB–b6&Bæ6&Bæ—5ö7&VGW&R¢6†ö–6W2Ò…F÷7&VGW&U6VÆV7F–öä÷F–öâ‚‚’’Â’²GWÆR€¢F÷7&VGW&U6VÆV7F–öä÷F–öâ‡GWÆR†6&Bæö&¦V7Eö–Bf÷"6&B–âw&÷W’¢f÷"VçF—G’–â&ævRƒÂÖ–â‡&öw&ÒæÖ†–×VÕö7&VGW&W2ÂÆVâ†VÆ–v–&ÆR’’²¢f÷"w&÷W–â6öÖ&–æF–öç2†VÆ–v–&ÆRÂVçF—G’¢–b7VÒ†6&BæÖæ÷fÇVRf÷"6&B–âw&÷W’ÃÒ&öw&ÒæÖ†–×VÕ÷F÷FÅöÖæ÷fÇVP¢¢f–WrÒF÷7&VGW&U6VÆV7F–öåf–Wuc"€¢Æ–W%ö–æFW‚À¢GWÆR†FW67&–&Uö6&B†6&Bæö&¦V7Eö–BÂ6&Bæ6&B’f÷"6&B–â–ç7V7FVB’À¢&öw&ÒæÖ†–×VÕö7&VGW&W2À¢&öw&ÒæÖ†–×VÕ÷F÷FÅöÖæ÷fÇVRÀ¢FV6—6–öåö6öçFW‡B‡6VÆbÂÆ–W%ö–æFW‚’À¢¢¦öæW2Ò6VÆbåöÆÅ÷¦öæUöÆ—7G2‚¢&Vf÷&U÷¦öæW2ÒGWÆR‡GWÆR‡¦öæR’f÷"¦öæR–â¦öæW2¢&æuö&Vf÷&RÒ6VÆbç&ærç7FFUöF–vW7@¢6VÆbå÷F÷ö7&VGW&U÷6VÆV7F–öåö6†ö–6Uö7F—fRÒG'VP¢G'“ ¢6†ö–6RÒ6VÆbçF÷ö7&VGW&U÷6VÆV7F–öåö6†ö÷6W"‡f–WrÂ6†ö–6W2¢–bæ÷B—6–ç7Fæ6R†6†ö–6RÂF÷7&VGW&U6VÆV7F–öä÷F–öâ’÷"6†ö–6Ræ÷B–â6†ö–6W3 ¢&—6RfÇVTW'&÷"‚'F÷Ö7&VGW&R6†ö÷6W"×W7B&WGW&âöæRÆVvÂ6öÖ&–æVB×fÇVR6†ö–6R"¢–b€¢ç’‡GWÆR‡¦öæR’Ò&Vf÷&Rf÷"¦öæRÂ&Vf÷&R–â¦—‡¦öæW2Â&Vf÷&U÷¦öæW2Â7G&–7CÕG'VR’¢÷"6VÆbç&ærç7FFUöF–vW7BÒ&æuö&Vf÷&P¢“ ¢&—6RfÇVTW'&÷"‚'F÷Ö7&VGW&R6†ö÷6W"×WFFVBWF†÷&—FF—fR7FFR"¢f–æÆÇ“ ¢6VÆbå÷F÷ö7&VGW&U÷6VÆV7F–öåö6†ö–6Uö7F—fRÒfÇ6P ¢6VÆV7FVBÒGWÆR€¢æW‡B†6&Bf÷"6&B–â–ç7V7FVB–b6&Bæö&¦V7Eö–BÓÒö&¦V7Eö–B¢f÷"ö&¦V7Eö–B–â6†ö–6Ræ6&Eö–G0¢¢&VÖ–æFW"Ò¶6&Bf÷"6&B–â–ç7V7FVB–b6&Bæ÷B–â6VÆV7FVEÐ¢&÷GFöÒÒ6VÆbç&ærç6‡VffÆVB‡&VÖ–æFW"ÂFöÖ–ãÖb'F÷ö7&VGW&U÷6VÆV7F–öåö&÷GFöÓ§·6÷W&6Uö–GÒ"¢Æ–'&'•³¥ÒÒ&÷GFöÒ²¶6&Bf÷"6&B–âÆ–'&'’–b6&Bæ÷B–â–ç7V7FVEÐ¢VçFW&VBÒµÐ¢f÷"6&B–â6VÆV7FVC ¢2F†R6VÆV7FVB6&G2†fRÇ&VG’&VVâ&VÖ÷fVBg&öÒF†RÆ–'&'’÷&FW&–æs°¢2&WF–âF†V—"WF†÷&—FF—fR6÷W&6R¦öæRVçF–ÂV6‚¦öæRG&ç6—F–öâà¢Æ–'&'’æVæB†6&B¢W&ÖæVçBÒ6VÆbæÖ÷fUöö&¦V7B€¢6&BÂ&&GFÆVf–VÆB"Â6öçG&öÆÆW#×Æ–W%ö–æFW‚Â&V6öãÒ'F÷ö7&VGW&U÷6VÆV7F–öåöVçG'’ ¢¢76W'B—6–ç7Fæ6R‡W&ÖæVçBÂW&ÖæVçB¢VçFW&VBæVæB‚†6&Bæö&¦V7Eö–BÂW&ÖæVçB’¢6VÆbæÆör€¢'F÷ö7&VGW&U÷6VÆV7F–öå÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–C×6÷W&6Uö–BÀ¢6öçG&öÆÆW#×Æ–W%ö–æFW‚À¢÷&6ÆUög&vÖVçC×&öw&ÒæVffV7Eög&vÖVçBÀ¢–ç7V7FVEö–G3Õ¶6&Bæö&¦V7Eö–Bf÷"6&B–â–ç7V7FVEÒÀ¢6VÆV7FVCÕ·²&Æ–'&'•ö–B#¢öÆBÂ&&GFÆVf–VÆEö–B#¢æWræö&¦V7Eö–GÒf÷"öÆBÂæWr–âVçFW&VEÒÀ¢&÷GFöÕö–G3Õ¶6&Bæö&¦V7Eö–Bf÷"6&B–â&÷GFöÕÒÀ¢Ö†–×VÕö7&VGW&W3×&öw&ÒæÖ†–×VÕö7&VGW&W2À¢Ö†–×VÕ÷F÷FÅöÖæ÷fÇVS×&öw&ÒæÖ†–×VÕ÷F÷FÅöÖæ÷fÇVRÀ¢¢6VÆbç&Vg&W6…÷7FF–5÷EöÖöF–f–W'2‚¢6VÆbå÷&ö6W75ö7&VGW&W5öVçFW&VE÷G&–vvW'2€¢GWÆR†æWrf÷"òÂæWr–âVçFW&VB’Â6÷W&6Uö–C×6÷W&6Uö–BÂFVfW%÷G&–vvW'3ÕG'VP¢ ¢FVb&W6öÇfU÷F÷ö6&E÷6VÆV7F–öâ‡6VÆbÂÆ–W%ö–æFW‚Â&öw&ÒÂ¢Â6÷W&6Uö–C¢7G"’ÓâæöæS ¢""$6†ö÷6R&—fFVÇ’g&öÒF†R–ç7V7FVBF÷6&G2ÂF†Vâ&æFöÖ—¦RöæÇ’F†R&VÖ–æFW"â"" ¢Æ–W"Ò6VÆbçÆ–W'5·Æ–W%ö–æFW…Ð¢Æ–'&'’ÒÆ–W"æÆ–'&'¢–ç7V7FVBÒGWÆR‡&WfW'6VB†Æ–'&'•²×&öw&Òæ6÷VçB¥Ò’¢VÆ–v–&ÆRÒGWÆR€¢6&@¢f÷"6&B–â–ç7V7FV@¢–b‡&öw&Òæ–æ6ÇVFUöÆæBæB6&Bæ—5öÆæB¢÷"&ööÂ‡6WB†6&BçG—UöÆ–æRç'F—F–öâ‚"(	B"•³%Òç7Æ—B‚’’b6WB‡&öw&Òç7V'G—W2’¢¢÷F–öç2Ò…F÷6&E6VÆV7F–öä÷F–öâ„æöæR’Â’²GWÆR€¢F÷6&E6VÆV7F–öä÷F–öâ†6&Bæö&¦V7Eö–B’f÷"6&B–âVÆ–v–&ÆP¢¢f–WrÒF÷6&E6VÆV7F–öåf–Wuc"€¢Æ–W%ö–æFW‚À¢GWÆR†FW67&–&Uö6&B†6&Bæö&¦V7Eö–BÂ6&Bæ6&B’f÷"6&B–â–ç7V7FVB’À¢FV6—6–öåö6öçFW‡B‡6VÆbÂÆ–W%ö–æFW‚’À¢¢&Vf÷&UöÆ–'&'’ÒGWÆR†Æ–'&'’¢&Vf÷&Uö†æBÒGWÆR‡Æ–W"æ†æB¢G'“ ¢6†ö–6RÒ6VÆbçF÷ö6&Eö6†ö÷6W"‡f–WrÂ÷F–öç2¢–bæ÷B—6–ç7Fæ6R†6†ö–6RÂF÷6&E6VÆV7F–öä÷F–öâ’÷"6†ö–6Ræ÷B–â÷F–öç3 ¢&—6RfÇVTW'&÷"‚'F÷6&B6†ö÷6W"×W7B&WGW&âöæRVÆ–v–&ÆR÷F–öâ"¢–bGWÆR†Æ–'&'’’Ò&Vf÷&UöÆ–'&'’÷"GWÆR‡Æ–W"æ†æB’Ò&Vf÷&Uö†æC ¢&—6RfÇVTW'&÷"‚'F÷6&B6†ö÷6W"×WFFVBWF†÷&—FF—fR¦öæW2"¢W†6WBW†6WF–öã ¢Æ–'&'•³¥ÒÒ&Vf÷&UöÆ–'&'¢Æ–W"æ†æE³¥ÒÒ&Vf÷&Uö†æ@¢&—6P¢6VÆV7FVBÒæW‡B‚†6&Bf÷"6&B–âVÆ–v–&ÆR–b6&Bæö&¦V7Eö–BÓÒ6†ö–6Ræ6&Eö–B’ÂæöæR¢–b6VÆV7FVB—2æ÷BæöæS ¢&WfVÆVEö–BÒ6VÆV7FVBæö&¦V7Eö–@¢6VÆbæÖ÷fUöö&¦V7B‡6VÆV7FVBÂ&†æB"Â&V6öãÒ'F÷ö6&E÷&WfVÆVE÷Fõö†æB"¢VÇ6S ¢&WfVÆVEö–BÒæöæP¢&VÖ–æFW"Ò¶6&Bf÷"6&B–â–ç7V7FVB–b6&B—2æ÷B6VÆV7FVEÐ¢&æFöÖ—¦VBÒ6VÆbç&ærç6‡VffÆVB‡&VÖ–æFW"ÂFöÖ–ãÒ'F÷ö6&E÷6VÆV7F–öåö&÷GFöÒ"¢–ç7V7FVEö–FVçF—F–W2Ò¶–B†6&B’f÷"6&B–â&VÖ–æFW'Ð¢Æ–'&'•³¥ÒÒ&æFöÖ—¦VB²¶6&Bf÷"6&B–âÆ–'&'’–b–B†6&B’æ÷B–â–ç7V7FVEö–FVçF—F–W5Ð¢6VÆbæÆör€¢'F÷ö6&E÷6VÆV7F–öå÷&W6öÇfVB"À¢6÷W&6Uö–C×6÷W&6Uö–BÀ¢Æ–W#×Æ–W"ææÖRÀ¢–ç7V7FVEö–G3Õ¶6&Bæö&¦V7Eö–Bf÷"6&B–â–ç7V7FVEÒÀ¢&WfVÆVEö–C×&WfVÆVEö–BÀ¢&÷GFöÕö–G3Õ¶6&Bæö&¦V7Eö–Bf÷"6&B–â&æFöÖ—¦VEÒÀ¢†æEö–C×Æ–W"æ†æE²ÓÒæö&¦V7Eö–B–b6VÆV7FVB—2æ÷BæöæRVÇ6RæöæRÀ¢ ¢7FF–6ÖWF†ö@¢FVböFVfVÇEöÆ–'&'•÷6V&6…ö6†ö–6R‡f–WrÂ÷F–öç2“ ¢""$6†ö÷6RæVVFVBÆæB÷"æV"×FW&Ò67F&ÆR7VÆÂg&öÒ&—fFR6&Bf7G2â"" ¢÷vâÒf–Wræ6öçFW‡Bæ&GFÆVf–VÆG5·f–WrçÆ–W%ö–æFW…Ð¢ÆæG2Ò7VÒ‚$ÆæB"–â—FVÒæ6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚’f÷"—FVÒ–â÷vâ¢ÆæEö–åö†æBÒç’€¢$ÆæB"–â6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚’f÷"6&B–âf–Wræ6öçFW‡Bæ÷våö†æ@¢¢f7G2Ò¶6&Bæö&¦V7Eö–C¢6&Bf÷"6&B–âf–Wræ6&G7Ð ¢FVb66÷&R†÷F–öâ“ ¢6&BÒf7G5¶÷F–öâæ6&Eö–EÐ¢ÆæBÒ$ÆæB"–â6&BçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚¢–bÆæBæBÆæG2ÂBæBæ÷BÆæEö–åö†æC ¢&WGW&âƒ2ÂÂ6&Bæö&¦V7Eö–B¢–bæ÷BÆæBæB6&BæÖæ÷fÇVRÃÒÆæG2² ¢&WGW&âƒ"Â6&BæÖæ÷fÇVRÂ6&Bæö&¦V7Eö–B¢–bæ÷BÆæC ¢&WGW&âƒÂÖ6&BæÖæ÷fÇVRÂ6&Bæö&¦V7Eö–B¢&WGW&âƒÂÂ6&Bæö&¦V7Eö–B ¢&WGW&âÖ‚†÷F–öç2Â¶W“×66÷&R ¢FVb&W6öÇfUö÷F–öæÅö†æE÷&W6WB€¢6VÆbÂVçF—G“¢–çBÂ÷&6ÆUög&vÖVçC¢7G"Â¢Â6÷W&6Uö–C¢7G ¢’ÓâæöæS ¢""$6öÆÆV7Bä6†ö–6W2ÂF†VâF—66&B6†÷6Vâ†æG2&Vf÷&Rç’Æ–W"G&w2â"" ¢÷&FW"Ò‡6VÆbæ7F—fU÷Æ–W"ÂÒ6VÆbæ7F—fU÷Æ–W"¢6†ö–6W3¢F–7E¶–çBÂ&ööÅÒÒ·Ð¢6æ6†÷G2ÒGWÆR‡GWÆR‡¦öæR’f÷"¦öæR–â6VÆbåöÆÅ÷¦öæUöÆ—7G2‚’¢f÷"–æFW‚–â÷&FW# ¢Æ–W"Ò6VÆbçÆ–W'5¶–æFW…Ð¢†æBÒGWÆR‡Æ–W"æ†æB¢6VÆbåö†æE÷&W6WEö6†ö–6Uö7F—fRÒG'VP¢G'“ ¢FV6—6–öâÒ6VÆbæ†æE÷&W6WEö6†ö÷6W"€¢–æFW‚À¢GWÆR†FW67&–&Uö6&B†6&Bæö&¦V7Eö–BÂ6&Bæ6&B’f÷"6&B–â†æB’À¢FV6—6–öåö6öçFW‡B‡6VÆbÂ–æFW‚’À¢¢–bG—R†FV6—6–öâ’—2æ÷B&ööÃ ¢&—6RfÇVTW'&÷"‚&†æB&W6WB6†ö–6R×W7B&R&ööÆVâ"¢–bç’€¢GWÆR‡¦öæR’Ò&Vf÷&P¢f÷"¦öæRÂ&Vf÷&R–â¦—‡6VÆbåöÆÅ÷¦öæUöÆ—7G2‚’Â6æ6†÷G2Â7G&–7CÕG'VR¢“ ¢&—6RfÇVTW'&÷"‚&†æB&W6WB6†ö÷6W"×WFFVBWF†÷&—FF—fR¦öæW2"¢W†6WBW†6WF–öã ¢f÷"¦öæRÂ&Vf÷&R–â¦—‡6VÆbåöÆÅ÷¦öæUöÆ—7G2‚’Â6æ6†÷G2Â7G&–7CÕG'VR“ ¢¦öæU³¥ÒÒ&Vf÷&P¢&—6P¢f–æÆÇ“ ¢6VÆbåö†æE÷&W6WEö6†ö–6Uö7F—fRÒfÇ6P¢6†ö–6W5¶–æFW…ÒÒFV6—6–öà¢F—66&FVC¢F–7E¶–çBÂÆ—7E·GWÆU·7G"Â7G%ÕÕÒÒ¶–æFWƒ¢µÒf÷"–æFW‚–â÷&FW'Ð¢f÷"–æFW‚–â÷&FW# ¢–b6†ö–6W5¶–æFW…Ó ¢f÷"6&B–âGWÆR‡6VÆbçÆ–W'5¶–æFW…Òæ†æB“ ¢Ö÷fVBÒ6VÆbæÖ÷fUöö&¦V7B€¢6&BÂ&w&fW–&B"Â&V6öãÒ&÷F–öæÅö†æE÷&W6WEöF—66&B ¢¢F—66&FVE¶–æFW…ÒæVæB‚†6&Bæö&¦V7Eö–BÂÖ÷fVBæö&¦V7Eö–B’¢G&vã¢F–7E¶–çBÂÆ—7E·7G%ÕÒÒ¶–æFWƒ¢µÒf÷"–æFW‚–â÷&FW'Ð¢7V66VVFVC¢F–7E¶–çBÂ&ööÅÒÒ·Ð¢f÷"–æFW‚–â÷&FW# ¢–b6†ö–6W5¶–æFW…Ó ¢Æ–W"Ò6VÆbçÆ–W'5¶–æFW…Ð¢&Vf÷&RÒÆVâ‡Æ–W"æ†æB¢7V66VVFVE¶–æFW…ÒÒ6VÆbæG&r‡Æ–W"ÂVçF—G’¢G&vå¶–æFW…ÒÒ¶6&Bæö&¦V7Eö–Bf÷"6&B–âÆ–W"æ†æE¶&Vf÷&S¥ÕÐ¢6VÆbæÆör€¢&÷F–öæÅö†æE÷&W6WE÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–C×6÷W&6Uö–BÀ¢÷&6ÆUög&vÖVçCÖ÷&6ÆUög&vÖVçBÀ¢æö÷&FW#ÖÆ—7B†÷&FW"’À¢6†ö–6W3Õ·²'Æ–W"#¢–æFW‚Â&F—66&EöæEöG&r#¢6†ö–6W5¶–æFW…×Òf÷"–æFW‚–â÷&FW%ÒÀ¢F—66&FVCÕ·²'Æ–W"#¢–æFW‚Â'¦öæUö–G2#¢F—66&FVE¶–æFW…×Òf÷"–æFW‚–â÷&FW%ÒÀ¢G&vãÕ·²'Æ–W"#¢–æFW‚Â&†æEö–G2#¢G&vå¶–æFW…×Òf÷"–æFW‚–â÷&FW%ÒÀ¢G&u÷VçF—G“×VçF—G’À¢G&u÷7V66VVFVCÕ·²'Æ–W"#¢–æFW‚Â'7V66W72#¢7V66VVFVBævWB†–æFW‚—Òf÷"–æFW‚–â÷&FW%ÒÀ¢ ¢FVb&W6öÇfUöÆ–'&'•÷6V&6…÷Fõö†æB€¢6VÆbÂÆ–W%ö–æFWƒ¢–çBÂ÷&6ÆUög&vÖVçC¢7G"Â¢Â6÷W&6Uö–C¢7G ¢’ÓâæöæS ¢""$v—fRF†R6V&6†–ærÆ–W"&—fFRÆVvÂ6†ö–6RÂÖ÷fR—BÂF†Vâ6‡VffÆRâ"" ¢Æ–W"Ò6VÆbçÆ–W'5·Æ–W%ö–æFW…Ð¢&Vf÷&UöÆ–'&'’ÒGWÆR‡Æ–W"æÆ–'&'’¢&Vf÷&Uö†æBÒGWÆR‡Æ–W"æ†æB¢6VÆV7FVBÒæöæP¢–b&Vf÷&UöÆ–'&'“ ¢÷F–öç2ÒGWÆR…F÷6&E6VÆV7F–öä÷F–öâ†6&Bæö&¦V7Eö–B’f÷"6&B–â&Vf÷&UöÆ–'&'’¢f–WrÒF÷6&E6VÆV7F–öåf–Wuc"€¢Æ–W%ö–æFW‚À¢GWÆR†FW67&–&Uö6&B†6&Bæö&¦V7Eö–BÂ6&Bæ6&B’f÷"6&B–â&Vf÷&UöÆ–'&'’’À¢FV6—6–öåö6öçFW‡B‡6VÆbÂÆ–W%ö–æFW‚’À¢¢6VÆbåöÆ–'&'•÷6V&6…ö6†ö–6Uö7F—fRÒG'VP¢G'“ ¢6†ö–6RÒ6VÆbæÆ–'&'•÷6V&6…ö6†ö÷6W"‡f–WrÂ÷F–öç2¢–bæ÷B—6–ç7Fæ6R†6†ö–6RÂF÷6&E6VÆV7F–öä÷F–öâ’÷"6†ö–6Ræ÷B–â÷F–öç3 ¢&—6RfÇVTW'&÷"‚&Æ–'&'’6V&6‚×W7B6VÆV7BöæRöffW&VB6&B"¢–bGWÆR‡Æ–W"æÆ–'&'’’Ò&Vf÷&UöÆ–'&'’÷"GWÆR‡Æ–W"æ†æB’Ò&Vf÷&Uö†æC ¢&—6RfÇVTW'&÷"‚&Æ–'&'’6V&6‚6†ö÷6W"×WFFVBWF†÷&—FF—fR¦öæW2"¢W†6WBW†6WF–öã ¢Æ–W"æÆ–'&'•³¥ÒÒ&Vf÷&UöÆ–'&'¢Æ–W"æ†æE³¥ÒÒ&Vf÷&Uö†æ@¢&—6P¢f–æÆÇ“ ¢6VÆbåöÆ–'&'•÷6V&6…ö6†ö–6Uö7F—fRÒfÇ6P¢6VÆV7FVBÒæW‡B†6&Bf÷"6&B–â&Vf÷&UöÆ–'&'’–b6&Bæö&¦V7Eö–BÓÒ6†ö–6Ræ6&Eö–B¢Ö÷fVBÒ€¢6VÆbæÖ÷fUöö&¦V7B‡6VÆV7FVBÂ&†æB"Â&V6öãÒ&Æ–'&'•÷6V&6…÷Fõö†æB"¢–b6VÆV7FVB—2æ÷BæöæP¢VÇ6RæöæP¢¢FöÖ–âÒb&Æ–'&'•÷6V&6ƒ§·6÷W&6Uö–GÒ ¢&U÷6‡VffÆUö–G2Ò¶6&Bæö&¦V7Eö–Bf÷"6&B–âÆ–W"æÆ–'&'•Ð¢Æ–W"æÆ–'&'•³¥ÒÒ6VÆbç&ærç6‡VffÆVB‡Æ–W"æÆ–'&'’ÂFöÖ–ãÖFöÖ–â¢6VÆbæÆör€¢&Æ–'&'•÷6V&6…÷Fõö†æE÷&W6öÇfVB"À¢7F6µöö&¦V7Eö–C×6÷W&6Uö–BÀ¢÷&6ÆUög&vÖVçCÖ÷&6ÆUög&vÖVçBÀ¢6V&6†–æu÷Æ–W#×Æ–W%ö–æFW‚À¢6VÆV7FVEö–CÔæöæR–b6VÆV7FVB—2æöæRVÇ6R6VÆV7FVBæö&¦V7Eö–BÀ¢†æEö–CÔæöæR–bÖ÷fVB—2æöæRVÇ6RÖ÷fVBæö&¦V7Eö–BÀ¢&U÷6‡VffÆUö–G3×&U÷6‡VffÆUö–G2À¢÷7E÷6‡VffÆUö–G3Õ¶6&Bæö&¦V7Eö–Bf÷"6&B–âÆ–W"æÆ–'&'•ÒÀ¢6‡VffÆUöFöÖ–ãÖFöÖ–âÀ¢ ¢7FF–6ÖWF†ö@¢FVbö—5öFW7G&÷•ö'F–f7EöVæ6†çFÖVçEö÷%÷÷vW%óEö7&VGW&U÷F&vWB€¢F&vWC¢W&ÖæVçBÀ¢’Óâ&ööÃ ¢""$WfÇVFRF†R&÷VæFVBF&vWB&VF–6FRg&öÒ7W'&VçB&GFÆVf–VÆB6†&7FW&—7F–72â"" ¢6&E÷G—W2Ò6WB‡F&vWBçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚’¢&WGW&â€¢$'F–f7B"–â6&E÷G—W0¢÷"$Væ6†çFÖVçB"–â6&E÷G—W0¢÷"‚$7&VGW&R"–â6&E÷G—W2æBF&vWBç÷vW"ãÒB¢ ¢FVböÆVvÅö÷F–öæÅöFW7G&÷•÷F&vWB‡6VÆbÂF&vWC¢W&ÖæVçBÂ6öçG&öÆÆW#¢–çB’Óâ&ööÃ ¢–bæ÷B6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"“ ¢&WGW&âfÇ6P¢6&E÷G—W2Ò6WB‡F&vWBçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚’¢VÆ–v–&ÆRÒ€¢$'F–f7B"–â6&E÷G—W0¢÷"$Væ6†çFÖVçB"–â6&E÷G—W0¢÷"‡F&vWBæ—5ö7&VGW&RæB6VÆbåö†5ö¶W—v÷&B‡F&vWBÂ$fÇ––ær"’¢¢–bæ÷BVÆ–v–&ÆS ¢&WGW&âfÇ6P¢&WGW&â6VÆbåöÆVvÅ÷F&vWF–æu÷&÷FV7F–öâ‡F&vWBÂ6öçG&öÆÆW" ¢FVböÆVvÅö6öæF—F–öæÅöFW7G&÷•÷F&vWB‡6VÆbÂF&vWC¢W&ÖæVçBÂ6öçG&öÆÆW#¢–çB’Óâ&ööÃ ¢–bæ÷B6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"“ ¢&WGW&âfÇ6P¢G—W2Ò6WB‡F&vWBçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚’¢–bæ÷BG—W2æ–çFW'6V7F–öâ‡²$'F–f7B"Â$7&VGW&R'Ò“ ¢&WGW&âfÇ6P¢&WGW&â6VÆbåöÆVvÅ÷F&vWF–æu÷&÷FV7F–öâ‡F&vWBÂ6öçG&öÆÆW" ¢FVböÆVvÅ÷F&vWFVE÷&VÖ÷fÅ÷F&vWB‡6VÆbÂF&vWBÂ6öçG&öÆÆW#¢–çBÂ&öw&Ò’Óâ&ööÃ ¢–bæ÷B—6–ç7Fæ6R‡F&vWBÂW&ÖæVçB’÷"æ÷B6VÆbæ—5öWF†÷&—FF—fR‡F&vWBÂ&&GFÆVf–VÆB"“ ¢&WGW&âfÇ6P¢G—W2Ò6WB‡F&vWBçG—UöÆ–æRç7Æ—B‚"(	B"Â•³Òç7Æ—B‚’¢&WGW&â€¢&ööÂ‡G—W2æ–çFW'6V7F–öâ‡&öw&ÒçF&vWE÷G—W2’¢æB€¢&öw&ÒæÖ†–×VÕöÖæ÷fÇVR—2æöæP¢÷"F&vWBæ6&BæÖæ÷fÇVRÃÒ&öw&ÒæÖ†–×VÕöÖæ÷fÇVP¢¢æB6VÆbåöÆVvÅ÷F&vWF–æu÷&÷FV7F–öâ‡F&vWBÂ6öçG&öÆÆW"¢ ¢FVböÆVvÅ÷F&vWF–æu÷&÷FV7F–öâ‡6VÆbÂF&vWC¢W&ÖæVçBÂ6öçG&öÆÆW#¢–çB’Óâ&ööÃ ¢FW‡BÒ""æ¦ö–â‚‚§F&vWBç'VÆW5ö6&Bæ¶W—v÷&G2ÂF&vWBç'VÆW5ö6&Bæ÷&6ÆU÷FW‡B’¢–b&Rç6V&6‚‡"%Æ'6‡&÷VEÆ'ÅÆ'v&EÆ'ÅÆ'&÷FV7F–öåÆ'Æ6âwB&Rƒó§F†R“÷F&vWB"ÂFW‡BÂ&Rä’“ ¢&WGW&âfÇ6P¢&WGW&âæ÷B€¢F&vWBæ6öçG&öÆÆW"Ò6öçG&öÆÆW ¢æB‡6VÆbåö†5ö¶W—v÷&B‡F&vWBÂ$†W‡&ööb"’÷"&Rç6V&6‚‡"%Æ&†W‡&ööeÆ""ÂFW‡BÂ&Rä’’¢ ¢FVbÆVvÅöGF6¶W'2‡6VÆbÂÆ–W%ö–æFWƒ¢–çB’ÓâÆ—7EµW&ÖæVçEÓ ¢&WGW&â°¢ ¢f÷"–â6VÆbçÆ–W'5·Æ–W%ö–æFW…Òæ&GFÆVf–VÆ@¢–bæ—5ö7&VGW&P¢æBæ÷BçFV@¢æB€¢æ÷Bç7VÖÖöæ–æu÷6–6°¢÷"6VÆbåö†5ö¶W—v÷&B‡Â$†7FR"¢÷"6VÆbæ†5÷FV×÷&'•ö¶W—v÷&B‡ÂFV×÷&'”¶W—v÷&Bä„5DR¢¢æB6VÆbæGF6¶–æu÷&W7G&–7F–öâ‡’—2æöæP¢Ð ¢FVbGF6¶–æu÷&W7G&–7F–öâ‡6VÆbÂGF6¶W#¢W&ÖæVçB’ÓâGWÆU·7G"Â7G%ÒÂæöæS ¢""%&WGW&âF†Rf—'7B÷&6ÆRÖFW&—fVB&W7G&–7F–öâF†BÖ¶W2âGF6²–ÆÆVvÂâ"" ¢–bGF6¶W"æW&öGF6µ÷&W7G&–7F–öç3 ¢&WGW&âGF6¶W"æW&öGF6µ÷&W7G&–7F–öç5³Õ³ÒÂ&W&ö6çEöGF6² ¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2†GF6¶W"ç'VÆW5ö6&B“ ¢–bæ÷B6VÆbæ–çFW'&WFW"ä4åEôED4µõTäÄU55ôäõD„U%ô%D”d5BægVÆÆÖF6‚†g&vÖVçB“ ¢6öçF–çVP¢†5ö÷F†W%ö'F–f7BÒç’€¢W&ÖæVçB—2æ÷BGF6¶W ¢æBW&ÖæVçBæ6öçG&öÆÆW"ÓÒGF6¶W"æ6öçG&öÆÆW ¢æB6VÆbæ—5öWF†÷&—FF—fR‡W&ÖæVçBÂ&&GFÆVf–VÆB"¢æB$'F–f7B"–âW&ÖæVçBæ6&BçG—UöÆ–æP¢f÷"W&ÖæVçB–â6VÆbçÆ–W'5¶GF6¶W"æ6öçG&öÆÆW%Òæ&GFÆVf–VÆ@¢¢–bæ÷B†5ö÷F†W%ö'F–f7C ¢&WGW&âg&vÖVçBÂ&GF6µ÷&WV—&W5öæ÷F†W%ö6öçG&öÆÆVEö'F–f7B ¢&WGW&âæöæP ¢FVb†5÷FV×÷&'•ö¶W—v÷&B‡6VÆbÂW&ÖæVçC¢W&ÖæVçBÂ¶W—v÷&C¢FV×÷&'”¶W—v÷&B’Óâ&ööÃ ¢""%&VB7W'&VçB&÷VæFVBFV×÷&'’¶W—v÷&Bg&öÒWF†÷&—FF—fR–æ6&æF–öâ7FFRâ"" ¢&WGW&â6VÆbæ—5öWF†÷&—FF—fR‡W&ÖæVçBÂ&&GFÆVf–VÆB"’æBç’€¢VffV7Bæ¶W—v÷&B—2¶W—v÷&Bf÷"VffV7B–âW&ÖæVçBæ7F—fU÷FV×÷&'•ö¶W—v÷&EöVffV7G0¢ ¢FVb&Æö6¶–æu÷&W7G&–7F–öâ€¢6VÆbÂGF6¶W#¢W&ÖæVçBÂ&Æö6¶W#¢W&ÖæVç@¢’ÓâGWÆU·7G"Â7G%ÒÂæöæS ¢""%&WGW&âF†Rf—'7B÷&6ÆRÖFW&—fVB&W7G&–7F–öâF†BÖ¶W2F†—2&Æö6²–ÆÆVvÂâ"" ¢–b6VÆbåö†5öfÇ––ær†GF6¶W"’æBæ÷B€¢6VÆbåö†5öfÇ––ær†&Æö6¶W"’÷"6VÆbåö†5÷&V6‚†&Æö6¶W"¢“ ¢&WGW&â$fÇ––ær"Â&fÇ––æu÷&WV—&W5öfÇ––æuö÷%÷&V6‚ ¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2†GF6¶W"ç'VÆW5ö6&B“ ¢–b6VÆbæ–çFW'&WFW"ä4åEô$Uô$Äô4´TEôeDU%ô%D”d5EôTåE%’ægVÆÆÖF6‚†g&vÖVçB’æBç’€¢—6–ç7Fæ6R†VçFW&VBÂW&ÖæVçB¢æBVçFW&VBæVçFW&VEö&GFÆVf–VÆE÷GW&âÓÒ6VÆbçGW&à¢æBVçFW&VBæVçFW&VE÷VæFW%ö6öçG&öÆÆW"ÓÒGF6¶W"æ6öçG&öÆÆW ¢æB$'F–f7B"–âVçFW&VBæ6&BçG—UöÆ–æP¢f÷"VçFW&VB–â6VÆbåöö&¦V7G2çfÇVW2‚¢“ ¢&WGW&âg&vÖVçBÂ&'F–f7EöVçFW&VE÷VæFW%öGF6¶W%ö6öçG&öÆÆW%÷F†—5÷GW&â ¢ÖF6‚Ò6VÆbæ–çFW'&WFW"ä4åEô$Uô$Äô4´TEô%•õõtU%ôõ%ôu$TDU"ægVÆÆÖF6‚†g&vÖVçB¢–bÖF6‚æB&Æö6¶W"ç÷vW"ãÒ–çB†ÖF6‚æw&÷Wƒ’“ ¢&WGW&âg&vÖVçBÂ&&Æö6¶W%÷÷vW%öEö÷%ö&÷fU÷&W7G&–7F–öâ ¢–b€¢6VÆbæ–çFW'&WFW"ä4åEô$Uô$Äô4´TEô%•ôu$TDU%õõtU"ægVÆÆÖF6‚†g&vÖVçB¢æB&Æö6¶W"ç÷vW"âGF6¶W"ç÷vW ¢“ ¢&WGW&âg&vÖVçBÂ&&Æö6¶W%÷÷vW%öw&VFW%÷F†åöGF6¶W" ¢&WGW&âæöæP ¢FVböWV—ÖVçEö¶W—v÷&G2‡6VÆbÂW&ÖæVçC¢W&ÖæVçB’Óâg&÷¦Vç6WE·7G%Ó ¢–bæ÷B6VÆbæ—5öWF†÷&—FF—fR‡W&ÖæVçBÂ&&GFÆVf–VÆB"“ ¢&WGW&âg&÷¦Vç6WB‚¢&WGW&âg&÷¦Vç6WB€¢6VÖçF–75³%Ð¢f÷"Æ–W"–â6VÆbçÆ–W'0¢f÷"6÷W&6R–âÆ–W"æ&GFÆVf–VÆ@¢–b6÷W&6RæGF6†VE÷FòÓÒW&ÖæVçBæö&¦V7Eö–@¢æB6VÆbæ—5öWF†÷&—FF—fR‡6÷W&6RÂ&&GFÆVf–VÆB"¢æB$WV—ÖVçB"–â6÷W&6RçG—UöÆ–æP¢æB€¢W&ÖæVçBæ&–Æ—G•öÆ÷75÷F–ÖW7F×—2æöæP¢÷"6÷W&6RæGF6†ÖVçE÷F–ÖW7F×âW&ÖæVçBæ&–Æ—G•öÆ÷75÷F–ÖW7F× ¢¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡6÷W&6Rç'VÆW5ö6&B¢–b‡6VÖçF–72£Ò6VÆbæ–çFW'&WFW"æWV—ÖVçE÷7FF–5÷6VÖçF–72‡6÷W&6Ræ6&BÂg&vÖVçB’¢—2æ÷BæöæP¢æB6VÖçF–75³%Ò—2æ÷BæöæP¢ ¢FVbö†5ö¶W—v÷&B‡6VÆbÂW&ÖæVçC¢W&ÖæVçBÂ¶W—v÷&C¢7G"’Óâ&ööÃ ¢6Æ75ö¶W—v÷&G2Ò€¢6VÖçF–75³%Ð¢f÷"6÷W&6R–â6VÆbçÆ–W'5·W&ÖæVçBæ6öçG&öÆÆW%Òæ&GFÆVf–VÆ@¢–bW&ÖæVçBæ—5ö7&VGW&P¢æB6÷W&6Ræ6Æ75öÆWfVÂ—2æ÷BæöæP¢æB6÷W&6Ræ6Æ75öÆWfVÂãÒ ¢æB6VÆbæ—5öWF†÷&—FF—fR‡6÷W&6RÂ&&GFÆVf–VÆB"¢æB€¢W&ÖæVçBæ&–Æ—G•öÆ÷75÷F–ÖW7F×—2æöæP¢÷"6÷W&6Ræ6Æ75öÆWfVÅ÷F–ÖW7F×âW&ÖæVçBæ&–Æ—G•öÆ÷75÷F–ÖW7F× ¢¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡6÷W&6Rç'VÆW5ö6&B¢–b6VÆbæ–çFW'&WFW"æ6Æ75öÆWfVÅö6†–ÆB‡6÷W&6Ræ6&BÂ"’ÓÒg&vÖVç@¢–b‡6VÖçF–72£Ò6VÆbæ–çFW'&WFW"æ6Æ75ö7&VGW&UöçF†VÒ‡6÷W&6Ræ6&BÂg&vÖVçB’¢—2æ÷BæöæP¢¢&WGW&â¶W—v÷&Bæ66VföÆB‚’–â°¢¢‡fÇVRæ66VföÆB‚’f÷"fÇVR–âW&ÖæVçBç'VÆW5ö6&Bæ¶W—v÷&G2’À¢§6VÆbåöWV—ÖVçEö¶W—v÷&G2‡W&ÖæVçB’À¢¢†VffV7Bæ¶W—v÷&BçfÇVRf÷"VffV7B–âW&ÖæVçBæ7F—fU÷FV×÷&'•ö¶W—v÷&EöVffV7G2’À¢¦6Æ75ö¶W—v÷&G2À¢¢€¢¶W—v÷&Bæ66VföÆB‚¢f÷"÷6÷W&6Uö–BÂög&vÖVçB–â6VÆbå÷7FF–5÷7V'G—Uö¶W—v÷&E÷6÷W&6W2€¢W&ÖæVçBÂ¶W—v÷&@¢¢’À¢Ð ¢FVb÷7FF–5÷7V'G—Uö¶W—v÷&E÷6÷W&6W2€¢6VÆbÂW&ÖæVçC¢W&ÖæVçBÂ¶W—v÷&C¢7G ¢’ÓâGWÆU·GWÆU·7G"Â7G%ÒÂââåÓ ¢""$WfÇVFR6öçG&öÆÆVB7V'G—Rw&çG2–âÆ–W"6—‚v–ç7B7W'&VçB7FFRâ"" ¢–bæ÷B6VÆbæ—5öWF†÷&—FF—fR‡W&ÖæVçBÂ&&GFÆVf–VÆB"’÷"æ÷BW&ÖæVçBæ—5ö7&VGW&S ¢&WGW&â‚¢7V'G—W2Ò6WB‡W&ÖæVçBçG—UöÆ–æRç'F—F–öâ‚"(	B"•³%Òç7Æ—B‚’¢6÷W&6W3¢Æ—7E·GWÆU·7G"Â7G%ÕÒÒµÐ¢f÷"6÷W&6R–â6VÆbçÆ–W'5·W&ÖæVçBæ6öçG&öÆÆW%Òæ&GFÆVf–VÆC ¢–bæ÷B6VÆbæ—5öWF†÷&—FF—fR‡6÷W&6RÂ&&GFÆVf–VÆB"“ ¢6öçF–çVP¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡6÷W&6Rç'VÆW5ö6&B“ ¢&öw&ÒÒ6VÆbæ–çFW'&WFW"ç7FF–5÷7V'G—Uö¶W—v÷&Eöw&çB‡6÷W&6Ræ6&BÂg&vÖVçB¢–b€¢&öw&Ò—2æ÷BæöæP¢æB&öw&Òæ¶W—v÷&BÓÒ¶W—v÷&Bæ66VföÆB‚¢æB&öw&Òæ7&VGW&U÷7V'G—R–â7V'G—W0¢æB€¢W&ÖæVçBæ&–Æ—G•öÆ÷75÷F–ÖW7F×—2æöæP¢÷"6÷W&6RæVçFW&VE÷F–ÖW7F×âW&ÖæVçBæ&–Æ—G•öÆ÷75÷F–ÖW7F× ¢¢“ ¢6÷W&6W2æVæB‚‡6÷W&6Ræö&¦V7Eö–BÂg&vÖVçB’¢&WGW&âGWÆR‡6÷W&6W2 ¢FVbö†5öfÇ––ær‡6VÆbÂW&ÖæVçC¢W&ÖæVçB’Óâ&ööÃ ¢&WGW&â6VÆbåö†5ö¶W—v÷&B‡W&ÖæVçBÂ$fÇ––ær"’÷"ç’€¢VffV7Bæ¶W—v÷&B—2FV×÷&'”¶W—v÷&BädÅ””äp¢f÷"VffV7B–âW&ÖæVçBæ7F—fU÷FV×÷&'•ö¶W—v÷&EöVffV7G0¢ ¢FVbö†5÷&V6‚‡6VÆbÂW&ÖæVçC¢W&ÖæVçB’Óâ&ööÃ ¢&WGW&â6VÆbåö†5ö¶W—v÷&B‡W&ÖæVçBÂ%&V6‚"’÷"ç’€¢VffV7Bæ¶W—v÷&B—2FV×÷&'”¶W—v÷&Bå$T4€¢f÷"VffV7B–âW&ÖæVçBæ7F—fU÷FV×÷&'•ö¶W—v÷&EöVffV7G0¢ ¢FVbö†5öÖVæ6R‡6VÆbÂGF6¶W#¢W&ÖæVçB’Óâ&ööÃ ¢&WGW&â6VÆbåö†5ö¶W—v÷&B†GF6¶W"Â$ÖVæ6R"’÷"ç’€¢g&vÖVçBæ66VföÆB‚’ç7F'G7v—F‚‚&ÖVæ6R"¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2†GF6¶W"ç'VÆW5ö6&B¢ ¢FVb÷6–ævÆUö&Æö6µöÆ–Ö—E÷6÷W&6W2‡6VÆbÂGF6¶W#¢W&ÖæVçB’ÓâGWÆU·GWÆU·7G"Â7G%ÒÂââåÓ ¢""$WfÇVFR7W'&VçB6VÆbæB6öçG&öÆÆVB×7V'G—R7FF–2&W7G&–7F–öç2â"" ¢–bæ÷B6VÆbæ—5öWF†÷&—FF—fR†GF6¶W"Â&&GFÆVf–VÆB"’÷"æ÷BGF6¶W"æ—5ö7&VGW&S ¢&WGW&â‚¢7V'G—RÒ6WB†GF6¶W"çG—UöÆ–æRç'F—F–öâ‚"(	B"•³%Òç7Æ—B‚’¢6÷W&6W2ÒµÐ¢f÷"6÷W&6R–â6VÆbçÆ–W'5¶GF6¶W"æ6öçG&öÆÆW%Òæ&GFÆVf–VÆC ¢–bæ÷B6VÆbæ—5öWF†÷&—FF—fR‡6÷W&6RÂ&&GFÆVf–VÆB"“ ¢6öçF–çVP¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡6÷W&6Rç'VÆW5ö6&B“ ¢ffV7FVBÒ6VÆbæ–çFW'&WFW"ç6–ævÆUö&Æö6µöÆ–Ö—B‡6÷W&6Ræ6&BÂg&vÖVçB¢–b€¢†ffV7FVBÓÒ'6VÆb"æB6÷W&6R—2GF6¶W"¢÷"€¢ffV7FVBÓÒ&6öçG&öÆÆVE÷v—F…ö6÷VçFW" ¢æBç’†6÷VçBâf÷"6÷VçB–âGF6¶W"æ6÷VçFW'2çfÇVW2‚’¢¢÷"€¢ffV7FVB—2æ÷BæöæP¢æBffV7FVBæ÷B–â²'6VÆb"Â&6öçG&öÆÆVE÷v—F…ö6÷VçFW"'Ð¢æBffV7FVB–â7V'G—P¢¢“ ¢6÷W&6W2æVæB‚‡6÷W&6Ræö&¦V7Eö–BÂg&vÖVçB’¢&WGW&âGWÆR‡6÷W&6W2 ¢FVb÷fÆ–Eö&Æö6µö76–væÖVçB€¢6VÆbÀ¢GF6¶W'3¢Æ—7EµW&ÖæVçEÒÀ¢76–væÖVçC¢GWÆU·GWÆU·7G"Â7G%ÒÂââåÒÀ¢FVfVæFW%ö–æFWƒ¢–çBÀ¢’Óâ&ööÃ ¢'•öGF6¶W#¢F–7E·7G"ÂÆ—7E·7G%ÕÒÒ·Ð¢f÷"GF6¶W%ö–BÂ&Æö6¶W%ö–B–â76–væÖVçC ¢'•öGF6¶W"ç6WFFVfVÇB†GF6¶W%ö–BÂµÒ’æVæB†&Æö6¶W%ö–B¢–bÆVâ‡¶&Æö6¶W%ö–Bf÷"òÂ&Æö6¶W%ö–B–â76–væÖVçGÒ’ÒÆVâ†76–væÖVçB“ ¢&WGW&âfÇ6P¢GF6¶W%öÖÒ¶GF6¶W"æö&¦V7Eö–C¢GF6¶W"f÷"GF6¶W"–âGF6¶W'7Ð¢–b6WB†'•öGF6¶W"’Ò6WB†GF6¶W%öÖ“ ¢&WGW&âfÇ6P¢f÷"GF6¶W"–âGF6¶W'3 ¢&Æö6¶W%ö–G2Ò'•öGF6¶W"ævWB†GF6¶W"æö&¦V7Eö–BÂµÒ¢–b6VÆbåö†5öÖVæ6R†GF6¶W"’æB&Æö6¶W%ö–G2æBÆVâ†&Æö6¶W%ö–G2’Â# ¢&WGW&âfÇ6P¢–bÆVâ†&Æö6¶W%ö–G2’âæB6VÆbå÷6–ævÆUö&Æö6µöÆ–Ö—E÷6÷W&6W2†GF6¶W"“ ¢&WGW&âfÇ6P¢f÷"&Æö6¶W%ö–B–â&Æö6¶W%ö–G3 ¢&Æö6¶W"Ò6VÆbåöö&¦V7G2ævWB†&Æö6¶W%ö–B¢–bæ÷B—6–ç7Fæ6R†&Æö6¶W"ÂW&ÖæVçB’÷"æ÷B6VÆbæ6åö&Æö6²€¢GF6¶W"Â&Æö6¶W"ÂFVfVæFW%ö–æFW€¢“ ¢&WGW&âfÇ6P¢&WGW&âG'VP ¢FVb÷v—FæW75÷Vç7W÷'FVEö&Æö6µö6öçFW‡B‡6VÆbÂGF6¶W#¢W&ÖæVçBÂ&Æö6¶W#¢W&ÖæVçB’ÓâæöæS ¢""%&V6÷&BÖVæ6R÷÷'GVæ—G’öæÇ’f÷"âWF†÷&—FF—fR&Æö6¶W"6æF–FFRâ"" ¢–bæ÷B€¢6VÆbç7FW—2GW&å7FWäDT4Ä$Uô$Äô4´U%0¢æB6VÆbæ—5öWF†÷&—FF—fR†GF6¶W"Â&&GFÆVf–VÆB"¢æB6VÆbæ—5öWF†÷&—FF—fR†&Æö6¶W"Â&&GFÆVf–VÆB"¢æBGF6¶W"æö&¦V7Eö–B–â6VÆbåö6öÖ&EöGF6¶W'0¢“ ¢&WGW&à¢f÷"ö67W'&Væ6R–â6VÆbç6VÖçF–5öö67W'&Væ6W3 ¢–bö67W'&Væ6Ræö&¦V7Eö–BÓÒGF6¶W"æö&¦V7Eö–BæBö67W'&Væ6Ræ÷&6ÆUög&vÖVçBç7F'G7v—F‚€¢$ÖVæ6R ¢“ ¢6VÆbå÷&V6÷&Eö÷÷'GVæ—G’€¢ö67W'&Væ6RÀ¢6W6Uö¶–æCÒ&ÆVvÅö&Æö6µö6öçFW‡B"À¢6W6Uö–CÒ€¢b&&Æö6³§·6VÆbçGW&çÓ§·6VÆbç7FWçfÇVWÓ¢ ¢b'¶GF6¶W"æö&¦V7Eö–GÓ§¶&Æö6¶W"æö&¦V7Eö–GÒ ¢’À¢6W6U÷7V&¦V7Eö–G3Ò†GF6¶W"æö&¦V7Eö–BÂ&Æö6¶W"æö&¦V7Eö–B’À¢ ¢FVb6åö&Æö6²‡6VÆbÂGF6¶W#¢W&ÖæVçBÂ&Æö6¶W#¢W&ÖæVçBÂFVfVæFW%ö–æFWƒ¢–çB’Óâ&ööÃ ¢&WGW&â€¢&Æö6¶W"æ6öçG&öÆÆW"ÓÒFVfVæFW%ö–æFW€¢æBç’†6æF–FFR—2&Æö6¶W"f÷"6æF–FFR–â6VÆbçÆ–W'5¶FVfVæFW%ö–æFW…Òæ&GFÆVf–VÆB¢æB&Æö6¶W"æ—5ö7&VGW&P¢æBæ÷B&Æö6¶W"çFV@¢æB6VÆbæ&Æö6¶–æu÷&W7G&–7F–öâ†GF6¶W"Â&Æö6¶W"’—2æöæP¢ ¢FVbvVæW&FUö&Æö6·2€¢6VÆbÀ¢GF6¶W'3¢Æ—7EµW&ÖæVçEÒÀ¢FVfVæFW%ö–æFWƒ¢–çBÀ¢¢À¢Æöu÷&V¦V7F–öç3¢&ööÂÒG'VRÀ¢’ÓâF–7E·7G"ÂW&ÖæVçEÓ ¢""$vVæW&FRFWFW&Ö–æ—7F–2öæR×FòÖöæR&Æö6·2W6–ærF†R6ÖRÆVvÆ—G’2fÆ–FF–öââ"" ¢f–Æ&ÆRÒ°¢W&ÖæVç@¢f÷"W&ÖæVçB–â6VÆbçÆ–W'5¶FVfVæFW%ö–æFW…Òæ&GFÆVf–VÆ@¢–bW&ÖæVçBæ—5ö7&VGW&RæBæ÷BW&ÖæVçBçFV@¢Ð¢&Æö6·3¢F–7E·7G"ÂW&ÖæVçEÒÒ·Ð¢f÷"GF6¶W"–âGF6¶W'3 ¢f÷"&Æö6¶W"–âf–Æ&ÆS ¢6VÆbå÷v—FæW75÷Vç7W÷'FVEö&Æö6µö6öçFW‡B†GF6¶W"Â&Æö6¶W"¢&W7G&–7F–öâÒ6VÆbæ&Æö6¶–æu÷&W7G&–7F–öâ†GF6¶W"Â&Æö6¶W"¢–b&W7G&–7F–öâ—2æ÷BæöæS ¢g&vÖVçBÂ&V6öâÒ&W7G&–7F–öà¢–bÆöu÷&V¦V7F–öç3 ¢6VÆbæÆör€¢&&Æö6µö6æF–FFU÷&V¦V7FVB"À¢GF6¶W#ÖGF6¶W"æ6&BææÖRÀ¢&Æö6¶W#Ö&Æö6¶W"æ6&BææÖRÀ¢÷&6ÆUög&vÖVçCÖg&vÖVçBÀ¢&V6öã×&V6öâÀ¢GF6¶W%÷÷vW#ÖGF6¶W"ç÷vW"À¢&Æö6¶W%÷÷vW#Ö&Æö6¶W"ç÷vW"À¢¢6öçF–çVP¢&Æö6·5¶GF6¶W"æö&¦V7Eö–EÒÒ&Æö6¶W ¢f–Æ&ÆRç&VÖ÷fR†&Æö6¶W"¢'&V°¢&WGW&â&Æö6·0 ¢FVb6öÖ&B€¢6VÆbÀ¢GF6¶W'3¢Æ—7EµW&ÖæVçEÒÀ¢&Æö6·3¢F–7E·7G"ÂW&ÖæVçEÒÂæöæRÒæöæRÀ¢¢À¢WFõö76–våö&Æö6¶W'3¢&ööÂÒfÇ6RÀ¢’ÓâæöæS ¢""$6ö×F–&–Æ—G’FFW"÷fW"F†RF‡&VRWF†÷&—FF—fR6öÖ&B7F–öç2â"" ¢–b6VÆbç7FW—2æ÷BGW&å7FWäDT4Ä$UôED4´U%3 ¢&—6RfÇVTW'&÷"‚&GF6¶W'26â&RFV6Æ&VBöæÇ’GW&–ærFV6Æ&RGF6¶W'2"¢GF6¶W%ö–G2ÒGWÆR†GF6¶W"æö&¦V7Eö–Bf÷"GF6¶W"–âGF6¶W'2¢GF6²ÒæW‡B€¢€¢÷F–öà¢f÷"÷F–öâ–â6VÆbæÆVvÅöGF6µö÷F–öç2‡6VÆbæ7F—fU÷Æ–W"¢–b÷F–öâæGF6¶W%ö–G2ÓÒGF6¶W%ö–G0¢æBÆÂ‡6VÆbåöö&¦V7G2ævWB†GF6¶W"æö&¦V7Eö–B’—2GF6¶W"f÷"GF6¶W"–âGF6¶W'2¢’À¢æöæRÀ¢¢–bGF6²—2æöæS ¢&—6RfÇVTW'&÷"‚&–ÆÆVvÂGF6¶W""¢FVfVæFW"ÒÒ6VÆbæ7F—fU÷Æ–W ¢–bæ÷BWFõö76–våö&Æö6¶W'3 ¢&Æö6·2Ò&Æö6·2÷"·Ð¢GF6¶W%ö–E÷6WBÒ6WB†GF6¶W%ö–G2¢–bç’†GF6¶W%ö–Bæ÷B–âGF6¶W%ö–E÷6WBf÷"GF6¶W%ö–B–â&Æö6·2“ ¢&—6RfÇVTW'&÷"‚&&Æö6²76–væVBFòæöæGF6¶W""¢–bÆVâ‡¶&Æö6¶W"æö&¦V7Eö–Bf÷"&Æö6¶W"–â&Æö6·2çfÇVW2‚—Ò’ÒÆVâ†&Æö6·2“ ¢&—6RfÇVTW'&÷"‚&–ÆÆVvÂ&Æö6¶W""¢–bç’€¢æ÷B6VÆbæ—5öWF†÷&—FF—fR†&Æö6¶W"Â&&GFÆVf–VÆB"¢÷"æ÷B6VÆbæ6åö&Æö6²€¢6VÆbåöö&¦V7G5¶GF6¶W%ö–EÒÀ¢&Æö6¶W"À¢FVfVæFW"Â2G—S¢–væ÷&U¶&r×G—UÐ¢¢f÷"GF6¶W%ö–BÂ&Æö6¶W"–â&Æö6·2æ—FV×2‚¢“ ¢&—6RfÇVTW'&÷"‚&–ÆÆVvÂ&Æö6¶W""¢6VÆbæW†V7WFUöGF6µö7F–öâ†GF6²¢–bWFõö76–våö&Æö6¶W'3 ¢–b&Æö6·2—2æ÷BæöæS ¢&—6RfÇVTW'&÷"‚&6ææ÷B&÷f–FR&Æö6·2v†VâWFòÖ76–væ–ær&Æö6¶W'2"¢&Æö6µö÷F–öç2Ò6VÆbæÆVvÅö&Æö6µö÷F–öç2†GF6²ÂFVfVæFW"¢Ö…ö&Æö6·2ÒÖ‚†ÆVâ†÷F–öâæ&Æö6·2’f÷"÷F–öâ–â&Æö6µö÷F–öç2¢&Æö6µö÷F–öâÒÖ‚€¢†÷F–öâf÷"÷F–öâ–â&Æö6µö÷F–öç2–bÆVâ†÷F–öâæ&Æö6·2’ÓÒÖ…ö&Æö6·2’À¢¶W“ÖÆÖ&F÷F–öã¢GWÆR€¢ÖGF6²æGF6¶W%ö–G2æ–æFW‚†GF6¶W%ö–B’f÷"GF6¶W%ö–BÂò–â÷F–öâæ&Æö6·0¢’À¢¢VÇ6S ¢76W'B&Æö6·2—2æ÷BæöæP¢&Æö6µö÷F–öâÒ7F–öä÷F–öâ€¢7F–öä¶–æBäDT4Ä$Uô$Äô4´U%2À¢FVfVæFW"À¢&Æö6·3×GWÆR€¢†GF6¶W%ö–BÂ&Æö6¶W"æö&¦V7Eö–B’f÷"GF6¶W%ö–BÂ&Æö6¶W"–â&Æö6·2æ—FV×2‚¢’À¢¢6VÆbæW†V7WFUö&Æö6µö7F–öâ†&Æö6µö÷F–öâ¢–b6VÆbç7FW—2GW&å7FWäDT4Ä$Uô$Äô4´U%3 ¢6VÆbæW†V7WFU÷6æVµö7F–öâ„7F–öä÷F–öâ„7F–öä¶–æBå52Â6VÆbæ7F—fU÷Æ–W"’¢v†–ÆR6VÆbç7FW—2GW&å7FWä4ôÔ$EôDÔtS ¢6VÆbç&W6öÇfUö6öÖ&EöFÖvR‚ ¢FVbVæE÷GW&â‡6VÆb’ÓâæöæS ¢""$6ö×F–&–Æ—G’†VÇW#¢föÆÆ÷rÆVvÂG&ç6—F–öç2F‡&÷Vv‚6ÆVçWâ"" ¢–b6VÆbç7FW–âµGW&å7FWå4UEUÂGW&å7FWä4ÄTåUÓ ¢&—6RfÇVTW'&÷"‚&VæE÷GW&â—2ÆVvÂöæÇ’GW&–ærâ7F—fRGW&â"¢v†–ÆR6VÆbç7FWæ÷B–âµGW&å7FWåõ5D4ôÔ$EôÔ”âÂGW&å7FWäTäEõ5DUÓ ¢–b6VÆbç7FW—2GW&å7FWä4ôÔ$EôDÔtS ¢6VÆbç&W6öÇfUö6öÖ&EöFÖvR‚¢VÇ6S ¢6VÆbæGfæ6U÷7FW‚¢–b6VÆbç7FW—2GW&å7FWåõ5D4ôÔ$EôÔ”ã ¢6VÆbæGfæ6U÷7FW‚¢6VÆbæGfæ6U÷Fò…GW&å7FWä4ÄTåU ¢FVbWE÷W&ÖæVçG5ö–çFõöw&fW–&B€¢6VÆbÀ¢W&ÖæVçG3¢GWÆUµW&ÖæVçBÂââåÒÀ¢¢À¢7FFUö&6VEö7F–öã¢7G"ÂæöæRÒæöæRÀ¢’ÓâGWÆU´6&Dö&¦V7BÂââåÓ ¢""$Ö÷fRöæR6–×VÇFæV÷W2&GFÆVf–VÆB&F6‚v—F‚6†&VBÆ7BÖ¶æ÷vâG&–vvW"6æ6†÷Bâ"" ¢–bÆVâ‡·W&ÖæVçBæö&¦V7Eö–Bf÷"W&ÖæVçB–âW&ÖæVçG7Ò’ÒÆVâ‡W&ÖæVçG2“ ¢&—6RfÇVTW'&÷"‚'6–×VÇFæV÷W2FW'GW&R&F6‚6öçF–ç2GWÆ–6FRö&¦V7G2"¢–bç’†æ÷B6VÆbæ—5öWF†÷&—FF—fR‡W&ÖæVçBÂ&&GFÆVf–VÆB"’f÷"W&ÖæVçB–âW&ÖæVçG2“ ¢&—6RfÇVTW'&÷"‚'6–×VÇFæV÷W2FW'GW&R&WV—&W2WF†÷&—FF—fRW&ÖæVçG2"¢WF†÷&—G’Ò6VÆbåö&GFÆVf–VÆEöWF†÷&—G•÷6æ6†÷B‚¢6÷W&6W2Ò6VÆbå÷W&ÖæVçEöÆVgE÷G&–vvW%÷6÷W&6W2‚¢2ÆÂFW'F–ærö&¦V7G2W6R&RÖWfVçB&–Æ—F–W2Â–æ6ÇVF–ær7W&W76VBF–W2ôÅD"FW‡Bà¢FVfW'&VBÒvWFGG"‡6VÆbÂ%ö6öçF–çV÷W5÷&Vg&W6…öFVfW'&VB"ÂfÇ6R¢6VÆbåö6öçF–çV÷W5÷&Vg&W6…öFVfW'&VBÒG'VP¢G'“ ¢&WGW&âGWÆR€¢6VÆbçWEö–çFõöw&fW–&B€¢W&ÖæVçBÀ¢7FFUö&6VEö7F–öã×7FFUö&6VEö7F–öâÀ¢öFW'GW&UöWF†÷&—G“ÖWF†÷&—G’À¢öFW'GW&U÷6÷W&6W3×6÷W&6W2À¢¢f÷"W&ÖæVçB–âW&ÖæVçG0¢¢f–æÆÇ“ ¢6VÆbåö6öçF–çV÷W5÷&Vg&W6…öFVfW'&VBÒFVfW'&V@¢6VÆbç&Vg&W6…÷7FF–5÷EöÖöF–f–W'2‚ ¢FVbWEö–çFõöw&fW–&B€¢6VÆbÀ¢W&ÖæVçC¢W&ÖæVçBÀ¢¢À¢7FFUö&6VEö7F–öã¢7G"ÂæöæRÒæöæRÀ¢öFW'GW&UöWF†÷&—G“¢GWÆU·GWÆU·7G"Â–çEÒÂââåÒÂæöæRÒæöæRÀ¢öFW'GW&U÷6÷W&6W3¢GWÆU·GWÆUµW&ÖæVçBÂ7G%ÒÂââåÒÂæöæRÒæöæRÀ¢’Óâ6&Dö&¦V7C ¢–bæ÷B6VÆbæ—5öWF†÷&—FF—fR‡W&ÖæVçBÂ&&GFÆVf–VÆB"“ ¢&—6RfÇVTW'&÷"‚'W&ÖæVçB—2æ÷BöâF†R&GFÆVf–VÆB"¢÷væW"Ò6VÆbçÆ–W'5·W&ÖæVçBæ÷væW%Ð¢6öçG&öÆÆW"ÒW&ÖæVçBæ6öçG&öÆÆW ¢&GFÆVf–VÆEöWF†÷&—G’Ò€¢6VÆbåö&GFÆVf–VÆEöWF†÷&—G•÷6æ6†÷B‚¢–böFW'GW&UöWF†÷&—G’—2æöæP¢VÇ6RöFW'GW&UöWF†÷&—G¢¢&ÖV6–ög&vÖVçBÒ6VÆbå÷&ÖV6–ög&vÖVçB‡W&ÖæVçBç'VÆW5ö6&B¢F–W5öG&uög&vÖVçG2ÒGWÆR€¢g&vÖVç@¢f÷"g&vÖVçB–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡W&ÖæVçBç'VÆW5ö6&B¢–b†6÷fW&vR£Ò6VÆbæ–çFW'&WFW"æF–W5öG&u÷6VÖçF–5ö6÷fW&vR‡W&ÖæVçBæ6&BÂg&vÖVçB’¢—2æ÷BæöæP¢æB6÷fW&vRægVÆÇ•÷7W÷'FV@¢¢Æ7Eö¶æ÷vå÷G—UöÆ–æRÒW&ÖæVçBçG—UöÆ–æP¢Æ7Eö¶æ÷våö—5ö7&VGW&RÒW&ÖæVçBæ—5ö7&VGW&P¢6VÆbæÆÆ–æ6UöÖöFW5ö6†÷6Vâç÷‡W&ÖæVçBæö&¦V7Eö–BÂæöæR¢f–æÆ—G’ÒW&ÖæVçBæ6÷VçFW'2ævWB‚&f–æÆ—G’"Â’â ¢FW7F–æF–öâÒ&W†–ÆR"–bf–æÆ—G’VÇ6R&w&fW–&B ¢&WÆ6VÖVçBÒ6VÆbæÖ÷fUöö&¦V7B€¢W&ÖæVçBÀ¢FW7F–æF–öâÀ¢&V6öãÒ‚&f–æÆ—G•öW†–ÆR"–bf–æÆ—G’VÇ6R‡7FFUö&6VEö7F–öâ÷"'WEö–çFõöw&fW–&B"’’À¢öFW'GW&UöWF†÷&—G“Ö&GFÆVf–VÆEöWF†÷&—G’À¢öFW'GW&U÷6÷W&6W3ÕöFW'GW&U÷6÷W&6W2À¢¢76W'B—6–ç7Fæ6R‡&WÆ6VÖVçBÂ6&Dö&¦V7B¢6VÆbç&Vg&W6…÷7FF–5÷EöÖöF–f–W'2‚¢6VÆbæÆör€¢'W&ÖæVçE÷FõöW†–ÆR"–bf–æÆ—G’VÇ6R'W&ÖæVçE÷Fõöw&fW–&B"À¢Æ–W#Ö÷væW"ææÖRÀ¢6&C×W&ÖæVçBæ6&BææÖRÀ¢7FFUö&6VEö7F–öã×7FFUö&6VEö7F–öâÀ¢¢–b†F–W5öG&uög&vÖVçG2÷"&ÖV6–ög&vÖVçB’æBÆ7Eö¶æ÷våö—5ö7&VGW&RæBæ÷Bf–æÆ—G“ ¢WfVçBÒ6VÆbåöæWu÷'VÆW5öWfVçB€¢'VÆW4WfVçD¶–æBä5$TEU$UôD”TBÀ¢6öçG&öÆÆW"À¢‡W&ÖæVçBæö&¦V7Eö–BÂ’À¢6÷W&6Uö–C×W&ÖæVçBæö&¦V7Eö–BÀ¢&GFÆVf–VÆEöWF†÷&—G“Ö&GFÆVf–VÆEöWF†÷&—G’À¢Æ7Eö¶æ÷våö&GFÆVf–VÆCÒ€¢€¢W&ÖæVçBæö&¦V7Eö–BÀ¢6öçG&öÆÆW"À¢Æ7Eö¶æ÷vå÷G—UöÆ–æRÀ¢Æ7Eö¶æ÷våö—5ö7&VGW&RÀ¢’À¢’À¢¢–b&ÖV6–ög&vÖVçC ¢6VÆbå÷&ÖV6–öFW'GW&W5·W&ÖæVçBæö&¦V7Eö–EÒÒ€¢W&ÖæVçBÀ¢&WÆ6VÖVçBÀ¢WfVçBÀ¢&ÖV6–ög&vÖVçBÀ¢¢6VÆbåöVçVWVU÷G&–vvW"€¢WfVçBÂW&ÖæVçBÂ&ÖV6–ög&vÖVçBÂG&–vvW$VffV7Bå$ÔT4”ôU„”ÄUô4„ô”4P¢¢f÷"g&vÖVçB–âF–W5öG&uög&vÖVçG3 ¢6VÆbåöVçVWVU÷G&–vvW"†WfVçBÂW&ÖæVçBÂg&vÖVçBÂG&–vvW$VffV7BäD”U5ôE$r¢&WGW&â&WÆ6VÖVç@ ¢FVbFW7G&÷’‡6VÆbÂW&ÖæVçC¢W&ÖæVçBÂ¢Â7FFUö&6VEö7F–öã¢7G"ÂæöæRÒæöæR’ÓâæöæS ¢–b6VÆbåö†5ö¶W—v÷&B‡W&ÖæVçBÂ$–æFW7G'V7F–&ÆR"“ ¢6VÆbæÆör€¢&FW7G'V7F–öå÷&WfVçFVB"ÂF&vWEö–C×W&ÖæVçBæö&¦V7Eö–BÂ&V6öãÒ&–æFW7G'V7F–&ÆR ¢¢&WGW&à¢6VÆbçWEö–çFõöw&fW–&B‡W&ÖæVçBÂ7FFUö&6VEö7F–öã×7FFUö&6VEö7F–öâ ¢FVb6†V6µ÷7FFUö&6VEö7F–öç2‡6VÆb’ÓâæöæS ¢6VÆbç&Vg&W6…÷7FF–5÷EöÖöF–f–W'2‚¢v†–ÆRG'VS ¢6†ævVBÒ6VÆbæW&÷7FFUö&6VEö7F–öç2‚¢f÷"7F–öâ–â6VÆbç7FFUö&6VEö7F–öç3 ¢–b7F–öâæÇ’‡6VÆb“ ¢6†ævVBÒG'VP¢6VÆbç&Vg&W6…÷7FF–5÷EöÖöF–f–W'2‚¢–bæ÷B6†ævVC ¢'&V°¢6VÆbæ6†V6µöÆ–fR‚¢–bæ÷B6VÆbæ—5÷FW&Ö–æÂæB6VÆbå÷WE÷VæF–æu÷G&–vvW'5ööå÷7F6²€¢°¢G&–vvW$VffV7BäD”U5ôE$rÀ¢G&–vvW$VffV7Bäu$åDTEôD”U5õ$UEU$âÀ¢G&–vvW$VffV7BåU$ÔäTåEôÄTeEõ4TÄeô4õTåDU"À¢G&–vvW$VffV7Bä4ôåE$ôÄÄTEô5$TEU$UôÄTeEôõôäTåEôÄõ52À¢G&–vvW$VffV7Bä4ôåE$ôÄÄTEô4õTåDU$TEô5$TEU$UôÄTeEôÄ”dRÀ¢G&–vvW$VffV7Bä4ôåE$ôÄÄTEô%D”d5Eô4õTåDU%õE$å4dU"À¢G&–vvW$VffV7BäDÔtUõDõõ4TÄeôÔäÀ¢G&–vvW$VffV7BäÅD%ôÕUDtTâÀ¢G&–vvW$VffV7Bå$ÔT4”ôU„”ÄUô4„ô”4RÀ¢G&–vvW$VffV7BåUD”Ä•E•õD$tUBÀ¢Ð¢“ ¢6VÆbåöG&–å÷G&–vvW&VEö&–Æ—F–W2‚¢6VÆbæ6†V6µö–çf&–çG2‚ ¢FVb6†V6µö–çf&–çG2‡6VÆb’ÓâæöæS ¢&WF–æVEö÷&–v–ç2Ò°¢WfVçBævWB‚'7F6µöö&¦V7Eö–B"“¢WfVç@¢f÷"WfVçB–â6VÆbæWfVçG0¢–bWfVçE²&WfVçB%ÒÓÒ&FÖvU÷Fõ÷6VÆeöÖæ÷&W6öÇfVB ¢Ð¢f÷"Æ–W%ö–æFW‚–â&ævR†ÆVâ‡6VÆbçÆ–W'2’“ ¢&öGV7F–öç2Ò6VÆbæfÆöF–æuöÖæç&öGV7F–öç2‡Æ–W%ö–æFW‚¢6öç7V×F–öç2Ò6VÆbæfÆöF–æuöÖææ6öç7V×F–öç2‡Æ–W%ö–æFW‚¢–bÆVâ‡·Væ—BæWfVçEö–Bf÷"Væ—B–â&öGV7F–öç7Ò’ÒÆVâ‡&öGV7F–öç2“ ¢&—6R76W'F–öäW'&÷"‚&fÆöF–ærÖæ&öGV7F–öâ”G2&Ræ÷BVæ—VR"¢W6VEö'•ö–C¢F–7E·7G"Â–çEÒÒ·Ð¢f÷"—FVÒ–â6öç7V×F–öç3 ¢W6VEö'•ö–E¶—FVÒç6÷W&6UöWfVçEö–EÒÒ€¢W6VEö'•ö–BævWB†—FVÒç6÷W&6UöWfVçEö–BÂ’²—FVÒçVçF—G¢¢–b6WB‡W6VEö'•ö–B’Ò·Væ—BæWfVçEö–Bf÷"Væ—B–â&öGV7F–öç7Ó ¢&—6R76W'F–öäW'&÷"‚&fÆöF–ærÖæ6öç7V×F–öâÆ6·2&öGV7F–öâ"¢&Ææ6S¢F–7E·7G"Â–çEÒÒ·Ð¢f÷"Væ—B–â&öGV7F–öç3 ¢W6VBÒW6VEö'•ö–BævWB‡Væ—BæWfVçEö–BÂ¢–bW6VBâVæ—BçVçF—G’÷"W6VBÂ ¢&—6R76W'F–öäW'&÷"‚&fÆöF–ærÖæ6öç7V×F–öâW†6VVG2&öGV7F–öâ"¢–bVæ—BçVçF—G’âW6VC ¢&Ææ6U·Væ—Bæ6öÆ÷%ÒÒ&Ææ6RævWB‡Væ—Bæ6öÆ÷"Â’²Væ—BçVçF—G’ÒW6V@¢–bVæ—BçW'6—7G5÷VçF–Å÷GW&åöVæC ¢÷&–v–âÒ&WF–æVEö÷&–v–ç2ævWB‡Væ—BæWfVçEö–B¢–b€¢÷&–v–â—2æöæP¢÷"÷&–v–âævWB‚'6÷W&6Uö–B"’ÒVæ—Bç6÷W&6Uö–@¢÷"÷&–v–âævWB‚&6öçG&öÆÆW""’ÒÆ–W%ö–æFW€¢÷"÷&–v–âævWB‚'VçF—G’"’ÒVæ—BçVçF—G¢÷"÷&–v–âævWB‚&6öÆ÷""’ÒVæ—Bæ6öÆ÷ ¢“ ¢&—6R76W'F–öäW'&÷"‚'&WF–æVBÖæÆ6·26÷W&6RG&–vvW"&÷fVææ6R"¢–b6VÆbæfÆöF–æuöÖæç6æ6†÷B‡Æ–W%ö–æFW‚’ÒF–7B‡6÷'FVB†&Ææ6Ræ—FV×2‚’’“ ¢&—6R76W'F–öäW'&÷"‚&fÆöF–ærÖæööÂF–ffW'2g&öÒ–æF—f–GVÂVæ—G2"¢FW'GW&W2Ò°¢†–æFW‚Â—FVÒ¢f÷"–æFW‚Â—FVÒ–âVçVÖW&FR‡6VÆbæWfVçG2¢–b—FVÕ²&WfVçB%ÒÓÒ'W&ÖæVçEöFW'FVB ¢Ð¢f÷"–æFW‚Â—FVÒ–âFW'GW&W3 ¢6÷W&6RÒ6VÆbåöö&¦V7G2ævWB†—FVÕ²'6÷W&6Uöö&¦V7Eö–B%Ò¢&V6VF–ærÒ6VÆbæWfVçG5¶–æFW‚ÒÒ–b–æFW‚VÇ6R·Ð¢–b€¢æ÷B—6–ç7Fæ6R‡6÷W&6RÂW&ÖæVçB¢÷"6÷W&6Rç¦öæRÒ&f÷&ÖW" ¢÷"6÷W&6Ræ6öçG&öÆÆW"Ò—FVÕ²&6öçG&öÆÆW"%Ð¢÷"6÷W&6RçG—UöÆ–æRÒ—FVÕ²'G—UöÆ–æR%Ð¢÷"&V6VF–ærævWB‚&WfVçB"’Ò'¦öæUö6†ævVB ¢÷"&V6VF–ærævWB‚'6÷W&6Uöö&¦V7Eö–B"’Ò—FVÕ²'6÷W&6Uöö&¦V7Eö–B%Ð¢÷"&V6VF–ærævWB‚&FW7F–æF–öåöö&¦V7Eö–B"’Ò—FVÕ²&FW7F–æF–öåöö&¦V7Eö–B%Ð¢÷"&V6VF–ærævWB‚'6÷W&6U÷¦öæR"’Ò&&GFÆVf–VÆB ¢÷"&V6VF–ærævWB‚&FW7F–æF–öå÷¦öæR"’ÓÒ&&GFÆVf–VÆB ¢÷"&V6VF–ærævWB‚'GW&â"’Ò—FVÕ²'GW&â%Ð¢“ ¢&—6R76W'F–öäW'&÷"‚&FW'GW&R†—7F÷'’Æ6·2¦öæRæB6öçG&öÆÆW"&÷fVææ6R"¢Æ–æ¶VEöw&çG2Ò¶w&çBf÷"w&çG2–â6VÆbåöÆ–æ¶VE÷Æ•öw&çG2çfÇVW2‚’f÷"w&çB–âw&çG5Ð¢–bÆVâ‡¶w&çBæw&çEö–Bf÷"w&çB–âÆ–æ¶VEöw&çG7Ò’ÒÆVâ†Æ–æ¶VEöw&çG2’÷"ç’€¢w&çBç6÷W&6Uö–BÒ6÷W&6Uö–@¢÷"6÷W&6Uö–Bæ÷B–â6VÆbåöö&¦V7G0¢÷"w&çBæ6öçG&öÆÆW"æ÷B–â&ævRƒ"¢÷"w&çBæW‡—&W5÷GW&ââ6VÆbçGW&à¢÷"w&çBç&VÖ–æ–æu÷Æ—2æ÷B–â³ÂÐ¢f÷"6÷W&6Uö–BÂw&çG2–â6VÆbåöÆ–æ¶VE÷Æ•öw&çG2æ—FV×2‚¢f÷"w&çB–âw&çG0¢“ ¢&—6R76W'F–öäW'&÷"‚&Æ–æ¶VBÆ’w&çB&÷fVææ6R÷"6öç7V×F–öâ—2ÖÆf÷&ÖVB"¢G'“ ¢6VÆbå÷fÆ–FFU÷7GVåö†—7F÷'’‚¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢6öÖ&Eö–G2Ò6VÆbåö6öÖ&EöGF6¶W'2²GWÆR€¢&Æö6¶W%ö–Bf÷"öGF6¶W%ö–BÂ&Æö6¶W%ö–B–â6VÆbåö6öÖ&Eö&Æö6·0¢¢Wf–FVæ6Uö–G2Ò¶—FVÒæWfVçEö–Bf÷"—FVÒ–â6VÆbå÷'VÆW5öWfVçEöWf–FVæ6UÐ¢–b€¢ÆVâ†Wf–FVæ6Uö–G2’ÒÆVâ‡6WB†Wf–FVæ6Uö–G2’¢÷"6WB†Wf–FVæ6Uö–G2’Ò6WB‡6VÆbå÷'VÆW5öWfVçG2¢÷"¶—FVÒæWfVçEö7W'6÷"f÷"—FVÒ–â6VÆbå÷'VÆW5öWfVçEöWf–FVæ6UÐ¢ÒÆ—7B‡&ævRƒÂÆVâ‡6VÆbå÷'VÆW5öWfVçEöWf–FVæ6R’²’¢“ ¢&—6R76W'F–öäW'&÷"‚''VÆW2ÖWfVçBWf–FVæ6RÆVFvW"—2–æ6ö×ÆWFR÷"GWÆ–6FVB"¢f÷"WfVçB–â6VÆbå÷'VÆW5öWfVçG2çfÇVW2‚“ ¢G'“ ¢6VÆbåöWF†VçF–6FUö÷&–v–æÅ÷'VÆW5öWfVçB†WfVçB¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢ö67W'&Væ6Uö'•ö–BÒ¶—FVÒæö67W'&Væ6Uö–C¢—FVÒf÷"—FVÒ–â6VÆbç6VÖçF–5öö67W'&Væ6W7Ð¢–bÆVâ†ö67W'&Væ6Uö'•ö–B’ÒÆVâ‡6VÆbç6VÖçF–5öö67W'&Væ6W2“ ¢&—6R76W'F–öäW'&÷"‚'6VÖçF–2ö67W'&Væ6R”G2×W7B&RVæ—VR"¢–bÆVâ‡¶—FVÒæ÷÷'GVæ—G•ö¶W’f÷"—FVÒ–â6VÆbæ÷÷'GVæ—G•÷v—FæW76W7Ò’ÒÆVâ€¢6VÆbæ÷÷'GVæ—G•÷v—FæW76W0¢“ ¢&—6R76W'F–öäW'&÷"‚&÷÷'GVæ—G’v—FæW76W2×W7B&RFWFW&Ö–æ—7F–6ÆÇ’FVGWÆ–6FVB"¢6öçFW‡Eö'•ö–BÒ¶—FVÒæ6öçFW‡Eö–C¢—FVÒf÷"—FVÒ–â6VÆbæ÷÷'GVæ—G•ö6öçFW‡G7Ð¢–bÆVâ†6öçFW‡Eö'•ö–B’ÒÆVâ‡6VÆbæ÷÷'GVæ—G•ö6öçFW‡G2“ ¢&—6R76W'F–öäW'&÷"‚&÷÷'GVæ—G’6öçFW‡B”G2×W7B&RVæ—VR"¢f÷"6öçFW‡B–â6VÆbæ÷÷'GVæ—G•ö6öçFW‡G3 ¢–b€¢6öçFW‡Bç6÷W&6Uö–Bæ÷B–â6VÆbåöö&¦V7G0¢÷"ç’‡7V&¦V7Eö–Bæ÷B–â6VÆbåöö&¦V7G2f÷"7V&¦V7Eö–B–â6öçFW‡Bç7V&¦V7Eö–G2¢÷"ÆVâ†6öçFW‡Bç7V&¦V7Eö–G2’ÒÆVâ†6öçFW‡Bç7V&¦V7E÷¦öæW2¢÷"6öçFW‡Bæ6öçG&öÆÆW"æ÷B–â&ævRƒ"¢÷"æ÷B&RægVÆÆÖF6‚‡"%³Ó–Öe×³cGÒ"Â6öçFW‡Bç7FFUöf–ævW'&–çB¢÷"6öçFW‡Bæ6öçFW‡Eö¶W¢Ò÷÷'GVæ—G•ö6öçFW‡Eö¶W’€¢6öçFW‡Bæ6öçFW‡Eö–BÀ¢6öçFW‡Bæ6öçFW‡Eö¶–æBÀ¢6öçFW‡BçGW&âÀ¢6öçFW‡Bç†6RÀ¢6öçFW‡Bç7FWÀ¢6öçFW‡Bæ7F—fU÷Æ–W"À¢6öçFW‡Bæ6öçG&öÆÆW"À¢6öçFW‡Bç6÷W&6Uö–BÀ¢6öçFW‡Bç7V&¦V7Eö–G2À¢6öçFW‡Bç7V&¦V7E÷¦öæW2À¢6öçFW‡Bæf7G2À¢6öçFW‡BæWfVçEö–BÀ¢6öçFW‡Bç7F6µöö&¦V7Eö–BÀ¢6öçFW‡Bç7FFUöf–ævW'&–çBÀ¢¢“ ¢&—6R76W'F–öäW'&÷"‚&÷÷'GVæ—G’6öçFW‡B&÷fVææ6R—2ÖÆf÷&ÖVB"¢–b6öçFW‡BæWfVçEö–B—2æ÷BæöæRæB6öçFW‡BæWfVçEö–Bæ÷B–â6VÆbå÷'VÆW5öWfVçG3 ¢&—6R76W'F–öäW'&÷"‚&÷÷'GVæ—G’6öçFW‡BWfVçB&÷fVææ6R—2Ö—76–ær"¢–b6öçFW‡Bç7F6µöö&¦V7Eö–B—2æ÷BæöæRæB6öçFW‡Bç7F6µöö&¦V7Eö–Bæ÷B–â6VÆbåöö&¦V7G3 ¢&—6R76W'F–öäW'&÷"‚&÷÷'GVæ—G’6öçFW‡B7F6²&÷fVææ6R—2Ö—76–ær"¢f÷"ö67W'&Væ6R–â6VÆbç6VÖçF–5öö67W'&Væ6W3 ¢6÷W&6RÒ6VÆbåöö&¦V7G2ævWB†ö67W'&Væ6Ræö&¦V7Eö–B¢–bæ÷B—6–ç7Fæ6R‡6÷W&6RÂ„6&Dö&¦V7BÂW&ÖæVçB’“ ¢&—6R76W'F–öäW'&÷"‚'6VÖçF–2ö67W'&Væ6R&VfW&Væ6W2æöæW†—7FVçBö&¦V7B"¢g&vÖVçG2Ò6VÆbå÷6VÖçF–5ög&vÖVçG2‡6÷W&6Ræ6&B¢–b€¢ö67W'&Væ6Ræg&vÖVçEö–æFW‚ãÒÆVâ†g&vÖVçG2¢÷"g&vÖVçG5¶ö67W'&Væ6Ræg&vÖVçEö–æFW…ÒÒö67W'&Væ6Ræ÷&6ÆUög&vÖVç@¢÷"g&vÖVçEöF–vW7B†ö67W'&Væ6Ræ÷&6ÆUög&vÖVçB’Òö67W'&Væ6Ræg&vÖVçEö†6€¢÷"6VÖçF–5ö¶W’€¢vWFGG"‡6÷W&6Ræ6&BÂ&÷&6ÆUö–B"Â""’À¢ö67W'&Væ6Ræf6Uö–æFW‚À¢ö67W'&Væ6Ræg&vÖVçEö–æFW‚À¢ö67W'&Væ6Ræ÷&6ÆUög&vÖVçBÀ¢¢Òö67W'&Væ6Rç6VÖçF–5ö¶W¢“ ¢&—6R76W'F–öäW'&÷"‚'6VÖçF–2ö67W'&Væ6RÖ—6ÖF6†W2WF†÷&—FF—fR÷&6ÆRFF"¢f÷"v—FæW72–â6VÆbæ÷÷'GVæ—G•÷v—FæW76W3 ¢ö67W'&Væ6RÒö67W'&Væ6Uö'•ö–BævWB‡v—FæW72æö67W'&Væ6Uö–B¢–bö67W'&Væ6R—2æöæR÷"€¢v—FæW72ç6VÖçF–5ö¶W’Òö67W'&Væ6Rç6VÖçF–5ö¶W¢÷"v—FæW72æö&¦V7Eö–BÒö67W'&Væ6Ræö&¦V7Eö–@¢÷"v—FæW72æ÷&6ÆUög&vÖVçBÒö67W'&Væ6Ræ÷&6ÆUög&vÖVç@¢“ ¢&—6R76W'F–öäW'&÷"‚&÷÷'GVæ—G’v—FæW72Ö—6ÖF6†W26VÖçF–2&W6Væ6R"¢G'“ ¢f7G2Ò6VÆbå÷fÆ–FFUö÷÷'GVæ—G•öÆ–6&–Æ—G’€¢ö67W'&Væ6RÀ¢6W6Uö¶–æC×v—FæW72æ6W6Uö¶–æBÀ¢6W6Uö–C×v—FæW72æ6W6Uö–BÀ¢6W6U÷7V&¦V7Eö–G3×v—FæW72æ6W6U÷7V&¦V7Eö–G2À¢†—7F÷&–6Ã×v—FæW72À¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bf7G2Ò€¢v—FæW72ç6÷W&6U÷¦öæRÀ¢v—FæW72ç6÷W&6Uö6öçG&öÆÆW"À¢v—FæW72æ6W6U÷7V&¦V7E÷¦öæW2À¢v—FæW72æ6W6UöWfVçEö¶–æBÀ¢“ ¢&—6R76W'F–öäW'&÷"‚&÷÷'GVæ—G’v—FæW72Æ–6&–Æ—G’f7G2&R–æ6öç6—7FVçB"¢–b€¢v—FæW72æ6W6Uö¶–æBÓÒ&WF†÷&—FF—fUö6öçFW‡B ¢æBv—FæW72æ6W6Uö–Bæ÷B–â6öçFW‡Eö'•ö–@¢“ ¢&—6R76W'F–öäW'&÷"‚&÷÷'GVæ—G’v—FæW726öçFW‡B&÷fVææ6R—2Ö—76–ær"¢–bÆVâ‡6WB‡6VÆbåö6öÖ&EöGF6¶W'2’’ÒÆVâ‡6VÆbåö6öÖ&EöGF6¶W'2“ ¢&—6R76W'F–öäW'&÷"‚&6öÖ&B7FFR6öçF–ç2GWÆ–6FRGF6¶W'2"¢–bÆVâ‡¶&Æö6¶W%ö–Bf÷"öGF6¶W%ö–BÂ&Æö6¶W%ö–B–â6VÆbåö6öÖ&Eö&Æö6·7Ò’ÒÆVâ€¢6VÆbåö6öÖ&Eö&Æö6·0¢“ ¢&—6R76W'F–öäW'&÷"‚&6öÖ&B7FFR6öçF–ç2GWÆ–6FR&Æö6¶W'2"¢–bç’†ö&¦V7Eö–Bæ÷B–â6öÖ&Eö–G2f÷"ö&¦V7Eö–B–â6VÆbåöf—'7EöFÖvU÷VÆ–f–VEö–G2“ ¢&—6R76W'F–öäW'&÷"‚&f—'7B×7G&–¶RVÆ–f–6F–öâ&VfW&Væ6W2æöæ6öÖ&FçB"¢–bç’†ö&¦V7Eö–Bæ÷B–â6öÖ&Eö–G2f÷"ö&¦V7Eö–B–â6VÆbå÷&VwVÆ%öFÖvUö–æ—F–Åö–G2“ ¢&—6R76W'F–öäW'&÷"‚'&VwVÆ"×7FWVÆ–f–6F–öâ&VfW&Væ6W2æöæ6öÖ&FçB"¢–bç’€¢ÆVâ€¢°¢†76–væÖVçBç6÷W&6Uö–BÂ76–væÖVçBçF&vWEö–BÂ76–væÖVçBçF&vWE÷Æ–W"¢f÷"76–væÖVçB–âWf–FVæ6Ræ76–væÖVçG0¢Ð¢¢ÒÆVâ†Wf–FVæ6Ræ76–væÖVçG2¢f÷"Wf–FVæ6R–â6VÆbæ6öÖ&EöFÖvUöWf–FVæ6P¢“ ¢&—6R76W'F–öäW'&÷"‚&6öÖ&FçB&WVFVBöæR76–væÖVçB–âFÖvR7FW"¢–bç’€¢76–væÖVçBæÖ÷VçBÃÒ ¢f÷"Wf–FVæ6R–â6VÆbæ6öÖ&EöFÖvUöWf–FVæ6P¢f÷"76–væÖVçB–âWf–FVæ6Ræ76–væÖVçG0¢“ ¢&—6R76W'F–öäW'&÷"‚&6öÖ&BWf–FVæ6R6öçF–ç2æöç÷6—F—fRFÖvR76–væÖVçB"¢f÷"Wf–FVæ6R–â6VÆbæ6öÖ&EöFÖvUöWf–FVæ6S ¢f÷"&W7VÇB–âWf–FVæ6RçG&×ÆU÷&W7VÇG3 ¢–b&W7VÇBæFÖvU÷7FW—2æ÷BWf–FVæ6Ræ¶–æB÷"&W7VÇBæGF6¶W%÷÷vW"ÃÒ ¢&—6R76W'F–öäW'&÷"‚%G&×ÆRWf–FVæ6R†2–çfÆ–B7FW÷"÷vW""¢–b€¢&W7VÇBæ&Æö6¶W%öFÖvUö76–væVB²&W7VÇBçÆ–W%öFÖvUö76–væV@¢Ò&W7VÇBæGF6¶W%÷÷vW ¢“ ¢&—6R76W'F–öäW'&÷"‚%G&×ÆRWf–FVæ6RFöW2æ÷B6öç6W'fR76–væVBFÖvR"¢–b€¢&W7VÇBæFVfVæF–æuöÆ–fUö&Vf÷&RÒ&W7VÇBçÆ–W%öFÖvUö76–væV@¢Ò&W7VÇBæFVfVæF–æuöÆ–fUögFW ¢“ ¢&—6R76W'F–öäW'&÷"‚%G&×ÆRWf–FVæ6RÆ–fR&W7VÇB—2–æ6öç6—7FVçB"¢–b&W7VÇBæ&Æö6¶W%÷F÷Vv†æW72—2æ÷BæöæRæB€¢&W7VÇBæ&Æö6¶W%öÖ&¶VEöFÖvUö&Vf÷&R—2æöæP¢÷"&W7VÇBæÆWF†Å÷&WV—&V@¢ÒÖ–â€¢Ö‚ƒÂ&W7VÇBæ&Æö6¶W%÷F÷Vv†æW72Ò&W7VÇBæ&Æö6¶W%öÖ&¶VEöFÖvUö&Vf÷&R’À¢–b&W7VÇBç6÷W&6UöFVF‡F÷V6‚VÇ6R&W7VÇBæ&Æö6¶W%÷F÷Vv†æW72À¢¢“ ¢&—6R76W'F–öäW'&÷"‚%G&×ÆRWf–FVæ6RÆWF†Â6Æ7VÆF–öâ—2–æ6öç6—7FVçB"¢–b&W7VÇBæ&Æö6¶W%÷7W'f—fVBÒ‡&W7VÇBæ&Æö6¶W%öÖ&¶VEöFÖvUögFW"—2æ÷BæöæR“ ¢&—6R76W'F–öäW'&÷"‚%G&×ÆRWf–FVæ6R&Æö6¶W"&W7VÇB—2–æ6öç6—7FVçB"¢–bç’€¢W&ÖæVçBæFVF‡F÷V6…öFÖvRæBW&ÖæVçBæFÖvRÃÒ ¢f÷"Æ–W"–â6VÆbçÆ–W'0¢f÷"W&ÖæVçB–âÆ–W"æ&GFÆVf–VÆ@¢“ ¢&—6R76W'F–öäW'&÷"‚$FVF‡F÷V6‚Ö&¶W"&WV—&W2÷6—F—fRFÖvR"¢–bÆVâ‡¶—FVÒç7F6µöö&¦V7Eö–Bf÷"—FVÒ–â6VÆbæWF%öG&–åöv–å÷67'•öWf–FVæ6WÒ’ÒÆVâ€¢6VÆbæWF%öG&–åöv–å÷67'•öWf–FVæ6P¢“ ¢&—6R76W'F–öäW'&÷"‚$UD"G&–âöv–âõ67'’Wf–FVæ6R7F6²”G2×W7B&RVæ—VR"¢f÷"—FVÒ–â6VÆbæWF%öG&–åöv–å÷67'•öWf–FVæ6S ¢&–Æ—G’Ò6VÆbåöö&¦V7G2ævWB†—FVÒç7F6µöö&¦V7Eö–B¢–bæ÷B—6–ç7Fæ6R†&–Æ—G’ÂG&–vvW&VD&–Æ—G”ö&¦V7B’÷"&–Æ—G’ç¦öæRÒ&f÷&ÖW"# ¢&—6R76W'F–öäW'&÷"‚$UD"G&–âöv–âõ67'’Wf–FVæ6RÆ6·2&W6öÇfVB7F6²WF†÷&—G’"¢G'“ ¢6VÆbå÷fÆ–FFUöWF%öG&–åöv–å÷67'•÷G&–vvW"†&–Æ—G’¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–b€¢—FVÒæWfVçEö–BÒ&–Æ—G’æWfVçBæWfVçEö–@¢÷"—FVÒç6÷W&6Uö–BÒ&–Æ—G’ç6÷W&6Uö–@¢÷"—FVÒç6÷W&6Uö6&BÒ&–Æ—G’ç6÷W&6Uö6&BææÖP¢÷"—FVÒæ6öçG&öÆÆW"Ò&–Æ—G’æ6öçG&öÆÆW ¢÷"—FVÒæ÷öæVçBÒÒ—FVÒæ6öçG&öÆÆW ¢÷"—FVÒæ÷&6ÆUög&vÖVçBÒ&–Æ—G’æ÷&6ÆUög&vÖVç@¢÷"—FVÒçGW&âÒ&–Æ—G’æWfVçBçGW&à¢÷"—FVÒç7FWÒ&–Æ—G’æWfVçBç7FW ¢÷"—FVÒæ÷öæVçEöÆ–fUögFW"Ò—FVÒæ÷öæVçEöÆ–fUö&Vf÷&RÒ¢“ ¢&—6R76W'F–öäW'&÷"‚$UD"G&–âöv–âõ67'’Wf–FVæ6R&÷fVææ6R—2–æ6öç6—7FVçB"¢–b—FVÒçFW&Ö–æÅögFW%öÆ–fUöÆ÷73 ¢–b€¢—FVÒæ÷öæVçEöÆ–fUögFW"â ¢÷"—FVÒæ6öçG&öÆÆW%öÆ–fUögFW"Ò—FVÒæ6öçG&öÆÆW%öÆ–fUö&Vf÷&P¢÷"—FVÒç67'•öWfVçEö–B—2æ÷BæöæP¢“ ¢&—6R76W'F–öäW'&÷"‚'FW&Ö–æÂUD"G&–âöv–âõ67'’Wf–FVæ6R—2–æ6öç6—7FVçB"¢VÇ6S ¢ÖF6†–æu÷67'’Ò°¢Wf–FVæ6P¢f÷"Wf–FVæ6R–â6VÆbç67'•öWf–FVæ6P¢–bWf–FVæ6RæWfVçEö–BÓÒ—FVÒç67'•öWfVçEö–@¢Ð¢–b€¢—FVÒæ÷öæVçEöÆ–fUögFW"ÃÒ ¢÷"—FVÒæ6öçG&öÆÆW%öÆ–fUögFW"Ò—FVÒæ6öçG&öÆÆW%öÆ–fUö&Vf÷&R²¢÷"ÆVâ†ÖF6†–æu÷67'’’Ò¢÷"ÖF6†–æu÷67'•³ÒçÆ–W%ö–æFW‚Ò—FVÒæ6öçG&öÆÆW ¢÷"ÖF6†–æu÷67'•³Òç&WVW7FVBÒ¢÷"ÖF6†–æu÷67'•³Òç6÷W&6Uö–BÒ—FVÒç6÷W&6Uö–@¢÷"ÖF6†–æu÷67'•³Òæ÷&6ÆUög&vÖVçBÒ—FVÒæ÷&6ÆUög&vÖVç@¢“ ¢&—6R76W'F–öäW'&÷"‚&6ö×ÆWFVBUD"G&–âöv–âõ67'’Wf–FVæ6R—2–æ6öç6—7FVçB"¢–bÆVâ‡¶—FVÒç7F6µöö&¦V7Eö–Bf÷"—FVÒ–â6VÆbæ7F—fF–öåöWf–FVæ6WÒ’ÒÆVâ€¢6VÆbæ7F—fF–öåöWf–FVæ6P¢“ ¢&—6R76W'F–öäW'&÷"‚&7F—fF–öâWf–FVæ6R7F6²”G2×W7B&RVæ—VR"¢f÷"—FVÒ–â6VÆbæ7F—fF–öåöWf–FVæ6S ¢–b—FVÒæ6öçG&öÆÆW"æ÷B–â&ævRƒ"’÷"—FVÒç6÷W&6Uö–Bæ÷B–â6VÆbåöö&¦V7G3 ¢&—6R76W'F–öäW'&÷"‚&7F—fF–öâWf–FVæ6R&VfW&Væ6W2–çfÆ–BWF†÷&—G’"¢&–Æ—G’Ò6VÆbåöö&¦V7G2ævWB†—FVÒç7F6µöö&¦V7Eö–B¢–bæ÷B—6–ç7Fæ6R†&–Æ—G’Â7F—fFVD&–Æ—G”ö&¦V7B“ ¢&—6R76W'F–öäW'&÷"‚&7F—fF–öâWf–FVæ6RÆ6·2—G2'VçF–ÖR7F6²ö&¦V7B"¢–b—FVÒç&W6öÇfVBÒ†&–Æ—G’ç¦öæRÓÒ&f÷&ÖW""“ ¢&—6R76W'F–öäW'&÷"‚&7F—fF–öâ&W6öÇWF–öâWf–FVæ6RF—6w&VW2v—F‚7F6²7FFR"¢–bÆVâ‡¶—FVÒç7F6µöö&¦V7Eö–Bf÷"—FVÒ–â6VÆbæfööEö7F—fF–öåöWf–FVæ6WÒ’ÒÆVâ€¢6VÆbæfööEö7F—fF–öåöWf–FVæ6P¢“ ¢&—6R76W'F–öäW'&÷"‚$fööB7F—fF–öâWf–FVæ6R7F6²”G2×W7B&RVæ—VR"¢f÷"—FVÒ–â6VÆbæfööEö7F—fF–öåöWf–FVæ6S ¢&–Æ—G’Ò6VÆbåöö&¦V7G2ævWB†—FVÒç7F6µöö&¦V7Eö–B¢67&–f–6VBÒ6VÆbåöö&¦V7G2ævWB†—FVÒç67&–f–6VEöFW7F–æF–öåö–B¢–bæ÷B—6–ç7Fæ6R†&–Æ—G’Â7F—fFVD&–Æ—G”ö&¦V7B“ ¢&—6R76W'F–öäW'&÷"‚$fööB7F—fF–öâWf–FVæ6RÆ6·2—G27F6²ö&¦V7B"¢6VÆbå÷fÆ–FFUöfööEö7F—fF–öåöÆ–æ¶vR†&–Æ—G’¢–b—FVÒç6÷W&6Uö–Bæ÷B–â6VÆbåöö&¦V7G2÷"æ÷B—6–ç7Fæ6R‡67&–f–6VBÂ6&Dö&¦V7B“ ¢&—6R76W'F–öäW'&÷"‚$fööB7F—fF–öâWf–FVæ6RÆ6·2–Ö×WF&ÆR6÷7B–FVçF—F–W2"¢–bæ÷B—FVÒçF÷–B÷"æ÷B—FVÒç67&–f–6U÷–C ¢&—6R76W'F–öäW'&÷"‚$fööB7F—fF–öâWf–FVæ6RÆ6·26ö×ÆWFR6æöæ–6Â6÷7G2"¢–b—FVÒç6÷W&6U÷v5÷Fö¶VâæB—FVÒæf–æÅ÷6÷W&6UöF—7÷6—F–öâÒ&f÷&ÖW"# ¢&—6R76W'F–öäW'&÷"‚'67&–f–6VBfööBFö¶Vâ×W7B6V6RBF†R4$&÷VæF'’"¢–b—FVÒç&W6öÇfVBÒ†&–Æ—G’ç¦öæRÓÒ&f÷&ÖW""“ ¢&—6R76W'F–öäW'&÷"‚$fööB7F—fF–öâ&W6öÇWF–öâWf–FVæ6RF—6w&VW2v—F‚7F6²"¢–b—FVÒç&W6öÇfVBæB€¢—FVÒæÆ–fUö&Vf÷&R—2æöæP¢÷"—FVÒæÆ–fUögFW"—2æöæP¢÷"—FVÒæÖ÷VçEöv–æVBÒ0¢÷"—FVÒæÆ–fUögFW"Ò—FVÒæÆ–fUö&Vf÷&RÒ0¢÷"—FVÒç&–÷&—G•÷76W2Ò†—FVÒæ6öçG&öÆÆW"ÂÒ—FVÒæ6öçG&öÆÆW"¢÷"æ÷B—FVÒç&W6öÇWF–öå÷W&Ö—GFV@¢“ ¢&—6R76W'F–öäW'&÷"‚$fööB7F—fF–öâÆ–fRWf–FVæ6R—2–æ6öç6—7FVçB"¢–bÆVâ‡¶—FVÒç7F6µöö&¦V7Eö–Bf÷"—FVÒ–â6VÆbç6æVµöWf–FVæ6WÒ’ÒÆVâ‡6VÆbç6æVµöWf–FVæ6R“ ¢&—6R76W'F–öäW'&÷"‚%6æV²Wf–FVæ6R7F6²”G2×W7B&RVæ—VR"¢f÷"—FVÒ–â6VÆbç6æVµöWf–FVæ6S ¢7VÆÂÒ6VÆbåöö&¦V7G2ævWB†—FVÒç7F6µöö&¦V7Eö–B¢–bæ÷B—6–ç7Fæ6R‡7VÆÂÂ7F6´ö&¦V7B“ ¢&—6R76W'F–öäW'&÷"‚%6æV²Wf–FVæ6RÆ6·2—G2'VçF–ÖR7F6²ö&¦V7B"¢–b—FVÒç6÷W&6U÷¦öæRæ÷B–â²&†æB"Â&W†–ÆR"Â&w&fW–&B'Ó ¢&—6R76W'F–öäW'&÷"‚%6æV²Wf–FVæ6R†2â–çfÆ–B67B÷&–v–â"¢–b—FVÒç6÷W&6U÷¦öæRÓÒ&w&fW–&B# ¢–b€¢—FVÒçW&Ö—76–öå÷6÷W&6Uö–B—2æöæP¢÷"æ÷B—6–ç7Fæ6R‡6VÆbåöö&¦V7G2ævWB†—FVÒçW&Ö—76–öå÷6÷W&6Uö–B’ÂW&ÖæVçB¢÷"æ÷B7VÆÂæ67Eög&öÕöw&fW–&@¢“ ¢&—6R76W'F–öäW'&÷"‚&w&fW–&B6æV²Æ6·2Æ–æ¶VBW&Ö—76–öâ&÷fVææ6R"¢VÆ–b—FVÒçW&Ö—76–öå÷6÷W&6Uö–B—2æ÷BæöæS ¢&—6R76W'F–öäW'&÷"‚%6æV²Wf–FVæ6R†2VæW‡V7FVBW&Ö—76–öâ&÷fVææ6R"¢–b—FVÒæ6öçG&öÆÆW"æ÷B–â&ævRƒ"’÷"—FVÒæFVfVæF–æu÷Æ–W"ÒÒ—FVÒæ6öçG&öÆÆW# ¢&—6R76W'F–öäW'&÷"‚%6æV²Wf–FVæ6R†2–çfÆ–BÆ–W"WF†÷&—G’"¢–b€¢—FVÒæ†æEöö&¦V7Eö–Bæ÷B–â6VÆbåöö&¦V7G0¢÷"—FVÒç&WGW&æVEöGF6¶W%ö–Bæ÷B–â6VÆbåöö&¦V7G0¢“ ¢&—6R76W'F–öäW'&÷"‚%6æV²Wf–FVæ6RÆ6·2–Ö×WF&ÆR6÷W&6R–FVçF—F–W2"¢–b—FVÒç&WGW&æVEö†æEö–Bæ÷B–â6VÆbåöö&¦V7G3 ¢&—6R76W'F–öäW'&÷"‚%6æV²Wf–FVæ6RÆ6·2&WGW&æVBÖö&¦V7B–FVçF—G’"¢&W6öÇfVBÒ—FVÒç&W6öÇfVEöö&¦V7Eö–B—2æ÷BæöæP¢6÷VçFW&VBÒç’€¢WfVçBævWB‚&WfVçB"’ÓÒ'7VÆÅö6÷VçFW&VB ¢æBWfVçBævWB‚'F&vWE÷7VÆÅö–B"’ÓÒ7VÆÂæö&¦V7Eö–@¢f÷"WfVçB–â6VÆbæWfVçG0¢¢–b7VÆÂæ67Eö¶–æB—267D¶–æBä5$TEU$S ¢–b&W6öÇfVBæB7VÆÂç¦öæRÒ&f÷&ÖW"# ¢&—6R76W'F–öäW'&÷"‚%6æV²Wf–FVæ6R&W6öÇWF–öâF—6w&VW2v—F‚7F6²7FFR"¢–bæ÷B&W6öÇfVBæB7VÆÂç¦öæRÓÒ&f÷&ÖW""æBæ÷B6÷VçFW&VC ¢&—6R76W'F–öäW'&÷"‚%6æV²Wf–FVæ6R&W6öÇWF–öâF—6w&VW2v—F‚7F6²7FFR"¢–b&W6öÇfVBæB€¢—FVÒç&W6öÇfVEöö&¦V7Eö–Bæ÷B–â6VÆbåöö&¦V7G0¢÷"—FVÒæVçFW&VE÷FVB—2æ÷BG'VP¢÷"—FVÒæVçFW&VEöGF6¶–ær—2æ÷BG'VP¢“ ¢&—6R76W'F–öäW'&÷"‚'&W6öÇfVB6æV²Wf–FVæ6RÆ6·2&GFÆVf–VÆB&W7VÇB"¢VÆ–b&W6öÇfVC ¢&—6R76W'F–öäW'&÷"‚&æöæ7&VGW&R6æV²Wf–FVæ6R†2&GFÆVf–VÆB&W7VÇB"¢–b6VÆbç&–÷&—G•÷7FFR—2æ÷BæöæS ¢7FFRÒ6VÆbç&–÷&—G•÷7FFP¢–bæ÷B6VÆbç7F6²æBæ÷B€¢6VÆbç7FW—2GW&å7FWäDT4Ä$Uô$Äô4´U%2æB6VÆbåö&Æö6¶W'5öFV6Æ&V@¢“ ¢&—6R76W'F–öäW'&÷"‚'&–÷&—G’7FFR&WV—&W2æöæV×G’7F6²"¢–b7FFRçÆ–W%ö–æFW‚æ÷B–â&ævRƒ"“ ¢&—6R76W'F–öäW'&÷"‚'&–÷&—G’Æ–W"—2–çfÆ–B"¢–bÆVâ‡7FFRæ6öç6V7WF—fU÷76W2’â# ¢&—6R76W'F–öäW'&÷"‚'&–÷&—G’726WVVæ6R—2FöòÆöær"¢–b7FFRæ6öç6V7WF—fU÷76W2æ÷B–â²‚’ÂƒÂ’ÂƒÂ’ÂƒÂ’ÂƒÂ—Ó ¢&—6R76W'F–öäW'&÷"‚'&–÷&—G’76W2×W7BÇFW&æFR&WGvVVâÆ–W'2"¢–b7FFRç&W6öÇWF–öå÷VæF–ærÒ†ÆVâ‡7FFRæ6öç6V7WF—fU÷76W2’ÓÒ"“ ¢&—6R76W'F–öäW'&÷"‚'&–÷&—G’&W6öÇWF–öâW&Ö—76–öâF—6w&VW2v—F‚76W2"¢&—6R76W'F–öäW'&÷"‚&7F—fF–öâWf–FVæ6R&W6öÇWF–öâ7FFR—2–æ6öç6—7FVçB"¢–b6VÆbç7FW—2GW&å7FWä4ôÔ$EôDÔtRæB6VÆbåö6öÖ&EöFÖvU÷7FWö¶–æBæ÷B–â°¢6öÖ&DFÖvU7FW¶–æBäd•%5Eõ5E$”´RÀ¢6öÖ&DFÖvU7FW¶–æBå$TuTÄ"À¢Ó ¢&—6R76W'F–öäW'&÷"‚&6öÖ&BFÖvRGW&â7FWÆ6·2â7F—fRFÖvR×7FW¶–æB"¢–b6VÆbç7FW–â°¢GW&å7FWåõ5D4ôÔ$EôÔ”âÀ¢GW&å7FWäTäEõ5DUÀ¢GW&å7FWä4ÄTåUÀ¢GW&å7FWåTåDÀ¢GW&å7FWåU´TUÀ¢GW&å7FWäE$rÀ¢GW&å7FWå$T4ôÔ$EôÔ”âÀ¢ÒæB€¢6öÖ&Eö–G0¢÷"6VÆbåöGF6¶W'5öFV6Æ&V@¢÷"6VÆbåö&Æö6¶W'5öFV6Æ&V@¢÷"6VÆbåö6öÖ&EöFÖvU÷&W6öÇfV@¢÷"6VÆbåö6öÖ&EöFÖvU÷7FWö¶–æB—2æ÷B6öÖ&DFÖvU7FW¶–æBääôäP¢÷"6VÆbåö6öÖ&EöFÖvU÷7FWöçVÖ&W ¢÷"6VÆbåö6öÖ&EöFÖvU÷F÷FÅ÷7FW0¢÷"6VÆbåöf—'7EöFÖvU÷VÆ–f–VEö–G0¢÷"6VÆbåöf—'7EöF÷V&ÆU÷7G&–¶Uö–G0¢÷"6VÆbå÷&VwVÆ%öFÖvUö–æ—F–Åö–G0¢“ ¢&—6R76W'F–öäW'&÷"‚&6ö×ÆWFVB6öÖ&B7FFRÆV¶VB÷WG6–FRF†R6öÖ&B†6R"¢–b·&V6÷&Bç6WVVæ6Rf÷"&V6÷&B–â6VÆbç&ærç&V6÷&G5ÒÒÆ—7B€¢&ævRƒÂÆVâ‡6VÆbç&ærç&V6÷&G2’²¢“ ¢&—6R76W'F–öäW'&÷"‚%$är6öç7V×F–öâ6WVVæ6R—2æ÷B6öçF–wV÷W2"¢–bç’€¢&Wf–÷W2ç7FFUögFW"Ò7W'&VçBç7FFUö&Vf÷&P¢f÷"&Wf–÷W2Â7W'&VçB–â¦—‡6VÆbç&ærç&V6÷&G2Â6VÆbç&ærç&V6÷&G5³¥ÒÂ7G&–7CÔfÇ6R¢“ ¢&—6R76W'F–öäW'&÷"‚%$är7FFRWf–FVæ6RFöW2æ÷Bf÷&ÒöæR6†–â"¢–b6VÆbç&ærç&V6÷&G2æB6VÆbç&ærç&V6÷&G5²ÓÒç7FFUögFW"Ò6VÆbç&ærç7FFUöF–vW7C ¢&—6R76W'F–öäW'&÷"‚%$är7W'&VçB7FFRFöW2æ÷BÖF6‚—G26öç7V×F–öâÆVFvW""¢ö67W–VC¢F–7E°¢7G"À¢GWÆU°¢–çBÂæöæRÀ¢7G"À¢6&Dö&¦V7@¢Â7F6´ö&¦V7@¢ÂG&–vvW&VD&–Æ—G”ö&¦V7@¢Â7F—fFVD&–Æ—G”ö&¦V7@¢ÂW&ÖæVçBÀ¢ÒÀ¢ÒÒ·Ð¢f÷"ö&¢–â6VÆbç7F6³ ¢–bæ÷B—6–ç7Fæ6R†ö&¢Â…7F6´ö&¦V7BÂG&–vvW&VD&–Æ—G”ö&¦V7BÂ7F—fFVD&–Æ—G”ö&¦V7B’“ ¢&—6R76W'F–öäW'&÷"‚'7F6²Ö’6öçF–âöæÇ’7VÆÂ÷"&–Æ—G’ö&¦V7G2"¢–bö&¢æö&¦V7Eö–B–âö67W–VC ¢&—6R76W'F–öäW'&÷"‚''VçF–ÖRö&¦V7Bö67W–W2Ö÷&RF†âöæR¦öæR"¢–b6VÆbåöö&¦V7G2ævWB†ö&¢æö&¦V7Eö–B’—2æ÷Bö&£ ¢&—6R76W'F–öäW'&÷"‚'7F6²6öçF–ç2âVç&Vv—7FW&VB÷"Æ–6VBö&¦V7B"¢–bö&¢ç¦öæRÒ'7F6²# ¢&—6R76W'F–öäW'&÷"‚'7F6²ö&¦V7B¦öæRFöW2æ÷BÖF6‚—G26öçF–æW""¢–bö&¢æ6öçG&öÆÆW"æ÷B–â&ævRƒ"“ ¢&—6R76W'F–öäW'&÷"‚'7F6²ö&¦V7B6öçG&öÆÆW"—2–çfÆ–B"¢–b—6–ç7Fæ6R†ö&¢Â7F6´ö&¦V7B“ ¢–bö&¢æ67Eö¶–æB—267D¶–æBåTå5Uõ%DTC ¢&—6R76W'F–öäW'&÷"‚'Vç7W÷'FVB7VÆÇ26ææ÷B&V6öÖR7F6²ö&¦V7G2"¢–bö&¢çF&vWEö–B—2æ÷BæöæRæBö&¢çF&vWEö–Bæ÷B–â6VÆbåöö&¦V7G3 ¢&—6R76W'F–öäW'&÷"‚'7F6²F&vWB”Bv2æWfW"&Vv—7FW&VB"¢–bç’‡F&vWEö–Bæ÷B–â6VÆbåöö&¦V7G2f÷"F&vWEö–B–âö&¢çF&vWEö–G2“ ¢&—6R76W'F–öäW'&÷"‚'7VÆÂF&vWB”Bv2æWfW"&Vv—7FW&VB"¢–bÆVâ‡6WB†ö&¢çF&vWEö–G2’’ÒÆVâ†ö&¢çF&vWEö–G2“ ¢&—6R76W'F–öäW'&÷"‚'7VÆÂF&vWG2&Ræ÷BF—7F–æ7B"¢VÆ–b—6–ç7Fæ6R†ö&¢ÂG&–vvW&VD&–Æ—G”ö&¦V7B“ ¢–bö&¢æWfVçBçÆ–W%ö–æFW‚æ÷B–â&ævRƒ"“ ¢&—6R76W'F–öäW'&÷"‚'G&–vvW"WfVçBÆ–W"—2–çfÆ–B"¢–bö&¢æVffV7B—2G&–vvW$VffV7BäD”U5ôE$s ¢G'“ ¢6VÆbå÷fÆ–FFUöF–W5öG&u÷G&–vvW"†ö&¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bö&¢æVffV7B—2G&–vvW$VffV7Bäu$åDTEôD”U5õ$UEU$ã ¢6÷W&6RÒ6VÆbåöö&¦V7G2ævWB†ö&¢ç6÷W&6Uö–B¢–bæ÷B—6–ç7Fæ6R‡6÷W&6RÂW&ÖæVçB“ ¢&—6R76W'F–öäW'&÷"‚&w&çFVBFVF‚G&–vvW"6÷W&6R—2–çfÆ–B"¢G'“ ¢6VÆbå÷fÆ–FFUöw&çFVEöFVF…÷&WGW&â€¢ö&¢æWfVçBÀ¢6÷W&6RÀ¢ö&¢æ÷&6ÆUög&vÖVçBÀ¢ö&¢æ6öçG&öÆÆW"À¢G&–vvW%ö–CÖö&¢çG&–vvW%ö–BÀ¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bö&¢æVffV7B—2G&–vvW$VffV7BäUD%ôE$”åôt”åõ45%“ ¢G'“ ¢6VÆbå÷fÆ–FFUöWF%öG&–åöv–å÷67'•÷G&–vvW"†ö&¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bö&¢æVffV7B—2G&–vvW$VffV7BäUD%õ4TÄeôÄ”dUôt”ã ¢G'“ ¢6VÆbå÷fÆ–FFUöWF%÷6VÆeöÆ–fUöv–å÷G&–vvW"†ö&¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bö&¢æVffV7B—2G&–vvW$VffV7BåU$ÔäTåEôÄTeEõ4TÄeô4õTåDU# ¢G'“ ¢6VÆbå÷fÆ–FFU÷W&ÖæVçEöÆVgEö6÷VçFW%÷&÷fVææ6R€¢6öçG&öÆÆW#Öö&¢æ6öçG&öÆÆW"À¢6÷W&6Uö–CÖö&¢ç6÷W&6Uö–BÀ¢6÷W&6Uö6&CÖö&¢ç6÷W&6Uö6&BÀ¢÷&6ÆUög&vÖVçCÖö&¢æ÷&6ÆUög&vÖVçBÀ¢WfVçCÖö&¢æWfVçBÀ¢G&–vvW%ö–CÖö&¢çG&–vvW%ö–BÀ¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bö&¢æVffV7B—2G&–vvW$VffV7Bä4ôåE$ôÄÄTEô5$TEU$UôÄTeEôõôäTåEôÄõ53 ¢G'“ ¢6VÆbå÷fÆ–FFUö6öçG&öÆÆVEö7&VGW&UöFW'GW&UöÆ÷72€¢6öçG&öÆÆW#Öö&¢æ6öçG&öÆÆW"À¢6÷W&6Uö–CÖö&¢ç6÷W&6Uö–BÀ¢6÷W&6Uö6&CÖö&¢ç6÷W&6Uö6&BÀ¢÷&6ÆUög&vÖVçCÖö&¢æ÷&6ÆUög&vÖVçBÀ¢WfVçCÖö&¢æWfVçBÀ¢G&–vvW%ö–CÖö&¢çG&–vvW%ö–BÀ¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bö&¢æVffV7B—2G&–vvW$VffV7Bä4ôåE$ôÄÄTEô4õTåDU$TEô5$TEU$UôÄTeEôÄ”dS ¢G'“ ¢6VÆbå÷fÆ–FFUö6÷VçFW&VEö7&VGW&UöFW'GW&UöÆ–fR€¢ö&¢æWfVçBÀ¢ö&¢ç6÷W&6Uö–BÀ¢ö&¢ç6÷W&6Uö6&BÀ¢ö&¢æ÷&6ÆUög&vÖVçBÀ¢ö&¢æ6öçG&öÆÆW"À¢G&–vvW%ö–CÖö&¢çG&–vvW%ö–BÀ¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bö&¢æVffV7B—2G&–vvW$VffV7Bä4ôåE$ôÄÄTEô%D”d5Eô4õTåDU%õE$å4dU# ¢G'“ ¢6VÆbå÷fÆ–FFUö'F–f7Eö6÷VçFW%÷G&ç6fW"€¢ö&¢æWfVçBÀ¢ö&¢ç6÷W&6Uö–BÀ¢ö&¢ç6÷W&6Uö6&BÀ¢ö&¢æ÷&6ÆUög&vÖVçBÀ¢ö&¢æ6öçG&öÆÆW"À¢G&–vvW%ö–CÖö&¢çG&–vvW%ö–BÀ¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bö&¢æVffV7B—2G&–vvW$VffV7BäDÔtUõDõõ4TÄeôÔä ¢G'“ ¢6VÆbå÷fÆ–FFUöFÖvU÷Fõ÷6VÆeöÖæ€¢ö&¢æWfVçBÀ¢ö&¢ç6÷W&6Uö–BÀ¢ö&¢ç6÷W&6Uö6&BÀ¢ö&¢æ÷&6ÆUög&vÖVçBÀ¢ö&¢æ6öçG&öÆÆW"À¢G&–vvW%ö–CÖö&¢çG&–vvW%ö–BÀ¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bö&¢æVffV7B—2G&–vvW$VffV7Bä4Ä55õ5TÄÅô45EõDTÕô4õTåDU# ¢6÷W&6RÒ6VÆbåöö&¦V7G2ævWB†ö&¢ç6÷W&6Uö–B¢–bæ÷B—6–ç7Fæ6R‡6÷W&6RÂW&ÖæVçB“ ¢&—6R76W'F–öäW'&÷"‚$6Æ727VÆÂÖ67B6÷W&6R—2–çfÆ–B"¢G'“ ¢6VÆbå÷fÆ–FFUö6Æ75÷7VÆÅö67E÷FVÕö6÷VçFW"€¢ö&¢Âö&¢æWfVçBÂ6÷W&6RÂö&¢æ÷&6ÆUög&vÖVçBÂö&¢æ6öçG&öÆÆW ¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bö&¢æVffV7B—2G&–vvW$VffV7BäUD%ô%D”d5EôE$s ¢G'“ ¢6VÆbå÷fÆ–FFUöWF%ö'F–f7EöG&u÷&÷fVææ6R€¢6öçG&öÆÆW#Öö&¢æ6öçG&öÆÆW"À¢6÷W&6Uö–CÖö&¢ç6÷W&6Uö–BÀ¢6÷W&6Uö6&CÖö&¢ç6÷W&6Uö6&BÀ¢÷&6ÆUög&vÖVçCÖö&¢æ÷&6ÆUög&vÖVçBÀ¢WfVçCÖö&¢æWfVçBÀ¢G&–vvW%ö–CÖö&¢çG&–vvW%ö–BÀ¢&WV—&Uö7W'&VçEö6öæF—F–öãÔfÇ6RÀ¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bö&¢æVffV7B—2G&–vvW$VffV7BäÄÄ”ä4UõDTÕõ$%•ô´U•tõ$Eô4„ô”4S ¢G'“ ¢6VÆbå÷fÆ–FFUöÆÆ–æ6U÷FV×÷&'•ö¶W—v÷&Eö6†ö–6U÷G&–vvW"†ö&¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bö&¢æVffV7B–â°¢G&–vvW$VffV7Bäu$åDTEô4ôÔ$EõTåDôt”âÀ¢G&–vvW$VffV7BäUT•ÔTåEõ5T%E•UôTåE%•ôED4‚À¢Ó ¢G'“ ¢6VÆbå÷fÆ–FFUöWV—ÖVçEöw&çFVE÷G&–vvW"†ö&¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bö&¢æVffV7B—2G&–vvW$VffV7Bä4ôÔ$EôDÔtUôE$uôÄõ4UôÄ”dS ¢G'“ ¢6VÆbå÷fÆ–FFUö6öÖ&EöG&uöÆ–fU÷G&–vvW"†ö&¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bö&¢æVffV7B—2G&–vvW$VffV7Bä4ôÔ$EôDÔtUôu$dU”$EôED4´U# ¢G'“ ¢6VÆbå÷fÆ–FFUö6öÖ&Eöw&fW–&E÷G&–vvW"†ö&¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bö&¢æVffV7B—2G&–vvW$VffV7BäUD%ôDU5E$õ•õD$tUEô5$TEU$S ¢G'“ ¢6VÆbå÷fÆ–FFUöWF%ö7&VGW&UöFW7G&÷•÷G&–vvW"†ö&¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bö&¢æVffV7B—2G&–vvW$VffV7BäUD%õD$tUEô5$TEU$UõTÕõTåD ¢G'“ ¢6VÆbå÷fÆ–FFUöWF%÷V×÷G&–vvW"†ö&¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢VÆ–b—6–ç7Fæ6R†ö&¢Â7F—fFVD&–Æ—G”ö&¦V7B“ ¢–bö&¢ç6÷W&6Uö–Bæ÷B–â6VÆbåöö&¦V7G3 ¢&—6R76W'F–öäW'&÷"‚&7F—fFVB&–Æ—G’6÷W&6R”Bv2æWfW"&Vv—7FW&VB"¢–bç’‡F&vWEö–Bæ÷B–â6VÆbåöö&¦V7G2f÷"F&vWEö–B–âö&¢çF&vWEö–G2“ ¢&—6R76W'F–öäW'&÷"‚&7F—fFVB&–Æ—G’F&vWB”Bv2æWfW"&Vv—7FW&VB"¢ö67W–VE¶ö&¢æö&¦V7Eö–EÒÒ„æöæRÂ'7F6²"Âö&¢¢–bÆVâ‡·G&–vvW"çG&–vvW%ö–Bf÷"G&–vvW"–â6VÆbçVæF–æu÷G&–vvW'7Ò’ÒÆVâ€¢6VÆbçVæF–æu÷G&–vvW'0¢“ ¢&—6R76W'F–öäW'&÷"‚'VæF–ærG&–vvW"”G2×W7B&RVæ—VR"¢f÷"G&–vvW"–â6VÆbçVæF–æu÷G&–vvW'3 ¢–bG&–vvW"æVffV7B—2G&–vvW$VffV7BäDÔtUõDõõ4TÄeôÔä ¢G'“ ¢6VÆbå÷fÆ–FFUöFÖvU÷Fõ÷6VÆeöÖæ€¢G&–vvW"æWfVçBÀ¢G&–vvW"ç6÷W&6Uö–BÀ¢G&–vvW"ç6÷W&6Uö6&BÀ¢G&–vvW"æ÷&6ÆUög&vÖVçBÀ¢G&–vvW"æ6öçG&öÆÆW"À¢G&–vvW%ö–C×G&–vvW"çG&–vvW%ö–BÀ¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bG&–vvW"æVffV7B—2G&–vvW$VffV7Bä4ôåE$ôÄÄTEô%D”d5Eô4õTåDU%õE$å4dU# ¢G'“ ¢6VÆbå÷fÆ–FFUö'F–f7Eö6÷VçFW%÷G&ç6fW"€¢G&–vvW"æWfVçBÀ¢G&–vvW"ç6÷W&6Uö–BÀ¢G&–vvW"ç6÷W&6Uö6&BÀ¢G&–vvW"æ÷&6ÆUög&vÖVçBÀ¢G&–vvW"æ6öçG&öÆÆW"À¢G&–vvW%ö–C×G&–vvW"çG&–vvW%ö–BÀ¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bG&–vvW"æVffV7B—2G&–vvW$VffV7BåU$ÔäTåEôÄTeEõ4TÄeô4õTåDU# ¢G'“ ¢6VÆbå÷fÆ–FFU÷W&ÖæVçEöÆVgEö6÷VçFW%÷&÷fVææ6R€¢6öçG&öÆÆW#×G&–vvW"æ6öçG&öÆÆW"À¢6÷W&6Uö–C×G&–vvW"ç6÷W&6Uö–BÀ¢6÷W&6Uö6&C×G&–vvW"ç6÷W&6Uö6&BÀ¢÷&6ÆUög&vÖVçC×G&–vvW"æ÷&6ÆUög&vÖVçBÀ¢WfVçC×G&–vvW"æWfVçBÀ¢G&–vvW%ö–C×G&–vvW"çG&–vvW%ö–BÀ¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–bG&–vvW"æVffV7B—2G&–vvW$VffV7BäUD%ô%D”d5EôE$s ¢G'“ ¢6VÆbå÷fÆ–FFUöWF%ö'F–f7EöG&u÷&÷fVææ6R€¢6öçG&öÆÆW#×G&–vvW"æ6öçG&öÆÆW"À¢6÷W&6Uö–C×G&–vvW"ç6÷W&6Uö–BÀ¢6÷W&6Uö6&C×G&–vvW"ç6÷W&6Uö6&BÀ¢÷&6ÆUög&vÖVçC×G&–vvW"æ÷&6ÆUög&vÖVçBÀ¢WfVçC×G&–vvW"æWfVçBÀ¢G&–vvW%ö–C×G&–vvW"çG&–vvW%ö–BÀ¢&WV—&Uö7W'&VçEö6öæF—F–öãÔfÇ6RÀ¢¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢f÷"Æ–W%ö–æFW‚ÂÆ–W"–âVçVÖW&FR‡6VÆbçÆ–W'2“ ¢f÷"¦öæUöæÖR–â‚&Æ–'&'’"Â&†æB"Â&&GFÆVf–VÆB"Â&w&fW–&B"Â&W†–ÆR"“ ¢f÷"ö&¢–âvWFGG"‡Æ–W"Â¦öæUöæÖR“ ¢–bæ÷B—6–ç7Fæ6R†ö&¢Â„6&Dö&¦V7BÂW&ÖæVçB’“ ¢&—6R76W'F–öäW'&÷"‚'¦öæW2Ö’6öçF–âöæÇ’&Vv—7FW&VB'VçF–ÖRö&¦V7G2"¢–bö&¢æö&¦V7Eö–B–âö67W–VC ¢&—6R76W'F–öäW'&÷"‚''VçF–ÖRö&¦V7Bö67W–W2Ö÷&RF†âöæR¦öæR"¢–b6VÆbåöö&¦V7G2ævWB†ö&¢æö&¦V7Eö–B’—2æ÷Bö&£ ¢&—6R76W'F–öäW'&÷"‚'¦öæR6öçF–ç2âVç&Vv—7FW&VB÷"Æ–6VBö&¦V7B"¢–bö&¢ç¦öæRÒ¦öæUöæÖS ¢&—6R76W'F–öäW'&÷"‚''VçF–ÖRö&¦V7B¦öæRFöW2æ÷BÖF6‚—G26öçF–æW""¢W‡V7FVEö†öÆFW"Òö&¢æ6öçG&öÆÆW"–b¦öæUöæÖRÓÒ&&GFÆVf–VÆB"VÇ6Rö&¢æ÷væW ¢–bW‡V7FVEö†öÆFW"ÒÆ–W%ö–æFWƒ ¢&—6R76W'F–öäW'&÷"‚''VçF–ÖRö&¦V7Bö67W–W2F†Rw&öærÆ–W"w2¦öæR"¢–b¦öæUöæÖRÒ&&GFÆVf–VÆB"æBö&¢æ6öçG&öÆÆW"Òö&¢æ÷væW# ¢&—6R76W'F–öäW'&÷"‚&æöæ&GFÆVf–VÆBö&¦V7B6öçG&öÆÆW"×W7B&W6WBFò÷væW""¢–b—6–ç7Fæ6R†ö&¢Â6&Dö&¦V7B’æBö&¢æ—5÷Fö¶Vã ¢&—6R76W'F–öäW'&÷"€¢&æöæ&GFÆVf–VÆBFö¶Vâ×W7B6V6RBF†R4$&÷VæF'’ ¢¢ö67W–VE¶ö&¢æö&¦V7Eö–EÒÒ‡Æ–W%ö–æFW‚Â¦öæUöæÖRÂö&¢¢f÷"ö&¦V7Eö–BÂö&¢–â6VÆbåöö&¦V7G2æ—FV×2‚“ ¢–bö&¢ç¦öæRÓÒ&f÷&ÖW"# ¢–bö&¦V7Eö–B–âö67W–VC ¢&—6R76W'F–öäW'&÷"‚&f÷&ÖW"ö&¦V7B7F–ÆÂö67W–W2¦öæR"¢VÆ–bö&¦V7Eö–Bæ÷B–âö67W–VC ¢&—6R76W'F–öäW'&÷"‚&WF†÷&—FF—fR'VçF–ÖRö&¦V7Bö67W–W2æò¦öæR" ¢f÷"Æ–W%ö–æFW‚ÂÆ–W"–âVçVÖW&FR‡6VÆbçÆ–W'2“ ¢ÆVvVæF'•öæÖW3¢6WE·7G%ÒÒ6WB‚¢f÷"W&ÖæVçB–âÆ–W"æ&GFÆVf–VÆC ¢–bW&ÖæVçBæ6öçG&öÆÆW"ÒÆ–W%ö–æFWƒ ¢&—6R76W'F–öäW'&÷"‚&&GFÆVf–VÆB6öçG&öÆÆW"FöW2æ÷BÖF6‚Æ–W"¦öæR"¢–bW&ÖæVçBæVçFW&VEö&GFÆVf–VÆE÷GW&ââ6VÆbçGW&ã ¢&—6R76W'F–öäW'&÷"‚'W&ÖæVçBVçFW&VBF†R&GFÆVf–VÆB–âgWGW&RGW&â"¢–bW&ÖæVçBæVçFW&VE÷VæFW%ö6öçG&öÆÆW"æ÷B–â&ævRƒ"“ ¢&—6R76W'F–öäW'&÷"‚'W&ÖæVçBÆ6·2—G2VçG'’6öçG&öÆÆW"&÷fVææ6R"¢–bW&ÖæVçBæ—5÷Fö¶VâÒ—6–ç7Fæ6R‡W&ÖæVçBæ6&BÂFö¶VäFVf–æ—F–öâ“ ¢&—6R76W'F–öäW'&÷"‚'Fö¶Vâ'VçF–ÖR7FFRFöW2æ÷BÖF6‚—G2Fö¶VâFVf–æ—F–öâ"¢–bæ÷BW&ÖæVçBçG—UöÆ–æS ¢&—6R76W'F–öäW'&÷"‚'W&ÖæVçBG—RÆ–æR×W7B&VÖ–âæöæV×G’"¢–bW&ÖæVçBæ6&Bæ—5ö7&VGW&RæB€¢W&ÖæVçBæ6&Bç÷vW"—2æöæR÷"W&ÖæVçBæ6&BçF÷Vv†æW72—2æöæP¢“ ¢&—6R76W'F–öäW'&÷"‚&7&VGW&RW&ÖæVçBÆ6·2&–çFVB÷vW"÷F÷Vv†æW72"¢–b€¢W&ÖæVçBæ—5ö7&VGW&P¢æBW&ÖæVçBæ†5÷&W&W6VçFVE÷÷vW%÷F÷Vv†æW70¢æBW&ÖæVçBçF÷Vv†æW72ÃÒ ¢“ ¢&—6R76W'F–öäW'&÷"‚&æöç÷6—F—fRF÷Vv†æW72×W7B&R†æFÆVB'’â4$"¢–çfÆ–Eö6÷VçFW'2Òç’€¢æ÷B—6–ç7Fæ6R†6÷VçFW%÷G—RÂ7G"¢÷"æ÷B6÷VçFW%÷G—P¢÷"æ÷B—6–ç7Fæ6R‡fÇVRÂ–çB¢÷"—6–ç7Fæ6R‡fÇVRÂ&ööÂ¢÷"fÇVRÃÒ ¢f÷"6÷VçFW%÷G—RÂfÇVR–âW&ÖæVçBæ6÷VçFW'2æ—FV×2‚¢¢–b–çfÆ–Eö6÷VçFW'3 ¢&—6R76W'F–öäW'&÷"‚&6÷VçFW"VçF—F–W2×W7B&RæöææVvF—fR–çFVvW'2"¢–bç’€¢g&vÖVçBæ÷B–â6VÆbæ–çFW'&WFW"æg&vÖVçG2‡W&ÖæVçBæ6&B¢÷"GW&ââ6VÆbçGW&à¢÷"GW&âÂ¢f÷"g&vÖVçBÂGW&â–âW&ÖæVçBæöæ6U÷W%÷GW&åö7F—fF–öç2æ—FV×2‚¢“ ¢&—6R76W'F–öäW'&÷"‚&öæ6R×W"×GW&â7F—fF–öâÖ&¶W"—2–çfÆ–B"¢f÷"ÖöF–f–W"–âW&ÖæVçBçEöÖöF–f–W'3 ¢–bÖöF–f–W"æGW&F–öâæ÷B–â²'W'6—7FVçB"Â'VçF–ÅöVæEööe÷GW&â'Ó ¢&—6R76W'F–öäW'&÷"‚'Væ¶æ÷vâõBÖöF–f–W"GW&F–öâ"¢–bÖöF–f–W"æ7&VFVE÷GW&ââ6VÆbçGW&ã ¢&—6R76W'F–öäW'&÷"‚%õBÖöF–f–W"÷&–v–æFW2–âgWGW&RGW&â"¢–bç’€¢VffV7BæGW&F–öâÒ'VçF–ÅöVæEööe÷GW&â ¢÷"æ÷B—6–ç7Fæ6R†VffV7Bæ¶W—v÷&BÂ…7G&–¶T¶W—v÷&BÂFV×÷&'”¶W—v÷&B’¢f÷"VffV7B–âW&ÖæVçBçFV×÷&'•ö¶W—v÷&EöVffV7G0¢“ ¢&—6R76W'F–öäW'&÷"‚'FV×÷&'’¶W—v÷&BVffV7B—2ÖÆf÷&ÖVB"¢–bç’€¢VffV7BæGW&F–öâæ÷B–â²'W'6—7FVçB"Â'VçF–ÅöVæEööe÷GW&â'Ð¢÷"æ÷BVffV7BæFFVE÷G—W0¢÷"ç’†æ÷B—FVÒf÷"—FVÒ–âVffV7BæFFVE÷G—W2¢÷"ç’†æ÷B—FVÒf÷"—FVÒ–âVffV7BæFFVE÷7V'G—W2¢f÷"VffV7B–âW&ÖæVçBçFV×÷&'•÷G—UöVffV7G0¢“ ¢&—6R76W'F–öäW'&÷"‚'FV×÷&'’G—RVffV7B—2ÖÆf÷&ÖVB"¢VffV7Eö–G2Ò¶VffV7BæVffV7Eö–Bf÷"VffV7B–âW&ÖæVçBæ6†&7FW&—7F–5öVffV7G7Ð¢–bÆVâ†VffV7Eö–G2’ÒÆVâ‡W&ÖæVçBæ6†&7FW&—7F–5öVffV7G2“ ¢&—6R76W'F–öäW'&÷"‚&6†&7FW&—7F–2VffV7B”G2×W7B&RVæ—VR"¢–bç’€¢VffV7BæGW&F–öâæ÷B–â²'W'6—7FVçB"Â'VçF–ÅöVæEööe÷GW&â'Ð¢f÷"VffV7B–âW&ÖæVçBæ6†&7FW&—7F–5öVffV7G0¢“ ¢&—6R76W'F–öäW'&÷"‚&6†&7FW&—7F–2VffV7BGW&F–öâ—2ÖÆf÷&ÖVB"¢–bç’€¢FWVæFVæ7’æ÷B–âVffV7Eö–G0¢f÷"VffV7B–âW&ÖæVçBæ6†&7FW&—7F–5öVffV7G0¢f÷"FWVæFVæ7’–âVffV7BæFWVæG5ööà¢“ ¢&—6R76W'F–öäW'&÷"‚&6†&7FW&—7F–2VffV7BFWVæFVæ7’—2Ö—76–ær"¢–bW&ÖæVçBæ—5ö7&VGW&RæBW&ÖæVçBæ†5÷&W&W6VçFVE÷÷vW%÷F÷Vv†æW73 ¢G'“ ¢W&ÖæVçBæWfÇVFU÷÷vW%÷F÷Vv†æW72‚¢W†6WBfÇVTW'&÷"2W'&÷# ¢&—6R76W'F–öäW'&÷"‡7G"†W'&÷"’’g&öÒW'&÷ ¢–b$ÆVvVæF'’"–âW&ÖæVçBæ6&BçG—UöÆ–æS ¢–bW&ÖæVçBæ6&BææÖR–âÆVvVæF'•öæÖW3 ¢&—6R76W'F–öäW'&÷"‚&ÆVvVæB'VÆRÆVgBGWÆ–6FRæÖW2öâ&GFÆVf–VÆB"¢ÆVvVæF'•öæÖW2æFB‡W&ÖæVçBæ6&BææÖR ¢FVb6†V6µöÆ–fR‡6VÆb’ÓâæöæS ¢æWvÇ•öÆ÷7BÒµÐ¢f÷"–æFW‚ÂÆ–W"–âVçVÖW&FR‡6VÆbçÆ–W'2“ ¢–bÆ–W"æÆ–fRÃÒæBæ÷BÆ–W"æÆ÷7C ¢Æ–W"æÆ÷7BÒG'VP¢Æ–W"æÆ÷75÷&V6öâÒ&Æ–fU÷¦W&õö÷%öÆW72 ¢æWvÇ•öÆ÷7BæVæB†–æFW‚¢6VÆbæÆör‚'Æ–W%öÆ÷7B"ÂÆ–W#×Æ–W"ææÖRÂ&V6öã×Æ–W"æÆ÷75÷&V6öâ¢–bÆVâ†æWvÇ•öÆ÷7B’ÓÒ# ¢6VÆbçv–ææW"ÒæöæP¢6VÆbçFW&Ö–æÅöG&rÒG'VP¢6VÆbæÆör‚&vÖUöG&r"Â&V6öãÒ'6–×VÇFæV÷W5÷Æ–W%öÆ÷72"¢VÆ–bæWvÇ•öÆ÷7C ¢6VÆbçv–ææW"ÒÒæWvÇ•öÆ÷7E³Ð ¢&÷W'G¢FVb—5÷FW&Ö–æÂ‡6VÆb’Óâ&ööÃ ¢&WGW&â6VÆbçv–ææW"—2æ÷BæöæR÷"6VÆbçFW&Ö–æÅöG&p ¢FVb&V6÷&Eö6öæf÷&Öæ6U÷7F÷€¢6VÆbÂ¶–æC¢7G"Â&Vf÷&Uöf–ævW'&–çC¢7G"Â¢ÂFWF–Ã¢7G ¢’Óâ6öæf÷&Öæ6U7F÷&V6÷&C ¢""%&V6÷&Bâ–ÆÆVvÂÖ×WFF–öâ÷"Væ6Æ76–f–VB×&V6‚7F÷FWFW&Ö–æ—7F–6ÆÇ’â"" ¢–b¶–æBæ÷B–â²&–ÆÆVvÅö×WFF–öâ"Â'Væ6Æ76–f–VE÷&V6‚"Â'6–ÆVçEö&÷†–ÖF–öâ'Ó ¢&—6RfÇVTW'&÷"‚&6öæf÷&Öæ6R7F÷¶–æB—2Vç7W÷'FVB"¢gFW"Ò6VÆbæWF†÷&—FF—fU÷7FFUöf–ævW'&–çB‚¢–b¶–æBÓÒ&–ÆÆVvÅö×WFF–öâ"æB&Vf÷&Uöf–ævW'&–çBÓÒgFW# ¢&—6RfÇVTW'&÷"‚&–ÆÆVvÂÖ×WFF–öâ7F÷&WV—&W2âö'6W'fVB7FFR6†ævR"¢&V6÷&BÒ6öæf÷&Öæ6U7F÷&V6÷&B€¢b'7F÷×¶ÆVâ‡6VÆbæ6öæf÷&Öæ6U÷7F÷÷&V6÷&G2’²£fGÒ"À¢¶–æBÀ¢6VÆbçGW&âÀ¢6VÆbç†6RÀ¢6VÆbç7FWçfÇVRÀ¢&Vf÷&Uöf–ævW'&–çBÀ¢gFW"À¢FWF–ÂÀ¢¢6VÆbæ6öæf÷&Öæ6U÷7F÷÷&V6÷&G2æVæB‡&V6÷&B¢&WGW&â&V6÷&@ ¢FVbWF†÷&—FF—fU÷7FFUöf–ævW'&–çB‡6VÆb’Óâ7G# ¢""%7F&ÆR×WFF–öâÖ&÷VæF'’F–vW7BW†6ÇVF–ærF–væ÷7F–72æBWf–FVæ6RÆVFvW'2â"" ¢&WGW&â6†#Sb€¢&W"‡6VÆbåöWF†÷&—FF—fU÷7FFUöf–ævW'&–çE÷&V–ÖvR‚’’æVæ6öFR‚'WFbÓ‚"¢’æ†W†F–vW7B‚ ¢FVböWF†÷&—FF—fU÷7FFUöf–ævW'&–çE÷&V–ÖvR‡6VÆb’ÓâGWÆU¶ö&¦V7BÂââåÓ ¢""%&WGW&âF†R6ö×ÆWFR6æöæ–6Â&V–ÖvRW6VB'’F†RW†—7F–ær7FFRf–ævW'&–çBâ"" ¢¦öæW2ÒGWÆR€¢€¢GWÆR†6&Bæö&¦V7Eö–Bf÷"6&B–âÆ–W"æÆ–'&'’’À¢GWÆR†6&Bæö&¦V7Eö–Bf÷"6&B–âÆ–W"æ†æB’À¢GWÆR‡W&ÖæVçBæö&¦V7Eö–Bf÷"W&ÖæVçB–âÆ–W"æ&GFÆVf–VÆB’À¢GWÆR†6&Bæö&¦V7Eö–Bf÷"6&B–âÆ–W"æw&fW–&B’À¢GWÆR†6&Bæö&¦V7Eö–Bf÷"6&B–âÆ–W"æW†–ÆR’À¢Æ–W"æÆ–fRÀ¢Æ–W"æÆ÷7BÀ¢Æ–W"æf–ÆVEöG&u÷VæF–ærÀ¢¢f÷"Æ–W"–â6VÆbçÆ–W'0¢¢÷&–v–æÂÒ€¢6VÆbçGW&âÀ¢6VÆbæ7F—fU÷Æ–W"À¢6VÆbç7FWçfÇVRÀ¢GWÆR†—FVÒæö&¦V7Eö–Bf÷"—FVÒ–â6VÆbç7F6²’À¢6VÆbåö6öÖ&EöGF6¶W'2À¢6VÆbåö6öÖ&Eö&Æö6·2À¢¦öæW2À¢6VÆbç&ærç7FFUöF–vW7BÀ¢6VÆbçv–ææW"À¢¢&WGW&â÷&–v–æÂ²…G'VRÂ’–b6VÆbçFW&Ö–æÅöG&rVÇ6R÷&–v–æÀ ¢FVbWF†÷&—FF—fU÷7FFUöf–ævW'&–çEöWf–FVæ6R‡6VÆb’ÓâF–7E·7G"Âö&¦V7EÓ ¢""%6W&–Æ—¦RF†RW†—7F–ærf–ævW'&–çB&V–ÖvRv—F†÷WBFVf–æ–ær6V6öæB7FFRÖöFVÂâ"" ¢WF†÷&—G’Ò6VÆbåöWF†÷&—FF—fU÷7FFUöf–ævW'&–çE÷&V–ÖvR‚¢¦öæW2ÒWF†÷&—G•³eÐ¢&WGW&â°¢'66†VÖR#¢&Væv–æSrÖWF†÷&—FF—fR×7FFRÖf–ævW'&–çB×&V–ÖvR×c"À¢'GW&â#¢WF†÷&—G•³ÒÀ¢&7F—fU÷Æ–W%ö–æFW‚#¢WF†÷&—G•³ÒÀ¢'7FW#¢WF†÷&—G•³%ÒÀ¢'7F6µöö&¦V7Eö–G2#¢Æ—7B†WF†÷&—G•³5Ò’À¢&6öÖ&EöGF6¶W%ö–G2#¢Æ—7B†WF†÷&—G•³EÒ’À¢&6öÖ&Eö&Æö6·2#¢¶Æ—7B†—FVÒ’f÷"—FVÒ–âWF†÷&—G•³UÕÒÀ¢'Æ–W'2#¢°¢°¢&Æ–'&'•öö&¦V7Eö–G2#¢Æ—7B‡Æ–W%³Ò’À¢&†æEöö&¦V7Eö–G2#¢Æ—7B‡Æ–W%³Ò’À¢&&GFÆVf–VÆEöö&¦V7Eö–G2#¢Æ—7B‡Æ–W%³%Ò’À¢&w&fW–&Eöö&¦V7Eö–G2#¢Æ—7B‡Æ–W%³5Ò’À¢&W†–ÆUöö&¦V7Eö–G2#¢Æ—7B‡Æ–W%³EÒ’À¢&Æ–fR#¢Æ–W%³UÒÀ¢&Æ÷7B#¢Æ–W%³eÒÀ¢&f–ÆVEöG&u÷VæF–ær#¢Æ–W%³uÒÀ¢Ð¢f÷"Æ–W"–â¦öæW0¢ÒÀ¢'&æu÷7FFUöF–vW7B#¢WF†÷&—G•³uÒÀ¢'v–ææW%ö–æFW‚#¢WF†÷&—G•³…ÒÀ¢¢¢‡²'FW&Ö–æÅöG&r#¢G'VWÒ–b6VÆbçFW&Ö–æÅöG&rVÇ6R·Ò’À¢Ð ¢FVböW†V7WFVEö6öæf÷&Öæ6U÷&VfW&Væ6W2‡6VÆb’ÓâÆ—7E¶F–7E·7G"Âö&¦V7EÕÓ ¢""$–æFW‚ÖGW&R7F–öâWf–FVæ6Rv—F†÷WB&WÆ6–ær÷"vV¶Væ–ærF†BWf–FVæ6Râ"" ¢6VÆbå÷fÆ–FFU÷7GVåö†—7F÷'’‚¢6VÆbåö6†V6µöÖ–ÆÅ÷F‡&VUö†—7F÷'’‚¢6VÆbå÷fÆ–FFUö·&æu÷&Vf–ÆÅöÆ—fR‚¢6VÆbåö6†V6µö§W'•÷&–uö†—7F÷'’‚¢6VÆbåö6†V6µ÷f–v–ÆçFUöÆ—fR‚¢6VÆbçfÆ–FFUöfööE÷6V&6…÷6æ6†÷EöWf–FVæ6R€¢²&WfVçG2#¢6VÆbæWfVçG2Â&fööE÷6V&6…öWf–FVæ6R#¢6VÆbæfööE÷6V&6…÷6æ6†÷EöWf–FVæ6R‚—Ð¢¢6VÆbçfÆ–FFUöG&uöF—66&E÷6æ6†÷EöWf–FVæ6R‡²&WfVçG2#¢6VÆbæWfVçG7Ò¢&VfW&Væ6W3¢Æ—7E¶F–7E·7G"Âö&¦V7EÕÒÒµÐ ¢FVbFB†¶–æC¢7G"ÂWf–FVæ6Uö–C¢7G"Â6÷W&6Uö–C¢7G"Âg&vÖVçC¢7G"’ÓâæöæS ¢6÷W&6RÒ6VÆbåöö&¦V7G2ævWB‡6÷W&6Uö–B¢–bæ÷B—6–ç7Fæ6R‡6÷W&6RÂ„6&Dö&¦V7BÂ7F6´ö&¦V7BÂW&ÖæVçB’“ ¢&WGW&à¢g&vÖVçG2Ò6VÆbå÷6VÖçF–5ög&vÖVçG2‡6÷W&6Ræ6&B¢–bg&vÖVçBæ÷B–âg&vÖVçG3 ¢&WGW&à¢–æFW‚Òg&vÖVçG2æ–æFW‚†g&vÖVçB¢&VfW&Væ6W2æVæB€¢°¢&Wf–FVæ6Uö¶–æB#¢¶–æBÀ¢&Wf–FVæ6Uö–B#¢Wf–FVæ6Uö–BÀ¢'6÷W&6Uö–B#¢6÷W&6Uö–BÀ¢'6VÖçF–5ö¶W’#¢6VÖçF–5ö¶W’€¢vWFGG"‡6÷W&6Ræ6&BÂ&÷&6ÆUö–B"Â""’ÂÂ–æFW‚Âg&vÖVç@¢’À¢&÷&6ÆUög&vÖVçB#¢g&vÖVçBÀ¢Ð¢ ¢f÷"—FVÒ–â6VÆbæ7F—fF–öåöWf–FVæ6S ¢–b—FVÒç&W6öÇfVC ¢FB‚&7F—fFVEö&–Æ—G’"Â—FVÒç7F6µöö&¦V7Eö–BÂ—FVÒç6÷W&6Uö–BÂ—FVÒæ÷&6ÆUög&vÖVçB¢f÷"—FVÒ–â6VÆbæfööEö7F—fF–öåöWf–FVæ6S ¢–b—FVÒç&W6öÇfVC ¢FB‚&fööEö7F—fF–öâ"Â—FVÒç7F6µöö&¦V7Eö–BÂ—FVÒç6÷W&6Uö–BÂ—FVÒæ÷&6ÆUög&vÖVçB¢f÷"—FVÒ–â6VÆbç6æVµöWf–FVæ6S ¢–b—FVÒç&W6öÇfVEöö&¦V7Eö–B—2æ÷BæöæS ¢FB‚'6æV²"Â—FVÒç7F6µöö&¦V7Eö–BÂ—FVÒæ†æEöö&¦V7Eö–BÂ—FVÒæ÷&6ÆUög&vÖVçB¢f÷"—FVÒ–â6VÆbæ†æEö&÷GFöÕöG&uöWf–FVæ6S ¢FB‚&†æEö&÷GFöÕöG&r"Â—FVÒæWfVçEö–BÂ—FVÒç6÷W&6Uö–BÂ—FVÒæ÷&6ÆUög&vÖVçB¢f÷"—FVÒ–â6VÆbæF—66&EöG&uöWf–FVæ6S ¢FB‚&F—66&EöG&r"Â—FVÒæWfVçEö–BÂ—FVÒç6÷W&6Uö–BÂ—FVÒæ÷&6ÆUög&vÖVçB¢f÷"—FVÒ–â6VÆbæÆ–fVÆ–æµöWf–FVæ6S ¢FB‚&Æ–fVÆ–æ²"Â—FVÒæWfVçEö–BÂ—FVÒç6÷W&6Uö–BÂ$Æ–fVÆ–æ²"¢f÷"—FVÒ–â6VÆbæWF%öG&–åöv–å÷67'•öWf–FVæ6S ¢FB€¢&WF%öG&–åöv–å÷67'’"À¢—FVÒç7F6µöö&¦V7Eö–BÀ¢—FVÒç6÷W&6Uö–BÀ¢—FVÒæ÷&6ÆUög&vÖVçBÀ¢¢f÷"Wf–FVæ6R–â6VÆbæ6öÖ&EöFÖvUöWf–FVæ6S ¢f÷"76–væÖVçB–âWf–FVæ6Ræ76–væÖVçG3 ¢6÷W&6RÒ6VÆbåöö&¦V7G2ævWB†76–væÖVçBç6÷W&6Uö–B¢–bæ÷B—6–ç7Fæ6R‡6÷W&6RÂW&ÖæVçB“ ¢6öçF–çVP¢–b76–væÖVçBçG&×ÆS ¢FB€¢'G&×ÆR"À¢b&6öÖ&C§¶Wf–FVæ6Rç6WVVæ6WÓ§¶76–væÖVçBç6÷W&6Uö–GÓ§G&×ÆR"À¢76–væÖVçBç6÷W&6Uö–BÀ¢%G&×ÆR"À¢¢f÷"¶W—v÷&B–â‚$f—'7B7G&–¶R"Â$F÷V&ÆR7G&–¶R"“ ¢–b¶W—v÷&B–â6VÆbå÷6VÖçF–5ög&vÖVçG2‡6÷W&6Ræ6&B“ ¢FB€¢'7G&–¶UöFÖvU÷7FW"À¢b&6öÖ&C§¶Wf–FVæ6Rç6WVVæ6WÓ§¶76–væÖVçBç6÷W&6Uö–GÓ§¶¶W—v÷&GÒ"À¢76–væÖVçBç6÷W&6Uö–BÀ¢¶W—v÷&BÀ¢¢f÷"WfVçB–â6VÆbæWfVçG3 ¢–b6&D–çFW'&WFW"æ—5ö·&æu÷&Vf–ÆÅög&vÖVçB†WfVçBævWB‚&÷&6ÆUög&vÖVçB"’“ ¢–bWfVçBævWB‚&WfVçB"’ÓÒ&·&æu÷&Vf–ÆÅö6öÖÖ—GFVB"æBWfVçE²'&WVW7FVB%Òâ ¢FB€¢&·&æu÷&Vf–ÆÂ"À¢WfVçE²'7F6µöö&¦V7Eö–B%ÒÀ¢WfVçE²'6÷W&6Uö–B%ÒÀ¢WfVçE²&÷&6ÆUög&vÖVçB%ÒÀ¢¢6öçF–çVP¢–bWfVçBævWB‚&÷&6ÆUög&vÖVçB"’ÓÒ6&D–çFW'&WFW"äÔ”ÄÅõD…$TUôe$tÔTåC ¢–bWfVçBævWB‚&WfVçB"’ÓÒ&Ö–ÆÅ÷F‡&VUö6öÖÖ—GFVB# ¢FB€¢&Ö–ÆÅ÷F‡&VR"À¢WfVçE²'7F6µöö&¦V7Eö–B%ÒÀ¢WfVçE²'6÷W&6Uö–B%ÒÀ¢WfVçE²&÷&6ÆUög&vÖVçB%ÒÀ¢¢6öçF–çVP¢–bWfVçBævWB‚&÷&6ÆUög&vÖVçB"’ÓÒ6&D–çFW'&WFW"ä¥U%•õ$”uôe$tÔTåC ¢–bWfVçBævWB‚&WfVçB"’ÓÒ&§W'•÷&–uö6öÖÖ—GFVB# ¢FB€¢&§W'•÷&–r"À¢WfVçE²'7F6µöö&¦V7Eö–B%ÒÀ¢WfVçE²'6÷W&6Uö–B%ÒÀ¢WfVçE²&÷&6ÆUög&vÖVçB%ÒÀ¢¢6öçF–çVP¢–bWfVçBævWB‚&VffV7B"’ÓÒ&WF%÷f–v–ÆçFR# ¢6öçF–çVP¢–bWfVçBævWB‚&WfVçB"’–â°¢&FÖvUöFVÇB"À¢'67'•ö6öÖÖ—GFVB"À¢'Fö¶Vç5ö7&VFVB"À¢'G&–vvW%÷&W6öÇfVB"À¢'7VÆÅ÷&W6öÇfVB"À¢'7VÆÅ÷&W6öÇfVEöæõöVffV7B"À¢&W&÷&W6öÇfVB"À¢Ó ¢6÷W&6Uö–BÒWfVçBævWB‚'6÷W&6Uö–B"¢g&vÖVçBÒWfVçBævWB‚&÷&6ÆUög&vÖVçB"¢Wf–FVæ6Uö–BÒWfVçBævWB‚&WfVçEö–B"’÷"WfVçBævWB‚'7F6µöö&¦V7Eö–B"¢–bÆÂ†—6–ç7Fæ6R‡fÇVRÂ7G"’f÷"fÇVR–â‡6÷W&6Uö–BÂg&vÖVçBÂWf–FVæ6Uö–B’“ ¢FB€¢7G"†WfVçE²&WfVçB%Ò’À¢7G"†Wf–FVæ6Uö–B’À¢7G"‡6÷W&6Uö–B’À¢7G"†g&vÖVçB’À¢¢Væ—VRÒ°¢€¢7G"†—FVÕ²&Wf–FVæ6Uö¶–æB%Ò’À¢7G"†—FVÕ²&Wf–FVæ6Uö–B%Ò’À¢7G"†—FVÕ²'6÷W&6Uö–B%Ò’À¢7G"†—FVÕ²'6VÖçF–5ö¶W’%Ò’À¢“¢—FVÐ¢f÷"—FVÒ–â&VfW&Væ6W0¢Ð¢&WGW&â6÷'FVB€¢Væ—VRçfÇVW2‚’À¢¶W“ÖÆÖ&F—FVÓ¢‡7G"†—FVÕ²&Wf–FVæ6Uö¶–æB%Ò’Â7G"†—FVÕ²&Wf–FVæ6Uö–B%Ò’’À¢ ¢FVb6æ6†÷B‡6VÆb’ÓâF–7E·7G"Âö&¦V7EÓ ¢&WGW&â°¢&Væv–æU÷fW'6–öâ#¢Tät”äUõdU%4”ôâÀ¢'GW&â#¢6VÆbçGW&âÀ¢'GW&ç5÷7F'FVB#¢6VÆbçGW&âÀ¢'FW&Ö–æÂ#¢6VÆbæ—5÷FW&Ö–æÂÀ¢'FW&Ö–æÅöG&r#¢6VÆbçFW&Ö–æÅöG&rÀ¢&7F—fU÷Æ–W"#¢6VÆbçÆ–W'5·6VÆbæ7F—fU÷Æ–W%ÒææÖRÀ¢'†6R#¢6VÆbç†6RÀ¢'7FW#¢6VÆbç7FWçfÇVRÀ¢'v–ææW"#¢æöæR–b6VÆbçv–ææW"—2æöæRVÇ6R6VÆbçÆ–W'5·6VÆbçv–ææW%ÒææÖRÀ¢&WF†÷&—FF—fU÷7FFUöf–ævW'&–çB#¢6VÆbæWF†÷&—FF—fU÷7FFUöf–ævW'&–çB‚’À¢&WF†÷&—FF—fU÷7FFUöf–ævW'&–çE÷&V–ÖvR#¢€¢6VÆbæWF†÷&—FF—fU÷7FFUöf–ævW'&–çEöWf–FVæ6R‚¢’À¢''VÆW5öWfVçEöWf–FVæ6R#¢°¢°¢&WfVçEö–B#¢—FVÒæWfVçEö–BÀ¢&WfVçEö7W'6÷"#¢—FVÒæWfVçEö7W'6÷"À¢&¶–æB#¢—FVÒæ¶–æBçfÇVRÀ¢'Æ–W%ö–æFW‚#¢—FVÒçÆ–W%ö–æFW‚À¢'7V&¦V7Eö–G2#¢Æ—7B†—FVÒç7V&¦V7Eö–G2’À¢'6÷W&6Uö–B#¢—FVÒç6÷W&6Uö–BÀ¢'F&vWE÷Æ–W"#¢—FVÒçF&vWE÷Æ–W"À¢&Ö÷VçB#¢—FVÒæÖ÷VçBÀ¢'GW&â#¢—FVÒçGW&âÀ¢'7FW#¢—FVÒç7FWÀ¢&7F—fU÷Æ–W"#¢—FVÒæ7F—fU÷Æ–W"À¢&&GFÆVf–VÆEöWF†÷&—G’#¢°¢²&ö&¦V7Eö–B#¢ö&¦V7Eö–BÂ&6öçG&öÆÆW"#¢6öçG&öÆÆW'Ð¢f÷"ö&¦V7Eö–BÂ6öçG&öÆÆW"–â—FVÒæ&GFÆVf–VÆEöWF†÷&—G¢ÒÀ¢&&GFÆVf–VÆEö6†&7FW&—7F–72#¢°¢°¢&ö&¦V7Eö–B#¢ö&¦V7Eö–BÀ¢&6öçG&öÆÆW"#¢6öçG&öÆÆW"À¢'G—UöÆ–æR#¢G—UöÆ–æRÀ¢Ð¢f÷"ö&¦V7Eö–BÂ6öçG&öÆÆW"ÂG—UöÆ–æR–â—FVÒæ&GFÆVf–VÆEö6†&7FW&—7F–70¢ÒÀ¢&Æ7Eö¶æ÷våö&GFÆVf–VÆB#¢°¢°¢&ö&¦V7Eö–B#¢ö&¦V7Eö–BÀ¢&6öçG&öÆÆW"#¢6öçG&öÆÆW"À¢'G—UöÆ–æR#¢G—UöÆ–æRÀ¢&—5ö7&VGW&R#¢—5ö7&VGW&RÀ¢Ð¢f÷"ö&¦V7Eö–BÂ6öçG&öÆÆW"ÂG—UöÆ–æRÂ—5ö7&VGW&R–â€¢—FVÒæÆ7Eö¶æ÷våö&GFÆVf–VÆ@¢¢ÒÀ¢Ð¢f÷"—FVÒ–â6VÆbå÷'VÆW5öWfVçEöWf–FVæ6P¢ÒÀ¢&6öæf÷&Öæ6R#¢°¢'6VÖçF–5öö67W'&Væ6W2#¢°¢°¢&ö67W'&Væ6Uö–B#¢—FVÒæö67W'&Væ6Uö–BÀ¢'6VÖçF–5ö¶W’#¢—FVÒç6VÖçF–5ö¶W’À¢&÷&6ÆUö–B#¢—FVÒæ÷&6ÆUö–BÀ¢&f6Uö–æFW‚#¢—FVÒæf6Uö–æFW‚À¢&g&vÖVçEö–æFW‚#¢—FVÒæg&vÖVçEö–æFW‚À¢&g&vÖVçEö†6‚#¢—FVÒæg&vÖVçEö†6‚À¢&ö&¦V7Eö–B#¢—FVÒæö&¦V7Eö–BÀ¢&6öçG&öÆÆW"#¢—FVÒæ6öçG&öÆÆW"À¢'¦öæR#¢—FVÒç¦öæRÀ¢&÷&6ÆUög&vÖVçB#¢—FVÒæ÷&6ÆUög&vÖVçBÀ¢&Æ–Ö—FF–öç2#¢Æ—7B†—FVÒæÆ–Ö—FF–öç2’À¢'GW&â#¢—FVÒçGW&âÀ¢'†6R#¢—FVÒç†6RÀ¢'7FW#¢—FVÒç7FWÀ¢'&Vv—7G&F–öåöWfVçEö7W'6÷"#¢—FVÒç&Vv—7G&F–öåöWfVçEö7W'6÷"À¢&6Æ76–f–6F–öâ#¢€¢'&V6†VE÷Vç7W÷'FVB ¢–bç’€¢v—FæW72æö67W'&Væ6Uö–BÓÒ—FVÒæö67W'&Væ6Uö–@¢f÷"v—FæW72–â6VÆbæ÷÷'GVæ—G•÷v—FæW76W0¢¢VÇ6R'&W6VçE÷Vç&V6†VB ¢’À¢Ð¢f÷"—FVÒ–â6VÆbç6VÖçF–5öö67W'&Væ6W0¢ÒÀ¢&÷÷'GVæ—G•÷v—FæW76W2#¢°¢°¢'v—FæW75ö–B#¢—FVÒçv—FæW75ö–BÀ¢&÷÷'GVæ—G•ö¶W’#¢—FVÒæ÷÷'GVæ—G•ö¶W’À¢&ö67W'&Væ6Uö–B#¢—FVÒæö67W'&Væ6Uö–BÀ¢'6VÖçF–5ö¶W’#¢—FVÒç6VÖçF–5ö¶W’À¢&ö&¦V7Eö–B#¢—FVÒæö&¦V7Eö–BÀ¢&6öçG&öÆÆW"#¢—FVÒæ6öçG&öÆÆW"À¢&÷&6ÆUög&vÖVçB#¢—FVÒæ÷&6ÆUög&vÖVçBÀ¢'GW&â#¢—FVÒçGW&âÀ¢'†6R#¢—FVÒç†6RÀ¢'7FW#¢—FVÒç7FWÀ¢&6W6Uö¶–æB#¢—FVÒæ6W6Uö¶–æBÀ¢&6W6Uö–B#¢—FVÒæ6W6Uö–BÀ¢&6W6U÷7V&¦V7Eö–G2#¢Æ—7B†—FVÒæ6W6U÷7V&¦V7Eö–G2’À¢'6÷W&6U÷¦öæR#¢—FVÒç6÷W&6U÷¦öæRÀ¢'6÷W&6Uö6öçG&öÆÆW"#¢—FVÒç6÷W&6Uö6öçG&öÆÆW"À¢&6W6U÷7V&¦V7E÷¦öæW2#¢Æ—7B†—FVÒæ6W6U÷7V&¦V7E÷¦öæW2’À¢&6W6UöWfVçEö¶–æB#¢—FVÒæ6W6UöWfVçEö¶–æBÀ¢&6Æ76–f–6F–öâ#¢—FVÒæ6Æ76–f–6F–öâçfÇVRÀ¢Ð¢f÷"—FVÒ–â6VÆbæ÷÷'GVæ—G•÷v—FæW76W0¢ÒÀ¢&÷÷'GVæ—G•ö6öçFW‡G2#¢°¢°¢&6öçFW‡Eö–B#¢—FVÒæ6öçFW‡Eö–BÀ¢&6öçFW‡Eö¶W’#¢—FVÒæ6öçFW‡Eö¶W’À¢&6öçFW‡Eö¶–æB#¢—FVÒæ6öçFW‡Eö¶–æBÀ¢'GW&â#¢—FVÒçGW&âÀ¢'†6R#¢—FVÒç†6RÀ¢'7FW#¢—FVÒç7FWÀ¢&7F—fU÷Æ–W"#¢—FVÒæ7F—fU÷Æ–W"À¢&6öçG&öÆÆW"#¢—FVÒæ6öçG&öÆÆW"À¢'6÷W&6Uö–B#¢—FVÒç6÷W&6Uö–BÀ¢'7V&¦V7Eö–G2#¢Æ—7B†—FVÒç7V&¦V7Eö–G2’À¢'7V&¦V7E÷¦öæW2#¢Æ—7B†—FVÒç7V&¦V7E÷¦öæW2’À¢&f7G2#¢¶¶W“¢fÇVRf÷"¶W’ÂfÇVR–â—FVÒæf7G7ÒÀ¢&WfVçEö–B#¢—FVÒæWfVçEö–BÀ¢'7F6µöö&¦V7Eö–B#¢—FVÒç7F6µöö&¦V7Eö–BÀ¢'7FFUöf–ævW'&–çB#¢—FVÒç7FFUöf–ævW'&–çBÀ¢Ð¢f÷"—FVÒ–â6VÆbæ÷÷'GVæ—G•ö6öçFW‡G0¢ÒÀ¢'7F÷÷&V6÷&G2#¢°¢°¢'7F÷ö–B#¢—FVÒç7F÷ö–BÀ¢&¶–æB#¢—FVÒæ¶–æBÀ¢'GW&â#¢—FVÒçGW&âÀ¢'†6R#¢—FVÒç†6RÀ¢'7FW#¢—FVÒç7FWÀ¢&&Vf÷&Uöf–ævW'&–çB#¢—FVÒæ&Vf÷&Uöf–ævW'&–çBÀ¢&gFW%öf–ævW'&–çB#¢—FVÒægFW%öf–ævW'&–çBÀ¢&FWF–Â#¢—FVÒæFWF–ÂÀ¢Ð¢f÷"—FVÒ–â6VÆbæ6öæf÷&Öæ6U÷7F÷÷&V6÷&G0¢ÒÀ¢&W†V7WFVE÷&VfW&Væ6W2#¢6VÆbåöW†V7WFVEö6öæf÷&Öæ6U÷&VfW&Væ6W2‚’À¢ÒÀ¢&Ö–ÆÅ÷F‡&VUöWf–FVæ6R#¢6VÆbæÖ–ÆÅ÷F‡&VU÷6æ6†÷EöWf–FVæ6R‚’À¢&·&æu÷&Vf–ÆÅöWf–FVæ6R#¢6VÆbæ·&æu÷&Vf–ÆÅ÷6æ6†÷EöWf–FVæ6R‚’À¢&§W'•÷&–uöWf–FVæ6R#¢6VÆbæ§W'•÷&–u÷6æ6†÷EöWf–FVæ6R‚’À¢'f–v–ÆçFUöWf–FVæ6R#¢6VÆbçf–v–ÆçFU÷6æ6†÷EöWf–FVæ6R‚’À¢&fööE÷6V&6…öWf–FVæ6R#¢6VÆbæfööE÷6V&6…÷6æ6†÷EöWf–FVæ6R‚’À¢'&ær#¢°¢'6VVB#¢6VÆbç&ærç6VVBÀ¢'7FFUöF–vW7B#¢6VÆbç&ærç7FFUöF–vW7BÀ¢'&V6÷&G2#¢°¢°¢'6WVVæ6R#¢&V6÷&Bç6WVVæ6RÀ¢&FöÖ–â#¢&V6÷&BæFöÖ–âÀ¢&÷W&F–öâ#¢&V6÷&Bæ÷W&F–öâÀ¢'&W7VÇB#¢€¢Æ—7B‡&V6÷&Bç&W7VÇB¢–b—6–ç7Fæ6R‡&V6÷&Bç&W7VÇBÂGWÆR¢VÇ6R&V6÷&Bç&W7VÇ@¢’À¢'7FFUö&Vf÷&R#¢&V6÷&Bç7FFUö&Vf÷&RÀ¢'7FFUögFW"#¢&V6÷&Bç7FFUögFW"À¢Ð¢f÷"&V6÷&B–â6VÆbç&ærç&V6÷&G0¢ÒÀ¢ÒÀ¢'7F6²#¢°¢€¢°¢&ö&¦V7Eö–B#¢VçG'’æö&¦V7Eö–BÀ¢&¶–æB#¢'7VÆÂ"À¢&6&B#¢VçG'’æ6&BææÖRÀ¢&÷væW"#¢VçG'’æ÷væW"À¢&6öçG&öÆÆW"#¢VçG'’æ6öçG&öÆÆW"À¢&67Eö¶–æB#¢VçG'’æ67Eö¶–æBçfÇVRÀ¢'F&vWEö–B#¢VçG'’çF&vWEö–BÀ¢¢¢‡²'F&vWEö–G2#¢Æ—7B†VçG'’çF&vWEö–G2—Ò–bVçG'’çF&vWEö–G2VÇ6R·Ò’À¢'6÷W&6U÷F&vWEö–B#¢VçG'’ç6÷W&6U÷F&vWEö–BÀ¢&ÖöFUög&vÖVçB#¢VçG'’æÖöFUög&vÖVçBÀ¢&¶–6¶W%÷67&–f–6Uö–B#¢VçG'’æ¶–6¶W%÷67&–f–6Uö–BÀ¢'6æVµ÷&WGW&æVEöGF6¶W%ö–B#¢VçG'’ç6æVµ÷&WGW&æVEöGF6¶W%ö–BÀ¢'6æVµ÷&WGW&æVEö†æEö–B#¢VçG'’ç6æVµ÷&WGW&æVEö†æEö–BÀ¢'6æVµöFVfVæF–æu÷Æ–W"#¢VçG'’ç6æVµöFVfVæF–æu÷Æ–W"À¢'6æVµö÷&6ÆUög&vÖVçB#¢VçG'’ç6æVµö÷&6ÆUög&vÖVçBÀ¢'6æVµöÖæ÷6÷W&6Uö–G2#¢Æ—7B†VçG'’ç6æVµöÖæ÷6÷W&6Uö–G2’À¢Ð¢–b—6–ç7Fæ6R†VçG'’Â7F6´ö&¦V7B¢VÇ6R°¢&ö&¦V7Eö–B#¢VçG'’æö&¦V7Eö–BÀ¢&¶–æB#¢&7F—fFVEö&–Æ—G’"À¢'6÷W&6R#¢VçG'’ç6÷W&6Uö6&BææÖRÀ¢'6÷W&6Uö–B#¢VçG'’ç6÷W&6Uö–BÀ¢&6öçG&öÆÆW"#¢VçG'’æ6öçG&öÆÆW"À¢&÷&6ÆUög&vÖVçB#¢VçG'’æ÷&6ÆUög&vÖVçBÀ¢'F&vWEö–G2#¢Æ—7B†VçG'’çF&vWEö–G2’À¢&6†ö–6Uö–G2#¢Æ—7B†VçG'’æ6†ö–6Uö–G2’À¢Ð¢–b—6–ç7Fæ6R†VçG'’Â7F—fFVD&–Æ—G”ö&¦V7B¢VÇ6R°¢&ö&¦V7Eö–B#¢VçG'’æö&¦V7Eö–BÀ¢&¶–æB#¢'G&–vvW&VEö&–Æ—G’"À¢¢¢€¢²'F&vWEö–B#¢VçG'’çF&vWEö–GÐ¢–bVçG'’æVffV7@¢–â°¢G&–vvW$VffV7BäUD%õDõ5ETâÀ¢G&–vvW$VffV7Bäu$åDTEô4ôÔ$EõTåDôt”âÀ¢G&–vvW$VffV7BäUT•ÔTåEõ5T%E•UôTåE%•ôED4‚À¢Ð¢VÇ6R·Ð¢’À¢¢¢€¢²&w&çE÷6÷W&6Uö–B#¢6VÆbå÷G&–vvW'5¶VçG'’çG&–vvW%ö–EÒæw&çE÷6÷W&6Uö–GÐ¢–bVçG'’æVffV7B—2G&–vvW$VffV7Bäu$åDTEô4ôÔ$EõTåDôt”à¢VÇ6R·Ð¢’À¢'6÷W&6R#¢VçG'’ç6÷W&6Uö6&BææÖRÀ¢'6÷W&6Uö–B#¢VçG'’ç6÷W&6Uö–BÀ¢&6öçG&öÆÆW"#¢VçG'’æ6öçG&öÆÆW"À¢&VffV7B#¢VçG'’æVffV7BçfÇVRÀ¢&WfVçEö–B#¢VçG'’æWfVçBæWfVçEö–BÀ¢'G&–vvW%ö–B#¢VçG'’çG&–vvW%ö–BÀ¢'F&vWEö–G2#¢Æ—7B†VçG'’çF&vWEö–G2’À¢Ð¢¢f÷"VçG'’–â6VÆbç7F6°¢ÒÀ¢'&–÷&—G’#¢€¢æöæP¢–b6VÆbç&–÷&—G•÷7FFR—2æöæP¢VÇ6R°¢&Wö6‚#¢6VÆbç&–÷&—G•÷7FFRæWö6‚À¢'Æ–W%ö–æFW‚#¢6VÆbç&–÷&—G•÷7FFRçÆ–W%ö–æFW‚À¢&6öç6V7WF—fU÷76W2#¢Æ—7B‡6VÆbç&–÷&—G•÷7FFRæ6öç6V7WF—fU÷76W2’À¢'&W6öÇWF–öå÷VæF–ær#¢6VÆbç&–÷&—G•÷7FFRç&W6öÇWF–öå÷VæF–ærÀ¢Ð¢’À¢'VæF–æu÷G&–vvW'2#¢·G&–vvW"çG&–vvW%ö–Bf÷"G&–vvW"–â6VÆbçVæF–æu÷G&–vvW'5ÒÀ¢'7GVåö†—7F÷'’#¢°¢²&WfVçEö7W'6÷"#¢7W'6÷"Â'&V6÷&B#¢F–7B‡&V6÷&B—Ð¢f÷"7W'6÷"Â&V6÷&B–â6VÆbå÷7GVåö†—7F÷'¢ÒÀ¢'67'’#¢°¢°¢&WfVçEö–B#¢—FVÒæWfVçEö–BÀ¢'Æ–W%ö–æFW‚#¢—FVÒçÆ–W%ö–æFW‚À¢'&WVW7FVB#¢—FVÒç&WVW7FVBÀ¢&–ç7V7FVEö–G2#¢Æ—7B†—FVÒæ–ç7V7FVEö–G2’À¢'F÷ö–G2#¢Æ—7B†—FVÒçF÷ö–G2’À¢&&÷GFöÕö–G2#¢Æ—7B†—FVÒæ&÷GFöÕö–G2’À¢'6÷W&6Uö6&B#¢—FVÒç6÷W&6Uö6&BÀ¢'6÷W&6Uö–B#¢—FVÒç6÷W&6Uö–BÀ¢&÷&6ÆUög&vÖVçB#¢—FVÒæ÷&6ÆUög&vÖVçBÀ¢Ð¢f÷"—FVÒ–â6VÆbç67'•öWf–FVæ6P¢ÒÀ¢&WF%öG&–åöv–å÷67'’#¢°¢°¢&WfVçEö–B#¢—FVÒæWfVçEö–BÀ¢'7F6µöö&¦V7Eö–B#¢—FVÒç7F6µöö&¦V7Eö–BÀ¢'6÷W&6Uö–B#¢—FVÒç6÷W&6Uö–BÀ¢'6÷W&6Uö6&B#¢—FVÒç6÷W&6Uö6&BÀ¢&6öçG&öÆÆW"#¢—FVÒæ6öçG&öÆÆW"À¢&÷öæVçB#¢—FVÒæ÷öæVçBÀ¢&÷&6ÆUög&vÖVçB#¢—FVÒæ÷&6ÆUög&vÖVçBÀ¢'GW&â#¢—FVÒçGW&âÀ¢'7FW#¢—FVÒç7FWÀ¢&÷öæVçEöÆ–fUö&Vf÷&R#¢—FVÒæ÷öæVçEöÆ–fUö&Vf÷&RÀ¢&÷öæVçEöÆ–fUögFW"#¢—FVÒæ÷öæVçEöÆ–fUögFW"À¢&6öçG&öÆÆW%öÆ–fUö&Vf÷&R#¢—FVÒæ6öçG&öÆÆW%öÆ–fUö&Vf÷&RÀ¢&6öçG&öÆÆW%öÆ–fUögFW"#¢—FVÒæ6öçG&öÆÆW%öÆ–fUögFW"À¢'67'•öWfVçEö–B#¢—FVÒç67'•öWfVçEö–BÀ¢'FW&Ö–æÅögFW%öÆ–fUöÆ÷72#¢—FVÒçFW&Ö–æÅögFW%öÆ–fUöÆ÷72À¢Ð¢f÷"—FVÒ–â6VÆbæWF%öG&–åöv–å÷67'•öWf–FVæ6P¢ÒÀ¢&6öÖ&EöFÖvR#¢°¢'7FWö¶–æB#¢6VÆbåö6öÖ&EöFÖvU÷7FWö¶–æBçfÇVRÀ¢'6WVVæ6R#¢6VÆbåö6öÖ&EöFÖvU÷7FWöçVÖ&W"À¢'F÷FÅ÷7FW2#¢6VÆbåö6öÖ&EöFÖvU÷F÷FÅ÷7FW2À¢&f—'7E÷VÆ–f–VEö–G2#¢Æ—7B‡6VÆbåöf—'7EöFÖvU÷VÆ–f–VEö–G2’À¢'&VwVÆ%ö–æ—F–Åö–G2#¢Æ—7B‡6VÆbå÷&VwVÆ%öFÖvUö–æ—F–Åö–G2’À¢&Wf–FVæ6R#¢°¢°¢&¶–æB#¢—FVÒæ¶–æBçfÇVRÀ¢'6WVVæ6R#¢—FVÒç6WVVæ6RÀ¢'F÷FÅ÷7FW2#¢—FVÒçF÷FÅ÷7FW2À¢&76–væÖVçG2#¢°¢°¢'6÷W&6Uö–B#¢76–væÖVçBç6÷W&6Uö–BÀ¢'F&vWEö–B#¢76–væÖVçBçF&vWEö–BÀ¢'F&vWE÷Æ–W"#¢76–væÖVçBçF&vWE÷Æ–W"À¢&Ö÷VçB#¢76–væÖVçBæÖ÷VçBÀ¢'&öÆR#¢76–væÖVçBç&öÆRÀ¢'G&×ÆR#¢76–væÖVçBçG&×ÆRÀ¢&ÆWF†Å÷&WV—&VB#¢76–væÖVçBæÆWF†Å÷&WV—&VBÀ¢Ð¢f÷"76–væÖVçB–â—FVÒæ76–væÖVçG0¢ÒÀ¢'&VÖ÷fVEö&Vf÷&UöæW‡E÷7FW#¢Æ—7B†—FVÒç&VÖ÷fVEö&Vf÷&UöæW‡E÷7FW’À¢'G&×ÆU÷&W7VÇG2#¢°¢°¢&GF6¶W%ö–B#¢&W7VÇBæGF6¶W%ö–BÀ¢&&Æö6¶W%ö–B#¢&W7VÇBæ&Æö6¶W%ö–BÀ¢&FÖvU÷7FW#¢&W7VÇBæFÖvU÷7FWçfÇVRÀ¢&GF6¶W%÷÷vW"#¢&W7VÇBæGF6¶W%÷÷vW"À¢&&Æö6¶W%÷F÷Vv†æW72#¢&W7VÇBæ&Æö6¶W%÷F÷Vv†æW72À¢&&Æö6¶W%öÖ&¶VEöFÖvUö&Vf÷&R#¢€¢&W7VÇBæ&Æö6¶W%öÖ&¶VEöFÖvUö&Vf÷&P¢’À¢&ÆWF†Å÷&WV—&VB#¢&W7VÇBæÆWF†Å÷&WV—&VBÀ¢&&Æö6¶W%öFÖvUö76–væVB#¢&W7VÇBæ&Æö6¶W%öFÖvUö76–væVBÀ¢'Æ–W%öFÖvUö76–væVB#¢&W7VÇBçÆ–W%öFÖvUö76–væVBÀ¢&FVfVæF–æu÷Æ–W"#¢&W7VÇBæFVfVæF–æu÷Æ–W"À¢&FVfVæF–æuöÆ–fUö&Vf÷&R#¢&W7VÇBæFVfVæF–æuöÆ–fUö&Vf÷&RÀ¢&FVfVæF–æuöÆ–fUögFW"#¢&W7VÇBæFVfVæF–æuöÆ–fUögFW"À¢&&Æö6¶W%öÖ&¶VEöFÖvUögFW"#¢‡&W7VÇBæ&Æö6¶W%öÖ&¶VEöFÖvUögFW"’À¢&&Æö6¶W%÷7W'f—fVB#¢&W7VÇBæ&Æö6¶W%÷7W'f—fVBÀ¢'6÷W&6UöFVF‡F÷V6‚#¢&W7VÇBç6÷W&6UöFVF‡F÷V6‚À¢Ð¢f÷"&W7VÇB–â—FVÒçG&×ÆU÷&W7VÇG0¢ÒÀ¢Ð¢f÷"—FVÒ–â6VÆbæ6öÖ&EöFÖvUöWf–FVæ6P¢ÒÀ¢ÒÀ¢&Æ–fVÆ–æ²#¢°¢°¢&WfVçEö–B#¢—FVÒæWfVçEö–BÀ¢'6÷W&6Uö–B#¢—FVÒç6÷W&6Uö–BÀ¢&6öçG&öÆÆW"#¢—FVÒæ6öçG&öÆÆW"À¢&Ö÷VçB#¢—FVÒæÖ÷VçBÀ¢&6öÖ&B#¢—FVÒæ6öÖ&BÀ¢&FÖvU÷7FW#¢„æöæR–b—FVÒæFÖvU÷7FW—2æöæRVÇ6R—FVÒæFÖvU÷7FWçfÇVR’À¢'F&vWEö–G2#¢Æ—7B†—FVÒçF&vWEö–G2’À¢'F&vWE÷Æ–W'2#¢Æ—7B†—FVÒçF&vWE÷Æ–W'2’À¢&Æ–fUö&Vf÷&R#¢—FVÒæÆ–fUö&Vf÷&RÀ¢&Æ–fUögFW"#¢—FVÒæÆ–fUögFW"À¢Ð¢f÷"—FVÒ–â6VÆbæÆ–fVÆ–æµöWf–FVæ6P¢ÒÀ¢&†æEö&÷GFöÕöG&r#¢°¢°¢&WfVçEö–B#¢—FVÒæWfVçEö–BÀ¢'Æ–W%ö–æFW‚#¢—FVÒçÆ–W%ö–æFW‚À¢'6÷W&6Uö–B#¢—FVÒç6÷W&6Uö–BÀ¢&÷&6ÆUög&vÖVçB#¢—FVÒæ÷&6ÆUög&vÖVçBÀ¢&öffW&VEö6†ö–6Uö–G2#¢Æ—7B†—FVÒæöffW&VEö6†ö–6Uö–G2’À¢'&Uö†æEö–G2#¢Æ—7B†—FVÒç&Uö†æEö–G2’À¢'&UöÆ–'&'•ö–G2#¢Æ—7B†—FVÒç&UöÆ–'&'•ö–G2’À¢'6VÆV7FVEö†æEö–B#¢—FVÒç6VÆV7FVEö†æEö–BÀ¢&Æ–'&'•ö&÷GFöÕö–B#¢—FVÒæÆ–'&'•ö&÷GFöÕö–BÀ¢&Ö÷fVÖVçE÷7V66VVFVB#¢—FVÒæÖ÷fVÖVçE÷7V66VVFVBÀ¢&6öæF—F–öæÅöG&u÷W&f÷&ÖVB#¢—FVÒæ6öæF—F–öæÅöG&u÷W&f÷&ÖVBÀ¢&G&våöÆ–'&'•ö–B#¢—FVÒæG&våöÆ–'&'•ö–BÀ¢&G&våö†æEö–B#¢—FVÒæG&våö†æEö–BÀ¢'÷7Eö†æEö–G2#¢Æ—7B†—FVÒç÷7Eö†æEö–G2’À¢'÷7EöÆ–'&'•ö–G2#¢Æ—7B†—FVÒç÷7EöÆ–'&'•ö–G2’À¢&FV6Æ–æVB#¢—FVÒæFV6Æ–æVBÀ¢Ð¢f÷"—FVÒ–â6VÆbæ†æEö&÷GFöÕöG&uöWf–FVæ6P¢ÒÀ¢&F—66&EöG&r#¢°¢°¢&WfVçEö–B#¢—FVÒæWfVçEö–BÀ¢'Æ–W%ö–æFW‚#¢—FVÒçÆ–W%ö–æFW‚À¢&GF6µ÷&÷fVææ6R#¢°¢&WfVçEö–B#¢—FVÒæGF6µ÷&÷fVææ6RæWfVçEö–BÀ¢&WfVçEö¶–æB#¢—FVÒæGF6µ÷&÷fVææ6RæWfVçEö¶–æBçfÇVRÀ¢&WfVçE÷Æ–W%ö–æFW‚#¢—FVÒæGF6µ÷&÷fVææ6RæWfVçE÷Æ–W%ö–æFW‚À¢'7V&¦V7Eö–G2#¢Æ—7B†—FVÒæGF6µ÷&÷fVææ6Rç7V&¦V7Eö–G2’À¢&GF6¶W%ö–B#¢—FVÒæGF6µ÷&÷fVææ6RæGF6¶W%ö–BÀ¢&6öçG&öÆÆW"#¢—FVÒæGF6µ÷&÷fVææ6Ræ6öçG&öÆÆW"À¢'GW&â#¢—FVÒæGF6µ÷&÷fVææ6RçGW&âÀ¢'7FW#¢—FVÒæGF6µ÷&÷fVææ6Rç7FWÀ¢&7F—fU÷Æ–W"#¢—FVÒæGF6µ÷&÷fVææ6Ræ7F—fU÷Æ–W"À¢ÒÀ¢'7F6µöö&¦V7Eö–B#¢—FVÒç7F6µöö&¦V7Eö–BÀ¢'6÷W&6Uö–B#¢—FVÒç6÷W&6Uö–BÀ¢&÷&6ÆUög&vÖVçB#¢—FVÒæ÷&6ÆUög&vÖVçBÀ¢&öffW&VEö6†ö–6Uö–G2#¢Æ—7B†—FVÒæöffW&VEö6†ö–6Uö–G2’À¢'&Uö†æEö–G2#¢Æ—7B†—FVÒç&Uö†æEö–G2’À¢'&UöÆ–'&'•ö–G2#¢Æ—7B†—FVÒç&UöÆ–'&'•ö–G2’À¢'&Uöw&fW–&Eö–G2#¢Æ—7B†—FVÒç&Uöw&fW–&Eö–G2’À¢'6VÆV7FVEö†æEö–B#¢—FVÒç6VÆV7FVEö†æEö–BÀ¢&F—66&FVEöw&fW–&Eö–B#¢—FVÒæF—66&FVEöw&fW–&Eö–BÀ¢&Ö÷fVÖVçE÷7V66VVFVB#¢—FVÒæÖ÷fVÖVçE÷7V66VVFVBÀ¢&6öæF—F–öæÅöG&u÷W&f÷&ÖVB#¢—FVÒæ6öæF—F–öæÅöG&u÷W&f÷&ÖVBÀ¢'&UöG&u÷F÷ö–B#¢—FVÒç&UöG&u÷F÷ö–BÀ¢&G&våö†æEö–B#¢—FVÒæG&våö†æEö–BÀ¢'÷7Eö†æEö–G2#¢Æ—7B†—FVÒç÷7Eö†æEö–G2’À¢'÷7EöÆ–'&'•ö–G2#¢Æ—7B†—FVÒç÷7EöÆ–'&'•ö–G2’À¢'÷7Eöw&fW–&Eö–G2#¢Æ—7B†—FVÒç÷7Eöw&fW–&Eö–G2’À¢&FV6Æ–æVB#¢—FVÒæFV6Æ–æVBÀ¢Ð¢f÷"—FVÒ–â6VÆbæF—66&EöG&uöWf–FVæ6P¢ÒÀ¢&7F—fFVEö&–Æ—F–W2#¢°¢°¢'7F6µöö&¦V7Eö–B#¢—FVÒç7F6µöö&¦V7Eö–BÀ¢'6÷W&6Uö–B#¢—FVÒç6÷W&6Uö–BÀ¢&6öçG&öÆÆW"#¢—FVÒæ6öçG&öÆÆW"À¢&÷&6ÆUög&vÖVçB#¢—FVÒæ÷&6ÆUög&vÖVçBÀ¢&Öæ÷6÷W&6Uö–G2#¢Æ—7B†—FVÒæÖæ÷6÷W&6Uö–G2’À¢'F÷6÷W&6R#¢—FVÒçF÷6÷W&6RÀ¢'&W6öÇfVB#¢—FVÒç&W6öÇfVBÀ¢&6÷7E÷F&vWEö–B#¢—FVÒæ6÷7E÷F&vWEö–BÀ¢Ð¢f÷"—FVÒ–â6VÆbæ7F—fF–öåöWf–FVæ6P¢ÒÀ¢&fööEö7F—fF–öç2#¢°¢°¢'6÷W&6Uö–B#¢—FVÒç6÷W&6Uö–BÀ¢'6÷W&6UöæÖR#¢—FVÒç6÷W&6UöæÖRÀ¢'6÷W&6U÷G—UöÆ–æR#¢—FVÒç6÷W&6U÷G—UöÆ–æRÀ¢'6÷W&6Uö÷væW"#¢—FVÒç6÷W&6Uö÷væW"À¢&6öçG&öÆÆW"#¢—FVÒæ6öçG&öÆÆW"À¢'6÷W&6U÷v5÷Fö¶Vâ#¢—FVÒç6÷W&6U÷v5÷Fö¶VâÀ¢&÷&6ÆUög&vÖVçB#¢—FVÒæ÷&6ÆUög&vÖVçBÀ¢'GW&â#¢—FVÒçGW&âÀ¢'7FW#¢—FVÒç7FWÀ¢'6÷W&6U÷¦öæUö&Vf÷&R#¢—FVÒç6÷W&6U÷¦öæUö&Vf÷&RÀ¢&Öæ÷&WV—&VÖVçB#¢°¢&vVæW&–2#¢—FVÒæÖæ÷&WV—&VÖVçBævVæW&–2À¢&6öÆ÷&VB#¢Æ—7B†—FVÒæÖæ÷&WV—&VÖVçBæ6öÆ÷&VB’À¢ÒÀ¢&Öæ÷6÷W&6Uö–G2#¢Æ—7B†—FVÒæÖæ÷6÷W&6Uö–G2’À¢'6÷W&6U÷FVEö&Vf÷&R#¢—FVÒç6÷W&6U÷FVEö&Vf÷&RÀ¢'F÷–B#¢—FVÒçF÷–BÀ¢'67&–f–6U÷–B#¢—FVÒç67&–f–6U÷–BÀ¢'67&–f–6VEöFW7F–æF–öåö–B#¢—FVÒç67&–f–6VEöFW7F–æF–öåö–BÀ¢'67&–f–6VEöFW7F–æF–öå÷¦öæR#¢—FVÒç67&–f–6VEöFW7F–æF–öå÷¦öæRÀ¢'7F6µöö&¦V7Eö–B#¢—FVÒç7F6µöö&¦V7Eö–BÀ¢'&–÷&—G•öWö6‚#¢—FVÒç&–÷&—G•öWö6‚À¢'&–÷&—G•÷76W2#¢Æ—7B†—FVÒç&–÷&—G•÷76W2’À¢'&W6öÇWF–öå÷W&Ö—GFVB#¢—FVÒç&W6öÇWF–öå÷W&Ö—GFVBÀ¢'&W6öÇfVB#¢—FVÒç&W6öÇfVBÀ¢&Æ–fUö&Vf÷&R#¢—FVÒæÆ–fUö&Vf÷&RÀ¢&Æ–fUögFW"#¢—FVÒæÆ–fUögFW"À¢&Ö÷VçEöv–æVB#¢—FVÒæÖ÷VçEöv–æVBÀ¢&f–æÅ÷6÷W&6UöF—7÷6—F–öâ#¢—FVÒæf–æÅ÷6÷W&6UöF—7÷6—F–öâÀ¢Ð¢f÷"—FVÒ–â6VÆbæfööEö7F—fF–öåöWf–FVæ6P¢ÒÀ¢'6æV²#¢°¢°¢&6&B#¢—FVÒæ6&EöæÖRÀ¢&†æEöö&¦V7Eö–B#¢—FVÒæ†æEöö&¦V7Eö–BÀ¢&6öçG&öÆÆW"#¢—FVÒæ6öçG&öÆÆW"À¢'GW&â#¢—FVÒçGW&âÀ¢'7FW#¢—FVÒç7FWÀ¢&÷&6ÆUög&vÖVçB#¢—FVÒæ÷&6ÆUög&vÖVçBÀ¢&Öæ÷&WV—&VÖVçB#¢°¢&vVæW&–2#¢—FVÒæÖæ÷&WV—&VÖVçBævVæW&–2À¢&6öÆ÷&VB#¢Æ—7B†—FVÒæÖæ÷&WV—&VÖVçBæ6öÆ÷&VB’À¢ÒÀ¢&Öæ÷6÷W&6Uö–G2#¢Æ—7B†—FVÒæÖæ÷6÷W&6Uö–G2’À¢'&WGW&æVEöGF6¶W%ö–B#¢—FVÒç&WGW&æVEöGF6¶W%ö–BÀ¢'&WGW&æVEö†æEö–B#¢—FVÒç&WGW&æVEö†æEö–BÀ¢&FVfVæF–æu÷Æ–W"#¢—FVÒæFVfVæF–æu÷Æ–W"À¢'7F6µöö&¦V7Eö–B#¢—FVÒç7F6µöö&¦V7Eö–BÀ¢'&–÷&—G•öWö6‚#¢—FVÒç&–÷&—G•öWö6‚À¢'&W6öÇfVEöö&¦V7Eö–B#¢—FVÒç&W6öÇfVEöö&¦V7Eö–BÀ¢&VçFW&VE÷FVB#¢—FVÒæVçFW&VE÷FVBÀ¢&VçFW&VEöGF6¶–ær#¢—FVÒæVçFW&VEöGF6¶–ærÀ¢¢¢€¢°¢'6÷W&6U÷¦öæR#¢—FVÒç6÷W&6U÷¦öæRÀ¢'W&Ö—76–öå÷6÷W&6Uö–B#¢—FVÒçW&Ö—76–öå÷6÷W&6Uö–BÀ¢Ð¢–b—FVÒç6÷W&6U÷¦öæRÓÒ&w&fW–&B ¢VÇ6R·Ð¢’À¢Ð¢f÷"—FVÒ–â6VÆbç6æVµöWf–FVæ6P¢ÒÀ¢'Æ–W'2#¢°¢°¢&æÖR#¢ææÖRÀ¢&Æ–fR#¢æÆ–fRÀ¢&Æ–'&'’#¢ÆVâ‡æÆ–'&'’’À¢&Æ–'&'•öö&¦V7Eö–G2#¢¶6&Bæö&¦V7Eö–Bf÷"6&B–âæÆ–'&'•ÒÀ¢&†æB#¢¶2ææÖRf÷"2–âæ†æEÒÀ¢&†æEöö&¦V7Eö–G2#¢¶6&Bæö&¦V7Eö–Bf÷"6&B–âæ†æEÒÀ¢&&GFÆVf–VÆB#¢°¢°¢&ö&¦V7Eö–B#¢‚æö&¦V7Eö–BÀ¢&6&B#¢°¢&æÖR#¢‚æ6&BææÖRÀ¢&Öæö6÷7B#¢‚æ6&BæÖæö6÷7BÀ¢&Öæ÷fÇVR#¢‚æ6&BæÖæ÷fÇVRÀ¢'G—UöÆ–æR#¢‚æ6&BçG—UöÆ–æRÀ¢&÷&6ÆU÷FW‡B#¢‚æ6&Bæ÷&6ÆU÷FW‡BÀ¢'÷vW"#¢‚æ6&Bç÷vW"À¢'F÷Vv†æW72#¢‚æ6&BçF÷Vv†æW72À¢&¶W—v÷&G2#¢Æ—7B‡‚æ6&Bæ¶W—v÷&G2’À¢ÒÀ¢&÷væW"#¢‚æ÷væW"À¢&6öçG&öÆÆW"#¢‚æ6öçG&öÆÆW"À¢'¦öæR#¢‚ç¦öæRÀ¢&—5÷Fö¶Vâ#¢‚æ—5÷Fö¶VâÀ¢&WfÇVFVE÷G—UöÆ–æR#¢‚çG—UöÆ–æRÀ¢&6öÆ÷'2#¢€¢Æ—7B‡‚æ6&Bæ6öÆ÷'2’–b—6–ç7Fæ6R‡‚æ6&BÂFö¶VäFVf–æ—F–öâ’VÇ6RµÐ¢’À¢'FVB#¢‚çFVBÀ¢'7VÖÖöæ–æu÷6–6²#¢‚ç7VÖÖöæ–æu÷6–6²À¢&VçFW&VEö&GFÆVf–VÆE÷GW&â#¢‚æVçFW&VEö&GFÆVf–VÆE÷GW&âÀ¢&VçFW&VE÷VæFW%ö6öçG&öÆÆW"#¢‚æVçFW&VE÷VæFW%ö6öçG&öÆÆW"À¢¢¢‡²&6Æ75öÆWfVÂ#¢‚æ6Æ75öÆWfVÇÒ–b‚æ6Æ75öÆWfVÂ—2æ÷BæöæRVÇ6R·Ò’À¢¢¢‡²&GF6†VE÷Fò#¢‚æGF6†VE÷F÷Ò–b‚æGF6†VE÷Fò—2æ÷BæöæRVÇ6R·Ò’À¢&VçFW&VE÷F–ÖW7F×#¢Æ—7B‡‚æVçFW&VE÷F–ÖW7F×’À¢&GF6†ÖVçE÷F–ÖW7F×#¢Æ—7B‡‚æGF6†ÖVçE÷F–ÖW7F×’À¢&&–Æ—G•öÆ÷75÷F–ÖW7F×#¢‚æ&–Æ—G•öÆ÷75÷F–ÖW7F×À¢&W&ö7&VGW&U÷G—R#¢‚æW&ö7&VGW&U÷G—RÀ¢&W&öVffV7Eö–G2#¢Æ—7B‡‚æW&öVffV7Eö–G2’À¢&W&öGF6µ÷&W7G&–7F–öç2#¢Æ—7B‡‚æW&öGF6µ÷&W7G&–7F–öç2’À¢&FÖvR#¢‚æFÖvRÀ¢&FVF‡F÷V6…öFÖvR#¢‚æFVF‡F÷V6…öFÖvRÀ¢&6÷VçFW'2#¢F–7B‡‚æ6÷VçFW'2’À¢&öæ6U÷W%÷GW&åö7F—fF–öç2#¢F–7B‡‚æöæ6U÷W%÷GW&åö7F—fF–öç2’À¢'EöÖöF–f–W'2#¢°¢°¢'÷vW"#¢ÖöF–f–W"ç÷vW"À¢'F÷Vv†æW72#¢ÖöF–f–W"çF÷Vv†æW72À¢&GW&F–öâ#¢ÖöF–f–W"æGW&F–öâÀ¢'6÷W&6Uö6&B#¢ÖöF–f–W"ç6÷W&6Uö6&BÀ¢&÷&6ÆUög&vÖVçB#¢ÖöF–f–W"æ÷&6ÆUög&vÖVçBÀ¢&7&VFVE÷GW&â#¢ÖöF–f–W"æ7&VFVE÷GW&âÀ¢&7&VFVEö÷&FW"#¢ÖöF–f–W"æ7&VFVEö÷&FW"À¢&FW&—fVE÷7FF–2#¢ÖöF–f–W"æFW&—fVE÷7FF–2À¢¢¢€¢²'6÷W&6Uöö&¦V7Eö–B#¢ÖöF–f–W"ç6÷W&6Uöö&¦V7Eö–GÐ¢–bÖöF–f–W"ç6÷W&6Uöö&¦V7Eö–B—2æ÷BæöæP¢VÇ6R·Ð¢’À¢Ð¢f÷"ÖöF–f–W"–â‚çEöÖöF–f–W'0¢ÒÀ¢&6†&7FW&—7F–5öVffV7G2#¢°¢°¢&VffV7Eö–B#¢VffV7BæVffV7Eö–BÀ¢&Æ–W"#¢VffV7BæÆ–W"çfÇVRÀ¢'7V&Æ–W"#¢€¢æöæR–bVffV7Bç7V&Æ–W"—2æöæRVÇ6RVffV7Bç7V&Æ–W"çfÇVP¢’À¢&÷W&F–öâ#¢VffV7Bæ÷W&F–öâçfÇVRÀ¢'÷vW"#¢VffV7Bç÷vW"À¢'F÷Vv†æW72#¢VffV7BçF÷Vv†æW72À¢'F–ÖW7F×#¢Æ—7B†VffV7BçF–ÖW7F×’À¢&FWVæG5ööâ#¢Æ—7B†VffV7BæFWVæG5ööâ’À¢'6÷W&6Uö6&B#¢VffV7Bç6÷W&6Uö6&BÀ¢¢¢€¢²&GW&F–öâ#¢VffV7BæGW&F–öçÐ¢–bVffV7BæGW&F–öâÒ'W'6—7FVçB ¢VÇ6R·Ð¢’À¢Ð¢f÷"VffV7B–â‚æ6†&7FW&—7F–5öVffV7G0¢ÒÀ¢¢¢€¢°¢'FV×÷&'•÷G—UöVffV7G2#¢°¢°¢&FFVE÷G—W2#¢Æ—7B†VffV7BæFFVE÷G—W2’À¢&GW&F–öâ#¢VffV7BæGW&F–öâÀ¢'6÷W&6Uö–B#¢VffV7Bç6÷W&6Uö–BÀ¢&÷&6ÆUög&vÖVçB#¢VffV7Bæ÷&6ÆUög&vÖVçBÀ¢'F–ÖW7F×#¢Æ—7B†VffV7BçF–ÖW7F×’À¢¢¢€¢²&FFVE÷7V'G—W2#¢Æ—7B†VffV7BæFFVE÷7V'G—W2—Ð¢–bVffV7BæFFVE÷7V'G—W0¢VÇ6R·Ð¢’À¢Ð¢f÷"VffV7B–â‚çFV×÷&'•÷G—UöVffV7G0¢Ð¢Ð¢–b‚çFV×÷&'•÷G—UöVffV7G0¢VÇ6R·Ð¢’À¢'FV×÷&'•ö¶W—v÷&EöVffV7G2#¢°¢°¢&¶W—v÷&B#¢VffV7Bæ¶W—v÷&BçfÇVRÀ¢'F–ÖW7F×#¢Æ—7B†VffV7BçF–ÖW7F×’À¢&GW&F–öâ#¢VffV7BæGW&F–öâÀ¢'6÷W&6Uö–B#¢VffV7Bç6÷W&6Uö–BÀ¢&÷&6ÆUög&vÖVçB#¢VffV7Bæ÷&6ÆUög&vÖVçBÀ¢Ð¢f÷"VffV7B–â‚çFV×÷&'•ö¶W—v÷&EöVffV7G0¢ÒÀ¢'FV×÷&'•öFVF…÷&WGW&åöVffV7G2#¢°¢°¢'F–ÖW7F×#¢Æ—7B†VffV7BçF–ÖW7F×’À¢&GW&F–öâ#¢VffV7BæGW&F–öâÀ¢'6÷W&6Uö–B#¢VffV7Bç6÷W&6Uö–BÀ¢&÷&6ÆUög&vÖVçB#¢VffV7Bæ÷&6ÆUög&vÖVçBÀ¢Ð¢f÷"VffV7B–â‚çFV×÷&'•öFVF…÷&WGW&åöVffV7G0¢ÒÀ¢Ð¢f÷"‚–âæ&GFÆVf–VÆ@¢ÒÀ¢&w&fW–&B#¢¶2ææÖRf÷"2–âæw&fW–&EÒÀ¢&w&fW–&Eöö&¦V7Eö–G2#¢¶6&Bæö&¦V7Eö–Bf÷"6&B–âæw&fW–&EÒÀ¢&Æ÷7B#¢æÆ÷7BÀ¢&Æ÷75÷&V6öâ#¢æÆ÷75÷&V6öâÀ¢&f–ÆVEöG&u÷VæF–ær#¢æf–ÆVEöG&u÷VæF–ærÀ¢Ð¢f÷"–â6VÆbçÆ–W'0¢ÒÀ¢&Æ–Ö—FF–öç2#¢6÷'FVB‡6VÆbæÆ–Ö—FF–öç2’À¢&WfVçG2#¢6VÆbæWfVçG2À¢Ð  ¦FVbö–çFVvW%ö6†&7FW&—7F–2‡fÇVS¢7G"ÂæöæR’Óâ–çBÂæöæS ¢–bfÇVR—2æöæS ¢&WGW&âæöæP¢G'“ ¢&WGW&â–çB‡fÇVR¢W†6WBfÇVTW'&÷# ¢&WGW&âæöæP  ¦FVbÆöEöf7G2†6FÆös¢6&DFF6FÆörÂæÖW3¢6WE·7G%Ò’ÓâF–7E·7G"Â6&Df7EÓ ¢f7G2Ò·Ð¢f÷"æÖR–â6÷'FVB†æÖW2“ ¢&÷rÒ6FÆörç&W6öÇfUöæÖR†æÖR¢Öæ÷fÇVRÒ–çB‡&÷ræÖæ÷fÇVR¢–bÖæ÷fÇVRÒ&÷ræÖæ÷fÇVS ¢&—6RfÇVTW'&÷"†b$Væv–æRãr6ææ÷B&W&W6VçBæöæ–çFVw&ÂÖæfÇVRf÷"¶æÖWÒ"¢f7G5¶æÖUÒÒ6&Df7B€¢æÖS×&÷rææÖRÀ¢Öæö6÷7C×&÷ræÖæö6÷7BÀ¢Öæ÷fÇVSÖÖæ÷fÇVRÀ¢G—UöÆ–æS×&÷rçG—UöÆ–æRÀ¢÷&6ÆU÷FW‡C×&÷ræ÷&6ÆU÷FW‡BÀ¢÷vW#Õö–çFVvW%ö6†&7FW&—7F–2‡&÷rç÷vW"’À¢F÷Vv†æW73Õö–çFVvW%ö6†&7FW&—7F–2‡&÷rçF÷Vv†æW72’À¢¶W—v÷&G3×&÷ræ¶W—v÷&G2À¢÷&6ÆUö–C×&÷ræ÷&6ÆUö–BÀ¢¢&WGW&âf7G0  ¦FVbÆöEöFV6²‡Fƒ¢F‚Âf7G3¢F–7E·7G"Â6&Df7EÒ’ÓâÆ—7E´6&Df7EÓ ¢6&G3¢Æ—7E´6&Df7EÒÒµÐ¢f÷"Æ–æR–âF‚ç&VE÷FW‡B†Væ6öF–æsÒ'WFbÓ‚"’ç7Æ—FÆ–æW2‚“ ¢–bæ÷BÆ–æR÷"Æ–æRÓÒ$FV6²# ¢6öçF–çVP¢VçF—G’ÂæÖRÒÆ–æRç7Æ—B‚""Â¢6&G2æW‡FVæB…¶f7G5¶æÖUÕÒ¢–çB‡VçF—G’’¢–bÆVâ†6&G2’Òc ¢&—6RfÇVTW'&÷"†b'·F‡Ó¢W‡V7FVBc6&G2Âf÷VæB¶ÆVâ†6&G2—Ò"¢&WGW&â6&G0 