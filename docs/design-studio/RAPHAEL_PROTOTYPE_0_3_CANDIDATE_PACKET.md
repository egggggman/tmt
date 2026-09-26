# Raphael Prototype 0.3 Candidate Packet

Status: candidate analysis only. No decklist is created or changed by this packet.

## Authorization and evidence chain

This packet is authorized only for the bounded Design Studio investigation recorded in
[`PROTOTYPE_0_3_LIMITED_AUTHORIZATION.md`](PROTOTYPE_0_3_LIMITED_AUTHORIZATION.md). It does not authorize a
card swap or a `PROTOTYPE_0.3` file.

The source run is `CALIBRATION_V1_20260923T141649Z_3f838930291e`, with completion audit
`AUDIT_PASS`. The run contains 184,320 distinct games, 368,640 authenticated executions, and
2,048 whole-roster blocks. The banked completion audit SHA-256 is
`D202D3B35814E2B67CF2959E73282264CD8AC2B93EA877FB8C8970D1D48616BE`.

The corrected analysis artifacts are `CALIBRATION_ANALYSIS_V1.json` (Git blob SHA-256
`EC409344E0BDB23C754106DAFB2DF6B828BCDEA0476999CD44357E12499131EE`) and
`CALIBRATION_ANALYSIS_V1.md` (Git blob SHA-256
`96EEC193CF7AE8E9AEC908F2B5879C399A032B087989F0FCCDCC074BEE7CB1C0`). The analysis reports
Raphael as `MIXED_OR_UNRESOLVED`. Production evidence remains external and is not modified here.

## Current prototype identity

The preserved baseline is [`decks/raphael/PROTOTYPE_0.1.txt`](../../decks/raphael/PROTOTYPE_0.1.txt),
with its identity and questions documented in [`PROTOTYPE_0.1.md`](../../decks/raphael/PROTOTYPE_0.1.md).
Raphael is intended to be impulsive, confrontational, momentum-oriented, and willing to trade
protection and long-term coordination for haste, risky combat, rummaging, and immediate pressure.
This packet preserves that identity and does not turn Raphael into generic red midrange.

The baseline is 60 cards: 22 Mountains, 24 creatures, and 14 noncreatures. It has 22 MV2 cards,
63.2% threat density, 10 card-draw copies, 4 selection copies, 2 finishers, and a concentration of
creature-entry, Alliance, combat, artifact, and equipment interactions.

## Named problem and ownership

**Raphael's pressure is broadly successful, but the current model cannot yet separate excessive
early-pressure consistency from AcceptancePilot amplification and incomplete opponent
counterplay.**

This is a mixed deck/simulator/play-experience problem, not a conclusion that one card is
overpowered. The evidence justifies a bounded investigation because the result is broad across
eight matchups, but it does not justify an exact card-level revision. Pilot policy, bounded
semantics, and weakly represented opposing plans may all contribute.

## Calibration evidence

Raphael played 36,864 games, winning 27,470 and losing 9,394, for a 74.52% win rate with an
approximately 74.07%--74.96% Wilson 95% confidence interval. It won 8 of 9 named pairings above
55%, one pairing was within 45%--55%, and none were below 45%.

The per-deck seat result was 18,432 games starting at 75.82% and 18,432 games second at 73.21%, a
first-minus-second difference of +2.62 percentage points. The complete frozen paired environment
has an overall seat effect of only +0.64 percentage points, so Raphael's deck-specific delta is a
diagnostic observation to inspect, not an engine-defect finding.

## Matchup structure

| Opponent | Raphael win rate | Structure |
| --- | ---: | --- |
| Leonardo | 79.57% | extreme favorable |
| Donatello | 81.98% | extreme favorable |
| Michelangelo | 68.92% | broad favorable |
| Splinter | 66.46% | broad favorable |
| Shredder | 47.24% | near-balanced control |
| Krang | 88.70% | extreme favorable |
| Bebop & Rocksteady | 87.87% | extreme favorable |
| April O'Neil | 91.11% | extreme favorable |
| Casey Jones | 58.81% | moderately favorable |

Shredder is the most informative control. Its removal, departure/sacrifice payoffs, and strong
threat pressure can contest Raphael before the latter's board plan becomes decisive. This pairing
tests whether Raphael's broad wins require opponents to lack counterplay. Casey's artifact and
board pressure produces meaningful but incomplete counterpressure, making it a second useful
control.

The very high April, Krang, Bebop & Rocksteady, Donatello, and Leonardo results may be genuine
deck-vs-deck structure, but they can also combine Raphael's aggressive Pilot alignment with
unsupported or bounded defensive/setup plans. Leonardo is especially important thematically, but
it is not a clean deck-quality comparison while opponent priority, protection, Sneak, and
coordination behavior remain bounded. No single mechanic is established as the sole driver.

