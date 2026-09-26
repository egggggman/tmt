# Prototype 0.3 Pre-Balance Authorization

Decision: **`AUTHORIZE_PROTOTYPE_0_3_PREBALANCE`**

Status: authorization to create four preserved candidate decklists only. No decklist is created by
this artifact.

## Purpose

Design Studio authorizes a conservative pre-balance pass so the first human-play environment is
reasonably competitive and enjoyable without pretending that Calibration V1 establishes a perfect
50% target. The project direction is:

**Calibration -> conservative pre-balance -> fun human play -> refinement**

The governing principle is: **Playable first. Explainable increasingly.** The pass should reduce
obvious extremes, preserve deck identities, use small reversible changes, and move human testing
away from gross simulated polarization. Human evidence becomes the primary refinement input after
the provisional pass.

## Authenticated evidence chain

This decision does not reopen or reinterpret frozen calibration evidence. It relies on the merged
records below:

- Completion audit: `docs/cardcade/CALIBRATION_V1_20260923T141649Z_3f838930291e/CALIBRATION_COMPLETION_AUDIT_V1.json`
  (`AUDIT_PASS`; 184,320 games; 368,640 authenticated executions; 2,048 blocks).
- Corrected statistical analysis: `docs/cardcade/CALIBRATION_V1_20260923T141649Z_3f838930291e/CALIBRATION_ANALYSIS_V1.json`
  and `.md`; audited evidence identity `D202D3B35814E2B67CF2959E73282264CD8AC2B93EA877FB8C8970D1D48616BE`.
- Interpretation review: `docs/design-studio/CALIBRATION_V1_PROTOTYPE_0_3_REVIEW.md`.
- Prior design-cycle authorization: `docs/design-studio/PROTOTYPE_0_3_LIMITED_AUTHORIZATION.md`.
- Merged candidate packets:
  - `docs/design-studio/SHREDDER_PROTOTYPE_0_3_CANDIDATE_PACKET.md`
  - `docs/design-studio/RAPHAEL_PROTOTYPE_0_3_CANDIDATE_PACKET.md`
  - `docs/design-studio/DONATELLO_PROTOTYPE_0_3_CANDIDATE_PACKET.md`
  - `docs/design-studio/CASEY_JONES_PROTOTYPE_0_3_CANDIDATE_PACKET.md`

The four packets provide the deck-specific named problems, tradeoffs, semantic/Pilot caveats, and
candidate shapes that bound this authorization. Their uncertainty is preserved; this decision does
not convert a hypothesis into a statistical correction.

## Authorized decks and bounded levers

Only the following four decks may receive new preserved Prototype 0.3 candidate decklists. Each
deck gets one primary lever and normally two to four changed cards. Exact replacements must be
documented in the decklist PR and remain reversible.

### Shredder -- 75.53%

Problem: broad pressure with too little recoverable counterplay in the represented environment.

Authorized lever: one small reduction in redundancy or pressure consistency. Preserve villainous
sacrifice, interaction, ruthless pressure, and the distinction from Splinter. Do not dismantle the
deck's core identity to pursue a numerical target.

### Raphael -- 74.52%

Problem: broad aggressive success that may combine genuine early-pressure consistency with
AcceptancePilot amplification.

Authorized lever: one small reduction in early-pressure or payoff consistency. Preserve aggression,
confrontation, momentum, risky combat, and the distinction from Leonardo.

### Donatello -- 36.57%

Problem: Prototype 0.2 may have reduced proactive engine reliability too far, while Pilot and
reactive-sequencing limitations remain material.

Authorized lever: one small restorative change, preferably restoring proactive artifact-engine
reliability, setup-to-payoff conversion, or closing ability rather than adding generic power. Do
not turn Donatello into passive draw-go control.

### Casey Jones -- 68.19%

Problem: redundant Equipment payoff density produces broad pressure against slower decks, while
attachment friction and Casey-specific behavior remain simulator-dependent.

Authorized candidate shape: approximately `-1 Hard-Won Jitte` and `-1 Improvised Arsenal`, with
exact replacements deferred to the decklist step. Do not change gear access, creature carriers,
Manhole Missile, or Vigilante randomness under this authorization without a separate justification.
Preserve Casey as scrappy, improvisational, gear-driven, risky, and distinct from Raphael.

## Change-size and preservation rules

- Normally change only 2--4 cards per deck.
- Use one primary lever per deck; do not bundle unrelated corrections.
- Prefer reversible swaps, not wholesale rebuilds or mathematical attempts to force 50% win rates.
- Create a new preserved Prototype 0.3 file for each deck.
- Never overwrite Prototype 0.1, Prototype 0.2, historical evidence, or prior playtest records.
- Document every changed card, rationale, expected upside, downside, identity risk, and validation
  plan in the decklist change.

## Frozen decks

The following remain unchanged and outside this authorization:

- Leonardo
- Michelangelo
- Splinter
- Krang
- Bebop & Rocksteady
- April O'Neil

They may participate in smoke testing and human play, but no revision to them is authorized. Their
Calibration V1 outcomes contain significant simulator limitations or insufficient actionable
evidence for this pre-balance pass.

## Smoke-test boundary

After the four candidate decklists exist, run one small deterministic smoke test only. Its purpose
is diagnostic: detect catastrophic regressions, check directional movement of the 75% decks, check
whether Donatello recovers somewhat, ensure no revised deck becomes a new extreme, and verify
decklist/runtime integrity.

The smoke must not become another Calibration V1. It must not run 184,320 games, claim statistical
calibration, tune repeatedly to simulated win rates, or automatically revise a deck. Use balanced
starting-player positions and deterministic seeds, with approximately 20--100 games per relevant
matchup and priority on the pairings named in the candidate packets.

## Human-play next gate

After smoke validation, proceed to human play from the provisional four-deck pre-balanced
environment. Human testing should evaluate fun and refinement questions:

- whether games feel competitive and recoverable;
- whether each deck still feels like its character;
- whether wins depend on interesting decisions;
- whether repeated or frustrating patterns remain;
- whether Equipment is fun rather than cumbersome;
- whether Casey has enough carriers and fair randomness;
- whether Shredder, Raphael, and Donatello retain their identities;
- whether any deck is still obviously too strong or too weak.

Human results are the primary refinement input. They do not authorize automatic iterative tuning.
Any subsequent card-level change requires a new explicit Design Studio decision.

## Explicit non-actions

This authorization does not permit:

- revisions to the six frozen decks;
- a broad ten-deck rebalance;
- overwriting Prototype 0.1 or Prototype 0.2;
- changing Cardcade engine, runtime, or Pilot behavior;
- modifying production evidence, seeds, or historical analysis;
- running a new full Calibration V1;
- repeated simulator tuning based only on smoke output;
- treating this artifact as authorization to merge decklist changes automatically;
- authorizing Prototype 0.4 or Prototype 0.3 beyond the four named candidate files.

The explicit decision is:

**`AUTHORIZE_PROTOTYPE_0_3_PREBALANCE`**
