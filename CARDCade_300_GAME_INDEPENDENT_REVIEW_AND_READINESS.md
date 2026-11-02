# Cardcade 300-Game Independent Review & Readiness

**Reviewed checkpoint:** `6aa3b0f50e677f1d9b67a5d8acde8c56bd68f93b`  
**Correction commit:** `6af09227806a4c2be990a4a95965a13ce2af9e64`  
**PR:** #374, draft, base `main`  
**Gameplay status:** BLOCKED — 0/300 games

## Decision

**BLOCKED — production execution trust is not implemented.** The exact checkpoint was reviewed from source. Two candidate-level issues were corrected in the continuation commit: the corrected verifier had reused the authorization public key to authenticate completion receipts, and the synthetic `EvidenceSnapshot` was only shallowly immutable. The verifier now requires a distinct receipt trust anchor and fails closed when none is configured; the synthetic snapshot now defensively copies and freezes its nested maps. These corrections improve the review candidate, but do not create the production issuer, attestor, Windows snapshot service, or signing boundary.

## Reviewed artifact identities

Hashes below are SHA-256 of checked-out raw bytes at correction commit `6af09227806a4c2be990a4a95965a13ce2af9e64`.

| Artifact | SHA-256 | Review status |
|---|---|---|
| Corrected batch verifier | `5f4b3b87b37afc8c4f4a8d18f0740e2b5504751106d448d597d6b41bb660d603` | Separate receipt verifier key is required; production trust anchor intentionally unset |
| Schedule integrity helper | `e342ac4ebca9103627a83028c0f6ca21c5be2bf916a955d54eb1fc815a7043ce` | Pins approved schedule, strict manifests, preflight and corrected verifier |
| Batch PowerShell wrapper v3 | `7b7063a22477f20c9437884a2c033d29f6a70138a05235073092564535238ee8` | Preserves reviewed wrapper flow; still requires owner-approved runtime controls |
| Synthetic trust-chain candidate | `1cdca7b204408715188cb3a26940abab839b5c2b432b8813fa5c0dd4d65eace7` | Test model only; no production OS/key access |
| Authorization dependency copy | `1fd4db87131a0fef996fc2df7aee5f6634fdbc2d7b90f226c76217596fdb6540` | Hash-pinned before import by verifier candidate |
| Batch dependency copy | `30720c8d720b52a9538b79063d785e57dc37762bf5099215b7ee05cef0a80293` | Hash-pinned before import by verifier candidate |
| Preserved 100-game verifier candidate | `86bd375f52df0e5d522547275f8845d2fcf535b54a6c60d56d0d6bb195ab9677` | Unmodified historical copy |
| Preserved verifier source copy | `259c5f18edbfe262778ba351651c28f845901f687764193afb2d0ef85402f39a` | Unmodified historical copy |
| Original unsigned wrapper | `06bb9d0a95c3964779edcb30960be46ea1b109e8a6316194b7246417a445d5f5` | Preserved; unsigned and not independently approved for execution |

The canonical 300-game schedule remains `9206c4267027473218f18e9482abcccb8a64dcfc62a7511d39b711a427a2179c`; its approved JSON file SHA-256 remains `3f6c0a0ec56fc788ae14287d3333364cffa547e420fad92ee4272debabfc3166`. No schedule rows, seeds, matchups, or orientations changed.

## Integrated review findings

### HIGH — Receipt and authorization trust anchors were shared at the checkpoint — corrected in `6af0922`

At checkpoint `6aa3b0f`, `verify_completed_batch.py` loaded one public key and passed it to both completion-receipt signature verification and grant verification. A compromised authorization signing authority could therefore authenticate a fabricated completion receipt. The corrected verifier has separate receipt-key path and fingerprint inputs, rejects equal authorization and receipt keys, and has no default production receipt key or fingerprint. Its CLI fails closed until those are independently approved and configured. Synthetic regressions cover authorization-key receipt signing, receipt-key substitution, and missing receipt trust configuration.

