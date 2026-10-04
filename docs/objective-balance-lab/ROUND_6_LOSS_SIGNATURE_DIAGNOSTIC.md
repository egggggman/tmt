# Krang Round 6 — Raphael/Shredder loss-signature diagnostic

**Diagnostic:** `OBL-R6-KRANG-LOSS-SIGNATURE-DIAGNOSTIC-001`  
**Control:** `OBL-BASELINE-003-RUNTIME-REFRESH-001`  
**Runtime:** `252f00317d8efbf552512768503d5f453ef9594ade48e27a94f95f05c7625982`  
**New simulations:** **0**

This is a Cardcade diagnostic pass over already-preserved Baseline 003, R6-A, and R6-B evidence. It does not modify Krang, design R6-C, authorize combined validation, or authorize promotion.

Design input for this diagnostic:

> **Falsified for Round 6:** replacing one dormant Negate with generally useful proactive artifact material is sufficient to smooth Krang's matchup distribution.

R6-A and R6-B remain preserved rejected experiments.

## Mechanical answer

**Additional proactive material helps Shredder modestly because Shredder exposes a board-combat conversion point that extra bodies or artifact power can contest. Raphael's failure signature is different: interaction-backed threat conversion remains intact, so generic board material does not materially change the matchup.**

The two matchups have nearly the same losing clock for Krang, so the distinction is not simply "Raphael is faster."

| Baseline 003 Krang loss signature | vs Raphael | vs Shredder |
|---|---:|---:|
| Krang WR | 13% | 12% |
| Mean ending turn in losses | 17.74 | 18.42 |
| Median ending turn in losses | 17 | 17 |
| Losses finished by turn 17 | 52.9% | 52.3% |
| Krang first creature, conditional mean | 8.61 | 8.21 |
| Opponent first creature, conditional mean | 5.32 | **3.13** |
| Krang interaction casts / loss | 4.02 | 4.09 |
| Opponent interaction casts / loss | **5.13** | 4.00 |

Shredder develops creatures much earlier, but its winning clock is not meaningfully faster. Raphael develops its first creature later while still ending games on roughly the same schedule and doing so with materially more interaction. That is the first strong split between the failure modes.

### Board texture

In Krang losses, conditional battlefield-presence means were:

| | T3 Krang / Opp | T5 Krang / Opp | T7 Krang / Opp |
|---|---:|---:|---:|
| Raphael | 0.88 / 0.69 | 1.46 / 1.39 | 2.01 / 2.11 |
| Shredder | 1.26 / 1.35 | 2.14 / 2.13 | **3.09 / 2.89** |

Raw creature count therefore does not explain either matchup by itself. Against Shredder, Krang can reach comparable or even slightly higher observed creature counts and still lose. The differentiator is more consistent with **board quality / combat conversion into closers** than simple deployment count.

Against Raphael, extra material is being asked to survive or matter through a higher-interaction sequence.

## Opponent win associations

These are descriptive presence lifts: how much more often the card appeared in opponent wins than opponent losses within the same Baseline 003 matchup. They are **not causal card estimates**.

### Raphael

Largest positive win-presence lifts:

- **Raphael, Tough Turtle:** +18.6 pp
- **Mutant Town Musicians:** +16.0 pp
- **Manhole Missile:** +15.1 pp
- **Raphael, Ninja Destroyer:** +12.9 pp
- **Raphael, Most Attitude:** +8.3 pp
- **Null Group Biological Assets:** +7.4 pp

Notably, Skateboard and Spicy Oatmeal Pizza were *more common in Raphael losses* than wins in this small comparison. The severe Krang matchup should therefore not be reduced to "Raphael's utility package beats Krang." The stronger signature is the combination of durable/aggressive threats plus removal/interaction.

### Shredder

Largest positive win-presence lifts:

- **Foot Mystic:** +33.3 pp
- **Shark Shredder, Killer Clone:** +23.1 pp
- **Shredder, Unrelenting:** +18.9 pp
- **Super Shredder:** +8.7 pp

Squirrelanoids, Tunnel Rats, and Oroku Saki were not positively associated with Shredder wins in this within-cell comparison. The loss pattern is more consistent with early board presence being converted by stronger middle/top-end threats.

