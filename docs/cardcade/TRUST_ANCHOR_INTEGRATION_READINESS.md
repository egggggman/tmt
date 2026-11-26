# Cardcade Trust-Anchor and Integration Readiness

## Recommendation

**READY FOR HQ REVIEW OF THE INTEGRATION PLAN; BLOCKED for merge, production-key provisioning, permit issuance, or gameplay.** The implementation chain is linear and descends from current accepted main, and PR #422 independently accepted PR #421's reconciliation-authenticity correction. The chain is still entirely draft/unmerged. No production public key is provisioned, and the present launcher has no online permit-revocation service or cross-host claim store. HQ must authorize the integration branch and accept a single-host revocation/operations policy before provisioning or issuing any permit.

## Repository and source identities

- Repository: `egggggman/tmt`.
- Accepted `main` at review: `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`; `origin/main` matched this SHA.
- Isolated report worktree: `.cardcade-trust-anchor-integration-readiness`, based on accepted main; no implementation files were changed.
- Cumulative candidate at PR #421: `92a29a3263d8555029904e8d4c9f097f38c50605`.
- Main is an ancestor of both the prerequisite PR #404 source and the PR #421 candidate. The implementation checkpoints below form the existing stacked ancestry; no merge or history rewrite is needed to preserve it.

## Implementation lineage

| Checkpoint | Candidate SHA | Parent/base SHA | Scope |
| --- | --- | --- | --- |
| PR #404 prerequisite | `67b9bb3083c9f4b2fe02e7fed258c4739581225f` | `ad2034026d6d37904f66da7ef71874f2306e1571` | Main-action cast triggers through priority; this is the base of #407 and carries the earlier engine/pilot source chain. |
| PR #407 | `fcbe5fbf9419f246663a29467797ed79df57433f` | `67b9bb3083c9f4b2fe02e7fed258c4739581225f` | Stop terminal combat continuation after lethal damage. |
| PR #411 | `b0c5097d56574321200e210a139a58d0ba320648` | `fcbe5fbf9419f246663a29467797ed79df57433f` | Preserve game and presence evidence on diagnostic exceptions. |
| PR #413 | `6612ba7ee36d7eeeb2b090a3a7664662d6fcdeac` | `b0c5097d56574321200e210a139a58d0ba320648` | Reset and bind diagnostic capture state per invocation. |
| PR #415 | `188da5fabc231c91b222c642b6c9cf6fe4377c9f` | `6612ba7ee36d7eeeb2b090a3a7664662d6fcdeac` | One-shot diagnostic launcher and synthetic dry-run harness. |
| PR #417 | `6ded938a7680e767f9ac5e231774591ef461a27b` | `188da5fabc231c91b222c642b6c9cf6fe4377c9f` | Exact source/input pinning, durable local one-use claim, and blocked/nonzero incomplete results. |
| PR #419 | `98e7a3a3e7247bb685d82f7200c791365d592365` | `6ded938a7680e767f9ac5e231774591ef461a27b` | Ed25519 source/run authorization and structural Stage 002 reconciliation validation. |
| PR #421 | `92a29a3263d8555029904e8d4c9f097f38c50605` | `98e7a3a3e7247bb685d82f7200c791365d592365` | Compare the supplied reconciliation report with a captured trusted reference calculation. |

PR #404 and #407–#421 remain open draft PRs. PR #422 independently accepted #421, but it is a report-only draft. The other review and evidence PRs (#405, #408–#410, #412, #414, #416, #418, #420, #422) are provenance records, not runtime prerequisites to cherry-pick into the implementation candidate. PR #406's Diagnostic Game 001 record is historical evidence and must stay immutable.

The cumulative implementation diff adds engine changes in #407, capture changes in #411/#413, launcher changes in #415/#417/#419/#421, named synthetic tests and acceptance reports. It does not change the frozen April/Casey decks, card-data JSON/manifest, Baseline 005 manifest, or the preserved PR #406 artifacts.

