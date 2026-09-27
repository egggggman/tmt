# Donatello Prototype 0.3a Post-Flying Pre-Balance Review

Status: focused Design Studio review; no deck change is authorized by this artifact alone.

## 1. Evidence chain

This review is based on the authenticated Prototype 0.3a deck and the preserved, exact frozen post-Flying smoke at repository commit `14a78e9be11b932c55018f1d1746c890cdbd9c65`:

- [Prototype 0.3a deck and rationale](../../decks/donatello/PROTOTYPE_0.3a.md)
- [Post-Flying smoke results](PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3A_POST_FLYING_RESULTS.md)
- [Post-Flying smoke review](PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3A_POST_FLYING_REVIEW.md)
- [Preserved post-Flying event evidence](PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3A_POST_FLYING_EVIDENCE.json.gz)
- [Prototype 0.3 smoke review](PROTOTYPE_0_3_SMOKE_REVIEW.md)
- [Donatello representation audit](DONATELLO_P0_3A_REPRESENTATION_AUDIT.md)
- [Donatello semantic coverage record](DONATELLO_P0_3A_SEMANTIC_COVERAGE.md)

The smoke completed 240/240 games with zero runtime errors, malformed games, draws, or turn caps. No smoke was rerun for this review.

## 2. Semantic-coverage checkpoint

The central setup → recovery → conversion → evasion path is now materially represented:

- Donatello's Technique was drawn, cast/resolved, drew cards, and exercised Sneak.
- Does Machines recorded 96 casts/resolutions, functioning setup, 77 level-2 advancements, and 106 recovered artifacts.
- Way with Machines recorded 75 casts/resolutions, 26 qualifying artifact-entry triggers, 26 counters, 79 attack assignments, and 149 direct combat damage.
- Flying was implemented generically and the compact post-Flying diagnostic observed legal blocker filtering.

These facts do not prove every remaining Donatello card is complete, but they do mean the 15% result cannot responsibly be attributed primarily to absent Technique, Does Machines setup/recovery, Way counters, or Flying.

## 3. Loss-pattern analysis

Across Donatello's 102 losses in the preserved smoke event log:

| Pattern | Count | Interpretation |
| --- | ---: | --- |
| No Does Machines cast before loss | 43 / 102 | Access and early-tempo failure remains common. |
| Does cast, but no Donatello level 2 before loss | 13 / 102 | Some games cannot pay the setup cost in time. |
| Donatello level 2 before loss | 46 / 102 | Engine completion alone does not stabilize or close games. |
| Way with Machines cast before loss | 41 / 102 | The payoff is often present. |
| Way attack assigned before loss | 8 / 102 | Only a minority of losses converted the payoff into an attack. |
| Way dealt direct damage in loss | 8 / 102 | Direct pressure is correspondingly sparse. |

The average loss turn was 17.45. In those losses, the average first Donatello creature appeared on turn 4.34, Does Machines was cast on turn 6.15 when cast, level 2 was reached on turn 6.52 when reached, and Way with Machines was cast on turn 13.51 when cast. The deck therefore does produce an early permanent in many games, but it spends critical mana on delayed value and frequently fails to convert that value into a protected attacker or a closing board.

By opponent, losses before a Does Machines cast were 13/33 against Shredder, 18/36 against Raphael, and 12/33 against Casey Jones. The Raphael losses were also fastest on average at turn 15.72, versus 18.58 against Shredder and 18.21 against Casey Jones. This is consistent with Donatello losing the tempo race against the fastest pressure before or around the first engine commitment.

Representative preserved losses show both sides of the pattern:

- `shredder-vs-donatello-3000`: first creature on turn 3, Way on turn 15, no Does Machines cast, and no Way attack before the turn-18 loss.
- `shredder-vs-donatello-3002`: Does Machines on turn 3 and level 2 on turn 5, but loss on turn 14 without Way; setup completed without enough battlefield conversion.
- `shredder-vs-donatello-3005`: Way attacked three times and dealt two direct damage, but the deck still lost on turn 17.
- `shredder-vs-donatello-3016`: Does Machines and level 2 occurred early and Way attacked five times for five direct damage, yet the game lasted to turn 36 and still ended in a loss. Late engine activity is not automatically a closer.

The event log does not provide a complete causal counterfactual for every combat trade, so these are observed sequences, not claims that a particular unplayed line would have won.

## 4. Speed analysis

Donatello's first creature turn of 4.34 is not a blanket failure to develop. The problem is what happens after that first permanent: much of the early mana is invested in Does Machines, level advancement, recovery, and conditional support rather than in immediately increasing the number or quality of blockers and attackers.

The matchup split matters. Raphael defeated Donatello 36–4 and produced the earliest average Donatello loss. The 18 Raphael losses without a Does cast show that the deck often never reaches its engine against aggressive pressure. The remaining 18 Raphael losses still include games where setup completed, so speed is not the entire diagnosis; it is the first part of a broader conversion failure.

## 5. Board-impact analysis

The engine produces cards and recovered artifacts, but the event evidence shows delayed value more reliably than immediate combat impact. Way with Machines was cast in 41 losses but attacked in only 8. That 33-game gap is the clearest preserved signal: a card can enter and receive support without becoming an active, protected threat.

The 21-creature package includes several setup or conditional bodies—Fugitive Droid, Crustacean Commando, Turtle Techie, Gadget Master, and Mutant Mechanic—alongside the actual pressure pieces. Buzz Bots, Way with Machines, and some artifact growth provide combat presence, but the current density does not consistently turn recovered-card advantage into a board that can race or stabilize.

## 6. Threat-quality analysis

