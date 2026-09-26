# Casey Jones Prototype 0.3

Status: **Provisional pre-balance candidate**

## Previous prototype

Prototype 0.1 remains preserved in `PROTOTYPE_0.1.md` and `PROTOTYPE_0.1.txt`. It contains 60
cards, 22 Mountain, 23 creatures, and 15 noncreatures.

## Exact change

- `-1 Hard-Won Jitte` (4 to 3)
- `-1 Improvised Arsenal` (4 to 3)
- `+1 Mouser Foundry` (2 to 3)
- `+1 Spicy Oatmeal Pizza` (2 to 3)

This is a four-card, single-lever Equipment-payoff reduction. Gear access, creature carriers,
Manhole Missile, Vigilante randomness, lands, and prior prototypes are unchanged.

## Rationale

Calibration V1 recorded 68.19%, with broad strength against Leonardo, Michelangelo, and Splinter,
while Raphael and Shredder remained meaningful controls. The Candidate Packet identified redundant
Equipment payoff density as the safest pre-balance lever while treating attachment friction and
Casey-specific behavior as simulator-dependent.

Hard-Won Jitte and Improvised Arsenal are each reduced by one copy. This is the smallest direct
reduction of the eight-copy Equipment payoff package and does not touch Jury-Rig Justiciar's access
or the carrier base. Mouser Foundry and Spicy Oatmeal Pizza are already in Casey's deck and card
pool, remain artifacts, and preserve the scrappy artifact-board identity without being Equipment
payoffs. Mouser Foundry adds Robot production and late sacrifice interaction; Spicy Oatmeal Pizza
adds risky artifact-based damage and life pressure.

The replacements are less likely to reproduce the same balance issue because neither provides the
same repeatable Equipment scaling or double-strike payoff. They also avoid adding unrelated
goodstuff or introducing a second carrier/access lever.

## Structural effect

| Metric | Prototype 0.1 | Prototype 0.3 |
| --- | ---: | ---: |
| Lands | 22 | 22 |
| Creatures | 23 | 23 |
| Noncreatures | 15 | 15 |
| Average nonland mana value | 2.42 | 2.45 |
| Equipment copies | 8 | 6 |
| Artifact copies | 19 | 19 |
| Mouser Foundry | 2 | 3 |
| Spicy Oatmeal Pizza | 2 | 3 |

The average nonland mana value increases by approximately 0.03 because a two-mana Jitte and a
two-mana Arsenal are replaced by a two-mana Foundry and a three-mana Pizza. Creature/noncreature,
land, and total artifact counts remain unchanged. The change slightly trades early Equipment payoff
density for artifact tokens, risky damage, and late interaction without changing the carrier or
access package.

## Identity preservation

Casey remains scrappy, improvisational, gear-driven, risky, and aggressive. Jitte and Arsenal are
still present at three copies each, while the replacements are artifacts that fit the jury-rigged
junk-to-weapons plan. Casey remains distinct from Raphael because the deck still depends on carriers,
artifacts, equipment, and improvised resource conversion rather than team-wide pressure.

## Expected effect and risks

Expected effect: slightly fewer automatic Equipment payoff openings and more opponent recovery
windows against slower decks, while retaining artifact-board development and Casey's volatile damage
identity.

Risks: the reduction may be too small to matter; Spicy Oatmeal Pizza may increase burst or self-risk
in an unhelpful way; Mouser Foundry may create a different board-growth pattern; and attachment
semantics may still dominate the observed result. This is a provisional starting environment, not a
claim of statistical balance.

## Smoke-test questions

- Does Casey remain competitive against Shredder and Raphael controls?
- Are Equipment draws less automatic without becoming cumbersome?
- Are there still enough carriers and memorable gear decisions?
- Do Mouser Foundry and Spicy Oatmeal Pizza preserve the scrappy artifact feel?
- Do sudden kills feel fair, and can opponents recover?
- Does Casey remain distinct from Raphael?

Use the shared deterministic plan in `docs/design-studio/PROTOTYPE_0_3_PREBALANCE_SMOKE_PLAN.md`.
Smoke output is diagnostic only. Human play, not smoke win rate, determines refinement.

## Refinement gate

Human play will determine whether the Equipment reduction improves fun, counterplay, and Casey's
identity. No further change is authorized by this file.
