# Objective Balance Lab — Round 3 Delta Results

All eight candidates completed 900 games against the nine OBL-BASELINE-001 opponents (7,200 games total). Negative Balance Δ is an improvement. Historical R1/R2 results remain contextual because their isolated parents predate OBL-BASELINE-001.

| Experiment | Parent WR | Candidate WR | Balance Δ | >60/40 | >70/30 | Hypothesis | Verdict |
|---|---:|---:|---:|---:|---:|---|---|
| `OBL-R3-RAPHAEL-A` | 75.11% | 77.89% | +2.78% | 8 | 6 | FALSIFIED | REJECT_BALANCE_REGRESSION |
| `OBL-R3-RAPHAEL-B` | 75.11% | 76.22% | +1.11% | 8 | 5 | FALSIFIED | REJECT_BALANCE_REGRESSION |
| `OBL-R3-SHREDDER-A` | 72.44% | 72.22% | +0.44% | 8 | 5 | PARTIALLY_SUPPORTED | REJECT_BALANCE_REGRESSION |
| `OBL-R3-SHREDDER-B` | 72.44% | 74.22% | +1.33% | 8 | 5 | FALSIFIED | REJECT_BALANCE_REGRESSION |
| `OBL-R3-APRIL_ONEIL-A` | 26.56% | 27.22% | -0.67% | 6 | 5 | SUPPORTED | ACCEPT_FOR_COMBINED_MATRIX |
| `OBL-R3-APRIL_ONEIL-B` | 26.56% | 23.78% | +2.78% | 8 | 6 | FALSIFIED | REJECT_BALANCE_REGRESSION |
| `OBL-R3-KRANG-A` | 38.33% | 36.00% | -0.33% | 7 | 4 | PARTIALLY_SUPPORTED | PROMISING_NEEDS_VARIANT |
| `OBL-R3-KRANG-B` | 38.33% | 27.00% | +4.00% | 6 | 5 | FALSIFIED | REJECT_BALANCE_REGRESSION |

## Per-candidate matchup deltas

### `OBL-R3-RAPHAEL-A` — IDENTITY_STRENGTHENED

leonardo: +6.00%; donatello: +7.00%; michelangelo: +3.00%; splinter: -3.00%; shredder: +3.00%; krang: +0.00%; bebop_rocksteady: +2.00%; april_oneil: +5.00%; casey_jones: +2.00%

### `OBL-R3-RAPHAEL-B` — IDENTITY_STRENGTHENED

leonardo: +3.00%; donatello: +6.00%; michelangelo: +2.00%; splinter: +2.00%; shredder: -3.00%; krang: -2.00%; bebop_rocksteady: +4.00%; april_oneil: +2.00%; casey_jones: -4.00%

### `OBL-R3-SHREDDER-A` — IDENTITY_PRESERVED

leonardo: -4.00%; raphael: -3.00%; donatello: -2.00%; michelangelo: -3.00%; splinter: -3.00%; krang: +2.00%; bebop_rocksteady: +4.00%; april_oneil: +4.00%; casey_jones: +3.00%

### `OBL-R3-SHREDDER-B` — IDENTITY_PRESERVED

leonardo: -8.00%; raphael: +2.00%; donatello: +1.00%; michelangelo: +0.00%; splinter: +3.00%; krang: +6.00%; bebop_rocksteady: +6.00%; april_oneil: +4.00%; casey_jones: +2.00%

### `OBL-R3-APRIL_ONEIL-A` — IDENTITY_STRENGTHENED

leonardo: -2.00%; raphael: -1.00%; donatello: -1.00%; michelangelo: +0.00%; splinter: +0.00%; shredder: +0.00%; krang: +10.00%; bebop_rocksteady: +1.00%; casey_jones: -1.00%

### `OBL-R3-APRIL_ONEIL-B` — IDENTITY_PRESERVED

leonardo: +3.00%; raphael: -2.00%; donatello: -11.00%; michelangelo: -2.00%; splinter: -7.00%; shredder: -6.00%; krang: -1.00%; bebop_rocksteady: -1.00%; casey_jones: +2.00%

### `OBL-R3-KRANG-A` — IDENTITY_STRENGTHENED

leonardo: -7.00%; raphael: +0.00%; donatello: -13.00%; michelangelo: +2.00%; splinter: +1.00%; shredder: +1.00%; bebop_rocksteady: +2.00%; april_oneil: -7.00%; casey_jones: +0.00%

### `OBL-R3-KRANG-B` — IDENTITY_STRENGTHENED

leonardo: -12.00%; raphael: -2.00%; donatello: -16.00%; michelangelo: -9.00%; splinter: -11.00%; shredder: -4.00%; bebop_rocksteady: -17.00%; april_oneil: -18.00%; casey_jones: -13.00%

## Synthesis

- **Raphael** — best `OBL-R3-RAPHAEL-B`; informative failure `OBL-R3-RAPHAEL-A`; Combined 002 suitable: `False`; unresolved question: A narrower, high-cost Raphael combat-risk effect lowers generic rate while preserving Raphael-specific attack decisions.
- **Shredder** — best `OBL-R3-SHREDDER-A`; informative failure `OBL-R3-SHREDDER-B`; Combined 002 suitable: `False`; unresolved question: Reducing the measurably active Squirrelanoids package lowers early development while slower villain cards preserve ruthless pressure.
- **April O'Neil** — best `OBL-R3-APRIL_ONEIL-A`; informative failure `OBL-R3-APRIL_ONEIL-B`; Combined 002 suitable: `True`; unresolved question: Replacing interaction density with April-specific selection and end-step card advantage improves reliable resource generation.
- **Krang** — best `OBL-R3-KRANG-A`; informative failure `OBL-R3-KRANG-B`; Combined 002 suitable: `True`; unresolved question: Artifact Food that draws a card and can become mana improves engine consistency without adding Does Machines.

Provisional Combined 002 pool: `{"april_oneil": "OBL-R3-APRIL_ONEIL-A", "krang": "OBL-R3-KRANG-A"}`.

Machine-readable evidence: `ROUND_3_EVIDENCE.json`; checkpoint: `ROUND_3_EVIDENCE.checkpoint.json`; pre-screen: `ROUND_3_CANDIDATES.md`; card-role dataset: `CARD_ROLE_EVIDENCE.json`.
