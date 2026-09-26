# Calibration V1 Design Studio / Prototype 0.3 Review

Status: **REVIEW ARTIFACT — PROTOTYPE 0.3 REMAINS CLOSED**

This document is the formal Design Studio interpretation of the completed audited
Calibration Protocol V1 run. It authorizes no deck-file edit, no new prototype file,
no engine change, and no additional simulation.

## Decision summary

The audited environment is materially imbalanced, and the imbalance is inspectable
enough to justify a bounded Design Studio design-cycle review. It is not sufficient to
prescribe card swaps automatically. The recommended scope is **AUTHORIZE_LIMITED_DECKS_ONLY**
for hypothesis development and human-play planning involving Shredder, Raphael,
Donatello, and Casey Jones, subject to independent review and merge of this artifact.

This is a recommendation for a limited design cycle, not execution authorization for
Prototype 0.3. Prototype 0.3 remains unauthorized until this review is independently
verified and merged and Design Studio records the next explicit authorization.

## Authoritative evidence chain

- Repository revision: `d07fa01949a98ffccabd45297f4aa4907b0c8d6c`
- Run: `CALIBRATION_V1_20260923T141649Z_3f838930291e`
- Completion audit: `AUDIT_PASS`
- Completion audit artifact: `docs/cardcade/CALIBRATION_V1_20260923T141649Z_3f838930291e/CALIBRATION_COMPLETION_AUDIT_V1.json`
- Analysis: `docs/cardcade/CALIBRATION_V1_20260923T141649Z_3f838930291e/CALIBRATION_ANALYSIS_V1.json` and `.md`
- Distinct games: 184,320; authenticated executions: 368,640; blocks: 2,048
- Overall first-player rate: 93,337 / 184,320 = 50.64% (Wilson 95% CI 50.41%–50.87%)
- Paired same-seed seat effect: +0.64 percentage points (paired 95% CI +0.42 to +0.85), 92,160 pairs

The canonical/reversed aggregate difference is retained only as a descriptive output:
**DECK-IDENTITY CONFOUNDED — NOT A SEAT-EFFECT ESTIMATE**. It is not an engine defect
finding. The paired same-seed result is the appropriate seat-position analysis.

## What Calibration V1 can and cannot tell Design Studio

### Credible deck-balance evidence

The run has complete roster coverage, authenticated duplicates, deterministic evidence
integrity, and broad matchup repetition. It credibly identifies persistent environment
strength differences and extreme matchup polarity. It does not identify the smallest
card-level correction or establish that a deck is unfun.

### Pilot-policy effects

`AcceptancePilot` is deterministic and legality-constrained, but its policy is not a
neutral human-decision model. It plays a land when available, chooses the lowest-cost
creature, attacks with the maximum attacker set, blocks with the maximum block set,
filters when the optional choice exists, and counters supplied opposing spells. These
choices can favor proactive board presence, simple damage plans, and visible immediate
value. The repository does not establish a quantitative correction for that effect.

### Unsupported or bounded semantics

The Foundation Matrix has 10 GREEN / 10 YELLOW / 0 RED / 0 UNKNOWN, but YELLOW means
explicitly unsupported extensions, not simulated neutral coverage. Relevant boundaries
include priority sequencing, attachments/equipment, broader combat, recursion, delayed
effects, some targeted answers, activated/additional costs, and Casey-specific future
random choices. Pilot Fitness V3 also leaves filtering INCONCLUSIVE and does not establish
general pilot competence for all decision surfaces. These limitations can bias individual
deck results, but their direction cannot be inferred safely without a deck-specific
semantic inventory and human-play evidence.

### Theme, product, and play experience

Win rate does not measure character identity, thematic success, accessibility, opponent
fun, or memorable play. Those remain Design Intent and human-play questions. A deck may
be strong and thematically wrong, or weak for reasons that are simulator-owned rather
than deck-owned.

## Per-deck evidence classification

Coverage is qualitative because the repository has no validated denominator for “strategically
important plan.” The bands below are not correction factors: **high** means the central
plan is substantially represented by executed semantics; **partial** means material plan
pieces are bounded or unsupported; **unknown** means the direction of the resulting bias
cannot be established.

