# Raphael Prototype 0.3

Status: **Provisional pre-balance candidate**

## Previous prototype

Prototype 0.1 remains preserved in `PROTOTYPE_0.1.md` and `PROTOTYPE_0.1.txt`. It contains 60
cards, 22 Mountain, 24 creatures, and 14 noncreatures.

## Exact change

- `-2 Wingnut, Bat on the Belfry` (4 to 2)
- `+1 Null Group Biological Assets` (3 to 4)
- `+1 Cool but Rude` (3 to 4)

This is a four-card, single-lever swap aimed at early-pressure consistency. No land, finisher,
Manhole Missile, or prior prototype changed. Both replacements remain within the four-copy limit.

## Rationale

Calibration V1 recorded 74.52% over 36,864 games, with eight matchups above 55%. The Candidate
Packet identified broad aggressive success as mixed between real pressure consistency and
AcceptancePilot amplification. Wingnut is a cheap two-mana evasive pressure card whose attack
trigger also improves the rest of the attack. Reducing two copies lowers the density of immediate
evasive starts without removing Raphael's core confrontation plan.

The replacements are one additional Null Group Biological Assets and one additional Cool but Rude,
both already in the deck and card pool. Null Group Biological Assets preserves a creature body and
discard/draw smoothing; Cool but Rude rewards attacking while offering discard/draw selection and
later discard damage. Together they preserve Raphael's impulsive momentum and card velocity, but are
less likely to reproduce the same immediate body-plus-evasion pressure because they require combat,
choices, or a later payoff to convert into value.

## Structural effect

| Metric | Prototype 0.1 | Prototype 0.3 |
| --- | ---: | ---: |
| Lands | 22 | 22 |
| Creatures | 24 | 23 |
| Noncreatures | 14 | 15 |
| Average nonland mana value | 2.63 | approximately 2.66 |
| Wingnut, Bat on the Belfry | 4 | 2 |
| Null Group Biological Assets | 3 | 4 |
| Cool but Rude | 3 | 4 |
| Card-flow/selection copies | 14 | 16 |

The swap reduces early evasive creature density, adds one creature-based selection body and one
attack-based selection Class, preserves the 60-card count, and leaves the mana base and Nightwatcher
burst package unchanged. The small average-mana increase comes from replacing two MV2 creatures
with one MV3 creature and one MV2 noncreature.

## Identity preservation

Raphael remains fast, confrontational, momentum-oriented, and willing to trade long-term caution for
immediate pressure. Cool but Rude still asks Raphael to attack and turn aggression into volatile
card velocity. The candidate does not turn the deck into generic midrange or remove risky combat.

## Expected effect and risks

Expected effect: fewer automatic early evasive boards and slightly more pressure that must be earned
through attacks and discard choices, leaving opponents more recovery windows.

Risks: the deck may become less threatening when it does not draw Wingnut; Cool but Rude may be too
slow or may amplify attack decisions in a different way; and AcceptancePilot behavior may still
favor the resulting aggressive plan. Raphael's +2.62 percentage-point deck-specific seat delta
remains a diagnostic observation, not an engine conclusion.

## Smoke-test questions

- Does Raphael still establish a meaningful two-drop and attack early?
- Does the deck retain confrontation and risky momentum without four Wingnut copies?
- Does Cool but Rude create decisions rather than passive value?
- Are Nightwatcher endings still memorable rather than too abrupt?
- Does Raphael remain distinct from Leonardo and still pressure Casey?

Use the shared deterministic plan in `docs/design-studio/PROTOTYPE_0_3_PREBALANCE_SMOKE_PLAN.md`.
Smoke output is diagnostic only. Human play, not smoke win rate, determines refinement.

## Refinement gate

Human play will determine whether the candidate preserves Raphael's identity, fun, counterplay, and
recoverability. No further change is authorized by this file.
