# Casey Jones Prototype 0.3 Candidate Packet

Status: candidate analysis only. No decklist is created or changed by this packet.

## Authorization and evidence chain

This packet is authorized only for the bounded Design Studio investigation recorded in
[`PROTOTYPE_0_3_LIMITED_AUTHORIZATION.md`](PROTOTYPE_0_3_LIMITED_AUTHORIZATION.md). It does not authorize a
card swap or a `PROTOTYPE_0.3` file. Casey's Prototype 0.1 remains preserved.

The source run is `CALIBRATION_V1_20260923T141649Z_3f838930291e`, with completion audit
`AUDIT_PASS`. The run contains 184,320 distinct games, 368,640 authenticated executions, and
2,048 whole-roster blocks. The corrected analysis reports Casey Jones at 25,137 wins and 11,727
losses in 36,864 games: 68.19%, with a 95% confidence interval of 67.71%--68.66%.

This packet uses the merged Calibration V1 Design Studio review, corrected analysis, the preserved
Casey prototype and playtest log, Pilot Fitness V3 limitations, and accepted Equipment, artifact,
targeting, combat, and randomness evidence. Production evidence remains external and is not
modified here.

## Current identity

Casey is one scrappy vigilante turning junk into weapons. The deck combines improvised Equipment,
artifact-producing Robots, risky card velocity, and oversized combat. It must remain aggressive,
chaotic, resourceful, and gear-driven while staying distinct from Raphael's team-pressure plan.

The preserved baseline is 60 cards: 22 Mountain, 23 creatures, and 15 noncreatures. It has 25
two-mana cards, 19 artifacts, 8 Equipment copies across Hard-Won Jitte and Improvised Arsenal,
6 token-creation copies, 8 draw copies, and 60.5% threat density. The baseline questions are
whether Equipment is exciting rather than cumbersome, whether there are enough carriers, whether
Vigilante randomness is fun, whether double strike creates sudden kills, and whether Casey remains
distinct from Raphael.

## Named problem and ownership

**Casey produces broad board and combat pressure with more redundant Equipment payoff than the
first human-play environment needs, while the exact contribution of gear access and attachment
friction remains simulator-dependent.**

This is a mixed deck/simulator problem. The evidence is credible enough for a small reversible
pre-balance experiment because Casey is above 55% against seven decks, including Leonardo,
Michelangelo, and Splinter, whose limitations are less extreme than April's or Krang's. It is not
evidence that Casey should be forced to 50%, nor that Jury-Rig Justiciar, Vigilante randomness, or
all artifact development should be changed.

## Calibration V1 evidence

Casey won 68.19% overall. Seven matchups were above 55%, two were below 45%, and none were within
45%--55%. The result is broad but not universal:

| Opponent | Casey win rate | Reading |
| --- | ---: | --- |
| Leonardo | 68.21% | useful pre-balance evidence |
| Raphael | 41.19% | meaningful pressure control |
| Donatello | 75.83% | favorable, mixed-ownership opponent |
| Michelangelo | 65.94% | useful pre-balance evidence |
| Splinter | 62.99% | useful but semantic caveats remain |
| Shredder | 37.28% | meaningful removal/pressure control |
| Krang | 87.43% | not a primary nerf anchor |
| Bebop & Rocksteady | 82.54% | broad favorable result, matchup structure unclear |
| April O'Neil | 92.29% | not a primary nerf anchor |

Shredder and Raphael demonstrate that Casey is not universally dominant. Their pressure, removal,
and stronger immediate threats can punish time spent deploying or equipping artifacts. That makes
them important controls for any pre-balance change: a reduction must not remove the deck's ability to
contest those pairings.

Leonardo, Michelangelo, and Splinter are better evidence for the starting environment than April or
Krang. Casey's 68.21%, 65.94%, and 62.99% results are still subject to Equipment, combat, recursion,
and Pilot limitations, but their breadth suggests that a small reduction in redundant payoff is
reasonable to investigate. Donatello remains mixed ownership. April and Krang are explicitly not
used to choose nerf magnitude.

## Matchup structure and controls

Casey appears to gain broad advantage when the opponent gives the artifact/Equipment engine time to
establish a board. Against Leonardo, Michelangelo, and Splinter, the result may reflect genuine
gear-plus-board pressure, but also simplified attachment and combat choices. The distinction must be
tested after a small pre-balance change.

Against Raphael at 41.19%, Casey faces early team pressure and combat before gear can compound.
Against Shredder at 37.28%, removal and threat quality punish setup and may clear the carrier or
payoff that would otherwise convert equipment into damage. These controls argue against reducing
Casey's creature carriers or Jury-Rig access as the first lever.

Donatello at 75.83% is informative about a slower technical plan but remains mixed because
Donatello's Pilot and recovery semantics are bounded. Krang at 87.43% and April at 92.29% are
descriptive extremes only; their simulator limitations make them unsafe anchors for a two-to-four
card revision.

## Semantic inventory

The following inventory covers every nonland card in Prototype 0.1. “Direction unknown” is used
where the repository cannot justify a safe bias claim.

