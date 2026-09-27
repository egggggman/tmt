# Donatello Prototype 0.3c

Status: **Provisional conversion candidate; not final balance**

## Parent prototype

Prototype 0.3c uses Donatello Prototype 0.3b as its immediate parent. P0.3b
remains unchanged, as do P0.1, P0.2, P0.3, and P0.3a.

## Authorization chain

This candidate follows the ownership and revision authorization in
[`DONATELLO_P0_3B_FAILURE_REVIEW.md`](../../docs/design-studio/DONATELLO_P0_3B_FAILURE_REVIEW.md),
the blocked-state record
[`DONATELLO_P0_3C_CANDIDATE_SELECTION_BLOCKED.md`](../../docs/design-studio/DONATELLO_P0_3C_CANDIDATE_SELECTION_BLOCKED.md),
and the semantic-enabler decision
[`DONATELLO_P0_3C_SEMANTIC_ENABLER_REVIEW.md`](../../docs/design-studio/DONATELLO_P0_3C_SEMANTIC_ENABLER_REVIEW.md).
Mouser's implementation is documented in
[`DONATELLO_MOUSER_MARK_III_SEMANTIC_COVERAGE.md`](../../docs/design-studio/DONATELLO_MOUSER_MARK_III_SEMANTIC_COVERAGE.md).

The decision was `AUTHORIZE_DONATELLO_P0_3C`, with a maximum four-card change
and no land changes.

## P0.3b failure and candidate-selection blocker

P0.3b replaced two Sewer-veillance Cam copies with two Utrom Scientists. The
card was exercised, but the frozen smoke remained 15--105 for Donatello
(P0.3a was 18--102). Its three-mana body averaged a turn-14.45 cast, so the
experiment did not address the critical early turns.

P0.3c was previously blocked because the available early artifact candidates
were not simultaneously Standard-legal, mono-blue castable, immediately useful,
and faithfully represented. The Mouser semantic-enabler review resolved that
specific blocker without authorizing broader Cardcade work.

## Exact revision

Relative to P0.3b, this candidate applies exactly:

- `-2 Sewer-veillance Cam` (2 to 0)
- `-2 Return to the Sewers` (2 to 0)
- `+3 Mouser Mark III` (0 to 3)
- `+1 Ooze Spill` (3 to 4)

No other cards or lands changed. Does Machines, Donatello's Technique, and
Donatello, Way with Machines remain at 3, 2, and 3 copies respectively.

## Early-stabilization hypothesis

Three Mouser Mark III copies add genuine turn-two artifact bodies: `{1}{U/R}`
is payable with Island, and the 2/3 body can block normally even when no other
artifact is controlled. This tests whether Donatello can establish profitable
defense before spending multiple turns on setup and level advancement.

## Interaction-density hypothesis

The fourth Ooze Spill raises the existing supported interaction package to its
legal four-copy maximum. Together with Mouser's early body, this tests whether
Donatello can interact and stabilize while the artifact engine develops rather
than merely accumulating delayed value.

## Artifact identity preservation

Mouser Mark III is an Artifact Creature -- Robot and creates an artifact entry
for Way with Machines. Its restriction is preserved faithfully: it cannot attack
unless its controller controls another artifact, but it can block normally.
The change therefore increases early artifact presence without turning the deck
into generic blue control or removing the Does Machines / Technique / Way core.

## Mouser semantic suitability

The current runtime/card-data support confirms that:

- Islands can pay Mouser's `{U/R}` hybrid symbol;
- Mouser casts as a 2/3 artifact creature;
- it may block without another artifact;
- it cannot attack alone;
- it can attack once another controlled artifact exists;
- AcceptancePilot receives the engine's legal attacker set without a Mouser-
  specific strategy change.

No semantic or Pilot change is made in this Design Studio candidate PR.

## Expected benefits

- Earlier meaningful battlefield presence than Utrom Scientists.
- More profitable early blocks against aggressive opponents.
- Three additional artifact entries for Way with Machines.
- More interaction available before Does Machines reaches level 2.
- A direct test of setup/value to battlefield conversion.

## Risks and tradeoffs

- Removing all Return to the Sewers reduces recovery/reactive redundancy.
- Removing the remaining Sewer-veillance Cam copies reduces delayed utility and
  any supported Cam-specific value.
- Mouser's attack restriction can limit offense if the artifact board is empty.
- Four Ooze Spill copies may create reactive density without solving threat
  quality or mana-tempo conflicts.
- The package may improve survival without supplying a closer.
- A single frozen smoke remains directional evidence, not calibrated balance.

## Structural comparison: P0.3b to P0.3c

| Measure | P0.3b | P0.3c |
| --- | ---: | ---: |
| Total cards | 60 | 60 |
| Lands | 23 | 23 |
| Creatures | 23 | 26 |
| Noncreatures | 14 | 11 |
| Artifacts | 14 | 15 |
| Average nonland mana value | 2.541 | 2.514 |
| One-mana creature bodies | 4 | 4 |
| Two-mana creature bodies | 8 | 11 |
| Three-mana creature bodies | 7 | 7 |
| Interaction copies (Ooze Spill) | 3 | 4 |
| Artifact-body count | 10 | 13 |

Changed-card counts are: Sewer-veillance Cam 2 to 0, Return to the Sewers 2 to
0, Mouser Mark III 0 to 3, and Ooze Spill 3 to 4.

## Next-smoke questions

The next frozen smoke should measure:

- Mouser draws, casts/resolutions, and average first cast turn;
- games with Mouser cast by turns 2, 3, 4, and 5;
- Mouser blocks, attacks, direct combat damage, and attacks prevented by its
  restriction;
- Ooze Spill casts/resolutions and supported targets/counters;
- first creature and first meaningful blocker timing;
- Does Machines timing and level-2 timing;
- Way casts, attacks, and direct damage;
- Donatello matchup results against the unchanged held lists.

The primary comparison is P0.3a at `18--102` and P0.3b at `15--105`. The run
must preserve the existing frozen schedule and should not be interpreted as a
calibrated win-rate estimate.

## Provisional status

P0.3c is a preserved experiment, not final balance. This PR does not run the
smoke, modify Cardcade semantics, modify Pilot behavior, alter any other deck,
or authorize a later prototype.
