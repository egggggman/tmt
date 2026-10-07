"""Reproducible OBL Round 1 validation, schedule, and controlled simulation runner."""

# The runner intentionally keeps compact evidence-recording expressions; its output contract is
# more important than line wrapping, and the nested aggregation closures are read-only.
# ruff: noqa: E501, B023, I001

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tmnt_design_studio.pilot07 import AcceptancePilot  # noqa: E402
from tmnt_design_studio.card_interpreter07 import CardInterpreter  # noqa: E402
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, run_game  # noqa: E402

SNAPSHOT = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
SNAPSHOT_MANIFEST = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json"
PARENT = {
    "leonardo": "decks/leonardo/PROTOTYPE_0.1.txt",
    "raphael": "decks/raphael/PROTOTYPE_0.3.txt",
    "donatello": "decks/donatello/PROTOTYPE_0.3c.txt",
    "michelangelo": "decks/michelangelo/PROTOTYPE_0.1.txt",
    "splinter": "decks/splinter/PROTOTYPE_0.1.txt",
    "shredder": "decks/shredder/PROTOTYPE_0.3.txt",
    "krang": "decks/krang/PROTOTYPE_0.2.txt",
    "bebop_rocksteady": "decks/bebop_rocksteady/PROTOTYPE_0.1.txt",
    "april_oneil": "decks/april_oneil/PROTOTYPE_0.1.txt",
    "casey_jones": "decks/casey_jones/PROTOTYPE_0.3.txt",
}
CANDIDATE = {
    deck: f"docs/objective-balance-lab/candidates/{deck.upper()}_OBL_R1.txt" for deck in PARENT
}
DISPLAY = {
    "leonardo": "Leonardo",
    "raphael": "Raphael",
    "donatello": "Donatello",
    "michelangelo": "Michelangelo",
    "splinter": "Splinter",
    "shredder": "Shredder",
    "krang": "Krang",
    "bebop_rocksteady": "Bebop & Rocksteady",
    "april_oneil": "April O'Neil",
    "casey_jones": "Casey Jones",
}
DECKS = tuple(PARENT)
PAIRS = tuple((DECKS[i], DECKS[j]) for i in range(10) for j in range(i + 1, 10))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[tuple[int, str]]:
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line and line != "Deck":
            count, name = line.split(" ", 1)
            result.append((int(count), name))
    return result


def catalog() -> dict[str, dict[str, object]]:
    records = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    result = {}
    for record in records:
        result.setdefault(record["name"], record)
    return result


def validate_deck(path: Path, cards: dict[str, dict[str, object]]) -> dict[str, object]:
    card_rows = rows(path)
    if sum(count for count, _ in card_rows) != 60:
        raise ValueError(f"{path}: main deck is not exactly 60 cards")
    counts = Counter()
    colors = set()
    land = creature = 0
    for count, name in card_rows:
        card = cards.get(name)
        if card is None:
            raise ValueError(f"{path}: unresolved card {name}")
        if card["legalities"].get("standard") != "legal":
            raise ValueError(f"{path}: non-Standard card {name}")
        counts[name] += count
        type_line = card.get("type_line", "")
        if "Basic Land" not in type_line and count > 4:
            raise ValueError(f"{path}: more than four copies of {name}")
        if "Land" in type_line:
            land += count
        elif "Creature" in type_line:
            creature += count
        symbols = re.findall(r"\{([^}]+)\}", card.get("mana_cost", ""))
        for symbol in symbols:
            colors.update(color for color in "WUBRG" if color in symbol.upper())
        if "Plains" in type_line:
            colors.add("W")
        if "Island" in type_line:
            colors.add("U")
        if "Swamp" in type_line:
            colors.add("B")
        if "Mountain" in type_line:
            colors.add("R")
        if "Forest" in type_line:
            colors.add("G")
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha(path),
        "cards": dict(sorted(counts.items())),
        "land_count": land,
        "creature_count": creature,
        "noncreature_count": 60 - land - creature,
        "color_identity": "".join(sorted(colors)),
    }


def diff(parent: dict[str, int], candidate: dict[str, int]) -> dict[str, dict[str, int]]:
    names = sorted(set(parent) | set(candidate))
    return {
        name: {"parent": parent.get(name, 0), "candidate": candidate.get(name, 0)}
        for name in names
        if parent.get(name, 0) != candidate.get(name, 0)
    }