### MEDIUM — Synthetic evidence snapshots were not deeply immutable — corrected in `6af0922`

The frozen dataclass at `6aa3b0f` accepted mutable nested mappings. A caller retaining the original dictionaries could change the snapshot after construction. `EvidenceSnapshot.__post_init__` now copies each mapping, wraps outer and nested maps in read-only proxies, and requires byte values. A deterministic test mutates the original maps and attempts mutation through the snapshot. This only freezes in-process synthetic input; it does not create a stable filesystem snapshot.

### HIGH — Production attestation authority and provenance are absent — unresolved

The synthetic `create_execution_attestation` signs a caller-supplied mapping through an injected test signer. It does not obtain process exit, Job Object termination, resource-limit readback, grant consumption, or output hashes from Windows handles. No production supervisor attestation signer, CNG operation, inaccessible-to-worker signing API, or attestation verifier integration exists in the wrapper. The mock chain proves schema and signature checks only.

### HIGH — Production snapshot and no-replace receipt publication are absent — unresolved

The synthetic issuer receives `EvidenceSnapshot` bytes from its caller. `publish_no_replace` delegates to an injected publisher; the test publisher simulates reservation and interrupted publication. Neither is a Windows filesystem implementation. No service identity, ACL-isolated evidence capture, handle locking, reparse-safe stable snapshot, atomic no-replacement publication, or crash-recovery behavior has been verified on the target host. Same-user file replacement between checking and use remains outside the synthetic proof.

### HIGH — Effective Job Object enforcement is not authenticated by the model — unresolved

The synthetic attestation binds a claimed `memory_limit_bytes` and runtime limit, but does not independently demonstrate Windows Job Object flags or effective limit readback from the terminated job. The batch manifest and synthetic checks cannot prove the approved `2,997,489,664`-byte limit was applied by Windows. Production attestation must bind the approved accounting semantics and observed readback, and fail before trust is granted on mismatch.

### MEDIUM — The verified CI suite is intentionally not the full gameplay suite — unresolved

The synthetic workflow runs only four reviewed test files. The general workflow skips full repository pytest for PR #374 because that suite includes complete-game execution. Thus the trust candidates have targeted synthetic coverage, while full gameplay regression behavior at this source identity is unverified. No gameplay was launched by this review.

## What the code and tests establish

- `batch_integrity_validation.integrity-v2.py` verifies the preserved schedule digest, file digest, strict manifest projection and ordering, exact 30-manifest set, 300 rows, and preserved preflight identity before the wrapper invokes grant issuance. The synthetic schedule tests exercise substitutions, missing/extra/duplicate/reordered entries, and the full 30-block fixture.
- The corrected verifier pins and hashes imported authorization/batch modules before import; validates signed grant claims against the manifest; rejects duplicate nonces; checks consumption-record digests; enforces required artifact inventories and hashes; and rejects absolute, traversal, out-of-tree, and Windows reparse-point paths.
- The synthetic chain uses three separate test keys for authorization, attestation, and receipt signing. It verifies a complete ten-game mock batch and rejects tampered grants, attestations, results, inventories, key substitution, missing consumption, path escape, interrupted signing/publication, and conflicting receipt destinations.
- The synthetic issuer validates all scheduled records before requesting a receipt signature. Failure injection shows no final receipt is published on the tested failures. These are test doubles, not production controls.
- The synthetic CI command names exactly four test files and does not invoke the batch wrapper, issuer, supervisor, live keys, or gameplay. The general workflow's complete pytest step was skipped only for PR #374; formatting, lint, and terminology checks still ran.

## Validation

For correction commit `6af09227806a4c2be990a4a95965a13ce2af9e64`:

