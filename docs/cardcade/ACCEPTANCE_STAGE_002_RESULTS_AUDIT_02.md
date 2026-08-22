# Acceptance Stage #002 Results Audit #2

## Verdict

**ACCEPT — the fresh Acceptance Stage #002 result is internally consistent, independently reconstructive at the accepted evidence boundaries, deterministic across all duplicate executions, and suitable to bank as Cardcade conformance evidence.**

This is a conformance/evidence acceptance. It is not balance evidence, does not claim complete Magic
coverage, and does not authorize Action #13, calibration, smoke testing, deck changes, Pilot tuning,
or Prototype 0.3.

## Frozen audit target

- Raw-results commit: `b8f4d757f4feaa821eb8c4f4c19b5697feb4f053`
- Raw artifact: `docs/cardcade/ACCEPTANCE_STAGE_002_RESULTS_02.json`
- Raw SHA-256: `aff642c43e7daed2f693d59128c821e18e8ca7b474b24997ee4ae037b43330e3`
- Merged runner baseline: `c656c02d30fbf0287c29d9e73b03f2e2e15c3010`
- Historical rejected raw result remains unchanged at SHA-256
  `0e1631f24fba87eca54566f9072a9e1651e00f9c9ca73e75e1bfaa7522fc66c7`.

The fresh raw artifact was committed and pushed before this report was written. It was not modified
during the audit, and no Stage game was rerun during Results Audit #2.

## Matrix and deterministic duplicate evidence

The artifact contains exactly the frozen 4-pairing × 2-seed × 2-orientation matrix:

- 16 distinct games;
- 32 executions;
- one canonical and one reversed orientation for each pairing/seed;
- two separately computed canonical-snapshot SHA-256 digests per game;
- exact first/second digest equality and an explicit true byte-equivalence claim for all 16 games.

| Game | Duplicate SHA-256 | Result |
|---|---|---|
| Donatello/Krang canonical 7201 | `f8104c22c01b497ef568112a8d83aa05911f9e7bb291a232460e3f65ee6a65db` | Donatello T21 |
| Donatello/Krang canonical 7202 | `5e5fa23e1fa39e007be8d32b1f37de2edbfa6269486396783cb05a22cb42c7a0` | Krang T16 |
| Donatello/Krang reversed 7201 | `6c6800097f8af852e430088d1e8d813f01a2816ae376236665d05a57368ddb01` | Krang T15 |
| Donatello/Krang reversed 7202 | `f972fe1742c4b723896e669783b56d018f977a0d9638aa4e2adf4bfb216ff4cd` | Krang T19 |
| Michelangelo/Bebop & Rocksteady canonical 7211 | `48eb28ad098f18ce8a6367c920118e91c4480c76d4eea26d27309f65543f82a0` | Michelangelo T17 |
| Michelangelo/Bebop & Rocksteady canonical 7212 | `331888a51b706b3417fada8df6fcae7fff80c4b418ccd2bb16e9bbf074f79c3f` | Michelangelo T19 |
| Michelangelo/Bebop & Rocksteady reversed 7211 | `30a63d49f254f1376860733ca5195dcfbcbdcf848e5f733ce8839e7ff16e0bf9` | Michelangelo T16 |
| Michelangelo/Bebop & Rocksteady reversed 7212 | `0a00cec405801853cb54c99e7717de8d1690d477ab690b9e2b3d15ea2b50bda5` | Michelangelo T14 |
| Splinter/Shredder canonical 7221 | `0036e020f0c212dd2fa4157a50269378241df513441740a9e6af9a176f56bedf` | Splinter T15 |
| Splinter/Shredder canonical 7222 | `a300e2637a88d1caa614382a8f52cbe600e8a30decd8b25e7b9f09911577ebdf` | Splinter T15 |
| Splinter/Shredder reversed 7221 | `408057b69674fa04b97724fb0fd349010c892cfdaa9b1009fe8b1c63e77e9e9a` | Shredder T17 |
| Splinter/Shredder reversed 7222 | `665d817dba873edbdee28e59aabdf58dae8f8f0bd220a2c8eda2f8feb065534f` | Shredder T17 |
| April/Casey canonical 7231 | `40df393342cc968c663ae7c571a6f3f00345e3a593f4ac03c431873af1225faf` | Casey T14 |
| April/Casey canonical 7232 | `45cf224cafc16158faecc53f37ec5e0d6b39fc9ee55087e3074cfdebf2bc7451` | Casey T18 |
| April/Casey reversed 7231 | `e033194aa55132fb7d5beda856a2b01a1c06806e39e154701d3279662d91beba` | Casey T21 |
| April/Casey reversed 7232 | `f9cb8b087fd4488a1f47a86a688c2a15d7f49c4c8ad015309fd60314bf07cb08` | Casey T15 |

No duplicate member, compatibility digest, or equivalence claim disagreed.

## Digest and aggregation reconstruction

The audit independently rebuilt the manifest from the frozen decks and authoritative card data,
then recomputed every digest and coverage aggregation:

| Evidence | Recomputed result |
|---|---|
| Manifest | exact structural match |
| Manifest digest | `58788be5bc4322ba7ffc5aa36b1df61fd3f487d6b2ea539b3129a998d4cdf771` |
| All 16 per-game report digests | exact |
| Aggregate digest | `9a9a302fb548206a892550c4d5c6c1c3a44b2c0a90eea0d954f1cefccc531288` |
| Game/pairing/orientation/deck unions and intersections | exact |
| Serialized runner stops | 0 |
| Serialized invariant violations | 0 |

