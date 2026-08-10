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

ENGINE_VERSION = "cardcade-0.5.0"
MATCH_SCHEMA_VERSION = "1.3.0"
STAGES = {"smoke": 20, "calibration": 100, "development": 500, "validation": 1000}
PROFILE_PRIOR_FIELDS = (
    "creature_rate",
    "interaction_rate",
    "board_value",
    "mana_value",
    "support_value",
    "interaction_value",
)


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
    cards: tuple[CardModel, ...] = ()


@dataclass(frozen=True)
class CardModel:
    name: str
    mana_value: int
    card_type: str = "generic"
    artifact_permanent: bool = False
    artifact_tokens: int = 0
    artifact_payoff: bool = False
    affinity: bool = False
    affinity_floor: int = 0


def load_roster(path: Path) -> list[DeckProfile]:
    data = json.loads(path.read_text(encoding="utf-8"))
    model_path = path.with_name("card-model-0.3.json")
    card_models = json.loads(model_path.read_text(encoding="utf-8"))["cards"]
    roster = []
    for row in data["decks"]:
        deck_cards = []
        if not row.get("artifact_plan"):
            roster.append(
                DeckProfile(
                    **{
                        **row,
                        "mana_curve": {
                            int(key): value for key, value in row["mana_curve"].items()
                        },
                    }
                )
            )
            continue
        in_deck = False
        for line in (path.parents[0] / ".." / row["decklist"]).resolve().read_text(
            encoding="utf-8"
        ).splitlines():
            if line.strip() == "Deck":
                in_deck = True
                continue
            if in_deck and line.strip():
                quantity, name = line.split(" ", 1)
                derived = card_models[name]
                card = CardModel(name=name, **derived)
                deck_cards.extend([card] * int(quantity))
        roster.append(
            DeckProfile(
                **{
                    **row,
                    "mana_curve": {int(key): value for key, value in row["mana_curve"].items()},
                    "cards": tuple(deck_cards),
                }
            )
        )
    return roster


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


def profile_prior_inventory(roster: list[DeckProfile]) -> dict[str, Any]:
    """Expose every deck-varying, non-card-derived numeric input used by Cardcade."""
    means = {
        field: sum(getattr(deck, field) for deck in roster) / len(roster)
        for field in PROFILE_PRIOR_FIELDS
    }
    return {
        "fields": {
            field: {
                "neutral_value": means[field],
                "deck_values": {deck.id: getattr(deck, field) for deck in roster},
                "use": (
                    "generic spell classification"
                    if field in {"creature_rate", "interaction_rate"}
                    else "cast-line valuation and/or final game score"
                ),
            }
            for field in PROFILE_PRIOR_FIELDS
        },
        "non_numeric_metadata": {
            "synergy": "telemetry label only; no outcome effect",
            "strategy": "telemetry label only; no outcome effect",
            "artifact_plan": (
                "selects card-derived artifact sequencing and execution telemetry; preserved"
            ),
            "artifact_rate": "legacy roster metadata; no outcome effect in Engine 0.5",
        },
    }


def apply_profile_prior_condition(
    roster: list[DeckProfile], *, fields: tuple[str, ...] = PROFILE_PRIOR_FIELDS, scale: float = 0.0
) -> list[DeckProfile]:
    """Scale selected deck-specific deviations from the roster mean.

    ``scale=0`` neutralizes a prior, ``scale=1`` is baseline, and bounded sensitivity
    values such as 0.5 and 1.5 contract or amplify the authored differences without
    tuning any deck toward a target win rate.
    """
    unknown = set(fields) - set(PROFILE_PRIOR_FIELDS)
    if unknown:
        raise ValueError(f"unknown profile-prior fields: {sorted(unknown)}")
    if scale < 0:
        raise ValueError("profile-prior scale must be non-negative")
    means = {
        field: sum(getattr(deck, field) for deck in roster) / len(roster) for field in fields
    }
    adjusted = []
    for deck in roster:
        values = asdict(deck)
        values["cards"] = deck.cards
        for field in fields:
            values[field] = means[field] + scale * (getattr(deck, field) - means[field])
        adjusted.append(DeckProfile(**values))
    return adjusted


