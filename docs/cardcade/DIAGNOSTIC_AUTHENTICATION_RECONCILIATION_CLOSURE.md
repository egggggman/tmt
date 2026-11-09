# Diagnostic Authorization and Reconciliation Closure

## Source and scope

- Authorized starting source: PR #417 `6ded938a7680e767f9ac5e231774591ef461a27b`.
- Correction branch: `fix/cardcade-diagnostic-auth-reconciliation`.
- Tested implementation HEAD: `8e6fd7e74b4f76c992bc30b4f4e231184d2f5b84`.
- Isolated worktree: `C:\projects\tmt\.cardcade-diagnostic-auth-reconciliation-correction`.
- Accepted main remained `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.
- Runtime: Python 3.12.10, pytest 8.4.2, cryptography 46.0.7, Ruff 0.16.1.
- Imported Stage 002 and engine modules were both from this worktree's `src`; `stage002.Game is engine07.Game`.
- No gameplay loop, complete game, smoke run, calibration, or real authorization was executed.

The final tested code adds `cryptography>=44,<47` and locks its resolved dependencies. Changes do not modify Stage 002, the decks, frozen card data, or Baseline 005.

## RED before correction

The two PR #418 reproductions were added first in commit `6e52a4d44a3580fb29b9026af839a06db4d3e3a8`, then run against the unchanged PR #417 implementation. Both failed as expected:

- `tests/test_cardcade_diagnostic_auth_reconciliation.py::test_unsigned_authorization_documents_are_rejected`: unsigned exact-field JSON was accepted.
- `tests/test_cardcade_diagnostic_auth_reconciliation.py::test_incomplete_stage002_reconciliation_cannot_return_ready`: a terminal synthetic snapshot paired with a two-field reconciliation object was accepted.

The observed prior PR #418 behavior was reproduced: caller-created approval JSON matching the current checkout passed `_verify_source()`. A reconciliation result containing only `{"stop_records": [], "invariant_violations": []}` yielded `READY` and CLI exit 0.

## Authorization signature contract

Source approvals and run authorizations now require detached Ed25519 signatures from the same trusted `signing_key_id`.

- Signature bytes are Base64 encoded.
- The signed payload is the canonical UTF-8 JSON encoding of every document field except `signature`, with sorted keys and compact separators. This includes the signer ID and all source, frozen-input, game, and authorization fields.
- The launcher requires exact schema field sets and rejects duplicate JSON keys, missing/extra fields, malformed signatures, altered content, unknown signers, mismatched signer IDs, source/run cross-binding errors, wrong HEADs, and unapproved input hashes.
- Existing durable exclusive one-use claims are unchanged.
- The signing private key is never in the launcher. Synthetic test-only Ed25519 keys are generated in memory by test support and are not persisted.

**Production trust-anchor status:** `TRUSTED_HQ_AUTHORIZATION_KEYS` is intentionally empty in this candidate. It fails closed for every real authorization until HQ provisions a reviewed public key in a subsequent source change. The actual HQ private signing key must be provisioned and held outside the repository and launcher. After a public key is provisioned, the source HEAD will change and HQ must sign approvals for that exact new HEAD. No real permits are included in this PR.

## Stage 002 reconciliation contract

The launcher validates the report returned by `stage002.reconcile_snapshot` against Stage 002's complete current report field set. It checks:

- The report digest equals `stage002.stable_digest` of the report body without `report_digest`.
- Required reconciliation fields and collection types are present; missing or unexpected fields block acceptance.
- Game ID, seed, orientation, seat order, terminal state, winner, turn, and RNG state match the authorized `GameSpec` and captured snapshot.
- The Stage 002 manifest's own digest is valid, its stage is `acceptance-002`, its game list contains the exact authorized match, and its card-data snapshot hash matches the approved frozen card-data input.
- The report's authoritative-evidence projection matches the preserved snapshot. Executed references and opportunity evidence match snapshot conformance; invariant evidence matches the event stream.
- Any validation failure is retained as reconciliation evidence, marks the diagnostic `BLOCKED`, and causes nonzero CLI exit. The snapshot and raw reconciliation result are kept.

The reconciler receives deep copies so it cannot mutate the authoritative in-memory snapshot or manifest while producing its report. A `reconciliation_binding.json` sidecar binds the report digest to the exact game, implementation SHA, Stage 002 source hash, and verified manifest digest. Existing stop-record, invariant, terminal-state, and presence blockers remain active.

## Synthetic RED/GREEN validation

The RED selections above each produced one expected failure on starting source `6ded938...`. The corrected 13-case selection passed on tested implementation `8e6fd7e...`:

- `test_unsigned_authorization_documents_are_rejected`
- `test_valid_synthetic_signature_is_bound_to_both_documents`
- `test_altered_authorization_content_fails_signature_verification` (two document cases)
- `test_source_and_run_authorization_must_use_same_trusted_signer`
- `test_unknown_signer_and_unconfigured_trust_anchor_fail_closed`
- `test_duplicate_json_authorization_fields_are_rejected`
- `test_incomplete_stage002_reconciliation_cannot_return_ready`
- `test_actual_reconciliation_digest_and_manifest_binding_are_preserved`
- `test_incomplete_or_altered_stage002_report_is_blocked` (digest, game identity, source evidence, and manifest-game cases)

Result: **13 passed, 0 failed, 0 skipped**.

The previous 36 named launcher, authorization, capture-lifecycle, and terminal-combat cases were rerun together with those new cases on the same tested implementation HEAD. Result: **49 passed, 0 failed, 0 skipped**. The exact previous 36-node list is preserved in `docs/cardcade/DIAGNOSTIC_LAUNCHER_SAFETY_CORRECTION.md`; the new nodes above were added to that selection. All tests use synthetic fixtures; the executor constructs initial state and snapshots without entering gameplay.

Commands:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & .venv\Scripts\python.exe -B -m pytest -q tests\test_cardcade_diagnostic_auth_reconciliation.py
```

The 49-case run used the same individually named pytest node selection documented in the PR #417 safety report, plus the nine new nodes listed above (13 parameter-expanded cases).

Quality checks passed on the changed Python files:

- `ruff format --check`
- `ruff check`
- `git diff --check` and the full correction-range whitespace check

## Frozen and historical evidence

All six approved frozen input hashes matched the launcher allowlist: Stage 002 source, April deck, Casey deck, card-data JSON, card-data manifest, and Baseline 005 manifest.

All nine preserved PR #406 diagnostic artifacts were rehashed and matched their previous full SHA-256 values. Its three historical stop records remain unchanged:

1. `illegal_mutation`, `stop-000001`, turn 16 / `combat_damage`.
2. `silent_approximation` with `presence_evidence_missing`.
3. `silent_approximation` with the preserved trample/combat event and object identities.

Accepted main, PR #417, PR #418, frozen decks, card data, Baseline 005, and historical artifacts remain unchanged.

## Remaining limitation and handoff

The cryptographic validation code is exercised only with ephemeral synthetic test keys. No production HQ public key was supplied, so this candidate intentionally cannot accept any real approval yet. HQ must provision a reviewed public trust anchor and retain the corresponding private signer outside the repository and launcher before issuing a future run authorization.

**Recommendation: READY FOR INDEPENDENT REVIEW OF THIS CORRECTION.** The launcher remains fail-closed for real use until HQ trust-anchor provisioning is completed. Diagnostic Game 002 and all gameplay remain unauthorized.