## Safe integration sequence

1. Before integration, fetch main and confirm it is still `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`. If main advanced, stop and establish a new reviewed base rather than moving the source silently.
2. After separate HQ authorization, create a disposable integration branch from current main. Verify the prerequisite chain through PR #404 and the exact linear checkpoints above. Keep the historical implementation branches and audit PRs unchanged.
3. Validate at the existing checkpoints in order: #404, #407, #411, #413, #415, #417, #419, then #421. Use only individually named synthetic nodes. Retain the accepted 55-case selection from PR #422, and run it on the final integration SHA. At the earlier checkpoints, run the corresponding targeted regression group before advancing.
4. Confirm Python 3.12 compatibility and a clean locked installation on the intended Windows runner. PR #419 adds `cryptography>=44,<47` to `pyproject.toml`; `uv.lock` resolves `cryptography 46.0.7` and its platform artifacts. No runtime dependency change occurs in #421.
5. Provision the public trust anchor only after the code/integration branch and all lockfiles are final. This is a source change and therefore creates a new SHA. Rerun the 55 cases, trust-anchor tests, the report-forgery tests, Ruff checks, and diff checks against that new SHA.
6. Have HQ independently verify and approve that exact final SHA and the six frozen input hashes. Only then may a distinct source-approval document and a separately signed, unique run authorization for April versus Casey / canonical / seed 7231 be issued.
7. Do not merge or launch gameplay as part of this plan. HQ must issue separate authorization for any later operation.

## Frozen inputs and accepted validation

The six source-pinned input hashes are:

| Input | SHA-256 |
| --- | --- |
| `src/tmnt_design_studio/stage002.py` | `69ecb217234ac892509de0fbe6417601826909b3fceba77f4a865d4959db8f1b` |
| `decks/april_oneil/PROTOTYPE_0.1.txt` | `684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4` |
| `decks/casey_jones/PROTOTYPE_0.1.txt` | `0fc0adbb370ecfddad03692a4229a04b23268739914a8f2a004b8e042ff3cebb` |
| `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json` | `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402` |
| `cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json` | `6b5271af75150a361f77e7b89306c709959dfdf497c448dfdc978e5dc9a17950` |
| `docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json` | `532bad7e489eb25f3184b5a90487e1361f7a2b19b8c02cac3c4115a0fc3e14bc` |

PR #422 records the accepted 55-case synthetic selection: 20 launcher/authorization, 16 capture/terminal-combat, 13 authentication/reconciliation, and 6 recomputed-report forgery cases; all passed. It also reverified all nine PR #406 artifact hashes and preserved all three historical stop records. No complete game was used to establish this readiness recommendation.

## Minimal production trust-anchor design

### Custody and verification

- HQ designates one Security/key custodian and a separate approver for source and run authorization. Two-person approval is required before the signing service signs either document.
- Generate the Ed25519 key only in an HQ-approved HSM or non-exportable signing service after a separate authorization. Do not generate, install, or export a production key during this checkpoint. Never put the private key in Git, the launcher, a developer workstation, CI, or a run artifact.
- The repository registry contains only a stable key ID and the raw Ed25519 public key bytes. The custodian independently checks the SHA-256 public-key fingerprint through an out-of-band channel; a second HQ reviewer confirms the fingerprint before the provisioning commit is accepted.
- Verify the key against known Ed25519 test vectors and the launcher’s synthetic valid/invalid signature tests. Keep the key ID, public fingerprint, provisioning commit, custodian approvals, and signing audit records in HQ's access-controlled key register.
- The current `TRUSTED_HQ_AUTHORIZATION_KEYS` registry is empty. No current candidate can accept a real permit until a reviewed public-key provisioning change is made.

### Source approval and one-use run authorization

The signer uses the existing canonical UTF-8 JSON format: sorted keys, compact separators, and every document field except `signature` in the signed payload. The signature includes the `signing_key_id` and all approval fields.

