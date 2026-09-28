# Prototype 0.3c Pre-Balance Smoke Results

Run identity: exact frozen Prototype 0.3 pre-balance smoke using Donatello
Prototype 0.3c. This artifact is distinct from the P0.3a and P0.3b reruns.

## Execution identity

- Repository: `ecf05b0aaba9ab944c38e3da6186e4183dfa8c9a`
- Harness: `tools/run_prototype_0_3_prebalance_smoke.py`
- Harness SHA-256: `c4af02470d06c7d7df8ab4e80869aa239af21a9664ee0a5907cd4ddbeda17a41`
- Runtime identity digest: `d2b25efc90e45b327a04e9928f0bd849ae7169fd5e1d96c172ccb893e37ca03a`
- Durable raw evidence: [`PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3C_EVIDENCE.json.gz`](PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3C_EVIDENCE.json.gz)

Runtime source hashes:

| Source | SHA-256 |
| --- | --- |
| `engine07.py` | `d969302c633e6e0d5f3c47843befa8470fce330cfa3a982ac8a35a046a868ab8` |
| `stage002.py` | `3ab1b23e28e00bdb840e59e1df034a0899e638c9ba200b56af4e90865ff50d13` |
| `pilot07.py` | `b69e6141ac63295454aa9641dcfa09045c28c8611b66e033d181a9c6b8848a82` |
| `card_interpreter07.py` | `cc8cd648891c83feb352b675c5b2dce19fe699f30a18f6f868394e977fccc0a6` |

## Authenticated inputs

| Deck | Input | SHA-256 |
| --- | --- | --- |
| Shredder P0.3 | `decks/shredder/PROTOTYPE_0.3.txt` | `818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2` |
| Raphael P0.3 | `decks/raphael/PROTOTYPE_0.3.txt` | `220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51` |
| Casey Jones P0.3 | `decks/casey_jones/PROTOTYPE_0.3.txt` | `f18d2dd6591520e495a0c723e1d15f5d3f4f6ce8a2693e4f93be0cd6660e838f` |
| Donatello P0.3c | `decks/donatello/PROTOTYPE_0.3c.txt` | `b0d8a0dc42b267ac1a162096fe6e0336176f92db9a79a95f1c7dbd0d5c2d2cc6` |

P0.3c was the only changed deck input relative to the P0.3b smoke:

```text
-2 Sewer-veillance Cam
-2 Return to the Sewers
+3 Mouser Mark III
+1 Ooze Spill
```

## Schedule and completion

The frozen six-matchup matrix was used unchanged. Each matchup used seeds
3000--3039, 40 games, and a 20/20 starting-player split, for 240 games total.

- Scheduled: 240
- Attempted: 240
- Completed: 240
- Runtime errors: 0
- Malformed: 0
- Draws: 0
- Turn caps: 0

## Matchups

Percentages are descriptive sample percentages, not calibrated win rates.

| Matchup | Result | Completed | Descriptive percentage | Starting-player split | Errors |
| --- | --- | ---: | --- | --- | ---: |
| Shredder / Raphael | Raphael 22--18 Shredder | 40 | Raphael 55.0%, Shredder 45.0% | 20 / 20 | 0 |
| Shredder / Casey Jones | Shredder 24--16 Casey Jones | 40 | Shredder 60.0%, Casey 40.0% | 20 / 20 | 0 |
| Shredder / Donatello | Shredder 30--10 Donatello | 40 | Shredder 75.0%, Donatello 25.0% | 20 / 20 | 0 |
| Raphael / Casey Jones | Raphael 25--15 Casey Jones | 40 | Raphael 62.5%, Casey 37.5% | 20 / 20 | 0 |
| Raphael / Donatello | Raphael 35--5 Donatello | 40 | Raphael 87.5%, Donatello 12.5% | 20 / 20 | 0 |
| Casey Jones / Donatello | Casey Jones 29--11 Donatello | 40 | Casey 72.5%, Donatello 27.5% | 20 / 20 | 0 |

