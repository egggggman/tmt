# Cardcade Verifier Trust Correction

**Recommendation: REVISE / NOT APPROVED FOR EXECUTION.** The verifier changes pass disposable tests and are ready for independent review. Execution remains blocked because no approved production completion-receipt signer is integrated, and the corrected verifier, wrapper, dependency pins, and evidence-signing use still require independent approval.

PR #374 remains draft. No production source, schedule, manifest, historic result, live key, grant store, or consumption ledger was modified or read. No live grant was issued and no game was launched. HQ status remains **0/300**.

## Identities

| Artifact | SHA-256 | Status |
|---|---|---|
| Original post-run verifier | `259c5f18edbfe262778ba351651c28f845901f687764193afb2d0ef85402f39a` | Preserved byte-for-byte in `sources/verify_completed_batch.py` |
| Corrected verifier candidate | `45d920a2128e430574ab2eed96f3bc62281d8128ab4e81b0155b7bc710232385` | New file under `corrected/`; unsigned and not independently approved |
| Existing authorization dependency | `1fd4db87131a0fef996fc2df7aee5f6634fdbc2d7b90f226c76217596fdb6540` | Exact unchanged source copy; pin is enforced before import |
| Existing batch dependency | `30720c8d720b52a9538b79063d785e57dc37762bf5099215b7ee05cef0a80293` | Exact unchanged source copy; pin is enforced before import |
| Revised schedule-validation helper | `b1fafc333a3c4a0720c8b84c23639eac70c40a09c6f180ac70d9ab9fa93af41d` | Separate copy pins corrected verifier identity |
| Corrected wrapper candidate | `f912753455f03013b484fde989a966fefc682aa41a16b2253d59a9dd8e8757ad` | New `integrity-v3` candidate; original wrapper unchanged |
| Test suite | `711790664981ef7dfd6a2d28f862b231bd45192e85bdaf0e8ae97729e6d5a51e` | Deterministic disposable tests |

The pinned public-key identity is `7cfe29b81f719601fd7c0a75925d6cdf4347d18e010df610745dc4d8642f3427`, matching the existing expected hash recorded in the reviewed issuer and supervisor source. The verifier requires an RSA-3072 modulus and exponent 65537 and compares the key file's raw SHA-256 before use. The live public-key file was not opened; tests use an isolated test-only key and pass its expected hash explicitly.

## Exact correction

The corrected verifier requires a detached `cardcade-stage002-batch-completion-v1` receipt at:

`G:\cardcade\diagnostics\<batch_id>.completion-receipt.json`

The receipt signature covers the batch ID, approved manifest digest, exact raw SHA-256 of the completed status file, and ten-game completion count. This separates **authenticity** (RSA signature from the pinned public key) from **internal consistency** (the signed status agrees with the manifest, game results, artifacts, grants, and consumption records). Recomputing unsigned hashes cannot make a changed status or result authentic.

Before importing either dependency, the verifier hashes both exact dependency files and rejects a mismatch. Before grant verification it hashes and validates the public key against the existing identity pin. It requires the frozen supervisor's five-file completed-game set: `status.json`, `run_manifest.json`, `result.json`, `stdout.log`, and `stderr.log`. Every file in the game output tree must appear in the signed inventory, and the inventory may not omit any required file.

Artifact paths reject absolute and drive-qualified forms, empty/dot/traversal components, Windows case-fold collisions, symlinks, junctions, and other reparse points. Each path is checked for containment before file hashing. The status, receipt, grant, public key, and consumption-record reads also reject reparse paths. Result/run-manifest fields are checked against the manifest and frozen execution identities; full event telemetry must be present in the result snapshot.

`execute_approved_batch.integrity-v3.ps1` uses the corrected verifier and helper hashes. The pre-issuance schedule/repository gate remains before the first issuer call. The original wrapper, original verifier, earlier correction candidate, and approved schedule package remain unchanged.

## Synthetic validation

Command:

```powershell
& '.diag003-preparation\python-nuget-3.13.15\tools\python.exe' -P -s -B -m unittest discover -s '.diag003-memory-independent-review\verifier-trust-review' -p 'test_*.py' -v
```

Combined old characterization and new correction suite: **24 tests run, 23 passed, 1 skipped**. The skipped case attempted an OS symlink and Windows returned `WinError 1314` (privilege not held). A real disposable Windows directory-junction/reparse escape test passed. The new correction suite's successful batch validates ten synthetic grants, 50 required artifacts, and a signed mock receipt.

| Required case | Result |
|---|---|
| Modified result, status unchanged | Rejected by artifact hash |
| Modified result and recomputed unsigned status hash | Rejected by signed status-digest receipt |
| Empty inventory | Rejected |
| Missing required artifact | Rejected |
| Traversal path | Rejected before hashing |
| Absolute/out-of-tree path | Rejected |
| Symlink/reparse escape | Symlink creation skipped by OS permission; Windows junction escape rejected |
| Modified imported dependency | Rejected before module import |
| Unexpected public key | Rejected by raw-byte SHA pin |
| Tampered authorization grant | Rejected by RSA signature verification |
| Missing or modified consumption record | Both rejected |
| Complete valid synthetic batch | Accepted: 10 games, 50 artifact hashes rechecked |

The separate 300-schedule integrity preflight passed: 30 blocks / 300 games, approved digest `9206c4267027473218f18e9482abcccb8a64dcfc62a7511d39b711a427a2179c`. The corrected PowerShell wrapper parsed successfully, and whitespace checks passed. The wrapper was not invoked. Ruff was not run because the available virtual environment cannot launch its Python child and the qualified interpreter does not have Ruff installed.

## Remaining gates and limitations

No production receipt writer currently exists. The corrected verifier will fail closed until a separately reviewed, owner-controlled process signs a completion receipt after a block completes and before post-run verification. The mock signer in the tests is test-only; it cannot be used for production. The existing HQ public-key hash is an identity pin sourced from issuer/supervisor code, but independent reviewers must approve its use for completion receipts, not infer that approval from the code constant.

Independent review must cover the exact corrected verifier and wrapper hashes, dependency candidates, key identity/purpose, receipt schema and signer isolation. Workstation-owner signing-method approval, signed-artifact approval, and HQ gameplay authorization remain distinct gates.

**Conclusion: READY FOR INDEPENDENT REVIEW; BLOCKED FOR SIGNING AND GAMEPLAY.** PR #374 is to remain draft. No merges, grants, signing, or execution are authorized by this report.
