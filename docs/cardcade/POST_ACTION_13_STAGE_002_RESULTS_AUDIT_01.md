# Post-Action #13 Acceptance Stage #002 Results Audit #1

## Verdict

**ACCEPT — the post-Action #13 Stage #002 artifact is internally consistent, deterministic,
independently reconstructive at the accepted evidence boundaries, and suitable to bank as
Cardcade conformance evidence.**

This verdict accepts the evidence. It is not balance evidence and does not by itself authorize
Action #14, deck changes, Pilot changes, smoke testing, calibration, or Prototype 0.3.

## Frozen audit target

- Merged execution baseline: `768585e13dd10bac1e749a161bbadb4da7de2c97`
- Raw-results commit: `f3e326cae114ce55350292636f440949027808ea`
- Raw artifact: `docs/cardcade/ACCEPTANCE_STAGE_002_RESULTS_03.json`
- Raw SHA-256: `ab9471d0320cb1a61b9048b6dc83788f3bfd5d12cb0d58800bc7a0dcd78da50a`
- Manifest digest: `9d4deae89ed04e9fc3204eb3abfcf4eebb45d1dafcfab785bebf3c701e060335`
- Aggregate digest: `2134b708eec35dca857896c74895ebd503ca976fd545fd348859620372adb07f`

The raw artifact was committed and pushed before this audit began. It was not modified, and no
Stage #002 game was rerun during the audit.

## Matrix and duplicate determinism

The artifact exactly contains the frozen 4-pairing × 2-seed × 2-orientation matrix: 16 distinct
games and 32 executions. Every report preserves both independently computed execution digests,
the two values agree, and every `duplicate_byte_equivalent` claim is true.

| Game | Duplicate SHA-256 | Result |
|---|---|---|
| Donatello/Krang canonical 7201 | `b85195c98cbae9316101372a6399f1a504ff4023d6ae9dbb8b3c5f2cddb0850a` | Donatello T21 |
| Donatello/Krang canonical 7202 | `744812b0807e34c895a2e20c69a286d7ac740d2e9feeff46ff93cc868507e3bc` | Krang T20 |
| Donatello/Krang reversed 7201 | `6d679e1f6085e6a31dfa9115a23749a003e5ca2f42d38b7e95fed96dfa0e53b3` | Krang T15 |
| Donatello/Krang reversed 7202 | `363d0d765e813db1f59c39f91c958cd4db5b9ea6ccc6e1cde83f9b7485719a6b` | Krang T19 |
| Michelangelo/Bebop & Rocksteady canonical 7211 | `15db6c721f58efc7e75a6e13b26ca4bd5a1dc374140204980f6e8afcf16ddb65` | Michelangelo T17 |
| Michelangelo/Bebop & Rocksteady canonical 7212 | `51d138ec207b404bd40d4fb3595a5251462216dd83470bd5f5e9458f8de396fc` | Michelangelo T19 |
| Michelangelo/Bebop & Rocksteady reversed 7211 | `fbe5ff22348df1ae8c0e20481fd9ea334317ec943d4c19e909b5222514bd2883` | Michelangelo T16 |
| Michelangelo/Bebop & Rocksteady reversed 7212 | `6b8ea761a7bba36f698138d22b5c3fa88b3f620f3fd0e4d284328fb7aba5d0db` | Michelangelo T14 |
| Splinter/Shredder canonical 7221 | `5360c05d240850727fb2900a478cf677c8f028311894d433331b0988c36d2b45` | Splinter T15 |
| Splinter/Shredder canonical 7222 | `13f633bed75ac3ff6729025e94bb7fe88258cb512b9522aa6e879a940c5263f2` | Splinter T15 |
| Splinter/Shredder reversed 7221 | `00f9e8e512ec3fb9e8c210f917fd61abeca18b73709c89f5f3f7f2dd86e96dfd` | Shredder T17 |
| Splinter/Shredder reversed 7222 | `17c10d7fc97ee259c5fbad198cd367a29e0dbf0229e03b6365938829de49fbf8` | Shredder T17 |
| April/Casey canonical 7231 | `395ce1430260b37f67da816e0a74b712670edcb12c23f5c9f9f4a9adc3101d4e` | Casey T14 |
| April/Casey canonical 7232 | `7d6532e5d759e355db7a1290733f1dcc7ca5ba1ab71d3a6ff2f0c62af11bb744` | Casey T18 |
| April/Casey reversed 7231 | `f4ecf265dd84fda69c1955fed4f7de4abb0ccdbf3f66da35f59bf9d4a9fbd29e` | Casey T19 |
| April/Casey reversed 7232 | `56b5bf2d54804b0f6545e7671c57c9ae1f25acc816c3dac529a67723a703f781` | Casey T15 |

Duplicate mismatches, runner stops, and invariant violations are all zero.

## Independent digest and aggregation reconstruction

The audit rebuilt the Stage manifest from the frozen deck files and authoritative card-data
snapshot. The rebuilt object exactly equals the serialized manifest. The accepted durable result
validator then independently recomputed:

- all duplicate digest/equivalence claims;
- all 16 per-game report digests;
- all occurrence and presence classifications;
- every execution-evidence reference;
- every opportunity-context key and witness link;
- every typed-event witness link;
- coverage unions and intersections;
- the aggregate digest.

No reconstruction or authentication check failed.

## Classification completeness and exclusivity

Every runtime semantic occurrence and every presence row has exactly one accepted class. Per-game
classification sets equal fresh projections from the classified evidence rows.

| Class | Unique semantic union | Semantic occurrences | Presence rows |
|---|---:|---:|---:|
| EXECUTED | 11 | 17 | 43 |
| REACHED / UNSUPPORTED | 15 | 53 | 53 |
| PRESENT / UNREACHED | 211 | 144 | 3,629 |