| Deck | Classification | Named problem / observation | Plan coverage and ownership assessment |
|---|---|---|---|
| Shredder | `DECK_REVISION_EVIDENCE_CREDIBLE` | Broad overperformance: 75.53%; 8 matchups above 55%, none below 45%. | High for the represented sacrifice/evasive/removal plan; remaining recursion, delayed effects, and broader combat limits are not shown to explain the breadth. Primarily deck/balance hypothesis, with pilot and semantic caveats. |
| Raphael | `MIXED_OR_UNRESOLVED` | Broad overperformance: 74.52%; 8 above 55%, none below 45%. | Aggressive board and combat plan is represented, but maximum-attacker AcceptancePilot behavior, priority limits, and interaction gaps may materially favor it. Deck and pilot/simulator ownership remain mixed. |
| Casey Jones | `MIXED_OR_UNRESOLVED` | Strong overall result: 68.19%; 7 above 55%, 2 below 45%; extreme 92.29% against April. | Artifact plan is visible, but Equipment/attachment semantics and Casey-specific random behavior are bounded or unsupported. Deck and simulator ownership cannot yet be separated. |
| Splinter | `SIMULATOR_LIMITATION_DOMINANT` | Moderate overperformance: 58.48%; 5 above 55%, 3 below 45%. | Recursion and leave/return identity are central to the stated plan, while the catalog records limited or zero recognized recursion. Simulator limitation is the dominant unresolved owner. |
| Michelangelo | `NO_ACTIONABLE_PROBLEM` | 54.18%; 5 above 55%, 3 below 45%, 1 within 45–55%. | Food, Mutagen, counters, and combat-trick plan are represented enough for a descriptive baseline. No revision problem is isolated without play-experience evidence. |
| Leonardo | `SIMULATOR_LIMITATION_DOMINANT` | Underperformance: 44.44%; 3 above 55%, 5 below 45%; 20.43% against Raphael. | Sneak, protection, recursion, equipment, and sequencing are material to the Design Intent but several are bounded or unsupported. The result cannot yet be assigned to the deck. |
| Donatello | `MIXED_OR_UNRESOLVED` | Underperformance: 36.57%; 2 above 55%, 5 below 45%; prior overperformance materially reversed. | Artifact setup is substantially represented, but recovery/answer semantics and the previous Prototype 0.2 intervention complicate attribution. A bounded deck hypothesis is credible; exact ownership is unresolved. |
| Bebop & Rocksteady | `SIMULATOR_LIMITATION_DOMINANT` | Underperformance: 34.32%; 1 above 55%, 6 below 45%, 2 near 45–55%. | Mutagen, token, and split-character plan contains bounded semantic surfaces. The broad low result is not safe deck-revision evidence yet. |
| Krang | `SIMULATOR_LIMITATION_DOMINANT` | Underperformance: 29.84%; 1 above 55%, 7 below 45%; 10.08% against Shredder. | Repository evidence explicitly warns that the engine/rehearsal does not reduce Krang’s cost for affinity. The key namesake plan is therefore not faithfully represented. |
| April O’Neil | `SIMULATOR_LIMITATION_DOMINANT` | Severe underperformance: 23.92%; all 9 matchups below 45%; 7.71% against Casey. | The deck’s answer/tempo plan is materially obscured by the catalog’s zero targeted-removal finding for cards the deck uses as answers. Simulator limitation dominates. |

## Matchup structure

The full 10×10 matrix is preserved in the analysis artifact. Structurally:

- Shredder: above 55% versus April, Bebop & Rocksteady, Casey Jones, Donatello,
  Krang, Leonardo, Michelangelo, and Splinter; 45–55% versus Raphael; below 45% versus none.
- Raphael: above 55% versus April, Bebop & Rocksteady, Casey Jones, Donatello, Krang,
  Leonardo, Michelangelo, and Splinter; 45–55% versus Shredder; below 45% versus none.
