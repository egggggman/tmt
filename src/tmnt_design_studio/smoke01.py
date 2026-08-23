"""Coverage-aware evidence runner for Engine Smoke Stage 0.1.

This module parameterizes the accepted Stage #002 gameplay and conformance
machinery.  It adds no gameplay semantics.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import subprocess
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from tmnt_design_studio.engine07 import Game, load_deck, load_facts
from tmnt_design_studio.pilot07 import AcceptancePilot, Pilot
from tmnt_design_studio.stage002 import (
    DeckSpec,
    GameSpec,
    _add_created_token_presence,
    _checked_action,
    _deck_rows,
    _drain_priority,
    _finish_presence,
    _initial_presence,
    _resolve_combat_damage_steps,
    build_deck_manifest,
    canonical_json,
    load_catalog,
    reconcile_snapshot,
    stable_digest,
)

STAGE_ID = "coverage-aware-engine-smoke-0.1"
REQUIRED_GAME_COUNT = 180
DECKS = (
    DeckSpec("april_oneil", "decks/april_oneil/PROTOTYPE_0.1.txt"),
    DeckSpec("bebop_rocksteady", "decks/bebop_rocksteady/PROTOTYPE_0.1.txt"),
    DeckSpec("casey_jones", "decks/casey_jones/PROTOTYPE_0.1.txt"),
    DeckSpec("donatello", "decks/donatello/PROTOTYPE_0.2.txt"),
    DeckSpec("krang", "decks/krang/PROTOTYPE_0.2.txt"),
    DeckSpec("leonardo", "decks/leonardo/PROTOTYPE_0.1.txt"),
    DeckSpec("michelangelo", "decks/michelangelo/PROTOTYPE_0.1.txt"),
    DeckSpec("raphael", "decks/raphael/PROTOTYPE_0.1.txt"),
    DeckSpec("shredder", "decks/shredder/PROTOTYPE_0.1.txt"),
    DeckSpec("splinter", "decks/splinter/PROTOTYPE_0.1.txt"),
)

FROZEN_PATHS = (
    "cardcade/roster-0.2.json",
    "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
    "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    "decks/leonardo/PROTOTYPE_0.1.txt",
    "decks/raphael/PROTOTYPE_0.1.txt",
    "decks/donatello/PROTOTYPE_0.2.txt",
    "decks/michelangelo/PROTOTYPE_0.1.txt",
    "decks/splinter/PROTOTYPE_0.1.txt",
    "decks/april_oneil/PROTOTYPE_0.1.txt",
    "decks/casey_jones/PROTOTYPE_0.1.txt",
    "decks/shredder/PROTOTYPE_0.1.txt",
    "decks/krang/PROTOTYPE_0.2.txt",
    "decks/bebop_rocksteady/PROTOTYPE_0.1.txt",
    "src/tmnt_design_studio/engine07.py",
    "src/tmnt_design_studio/card_interpreter07.py",
    "src/tmnt_design_studio/pilot07.py",
    "src/tmnt_design_studio/stage002.py",
    "src/tmnt_design_studio/conformance07.py",
)
FROZEN_DIGESTS = (
    "fdbc141b1119227d71dbf0a41a7f3970c1548f6fff1884f1173f9d018b5eb4ed",
    "56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402",
    "6b5271af75150a361f77e7b89306c709959dfdf497c448dfdc978e5dc9a17950",
    "d49d155858938d6fc64127c1678e591ee77abad3b7da8302880f16379476fb08",
    "07eed928ef6c47aea1f8fb2df2c494d0fae12c10bee8836e7aa9cf2a8784a834",
    "8c7ac3bf72e9c8f44e89906567b5fca2c59200f695ba43608c5a91842beb9ce2",
    "f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9",
    "74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a",
    "684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4",
    "0fc0adbb370ecfddad03692a4229a04b23268739914a8f2a004b8e042ff3cebb",
    "d0c6479ef2df6d3c64911e8f93465310760f6509282b018fb1c8319cc2c3d6a1",
    "5a52bc59b5de1034721ba17d1c1d4f12c493ec70681c1a910c8230808e4e4f96",
    "3875706a76ffab14d2a82ba836da9e59bce49de2f990a348941490e78a61ef9d",
    "501c3af019c0ac123a2589e6652f49931dfff23d86670d7451dcb25369bc4be9",
    "2407cb6bf72c638036c8d2b7ffbb720f2abe2921fe82696827c88b01449109ab",
    "8b1365cf58794c9df0045d6aaf8024c5f67dd41dea5bdd80b4f07569adbbc883",
    "c2b17ad738d3dc9fa29fc0c080f86af00e5329d31cad63ac32847be792b75250",
    "cd3f4ef06c7c423e317978e52abad1ace988f26dcfe2df682c8f1d342727ad29",
)
FROZEN_HASHES = dict(zip(FROZEN_PATHS, FROZEN_DIGESTS, strict=True))


@dataclass(frozen=True)
class SmokeGameFailure(RuntimeError):
    message: str
    snapshot: dict[str, object]

    def __str__(self) -> str:
        return self.message


def smoke_games() -> tuple[GameSpec, ...]:
    games: list[GameSpec] = []
    for pairing_index, (first, second) in enumerate(itertools.combinations(DECKS, 2)):
        pairing_id = f"{first.display_id}--{second.display_id}"
        for seed in (8001 + 2 * pairing_index, 8002 + 2 * pairing_index):
            for orientation, seats in (
                ("canonical", (first, second)),
                ("reversed", (second, first)),
            ):
                games.append(
                    GameSpec(
                        f"{pairing_id}:{orientation}:{seed}",
                        pairing_id,
                        seed,
                        orientation,
                        seats,
                    )
                )
    return tuple(games)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _execution_commit(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def build_smoke_manifest(root: Path) -> dict[str, object]:
    """Reconstruct the complete frozen plan without creating a Game or consuming RNG."""
    actual_hashes = {relative: _sha256(root / relative) for relative in FROZEN_HASHES}
    mismatches = {
        relative: {"expected": FROZEN_HASHES[relative], "actual": actual}
        for relative, actual in actual_hashes.items()
        if actual != FROZEN_HASHES[relative]
    }
    if mismatches:
        raise ValueError(f"frozen Smoke 0.1 input mismatch: {mismatches}")
    catalog = load_catalog(root)
    if len(catalog.cards) != 472 or len({card.oracle_id for card in catalog.cards}) != 332:
        raise ValueError("authoritative Smoke 0.1 corpus membership mismatch")
    decks = [build_deck_manifest(root, spec, catalog) for spec in DECKS]
    games = [
        {
            "game_id": game.game_id,
            "pairing_id": game.pairing_id,
            "seed": game.seed,
            "orientation": game.orientation,
            "seats": [seat.display_id for seat in game.seats],
        }
        for game in smoke_games()
    ]
    if len(games) != 180 or len({game["game_id"] for game in games}) != 180:
        raise ValueError("Smoke 0.1 matrix is not exactly 180 collision-free games")
    body = {
        "stage": STAGE_ID,
        "execution_commit": _execution_commit(root),
        "runner_sha256": _sha256(Path(__file__)),
        "pilot": "tmnt_design_studio.pilot07.AcceptancePilot",
        "frozen_hashes": actual_hashes,
        "catalog": {
            "print_count": len(catalog.cards),
            "oracle_object_count": len({card.oracle_id for card in catalog.cards}),
            "snapshot_sha256": catalog.snapshot_sha256,
        },
        "decks": decks,
        "games": games,
        "pairing_count": 45,
        "distinct_game_count": 180,
        "duplicate_executions_per_game": 2,
        "execution_count": 360,
    }
    return {**body, "manifest_digest": stable_digest(body)}


def plan(root: Path) -> dict[str, object]:
    return {"authorized": False, "manifest": build_smoke_manifest(root)}


def run_smoke_game(root: Path, spec: GameSpec, pilot: Pilot | None = None) -> dict[str, object]:
    """Drive the accepted game lifecycle while retaining failure-state evidence."""
    catalog = load_catalog(root)
    paths = tuple(root / seat.relative_path for seat in spec.seats)
    names = {name for path in paths for _quantity, name in _deck_rows(path)}
    facts = load_facts(catalog, names)
    game = Game(
        (load_deck(paths[0], facts), load_deck(paths[1], facts)),
        names=tuple(seat.display_id for seat in spec.seats),
        seed=spec.seed,
    )
    presence = _initial_presence(game)
    chosen_pilot = pilot or AcceptancePilot()
    game.scry_chooser = chosen_pilot.choose_scry
    game.hand_bottom_draw_chooser = chosen_pilot.choose_hand_bottom_draw
    game.discard_draw_chooser = chosen_pilot.choose_discard_draw
    try:
        while game.winner is None and game.turn < 120:
            _checked_action(game, game.begin_turn, "begin turn")
            if game.winner is not None:
                break
            active = game.active_player
            for stage in ("land", "activate", "damage", "destroy", "creature"):
                options = game.legal_main_actions(active)
                choice = chosen_pilot.choose_main_action(game.public_view(), options, stage)
                _checked_action(
                    game, lambda choice=choice: game.execute_main_action(choice), "main action"
                )
                _drain_priority(game, chosen_pilot)
            _checked_action(game, game.advance_step, "advance to combat")
            _checked_action(game, game.advance_step, "advance to attackers")
            attack = chosen_pilot.choose_attack(
                game.public_view(), game.legal_attack_options(active)
            )
            _checked_action(
                game, lambda attack=attack: game.execute_attack_action(attack), "attack action"
            )
            _drain_priority(game, chosen_pilot)
            blocks = chosen_pilot.choose_blocks(
                game.public_view(), game.legal_block_options(attack, 1 - active)
            )
            _checked_action(
                game, lambda blocks=blocks: game.execute_block_action(blocks), "block action"
            )
            while game.step.value == "declare_blockers":
                options = game.legal_sneak_actions(active)
                choice = chosen_pilot.choose_sneak(game.public_view(), options)
                _checked_action(
                    game, lambda choice=choice: game.execute_sneak_action(choice), "sneak"
                )
                _drain_priority(game, chosen_pilot)
            _resolve_combat_damage_steps(game, chosen_pilot)
            _checked_action(game, game.advance_step, "advance after combat")
            game.check_invariants()
            _checked_action(game, game.end_turn, "end turn")
        if game.winner is None:
            game.log("acceptance_incomplete", reason="turn_limit")
        snapshot = game.snapshot()
        _add_created_token_presence(game, presence, snapshot["events"])
        snapshot["stage002_presence"] = _finish_presence(presence, snapshot["events"])
        return snapshot
    except Exception as error:
        snapshot = game.snapshot()
        snapshot["stage002_presence"] = _finish_presence(presence, snapshot["events"])
        raise SmokeGameFailure(str(error), snapshot) from error


Runner = Callable[[Path, GameSpec, Pilot | None], dict[str, object]]


def _mechanical_label(report: dict[str, object], snapshot: dict[str, object]) -> str:
    if report["stop_records"] or report["invariant_violations"] or snapshot.get("winner") is None:
        raise RuntimeError("mechanically invalid or incomplete game")
    occurrence_ids = [item["occurrence_id"] for item in report["occurrences"]]
    if len(occurrence_ids) != len(set(occurrence_ids)):
        raise RuntimeError("semantic occurrence is not classified exactly once")
    accepted = {"executed", "reached_unsupported", "present_unreached"}
    if any(item["classification"] not in accepted for item in report["occurrences"]):
        raise RuntimeError("semantic occurrence has an unknown classification")
    return (
        "mechanically_clean_coverage_limited"
        if report["classification_sets"]["reached_unsupported"]
        else "mechanically_clean_coverage_complete"
    )


def _atomic_write(path: Path, payload: dict[str, object]) -> str:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(rendered, encoding="utf-8", newline="\n")
    os.replace(temporary, path)
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    sidecar = path.with_suffix(path.suffix + ".sha256")
    sidecar_temporary = sidecar.with_name(f".{sidecar.name}.tmp")
    sidecar_temporary.write_text(f"{digest}  {path.name}\n", encoding="ascii", newline="\n")
    os.replace(sidecar_temporary, sidecar)
    return digest


def _failure_artifact(
    manifest: dict[str, object],
    spec: GameSpec,
    duplicate_member: str,
    ordinal: int,
    completed: int,
    completed_game_digests: list[dict[str, str]],
    error: BaseException,
) -> dict[str, object]:
    snapshot = error.snapshot if isinstance(error, SmokeGameFailure) else None
    return {
        "stage": STAGE_ID,
        "accepted_aggregate": False,
        "manifest_digest": manifest["manifest_digest"],
        "active_execution": {
            "game_id": spec.game_id,
            "pairing_id": spec.pairing_id,
            "seed": spec.seed,
            "orientation": spec.orientation,
            "duplicate_member": duplicate_member,
            "execution_ordinal": ordinal,
            "completed_distinct_game_count": completed,
        },
        "failure": {
            "kind": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        },
        "completed_game_digests": completed_game_digests,
        "last_authoritative_state": None
        if snapshot is None
        else {
            "turn": snapshot.get("turn"),
            "phase": snapshot.get("phase"),
            "step": snapshot.get("step"),
            "state_fingerprint": snapshot.get("authoritative_state_fingerprint"),
            "stack": snapshot.get("stack"),
            "priority": snapshot.get("priority"),
        },
    }


def execute_smoke(
    root: Path,
    *,
    output: Path,
    failure_output: Path,
    runner: Runner = run_smoke_game,
) -> dict[str, object]:
    """Execute atomically or preserve the first fail-closed checkpoint."""
    manifest = build_smoke_manifest(root)
    selected = smoke_games()
    if len(selected) != REQUIRED_GAME_COUNT:
        raise RuntimeError("Smoke 0.1 execution requires the complete 180-game matrix")
    reports: list[dict[str, object]] = []
    for game_index, spec in enumerate(selected):
        snapshots: dict[str, dict[str, object]] = {}
        try:
            for member in ("first", "second"):
                snapshots[member] = runner(root, spec, None)
            canonical = {member: canonical_json(value) for member, value in snapshots.items()}
            digests = {
                member: hashlib.sha256(value.encode("utf-8")).hexdigest()
                for member, value in canonical.items()
            }
            if canonical["first"] != canonical["second"]:
                raise RuntimeError("nondeterministic duplicate")
            report = reconcile_snapshot(spec, snapshots["first"], manifest)
            label = _mechanical_label(report, snapshots["first"])
            reports.append(
                {
                    **report,
                    "pairing_id": spec.pairing_id,
                    "mechanical_label": label,
                    "future_balance_candidate": {
                        "eligible_by_coverage": label == "mechanically_clean_coverage_complete",
                        "balance_valid": False,
                        "reason": "Pilot and statistical-design gates are not authorized",
                    },
                    "duplicate_execution_digests": digests,
                    "duplicate_byte_equivalent": True,
                    "duplicate_snapshots": snapshots,
                }
            )
        except Exception as error:
            member = "second" if "first" in snapshots else "first"
            artifact = _failure_artifact(
                manifest,
                spec,
                member,
                game_index * 2 + (2 if member == "second" else 1),
                len(reports),
                [
                    {"game_id": str(report["game_id"]), "report_digest": report["report_digest"]}
                    for report in reports
                ],
                error,
            )
            _atomic_write(failure_output, artifact)
            raise
    coverage_complete = [
        report["game_id"]
        for report in reports
        if report["mechanical_label"] == "mechanically_clean_coverage_complete"
    ]
    coverage_limited = [
        report["game_id"]
        for report in reports
        if report["mechanical_label"] == "mechanically_clean_coverage_limited"
    ]
    aggregate_body = {
        "stage": STAGE_ID,
        "manifest_digest": manifest["manifest_digest"],
        "distinct_game_count": len(reports),
        "execution_count": len(reports) * 2,
        "mechanical_labels": {
            "mechanically_clean_coverage_complete": coverage_complete,
            "mechanically_clean_coverage_limited": coverage_limited,
            "mechanically_invalid": [],
        },
        "future_balance_candidate_games": [
            {
                "game_id": game_id,
                "balance_valid": False,
                "reason": "Pilot and statistical-design gates are not authorized",
            }
            for game_id in coverage_complete
        ],
        "games": reports,
    }
    result_body = {
        "manifest": manifest,
        "aggregate": {**aggregate_body, "aggregate_digest": stable_digest(aggregate_body)},
    }
    result = {**result_body, "raw_artifact_body_digest": stable_digest(result_body)}
    _atomic_write(output, result)
    return result


def validate_smoke_result(result: dict[str, object]) -> None:
    manifest = result.get("manifest")
    aggregate = result.get("aggregate")
    if not isinstance(manifest, dict) or not isinstance(aggregate, dict):
        raise ValueError("Smoke result lacks manifest or aggregate")
    manifest_body = {key: value for key, value in manifest.items() if key != "manifest_digest"}
    if stable_digest(manifest_body) != manifest.get("manifest_digest"):
        raise ValueError("Smoke manifest digest mismatch")
    aggregate_body = {key: value for key, value in aggregate.items() if key != "aggregate_digest"}
    if stable_digest(aggregate_body) != aggregate.get("aggregate_digest"):
        raise ValueError("Smoke aggregate digest mismatch")
    result_body = {key: value for key, value in result.items() if key != "raw_artifact_body_digest"}
    if stable_digest(result_body) != result.get("raw_artifact_body_digest"):
        raise ValueError("Smoke raw artifact body digest mismatch")
    reports = aggregate.get("games")
    if not isinstance(reports, list):
        raise ValueError("Smoke game reports are missing")
    if (
        len(reports) != manifest.get("distinct_game_count")
        or aggregate.get("distinct_game_count") != len(reports)
        or aggregate.get("execution_count") != len(reports) * 2
    ):
        raise ValueError("Smoke result matrix counts are inconsistent")
    labels = aggregate.get("mechanical_labels")
    if not isinstance(labels, dict):
        raise ValueError("Smoke mechanical labels are missing")
    memberships = [game_id for values in labels.values() for game_id in values]
    game_ids = [report.get("game_id") for report in reports]
    if sorted(memberships) != sorted(game_ids) or len(memberships) != len(set(memberships)):
        raise ValueError("Smoke games do not have exactly one mechanical label")
    limited = set(labels.get("mechanically_clean_coverage_limited", []))
    candidates = aggregate.get("future_balance_candidate_games", [])
    if any(
        candidate.get("game_id") in limited or candidate.get("balance_valid") is not False
        for candidate in candidates
    ):
        raise ValueError("coverage-limited or balance-valid game leaked into projection")
    for report in reports:
        snapshots = report.get("duplicate_snapshots")
        digests = report.get("duplicate_execution_digests")
        if not isinstance(snapshots, dict) or not isinstance(digests, dict):
            raise ValueError("Smoke duplicate evidence is missing")
        reconstructed = {
            member: hashlib.sha256(canonical_json(snapshot).encode("utf-8")).hexdigest()
            for member, snapshot in snapshots.items()
        }
        if (
            set(reconstructed) != {"first", "second"}
            or reconstructed != digests
            or digests["first"] != digests["second"]
            or report.get("duplicate_byte_equivalent") is not True
        ):
            raise ValueError("Smoke duplicate evidence is unauthenticated")
        seats = report.get("seats")
        if not isinstance(seats, list) or len(seats) != 2:
            raise ValueError("Smoke report seat evidence is malformed")
        spec = GameSpec(
            str(report.get("game_id")),
            str(report.get("pairing_id")),
            int(report.get("seed")),
            str(report.get("orientation")),
            tuple(DeckSpec(str(seat), "") for seat in seats),
        )
        reconstructed = reconcile_snapshot(spec, snapshots["first"], manifest)
        if any(report.get(key) != value for key, value in reconstructed.items()):
            raise ValueError("Smoke conformance report is not reconstructive")
        if report.get("mechanical_label") != _mechanical_label(reconstructed, snapshots["first"]):
            raise ValueError("Smoke mechanical label is not reconstructive")