def schedule() -> list[dict[str, object]]:
    # The first 50 sealed V2 blocks provide 100 games per unordered pair:
    # canonical seat order plus the reversed seat order, same seed.
    table = json.loads((ROOT / "docs/cardcade/CALIBRATION_SEED_TABLE_V2.json").read_text())["rows"]
    by_pair = defaultdict(dict)
    for row in table[: 50 * 90]:
        key = tuple(row["decks"])
        by_pair[(min(key), max(key), row["block"], row["orientation"])] = row
    result = []
    for left, right in PAIRS:
        for block in range(50):
            canonical = (
                by_pair[(left, right, block, "canonical")]
                if left < right
                else by_pair[(right, left, block, "reversed")]
            )
            reversed_row = (
                by_pair[(left, right, block, "reversed")]
                if left < right
                else by_pair[(right, left, block, "canonical")]
            )
            for row in (canonical, reversed_row):
                result.append(
                    {
                        "pair": [left, right],
                        "decks": row["decks"],
                        "orientation": row["orientation"],
                        "block": block,
                        "seed": row["seed"],
                        "pair_index": row["pair_index"],
                    }
                )
    return result


def card_from_event(event: dict[str, object]) -> str | None:
    card = event.get("card")
    return card if isinstance(card, str) else None


def game_metrics(
    snapshot: dict[str, object], seats: tuple[str, str], cards: dict[str, dict[str, object]]
) -> dict[str, object]:
    events = snapshot.get("events", [])
    aura_names = {name for name, card in cards.items() if "Aura" in card.get("type_line", "")}
    aura_events = [
        event
        for event in events
        if str(event.get("event", "")).startswith("aura_")
        or (event.get("event") == "spell_cast" and event.get("card") in aura_names)
        or (event.get("event") == "spell_countered" and event.get("target_card") in aura_names)
    ]
    activation_events = [
        event
        for event in events
        if str(event.get("event", "")).startswith(
            ("activation_", "activated_ability_", "landcycling_", "mutagen_counter_")
        )
        or (
            event.get("event") == "zone_changed"
            and event.get("reason") in {"activation_sacrifice_cost", "landcycling_discard_cost"}
        )
        or (event.get("event") == "tokens_created" and event.get("token") == "Mutagen")
    ]
    etb_life_gain_events = [
        event for event in events if event.get("event") == "etb_life_gain_resolved"
    ]
    static_source_names = {
        name
        for name, card in cards.items()
        if any(
            CardInterpreter.STATIC_OTHER_QUALIFIED_CREATURES.fullmatch(line.strip())
            for line in (card.get("oracle_text") or "").splitlines()
        )
    }
    static_modifier_changes = [
        {
            key: event[key]
            for key in (
                "action",
                "source",
                "source_object_id",
                "target",
                "target_object_id",
                "power_delta",
                "toughness_delta",
                "power",
                "toughness",
                "qualifying_targets",
                "oracle_fragment",
            )
        }
        for event in events
        if event.get("event") == "pt_static_team_modifier_changed"
    ]
    static_source_zone_changes = [
        {
            key: event[key]
            for key in (
                "card",
                "source_object_id",
                "destination_object_id",
                "source_zone",
                "destination_zone",
                "reason",
            )
        }
        for event in events
        if event.get("event") == "zone_changed"
        and event.get("card") in static_source_names
        and "battlefield" in (event.get("source_zone"), event.get("destination_zone"))
    ]
    rules = snapshot.get("rules_event_evidence", [])
    cast = [e for e in events if e.get("event") == "spell_cast"]
    creatures = [e for e in events if e.get("event") == "creature_resolved"]
    lands = [e for e in events if e.get("event") == "land_played"]
    interaction_names = {
        name
        for name, card in cards.items()
        if any(
            word in (card.get("oracle_text") or "").lower()
            for word in ("counter target", "destroy target", "exile target", "return target")
        )
    }
    first = {
        deck: {"land_miss": None, "creature": None, "blocker": None, "interaction": None}
        for deck in seats
    }
    casts_by_deck = Counter()
    signatures = Counter()
    battlefield = {deck: {} for deck in seats}
    for event in lands:
        player = str(event.get("player"))
        deck = seats[0] if player in {"a", "0", seats[0]} else seats[1]
        turn = int(event.get("turn", 0))
        battlefield[deck][turn] = battlefield[deck].get(turn, 0)
    for event in creatures:
        deck = seats[0] if str(event.get("player")) in {"a", "0", seats[0]} else seats[1]
        first[deck]["creature"] = first[deck]["creature"] or int(event.get("turn", 0))
    for event in cast:
        deck = seats[0] if str(event.get("player")) in {"a", "0", seats[0]} else seats[1]
        name = card_from_event(event)
        casts_by_deck[deck] += 1
        if name in interaction_names:
            first[deck]["interaction"] = first[deck]["interaction"] or int(event.get("turn", 0))
        if name:
            signatures[f"{deck}:{name}"] += 1
    for event in rules:
        if event.get("kind") != "creature_entered":
            continue
        deck = seats[0] if int(event.get("player_index", 0)) == 0 else seats[1]
        turn = int(event.get("turn", 0))
        first[deck]["blocker"] = first[deck]["blocker"] or turn
        count = sum(
            "Creature" in row.get("type_line", "")
            for row in event.get("battlefield_characteristics", [])
        )
        for threshold in (3, 5, 7):
            if turn <= threshold:
                battlefield[deck][threshold] = max(battlefield[deck].get(threshold, 0), count)
    for deck in seats:
        turn_starts = Counter(
            int(e.get("turn", 0))
            for e in events
            if e.get("event") == "turn_started"
            and str(e.get("active_player"))
            in {deck, "a" if deck == seats[0] else "b", "0" if deck == seats[0] else "1"}
        )
        played = Counter(
            int(e.get("turn", 0))
            for e in lands
            if str(e.get("player"))
            in {deck, "a" if deck == seats[0] else "b", "0" if deck == seats[0] else "1"}
        )
        for turn in sorted(turn_starts):
            if sum(played[t] for t in played if t <= turn) < sum(
                turn_starts[t] for t in turn_starts if t <= turn
            ):
                first[deck]["land_miss"] = turn
                break
    winner = snapshot.get("winner")
    winner_deck = (
        seats[0]
        if winner in {seats[0], "a", "0"}
        else seats[1]
        if winner in {seats[1], "b", "1"}
        else None
    )
    ending_turn = int(snapshot.get("turn", 0))
    return {
        "winner": winner_deck,
        "draw": winner_deck is None,
        "turn": ending_turn,
        "first_player": seats[0],
        "first": first,
        "battlefield_presence": battlefield,
        "casts": dict(casts_by_deck),
        "signature_casts": dict(signatures),
        "interaction_casts": {
            deck: sum(
                1 for key, value in signatures.items() if key.startswith(deck + ":") and value
            )
            for deck in seats
        },
        "runtime_fingerprint": snapshot.get("authoritative_state_fingerprint"),
        "static_modifier_changes": static_modifier_changes,
        "static_source_zone_changes": static_source_zone_changes,
        "aura_events": aura_events,
        "activation_events": activation_events,
        "etb_life_gain_events": etb_life_gain_events,
    }


