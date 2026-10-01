# Round 4B Raphael Utility Refinement

Parent: `decks/raphael/PROTOTYPE_0.3.txt` from `OBL-BASELINE-001`, SHA-256 `220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51`.

## Pre-screen

| Card | Baseline copies | MV | Type | Rules text | Semantic/Pilot support | Prior evidence | Expected direction |
|---|---:|---:|---|---|---|---|---|
| Casey Jones, Jury-Rig Justiciar | 4 | 2 | Legendary Creature — Human Berserker | Haste; ETB looks at four and may take an artifact. | Supported; prior R4 substitutions reduced Casey to 2. | R4-A/B removed two; remaining copies can amplify artifact density. | Lower generic pressure, but artifact-search feedback risk. |
| Mutant Town Musicians | 3 | 3 | Creature — Mutant Bard Performer | Trample; Alliance gives another creature +1/+0. | Supported creature/Alliance pressure. | No direct R4 utility test; chosen as generic support rather than Raphael signature. | Lower early pressure. |
| Skateboard | 2 | 1 | Artifact — Equipment | ETB taps a permanent; equipped creature gets +1/+0 and haste; Equip {1}. | Fully supported; R4-A post-support: 970 casts and 2,540 equips. | R4-A utility direction produced 72.00% WR and -4.78 pp balance delta. | Lower pressure density with usable gear. |
| Spicy Oatmeal Pizza | 0 | 3 | Artifact — Food | ETB deals 4 damage to any target and 3 to you; `{2}, {T}, Sacrifice`: gain 3 life. | Fully supported; R4-B post-support: 139 casts and 77 activations. | R4-B post-support showed Pizza usage but was not the primary candidate. | Slower, broader utility and stabilization. |

## Candidates

### OBL-R4-RAPHAEL-C

Diff: `-2 Casey Jones, Jury-Rig Justiciar; -1 Mutant Town Musicians; +2 Skateboard; +1 Spicy Oatmeal Pizza`.

Hypothesis: a slightly deeper shift from generic creature pressure into supported gear/Food utility lowers Raphael further while preserving confrontation identity.

### OBL-R4-RAPHAEL-D

Diff: `-2 Casey Jones, Jury-Rig Justiciar; +2 Spicy Oatmeal Pizza`.

Hypothesis: Raphael’s balance improvement comes from reducing creature pressure generally, not specifically from Skateboard.

Both candidates remain exactly 60 cards, mono-red, and start from the unchanged official baseline.
