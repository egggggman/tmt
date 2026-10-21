# Design Studio — Bebop & Rocksteady dual-purpose trial: evidence and candidate design brief

Status: PROPOSAL / NO CANDIDATE AUTHORIZED. HQ reversible workflow trial; not an experiment result.

## Verified source material
- Frozen Baseline 005 deck: `docs/objective-balance-lab/baselines/BEBOP_ROCKSTEADY_OBL_BASELINE_005.txt`, manifest SHA-256 `aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed`.
- Rejected R9-B: `docs/objective-balance-lab/candidates/BEBOP_ROCKSTEADY_OBL_R9_B.txt` (-1 Frog Butler, +1 Stomped by the Foot).
- Published R9-B: 323/900 = 35.89%, vs preserved Attempt 9 report 316/900 = 35.11%; nine replay cells matched, no errors. Original Attempt 9 raw control artifact is unavailable and not independently verified.
- R9-B per-cell wins: Splinter 17, Raphael 31, Casey 28, Donatello 36, Michelangelo 39, Shredder 45, Krang 36, Leonardo 43, April 48.
- Control per-cell B&R wins: Splinter 16, Raphael 29, Casey 29, Donatello 41, Michelangelo 42, Shredder 43, Krang 34, Leonardo 37, April 45.
- Baseline 005 contains 20 lands (10 Swamp, 10 Forest); 2 Frog Butler, 2 Primordial Pachyderm, 3 Stomped by the Foot, 2 Illegitimate Business, and core character creatures.

## Interpretation
R9-B's +7 wins across 900 games and marginal gains in three of the weakest cells do not substantiate that one extra Stomped fixes the problem. Differences in 100-game cells have wide uncertainty. Existing published aggregate/per-cell summaries do NOT identify causal card failures, early-turn development, missed land drops, pilot action selection, or creature survival. Do not invent those measurements.

## Candidate mechanism to investigate (not yet established)
Hypothesis: the deck fails to turn early creature development into *sustained combat pressure* against fast pressure and durable boards, rather than simply lacking one more removal spell.

Alternatives requiring discrimination: slow curve / mana; ineffective combat trades or survival; pilot's attack/block choices; removal timing; matchup-specific card interactions.

## Candidate design brief — gate before exact list
Design Studio should examine available card definitions and existing game telemetry, then propose a *single coherent* 4–6-slot pressure/resilience package if supported, keeping:
- 60 cards, Standard legality, 20-land configuration unless a mana-specific hypothesis justifies changing it;
- Bebop & Rocksteady identity, key character cards, and core aggro/combat pattern;
- Baseline 005 untouched; one new versioned candidate with exact per-card diff, hash, and thematic rationale;
- avoid a disguised repeat of R9-B's +1 Stomped interaction-density hypothesis.

The source evidence does not yet justify naming 4–6 exact substitutions. Card legality, copies, and effect semantics must be verified before submitting the candidate for HQ approval.

## Proposed trial telemetry contract
Attributable per game and by turn when instrumentation supports it: (1) early creature deployments, legal attacks, actual attacks, blockers and damage by turn 3/5/7; (2) creature survival and trades, removal opportunities and resolutions; (3) mana/lands, cards stranded, castability; (4) pilot legal-action opportunity vs selected action; (5) mechanic/action/trigger branches exercised and new coverage per 1,000 games; (6) win/draw, matchup, first-player and ending-turn metrics; (7) invariant failures, replay mismatches and hashes. Label unavailable metrics, never synthesize them. Instrumentation additions require separate engine validation and runtime reauthentication.

## Decision gates and rollback
1. Diagnose mechanism from existing evidence where available; report limitations.
2. Design Studio submits exact proposed 60-card list, single mechanism, structural/legal checks, predicted effects and risks. HQ reviews before execution.
3. After separate HQ authorization, one 900-game isolation on the frozen nine-opponent schedule with balanced starts, authenticated runtime and fail-closed safeguards.
4. Evaluate signal size, polarization, pilot behavior, mechanic coverage, reproducibility and runtime. If not more actionable than one-card probes, HQ may return to the prior workflow. No automatic promotion, combined validation or Prototype 0.3.

No simulation, card revision, merge, or baseline promotion was performed by this document.
