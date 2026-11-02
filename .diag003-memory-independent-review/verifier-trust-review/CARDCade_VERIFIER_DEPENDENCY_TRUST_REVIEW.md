# Cardcade Verifier Dependency and Trust Review

**Result: REVISE — verifier trust and artifact-integrity defects demonstrated.**

This was a read-only source review plus deterministic synthetic tests. The verifier and dependency sources were copied byte-for-byte into `sources/`; those originals were not edited. Tests used a temporary filesystem and a fixed test-only RSA key. They did not read or modify the real G: diagnostic directory, owner public key, live authorization files, consumption ledger, checkpoints, or RUN_STOP state. No grants were issued and no games were launched. PR #374 remains draft.

## Exact reviewed source files

| Source | Preserved path | SHA-256 |
|---|---|---|
| Post-run verifier | `.diag003-memory-independent-review/100-game-exploratory-r3/execution-preflight/verify_completed_batch.py` | `259c5f18edbfe262778ba351651c28f845901f687764193afb2d0ef85402f39a` |
| Authorization verification dependency | `.diag003-memory-independent-review/correction/tools/stage002_authorization.py` | `1fd4db87131a0fef996fc2df7aee5f6634fdbc2d7b90f226c76217596fdb6540` |
| Batch manifest/claims dependency | `.diag003-memory-independent-review/correction/tools/stage002_batch.py` | `30720c8d720b52a9538b79063d785e57dc37762bf5099215b7ee05cef0a80293` |

Exact byte copies are included in [`sources/verify_completed_batch.py`](sources/verify_completed_batch.py), [`sources/stage002_authorization.py`](sources/stage002_authorization.py), and [`sources/stage002_batch.py`](sources/stage002_batch.py). The tests verify each copy against the SHA-256 above before importing it.

## Dependency and trust findings

The verifier imports `canonical_claims`, `verify_claims`, `digest`, and `entry_claims` from the two Stage 002 modules through the hard-coded tools directory. The corrected wrapper pins the verifier file, but does not pin either imported dependency immediately before verifier execution. The helper checks their expected files exist but does not hash-check them. A verifier hash alone therefore does not identify the code actually used for claim and manifest verification.

`stage002_authorization.verify_rsa_sha256` implements RSA PKCS#1 v1.5 with SHA-256 and constant-time encoded-message comparison. `verify_claims` checks schema, all supplied expected claims, exact booleans/integers for expected scalar values, nonce syntax, and time validity. However, the verifier loads a public-key JSON file by path without checking its fingerprint against an independently approved key identity. The RSA parser accepts keys as small as 62 bytes; it does not enforce the operational RSA-3072 identity. The test key used here is a weak 512-bit mock key only and is not the owner key.

`stage002_batch.digest` and `entry_claims` canonicalize the manifest and bind each signed grant to one row plus the source/runtime/resource claims. The module also contains `validate_manifest` and a callback-driven `run_sequential_batch`; the verifier only imports the digest/claims helpers and does not call the dispatch function. Importing these modules did not run gameplay or write authorization state.

The verifier trusts the unsigned status JSON as the source of both completion state and the artifact hash inventory. It does not require a nonempty or complete list of mandatory artifact hashes, nor authenticate the status file or inventory against an external signed record. It also joins status-supplied artifact paths to the game output directory without rejecting `..` traversal or verifying resolved containment. It checks symlinks only on the final artifact path, not all parent components. `run_manifest.json` and `result.json` are opened without required-file hash membership or symlink/containment checks.

The verifier checks that a result winner is one of the two assigned decks, and that run ID, seed, completion state, source commit, limits, and batch digest are internally consistent. It cannot establish that an otherwise plausible result or winner is authentic if an attacker can alter the unsigned status/hash inventory and corresponding output together.

## Deterministic synthetic tests

Run command:

```powershell
& '.diag003-preparation\python-nuget-3.13.15\tools\python.exe' -P -s -B -m unittest discover -s '.diag003-memory-independent-review\verifier-trust-review' -p 'test_*.py' -v
```

Result: **9 tests passed**. The tests construct a ten-entry disposable manifest, result files, artifact files, signed mock grants, and consumption records under `TemporaryDirectory`; each test resets those fixtures. The test-only key is fixed and deterministic, and no private owner key is accessed.

| Test | Observed result | Interpretation |
|---|---|---|
| Untampered synthetic ten-game batch | Accepted; 10 games and 30 listed artifacts checked | Positive control |
| Result altered while its recorded artifact hash remains unchanged | Rejected | Hash detects isolated result-file change |
| Result winner changed and unsigned status hash updated | Accepted | **Finding:** mutable status/hash inventory can bless a changed result |
| Telemetry artifact altered with stale recorded hash | Rejected | Hash detects isolated artifact change |
| Artifact inventory emptied and telemetry altered | Accepted; 0 artifacts checked | **Finding:** incomplete inventory is treated as successful verification |
| Artifact entry uses `..\\..\\outside-assigned-game.bin` | Accepted | **Finding:** artifact path escapes the per-game output directory |
| Signed grant claim altered without re-signing | Rejected by RSA signature verification | Positive tamper rejection |
| Nonce consumption record missing | Rejected | Positive replay-evidence check |
| Nonce consumption record digest altered | Rejected | Positive tamper rejection |

“9 tests passed” means the assertions, including the three vulnerability-characterization assertions, behaved as expected. It does not mean the verifier passed trust review.

## Recommendation and required follow-up

Do not approve verifier SHA `259c5f18edbfe262778ba351651c28f845901f687764193afb2d0ef85402f39a` for execution yet. Smallest required correction package for a later authorized change:

1. Pin and verify both imported dependency hashes and the approved public-key identity/strength before verification.
2. Require an authenticated completion record or another immutable trust anchor for status and its complete mandatory artifact inventory.
3. Enforce resolved-path containment under the assigned game output and reject traversal/reparse-point parents.
4. Require and hash the mandatory result/run-manifest/telemetry files; do not report `VERIFIED_COMPLETE` when the list is missing or empty.
5. Add deterministic regression tests for those rejection rules, then obtain independent review of the exact verifier and dependency identities.

The existing source-only tests do not establish that the owner key file, G: ACLs, or Windows reparse-point behavior provide the required external trust boundary. No production source was modified under this review. Signing, grants, and all gameplay remain blocked; 0/300 games remain executed.
