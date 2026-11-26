# Final Pre-Integration Validation

## Verdict

**Source integration: READY for HQ review of controlled integration.** The cumulative implementation passed the accepted launcher selection and the individually selected inherited engine, pilot, payment, and composition regressions at the exact candidate SHA.

**Production trust-anchor implementation: BLOCKED.** This Windows workspace is not a suitably restricted designated runner: its root and shared durable-claim directory inherit `Authenticated Users: Modify`, the production public-key registry is empty, and no deployed service account, permit ACL, or revocation procedure has been validated.

No merge, production key, real permit, gameplay, deck edit, or historical evidence change occurred.

## Source identity and review scope

- Candidate and tested source: `92a29a3263d8555029904e8d4c9f097f38c50605`.
- Disposable worktree: `C:\\projects\\tmt\\.cardcade-final-preintegration-validation`, detached, clean before validation; final `git status --short` remained empty.
- Accepted main: `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`; it remains an ancestor of the candidate and was not changed.
- Cumulative diff against main: 65 files, 14,382 insertions, 320 deletions. It contains five runtime modules, two tools, 30 test files, 25 documentation files, `pyproject.toml`, `uv.lock`, and `.gitignore`. Frozen decks, card data, and Baseline 005 are outside the diff.
- PR #424 remains open, draft, and unmerged. Its existing report-only branch is used for this supplemental report.

## Environment and locked dependencies

The project environment was created from the checked-in lock in the disposable worktree using:

```powershell
uv run --locked --offline --python 'C:\\Users\\cowabunga\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' -- python -c "import sys,pytest,cryptography; print(sys.version); print(pytest.__version__); print(cryptography.__version__)"
uv lock --check
```

Observed versions: Python 3.12.10, pytest 8.4.2, cryptography 46.0.7, Ruff 0.16.1. `uv lock --check` passed and resolved 17 packages. The launcher, engine, and Stage 002 imports resolved inside this exact candidate worktree:

- `tools/cardcade_diagnostic_launcher.py`
- `src/tmnt_design_studio/engine07.py`
- `src/tmnt_design_studio/stage002.py`

`TRUSTED_HQ_AUTHORIZATION_KEYS` contains zero keys.

## Synthetic validation

All test selections were individually named, run with `PYTHONDONTWRITEBYTECODE=1`, `-B`, and pytest's cache provider disabled. The sum below is 198 passing test executions across groups; selections overlap, so it is not a count of unique test cases.

| Selection | Named selection source | Result |
| --- | --- | --- |
| Accepted launcher, capture, terminal, signature, reconciliation, and valid-digest forgery regression | The 35 launcher/capture/terminal nodes in `DIAGNOSTIC_LAUNCHER_SAFETY_CORRECTION.md`, nine auth/reconciliation nodes in `DIAGNOSTIC_AUTHENTICATION_RECONCILIATION_CLOSURE.md`, and six forgery nodes in `PR419_RECONCILIATION_AUTHENTICITY_CORRECTION.md` | 55 passed, 0 failed, 0 skipped |
| Inherited PR #381–#386 combined engine selection plus final fidelity gate | Exact selection in `CARDCade_PR381_382_385_COMBINED_VALIDATION.md` | 56 passed, 0 failed, 0 skipped |
| Pilot fidelity and supported mechanics | 54 named nodes listed in `PILOT_FIDELITY_CORRECTION_ACCEPTANCE.md` | 56 passed, 0 failed, 0 skipped |
| Restricted activated-ability payment compatibility | 27 named nodes listed in `RESTRICTED_ABILITY_PAYMENT_INTEGRATION_ACCEPTANCE.md` | 27 passed, 0 failed, 0 skipped |
| Main-cast trigger/priority composition | Four named nodes in `test_integrated_readiness_audit.py`, including Punks → Pizza → Ravenous Robots through `execute_main_action` | 4 passed, 0 failed, 0 skipped |

The selections cover source and frozen-input binding, Ed25519 verification using synthetic credentials, cross-process one-use claims, failed-execution claim persistence, no retry, complete reconciliation agreement, report forgery rejection, capture lifecycle, terminal combat, priority, Pizza, April, Ravenous Robots, Punks, restricted spell/ability payment, Frog Butler compatibility, and ordinary cast compatibility. Every selected test uses synthetic fixtures; no gameplay runner or complete game was invoked.

