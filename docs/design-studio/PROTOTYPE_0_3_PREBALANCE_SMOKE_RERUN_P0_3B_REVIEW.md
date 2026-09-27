# Prototype 0.3b Post-Revision Smoke Review

Run status: **complete; evidence only; no follow-up revision authorized by this artifact**

## Run identity and authority

- Repository SHA: `08ba5021d0551739b10adbef78fad88ffa293f74`
- Harness: [`tools/run_prototype_0_3_prebalance_smoke.py`](../../tools/run_prototype_0_3_prebalance_smoke.py)
- Evidence: [`PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3B_EVIDENCE.json.gz`](PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3B_EVIDENCE.json.gz)
- Harness-produced summary: [`PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3B_RESULTS.md`](PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3B_RESULTS.md)
- Runtime identity digest: `3087b0dc30b12a67b27c18d34f3f9c813130bccbec61cc540f395288d3e818ab`

The run used the authenticated Shredder P0.3, Raphael P0.3, Casey Jones P0.3, and Donatello P0.3b
inputs. Donatello P0.3b was authenticated with SHA-256
`244363af025331d6eb2895734aeeb565a67635949f26666d47155d01d78c4340`.

The exact frozen six-matchup schedule was used: 40 games per pairing, seeds 3000–3039, and 20
starts per deck, for 240 games total. No retries, replacement seeds, adaptive runs, or extra games
were used.

## Completion summary

| Measure | Result |
| --- | ---: |
| Scheduled | 240 |
| Attempted | 240 |
| Completed | 240 |
| Runtime errors | 0 |
| Malformed | 0 |
| Draws | 0 |
| Turn caps | 0 |

## Matchup results

Percentages are descriptive shares of completed games only; this sample is not a calibrated win-rate
estimate.

| Matchup | Result | Descriptive percentage | Completed | Starting-player split | Errors |
| --- | --- | ---: | ---: | --- | ---: |
| Shredder / Raphael | Raphael 22–18 Shredder | Raphael 55.0% | 40 | 20 / 20 | 0 |
| Shredder / Casey Jones | Shredder 24–16 Casey Jones | Shredder 60.0% | 40 | 20 / 20 | 0 |
| Shredder / Donatello | Shredder 33–7 Donatello | Shredder 82.5% | 40 | 20 / 20 | 0 |
| Raphael / Casey Jones | Raphael 25–15 Casey Jones | Raphael 62.5% | 40 | 20 / 20 | 0 |
| Raphael / Donatello | Raphael 36–4 Donatello | Raphael 90.0% | 40 | 20 / 20 | 0 |
| Casey Jones / Donatello | Casey Jones 33–7 Donatello | Casey Jones 82.5% | 40 | 20 / 20 | 0 |

## Deck aggregates

| Deck | W–L–D | Games | Descriptive win share |
| --- | --- | ---: | ---: |
| Shredder | 76–44–0 | 120 | 63.3% |
| Raphael | 85–35–0 | 120 | 70.8% |
| Casey Jones | 64–56–0 | 120 | 53.3% |
| Donatello | 15–105–0 | 120 | 12.5% |

## Utrom Scientists telemetry

The replacement card was visibly exercised, so the run tested the intended semantic surface rather
than merely authenticating an unused list change:

| Measure | P0.3b result |
| --- | ---: |
| Draw records | 110 |
| Games with a draw record | 74 / 120 |
| Casts | 55 |
| Games with a cast | 44 / 120 |
| Resolutions | 55 |
| ETB tap/stun effects | 55 |
| Targets affected | 55 |
| Average cast turn | 14.45 |
| Attacks involving Utrom Scientists | 35 |
| Creature-combat events involving it | 44 |
| Direct combat damage | 56 |

Every recorded Utrom resolution produced the supported ETB tap/stun event and a target. Representative
event sequences include:

- `shredder-vs-donatello-3001`: cast and ETB on turn 12, targeting Crustacean Commando; no Utrom
  attack or direct damage before the recorded game ended.