## Semantic and Pilot analysis

The following inventory describes representation and attribution limits without applying a
numerical correction factor.

| Card | Intended role | Representation and likely Pilot interaction | Performance direction |
| --- | --- | --- | --- |
| Casey Jones, Jury-Rig Justiciar (4) | Artifact/gear setup and pressure | Partial: artifact entry, selection, and hand movement choices are bounded; low-cost creature sequencing may favor early deployment. | Direction unknown; artifact decisions may be understated. |
| Raphael, Tough Turtle (4) | Creature-entry pressure payoff | Partial: creature-entry/Alliance behavior is represented on bounded paths, but repeated team math and choices are not a neutral human policy. Low-cost sequencing and maximum attacks amplify it. | Plausibly overstated; direction not proven. |
| Wingnut, Bat on the Belfry (4) | Cheap evasive pressure | Ordinary creature/combat/evasion behavior is broadly represented. Maximum-attacker policy reliably converts board presence into attacks. | Plausibly overstated by Pilot policy. |
| Mutant Town Musicians (3) | Alliance and body-commitment payoff | Partial: Alliance/token and sequencing branches are bounded; the Pilot favors committing available bodies. | Direction unknown, with overstatement plausible. |
| Null Group Biological Assets (3) | Creature/artifact support and card exchange | Partial: targeting, exchange, and filtering choices are bounded. | Direction unknown. |
| Raphael, Most Attitude (2) | Midgame threat and pressure | Partial card-specific behavior and combat choices are bounded; deterministic creature development favors its straightforward use. | Direction unknown. |
| Raphael, Ninja Destroyer (2) | Threat, combat, and possible interaction | Partial: card-specific targets and combat branches are not fully human-equivalent. | Direction unknown. |
| Raphael, the Nightwatcher (2) | Sneak/Double Strike burst finisher | Partial: bounded Sneak and Double Strike paths exist, while priority, additional costs, entering-attacking, and return-attacker choices remain sensitive. The Pilot takes the first legal Sneak option. | Direction unknown; burst may be overstated or missed. |
| Skateboard (2) | Artifact/equipment and evasion support | Partial: attachment and equipment decisions are bounded rather than fully strategic. | Likely understated for skillful attachment use. |
| Cool but Rude (3) | Rummaging and card flow | Partial: filtering and discard choices are policy-bound; optional filter behavior is deterministic. | Direction unknown. |
| Manhole Missile (4) | Blocker clearing and interaction | Partial semantic warning: older capability analysis recognized zero targeted interaction, while bounded Deal Damage paths exist. The AcceptancePilot selects a low-toughness target when available. | Direction unknown; easy target selection may overstate, missing lines may understate. |
| Mouser Attack! (3) | Pressure and Alliance support | Partial: token, Alliance, forced-block, and choice semantics are bounded; maximum attacks favor its pressure role. | Direction unknown, overstatement plausible. |
| Raphael's Technique (2) | Volatile reload and hand reset | Partial: draw/discard and symmetric draw-seven choices are policy-bound and may benefit opponents as well. | Direction unknown. |

The AcceptancePilot chooses the maximum number of attackers and blockers, sequences a lowest-cost
creature, chooses the first legal Sneak option, and has deterministic handling for filtering and
damage targeting. Those rules align unusually well with Raphael's visible aggressive plan. This is
strong evidence for a Pilot-amplification hypothesis, not proof that all of Raphael's simulated
strength is artificial. Recovery after overextension, forced blocks, menace, nuanced combat tricks,
and opponent setup decisions are not represented as a human strategy equivalent.

## Competing strength hypotheses

| Hypothesis | Current assessment | Smallest investigation lever |
| --- | --- | --- |
| H1: Pilot-policy amplification | Credible and ownership-uncertain. Maximum attacks, cheap sequencing, and deterministic choices directly reward Raphael's plan. | Human games with varied attack, block, filter, and finisher decisions before changing cards. |
| H2: threat-density/curve pressure | Credible. Twenty-two MV2 cards and 63.2% threat density can create genuine early consistency. | Test one bounded early-creature redundancy package; do not select a swap yet. |
| H3: Tough Turtle/entry redundancy | Plausible. Four Tough Turtle plus three Mutant Town Musicians may compound creature-entry pressure. | Observe trigger frequency, decision quality, and whether value is oppressive or merely visible. |
| H4: blocker clearing plus follow-through | Plausible but semantically unresolved. Four Manhole Missile may leave too little stabilization space, but targeting support is bounded. | Human observation of actual removal contribution and opponent recovery. |
| H5: burst finishers | Plausible but unproven. Two Nightwatcher copies may create abrupt Double Strike endings. | Record appearances, damage, and whether opponents had meaningful windows. |
| H6: opponent semantic weakness | Credible in extreme pairings. Bounded defensive/setup plans can inflate Raphael's apparent advantage. | Prioritize Leonardo, Donatello, and April play with explicit counterplay logging. |

