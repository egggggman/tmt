"""Authoritative floating-mana ledger primitives."""

from dataclasses import dataclass

MANA_COLORS = frozenset("WUBRGC")


@dataclass(frozen=True)
class ManaProduction:
    source_id: str
    color: str
    quantity: int
    event_id: str


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

    def add(self, player: int, source_id: str, color: str, quantity: int, event_id: str) -> None:
        if color not in MANA_COLORS or quantity <= 0 or not event_id or not source_id:
            raise ValueError("invalid mana production")
        self._pools[player][color] = self._pools[player].get(color, 0) + quantity
        self._productions[player].append(ManaProduction(source_id, color, quantity, event_id))

    def available(self, player: int, color: str) -> int:
        return self._pools[player].get(color, 0)

    def consume(self, player: int, color: str, quantity: int, payment_id: str) -> ManaConsumption:
        if color not in MANA_COLORS or quantity <= 0 or self.available(player, color) < quantity:
            raise ValueError("floating mana unavailable")
        remaining = quantity
        for production in self._productions[player]:
            used = sum(
                item.quantity
                for item in self._consumptions[player]
                if item.source_event_id == production.event_id
            )
            if production.color != color or used >= production.quantity:
                continue
            take = min(remaining, production.quantity - used)
            self._consumptions[player].append(
                ManaConsumption(production.event_id, color, take, payment_id)
            )
            remaining -= take
            if remaining == 0:
                break
        if remaining:
            raise AssertionError("mana consumption lineage incomplete")
        self._pools[player][color] -= quantity
        if self._pools[player][color] == 0:
            del self._pools[player][color]
        return self._consumptions[player][-1]

    def empty(self, player: int) -> None:
        self._pools[player].clear()

    def snapshot(self, player: int) -> dict[str, int]:
        return dict(sorted(self._pools[player].items()))

    def productions(self, player: int) -> tuple[ManaProduction, ...]:
        return tuple(self._productions[player])

    def consumptions(self, player: int) -> tuple[ManaConsumption, ...]:
        return tuple(self._consumptions[player])
