# Post-Action #30 merged-baseline Stage #002 remeasurement

PR #100 was merged with the exact-head guard at accepted candidate `ff1aece11d9811c5e50d67821d2277a1f903ee7f`, following HQ acceptance comment #5594680183. Authoritative merge SHA: `1c54dd755d97b9a963589c32e76bc66526a1132a`.

Local main was synchronized to that exact merge and verified clean before execution. The unchanged runner was invoked exactly once:

```
.venv/Scripts/python.exe scripts/run_acceptance_stage_002.py --execute --output docs/cardcade/POST_ACTION_30_MERGED_STAGE_002_RESULTS.json
```

The frozen 16 distinct games / 32 executions completed. Subsequent verification used saved evidence only; no additional Stage or Smoke games were run.

Observed result: **30 EXECUTED / 1 REACHED-UNSUPPORTED / 133 PRESENT-UNREACHED**. These counts were measured, not forced. The entire parsed result is identical to the accepted candidate result. The frozen manifest matches; all duplicate evidence matches; zero stops and zero invariant violations occurred. All 16 reports reconstruct independently, including the complete Jury-Rig and Vigilante evidence chains.

No previously EXECUTED game/semantic occurrence count decreases against either the accepted Action #30 candidate or the authoritative post-Action #29 merged result. Courier, resolved Vigilante, all three Jury-Rig transactions and every other banked execution witness retain continuity. The prior comparison artifacts' SHA-256 sidecars were checked against committed bytes.

The only remaining unsupported occurrence is Casey Jones, Vigilante in `april-casey:canonical:7231`: the game ends before its outstanding delayed obligation is due. It remains conservatively REACHED-UNSUPPORTED. There are no remaining reached-unsupported Jury-Rig occurrences in this matrix.

Fresh evidence, each with SHA-256 sidecar:

- `POST_ACTION_30_MERGED_STAGE_002_RESULTS.json`: full fresh result.
- `POST_ACTION_30_MERGED_INVENTORY.json`: observed counts, exact references, baseline and continuity checks.
- `POST_ACTION_30_MERGED_UNSUPPORTED_RANKING.json`: remaining exact Vigilante witness.
- `POST_ACTION_30_MERGED_TRANSACTION_CHAINS.json`: full natural Jury-Rig/Vigilante authoritative chain evidence.

All new sidecars were checked against staged bytes before commit. No historical artifacts, production code, runner configuration, decks or matrix inputs changed. This evidence-only commit preserves the measurement on top of the exact merge baseline.

HQ interpretation is the next gate, including whether an engine-validation checkpoint is warranted. This measurement does not authorize further work. Action #31 remains NOT AUTHORIZED. Calibration remains BLOCKED. Prototype 0.3 remains NOT AUTHORIZED.
