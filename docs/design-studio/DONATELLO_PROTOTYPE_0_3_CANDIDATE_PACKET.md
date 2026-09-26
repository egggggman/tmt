# Donatello Prototype 0.3 Candidate Packet

Status: candidate analysis only. No decklist is created or changed by this packet.

## Authorization and evidence chain

This packet is authorized only for the bounded Design Studio investigation recorded in
[`PROTOTYPE_0_3_LIMITED_AUTHORIZATION.md`](PROTOTYPE_0_3_LIMITED_AUTHORIZATION.md). It does not authorize a
card swap or a `PROTOTYPE_0.3` file. Prototype 0.1 and Prototype 0.2 remain preserved.

The source run is `CALIBRATION_V1_20260923T141649Z_3f838930291e`, with completion audit
`AUDIT_PASS`. The run contains 184,320 distinct games, 368,640 authenticated executions, and
2,048 whole-roster blocks. The corrected analysis records Donatello at 13,482 wins and 23,382
losses in 36,864 games: 36.57%, with a Wilson 95% confidence interval of 36.08%--37.07%.

This packet uses the merged Calibration V1 Design Studio review, the corrected analysis artifact,
the preserved Donatello prototype history, the Pilot Fitness V3 limitations, and the repository's
accepted semantic evidence. Production evidence remains external and is not modified here.

## Prototype 0.1 to 0.2 history

Prototype 0.1 established the intended identity: a network of small artifacts learns from pieces
entering or breaking and converts preparation into adaptable battlefield advantage. It contained
23 lands, 21 creatures, 14 artifacts, 15 draw copies, 7 counterspells, 11 evasion copies, and 9
token-creation copies. Its known risks were a thin creature count, a clogged three-mana slot,
insufficient Gadget Master targets, slow Does Machines, value without closing, and loss of the
inventive rather than passive draw-go feel.

Prototype 0.2 preserved every creature, artifact setup piece, and land. Its only intervention was:

| Removed | Added |
| --- | --- |
| 2 Does Machines | 2 Negate |
| 2 Donatello's Technique | 2 Return to the Sewers |

The resulting noncreature package is 4 Sewer-veillance Cam, 1 Does Machines, 2 Negate, 3 Ooze
Spill, 2 Bespoke Bō, and 4 Return to the Sewers, with 23 Island unchanged.

The intervention followed Calibration 0.1, where Donatello recorded 63.2% wins, 98.8% setup,
93.8% realized payoffs, 92.0% full execution, and 2.77 realized payoffs per game. The stated goal
was to reduce repeated setup-to-payoff conversion while preserving the artifact engine. Calibration
V1 now reports a material reversal to 36.57%; that establishes an outcome change, not that the
intervention itself caused the change or that Prototype 0.2 was over-nerfed.

## Current identity

Donatello should remain inventive, technical, and proactive: assemble small components, recognize
the problem presented by the board, and turn prepared artifacts into a clever solution. The deck
must not become generic blue control, passive draw-go, or artifact aggro without problem-solving
texture.

The current baseline is 60 cards: 23 Island, 21 creatures, and 16 noncreatures. It remains a low
curve with artifact entry/departure value, evasive growth, answers that can create Mutagen, and
multiple ways to turn a prepared network into cards or board presence.

## Named problem and ownership

**Prototype 0.2 does not reliably convert Donatello's prepared artifact network into timely
stabilization and a closing advantage under the represented model, but the ownership is unresolved
between reduced proactive redundancy, AcceptancePilot sequencing, bounded reactive/recursion
semantics, and severe pressure-matchup structure.**

This is a mixed deck/simulator/Pilot problem. The low result is too broad to dismiss, especially
against Raphael, Shredder, Casey Jones, Michelangelo, and Splinter. It is not enough to prescribe
restoring Does Machines or Donatello's Technique: a human-play comparison is needed to distinguish
lost reliability from a model that cannot execute technical choices or from opponents whose plans
are disproportionately effective in the simulation.

## Calibration V1 evidence

Donatello's seat split was 18,432 games first at 37.74% and 18,432 games second at 35.40%, a
first-minus-second difference of +2.34 percentage points. The overall paired environment seat effect
was only +0.64 percentage points; Donatello's delta is therefore a deck-specific observation to
inspect, not an engine-defect finding.

