# Round 4A Raphael Utility Substitution — Post-Support Results

This artifact is a post-semantic-support replay. The original Round 4A evidence is preserved unchanged and remains the pre-fix comparison.

| Candidate | Pre-fix WR | Post-support WR | Post vs official parent Δ | Balance Δ | Skateboard casts | Pizza casts | Hypothesis | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|---|
| OBL-R4-RAPHAEL-A | 75.67% | 72.00% | -4.78% | -4.78% | 970 | 0 | UTILITY_HYPOTHESIS_PARTIALLY_SUPPORTED | PROMISING_NEEDS_VARIANT |
| OBL-R4-RAPHAEL-B | 75.67% | 73.00% | -3.78% | -3.78% | 725 | 139 | UTILITY_HYPOTHESIS_PARTIALLY_SUPPORTED | PROMISING_NEEDS_VARIANT |

## Interpretation

Both utility cards are now observable: legal opportunities, selections, casts, resolutions, and uses are separately counted. The utility-substitution direction is therefore no longer semantically unresolved. The results remain a promising but not accepted variant until a future combined validation confirms that the changed utility behavior improves Raphael's power profile without creating a new artifact-search interaction problem.

## Telemetry

### OBL-R4-RAPHAEL-A
- Skateboard: drawn=1057, legal_opportunities=19454, selected=970, casts=970, resolved=970, activations=2540, equips=2540, effect_used=2540
- Spicy Oatmeal Pizza: drawn=0, legal_opportunities=0, selected=0, casts=0, resolved=0, activations=0, equips=0, effect_used=0
- Matchup rates: {"april_oneil": 0.91, "bebop_rocksteady": 0.79, "casey_jones": 0.61, "donatello": 0.78, "krang": 0.86, "leonardo": 0.82, "michelangelo": 0.66, "shredder": 0.5, "splinter": 0.55}
- Matchup deltas vs official parent: {"april_oneil": -0.05999999999999994, "bebop_rocksteady": -0.08999999999999997, "casey_jones": -0.010000000000000009, "donatello": -0.030000000000000027, "krang": -0.07000000000000006, "leonardo": 0.0, "michelangelo": -0.010000000000000009, "shredder": -0.06999999999999995, "splinter": -0.08999999999999997}
- Extremes: {"over_60_40": 7, "over_70_30": 5, "weakest_matchup": "shredder", "weakest_matchup_win_rate": 0.5, "worst_matchup": "april_oneil", "worst_matchup_win_rate": 0.91}
### OBL-R4-RAPHAEL-B
- Skateboard: drawn=790, legal_opportunities=14112, selected=725, casts=725, resolved=725, activations=2039, equips=2039, effect_used=2039
- Spicy Oatmeal Pizza: drawn=267, legal_opportunities=7554, selected=139, casts=139, resolved=139, activations=77, equips=0, effect_used=77
- Matchup rates: {"april_oneil": 0.91, "bebop_rocksteady": 0.8, "casey_jones": 0.65, "donatello": 0.78, "krang": 0.87, "leonardo": 0.84, "michelangelo": 0.67, "shredder": 0.5, "splinter": 0.55}
- Matchup deltas vs official parent: {"april_oneil": -0.05999999999999994, "bebop_rocksteady": -0.07999999999999996, "casey_jones": 0.030000000000000027, "donatello": -0.030000000000000027, "krang": -0.06000000000000005, "leonardo": 0.020000000000000018, "michelangelo": 0.0, "shredder": -0.06999999999999995, "splinter": -0.08999999999999997}
- Extremes: {"over_60_40": 7, "over_70_30": 5, "weakest_matchup": "shredder", "weakest_matchup_win_rate": 0.5, "worst_matchup": "april_oneil", "worst_matchup_win_rate": 0.91}
