# Issue #90: post-Action #26 bounded Stage #002 measurement

Baseline: `9febd70c9b6c2512823ca97062c48d18ec489fd3` (authoritative Action #26 merge).
Local main and a clean worktree were verified immediately before execution.
Command: `.venv/Scripts/python.exe scripts/run_acceptance_stage_002.py --execute --output docs/cardcade/POST_ACTION_26_ISSUE_90_STAGE_002_RESULTS.json`.

## Execution and integrity

Exactly one frozen matrix run completed: 16 distinct games / 32 executions, including duplicates. Pairings and seeds were Donatello / Krang (7201, 7202), Michelangelo / Bebop & Rocksteady (7211, 7212), Splinter / Shredder (7221, 7222), and April / Casey (7231, 7232), both seat orientations. No additional games were used for analysis.

All duplicates were byte-equivalent. Invariant violations: 0. Runner stops: 0. Existing serialized evidence validation passed, including Stockman reconstruction. The static manifest matched `build_stage_manifest` exactly. All 16 report bodies reconstructed exactly through `reconcile_snapshot` using serialized authoritative evidence, presence, occurrences, execution references, contexts and witnesses. Report and aggregate digests verified.

The fresh result, complete inventory, and exact ranking each have raw-byte SHA-256 sidecars, verified against working-tree and staged Git bytes. Existing `POST_ACTION_26_*` LF rules cover these new artifacts. Result SHA-256: `4d1ad9215620a1ab4eae28c240191de916871ca9cc9166b2c2363f919828a49d`.

## Inventory and continuity

| Measurement | EXECUTED | REACHED / UNSUPPORTED | PRESENT / UNREACHED |
| --- | ---: | ---: | ---: |
| Issue #87 post-Action #25 | 22 | 8 | 133 |
| Accepted Action #26 candidate | 23 | 7 | 134 |
| Fresh Issue #90 merged baseline | 23 | 7 | 134 |

These counts cover semantic occurrence rows across the 16 distinct games; duplicates are not double-counted. Complete physical-card/token presence is separately retained in the result artifact: 73 EXECUTED, 7 REACHED / UNSUPPORTED, 3645 PRESENT / UNREACHED presence rows.

Explicit EXECUTED witnesses:

- Stockman ETB draw then discard: `donatello-krang:canonical:7202`.
- Action #21 Donatello artifact-entry self-counter: `donatello-krang:canonical:7201` and `donatello-krang:reversed:7202`.
- Action #25 Shredder temporary deathtouch: `splinter-shredder:reversed:7222`.

None of these fragments remains REACHED / UNSUPPORTED where naturally reached. Across every game/semantic classification, there are no differences from the accepted Action #26 candidate, and no previously EXECUTED occurrence count decreased relative to Issue #87. The fresh aggregate is identical to the accepted candidate aggregate; this was independently rerun at the merge baseline, not copied.

Relative to Issue #87, Stockman's one occurrence moves from REACHED / UNSUPPORTED to EXECUTED. Fugitive Droid has one additional PRESENT / UNREACHED occurrence in `donatello-krang:canonical:7202` (3 to 4), matching the accepted candidate. No other occurrence-count delta was observed. No previously banked semantic continuity anomaly or foundational simulator blocker was observed within this bounded matrix. This finding does not establish behavior for unreached semantics.

## Remaining unsupported ranking

Ranking is descending occurrence count, then game count, then matchup count, with alphabetical ties. It contains no next-action selection or balance inference.

| Rank | Card | Occurrences | Games | Matchups |
| --- | --- | ---: | ---: | ---: |
| 1 | Casey Jones, Jury-Rig Justiciar | 3 | 3 | 1 |
| 2 | Casey Jones, Vigilante | 2 | 2 | 1 |
| 3 | Courier of Comestibles | 1 | 1 | 1 |
| 4 | Zoo Escapees | 1 | 1 | 1 |

Exact Oracle fragments, limitations, game/object/occurrence identifiers and witnesses are in `POST_ACTION_26_ISSUE_90_UNSUPPORTED_RANKING.json`. All three complete semantic occurrence inventories, authenticated execution references, continuity witnesses and comparison deltas are in `POST_ACTION_26_ISSUE_90_INVENTORY.json`. Full physical presence and authoritative event evidence remain in the result JSON.

## Handoff

Evidence only for Issue #90. All prior measurements and Action #26 candidate artifacts remain unchanged. No engine, interpreter, runner, deck, Pilot or calibration change. HQ must independently interpret the fresh inventory and authorize any next action. Action #27 remains NOT AUTHORIZED.
