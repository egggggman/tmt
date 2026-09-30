# Objective Balance Lab — Round 3 Targeted Outliers

Round 3 starts from the exact ten-deck `OBL-BASELINE-001` environment. It tests only Raphael, Shredder, April O'Neil, and Krang; the other six decks remain frozen. There are eight isolated candidates, each played against the nine baseline opponents for 900 games. No early-stop rule is used: the predeclared total is 7,200 games.

## Efficiency gate

All eight proposals passed the pre-simulation gate. Each is a two-card-slot change (four card copies moved), remains Standard/color/legal under the frozen TMNT snapshot, and has a hypothesis distinct from the other candidate for its deck. No proposed effect was rejected as unsupported. Shredder selection was telemetry-driven: prior Stomped by Foot swaps were discarded because they produced zero observable delta; Squirrelanoids and Shredder's Armor were selected because they are active in the baseline telemetry.

The parent environment is `OBL-BASELINE-001`, with source and parent hashes taken from `baselines/OBL_BASELINE_001_MANIFEST.json`. Candidate deck files are preserved under `candidates/` and are not prototype replacements.

## Candidate index

| Experiment | Deck | Exact diff | Hypothesis |
|---|---|---|---|
| `OBL-R3-RAPHAEL-A` | Raphael | -2 Casey Jones, Jury-Rig Justiciar; +2 Raphael, Most Attitude | Remove Casey density for a higher-mana Raphael threat: preserve confrontation identity while lowering early efficiency. |
| `OBL-R3-RAPHAEL-B` | Raphael | -2 Casey Jones, Jury-Rig Justiciar; +2 Raphael's Technique | Use a narrower, high-cost combat-risk effect to lower generic conversion while preserving attack decisions. |
| `OBL-R3-SHREDDER-A` | Shredder | -2 Squirrelanoids; +1 Oroku Saki, Shredder Rising; +1 Shredder's Technique | Lower active early development while preserving slower villain interaction and pressure. |
| `OBL-R3-SHREDDER-B` | Shredder | -2 Shredder's Armor; +1 Oroku Saki, Shredder Rising; +1 Shredder's Technique | Test a distinct interaction/pressure efficiency lever while retaining villain control identity. |
| `OBL-R3-APRIL_ONEIL-A` | April O'Neil | -2 Mind Transfer Protocol; +1 April, Reporter of the Weird; +1 April O'Neil, Hacktivist | Improve reliable resource generation through April-specific selection and card advantage. |
| `OBL-R3-APRIL_ONEIL-B` | April O'Neil | -2 Buzz Bots; +1 Negate; +1 Retro-Mutation | Test adaptive interaction and stabilization rather than additional value creatures. |
| `OBL-R3-KRANG-A` | Krang | -2 Crustacean Commando; +2 Omni-Cheese Pizza | Improve artifact-engine consistency through draw/mana smoothing without adding Does Machines. |
| `OBL-R3-KRANG-B` | Krang | -2 Ray Fillet, Man Ray; +2 Krang, Master Mind | Test artifact-engine payoff and closing power rather than generic rate. |

## Card-level pre-screen

The text below is from the authoritative frozen card snapshot. “Supported” means the relevant behavior is represented sufficiently for a controlled experiment; generic effects may still have lower semantic confidence than named-card telemetry.

### Raphael

| Card | MV / type | Relevant rules text | Coverage and reason |
|---|---|---|---|
| Casey Jones, Jury-Rig Justiciar | 2 / legendary creature | Haste; on entry, look at four and may reveal an artifact to hand. | Existing active baseline card; removal directly tests the unresolved Casey-density problem. |
| Raphael, Most Attitude | 4 / legendary creature | Menace; Alliance may exile the top card; attacks may play cards exiled with Raphael. | Supported creature/attack/Alliance telemetry; higher-cost Raphael identity and lower early efficiency. |
| Raphael's Technique | 6 / instant | Sneak; each player may discard their hand and draw seven. | Supported instant/Sneak and hand-replacement semantics; deliberately narrow, high-cost combat-risk lever. |

### Shredder

| Card | MV / type | Relevant rules text | Coverage and reason |
|---|---|---|---|
| Squirrelanoids | 1 / creature | Deathtouch. | Baseline signature casts are active; removal tests early-pressure density directly. |
| Shredder's Armor | 2 / artifact equipment | Enters attached; equipped creature gets +2/+1; equip sacrifices another nonland permanent. | Existing active equipment path; removal tests pressure/conversion efficiency. |
| Oroku Saki, Shredder Rising | 3 / legendary creature | Sneak; enters tapped and attacking; combat damage draws a card and loses 1 life. | Existing Shredder signature and combat/Sneak semantics; slower but strongly thematic replacement. |
| Shredder's Technique | 3 / sorcery | Sneak; destroy target creature or enchantment. | Existing interaction/Sneak semantics; slower villain interaction replacement. |

### April O'Neil

| Card | MV / type | Relevant rules text | Coverage and reason |
|---|---|---|---|
| Mind Transfer Protocol | 3 / instant | Makes an artifact or creature a 4/5 artifact creature and draws a card. | Existing April interaction/card-draw path; removal tests whether value is more important than this conversion. |
| April, Reporter of the Weird | 3 / legendary creature | Combat damage draws that many cards, then discards one. | Supported combat/card-draw semantics; April-specific selection and information identity. |
| April O'Neil, Hacktivist | 4 / legendary creature | End step draws for each card type among spells cast that turn. | Existing Round 1/Round 2 evidence and supported signature; direct resource-generation test. |
| Buzz Bots | 2 / artifact creature | Flying, vigilance; on death, draw a card. | Existing artifact-creature/death-draw path; removal tests survival rather than value. |
| Negate | 2 / instant | Counter target noncreature spell. | Existing counterspell semantics; adaptive interaction replacement. |
| Retro-Mutation | 3 / flash aura | Enchanted creature becomes a 0/1 Turtle, cannot attack, and loses abilities. | Existing aura/removal semantics; board-stabilization replacement. |

### Krang

| Card | MV / type | Relevant rules text | Coverage and reason |
|---|---|---|---|
| Crustacean Commando | 4 / creature | Baseline creature body. | Removal lowers generic early material without changing Does Machines density. |
| Omni-Cheese Pizza | 2 / artifact Food | Enters drawing a card; can be sacrificed for any-color mana or life. | Generic artifact/ETB draw/Food path is observable; consistency and smoothing test, with partial semantic-confidence caveat recorded in evidence. |
| Ray Fillet, Man Ray | 3 / creature | Existing generic creature support. | Removal tests whether Krang already assembles enough material and needs payoff instead. |
| Krang, Master Mind | 8 / legendary artifact creature | Affinity for artifacts; enters refilling hand to four; gets +1/+0 per other artifact. | Existing Krang signature and artifact-payoff semantics; direct closing-power test. |

## Reproducibility

The machine-readable pre-screen and candidate manifests are emitted by `tools/run_objective_balance_lab_round3.py`. Simulation uses the frozen Round 1 schedule, with the same 50/50 orientation for every opponent pair, no adaptive or replacement seeds, and candidate-only slices. The final evidence records exact parent/candidate hashes, card diffs, schedule identity, game results, fingerprints, and runtime errors.

Round 3 does not promote or overwrite any official deck. The provisional Combined 002 pool is determined only after the complete evidence and validation pass.