## Krang win associations

Krang's rare wins also point away from a "just add another generic body" diagnosis.

Against Raphael, the largest Krang win-presence lifts were:

- **Stockman, Mad Fly-entist:** +57.0 pp
- **Ray Fillet, Man Ray:** +33.6 pp
- **Crustacean Commando:** +22.2 pp
- **Utrom Scientists:** +22.2 pp

Against Shredder:

- **Ray Fillet, Man Ray:** +49.6 pp
- **Stockman, Mad Fly-entist:** +45.1 pp
- **Fugitive Droid:** +15.2 pp
- **Utrom Scientists:** +10.2 pp

These are associations, not proof that drawing any one of these cards causes a win. But successful Krang games are more closely associated with **higher-impact board/interaction sequences** than with merely increasing generic permanent density.

## Round 6 cross-check

Both proactive-material experiments show the same opponent split when the added permanent was actually cast.

| Candidate / observation | vs Raphael | vs Shredder |
|---|---:|---:|
| R6-A Turtle Techie — candidate WR | 14% | 17% |
| R6-A games with Turtle Techie cast | 16 | 19 |
| WR in those cast games | **12.5%** | **42.1%** |
| R6-B Chrome Dome — candidate WR | 13% | 15% |
| R6-B games with Chrome Dome cast | 25 | 23 |
| WR in those cast games | **12.0%** | **26.1%** |
| R6-B games with actual Chrome Dome modifier impact | 10 | 16 |
| WR in modifier-impact games | **20.0%** | **37.5%** |

These conditional records are especially selection-sensitive and are not causal estimates. Their value is that **two different proactive permanents reproduce the same directional split**: when the added permanent appears, Shredder is more contestable while Raphael remains close to its baseline failure rate.

R6-B's own early-board telemetry reinforces that point. Against Raphael, Krang's conditional first-creature timing actually moved later (8.45 → 9.65), first-blocker timing moved later (3.70 → 3.96), and observed T3/T5/T7 battlefield means did not improve. Against Shredder, first-creature timing was effectively unchanged, the first-blocker proxy improved modestly (4.02 → 3.82), and T3 presence rose slightly.

So the aggregate R6-B early-board improvement was **not** a repair of the Raphael cell.

## Mechanical diagnosis for Design Studio

### Shredder
**Board-contestable progression into closers.**

Shredder puts creatures onto the table early. Krang can eventually match raw count, but Shredder's winning sequences are more associated with higher-impact threats. Extra artifact material can change blocks, trades, and combat math enough to flip a small subset of games. That explains why both Turtle Techie and Chrome Dome show a modest Shredder response.

### Raphael
**Interaction-assisted threat conversion.**

Raphael does not need to establish the earliest creature board to kill on the same schedule. Its wins pair threats with a heavier interaction load, and the strongest within-cell associations include Tough Turtle, Manhole Missile, Ninja Destroyer, and Null Group. Adding one generally useful permanent gives Raphael another object to interact through without attacking the sequence that actually converts its position into a win.

That is why the Round 6 family can be closed: **generic proactive material addresses a symptom in the Shredder matchup but does not address the Raphael failure mechanism.**

## Evidence limits

The preserved OBL game summaries do **not** contain per-turn life totals or damage-source trajectories, so damage distribution cannot be reconstructed honestly; ending-turn distribution is the available pressure proxy.

They also do not contain per-turn hand size, unused mana, stranded cards, flood/screw, or an authoritative loss-cause label. Those remain unavailable rather than zero. Opponent first-interaction timing is also not populated in these summaries, so interaction comparison uses cast totals and card/action associations.

Finally, these severe matchups provide only 13 Krang wins against Raphael and 12 against Shredder in the baseline cell. Presence lifts and conditional cast-game WRs are therefore diagnostic associations, not card-level causality.

## Handoff

**Owner: 🧪 Design Studio**

Cardcade does **not** propose a replacement card.

Design Studio may now decide whether a mechanism-specific R6-C is justified from this diagnosis. Any R6-C must test a hypothesis materially different from:

`-1 Negate / +1 generally useful proactive permanent`

No combined validation or promotion is authorized.
