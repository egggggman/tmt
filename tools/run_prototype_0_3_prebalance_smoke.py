"""Dedicated, fail-closed runner for the authorized Prototype 0.3 smoke matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from tmnt_design_studio.smoke01 import run_smoke_game  # noqa: E402
from tmnt_design_studio.stage002 import (  # noqa: E402
    DeckSpec,
    GameSpec,
    build_deck_manifest,
    load_catalog,
)

AUTHORIZED_BASE_COMMIT = "023570e22b6790108fb7a3f585cf0f56a70b3ba8"
REQUIRED_GAME_COUNT = 240
SEEDS = tuple(range(3000, 3040))
DECKS = {
    "shredder": (
        "Shredder",
        "decks/shredder/PROTOTYPE_0.3.txt",
        "818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2",
    ),
    "raphael": (
        "Raphael",
        "decks/raphael/PROTOTYPE_0.3.txt",
        "220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51",
    ),
    "donatello": (
        "Donatello",
        "decks/donatello/PROTOTYPE_0.3.txt",
        "77eaf396e6e995a0cbce39b5ad1bf5202f774e8650796480a416122d4a526f08",
    ),
    "casey_jones": (
        "Casey Jones",
        "decks/casey_jones/PROTOTYPE_0.3.txt",
        "f18d2dd6591520e495a0c723e1d15f5d3f4f6ce8a2693e4f93be0cd6660e838f",
    ),
}
MATCHUPS = (
    ("shredder", "raphael"),
    ("shredder", "casey_jones"),
    ("shredder", "donatello"),
    ("raphael", "casey_jones"),
    ("raphael", "donatello"),
    ("casey_jones", "donatello"),
)


class PreflightError(RuntimeError):
    """A pre-execution gate failed; no game may be started."""


@dataclass(frozen=True)
class ScheduledGame:
    game_id: str
    matchup: str
    seed: int
    orientation: str
    starting_deck: str
    opposing_deck: str
    starting_deck_sha256: str
    opposing_deck_sha256: str
    runtime_identity: str


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def _runtime_identity(root: Path, head: str) -> dict[str, str]:
    paths = (
        "src/tmnt_design_studio/engine07.py",
        "src/tmnt_design_studio/stage002.py",
        "src/tmnt_design_studio/pilot07.py",
        "src/tmnt_design_studio/card_interpreter07.py",
    )
    return {
        "repository_head": head,
        "runtime_files_sha256": {
            path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in paths
        },
    }


def build_schedule(root: Path, expected_head: str) -> tuple[ScheduledGame, ...]:
    runtime = json.dumps(
        _runtime_identity(root, expected_head), sort_keys=True, separators=(",", ":")
    )
    runtime_digest = hashlib.sha256(runtime.encode()).hexdigest()
    schedule = []
    for left, right in MATCHUPS:
        earlier, later = sorted((left, right), key=lambda key: DECKS[key][0].casefold())
        for seed in SEEDS:
            starting, opposing = (earlier, later) if seed % 2 == 0 else (later, earlier)
            schedule.append(
                ScheduledGame(
                    game_id=f"{left}-vs-{right}-{seed}",
                    matchup=f"{left}/{right}",
                    seed=seed,
                    orientation="alphabetical-earlier" if seed % 2 == 0 else "other",
                    starting_deck=starting,
                    opposing_deck=opposing,
                    starting_deck_sha256=DECKS[starting][2],
                    opposing_deck_sha256=DECKS[opposing][2],
                    runtime_identity=runtime_digest,
                )
            )
    return tuple(schedule)


def _authenticate_decks(root: Path) -> dict[str, dict[str, Any]]:
    catalog = load_catalog(root)
    manifests = {}
    for key, (_display, relative_path, expected_hash) in DECKS.items():
        path = root / relative_path
        if not path.is_file():
            raise PreflightError(f"missing authenticated deck: {relative_path}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected_hash:
            raise PreflightError(f"deck hash mismatch: {relative_path}")
        try:
            rows = []
            for line in path.read_text(encoding="utf-8").splitlines():
                if line and line != "Deck":
                    quantity, name = line.split(" ", 1)
                    rows.append((int(quantity), name))
            for quantity, name in rows:
                card = catalog.resolve_name(name)
                basic = any(
                    subtype in card.type_line
                    for subtype in ("Plains", "Island", "Swamp", "Mountain", "Forest")
                )
                if card.legalities.get("standard") != "legal":
                    raise PreflightError(f"non-Standard card: {name}")
                if quantity <= 0 or (quantity > 4 and not basic):
                    raise PreflightError(f"invalid quantity for {name}: {quantity}")
        except PreflightError:
            raise
        except (TypeError, ValueError) as error:
            raise PreflightError(f"malformed deck: {relative_path}") from error
        manifest = build_deck_manifest(root, DeckSpec(f"{key}-p0.3", relative_path), catalog)
        if manifest["slot_count"] != 60:
            raise PreflightError(f"deck is not exactly 60 cards: {relative_path}")
        manifests[key] = manifest
        if manifest["deck_sha256"] != expected_hash:
            raise PreflightError(f"manifest hash mismatch: {relative_path}")
    return manifests


def preflight(root: Path, expected_head: str = AUTHORIZED_BASE_COMMIT) -> dict[str, Any]:
    head = _git(root, "rev-parse", "HEAD")
    if head != expected_head:
        raise PreflightError(f"HEAD {head} does not equal expected {expected_head}")
    if _git(root, "status", "--porcelain"):
        raise PreflightError("worktree is not clean")
    manifests = _authenticate_decks(root)
    schedule = build_schedule(root, head)
    if len(schedule) != REQUIRED_GAME_COUNT:
        raise PreflightError("schedule does not contain exactly 240 games")
    for matchup in MATCHUPS:
        games = [item for item in schedule if item.matchup == f"{matchup[0]}/{matchup[1]}"]
        if [item.seed for item in games] != list(SEEDS):
            raise PreflightError(f"invalid seeds for {matchup}")
        starts = Counter(item.starting_deck for item in games)
        if any(starts[key] != 20 for key in matchup):
            raise PreflightError(f"invalid orientation split for {matchup}")
    return {
        "head": head,
        "deck_manifests": manifests,
        "schedule": [asdict(item) for item in schedule],
        "required_game_count": REQUIRED_GAME_COUNT,
    }


def _result_record(game: ScheduledGame, snapshot: dict[str, Any]) -> dict[str, Any]:
    winner = snapshot.get("winner")
    winner_key = next((key for key in DECKS if f"{key}-p0.3" == winner), None)
    return {
        **asdict(game),
        "winner": winner_key,
        "loser": (
            game.opposing_deck
            if winner_key == game.starting_deck
            else game.starting_deck
            if winner_key
            else None
        ),
        "draw": winner is None,
        "terminal_reason": "turn_cap" if winner is None else "winner_declared",
        "turn": snapshot.get("turn"),
        "snapshot": snapshot,
    }


def execute_smoke(root: Path, output: Path, expected_head: str) -> dict[str, Any]:
    """Preflight completely before invoking the accepted single-game runner."""
    manifest = preflight(root, expected_head)
    results = []
    for item in manifest["schedule"]:
        game = ScheduledGame(**item)
        spec = GameSpec(
            game.game_id,
            game.matchup,
            game.seed,
            game.orientation,
            (
                DeckSpec(f"{game.starting_deck}-p0.3", DECKS[game.starting_deck][1]),
                DeckSpec(f"{game.opposing_deck}-p0.3", DECKS[game.opposing_deck][1]),
            ),
        )
        try:
            results.append(_result_record(game, run_smoke_game(root, spec)))
        except Exception as error:
            results.append(
                {
                    **asdict(game),
                    "winner": None,
                    "loser": None,
                    "draw": False,
                    "terminal_reason": "runtime_error",
                    "turn": None,
                    "runtime_error": f"{type(error).__name__}: {error}",
                }
            )
    by_matchup = {}
    for item in results:
        summary = by_matchup.setdefault(
            item["matchup"],
            {"games": 0, "wins": Counter(), "draws": 0, "runtime_failures": 0},
        )
        summary["games"] += 1
        if item["terminal_reason"] == "runtime_error":
            summary["runtime_failures"] += 1
        elif item["draw"]:
            summary["draws"] += 1
        else:
            summary["wins"][item["winner"]] += 1
    matchup_summary = {
        key: {
            "games": value["games"],
            "wins": dict(value["wins"]),
            "draws": value["draws"],
            "runtime_failures": value["runtime_failures"],
            "starting_player_games": dict(
                Counter(item["starting_deck"] for item in results if item["matchup"] == key)
            ),
        }
        for key, value in by_matchup.items()
    }
    deck_summary = {
        key: {
            "games": sum(
                item["starting_deck"] == key or item["opposing_deck"] == key for item in results
            ),
            "wins": sum(item["winner"] == key for item in results),
            "losses": sum(
                item["winner"] is not None
                and item["winner"] != key
                and (item["starting_deck"] == key or item["opposing_deck"] == key)
                for item in results
            ),
            "draws": sum(
                item["draw"] and (item["starting_deck"] == key or item["opposing_deck"] == key)
                for item in results
            ),
        }
        for key in DECKS
    }
    evidence = {
        "schema": "prototype-0.3-prebalance-smoke-v1",
        "execution_identity": manifest["head"],
        "required_game_count": REQUIRED_GAME_COUNT,
        "games_attempted": len(results),
        "games_completed": sum(item["terminal_reason"] != "runtime_error" for item in results),
        "deck_manifests": manifest["deck_manifests"],
        "schedule": manifest["schedule"],
        "results": results,
        "matchup_summary": matchup_summary,
        "deck_summary": deck_summary,
        "malformed_results": 0,
        "runtime_failures": sum(item["terminal_reason"] == "runtime_error" for item in results),
        "turn_cap_outcomes": sum(item["terminal_reason"] == "turn_cap" for item in results),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return evidence


def write_summary(evidence: dict[str, Any], path: Path) -> None:
    lines = [
        "# Prototype 0.3 Pre-Balance Smoke Results",
        "",
        f"- Repository head: `{evidence['execution_identity']}`",
        f"- Games scheduled: {evidence['required_game_count']}",
        f"- Games attempted: {evidence['games_attempted']}",
        f"- Games completed: {evidence['games_completed']}",
        f"- Runtime failures: {evidence['runtime_failures']}",
        f"- Turn-cap outcomes: {evidence['turn_cap_outcomes']}",
        "",
        "## Matchups",
        "",
        "| Matchup | Games | Wins | Draws | Runtime failures | Starting-player games |",
        "| --- | ---: | --- | ---: | ---: | --- |",
    ]
    for matchup, summary in evidence["matchup_summary"].items():
        wins = ", ".join(f"{key}: {value}" for key, value in summary["wins"].items())
        starts = ", ".join(
            f"{key}: {value}" for key, value in summary["starting_player_games"].items()
        )
        lines.append(
            f"| {matchup} | {summary['games']} | {wins} | {summary['draws']} | "
            f"{summary['runtime_failures']} | {starts} |"
        )
    lines.extend(
        [
            "",
            "## Deck aggregates",
            "",
            "| Deck | Games | Wins | Losses | Draws |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for deck, summary in evidence["deck_summary"].items():
        lines.append(
            f"| {DECKS[deck][0]} | {summary['games']} | {summary['wins']} | "
            f"{summary['losses']} | {summary['draws']} |"
        )
    lines.extend(
        [
            "",
            "This is a 240-game diagnostic smoke, not Calibration V1 or a calibrated "
            "balance estimate.",
            "No automatic deck, engine, Pilot, or evidence changes are authorized by this report.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--plan-output", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summary-output", type=Path)
    args = parser.parse_args()
    if args.execute and args.output is None:
        parser.error("--output is required with --execute")
    if args.execute:
        evidence = execute_smoke(args.root, args.output, args.expected_head)
        if args.summary_output:
            write_summary(evidence, args.summary_output)
        print(
            json.dumps({"games_completed": evidence["games_completed"], "output": str(args.output)})
        )
    else:
        manifest = preflight(args.root, args.expected_head)
        payload = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        if args.plan_output:
            args.plan_output.write_text(payload, encoding="utf-8")
        else:
            print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
