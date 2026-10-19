# Baseline 005 Control Attempt 5

**Status: BLOCKED — fail-closed simulator defect**

Attempt 5 used the unchanged ten-deck Baseline 005 environment, the repaired Food-search runtime `8d873b6ae9527a9274c0d783c90c71f26f5c1302d161e43998eee8c9cd559972`, and the authenticated 45-cell schedule. The safeguarded runner completed 1,300 games across 13 cells, then stopped without retrying when the `raphael|krang` cell produced two identical classes of runtime failure.

| Item | Result |
|---|---:|
| Required games | 4,500 |
| Completed games | 1,300 |
| Completed cells | 13 / 45 |
| Runtime failures | 2 |
| Draws | 0 |
| Replay cells | 1 |
| Final artifact | gzip/read-back valid |
| Balance interpretation | Not admissible |

Failures:

- Canonical block 6, seed `108687052940046901150408742631474974084904382487031619852802729825648363318082`, seats Krang/Raphael, first player Krang: `ValueError: damage creature target is invalid`.
- Canonical block 40, seed `63960804773867057066244079686420048244385109677095274722534118927427377020047`, seats Krang/Raphael, first player Krang: `ValueError: damage creature target is invalid`.

The partial artifact is preserved at `BASELINE_005_ISSUE289_FOOD_SEARCH_CONTROL_ATTEMPT_005.json.gz` with SHA-256 `93ad17ed91bf5b7c1f0dd1c32414767f2a5a8ffe2806466ebb811fc06c1ab5e7`. It was atomically finalized, decompressed, hashed, and read back before the runner stopped.

No games were retried, no schedule or deck was changed, and no historical artifact was overwritten. The completed 1,300 games are diagnostic evidence only and must not be used as a balance baseline. The failure indicates a remaining generic damage-target legality defect, separate from the Food-search repair. Further calibration is blocked pending diagnosis and repair.
