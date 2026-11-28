"""Gate A disposable *model*, NOT production Cardcade integration.

Run only this named synthetic proof with:
    python -m unittest experiments.test_cardcade_cast_gate_a -v

Uses an intentionally small object/ledger model. Passing tests establish only
the model's behavior, not isolation of real Game readers, callbacks or objects.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock, get_ident
import unittest


@dataclass(eq=False)
class Card:
    object_id: str
    zone: str


@dataclass(eq=False)
class Permanent:
    object_id: str
    tapped: bool = False


@dataclass
class Ledger:
    authority: object = field(default_factory=object)
    revision: int = 0
    remaining: int = 3
    committed_ids: set[str] = field(default_factory=set)


class ReentrantReadBlocked(RuntimeError):
    pass


class SyntheticGame:
    def __init__(self):
        self._lock = RLock()
        self._publishing = False
        self._owner: int | None = None
        self._generation = 0
        self.card = Card("card-1", "hand")
        self.land = Permanent("land-1")
        self.ledger = Ledger()
        self.hand = [self.card]
        self.stack: list[Card] = []
        self.events: list[str] = []
        self.outcomes: dict[str, str] = {}

    def snapshot(self):
        # This model is guarded. Real Game.snapshot() is NOT.
        if self._publishing:
            raise ReentrantReadBlocked("public read during provisional publication")
        with self._lock:
            return (self.card.zone, self.land.tapped, tuple(self.hand),
                    tuple(self.stack), tuple(self.events),
                    self.ledger.remaining, self.ledger.revision,
                    frozenset(self.ledger.committed_ids))

    def begin(self, txn_id: str):
        if self._publishing:
            raise ReentrantReadBlocked("nested transaction")
        if txn_id in self.outcomes:
            raise ValueError("used transaction ID")
        with self._lock:
            return Candidate(self, txn_id, self._generation,
                             self.ledger.authority, self.ledger.revision)

    def commit(self, candidate, *, fail_at=None, observer=None):
        if candidate.game is not self or candidate.final:
            raise ValueError("invalid transaction")
        if candidate.base_generation != self._generation:
            candidate.final = True
            self.outcomes[candidate.txn_id] = "aborted"
            raise ValueError("stale generation")
        if candidate.ledger_authority is not self.ledger.authority:
            raise ValueError("ledger authority mismatch")
        if candidate.ledger_revision != self.ledger.revision:
            raise ValueError("ledger revision mismatch")
        if self.ledger.remaining < 1:
            raise ValueError("insufficient mana")
        if candidate.txn_id in self.ledger.committed_ids:
            raise ValueError("duplicate payment")
        # All fallible staging is private. These synthetic boundaries are NOT
        # the real engine event/trigger/witness/callback code paths.
        for seam in ("mana", "zone", "event", "trigger", "evidence"):
            if fail_at == seam:
                candidate.final = True
                self.outcomes[candidate.txn_id] = "aborted"
                raise RuntimeError("synthetic failure: " + seam)
        with self._lock:
            if self._publishing:
                raise ReentrantReadBlocked("nested publication")
            self._publishing = True
            self._owner = get_ident()
            try:
                if observer is not None:
                    observer(self)  # must fail closed via public snapshot()
                # The following is a multi-write installation: safe ONLY
                # to guard-aware observers. Direct references can see it.
                self.ledger.remaining -= 1
                self.ledger.revision += 1
                self.ledger.committed_ids.add(candidate.txn_id)
                self.land.tapped = True
                self.hand.remove(self.card)
                self.card.zone = "stack"
                self.stack.append(self.card)
                self.events.extend(("SPELL_CAST", "trigger", "cost_paid"))
                self._generation += 1
                self.outcomes[candidate.txn_id] = "committed"
                candidate.final = True
            finally:
                self._publishing = False
                self._owner = None
        return self.snapshot()

    def abort(self, candidate):
        if candidate.final:
            return self.outcomes.get(candidate.txn_id) == "aborted"
        candidate.final = True
        self.outcomes[candidate.txn_id] = "aborted"
        return True


@dataclass
class Candidate:
    game: SyntheticGame
    txn_id: str
    base_generation: int
    ledger_authority: object
    ledger_revision: int
    final: bool = False


class GateASyntheticTests(unittest.TestCase):
    def test_prepublication_injection_is_pure_at_all_model_seams(self):
        for seam in ("mana", "zone", "event", "trigger", "evidence"):
            with self.subTest(seam=seam):
                game = SyntheticGame()
                baseline = game.snapshot()
                card = game.card
                authority = game.ledger.authority
                tx = game.begin("tx")
                with self.assertRaisesRegex(RuntimeError, seam):
                    game.commit(tx, fail_at=seam)
                self.assertEqual(game.snapshot(), baseline)
                self.assertIs(game.card, card)
                self.assertIs(game.ledger.authority, authority)
                self.assertTrue(game.abort(tx))

    def test_success_preserves_instances_authority_and_once_only_payment(self):
        game = SyntheticGame()
        card, land, authority = game.card, game.land, game.ledger.authority
        game.commit(game.begin("tx"))
        self.assertIs(game.card, card)
        self.assertIs(game.land, land)
        self.assertIs(game.ledger.authority, authority)
        self.assertEqual(game.ledger.revision, 1)
        self.assertEqual(game.ledger.remaining, 2)
        self.assertEqual(game.outcomes["tx"], "committed")
        with self.assertRaisesRegex(ValueError, "used transaction ID"):
            game.begin("tx")

    def test_stale_generation_rejected(self):
        game = SyntheticGame()
        stale = game.begin("old")
        game.commit(game.begin("new"))
        with self.assertRaisesRegex(ValueError, "stale generation"):
            game.commit(stale)

    def test_public_observer_rejected_before_publication(self):
        game = SyntheticGame()
        original = game.snapshot()
        def reader(g):
            with self.assertRaises(ReentrantReadBlocked):
                g.snapshot()
            with self.assertRaises(ReentrantReadBlocked):
                g.begin("nested")
        game.commit(game.begin("tx"), observer=reader)
        self.assertNotEqual(game.snapshot(), original)

    def test_direct_reference_is_not_guarded_this_is_the_real_blocker(self):
        # Deliberate limitation: existing engine exposes the same objects.
        # No guarded snapshot method can block 'card.zone' directly.
        game = SyntheticGame()
        external_card_reference = game.card
        self.assertEqual(external_card_reference.zone, "hand")
        game.commit(game.begin("tx"))
        self.assertEqual(external_card_reference.zone, "stack")
        self.assertIs(external_card_reference, game.card)


if __name__ == "__main__":
    unittest.main()
