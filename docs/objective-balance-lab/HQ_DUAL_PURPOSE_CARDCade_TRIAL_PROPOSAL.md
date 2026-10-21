# HQ Proposal — Reversible Dual-Purpose Cardcade Trial

Status: HQ-authorized experimental workflow; NOT a permanent policy change or deck revision.
Owner: HQ (trial governance); Design Studio (candidate and interpretation); Cardcade (execution, engine validation, telemetry).
Parent control: OBL-BASELINE-005-LTB-REPAIR-CONTROL-ATTEMPT-009. Baseline 005 remains frozen.

## Objective
Evaluate whether a focused, mechanism-driven deck package and dual-purpose telemetry provide more actionable balance and engine-confidence evidence per run than one-card probes. More games increase sampling precision, not protection against systematic simulator/pilot errors.

## Trial scope
- First subject: Bebop & Rocksteady. Design Studio first reviews available R9-B evidence and chooses one coherent mechanism (e.g., early pressure, resilience, or pilot selection). A 4–6-slot substitution package is a design target, not a requirement; exact card identities and legality must be reviewed and approved by HQ before execution.
- Keep original nine-opponent, 900-game isolated schedule and balanced starting-player assignments for the first trial. No automatic expansion.
- Preserve all frozen deck hashes, original coverage ledger, historic prototypes, rejected R9-A/R9-B candidates, and evidence. Never replace the parent control.
- Engine runtime and pilot must be authenticated before the trial. If changed for a genuine defect, repair and validate separately before interpreting balance.

## Evidence contract
Collect, where supported and attributable:
1. Per-cell wins, draws, uncertainty, first-player effects, game length and polarization.
2. Mechanic opportunities/attempts/resolutions, action and trigger coverage, invariant failures and replay mismatches.
3. Turn-indexed mana/land usage, cards stranded in hand, early attackers/blockers, damage and creature survival.
4. Pilot legal-action opportunities, selected/passed actions and policy limitations.
5. Novel mechanic/branch coverage per 1,000 games compared with a compatible reference, explicitly marking unavailable measures.

Execution counts are not causal card-effectiveness evidence. Do not infer missing telemetry or silently weaken provenance. Fail closed on runtime/integrity errors. Require artifact hashes, schema/readback, reproducible seeds, and deterministic replay checks.

## Gates
1. Design Studio supplies an evidence-backed mechanism and exact proposed package; HQ separately approves the candidate.
2. Cardcade performs structural/legal/runtime/preflight checks; HQ authorizes the single isolation.
3. Run 900 games, authenticate and preserve evidence; separate simulator defects from deck results.
4. Design Studio recommends ACCEPT/REJECT/INCONCLUSIVE, considering polarization, theme, pilot quality and uncertainty; HQ decides any next test or promotion.

## Reversibility and evaluation
Compare with the prior workflow on useful diagnostic findings, new mechanic coverage, time/cost, reproducibility and clarity of causal interpretation. If coverage instrumentation is unreliable, the pilot introduces unexplained variance, or results are not more actionable, HQ can terminate the trial and return to one-slot isolated probes. No automatic merge to main, baseline promotion, further simulations or Prototype 0.3 authorization.
