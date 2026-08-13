# Cardcade Engine Contract

Cardcade is a bounded heuristic rehearsal system, not a Magic rules engine. It consumes frozen,
versioned deck profiles and emits reproducible observations and hypotheses. It does not edit
decklists or authorize Design Studio revisions.

## Engine 0.7 executable foundation (development)

Engine `cardcade-0.7.0-alpha.4` is an isolated rules-grounded foundation; it does not replace or
reinterpret the preserved Engine 0.1–0.6 heuristic evidence. It provides deterministic two-player
state, basic turn/land/mana/casting rules, stateful creatures with actual base power/toughness,
separate counter and continuous-modifier state, cleanup-expiring and persistent derived P/T
effects, reusable typed counter placement and derived +1/+1-counter characteristics,
Oracle-derived power-based blocking restrictions shared by block generation and validation, basic
combat, reusable state-based actions including the legend rule, two safely grounded target-aware
interactions, actual loss conditions and an auditable event log. Acceptance Match #001 loads the
frozen Leonardo and Raphael Prototype 0.1 files directly.

Unsupported card semantics are skipped and recorded rather than assigned invented value. See
`docs/cardcade/RULES_COVERAGE_0.7.md` for the exact coverage boundary. This is deterministic-test
and focused-acceptance work only; it does not pass the trust gate for a 900-game smoke.

## Engine 0.6 generic card-fact modeling

Engine `cardcade-0.6.0` loads the actual 60 frozen cards for every deck and derives generic roles
from versioned mana costs/values, type lines, Oracle text, and keywords. The same facts always yield
the same role units regardless of deck or character identity. All six Engine 0.5 profile priors
remain inspectable but no longer affect classification, line choice, or outcomes. Artifact
sequencing is enabled by card facts rather than `artifact_plan`; affinity still requires actual
Affinity rules text and respects the colored-mana floor.

Card-derived values are card identity/count, mana data, type and text facts, roles, role-unit events,
artifact setup/payoff facts, and affinity eligibility. Universal heuristics remain for role-unit
magnitudes, scoring weights, line-choice look-ahead, artifact milestones, interaction target caps,
starting-player advantage, mulligan penalty, and closing variance. They are not fitted to outcomes.

Smoke 0.6 preserves the exact 900-game protocol but fails the stability gate with 18 matchups over
15 points. Zero observed tempo and finisher use identifies the next correction: richer rules-text
semantics and magnitude modeling, including quantities, conditions, modal/triggered effects,
creature combat contribution, and target/relevance handling. Prototype 0.3 remains unauthorized.

## Engine 0.5 profile-strength audit

Engine `cardcade-0.5.0` makes all six deck-varying, non-card-derived numeric priors inspectable and
supports paired baseline, neutralized, isolated-field, and bounded-deviation conditions. Neutralized
values are roster means and are never fitted to outcomes. Per-match score telemetry separates board,
mana, support, interaction, artifact, affinity, mulligan, starting-player, and variance terms.

The audited fields are `creature_rate`, `interaction_rate`, `board_value`, `mana_value`,
`support_value`, and `interaction_value`. Card-derived artifact roles/costs, payoff sequencing,
affinity floors, and target-limited interaction behavior remain intact. See
`runs/profile-strength-audit-0.5/REPORT.md` for results and the resulting design freeze.

## Engine 0.4

Engine `cardcade-0.4.0` replaces forced artifact sequencing with a comparison of every legal cast,
a resource-preservation option, and one-step look-ahead across alternative sequences. Decisions
weigh immediate board or utility value, delayed setup value, payoff readiness and board relevance,
mana efficiency, affinity savings, and the opportunity cost of consuming scarce resources. An
artifact tag is evidence for evaluation, never an instruction to pursue that line.

Casting a payoff and realizing its artifact value are separate events. Match telemetry records
legal and rejected lines, chosen reasons, rejected payoff lines, resource-preservation holds, and
realized payoffs. Engine 0.4 retains the Engine 0.3 card-derived roles and affinity rules.

Promotion requires software validation, credible explanatory telemetry, and no unexplained matchup
movement greater than 15 percentage points from the immediately preceding engine under the same
seeded smoke protocol. A shift of exactly 15 points does not exceed this gate.

## Engine 0.3 history

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
hash. Engine 0.4 match and run records use schema `1.3.0`.

Calibration is blocked whenever smoke evidence indicates the decision model is responsible for a
major aggregate or matchup shift. Cardcade reports the block and its hypotheses; it never changes a
Prototype deck.