def aggregate(games: list[dict[str, object]], deck_ids: tuple[str, str]) -> dict[str, object]:
    result = {}
    for deck in deck_ids:
        own = [game for game in games if deck in game["seats"]]
        wins = sum(game["winner"] == deck for game in own)
        draws = sum(game["draw"] for game in own)
        starts = [game for game in own if game["first_player"] == deck]

        def average_field(field: str) -> float | None:
            values = [game[field] for game in own if game[field] is not None]
            return round(statistics.mean(values), 4) if values else None

        def average_first(metric: str) -> float | None:
            values = [
                game["first"][deck][metric]
                for game in own
                if game["first"].get(deck, {}).get(metric) is not None
            ]
            return round(statistics.mean(values), 4) if values else None

        result[deck] = {
            "games": len(own),
            "wins": wins,
            "losses": len(own) - wins - draws,
            "draws": draws,
            "win_rate": round((wins + draws / 2) / len(own), 6) if own else None,
            "first_player_rate": round(
                sum(game["winner"] == deck for game in starts) / len(starts), 6
            )
            if starts
            else None,
            "average_turn": average_field("turn"),
            "median_turn": statistics.median([game["turn"] for game in own]) if own else None,
            "first_play": {
                metric: average_first(metric)
                for metric in ("land_miss", "creature", "blocker", "interaction")
            },
            "interaction_casts": round(
                statistics.mean(game["interaction_casts"].get(deck, 0) for game in own), 4
            )
            if own
            else None,
            "battlefield_presence": {
                str(t): round(
                    statistics.mean(
                        game["battlefield_presence"].get(deck, {}).get(t, 0) for game in own
                    ),
                    4,
                )
                for t in (3, 5, 7)
            },
        }
    return result


_WORKER_CARDS: dict[str, dict[str, object]] = {}


def _init_worker(cards: dict[str, dict[str, object]]) -> None:
    global _WORKER_CARDS
    _WORKER_CARDS = cards
    # run_game's public contract is unchanged; cache the immutable catalog once per worker
    # instead of reparsing the frozen 472-print snapshot for every game.
    import tmnt_design_studio.stage002 as stage002

    frozen_catalog = stage002.load_catalog(ROOT)
    stage002.load_catalog = lambda _root: frozen_catalog


