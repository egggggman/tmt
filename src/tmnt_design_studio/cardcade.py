"""TMNT the Cardcade Game: reproducible beta-environment rehearsal.

Cardcade is intentionally a coarse gameplay model, not a Magic rules engine. It reports
observations and hypotheses; it never edits decklists or Design Intent.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

ENGINE_VERSION = "cardcade-0.1.0"
MATCH_SCHEMA_VERSION = "1.0.0"
STAGES = {"smoke": 20, "calibration": 100, "development": 500, "validation": 1000}


@dataclass(frozen=True)
class DeckProfile:
    id: str
    name: str
    decklist: str
    mana_curve: dict[int, int]
    creature_rate: float
    interaction_rate: float
    board_value: float
    mana_value: float
    support_value: float
    interaction_value: float
    synergy: str
    strategy: str


def load_roster(path: Path) -> list[DeckProfile]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        DeckProfile(
            **{**row, "mana_curve": {int(key): value for key, value in row["mana_curve"].items()}}
        )
        for row in data["decks"]
    ]


def validate_roster(roster: list[DeckProfile], root: Path) -> list[dict[str, Any]]:
    if len(roster) != 10 or len({deck.id for deck in roster}) != 10:
        raise ValueError("Cardcade beta roster must contain exactly ten uniquely identified decks")
    results = []
    for deck in roster:
        if sum(deck.mana_curve.values()) != 60:
            raise ValueError(f"{deck.id}: profile curve does not contain 60 cards")
        path = root / deck.decklist
        quantities = []
        in_deck = False
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() == "Deck":
                in_deck = True
                continue
            if in_deck and line.strip():
                quantity, _ = line.split(" ", 1)
                quantities.append(int(quantity))
        if sum(quantities) != 60:
            raise ValueError(f"{deck.id}: decklist does not contain 60 cards")
        results.append({"deck_id": deck.id, "cards": 60, "status": "structurally_valid"})
    return results


def _cards(profile: DeckProfile) -> list[int]:
    return [mv for mv, count in profile.mana_curve.items() for _ in range(count)]


def _opening_hand(rng: random.Random, profile: DeckProfile) -> tuple[list[int], list[int], int]:
    deck = _cards(profile)
    mulligans = 0
    while True:
        rng.shuffle(deck)
        hand, library = deck[:7], deck[7:]
        if 2 <= hand.count(0) <= 5 or mulligans == 2:
            break
        mulligans += 1
    for _ in range(mulligans):
        hand.remove(0 if hand.count(0) > 3 else max((x for x in hand if x), default=0))
    return hand, library, mulligans


def _pilot(rng: random.Random, profile: DeckProfile, on_play: bool) -> dict[str, Any]:
    hand, library, mulligans = _opening_hand(rng, profile)
    lands = board = support = interaction = mana_spent = missed = 0
    board_t3 = 0
    for turn in range(1, 9):
        if (turn > 1 or not on_play) and library:
            hand.append(library.pop(0))
        if 0 in hand:
            hand.remove(0)
            lands += 1
        else:
            missed += 1
        mana = lands
        while choices := [mv for mv in hand if 0 < mv <= mana]:
            mv = min(choices)
            hand.remove(mv)
            mana -= mv
            mana_spent += mv
            roll = rng.random()
            if roll < profile.creature_rate:
                board += 1
            elif roll < (
                profile.creature_rate
                + profile.interaction_rate * (1 - profile.creature_rate)
            ):
                interaction += 1
            else:
                support += 1
        if turn == 3:
            board_t3 = board
    synergy = board >= 3 and support + interaction >= 1 and mana_spent >= 10
    if profile.id in {"donatello", "krang"}:
        synergy = support >= 2 and board >= 2 and mana_spent >= 11
    return {
        "mulligans": mulligans,
        "lands_t8": lands,
        "missed_land_drops_t8": missed,
        "mana_screw": lands < 3,
        "mana_flood": lands >= 7,
        "board_t3": board_t3,
        "board_t8": board,
        "support": support,
        "interaction": interaction,
        "mana_spent": mana_spent,
        "cards_in_hand_t8": len(hand),
        "strategy_executed": synergy,
    }


def _score(profile: DeckProfile, state: dict[str, Any]) -> float:
    return (
        profile.board_value * state["board_t8"]
        + profile.mana_value * state["mana_spent"]
        + profile.support_value * state["support"]
        + profile.interaction_value * state["interaction"]
        - 0.8 * state["mulligans"]
    )


def simulate_match(
    rng: random.Random, run_id: str, index: int, a: DeckProfile, b: DeckProfile, a_starts: bool
) -> dict[str, Any]:
    a_state, b_state = _pilot(rng, a, a_starts), _pilot(rng, b, not a_starts)
    delta = _score(a, a_state) - _score(b, b_state)
    delta += 0.3 * (a_state["interaction"] - b_state["interaction"])
    delta += 1.5 if a_starts else -1.5
    delta += rng.gauss(0, 3.8)
    winner = a.id if delta > 0 else b.id
    loser = b.id if winner == a.id else a.id
    winner_state = a_state if winner == a.id else b_state
    loser_state = b_state if winner == a.id else a_state
    closing_turn = max(4, min(14, round(11 - abs(delta) / 2 + rng.gauss(0, 1.2))))
    return {
        "schema_version": MATCH_SCHEMA_VERSION,
        "run_id": run_id,
        "match_id": f"{run_id}-{index:04d}",
        "deck_a": a.id,
        "deck_b": b.id,
        "starting_player": a.id if a_starts else b.id,
        "winner": winner,
        "loser": loser,
        "turns": closing_turn,
        "closing_behavior": "runaway" if abs(delta) >= 8 else "contested",
        "players": {a.id: a_state, b.id: b_state},
        "winner_strategy_executed": winner_state["strategy_executed"],
        "loser_strategy_executed": loser_state["strategy_executed"],
    }


def _rate(rows: list[dict[str, Any]], predicate) -> float:
    return sum(bool(predicate(row)) for row in rows) / len(rows)


def run_round_robin(roster: list[DeckProfile], games: int, seed: int) -> dict[str, Any]:
    if games <= 0 or games % 2:
        raise ValueError("games per pairing must be a positive even number")
    roster_hash = hashlib.sha256(
        json.dumps([asdict(deck) for deck in roster], sort_keys=True).encode()
    ).hexdigest()
    run_id = f"{ENGINE_VERSION}-{seed}-{games}-{roster_hash[:8]}"
    rng = random.Random(seed)
    matches = []
    pairings = {}
    index = 0
    for a, b in combinations(roster, 2):
        rows = []
        for game in range(games):
            index += 1
            row = simulate_match(rng, run_id, index, a, b, game % 2 == 0)
            rows.append(row)
            matches.append(row)
        a_wins = sum(row["winner"] == a.id for row in rows)
        p = a_wins / games
        se = math.sqrt(p * (1-p) / games)
        pairings[f"{a.id}_vs_{b.id}"] = {
            "deck_a": a.id, "deck_b": b.id, "games": games,
            "deck_a_win_rate": p,
            "sampling_95_ci": [max(0, p-1.96*se), min(1, p+1.96*se)],
            "first_player_win_rate": _rate(rows, lambda r: r["winner"] == r["starting_player"]),
            "average_turns": sum(r["turns"] for r in rows)/games,
        }
    decks = {}
    for deck in roster:
        rows = [row for row in matches if deck.id in (row["deck_a"], row["deck_b"])]
        states = [row["players"][deck.id] for row in rows]
        decks[deck.id] = {
            "games": len(rows),
            "win_rate": _rate(rows, lambda r, deck_id=deck.id: r["winner"] == deck_id),
            "mulligan_rate": sum(s["mulligans"] > 0 for s in states)/len(states),
            "mana_screw_rate": sum(s["mana_screw"] for s in states)/len(states),
            "mana_flood_rate": sum(s["mana_flood"] for s in states)/len(states),
            "strategy_execution_rate": sum(s["strategy_executed"] for s in states)/len(states),
            "average_board_t3": sum(s["board_t3"] for s in states)/len(states),
            "average_board_t8": sum(s["board_t8"] for s in states)/len(states),
        }
    return {
        "schema_version": "1.0.0",
        "engine_version": ENGINE_VERSION,
        "model_scope": "heuristic rehearsal; not a Magic rules engine or real balance evidence",
        "seed": seed, "games_per_pairing": games, "pairing_count": 45,
        "total_games": len(matches), "roster_hash": roster_hash,
        "decks": decks, "pairings": pairings, "matches": matches,
    }


def write_run(result: dict[str, Any], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "run.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    matrix = {deck: {other: None for other in result["decks"]} for deck in result["decks"]}
    for pairing in result["pairings"].values():
        a, b, rate = pairing["deck_a"], pairing["deck_b"], pairing["deck_a_win_rate"]
        matrix[a][b], matrix[b][a] = rate, 1-rate
    (directory / "matchup-matrix.json").write_text(json.dumps(matrix, indent=2), encoding="utf-8")