def _cards(profile: DeckProfile) -> list[CardModel]:
    if profile.cards:
        return list(profile.cards)
    return [
        CardModel(name=f"generic-{mv}-{index}", mana_value=mv)
        for mv, count in profile.mana_curve.items()
        for index in range(count)
    ]


def _opening_hand(
    rng: random.Random, profile: DeckProfile
) -> tuple[list[CardModel], list[CardModel], int]:
    deck = _cards(profile)
    mulligans = 0
    while True:
        rng.shuffle(deck)
        hand, library = deck[:7], deck[7:]
        lands = sum(card.mana_value == 0 for card in hand)
        if 2 <= lands <= 5 or mulligans == 2:
            break
        mulligans += 1
    for _ in range(mulligans):
        lands = [card for card in hand if card.mana_value == 0]
        spells = [card for card in hand if card.mana_value > 0]
        hand.remove(lands[0] if len(lands) > 3 else max(spells, key=lambda card: card.mana_value))
    return hand, library, mulligans


def _classify_spell(rng: random.Random, profile: DeckProfile, card: CardModel) -> str:
    if card.card_type != "generic":
        return card.card_type
    roll = rng.random()
    if roll < profile.creature_rate:
        return "creature"
    if roll < profile.creature_rate + profile.interaction_rate * (1 - profile.creature_rate):
        return "interaction"
    return "support"


def _casting_cost(card: CardModel, artifacts: int) -> int:
    discount = (
        min(artifacts, card.mana_value - card.affinity_floor) if card.affinity else 0
    )
    return card.mana_value - discount


def _line_value(
    profile: DeckProfile,
    card: CardModel,
    *,
    artifacts: int,
    board: int,
    mana: int,
    hand: list[CardModel],
) -> tuple[float, str]:
    """Estimate immediate and delayed value without treating a tag as a command."""
    cost = _casting_cost(card, artifacts)
    type_value = {
        "creature": profile.board_value,
        "interaction": profile.interaction_value * (0.55 if board == 0 else 0.75),
        "support": profile.support_value,
        "generic": 0.75,
    }[card.card_type]
    value = type_value + 0.12 * card.mana_value
    reasons = ["immediate_board" if card.card_type == "creature" else "immediate_utility"]

    setup_added = int(card.artifact_permanent) + card.artifact_tokens
    payoff_ready = artifacts >= 2
    payoff_waiting = any(choice.artifact_payoff and choice is not card for choice in hand)
    if setup_added:
        relevant_setup = min(setup_added, max(0, 2 - artifacts))
        value += 0.38 * relevant_setup
        if relevant_setup and payoff_waiting:
            value += 0.32
            reasons.append("enables_delayed_payoff")
        elif artifacts >= 2:
            value -= 0.10 * setup_added
            reasons.append("setup_saturated")
    if card.artifact_payoff:
        if payoff_ready:
            relevance = min(1.0, (artifacts + board) / 4)
            value += 0.72 * relevance
            reasons.append("payoff_relevant")
        else:
            # A payoff creature may still be the best board play.  It is not forced to wait,
            # but the unrealized synergy is explicitly valued below a live payoff.
            value -= 0.28
            reasons.append("payoff_not_ready")
    if card.affinity:
        saved = card.mana_value - cost
        value += 0.16 * saved
        reasons.append("affinity_efficiency")

    # Prefer lines that use available mana, while preserving resources when a low-value play
    # would merely empty the hand.  This term is intentionally smaller than board/card value.
    value += 0.10 * cost
    value -= 0.18 * max(0, mana - cost) if len(hand) <= 2 else 0
    return value, "+".join(reasons)


