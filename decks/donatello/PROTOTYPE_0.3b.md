# Donatello Prototype 0.3b

Status: **Provisional conversion candidate; not final balance**

## Parent prototype

Prototype 0.3a is preserved in [`PROTOTYPE_0.3a.md`](PROTOTYPE_0.3a.md) and
[`PROTOTYPE_0.3a.txt`](PROTOTYPE_0.3a.txt). This candidate is a new preserved revision. It does
not overwrite Prototype 0.1, Prototype 0.2, Prototype 0.3, or Prototype 0.3a.

## Authorization source

This candidate is authorized by
[`DONATELLO_POST_FLYING_PREBALANCE_REVIEW.md`](../../docs/design-studio/DONATELLO_POST_FLYING_PREBALANCE_REVIEW.md),
which classified ownership as `MIXED_BUT_DECK_REVISION_JUSTIFIED` and selected
`AUTHORIZE_DONATELLO_P0_3B`. The authorization permits a maximum four-card change, preferably one
coherent two-card conversion lever, with no land changes.

## Exact swap

From Prototype 0.3a:

- `-2 Sewer-veillance Cam` (4 to 2)
- `+2 Utrom Scientists` (0 to 2)

No lands, Does Machines copies, Donatello's Technique copies, or other cards changed.

## Candidate-selection analysis

The authoritative Standard snapshot was reviewed for low-cost artifact creatures and artifact-based
tempo bodies. The principal candidates were:

| Candidate | Cost / body | Relevant text and coverage | Assessment |
| --- | --- | --- | --- |
| **Utrom Scientists** | `{2}{U}`, 2/2 artifact creature | “When this creature enters, tap up to one target creature and put a stun counter on it.” ETB tap/stun is already exercised by Cardcade tests. | **Selected:** immediate stabilization, artifact entry, mono-blue fit, and high semantic fidelity. |
| Ravenous Robots | `{1}{R}`, 2/1 artifact creature | Cast-artifact token trigger and token haste activation. | Rejected: off-color and its important token/activation package is not the cleanest supported slice. |
| Mouser Mark III | `{1}{U/R}`, 2/3 artifact creature | Cannot attack without another artifact. | Rejected: hybrid identity and its attack restriction adds less immediate interaction than Utrom's ETB. |
| Mechanized Ninja Cavalry | `{1}{R/W}`, 1/1 artifact creature | ETB creates a 1/1 Robot artifact token. | Rejected: off-color hybrid mana and lower immediate stabilizing body. |
| Mouser Foundry | `{1}{R}`, artifact | ETB/LTB token creation and an expensive damage activation. | Rejected: off-color and not a creature body without relying on token behavior. |
| Chrome Dome | `{2}`, 1/3 artifact creature | Static artifact-creature boost plus an expensive copy activation. | Rejected: defensive but delayed payoff; no immediate tempo effect. |

Utrom Scientists is the cleanest combination of early stabilization, artifact-entry density, pressure
through an additional body, semantic fidelity, and Donatello's technical identity. Its three-mana
cost also fits the deck's existing blue mana base. Its ETB can tap an opposing attacker or blocker and
stun it, creating a real battlefield consequence while triggering Way with Machines when Way is
present.

## Named problem

The post-Flying smoke showed a functioning engine but weak conversion: 43/102 losses occurred before
Does Machines was cast, 46/102 reached level 2 and still lost, and Way with Machines appeared in 41
losses but attacked in only 8. The current setup/value package therefore often fails to become
immediate battlefield pressure. Preserved losses also contained no observed Donatello casts of
Sewer-veillance Cam.

## Conversion hypothesis

Replacing two delayed utility slots with Utrom Scientists tests whether an artifact body with an
immediate ETB tempo effect can bridge setup/value into battlefield impact. It should add blockers,
create additional qualifying artifact entries for Way with Machines, and make it easier to survive
long enough for Does Machines recovery to matter. This is a two-card experiment, not a generic power
increase and not an attempt to add more card draw.

## Identity preservation

The candidate remains mono-blue and artifact-centered. Utrom Scientists is an artifact creature with
an invention/technology identity and a precise tap/stun tool, so the change strengthens Donatello's
setup-to-board conversion without turning the deck into generic blue control. Two Sewer-veillance Cam
copies remain, and the Does Machines / Technique / Way package is unchanged.

## Expected benefits

- Earlier access to a meaningful artifact body.
- More blockers against aggressive openings.
- Immediate tap/stun interaction rather than delayed card advantage alone.
- More artifact entries for Way with Machines counters.
- A supported ETB that can create a real opening for attacks or preserve a favorable board.

## Risks and tradeoffs

- Two fewer Sewer-veillance Cam copies reduce artifact utility, tap/untap support, and the deck's
  delayed draw-two option.
- Three mana may still be too slow against the fastest starts.
- A 2/2 body is not a standalone closer and may not solve late-game conversion.
- The ETB target choice is subject to Pilot behavior; human play may value timing differently.
- A two-copy sample cannot establish balance or prove causation from a single smoke.

## Semantic-coverage suitability

Utrom Scientists is recognized by the authoritative card data and Standard-legal. Its artifact-creature
entry is already within the supported permanent-entry surface, and its ETB tap/stun behavior has focused
Cardcade coverage. No Cardcade semantic change is required for this candidate. The existing Flying,
Way with Machines, Does Machines, and Technique work remains unchanged.

## Structural composition

| Category | Prototype 0.3a | Prototype 0.3b |
| --- | ---: | ---: |
| Total cards | 60 | 60 |
| Lands | 23 | 23 |
| Creatures | 21 | 23 |
| Noncreatures | 16 | 14 |
| Artifacts | 14 | 14 |
| Early creatures/bodies (mana value 1–3) | 17 | 19 |
| Average nonland mana value | 2.432 | 2.541 |
| Sewer-veillance Cam | 4 | 2 |
| Utrom Scientists | 0 | 2 |

The artifact count remains unchanged because both the cut card and addition are artifacts. The creature
count rises by two and noncreatures fall by two; lands are unchanged.

## Next-smoke questions

Use the same frozen six-matchup schedule in a separate validation step. Ask:

- Does Utrom Scientists appear early enough to improve survival against Shredder, Raphael, and Casey Jones?
- Does its ETB tap/stun effect create observable stabilization or profitable attacks?
- Does the extra artifact-entry density increase Way with Machines counters and, importantly, attacks?
- Does reducing Cam density hurt recovery, artifact utility, or card flow more than the added bodies help?
- Does Donatello still preserve an inventive artifact-network identity?

Do not interpret movement in a single 40-game pairing as calibrated win-rate evidence.

## Provisional status

Prototype 0.3b is a preserved diagnostic candidate, not final balance. This PR does not run the smoke,
modify Cardcade semantics, alter any other deck, or authorize Prototype 0.4.
