# Shredder Prototype 0.3

Status: **Provisional pre-balance candidate**

## Previous prototype

Prototype 0.1 remains preserved in `PROTOTYPE_0.1.md` and `PROTOTYPE_0.1.txt`. It contains 60
cards, 22 Swamp, 24 creatures, and 14 noncreatures.

## Exact change

- `-1 Super Shredder` (4 to 3)
- `+1 Stomped by the Foot` (3 to 4)

This is a two-card, single-lever swap. No other Shredder card, land, or prior prototype changed.

## Rationale

Calibration V1 recorded 75.53% over 36,864 games, with broad pressure across eight matchups above
55%. The Candidate Packet identified pressure/payoff redundancy as the narrowest credible problem.
Super Shredder is a two-mana legendary threat with menace that grows whenever another permanent
leaves the battlefield. Reducing one copy slightly lowers automatic early threat access without
removing the leave-battlefield or sacrifice identity.

The replacement is one additional Stomped by the Foot, already in the deck and card pool. It is a
conditional removal spell that can sacrifice an artifact or creature for a larger effect, so it
preserves ruthless interaction and creates recoverable counterplay rather than adding generic value.
It is less likely to reproduce the same snowball pattern because it does not create a growing threat.

## Structural effect

| Metric | Prototype 0.1 | Prototype 0.3 |
| --- | ---: | ---: |
| Lands | 22 | 22 |
| Creatures | 24 | 23 |
| Noncreatures | 14 | 15 |
| Average nonland mana value | 2.66 | 2.66 |
| Super Shredder | 4 | 3 |
| Stomped by the Foot | 3 | 4 |
| Artifact copies | 6 | 6 |
| Sacrifice-support copies | 3 | 4 |

The equal mana value keeps the curve unchanged. The change trades one creature for one instant and
slightly increases interaction while preserving the 60-card count and mana base.

## Identity preservation

Shredder remains ruthless, villainous, sacrifice-driven, interactive, and pressure-oriented. The
candidate does not remove the sacrifice themes, evasive threats, legends, or removal package. It
creates a little more opportunity for an opponent to recover instead of gutting the deck.

## Expected effect and risks

Expected effect: a modest reduction in repeated early Super Shredder starts and more access to
sacrifice-compatible removal, especially in matchups where a growing threat becomes difficult to
answer.

Risks: Stomped by the Foot may be weaker when no legal target or sacrifice is available; the deck
may lose too much early pressure in the Raphael control; and a single-copy change may not materially
move broad results. This is not a claim of statistical rebalancing.

## Smoke-test questions

- Does Shredder still pressure Raphael and Casey without automatic Super Shredder openings?
- Does the extra Stomped by the Foot create meaningful counterplay against Donatello and Casey?
- Are sacrifice decisions still ruthless rather than merely defensive?
- Does Shredder remain distinct from Splinter?
- Is there any catastrophic loss of early board presence?

Use the shared deterministic plan in `docs/design-studio/PROTOTYPE_0_3_PREBALANCE_SMOKE_PLAN.md`.
Smoke output is diagnostic only. Human play, not smoke win rate, determines refinement.

## Refinement gate

Human play will determine whether the candidate preserves Shredder's identity, recoverability, and
fun. No further change is authorized by this file.