def _choose_cast(
    profile: DeckProfile,
    hand: list[CardModel],
    choices: list[CardModel],
    *,
    artifacts: int,
    board: int,
    mana: int,
) -> tuple[CardModel | None, dict[str, Any]]:
    """Compare legal casts with one-step sequencing alternatives and a preserve option."""
    evaluated = []
    for index, card in enumerate(choices):
        immediate, reason = _line_value(
            profile, card, artifacts=artifacts, board=board, mana=mana, hand=hand
        )
        remaining = mana - _casting_cost(card, artifacts)
        next_artifacts = artifacts + int(card.artifact_permanent) + card.artifact_tokens
        followups = [
            other
            for other_index, other in enumerate(choices)
            if other_index != index and _casting_cost(other, next_artifacts) <= remaining
        ]
        followup_value = 0.0
        if followups:
            followup_value = max(
                _line_value(
                    profile,
                    other,
                    artifacts=next_artifacts,
                    board=board + int(card.card_type == "creature"),
                    mana=remaining,
                    hand=hand,
                )[0]
                for other in followups
            )
        evaluated.append((immediate + 0.65 * followup_value, immediate, card, reason))
    evaluated.sort(key=lambda row: (row[0], row[1], -row[2].mana_value, row[2].name), reverse=True)
    best = evaluated[0]
    preserve_value = 0.45 if len(hand) <= 2 else 0.0
    chosen = best[2] if best[0] >= preserve_value else None
    return chosen, {
        "legal_lines": len(evaluated) + 1,
        "rejected_lines": len(evaluated) if chosen is None else len(evaluated) - 1,
        "chosen_reason": best[3] if chosen is not None else "resource_preservation",
        "chosen_value": round(best[0], 4) if chosen is not None else preserve_value,
        "best_rejected_value": round(
            max((row[0] for row in evaluated if row[2] is not chosen), default=preserve_value), 4
        ),
    }


def _pilot(rng: random.Random, profile: DeckProfile, on_play: bool) -> dict[str, Any]:
    hand, library, mulligans = _opening_hand(rng, profile)
    lands = board = support = interaction = mana_spent = missed = 0
    artifacts = artifact_setup = artifact_payoffs = sequencing_holds = affinity_saved = 0
    affinity_spells = affinity_discount_events = mana_value_cast = 0
    payoff_cards_cast = payoff_rejections = decision_count = 0
    legal_lines = rejected_lines = resource_preservations = 0
    chosen_reasons: dict[str, int] = {}
    board_t3 = 0
    for turn in range(1, 9):
        if (turn > 1 or not on_play) and library:
            hand.append(library.pop(0))
        land = next((card for card in hand if card.mana_value == 0), None)
        if land:
            hand.remove(land)
            lands += 1
        else:
            missed += 1
        mana = lands
        while choices := [
            card
            for card in hand
            if card.mana_value > 0
            and (
                _casting_cost(card, artifacts) <= mana
            )
        ]:
            if profile.artifact_plan:
                card, decision = _choose_cast(
                    profile, hand, choices, artifacts=artifacts, board=board, mana=mana
                )
                decision_count += 1
                legal_lines += decision["legal_lines"]
                rejected_lines += decision["rejected_lines"]
                reason = decision["chosen_reason"]
                chosen_reasons[reason] = chosen_reasons.get(reason, 0) + 1
                payoff_rejections += sum(
                    choice.artifact_payoff and choice is not card for choice in choices
                )
                if card is None:
                    sequencing_holds += 1
                    resource_preservations += 1
                    break
            else:
                card = min(choices, key=lambda choice: _casting_cost(choice, artifacts))
            if card is None:
                break
            hand.remove(card)
            discount = (
                min(artifacts, card.mana_value - card.affinity_floor) if card.affinity else 0
            )
            affinity_saved += discount
            affinity_spells += int(card.affinity)
            affinity_discount_events += int(discount > 0)
            paid = card.mana_value - discount
            mana -= min(mana, paid)
            mana_spent += paid
            mana_value_cast += card.mana_value
            spell_type = _classify_spell(rng, profile, card)
            if spell_type == "creature":
                board += 1
            elif spell_type == "interaction":
                interaction += 1
            else:
                support += 1
            artifacts_added = int(card.artifact_permanent) + card.artifact_tokens
            artifacts += artifacts_added
            if artifacts_added:
                artifact_setup += artifacts_added
            payoff_cards_cast += int(card.artifact_payoff)
            # Realization depends on relevant infrastructure before the payoff resolves;
            # the payoff cannot count itself as setup.
            if card.artifact_payoff and artifacts - artifacts_added >= 2:
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
        "artifact_payoff_cards_cast": payoff_cards_cast,
        "artifact_payoffs_realized": artifact_payoffs,
        "artifact_payoff_lines_rejected": payoff_rejections,
        "artifact_sequencing_holds": sequencing_holds,
        "sequencing_decisions": decision_count,
        "sequencing_legal_lines": legal_lines,
        "sequencing_rejected_lines": rejected_lines,
        "resource_preservation_holds": resource_preservations,
        "sequencing_chosen_reasons": chosen_reasons,
        "affinity_mana_saved": affinity_saved,
        "affinity_spells_cast": affinity_spells,
        "affinity_discount_events": affinity_discount_events,
        "mana_spent": mana_spent,
        "mana_value_cast": mana_value_cast,
        "cards_in_hand_t8": len(hand),
        "strategy_executed": synergy,
    }


