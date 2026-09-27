# Donatello Prototype 0.3b Failure Review

Status: focused Design Studio analysis; no deck or Cardcade change is made by this
artifact.

## 1. Evidence chain

This review uses the authenticated P0.3b deck, the preserved frozen smoke, and the
prior post-Flying loss analysis:

- [P0.3b smoke review](PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3B_REVIEW.md)
- [P0.3b smoke results](PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3B_RESULTS.md)
- [P0.3b event evidence](PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3B_EVIDENCE.json.gz)
- [P0.3a post-Flying review](PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3A_POST_FLYING_REVIEW.md)
- [P0.3a semantic coverage record](DONATELLO_P0_3A_SEMANTIC_COVERAGE.md)
- [P0.3a post-Flying Design Studio review](DONATELLO_POST_FLYING_PREBALANCE_REVIEW.md)

The P0.3b smoke completed all 240 scheduled games with zero runtime errors,
malformed games, draws, or turn caps. Its matchup results were identical to the
P0.3a post-Flying baseline:

| Matchup | P0.3a | P0.3b |
| --- | ---: | ---: |
| Shredder / Donatello | Donatello 7–33 | Donatello 7–33 |
| Raphael / Donatello | Donatello 4–36 | Donatello 4–36 |
| Casey Jones / Donatello | Donatello 7–33 | Donatello 7–33 |
| Aggregate | Donatello 18–102 | Donatello 15–105 |

The aggregate difference is caused by the unchanged Donatello pairings plus the
changed deck aggregate accounting; it is not a matchup improvement. The direct
Shredder/Raphael/Casey pairings remained stable.

## 2. P0.3b hypothesis

P0.3b tested one coherent conversion hypothesis:

```text
-2 Sewer-veillance Cam
+2 Utrom Scientists
```

The intended mechanism was that earlier supported artifact bodies would stabilize
the battlefield, add artifact entries for Way with Machines, and turn setup/value
into pressure without changing Donatello's invention identity.

The card was represented and used. Across the 120 Donatello games, Utrom Scientists
was recorded 110 times in draws, cast 55 times, resolved 55 times, and produced 55
ETB tap/stun effects against 55 targets. It attacked 35 times and dealt 56 direct
combat damage. The experiment therefore tested the intended semantic surface; it
did not fail because Utrom was wholly inert.

## 3. Why it failed

The primary failure classification is:

`MIXED`

The swap improved activity but not the conversion bottleneck. It combined several
weaknesses:

- **Too late and too low-density:** Utrom was cast on average on turn 14.45. It was
  drawn in 74 of 120 games with a draw record but cast in only 44 games, so the two
  copies rarely affected the critical opening turns.
- **Insufficient interaction:** tap/stun was real but usually arrived after the
  opponent had already established pressure. Prior preserved loss records contain
  no casts of Ooze Spill, Return to the Sewers, Bespoke Bō, or Sewer-veillance Cam;
  this is an observed-use signal, not proof that every copy was drawn or legal.
- **Insufficient threat conversion:** Does Machines, recovery, Way triggers, and
  direct damage all increased, but the result stayed unchanged. Value was generated
  more reliably than a protected attacker, a profitable trade, or lethal pressure.
- **Mana-tempo conflict:** more Does Machines casts and level-two advancements are
  not automatically beneficial if those turns displace bodies or stabilization.
  In the prior loss analysis, 46 of 102 losses had already reached level 2 and
  still lost.

The experiment therefore does not validate a simple “add an early body” fix. It
shows that the deck needs a more structural improvement to the path from mana and
cards into board control and closing pressure.

## 4. Timing analysis

P0.3b did improve the average first-creature record from turn 4.19 to 3.69, but it
did not change the average first-artifact-entry turn, which remained 3.56. Utrom's
own average cast turn of 14.45 is the more important measure: it was not functioning
as an early stabilizer in most games.

