# Issue #93: post-Action #27 bounded Stage #002 measurement

Baseline: `68baed4707a32ce4fae5bedc9c7077d926bc8d23`, verified on clean `main` before execution. The accepted runner was executed once, unchanged:

```
.venv/Scripts/python.exe scripts/run_acceptance_stage_002.py --execute --output docs/cardcade/POST_ACTION_27_ISSUE_93_STAGE_002_RESULTS.json
```

The frozen matrix contains 16 distinct games / 32 executions: Donatello?Krang seeds 7201/7202, Michelangelo?Bebop/Rocksteady 7211/7212, Splinter?Shredder 7221/7222, and April?Casey 7231/7232, each in both orientations with duplicate execution. Subsequent checks used serialized evidence and ran no additional games.

## Results

| Measurement | EXECUTED | REACHED-UNSUPPORTED | PRESENT-UNREACHED |
|---|---:|---:|---:|
| Issue #90 merged baseline | 23 | 7 | 134 |
| Accepted Action #27 candidate | 24 | 6 | 134 |
| Issue #93 fresh merged baseline | 24 | 6 | 134 |

These are semantic occurrence counts across the 16 distinct games; duplicates are not counted twice. Physical card/token presence counts are separately 74 / 6 / 3646. The aggregate is identical to the accepted Action #27 candidate.

All duplicates are byte-equivalent. There are zero invariant violations and zero runner stops. The frozen manifest matches reconstruction, accepted evidence validation passes, and all 16 game reports reconstruct exactly from their serialized authoritative evidence. SHA-256 sidecars were verified for fresh artifacts and prior comparison artifacts; historical sidecars were also checked against committed bytes.

## Continuity and support boundary

- Zoo Escapees' exact leave-battlefield Mutagen-creation fragment is EXECUTED in `michelangelo-bebop-rocksteady:canonical:7212`.
- Stockman's draw-then-discard witness remains EXECUTED in `donatello-krang:canonical:7202`.
- Donatello's artifact-entry self-counter witnesses remain EXECUTED in `donatello-krang:canonical:7201` and `donatello-krang:reversed:7202`.
- Shredder's temporary deathtouch witness remains EXECUTED in `splinter-shredder:reversed:7222`.
- No previously EXECUTED game/semantic occurrence count decreased against Issue #87, Issue #90, or the accepted Action #27 candidate. Complete classification deltas and witness records are preserved in the inventory.

Mutagen activation remains unsupported. All 18 runtime Mutagen token presence rows are PRESENT-UNREACHED, with no authenticated execution references or activation records for those token identities. The interpreter still reports unsupported nonmana activation costs, targets/choices, child semantics, and timing restriction. Zoo Escapees' authenticated token creation retains `token_activated_ability_not_implemented`; creation does not establish activation support. The matrix does not demonstrate a Mutagen activation attempt.

No continuity anomaly or foundational simulator blocker was observed within this bounded measurement.

## Remaining unsupported ranking

Ranking uses descending occurrence count, distinct game count, then distinct matchup count; alphabetical order breaks ties.

| Card | Occurrences | Games | Matchups |
|---|---:|---:|---:|
| Casey Jones, Jury-Rig Justiciar | 3 | 3 | 1 |
| Casey Jones, Vigilante | 2 | 2 | 1 |
| Courier of Comestibles | 1 | 1 | 1 |

## Preserved artifacts

- [Fresh Stage #002 results](POST_ACTION_27_ISSUE_93_STAGE_002_RESULTS.json) and adjacent SHA-256 sidecar.
- [Complete classified inventory and continuity audit](POST_ACTION_27_ISSUE_93_INVENTORY.json) and adjacent SHA-256 sidecar.
- [Exact unsupported fragments, ranking, and witnesses](POST_ACTION_27_ISSUE_93_UNSUPPORTED_RANKING.json) and adjacent SHA-256 sidecar.

Result SHA-256: `a199f67e2710d18d4208c51e5d1ea6b08e6f88196faacac5c57d4e42199bf2de`.

All prior measurements are preserved. This change contains evidence only. Independent HQ interpretation and selection of any next action remain pending; Action #28 is NOT AUTHORIZED.
