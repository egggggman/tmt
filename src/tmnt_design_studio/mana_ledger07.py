"""Authoritative floating-mana ledger primitives."""

from dataclasses import dataclass

MANA_COLORS = frozenset("WUBRGC")


@dataclass(frozen=True)
class ManaProduction:
    source_id: str
    color: str
    quantity: int
    event_id: str
    allowed_spending: tuple[str, ...] = ()
    persists_until_turn_end: bool = False


@dataclass(frozen=True)
class ManaConsumption:
    source_event_id: str
    color: str
    quantity: int
    payment_id: str


class FloatingManaLedger:
    """Deterministic per-player floating mana with exact production lineage."""

    def __init__(self, players: int = 2) -> None:
        self._pools: list[dict[str, int]] = [{} for _ in range(players)]
        self._productions: list[list[ManaProduction]] = [[] for _ in range(players)]
        self._consumptions: list[list[ManaConsumption]] = [[] for _ in range(players)]

    def add(
        self,
        player: int,
        source_id: str,
        color: str,
        quantity: int,
        event_id: str,
        allowed_spending: tuple[str, ...] = (),
        persists_until_turn_end: bool = False,
    ) -> None:
        if color not in MANA_COLORS or quantity <= 0 or not event_id or not source_id:
            raise ValueError("invalid mana production")
        if any(item not in {"artifact_spell", "activate_ability"} for item in allowed_spending):
            raise ValueError("invalid mana spending restriction")
        if any(item.event_id == event_id for item in self._productions[player]):
            raise ValueError("duplicate mana event")
        self._pools[player][color] = self._pools[player].get(color, 0) + quantity
        self._productions[player].append(
            ManaProduction(
                source_id,
                color,
                quantity,
                event_id,
                allowed_spending,
                persists_until_turn_end,
            )
        )

    def eligible(self, player: int, context: str) -> tuple[ManaProduction, ...]:
        """Unspent units usable for this payment; restrictions remain with their source."""
        return tuple(
            item
            for item in self._productions[player]
            for _ in range(
                item.quantity
                - sum(
                    used.quantity
                    for used in self._consumptions[player]
                    if used.source_event_id == item.event_id
                )
            )
            if not item.allowed_spending or context in item.allowed_spending
        )

    def consume_events(
        self, player: int, event_ids: tuple[str, ...], payment_id: str, context: str
    ) -> tuple[ManaConsumption, ...]:
        """Validate the complete payment before consuming any mana."""
        eligible = list(self.eligible(player, context))
        selected = []
        for event_id in event_ids:
            item = next((unit for unit in eligible if unit.event_id == event_id), None)
            if item is None:
                raise ValueError("floating mana unavailable for payment context")
            eligible.remove(item)
            selected.append(item)
        result = tuple(
            ManaConsumption(item.event_id, item.color, 1, payment_id) for item in selected
        )
        for item in result:
            self._consumptions[player].append(item)
            self._pools[player][item.color] -= 1
            if not self._pools[player][item.color]:
                del self._pools[player][item.color]
        return result

    def available(self, player: int, color: str) -> int:
        return self._pools[player].get(color, 0)

    def consume(self, player: int, color: str, quantity: int, payment_id: str) -> ManaConsumption:
        if color not in MANA_COLORS or quantity <= 0:
            raise ValueError("floating mana unavailable")
        ids = tuple(
            item.event_id for item in self.eligible(player, "unrestricted") if item.color == color
        )[:quantity]
        if len(ids) != quantity:
            raise ValueError("floating mana unavailable")
        return self.consume_events(player, ids, payment_id, "unrestricted")[-1]

    def empty(self, player: int, *, preserve_turn_end: bool = False) -> dict[str, int]:
        """Expire ordinary units at each boundary and retained units after cleanup."""
        retained: dict[str, int] = {}
        expired: dict[str, int] = {}
        for item in self._productions[player]:
            remaining = item.quantity - sum(
                used.quantity
                for used in self._consumptions[player]
                if used.source_event_id == item.event_id
            )
            if not remaining:
                continue
            if preserve_turn_end and item.persists_until_turn_end:
                retained[item.color] = retained.get(item.color, 0) + remaining
            else:
                self._consumptions[player].append(
                    ManaConsumption(item.event_id, item.color, remaining, "mana_pool_emptied")
                )
                expired[item.color] = expired.get(item.color, 0) + remaining
        self._pools[player] = retained
        return dict(sorted(expired.items()))

    def snapshot(self, player: int) -> dict[str, int]:
        return dict(sorted(self._pools[player].items()))

    def productions(self, player: int) -> tuple[ManaProduction, ...]:
        return tuple(self._productions[player])

    def consumptions(self, player: int) -> tuple[ManaConsumption, ...]:
        return tuple(self._consumptions[player])
