# HQ Current State

Last synchronized from merged GitHub evidence: **2026-08-26**

This is a compact dispatch view. Historical evidence remains in its original files and PRs.

## Overall

**ACTIVE DEVELOPMENT**

Critical path: **Cardcade engine validation toward a credible controlled calibration gate.**

Prototype 0.2: **FROZEN**

Prototype 0.3: **NOT AUTHORIZED**

## Cardcade

### Accepted foundation

Engine 0.8 architectural foundation remains accepted with the Foundation Matrix at **10 GREEN / 10 YELLOW / 0 RED / 0 UNKNOWN**.

### Accepted post-foundation coverage

The repository has advanced well beyond the older PR #33 status:

- PR #35 — bounded activated-ability delivery / represented Priority-pass lifecycle;
- PR #36 — bounded targeted Return to Hand;
- PR #37 — bounded Trample;
- PR #38 — bounded Lifelink;
- PR #39 — bounded hand-bottom then conditional Draw;
- PR #40 — bounded Discard/Draw attack trigger;
- PR #41 — bounded Sneak casting;
- PR #42 — bounded canonical Food activation;
- PR #50 — bounded creature-dies → Draw-one trigger (Action #13);
- PR #58 — bounded ETB drain/gain/Scry (Action #14);
- PR #59 — bounded permanent-leaves +1/+1 counter trigger (Action #15);
- PR #60 — bounded ETB artifact-condition Draw (Action #16).

Multiple engine/runner corrections between these Actions preserved fail-closed behavior, Stack/Priority ordering, ETB provenance, terminal combat handling, and deterministic evidence.

### Validation stages

Coverage-Aware Smoke / Engine Validation work is now the active validation path.

PR #61 merged the accepted **Engine Validation Stage 0.2 evidence runner and plan-only launcher** with:

- 45 pairings;
- 225 distinct planned games;
- 450? No: the accepted contract records 45 / 225 / 450 / 900 evidence counts across plan/execution/duplicate artifact structure;
- exact independent execution commitments and directory inventory validation;
- `balance_valid: false` during engine validation;
- local validation reported **784 passed / 1 skipped**;
- exact-head CI passed before merge.

**Important:** PR #61 integrated tooling only. Stage 0.2 gameplay execution was not authorized by that merge and remained gated on a merged-main readiness audit.

### Next Cardcade decision

Use the latest merged readiness evidence to determine whether Stage 0.2 execution is now authorized. Do not jump directly to calibration or Prototype 0.3.

## Design Studio

- Ten-deck Prototype 0.2 remains frozen.
- No deck revision should compensate for engine defects.
- Design Studio waits for trustworthy Cardcade evidence and then owns any revision decision.

## Mr. Paperback

- Physical-product work remains independently actionable where it does not depend on deck revisions.
- Sewer Stamps have a repository-visible prototype registration.
- Continue print/cut/fold/fit testing and preserve physical evidence.

## Canon / Source Material

Actionable for targeted support requested by Design Studio, Mr. Paperback, or publishing work.

## The Underground Press

May continue Issue #1 and component-library production independently of the Cardcade gate.

## HQ resilience initiative

**Resilience 0.1 — GitHub Can Run the Project** is now active.

Immediate HQ work:

1. synchronize stale front-door/current-state documents;
2. establish portable Work Packets;
3. establish fresh-clone recovery instructions;
4. make next actions tool-independent;
5. reduce dashboard dependence on chat history;
6. eventually generate status from repository evidence where practical.

## Open documentation item

The Cardcade GUI / DECKDAEMON (DD.0) goal is valid, but it remains subordinate to simulator credibility. The GUI should present authoritative engine/evidence state, never become a second rules engine, and never hide unsupported mechanics.

## Next Move

**Complete the merged-main readiness decision for Cardcade Engine Validation Stage 0.2. In parallel, finish Resilience 0.1 so that the next Cardcade task can be handed to any suitable tool through GitHub without reconstructing chat context.**
