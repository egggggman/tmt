# Krang Round 6-B — Design Studio candidate gate

This is a Design Studio-owned pre-simulation candidate from OBL-BASELINE-003 after preservation of the rejected R6-A evidence. It is not a Cardcade design decision and not a promotion.

## OBL-R6-KRANG-B

Exact diff from Baseline 003 Krang:

- -1 Negate
- +1 Chrome Dome

No land, artifact-core, Utrom Scientists, or other shell changes. The deck remains 60 cards.

## Diagnosis

R6-A (-1 Negate; +1 Donatello, Turtle Techie) confirmed that activating a dormant Negate slot can improve Krang's severe diagnostics, but failed the distribution objective. Aggregate WR rose 35.33% to 40.11%, Shredder improved 12% to 17%, and Raphael 13% to 14%, while mean matchup balance error worsened 19.56% to 19.89%, >60/40 increased 6 to 7, and April moved 53% to 67% Krang-favored.

R6-B therefore changes mechanism from four-mana value conversion to cheap artifact-board stabilization.

Chrome Dome is a Standard-legal colorless two-mana 1/3 Artifact Creature — Robot Ninja. Other artifact creatures get +1/+0. Its five-mana activated copy ability is not required by this hypothesis.

It is selected because it can contribute earlier than Turtle Techie, directly preserves Krang's artifact/technology identity, does not add another ETB draw effect, and does not alter lands, the artifact core, Does Machines density, or high-end Krang density. Krang already contains four Utrom Scientists, so increasing that existing stun body is not legal.

## Falsifiable hypothesis

Replacing one dormant Negate with one Chrome Dome will improve Krang's early board resistance enough to move the severe Shredder and Raphael cells toward center while producing a smoother opponent distribution than R6-A.

Primary diagnostics:

- Shredder: Baseline 003 Krang 12%.
- Raphael: Baseline 003 Krang 13%.

Distribution guardrails:

- report mean matchup balance error;
- report >60/40 and >70/30 counts;
- April at 53% is an explicit anti-polarization sentinel after R6-A reached 67%;
- inspect Casey Jones and Leonardo for broad over-conversion;
- aggregate WR increase alone is not success.

Mechanism telemetry where supported:

- Chrome Dome casts;
- first-creature timing;
- battlefield presence at turns 3/5/7;
- artifact-creature power/toughness modifier observations or equivalent supported telemetry;
- interaction casts;
- first-player split and ending-turn distribution.

The hypothesis depends on the creature body and artifact-creature continuous modifier. The activated copy ability is not part of the success condition unless Cardcade independently confirms it is executed.

## Cardcade handoff

Cardcade receives the exact preserved candidate bytes in candidates/KRANG_OBL_R6_B.txt. It may validate the candidate, confirm semantic coverage, execute the controlled isolated test against the nine exact OBL-BASELINE-003 opponents, and report evidence. Cardcade must not change the list or originate a replacement card.

Use the established frozen 100-game-per-opponent structure with 50 starts per side and authenticated schedule/runtime. A staged diagnostic may be used only if predeclared and comparable. No candidate-vs-candidate cells, combined validation, baseline mutation, or promotion are authorized.

Return the evidence to Design Studio for accept, reject, or revise.
