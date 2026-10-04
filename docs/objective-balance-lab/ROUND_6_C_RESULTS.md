# Round 6 C — threat suppression

Handoff: **RETURN_TO_DESIGN_STUDIO**. Gameplay mechanism: **EXECUTED_AND_TELEMETRY_VERIFIED**. No redesign, combined candidate validation, or promotion occurred.

On the frozen schedule, aggregate win rate moved 38.56% → 41.22%; mean matchup balance error moved 17.22% → 18.11%. Raphael changed +2.00 pp, Shredder +4.00 pp, and April +6.00 pp. Strict >60/40 matchups moved 6 → 7; strict >70/30 moved 4 → 5. April is a new >60/40 matchup and Leonardo a new >70/30 matchup. The suppression mechanism executed, but the tested list did not produce a smoother matchup distribution. Design Studio owns the interpretation and any subsequent design decision.

Frozen `OBL-R6-KRANG-C`: **−1 Negate / +1 Retro-Mutation**, 60 cards, SHA-256 `c458ff8bd6b5d4f30ce1cd03313492b4d69bfba253f795e22b78bd9292728ac5`. The nine opponents are the exact authenticated Baseline 003 decks in the raw evidence's opponent manifest. Raphael is the primary diagnostic, Shredder secondary, April the anti-polarization sentinel.

Runtime `ccfa75ed8e817bc3af0a04f75ef048aaee54e5175c06abfc21feaad6515bb0ec` at source commit `bd361c5fa5d0671734dacce6fe90a0f6b6a102be`. The [new control](BASELINE_003_AURA_RUNTIME_CONTROL.md) completed before candidate execution; the older control is not used for candidate deltas. All **900 candidate games and 900 full-record deterministic replays** completed, with **zero runtime errors** and **50 starts each way per opponent**. Schedule SHA-256: `b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27`.

[Machine analysis](ROUND_6_C_ANALYSIS.json) · [raw candidate events and games](ROUND_6_C_EVIDENCE.json.gz) · [raw control](BASELINE_003_AURA_RUNTIME_CONTROL.json.gz) · [semantic readiness](ROUND_6_C_SEMANTIC_READINESS.json) · [frozen candidate](candidates/KRANG_OBL_R6_C.txt).

| Opponent | Control | R6-C | Delta |
|---|---:|---:|---:|
| Raphael — primary | 19.00% | 21.00% | +2.00 pp |
| Shredder — secondary | 22.00% | 26.00% | +4.00 pp |
| April O'Neil — sentinel | 56.00% | 62.00% | +6.00 pp |
| Splinter | 26.00% | 26.00% | +0.00 pp |
| Casey Jones | 24.00% | 25.00% | +1.00 pp |
| Michelangelo | 36.00% | 39.00% | +3.00 pp |
| Donatello | 44.00% | 42.00% | -2.00 pp |
| Bebop & Rocksteady | 54.00% | 58.00% | +4.00 pp |
| Leonardo | 66.00% | 72.00% | +6.00 pp |

| Distribution metric | Control | R6-C |
|---|---:|---:|
| wins | 347 | 371 |
| losses | 553 | 529 |
| draws | 0 | 0 |
| win_rate | 38.56% | 41.22% |
| mean_matchup_balance_error | 17.22% | 18.11% |
| median_matchup_deviation | 16.00% | 22.00% |
| over_60_40 | 6 | 7 |
| over_70_30 | 4 | 5 |
| first_player_result_rate | 40.89% | 42.44% |
| mean_ending_turn | 21.2722 | 21.75 |
| median_ending_turn | 20.0 | 21.0 |

Strict >60/40 and >70/30 thresholds use the established metric definitions. Ending-turn histograms, per-cell starts, paired outcome shifts, first-land-miss/creature/blocker/interaction timing, battlefield presence, and all signature casts are retained in the machine analysis.

