# Prototype 0.3a Post-Flying Pre-Balance Smoke Review

Decision: `PREBALANCE_REVIEW_REQUIRED`

This is the exact frozen 240-game diagnostic after the validated Technique,
Does Machines, level-2 recovery, Way with Machines, and generic Flying work. It
is directional smoke evidence, not a calibrated win-rate estimate.

## Run identity and evidence set

- Repository SHA: `3d4122ffd95bd5e07869999f728428cc85347656`
- Harness: `tools/run_prototype_0_3_prebalance_smoke.py`
- Harness SHA-256:
  `4f07be fdadc97da9c614123471f555b70f0e320f24eb7ba38a838c6ae2c2854f`
- Runtime identity digest: `9a114524a23a97e9d09a0b2c85781361db286d2254686dd3b63de292a1cde65c`
- Runtime files: `engine07.py`, `stage002.py`, `pilot07.py`, and
  `card_interpreter07.py`; no runtime files were changed for this run.
- Durable raw evidence:
  [`PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3A_POST_FLYING_EVIDENCE.json.gz`](PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3A_POST_FLYING_EVIDENCE.json.gz)

The raw event log is gzip-compressed byte-for-byte from the harness JSON output
so the complete durable event evidence remains available within the repository
file-size limit.

Authenticated deck SHA-256 values:

| Deck | SHA-256 |
| --- | --- |
| Shredder P0.3 | `818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2` |
| Raphael P0.3 | `220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51` |
| Casey Jones P0.3 | `f18d2dd6591520e495a0c723e1d15f5d3f4f6ce8a2693e4f93be0cd6660e838f` |
| Donatello P0.3a | `25812e2d7f0ac64ae2476c0d62298db35196d1719c9376b5369d5080faa6aad1` |

The schedule identity is the unchanged harness matrix: six specified pairings,
seeds `3000–3039` for each, parity-based 20/20 starting-player split, and 240
games. The harness file identity above is the schedule/runtime contract used by
preflight.

## Completion summary

- Scheduled: 240
- Attempted: 240
- Completed: 240
- Runtime errors: 0
- Malformed results: 0
- Draws: 0
- Turn caps: 0
- Retries or replacement seeds: 0

## Matchups

Percentages are descriptive shares of completed games only.

| Matchup | W/L/D | Descriptive result | Starting-player split | Errors |
| --- | --- | --- | --- | ---: |
| Shredder / Raphael | Shredder 18–22–0; Raphael 22–18–0 | 45.0% / 55.0% | 20 each | 0 |
| Shredder / Casey Jones | Shredder 24–16–0; Casey 16–24–0 | 60.0% / 40.0% | 20 each | 0 |
| Shredder / Donatello | Shredder 33–7–0; Donatello 7–33–0 | 82.5% / 17.5% | 20 each | 0 |
| Raphael / Casey Jones | Raphael 25–15–0; Casey 15–25–0 | 62.5% / 37.5% | 20 each | 0 |
| Raphael / Donatello | Raphael 36–4–0; Donatello 4–36–0 | 90.0% / 10.0% | 20 each | 0 |
| Casey Jones / Donatello | Casey 33–7–0; Donatello 7–33–0 | 82.5% / 17.5% | 20 each | 0 |

## Deck aggregates

| Deck | W/L/D | Descriptive share |
| --- | --- | ---: |
| Shredder | 75–45–0 | 62.5% |
| Raphael | 83–37–0 | 69.2% |
| Casey Jones | 64–56–0 | 53.3% |
| Donatello | 18–102–0 | 15.0% |

## Donatello semantic telemetry

The counts below are extracted from the preserved event logs. They describe
execution, not balance quality.

| Package | Telemetry |
| --- | --- |
| Technique | 70 draws; 52 `spell_cast` records; 60 draw-resolution records; 120 cards drawn; 66 Sneak records |
| Does Machines | 103 draws; 96 casts; 96 resolutions; 96 setup-trigger records; 77 level-2 advancements; 106 artifacts recovered |
| Does Machines recovered casts | 142 later casts whose card name matched a recovered artifact name; this is a name-match proxy, not exact per-copy linkage |
| Way with Machines | 121 draws; 75 casts/resolutions; 26 artifact-entry triggers; 26 counters placed; 79 attack assignments; 149 direct combat damage |

The raw event stream records the Way counter triggers and combat damage, but the
frozen harness does not emit the candidate blocker set or rejection reason for
each attack. Exact full-run `Flying-restricted attack` and
`Flying/Reach-block` counts are therefore not available without adding
instrumentation or rerunning. No instrumentation was added and no game was
replayed. The compact post-Flying diagnostic did directly observe 9 filtered
attacks in 30 games and 0 successful Flying/Reach blocks.

Representative preserved events include:

- `shredder-vs-donatello-3002`: Does Machines level-up and artifact recovery;
- `shredder-vs-donatello-3004`: two `artifact_entry_counter_resolved` events;
- `shredder-vs-donatello-3006`: Technique `draw_spell_resolved` with quantity 2;
- `shredder-vs-donatello-3007`: level-up/recovery followed by a Way trigger.

## Comparison with earlier smoke states

| State | Donatello result |
| --- | ---: |
| Before meaningful semantic coverage | 18–102, 15.0% |
| After Technique coverage | 15–105, 12.5% |
| Compact post-Flying diagnostic | 5–25, 16.7% |
| Exact post-Flying 240-game smoke | 18–102, 15.0% |

The compact directional improvement did not persist in the frozen 240-game
sample. Donatello's full-smoke result is exactly unchanged from the earlier
18–102 state. The three other decks remain functional and broadly stable:
Shredder is 75–45, Raphael 83–37, and Casey Jones 64–56, with no new runtime
failures.

The semantic telemetry shows that the intended setup/recovery/conversion path is
being exercised: Does Machines advances and recovers artifacts, Way receives
counters and attacks, and Flying is represented by the runtime. The unchanged
aggregate result means this evidence does not authorize human-play readiness;
it also does not isolate one remaining missing mechanic strongly enough to
authorize another semantic implementation from this smoke alone.

## Readiness decision

`PREBALANCE_REVIEW_REQUIRED`

The four-deck environment is runtime-clean, but Donatello remains at the
obviously noncompetitive 15.0% aggregate result, unchanged from the prior
full-smoke state. No single remaining unsupported mechanic is established here
as the sole foundational blocker, so this report does not select
`ONE_MORE_CORE_SEMANTIC_REQUIRED`.

No deck revision, P0.3b/P0.4 candidate, additional semantic implementation, or
Calibration V1 launch is authorized by this evidence. The next action requires
a separate Design Studio review of the unchanged full-smoke result.
