"""Authoritative floating-mana production lots, allocations, and history."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

MANA_COLORS = frozenset("WUBRGC")


class ManaSpendingContext(StrEnum):
    """Spending contexts currently represented by the engine contract."""

    ARTIFACT_SPELL = "artifact_spell"
    NONARTIFACT_SPELL = "nonartifact_spell"
    ACTIVATED_ABILITY = "activated_ability"


def _context(value: ManaSpendingContext | str | None) -> ManaSpendingContext | None:
    if value is None:
        return None
    if isinstance(value, ManaSpendingContext):
        return value
    try:
        return ManaSpendingContext(value)
    except ValueError as error:
        raise ValueError("unsupported mana spending context") from error


def _allowed_contexts(
    values: Iterable[ManaSpendingContext | str] | None,
) -> frozenset[ManaSpendingContext] | None:
    if values is None:
        return None
    normalized = tuple(_context(value) for value in values)
    if not normalized or any(value is None for value in normalized):
        raise ValueError("restricted mana must have at least one allowed spending context")
    return frozenset(normalized)


@dataclass(frozen=True)
class ManaProduction:
    """Immutable identity and restrictions for one production lot."""

    source_id: str
    color: str
    quantity: int
    event_id: str
    controller: int = 0
    allowed_contexts: frozenset[ManaSpendingContext] | None = None
    expiration_boundary: str | None = None

    @property
    def unrestricted(self) -> bool:
        return self.allowed_contexts is None


@dataclass(frozen=True)
class ManaProductionLot:
    """Current immutable view of a production lot and its lifecycle state."""

    production: ManaProduction
    remaining_quantity: int
    valid: bool
    expired_at: str | None


@dataclass(frozen=True)
class ManaAllocation:
    """Pure plan for consuming a quantity from one exact production lot."""

    production_event_id: str
    controller: int
    color: str
    quantity: int


@dataclass(frozen=True)
class ManaPaymentPlan:
    """Immutable exact colored-cost allocation bound to its payment and purpose."""

    controller: int
    payment_id: str
    spending_context: ManaSpendingContext | None
    requirements: tuple[tuple[str, int], ...]
    allocations: tuple[ManaAllocation, ...]


@dataclass(frozen=True)
class PaymentAllocation:
    """Immutable consumption evidence joined to its production and payment."""

    source_event_id: str
    color: str
    quantity: int
    payment_id: str
    controller: int = 0
    spending_context: ManaSpendingContext | None = None

    @property
    def production_event_id(self) -> str:
        return self.source_event_id


# Preserve the existing public name used by engine callers and tests.
ManaConsumption = PaymentAllocation


@dataclass(frozen=True)
class ManaExpiration:
    """Immutable evidence for a lot's remaining amount at its expiry boundary."""

    production_event_id: str
    controller: int
    color: str
    quantity: int
    boundary_id: str