| Opponent | Donatello win rate | Reading |
| --- | ---: | --- |
| Leonardo | 47.41% | near-balanced control |
| Raphael | 18.02% | severe pressure failure |
| Michelangelo | 32.23% | broad unfavorable result |
| Splinter | 22.00% | broad unfavorable result |
| Shredder | 12.84% | severe pressure/removal failure |
| Krang | 59.33% | favorable, simulator-confounded |
| Bebop & Rocksteady | 49.24% | near-balanced control |
| April O'Neil | 63.92% | favorable, simulator-limitation-dominant opponent |
| Casey Jones | 24.17% | severe pressure failure |

The structure is two matchups above 55%, two at 45%--55%, and five below 45%. The prior
Donatello-overperformance hypothesis is materially reversed, but the matrix does not identify a
single failed card. Leonardo and Bebop & Rocksteady are the useful controls: their near-balanced
results show that Donatello can compete in some represented environments. Krang and April cannot
be used as clean evidence of Donatello strength because both have material simulator limitations.

## Matchup structure

### Pressure and removal tests

Raphael at 18.02%, Shredder at 12.84%, and Casey Jones at 24.17% show that Donatello often fails
to stabilize before an aggressive or removal-capable opponent turns its setup time into a liability.
Possible explanations include too much tempo spent assembling artifacts, reactive cards arriving too
late, poor Negate timing, reduced Does Machines recovery, weak closing after stabilization, or
aggressive AcceptancePilot policies on the opposing side. The result supports a pressure-fragility
hypothesis but does not distinguish those mechanisms.

### Non-pure-aggression controls

Michelangelo at 32.23% and Splinter at 22.00% demonstrate that the problem is not only a simple
race against maximum attackers. Their counters, combat tools, recursion, and board interactions may
also expose Donatello's inability to convert preparation into a decisive position. Splinter's own
recursion and leave/return semantics are bounded, so the pairing is informative but not a clean
deck-quality verdict.

### Near-balanced and favorable pairings

Leonardo at 47.41% is the most stable control. Both decks develop a technical or prepared plan, and
neither has the extreme pressure polarity seen against Raphael or Shredder. This pairing can reveal
whether Donatello's problem is tempo, answer timing, or failure to close after assembling.

Bebop & Rocksteady at 49.24% is a second control. Its near balance suggests that Donatello can
contest a slower or differently structured artifact/token plan when the opposing semantic surface
does not immediately punish setup. It should be used as a baseline, not proof of general health.

Krang at 59.33% and April at 63.92% are the only favorable results. Krang's affinity/cost behavior
and April's answer/targeting surface are both known simulator limitations. These wins may reflect
real pairing structure, but they cannot establish that Donatello is strong or that its engine is
working correctly.

## Semantic and Pilot inventory

The inventory below covers every nonland card in Prototype 0.2. “Direction unknown” is intentional:
the repository does not support a safe numerical correction factor.

| Card | Intended role and identity centrality | Representation and AcceptancePilot handling | Bias direction |
| --- | --- | --- | --- |
| Fugitive Droid (4) | Small artifact/creature component; sacrifice-based protection for a controlled artifact or creature. Central to technical interaction. | Partial: the exact sacrifice, target, priority, and counterspell response has accepted bounded coverage, but the Pilot does not demonstrate human timing or subject selection. | Direction unknown; likely understated if timely sacrifice decisions matter. |
| Buzz Bots (4) | Cheap artifact body whose departure draws a card; central to learning from pieces breaking. | Partial-to-strong for fixed death-trigger draw on represented paths; the Pilot does not value future departure or choose sacrifice lines like a human. | Direction unknown. |
| Crustacean Commando (4) | Early artifact/body development and token or board-presence support. Central to assembling a network without being passive. | Partial: token and artifact sequencing are represented on bounded paths; lowest-cost creature sequencing favors early deployment but not adaptive timing. | Direction unknown, with setup overstatement plausible. |
| Donatello, Way with Machines (3) | Converts artifact entries into a growing evasive threat; primary proactive payoff. | Strong for the observed artifact-entry trigger and counter delivery, but the Pilot's closing behavior is simple and may not protect or time the threat optimally. | Direction unknown. |
| Donatello, Gadget Master (2) | Sneak/copy payoff that turns a prepared artifact into an adaptive solution; central to cleverness. | Partial: bounded Sneak exists, but copy-target quality, timing, and broader priority choices are not equivalent to human problem-solving. | Likely understated for adaptive play; direction not proven. |
| Donatello, Turtle Techie (2) | Artifact-conditional entry draw; rewards preparation. | Strong for the accepted artifact predicate and fixed Draw path, but the Pilot may play it for lowest-cost sequencing rather than maximize the network value. | Direction unknown. |
| Donatello, Mutant Mechanic (2) | Converts a utility artifact into a Robot while preserving work after it breaks; identity-central recursion/continuity. | Partial: artifact departure and token paths exist, but preserving and reusing value across more complex board states is bounded. | Direction unknown; recovery may be understated. |
| Sewer-veillance Cam (4) | Early artifact setup and network anchor. Identity-central. | Partial: artifact presence/entry is represented, but its information/setup choices are not a broad human search. Lowest-cost sequencing may overvalue immediate deployment. | Direction unknown. |
| Does Machines (1) | Selects and recovers components; the remaining proactive reliability lever. Identity-central. | Partial: bounded selection/recovery evidence exists, but reducing it to one copy materially changes access and the Pilot's choice quality is uncertain. | Direction unknown; current reliability may be understated. |
| Negate (2) | Reactive technical protection for a key spell or engine piece. | Partial/poorly established for deck use: counterspell primitives exist, but AcceptancePilot counters supplied opposing spells rather than reasoning about timing, future threats, or holding mana. | Plausibly understated in human hands; may be dead or mistimed under the Pilot. |
| Ooze Spill (3) | Instant answer that can also create Mutagen; flexible technical interaction. | Partial: accepted counterspell/Mutagen paths exist, but response timing and target/value selection are bounded. | Direction unknown. |
| Bespoke Bō (2) | Artifact/equipment utility, evasion, and technical combat conversion. | Partial: attachment/equipment semantics and strategic equip timing are known boundaries. | Likely understated for skillful use; direction not proven. |
| Return to the Sewers (4) | Precise answer plus Mutagen; added as a reactive replacement for proactive engine pieces. | Partial: token/return/answer paths are represented, but target selection and timing are deterministic rather than human-adaptive. | Direction unknown. |
| Island (23) | Stable blue mana for a low curve and reactive protection. | Land play is represented, but mana-hold decisions and the cost of keeping Negate open are Pilot-bound. | Direction unknown; reactive opportunity cost may be understated. |

