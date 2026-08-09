# Cardcade Engine Contract

Cardcade is a bounded heuristic rehearsal system, not a Magic rules engine. It consumes frozen,
versioned deck profiles and emits reproducible observations and hypotheses. It does not edit
decklists or authorize Design Studio revisions.

## Engine 0.3

Engine `cardcade-0.3.0` replaces profile-wide artifact guesses with versioned facts derived from the
project card database and frozen decklists. Only cards whose rules text says "Affinity for
artifacts" receive a discount, colored mana floors are preserved, and artifact permanents, token
makers, and payoffs have distinct roles. Full role counts remain telemetry, while scoring awards
bounded setup/payoff milestones so repeated pieces cannot create unbounded value.

Engine 0.3 also reports affinity spells cast, discount-event rate, mana value cast, and mana
actually paid. The card facts are stored in `card-model-0.3.json`; the simulator does not require
the local generated database at run time.

## Engine 0.2 history

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
hash. Engine 0.3 match and run records use schema `1.2.0`.

Calibration is blocked whenever smoke evidence indicates the decision model is responsible for a
major aggregate or matchup shift. Cardcade reports the block and its hypotheses; it never changes a
Prototype deck.
