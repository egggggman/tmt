# Donatello Prototype 0.3c Candidate Selection

Decision: **`P0_3C_CANDIDATE_SELECTION_BLOCKED`**

No Prototype 0.3c deck is created by this review. The authorized revision is
preserved as a decision to investigate, not converted into an unsupported or
illegal decklist.

## Authority and scope

The candidate search is authorized by
[the P0.3b failure review](DONATELLO_P0_3B_FAILURE_REVIEW.md), which recorded:

- ownership: `MIXED_BUT_DECK_REVISION_STILL_JUSTIFIED`;
- revision scale: `STRUCTURAL_4_CARD_REVISION`;
- next gate: `AUTHORIZE_DONATELLO_P0_3C`;
- maximum: four cards changed and no land changes.

The intended experiment is one coherent package testing both earlier supported
artifact presence and immediate supported tempo. Does Machines, Donatello's
Technique, and Donatello, Way with Machines are protected from cuts. No Cardcade
semantics or smoke run is authorized here.

The canonical sources inspected were:

- [`cardcade/scryfall-tmt-pza-tmc-2026-08-13.json`](../../cardcade/scryfall-tmt-pza-tmc-2026-08-13.json)
- [`cardcade/card-model-0.6.json`](../../cardcade/card-model-0.6.json)
- the current Cardcade interpreter and focused semantic tests.

## P0.3b lesson

P0.3b already supplied the cleanest apparently supported body candidate:

```text
-2 Sewer-veillance Cam
+2 Utrom Scientists
```

Utrom Scientists is `{2}{U}`, a 2/2 Artifact Creature, with:

> When this creature enters, tap up to one target creature and put a stun counter on it.

Cardcade cast and resolved it 55 times, produced 55 ETB tap/stun effects, and
recorded an average cast turn of 14.45. Donatello remained 15–105 in the frozen
P0.3b smoke. Repeating Utrom as the body half would not be a new test of the
critical-turn problem.

## Candidate analysis

| Candidate | Authoritative profile | Standard | Cardcade suitability | Decision |
| --- | --- | --- | --- | --- |
| **Mouser Mark III** | `{1}{U/R}`, 2/3 Artifact Creature — Robot. “This creature can't attack unless you control another artifact.” | Legal | Generic creature casting is available, but the attack restriction is not an executable supported card-specific mechanic. Treating it as an unrestricted attacker would overstate its conversion value. | Reject |
| **Chrome Dome** | `{2}`, 1/3 Artifact Creature — Robot Ninja. Other artifact creatures get +1/+0; `{5}` creates a temporary artifact copy. | Legal | The body can be recognized, but its static artifact-creature boost and copy ability are not both represented as executable behavior. Its important payoff would be silently omitted. | Reject |
| **Skateboard** | `{1}`, Artifact — Equipment. ETB taps a permanent; equipped creature gets +1/+0 and haste; equip `{1}`. | Legal | The authoritative card is recognized, but the ETB tap, attachment, and granted haste path are not a complete supported package for this smoke. | Reject |
| **Ravenous Robots** | `{1}{R}`, 2/1 Artifact Creature — Robot. Artifact-cast creates a Robot; `{R},{T}` grants token haste. | Legal | It is off-color for Donatello's Island-only mana base, and its most relevant token/haste package is not a clean mono-blue test. | Reject |
| **Mechanized Ninja Cavalry** | `{1}{R/W}`, 1/1 Artifact Creature — Robot Ninja. ETB creates a Robot artifact token. | Legal | Hybrid cost is off the deck's blue identity and the proposed package would rely on a non-blue mana symbol; the body is also a weak stabilizer. | Reject |
| **Mouser Foundry** | `{1}{R}`, Artifact. ETB/LTB creates a Robot; `{4}{R}` sacrifices it for 3 damage. | Legal | Off-color and not a creature body; its meaningful damage activation is not an early supported line. | Reject |
| **Ooze Spill** | `{2}{U}`, Instant. Counter target spell and create a Mutagen token. | Legal | This is a supported artifact-aligned tempo card and is the strongest interaction candidate. The list already has three copies, so legality allows only one additional copy. It cannot supply the two-card body half. | Partial fit |
| **Bespoke Bō** | `{2}{U}`, Artifact — Equipment. ETB returns a nonland permanent; equip grants +2/+1 and vigilance. | Legal | It is already present at two copies, and the bounce/equipment conversion is not sufficiently represented for a new four-card diagnostic. | Reject |
| **Utrom Scientists** | `{2}{U}`, 2/2 Artifact Creature with ETB tap/stun. | Legal | Fully exercised in P0.3b, but its average cast turn was 14.45 and it did not improve the smoke. | Reject as a new test |

## Why no package is authorized

The current list already has the maximum four copies of each straightforward,
supported blue artifact body that could be added without introducing a new card
mechanic: Fugitive Droid, Buzz Bots, and Crustacean Commando. Way with Machines is
explicitly protected. The remaining supported interaction, Ooze Spill, can rise
from three to only four copies under legal quantity limits.

The plausible new body candidates therefore fall into one of two unacceptable
categories:

1. **Repeat the failed experiment:** Utrom Scientists is supported, but P0.3b
   already established that its three-mana ETB body arrived too late and at too
   low a density to solve the shared problem.
2. **Create a semantic confound:** Mouser Mark III, Chrome Dome, or Skateboard
   could enter as generic permanents, but their relevant attack, static, tap,
   attachment, or haste behavior would be missing or incomplete. A smoke result
   would then measure an inaccurately executed card.

The only superficially tempting four-copy construction—two new artifact bodies
plus two Ooze Spill—would either exceed the four-copy Ooze Spill limit or require
additional cuts outside the authorized four-slot pool. A package using only
supported existing cards cannot add a new early body because their legal copies
are already at four.

Consequently, no candidate credibly tests both “early battlefield presence” and
“immediate supported tempo” while preserving Standard legality, mono-blue mana,
legal quantities, semantic fidelity, and the four-card budget.

## Preserved prototypes

No deck file was created or changed. P0.1, P0.2, P0.3, P0.3a, and P0.3b remain
the preserved history. No smoke was run, no other deck was touched, and no engine,
runtime, Pilot, or semantic code was modified.

## Next gate

The P0.3c authorization is blocked at candidate selection. The next responsible
choice is a separate Design Studio decision to either authorize a bounded semantic
slice for one carefully selected artifact body/tempo card, or revise the candidate
profile. That decision must precede any deck creation; this artifact does not
authorize Cardcade implementation, another deck revision, or a smoke run.
