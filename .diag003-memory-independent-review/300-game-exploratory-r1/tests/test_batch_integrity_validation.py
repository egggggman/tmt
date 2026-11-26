from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

TEST_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEST_ROOT))

INTEGRITY_HELPER = TEST_ROOT / "batch_integrity_validation.integrity-v2.py"
INTEGRITY_SPEC = importlib.util.spec_from_file_location(
    "batch_integrity_validation_integrity_v2", INTEGRITY_HELPER
)
assert INTEGRITY_SPEC is not None and INTEGRITY_SPEC.loader is not None
integrity = importlib.util.module_from_spec(INTEGRITY_SPEC)
INTEGRITY_SPEC.loader.exec_module(integrity)
CORRECTED_VERIFIER = (
    TEST_ROOT.parent / "verifier-trust-review" / "corrected" / "verify_completed_batch.py"
)

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_TEMP = tempfile.TemporaryDirectory()
FIXTURE_REPO_ROOT = Path(FIXTURE_TEMP.name) / "repo"
with zipfile.ZipFile(TEST_ROOT / "schedule_validation_fixtures.zip") as fixture_archive:
    fixture_archive.extractall(FIXTURE_REPO_ROOT)
SCHEDULE_ROOT = FIXTURE_REPO_ROOT / ".diag003-memory-independent-review" / "300-game-exploratory-r1"


class ManifestProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = json.loads(
            (SCHEDULE_ROOT / "explore300r1.schedule.json").read_text(encoding="utf-8")
        )
        cls.block = cls.plan["blocks"][0]
        cls.manifest_path = SCHEDULE_ROOT / "manifests" / f"{cls.block['batch_id']}.manifest.json"
        cls.manifest = json.loads(cls.manifest_path.read_text(encoding="utf-8"))

    def assert_rejected(self, mutated: dict) -> None:
        with self.assertRaises(integrity.IntegrityError):
            integrity.validate_manifest_projection(mutated, self.plan, self.block)

    def test_unchanged_all_30_blocks_pass(self) -> None:
        report = integrity.validate_schedule_manifest_set(root=FIXTURE_REPO_ROOT)
        self.assertEqual(report["state"], "SCHEDULE_MANIFESTS_VERIFIED")
        self.assertEqual(report["blocks_verified"], 30)
        self.assertEqual(report["games_verified"], 300)

    def test_seed_substitution_rejected(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["games"][0]["seed"] += 1000
        self.assert_rejected(changed)

    def test_matchup_substitution_rejected(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["games"][0]["seats"] = copy.deepcopy(changed["games"][1]["seats"])
        changed["games"][0]["pairing_id"] = changed["games"][1]["pairing_id"]
        self.assert_rejected(changed)

    def test_orientation_substitution_rejected(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["games"][0]["orientation"] = "reversed"
        self.assert_rejected(changed)

    def test_missing_game_rejected(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["games"].pop()
        self.assert_rejected(changed)

    def test_extra_game_rejected(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["games"].append(copy.deepcopy(changed["games"][-1]))
        self.assert_rejected(changed)

    def test_duplicate_game_rejected(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["games"][1] = copy.deepcopy(changed["games"][0])
        self.assert_rejected(changed)

    def test_reordered_games_rejected(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["games"].reverse()
        self.assert_rejected(changed)

    def test_boolean_substitution_for_numeric_field_rejected(self) -> None:
        changed = copy.deepcopy(self.manifest)
        changed["games"][0]["index"] = True
        self.assert_rejected(changed)


class VerifierAndRepositoryIdentityTests(unittest.TestCase):
    def test_matching_repository_identity_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            integrity.validate_repository_identity(
                repository_root=root,
                working_directory=root,
                git_top_level=root,
                origin=integrity.EXPECTED_ORIGIN,
                expected_root=root,
            )

    def test_active_verifier_pin_matches_candidate(self) -> None:
        verifier = CORRECTED_VERIFIER
        integrity.verify_file_identity(verifier, integrity.EXPECTED_VERIFIER_SHA256)

    def test_modified_verifier_rejected(self) -> None:
        verifier = CORRECTED_VERIFIER
        with tempfile.TemporaryDirectory() as temporary:
            changed = Path(temporary) / "verify_completed_batch.py"
            changed.write_bytes(verifier.read_bytes() + b"\n# changed\n")
            with self.assertRaises(integrity.IntegrityError):
                integrity.verify_file_identity(changed, integrity.EXPECTED_VERIFIER_SHA256)

    def test_missing_verifier_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "verify_completed_batch.py"
            with self.assertRaises(integrity.IntegrityError):
                integrity.verify_file_identity(missing, integrity.EXPECTED_VERIFIER_SHA256)

    def test_unexpected_working_directory_rejected(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temporary,
            self.assertRaises(integrity.IntegrityError),
        ):
            integrity.validate_repository_identity(
                repository_root=REPO_ROOT,
                working_directory=temporary,
                git_top_level=REPO_ROOT,
                origin=integrity.EXPECTED_ORIGIN,
            )

    def test_missing_or_incorrect_repository_identity_rejected(self) -> None:
        invalid_identities = (
            ("", integrity.EXPECTED_ORIGIN),
            (str(REPO_ROOT), "https://example.invalid/repo.git"),
        )
        for git_top_level, origin in invalid_identities:
            with (
                self.subTest(git_top_level=git_top_level, origin=origin),
                self.assertRaises(integrity.IntegrityError),
            ):
                integrity.validate_repository_identity(
                    repository_root=REPO_ROOT,
                    working_directory=REPO_ROOT,
                    git_top_level=git_top_level,
                    origin=origin,
                )


class WrapperOrderingTests(unittest.TestCase):
    def test_wrapper_pins_exact_integrity_helper_and_verifier(self) -> None:
        wrapper = (TEST_ROOT / "execute_approved_batch.integrity-v3.ps1").read_text(
            encoding="utf-8"
        )
        helper_path = INTEGRITY_HELPER
        helper_hash = integrity.file_sha256(helper_path)
        self.assertIn(f"$expectedIntegrityHelper = '{helper_hash}'", wrapper)
        self.assertIn(f"$expectedVerifier = '{integrity.EXPECTED_VERIFIER_SHA256}'", wrapper)
        self.assertIn(
            f'EXPECTED_VERIFIER_SHA256 = "{integrity.EXPECTED_VERIFIER_SHA256}"',
            helper_path.read_text(encoding="utf-8"),
        )

    def test_integrity_gate_precedes_first_grant_issuance(self) -> None:
        wrapper = (TEST_ROOT / "execute_approved_batch.integrity-v3.ps1").read_text(
            encoding="utf-8"
        )
        integrity_call = wrapper.index("$integrityLines = @(& $python")
        integrity_fail_closed = wrapper.index("Schedule/repository integrity preflight failed")
        create_execution_log = wrapper.index("New-Item -ItemType Directory -Path $logDir")
        issue_grant = wrapper.index("--issue-batch")
        self.assertLess(integrity_call, integrity_fail_closed)
        self.assertLess(integrity_fail_closed, create_execution_log)
        self.assertLess(create_execution_log, issue_grant)

    def test_verifier_rechecked_immediately_before_execution(self) -> None:
        wrapper = (TEST_ROOT / "execute_approved_batch.integrity-v3.ps1").read_text(
            encoding="utf-8"
        )
        existence = wrapper.index("Pinned post-run verifier candidate is missing")
        digest = wrapper.index("Post-run verifier identity mismatch")
        invocation = wrapper.index("$verifyLines = @(& $python")
        self.assertLess(existence, digest)
        self.assertLess(digest, invocation)
        self.assertLess(invocation - digest, 500)


if __name__ == "__main__":
    unittest.main()
