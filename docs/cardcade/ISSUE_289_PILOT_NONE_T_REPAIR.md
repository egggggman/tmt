# Issue #289 — Generic pilot P/T projection repair

## Decision

**READY for independent repair acceptance; BLOCKED for renewed Baseline 005 calibration authorization.**

The preserved `OBL-BASELINE-005-REPAIRED-CONTROL-001` artifact remains immutable. No calibration control was rerun.

## Root cause

Both preserved Raphael/Donatello failures share one generic defect. During the damage-stage pilot decision, `pilot07.py:201` scored Manhole Missile targets with:

```text
battlefield[option.target_id].toughness - battlefield[option.target_id].damage
```

The target was a current creature whose printed card was not a creature: a Mutagen artifact animated by a persistent/base-P/T effect. The engine correctly evaluated its current toughness (6 with counters), but `pilot_input_v2.py` projected power/toughness only when `permanent.card.is_creature` was true, exposing `None`. The first violated boundary was therefore the pilot observation projection, not combat, provenance, or resource accounting.

The same condition appeared in both exact failures:

- Block 17, seed `110127092095985089794094274391071537768831682357719713359846607269436624903`, turn 13, targeting Mutagen `object-000194` (`Artifact Creature — Mutagen Robot`, effective toughness 6, printed toughness absent).
- Block 24, seed `14531251592110549889095900528423591910809141390939740757152`, turn 15, with current targets including Mutagen `object-000188`; the preceding turn contained normal combat damage and a lethal Fugitive Droid departure.

The immediate event histories show ordinary `permanent_resolved`/`creature_entered` and combat/state-based-action events before the pilot call. No malformed event provenance or forged state was observed.

## Repair

`pilot_input_v2.py` now projects evaluated P/T whenever `permanent.is_creature` is true. This is the generic current-characteristics rule: it covers animated artifacts and any other permanent whose type changes. It does not replace `None` with zero, suppress the exception, or add Raphael/Donatello behavior.

## Validation

- Focused semantic/projection/provenance tests: **60 passed**.
- Full regression: **2,104 passed, 10 skipped**.
- Ruff format/check and diff validation: **pass**.
- Exact block-17 seed: **4/4 deterministic replays**, all identical; replay hash `0a890eae0ae49334e3dcd24e77239cf5ed346ebb511f6f0d5cdd21f99b937136`.
- Exact block-24 seed: **4/4 deterministic replays**, all identical; replay hash `fa8b9412f3a6e3c07a122ee54e4e70a529a9c45b74be896f71b10557d94050b1`.
- Raphael/Donatello repair diagnostic: **100/100 completed, 0 errors**; wins Raphael 60, Donatello 40; turns 11–25, mean 15.7. This is repair evidence only, not balance evidence.
- New semantic runtime: `dc80bc679e2c0d118f543d12ae4a95661033039058b1525f32e8d076dae8d308`.
- Ten Baseline 005 deck hashes and the 172-row ledger remain unchanged.
- Prior control artifact SHA-256 remains `45c4cdcd95708bb5974620b543fb50ee4dfb43b2a0d09c288e01ceb9dfeb15d7`.

## Scope assessment

The defect can affect any deck or matchup where the generic pilot scores Manhole Missile against an animated noncreature permanent. Other pilot scoring paths either use safe zero defaults or explicitly require represented toughness. This checkpoint closes the projection defect only; it does not authorize calibration.

## Recommendation

**Repair checkpoint: READY.**  
**Baseline 005 calibration: BLOCKED pending separate HQ authorization.**
