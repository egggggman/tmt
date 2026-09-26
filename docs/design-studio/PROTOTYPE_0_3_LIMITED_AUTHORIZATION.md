# Prototype 0.3 Limited Authorization

Decision: **`AUTHORIZE_LIMITED_DECKS_ONLY`**

Decision date: 2026-09-25

## Authority and evidence

This record follows the merged Calibration V1 Design Studio review:

- Review: `docs/design-studio/CALIBRATION_V1_PROTOTYPE_0_3_REVIEW.md`
- Calibration run: `CALIBRATION_V1_20260923T141649Z_3f838930291e`
- Completion state: `AUDIT_PASS`
- Distinct games: 184,320
- Authenticated executions: 368,640
- Whole-roster blocks: 2,048
- Overall first-player result: 50.64%, Wilson 95% CI 50.41%–50.87%
- Paired same-seed seat effect: +0.64 percentage points, paired 95% CI +0.42 to +0.85
- Repository evidence remains linked through the banked completion audit and corrected analysis artifacts under `docs/cardcade/CALIBRATION_V1_20260923T141649Z_3f838930291e/`.

This is a Design Studio governance decision. It does not change Cardcade, the engine,
the Pilot, the production evidence, the frozen seed table, or any deck file.

## Authorized design-cycle scope

The following decks are authorized for bounded Prototype 0.3 design-cycle investigation:

- Shredder
- Raphael
- Donatello
- Casey Jones

Authorized work may:

- inspect Design Intent and preserved prototype history;
- analyze the audited matchup structure;
- identify deck-specific hypotheses;
- identify simulator and Pilot confounds;
- define human-play questions;
- propose the smallest candidate changes;
- document expected upside, downside, and tradeoffs;
- prepare candidate revision packets for later approval.

## Frozen and out-of-scope decks

The following remain frozen and outside this authorization:

- Leonardo
- Michelangelo
- Splinter
- Krang
- Bebop & Rocksteady
- April O’Neil

Their Calibration V1 findings are simulator-limitation-dominant or do not establish an
actionable deck problem under the merged review. This authorization does not permit a
broad ten-deck rebalance.

## Explicit non-authorization

The design-cycle authorization is not deck-file authorization. The following remain
prohibited:

- actual card swaps;
- creating `PROTOTYPE_0.3` deck files;
- mutating Prototype 0.1 or Prototype 0.2;
- modifying any preserved deck history;
- changing Cardcade engine/runtime or Pilot behavior;
- rerunning Calibration V1 or consuming seeds;
- modifying production evidence;
- expanding the authorized scope.

Any card-level revision requires a later explicit approval after the candidate packet,
human-play evidence, tradeoffs, and validation plan are reviewed. Any future Prototype
0.3 must be a new preserved version; earlier prototype files must remain unchanged.

## Required Prototype 0.3 Candidate Packet

Each authorized deck must have a separate candidate packet before a decklist can be
considered. The packet must contain:

1. named problem;
2. inspectable evidence;
3. Design Intent relevance;
4. simulator/Pilot limitations and confounds;
5. human-play questions;
6. smallest candidate change;
7. expected upside;
8. expected downside and tradeoffs;
9. validation plan;
10. explicit recommendation: **proceed to candidate decklist**, **gather human evidence first**, or **no change**.

Candidate packets are not created by this authorization record and are not implied by
the authorization decision.

## Current state

Prototype 0.3 design-cycle investigation is **LIMITED AUTHORIZATION** for the four named
decks. Actual Prototype 0.3 deck files remain **NOT YET AUTHORIZED**. No deck revision
begins from this record alone.