- GitHub [synthetic trust CI run 41531229001](https://github.com/egggggman/tmt/actions/runs/41531229001): **55 passed, 1 skipped**, Ruff format and Ruff lint passed. The skip is the Windows junction creation test on Ubuntu; the test remains enabled on Windows. Pytest reports one harmless collection warning for helper class `TestSigner`.
- GitHub [general CI run 41531229038](https://github.com/egggggman/tmt/actions/runs/41531229038): **passed**. Ruff format, Ruff lint, and terminology scan passed; the full pytest step was skipped by the PR #374 synthetic-only condition.
- Local Windows: **56 unittest cases run, 55 passed, 1 skipped** because Windows denied disposable symlink creation; the junction-escape check passed.
- Local Ruff format check: **691 files already formatted**. Ruff lint and `git diff --check` passed.
- No production grants or receipts were issued; the synthetic tests use only disposable test keys and fixtures. The wrapper was not executed and no games were launched.

## Production implementation and approval plan

1. **Supervisor attestor:** implement inside the existing trusted Stage 002 supervisor. It must collect facts from terminated child/Job Object handles and protected output handles, sign only with a dedicated non-exportable attestation key, and expose no signing operation to workers or the batch controller. Bind source, runtime, grant/nonce, effective Job Object readback, timeout/exit state, and complete artifact inventory.
2. **Receipt issuer:** implement as a separate restricted Windows service. Independently validate the exact approved block and all ten supervisor attestations, grant consumption, and output identities. Use a third dedicated non-exportable receipt key. Do not accept caller-supplied trust anchors or arbitrary verifier paths.
3. **Evidence capture/publication:** open approved paths without following reparse points, capture a stable immutable byte snapshot under a restricted service identity, hash every required artifact, and atomically publish using a no-replace Windows operation. Define and test interruption recovery without replacing a receipt or trusting partial state.
4. **Verifier trust configuration:** approve distinct authorization, attestation, and receipt public-key fingerprints through an independent trust anchor. Configure the corrected verifier only after these identities are approved; until then its CLI remains fail-closed.
5. **Windows execution identity:** owner provisions the dedicated service identity, private-key ACLs, evidence/output ACLs, and a signing interface that the gameplay process cannot invoke. Verify AppContainer access, Job Object flags and exact readback on disposable protected replicas.
6. **Wrapper signing:** preserve the unsigned artifact; owner selects a trusted code-signing certificate and confirms effective Group Policy permits the process-only launch method. Sign a separately identified copy, verify Authenticode signer/trust and SHA-256, then obtain independent approval of that exact signed artifact.
7. **Final authorization:** only after independent code/security review, workstation-owner approval, and exact source/input/output preflight may HQ consider a separate gameplay authorization. This report grants none.

### Workstation-owner checklist

- Approve the service account and ACL design, CNG key purposes, signer isolation, and trust-store/certificate process.
- Approve the signing certificate and process-only execution policy method; do not change machine/user policy outside that approval.
- Verify the three distinct public-key fingerprints and the final signed wrapper artifact.
- Confirm protected historical-data boundaries and disposable output ACLs.

### Remaining HQ gates

- Independent acceptance of this corrected candidate and the production service/attestor design.
- Owner approval and implementation of production keys, service identities, ACLs, and trust anchors.
- Verified stable snapshot and Windows atomic no-replace publication.
- Independent approval of final signed wrapper identity.
- Explicit HQ authorization to issue grants and launch the 300-game batch.

## Recommendation / NEXT MOVE

**BLOCKED — 0/300 games.** The synthetic trust chain passes, but no production attestation signer, receipt issuer, stable Windows evidence capture, atomic receipt publication, or approved production trust anchors exist. PR #374 remains draft. The smallest next action is independent review of commit `6af09227806a4c2be990a4a95965a13ce2af9e64`, followed by workstation-owner approval of the separate production signing identities and Windows service/ACL design. Do not sign, issue production grants, or launch the wrapper until those gates are satisfied.
