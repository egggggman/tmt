# Donatello Prototype 0.3

Status: **Provisional pre-balance candidate**

## Previous prototype

Prototype 0.2 remains preserved in `PROTOTYPE_0.2.md` and `PROTOTYPE_0.2.txt`. It contains 60
cards, 23 Island, 21 creatures, and 16 noncreatures. Prototype 0.2 itself remains the preserved
result of the earlier `-2 Does Machines / -2 Donatello's Technique / +2 Negate / +2 Return to the
Sewers` intervention from Prototype 0.1.

## Exact change

- `-2 Negate` (2 to 0)
- `+2 Does Machines` (1 to 3)

This is a four-card, single-lever partial reversal that restores proactive artifact-engine
reliability. No creature, land, artifact setup body, or Return to the Sewers copy changed.

## Rationale

Calibration V1 recorded 36.57%, while the prior calibration identified repeated setup-to-payoff
conversion as a reliability concern in the opposite direction. The Candidate Packet found that
Prototype 0.2 may have exchanged proactive engine pieces for reactive cards that AcceptancePilot
does not exploit like a human. Does Machines selects and recovers components and can turn a prepared
artifact into a growing threat; Negate requires a timely opposing noncreature spell and a decision to
hold mana.

Restoring Does Machines from one copy to three and removing the two Negates is the smallest direct
restoration of the intervention's proactive engine lever. It is not generic power: it restores
Donatello's stated artifact assembly, recovery, and setup-to-payoff identity. It also avoids adding
more reactive answers that may remain underused by the Pilot.

## Structural effect

| Metric | Prototype 0.2 | Prototype 0.3 |
| --- | ---: | ---: |
| Lands | 23 | 23 |
| Creatures | 21 | 21 |
| Noncreatures | 16 | 16 |
| Average nonland mana value | 2.43 | 2.43 |
| Does Machines | 1 | 3 |
| Negate | 2 | 0 |
| Artifact setup pieces | 14 | 14 |
| Counterspells | 2 | 0 |

Both cards have mana value two, so the average curve and mana base remain unchanged. The artifact
count remains unchanged because Does Machines is a Class rather than an artifact; the relevant change
is proactive selection/recovery versus reactive counterspell access. The deck remains 60 cards.

## Identity preservation

Donatello remains inventive, technical, artifact-network driven, and adaptable. Does Machines asks
the player to find the component that solves the board rather than simply draw-go. The candidate does
not add generic threats, remove the artifact network, or turn Donatello into a passive counterspell
deck.

## Expected effect and risks

Expected effect: more reliable access to artifacts and payoff pieces, better recovery after an
artifact is lost, and more opportunities to convert preparation into a closing board.

Risks: restoring Does Machines may recreate too much automatic setup-to-payoff conversion; removing
Negate may reduce protection against noncreature answers; and the Pilot may still fail to use
selection/recovery intelligently. The low V1 result remains simulator-confounded and this swap is
not a claim that Donatello should be numerically corrected to 50%.

## Smoke-test questions

- Does Donatello assemble an artifact network earlier without becoming automatic?
- Does Does Machines provide meaningful component choices and recovery?
- Can the deck stabilize Raphael, Shredder, and Casey more often?
- Does it convert stabilization into a win rather than only generate value?
- Is the deck still inventive and distinct from generic blue control?

Use the shared deterministic plan in `docs/design-studio/PROTOTYPE_0_3_PREBALANCE_SMOKE_PLAN.md`.
Smoke output is diagnostic only. Human play, not smoke win rate, determines refinement.

## Refinement gate

Human play will determine whether proactive restoration is fun, clever, and sufficiently recoverable,
and whether any reactive protection must return. No further change is authorized by this file.
