# Krang Round 6 — Design Studio candidate gate

This is a **Design Studio-owned pre-simulation candidate**, not a Cardcade design decision and not a promotion. The exact parent is OBL-BASELINE-003 Krang, which retains `decks/krang/PROTOTYPE_0.2.txt`.

## OBL-R6-KRANG-A

Exact diff from Baseline 003 Krang:

- -1 Negate
- +1 Donatello, Turtle Techie

No land, artifact-core, or other shell changes. The deck remains 60 cards.

## Diagnosis

Baseline 003 carries forward Krang's severe Shredder matchup at 12/88, with Raphael also strongly favored over Krang. Round 5 established that Negate was dormant in the authenticated parent samples and that converting both Negate slots to active artifact-linked bodies is a real lever.

R5-A (-2 Negate; +2 Mouser Mark III) raised Krang's WR but worsened mean matchup balance error and increased extreme matchups. R5-B (-2 Negate; +2 Donatello, Turtle Techie) improved WR and mean balance error but still increased >60/40 extremes from 6 to 8 and was not promotion-eligible after Combined 004.

## Falsifiable hypothesis

A one-copy Turtle Techie intervention will capture part of R5-B's useful midgame conversion without reproducing the two-copy candidate's matchup polarization.

Primary observables:

- Krang vs Shredder, with 12% Krang WR as the Baseline 003 reference.
- Krang vs Raphael, with 13% Krang WR as a secondary diagnostic.
- aggregate Krang WR and mean matchup balance error.
- strict >60/40 and >70/30 matchup counts.
- first-player result and ending-turn distribution.
- first-creature and turn-3/5/7 battlefield-presence proxies where available.
- Donatello, Turtle Techie signature casts and supported ETB artifact-draw telemetry where emitted.

Success is **not** defined as simply increasing Krang's aggregate WR. A useful candidate must move the severe weak matchups toward center without creating compensating extreme favorable matchups.

## Cardcade handoff

Cardcade receives the frozen candidate bytes in `candidates/KRANG_OBL_R6_A.txt`. Cardcade may validate, execute the controlled test, report telemetry, and compare against OBL-BASELINE-003. Cardcade must not alter the candidate or originate replacement card choices.

Run the candidate independently against the nine exact OBL-BASELINE-003 opponents using the established frozen 100-game pairing structure with 50 starts per seat and the authenticated schedule/runtime required by the current OBL authority. Do not regenerate or modify Baseline 003. Do not run candidate-vs-candidate cells.

After results, return evidence to Design Studio for accept/reject/revise. No combined validation or promotion is authorized by this artifact.