Each pytest process used this command form with the individually named IDs from the cited selection documents:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH=(Resolve-Path src).Path
& .venv\\Scripts\\python.exe -B -m pytest -q -p no:cacheprovider <named test node IDs>
```

The 37 changed Python files pass `ruff format --check` and `ruff check`. `git diff --check 10d2ac80ef5b81b3a209a3133eb0a84633a1f944...92a29a3263d8555029904e8d4c9f097f38c50605` passed. The candidate worktree remained clean.

## Frozen inputs

All six approved frozen-input digests were recomputed from the candidate worktree and matched:

| Input | SHA-256 |
| --- | --- |
| `src/tmnt_design_studio/stage002.py` | `69ecb217234ac892509de0fbe6417601826909b3fceba77f4a865d4959db8f1b` |
| April prototype deck | `684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4` |
| Casey prototype deck | `0fc0adbb370ecfddad03692a4229a04b23268739914a8f2a004b8e042ff3cebb` |
| Frozen card-data JSON | `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402` |
| Frozen card-data manifest | `6b5271af75150a361f77e7b89306c709959dfdf497c448dfdc978e5dc9a17950` |
| Baseline 005 manifest | `532bad7e489eb25f3184b5a90487e1361f7a2b19b8c02cac3c4115a0fc3e14bc` |

Deck prototypes, Baseline 005, and frozen card data remain byte-identical.

## Diagnostic Game 001 evidence

The nine artifacts in the preserved PR #406 replay bundle were rehashed read-only against its `artifact_sha256.json`; all nine matched. The index SHA-256 is `8d37d74145fa0349d86515fc96c0ba8155247343febd2b48db811bbc189d596d`.

| Replay artifact | SHA-256 |
| --- | --- |
| `events.json` | `e25d42bb57d75bc9ae0d1400d3abc840a67c9908f28c35e0d26a6ff31b245bec` |
| `exception.json` | `d9c2de38b2604a149eec2b693e337bc7ed36713f202f8d4050bb16660b2dd3d3` |
| `priority_stack_combat_trace.json` | `94d7f067506ce754479b5a718153c8fc1b354f37b5c0dd0c826b0561717754b5` |
| `reconciliation.json` | `7e943b7cde607cff0bea4018447a4b33f6a74244d2efb997a6fd7be875a65425` |
| `run_metadata.json` | `9ad906f7339f2e72b4f8321b4eef47abb8992ff862bfee344915eea5edbc3272` |
| `run_once.py` | `aa2004aff460142ee20114466f9bb291d78d24283cadf855afc12aaf7a49bae0` |
| `run_status.json` | `532ac90c2c82dbd9dbc3ddbe6ce9b047133afdc2bca3c02a1a1a222f102c5cf8` |
| `snapshot.json` | `53092f2e688c6b6f158d5012419a95fa31f948bbcb115184a13809e65962142a` |
| `stage_manifest.json` | `414b6ec1482c0e1874f8685479781071786f3ab1bb27448a5a5161bd1152fcbb` |

The replay's three historical stop records remain in order and unchanged: `stop-000001` (`illegal_mutation`, turn 16 / `combat_damage`); `silent_approximation` with `presence_evidence_missing`; and `silent_approximation` with the recorded trample/combat event and object references. No record was reconstructed, removed, or reclassified.

For clarity, the separate raw Smoke 001 directory at `.cardcade-smoke-001-8f9ed012-20261106` also retained its own artifact hashes, but its original saved reconciliation and run-status files report zero stop records. The three stops above belong to the preserved PR #406 replay bundle at `.cardcade-diagnostic001-report\\docs\\cardcade\\diagnostic_game_001\\evidence`, not that raw bundle. Both directories were read-only during this audit.

## Windows single-host operational check

The machine's C: volume is NTFS. Read-only `Get-Acl` inspection found:

- `C:\\projects\\tmt` is owned by `CARDCADE\\cowabunga`, but inherits `NT AUTHORITY\\Authenticated Users: Modify`; `CARDCADE\\CodexSandboxUsers` also has Modify. The disposable worktree inherits those entries.
- `C:\\projects\\tmt\\.cardcade-diagnostic-claims` inherits the same broad Modify access. The launcher creates durable claims under this directory adjacent to the repository's common Git directory.
- The temporary directory is owned by `CARDCADE\\cowabunga` and grants `CARDCADE\\CodexSandboxUsers: Modify`. No production approval or run-authorization files exist here, so their intended deployed ACL could not be verified.

Technical controls were exercised synthetically: exclusive cross-process claim creation, claim persistence after execution failure, single executor call, and zero retries passed. The claims are local to one shared filesystem and do not coordinate separate machines. The test suite did not simulate power loss or validate backup/restore recovery. The launcher does not set or audit NTFS ACLs and is not an OS process sandbox.

The empty trusted-key registry rejects all real permits. No production key or permit was created, installed, or used. There is no online revocation service; operational revocation and designated-host restrictions remain undefined.

## Recommendations

### Source integration — READY for HQ review

The exact candidate passed the 55 launcher cases and the additional inherited deterministic/invariant selections. Source ancestry, locked dependency resolution, source imports, six frozen inputs, nine replay-artifact hashes, and the three replay stop records were verified. This recommendation is for controlled source-integration review only; it is not a merge instruction or gameplay authorization.

### Production trust-anchor — BLOCKED

Before trust-anchor provisioning or real permits, HQ must designate and isolate the Windows runner, harden and verify NTFS ACLs for checkout, approval/authorization files, output, and claim storage, define crash recovery and authorization revocation, and provision the reviewed public key through an approved custody process. The current host ACL evidence does not meet that boundary.

