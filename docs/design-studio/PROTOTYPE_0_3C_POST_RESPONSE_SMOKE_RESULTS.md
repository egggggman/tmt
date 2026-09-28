# Prototype 0.3c Post-Response Smoke Results

Run identity: exact frozen Prototype 0.3 pre-balance smoke after the bounded
Ooze Spill hand-response support. This is a new evidence set, distinct from
the pre-response P0.3c smoke.

## Execution identity

- Repository: `b39d365378b5abf385a1fb6f7798b5219f2a6a9b`
- Harness: `tools/run_prototype_0_3_prebalance_smoke.py`
- Harness SHA-256: `c4af02470d06c7d7df8ab4e80869aa239af21a9664ee0a5907cd4ddbeda17a41`
- Runtime identity: `1e7a4c414b97045c32d89941c025eccade962fa6ce17939a2de28a376ea69160`
- Schedule identity (canonical schedule SHA-256): `2d87dde6343045f644a4abfb44c28029af22e80722f8472f830254a2216bb7bb`
- Durable raw evidence: [`PROTOTYPE_0_3C_POST_RESPONSE_SMOKE_EVIDENCE.json.gz`](PROTOTYPE_0_3C_POST_RESPONSE_SMOKE_EVIDENCE.json.gz)

Runtime source hashes were preserved in the raw evidence. No runtime,
decklist, Pilot, schedule, seed, or orientation change was made for this run.

## Authenticated inputs

| Deck | Input | SHA-256 |
| --- | --- | --- |
| Shredder P0.3 | `decks/shredder/PROTOTYPE_0.3.txt` | `818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2` |
| Raphael P0.3 | `decks/raphael/PROTOTYPE_0.3.txt` | `220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51` |
| Casey Jones P0.3 | `decks/casey_jones/PROTOTYPE_0.3.txt` | `f18d2dd6591520e495a0c723e1d15f5d3f4f6ce8a2693e4f93be0cd6660e838f` |
| Donatello P0.3c | `decks/donatello/PROTOTYPE_0.3c.txt` | `b0d8a0dc42b267ac1a162096fe6e0336176f92db9a79a95f1c7dbd0d5c2d2cc6` |

## Schedule and completion

The six frozen matchups used seeds `3000`--`3039`, 40 games per matchup,
and a 20/20 starting-player split: 240 games total.

- Scheduled: 240
- Attempted: 240
- Completed: 240
- Runtime errors: 0
- Malformed: 0
- Draws: 0
- Turn caps: 0
- Retries or replacement seeds: none

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
| Donatello | 120 | 26-94-0 | 21.7% |
| Casey Jones | 120 | 60-60-0 | 50.0% |

## Ooze Spill response telemetry

| Measure | Result |
| --- | ---: |
| Draw records | 152 |
| Games with Ooze in hand | 88 |
| Generic priority/response windows recorded | 2,278 |
| Dedicated legal-Ooze-exposed records | 0 |
| Ooze responses selected | 3 |
| Ooze casts | 3 |
| Ooze resolutions | 3 |
| Average response/cast turn | 9.67 |
| Creature spells countered | 3 |
| Noncreature spells countered | 0 |
| Mutagen tokens created | 3 |
| Original spells confirmed not to resolve | 3 |

The three selected responses occurred in Shredder / Donatello games at turns
8, 8, and 13. Every target was `Shredder, Unrelenting`, a creature spell.
No Ooze response was selected against Raphael or Casey Jones in this frozen
sample. The raw `response_window_opened` count is a generic priority-window
count, not an opponent-spell-only count. The current event schema also did not
emit a dedicated `legal Ooze exposed` record; the three selected responses
demonstrate three legal response opportunities, but unused legal opportunities
cannot be counted precisely from this run.

Representative event sequence, preserved in the raw evidence, is:

`response_selected` -> `response_target_selected` -> `spell_countered` ->
`ooze_spill_resolved` with `mutagen_token_id`; the targeted Shredder spell has
no resolving battlefield-entry event.

## Mouser Mark III telemetry

- Draw records: 118
- Casts/resolutions: 84 / 84
- Games with a cast: 67
- Average cast turn: 11.90
- Cast by turn 3 / 4 / 5: 4 / 8 / 9
- Blocks assigned: 30
- Attack assignments: 107
- Direct combat damage: 152
- Deaths to the graveyard: 55

This confirms the P0.3c body package remained active; the current run's Mouser
counts differ slightly from the earlier preserved pre-response summary because
they are measured from this run's raw event log.

## Existing Donatello engine telemetry

- Technique casts: 62; resolutions: 68; Sneak executions: 6
- Does Machines casts: 110; level-2 advancement events: 78
- Way with Machines casts/resolutions: 65 / 65
- Way artifact-entry triggers/counters: 43 / 43
- Way direct combat damage: 82 event records (the raw event schema records
  player-damage events rather than a separate aggregate field)

The new response path therefore executed alongside the existing Technique,
Does Machines, recovery, Way, counter, and Flying semantics without runtime
failures.

## Comparison and decisions

| State | Donatello aggregate |
| --- | --- |
| P0.3a | 18--102 (15.0%) |
| P0.3b | 15--105 (12.5%) |
| P0.3c before Ooze response support | 26--94 (21.7%) |
| P0.3c after Ooze response support | 26--94 (21.7%) |

The response support is **semantically validated**: supported hand responses
were selected, paid for, resolved, countered legal creature spells, created
Mutagen tokens, and prevented the original spells from resolving. It had no
descriptive win/loss movement in this 240-game sample, and only three response
uses occurred, all against Shredder. The correct conclusion is not that Ooze
is a weak card; the run demonstrates a real but sparse response path.

Response-support decision: **`P0_3C_RESPONSE_SUPPORT_VALIDATED`**

Human-play readiness: **`HUMAN_PLAY_WITH_KNOWN_IMBALANCE`**

The environment was clean and Donatello's identity now includes deployable
artifact bodies, engine setup/recovery, Way conversion, Flying, and executable
Ooze responses. Donatello remains materially under parity, so this is not a
balance approval. Human play is the more informative next gate than another
automatic deck revision or semantic expansion. No P0.3d was created, no deck
was edited, and no calibration run was launched.
