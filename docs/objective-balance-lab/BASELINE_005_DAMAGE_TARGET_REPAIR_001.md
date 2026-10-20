# Baseline 005 Damage-Target Repair Checkpoint

**Repair checkpoint: READY for independent acceptance.**

The two preserved Attempt 5 failures share one generic defect. `Game.deal_damage()` checked `candidate.card.is_creature`, which describes only the printed card. `Sewer-veillance Cam` was an artifact whose current effective type included Creature because of a live animation effect. Action generation correctly offered it as a legal creature target, but resolution rejected it using the stale printed characteristic.

The repair validates `candidate.is_creature`, the current effective permanent characteristic. Resolution-time legality remains strict: if a target leaves the battlefield or loses Creature status before resolution, the spell resolves with no effect rather than redirecting, substituting, or raising an exception.

## Exact reproductions

- Block 6, seed `108687052940046901150408742631474974084904382487031619852802729825648363318082`
- Block 40, seed `63960804773867057066244079686420048244385109677095274722534118927427377020047`

Both previously failed at `engine07.py:3529` while resolving `Manhole Missile` against an animated `Sewer-veillance Cam`. Both now complete deterministically twice with identical snapshots.

Focused legality and repair tests: **32 passed**. The new 100-game Raphael/Krang diagnostic completed **100/100**, with zero errors and balanced starting positions. Its result is diagnostic only: Raphael 64, Krang 36, mean turn 17.64.

Diagnostic artifact: `BASELINE_005_DAMAGE_TARGET_REPAIR_RAPHAEL_KRANG_DIAGNOSTIC.json.gz`, SHA-256 `3d9b0b4620787460674416ddfc8bf4af70e66044193e8e85619d6f3f8e7dd921`.

New semantic runtime: `ee8d37b192a6eb37526283a458e54fb243e17d5e4dad68bd60cd863bfcf1a194`.

The Attempt 5 failed artifact and all historical controls remain unchanged. No calibration control, deck revision, historical rewrite, merge, or promotion was performed.

Recommendation: **READY for independent repair acceptance; BLOCKED for renewed calibration authorization.**