| Timing / board proxy | Control | R6-C |
|---|---:|---:|
| First land_miss: mean turn (observed games) | None (0) | None (0) |
| First creature: mean turn (observed games) | 9.7322 (814) | 9.9189 (814) |
| First blocker: mean turn (observed games) | 3.8317 (897) | 3.8562 (897) |
| First interaction: mean turn (observed games) | 6.2307 (724) | 6.4625 (733) |
| Turn 3 creatures: mean (observed games) | 1.1595 (608) | 1.1595 (608) |
| Turn 5 creatures: mean (observed games) | 1.8532 (756) | 1.8386 (756) |
| Turn 7 creatures: mean (observed games) | 2.5702 (805) | 2.5405 (803) |

Retro-Mutation is excluded from the historical interaction proxy; its execution is counted separately below. Printed creature counts are unchanged by the candidate substitution.

| Retro-Mutation execution | Control | R6-C |
|---|---:|---:|
| casts | 504 | 753 |
| resolutions | 504 | 753 |
| failed_illegal_target | 0 | 0 |
| countered | 0 | 0 |
| games_with_cast | 437 | 553 |
| games_with_resolution | 437 | 553 |
| attachments_verified | 504 | 753 |
| recalculation_events | 508 | 759 |
| restoration_events | 4 | 6 |
| mean_first_cast_turn_if_observed | 11.373 | 10.9222 |

Every recorded resolution links back to its cast and locked target ID and an attachment reporting ability removal and an attack restriction. Targets, object IDs, turns, phase/step, effective P/T and source IDs are in the raw game records. Final P/T may exceed 0/1 after counters or later modifiers; the base-setting layer is separately tested.

| Diagnostic | Control casts / resolves | R6-C casts / resolves | Control / R6-C games with resolution |
|---|---:|---:|---:|
| Raphael | 48 / 48 | 76 / 76 | 41 / 58 |
| Shredder | 62 / 62 | 91 / 91 | 50 / 64 |
| April O'Neil | 58 / 58 | 101 / 101 | 49 / 67 |

| Resolved target | Control | R6-C |
|---|---:|---:|
| April O'Neil, Hacktivist | 1 | 5 |
| April O'Neil, Kunoichi Trainee | 8 | 13 |
| April, Reporter of the Weird | 9 | 16 |
| Bebop, Warthog Warrior | 6 | 9 |
| Buzz Bots | 27 | 39 |
| Casey Jones, Jury-Rig Justiciar | 13 | 18 |
| Casey Jones, Vigilante | 9 | 10 |
| Courier of Comestibles | 7 | 12 |
| Crustacean Commando | 10 | 20 |
| Donatello, Gadget Master | 1 | 2 |
| Donatello, Mutant Mechanic | 14 | 15 |
| Donatello, Turtle Techie | 3 | 3 |
| Donatello, Way with Machines | 5 | 5 |
| Dream Beavers | 8 | 15 |
| Foot Mystic | 11 | 18 |
| Frog Butler | 8 | 9 |
| Fugitive Droid | 31 | 48 |
| Insectoid Exterminator | 9 | 14 |
| Leonardo, Big Brother | 10 | 17 |
| Leonardo, Cutting Edge | 2 | 3 |
| Leonardo, Leader in Blue | 15 | 25 |
| Leonardo, Sewer Samurai | 4 | 5 |
| Lita, Little Orphan Amphibian | 5 | 7 |
| Michelangelo, Game Master | 7 | 14 |
| Michelangelo, Improviser | 9 | 13 |
| Michelangelo, Mutant BFF | 3 | 5 |
| Michelangelo, Weirdness to 11 | 6 | 7 |
| Mouser Mark III | 6 | 11 |
| Mutant Town Musicians | 7 | 12 |
| Null Group Biological Assets | 11 | 17 |
| Oroku Saki, Shredder Rising | 9 | 14 |
| Paramecia Coloniex | 11 | 15 |
| Prehistoric Pet | 18 | 23 |
| Purple Dragon Punks | 25 | 30 |
| Raphael, Most Attitude | 2 | 5 |
| Raphael, Ninja Destroyer | 7 | 12 |
| Raphael, Tough Turtle | 17 | 22 |
| Ravenous Robots | 4 | 10 |
| Ray Fillet, Man Ray | 5 | 6 |
| Rock Soldiers | 5 | 7 |
| Rocksteady, Crash Courser | 2 | 6 |
| Shark Shredder, Killer Clone | 14 | 19 |
| Shredder, Unrelenting | 7 | 12 |
| Splinter, Hamato Yoshi | 14 | 20 |
| Squirrelanoids | 14 | 17 |
| Super Shredder | 15 | 20 |
| Tunnel Rats | 23 | 32 |
| Utrom Scientists | 10 | 20 |
| Wingnut, Bat on the Belfry | 4 | 7 |
| Zoo Escapees | 33 | 49 |

