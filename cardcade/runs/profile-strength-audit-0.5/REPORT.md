# Cardcade Engine 0.5 — Profile Strength Audit

## Protocol and scope

All Prototype 0.1 and 0.2 decklists are frozen. Each condition uses roster 0.2, seed `20260809`,
all 45 matchups, 20 games per matchup, and exact 10/10 starting-player splits: 900 games per
condition. The baseline reproduces Smoke 0.5 exactly. Neutral values are arithmetic roster means;
they were not selected to force 50% results.

Cardcade is a heuristic rehearsal, not a Magic rules engine. Smoke-size five-point matchup steps
are directional evidence. The paired conditions isolate model sensitivity, not real deck power.

## Complete fixed profile-prior inventory

Six deck-varying numeric inputs influence outcomes independently of parsed card facts:

| Prior | Outcome path | Neutral value | Authored range |
|---|---|---:|---:|
| `creature_rate` | Classifies generic spells during play | 0.616 | 0.57–0.69 |
| `interaction_rate` | Classifies remaining generic spells during play | 0.550 | 0.45–0.63 |
| `board_value` | Artifact line choice and final board score | 1.570 | 1.45–1.70 |
| `mana_value` | Final mana-spent score | 0.359 | 0.34–0.38 |
| `support_value` | Artifact line choice and final support score | 0.735 | 0.35–1.00 |
| `interaction_value` | Artifact line choice and final live-interaction score | 0.835 | 0.65–1.00 |

`synergy` and `strategy` are labels only. `artifact_rate` is legacy, unused metadata.
`artifact_plan` selects artifact sequencing and telemetry, but its effects use card-derived tags; it
was preserved. Card-derived mana curves, artifact roles and costs, payoff sequencing, Krang affinity
floors/discounts, and target-limited interaction resolution were also preserved.

Global hard-coded assumptions affect every deck rather than encode deck identity: the +1.5/-1.5
starting-player term, Gaussian closing variance (σ 3.8), +0.3 live-interaction resolution term,
artifact setup/payoff terms (0.45/0.85), affinity savings term (0.12), mulligan penalty (0.8), and
line-choice constants. Engine 0.5 now emits each final score-delta component per match. They are not
neutralized because they are shared gameplay-model assumptions, not fixed profile-strength priors.

## Main comparison

| Deck | Baseline | Neutralized | Delta | 50% contraction | 150% amplification |
|---|---:|---:|---:|---:|---:|
| Leonardo | 38.9% | 44.4% | +5.6 pp | 41.1% | 37.8% |
| Raphael | 52.8% | 46.1% | -6.7 pp | 48.9% | 56.1% |
| Donatello | 66.7% | 66.7% | 0.0 pp | 67.2% | 66.7% |
| Michelangelo | 44.4% | 43.9% | -0.6 pp | 44.4% | 44.4% |
| Splinter | 46.7% | 50.6% | +3.9 pp | 47.8% | 41.7% |
| April O'Neil | 47.2% | 51.1% | +3.9 pp | 48.9% | 45.0% |
| Casey Jones | 47.2% | 46.7% | -0.6 pp | 46.7% | 47.2% |
| Shredder | 46.1% | 42.8% | -3.3 pp | 43.3% | 49.4% |
| Krang | 62.8% | 65.0% | +2.2 pp | 65.0% | 61.7% |
| Bebop & Rocksteady | 47.2% | 42.8% | -4.4 pp | 46.7% | 50.0% |

Donatello's 66.7% survives complete neutralization unchanged. Its execution is 83.3% versus 83.9%
at baseline. Krang rises to 65.0% while execution rises from 58.9% to 60.6%; affinity savings remain
exactly 1.89 mana/game. Leonardo improves by 5.6 points but remains below the 45–55% aggregate band.
Splinter reaches 50.6% without a deck change. Bebop & Rocksteady's 38.3% flood rate is identical,
confirming that flood comes from its frozen 24-land curve rather than these priors.

## Isolated attribution and matchup polarity

The largest isolated deck-rate movements came from `board_value` (up to 6.7 points) and
`support_value` (up to 5.0). `mana_value` moved decks by at most 4.4; classification and interaction
priors moved decks by at most 3.9 and 2.2 respectively. These isolated effects are not additive.
Full machine-readable per-deck attribution is in `profile-strength-audit.json`.

The 11 baseline matchups outside 35–65% reproduce Smoke 0.5. Complete neutralization leaves ten
outside the band. Seven original outliers survive: Leonardo–Donatello, Leonardo–Krang,
Donatello–April, Donatello–Shredder, Splinter–Shredder, Casey–Krang, and Shredder–Krang. Four
contract into the band, while three different smoke-size outliers appear. The largest paired shifts
are Leonardo–Shredder and Leonardo–Bebop & Rocksteady at 20 points; three shift 15 points.

## Decision

Engine 0.5 is trustworthy enough to distinguish the six injected deck-profile priors from the
preserved card/gameplay model. Donatello and Krang strength survives neutralization. Leonardo's
weakness is partly injected, but its residual 44.4% result is too close to the smoke boundary to
authorize a card buff. Splinter's unmodified recovery also survives.

Cardcade is **not yet trustworthy enough to resume deck design**. Neutralizing deck-specific priors
does not explain the dominant outliers, so Prototype 0.3 would risk compensating decklists for coarse
generic-card modeling. The warranted next step is another engine-model correction: derive generic
spell roles and outcome values from actual card facts for all ten decks, then repeat this protocol.
