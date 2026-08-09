# Cardcade Engine Contract

Cardcade is a bounded heuristic rehearsal system, not a Magic rules engine. It consumes frozen,
versioned deck profiles and emits reproducible observations and hypotheses. It does not edit
decklists or authorize Design Studio revisions.

## Engine 0.2

Engine `cardcade-0.2.0` adds:

- deterministic per-game random streams derived from seed, pairing, and game number;
- artifact setup, payoff, sequencing-hold, and affinity-mana telemetry;
- setup-before-payoff sequencing for artifact plans;
- capped affinity discounts;
- target-dependent interaction use and explicit dead-interaction telemetry;
- a versioned Engine 0.1-to-0.2 sensitivity-comparison artifact.

The artifact density values in `roster-0.1.json` are model inputs, not deck revisions. They remain
hypotheses until Cardcade derives card roles from deck/card data or real-game evidence validates
them.

## Protocol

Smoke is 20 games for each of 45 unique pairings: 900 games total. Every pairing splits the
starting player 10/10. A run is identified by engine version, seed, games per pairing, and roster
hash. Match records use schema `1.1.0`; run records use schema `1.1.0`.

Calibration is blocked whenever smoke evidence indicates the decision model is responsible for a
major aggregate or matchup shift. Cardcade reports the block and its hypotheses; it never changes a
Prototype deck.
