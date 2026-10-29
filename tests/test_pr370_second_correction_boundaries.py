"""Independent correction audit probes. Never invokes an actual game."""

import hashlib
import json
from pathlib import Path

import pytest
import test_fresh900_live_audit as preserved
from fresh900_native_fixtures import native_snapshot

from tmnt_design_studio import fresh900 as persistence
from tmnt_design_studio import fresh900_identity as identity
from tmnt_design_studio import fresh900_live as live
from tmnt_design_studio import fresh900_native as native
from tmnt_design_studio import smoke01, stage002
from tmnt_design_studio.engine07 import phase_for_step
from tools.run_bad_guys_initial_calibration import build_schedule

ROOT = Path(__file__).resolve().parents[1]
GIT = "C:/Program Files/Git/cmd/git.exe"


def spec():
    return stage002.GameSpec(
        "audit",
        "audit",
        1000000,
        "candidate_first",
        (stage002.DeckSpec("a", ""), stage002.DeckSpec("b", "")),
    )


def canonical_native(game_spec):
    value = native_snapshot(game_spec)
    # Correct the implementation's "complete" fixture's non-native phase.
    value["phase"] = phase_for_step(value["step"])
    for event in value["events"]:
        event["phase"] = phase_for_step(event["step"])
    return value


def check(value, game_spec):
    native.validate_native(value, game_spec)
    report = stage002.reconcile_snapshot(game_spec, value, {"decks": []})
    native.validate_reconciliation(value, game_spec, report)


def rehash(value):
    p = value["authoritative_state_fingerprint_preimage"]
    zones = tuple(
        (
            *(
                tuple(player[z + "_object_ids"])
                for z in ("library", "hand", "battlefield", "graveyard", "exile")
            ),
            player["life"],
            player["lost"],
            player["failed_draw_pending"],
        )
        for player in p["players"]
    )
    authority = (
        p["turn"],
        p["active_player_index"],
        p["step"],
        tuple(p["stack_object_ids"]),
        tuple(p["combat_attacker_ids"]),
        tuple(tuple(v) for v in p["combat_blocks"]),
        zones,
        p["rng_state_digest"],
        p["winner_index"],
    )
    value["authoritative_state_fingerprint"] = hashlib.sha256(repr(authority).encode()).hexdigest()


def test_canonical_artificial_baseline_passes_real_validators():
    check(canonical_native(spec()), spec())


def test_pilot_default_cannot_spoof_none_by_equality(monkeypatch):
    original = smoke01.run_smoke_game
    assert live._bind_executor(smoke01, ROOT, GIT) is original  # Identity only, no game call.

    class SubstitutePilot:
        def __eq__(self, other):
            return other is None

    pilot = SubstitutePilot()
    assert pilot is not None and bool(pilot)
    monkeypatch.setattr(original, "__defaults__", (pilot,))
    with pytest.raises(identity.FreshRefused):
        live._bind_executor(smoke01, ROOT, GIT)


@pytest.mark.parametrize("phase", ["main", "combat", "not-a-native-phase"])
def test_contradictory_native_phase_rejected(phase):
    value = canonical_native(spec())
    assert phase != phase_for_step(value["step"])
    value["phase"] = phase
    with pytest.raises((identity.FreshRefused, ValueError, KeyError)):
        check(value, spec())


def test_unknown_step_rejected_even_with_matching_fingerprint():
    value = canonical_native(spec())
    value["step"] = "NOT_AN_ENGINE_STEP"
    value["authoritative_state_fingerprint_preimage"]["step"] = value["step"]
    rehash(value)
    with pytest.raises((identity.FreshRefused, ValueError, KeyError)):
        check(value, spec())


def test_missing_nested_combat_evidence_rejected():
    value = canonical_native(spec())
    del value["combat_damage"]["evidence"]
    with pytest.raises((identity.FreshRefused, ValueError, KeyError)):
        check(value, spec())


@pytest.mark.parametrize("fault", ["phase", "missing-combat-evidence"])
def test_full_plan_does_not_commit_invalid_native_result(tmp_path, monkeypatch, request, fault):
    # Existing test-only controlled mock binding; full production plan verifier.
    plan, approval, mock = preserved.boundary.__wrapped__(tmp_path, monkeypatch, request)
    plan["schedule"] = build_schedule(ROOT)
    plan["adapter"]["source_sha256"] = identity.file_hash(
        ROOT / "src/tmnt_design_studio/fresh900_live.py"
    )
    approval["plan_sha256"] = identity.digest(plan)
    monkeypatch.setattr(persistence, "verify_plan", identity.verify_plan)
    calls = []

    def execute(root, game_spec):
        calls.append(game_spec.game_id)
        if len(calls) > 1:
            raise RuntimeError("AUDIT STOP at second mock dispatch; no game")
        value = canonical_native(game_spec)
        if fault == "phase":
            value["phase"] = "combat"
        else:
            del value["combat_damage"]["evidence"]
        return value

    mock.side_effect = execute
    with pytest.raises((identity.FreshRefused, live.AdapterGameFailure)):
        live.run_authorized_live(
            plan, approval, expected_authorization_sha256=identity.digest(approval)
        )
    assert calls, "Audit failed before reaching the mock boundary"
    root = Path(plan["output"])
    saved = json.loads((root / "checkpoints/checkpoint.json").read_bytes())
    assert saved["completed_games"] == 0, f"{fault}: invalid first result committed"
    status = json.loads((root / "telemetry/status.json").read_bytes())
    assert status["committed_games"] == 0
