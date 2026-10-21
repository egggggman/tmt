# Cardcade dual-purpose telemetry feasibility

Status: proposal only; no gameplay changes or simulation authorized.

The existing Round 9-B runner authenticates the runtime, deck and schedule; selects 900 games in nine balanced 100-game cells; repeats each cell for deterministic replay; and writes a separate evidence artifact.

Currently available summary measures: per-opponent wins/draws, first-player results, ending turns, casts, interaction casts, activation events, aura events, and ETB life gain events. The published markdown does not provide legal attack opportunities, cards stranded in hand, or causal card contributions.

Before implementation, Cardcade should document the originating event/state field and attribution rule for every new measurement. Proposed metrics include early creature deployments, actual attacks, combat damage, deaths, mana utilization, pilot choices, mechanic coverage, and invariant violations. A chosen action is not proof of all legal opportunities. Missing instrumentation must be marked unavailable rather than zero. Coverage novelty must be compared only across compatible instrumented runtimes.

Gate 1: Design Studio provides exact legal 60-card candidate and single-mechanism rationale. Gate 2: Cardcade demonstrates measurable fields with deterministic fixtures and checks runtime identity. Gate 3: HQ separately authorizes one 900-game isolation. Gate 4: preserve artifact and full-cell replays, distinguish engine reliability from balance, and document the missing historical raw-control limitation.

Stop on runtime errors, invalid provenance, replay mismatch, or evidence corruption. Baseline 005 and historical candidates remain frozen. The trial may be reverted to one-card probes if additional metrics are unreliable or not actionable.