- Casey Jones: above 55% versus April, Bebop & Rocksteady, Donatello, Krang, Leonardo,
  Michelangelo, Splinter; below 45% versus Raphael and Shredder.
- Donatello: above 55% versus April and Krang; below 45% versus Casey Jones, Michelangelo,
  Raphael, Shredder, and Splinter; near-balanced versus Bebop & Rocksteady and Leonardo.
- Krang: above 55% only versus April; below 45% versus Casey Jones, Donatello, Leonardo,
  Michelangelo, Raphael, Shredder, and Splinter; near-balanced versus Bebop & Rocksteady.
- Leonardo: above 55% versus April, Bebop & Rocksteady, and Krang; below 45% versus Casey
  Jones, Michelangelo, Raphael, Shredder, and Splinter; near-balanced versus Donatello.
- Michelangelo: above 55% versus April, Bebop & Rocksteady, Donatello, Krang, and Leonardo;
  below 45% versus Casey Jones, Raphael, and Shredder; near-balanced versus Splinter.
- Splinter: above 55% versus April, Bebop & Rocksteady, Donatello, Krang, and Leonardo;
  below 45% versus Casey Jones, Raphael, and Shredder; near-balanced versus Michelangelo.
- Bebop & Rocksteady: above 55% only versus April; below 45% versus Casey Jones, Leonardo,
  Michelangelo, Raphael, Shredder, and Splinter; near-balanced versus Donatello and Krang.
- April O’Neil: below 45% versus every opponent.

The environment-wide range of 51.61 percentage points, median 49.31%, population SD
17.94 points, and only one deck inside 45–55% justify opening a design-cycle review.
They do not justify treating 50% as a mandatory target or prescribing a universal rebalance.

## Historical interpretation

Donatello’s and Krang’s prior overperformance hypotheses are materially reversed in this
run. Leonardo’s underperformance persists, while Splinter moved materially upward from
the earlier near/sub-50 observation. The earlier 52–53% first-player observation is not
reproduced: the current overall rate is 50.64%, and the paired estimate is small. Prior
engine versions and samples are not pooled with V1.

## Revision-gate evaluation

### Gate 1 — Named problem supported by inspectable evidence

**PASS, limited.** Shredder’s broad overperformance and Donatello/Casey/Raphael’s
structural observations are inspectable in the banked matrix and analysis. Low results
whose key plans are not represented are recorded as simulator-limited rather than deck
problems.

### Gate 2 — Problem ownership classified

**PASS, provisionally.** Each deck is assigned a primary classification above, with pilot
and semantic confounds explicitly retained. Several decks remain mixed or simulator-owned.

### Gate 3 — Smallest proposed change and tradeoffs

**NOT YET READY for card-level changes.** The smallest defensible next step is a bounded
hypothesis packet and human-play plan for Shredder, Raphael, Donatello, and Casey Jones:
measure whether the observed strength/polarity survives representative human play and
whether the suspected semantic/pilot confounds are material. No exact card swap is
supported yet. Tradeoffs to track include identity, interaction, pressure, resilience,
and opponent counterplay.

### Gate 4 — Explicit Design Studio authorization

**RECOMMEND `AUTHORIZE_LIMITED_DECKS_ONLY`.** This artifact recommends opening only the
bounded hypothesis/design-review cycle named above. It does not itself authorize creation
or mutation of Prototype 0.3 files; that authorization remains closed until independent
verification and merge followed by the explicit next Design Studio decision.

### Gate 5 — Preserved prototype versioning

**PASS.** Existing `PROTOTYPE_0.1` and `PROTOTYPE_0.2` files are preserved by deck, and
the repository’s versioned deck paths support a new preserved version without mutation.

## Scope and non-actions

Recommended scope: Shredder, Raphael, Donatello, and Casey Jones only, beginning with
evidence review and human-play questions. Do not revise the other six decks from this
calibration alone. No decklist, engine/runtime, production evidence, seed, or prior
prototype was changed by this review.

Prototype 0.3 remains unauthorized pending independent verification and merge of this
review and a separate explicit authorization decision.
