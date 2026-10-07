"""Read-only loss-signature audit of preserved B&R evidence across semantic runtimes."""

# Complete source and telemetry descriptions are retained as evidence literals.
# ruff: noqa: E501

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OBL = ROOT / "docs/objective-balance-lab"
B = "bebop_rocksteady"
FILES = {
    "round2": OBL / "ROUND_2_EVIDENCE.json",
    "aura": OBL / "BASELINE_003_AURA_RUNTIME_CONTROL.json.gz",
    "new": OBL / "BASELINE_003_R7A_SEMANTIC_CONTROL.json.gz",
    "combined": OBL / "COMBINED_006_R7A_EVIDENCE.json.gz",
    "candidate": OBL / "candidates/BEBOP_ROCKSTEADY_OBL_R2_B.txt",
}
EXPECTED = {
    "round2": "f08d0682c282399b717b1ad7c058cc8b0b29002b33c104c56e31457220c99b6b",
    "aura": "dc5b1400f539d89680fd55d4458f1b81b745d06289427514e1bb716537f94cf9",
    "new": "85a8aee4fb5349b1755a31870aa0e0df4f0039fb1babf81445b24fa4db14cd02",
    "combined": "450d5bc059c747b5951248f2b606fa50534ce6f17e0f99cd77a4291610c130d7",
    "candidate": "6d9fb051c62f16b49a6ffc9045efb40d26007e2ffbcdac1e0524e1722cd4f509",
}
SCHEDULE = "b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27"
NEW_RUNTIME = "f40c4888ef9128d03819fc1be86dde1316b2115fd0d4fb365cd03b288453afa1"
CYCLERS = ("Rocksteady, Crash Courser", "Bebop, Warthog Warrior")
SIGNATURES = (
    *CYCLERS,
    "Zoo Escapees",
    "Frog Butler",
    "Paramecia Coloniex",
    "Bebop & Rocksteady",
    "Mutagen Man, Living Ooze",
    "Cowabunga!",
    "Mutant Chain Reaction",
    "Stomped by the Foot",
    "Illegitimate Business",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> dict:
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def key(game: dict) -> str:
    return json.dumps(game["schedule"], sort_keys=True, separators=(",", ":"))


def average(values: list[int]) -> float | None:
    return round(statistics.mean(values), 4) if values else None


def cycler_events(game: dict) -> list[dict]:
    return [
        event
        for event in game.get("activation_events", [])
        if event["event"] == "activation_announced"
        and event.get("player") == B
        and event.get("source") in CYCLERS
        and "cycling" in event.get("oracle_fragment", "").lower()
    ]


def summary(games: list[dict], *, has_activations: bool) -> dict:
    assert len(games) == 900
    assert len({key(game) for game in games}) == 900
    assert all(game["runtime_error"] is None and B in game["seats"] for game in games)
    assert Counter(game["first_player"] == B for game in games) == {True: 450, False: 450}
    opponents = sorted({deck for game in games for deck in game["seats"] if deck != B})
    creature_times = [game["first"][B]["creature"] for game in games]
    times = [value for value in creature_times if value is not None]
    cast = Counter()
    for game in games:
        for name, quantity in game["signature_casts"].items():
            if name.startswith(f"{B}:"):
                cast[name[len(B) + 1 :]] += quantity
    result = {
        "games": 900,
        "wins": sum(game["winner"] == B for game in games),
        "draws": sum(game["draw"] for game in games),
        "first_player_wins": sum(
            game["winner"] == B and game["first_player"] == B for game in games
        ),
        "opponents": {
            opponent: sum(game["winner"] == B for game in games if opponent in game["seats"])
            for opponent in opponents
        },
        "first_creature": {
            "mean_turn_when_observed": average(times),
            "missing_games": 900 - len(times),
            "by_turn_4": sum(value is not None and value <= 4 for value in creature_times),
            "by_turn_8": sum(value is not None and value <= 8 for value in creature_times),
        },
        "battlefield_presence_mean": {
            str(turn): average(
                [game["battlefield_presence"][B].get(str(turn), 0) for game in games]
            )
            for turn in (3, 5, 7)
        },
        "casts": {
            "total": sum(game["casts"].get(B, 0) for game in games),
            "zero_cast_games": sum(game["casts"].get(B, 0) == 0 for game in games),
            "selected_cards": {name: cast[name] for name in SIGNATURES},
        },
        "ending_turn": {
            "mean": average([game["turn"] for game in games]),
            "median": statistics.median(game["turn"] for game in games),
            "by_turn_15": sum(game["turn"] <= 15 for game in games),
            "wins_by_turn_15": sum(game["turn"] <= 15 and game["winner"] == B for game in games),
            "histogram": dict(
                sorted(
                    Counter(str(game["turn"]) for game in games).items(),
                    key=lambda row: int(row[0]),
                )
            ),
        },
        "opponent_casts_selected": {
            name: sum(
                count
                for game in games
                for signature, count in game["signature_casts"].items()
                if signature.endswith(f":{name}") and not signature.startswith(f"{B}:")
            )
            for name in (
                "Fugitive Droid",
                "Make Your Move",
                "Prehistoric Pet",
                "Leonardo, Leader in Blue",
            )
        },
    }
    if has_activations:
        all_cycle = [event for game in games for event in cycler_events(game)]
        found = paid = shuffled = counter_placed = created = 0
        for game in games:
            events = game["activation_events"]
            cycling_ids = {event["source_id"] for event in cycler_events(game)}
            mutagen_ids = {
                event["source_id"]
                for event in events
                if event["event"] == "activation_announced"
                and event.get("player") == B
                and event.get("source") == "Mutagen"
            }
            paid += sum(
                event["event"] == "activation_cost_paid" and event.get("source_id") in cycling_ids
                for event in events
            )
            found += sum(
                event["event"] == "landcycling_found" and event.get("source_id") in cycling_ids
                for event in events
            )
            shuffled += sum(
                event["event"] == "landcycling_shuffled" and event.get("source_id") in cycling_ids
                for event in events
            )
            counter_placed += sum(
                event["event"] == "mutagen_counter_placed" and event.get("source_id") in mutagen_ids
                for event in events
            )
            created += sum(
                event.get("quantity", 0)
                for event in events
                if event["event"] == "tokens_created"
                and event.get("token") == "Mutagen"
                and event.get("controller") == B
            )
        result["newly_observable_activations"] = {
            "cycling_count_by_card": dict(Counter(event["source"] for event in all_cycle)),
            "cycling_games": sum(bool(cycler_events(game)) for game in games),
            "cycling_paid": paid,
            "cycling_found_land": found,
            "cycling_shuffled": shuffled,
            "cycling_first_turn_histogram": dict(
                sorted(
                    Counter(str(event["turn"]) for event in all_cycle).items(),
                    key=lambda row: int(row[0]),
                )
            ),
            "mutagen_counters_placed_by_B": counter_placed,
            "mutagen_tokens_created_by_B": created,
        }
    else:
        result["activation_telemetry_available"] = False
    return result


def paired(old: list[dict], new: list[dict]) -> dict:
    before = {key(game): game for game in old}
    after = {key(game): game for game in new}
    assert before.keys() == after.keys()
    changed = Counter()
    groups: defaultdict[str, Counter] = defaultdict(Counter)
    for item in before:
        prior, later = before[item], after[item]
        opponent = next(deck for deck in prior["seats"] if deck != B)
        cycled = bool(cycler_events(later))
        label = "cycled" if cycled else "not_cycled"
        group = groups[label]
        group["games"] += 1
        group["prior_wins"] += prior["winner"] == B
        group["later_wins"] += later["winner"] == B
        group["wins_lost"] += prior["winner"] == B and later["winner"] != B
        group["wins_gained"] += prior["winner"] != B and later["winner"] == B
        if prior["winner"] != later["winner"]:
            changed[opponent] += 1
    return {
        "outcome_changed": sum(changed.values()),
        "changed_by_opponent": dict(sorted(changed.items())),
        "cycling_association": {name: dict(row) for name, row in sorted(groups.items())},
    }


def build() -> dict:
    actual = {name: sha(path.read_bytes()) for name, path in FILES.items()}
    assert actual == EXPECTED, "preserved source identity changed"
    round2 = load(FILES["round2"])
    aura = load(FILES["aura"])
    control = load(FILES["new"])
    combined = load(FILES["combined"])
    assert (
        round2["schedule_sha256"]
        == aura["schedule_sha256"]
        == control["schedule_sha256"]
        == combined["schedule_sha256"]
        == SCHEDULE
    )
    assert control["semantic_runtime_sha256"] == combined["semantic_runtime_sha256"] == NEW_RUNTIME
    assert aura["semantic_runtime_sha256"] != NEW_RUNTIME
    assert round2["manifests"][B]["candidates"]["B"]["sha256"] == EXPECTED["candidate"]
    assert (
        next(row for row in aura["baseline_decks"] if row["deck_key"] == B)["sha256"]
        == EXPECTED["candidate"]
    )
    assert (
        next(row for row in control["baseline_decks"] if row["deck_key"] == B)["sha256"]
        == EXPECTED["candidate"]
    )
    assert control["runtime_errors"] == aura["runtime_errors"] == combined["runtime_errors"] == 0
    source = {
        "round2": round2["candidate_results"][B]["B"],
        "aura": [game for game in aura["games"] if B in game["seats"]],
        "new_control": [game for game in control["games"] if B in game["seats"]],
        "combined_006": [game for game in combined["combined_games"] if B in game["seats"]],
    }
    old_map = {key(game): game for game in source["new_control"]}
    changed_in_combined = [game for game in source["combined_006"] if game != old_map[key(game)]]
    assert len(changed_in_combined) <= 100
    assert all("krang" in game["seats"] for game in changed_in_combined)
    assert all(
        game == old_map[key(game)]
        for game in source["combined_006"]
        if "krang" not in game["seats"]
    )
    summaries = {
        label: summary(games, has_activations=label in {"new_control", "combined_006"})
        for label, games in source.items()
    }
    assert [summaries[label]["wins"] for label in source] == [345, 339, 61, 58]
    assert paired(source["new_control"], source["combined_006"])["outcome_changed"] == 13
    assert summaries["new_control"]["casts"]["selected_cards"]["Rocksteady, Crash Courser"] == 0
    assert summaries["new_control"]["casts"]["selected_cards"]["Bebop, Warthog Warrior"] == 0
    return {
        "schema": "obl-round8-bebop-environment-collapse-diagnostic-v1",
        "status": "DIAGNOSTIC_ONLY_RETURN_TO_DESIGN_STUDIO",
        "baseline_004_manifest_git_blob_sha1": "cc17b1760410d7a8547626bb9dbd4a0cd534207f",
        "baseline_004_source_combined_git_blob_sha1": "67adbd9fcd0e39d3a77847570df80ae7c317c330",
        "source_sha256": actual,
        "candidate_sha256": actual["candidate"],
        "schedule_sha256": SCHEDULE,
        "aura_runtime_sha256": aura["semantic_runtime_sha256"],
        "new_runtime_sha256": NEW_RUNTIME,
        "summaries": summaries,
        "paired_aura_to_new": paired(source["aura"], source["new_control"]),
        "paired_new_to_combined": paired(source["new_control"], source["combined_006"]),
        "telemetry_limits": [
            "No per-turn life/damage trace or attack declarations are preserved in these OBL game records.",
            "No authoritative mana spent/unused, hand composition, or stranded-card sequence is preserved.",
            "The legacy Aura and R2 records have no activation-event field; absence is not evidence of zero old activations.",
            "The historical interaction_casts field counts distinct cast card names, not actual removal exposure; it is not used as a removal metric.",
            "Signature spell casts lack resolved target/removal outcomes in these records.",
        ],
        "new_games": 0,
        "redesign": False,
        "baseline_changed": False,
        "promotion_proposed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write derived JSON evidence to this path")
    args = parser.parse_args()
    result = build()
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "wins": {name: row["wins"] for name, row in result["summaries"].items()},
                "paired": result["paired_aura_to_new"],
                "new_games": 0,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
