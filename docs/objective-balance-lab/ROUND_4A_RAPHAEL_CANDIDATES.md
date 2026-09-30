# Objective Balance Lab — Round 4A Raphael Utility Substitution

Round 4A tests only Raphael, from the exact `decks/raphael/PROTOTYPE_0.3.txt` parent in `OBL-BASELINE-001`. Both candidates remove two Casey Jones, Jury-Rig Justiciar copies and retain the parent’s 22 Mountain mana base. No other deck changes.

## Pre-screen

| Card | MV | Type | Color / legality | Relevant rules text | Cardcade / AcceptancePilot coverage | Prior evidence |
|---|---:|---|---|---|---|---|
| Skateboard | 1 | Artifact — Equipment | Colorless; Standard legal | When it enters, tap target permanent. Equipped creature gets +1/+0 and haste. Equip {1}. | Supported artifact entry, target tap, Equipment attachment, power/haste semantics; actively represented in prior Casey experiments. | R2 Casey A used +1 Skateboard; it is also present in the parent and appears in prior signature telemetry. |
| Spicy Oatmeal Pizza | 3 | Artifact — Food | Red; Standard legal in Raphael | When it enters, deal 4 damage to any target and 3 damage to you. {2}, {T}, sacrifice: gain 3 life. | Supported artifact ETB damage and Food activation; active in R2 Casey B and the authoritative damage/Food tests. | R2 Casey B used +1 Spicy Oatmeal Pizza and was promoted into Baseline 001. |

Both additions can be found by Casey Jones, Jury-Rig Justiciar. Increasing artifact density may therefore improve the remaining two Casey copies; that is an explicit countervailing mechanism in both hypotheses, not an ignored confounder.

## Candidates

| ID | Exact diff | Hypothesis |
|---|---|---|
| `OBL-R4-RAPHAEL-A` | -2 Casey Jones, Jury-Rig Justiciar; +2 Skateboard | Utility density lowers Raphael’s board-pressure efficiency while preserving street-fighter / improvised-gear identity. |
| `OBL-R4-RAPHAEL-B` | -2 Casey Jones, Jury-Rig Justiciar; +1 Skateboard; +1 Spicy Oatmeal Pizza | Diversified utility lowers threat density without overconcentrating Raphael around one support card. |

Both candidates are exactly 60 cards, preserve 22 Mountains, remain color/legal, and change only four card copies. The experiment runs 900 games per candidate against the nine frozen `OBL-BASELINE-001` opponents, using the frozen schedule and no adaptive or replacement seeds.

The primary comparison is utility substitution versus prior threat substitutions: R1 Casey → Raphael, Ninja Destroyer; R2 Casey → Most Attitude / Nightwatcher; and R3 Casey → Most Attitude / Raphael’s Technique.
