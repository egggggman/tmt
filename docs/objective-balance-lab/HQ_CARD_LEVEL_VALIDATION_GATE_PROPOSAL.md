# HQ decision proposal — Evidence-led Cardcade validation gate

Status: HQ-authorized planning checkpoint, pending review/merge. No simulator or deck change authorized.

## Rationale — development learning, not retrospective fault
Prior calibration runs were useful: they established reproducible execution, identified matchup polarizations, and exposed specific questions about gameplay. This is **not recorded as an oversight**. It is an evidence-led improvement to the validation process: **Build → Measure → Understand → Validate → Refine**. Do not discard, overwrite, or retroactively reclassify historical results. Their interpretation is conditional on the recorded runtime and pilot.

## Core decision
Every distinct card in the ten frozen Baseline 005 decks, plus the separate Bad Guys sandbox, needs a traceable validation disposition. Avoid redundant per-card test suites: reuse deterministic tests for shared actions/mechanics, while checking each card's actual Oracle interpretation, costs, conditions, targets, timing, and pilot opportunities.

Card status vocabulary: VERIFIED, PARTIAL, UNSUPPORTED, DEFECT, UNTESTED. Maintain **three independent dimensions**: Oracle semantics; pilot action competence; multi-card/gameplay integration. VERIFIED is permitted only with test identifiers, passing results and runtime identity for all material dimensions.

## Efficient implementation sequence
1. Inventory the ten decklists in the official Baseline 005 manifest, plus `decks/bad_guys/PROTOTYPE_0.1.txt` on its sandbox branch. Deduplicate card names and resolve against the versioned Scryfall snapshot; flag unresolved names, duplicate oracle IDs, missing faces, stale legality, and mismatched text. Preserve the existing 172-fragment Oracle coverage ledger and reconcile, do not reset.
2. Join each card to the actual action/ability coverage ledger and existing tests. Produce a machine-readable card × ability × Oracle/pilot/integration coverage matrix with test IDs, source snapshot hash, runtime hash, evidence link, and status reason. Do not infer VERIFIED from interpreter keyword presence or a deterministic replay alone.
3. Prioritize by (a) gameplay frequency and observed matchup impact; (b) unsupported or partially implemented mechanics; (c) complex timing/choice/targeting; (d) Bad Guys new card package and the Splinter/Casey/Raphael weak cells. Use a risk score for ordering only, not as proof of defects.
4. Implement **small, generic deterministic fixtures** for the highest-risk missing mechanics and a small number of card-specific combinations. For each fixture include positive, negative, boundary, timing, and pilot-opportunity cases where applicable.
5. Triage confirmed defects separately from balance hypotheses. Fix semantics without altering deck lists; authenticate new runtime, re-run affected regression tests and compatible frozen controls before making balance comparisons.
6. Report coverage gained, defects fixed, test reuse, pilot limitations, and remaining risk. Escalate to HQ before any large calibration or deck promotion.

## Evidence and fail-closed rules
- Static text searches, card-name resolution, and reproducible replay are **not** proof of Oracle correctness.
- Distinguish unsupported mechanic from a confirmed defect, and untested from failed.
- No invented opportunity counts, missing game telemetry, or fabricated test results.
- Keep historical Baseline 005 and R9-B evidence; no 900-game launch or baseline promotion from this proposal.
- Do not expand test batches while engine behavior is questionable.
- For Bad Guys, verify Foot Elite, Foot Mystic, Foot Ninjas, Shredder's Armor, Tokka & Rahzar, Bebop & Rocksteady, and interaction/sacrifice actions before gameplay testing.

## Exit gate
HQ may authorize the smallest deterministic smoke only when material card/ability paths in the proposed candidate and opponents are VERIFIED or explicitly risk-accepted, no critical semantic defect remains, pilot can execute the strategy, and the authenticated runtime plus test evidence is published. Otherwise BLOCKED with precise defect IDs and next fixes.

## Current evidence boundary
The frozen Baseline 005 manifest and the 472-entry historical Scryfall snapshot were inspected. A complete deduplicated card inventory, joined coverage matrix, and executable test outcomes have **not** yet been produced. This is an implementation specification, not a claim of completed validation.