def _score(profile: DeckProfile, state: dict[str, Any]) -> float:
    return sum(_score_components(profile, state).values())


def _score_components(profile: DeckProfile, state: dict[str, Any]) -> dict[str, float]:
    """Return outcome terms separately so injected priors are observable."""
    return {
        "board_value": profile.board_value * state["board_t8"],
        "mana_value": profile.mana_value * state["mana_spent"],
        "support_value": profile.support_value * state["support"],
        "interaction_value": profile.interaction_value * state["interaction_used"],
        "artifact_setup": 0.45 * min(state["artifact_setup_cast"], 2),
        "artifact_payoff": 0.85 * min(state["artifact_payoffs_cast"], 1),
        "affinity_savings": 0.12 * state["affinity_mana_saved"],
        "mulligan_penalty": -0.8 * state["mulligans"],
    }


def simulate_match(
    rng: random.Random, run_id: str, index: int, a: DeckProfile, b: DeckProfile, a_starts: bool
) -> dict[str, Any]:
    a_state, b_state = _pilot(rng, a, a_starts), _pilot(rng, b, not a_starts)
    for state, opponent in ((a_state, b_state), (b_state, a_state)):
        state["interaction_used"] = min(state["interaction"], opponent["board_t8"])
        state["interaction_dead"] = state["interaction"] - state["interaction_used"]
    a_components = _score_components(a, a_state)
    b_components = _score_components(b, b_state)
    component_delta = {
        name: a_components[name] - b_components[name] for name in a_components
    }
    component_delta["interaction_resolution"] = 0.3 * (
        a_state["interaction_used"] - b_state["interaction_used"]
    )
    component_delta["starting_player"] = 1.5 if a_starts else -1.5
    component_delta["closing_variance"] = rng.gauss(0, 3.8)
    delta = sum(component_delta.values())
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
        "score_delta_components": component_delta,
        "score_delta": delta,
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
            "artifact_payoff_cast_rate": sum(
                s["artifact_payoff_cards_cast"] > 0 for s in states
            )/len(states),
            "average_artifact_payoffs_realized": sum(
                s["artifact_payoffs_realized"] for s in states
            )/len(states),
            "average_artifact_payoff_lines_rejected": sum(
                s["artifact_payoff_lines_rejected"] for s in states
            )/len(states),
            "average_artifacts_cast": sum(s["artifacts_cast"] for s in states)/len(states),
            "average_artifact_sequencing_holds": sum(
                s["artifact_sequencing_holds"] for s in states
            )/len(states),
            "average_sequencing_decisions": sum(
                s["sequencing_decisions"] for s in states
            )/len(states),
            "average_sequencing_rejected_lines": sum(
                s["sequencing_rejected_lines"] for s in states
            )/len(states),
            "resource_preservation_hold_rate": sum(
                s["resource_preservation_holds"] > 0 for s in states
            )/len(states),
            "average_affinity_mana_saved": sum(
                s["affinity_mana_saved"] for s in states
            )/len(states),
            "average_affinity_spells_cast": sum(
                s["affinity_spells_cast"] for s in states
            )/len(states),
            "affinity_discount_event_rate": sum(
                s["affinity_discount_events"] > 0 for s in states
            )/len(states),
            "average_mana_value_cast": sum(s["mana_value_cast"] for s in states)/len(states),
            "average_mana_paid": sum(s["mana_spent"] for s in states)/len(states),
        }
    return {
        "schema_version": MATCH_SCHEMA_VERSION,
        "engine_version": ENGINE_VERSION,
        "model_scope": "heuristic rehearsal; not a Magic rules engine or real balance evidence",
        "seed": seed, "games_per_pairing": games, "pairing_count": 45,
        "total_games": len(matches), "roster_hash": roster_hash,
        "first_player_win_rate": _rate(
            matches, lambda match: match["winner"] == match["starting_player"]
        ),
        "decks": decks, "pairings": pairings, "matches": matches,
    }


