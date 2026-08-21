"""Small, deterministic, rules-grounded Cardcade Engine 0.7 foundation.

This module deliberately implements only the rules surface it can represent honestly.  It is
separate from the preserved Engine 0.1--0.6 heuristic simulator.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
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
    ScryProgram,
    StrikeApplicability,
    StrikeKeyword,
    TokenCreationProgram,
    TokenDefinition,
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
class ActivationPaymentPlan:
    """A proposed fixed-mana/tap activation payment using authoritative IDs."""

    player_index: int
    source_id: str
    oracle_fragment: str
    requirement: ManaRequirement
    mana_source_ids: tuple[str, ...]
    tap_source: bool


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


class RulesEventKind(Enum):
    CREATURE_ENTERED = "creature_entered"
    TOKENS_CREATED = "tokens_created"
    LIFE_GAINED = "life_gained"
    ATTACKERS_DECLARED = "attackers_declared"
    DAMAGE_DEALT = "damage_dealt"
    SCRIED = "scried"


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


@dataclass(frozen=True)
class RulesEvent:
    event_id: str
    kind: RulesEventKind
    player_index: int
    subject_ids: tuple[str, ...]
    source_id: str | None = None
    target_player: int | None = None
    amount: int | None = None


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
    source_card: CardFact
    oracle_fragment: str
    program: ActivatedAbilityProgram
    mana_source_ids: tuple[str, ...]
    tap_source: bool
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
                for permanent in permanents:
                    if permanent is not keep:
                        game.put_into_graveyard(permanent, state_based_action=self.name)
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
        self._next_priority_epoch = 1
        self.pending_triggers: list[TriggerInstance] = []
        self._next_event_number = 1
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
        self.combat_damage_evidence: list[CombatDamageStepEvidence] = []
        self.lifelink_evidence: list[LifelinkEvidence] = []
        self.activation_evidence: list[ActivationEvidence] = []
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
        return STEP_PHASE[self._step].value

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
    ) -> tuple[Permanent, ...]:
        """Atomically create one deterministic batch of Oracle-derived token permanents."""
        if creator_index not in range(2):
            raise ValueError("token creator is invalid")
        destination_controller = creator_index if controller is None else controller
        if destination_controller not in range(2):
            raise ValueError("token controller is invalid")
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

        source_zone = obj.zone
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

    def report_unsupported_abilities(self, player_index: int, card: CardFact) -> None:
        """Report each unresolved Oracle line without interpreting or combining its meaning."""
        for fragment, reason in self.interpreter.unsupported_fragments(card):
            self.unsupported(
                card,
                reason,
                player_index=player_index,
                oracle_fragment=fragment,
            )

    def _new_rules_event(
        self,
        kind: RulesEventKind,
        player_index: int,
        subject_ids: tuple[str, ...],
        *,
        source_id: str | None = None,
        target_player: int | None = None,
        amount: int | None = None,
    ) -> RulesEvent:
        event = RulesEvent(
            f"event-{self._next_event_number:06d}",
            kind,
            player_index,
            subject_ids,
            source_id,
            target_player,
            amount,
        )
        self._next_event_number += 1
        self.log(
            "rules_event",
            event_id=event.event_id,
            rules_event=event.kind.value,
            player=self.players[player_index].name,
            subject_ids=list(subject_ids),
            source_id=source_id,
            target_player=target_player,
            amount=amount,
        )
        return event

    def deal_damage(self, transaction: DamageTransaction) -> RulesEvent:
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
        self.check_state_based_actions()
        self.check_life()
        if lifelink_applied:
            self._put_pending_triggers_on_stack()
            self._drain_triggered_abilities()
        return event

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
            oracle_fragment=evidence.oracle_fragment,
        )
        return choice

    def _enqueue_trigger(
        self,
        event: RulesEvent,
        source: Permanent,
        fragment: str,
        effect: TriggerEffect,
    ) -> None:
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
        self.pending_triggers.append(trigger)
        self.log(
            "trigger_pending",
            trigger_id=trigger.trigger_id,
            event_id=event.event_id,
            source=source.card.name,
            controller=self.players[source.controller].name,
            oracle_fragment=fragment,
        )

    def _put_pending_triggers_on_stack(self) -> None:
        """Put one detected batch on the stack in deterministic APNAP/source order."""
        if not self.pending_triggers:
            return
        batch = list(self.pending_triggers)
        self.pending_triggers.clear()
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

    def _resolve_triggered_ability(self, ability: TriggeredAbilityObject) -> None:
        if (
            not self.stack
            or self.stack[-1] is not ability
            or not self.is_authoritative(ability, "stack")
        ):
            raise ValueError("triggered ability must be the authoritative top stack object")
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
            )
        elif ability.effect is TriggerEffect.SNEAK_ETB_CONDITION:
            self.log(
                "pt_effect_condition_not_met",
                source=ability.source_card.name,
                condition="sneak_cost_paid",
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
            effect=ability.effect.value,
        )

    def _drain_triggered_abilities(self) -> None:
        """Immediate compatibility drain until Priority owns all-pass resolution."""
        while self.stack and isinstance(self.stack[-1], TriggeredAbilityObject):
            self._resolve_triggered_ability(self.stack[-1])

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
    ) -> None:
        enabled = effects or {
            TriggerEffect.SNEAK_ETB_CONDITION,
            TriggerEffect.ALLIANCE_PT,
            TriggerEffect.ALLIANCE_COUNTER,
            TriggerEffect.ALLIANCE_MODAL,
            TriggerEffect.CREATE_TOKEN,
            TriggerEffect.DEAL_DAMAGE,
            TriggerEffect.SCRY,
        }
        for permanent in entering:
            event = self._new_rules_event(
                RulesEventKind.CREATURE_ENTERED,
                permanent.controller,
                (permanent.object_id,),
            )
            self._detect_creature_entered_triggers(permanent, event, enabled)
        self._put_pending_triggers_on_stack()
        self._drain_triggered_abilities()

    def _process_creature_entered_triggers(
        self, entering: Permanent, effects: set[TriggerEffect] | None = None
    ) -> None:
        self._process_creatures_entered_triggers((entering,), effects)

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
        self._put_pending_triggers_on_stack()
        self._drain_triggered_abilities()

    def draw(self, player: PlayerState, count: int = 1, *, setup: bool = False) -> bool:
        for _ in range(count):
            if not player.library:
                player.lost = True
                player.loss_reason = "draw_from_empty_library"
                self.winner = 1 - self.players.index(player)
                self.log("player_lost", player=player.name, reason=player.loss_reason)
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
        self.resolve_top_of_stack()
        self.priority_state = None
        self.check_state_based_actions()
        if self.winner is None and self.stack:
            self._begin_priority_window()
        return True

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
        self.log(
            "priority_granted",
            player=self.players[self.active_player].name,
            player_index=self.active_player,
            priority_epoch=epoch,
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

    def execute_attack_action(self, attack: ActionOption) -> None:
        """Revalidate and execute the declare-attackers turn-based action."""
        if attack not in self.legal_attack_options(attack.player_index):
            raise ValueError("attack option is not currently legal")
        attackers = [self._objects[object_id] for object_id in attack.attacker_ids]
        if not all(isinstance(obj, Permanent) for obj in attackers):
            raise ValueError("combat option references a nonpermanent")
        for attacker in attackers:
            attacker.tapped = True  # type: ignore[union-attr]
        self.resolve_attack_pt_effects(attackers)  # type: ignore[arg-type]
        self._combat_attackers = attack.attacker_ids
        self._attackers_declared = True
        self.log("attackers_declared", attackers=list(attack.attacker_ids))
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
        self.transition_to(TurnStep.COMBAT_DAMAGE)

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
        if resolved_kind is CombatDamageStepKind.FIRST_STRIKE and self.winner is None:
            self._start_combat_damage_step(CombatDamageStepKind.REGULAR, 2, 2)
        else:
            self._combat_damage_step_kind = CombatDamageStepKind.COMPLETE
            self.transition_to(TurnStep.END_OF_COMBAT)
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
        prior_mana_taps = tuple(candidate.tapped for candidate in mana_sources)
        prior_source_tapped = source.tapped
        starting_object_number = self._next_object_number
        ability: ActivatedAbilityObject | None = None
        try:
            for mana_source in mana_sources:
                mana_source.tapped = True
            if plan.tap_source:
                source.tapped = True
            ability = ActivatedAbilityObject(
                self._allocate_object_id(),
                player_index,
                source.object_id,
                source.card,
                oracle_fragment,
                semantics.program,
                plan.mana_source_ids,
                plan.tap_source,
                target_ids,
                choice_ids,
            )
            self._register(ability)
            self.stack.append(ability)
        except Exception:
            for mana_source, tapped in zip(mana_sources, prior_mana_taps, strict=True):
                mana_source.tapped = tapped
            source.tapped = prior_source_tapped
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
        )
        self.log(
            "activated_ability_stacked",
            stack_object_id=ability.object_id,
            source_id=source.object_id,
            controller=self.players[player_index].name,
        )
        self._begin_priority_window()
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
        self.log(
            "activated_ability_resolved",
            stack_object_id=ability.object_id,
            source_id=ability.source_id,
            controller=self.players[ability.controller].name,
            delivered=delivered,
        )

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
            self._resolve_triggered_ability(spell)
            return None
        if isinstance(spell, ActivatedAbilityObject):
            if self.priority_state is None or not self.priority_state.resolution_pending:
                raise ValueError("activated ability cannot resolve before all players pass")
            self._resolve_activated_ability(spell)
            return None
        player = self.players[spell.controller]
        target = self._objects.get(spell.target_id or "")

        if spell.cast_kind is CastKind.CREATURE:
            permanent = self.move_object(
                spell,
                "battlefield",
                controller=spell.controller,
                summoning_sick="Haste" not in spell.card.keywords,
                reason="creature_resolved",
            )
            assert isinstance(permanent, Permanent)
            self.log("creature_resolved", player=player.name, card=spell.name)
            self.refresh_static_pt_modifiers()
            self._process_creature_entered_triggers(permanent)
            self.report_unsupported_abilities(spell.controller, spell.card)
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
        if spell.cast_kind in {CastKind.DAMAGE_3_OPPOSING_CREATURE, CastKind.DEAL_DAMAGE}:
            semantics = self.interpreter.damage_semantic_coverage(
                spell.card, spell.card.oracle_text
            )
            if semantics is None or not semantics.coverage.payload_executable:
                raise AssertionError("stacked damage spell no longer has executable semantics")
            assert semantics.program.amount is not None
            self.deal_damage(
                DamageTransaction(
                    spell.controller,
                    spell,
                    DamageTargetKind.CREATURE,
                    semantics.program.amount,
                    spell.card.oracle_text,
                    target=target,
                )
            )
        elif spell.cast_kind is CastKind.DESTROY_OPPOSING_POWER_4:
            self.destroy(target)
        resolved_card = self.move_object(spell, "graveyard", reason="spell_resolved")
        assert isinstance(resolved_card, CardObject)
        self.report_unsupported_abilities(spell.controller, spell.card)
        self.log("spell_resolved", player=player.name, card=spell.name, target=target.card.name)
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

    def put_into_graveyard(
        self, permanent: Permanent, *, state_based_action: str | None = None
    ) -> CardObject:
        if not self.is_authoritative(permanent, "battlefield"):
            raise ValueError("permanent is not on the battlefield")
        owner = self.players[permanent.owner]
        self.alliance_modes_chosen.pop(permanent.object_id, None)
        replacement = self.move_object(
            permanent,
            "graveyard",
            reason=state_based_action or "put_into_graveyard",
        )
        assert isinstance(replacement, CardObject)
        self.refresh_static_pt_modifiers()
        self.log(
            "permanent_to_graveyard",
            player=owner.name,
            card=permanent.card.name,
            state_based_action=state_based_action,
        )
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
        self.check_invariants()

    def check_invariants(self) -> None:
        combat_ids = self._combat_attackers + tuple(
            blocker_id for _attacker_id, blocker_id in self._combat_blocks
        )
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
            elif isinstance(obj, TriggeredAbilityObject) and obj.event.player_index not in range(2):
                raise AssertionError("trigger event player is invalid")
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
            "step": self.step.value,
            "winner": None if self.winner is None else self.players[self.winner].name,
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
            "players": [
                {
                    "name": p.name,
                    "life": p.life,
                    "library": len(p.library),
                    "hand": [c.name for c in p.hand],
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
                    "lost": p.lost,
                    "loss_reason": p.loss_reason,
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