The card was not merely absent. Of the 74 games with a Utrom draw record, only 44
had a game with a Utrom cast record. The remaining gap can reflect hand timing,
mana sequencing, competing legal plays, or Pilot priorities; the preserved log
does not establish one exclusive cause. Regardless of cause, two copies did not
provide enough critical-turn density.

The first Donatello creature being earlier did not produce an earlier first artifact
entry or a better result. This separates “first body exists” from “first body
stabilizes the game.”

## 5. Interaction analysis

Donatello's nominal interaction/stabilization package remains delayed or conditional:

- 3 Ooze Spill
- 2 Bespoke Bō
- 2 Return to the Sewers
- the removed Cam copies in the P0.3a parent
- Utrom Scientists as the P0.3b ETB tap/stun body

In preserved P0.3a losses, event records show 44 Technique casts, 79 Does Machines
casts, and 56 Way casts, but zero recorded casts for Ooze Spill, Return to the
Sewers, Bespoke Bō, or Sewer-veillance Cam. The absence is underdetermined: a card
may not have been drawn, may not have been legal, or may not have been selected.
It nevertheless means the list did not demonstrate reliable reactive tempo when
losing.

Utrom's 55 tap/stun resolutions demonstrate that the replacement supplied a real
interaction event. Its average cast turn and the unchanged matchups indicate that
the event usually bought too little time, too late. The likely missing axis is not
another value engine; it is earlier, repeatable ability to remove, neutralize, or
profitably block opposing threats.

## 6. Threat-quality analysis

P0.3b produced more engine activity than P0.3a:

| Measure | P0.3a | P0.3b |
| --- | ---: | ---: |
| Does Machines casts | 96 | 121 |
| Level-two advancements | 77 | 92 |
| Way triggers/counters | 26 | 40 |
| Way direct damage | 149 | 190 |

Those increases are material evidence that the deck was doing more, not less. They
also expose the conversion problem: more Way damage did not create more wins, and
the three Donatello matchup records did not move.

The 21-creature package contains setup- and support-oriented bodies as well as
pressure pieces. Way with Machines is the principal scalable evasive closer, which
places too much closing responsibility on a single payoff. In the prior loss
evidence, Way appeared in 41 losses but attacked in only 8. A payoff that is on the
battlefield but rarely attacks is not yet a reliable closer, even when its counters
and Flying are correctly represented.

The problem is therefore not simply creature count. It is the quality, timing, and
survivability of bodies that must bridge setup into combat.

## 7. Mana-tempo analysis

Does Machines setup, level advancement, artifact recovery, Technique, and Way all
consume turns and mana before they create pressure. P0.3b increased Does casts from
96 to 121 and level-two advancements from 77 to 92, while Way triggers rose from 26
to 40. That is positive engine execution but also confirms that a larger share of
games invested in the engine without a corresponding outcome change.

The prior loss analysis provides the clearest boundary: 43 of 102 losses ended
before Does Machines was cast, 13 cast it without reaching level 2, and 46 reached
level 2 and still lost. Thus the deck has both an access/tempo failure and a
post-engine conversion failure. Adding a late body does not resolve either one
reliably.

The next revision should reduce the opportunity cost of setup rather than add more
card selection. It should test whether the same mana curve can establish a board
that blocks, attacks, or removes threats while the artifact engine develops.

## 8. Matchup-specific analysis

The same structural problem appears against all three opponents, so a matchup-only
intervention is not justified.

- **Shredder:** Donatello remained 7–33. The prior loss sample included games lost
  before Does Machines and games in which level 2 completed without enough Way
  pressure. Shredder therefore tests both early survival and closing.
- **Raphael:** Donatello remained 4–36, the clearest speed failure. Eighteen of the
  36 prior losses ended before a Does cast, and the average loss turn was 15.72.
  Utrom's turn-14.45 average cast is too late to be the principal answer.
