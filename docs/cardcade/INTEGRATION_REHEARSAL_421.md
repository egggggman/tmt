# Cardcade Cumulative Integration Rehearsal

## Verdict

**READY for HQ review of the isolated cumulative candidate and integration sequence. BLOCKED for merging, production trust-anchor provisioning, real permits, or gameplay.** The 55-case synthetic selection passes on the exact cumulative candidate and the historical inputs remain byte-identical. Deployment controls for a single Windows host still need to be established and accepted by HQ.

## Source identity and ancestry

- Current `origin/main`: `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.
- Cumulative candidate: PR #421 HEAD `92a29a3263d8555029904e8d4c9f097f38c50605`.
- Disposable integration worktree: `.integration-cardcade-rehearsal`, detached at the candidate SHA and clean before validation.
- The candidate is a descendant of current main. The source history contains 105 commits after main.
- The implementation PRs remain open, draft, and unmerged. The companion audit/evidence PRs are report-only and are not code dependencies.

| Checkpoint | Head | Parent/base | Purpose |
| --- | --- | --- | --- |
| PR #404 prerequisite | `67b9bb3083c9f4b2fe02e7fed258c4739581225f` | `ad2034026d6d37904f66da7ef71874f2306e1571` | Cumulative engine/pilot source through main-action trigger priority. |
| PR #407 | `fcbe5fbf9419f246663a29467797ed79df57433f` | `67b9bb3083c9f4b2fe02e7fed258c4739581225f` | Terminal combat after lethal damage. |
| PR #411 | `b0c5097d56574321200e210a139a58d0ba320648` | `fcbe5fbf9419f246663a29467797ed79df57433f` | Exception-time game/presence evidence capture. |
| PR #413 | `6612ba7ee36d7eeeb2b090a3a7664662d6fcdeac` | `b0c5097d56574321200e210a139a58d0ba320648` | Fresh capture lifecycle and binding. |
| PR #415 | `188da5fabc231c91b222c642b6c9cf6fe4377c9f` | `6612ba7ee36d7eeeb2b090a3a7664662d6fcdeac` | One-shot launcher and synthetic dry-run harness. |
| PR #417 | `6ded938a7680e767f9ac5e231774591ef461a27b` | `188da5fabc231c91b222c642b6c9cf6fe4377c9f` | Exact source/input checks and persistent local one-use claims. |
| PR #419 | `98e7a3a3e7247bb685d82f7200c791365d592365` | `6ded938a7680e767f9ac5e231774591ef461a27b` | Ed25519 permit signatures and reconciliation contract checks. |
| PR #421 | `92a29a3263d8555029904e8d4c9f097f38c50605` | `98e7a3a3e7247bb685d82f7200c791365d592365` | Trusted full-report comparison against the pinned reconciler. |

PR #405, #408–#410, #412, #414, #416, #418, #420, and #422 record reviews or evidence; retain them as provenance, but exclude their audit-only branches from the runtime integration branch. PR #422 independently accepted the bounded #421 correction. PR #423 is the earlier readiness report and remains separate.

## Cumulative diff classification

Relative to `main`, the candidate changes **65 files: 14,382 insertions and 320 deletions**:

- Five runtime modules: `card_interpreter07.py`, `engine07.py`, `mana_ledger07.py`, `pilot07.py`, and `stage002.py`.
- One diagnostic launcher and one Stage 002 stop-ledger tool.
- Thirty test files covering the earlier engine/pilot mechanics, launcher, authorization, capture, terminal combat, and reconciliation evidence.
- Twenty-five documentation/report files.
- `pyproject.toml` and `uv.lock`, plus `.gitignore`.
- No frozen deck, card-data JSON/manifest, Baseline 005 manifest, or PR #406 artifact path appears in the main-to-candidate diff.

PR #419 introduces `cryptography>=44,<47`; `uv.lock` resolves `cryptography 46.0.7` and includes a Windows AMD64 wheel. The project requires Python `>=3.12`. PR #421 adds no runtime dependency. The validation environment was Python 3.12.10, pytest 8.4.2, and cryptography 46.0.7.

## Synthetic validation on the disposable candidate

The previously accepted selection was rerun with individually named nodes from the existing launcher and reconciliation reports:

| Coverage group | Result |
| --- | --- |
| Launcher and authorization safety, including cross-process one-use claims | 20 passed, 0 failed, 0 skipped |
| Capture lifecycle and terminal-combat regressions | 16 passed, 0 failed, 0 skipped |
| Ed25519, source/input binding, and reconciliation closure | 13 passed, 0 failed, 0 skipped |
| Recomputed-digest reconciliation forgeries | 6 passed, 0 failed, 0 skipped |
| **Total** | **55 passed, 0 failed, 0 skipped** |

The six forgery cases cover `transaction_counts`, `engine_boundary_counts`, `classification_sets`, `presence`, `authenticated_executed_references`, and the original PR #420 transaction-count reproduction. They recompute a valid digest and still require full-report mismatch to produce BLOCKED/nonzero while preserving both reports and not retrying. The prior 49 node identities are recorded in `DIAGNOSTIC_LAUNCHER_SAFETY_CORRECTION.md` and `DIAGNOSTIC_AUTHENTICATION_RECONCILIATION_CLOSURE.md`; the six new node identities are recorded in `PR419_RECONCILIATION_AUTHENTICITY_CORRECTION.md`.

The tests imported the launcher and Stage 002 modules from `.integration-cardcade-rehearsal`. No gameplay loop or complete game ran.

## Frozen input and historical evidence integrity

All six frozen inputs matched their approved SHA-256 identities:

| Input | SHA-256 |
| --- | --- |
| `src/tmnt_design_studio/stage002.py` | `69ecb217234ac892509de0fbe6417601826909b3fceba77f4a865d4959db8f1b` |
| `decks/april_oneil/PROTOTYPE_0.1.txt` | `684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4` |
| `decks/casey_jones/PROTOTYPE_0.1.txt` | `0fc0adbb370ecfddad03692a4229a04b23268739914a8f2a004b8e042ff3cebb` |
| `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json` | `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402` |
| `cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json` | `6b5271af75150a361f77e7b89306c709959dfdf497c448dfdc978e5dc9a17950` |
| `docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json` | `532bad7e489eb25f3184b5a90487e1361f7a2b19b8c02cac3c4115a0fc3e14bc` |

All nine Diagnostic Game 001 artifacts matched the preserved `artifact_sha256.json` manifest. Its three original stop records are still present: `stop-000001` (`illegal_mutation`, turn 16 / `combat_damage`), `presence_evidence_missing`, and the trample/combat event and object references. No historical artifact was edited.

## Single-host operations

| Area | Implemented protection | Deployment control still required |
| --- | --- | --- |
| Source and inputs | Exact signed source SHA; exact frozen-input hashes; repository module-path checks. | Provision only the final reviewed SHA and run from a controlled checkout. Changes to code, key registry, lockfile, or approved inputs require fresh source approval. |
| Authorization files | Separate Ed25519 source approval and run authorization; duplicate/malformed/tampered documents fail closed. Registry is currently empty. | Restrict both documents to a designated Windows service account and approved custody path; the launcher does not set or audit NTFS ACLs. |
| Single-use claim | Atomic `O_EXCL` creation before executor invocation, file flush, persistent claim, one call per instance, no retry. Separate processes sharing the Git common directory contend for the same claim. | Keep `.cardcade-diagnostic-claims` on local durable NTFS under locked-down ACLs. Do not use a network share or assume claims coordinate separate machines. Confirm backup/restore and post-crash claim retention operationally. |
| Process isolation | Cross-process duplicate claim is tested; launcher records one invocation and zero retries. | The claim is not an OS sandbox. Use one designated host/account, prevent schedulers or wrappers from relaunching, and restrict process access to the checkout and permit files. |
| Crash recovery | A consumed claim remains consumed after executor/evidence failure; evidence failures block and prohibit retry. | After a crash, preserve the output and claim, investigate, and issue a new unique authorization only after HQ review. Never delete/reuse a claim to retry. |
| Revocation | HQ can stop issuance and remove a key in a reviewed source change. | There is no online permit-revocation lookup, expiry, or distributed claim service. Disable old source SHAs and outstanding permits through a controlled operational register; if multi-host or offline revocation is required, implement it before production authorization. |

No production public key exists in the candidate. Synthetic test credentials only were used in prior validation. This rehearsal generated or installed no keys and issued no permits.

## Recommended integration sequence

1. After HQ authorization, confirm `main` still equals `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`. If it advances, stop and establish a new reviewed base.
2. Create a controlled integration branch from main and preserve the exact linear implementation ancestry through the PR #404 prerequisite, then #407, #411, #413, #415, #417, #419, and #421. Do not cherry-pick report-only audit PRs or rewrite original branches.
3. Run the 55 selected cases on the final cumulative SHA and the relevant named engine/pilot synthetic selections inherited from PRs #386–#404. Check clean dependency installation with the locked Windows/Python 3.12 environment. Keep test output and source/import identities with the candidate.
4. Only after the implementation source and frozen inputs are final may HQ separately authorize a reviewed public-key registry change. That change creates a new source SHA; rerun the full selected tests and source/signature checks, then have HQ approve the exact resulting SHA.
5. Create the source-approval document and, separately, the unique run authorization bound to `april-casey:canonical:7231`. Limit this to one designated host and enforce NTFS ACLs/claim retention before any future run authorization is considered.
6. Stop for HQ's separate merge and gameplay decisions. This rehearsal authorizes neither.

## Handoff

**READY for HQ review of the cumulative integration candidate and sequence. BLOCKED for merge, public-key provisioning, real permits, and gameplay until HQ authorizes the next gate and accepts the single-host ACL, crash-recovery, and revocation controls.**
