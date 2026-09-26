# Donatello Prototype 0.3a

Status: **Provisional recovery candidate; not final balance**

## Parent prototype

Prototype 0.3 remains preserved in [`PROTOTYPE_0.3.md`](PROTOTYPE_0.3.md) and
[`PROTOTYPE_0.3.txt`](PROTOTYPE_0.3.txt). This candidate is a new preserved revision authorized by
[`PROTOTYPE_0_3_SMOKE_REVIEW.md`](../../docs/design-studio/PROTOTYPE_0_3_SMOKE_REVIEW.md); it does
not overwrite Prototype 0.3, Prototype 0.2, or Prototype 0.1.

## Exact change

From Prototype 0.3:

- `-2 Return to the Sewers` (4 to 2)
- `+2 Donatello's Technique` (0 to 2)

No lands, creatures, Does Machines copies, or other noncreature cards changed.

## Smoke evidence

The authorized change responds to the completed Prototype 0.3 pre-balance smoke review. The fixed
240-game smoke completed 238 games, with 0 malformed results, 0 draws, 0 turn-cap outcomes, and 2
runtime failures preserved without retry. Donatello completed all 120 scheduled games but recorded
18–102 across the three pairings: Shredder 5–35, Raphael 5–35, and Casey Jones 8–32. These are
directional smoke observations only, not calibrated win rates. The two runtime failures did not
involve Donatello and remain a separate Cardcade triage item.

The review's decision is `AUTHORIZE_DONATELLO_RECOVERY_REVISION`, with the exact authorized shape
`-2 Return to the Sewers / +2 Donatello's Technique`. P0.3a is therefore a diagnostic candidate,
not an automatic balance correction.

## Recovery hypothesis

Prototype 0.3 restored proactive setup and component recovery to three Does Machines, but left
Donatello with zero Technique and four Return to the Sewers. The smoke indicates that setup access
alone did not provide enough setup-to-payoff or closing conversion. Return to the Sewers is a
reactive answer/recovery card that depends on an opposing target and timing window; four copies may
leave too much reactive density relative to proactive conversion in the represented Pilot.

Restoring two Technique copies tests whether an unblocked route can convert the prepared artifact
network into cards and a closing advantage. It is one narrow lever, not a claim that every Return
copy is undesirable or that simulator output establishes a true target win rate.

## Identity rationale

Donatello remains inventive, technical, proactive, and artifact-network driven. Does Machines finds
and recovers components; Technique turns a successful prepared route into additional options. The
candidate restores the P0.1 setup/payoff/recovery shape without adding generic power, altering the
mana base, changing creatures, or turning Donatello into passive draw-go control.

## Risks and tradeoffs

- Two fewer Return to the Sewers copies reduce reactive answers and Mutagen-producing recovery.
- Technique may recreate repetitive or overly automatic setup-to-payoff conversion.
- The Pilot may not choose attack routes, timing, or closing lines as a human would.
- Pressure matchups may still expose a creature, tempo, or simulator limitation that this swap does
  not solve.

The candidate must be evaluated for meaningful decisions, stabilization, closing conversion, and
identity—not for movement toward a numerical 50% result.

## Structural composition

| Category | Count |
| --- | ---: |
| Total cards | 60 |
| Lands | 23 |
| Creatures | 21 |
| Noncreatures | 16 |
| Does Machines | 3 |
| Donatello's Technique | 2 |
| Return to the Sewers | 2 |
| Negate | 0 |

## Next-smoke questions

Use the same frozen six-matchup smoke schedule after the separate runtime fix and independent
validation. Ask:

- Does Donatello still assemble its artifact network reliably?
- Does Technique create meaningful setup-to-payoff and closing choices?
- Does reducing Return density make reactive cards less stranded without losing needed answers?
- Can Donatello stabilize and close more often against Shredder, Raphael, and Casey Jones?
- Does the deck remain inventive and distinct from generic blue control?
- Does the candidate remain functional when the runtime failure path is corrected?

If the environment is reasonably functional, move to balanced human play rather than continuing
simulator optimization. Human play determines whether this candidate is fun, clever, recoverable,
and ready for any later decision.

## Provisional status

Prototype 0.3a is a preserved, provisional recovery candidate. It is not final balance, does not
authorize Prototype 0.4, and does not authorize further card changes. Prototype 0.1, Prototype 0.2,
and Prototype 0.3 remain unchanged and preserved.
