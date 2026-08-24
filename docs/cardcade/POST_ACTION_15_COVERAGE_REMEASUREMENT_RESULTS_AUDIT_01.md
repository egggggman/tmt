# Post-Action #15 Coverage Remeasurement Results Audit #1

Date: 2026-08-24  
Merged baseline: `d1b6c7ac77d0dff26389faf51dccad295145d608`  
Raw artifact: `C:\Projects\tmt-evidence-archive\post-action15\POST_ACTION_15_COVERAGE_AWARE_ENGINE_SMOKE_STAGE_0.1_RESULTS.json`

## Verdict

**ACCEPT — the Post-Action #15 Coverage Remeasurement is authentic, deterministic, internally reconstructive, and suitable to bank as coverage evidence.**

This verdict is evidence-only. It makes no balance claim and does not select a subsequent Action.

## Artifact authentication

The 341,177,656-byte raw file independently hashed to:

`c89affcc6ec5d21123757640d24902d7e1e17927fac57235131fdbf62001e4ab`

The separately preserved `.sha256` sidecar named the same digest and artifact. The JSON was not
interpreted until those values matched. The accepted validator then reproduced:

- manifest digest: `265122e8e41bde2f0ffd3afe32e5ace282db3637be207c4f6173ef4bcedbedb8`;
- aggregate digest: `17fdbd5e2ba67811b398c70b1960fba737ed0e774db4418b77bdaf6f90b664a8`;
- raw artifact body digest: `1fbac1481a36cc31709ac960ba2a76d8568dbaeaa41b28fdfb2c66ed9e175311`.

The serialized execution commit is the audited baseline. Rebuilding the complete manifest from the
repository reproduced every canonical frozen-input identity, hashing scheme, catalog/deck
membership, game specification, runner identity, and manifest field exactly.

## Matrix, duplicates, and classifications

Independent matrix generation reproduced 45 unordered deck pairings. Each pairing contains exactly
two seeds and both canonical/reversed orientations, yielding 180 collision-free distinct games and
360 executions.

For every game, the canonical JSON for `first` and `second` duplicate snapshots was independently
hashed. All 180 digest pairs matched each other and their serialized duplicate evidence. Each game
report was reconstructed from its authenticated first snapshot and frozen manifest.

The reconstructed mechanical classifications are:

| Classification | Games |
| --- | ---: |
| mechanically clean / coverage complete | 17 |
| mechanically clean / coverage limited | 163 |
| mechanically invalid | 0 |

Every game belongs to exactly one classification. Aggregate membership equals the union of the
individual reconstructed reports. No game contains a runner stop or invariant violation.
`balance_valid` independently reconstructs to `false` for all 180 games, including all 17
coverage-complete games; no completed game can silently become balance evidence under this contract.

The occurrence totals independently reconstructed from individual games are:

| Runtime class | Occurrences |
| --- | ---: |
| EXECUTED | 220 |
| REACHED / UNSUPPORTED | 562 |
| PRESENT / UNREACHED | 1,638 |

Opportunity contexts, typed-event witnesses, execution references, source lineages, Oracle-fragment
identities, and per-game classification sets were reauthenticated through the accepted reconciliation
path rather than accepted from aggregate labels.

## Action #15 authentication

The exact audited fragment is:

> Whenever another permanent leaves the battlefield, put a +1/+1 counter on Super Shredder.

For each authenticated execution reference, the audit required one exact chain:

`battlefield zone transition → PERMANENT_LEFT rules event → departure identity → Action #15 trigger and Stack identity → counter-resolution record → trigger completion`

The source ID, departed object ID, event ID, trigger ID, Stack object ID, Oracle fragment, and event
ordering had to agree throughout. The reconstruction produced:

| Evidence | Count |
| --- | ---: |
| legitimate executions | 55 |
| affected games | 16 |
| affected matchups | 8 |
| unique game-scoped trigger identities | 55 |
| unique game-scoped source incarnations | 18 |
| unique game-scoped departure identities | 55 |
| successful +1/+1 counter placements | 47 |
| legitimate resolutions with the original source absent | 8 |

The `47 + 8` split accounts for all 55 trigger resolutions. Every successful placement increments
the recorded counter total by exactly one. Each non-placement has an authoritative earlier
battlefield departure for the exact original source incarnation. None redirects its counter to a
destination/new incarnation of that card.

The 55 qualifying departures reconstruct as:

| Destination/reason | Count |
| --- | ---: |
| battlefield → graveyard | 53 |
| battlefield → hand | 2 |
| lethal damage | 46 |
| legend rule | 7 |
| activated return to owner's hand | 2 |

There are zero remaining REACHED / UNSUPPORTED occurrences for the exact Action #15 fragment and
zero other Super Shredder unsupported reaches.

## Re-signed adversarial reconstruction

Each attack changed an in-memory copy and recomputed the applicable outer aggregate/body digests.
The preserved file was never modified.

| Attack | Independent result |
| --- | --- |
| change one duplicate execution and recompute its digest | rejected: duplicate evidence no longer authenticates |
| fabricate an authenticated semantic evidence ID | rejected: conformance report is not reconstructive |
| substitute a game's mechanical classification and aggregate membership | rejected: mechanical label is not reconstructive |
| relink an Action #15 reference to a fabricated source | rejected: execution/conformance linkage is not reconstructive |
| change an applied Action #15 counter into a source-absent claim while rebuilding the report | rejected: no source departure authenticates the claim |
| claim a counter was applied after the original source incarnation departed | rejected: source-incarnation reconstruction forbids attachment |
| replace a frozen-input digest and re-sign manifest/aggregate/body | rejected against independently rebuilt frozen manifest |
| forge `balance_valid: true` | rejected: per-game balance boundary is derived, not trusted |

The two Action-specific counter-claim attacks were intentionally rebuilt into otherwise internally
consistent duplicate snapshots and reports. The accepted generic Smoke validator continued to
validate the generic report structure, while the independent Action #15 cross-event reconstruction
correctly rejected the false semantic claims. This demonstrates that the audit did not rely on outer
checksums or producer assertions for the 47/8 split.

## Scope and repository state

No game was rerun. No engine, runner, Action, Pilot, deck, or raw artifact was modified. No coverage
interpretation, Action #16 selection, balance analysis, calibration, or Prototype 0.3 work was
performed. The only repository addition is this uncommitted evidence report.