The strongest repository-supported concern is not that Donatello's core artifact triggers are absent:
several are accepted. It is that the technical plan spans timing, target, recursion, copy, equipment,
and recovery decisions that the AcceptancePilot does not execute as a human strategy. Pilot Fitness
V3 does not establish general competence over these surfaces; filtering remains inconclusive. The
current Pilot can develop a low-cost board, but the evidence does not show that it can choose when
to hold Negate, sacrifice Fugitive Droid, preserve a copy target, or convert a stabilized board into
a win.

## Prototype 0.2 intervention analysis

### Reliability

Reducing Does Machines from three copies to one plausibly removed proactive component selection and
recovery redundancy. Reducing Donatello's Technique from two to zero also removed a route for an
unblocked board to become cards and future options. The V1 result is consistent with lost
reliability, but it cannot establish that this was the cause because the Pilot and opponent plans
are different confounds.

### Pilot competence

Negate is not a simple replacement for a proactive artifact engine piece. AcceptancePilot's
countering rule is legality-driven and deterministic, not a human assessment of whether to reserve
mana, what future threat matters, or whether a spell is worth answering. This makes a reactive shift
especially vulnerable to Pilot underuse or mistiming.

### Reactive shift

The intervention exchanged four proactive conversion slots for two Negate and two additional Return
to the Sewers. It preserved technical color identity but increased the proportion of cards that
require an opponent action, a legal target, or a timing window. That can be a sound human design
choice, but under the current Pilot it may reduce the number of useful actions available during the
setup turns.

### Closing power

Removing Donatello's Technique may reduce the deck's ability to convert an unblocked route into
additional cards. The existing list still has Way with Machines and artifact-driven threats, so a
closing failure cannot be attributed to Technique alone. Human games must record whether Donatello
stabilizes and then fails to finish, or never stabilizes at all.

### Redundancy

Taking Does Machines from three copies to one may have weakened component access more than intended,
especially because the deck's identity depends on finding the right invention rather than merely
drawing more cards. This is a credible bounded hypothesis, not proof that one copy should be restored.

## Smoke-question review

| Prototype 0.2 question | Finding |
| --- | --- |
| Move aggregate strength toward 45%--55% without erasing invention? | Numerical target failed: V1 is 36.57%. Whether the design objective failed is unresolved because Pilot and semantic ownership are mixed. Requires human play. |
| Keep setup/payoff coherent but less automatic? | Unresolved. The V1 result suggests a possible reliability loss, but no V1 field proves setup/payoff coherence or its absence. Requires human play. |
| Contract prior >65% polarity matchups? | Simulator-confounded. Current severe losses are documented, but the relevant Prototype 0.1 polarity history and opponent semantics are not a clean causal comparison. |
| Make Negate create meaningful protection choices? | Unresolved and simulator-confounded. The Pilot has counterspell primitives but does not establish human-quality hold/counter timing. Requires human play. |

