# Privacy Seal Defect Return to HQ

Status: **assessment only; no additional Pilot calls**. The original seal at `9fb8574` is preserved. Specification V3 is `c18a8fc`. Invalid synthetic attempt `32e692b`, genuine two-call proof `37054b7`, and current runner `efe0968` are preserved without modification. No new privacy states or recipes are proposed or constructed.

## Finding and bounded evidence

The privacy portion of the original seal contains eligibility metadata and unsupported completion assertions, not executable paired inputs. A hash authenticates those assertions; it does not establish that the pairs were constructed.

- At `9fb8574`, `scripts/seal_v3_phase1_packet.py:79-84` emits only `eligible`, a generic reason, `pair_required`, and a fixture-level `pair_id`. Line 112 assigns `paired_versions: 16` as a literal. The script reads candidate JSON and computes offline digests; it does not construct or perturb hidden game states, capture paired observations, or compare pair-specific outputs.
- At `9fb8574`, `scripts/seal_v3_phase2_deterministic.py:57-61` emits `eligible_seat_versions: 2`, literal `paired: true`, and a generic reason. Line 81 asserts `privacy_pairs: true`. No paired authoritative states, construction recipe, pair-state identifiers, or pair-specific equality check is produced.
- The original Phase 1 candidate explicitly says `eligibility pending paired reconstruction` for all eight fixtures. The Phase 2 candidate lists `complete Scry/Sneak seat counterparts and privacy pairs` among work missing before sealing.
- `scripts/build_v3_global_integration.py:48` assigns `transformations_and_privacy_sealed: true`; integration preserves counts and hashes but supplies no missing pairs. The canonical observations cannot establish an opponent-private perturbation on their own. Repeating them would not repair the missing provenance.

Evidence was read from the original Git tree, not inferred from the later failed scoring artifacts. The companion JSON preserves exact privacy metadata for every fixture-seat row, source-line references, and SHA-256 hashes of original Git blobs. The negative finding is bounded to the original seal, its source candidates, and construction/integration scripts; no external unpreserved inputs are assumed.

## Schedule partition

| Component | Calculation | Calls | Execution disposition |
| --- | --- | ---: | --- |
| Deterministic / transformations / duplicate replay | 12 fixtures x 2 seats x 3 variants x 2 replays x 2 Pilots | 288 | Reconstructable in principle; not executed as a suite |
| Privacy | 24 fixture-seat pairs x 2 paired observations x 2 Pilots | 96 | Not reconstructable from original seal; INCONCLUSIVE / unexecuted |
| Original planned total | 288 + 96 | 384 | No completed scoring result |

The 288 comprise 192 Phase 1 calls and 96 Phase 2A calls. Their variants are canonical, option permutation, and consistent runtime-ID renaming. The missing privacy calls comprise 64 Phase 1 calls and 32 Phase 2A calls. They are four calls per fixture-seat pair, not four pairs per fixture.

Offline checks recovered all 12 canonical observations/options and oracles from the pre-run candidate files and matched every sealed replay digest. Thus the earlier blanket claim that canonical data was missing was too broad. This is evidence of reconstructability, not proof that a full 288-call runner already works: opposite-seat/variant dispatch and full typed reconstruction still require execution-only implementation and validation after HQ authorization. This assessment neither executes that work nor promotes transformation metadata to completed execution evidence.

## All 24 missing privacy seat-version pairs

The identifiers below use existing fixture IDs plus seat, solely to enumerate missing schedule entries. They do not create new sealed pair identities. Every row lacks authoritative paired hidden-state inputs and a pre-run reconstruction recipe; each blocks four calls.

| Fixture | Seat | Hook | Category | Missing pair status | Blocked calls |
| --- | ---: | --- | --- | --- | ---: |
| V3-P1-001 | 0 | main | T | Missing authoritative pair | 4 |
| V3-P1-001 | 1 | main | T | Missing authoritative pair | 4 |
| V3-P1-002 | 0 | attack | T | Missing authoritative pair | 4 |
| V3-P1-002 | 1 | attack | T | Missing authoritative pair | 4 |
| V3-P1-003 | 0 | blocks | T | Missing authoritative pair | 4 |
| V3-P1-003 | 1 | blocks | T | Missing authoritative pair | 4 |
| V3-P1-004 | 0 | priority | T | Missing authoritative pair | 4 |
| V3-P1-004 | 1 | priority | T | Missing authoritative pair | 4 |
| V3-P1-005 | 0 | main | B | Missing authoritative pair | 4 |
| V3-P1-005 | 1 | main | B | Missing authoritative pair | 4 |
| V3-P1-006 | 0 | attack | B | Missing authoritative pair | 4 |
| V3-P1-006 | 1 | attack | B | Missing authoritative pair | 4 |
| V3-P1-007 | 0 | blocks | B | Missing authoritative pair | 4 |
| V3-P1-007 | 1 | blocks | B | Missing authoritative pair | 4 |
| V3-P1-008 | 0 | priority | B | Missing authoritative pair | 4 |
| V3-P1-008 | 1 | priority | B | Missing authoritative pair | 4 |
| V3-P2-001 | 0 | scry | R | Missing authoritative pair | 4 |
| V3-P2-001 | 1 | scry | R | Missing authoritative pair | 4 |
| V3-P2-002 | 0 | sneak | T | Missing authoritative pair | 4 |
| V3-P2-002 | 1 | sneak | T | Missing authoritative pair | 4 |
| V3-P2-003 | 0 | scry | B | Missing authoritative pair | 4 |
| V3-P2-003 | 1 | scry | B | Missing authoritative pair | 4 |
| V3-P2-004 | 0 | sneak | B | Missing authoritative pair | 4 |
| V3-P2-004 | 1 | sneak | B | Missing authoritative pair | 4 |

## Preserved genuine execution proof

`37054b7` records two actual `choose_attack` calls on `V3-P1-002`. AcceptancePilot returned `attacker_ids: [object-000135]`, a member of the sealed acceptable set. PassingPilot returned `attacker_ids: []`, outside that set. Both were legal options. The proof JSON, sidecar, and report remain unchanged; no calls were repeated for this assessment. The proof demonstrates control separation on one fixture only and is not a completed 288-call result or privacy test.

## HQ decision: exactly two prospective paths

**Path A — preferred under the stated resource limit:** authorize scoring only the original 288 non-privacy calls, retaining frozen fixtures and oracles. Report privacy as INCONCLUSIVE / unexecuted and state the reduced scope explicitly. Do not claim completion of 384 calls or a privacy pass. The current proof-only runner still requires the bounded execution implementation for those calls. This report is not authorization to run it.

**Path B:** authorize a new prospective Privacy Addendum seal. Construct and freeze the 24 real pairs before any more Pilot calls, then execute the extra 96 privacy calls separately. Preserve the original seal and distinguish the addendum's authority and results. No proposed hidden-state values or new recipe are included here.

The resource preference supports Path A; the available proof does not determine whether privacy testing is dispensable for calibration confidence. HQ retains that decision. Pilot Fitness remains unknown, filtering remains INCONCLUSIVE / unchanged, and calibration remains blocked. No methodology expansion or further research is requested.

## Verification

Read-only Git/JSON/hash inspection verified the three integration source hashes, all 12 canonical replay digests, 24 unique fixture-seat entries, the 288/96 partition, both existing proof outcomes, unchanged proof and runner files, and ancestry of all four preserved commits. No Pilot modules or fixture builders were imported or executed. Only this assessment and its hash sidecars are added.