The differences from the accepted pre-Action result are not forced arithmetic. New Draws can alter
later trajectories, presence, and exposure; the artifact records those consequences rather than
preserving historical totals.

## Execution authentication

All 70 EXECUTED references authenticate against the serialized mature transaction/event evidence,
exact evidence kind and ID, source identity, Oracle fragment, semantic key, and represented runtime
object lineage.

| Evidence kind | References |
|---|---:|
| Trigger resolution | 41 |
| Token creation | 17 |
| Deal Damage | 2 |
| Discard/Draw | 3 |
| Hand-bottom/Draw | 2 |
| Strike damage step | 2 |
| Lifelink | 1 |
| Sneak | 1 |
| Trample | 1 |
| **Total** | **70** |

No malformed, missing, borrowed, or unauthenticated execution reference is present.

## Opportunity provenance

The artifact contains 46 distinct authoritative opportunity contexts and 92 opportunity witnesses:

- context-backed witness links: 60;
- typed-rules-event witness links: 32;
- duplicate context identities: 0;
- malformed or unreconstructible context keys: 0;
- orphan, missing, borrowed, or mismatched context links: 0;
- typed-event identity/kind/provenance failures: 0.

Every context key reconstructs from its immutable identity, timing, controller, source, subjects,
zones, facts, event/Stack provenance, and state fingerprint.

## Buzz Bots post-Action finding

Only after the mechanical evidence gate passed, the audit examined the exact Buzz Bots fragment:

`When this creature dies, draw a card.`

The pre-Action accepted artifact classified that semantic as REACHED / UNSUPPORTED 13 times across
eight games. The post-Action artifact contains 13 authenticated `trigger_resolved` references for
the same exact Oracle fragment across the same eight games:

| Game | Authenticated executions |
|---|---:|
| Donatello/Krang canonical 7201 | 1 |
| Donatello/Krang canonical 7202 | 2 |
| Donatello/Krang reversed 7201 | 1 |
| Donatello/Krang reversed 7202 | 2 |
| April/Casey canonical 7231 | 2 |
| April/Casey canonical 7232 | 1 |
| April/Casey reversed 7231 | 3 |
| April/Casey reversed 7232 | 1 |
| **Total** | **13** |

Each reference resolves to authoritative trigger evidence carrying its own event ID, source runtime
identity, semantic key, and exact Oracle fragment. Buzz Bots has zero remaining
REACHED / UNSUPPORTED occurrences for this fragment.

This is genuine runtime execution evidence, not a coverage-only reclassification. Two trajectories
changed relative to the accepted pre-Action artifact: Donatello/Krang canonical 7202 remains a
Krang win but moves from turn 16 to turn 20, and April/Casey reversed 7231 remains a Casey win but
moves from turn 21 to turn 19. The artifact preserves the resulting downstream exposure rather
than treating trajectory change as balance evidence.

## Residual reached-but-unsupported surface

The residual exact set contains the other 15 previously audited semantic keys. Buzz Bots is the
only prior reached-unsupported semantic removed from this set.

| Card / semantic | Games | Occurrences | Witnesses |
|---|---:|---:|---:|
| Rock Soldiers — ETB artifact destruction | 2 | 2 | 2 |
| Courier of Comestibles — conditional Food search/token | 1 | 1 | 1 |
| Zoo Escapees — departure Mutagen creation | 1 | 1 | 1 |
| Donatello, Way with Machines — artifact-entry counter | 2 | 3 | 4 |
| Ravenous Robots — token-haste activation | 3 | 3 | 6 |
| Shredder, Unrelenting — attack/ETB deathtouch | 1 | 1 | 1 |
| Ray Fillet — remove-counter Draw activation | 3 | 3 | 14 |
| Utrom Scientists — ETB tap/stun | 6 | 9 | 9 |
| Dream Beavers — ETB life/Scry compound | 4 | 8 | 8 |
| Casey Jones, Jury-Rig Justiciar — top-four artifact selection | 3 | 3 | 3 |
| Super Shredder — permanent-departure counter | 3 | 5 | 13 |
| Stockman — ETB Draw then Discard | 2 | 2 | 2 |
| Casey Jones, Vigilante — Draw/delayed random Discard | 2 | 2 | 2 |
| Fugitive Droid — sacrifice/counter response | 4 | 6 | 8 |
| Donatello, Turtle Techie — artifact-conditional Draw | 2 | 4 | 4 |

All remain explicit unsupported gameplay semantics. None is silently executed.

## Engine and runner finding

The newly executable dies/Draw path exercised the real combat → SBA → trigger → Stack → Priority →
resolution lifecycle. Across the complete matrix the artifact records:

- zero runner stops;
- zero invariant violations;
- zero duplicate mismatches;
- zero unauthenticated execution references;
- zero malformed opportunity provenance.

No new engine or runner defect is established by this run. This finding does not prove that no
unrepresented defect exists outside the tested matrix.

## Decision

- Post-Action #13 Stage #002 Results Audit #1: **ACCEPT**
- Raw Stage #002 artifact: suitable to bank and integrate as empirical conformance evidence
- Buzz Bots dies/Draw: moved from 13 authenticated reaches to 13 authenticated executions
- Gameplay/runner foundational blocker established: none
- Balance conclusion: none authorized
- Action #14 or broader validation: requires a separate evidence-interpretation decision

**ACCEPT — Post-Action #13 Acceptance Stage #002 completed deterministically across the frozen
matrix, and its execution, reach, presence, duplicate, and provenance evidence is independently
auditable.**
