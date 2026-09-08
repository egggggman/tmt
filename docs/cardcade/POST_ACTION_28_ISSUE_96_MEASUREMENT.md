# Issue #96: post-Action #28 bounded Stage #002 measurement

Exact baseline: `e63c6aad53464aae37f8a3b7326f2478c5ad1094`. Local `main` was synchronized to that merge and the worktree was clean before execution.

The accepted runner was executed exactly once, unchanged:

```
.venv/Scripts/python.exe scripts/run_acceptance_stage_002.py --execute --output docs/cardcade/POST_ACTION_28_ISSUE_96_STAGE_002_RESULTS.json
```

The frozen matrix completed 16 distinct deterministic games / 32 executions: Donatello / Krang seeds 7201 and 7202; Michelangelo / Bebop & Rocksteady 7211 and 7212; Splinter / Shredder 7221 and 7222; April / Casey 7231 and 7232. Each pairing used both orientations and duplicate execution. All subsequent verification used saved evidence; no additional games were run.

## Observed results

| Measurement | EXECUTED | REACHED-UNSUPPORTED | PRESENT-UNREACHED |
|---|---:|---:|---:|
| Accepted Action #28 comparison target | 25 | 5 | 134 |
| Fresh Issue #96 merged baseline | 25 | 5 | 134 |

Counts were derived from observed semantic occurrences, not forced to the comparison target. Duplicates are not counted twice. Complete physical card/token presence counts are separately 75 / 5 / 3646.

All duplicate executions are byte-equivalent. Zero invariant violations and zero runner stops occurred. The frozen manifest reconstructs exactly. Accepted serialized evidence validation passes, and each of the 16 game reports reconstructs exactly through the accepted reconciler. Fresh SHA-256 sidecars are verified against working and staged Git bytes. The Issue #93 and accepted Action #28 comparison sidecars were verified against committed bytes.

The fresh aggregate is identical to the accepted Action #28 candidate. There are no classification deltas against that candidate. No previously EXECUTED game/semantic occurrence count decreases against either the candidate or Issue #93.

## Continuity

- Courier of Comestibles remains EXECUTED in `michelangelo-bebop-rocksteady:canonical:7211`.
- Zoo Escapees remains EXECUTED in `michelangelo-bebop-rocksteady:canonical:7212`.
- Stockman remains EXECUTED in `donatello-krang:canonical:7202`.
- Action #21 Donatello witnesses remain EXECUTED in `donatello-krang:canonical:7201` and `donatello-krang:reversed:7202`.
- Action #25 Shredder remains EXECUTED in `splinter-shredder:reversed:7222`.
- All other banked EXECUTED game/semantic occurrences retain continuity. Complete execution references and classification comparisons are in the inventory.

No foundational simulator blocker was observed within this bounded matrix. This is not a claim of complete simulator support.

## Remaining reached-unsupported ranking

Ranked by descending occurrence count, distinct game count, then distinct matchup count; card name breaks ties.

| Semantic | Occurrences | Games | Matchups |
|---|---:|---:|---:|
| Casey Jones, Jury-Rig Justiciar: ETB top-four artifact selection and random-bottom ordering | 3 | 3 | 1 |
| Casey Jones, Vigilante: ETB draw three and delayed next-upkeep random discard | 2 | 2 | 1 |

Exact Oracle fragments and every witness are preserved in the ranking artifact.

## Preserved evidence

- [Fresh Stage #002 results](POST_ACTION_28_ISSUE_96_STAGE_002_RESULTS.json).
- [Complete occurrence/presence inventories and continuity comparisons](POST_ACTION_28_ISSUE_96_INVENTORY.json).
- [Remaining unsupported ranking and exact witnesses](POST_ACTION_28_ISSUE_96_UNSUPPORTED_RANKING.json).

Each JSON has an adjacent SHA-256 sidecar. All prior artifacts remain unchanged. This commit contains evidence only: no engine, test, runner, roster, seed, deck, Pilot, calibration, balance, GUI, or Prototype 0.3 changes.

HQ interpretation and next-Action selection remain pending. Action #29 is NOT AUTHORIZED.