1. Freeze the integrated source and six input hashes. Record the final exact Git SHA and verify the runner imports code from that checkout.
2. HQ independently reviews that source SHA and signs a `cardcade-reviewed-implementation-v1` source-approval document binding the SHA and complete input hash map.
3. After approval, a distinct HQ authorization step signs one `cardcade-diagnostic-run-authorization-v1` document. It names the source approval ID, unique authorization ID, exact same source/input identities, game ID `april-casey:canonical:7231`, pairing `april-casey`, orientation `canonical`, and seed `7231`.
4. Deliver both documents through a controlled access path to one designated runner. The runner must reject stale source or input hashes before dispatch. The durable claim is recorded before the single executor call and remains consumed after failure; never retry with the same authorization.
5. Any source, dependency, trust registry, or frozen-input change creates a new source identity and invalidates the prior exact-source approval. HQ must review and sign fresh documents for the new SHA.

### Rotation, revocation, and recovery

- **Rotation:** Pause issuance and execution. For the current schema, use a hard cutover rather than an indefinite dual-key overlap: provision the new public key through a reviewed source change, independently verify its fingerprint, test signatures, remove the old key in the cutover, and reauthorize the new exact SHA. Do not issue while key IDs or allowed SHAs are ambiguous.
- **Revocation:** Disable the HSM/signing account immediately, stop the runner, and mark unspent source approvals and run authorization IDs revoked in HQ's controlled issuance register. Remove the compromised public key in a reviewed source change and permit only the new approved SHA on the designated runner. The current launcher has no online revocation lookup or authorization expiry, and older code still contains its prior registry; this is why old source SHAs must be blocked operationally. If HQ requires multi-host or offline permit revocation, add and independently review a signed revocation/expiry mechanism before production issuance.
- **Recovery:** Prefer provider-managed HSM recovery with quorum. If the key is irrecoverable or compromised, treat it as revoked and provision a replacement through the rotation process; do not restore key bytes from source control or an ordinary workstation backup. Preserve signed-document and access logs for audit.

## Integration validation requirements

Run these on the final integrated source and again after any trust-registry change:

- The accepted 55 individually named synthetic cases from PR #422, with exact source/import-path recording.
- Ed25519 positive vector and rejection tests for unsigned, altered, malformed, duplicate-field, unknown-key, cross-key, wrong-source, wrong-input, and wrong-game documents.
- Source approval and run authorization remain distinct, bound to one exact SHA and input map, and signed by the configured trusted key.
- Cross-process duplicate-authorization race: exactly one claim succeeds across launcher instances and output directories; claim survives executor, reconciliation, and evidence-persistence failure; no retries occur.
- Reconciliation reference comparison: validly rehashed mutations of transaction counts, boundary counts, classifications, presence, authenticated execution references, identity, and manifest all block; mutation of report input copies does not mutate the authoritative snapshot; trusted-reference exceptions block and preserve available evidence.
- Evidence persistence: snapshot, supplied report, expected report, error, status, and hashes survive each supported failure path; incomplete or failed reconciliation exits nonzero.
- Terminal-combat/capture regressions and frozen-input/historical-artifact checks remain green. No game runner, smoke, batch, or calibration command belongs in this integration suite.

## Unresolved risks and recommendation

The local one-use claim store coordinates processes/worktrees sharing the same Git common directory; it is not a distributed multi-host authorization service. The launcher has no online permit revocation or expiry. For a first controlled run, HQ would need a single designated host, exclusive authorization-file access, controlled source checkout, a durable backed-up claim directory, and an out-of-band revocation procedure. If HQ cannot enforce those controls, the next engineering checkpoint should add a central claim/revocation service before any permit is issued.

**Status: BLOCKED for merge, production-key provisioning, real authorization, and gameplay until HQ approves the integration branch and the single-host trust/revocation operating model. READY for HQ review of this plan.** No keys were generated or installed, no permits issued, and no PRs merged.
