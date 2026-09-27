# Prototype 0.3a Semantic-Coverage Smoke Rerun Review

This is the exact frozen 240-game rerun after the Donatello semantic-coverage
implementation and diagnostic. It is descriptive evidence, not a calibrated win-rate
estimate.

## Run identity

- Repository SHA: `55aa0d4994903fff5c4d4abe05d94af970b221a1`
- Harness: `tools/run_prototype_0_3_prebalance_smoke.py`
- Harness SHA-256: `4f07befdadc97da9c614123471f555b70f0e320f24eb7ba38a838c6ae2c2854f`
- Runtime identity digest: `d4074ad9f69c2c0db0e2d608b09ad94ca817232717e09be1fc733f225e39c533`
- Schedule identity SHA-256: `608230400bd3466e9a43cfc160bbd93d93be074c7a31c07ab1eae430331e2928`
- Evidence: `PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3A_SEMANTIC_COVERAGE_EVIDENCE.json`

Runtime component hashes:

| Component | SHA-256 |
| --- | --- |
| `engine07.py` | `9e03ac0758ac81e82e557822890977664e730a376ffcb13301b73ae362fda207` |
| `stage002.py` | `3ab1b23e28e00bdb840e59e1df034a0899e638c9ba200b56af4e90865ff50d13` |
| `pilot07.py` | `478074ec72fb4c5389ecf1cfa9639a8773b54fdafef5fc3b70e48fbbdeba1363` |
| `card_interpreter07.py` | `580ac99a9d0aa4c07a42a6b661dfe96be07302516a446d2fd34417e8e756ca44` |

## Authenticated inputs and completion

| Deck | Input SHA-256 |
| --- | --- |
| Shredder P0.3 | `818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2` |
| Raphael P0.3 | `220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51` |
| Casey Jones P0.3 | `f18d2dd6591520e495a0c723e1d15f5d3f4f6ce8a2693e4f93be0cd6660e838f` |
| Donatello P0.3a | `25812e2d7f0ac64ae2476c0d62298db35196d1719c9376b5369d5080faa6aad1` |

- Scheduled: 240
- Attempted: 240
- Completed: 240
- Runtime errors: 0
- Malformed: 0
- Draws: 0
- Turn caps: 0
- Replacement seeds, retries, and extra games: none

## Matchup results

Each row used 40 completed games, seeds 3000–3039, and a 20/20 starting-player split.
Percentages are descriptive shares only.

| Matchup | W/L/D | Descriptive percentage | Starting-player split | Errors |
| --- | --- | --- | --- | ---: |
| Shredder / Raphael | Shredder 22–18 Raphael | 55.0% / 45.0% | 20 Shredder / 20 Raphael | 0 |
| Shredder / Casey Jones | Shredder 22–18 Casey Jones | 55.0% / 45.0% | 20 Shredder / 20 Casey Jones | 0 |
| Shredder / Donatello | Shredder 36–4 Donatello | 90.0% / 10.0% | 20 Shredder / 20 Donatello | 0 |
| Raphael / Casey Jones | Raphael 25–15 Casey Jones | 62.5% / 37.5% | 20 Raphael / 20 Casey Jones | 0 |
| Raphael / Donatello | Raphael 36–4 Donatello | 90.0% / 10.0% | 20 Raphael / 20 Donatello | 0 |
| Casey Jones / Donatello | Casey Jones 33–7 Donatello | 82.5% / 17.5% | 20 Casey Jones / 20 Donatello | 0 |

## Deck aggregates

| Deck | W/L/D | Descriptive percentage |
| --- | --- | ---: |
| Shredder | 80–40–0 | 66.7% |
| Raphael | 79–41–0 | 65.8% |
| Casey Jones | 66–54–0 | 55.0% |
| Donatello | 15–105–0 | 12.5% |

## Donatello semantic telemetry

Telemetry was derived from the persisted per-game event logs; no harness, runtime, Pilot,
deck, or schedule changes were made.

| Measure | Result |
| --- | ---: |
| Technique draw occurrences | 68 |
| Games with a Technique draw | 57 |
| Technique casts | 59 main-phase casts + 9 Sneak casts = 68 |
| Technique resolutions | 68 |
| Cards drawn through Technique | 136 |
| Successful Technique draw-resolution events | 68 |
| Technique Sneak executions | 9 |

The existing smoke evidence records executed Sneak announcements but does not emit
declined/available-choice events. Therefore exact Technique Sneak opportunity count is
`NOT_CAPTURED_BY_EXISTING_HARNESS`, not zero. The evidence records 50 total Sneak
announcements across all cards, including 9 for Technique. No additional instrumentation
was added because this task forbids harness/runtime changes during execution.

Representative evidence is game `shredder-vs-donatello-3006`: on turn 5, Technique
produced `cost_paid`, `spell_cast`, `draw_spell_resolved` with `quantity: 2` and
`draw_succeeded: true`, then `spell_resolved`. Across 57 games with a Technique
resolution, 57 had later meaningful events; 3,267 such subsequent events were observed.
This demonstrates real state progression after resolution, without attributing every later
action solely to Technique.

## Comparison with prior smoke states

Both the original P0.3 smoke and the pre-coverage P0.3a rerun recorded Donatello at:

- 5–35 versus Shredder;
- 5–35 versus Raphael;
- 8–32 versus Casey Jones;
- 18–102 aggregate.

The semantic-coverage rerun changed the aggregate to 15–105, or 12.5%, with clean
execution. Technique is now genuinely drawn, cast, Sneak-cast in some games, resolved,
and drawing cards, but the deck did not move out of the obviously noncompetitive range.
The change is therefore a representation success, not a balance recovery.

Shredder, Raphael, and Casey Jones remained directionally stable against one another:
22–18, 22–18, and 25–15 respectively, with no runtime failures.

## Remaining semantic blockers

The result still appears materially constrained by unimplemented central Donatello
semantics, especially:

- Does Machines Class levels and setup/recovery effects;
- Donatello, Way with Machines artifact-entry counters;
- Donatello, Gadget Master combat-damage artifact-copy trigger;
- Donatello, Mutant Mechanic counter/animation activation and transfer trigger;
- Sewer-veillance Cam tap/untap and sacrifice-draw choices;
- Bespoke Bō support semantics.

No additional semantics or card changes are authorized by this rerun.

## Readiness decision

`MORE_DONATELLO_COVERAGE_REQUIRED`

The environment is runtime-clean and Technique coverage is demonstrably active, but
Donatello remains at 15–105 and the remaining central setup/payoff mechanics are still
underrepresented. Human-play authorization would be premature on this evidence.

Next gate: identify and authorize one narrowly scoped highest-leverage semantic slice,
starting with Does Machines’ central setup/recovery behavior, before another balance
revision or human-play gate. Do not create P0.3b/P0.4 or launch Calibration V1 from this
run.