The implementation recognizes a bounded Oracle-text Aura template with variable creature type and base P/T. It does not dispatch on experiment IDs, opponent identities or target names. Tests cover legal targeting, attachment, layer 7b versus counters/modifiers, layer-6 keyword order, static/trigger/activated ability suppression, retained already-stacked abilities, Flash priority, retargeting, source removal, incarnation changes, simultaneous departures, state-based actions and deterministic execution.

Validation before freezing the final runtime: 1,604 passed and 2 skipped in one invocation, including 17 Aura tests and nine combat-enumeration equivalence tests. Final evidence authentication and tamper checks are additionally covered by `tests/test_objective_balance_lab_round6c.py`. Ruff check/format and diff checks passed.

Limits:

- Bounded creature-Aura Oracle template; other Aura payloads remain unsupported.
- Ward/protection targeting dependencies fail closed; no such baseline creature was found.
- Pilot uses a generic main-phase suppression policy; Flash is executable in priority windows but the pilot does not optimize Flash timing.
- Historical Negate and other unrelated unsupported mechanics remain unimplemented.
- Both control and candidate now execute Retro-Mutation (two versus three copies); cast telemetry cannot identify the marginal physical copy.
- Historical interaction and first-interaction proxies exclude Aura suppression; Aura execution is reported separately.
- Cast-conditioned win rates are descriptive selection-biased subsets, not causal estimates.
- Effective P/T after resolution can exceed 0/1 because counters and other modifiers apply after base P/T setting.
- Full saved-record replay hashes include Aura events. The older runtime_fingerprint field alone does not encode every continuous characteristic.
- Suppression and attachment are observed; counterfactual prevented attacks or damage are not quantified.

Two attempts are preserved for audit: [the invalid-target logging fix](audit/R6_C_SUPERSEDED_RUNTIME_001/AUDIT.json) and [the combat enumeration bottleneck](audit/R6_C_SUPERSEDED_RUNTIME_002/AUDIT.json). Each contains a superseded control and 400 completed candidate games; none are included in final metrics. The latter identified scheduled game 424 against Splinter as the slow case. Pruning impossible block assignments preserved the full ordered legal action surface and reduced that diagnostic game to under one second. All 4,500 final control records and the first 400 final candidate records exactly match the pre-pruning records, but were freshly executed under the final runtime. The complete 900-game final test uses this same runtime throughout.

Reproduce without mixing runtimes:

```sh
uv sync --locked --dev
uv run python tools/run_objective_balance_lab_round6c.py
uv run python tools/run_objective_balance_lab_round6c.py --control --workers 8
uv run python tools/run_objective_balance_lab_round6c.py --candidate --workers 8
uv run python tools/build_objective_balance_lab_round6c_results.py --check
```

The runner verifies completed checkpoints and resumes only missing work; it does not rerun a completed cell. For fresh execution, use a separate checkout and move the two final `.json.gz` files aside there before running. Keep the published evidence intact.
