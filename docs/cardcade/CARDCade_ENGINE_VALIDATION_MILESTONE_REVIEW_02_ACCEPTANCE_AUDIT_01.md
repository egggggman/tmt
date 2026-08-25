# Cardcade Engine Validation Milestone Review #2 Acceptance Audit #1

## Verdict

**ACCEPT — the Milestone Review #2 `CONDITIONAL ADVANCE` verdict follows from accepted Cardcade
evidence, preserves the coverage and balance boundaries, and authorizes only specification and
readiness audit of a larger bounded coverage-aware engine-validation stage.**

This is an evidence-only audit. It does not authorize Stage 0.2 execution, Action #17, balance
analysis, calibration, Pilot or deck changes, Design Studio revisions, or Prototype 0.3.

## Audited artifact

- report: `docs/cardcade/CARDCade_ENGINE_VALIDATION_MILESTONE_REVIEW_02.md`;
- expected SHA-256: `b1529f24ac5963f5164432aa3808e5c9396866a71bd2b1975b9e1251071cb6b3`;
- independently reproduced SHA-256:
  `b1529f24ac5963f5164432aa3808e5c9396866a71bd2b1975b9e1251071cb6b3`.

The milestone review was not modified during this audit.

## Evidence reconstructed

The review's quantitative progression agrees with the accepted Smoke and post-Action evidence:

| Checkpoint | Coverage-complete | Coverage-limited | REACHED / UNSUPPORTED |
| --- | ---: | ---: | ---: |
| initial Coverage-Aware Smoke 0.1 | 5/180 | 175/180 | 692 |
| post-Action #14 | 10/180 | 170/180 | 599 |
| post-Action #15 | 17/180 | 163/180 | 562 |
| post-Action #16 | 18/180 | 162/180 | 548 |

The accepted post-Action #14 interpretation records the `5 → 10` and `692 → 599` movement, 180
byte-identical duplicate pairs, and zero runner stops or invariant violations. The accepted
post-Action #15 Results Audit and interpretation independently record `17/180`, `562` unsupported
reaches, 180 byte-identical duplicate pairs, zero invalid games, zero stops, zero invariant
violations, and `balance_valid: false` for every game. Their repository SHA-256 values reproduce as
`20aff69398715d09033bb96d40ca4f324b55f939948821b263af6722b4589ea1` and
`654916ae9a446e2c1a91dfbc4c78561afab4ac40c4f75511db05246bddd4241f`.

The accepted post-Action #16 Results Audit reproduces as
`2538d77a2e5211d08e2f3fac1d406a574e956dde493c7d10516d3a461f5d7bda`. It independently
reconstructs the 45-pairing, 180-distinct-game, 360-execution matrix; 180/180 byte-identical
duplicate pairs; 18 coverage-complete, 162 coverage-limited, and zero invalid games; 548
REACHED / UNSUPPORTED occurrences; zero runner stops; zero invariant violations; and
`balance_valid: false` for all 180 games. The accepted post-Action #16 interpretation reproduces as
`acfff1d3ba0d66d5d5052f015fedb861c298b774aee9ed3cff43963d6f20b90e` and establishes exactly
25 residual exact-fragment clusters, 160 nonzero overlaps, and 14/25 clusters with zero solo
clearance.

The four complete matrix runs therefore supply 720 versioned distinct-game reports and 1,440
executions as regression and engine-validation evidence. They are not 720 statistically independent
balance samples. The review states this limitation explicitly.

## Mechanical credibility versus semantic coverage

The review correctly treats mechanical credibility as a claim about represented transactions and
their evidence, not about complete Magic semantics. The accepted record supports:

- exact duplicate determinism across every complete 180-game matrix;
- zero stops, invariant violations, invalid games, or duplicate mismatches in accepted artifacts;
- real fail-closed stops on lifecycle, provenance, Stack/Priority, token-identity, frozen-input, and
  persistence defects before later clean reruns;
- reconstructive authentication of executions, opportunity witnesses, contexts, typed events,
  source incarnations, zone lineage, and aggregate membership;
- accepted Stack/Priority, child-trigger deferral, combat-trigger, First Strike, terminal-SBA, failed
  Draw, and post-resolution behavior for represented shapes;
- historical trigger-time facts anchored to independent original event evidence rather than only
  mutually consistent derived registries;
- authoritative battlefield characteristics where the implemented rules predicates require them;
- versioned cross-platform Git-clean input identity with dirty/missing/untracked drift rejected;
- unchanged deterministic Acceptance #001 trajectories through Actions #14–#16.

The evidence does not establish complete targeting, response timing, replacement effects,
continuous effects, combat legality, search, choice, or alternate-zone semantics. The review names
those limitations and therefore does not convert mechanical credibility into a complete-engine
claim.

## Coverage versus balance eligibility

The review correctly preserves three distinct propositions:

1. a mechanically clean game can still be coverage-limited;
2. a coverage-complete game has no known reached unsupported opportunity under the represented
   conformance model;
