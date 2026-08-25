# Post-Action #16 Coverage Remeasurement Results Audit #1

Date: 2026-08-25
Merged baseline: `e600e680f3b974490dcb5cb1beab24d0c998a630`
Raw artifact: `C:\Projects\tmt-evidence-archive\post-action16\POST_ACTION_16_COVERAGE_AWARE_ENGINE_SMOKE_STAGE_0.1_RESULTS.json`

## Verdict

**ACCEPT — the Post-Action #16 Coverage Remeasurement is authentic, deterministic,
reconstructive, and suitable to preserve as coverage evidence.**

This verdict is evidence-only. It makes no balance claim, interprets no residual coverage, and does
not select Action #17.

## Artifact authentication

The preserved 486,221,198-byte raw file independently hashed to:

`e02b34b885d2e139f4eee21cc0ee760ac998d33163fd5c6a872e3b0fedd12965`

The independent `.sha256` sidecar names the same digest and artifact. JSON contents were not
interpreted until both values agreed. Reconstructive validation then reproduced:

- manifest digest: `4d0a1b3d1ef7495003c4caadf115d4176c0f248062c7e2aac20aa2f1d871fcbf`;
- aggregate digest: `fc9b04764cbabd2bf50bb2eb5dd77c37e51bcc107d9faf4ebbf687fae734536d`;
- raw artifact body digest: `10f6e1555a09587f755f4dcc8b147be331b3b41a742802cbec26d61ada288a5d`.

The serialized execution commit is exactly the audited baseline. Rebuilding the manifest from that
repository state reproduced the complete manifest byte-for-byte: all 18 frozen-input identities and
hashing methods, catalog and deck membership, game specifications, runner identity, and manifest
digest.

## Matrix, duplicate determinism, and classifications

Independent matrix generation reconstructed 45 unordered deck pairings. Each pairing has exactly
two seeds and both canonical and reversed orientations, yielding 180 collision-free distinct game
IDs and 360 executions.

For every distinct game, both serialized duplicate snapshots were independently canonicalized and
hashed. All 180 first/second digest pairs matched their snapshots, matched one another, and retained
`duplicate_byte_equivalent: true`. No duplicate is counted as another distinct game.

The accepted runner validator independently reconciled every game report from its first immutable
snapshot and the frozen manifest. This reauthenticated semantic presence, runtime occurrences,
opportunity contexts and witnesses, typed-event evidence, executed references, source lineages,
Oracle-fragment identities, transaction evidence, Priority/Stack boundaries, and report digests.

The reconstructed mechanical classifications are:

| Classification | Games |
| --- | ---: |
| mechanically clean / coverage complete | 18 |
| mechanically clean / coverage limited | 162 |
| mechanically invalid | 0 |

Every game belongs to exactly one reconstructed aggregate membership. There are zero runner stops
and zero invariant violations. The per-game balance boundary reconstructs to `balance_valid: false`
for all 180 games, including every coverage-complete game; aggregate future-candidate records retain
the same structural exclusion.

The occurrence totals independently reconstructed from the 180 reports are:

| Runtime class | Occurrences |
| --- | ---: |
| EXECUTED | 220 |
| REACHED / UNSUPPORTED | 548 |
| PRESENT / UNREACHED | 1,638 |

## Action #16 authentication

The exact audited fragment is:

> When Donatello enters, if you control an artifact, draw a card.

Each Action #16 execution was required to reconstruct one exact chain:

`original rules_event ledger → immutable rules_event_evidence ETB anchor → trigger pending →
Stack identity → Priority/pass permission → resolution condition record → Draw zone transition →
trigger_resolved → authenticated execution reference`

For every chain, event ID/cursor, `creature_entered` kind, source battlefield incarnation, frozen
trigger controller, turn/step, Stack object, trigger ID, Oracle fragment, and source lineage agree.
The immutable ETB anchor was independently compared field-for-field with the original `rules_event`
record rather than trusted because the downstream trigger and Stack records agreed.

Historical artifact qualification was reconstructed from the anchor's complete battlefield
authority and evaluated battlefield-characteristic records. A qualifier counted only when the exact
game/object incarnation was historically controlled by the frozen trigger controller and its
evaluated type line contained `Artifact`. The authentic chains contain 13 unique game/object
qualifier identities across eight ETB anchors. They include Mutagen artifacts and Artifact Creatures;
printed card types were not substituted for the recorded battlefield characteristics.

The reconstruction produced:

| Evidence | Count |
| --- | ---: |
| legitimate executions | 8 |
| affected distinct games | 7 |
| affected matchups | 6 |
| unique game-scoped trigger identities | 8 |
| unique game-scoped source incarnations | 8 |
| authenticated historical ETB anchors | 8 |
| qualifying artifact game/object identities | 13 |
| resolution-condition successes | 8 |
| resolution-condition failures | 0 |
| successful Draws | 8 |
| failed Draws | 0 |

Each successful Draw removes exactly one library incarnation and creates its linked hand
incarnation through an authoritative `zone_changed` record before the Action resolution and parent
`trigger_resolved` boundary. The hand and library before/after sets, zone-transition identities, and
controller all agree.

The seven affected games are:

- `april_oneil--donatello:canonical:8006`;
- `bebop_rocksteady--donatello:canonical:8021`;
- `casey_jones--donatello:canonical:8036`;
- `donatello--krang:canonical:8050`;
- `donatello--leonardo:canonical:8051`;
- `donatello--leonardo:reversed:8052`;
- `donatello--raphael:reversed:8055` (two executions).

There are zero remaining REACHED / UNSUPPORTED classifications for the exact Action #16 fragment
and zero other Donatello, Turtle Techie unsupported reaches.

## Re-signed adversarial reconstruction

Every attack operated on a fresh in-memory copy. Duplicate-member digests and all applicable
manifest, aggregate, and raw-body digests were recomputed. The preserved raw file and sidecar were
never modified.

| Attack | Independent fail-closed result |
| --- | --- |
| change one duplicate snapshot and re-sign its member digest | duplicate identity no longer authenticates |
| promote a semantic occurrence classification and re-sign | conformance report no longer reconstructs |
| relink an Action #16 resolution to a fabricated source | event/trigger/Stack/source chain is no longer unique and authentic |
| remove `Artifact` from a historical qualifier in both duplicate snapshots | immutable evidence disagrees with the original rules-event ledger |
| claim the resolution condition was false while retaining the Draw | condition and transaction evidence disagree |
| claim Draw failure while retaining the successful zone transaction | successful-condition Draw was silently omitted |
| replace a frozen-input digest and re-sign the manifest | rebuilt repository manifest disagrees |
| set a game's `balance_valid` field to true and re-sign | derived per-game balance boundary rejects it |

These attacks establish that producer agreement, outer checksums, and mutually edited duplicate
snapshots are insufficient to authenticate Action #16 history. In particular, historical artifact
qualification remains anchored to the independent original rules-event record.

## Scope

No game was rerun. No raw artifact, sidecar, engine, runner, Action, Pilot, or deck was modified. No
residual coverage interpretation, Action #17 selection, balance analysis, calibration, or Prototype
0.3 work was performed. The only intended repository addition is this uncommitted evidence report.
