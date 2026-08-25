"""Evidence runner for Coverage-Aware Engine Validation Stage 0.2.

This module parameterizes the accepted Smoke 0.1 game driver and Stage #002
conformance machinery. It adds no gameplay semantics.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import re
import subprocess
import traceback
from collections import defaultdict
from collections.abc import Callable, Iterable
from pathlib import Path

from tmnt_design_studio.engine07 import phase_for_step
from tmnt_design_studio.smoke01 import (
    DECKS,
    SmokeGameFailure,
    _atomic_write,
    _mechanical_label,
    build_smoke_manifest,
    run_smoke_game,
)
from tmnt_design_studio.stage002 import (
    DeckSpec,
    GameSpec,
    canonical_json,
    reconcile_snapshot,
    stable_digest,
)

STAGE_ID = "coverage-aware-engine-validation-0.2"
SCHEMA_VERSION = "coverage-aware-engine-validation-0.2-evidence-v1"
REQUIRED_PAIRING_COUNT = 45
REQUIRED_SEED_ASSIGNMENT_COUNT = 225
REQUIRED_GAME_COUNT = 450
REQUIRED_EXECUTION_COUNT = 900
TURN_CAP = 120

Runner = Callable[[Path, GameSpec, object | None], dict[str, object]]
AUTHORITY_PREIMAGE_SCHEME = "engine07-authoritative-state-fingerprint-preimage-v1"
EXECUTION_COMMITMENT_SCHEME = "stage02-independent-execution-commitment-v1"


def _authority_tuple_from_preimage(preimage: object) -> tuple[object, ...]:
    """Reconstruct the exact tuple hashed by Game.authoritative_state_fingerprint()."""
    if not isinstance(preimage, dict) or preimage.get("scheme") != AUTHORITY_PREIMAGE_SCHEME:
        raise ValueError("authoritative-state fingerprint preimage is missing or unsupported")
    players = preimage.get("players")
    if not isinstance(players, list) or len(players) != 2:
        raise ValueError("authoritative-state player preimage is malformed")
    zones = []
    for player in players:
        if not isinstance(player, dict):
            raise ValueError("authoritative-state player preimage is malformed")
        zone_values = []
        for key in (
            "library_object_ids",
            "hand_object_ids",
            "battlefield_object_ids",
            "graveyard_object_ids",
        ):
            values = player.get(key)
            if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
                raise ValueError("authoritative-state zone preimage is malformed")
            zone_values.append(tuple(values))
        life = player.get("life")
        lost = player.get("lost")
        failed_draw = player.get("failed_draw_pending")
        if (
            not isinstance(life, int)
            or not isinstance(lost, bool)
            or not isinstance(failed_draw, bool)
        ):
            raise ValueError("authoritative-state player facts are malformed")
        zones.append((*zone_values, life, lost, failed_draw))
    stack = preimage.get("stack_object_ids")
    attackers = preimage.get("combat_attacker_ids")
    blocks = preimage.get("combat_blocks")
    if (
        not isinstance(stack, list)
        or any(not isinstance(value, str) for value in stack)
        or not isinstance(attackers, list)
        or any(not isinstance(value, str) for value in attackers)
        or not isinstance(blocks, list)
        or any(
            not isinstance(item, list)
            or len(item) != 2
            or any(not isinstance(value, str) for value in item)
            for item in blocks
        )
    ):
        raise ValueError("authoritative-state combat or Stack preimage is malformed")
    turn = preimage.get("turn")
    active = preimage.get("active_player_index")
    step = preimage.get("step")
    rng_digest = preimage.get("rng_state_digest")
    winner = preimage.get("winner_index")
    if (
        not isinstance(turn, int)
        or active not in {0, 1}
        or not isinstance(step, str)
        or not isinstance(rng_digest, str)
        or (winner is not None and winner not in {0, 1})
    ):
        raise ValueError("authoritative-state scalar preimage is malformed")
    return (
        turn,
        active,
        step,
        tuple(stack),
        tuple(attackers),
        tuple(tuple(item) for item in blocks),
        tuple(zones),
        rng_digest,
        winner,
    )


def _fingerprint_from_preimage(preimage: object) -> str:
    authority = _authority_tuple_from_preimage(preimage)
    return hashlib.sha256(repr(authority).encode("utf-8")).hexdigest()


def _authoritative_state_stops(snapshot: dict[str, object]) -> list[str]:
    """Join serialized projections to the independently reconstructible engine commitment."""
    try:
        authority = _authority_tuple_from_preimage(
            snapshot.get("authoritative_state_fingerprint_preimage")
        )
    except ValueError as error:
        return [str(error)]
    stops: list[str] = []
    reconstructed = hashlib.sha256(repr(authority).encode("utf-8")).hexdigest()
    if snapshot.get("authoritative_state_fingerprint") != reconstructed:
        stops.append("authoritative-state fingerprint does not reconstruct from its preimage")
    players = snapshot.get("players")
    stack = snapshot.get("stack")
    rng = snapshot.get("rng")
    if (
        not isinstance(players, list)
        or len(players) != 2
        or not isinstance(stack, list)
        or not isinstance(rng, dict)
    ):
        return [*stops, "authoritative-state snapshot projections are malformed"]
    names = [player.get("name") for player in players]
    if snapshot.get("turn") != authority[0]:
        stops.append("authoritative-state turn projection disagrees")
    if authority[1] not in {0, 1} or snapshot.get("active_player") != names[authority[1]]:
        stops.append("authoritative-state active-player projection disagrees")
    if snapshot.get("step") != authority[2]:
        stops.append("authoritative-state step projection disagrees")
    try:
        expected_phase = phase_for_step(str(authority[2]))
    except ValueError:
        stops.append("authoritative-state step is not supported by the engine turn structure")
    else:
        if snapshot.get("phase") != expected_phase:
            stops.append("authoritative-state phase does not derive from authenticated step")
    if [item.get("object_id") for item in stack] != list(authority[3]):
        stops.append("authoritative-state Stack projection disagrees")
    if rng.get("state_digest") != authority[7]:
        stops.append("authoritative-state RNG projection disagrees")
    expected_winner = None if authority[8] is None else names[authority[8]]
    if snapshot.get("winner") != expected_winner:
        stops.append("authoritative-state winner projection disagrees")
    for index, player in enumerate(players):
        zone_state = authority[6][index]
        battlefield = player.get("battlefield")
        if not isinstance(battlefield, list):
            stops.append("authoritative-state battlefield projection is malformed")
            continue
        comparisons = (
            (player.get("library"), len(zone_state[0])),
            (player.get("library_object_ids"), list(zone_state[0])),
            (player.get("hand_object_ids"), list(zone_state[1])),
            (len(player.get("hand", [])), len(zone_state[1])),
            ([item.get("object_id") for item in battlefield], list(zone_state[2])),
            (player.get("graveyard_object_ids"), list(zone_state[3])),
            (len(player.get("graveyard", [])), len(zone_state[3])),
            (player.get("life"), zone_state[4]),
            (player.get("lost"), zone_state[5]),
            (player.get("failed_draw_pending"), zone_state[6]),
        )
        if any(left != right for left, right in comparisons):
            stops.append(f"authoritative-state player projection disagrees for index {index}")
    return stops


def commitment_directory_for(output: Path) -> Path:
    """Locate the independent execution-commitment channel for one result path."""
    return output.with_name(f"{output.name}.commitments")


def _execution_commitment(
    spec: GameSpec,
    member: str,
    ordinal: int,
    snapshot: dict[str, object],
) -> dict[str, object]:
    """Bind a complete authoritative execution snapshot outside the result body."""
    stops = _authoritative_state_stops(snapshot)
    if stops:
        raise ValueError(f"execution commitment state does not reconstruct: {stops}")
    preimage = snapshot["authoritative_state_fingerprint_preimage"]
    body = {
        "scheme": EXECUTION_COMMITMENT_SCHEME,
        "execution_ordinal": ordinal,
        "game_id": spec.game_id,
        "pairing_id": spec.pairing_id,
        "seed": spec.seed,
        "orientation": spec.orientation,
        "seats": [seat.display_id for seat in spec.seats],
        "duplicate_member": member,
        "snapshot_sha256": hashlib.sha256(canonical_json(snapshot).encode("utf-8")).hexdigest(),
        "authoritative_state_fingerprint": snapshot["authoritative_state_fingerprint"],
        "authoritative_preimage_sha256": hashlib.sha256(
            canonical_json(preimage).encode("utf-8")
        ).hexdigest(),
        "terminal": snapshot.get("winner") is not None,
        "winner": snapshot.get("winner"),
        "turn": snapshot.get("turn"),
        "phase": snapshot.get("phase"),
        "step": snapshot.get("step"),
    }
    return {**body, "commitment_digest": stable_digest(body)}


def _commitment_path(directory: Path, ordinal: int) -> Path:
    return directory / f"execution-{ordinal:04d}.json"


def _persist_execution_commitment(directory: Path, record: dict[str, object]) -> None:
    path = _commitment_path(directory, int(record["execution_ordinal"]))
    if path.exists() or path.with_suffix(path.suffix + ".sha256").exists():
        raise ValueError("independent execution commitment path is not empty")
    try:
        digest = _atomic_write(path, record)
        _validate_written_pair(path, digest)
    except Exception:
        _remove_incomplete_pair(path)
        raise


def load_execution_commitments(directory: Path) -> list[dict[str, object]]:
    """Authenticate the independent per-execution JSON+sidecar evidence channel."""
    if not directory.is_dir():
        raise ValueError("independent execution commitment channel is missing")
    entries = {path.name for path in directory.iterdir()}
    json_pattern = re.compile(r"execution-[0-9]{4}\.json")
    json_paths = sorted(
        path for path in directory.iterdir() if path.is_file() and json_pattern.fullmatch(path.name)
    )
    expected_inventory = {
        name for path in json_paths for name in (path.name, f"{path.name}.sha256")
    }
    if entries != expected_inventory:
        raise ValueError("independent execution commitment inventory is not exact")
    records: list[dict[str, object]] = []
    for path in json_paths:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        _validate_written_pair(path, digest)
        record = json.loads(path.read_text(encoding="utf-8"))
        body = {key: value for key, value in record.items() if key != "commitment_digest"}
        if record.get("scheme") != EXECUTION_COMMITMENT_SCHEME or stable_digest(body) != record.get(
            "commitment_digest"
        ):
            raise ValueError("independent execution commitment is malformed")
        records.append(record)
    ordinals = [record.get("execution_ordinal") for record in records]
    if ordinals != list(range(1, len(records) + 1)):
        raise ValueError("independent execution commitment ordering is incomplete")
    return records


def _commitment_channel(records: list[dict[str, object]], directory: Path) -> dict[str, object]:
    return {
        "scheme": EXECUTION_COMMITMENT_SCHEME,
        "directory_name": directory.name,
        "record_count": len(records),
        "commitment_digests": [record["commitment_digest"] for record in records],
    }


def _validate_commitment_join(
    records: list[dict[str, object]],
    reports: list[dict[str, object]],
    channel: object,
    directory: Path,
) -> None:
    if channel != _commitment_channel(records, directory):
        raise ValueError("result commitment references disagree with independent channel")
    expected: list[dict[str, object]] = []
    for game_index, report in enumerate(reports):
        spec = _game_spec_from_report(report)
        for offset, member in enumerate(("first", "second"), 1):
            expected.append(
                _execution_commitment(
                    spec,
                    member,
                    game_index * 2 + offset,
                    report["duplicate_snapshots"][member],
                )
            )
    if records != expected:
        raise ValueError("execution snapshots do not reconstruct independent commitments")


def _terminal_outcome_stops(snapshot: dict[str, object]) -> list[str]:
    """Reconstruct one terminal winner from authoritative player-loss state/evidence."""
    players = snapshot.get("players")
    events = snapshot.get("events")
    winner = snapshot.get("winner")
    if not isinstance(players, list) or len(players) != 2 or not isinstance(events, list):
        return ["terminal player state is malformed"]
    if winner is None:
        return []
    names = [player.get("name") for player in players]
    if any(not isinstance(name, str) or not name for name in names) or len(set(names)) != 2:
        return ["terminal player identity is malformed"]
    lost_indices = [index for index, player in enumerate(players) if player.get("lost") is True]
    stops: list[str] = []
    if len(lost_indices) != 1:
        stops.append("terminal result does not have exactly one authoritative loser")
        return stops
    loser_index = lost_indices[0]
    loser = players[loser_index]
    expected_winner = names[1 - loser_index]
    if winner != expected_winner:
        stops.append("serialized winner disagrees with authoritative player-loss state")
    reason = loser.get("loss_reason")
    if reason == "life_zero_or_less":
        life = loser.get("life")
        if not isinstance(life, int) or life > 0:
            stops.append("life-loss terminal result lacks authoritative lethal life state")
    elif reason == "draw_from_empty_library":
        if loser.get("library") != 0 or loser.get("failed_draw_pending") is not False:
            stops.append("failed-Draw terminal result lacks authoritative resolved Draw state")
    else:
        stops.append("terminal loss reason is unsupported or missing")
    loss_events = [event for event in events if event.get("event") == "player_lost"]
    if len(loss_events) != 1 or (
        loss_events[0].get("player"),
        loss_events[0].get("reason"),
    ) != (names[loser_index], reason):
        stops.append("terminal player-loss event does not authenticate the result")
    if players[1 - loser_index].get("lost") is not False:
        stops.append("terminal winner is not authoritative as a surviving player")
    return stops


def stage02_games() -> tuple[GameSpec, ...]:
    """Return the frozen 45 x 5 x 2 Stage 0.2 matrix."""
    games: list[GameSpec] = []
    for pairing_index, (first, second) in enumerate(itertools.combinations(DECKS, 2)):
        pairing_id = f"{first.display_id}--{second.display_id}"
        for seed in range(9001 + 5 * pairing_index, 9006 + 5 * pairing_index):
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


def _git_clean_candidate_identity(root: Path, relative: str) -> str:
    """Compute the eventual Git-clean blob identity for a runner candidate."""
    path = root / relative
    if not path.is_file():
        raise ValueError(f"Stage 0.2 tooling input is missing: {relative}")
    return subprocess.run(
        [
            "git",
            "-c",
            "core.autocrlf=true",
            "hash-object",
            f"--path={relative}",
            "--",
            str(path),
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _matrix_rows(games: Iterable[GameSpec]) -> list[dict[str, object]]:
    return [
        {
            "game_id": game.game_id,
            "pairing_id": game.pairing_id,
            "seed": game.seed,
            "orientation": game.orientation,
            "seats": [seat.display_id for seat in game.seats],
        }
        for game in games
    ]


def _validate_matrix_rows(rows: list[dict[str, object]]) -> None:
    expected = _matrix_rows(stage02_games())
    if rows != expected:
        raise ValueError("Stage 0.2 matrix does not reconstruct")
    if (
        len(rows) != REQUIRED_GAME_COUNT
        or len({str(row["game_id"]) for row in rows}) != REQUIRED_GAME_COUNT
        or len({str(row["pairing_id"]) for row in rows}) != REQUIRED_PAIRING_COUNT
    ):
        raise ValueError("Stage 0.2 matrix count or identity mismatch")
    assignments = {(str(row["pairing_id"]), int(row["seed"])) for row in rows}
    if len(assignments) != REQUIRED_SEED_ASSIGNMENT_COUNT:
        raise ValueError("Stage 0.2 seed-assignment count mismatch")
    seeds = {seed for _pairing, seed in assignments}
    expected_seeds = {int(row["seed"]) for row in expected}
    if seeds != expected_seeds:
        raise ValueError("Stage 0.2 seed range mismatch")
    for pairing in {str(row["pairing_id"]) for row in rows}:
        pairing_seeds = {int(row["seed"]) for row in rows if row["pairing_id"] == pairing}
        expected_pairing_seeds = {
            int(row["seed"]) for row in expected if row["pairing_id"] == pairing
        }
        if pairing_seeds != expected_pairing_seeds:
            raise ValueError("Stage 0.2 pairing does not have five seeds")
        for seed in pairing_seeds:
            orientations = {
                str(row["orientation"])
                for row in rows
                if row["pairing_id"] == pairing and row["seed"] == seed
            }
            expected_orientations = {
                str(row["orientation"])
                for row in expected
                if row["pairing_id"] == pairing and row["seed"] == seed
            }
            if orientations != expected_orientations:
                raise ValueError("Stage 0.2 seed lacks both orientations")


def build_stage02_manifest(root: Path) -> dict[str, object]:
    """Reconstruct Stage 0.2 without creating a Game or consuming gameplay RNG."""
    smoke = build_smoke_manifest(root)
    smoke_body = {key: value for key, value in smoke.items() if key != "manifest_digest"}
    games = _matrix_rows(stage02_games())
    _validate_matrix_rows(games)
    accepted_smoke_runner = smoke_body["runner_identity"]
    body = {
        **smoke_body,
        "stage": STAGE_ID,
        "schema_version": SCHEMA_VERSION,
        "accepted_smoke_runner_identity": accepted_smoke_runner,
        "runner_identity": {
            "scheme": "git-clean-blob-oid-sha1-v1",
            "digest": _git_clean_candidate_identity(root, "src/tmnt_design_studio/stage02.py"),
        },
        "launcher_identity": {
            "scheme": "git-clean-blob-oid-sha1-v1",
            "digest": _git_clean_candidate_identity(
                root, "scripts/run_coverage_aware_engine_validation_02.py"
            ),
        },
        "games": games,
        "pairing_count": REQUIRED_PAIRING_COUNT,
        "seed_assignment_count": REQUIRED_SEED_ASSIGNMENT_COUNT,
        "distinct_game_count": REQUIRED_GAME_COUNT,
        "duplicate_executions_per_game": 2,
        "execution_count": REQUIRED_EXECUTION_COUNT,
        "turn_cap": TURN_CAP,
        "artifact_policy": {
            "external_paths_required": True,
            "ordinary_git_history_forbidden": True,
            "atomic_json_and_sha256_sidecar": True,
            "execution_commitment_scheme": EXECUTION_COMMITMENT_SCHEME,
            "execution_commitments_are_independent_artifacts": True,
            "execution_commitment_order": "execution_ordinal_ascending",
            "execution_commitment_digest": "canonical-json-sha256",
        },
        "balance_policy": {
            "balance_valid": False,
            "reason": "Pilot and statistical balance gates are not authorized",
        },
    }
    return {**body, "manifest_digest": stable_digest(body)}


def plan(root: Path) -> dict[str, object]:
    return {"authorized": False, "manifest": build_stage02_manifest(root)}


def _balance_record() -> dict[str, object]:
    return {
        "balance_valid": False,
        "reason": "Pilot and statistical balance gates are not authorized",
    }


def _original_event_evidence_stops(snapshot: dict[str, object]) -> list[str]:
    records = snapshot.get("rules_event_evidence", [])
    events = snapshot.get("events", [])
    players = snapshot.get("players", [])
    if (
        not isinstance(records, list)
        or not isinstance(events, list)
        or not isinstance(players, list)
    ):
        return ["original rules-event collections are malformed"]
    ledger = [event for event in events if event.get("event") == "rules_event"]
    record_ids = [record.get("event_id") for record in records]
    ledger_ids = [event.get("event_id") for event in ledger]
    stops: list[str] = []
    if len(record_ids) != len(set(record_ids)) or len(ledger_ids) != len(set(ledger_ids)):
        stops.append("original rules-event identity is duplicated")
    if record_ids != ledger_ids:
        stops.append("rules-event registry and original ledger membership disagree")
    expected_cursors = list(range(1, len(records) + 1))
    if [record.get("event_cursor") for record in records] != expected_cursors:
        stops.append("original rules-event cursor sequence is malformed")
    ledger_by_id = {event.get("event_id"): event for event in ledger}
    for record in records:
        event_id = record.get("event_id")
        event = ledger_by_id.get(event_id)
        if event is None:
            continue
        player_index = record.get("player_index")
        player_name = None
        if isinstance(player_index, int) and 0 <= player_index < len(players):
            player_name = players[player_index].get("name")
        comparisons = (
            (event.get("rules_event"), record.get("kind")),
            (event.get("player"), player_name),
            (event.get("subject_ids"), record.get("subject_ids")),
            (event.get("source_id"), record.get("source_id")),
            (event.get("target_player"), record.get("target_player")),
            (event.get("amount"), record.get("amount")),
            (event.get("event_turn"), record.get("turn")),
            (event.get("event_step"), record.get("step")),
            (event.get("event_active_player"), record.get("active_player")),
            (event.get("battlefield_authority"), record.get("battlefield_authority")),
            (
                event.get("battlefield_characteristics"),
                record.get("battlefield_characteristics"),
            ),
            (event.get("last_known_battlefield"), record.get("last_known_battlefield")),
        )
        if any(left != right for left, right in comparisons):
            stops.append(f"original rules-event evidence disagrees for {event_id}")
    return stops


def _report_for(
    spec: GameSpec,
    snapshots: dict[str, dict[str, object]],
    manifest: dict[str, object],
) -> dict[str, object]:
    canonical = {member: canonical_json(snapshot) for member, snapshot in snapshots.items()}
    digests = {
        member: hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        for member, rendered in canonical.items()
    }
    if set(snapshots) != {"first", "second"} or canonical["first"] != canonical["second"]:
        raise RuntimeError("nondeterministic duplicate")
    original_event_stops = _original_event_evidence_stops(snapshots["first"])
    if original_event_stops:
        raise RuntimeError(f"original event evidence failure: {original_event_stops}")
    authority_stops = _authoritative_state_stops(snapshots["first"])
    if authority_stops:
        raise RuntimeError(f"authoritative state evidence failure: {authority_stops}")
    terminal_stops = _terminal_outcome_stops(snapshots["first"])
    if terminal_stops:
        raise RuntimeError(f"terminal outcome evidence failure: {terminal_stops}")
    report = reconcile_snapshot(spec, snapshots["first"], manifest)
    label = _mechanical_label(report, snapshots["first"])
    return {
        **report,
        "pairing_id": spec.pairing_id,
        "mechanical_label": label,
        "balance": _balance_record(),
        "distinct_game_weight": 1,
        "duplicate_execution_count": 2,
        "duplicate_execution_digests": digests,
        "duplicate_byte_equivalent": True,
        "duplicate_snapshots": snapshots,
    }


def _coverage_dimensions(reports: list[dict[str, object]]) -> dict[str, object]:
    classes = ("executed", "reached_unsupported", "present_unreached")
    groups: dict[str, dict[str, list[dict[str, object]]]] = {
        "pairing": defaultdict(list),
        "seed": defaultdict(list),
        "orientation": defaultdict(list),
        "deck": defaultdict(list),
    }
    for report in reports:
        groups["pairing"][str(report["pairing_id"])].append(report)
        groups["seed"][str(report["seed"])].append(report)
        groups["orientation"][str(report["orientation"])].append(report)
        for deck in report["seats"]:
            groups["deck"][str(deck)].append(report)

    def summary(items: list[dict[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for classification in classes:
            sets = [set(item["classification_sets"][classification]) for item in items]
            result[classification] = {
                "union": sorted(set().union(*sets) if sets else set()),
                "intersection": sorted(set.intersection(*sets) if sets else set()),
            }
        return result

    return {
        "all_games": summary(reports),
        **{
            dimension: {key: summary(items) for key, items in sorted(dimension_groups.items())}
            for dimension, dimension_groups in groups.items()
        },
    }


def _semantic_memberships(reports: list[dict[str, object]]) -> list[dict[str, object]]:
    entries: dict[tuple[str, str], dict[str, object]] = {}
    for report in reports:
        for occurrence in report["occurrences"]:
            key = (str(occurrence["semantic_key"]), str(occurrence["classification"]))
            entry = entries.setdefault(
                key,
                {
                    "semantic_key": key[0],
                    "classification": key[1],
                    "occurrence_ids": [],
                    "game_ids": set(),
                    "pairing_ids": set(),
                    "seeds": set(),
                    "orientations": set(),
                    "decks": set(),
                },
            )
            entry["occurrence_ids"].append(f"{report['game_id']}:{occurrence['occurrence_id']}")
            entry["game_ids"].add(report["game_id"])
            entry["pairing_ids"].add(report["pairing_id"])
            entry["seeds"].add(report["seed"])
            entry["orientations"].add(report["orientation"])
            entry["decks"].update(report["seats"])
    result = []
    for entry in entries.values():
        occurrence_ids = sorted(entry["occurrence_ids"])
        result.append(
            {
                "semantic_key": entry["semantic_key"],
                "classification": entry["classification"],
                "occurrence_count": len(occurrence_ids),
                "occurrence_ids": occurrence_ids,
                "game_ids": sorted(entry["game_ids"]),
                "pairing_ids": sorted(entry["pairing_ids"]),
                "seeds": sorted(entry["seeds"]),
                "orientations": sorted(entry["orientations"]),
                "decks": sorted(entry["decks"]),
            }
        )
    return sorted(result, key=lambda item: (item["semantic_key"], item["classification"]))


def _aggregate(reports: list[dict[str, object]], manifest: dict[str, object]) -> dict[str, object]:
    labels = {
        "mechanically_clean_coverage_complete": [],
        "mechanically_clean_coverage_limited": [],
        "mechanically_invalid": [],
    }
    for report in reports:
        labels[str(report["mechanical_label"])].append(report["game_id"])
    occurrence_counts: dict[str, int] = defaultdict(int)
    for report in reports:
        for occurrence in report["occurrences"]:
            occurrence_counts[str(occurrence["classification"])] += 1
    body = {
        "stage": STAGE_ID,
        "schema_version": SCHEMA_VERSION,
        "manifest_digest": manifest["manifest_digest"],
        "pairing_count": REQUIRED_PAIRING_COUNT,
        "seed_assignment_count": REQUIRED_SEED_ASSIGNMENT_COUNT,
        "distinct_game_count": len(reports),
        "execution_count": len(reports) * 2,
        "duplicate_pair_count": len(reports),
        "mechanical_labels": labels,
        "balance_valid": False,
        "balance_records": [
            {"game_id": report["game_id"], **_balance_record()} for report in reports
        ],
        "occurrence_counts": dict(sorted(occurrence_counts.items())),
        "semantic_memberships": _semantic_memberships(reports),
        "coverage": _coverage_dimensions(reports),
        "games": reports,
    }
    return {**body, "aggregate_digest": stable_digest(body)}


def _failure_artifact(
    *,
    manifest: dict[str, object] | None,
    stage: str,
    spec: GameSpec | None,
    member: str,
    ordinal: int,
    completed_reports: list[dict[str, object]],
    error: BaseException,
    snapshots: dict[str, dict[str, object]] | None = None,
    commitments: list[dict[str, object]] | None = None,
    commitment_directory: Path | None = None,
) -> dict[str, object]:
    available = snapshots or {}
    completed_evidence = list(completed_reports)
    last_completed = completed_evidence[-1] if completed_evidence else None
    last_completed_snapshots = (
        last_completed.get("duplicate_snapshots", {}) if isinstance(last_completed, dict) else {}
    )
    last = (
        available.get("second")
        or available.get("first")
        or last_completed_snapshots.get("second")
        or last_completed_snapshots.get("first")
    )
    body = {
        "stage": STAGE_ID,
        "schema_version": SCHEMA_VERSION,
        "status": "failed",
        "accepted_aggregate": False,
        "success_artifact_valid": False,
        "balance_valid": False,
        "manifest_digest": None if manifest is None else manifest.get("manifest_digest"),
        "manifest": manifest,
        "active_execution": {
            "stage": stage,
            "game_id": None if spec is None else spec.game_id,
            "pairing_id": None if spec is None else spec.pairing_id,
            "seed": None if spec is None else spec.seed,
            "orientation": None if spec is None else spec.orientation,
            "duplicate_member": member,
            "execution_ordinal": ordinal,
            "completed_distinct_game_count": len(completed_reports),
        },
        "failure": {
            "kind": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        },
        "completed_game_digests": [
            {"game_id": report["game_id"], "report_digest": report["report_digest"]}
            for report in completed_reports
        ],
        "completed_game_evidence": completed_evidence,
        "available_duplicate_digests": {
            key: hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
            for key, value in available.items()
        },
        "available_duplicate_snapshots": available,
        "execution_commitment_channel": None
        if commitment_directory is None
        else _commitment_channel(commitments or [], commitment_directory),
        "last_authoritative_snapshot": last,
        "last_authoritative_state": None
        if last is None
        else {
            "turn": last.get("turn"),
            "phase": last.get("phase"),
            "step": last.get("step"),
            "winner": last.get("winner"),
            "state_fingerprint": last.get("authoritative_state_fingerprint"),
            "stack": last.get("stack"),
            "priority": last.get("priority"),
            "pending_triggers": last.get("pending_triggers"),
            "invariant_violations": [
                event
                for event in last.get("events", [])
                if event.get("event") == "invariant_violation"
            ],
        },
    }
    return {**body, "failure_body_digest": stable_digest(body)}


def validate_failure_artifact(
    artifact: dict[str, object],
    *,
    commitments: list[dict[str, object]] | None = None,
    commitment_directory: Path | None = None,
) -> None:
    body = {key: value for key, value in artifact.items() if key != "failure_body_digest"}
    if stable_digest(body) != artifact.get("failure_body_digest"):
        raise ValueError("Stage 0.2 failure body digest mismatch")
    if (
        artifact.get("stage") != STAGE_ID
        or artifact.get("status") != "failed"
        or artifact.get("accepted_aggregate") is not False
        or artifact.get("success_artifact_valid") is not False
        or artifact.get("balance_valid") is not False
        or "aggregate" in artifact
    ):
        raise ValueError("Stage 0.2 failure artifact can masquerade as success")
    active = artifact.get("active_execution")
    failure = artifact.get("failure")
    completed = artifact.get("completed_game_evidence")
    completed_digests = artifact.get("completed_game_digests")
    available = artifact.get("available_duplicate_snapshots")
    available_digests = artifact.get("available_duplicate_digests")
    if (
        not isinstance(active, dict)
        or not isinstance(failure, dict)
        or not isinstance(completed, list)
        or not isinstance(completed_digests, list)
        or not isinstance(available, dict)
        or not isinstance(available_digests, dict)
        or not isinstance(failure.get("kind"), str)
        or not isinstance(failure.get("message"), str)
    ):
        raise ValueError("Stage 0.2 failure diagnostic structure is incomplete")
    manifest = artifact.get("manifest")
    if manifest is None:
        if artifact.get("manifest_digest") is not None:
            raise ValueError("Stage 0.2 preflight manifest evidence is inconsistent")
    elif not isinstance(manifest, dict):
        raise ValueError("Stage 0.2 failure manifest is malformed")
    else:
        manifest_body = {key: value for key, value in manifest.items() if key != "manifest_digest"}
        if stable_digest(manifest_body) != manifest.get("manifest_digest") or artifact.get(
            "manifest_digest"
        ) != manifest.get("manifest_digest"):
            raise ValueError("Stage 0.2 failure manifest does not authenticate")
    stage = active.get("stage")
    if stage not in {
        "manifest_preflight",
        "matrix_preflight",
        "game_execution",
        "execution_commitment_persistence",
        "aggregate_reconstruction",
        "final_success_serialization",
    }:
        raise ValueError("Stage 0.2 failure phase is unsupported")
    expected_completed_digests = [
        {"game_id": report.get("game_id"), "report_digest": report.get("report_digest")}
        for report in completed
    ]
    if completed_digests != expected_completed_digests or active.get(
        "completed_distinct_game_count"
    ) != len(completed):
        raise ValueError("Stage 0.2 completed failure evidence is inconsistent")
    for report in completed:
        report_snapshots = report.get("duplicate_snapshots")
        report_digests = report.get("duplicate_execution_digests")
        if not isinstance(report_snapshots, dict) or not isinstance(report_digests, dict):
            raise ValueError("Stage 0.2 completed report lacks duplicate evidence")
        reconstructed = {
            member: hashlib.sha256(canonical_json(snapshot).encode("utf-8")).hexdigest()
            for member, snapshot in report_snapshots.items()
        }
        if (
            set(reconstructed) != {"first", "second"}
            or reconstructed != report_digests
            or reconstructed["first"] != reconstructed["second"]
            or report_snapshots["first"] != report_snapshots["second"]
        ):
            raise ValueError("Stage 0.2 completed failure duplicate evidence is invalid")
        if manifest is None:
            raise ValueError("Stage 0.2 completed evidence lacks its frozen manifest")
        spec = _game_spec_from_report(report)
        try:
            reconstructed_report = _report_for(spec, report_snapshots, manifest)
        except (RuntimeError, ValueError) as error:
            raise ValueError("Stage 0.2 completed failure report does not reconstruct") from error
        if reconstructed_report != report:
            raise ValueError("Stage 0.2 completed failure report is not authentic")
    reconstructed_available = {
        member: hashlib.sha256(canonical_json(snapshot).encode("utf-8")).hexdigest()
        for member, snapshot in available.items()
    }
    if reconstructed_available != available_digests or not set(available).issubset(
        {"first", "second"}
    ):
        raise ValueError("Stage 0.2 available failure evidence is inconsistent")
    for snapshot in available.values():
        authority_stops = _authoritative_state_stops(snapshot)
        if authority_stops:
            raise ValueError(
                f"Stage 0.2 available authoritative state does not reconstruct: {authority_stops}"
            )
    records = commitments or []
    channel = artifact.get("execution_commitment_channel")
    if commitment_directory is None:
        if channel is not None:
            raise ValueError("Stage 0.2 failure commitment channel was not supplied")
    elif channel != _commitment_channel(records, commitment_directory):
        raise ValueError("Stage 0.2 failure commitment references do not authenticate")
    available_specs: list[tuple[GameSpec, str, int, dict[str, object]]] = []
    for report_index, report in enumerate(completed):
        report_spec = _game_spec_from_report(report)
        for offset, duplicate_member in enumerate(("first", "second"), 1):
            available_specs.append(
                (
                    report_spec,
                    duplicate_member,
                    report_index * 2 + offset,
                    report["duplicate_snapshots"][duplicate_member],
                )
            )
    if isinstance(active.get("game_id"), str):
        if not isinstance(manifest, dict):
            raise ValueError("Stage 0.2 game failure lacks commitment manifest evidence")
        active_spec = GameSpec(
            str(active["game_id"]),
            str(active["pairing_id"]),
            int(active["seed"]),
            str(active["orientation"]),
            tuple(
                DeckSpec(str(seat), "")
                for seat in manifest["games"][int(active["execution_ordinal"] - 1) // 2]["seats"]
            ),
        )
        for duplicate_member, snapshot in available.items():
            ordinal = int(active["execution_ordinal"])
            if duplicate_member == "first":
                ordinal = ((ordinal - 1) // 2) * 2 + 1
            available_specs.append((active_spec, duplicate_member, ordinal, snapshot))
    expected_records = [
        _execution_commitment(spec, member, ordinal, snapshot)
        for spec, member, ordinal, snapshot in available_specs
    ]
    if records != expected_records and stage != "execution_commitment_persistence":
        raise ValueError("Stage 0.2 failure snapshots do not reconstruct commitments")
    if stage == "execution_commitment_persistence" and records != expected_records[: len(records)]:
        raise ValueError("Stage 0.2 persisted failure commitments are not an authentic prefix")
    last_completed_snapshots = completed[-1].get("duplicate_snapshots", {}) if completed else {}
    expected_last = (
        available.get("second")
        or available.get("first")
        or last_completed_snapshots.get("second")
        or last_completed_snapshots.get("first")
    )
    if artifact.get("last_authoritative_snapshot") != expected_last:
        raise ValueError("Stage 0.2 last authoritative snapshot is inconsistent")
    expected_last_state = None
    if expected_last is not None:
        expected_last_state = {
            "turn": expected_last.get("turn"),
            "phase": expected_last.get("phase"),
            "step": expected_last.get("step"),
            "winner": expected_last.get("winner"),
            "state_fingerprint": expected_last.get("authoritative_state_fingerprint"),
            "stack": expected_last.get("stack"),
            "priority": expected_last.get("priority"),
            "pending_triggers": expected_last.get("pending_triggers"),
            "invariant_violations": [
                event
                for event in expected_last.get("events", [])
                if event.get("event") == "invariant_violation"
            ],
        }
    if artifact.get("last_authoritative_state") != expected_last_state:
        raise ValueError("Stage 0.2 last authoritative state is inconsistent")
    if stage in {"manifest_preflight", "matrix_preflight"} and (
        completed or available or expected_last is not None
    ):
        raise ValueError("Stage 0.2 preflight failure contains impossible game evidence")
    if stage == "game_execution" and failure.get("kind") == "SmokeGameFailure" and not available:
        raise ValueError("Stage 0.2 inherited game failure lost its authoritative snapshot")
    if stage in {"aggregate_reconstruction", "final_success_serialization"} and (
        not completed or expected_last is None
    ):
        raise ValueError("Stage 0.2 late failure lacks completed authoritative evidence")


def _external_path(root: Path, path: Path) -> Path:
    resolved_root = root.resolve()
    resolved = path.resolve()
    if resolved == resolved_root or resolved_root in resolved.parents:
        raise ValueError("Stage 0.2 raw artifacts must be outside ordinary repository history")
    return resolved


def _remove_incomplete_pair(path: Path) -> None:
    candidates = (
        path,
        path.with_suffix(path.suffix + ".sha256"),
        path.with_name(f".{path.name}.tmp"),
        path.with_suffix(path.suffix + ".sha256").with_name(
            f".{path.with_suffix(path.suffix + '.sha256').name}.tmp"
        ),
    )
    for candidate in candidates:
        if candidate.exists():
            candidate.unlink()


def _write_failure(
    path: Path,
    artifact: dict[str, object],
    *,
    commitments: list[dict[str, object]],
    commitment_directory: Path,
) -> None:
    validate_failure_artifact(
        artifact,
        commitments=commitments,
        commitment_directory=commitment_directory,
    )
    _atomic_write(path, artifact)


def _validate_written_pair(path: Path, expected_digest: str) -> None:
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    sidecar = path.with_suffix(path.suffix + ".sha256")
    expected_line = f"{expected_digest}  {path.name}\n"
    if actual != expected_digest or sidecar.read_text(encoding="ascii") != expected_line:
        raise ValueError("Stage 0.2 artifact or sidecar does not authenticate")


def execute_stage02(
    root: Path,
    *,
    output: Path,
    failure_output: Path,
    runner: Runner = run_smoke_game,
) -> dict[str, object]:
    """Execute the complete frozen stage or preserve one fail-closed artifact."""
    output = _external_path(root, output)
    failure_output = _external_path(root, failure_output)
    commitment_directory = _external_path(root, commitment_directory_for(output))
    if output == failure_output:
        raise ValueError("Stage 0.2 success and failure paths must differ")
    if output.exists() or output.with_suffix(output.suffix + ".sha256").exists():
        raise ValueError("Stage 0.2 success artifact path is not empty")
    if (
        failure_output.exists()
        or failure_output.with_suffix(failure_output.suffix + ".sha256").exists()
    ):
        raise ValueError("Stage 0.2 failure artifact path is not empty")
    if commitment_directory.exists():
        raise ValueError("Stage 0.2 execution commitment channel is not empty")

    manifest: dict[str, object] | None = None
    reports: list[dict[str, object]] = []
    commitments: list[dict[str, object]] = []
    try:
        manifest = build_stage02_manifest(root)
    except Exception as error:
        artifact = _failure_artifact(
            manifest=None,
            stage="manifest_preflight",
            spec=None,
            member="preflight",
            ordinal=0,
            completed_reports=[],
            error=error,
            commitments=commitments,
            commitment_directory=commitment_directory,
        )
        _write_failure(
            failure_output,
            artifact,
            commitments=commitments,
            commitment_directory=commitment_directory,
        )
        raise

    selected = stage02_games()
    if len(selected) != REQUIRED_GAME_COUNT:
        error = RuntimeError("Stage 0.2 requires the complete 450-game matrix")
        artifact = _failure_artifact(
            manifest=manifest,
            stage="matrix_preflight",
            spec=None,
            member="preflight",
            ordinal=0,
            completed_reports=[],
            error=error,
            commitments=commitments,
            commitment_directory=commitment_directory,
        )
        _write_failure(
            failure_output,
            artifact,
            commitments=commitments,
            commitment_directory=commitment_directory,
        )
        raise error

    for game_index, spec in enumerate(selected):
        snapshots: dict[str, dict[str, object]] = {}
        active_member = "first"
        active_stage = "game_execution"
        try:
            for member in ("first", "second"):
                active_member = member
                try:
                    snapshots[member] = runner(root, spec, None)
                except SmokeGameFailure as error:
                    snapshots[member] = error.snapshot
                    active_stage = "execution_commitment_persistence"
                    record = _execution_commitment(
                        spec,
                        member,
                        game_index * 2 + (2 if member == "second" else 1),
                        snapshots[member],
                    )
                    _persist_execution_commitment(commitment_directory, record)
                    commitments.append(record)
                    active_stage = "game_execution"
                    raise
                active_stage = "execution_commitment_persistence"
                record = _execution_commitment(
                    spec,
                    member,
                    game_index * 2 + (2 if member == "second" else 1),
                    snapshots[member],
                )
                _persist_execution_commitment(commitment_directory, record)
                commitments.append(record)
                active_stage = "game_execution"
            reports.append(_report_for(spec, snapshots, manifest))
        except Exception as error:
            artifact = _failure_artifact(
                manifest=manifest,
                stage=active_stage,
                spec=spec,
                member=active_member,
                ordinal=game_index * 2 + (2 if active_member == "second" else 1),
                completed_reports=reports,
                error=error,
                snapshots=snapshots,
                commitments=commitments,
                commitment_directory=commitment_directory,
            )
            _write_failure(
                failure_output,
                artifact,
                commitments=commitments,
                commitment_directory=commitment_directory,
            )
            raise

    try:
        aggregate = _aggregate(reports, manifest)
        result_body = {
            "manifest": manifest,
            "aggregate": aggregate,
            "execution_commitment_channel": _commitment_channel(commitments, commitment_directory),
        }
        result = {**result_body, "raw_artifact_body_digest": stable_digest(result_body)}
        validate_stage02_result(
            result,
            root,
            commitments=commitments,
            commitment_directory=commitment_directory,
        )
    except Exception as error:
        artifact = _failure_artifact(
            manifest=manifest,
            stage="aggregate_reconstruction",
            spec=None,
            member="complete",
            ordinal=REQUIRED_EXECUTION_COUNT,
            completed_reports=reports,
            error=error,
            commitments=commitments,
            commitment_directory=commitment_directory,
        )
        _write_failure(
            failure_output,
            artifact,
            commitments=commitments,
            commitment_directory=commitment_directory,
        )
        raise

    try:
        digest = _atomic_write(output, result)
        _validate_written_pair(output, digest)
    except Exception as error:
        _remove_incomplete_pair(output)
        artifact = _failure_artifact(
            manifest=manifest,
            stage="final_success_serialization",
            spec=None,
            member="complete",
            ordinal=REQUIRED_EXECUTION_COUNT,
            completed_reports=reports,
            error=error,
            commitments=commitments,
            commitment_directory=commitment_directory,
        )
        _write_failure(
            failure_output,
            artifact,
            commitments=commitments,
            commitment_directory=commitment_directory,
        )
        raise
    return result


def _game_spec_from_report(report: dict[str, object]) -> GameSpec:
    seats = report.get("seats")
    if not isinstance(seats, list) or len(seats) != 2:
        raise ValueError("Stage 0.2 report seat evidence is malformed")
    return GameSpec(
        str(report.get("game_id")),
        str(report.get("pairing_id")),
        int(report.get("seed")),
        str(report.get("orientation")),
        tuple(DeckSpec(str(seat), "") for seat in seats),
    )


def validate_stage02_result(
    result: dict[str, object],
    root: Path,
    *,
    commitments: list[dict[str, object]],
    commitment_directory: Path,
) -> None:
    """Reconstruct the complete Stage 0.2 result from frozen inputs and snapshots."""
    manifest = result.get("manifest")
    aggregate = result.get("aggregate")
    if not isinstance(manifest, dict) or not isinstance(aggregate, dict):
        raise ValueError("Stage 0.2 result lacks manifest or aggregate")
    expected_manifest = build_stage02_manifest(root)
    if manifest != expected_manifest:
        raise ValueError("Stage 0.2 frozen manifest does not reconstruct")
    manifest_body = {key: value for key, value in manifest.items() if key != "manifest_digest"}
    if stable_digest(manifest_body) != manifest.get("manifest_digest"):
        raise ValueError("Stage 0.2 manifest digest mismatch")
    _validate_matrix_rows(manifest["games"])

    aggregate_body = {key: value for key, value in aggregate.items() if key != "aggregate_digest"}
    if stable_digest(aggregate_body) != aggregate.get("aggregate_digest"):
        raise ValueError("Stage 0.2 aggregate digest mismatch")
    result_body = {key: value for key, value in result.items() if key != "raw_artifact_body_digest"}
    if stable_digest(result_body) != result.get("raw_artifact_body_digest"):
        raise ValueError("Stage 0.2 raw artifact body digest mismatch")

    reports = aggregate.get("games")
    if not isinstance(reports, list) or len(reports) != REQUIRED_GAME_COUNT:
        raise ValueError("Stage 0.2 result does not contain exactly 450 games")
    if aggregate.get("execution_count") != REQUIRED_EXECUTION_COUNT:
        raise ValueError("Stage 0.2 execution count mismatch")
    expected_rows = manifest["games"]
    report_identity = [
        {
            "game_id": report.get("game_id"),
            "pairing_id": report.get("pairing_id"),
            "seed": report.get("seed"),
            "orientation": report.get("orientation"),
            "seats": report.get("seats"),
        }
        for report in reports
    ]
    if report_identity != expected_rows:
        raise ValueError("Stage 0.2 game membership does not match the frozen matrix")

    reconstructed_reports = []
    for report in reports:
        snapshots = report.get("duplicate_snapshots")
        digests = report.get("duplicate_execution_digests")
        if not isinstance(snapshots, dict) or not isinstance(digests, dict):
            raise ValueError("Stage 0.2 duplicate evidence is missing")
        reconstructed_digests = {
            member: hashlib.sha256(canonical_json(snapshot).encode("utf-8")).hexdigest()
            for member, snapshot in snapshots.items()
        }
        if (
            set(reconstructed_digests) != {"first", "second"}
            or reconstructed_digests != digests
            or digests["first"] != digests["second"]
            or snapshots["first"] != snapshots["second"]
            or report.get("duplicate_byte_equivalent") is not True
            or report.get("duplicate_execution_count") != 2
            or report.get("distinct_game_weight") != 1
        ):
            raise ValueError("Stage 0.2 duplicate evidence does not authenticate")
        original_stops = _original_event_evidence_stops(snapshots["first"])
        if original_stops:
            raise ValueError(f"Stage 0.2 original event evidence is malformed: {original_stops}")
        spec = _game_spec_from_report(report)
        try:
            reconstructed = _report_for(spec, snapshots, manifest)
        except (RuntimeError, ValueError) as error:
            raise ValueError("Stage 0.2 game evidence does not reconstruct") from error
        if report != reconstructed:
            raise ValueError("Stage 0.2 game report is not reconstructive")
        reconstructed_reports.append(reconstructed)

    _validate_commitment_join(
        commitments,
        reconstructed_reports,
        result.get("execution_commitment_channel"),
        commitment_directory,
    )

    expected_aggregate = _aggregate(reconstructed_reports, manifest)
    if aggregate != expected_aggregate:
        raise ValueError("Stage 0.2 aggregate is not reconstructive")
    if aggregate.get("balance_valid") is not False or any(
        record.get("balance_valid") is not False for record in aggregate.get("balance_records", [])
    ):
        raise ValueError("Stage 0.2 balance firewall is not reconstructive")


def load_and_validate_result(path: Path, root: Path) -> dict[str, object]:
    """Authenticate a serialized result and its file sidecar before returning it."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    _validate_written_pair(path, digest)
    result = json.loads(path.read_text(encoding="utf-8"))
    directory = commitment_directory_for(path)
    commitments = load_execution_commitments(directory)
    validate_stage02_result(
        result,
        root,
        commitments=commitments,
        commitment_directory=directory,
    )
    return result