3. neither classification makes the game balance-valid.

The accepted Smoke contract reconstructs `balance_valid: false` for every game, including all 18
current coverage-complete games. The review requires Stage 0.2 to retain derived structural balance
exclusion and forbids win-rate, turn-length, or matchup conclusions. It does not silently admit the
162 coverage-limited games—or the 18 coverage-complete games—into balance evidence.

## Duplicate executions versus independent games

The report consistently identifies each matrix as 180 distinct games and 360 executions. It treats
the second execution of each game as reproducibility evidence and not an additional sample. Its
proposed design example similarly labels 450 new-seed games duplicated exactly as 900 executions,
not 900 independent games. This is consistent with the accepted Smoke evidence contract.

## Action-construction economics

The residual graph supports the report's conclusion that targeted Action construction remains
available but no longer needs to be automatic:

- 14 of 25 clusters clear no current game alone;
- every cluster clearing at least three games is compound or broad;
- the remaining bounded candidates have low solo clearance or limited exposure;
- repeated use of the same two-seed matrix has diminishing power to expose new engine interactions.

The Ray Fillet path is correctly treated as a prerequisite-plus-Action sequence, not as an already
bounded Draw Action. Its 30 occurrences across 29 games and 14 matchups produce only two static solo
clearances. Existing mana, counter, Stack/Priority, Draw, and failed-Draw machinery is relevant, but
the engine still needs authoritative selection and atomic removal of a +1/+1 counter from a
controlled creature as a nonmana activation cost, including legality, payment evidence, rollback,
identity, and revalidation. That prerequisite requires its own governed evidence boundary before
the Ray Fillet transaction becomes small.

The review also distinguishes correctly among:

- bounded future candidates such as mill three, ordered Draw/discard, artifact-entry self-counter,
  temporary Reach, and graveyard self-return;
- prerequisite chains involving counter-removal costs, optional constrained targets, disjunctive
  target predicates, or color-choice/mana treatment;
- compound semantics combining multiple actions, choices, permissions, targets, or durations;
- broad engine programs such as stun replacement, Menace legality, alternate-zone/finality
  replacement, and reactive Stack targeting;
- low-exposure omissions whose explicit fail-closed classification can safely remain during the
  next validation stage.

This taxonomy is supported by the accepted 25-cluster graph and does not infer implementation
readiness from occurrence frequency alone.

## Challenge to conditional advancement

Known unsupported semantics do not by themselves defeat advancement because the proposed next
stage asks an engine-validation question, not a complete-game or balance question. The accepted
system can continue to produce useful evidence only while it:

- authenticates every EXECUTED / REACHED / PRESENT classification;
- stops immediately on nondeterminism, invariants, illegal mutation, silent approximation,
  unauthenticated evidence, or incomplete execution;
- keeps coverage-limited games explicit;
- derives `balance_valid: false` for every game;
- uses new frozen seeds and counts duplicates only as reproducibility evidence;
- preserves independently auditable success and failure artifacts.

The milestone review makes all of these conditions mandatory. Its proposed Stage 0.2 question—does
the represented engine remain deterministic, invariant-clean, provenance-authentic, and fail-closed
over more frozen seeds, and does the larger sample reveal new foundational interactions or change
the semantic-priority graph—is supported by the evidence progression. A larger predeclared sample
can test rare lifecycle combinations and graph stability even when most games remain
coverage-limited.

The conclusion would be unsupported if Stage 0.2 were intended to measure deck strength, if
unsupported opportunities could be silently ignored, or if the report authorized execution before
specification and readiness review. It does none of those things. `CONDITIONAL ADVANCE` is therefore
more accurate than unconditional advance, automatic Action construction, or HOLD/remediate.

## Historical 900-game smoke

The report correctly keeps the historical 900-game smoke retired. Its original design lacks the
accepted coverage classes, authenticated duplicate policy, fail-closed atomic evidence,
cross-platform frozen-input reconstruction, and structural balance exclusion. Scale cannot repair
those missing contracts.

The number 900 may reappear only as the arithmetic result of a new coverage-aware specification.
The report's example—45 pairings, five new seeds, two orientations, and exact duplicates—would be
450 distinct games and 900 executions. It explicitly rejects counting the duplicates as additional
games and does not authorize that design or sample size.

## Authorization boundary

The audited report authorizes only specification and independent readiness audit of Coverage-Aware
Engine Validation Stage 0.2. It explicitly does not authorize:

- Stage 0.2 execution;
- Action #17;
- balance analysis;
- calibration;
- Pilot changes;
- deck changes;
- Design Studio revisions;
- Prototype 0.3.

## Final decision

**ACCEPT — the `CONDITIONAL ADVANCE` verdict is evidence-backed. Cardcade may specify and
independently audit a larger bounded coverage-aware engine-validation stage, but no execution or
downstream gameplay/design work is authorized by this audit.**
