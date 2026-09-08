# Post-Action #29 merged-baseline Stage #002 remeasurement

PR #98 was merged using the exact-head guard at accepted head `78e46f742baa5cccc8e92f1a2bcc9980b6175ec2`, following HQ acceptance comment #5590883604. Authoritative merge SHA: `e263f1355fd7f93e700f0739e535f967356435b7`.

Local `main` was synchronized to that exact merge and verified clean before execution. Its tree matched the accepted candidate. The existing runner was executed exactly once, unchanged:

```
.venv/Scripts/python.exe scripts/run_acceptance_stage_002.py --execute --output docs/cardcade/POST_ACTION_29_MERGED_STAGE_002_RESULTS.json
```

The frozen matrix completed 16 distinct games / 32 executions: Donatello/Krang 7201 and 7202, Michelangelo/Bebop & Rocksteady 7211 and 7212, Splinter/Shredder 7221 and 7222, April/Casey 7231 and 7232; both orientations and duplicate executions. Subsequent checks used saved evidence only. No additional Stage or Smoke execution occurred during this merged-baseline remeasurement.

## Fresh result

| Measurement | EXECUTED | REACHED-UNSUPPORTED | PRESENT-UNREACHED |
|---|---:|---:|---:|
| Accepted Action #29 candidate | 27 | 4 | 134 |
| Fresh merged baseline | 27 | 4 | 134 |

The counts are observed semantic occurrences, not forced targets. The fresh aggregate is identical to the accepted candidate. All duplicates are byte-equivalent; zero invariant violations and zero runner stops occurred. The static manifest matches, accepted evidence validation passes, and all 16 game reports reconstruct exactly. Full Vigilante delayed-chain reconstruction passes for both natural games, including terminal state evidence.

No previously EXECUTED game/semantic occurrence count decreases against either the accepted Action #29 candidate or Issue #96. Courier, Zoo Escapees, Stockman, Donatello #21, Shredder #25 and every other banked execution witness retain continuity. All exact references and comparisons are preserved in the inventory.

## Remaining ranking for HQ

Ranked by descending occurrence count, distinct games, then distinct matchups.

| Semantic | Occurrences | Games | Matchups | Meaning |
|---|---:|---:|---:|---|
| Casey Jones, Jury-Rig Justiciar | 3 | 3 | 1 | Unimplemented, excluded semantic |
| Casey Jones, Vigilante | 1 | 1 | 1 | Terminal-pending obligation, not missing delayed-discard implementation |

The original Vigilante chains in `april-casey:canonical:7231` and `april-casey:canonical:7232` remain resolved and consumed. The additional source `object-000196` / schedule `object-000198` in canonical seed 7231 remains pending when the game ends before its next upkeep. Its immediate draw is not falsely credited as whole-semantic EXECUTED. This is why the existing three-class taxonomy still contains one Vigilante REACHED-UNSUPPORTED row.

No foundational simulator blocker was observed within this bounded matrix. Whether Jury-Rig warrants Action #30 is reserved for HQ; this measurement does not authorize it.

## Fresh evidence

- [Complete Stage result](POST_ACTION_29_MERGED_STAGE_002_RESULTS.json).
- [Complete semantic/physical inventories and continuity](POST_ACTION_29_MERGED_INVENTORY.json).
- [Exact unsupported fragments and ranked witnesses](POST_ACTION_29_MERGED_UNSUPPORTED_RANKING.json).
- [Full natural delayed-chain evidence](POST_ACTION_29_MERGED_DELAYED_CHAINS.json).

Every JSON has a SHA-256 sidecar verified against working-tree and staged Git bytes. Prior comparison sidecars were checked against committed bytes. No historical artifacts or production files were changed; only these new measurement artifacts and this handoff were added.

Action #30 remains NOT AUTHORIZED. Calibration remains BLOCKED. Prototype 0.3 remains NOT AUTHORIZED. HQ interpretation is the next gate.