- `shredder-vs-donatello-3004`: cast and ETB on turn 19, targeting Shark Shredder, Killer Clone;
  six Utrom attack assignments and eight direct damage were recorded.
- `shredder-vs-donatello-3006`: cast and ETB on turn 9, targeting Donatello, Way with Machines;
  four Utrom attack assignments and eight direct damage were recorded.

The event log records target selection and stun-counter placement, but does not preserve a complete
counterfactual “attack would have occurred without stun” analysis. The observed numbers therefore
demonstrate execution, not causal combat attribution.

## Early-board timing

The following uses the same preserved event interpretation for both runs and is limited to the 120
Donatello games in each smoke:

| Timing measure | P0.3a | P0.3b |
| --- | ---: | ---: |
| Games with a first creature record | 118 | 118 |
| Average first creature turn | 4.19 | 3.69 |
| Games with a first artifact-entry record | 119 | 119 |
| Average first artifact-entry turn | 3.56 | 3.56 |
| Games with a Way cast | 57 | 57 |
| Average first Way cast turn | 12.91 | 11.98 |

P0.3b did produce an earlier average first creature record by 0.50 turn, but first artifact entry was
unchanged and Utrom's own average cast turn was 14.45. The added body was therefore real but not an
early-game event in most games. The change did not create a clear early stabilization breakpoint.

## Donatello engine telemetry

| Measure | P0.3a | P0.3b |
| --- | ---: | ---: |
| Technique draw records | 70 | 74 |
| Technique casts | 52 | 60 |
| Technique draw-resolution records | 60 | 67 |
| Technique Sneak executions | 8 | 7 |
| Does Machines casts | 96 | 121 |
| Does Machines resolutions | 96 | 121 |
| Does Machines setup triggers | 96 | 121 |
| Does Machines level-2 advancements | 77 | 92 |
| Artifacts recovered | 77 | 92 |
| Way with Machines casts | 75 | 71 |
| Way artifact-entry triggers | 26 | 40 |
| Way +1/+1 counters | 26 | 40 |
| Way attack assignments | 79 | 80 |
| Way direct combat damage | 149 | 190 |

The event log shows the broader engine firing more often in P0.3b: Does Machines casts, level-2
advancement, recovery, and Way trigger/counter totals all rose. This makes the result more informative:
the added Utrom bodies did not simply fail to appear. They entered, resolved, selected targets, and
contributed to combat, while the core engine remained active.

## Comparison with P0.3a

The P0.3a post-Flying baseline was:

- Shredder: 7–33 Donatello
- Raphael: 4–36 Donatello
- Casey Jones: 7–33 Donatello
- aggregate: 18–102, or 15.0%

P0.3b produced:

- Shredder: 7–33 Donatello
- Raphael: 4–36 Donatello
- Casey Jones: 7–33 Donatello
- aggregate: 15–105, or 12.5%

The three Donatello matchup records are identical to the P0.3a baseline. The aggregate moved down by
three wins, not up. Shredder/Raphael/Casey Jones remained stable in their direct pairings: Shredder
18–22 against Raphael and 24–16 against Casey, Raphael 25–15 against Casey. Their aggregate movement
is attributable to the changed Donatello pairings, not a new direct-pairing result.

Utrom Scientists clearly exercised the intended supported effect, but the effect did not produce a
meaningful directional improvement in Donatello's functional environment. Its average cast turn and
the unchanged matchup outcomes indicate that the two-copy conversion lever was too infrequent and/or
too late to solve the deck's pressure and stabilization problem.

## Required decision

`P0_3B_REVISION_FAILED`

This decision means the specific `-2 Sewer-veillance Cam / +2 Utrom Scientists` experiment did not
validate its directional hypothesis in the frozen sample. It does not claim Donatello is finally
balanced, and it does not authorize P0.3c, P0.4, another deck change, additional semantic work, or
Calibration V1.

No automatic follow-up is authorized. The preserved evidence should be reviewed before any future
Design Studio decision.
