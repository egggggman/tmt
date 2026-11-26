# Independent review: PR #427 source guard and PR #406 evidence

**Verdict: ACCEPT** for the bounded source-guard correction at exact candidate HEAD
`dcc2fc692240691dbcec09971bc0b6e8dbdaa9c2`.

This review is independent of the implementation run. It is not merge authorization, production approval, or permission to execute gameplay. PR #427 remains draft and unmerged.

## Audited source identity

- Candidate repository: `egggggman/tmt`
- Candidate HEAD: `dcc2fc692240691dbcec09971bc0b6e8dbdaa9c2`
- Candidate tree: `370b48fe0e0b978f19ea4a217357cbe5407b288d`
- Candidate parent: `a47f2b5a81720c6283983f1ca5ad0331cac59098`
- Trusted integration baseline: `891963754d7cc6342ae963a0bf4b69918861460f`
- Worktree was clean during review. Only the launcher and its safety test module differ from the base.

## Source-guard assessment

The guard uses Git's `merge-base --is-ancestor` operation. It requires the immutable trusted baseline to be an ancestor of `origin/main`, then requires `origin/main` and the exact implementation checkout to be ancestor-comparable. This permits the pre-merge PR checkout (main is its ancestor) and a history-preserving post-merge main (the checkout is its ancestor). Stale pre-integration, unrelated, and divergent histories fail closed. Git ancestry errors other than the ordinary “not an ancestor” result raise `DiagnosticLauncherError`.

Ancestry does not authorize implementation code. The signed HQ source approval and separate run authorization are still verified; both must bind the exact checked-out implementation SHA. The launcher still checks the six frozen-input hashes, imported source identity, and clean worktree before dispatch. The production trust-key registry remains empty.

## Independent synthetic validation

Reran the reviewed launcher, source-pin, authorization/reconciliation, capture, stop-ledger, and two Stage 002 transaction tests at the exact candidate SHA. No complete gameplay was executed.

- Synthetic cases: **61 passed**.
- Ruff format: **730 files already formatted**.
- Ruff lint: **passed**.
- Base-to-candidate `git diff --check`: **passed**.

The 61 cases cover current main, future merge ancestry, stale main, unrelated and divergent history, exact source-SHA binding, a tampered source signature, frozen-input mismatch, and fail-closed dispatch behavior, along with inherited capture and reconciliation regressions.

## PR #406 artifact investigation

The original execution metadata records authorized and observed source HEAD
`67b9bb3083c9f4b2fe02e7fed258c4739581225f`; the source worktree was
`C:\\projects\\tmt\\.diag001-pr404-67b9bb3`.

All nine files in the retained original output directory
`C:\\projects\\tmt\\.cardcade-diagnostic-001-pr404-67b9bb3-20261107`
match its `artifact_sha256.json` manifest. All nine files in the available report worktree also match:

- Report worktree: `C:\\projects\\tmt\\.cardcade-diagnostic001-report`
- Branch: `reports/cardcade-diagnostic-game-001`
- HEAD: `51789292867bddfc364817d389c12294fb74a79c`
- The report worktree's `run_once.py` is 6,124 bytes and hashes to the expected `aa2004aff460142ee20114466f9bb291d78d24283cadf855afc12aaf7a49bae0`. Its raw bytes equal the retained original output file byte for byte.

The earlier observed `3ae6f1e2475e5c423fab4dd70de6364c6d76aa217ce1c4552f63802b49f98057` came from the Windows `git archive` export copy, not either original raw file:

| Representation | Size | SHA-256 | Git identity / line endings |
|---|---:|---|---|
| Retained output raw file | 6,124 bytes | `aa2004aff460142ee20114466f9bb291d78d24283cadf855afc12aaf7a49bae0` | Raw blob ID `f3c60c4254bbe4e3d79947f5f5f55f9c9b5fabd7`; UTF-8 BOM; 4 CRLF pairs and 109 LF-only newlines |
| Report worktree raw file at `5178929…` | 6,124 bytes | `aa2004aff460142ee20114466f9bb291d78d24283cadf855afc12aaf7a49bae0` | Byte-for-byte equal to retained output |
| Report branch Git blob | 6,120 bytes | `ee3e984e537b51b43faabe3b0eb41c83c44c701e93975259d59de4ca8c2ae737` | Blob ID `73a54df9d0588f46265264997dcafc400ae6f0fb`; UTF-8 BOM; LF-only |
| Windows `git archive` ZIP entry/export | 6,233 bytes | `3ae6f1e2475e5c423fab4dd70de6364c6d76aa217ce1c4552f63802b49f98057` | Raw blob ID `f93cd03901290a3be05fde1a6254e912d2efaa5c`; UTF-8 BOM; 113 CRLF pairs |

The export copy was created at
`C:\\Users\\cowabunga\\AppData\\Local\\Temp\\pr406-artifacts-e375a3cc856f42fab49fcd17de730e24.zip`
and extracted under the matching `pr406-artifacts-e375a3cc856f42fab49fcd17de730e24` directory. The repository's system Git config reports `core.autocrlf=true`; no path-specific text/eol attribute applies to this artifact. After normalizing CRLF to LF, the original output, report-branch blob, and archive export are each exactly the same 6,120-byte sequence. The UTF-8 BOM is present in all three. No source-content difference exists; the different SHA-256 values are due solely to line-ending representation.

**Classification:** verification/path-handling error in the earlier check. It hashed a Windows archive/export representation instead of the retained raw output. This is not a distinct historical code version or a genuine content-integrity mismatch. The original raw bytes remain available and match the manifest. The other eight artifacts also match in both retained locations.

The three original reconciliation stops were independently read from the preserved report and remain:
1. `stop-000001`, `illegal_mutation`, turn 16 / `combat_damage`.
2. `silent_approximation`, `presence_evidence_missing`.
3. `silent_approximation`, the preserved trample/combat event and object references.

No artifact, manifest, deck, Baseline 005 file, or accepted decision was changed.

## Handoff

**ACCEPT** the bounded ancestry guard and historical evidence integrity finding. Keep PR #427 draft and unmerged pending HQ disposition. This verdict authorizes no merge, production credentials, real permits, Windows ACL changes, gameplay, Smoke, calibration, deck changes, or baseline promotion.
