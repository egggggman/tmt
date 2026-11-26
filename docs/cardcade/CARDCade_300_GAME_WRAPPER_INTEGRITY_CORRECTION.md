# Cardcade 300-Game Wrapper Integrity Correction

**Status: READY FOR INDEPENDENT REVIEW; signing and execution remain blocked.**

This correction addresses the schedule-binding and path/verifier-integrity defects in the preserved 300-game wrapper. It does not authorize signing, grants, or gameplay. No authorizations were issued and no games were launched.

## Artifact identities

| Artifact | SHA-256 | Provenance/status |
|---|---|---|
| Original unsigned wrapper, preserved unchanged | `06bb9d0a95c3964779edcb30960be46ea1b109e8a6316194b7246417a445d5f5` | Existing wrapper; its bytes were not edited |
| Corrected wrapper candidate | `d715ba13d17a1510a980300549f956c853cef070d61baf6229ae090fda24327f` | Separate artifact; not signed or independently approved |
| Integrity helper | `21a86fbbabfb8da83252b486b4a3561ec78e792763ba1ece8fb19932da362686` | Exact helper pinned by the corrected wrapper |
| Post-run verifier candidate | `259c5f18edbfe262778ba351651c28f845901f687764193afb2d0ef85402f39a` | Byte-for-byte copy of the preserved 100-game verifier; independent approval was not found |
| Synthetic schedule fixture bundle | `030e2744fdf94a306eba9c7f9008f0710037f709850bdf6c19a6d9794b31ec79` | ZIP contains the unchanged schedule, sidecars, 30 manifests, and 30 preflight log/exit-code pairs |

The original unsigned wrapper remains at `.diag003-memory-independent-review/300-game-exploratory-r1/execute_approved_batch.ps1`. The corrected candidate is `execute_approved_batch.integrity-v2.ps1`; the other correction artifacts are in the same directory. The report is at `docs/cardcade/CARDCade_300_GAME_WRAPPER_INTEGRITY_CORRECTION.md`.

## Corrections

The helper pins both the schedule's raw-file SHA-256 (`3f6c0a0ec56fc788ae14287d3333364cffa547e420fad92ee4272debabfc3166`) and approved canonical digest (`9206c4267027473218f18e9482abcccb8a64dcfc62a7511d39b711a427a2179c`). It checks the 30 ordered blocks and 300 ordered games, then constructs each expected strict manifest directly from its schedule block and compares the entire canonical JSON representation. This covers execution-relevant top-level identities and every ordered game field, including run ID, seed, matchup, orientation/seats, output and authorization destinations, one-game invocation, and zero retries. Canonical-byte comparison is type-exact; Python's `True == 1` behavior cannot make a boolean pass as an integer. The helper also checks manifest sidecars, exact manifest-directory membership, and preserved successful preflight identities. It does not regenerate or repair any input.

The corrected wrapper derives its root from its own location, requires that root and the caller's working directory to be `C:\projects\tmt`, and verifies Git's top-level and `origin` repository identity. It hash-checks the helper and completes the schedule/repository validation before creating the execution log directory or invoking the issuer. It checks the pinned verifier at preflight and again immediately before invocation. Missing, changed, reparse-point, or mismatched verifier content is rejected.

The verifier SHA is deliberately labeled a **candidate pin** in the source. The preserved records identify the copied file and hash but do not establish independent approval of its content. That approval is an outstanding review gate; no claim of approval is made here.

## Exact source changes

The separate correction package contains:

- `execute_approved_batch.integrity-v2.ps1`: root and repository identity checks; pinned helper/verifier identities; pre-issuance gate; immediate verifier recheck.
- `batch_integrity_validation.py`: exact schedule-to-manifest projection, ordered-set and identity checks, type-exact canonical comparison, repository identity checks, and read-only preflight CLI.
- `verify_completed_batch.candidate.py`: byte-for-byte preserved verifier candidate, separately hashed.
- `tests/test_batch_integrity_validation.py`: deterministic synthetic positive and negative checks.
- The unchanged original wrapper plus the exact schedule, 30 strict manifests, their sidecars, and 30 preserved preflight logs/exit codes used by the tests.

The original wrapper, approved schedule, manifests, preflight evidence, simulator, controller, issuer, decks, and historical artifacts were not modified. The old report of the original wrapper remains unchanged.

## Synthetic validation

The isolated test command ran **18 tests: 18 passed**. Coverage includes:

- Positive validation of the unchanged approved schedule: all 30 blocks and 300 games.
- Rejection of seed, matchup, orientation, missing, extra, duplicate, reordered, and boolean-for-number substitutions.
- Rejection of changed and missing verifier files; verification of the candidate file's pinned digest.
- Rejection of unexpected working directory and missing/incorrect Git repository identity; acceptance of matching identity.
- Static ordering checks that the integrity gate precedes the first grant issuance and that verifier identity is rechecked immediately before invocation.
- Confirmation that wrapper and helper verifier pins agree.

The helper's read-only preflight also returned `SCHEDULE_MANIFESTS_VERIFIED`, 30 blocks, 300 games, with the approved canonical schedule digest. The corrected PowerShell wrapper passed parser validation. **The wrapper itself was not invoked.**

Final Ruff checks could not run in this environment: the repository `.venv` trampoline could not start its Python child (`entity not found`), and the qualified isolated Python has no Ruff module installed. No dependency was installed. Whitespace checks should be rerun in independent review/CI.

## Independent-review gate and remaining risks

The corrected wrapper has not been independently approved. In particular, an independent reviewer must inspect the exact wrapper/helper diff and the verifier source and imports, then either approve verifier SHA `259c5f18edbfe262778ba351651c28f845901f687764193afb2d0ef85402f39a` or require another reviewed verifier identity. The source pin and passing synthetic tests establish content checking, not trust in that content.

The wrapper remains tied to the expected `C:\projects\tmt` checkout and its existing workspace dependencies. The exact Git root/origin check is intended to prevent accidental execution elsewhere; relocating this artifact requires a new reviewed identity. Like any file check followed by execution, a concurrent same-user replacement remains a filesystem race unless the approved operational environment prevents writes to the dependency tree during execution. Existing issuer/controller/supervisor safeguards and their own identity checks remain required.

No signature or certificate was created, no execution-policy setting was changed, no grant was issued, and no gameplay was launched. The approved schedule digest remains `9206c4267027473218f18e9482abcccb8a64dcfc62a7511d39b711a427a2179c`.

**Recommendation: BLOCKED pending independent review and approval of the verifier identity.** After review, the workstation owner must separately approve the signing method; the signed artifact must receive independent signature/hash review; HQ must separately authorize gameplay. Passing this synthetic suite alone does not clear those gates.

## Review publication

The correction package is available as draft [PR #374](https://github.com/egggggman/tmt/pull/374), branch `fix/cardcade-300-wrapper-integrity`, targeting `main`. The current PR head is recorded by the branch ref; the report avoids self-referencing the commit that contains it. The PR is open and draft; it is not merged or approved.