- **Casey Jones:** Donatello remained 7–33. Longer games can expose the same issue:
  engine activity and Way damage accumulate without reliably becoming a winning
  board. Casey is not evidence that only faster starts are needed.

Because the result repeats across all three opponents, the next experiment should
target shared conversion: early bodies plus actual tempo/interaction, while
retaining the artifact plan.

## 9. Remaining simulator limitations

The current evidence is sufficient for a deck-level review, but it has limits:

- event logs do not provide a complete counterfactual analysis of whether a stun or
  unplayed interaction would have changed a combat result;
- a zero cast record does not distinguish unavailable cards from Pilot refusal or
  an illegal timing window;
- the AcceptancePilot is a deterministic baseline, not a human priority model;
- Gadget Master, Mutant Mechanic, Sewer-veillance Cam, Bespoke Bō, and Does Machines
  level 3 still have tracked semantic or choice limitations.

These limitations should be preserved in later interpretation. None is isolated by
the P0.3b smoke as the sole foundational explanation for the unchanged 15%-class
result. The supported Utrom experiment and the clean runtime make another isolated
semantic change less justified than a focused deck conversion test.

## 10. Revision-scale decision

`STRUCTURAL_4_CARD_REVISION`

The two-card Utrom experiment was exercised but did not move any Donatello matchup.
A second two-card replacement would risk repeating the same narrow test without
addressing the combined early-survival and post-engine-closing failures. The next
revision should remain one coherent lever and stay within a maximum of four card
changes, with no land changes.

The authorized scale is not permission to broadly retune the deck. It is a bounded
four-card test of immediate battlefield conversion.

## 11. Ownership classification

`MIXED_BUT_DECK_REVISION_STILL_JUSTIFIED`

The dominant evidence is deck-level: the core engine is active, yet Donatello still
loses before it matters or reaches it without enough interaction and pressure.
Semantic and Pilot limitations remain relevant, especially for interpreting unused
reactive cards, but no remaining semantic gap was shown to be the single cause of
the result. The P0.3b failure is therefore not responsibly classified as
semantic-dominant.

## 12. Next-gate decision

`AUTHORIZE_DONATELLO_P0_3C`

The preserved P0.3c candidate may be created in a separate focused PR under these
constraints:

- **Named problem:** setup and card advantage are not becoming early stabilization
  or a protected closing board; Utrom supplied real activity but arrived too late
  and at too low a density.
- **Scale and budget:** one structural four-card revision, maximum four cards
  changed, no land changes, and no additional semantic implementation in the deck
  PR.
- **Strategic lever:** convert delayed or conditional utility into immediate,
  supported artifact battlefield impact plus real tempo, while retaining Does
  Machines, Donatello's Technique, Way with Machines, and the invention identity.
- **Preferred cuts:** begin with delayed/low-conversion utility slots—remaining
  Sewer-veillance Cam, Return to the Sewers, or another slot only after its exact
  card role and timing are authenticated. Do not cut Does Machines or Technique.
- **Preferred additions:** supported one-to-three-mana artifact bodies that can
  block or pressure immediately, and/or artifact-based interaction/tempo that
  affects an opposing threat on the critical turns. Avoid cards whose test depends
  on another major unsupported mechanic.
- **Expected benefit:** earlier meaningful blockers, more profitable artifact
  entries, better survival through engine turns, and a higher Way cast-to-attack
  and attack-to-lethal conversion rate.
- **Tradeoffs:** reduced recovery/card-selection redundancy, possible loss of
  technical utility, and the risk that the four-card change remains insufficient
  against Raphael-speed pressure.
- **Next-smoke questions:** compare first creature and first meaningful blocker
  turns; count interaction casts and targets; measure Does/level-two timing and
  mana opportunity cost; measure Way cast-to-attack, survival, and lethal
  contribution; and rerun the same frozen 240-game schedule without adaptive
  changes.

This authorization does not create P0.3c, alter any existing prototype, authorize
another semantic PR, or authorize Calibration V1.
