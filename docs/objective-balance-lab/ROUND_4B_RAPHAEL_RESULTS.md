# Round 4B Raphael Utility Refinement — Results

Parent: OBL-BASELINE-001 Raphael. Round 4A post-support evidence remains the direct comparison for Candidates A and B.

| Build | WR | Balance Δ | 60/40 | >70/30 | Worst matchup | Utility usage | Hypothesis | Verdict |
|---|---:|---:|---:|---:|---|---|---|---|
| Baseline | 75.11% | — | 8 | 5 | krang 92.00% | — | — | BASELINE |
| OBL-R4-RAPHAEL-A | 72.00% | -4.78% | 7 | 5 | april_oneil 91.00% | Skateboard 970; Pizza 0 | prior utility direction | PROMISING_NEEDS_VARIANT |
| OBL-R4-RAPHAEL-B | 73.00% | -3.78% | 7 | 5 | april_oneil 91.00% | Skateboard 725; Pizza 139 | prior utility direction | PROMISING_NEEDS_VARIANT |
| OBL-R4-RAPHAEL-C | 70.22% | -4.78% | 7 | 5 | april_oneil 91.00% | Skateboard 964; Pizza 155 | UTILITY_HYPOTHESIS_PARTIALLY_SUPPORTED | PROMISING_NEEDS_VARIANT |
| OBL-R4-RAPHAEL-D | 74.56% | -2.22% | 7 | 5 | april_oneil 91.00% | Skateboard 466; Pizza 282 | UTILITY_HYPOTHESIS_PARTIALLY_SUPPORTED | PROMISING_NEEDS_VARIANT |

## Candidate detail

### OBL-R4-RAPHAEL-C

- Per-matchup deltas: `{"april_oneil": 0.010000000000000009, "bebop_rocksteady": -0.030000000000000027, "casey_jones": -0.05999999999999994, "donatello": -0.010000000000000009, "krang": -0.050000000000000044, "leonardo": -0.029999999999999916, "michelangelo": -0.020000000000000018, "shredder": -0.14999999999999997, "splinter": -0.09999999999999998}`
- First-player rate: 50.00%; mean/median turn: 18.13/17.0
- First creature: 5.44; battlefield presence turns 3/5/7: `{'3': 0.3211111111111111, '5': 0.9955555555555555, '7': 1.8033333333333332}`
- Interaction casts/game: 5.20
- Utility telemetry: `{"Skateboard": {"activations": 2562, "casts": 964, "drawn": 1059, "effect_used": 2562, "equips": 2562, "legal_opportunities": 19274, "resolved": 964, "selected": 964}, "Spicy Oatmeal Pizza": {"activations": 78, "casts": 155, "drawn": 262, "effect_used": 78, "equips": 0, "legal_opportunities": 7178, "resolved": 155, "selected": 155}}`

### OBL-R4-RAPHAEL-D

- Per-matchup deltas: `{"april_oneil": 0.010000000000000009, "bebop_rocksteady": 0.039999999999999925, "casey_jones": -0.009999999999999898, "donatello": 0.030000000000000027, "krang": -0.050000000000000044, "leonardo": 0.0, "michelangelo": 0.029999999999999916, "shredder": -0.019999999999999907, "splinter": -0.07999999999999996}`
- First-player rate: 50.00%; mean/median turn: 17.61/17.0
- First creature: 5.41; battlefield presence turns 3/5/7: `{'3': 0.3211111111111111, '5': 1.041111111111111, '7': 1.8822222222222222}`
- Interaction casts/game: 5.20
- Utility telemetry: `{"Skateboard": {"activations": 1484, "casts": 466, "drawn": 508, "effect_used": 1484, "equips": 1484, "legal_opportunities": 8608, "resolved": 466, "selected": 466}, "Spicy Oatmeal Pizza": {"activations": 164, "casts": 282, "drawn": 549, "effect_used": 164, "equips": 0, "legal_opportunities": 15996, "resolved": 282, "selected": 282}}`

## Synthesis

The utility direction is `UTILITY_DIRECTION_CONFIRMED`: both candidates retain meaningful utility usage and lower Raphael’s isolated balance error under the authenticated balance reference.

Best current candidate: `OBL-R4-RAPHAEL-C`, with 70.22% WR and the same -4.78 pp balance delta as the proven A direction while adding Pizza usage.
Most informative alternate: `OBL-R4-RAPHAEL-D`, which isolates Pizza-heavy utility substitution and shows a smaller balance gain.

Raphael now has a provisional candidate suitable for Combined 003: `OBL-R4-RAPHAEL-C`. This is not combined validation or promotion; Candidate D remains preserved evidence.
