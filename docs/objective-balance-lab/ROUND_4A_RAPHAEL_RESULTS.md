# Objective Balance Lab — Round 4A Raphael Results

Each candidate completed 900 games against the nine OBL-BASELINE-001 opponents. Negative Balance Δ is improvement. Casey jury-rig artifact-hit telemetry is unavailable in the compact runner output and is explicitly not inferred.

| Candidate | Parent WR | Candidate WR | Balance Δ | 60/40 | 70/30 | Hypothesis | Verdict |
|---|---:|---:|---:|---:|---:|---|---|
| `OBL-R4-RAPHAEL-A` | 75.11% | 75.67% | +0.56% | 8→7 | 5→5 | SEMANTICALLY_UNRESOLVED | REJECT_SEMANTIC_CONFIDENCE |
| Signature usage | Skateboard 0 casts; Pizza 0 casts; remaining Casey 467 casts | | | | | | |
| `OBL-R4-RAPHAEL-B` | 75.11% | 75.67% | +0.56% | 8→7 | 5→5 | SEMANTICALLY_UNRESOLVED | REJECT_SEMANTIC_CONFIDENCE |
| Signature usage | Skateboard 0 casts; Pizza 0 casts; remaining Casey 467 casts | | | | | | |

## Per-matchup deltas

### `OBL-R4-RAPHAEL-A`

leonardo: +0.00%; donatello: +5.00%; michelangelo: +2.00%; splinter: -5.00%; shredder: -1.00%; krang: -3.00%; bebop_rocksteady: +5.00%; april_oneil: +4.00%; casey_jones: -2.00%

### `OBL-R4-RAPHAEL-B`

leonardo: +0.00%; donatello: +5.00%; michelangelo: +2.00%; splinter: -5.00%; shredder: -1.00%; krang: -3.00%; bebop_rocksteady: +5.00%; april_oneil: +4.00%; casey_jones: -2.00%

## Prior Raphael context

R1 and R2 threat substitutions increased Raphael’s power by +1.44 to +2.11 pp; R3 threat substitutions increased it by +1.11 to +2.78 pp. Round 4A isolates utility density and diversified utility as the structural-nerf direction.

| Historical experiment | Parent WR | Candidate WR | Balance Δ |
|---|---:|---:|---:|
| OBL-R1-RAPHAEL-A | 76.78% | 78.22% | +1.44 pp |
| OBL-R2-RAPHAEL-A | 76.78% | 78.89% | +2.11 pp |
| OBL-R2-RAPHAEL-B | 76.78% | 78.22% | +1.44 pp |
| OBL-R3-RAPHAEL-A | 75.11% | 77.89% | +2.78 pp |
| OBL-R3-RAPHAEL-B | 75.11% | 76.22% | +1.11 pp |

Best next Raphael direction: `SEMANTIC_INSTRUMENTATION_REQUIRED`. Machine evidence: `ROUND_4A_RAPHAEL_EVIDENCE.json`; checkpoint: `ROUND_4A_RAPHAEL_EVIDENCE.checkpoint.json`.