class FloatingManaLedger:
    """One source-authenticated ledger; live pool totals are derived from active lots."""

    def __init__(self, players: int = 2) -> None:
        if not isinstance(players, int) or isinstance(players, bool) or players <= 0:
            raise ValueError("mana ledger requires at least one player")
        self._players = players
        self._productions: list[list[ManaProduction]] = [[] for _ in range(players)]
        self._production_by_event: dict[str, ManaProduction] = {}
        self._remaining: dict[str, int] = {}
        self._expired_at: dict[str, str] = {}
        self._consumptions: list[list[PaymentAllocation]] = [[] for _ in range(players)]
        self._expirations: list[list[ManaExpiration]] = [[] for _ in range(players)]
        self._committed_allocation_keys: set[tuple[int, str, str]] = set()
        self._committed_payment_ids: set[tuple[int, str]] = set()
        self._issued_payment_plans: dict[tuple[int, str], ManaPaymentPlan] = {}

    def _check_player(self, player: int) -> None:
        if (
            not isinstance(player, int)
            or isinstance(player, bool)
            or player not in range(self._players)
        ):
            raise ValueError("invalid mana controller")

    def add(
        self,
        player: int,
        source_id: str,
        color: str,
        quantity: int,
        event_id: str,
        *,
        controller: int | None = None,
        allowed_contexts: Iterable[ManaSpendingContext | str] | None = None,
        expiration_boundary: str | None = None,
    ) -> None:
        self._check_player(player)
        controller = player if controller is None else controller
        self._check_player(controller)
        if (
            controller != player
            or color not in MANA_COLORS
            or not isinstance(quantity, int)
            or isinstance(quantity, bool)
            or quantity <= 0
            or not isinstance(event_id, str)
            or not event_id
            or not isinstance(source_id, str)
            or not source_id
            or event_id in self._production_by_event
            or (
                expiration_boundary is not None
                and (not isinstance(expiration_boundary, str) or not expiration_boundary)
            )
        ):
            raise ValueError("invalid mana production")
        production = ManaProduction(
            source_id,
            color,
            quantity,
            event_id,
            controller,
            _allowed_contexts(allowed_contexts),
            expiration_boundary,
        )
        self._productions[player].append(production)
        self._production_by_event[event_id] = production
        self._remaining[event_id] = quantity

    def _eligible(
        self,
        production: ManaProduction,
        purpose: ManaSpendingContext | None,
    ) -> bool:
        if production.allowed_contexts is None:
            return True
        # A legacy caller without a typed purpose cannot spend restricted mana.
        return purpose is not None and purpose in production.allowed_contexts

    def plan_payment(
        self,
        player: int,
        requirements: Mapping[str, int],
        payment_id: str,
        purpose: ManaSpendingContext | str | None,
    ) -> ManaPaymentPlan | None:
        """Allocate eligible lots in stable production order without mutation."""
        self._check_player(player)
        purpose = _context(purpose)
        if not isinstance(payment_id, str) or not payment_id:
            raise ValueError("payment identity is required")
        if not isinstance(requirements, Mapping) or not requirements:
            raise ValueError("mana payment requires at least one color")
        normalized: dict[str, int] = {}
        for color, quantity in requirements.items():
            if (
                color not in MANA_COLORS
                or not isinstance(quantity, int)
                or isinstance(quantity, bool)
                or quantity <= 0
            ):
                raise ValueError("invalid mana payment requirement")
            normalized[color] = quantity

        allocations: list[ManaAllocation] = []
        for color in sorted(normalized):
            remaining = normalized[color]
            for production in self._productions[player]:
                available = self._remaining[production.event_id]
                if (
                    production.color != color
                    or available <= 0
                    or not self._eligible(production, purpose)
                ):
                    continue
                quantity = min(remaining, available)
                allocations.append(
                    ManaAllocation(production.event_id, production.controller, color, quantity)
                )
                remaining -= quantity
                if remaining == 0:
                    break
            if remaining:
                return None
        plan = ManaPaymentPlan(
            player,
            payment_id,
            purpose,
            tuple(sorted(normalized.items())),
            tuple(allocations),
        )
        key = (player, payment_id)
        if key in self._issued_payment_plans or key in self._committed_payment_ids:
            raise ValueError("payment identity was already issued")
        self._issued_payment_plans[key] = plan
        return plan

    def commit_payment(
        self,
        player: int,
        plan: ManaPaymentPlan,
    ) -> tuple[PaymentAllocation, ...]:
        """Validate every lot before atomically recording any consumption."""
        self._check_player(player)
        if (
            not isinstance(plan, ManaPaymentPlan)
            or not isinstance(plan.controller, int)
            or isinstance(plan.controller, bool)
            or plan.controller != player
            or not isinstance(plan.payment_id, str)
            or not plan.payment_id
            or (player, plan.payment_id) in self._committed_payment_ids
            or self._issued_payment_plans.get((player, plan.payment_id)) != plan
            or not isinstance(plan.requirements, tuple)
            or not isinstance(plan.allocations, tuple)
            or not plan.allocations
        ):
            raise ValueError("payment requires immutable exact allocations")
        purpose = _context(plan.spending_context)
        requirements = dict(plan.requirements)
        if (
            not plan.requirements
            or len(requirements) != len(plan.requirements)
            or any(
                color not in MANA_COLORS
                or not isinstance(quantity, int)
                or isinstance(quantity, bool)
                or quantity <= 0
                for color, quantity in requirements.items()
            )
        ):
            raise ValueError("payment plan requirements are malformed")
        allocated: dict[str, int] = {}
        seen_events: set[str] = set()
        staged: list[tuple[ManaProduction, ManaAllocation]] = []
        for allocation in plan.allocations:
            if not isinstance(allocation, ManaAllocation):
                raise ValueError("payment allocation is malformed")
            production = self._production_by_event.get(allocation.production_event_id)
            if (
                production is None
                or allocation.production_event_id in seen_events
                or allocation.controller != player
                or allocation.controller != production.controller
                or allocation.color != production.color
                or allocation.color not in MANA_COLORS
                or not isinstance(allocation.quantity, int)
                or isinstance(allocation.quantity, bool)
                or allocation.quantity <= 0
                or self._expired_at.get(production.event_id) is not None
                or self._remaining[production.event_id] < allocation.quantity
                or not self._eligible(production, purpose)
            ):
                raise ValueError("payment allocation is stale, forged, or ineligible")
            seen_events.add(allocation.production_event_id)
            allocated[allocation.color] = allocated.get(allocation.color, 0) + allocation.quantity
            staged.append((production, allocation))
        if allocated != requirements:
            raise ValueError("payment allocations do not satisfy the planned cost")

        committed: list[PaymentAllocation] = []
        for production, allocation in staged:
            key = (player, plan.payment_id, production.event_id)
            if key in self._committed_allocation_keys:
                raise ValueError("payment allocation was already consumed")
            committed.append(
                PaymentAllocation(
                    production.event_id,
                    allocation.color,
                    allocation.quantity,
                    plan.payment_id,
                    player,
                    purpose,
                )
            )
        # Validation above is side-effect free; mutation begins only after all checks pass.
        for allocation in committed:
            self._remaining[allocation.source_event_id] -= allocation.quantity
            self._committed_allocation_keys.add(
                (player, allocation.payment_id, allocation.source_event_id)
            )
            self._consumptions[player].append(allocation)
        self._committed_payment_ids.add((player, plan.payment_id))
        return tuple(committed)

    def consume(
        self,
        player: int,
        color: str,
        quantity: int,
        payment_id: str,
        *,
        purpose: ManaSpendingContext | str | None = None,
    ) -> PaymentAllocation:
        """Compatibility consumption; untyped callers can spend unrestricted lots only."""
        self._check_player(player)
        if (
            color not in MANA_COLORS
            or not isinstance(quantity, int)
            or isinstance(quantity, bool)
            or quantity <= 0
            or not isinstance(payment_id, str)
            or not payment_id
        ):
            raise ValueError("floating mana unavailable")
        context = _context(purpose)
        remaining = quantity
        allocations: list[ManaAllocation] = []
        for production in self._productions[player]:
            available = self._remaining[production.event_id]
            if (
                production.color != color
                or available <= 0
                or not self._eligible(production, context)
            ):
                continue
            take = min(remaining, available)
            allocations.append(
                ManaAllocation(production.event_id, production.controller, color, take)
            )
            remaining -= take
            if remaining == 0:
                break
        if remaining:
            raise ValueError("floating mana unavailable for spending context")
        consumed = self._consume_legacy_plan(player, tuple(allocations), payment_id, context)
        return consumed[-1]

    def _consume_legacy_plan(
        self,
        player: int,
        plan: tuple[ManaAllocation, ...],
        payment_id: str,
        purpose: ManaSpendingContext | None,
    ) -> tuple[PaymentAllocation, ...]:
        """Apply a legacy one-color plan while retaining exact source evidence."""
        committed = tuple(
            PaymentAllocation(
                item.production_event_id,
                item.color,
                item.quantity,
                payment_id,
                item.controller,
                purpose,
            )
            for item in plan
        )
        # Old payment paths may call once per mana unit under one payment ID.
        for allocation in committed:
            production = self._production_by_event.get(allocation.source_event_id)
            if (
                production is None
                or production.controller != player
                or production.color != allocation.color
                or self._expired_at.get(production.event_id) is not None
                or self._remaining[production.event_id] < allocation.quantity
                or not self._eligible(production, purpose)
            ):
                raise ValueError("floating mana allocation is no longer valid")
        for allocation in committed:
            self._remaining[allocation.source_event_id] -= allocation.quantity
            self._consumptions[player].append(allocation)
        return committed

    def available(
        self,
        player: int,
        color: str,
        purpose: ManaSpendingContext | str | None = None,
    ) -> int:
        self._check_player(player)
        if color not in MANA_COLORS:
            return 0
        purpose = _context(purpose)
        return sum(
            self._remaining[production.event_id]
            for production in self._productions[player]
            if production.color == color and self._eligible(production, purpose)
        )

    def snapshot(
        self,
        player: int,
        purpose: ManaSpendingContext | str | None = None,
    ) -> dict[str, int]:
        """Return mana eligible for one context; absent context means unrestricted only."""
        self._check_player(player)
        purpose = _context(purpose)
        return {
            color: quantity
            for color in sorted(MANA_COLORS)
            if (quantity := self.available(player, color, purpose))
        }

    def total_snapshot(self, player: int) -> dict[str, int]:
        """Return all active mana for expiry diagnostics, without authorizing a payment."""
        self._check_player(player)
        return {
            color: quantity
            for color in sorted(MANA_COLORS)
            if (
                quantity := sum(
                    self._remaining[item.event_id]
                    for item in self._productions[player]
                    if item.color == color
                )
            )
        }

    def expire(self, player: int, boundary_id: str) -> tuple[ManaExpiration, ...]:
        """Expire active lots and retain an immutable record for every lot."""
        self._check_player(player)
        if not isinstance(boundary_id, str) or not boundary_id:
            raise ValueError("mana expiration requires a boundary identity")
        if any(
            production.event_id not in self._expired_at
            and production.expiration_boundary not in {None, boundary_id}
            for production in self._productions[player]
        ):
            raise ValueError("mana expiration boundary does not match active production")
        expired: list[ManaExpiration] = []
        for production in self._productions[player]:
            if production.event_id in self._expired_at:
                continue
            quantity = self._remaining[production.event_id]
            record = ManaExpiration(
                production.event_id,
                production.controller,
                production.color,
                quantity,
                boundary_id,
            )
            self._remaining[production.event_id] = 0
            self._expired_at[production.event_id] = boundary_id
            self._expirations[player].append(record)
            expired.append(record)
        return tuple(expired)

    def empty(self, player: int, boundary_id: str | None = None) -> None:
        """Preserve the legacy API while explicitly closing active production lots."""
        self.expire(player, boundary_id or "unspecified-boundary")

    def productions(self, player: int) -> tuple[ManaProduction, ...]:
        self._check_player(player)
        return tuple(self._productions[player])

    def lots(self, player: int) -> tuple[ManaProductionLot, ...]:
        self._check_player(player)
        return tuple(
            ManaProductionLot(
                production,
                self._remaining[production.event_id],
                production.event_id not in self._expired_at,
                self._expired_at.get(production.event_id),
            )
            for production in self._productions[player]
        )

    def consumptions(self, player: int) -> tuple[PaymentAllocation, ...]:
        self._check_player(player)
        return tuple(self._consumptions[player])

    def expirations(self, player: int) -> tuple[ManaExpiration, ...]:
        self._check_player(player)
        return tuple(self._expirations[player])

    def evidence_snapshot(self) -> dict[str, object]:
        """Serialize complete immutable provenance plus the currently spendable lots."""
        return {
            "schema": "floating-mana-lots-v1",
            "players": [
                {
                    "controller": player,
                    "active_mana": self.total_snapshot(player),
                    "productions": [
                        {
                            "source_id": lot.production.source_id,
                            "controller": lot.production.controller,
                            "event_id": lot.production.event_id,
                            "color": lot.production.color,
                            "quantity": lot.production.quantity,
                            "allowed_contexts": (
                                None
                                if lot.production.allowed_contexts is None
                                else sorted(
                                    context.value for context in lot.production.allowed_contexts
                                )
                            ),
                            "expiration_boundary": lot.production.expiration_boundary,
                            "remaining_quantity": lot.remaining_quantity,
                            "valid": lot.valid,
                            "expired_at": lot.expired_at,
                        }
                        for lot in self.lots(player)
                    ],
                    "payments": [
                        {
                            "production_event_id": allocation.source_event_id,
                            "controller": allocation.controller,
                            "color": allocation.color,
                            "quantity": allocation.quantity,
                            "payment_id": allocation.payment_id,
                            "spending_context": (
                                None
                                if allocation.spending_context is None
                                else allocation.spending_context.value
                            ),
                        }
                        for allocation in self.consumptions(player)
                    ],
                    "expirations": [
                        {
                            "production_event_id": item.production_event_id,
                            "controller": item.controller,
                            "color": item.color,
                            "quantity": item.quantity,
                            "boundary_id": item.boundary_id,
                        }
                        for item in self.expirations(player)
                    ],
                }
                for player in range(self._players)
            ],
        }

    def fingerprint_state(self) -> tuple[object, ...]:
        """Canonical ledger state included in the engine authoritative fingerprint."""
        return tuple(
            (
                player,
                tuple(
                    (
                        lot.production.event_id,
                        lot.production.source_id,
                        lot.production.controller,
                        lot.production.color,
                        lot.production.quantity,
                        (
                            None
                            if lot.production.allowed_contexts is None
                            else tuple(
                                sorted(context.value for context in lot.production.allowed_contexts)
                            )
                        ),
                        lot.production.expiration_boundary,
                        lot.remaining_quantity,
                        lot.valid,
                        lot.expired_at,
                    )
                    for lot in self.lots(player)
                ),
                tuple(
                    (
                        item.source_event_id,
                        item.controller,
                        item.color,
                        item.quantity,
                        item.payment_id,
                        None if item.spending_context is None else item.spending_context.value,
                    )
                    for item in self.consumptions(player)
                ),
                tuple(
                    (
                        item.production_event_id,
                        item.controller,
                        item.color,
                        item.quantity,
                        item.boundary_id,
                    )
                    for item in self.expirations(player)
                ),
            )
            for player in range(self._players)
        )
