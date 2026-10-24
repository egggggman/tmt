# HQ proposal — Game Night First cross-department alignment

**Date:** 2026-10-24
**Status:** Proposed for independent review; NOT accepted policy until HQ/user acceptance and merge.
**Basis:** Main at `cb1da2b06cde51fc230529e02d9c1aaa461ea64f`, existing playable-first principle, human game-day records, and 2026-10-24 HQ conversation.
**Ownership:** HQ coordinates. Each department retains implementation authority.

## Mission and success criterion

Build a cohesive, fun, distinctive set of Standard-legal 60-card TMNT decks that people can bring to a table, teach, play, and want to play again.

**Playable first. Explainable increasingly. Fun is the destination.**

Mechanical reliability and reasonable fairness are required; a mathematically perfect 50% win rate for every deck is not. Simulation is evidence, not a substitute for human enjoyment. Do not hold up safe, legal tabletop prototypes merely because full Cardcade calibration is unfinished.

## Two distinct gates

### Gate A — Game Night Ready

- Each presented deck has an explicitly identified, frozen 60-card list with card identity and Standard legality verified for its intended play date.
- Structural checks pass; a human can understand the deck's plan and key actions; known severe rules defects and obvious non-games receive triage.
- Initial human sessions are authorized as observational testing, with simple matchup, pilot, turns, outcome, rules confusion, enjoyment, and desire-to-replay notes.
- Game Night Ready does **not** assert statistical balance, full simulator compatibility, or final product acceptance.

### Gate B — Refined Battle Set

- Cardcade runtime, oracle semantics, replay identities and outputs have passed independent review; authorized calibration controls are complete.
- The matchup matrix, seat effect, game pace, mana consistency, non-games, and synergy opportunities are analyzed.
- Design Studio tests the smallest evidence-backed deck revisions against preserved controls; user-facing fun and fairness feedback guides final acceptance.
- Physical products are verified for printing, cutting, fit, handling, and real-table use.

## Department handoffs

| Department | Responsibility under this proposal |
| --- | --- |
| HQ | Coordinate priorities; make/record roster and gate decisions; commission independent acceptance; never self-merge an implementation candidate. |
| Design Studio | Own legal deck construction, design intent, frozen prototypes and revisions; complete new candidates and iterate only from evidence. |
| Cardcade | Own engine validity, deterministic replay, telemetry, transparent matchup evidence and error diagnoses. No autonomous deck redesign, no speculative calibration. |
| Mr. Paperback | Deliver travel-ready physical Game Night kit, accessible quick-start aids, tokens, dividers and trackable matchup notes; verify physical print/cut/fit. |
| Canon | Check character representation, accessible flavor and recognizable themed identity; do not overrule playable mechanics. |
| Underground Press | Keep publication distinct; support promotion/event storytelling when requested, without blocking deck readiness. |

## Roster ambiguity requiring explicit HQ decision

Authoritative frozen competitive environment remains **Baseline 005: ten decks**, including Bebop & Rocksteady.

- Baxter's Mutant Menagerie: draft 60-card eleventh challenger, PR #362, not independently validated or promoted.
- Bad Guys — Shredder's Cronies: PR #363 is a **research sandbox**, not a verified 60-card prototype.
- Issue #359 proposes broadening/replacing the Bebop & Rocksteady slot; conversations have also discussed **adding** Cronies for a 12-deck collection. These are different roster models. **No roster change or 12-deck promotion is accepted by this proposal.** HQ must explicitly choose replacement vs separate additional deck, preserving B&R history either way.

## Cardcade evidence and operational boundary

- PR #358 merged R9-B evidence: 323/900 (35.89%) vs historical reported control 316/900 (35.11%), +0.78 points. Original Attempt 9 raw artifact unavailable; insufficient evidence for promotion.
- PR #356 is a draft repair reporting 2,107 regression passes and 100/100 bounded diagnostic games; self-results are not independent acceptance.
- The 4,500-game Baseline 005 control is **not automatically authorized**; prior fail-closed controls and repairs must remain distinguished.
- Windows-local checks (2026-10-24): local and remote main both `cb1da2b`; no Cardcade Python process seen; G: TMT volume healthy, historical directories present; external archive writer/destination still unverified.
- Simulator need not be continuously running. Preserve each historical result, prototype, manifest, hash, and runtime identity. Fix simulator errors in simulator code, not in decks.

## Near-term sequencing (parallel where safe)

1. Cardcade: independent review of PR #356 repair chain, plus portable historical validator and evidence output/archive-path checks. Stop if engine provenance or deterministic replay remains in doubt. Do not start large control automatically.
2. Design Studio: independently verify Baxter draft; finish a frozen Cronies candidate; report legal/structural gaps and basic pilot instructions before Game Night.
3. HQ: resolve the 11-versus-12 roster ambiguity and document that decision separately.
4. Mr. Paperback: prepare lightweight practical test materials and tracking, not a prematurely final collector run.
5. Human testers: play ready decks early and log fun, pace, friction and rematch interest. Treat these as qualitative notes rather than statistical win-rate proof.
6. After independent engine acceptance, HQ may authorize a distinct complete Baseline 005 calibration; Design Studio owns response to any balance finding.

## Acceptance checklist for this proposal

- [ ] Independent review verifies no existing policy or accepted baseline is overwritten.
- [ ] HQ approves the two readiness milestones and cross-department remit.
- [ ] HQ resolves roster cardinality separately.
- [ ] Relevant department status/roadmap/decision files are synchronized in a subsequent PR or follow-up commit.
- [ ] No deck revisions, game simulations, or physical production changes are silently authorized.

**COWABUNGA.**
