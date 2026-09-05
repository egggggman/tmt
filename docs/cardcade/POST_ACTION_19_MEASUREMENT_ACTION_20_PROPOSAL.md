# Post?Action #19 measurement and Action #20 proposal

Proposal only. Action #20 is not implemented, accepted, or authorized by this report.

## Baseline and command

Executed from `C:\Projects\tmt` on clean `main` at `34124fbd96ed56e683ffe855ecbbccba787c9ab6`, where Action #19 ? Stun Counters is banked.

```powershell
.venv\Scripts\python.exe -B scripts/run_acceptance_stage_002.py --execute --output docs/cardcade/POST_ACTION_19_ACCEPTANCE_STAGE_002_RESULTS.json
```

This is the existing smallest coverage-aware Acceptance Stage #002 matrix: 16 distinct games / 32 executions, with each game run twice for byte-equivalence. It is an eight-deck, four-matchup screening sample; it is not full-roster coverage, calibration, balance testing, a 900-game smoke, or Prototype 0.3 work.

| Pairing | Seeds |
| --- | --- |
| Donatello P0.2 / Krang P0.2 | 7201, 7202 |
| Michelangelo P0.1 / Bebop-Rocksteady P0.1 | 7211, 7212 |
| Splinter P0.1 / Shredder P0.1 | 7221, 7222 |
| April O?Neil P0.1 / Casey Jones P0.1 | 7231, 7232 |

The raw result is 12,021,752 bytes with SHA-256 `0c5fa3215288f0128cf17c5ffde2ffe6533b011644b031dac1256cca31e95b2b`. The manifest digest is `b3cebe9298fc320a34e47da4e00b6082e3b1fa567a9d362c9e987bf7fd41c4e7`; the aggregate digest is recorded in the raw result and ranking artifact.

## Result and ranking

The fresh result classifies **16 EXECUTED, 26 REACHED/UNSUPPORTED, and 144 PRESENT/UNREACHED occurrence records**. All 16 duplicate pairs are byte-equivalent; there are zero conformance stops and zero invariant violations. Five games contain no reached/unsupported occurrence records.

Ranks use occurrences, then games, then matchups, with semantic key as the deterministic tie-break. Solo-clearance is an observed singleton-key game derived from existing occurrence evidence; it is not a prediction.

| Rank | Frozen corpus member | Occurrences | Games | Matchups | Solo-clearance games |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | Fugitive Droid ? sacrifice to counter a qualifying spell | 7 | 4 | 1 | 0 |
| 2 | Ravenous Robots ? activated token haste | 3 | 3 | 1 | 0 |
| 3 | Ray Fillet, Man Ray ? remove a +1/+1 counter to draw | 3 | 3 | 1 | 0 |
| 4 | Casey Jones, Jury-Rig Justiciar ? ETB top-four artifact selection | 3 | 3 | 1 | 0 |
| 5 | Rock Soldiers ? ETB noncreature-artifact destruction | 2 | 2 | 1 | 0 |
| 6 | Donatello, Way with Machines ? artifact-entry +1/+1 counter | 2 | 2 | 1 | 0 |
| 7 | Casey Jones, Vigilante ? delayed random discard | 2 | 2 | 1 | 0 |
| 8 | Courier of Comestibles ? Food search/fallback token | 1 | 1 | 1 | 1 |
| 9 | Zoo Escapees ? Mutagen creation | 1 | 1 | 1 | 1 |
| 10 | Shredder, Unrelenting ? entry/attack deathtouch | 1 | 1 | 1 | 1 |
| 11 | Stockman, Mad Fly-entist ? ETB draw then discard | 1 | 1 | 1 | 0 |

Exact semantic keys, object IDs, game IDs, fragments, limitations, and singleton-game sets are preserved in the ranking JSON.

## Comparison with accepted post?Action #18 evidence

The comparison is valid for the same frozen Stage #002 matrix and the same occurrence classification model. It is coverage evidence, not balance evidence.

