# Issue #289 — temporary granted death return

Draft checkpoint stacked on #343. Baseline 005's ten deck files, the original 172-row ledger, every earlier overlay, historical results and runtime identities are preserved. No calibration or balance run was launched.

## Selection and frozen authority

The three-copy Splinter instant **Pain 101** costs `{1}{B}` and reads: “Until end of turn, target creature gains deathtouch and ‘When this creature dies, return it to the battlefield tapped under its owner's control.’” Its single remaining important row represented the whole effect. Two-copy **Donatello, Gadget Master** has a combat-damage trigger that copies a targeted artifact you control; three-copy **Improvised Arsenal** has a paid ability that copies itself. The ledger represents those latter clauses twice each. Their common copiable-values and independent token model would still require separate combat-trigger targeting and Equipment activation paths. Pain 101 is a complete, bounded three-copy intervention using existing targeted spell, temporary keyword, death event and zone-incarnation machinery.

The four unbounded important effects remain open. Bebop's Rhino-wide menace, Leonardo's temporary pump/flying/scry, Michelangelo's combat-damage hand entry, and Michelangelo's counter-conditioned blocking limit all affect real combat or resources. Their score of 25 does not establish a credible upper bound; Bebop's shared keyword grant may be the next smaller intervention before the copy family. The eight remaining rows and family ranking are preserved in the readiness JSON.

## Executed rule and verification

A complete Oracle-fragment parser accepts the temporary deathtouch plus quoted self-death trigger only as one spell program. Incomplete companion clauses fail closed. Normal payment, priority and protection checks govern either player's target creature. Resolution grants the keyword and a bounded triggered ability to the selected incarnation. Ability loss after the grant suppresses both; cleanup expires both. A battlefield-to-graveyard transition captures the original controller, ability grant, departure authority and exact destination incarnation, including sacrifice and combat deaths. The granted ability is independent of the spell source. It returns that same card only if it is still in that graveyard incarnation at resolution, tapped under its owner. An exiled or otherwise moved card does not return. The returned permanent is a new object without the old temporary grants. No card or deck name dispatch implements these rules.

Focused tests use the frozen catalog spell and a renamed generic copy. They verify parser rejection, paid target selection, protected and invalid targets, target departure before resolution, control change and owner return, sacrifice death, graveyard response, ability suppression, cleanup, combat and deterministic replay. Full regression, Ruff, structural checks and final-head CI are recorded on the PR.

Six authenticated frozen Baseline 005 games used Splinter against Raphael, Bebop & Rocksteady, and Casey Jones in both seats. Each ran twice with identical full-result and pilot-observation digests. The pilot saw 45 legal cast offerings across stages, selected and cast Pain 101 three times, and each grant resolved. The diagnostic sample had zero qualifying post-grant deaths, so it observed zero granted death triggers or returns. Focused deterministic tests establish the full death-and-return path; the sample is **pilot exposure evidence, not a balance estimate**. An offering is a decision-stage observation, not a distinct card or game.

`ISSUE_289_DEATH_RETURN_CHECKPOINT.json` preserves all 172 identities and closes precisely the complete Pain 101 row. `ISSUE_289_DEATH_RETURN_CALIBRATION_READINESS.json` independently ranks the remaining risks. `ISSUE_289_DEATH_RETURN_SMOKE.json` stores frozen-game event and replay evidence. Reproducers are `tools/report_issue289_death_return.py` and `tools/run_issue289_death_return_smoke.py`.

## Gates

**Checkpoint acceptance: READY subject to successful final-head CI.** **Baseline 005 calibration readiness: BLOCKED.** No critical rows remain; eight important rows remain, comprising four identified artifact-copy ledger rows and four unbounded effects. The copy family is still unimplemented, and the four unbounded effects have no credible calibration bound. No deck revision, 4,500-game control, merge or promotion is authorized.
