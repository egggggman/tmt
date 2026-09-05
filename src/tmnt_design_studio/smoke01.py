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
FROZEN_IDENTITIES = (
    "bad8104fcef826ef5cfd7fec1bdfe921cdd4c306",
    "761376d5f932fe6cfbbe140d5c76793c9dd5b169",
    "768d25bbed8392a2f92b7b7f06ae8a34e2602423",
    "99e082b2cbcc2446159b4a01c3ca9f89d59a2a3e",
    "964ceb42e13fd0d60fd43346c0b2415bbbe19c30",
    "ec05b95268ba72cd6f0d6b64d9a5dfa1ecd81317",
    "70e5104e109405b2ad0a3bdd93e16c5bf75f39e9",
    "354e56cf9dca8e84e8824afe20cd6239d076fd37",
    "aa02bd4cd5ce78b182d78d2f4d1b819693e2e033",
    "ebcddef99784da507055ff1bac84134e5d355ac6",
    "306fd267482b72f188c69222d57fcc547d654091",
    "ecdffa18463076503f5d338687041f42a3a599d9",
    "d12cb8dca2412eb5267496ef3530f9b95e3032a1",
    "236b8c6607eaed517ed0e582477a3805021028b9",
    "8b69c064bf0c182bcf6eb1505f2e10882bf50c4d",
    "3eb8bfd8654294e1ef7e6137882651801bf1e2d6",
    "5bd2711bdc3cbc37d2315c2cbd9b59e8ae5eaf02",
    "f2fa5e1b3433a749b7b6e1a862a242f4940af1e6",
)
GIT_TEXT_HASH_SCHEME = "git-clean-blob-oid-sha1-v1"
RAW_BINARY_HASH_SCHEME = "raw-bytes-sha256-v1"
FROZEN_INPUTS = {
    path: {"scheme": GIT_TEXT_HASH_SCHEME, "digest": digest}
    for path, digest in zip(FROZEN_PATHS, FROZEN_IDENTITIES, strict=True)
}


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


def _git_text_identity(root: Path, relative: str, source: Path | None = None) -> str:
    """Hash tracked text through explicit Git clean-filter semantics."""
    subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=root,
        check=True,
        capture_output=True,
    )
    candidate = root / relative if source is None else source
    if not candidate.is_file():
        raise ValueError(f"frozen input is missing: {candidate}")
    return subprocess.run(
        [
            "git",
            "-c",
            "core.autocrlf=true",
            "hash-object",
            f"--path={relative}",
            "--",
            str(candidate),
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _input_identity(root: Path, relative: str, contract: dict[str, str]) -> dict[str, str]:
    scheme = contract["scheme"]
    if scheme == GIT_TEXT_HASH_SCHEME:
        digest = _git_text_identity(root, relative)
    elif scheme == RAW_BINARY_HASH_SCHEME:
        digest = _sha256(root / relative)
    else:
        raise ValueError(f"unknown frozen-input hashing scheme: {scheme}")
    return {"scheme": scheme, "digest": digest}


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
    actual_hashes = {
        relative: _input_identity(root, relative, contract)
        for relative, contract in FROZEN_INPUTS.items()
    }
    mismatches = {
        relative: {"expected": FROZEN_INPUTS[relative], "actual": actual}
        for relative, actual in actual_hashes.items()
        if actual != FROZEN_INPUTS[relative]
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
        "hashing_contract": {
            "version": "smoke-frozen-input-hashing-v2",
            "tracked_text": GIT_TEXT_HASH_SCHEME,
            "binary_or_non_git": RAW_BINARY_HASH_SCHEME,
        },
        "runner_identity": {
            "scheme": GIT_TEXT_HASH_SCHEME,
            "digest": _git_text_identity(root, "src/tmnt_design_studio/smoke01.py"),
        },
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
            if game.winner is not None:
                break
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


def _balance_record(label: str) -> dict[str, object]:
    return {
        "eligible_by_coverage": label == "mechanically_clean_coverage_complete",
        "balance_valid": False,
        "reason": "Pilot and statistical-design gates are not authorized",
    }


def _failure_artifact(
    manifest: dict[str, object] | None,
    spec: GameSpec | None,
    duplicate_member: str,
    ordinal: int,
    completed: int,
    completed_game_digests: list[dict[str, str]],
    error: BaseException,
    available_snapshot: dict[str, object] | None = None,
    available_duplicate_digests: dict[str, str] | None = None,
) -> dict[str, object]:
    snapshot = error.snapshot if isinstance(error, SmokeGameFailure) else available_snapshot
    return {
        "stage": STAGE_ID,
        "accepted_aggregate": False,
        "manifest_digest": None if manifest is None else manifest["manifest_digest"],
        "active_execution": {
            "stage": "manifest_preflight" if spec is None else "game_execution",
            "game_id": None if spec is None else spec.game_id,
            "pairing_id": None if spec is None else spec.pairing_id,
            "seed": None if spec is None else spec.seed,
            "orientation": None if spec is None else spec.orientation,
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
        "available_duplicate_digests": available_duplicate_digests or {},
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
    try:
        manifest = build_smoke_manifest(root)
    except Exception as error:
        artifact = _failure_artifact(None, None, "preflight", 0, 0, [], error)
        _atomic_write(failure_output, artifact)
        raise
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
                    "future_balance_candidate": _balance_record(label),
                    "duplicate_execution_digests": digests,
                    "duplicate_byte_equivalent": True,
                    "duplicate_snapshots": snapshots,
                }
            )
        except Exception as error:
            member = "second" if "first" in snapshots else "first"
            available_digests = {
                key: hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
                for key, value in snapshots.items()
            }
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
                snapshots.get("second") or snapshots.get("first"),
                available_digests,
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
                **_balance_record("mechanically_clean_coverage_complete"),
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
    reconstructed_labels = {
        "mechanically_clean_coverage_complete": [],
        "mechanically_clean_coverage_limited": [],
        "mechanically_invalid": [],
    }
    memberships = [game_id for values in labels.values() for game_id in values]
    game_ids = [report.get("game_id") for report in reports]
    if sorted(memberships) != sorted(game_ids) or len(memberships) != len(set(memberships)):
        raise ValueError("Smoke games do not have exactly one mechanical label")
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
        reconstructed_label = _mechanical_label(reconstructed, snapshots["first"])
        if report.get("mechanical_label") != reconstructed_label:
            raise ValueError("Smoke mechanical label is not reconstructive")
        reconstructed_labels[reconstructed_label].append(report["game_id"])
        if report.get("future_balance_candidate") != _balance_record(reconstructed_label):
            raise ValueError("Smoke per-game balance boundary is not reconstructive")
    if labels != reconstructed_labels:
        raise ValueError("Smoke aggregate mechanical labels are not reconstructive")
    expected_candidates = [
        {
            "game_id": game_id,
            **_balance_record("mechanically_clean_coverage_complete"),
        }
        for game_id in reconstructed_labels["mechanically_clean_coverage_complete"]
    ]
    if aggregate.get("future_balance_candidate_games") != expected_candidates:
        raise ValueError("Smoke balance projection is not reconstructive")