The result therefore does not justify calling Prototype 0.2 an over-nerf. It justifies testing whether
the intervention removed too much proactive redundancy and whether the new reactive package is usable
by human players and faithfully represented by the model.

## Candidate hypotheses and tradeoffs

These are investigation packets, not approved card changes.

1. **Restore a small amount of proactive engine redundancy.** Inspect the one remaining Does
   Machines slot and the removed Donatello's Technique package. Evidence: the V1 result is low and
   the intervention removed selection/recovery and closing conversion. Upside: more reliable access
   to inventions and a better chance to convert preparation into a win. Risk: recreate the prior
   automatic 63.2% strength or return to repetitive setup-to-payoff conversion. Matchup impact would
   most likely be against Raphael, Shredder, and Casey, but the direction is not quantified. Human
   evidence must precede a choice.
2. **Reduce dependence on reactive cards.** Inspect the two Negate and four Return to the Sewers
   slots as a package, not as isolated swaps. Evidence: the package requires opponent timing and
   target opportunities that AcceptancePilot may not value. Upside: fewer dead cards and more
   proactive artifacts. Risk: lose Donatello's technical protection and become vulnerable to the
   exact pressure the revision was meant to answer. Human play is required.
3. **Improve early stabilization without rebuilding the deck.** Examine one bounded tempo/answer
   hypothesis against Raphael, Shredder, and Casey. Evidence: those matchups are 18.02%, 12.84%, and
   24.17%. Upside: create time for the artifact network. Risk: genericize the deck, overfit to
   aggressive opponents, or misdiagnose Pilot-amplified opposing pressure. Do not select a card yet.
4. **Restore closing conversion.** Observe Way with Machines, Gadget Master, Mutant Mechanic, and
   the removed Technique line after stabilization. Evidence: the baseline explicitly worried about
   value without closing, and Technique was removed. Upside: make preparation produce a decisive
   battlefield advantage. Risk: add another automatic conversion layer or make the deck passive while
   searching for a finish. Human play must determine whether closing is the actual failure.
5. **Preserve Prototype 0.2 pending human evidence.** Evidence: the core artifact triggers are
   represented, but technical timing and choice behavior are not fully established. Upside: avoid
   changing a deck in response to simulator-owned results. Risk: leave genuine pressure fragility
   unresolved. This is the current safest recommendation.

Every hypothesis preserves inventions, preparation, technical problem-solving, the artifact network,
adaptability, and the feeling of assembling a clever solution. None authorizes a decklist.

## Focused human-play validation plan

Use a minimum useful sample of 24 human games: six each against Raphael, Shredder, Leonardo, and
Bebop & Rocksteady, with three games starting and three drawing in each pairing. Add six Casey Jones
games if capacity permits. Prioritize Raphael for pressure, Shredder for pressure/removal, Leonardo
as the near-balanced technical control, and Bebop & Rocksteady as the second near-balanced control.

Record the turn the artifact network becomes functional; meaningful pieces assembled; whether Does
Machines changes access; whether Negate has useful targets and whether holding it is correct; Return
to the Sewers timing and value; whether the absence of Technique is felt; early stabilization;
conversion of stabilization into a win; dead/reactive cards; missed mana; closing failures; clever
“Donatello solution” moments; fun to pilot and face; and whether Prototype 0.2 still feels inventive
rather than passive.

Balance play/draw and record mulligans, first pressure, first answer, and opponent recovery. A
useful comparison should include games where players deliberately vary whether to hold Negate,
deploy another artifact, sacrifice Fugitive Droid, or spend Return to the Sewers. Do not treat these
as a new simulation or as permission to alter the deck.

The current hypothesis is falsified or weakened if human players reliably assemble and close while
the Pilot fails to do so; if Negate and Return create meaningful choices; if early pressure can be
answered without changing the engine; if the absence of Technique is not felt; or if the V1 losses
are largely caused by unsupported opponent behavior. It is also weakened if restoring proactive
redundancy produces repetitive, automatic games rather than clever adaptation.

## Recommendation

The evidence supports a bounded Donatello investigation but does not support a card-level revision.
Prototype 0.2 should remain preserved while human play tests whether the low result is lost engine
reliability, reactive/Pilot mismatch, pressure fragility, incomplete semantics, or a combination.
Any later candidate decklist requires separate explicit approval and must preserve Prototype 0.1 and
Prototype 0.2.

GATHER_HUMAN_EVIDENCE_FIRST