## Baseline-question review

| Baseline question | Finding |
| --- | --- |
| Tough Turtle plus repeated entries: Raphael pressure or generic Alliance math? | Unresolved; requires human play and trigger-quality observations. |
| Nightwatcher memorable without abrupt endings? | Supported concern; requires human play. |
| Are 22 Mountains sufficient? | Unresolved; record missed land drops and stranded expensive cards. |
| Is Raphael's Technique satisfying or too favorable? | Unresolved; symmetric draw and filter choices are Pilot-bound. |
| Does legendary congestion strand copies? | Unresolved; record dead legends and timing tension. |
| Does the deck fold after its first wave? | Unresolved and central to the named problem; human recovery evidence is required. |
| Does the Pilot experience confrontation over caution? | Requires human play; the current Pilot's maximum-attack rule is not a player-experience measure. |
| Does Manhole Missile provide meaningful interaction? | Supported semantic warning; requires human validation of targets and counterplay. |
| Is the deck distinct from Leonardo? | Simulation suggests pressure contrast, but identity and fun require human play. |

## Candidate hypotheses and tradeoffs

These are investigation packets, not approved card changes.

1. **Early-creature redundancy:** inspect the Casey Jones, Wingnut, Mutant Town Musicians, and
   related MV2 package. Reducing one redundant early-pressure copy could create recovery windows and
   reduce Pilot amplification, but risks removing Raphael's confrontation identity and making the
   deck fail to establish pressure. Human play must establish whether the issue is density or
   policy before any card-level proposal.
2. **Tough Turtle/Alliance concentration:** inspect the four Tough Turtle and three Mutant Town
   Musicians copies as a package. Lowering repeated entry payoffs could reduce snowballing while
   preserving a smaller payoff core, but risks making creature entry feel generic and weakening the
   defining Raphael engine. Human play is required first.
3. **Manhole Missile density:** inspect the four copies only after confirming that removal, rather
   than threat density, is causing the pressure. A reduction could restore blocker counterplay, but
   it could also leave Raphael unable to enact confrontational interaction and would be unsafe while
   the card's representation remains bounded.
4. **Nightwatcher burst:** inspect the two copies for abrupt-ending frequency. Reducing burst could
   improve counterplay, but risks removing memorable all-in turns and Raphael's willingness to risk
   everything. Human games should precede this lever.
5. **Reload and legendary friction:** inspect Raphael's Technique, Cool but Rude, and the legendary
   package as possible tension levers. More friction could improve balance without deleting early
   pressure, but may create non-games, stranded legends, or an unfun hand reset. No direction is
   justified yet.
6. **Curve/mana friction:** verify whether 22 Mountains support the higher-cost cards. Adding
   friction may lower consistency but risks making the deck fail its intended two-drop and attack
   pattern. This is a measurement question, not a recommendation.

All hypotheses preserve aggression, confrontation, risky momentum, uncomfortable combat, and the
contrast with Leonardo's coordination/protection. None authorizes a decklist.

## Focused human-play validation plan

Use a minimum useful sample of 24 human games: six each against Shredder, Casey Jones, Leonardo,
and either Donatello or April, with three games on the play and three on the draw per pairing. A
larger 32--40 game set is preferable if available. Prioritize Shredder as the near-balanced control,
Casey as moderate counterpressure, Leonardo as the thematic extreme, and Donatello or April as a
setup/defense stress test.

Record first meaningful attack, first blocker/removal interaction, damage before turns four and
five, Tough Turtle triggers, Nightwatcher appearance and burst damage, Manhole Missile contribution,
overextension, recovery after the first wave, stranded legends or expensive cards, missed land
drops, opponent counterplay, fun to pilot, fun to face, whether it felt like Raphael, and whether
it remained distinct from Leonardo.

The current hypothesis is falsified or weakened if Raphael's wins require risky overextension,
opponents consistently have meaningful recovery, Manhole Missile is not decisive, Nightwatcher
rarely ends games abruptly, extremes disappear when opponents use represented counterplay, or human
choices materially reduce the advantage relative to the deterministic Pilot. It is also weakened
if the deck remains fun and confrontational without oppressive experiences.

## Recommendation

The evidence supports continuing the authorized investigation but not selecting a card-level
revision. Human play should resolve whether the broad result is deck density, Pilot amplification,
semantic weakness in opponents, or a combination. Any later candidate decklist requires a separate
explicit approval and must preserve Prototype 0.1.

GATHER_HUMAN_EVIDENCE_FIRST