| Card | Intended role and identity importance | Cardcade coverage and Pilot interaction | Bias direction |
| --- | --- | --- | --- |
| Casey Jones, Jury-Rig Justiciar (4) | Haste and artifact access; the primary scrappy gear-finding identity card. | Partial but high-complexity: top-four artifact selection, reveal, hand movement, and random bottom ordering have bounded evidence. AcceptancePilot receives deterministic legal choices rather than evaluating future gear quality. | Direction unknown; access may be understated or over-simplified. |
| Casey Jones, Vigilante (3) | Risky card velocity: draw three now, accept three random discards later. Central to chaos and resourcefulness. | Partial-to-strong for the delayed trigger/RNG chain and random discard evidence, but whether the Pilot values the temporary hand advantage or the delayed cost is not human-equivalent. | Direction unknown. |
| Mutant Town Musicians (3) | Alliance pressure when bodies enter; links artifact-produced Robots to combat. Important but not the sole identity engine. | Strong for observed Alliance/trample paths, but maximum-attacker behavior can convert bodies into damage without human caution. | Plausibly overstated in wide-board states; not proven. |
| Null Group Biological Assets (2) | First-strike attacker and discard/draw smoothing; helps turn awkward gear into velocity. | Partial: discard/draw choice and combat timing are bounded; Pilot filtering behavior is deterministic. | Direction unknown. |
| Purple Dragon Punks (4) | Cheap carrier and artifact-mana acceleration; enables early gear and artifact spells. | Partial: mana restriction and sequencing are represented, but the Pilot's lowest-cost creature policy may favor immediate deployment over preserving a carrier. | Direction unknown. |
| Ravenous Robots (4) | Artifact-cast triggers create more Robot bodies; central artifact-board growth engine. | Partial: token creation is represented, but repeated artifact entry, token timing, haste activation, and attack selection are not human-strategic. | Plausibly overstated when maximum attacks exploit the board; direction not proven. |
| Rock Soldiers (3) | Larger artifact body and artifact removal on entry; stabilizes or clears opposing artifacts. | Partial: bounded artifact destruction exists, but target selection and four-mana timing are deterministic. | Direction unknown. |
| Hard-Won Jitte (4) | Equipment payoff granting double strike; major burst and combat identity. | Partial: Equipment/attachment context is a known boundary; strike-damage evidence recognizes the card but specifically records unsupported attachment context. | May be overstated if equip friction is simplified; may be understated if attachment choices are cumbersome. |
| Improvised Arsenal (4) | Scales equipped creature with artifact count and can copy itself; the densest payoff/board-growth lever. | Partial: artifact/token creation paths exist, while copy-Equipment and attachment choices are not fully represented as human decisions. | Plausibly overstated through simplified redundant payoff; direction not proven. |
| Manhole Missile (3) | Blocker removal and optional hand filtering; interaction that opens a combat route. | Partial semantic warning: the catalog reports zero recognized interaction for the deck despite bounded damage/hand-bottom paths. AcceptancePilot selects available damage targets deterministically. | Direction unknown; targeting simplification may overstate or understate. |
| Mouser Foundry (2) | Artifact enters/leaves create Robots; expensive sacrifice damage provides late interaction. | Partial: token creation is represented, but the five-mana sacrifice activation is explicitly bounded/not fully accepted as a general damage path. | Likely understated for its removal role; direction unknown overall. |
| Spicy Oatmeal Pizza (2) | Artifact-based burst damage and life-risk/recovery; reinforces scrappy all-in play. | Partial: Deal Damage and Food-like sacrifice/life paths are bounded, but timing and risk evaluation are Pilot-bound. | Direction unknown. |

The largest semantic uncertainty is Equipment: the deck's defining action is not a cleanly neutral
simulation surface. Casey-specific randomness is better instrumented than generic random choices,
but a deterministic AcceptancePilot still does not show whether a human keeps a risky hand, chooses a
carrier, delays an equip, or values a double-strike window. These caveats make a small payoff-density
experiment safer than an access, carrier, or random-behavior change.

## Candidate levers