Donatello has an artifact/invention identity, but not all 21 creatures are equivalent threats. Fugitive Droid and Crustacean Commando establish artifact count and setup; Turtle Techie is value-oriented; Gadget Master and Mutant Mechanic depend on additional support or still-incomplete semantics. Way with Machines is the primary scalable evasive threat, while Buzz Bots supply useful early pressure and defense.

The preserved losses show that simply adding more cards to hand or graveyard does not solve the shortage of immediate, resilient pressure. The deck appears to lack enough early artifact bodies that both block profitably and create the artifact-entry density needed to make Way a timely closer. This is a threat-quality and conversion problem, not evidence that the deck should become generic control.

## 7. Interaction and stabilization analysis

The nominal noncreature package is:

- 4 Sewer-veillance Cam
- 3 Does Machines
- 3 Ooze Spill
- 2 Bespoke Bō
- 2 Donatello's Technique
- 2 Return to the Sewers

In Donatello's 102 losses, preserved `spell_cast` records show 44 Technique casts, 79 Does Machines casts, and 56 Way casts. There were no corresponding Donatello cast records for Ooze Spill, Return to the Sewers, Bespoke Bō, or Sewer-veillance Cam in those losses. This is an observed runtime/Pilot-use signal, not proof that every copy was drawn or every legal line was available. It nevertheless means the nominal stabilization package is not currently showing up as tempo in the losing games.

The deck consequently has two related vulnerabilities: it can lose before the engine is cast, and it can cast the engine without a demonstrated way to remove attackers, create profitable blocks, or close. Bespoke Bō and Return to the Sewers may be strategically useful in human play, but their observed absence from loss casts makes their current slots reasonable candidates for a narrowly scoped conversion test rather than automatic inclusions.

## 8. Historical prototype comparison

Prototype 0.1 contained three Does Machines, two Donatello's Technique, and two Return to the Sewers. Prototype 0.2 removed two Does Machines and both Technique, added two Negate, and added two Return to the Sewers. Prototype 0.3 removed the two Negate and restored two Does Machines. Prototype 0.3a then changed two Return to the Sewers into two Donatello's Technique.

The sequence mostly moved setup, recovery, and card-advantage density around. It successfully clarified that setup reliability alone was not the answer, and the semantic work now demonstrates that Technique and Does Machines can operate. The post-Flying result remaining 18–102 indicates that the unresolved issue is not simply which value card is present; it is the conversion of those resources into early stabilization and a credible closer.

## 9. Remaining semantic-gap assessment

No remaining gap was isolated as the sole foundational explanation for 15%:

- Gadget Master's artifact-copy trigger could improve late-game value and closing, but the current losses already show a more immediate attack/conversion problem.
- Mutant Mechanic could improve counter distribution and artifact utility, but it is a secondary board-growth mechanic after the deck has survived.
- Sewer-veillance Cam and Bespoke Bō could materially affect tempo if their actions are selected and resolved, but their zero loss-cast records indicate a mixed card-density/Pilot-use surface rather than proof that another engine implementation alone will solve the deck.
- Does Machines level 3 is a late payoff. Level 2 already occurs in 46 losses, including early examples, without producing sufficient pressure; level 3 is therefore not the first justified intervention.

These gaps remain relevant and should be tracked, but the evidence does not support delaying all deck review for another isolated semantic implementation.

## 10. Ownership classification

`MIXED_BUT_DECK_REVISION_JUSTIFIED`

The dominant evidence is deck-level: Donatello frequently spends mana on value, often reaches the engine, and still has too little immediate interaction and closing pressure. There is also a secondary representation/Pilot-use component because several nominal stabilization cards never appear as casts in losses and some card semantics remain incomplete. That mixed component is not sufficiently foundational to classify the whole result as semantic-coverage-dominant.

## 11. Revision hypothesis

A preserved Prototype 0.3b candidate is justified, but it must be a small conversion experiment rather than a broad power increase.

Named problem: the current list has delayed or conditional noncreature density that does not reliably stabilize the battlefield, while Way with Machines is too often cast without an attack before the loss.

Preferred hypothesis: exchange 2–4 low-impact or delayed setup/utility slots for 2–4 early artifact bodies or one artifact-based closer with immediate battlefield impact. The preferred first candidate direction is to retain the artifact identity while reducing part of the redundant delayed utility density—most narrowly, evaluate `-2 Sewer-veillance Cam` or `-2 Return to the Sewers` against `+2` early artifact/tempo bodies in the separate candidate review. Exact card identities must be authenticated and selected in the P0.3b change PR; no swap is made here.

Maximum change budget: 4 cards changed, with one coherent lever and no land changes. The expected benefit is earlier blockers, more artifact entries for Way, and a higher Way-cast-to-attack conversion rate. Risks are reduced card flow or interaction, loss of technical identity, and over-reading a directional sample. The next smoke should therefore preserve the exact 240-game schedule and measure first-creature timing, Does/level-2 timing, interaction casts, Way cast-to-attack conversion, direct damage, and the same matchup results.

## 12. Next-gate decision

`AUTHORIZE_DONATELLO_P0_3B`

This review authorizes creation of a separate, preserved P0.3b candidate within the four-card maximum above. It does not create or overwrite any deck, does not authorize another semantic PR, and does not authorize tuning Shredder, Raphael, Casey Jones, the smoke schedule, or frozen evidence.

The P0.3b candidate must be reviewed as a new deck artifact, then run through the same frozen smoke and compared descriptively. Human play remains a useful later gate, but the current 15% aggregate and the observed inability to turn engine activity into combat pressure justify one narrowly scoped conversion revision first.
