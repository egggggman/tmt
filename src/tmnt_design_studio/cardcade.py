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

ENGINE_VERSION = "cardcade-0.2.0"
MATCH_SCHEMA_VERSION = "1.1.0"
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
    artifact_plan: str | None = None
    artifact_rate: float = 0.0


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


def _classify_spell(rng: random.Random, profile: DeckProfile) -> str:
    roll = rng.random()
    if roll < profile.creature_rate:
        return "creature"
    if roll < profile.creature_rate + profile.interaction_rate * (1 - profile.creature_rate):
        return "interaction"
    return "support"


def _pilot(rng: random.Random, profile: DeckProfile, on_play: bool) -> dict[str, Any]:
    hand, library, mulligans = _opening_hand(rng, profile)
    lands = board = support = interaction = mana_spent = missed = 0
    artifacts = artifact_setup = artifact_payoffs = sequencing_holds = affinity_saved = 0
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
        while choices := [
            mv
            for mv in hand
            if mv > 0
            and (
                mv <= mana
                or (
                    profile.artifact_plan == "affinity"
                    and mv - min(artifacts, 3, mv - 1) <= mana
                )
            )
        ]:
            affordable = [mv for mv in choices if mv <= mana]
            if not affordable:
                break
            mv = min(affordable)
            if profile.artifact_plan == "affinity" and artifacts >= 2:
                expensive = [
                    value
                    for value in choices
                    if value >= 4 and value - min(artifacts, 3, value - 1) <= mana
                ]
                if expensive:
                    mv = max(expensive)
                    affinity_saved += min(artifacts, 3, mv - 1)
            elif profile.artifact_plan and artifacts < 2:
                setup = [value for value in affordable if value <= 2]
                if setup:
                    mv = min(setup)
                elif any(value >= 4 for value in affordable):
                    sequencing_holds += 1
                    break
            hand.remove(mv)
            discount = (
                min(artifacts, 3, mv - 1)
                if profile.artifact_plan == "affinity" and mv >= 4
                else 0
            )
            paid = mv - discount
            mana -= min(mana, paid)
            mana_spent += mv
            spell_type = _classify_spell(rng, profile)
            if spell_type == "creature":
                board += 1
            elif spell_type == "interaction":
                interaction += 1
            else:
                support += 1
            is_artifact = profile.artifact_plan and (
                spell_type == "support" or rng.random() < profile.artifact_rate
            )
            if is_artifact:
                artifacts += 1
                if mv <= 2:
                    artifact_setup += 1
            if profile.artifact_plan and mv >= 4 and artifacts >= 2:
                artifact_payoffs += 1
        if turn == 3:
            board_t3 = board
    synergy = board >= 3 and support + interaction >= 1 and mana_spent >= 10
    if profile.artifact_plan:
        synergy = artifact_setup >= 2 and artifact_payoffs >= 1 and mana_spent >= 11
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
        "interaction_used": 0,
        "interaction_dead": interaction,
        "artifacts_cast": artifacts,
        "artifact_setup_cast": artifact_setup,
        "artifact_payoffs_cast": artifact_payoffs,
        "artifact_sequencing_holds": sequencing_holds,
        "affinity_mana_saved": affinity_saved,
        "mana_spent": mana_spent,
        "cards_in_hand_t8": len(hand),
        "strategy_executed": synergy,
    }


def _score(profile: DeckProfile, state: dict[str, Any]) -> float:
    return (
        profile.board_value * state["board_t8"]
        + profile.mana_value * state["mana_spent"]
        + profile.support_value * state["support"]
        + profile.interaction_value * state["interaction_used"]
        + 0.45 * state["artifact_setup_cast"]
        + 0.85 * state["artifact_payoffs_cast"]
        + 0.12 * state["affinity_mana_saved"]
        - 0.8 * state["mulligans"]
    )