## Deck aggregates

| Deck | Games | W-L-D | Descriptive win percentage |
| --- | ---: | --- | ---: |
| Shredder | 120 | 72-48-0 | 60.0% |
| Raphael | 120 | 82-38-0 | 68.3% |
| Casey Jones | 120 | 60-60-0 | 50.0% |
| Donatello | 120 | 26-94-0 | 21.7% |

## P0.3c telemetry

Telemetry below is derived from the preserved event logs. The harness did not
change instrumentation for this run.

### Mouser Mark III

- Draw records: 117
- Games with a Mouser cast: 66
- Casts: 83
- Resolutions: 83
- Average cast turn: 11.82
- Cast by turn 2: 0
- Cast by turn 3: 4
- Cast by turn 4: 8
- Cast by turn 5: 9
- Block records: 67
- Attack/combat assignments: 78
- Combat damage assignments: 156 damage
- Direct combat damage: 152
- Deaths to lethal damage: 54

The event schema does not emit a dedicated “attack disallowed by another
artifact” record, so that count cannot be measured from this run. A missing
record is not evidence that the restriction was never encountered. The focused
Mouser regressions separately establish that the engine supplies the correct
legal attacker set.

Mouser was therefore exercised in real games and produced substantial blocking
and combat activity, but it was still usually cast well after the intended
turn-two-to-five stabilization window.

### Ooze Spill

- Draw records: 150
- Casts: 0
- Resolutions: 0
- Targets/countered spells: none recorded
- Mutagen/token output: none recorded
- Average cast turn: not applicable

The fourth copy increased availability in the deck, but AcceptancePilot did not
cast Ooze Spill in this smoke. The event logs therefore do not demonstrate an
interaction benefit from that slot.

### Early-board timing

Across Donatello's 120 games, event-log observations were:

- First creature: 118 games, average turn 3.88
- First artifact: 118 games, average turn 4.12
- First supported interaction/setup cast: 114 games, average turn 6.75
- First Mouser cast: average turn 11.82 among 83 casts

The first-creature and first-artifact measures are broad event-log measures;
the harness does not preserve a separate “meaningful blocker” classification.
Mouser-specific block activity is reported above.

### Existing engine activity

- Donatello's Technique casts: 61
- Technique draw resolutions: 67
- Cards drawn through Technique: 134
- Sneak executions in Donatello games: 12
- Does Machines setup resolutions: 56
- Does Machines level-2 advancements: 56
- Artifacts recovered: 62
- Way with Machines casts/resolutions: 66 / 66
- Way artifact-entry triggers: 42
- Way counters placed: 42
- Way combat assignments: 35
- Way direct combat damage: 205

## Comparison and interpretation

Donatello improved from P0.3a's `18--102` to `26--94`, and from P0.3b's
`15--105` to `26--94`. The aggregate descriptive result moved from 15.0% to
21.7%. The improvement was directional and the environment remained runtime
clean, but Donatello remained strongly behind Raphael and Casey Jones.

The structural package clearly changed the battlefield: Mouser resolved 83
times, blocked 67 times, and dealt observable combat damage. The early-board
hypothesis was only partially realized, however, because only 9 Mouser casts
occurred by turn 5 and Ooze Spill was never cast. The extra interaction copy
therefore did not produce observable tempo in this run.

The result is best classified as `P0_3C_PARTIAL_IMPROVEMENT`: the early artifact
body produced real board and combat activity and the aggregate moved materially,
but the package did not yet validate the complete early-stabilization plus
interaction-conversion hypothesis. This is not a balance conclusion.

## Decision and boundary

Decision: **`P0_3C_PARTIAL_IMPROVEMENT`**

No automatic follow-up is authorized by this evidence. No deck, semantic,
Pilot, opponent, schedule, or calibration changes were made, and no P0.3d or
P0.4 candidate was created.
