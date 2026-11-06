# Stage 002 `silent_approximation` Stop Ledger

## Scope and provenance

This is a read-only reconciliation of the preserved 300-game archive. It does
not rewrite a result, snapshot, manifest, or run record. The row-level source
links and the SHA-256 of each source `result.json` are in
[`CARDCade_STAGE_002_SILENT_STOP_LEDGER.csv`](CARDCade_STAGE_002_SILENT_STOP_LEDGER.csv).

- Archive: `G:\cardcade\diagnostics\cardcade-smoke10-20261031-explore300r1-b01-g01` through `...-b30-g10`.
- Source run identity: `32a80228714674327aca62f8b86b70c4c4afc929`.
- Frozen Stage 002 source blob: `bed173e3f4f3f13b0d1320a3a910153c38d844be`.
- Frozen card data SHA-256: `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`.
- Preserved accepted Stage 002 manifest: `docs/cardcade/ACCEPTANCE_STAGE_002_RESULTS.json`, digest `58788be5bc4322ba7ffc5aa36b1df61fd3f487d6b2ea539b3129a998d4cdf771`.
- Frozen reconciler used: `reconcile_snapshot` from the source-identified frozen Stage 002 module above.
- Builder: `tools/cardcade_stage002_silent_stop_ledger.py`.

The builder verified all 300 unique run IDs, result/run-manifest ID and seed
agreement, expected source commit, and `COMPLETE` result states. It emitted
exactly 485 `silent_approximation` rows across 201 distinct run IDs. Each row
contains a stable record identity, game/run ID, stop detail, mechanic family,
provisional cause, severity, confidence, exact source JSON pointer, result
SHA-256, and a hash of the canonical reconciler stop record. Raw archived
stops link to their exact `snapshot.conformance.stop_records` index. Stops
added by the frozen reconciler are explicitly labeled as derived and point to
the conformance snapshot from which they were derived.

## Record-level reconciliation

| Provisional classification | Records | Distinct affected games |
| --- | ---: | ---: |
| Indeterminate | 303 | 173 |
| Conformance/provenance defect | 126 | 126 |
| Unsupported semantic | 56 | 28 |
| **Total** | **485** | **201** |

The earlier provisional aggregate was 317 indeterminate / 126 provenance /
42 unsupported. Re-running the frozen reconciler against the archived bytes
does not reproduce that split. Fifty-six stop records directly identify
semantic keys present in the frozen report's `reached_unsupported` set; the
builder classifies those records as unsupported. This is 14 more than the
earlier unsupported aggregate and 14 fewer indeterminate records. The earlier
42-count had no record-level membership map available for a one-to-one
comparison, so this report does not invent which particular records were
previously in each category. The CSV supplies the evidence for all 56 records
so HQ can audit the revised aggregate. No historical outcome is reclassified.

Provenance classification is based on details that identify an execution
reference the frozen reconciler does not authenticate, or a context/witness
identity that cannot be joined to a reached unsupported semantic. Indeterminate
means the stop does not supply a reconstructive link sufficient for either
classification. “Unsupported semantic” means the frozen reconciler proves the
semantic was reached but does not authenticate its execution; it does not
establish that the game outcome was wrong.

## Mechanic-family counts

Rows can name more than one family; these counts intentionally overlap and do
not sum to 485.

| Mechanic family | Indeterminate | Provenance | Unsupported |
| --- | ---: | ---: | ---: |
| Artifact interaction | 66 | 31 | 12 |
| Combat legality | 104 | 13 | 28 |
| Mana and payment | 28 | 0 | 4 |
| Other static or triggered ability | 116 | 56 | 12 |
| Unresolved evidence/index identity | 105 | 46 | 0 |
| Zone transition and recursion | 18 | 29 | 56 |

The evidence does not support an outcome-impact severity ranking for individual
historical games. Severity is therefore recorded as high evidence risk for the
126 provenance rows, potential gameplay consequence with outcome effect
unproven for the 56 reached unsupported rows, and undetermined for the 303
indeterminate rows. Confidence is similarly limited to the evidence property
being classified, not to whether a historical result would change under a
different engine.

## Reproduction and integrity

From the PR #381 worktree, the bounded command was:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & .venv\Scripts\python.exe -B tools\cardcade_stage002_silent_stop_ledger.py --archive-root G:\cardcade\diagnostics --frozen-root C:\projects\tmt\.diag003-frozen-32a8022 --manifest docs\cardcade\ACCEPTANCE_STAGE_002_RESULTS.json --output docs\cardcade\CARDCade_STAGE_002_SILENT_STOP_LEDGER.csv
```

Result: 485 rows, 300 unique complete runs, classification totals 303 / 126 /
56. CSV SHA-256: `4476cc931b91354c076dedc543c9fea89ef5c43c62c0cf786a889a3bc7b884c5`.

The archive remains the historical source of record. The ledger is a derived
analysis product, not a replacement for it.

## Limits

This ledger classifies evidence records, not unique mechanic defects. Several
records may describe the same underlying event or semantic, and one stop may
link to multiple mechanic families. The frozen reconciler cannot establish
whether any historical outcome would differ. Classification is provisional
and should be revised only if source-linked evidence establishes a stronger
record-level explanation.