def simulate_match(
    rng: random.Random, run_id: str, index: int, a: DeckProfile, b: DeckProfile, a_starts: bool
) -> dict[str, Any]:
    a_state, b_state = _pilot(rng, a, a_starts), _pilot(rng, b, not a_starts)
    for state, opponent in ((a_state, b_state), (b_state, a_state)):
        state["interaction_used"] = min(state["interaction"], opponent["board_t8"])
        state["interaction_dead"] = state["interaction"] - state["interaction_used"]
    delta = _score(a, a_state) - _score(b, b_state)
    delta += 0.3 * (a_state["interaction_used"] - b_state["interaction_used"])
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
    matches = []
    pairings = {}
    index = 0
    for a, b in combinations(roster, 2):
        rows = []
        for game in range(games):
            index += 1
            game_seed = f"{seed}:{a.id}:{b.id}:{game}"
            row = simulate_match(random.Random(game_seed), run_id, index, a, b, game % 2 == 0)
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
            "deck_a_interaction_used_rate": _rate(
                rows, lambda r, deck_id=a.id: r["players"][deck_id]["interaction_used"] > 0
            ),
            "deck_b_interaction_used_rate": _rate(
                rows, lambda r, deck_id=b.id: r["players"][deck_id]["interaction_used"] > 0
            ),
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
            "average_interaction_seen": sum(s["interaction"] for s in states)/len(states),
            "average_interaction_used": sum(s["interaction_used"] for s in states)/len(states),
            "average_interaction_dead": sum(s["interaction_dead"] for s in states)/len(states),
            "artifact_setup_rate": sum(s["artifact_setup_cast"] >= 2 for s in states)/len(states),
            "artifact_payoff_rate": sum(s["artifact_payoffs_cast"] > 0 for s in states)/len(states),
            "average_artifacts_cast": sum(s["artifacts_cast"] for s in states)/len(states),
            "average_artifact_sequencing_holds": sum(
                s["artifact_sequencing_holds"] for s in states
            )/len(states),
            "average_affinity_mana_saved": sum(
                s["affinity_mana_saved"] for s in states
            )/len(states),
        }
    return {
        "schema_version": "1.1.0",
        "engine_version": ENGINE_VERSION,
        "model_scope": "heuristic rehearsal; not a Magic rules engine or real balance evidence",
        "seed": seed, "games_per_pairing": games, "pairing_count": 45,
        "total_games": len(matches), "roster_hash": roster_hash,
        "first_player_win_rate": _rate(
            matches, lambda match: match["winner"] == match["starting_player"]
        ),
        "decks": decks, "pairings": pairings, "matches": matches,
    }


def compare_runs(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Compare two same-protocol runs without making deck-change recommendations."""
    if baseline["games_per_pairing"] != candidate["games_per_pairing"]:
        raise ValueError("sensitivity runs must use the same games-per-pairing protocol")
    if set(baseline["pairings"]) != set(candidate["pairings"]):
        raise ValueError("sensitivity runs must contain the same pairings")
    shifts = []
    for pairing_id, current in candidate["pairings"].items():
        previous = baseline["pairings"][pairing_id]
        shifts.append(
            {
                "pairing": pairing_id,
                "baseline_deck_a_win_rate": previous["deck_a_win_rate"],
                "candidate_deck_a_win_rate": current["deck_a_win_rate"],
                "shift": current["deck_a_win_rate"] - previous["deck_a_win_rate"],
            }
        )
    shifts.sort(key=lambda row: abs(row["shift"]), reverse=True)
    return {
        "schema_version": "1.0.0",
        "baseline_run_id": baseline["matches"][0]["run_id"],
        "candidate_run_id": candidate["matches"][0]["run_id"],
        "protocol": {
            "games_per_pairing": candidate["games_per_pairing"],
            "pairings": candidate["pairing_count"],
            "total_games": candidate["total_games"],
            "seed": candidate["seed"],
        },
        "first_player_win_rate": {
            "baseline": _rate(
                baseline["matches"],
                lambda match: match["winner"] == match["starting_player"],
            ),
            "candidate": candidate["first_player_win_rate"],
        },
        "deck_win_rate_shifts": {
            deck_id: candidate["decks"][deck_id]["win_rate"]
            - baseline["decks"][deck_id]["win_rate"]
            for deck_id in candidate["decks"]
        },
        "matchup_shifts": shifts,
        "diagnostics": {
            deck_id: candidate["decks"][deck_id]
            for deck_id in ("donatello", "krang", "shredder")
        },
        "governance": "evidence and hypotheses only; no decklist mutations authorized",
    }


def write_run(result: dict[str, Any], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "run.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    matrix = {deck: {other: None for other in result["decks"]} for deck in result["decks"]}
    for pairing in result["pairings"].values():
        a, b, rate = pairing["deck_a"], pairing["deck_b"], pairing["deck_a_win_rate"]
        matrix[a][b], matrix[b][a] = rate, 1-rate
    (directory / "matchup-matrix.json").write_text(json.dumps(matrix, indent=2), encoding="utf-8")