def _run_one(payload: tuple[int, dict[str, str], dict[str, object]]) -> dict[str, object]:
    index, deck_paths, item = payload
    a, b = item["decks"]
    try:
        spec = GameSpec(
            f"obl-r1-{index:05d}",
            f"{a}-vs-{b}",
            item["seed"],
            item["orientation"],
            (DeckSpec(a, deck_paths[a]), DeckSpec(b, deck_paths[b])),
        )
        snapshot = run_game(ROOT, spec, AcceptancePilot())
        metrics = game_metrics(snapshot, (a, b), _WORKER_CARDS)
        metrics.update({"schedule": item, "seats": [a, b], "runtime_error": None})
        return metrics
    except Exception as error:  # preserve a per-game runtime failure without changing the schedule
        return {
            "schedule": item,
            "seats": [a, b],
            "winner": None,
            "draw": False,
            "turn": None,
            "first_player": a,
            "first": {},
            "battlefield_presence": {},
            "casts": {},
            "signature_casts": {},
            "interaction_casts": {},
            "runtime_fingerprint": None,
            "runtime_error": f"{type(error).__name__}: {error}",
        }


def run_set(
    deck_paths: dict[str, str],
    games: list[dict[str, object]],
    cards: dict[str, dict[str, object]],
    workers: int,
) -> list[dict[str, object]]:
    payloads = [(index, deck_paths, item) for index, item in enumerate(games, 1)]
    results = []
    with ProcessPoolExecutor(
        max_workers=workers, initializer=_init_worker, initargs=(cards,)
    ) as executor:
        for index, result in enumerate(executor.map(_run_one, payloads, chunksize=1), 1):
            results.append(result)
            if index % 250 == 0:
                print(f"completed {index}/{len(games)}", flush=True)
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    cards = catalog()
    if (
        hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest()
        != json.loads(SNAPSHOT_MANIFEST.read_text())["snapshot"]["sha256"]
    ):
        raise SystemExit("authoritative snapshot checksum mismatch")
    manifests = {"baseline": {}, "candidate": {}}
    for deck in DECKS:
        manifests["baseline"][deck] = validate_deck(ROOT / PARENT[deck], cards)
        manifests["candidate"][deck] = validate_deck(ROOT / CANDIDATE[deck], cards)
        manifests["candidate"][deck]["diff"] = diff(
            manifests["baseline"][deck]["cards"], manifests["candidate"][deck]["cards"]
        )
    payload = {
        "schema": "objective-balance-lab-round-1-v1",
        "main": "dd439b892e7d97ff65744419855fc581eff218a6",
        "snapshot": {"path": SNAPSHOT.relative_to(ROOT).as_posix(), "sha256": sha(SNAPSHOT)},
        "manifests": manifests,
        "schedule": schedule(),
    }
    if args.validate_only:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        return 0
    if args.output is None:
        raise SystemExit("--output is required for simulation")
    baseline_games = schedule()
    baseline_paths = dict(PARENT)
    baseline_results = run_set(baseline_paths, baseline_games, cards, args.workers)
    candidate_results = {}
    checkpoint = args.output.with_name(args.output.stem + ".checkpoint.json")
    payload["baseline_results"] = baseline_results
    checkpoint.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    def candidate_run(deck: str) -> tuple[str, list[dict[str, object]]]:
        games = [item for item in baseline_games if deck in item["pair"]]
        paths = dict(PARENT)
        paths[deck] = CANDIDATE[deck]
        # Ten independent processes keep the candidate slices isolated while using
        # the same immutable runtime and sealed schedule. The baseline remains wider.
        return deck, run_set(paths, games, cards, max(1, args.workers // 10))

    with ThreadPoolExecutor(max_workers=len(DECKS)) as executor:
        for deck, results in executor.map(candidate_run, DECKS):
            candidate_results[deck] = results
            payload["candidate_results"] = candidate_results
            checkpoint.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
    payload["baseline_results"] = baseline_results
    payload["candidate_results"] = candidate_results
    payload["baseline_summary"] = aggregate(baseline_results, DECKS)
    payload["candidate_summary"] = {
        deck: aggregate(results, tuple(item for item in DECKS if item != deck) + (deck,))
        for deck, results in candidate_results.items()
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "baseline_games": len(baseline_results),
                "candidate_games": sum(map(len, candidate_results.values())),
                "output": str(args.output),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