## Classification totals and completeness

Every semantic occurrence and every presence/object-fragment row has exactly one allowed class. Each
per-game classification set exactly equals a fresh projection from its classified presence rows.

| Class | Unique semantic union | Semantic occurrences | Presence rows |
|---|---:|---:|---:|
| EXECUTED | 10 | 15 | 29 |
| REACHED / UNSUPPORTED | 16 | 66 | 66 |
| PRESENT / UNREACHED | 209 | 142 | 3,628 |

All-class intersections across all 16 games are empty. A semantic key may occur in different
classes for different runtime objects within one game; object and occurrence identity keeps those
rows exclusive and auditable.

## Execution authentication

All 55 execution references authenticate against the serialized mature transaction/event evidence,
exact evidence kind/ID, source identity, Oracle fragment, semantic key, and runtime presence lineage.
No unauthenticated execution claim is present.

| Evidence kind | References |
|---|---:|
| Trigger resolution | 26 |
| Token creation | 15 |
| Deal Damage | 3 |
| Discard/Draw | 3 |
| Hand-bottom/Draw | 3 |
| Strike damage step | 2 |
| Lifelink | 1 |
| Sneak | 1 |
| Trample | 1 |
| **Total** | **55** |

## Opportunity-context and typed-event provenance

The fresh artifact serializes 56 distinct authoritative opportunity contexts. The audit independently
recomputed every context key from its context ID/kind, timing, active player, controller, source,
ordered subjects/zones, typed facts, event/Stack provenance, and state fingerprint.

- Context key reconstruction failures: 0
- Duplicate context IDs: 0
- Orphan contexts: 0
- Context-backed witness links: 68
- Context-witness cardinality/provenance failures: 0
- Typed rules-event witness links: 32
- Typed-event identity/kind failures: 0

Context reuse accounts for 68 witness links over 56 authoritative contexts. Every link agrees on
source, controller, turn, phase, step, subjects, and zones. The 32 rules-event witnesses each resolve
to exactly one matching typed event.

## The 16 reached-but-unsupported semantics

The exact semantic membership and frequency remain the independently audited set from Results Audit
#1. Frequency is games / classified occurrences / witnesses:

| Card / semantic family | Frequency | Reach authority |
|---|---:|---|
| Rock Soldiers — ETB artifact destruction | 2 / 2 / 2 | typed self-ETB event |
| Courier of Comestibles — conditional Food search/token | 1 / 1 / 1 | typed self-ETB event |
| Zoo Escapees — departure Mutagen creation | 1 / 1 / 1 | authenticated departure context |
| Donatello, Way with Machines — artifact-entry counter | 2 / 3 / 3 | authenticated artifact context |
| Buzz Bots — death Draw | 8 / 13 / 13 | authenticated departure contexts |
| Ravenous Robots — token haste activation | 3 / 3 / 6 | authenticated activation contexts |
| Shredder, Unrelenting — attack/ETB deathtouch | 1 / 1 / 1 | typed attack event |
| Ray Fillet — remove-counter Draw activation | 3 / 3 / 12 | authenticated activation contexts |
| Utrom Scientists — ETB tap/stun | 6 / 9 / 9 | typed self-ETB events |
| Dream Beavers — ETB life/Scry compound | 4 / 8 / 8 | typed self-ETB events |
| Casey Jones, Jury-Rig Justiciar — top-four artifact selection | 3 / 3 / 3 | typed self-ETB events |
| Super Shredder — permanent-departure counter | 3 / 5 / 13 | authenticated departure contexts |
| Stockman — ETB Draw then Discard | 2 / 2 / 2 | typed self-ETB events |
| Casey Jones, Vigilante — Draw/delayed random Discard | 2 / 2 / 2 | typed self-ETB events |
| Fugitive Droid — sacrifice/counter response | 4 / 6 / 8 | authenticated activation/response contexts |
| Donatello, Turtle Techie — artifact-conditional Draw | 2 / 4 / 4 | typed self-ETB events |

Only Casey Jones, Jury-Rig Justiciar overlaps Acceptance #001; the other 15 exact semantic keys are
Stage #002 novelty. All remain explicit unsupported gameplay semantics. None is silently executed,
and their presence does not itself constitute an engine failure.

## Comparison with the rejected historical run

After removing only the new `opportunity_contexts`, paired duplicate-digest, byte-equivalence, and
changed digest fields, every per-game gameplay, trajectory, classification, witness, execution,
transaction, boundary, and presence record is exactly equal to the historical run.

Thus the new run did not alter gameplay to reproduce old totals. It independently reproduced the
same deterministic results while adding the evidence that Audit #1 found missing.

## Acceptance decision

No runner defect, silent approximation, unauthenticated execution, unclassified reach, invariant
violation, illegal mutation, or nondeterminism is present in the fresh artifact.

- Acceptance Stage #002 Results Audit #2: **ACCEPT**
- Stage #002 conformance evidence: suitable to bank and integrate
- Gameplay defect established: none
- Foundational blocker established: none
- Balance conclusion: none authorized
- Action #13 and downstream development: not authorized by this audit alone

**ACCEPT — Acceptance Stage #002 completed deterministically across the frozen 16-game matrix, and its EXECUTED / REACHED-UNSUPPORTED / PRESENT-UNREACHED evidence is independently auditable.**