| Lever | Why it could matter | Simulation confidence, identity risk, and matchup effect | 1--2 copy pre-balance experiment? |
| --- | --- | --- | --- |
| Gear redundancy: Hard-Won Jitte / Improvised Arsenal | Eight payoff copies may make equipment pressure too consistently available against slower decks. Arsenal's artifact-count scaling and copy potential can compound normal board growth; Jitte supplies abrupt double-strike damage. | Mixed confidence because attachment friction is bounded. Removing one copy of each preserves carriers and access while opening modest counterplay. It should reduce broad wins versus Leonardo/Michelangelo/Splinter without intentionally changing the Shredder/Raphael control pattern. | **Yes; safest primary lever.** Candidate shape: `-1 Hard-Won Jitte`, `-1 Improvised Arsenal`. This is not a decklist or approval to edit. |
| Gear access: Jury-Rig Justiciar | Four copies make the deck consistently find artifacts and express its identity. | Too simulator-dependent: selection is high-complexity and the card is the clearest Casey-specific identity anchor. Cutting access could make the deck generic and may not correct actual payoff excess. | No, defer. |
| Artifact-board growth: Ravenous Robots / Mutant Town Musicians / Mouser Foundry | Robots and Alliance convert each artifact/body into more board pressure. | Plausible broad contributor, but changing several engines at once would hide causality. Robots and Musicians are identity-bearing carriers of the deck's scrappy swarm feel. | Not as first experiment; reserve for refinement. |
| Interaction: Manhole Missile | Three copies may clear blockers and convert gear pressure into burst. | Too semantic-dependent: recognized interaction is inconsistent in the catalog, so a reduction could punish Casey against Shredder/Raphael without addressing simulated simplification. | No, defer until human games establish its actual contribution. |
| Burst/randomness: Casey Jones, Vigilante | Draw-three/random-discard creates volatile resource spikes; double-strike adjacency may produce sudden kills. | Random lifecycle is instrumented, but the fun and fairness of the result are human questions. Cutting it first could remove Casey's character. | No, defer. |

## Safe provisional pre-balance versus deferred changes

**Safe enough for provisional pre-balance:** a two-slot reduction within the redundant Equipment
payoff package, represented as one fewer Hard-Won Jitte and one fewer Improvised Arsenal in a later
candidate decklist. It uses one primary lever, is reversible, leaves the four Jury-Rig Justiciar
access cards and creature carriers intact, and does not attempt to fix every simulator limitation.
It should be evaluated against Leonardo, Michelangelo, and Splinter while checking that Shredder and
Raphael remain meaningful controls.

**Too simulator-dependent to touch yet:** Jury-Rig access, Manhole Missile, Casey-specific
Vigilante randomness, the full Ravenous Robots/Musicians engine, and broad changes to carriers or
artifact density. Those levers need human evidence about attachment friction, target quality,
counterplay, and fun before a change is defensible.

## Ranked candidate hypotheses

1. **Gear payoff redundancy:** candidate shape `-1 Hard-Won Jitte / -1 Improvised Arsenal`.
   Expected upside is modestly fewer automatic equipment payoffs and more opponent recovery windows.
   Risk is reducing Casey's signature double-strike and artifact-scaling moments. This is the safest
   provisional pre-balance experiment.
2. **One-package Arsenal reduction:** a narrower `-1/-2` reduction from Improvised Arsenal alone.
   This keeps Jitte's memorable combat identity intact but may leave the artifact-count scaling that
   appears most capable of compounding board growth. It is a useful alternate if human play shows
   Jitte is fun and fair while Arsenal is repetitive.
3. **Artifact-board growth adjustment:** one small reduction from Ravenous Robots or Mouser Foundry.
   This may lower token snowballing or late interaction, but risks changing the scrappy artifact
   network and is less attributable than the gear-payoff lever.
4. **Access or interaction adjustment:** Jury-Rig Justiciar or Manhole Missile.
   These are not first experiments because their selection/targeting semantics are too bounded and
   they could weaken the Shredder/Raphael controls.

These shapes are hypotheses only. No decklist is created, and the candidate change still requires a
separate explicit approval.

## Post-pre-balance human-play plan

Under the updated Design Studio direction, human play should begin after the smallest provisional
pre-balance experiment rather than being asked to discover the already-obvious gross environment
extremes from the frozen list. Use a minimum useful sample of 24 games: six each against Shredder,
Raphael, Leonardo, and Michelangelo or Splinter, with three games on the play and three on the draw
per pairing. Add Donatello if capacity allows, but do not use April or Krang as primary calibration
of fun or balance.

Record whether Equipment feels fun rather than cumbersome; whether Casey still has enough carriers;
how often Jury-Rig finds useful gear; whether Improvised Arsenal and Jitte create repetitive or
memorable decisions; whether Vigilante's random outcomes are fun for both players; whether sudden
kills feel fair; whether opponents can recover after a gear turn; whether Casey remains distinct
from Raphael; mana and legendary congestion; and whether the revised environment produces enjoyable
scrappy games rather than merely lower numbers.

The pre-balance hypothesis is weakened if the two-slot reduction does not change perceived pressure,
if the removed payoffs were rarely relevant, if Casey loses too many memorable decisions, or if
Shredder/Raphael become non-games. It is falsified as a useful lever if human players identify
Jury-Rig access, interaction timing, or opponent semantic weakness as the dominant issue instead.
Those observations should guide a later refinement packet rather than trigger a broader rebalance.

## Recommendation

The evidence supports a small, reversible pre-balance experiment focused on redundant Equipment
payoffs. It does not support touching gear access, carriers, Manhole Missile, or Vigilante until
human play tests the post-pre-balance environment. Casey's identity remains scrappy,
improvisational, gear-driven, aggressive, and distinct from Raphael. Any future decklist requires
separate explicit approval and must preserve Prototype 0.1.

PROCEED_TO_CANDIDATE_DECKLIST
