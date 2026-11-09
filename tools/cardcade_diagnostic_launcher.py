"""One-shot Acceptance Match #001 diagnostic launcher.

The CLI is intentionally fixed to the committed April-vs-Casey canonical seed. Tests may
inject an executor, but the command-line entry point never exposes that seam.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import traceback
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

# Always load the implementation from this exact checkout, even when the selected
# Python environment has another editable Cardcade worktree installed.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORY = str(REPOSITORY_ROOT / "src")
if SOURCE_DIRECTORY in sys.path:
    sys.path.remove(SOURCE_DIRECTORY)
sys.path.insert(0, SOURCE_DIRECTORY)

from tmnt_design_studio import engine07, stage002  # noqa: E402

ACCEPTED_MAIN = "10d2ac80ef5b81b3a209a3133eb0a84633a1f944"
EXPECTED_GAME_ID = "april-casey:canonical:7231"
EXPECTED_PAIRING_ID = "april-casey"
EXPECTED_ORIENTATION = "canonical"
EXPECTED_SEED = 7231
INPUT_PATHS = (
    "src/tmnt_design_studio/stage002.py",
    "decks/april_oneil/PROTOTYPE_0.1.txt",
    "decks/casey_jones/PROTOTYPE_0.1.txt",
    "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
    "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json",
)
APPROVED_INPUT_SHA256 = {
    "src/tmnt_design_studio/stage002.py": (
        "69ecb217234ac892509de0fbe6417601826909b3fceba77f4a865d4959db8f1b"
    ),
    "decks/april_oneil/PROTOTYPE_0.1.txt": (
        "684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4"
    ),
    "decks/casey_jones/PROTOTYPE_0.1.txt": (
        "0fc0adbb370ecfddad03692a4229a04b23268739914a8f2a004b8e042ff3cebb"
    ),
    "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json": (
        "56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402"
    ),
    "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json": (
        "6b5271af75150a361f77e7b89306c709959dfdf497c448dfdc978e5dc9a17950"
    ),
    "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json": (
        "532bad7e489eb25f3184b5a90487e1361f7a2b19b8c02cac3c4115a0fc3e14bc"
    ),
}
SOURCE_APPROVAL_SCHEMA = "cardcade-reviewed-implementation-v1"
RUN_AUTHORIZATION_SCHEMA = "cardcade-diagnostic-run-authorization-v1"
# Provision the production HQ public key through a reviewed source change. The
# empty default deliberately fails closed; private signing keys never belong here.
TRUSTED_HQ_AUTHORIZATION_KEYS: dict[str, bytes] = {}
SOURCE_APPROVAL_FIELDS = {
    "schema",
    "approval_id",
    "implementation_sha",
    "input_sha256",
    "signing_key_id",
    "signature",
}
RUN_AUTHORIZATION_FIELDS = {
    "schema",
    "authorization_id",
    "source_approval_id",
    "implementation_sha",
    "input_sha256",
    "game_id",
    "pairing_id",
    "orientation",
    "seed",
    "signing_key_id",
    "signature",
}
RECONCILIATION_REPORT_FIELDS = {
    "game_id",
    "seed",
    "orientation",
    "seats",
    "terminal",
    "winner",
    "turn",
    "rng_state_digest",
    "occurrences",
    "presence",
    "classification_sets",
    "executed_references",
    "authenticated_executed_references",
    "opportunity_witnesses",
    "opportunity_contexts",
    "authoritative_evidence",
    "stop_records",
    "invariant_violations",
    "transaction_counts",
    "engine_boundary_counts",
    "report_digest",
}
AUTHORITATIVE_EVIDENCE_FIELDS = (
    "mill_three_evidence",
    "krang_refill_evidence",
    "jury_rig_evidence",
    "vigilante_evidence",
    "winner",
    "food_search_evidence",
    "rng",
    "stack",
    "priority",
    "pending_triggers",
    "rules_event_evidence",
    "floating_mana_ledger",
    "spell_payment_evidence",
    "scry",
    "etb_drain_gain_scry",
    "stun_history",
    "combat_damage",
    "lifelink",
    "hand_bottom_draw",
    "discard_draw",
    "activated_abilities",
    "food_activations",
    "sneak",
    "players",
    "events",
    "terminal",
)
TRACE_EVENTS = {
    "priority_granted",
    "priority_passed",
    "priority_window_closed",
    "stack_resolution_permitted",
    "trigger_stacked",
    "trigger_resolved",
    "attack_declared",
    "attackers_declared",
    "block_declared",
    "blockers_declared",
    "sneak",
    "combat_damage",
    "step_changed",
}


class DiagnosticLauncherError(RuntimeError):
    """Raised when launcher preflight or evidence validation cannot complete."""


class EvidencePersistenceError(DiagnosticLauncherError):
    """Raised when a successful synthetic/real invocation cannot be fully persisted."""


class OneShotDiagnosticLauncher:
    """Run one exact committed match and persist its evidence into a new directory."""

    def __init__(
        self,
        root: Path,
        output_directory: Path,
        *,
        source_approval_path: Path,
        run_authorization_path: Path,
    ) -> None:
        self.root = root.resolve()
        self.requested_output_directory = output_directory.absolute()
        self.output_directory = output_directory.resolve()
        self.source_approval_path = source_approval_path.resolve()
        self.run_authorization_path = run_authorization_path.resolve()
        self._consumed = False
        self._run_game_call_count = 0
        self._storage_error: str | None = None

    @staticmethod
    def _git(root: Path, *args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(root), *args],
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()

    @staticmethod
    def _read_authorization(path: Path, *, label: str) -> dict[str, Any]:
        def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"duplicate authorization field: {key}")
                result[key] = value
            return result

        try:
            document = json.loads(
                path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys
            )
        except (OSError, ValueError) as error:
            raise DiagnosticLauncherError(f"cannot read {label}: {error}") from error
        if not isinstance(document, dict):
            raise DiagnosticLauncherError(f"{label} must be a JSON object")
        return document

    @staticmethod
    def _verify_authorization_signature(
        document: dict[str, Any], *, label: str, expected_fields: set[str]
    ) -> str:
        if set(document) != expected_fields:
            raise DiagnosticLauncherError(f"{label} has missing or unexpected signed fields")
        key_id = document.get("signing_key_id")
        if not isinstance(key_id, str) or not key_id:
            raise DiagnosticLauncherError(f"{label} is missing signing_key_id")
        public_key_bytes = TRUSTED_HQ_AUTHORIZATION_KEYS.get(key_id)
        if public_key_bytes is None:
            raise DiagnosticLauncherError(f"{label} signature uses an untrusted key ID: {key_id}")
        if len(public_key_bytes) != 32:
            raise DiagnosticLauncherError(f"trusted public key {key_id} is not Ed25519")
        try:
            signature = base64.b64decode(document["signature"], validate=True)
            if len(signature) != 64:
                raise ValueError("Ed25519 signatures must contain 64 bytes")
            signed_fields = {key: value for key, value in document.items() if key != "signature"}
            payload = json.dumps(
                signed_fields,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            Ed25519PublicKey.from_public_bytes(public_key_bytes).verify(signature, payload)
        except (InvalidSignature, ValueError, TypeError) as error:
            raise DiagnosticLauncherError(f"{label} signature verification failed") from error
        return key_id

    def _verify_source(self) -> dict[str, Any]:
        head = self._git(self.root, "rev-parse", "HEAD")
        branch = self._git(self.root, "branch", "--show-current") or "(detached HEAD)"
        status = self._git(self.root, "status", "--porcelain=v1")
        main = self._git(self.root, "rev-parse", "refs/remotes/origin/main")
        expected_stage002 = (self.root / "src/tmnt_design_studio/stage002.py").resolve()
        imported_stage002 = Path(stage002.__file__).resolve()
        expected_engine = (self.root / "src/tmnt_design_studio/engine07.py").resolve()
        imported_engine = Path(engine07.__file__).resolve()
        if status:
            raise DiagnosticLauncherError(f"launcher worktree is not clean: {status}")
        if imported_stage002 != expected_stage002:
            raise DiagnosticLauncherError(
                f"Stage 002 imported from {imported_stage002}, expected {expected_stage002}"
            )
        if imported_engine != expected_engine:
            raise DiagnosticLauncherError(
                f"engine imported from {imported_engine}, expected {expected_engine}"
            )
        if stage002.Game is not engine07.Game:
            raise DiagnosticLauncherError(
                "Stage 002 and engine imports do not share one Game class"
            )
        if main != ACCEPTED_MAIN:
            raise DiagnosticLauncherError(f"accepted main changed: {main}")

        source_approval = self._read_authorization(
            self.source_approval_path, label="HQ source approval"
        )
        run_authorization = self._read_authorization(
            self.run_authorization_path, label="one-use run authorization"
        )
        if source_approval.get("schema") != SOURCE_APPROVAL_SCHEMA:
            raise DiagnosticLauncherError("unsupported HQ source approval schema")
        if run_authorization.get("schema") != RUN_AUTHORIZATION_SCHEMA:
            raise DiagnosticLauncherError("unsupported one-use run authorization schema")
        source_key_id = self._verify_authorization_signature(
            source_approval,
            label="HQ source approval",
            expected_fields=SOURCE_APPROVAL_FIELDS,
        )
        run_key_id = self._verify_authorization_signature(
            run_authorization,
            label="one-use run authorization",
            expected_fields=RUN_AUTHORIZATION_FIELDS,
        )
        if source_key_id != run_key_id:
            raise DiagnosticLauncherError(
                "source approval and run authorization use different HQ signing keys"
            )
        if source_approval.get("implementation_sha") != head:
            raise DiagnosticLauncherError(
                f"HEAD {head} does not equal exact approved implementation "
                f"{source_approval.get('implementation_sha')}"
            )
        if run_authorization.get("implementation_sha") != head:
            raise DiagnosticLauncherError(
                "run authorization does not identify the exact checked-out implementation"
            )
        approval_id = source_approval.get("approval_id")
        if not isinstance(approval_id, str) or not approval_id:
            raise DiagnosticLauncherError("HQ source approval is missing approval_id")
        if run_authorization.get("source_approval_id") != approval_id:
            raise DiagnosticLauncherError(
                "run authorization references a different source approval"
            )
        authorization_id = run_authorization.get("authorization_id")
        if not isinstance(authorization_id, str) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", authorization_id
        ):
            raise DiagnosticLauncherError("run authorization has an invalid authorization_id")
        for label, document in (
            ("HQ source approval", source_approval),
            ("one-use run authorization", run_authorization),
        ):
            if document.get("input_sha256") != APPROVED_INPUT_SHA256:
                raise DiagnosticLauncherError(f"{label} does not contain the approved input hashes")
        actual_input_hashes = {
            relative: hashlib.sha256((self.root / relative).read_bytes()).hexdigest()
            for relative in INPUT_PATHS
        }
        if actual_input_hashes != APPROVED_INPUT_SHA256:
            raise DiagnosticLauncherError(
                "frozen deck/card-data/Baseline inputs do not match approval"
            )
        if (
            run_authorization.get("game_id") != EXPECTED_GAME_ID
            or run_authorization.get("pairing_id") != EXPECTED_PAIRING_ID
            or run_authorization.get("orientation") != EXPECTED_ORIENTATION
            or run_authorization.get("seed") != EXPECTED_SEED
        ):
            raise DiagnosticLauncherError(
                "run authorization does not match the fixed diagnostic spec"
            )
        return {
            "head": head,
            "branch": branch,
            "accepted_main": main,
            "source_approval": source_approval,
            "run_authorization": run_authorization,
            "source_approval_sha256": hashlib.sha256(
                self.source_approval_path.read_bytes()
            ).hexdigest(),
            "run_authorization_sha256": hashlib.sha256(
                self.run_authorization_path.read_bytes()
            ).hexdigest(),
            "input_sha256": actual_input_hashes,
        }

    def _match_spec(self) -> stage002.GameSpec:
        matches = [game for game in stage002.stage_games() if game.game_id == EXPECTED_GAME_ID]
        if len(matches) != 1:
            raise DiagnosticLauncherError(
                f"expected exactly one committed spec for {EXPECTED_GAME_ID}, found {len(matches)}"
            )
        spec = matches[0]
        if (
            spec.pairing_id != EXPECTED_PAIRING_ID
            or spec.orientation != EXPECTED_ORIENTATION
            or spec.seed != EXPECTED_SEED
            or tuple(seat.display_id for seat in spec.seats)
            != ("april-oneil-p0.1", "casey-jones-p0.1")
        ):
            raise DiagnosticLauncherError("committed Acceptance Match #001 spec changed")
        return spec

    def _prepare_output(self) -> None:
        diagnostics_root = self.root / ".cardcade-diagnostic-runs"
        if diagnostics_root.is_symlink():
            raise DiagnosticLauncherError("diagnostic output root cannot be a symlink")
        diagnostics_root.mkdir(exist_ok=True)
        allowed_root = diagnostics_root.resolve()
        if self.requested_output_directory.is_symlink():
            raise DiagnosticLauncherError("output directory cannot be a symlink")
        if self.requested_output_directory.parent.resolve() != allowed_root:
            raise DiagnosticLauncherError(
                "output directory must be a direct child of .cardcade-diagnostic-runs"
            )
        if not self.output_directory.name.startswith("diagnostic-game-"):
            raise DiagnosticLauncherError("output directory must start with diagnostic-game-")
        self.output_directory.mkdir(exist_ok=False)
        probe = self.output_directory / ".write-probe"
        try:
            with probe.open("xb") as stream:
                stream.write(b"diagnostic evidence preflight\n")
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            if probe.exists():
                probe.unlink()

    def _claim_authorization(self, source: dict[str, Any]) -> Path:
        """Durably claim one authorization ID with an exclusive cross-process create."""
        common_git_directory = Path(
            self._git(self.root, "rev-parse", "--path-format=absolute", "--git-common-dir")
        ).resolve()
        claim_directory = common_git_directory.parent / ".cardcade-diagnostic-claims"
        if claim_directory.is_symlink():
            raise DiagnosticLauncherError("authorization claim storage cannot contain symlinks")
        claim_directory.mkdir(parents=True, exist_ok=True)
        if claim_directory.resolve().parent != common_git_directory.parent:
            raise DiagnosticLauncherError(
                "authorization claim directory escaped the repository root"
            )
        authorization = source["run_authorization"]
        authorization_id = authorization["authorization_id"]
        claim_key = hashlib.sha256(authorization_id.encode("utf-8")).hexdigest()
        claim_path = claim_directory / f"{claim_key}.json"
        claim = {
            "schema": "cardcade-diagnostic-authorization-claim-v1",
            "authorization_id": authorization_id,
            "implementation_sha": source["head"],
            "source_approval_sha256": source["source_approval_sha256"],
            "run_authorization_sha256": source["run_authorization_sha256"],
            "claimed_utc": datetime.now(UTC).isoformat(),
            "state": "consumed-before-invocation",
        }
        payload = json.dumps(claim, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        try:
            descriptor = os.open(
                claim_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError as error:
            raise DiagnosticLauncherError(
                f"authorization already consumed: {authorization_id}"
            ) from error
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        return claim_path

    @staticmethod
    def _write_json(directory: Path, filename: str, value: object) -> None:
        destination = directory / filename
        temporary = directory / f".{filename}.tmp"
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        try:
            with temporary.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _persist_hashes(self) -> dict[str, str]:
        hashes = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(self.output_directory.iterdir())
            if path.is_file() and path.name != "artifact_sha256.json"
        }
        self._write_json(self.output_directory, "artifact_sha256.json", hashes)
        return hashes

    @staticmethod
    def _safe_error(error: BaseException) -> dict[str, str]:
        try:
            message = str(error)
        except BaseException as formatting_error:
            message = f"<message unavailable: {type(formatting_error).__name__}>"
        try:
            rendered = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        except BaseException as formatting_error:
            rendered = f"<traceback unavailable: {type(formatting_error).__name__}>"
        return {"type": type(error).__name__, "message": message, "traceback": rendered}

    def _serialize_snapshot(
        self,
        snapshot: dict[str, Any],
        spec: stage002.GameSpec,
        manifest: dict[str, object],
        source: dict[str, Any],
    ) -> tuple[dict[str, object] | None, dict[str, object] | None]:
        try:
            self._write_json(self.output_directory, "snapshot.json", snapshot)
            events = snapshot.get("events", [])
            if not isinstance(events, list):
                raise DiagnosticLauncherError("snapshot event stream is not a list")
            self._write_json(self.output_directory, "events.json", events)
            self._write_json(
                self.output_directory,
                "priority_stack_combat_trace.json",
                [event for event in events if event.get("event") in TRACE_EVENTS],
            )
        except OSError as error:
            raise EvidencePersistenceError(
                "snapshot evidence could not be persisted; do not retry this launcher"
            ) from error
        try:
            reconciliation = stage002.reconcile_snapshot(spec, snapshot, manifest)
        except BaseException as error:
            return None, self._safe_error(error)
        self._write_json(self.output_directory, "reconciliation.json", reconciliation)
        validation_errors = self._validate_reconciliation(
            reconciliation, spec, snapshot, manifest, source
        )
        if validation_errors:
            return (
                reconciliation if isinstance(reconciliation, dict) else None,
                {
                    "type": "InvalidReconciliation",
                    "message": "; ".join(validation_errors),
                    "traceback": "",
                },
            )
        self._write_json(
            self.output_directory,
            "reconciliation_binding.json",
            {
                "schema": "cardcade-stage002-reconciliation-binding-v1",
                "game_id": spec.game_id,
                "seed": spec.seed,
                "orientation": spec.orientation,
                "implementation_sha": source["head"],
                "stage002_sha256": source["input_sha256"]["src/tmnt_design_studio/stage002.py"],
                "stage_manifest_digest": manifest["manifest_digest"],
                "reconciliation_report_digest": reconciliation["report_digest"],
            },
        )
        return reconciliation, None

    @staticmethod
    def _validate_reconciliation(
        reconciliation: object,
        spec: stage002.GameSpec,
        snapshot: dict[str, Any],
        manifest: dict[str, object],
        source: dict[str, Any],
    ) -> list[str]:
        errors: list[str] = []
        if not isinstance(manifest, dict):
            return ["Stage 002 manifest is not an object"]
        manifest_digest = manifest.get("manifest_digest")
        manifest_body = {key: value for key, value in manifest.items() if key != "manifest_digest"}
        if (
            not isinstance(manifest_digest, str)
            or stage002.stable_digest(manifest_body) != manifest_digest
        ):
            errors.append("Stage 002 manifest digest is missing or invalid")
        if manifest.get("stage") != "acceptance-002":
            errors.append("Stage 002 manifest has the wrong stage identity")
        manifest_games = manifest.get("games")
        expected_game = {
            "game_id": spec.game_id,
            "pairing_id": spec.pairing_id,
            "seed": spec.seed,
            "orientation": spec.orientation,
            "seats": [seat.display_id for seat in spec.seats],
        }
        if not isinstance(manifest_games, list) or expected_game not in manifest_games:
            errors.append("Stage 002 manifest is not bound to the authorized game")
        expected_catalog_sha = source.get("input_sha256", {}).get(
            "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
        )
        if manifest.get("snapshot_sha256") != expected_catalog_sha:
            errors.append("Stage 002 manifest is not bound to the approved card-data source")
        if not isinstance(reconciliation, dict):
            errors.append("Stage 002 reconciliation report is missing or not an object")
            return errors
        if set(reconciliation) != RECONCILIATION_REPORT_FIELDS:
            errors.append("Stage 002 reconciliation report has missing or unexpected fields")
        report_digest = reconciliation.get("report_digest")
        report_body = {
            key: value for key, value in reconciliation.items() if key != "report_digest"
        }
        if (
            not isinstance(report_digest, str)
            or stage002.stable_digest(report_body) != report_digest
        ):
            errors.append("Stage 002 reconciliation report digest is missing or invalid")
        expected_identity = {
            "game_id": spec.game_id,
            "seed": spec.seed,
            "orientation": spec.orientation,
            "seats": [seat.display_id for seat in spec.seats],
            "terminal": snapshot.get("terminal"),
            "winner": snapshot.get("winner"),
            "turn": snapshot.get("turn"),
            "rng_state_digest": snapshot.get("rng", {}).get("state_digest")
            if isinstance(snapshot.get("rng"), dict)
            else None,
        }
        for key, expected in expected_identity.items():
            if reconciliation.get(key) != expected:
                errors.append(f"Stage 002 report {key} does not match authoritative source")
        if not isinstance(reconciliation.get("occurrences"), list):
            errors.append("Stage 002 report occurrences are missing")
        if not isinstance(reconciliation.get("presence"), list):
            errors.append("Stage 002 report presence evidence is missing")
        if not isinstance(reconciliation.get("classification_sets"), dict):
            errors.append("Stage 002 report classification sets are missing")
        for field in (
            "executed_references",
            "authenticated_executed_references",
            "opportunity_witnesses",
            "opportunity_contexts",
            "stop_records",
            "invariant_violations",
        ):
            if not isinstance(reconciliation.get(field), list):
                errors.append(f"Stage 002 report {field} evidence is missing")
        for field in ("transaction_counts", "engine_boundary_counts"):
            if not isinstance(reconciliation.get(field), dict):
                errors.append(f"Stage 002 report {field} evidence is missing")
        expected_authoritative = {key: snapshot.get(key) for key in AUTHORITATIVE_EVIDENCE_FIELDS}
        if reconciliation.get("authoritative_evidence") != expected_authoritative:
            errors.append("Stage 002 report authoritative evidence does not match the snapshot")
        conformance = snapshot.get("conformance")
        if not isinstance(conformance, dict):
            errors.append("authoritative snapshot conformance evidence is missing")
        else:
            if reconciliation.get("executed_references") != conformance.get("executed_references"):
                errors.append("Stage 002 executed references do not match the snapshot")
            if reconciliation.get("opportunity_witnesses") != conformance.get(
                "opportunity_witnesses"
            ):
                errors.append("Stage 002 opportunity witnesses do not match the snapshot")
            if reconciliation.get("opportunity_contexts") != conformance.get(
                "opportunity_contexts"
            ):
                errors.append("Stage 002 opportunity contexts do not match the snapshot")
        expected_invariants = [
            event
            for event in snapshot.get("events", [])
            if isinstance(event, dict) and event.get("event") == "invariant_violation"
        ]
        if reconciliation.get("invariant_violations") != expected_invariants:
            errors.append("Stage 002 invariant evidence does not match authoritative events")
        return errors

    @staticmethod
    def _blocking_findings(
        snapshot: object,
        reconciliation: object,
        reconciliation_error: dict[str, str] | None,
    ) -> list[str]:
        findings: list[str] = []
        if not isinstance(snapshot, dict):
            return ["snapshot_missing_or_invalid"]
        if snapshot.get("terminal") is not True:
            findings.append("game_not_terminal")
        if not isinstance(snapshot.get("stage002_presence"), list):
            findings.append("presence_evidence_missing")
        events = snapshot.get("events")
        if not isinstance(events, list):
            findings.append("event_stream_missing_or_invalid")
            events = []
        event_names = [event.get("event") for event in events if isinstance(event, dict)]
        if "invariant_violation" in event_names:
            findings.append("invariant_violation_event")
        if "acceptance_incomplete" in event_names:
            findings.append("acceptance_incomplete_event")
        if reconciliation_error is not None:
            findings.append("reconciliation_failed")
        if not isinstance(reconciliation, dict):
            findings.append("reconciliation_missing")
            return findings
        stop_records = reconciliation.get("stop_records")
        if not isinstance(stop_records, list):
            findings.append("reconciliation_stop_records_missing")
        elif stop_records:
            findings.append("blocking_reconciliation_stop_records")
        invariant_violations = reconciliation.get("invariant_violations")
        if not isinstance(invariant_violations, list):
            findings.append("reconciliation_invariant_evidence_missing")
        elif invariant_violations:
            findings.append("reconciliation_invariant_violations")
        return findings

    def run_once(
        self,
        executor: Callable[..., dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Run the fixed match once. `executor` is a synthetic-test injection seam only."""
        if self._consumed:
            raise DiagnosticLauncherError("this launcher instance has already been consumed")
        self._consumed = True
        source = self._verify_source()
        spec = self._match_spec()
        self._prepare_output()
        manifest = stage002.build_stage_manifest(self.root)
        input_hashes = source["input_sha256"]
        source_approval = source["source_approval"]
        run_authorization = source["run_authorization"]
        metadata: dict[str, object] = {
            "run_id": "cardcade-diagnostic-launcher-once",
            "source_approval_id": source_approval["approval_id"],
            "run_authorization_id": run_authorization["authorization_id"],
            "approved_implementation_sha": source["head"],
            "observed_head": source["head"],
            "accepted_main": source["accepted_main"],
            "branch": source["branch"],
            "worktree": str(self.root),
            "output_directory": str(self.output_directory),
            "python_version": platform.python_version(),
            "python_executable": sys.executable,
            "stage002_module_path": str(Path(stage002.__file__).resolve()),
            "engine_module_path": str(Path(engine07.__file__).resolve()),
            "source_approval_sha256": source["source_approval_sha256"],
            "run_authorization_sha256": source["run_authorization_sha256"],
            "game_id": spec.game_id,
            "pairing_id": spec.pairing_id,
            "orientation": spec.orientation,
            "seed": spec.seed,
            "seats": [
                {"display_id": seat.display_id, "deck_path": seat.relative_path}
                for seat in spec.seats
            ],
            "stage_manifest_digest": manifest["manifest_digest"],
            "input_sha256": input_hashes,
            "invocation": "stage002.run_game(root, committed_spec, AcceptancePilot())",
            "run_game_call_count": 0,
            "retry_count": 0,
            "additional_seeds": 0,
            "batch_or_calibration": False,
            "runner_control_flow": (
                "one durable authorization claim per authorization ID; one executor call; "
                "no outer pairing loop, retry, or seed expansion"
            ),
            "started_utc": datetime.now(UTC).isoformat(),
        }
        self._write_json(self.output_directory, "stage_manifest.json", manifest)
        self._write_json(self.output_directory, "run_metadata.json", metadata)
        capture = stage002.DiagnosticExecutionCapture()
        invoke = executor or stage002.run_game

        def call_once() -> dict[str, Any]:
            if self._run_game_call_count:
                raise DiagnosticLauncherError("executor call limit exceeded")
            claim_path = self._claim_authorization(source)
            metadata["authorization_claim"] = str(claim_path)
            metadata["authorization_claimed_utc"] = datetime.now(UTC).isoformat()
            self._write_json(self.output_directory, "run_metadata.json", metadata)
            self._run_game_call_count += 1
            return invoke(self.root, spec, diagnostic_capture=capture)

        try:
            snapshot = stage002.capture_diagnostic_call(capture, call_once)
        except BaseException as original_error:
            metadata["run_game_call_count"] = self._run_game_call_count
            metadata["finished_utc"] = datetime.now(UTC).isoformat()
            failure = capture.failure or self._safe_error(original_error)
            failure_without_snapshot = {
                key: value for key, value in failure.items() if key != "snapshot"
            }
            persist_error: BaseException | None = None
            try:
                self._write_json(self.output_directory, "exception.json", failure_without_snapshot)
                captured_snapshot = failure.get("snapshot")
                if isinstance(captured_snapshot, dict):
                    _reconciliation, reconciliation_error = self._serialize_snapshot(
                        captured_snapshot, spec, manifest, source
                    )
                    if reconciliation_error is not None:
                        self._write_json(
                            self.output_directory,
                            "reconciliation_error.json",
                            reconciliation_error,
                        )
                self._write_json(self.output_directory, "run_metadata.json", metadata)
                status = {
                    "run_returned_normally": False,
                    "diagnostic_status": "BLOCKED",
                    "blocking_findings": ["execution_exception"],
                    "reconciliation_completed": (
                        self.output_directory / "reconciliation.json"
                    ).exists(),
                    "run_game_call_count": self._run_game_call_count,
                    "retry_count": 0,
                    "snapshot_captured": isinstance(captured_snapshot, dict),
                    "winner": captured_snapshot.get("winner")
                    if isinstance(captured_snapshot, dict)
                    else None,
                    "terminal": captured_snapshot.get("terminal")
                    if isinstance(captured_snapshot, dict)
                    else None,
                }
                self._write_json(self.output_directory, "run_status.json", status)
                self._persist_hashes()
            except BaseException as error:
                persist_error = error
                self._storage_error = self._safe_error(error)["message"]
            if persist_error is not None and hasattr(original_error, "add_note"):
                original_error.add_note(
                    f"diagnostic evidence persistence failed: {self._storage_error}"
                )
            raise

        metadata["run_game_call_count"] = self._run_game_call_count
        metadata["finished_utc"] = datetime.now(UTC).isoformat()
        reconciliation = None
        reconciliation_error = None
        serialization_error = None
        try:
            self._write_json(self.output_directory, "run_metadata.json", metadata)
            if isinstance(snapshot, dict):
                try:
                    reconciliation, reconciliation_error = self._serialize_snapshot(
                        snapshot, spec, manifest, source
                    )
                except EvidencePersistenceError:
                    raise
                except BaseException as error:
                    serialization_error = self._safe_error(error)
                    reconciliation_error = serialization_error
            else:
                serialization_error = {
                    "type": "InvalidSnapshot",
                    "message": "executor returned a non-object snapshot",
                    "traceback": "",
                }
                self._write_json(self.output_directory, "snapshot_error.json", serialization_error)
            if reconciliation_error is not None:
                self._write_json(
                    self.output_directory, "reconciliation_error.json", reconciliation_error
                )
            events = snapshot.get("events", []) if isinstance(snapshot, dict) else []
            if not isinstance(events, list):
                events = []
            counts = Counter(str(event.get("event")) for event in events if isinstance(event, dict))
            blockers = self._blocking_findings(snapshot, reconciliation, reconciliation_error)
            if serialization_error is not None and "snapshot_missing_or_invalid" not in blockers:
                blockers.append("snapshot_serialization_failed")
            status = {
                "run_returned_normally": True,
                "diagnostic_status": "READY" if not blockers else "BLOCKED",
                "blocking_findings": blockers,
                "reconciliation_completed": reconciliation is not None,
                "winner": snapshot.get("winner") if isinstance(snapshot, dict) else None,
                "terminal": snapshot.get("terminal") if isinstance(snapshot, dict) else None,
                "turn": snapshot.get("turn") if isinstance(snapshot, dict) else None,
                "step": snapshot.get("step") if isinstance(snapshot, dict) else None,
                "event_count": len(events),
                "event_counts": dict(sorted(counts.items())),
                "run_game_call_count": self._run_game_call_count,
                "retry_count": 0,
                "invariant_violation_count": counts.get("invariant_violation", 0),
                "acceptance_incomplete_count": counts.get("acceptance_incomplete", 0),
                "reconciliation_stop_records": reconciliation.get("stop_records", [])
                if reconciliation is not None
                else None,
            }
            self._write_json(self.output_directory, "run_status.json", status)
            self._persist_hashes()
        except BaseException as error:
            self._storage_error = self._safe_error(error)["message"]
            raise EvidencePersistenceError(
                "executor completed once, but complete diagnostic evidence could not be persisted; "
                "do not retry this launcher"
            ) from error
        if blockers:
            raise DiagnosticLauncherError(
                "diagnostic BLOCKED: " + ", ".join(blockers) + "; do not retry this authorization"
            )
        return snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-directory",
        type=Path,
        help="new isolated directory; defaults to .cardcade-diagnostic-runs/<UTC run id>",
    )
    parser.add_argument("--source-approval", type=Path, required=True)
    parser.add_argument("--run-authorization", type=Path, required=True)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    run_id = datetime.now(UTC).strftime("diagnostic-game-%Y%m%dT%H%M%SZ")
    output = args.output_directory or root / ".cardcade-diagnostic-runs" / run_id
    launcher = OneShotDiagnosticLauncher(
        root,
        output,
        source_approval_path=args.source_approval,
        run_authorization_path=args.run_authorization,
    )
    try:
        launcher.run_once()
    except BaseException as error:
        print(f"diagnostic launcher stopped: {error}", file=sys.stderr)
        print(f"evidence directory: {output}", file=sys.stderr)
        return 2
    print(f"diagnostic evidence: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