def run_profile_strength_audit(
    roster: list[DeckProfile], games: int, seed: int
) -> dict[str, Any]:
    """Run baseline, neutralization, isolated attribution, and bounded sensitivity."""
    conditions: dict[str, dict[str, Any]] = {
        "baseline": run_round_robin(roster, games, seed),
        "neutralized": run_round_robin(
            apply_profile_prior_condition(roster), games, seed
        ),
        "contracted_50pct": run_round_robin(
            apply_profile_prior_condition(roster, scale=0.5), games, seed
        ),
        "amplified_150pct": run_round_robin(
            apply_profile_prior_condition(roster, scale=1.5), games, seed
        ),
    }
    for field in PROFILE_PRIOR_FIELDS:
        conditions[f"neutralize_{field}"] = run_round_robin(
            apply_profile_prior_condition(roster, fields=(field,)), games, seed
        )
    baseline = conditions["baseline"]
    comparisons = {
        name: compare_runs(baseline, run)
        for name, run in conditions.items()
        if name != "baseline"
    }
    return {
        "schema_version": "1.0.0",
        "engine_version": ENGINE_VERSION,
        "protocol": {
            "seed": seed,
            "games_per_pairing": games,
            "pairings": baseline["pairing_count"],
            "games_per_condition": baseline["total_games"],
            "starts_per_deck_per_pairing": games // 2,
        },
        "inventory": profile_prior_inventory(roster),
        "condition_definitions": {
            "baseline": "authored Engine 0.4 / Smoke 0.5 deck-profile values (scale 1.0)",
            "neutralized": "all six deck-varying priors set to roster means (scale 0.0)",
            "contracted_50pct": "all deviations from roster means scaled to 0.5",
            "amplified_150pct": "all deviations from roster means scaled to 1.5",
            **{
                f"neutralize_{field}": f"only {field} set to its roster mean"
                for field in PROFILE_PRIOR_FIELDS
            },
        },
        "comparisons_to_baseline": comparisons,
        "condition_summaries": {
            name: {
                "run_id": run["matches"][0]["run_id"],
                "first_player_win_rate": run["first_player_win_rate"],
                "decks": run["decks"],
                "pairings": run["pairings"],
            }
            for name, run in conditions.items()
        },
        "conditions": conditions,
        "governance": (
            "profile priors are audited without decklist mutation or outcome-targeted tuning"
        ),
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
        shift = round(current["deck_a_win_rate"] - previous["deck_a_win_rate"], 10)
        shifts.append(
            {
                "pairing": pairing_id,
                "baseline_deck_a_win_rate": previous["deck_a_win_rate"],
                "candidate_deck_a_win_rate": current["deck_a_win_rate"],
                "shift": shift,
            }
        )
    shifts.sort(key=lambda row: abs(row["shift"]), reverse=True)
    threshold_exceeded = [row for row in shifts if abs(row["shift"]) > 0.15]
    return {
        "schema_version": "1.1.0",
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
        "engine_stability_gate": {
            "criterion": (
                "no unexplained matchup movement greater than 15 percentage points "
                "between consecutive same-protocol engines"
            ),
            "threshold": 0.15,
            "threshold_exceeded": threshold_exceeded,
            "passed": not threshold_exceeded,
        },
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


def write_profile_strength_audit(audit: dict[str, Any], directory: Path) -> None:
    """Preserve every condition as a normal run plus one compact cross-condition audit."""
    directory.mkdir(parents=True, exist_ok=True)
    compact = {key: value for key, value in audit.items() if key != "conditions"}
    (directory / "profile-strength-audit.json").write_text(
        json.dumps(compact, indent=2), encoding="utf-8"
    )
    for name, result in audit["conditions"].items():
        write_run(result, directory / "conditions" / name)