- Total reached/unsupported fell from 37 to 26 (11 fewer).
- Executed rose from 17 to 16 in the saved aggregate?s occurrence totals because Action #19 changes the classification and execution surface; these totals are occurrence records, not game wins and should not be read as a performance metric.
- Utrom Scientists? exact stun semantic fell from 9 reached/unsupported occurrences across 6 games and 2 matchups to 0 reached/unsupported; the fresh result records it as executed in the supported path.
- Fugitive Droid is now the highest remaining reached/unsupported semantic at 7 occurrences across 4 games and 1 matchup. Its count differs from the earlier 6 because the deterministic supported Action #19 path changes game progression; this is a measurement observation, not a causal or balance claim.
- Donatello, Way with Machines fell from 4 to 2; Stockman fell from 2 to 1. The other remaining semantics persist with changed or equal observed counts.

No historical totals were reused as new measurements. The accepted raw Action #18 SHA-256 is `2daa13956f2a8571d3d77f6c48d9f373ec516ad206eb47e387d78c42b72796ec`.

## Proposed Action #20 ? Counter Target Spell

### ACTION

Implement the actual Magic counterspell action, initially bounded to Fugitive Droid?s frozen activated ability: `{U}, Sacrifice this creature: Counter target spell that targets an artifact or creature you control.`

### RESOLVE

Recognize the exact frozen fragment through generic activated-ability, mana-payment, sacrifice, target, Stack, and Priority machinery. Authenticate the source incarnation, activation, sacrifice cost, target spell, and target spell?s target relationship. Put the ability on the existing Stack; after normal priority passes, counter the legal target spell and record authoritative activation, cost, target, resolution, zone, and event provenance. An illegal, absent, replaced, or relinked target fails closed. Preserve deterministic choices and ordinary counter-resolution timing.

### EXCLUSIONS

No universal counterspell framework, unrelated Fugitive Droid behavior, other counterspell cards, arbitrary spell-target predicates, deck changes, balance tuning, calibration, broad simulation, Prototype 0.3, or GUI/infrastructure work. Preserve unsupported near-neighbor semantics. Any interaction requiring an absent rules subsystem remains an explicit unsupported dependency.

### ACCEPTANCE

Exact frozen fragment recognition; generic source validation; deterministic legal target choice; normal activation/Stack/Priority lifecycle; authenticated `{U}` payment; authenticated sacrifice and source departure; target spell targeting an artifact or creature controlled by the activator; fail-closed stale, fabricated, wrong-zone, retargeted, and illegal targets; countered spell leaves the Stack authoritatively; source/target/activation/event history sufficient to reconstruct the action; deterministic replay; focused negative controls; relevant Stage/Smoke regressions; full pytest; Ruff check and format; diff check. Do not claim support for neighboring counterspell grammar or unsupported target predicates.

### BALANCE

Priority/value evidence only: Fugitive Droid leads the fresh sample at 7 occurrences, 4 games, and 1 matchup. This does not establish balance, win-rate impact, optimality, or guaranteed game clearance. `balance_valid` remains false.

### READY

Ready only for independent owner review of this bounded proposal and its sample limitations. Not ready to implement, bank, merge, or authorize.

## Validation and limitations

The existing `validate_stage_result_evidence` passed on the raw result, and the current manifest equals the saved manifest. The ranking was recomputed from raw occurrence records and cross-checked for ordering, IDs, fragments, limitations, matchup sets, and solo-clearance sets. A SHA-256 sidecar is saved for the raw result and for the ranking JSON.

The measurement covers only eight decks, four pairings, two seeds, and both orientations. Occurrence IDs are game-scoped semantic records, not every possible repeated opportunity. Five games have no reached/unsupported records. The run is deterministic and internally consistent, but it is not independent acceptance, balance evidence, or a complete rules-coverage census. No implementation branch or Action #20 code was created.
