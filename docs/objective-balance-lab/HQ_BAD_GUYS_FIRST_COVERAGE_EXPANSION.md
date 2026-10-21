# HQ staged coverage-expansion directive — Bad Guys first

Status: AUTHORIZED WORK PLAN. Execution of simulations and promotion remain separately gated.

## Decision
Use Bad Guys Prototype 0.1 as the first validation target. After its structural, Oracle, pilot and deterministic checks, and after an HQ-authorized gameplay test produces interpretable evidence, Design Studio may propose separate versioned card swaps in the other nine decks to broaden mechanically useful coverage. Cardcade does not design those swaps.

This is an adaptive learning strategy, not a correction for an earlier oversight. Existing calibrations were necessary to establish reproducible baselines and identify high-value validation questions.

## Inventory checkpoint
From the official Baseline 005 manifest on main, all ten decks have 60 cards. There are 143 deck-by-distinct-card occurrences and 105 unique card names across the ten frozen lists (basic lands included). Counts derive from the manifest's exact source_path files, not assumed latest deck prototypes. Bad Guys is a separate sandbox with 60 cards and 17 distinct names; deduplication across the 11 lists and Oracle-action joins are next tasks.

## Gate A — Bad Guys
1. Preserve `decks/bad_guys/PROTOTYPE_0.1.txt` on `design/bad-guys-prototype-0-1`. Its existing repository preflight reports 60 cards, 20 lands, 30 creatures, and historical snapshot legality. This is NOT a validated live legality or engine readiness result.
2. Reconcile the existing 172-fragment Oracle ledger and current deterministic tests to all 17 Bad Guys card names. For each: Oracle semantics, pilot choices, and integration; status VERIFIED/PARTIAL/UNSUPPORTED/DEFECT/UNTESTED, test ID, runtime identity and provenance.
3. Prioritize Foot Elite, Foot Mystic, Foot Ninjas, Shredder's Armor, Tokka & Rahzar, Bebop & Rocksteady, sacrifice/removal interactions. Validate effective mana curve and opening-play opportunity.
4. Run deterministic fixture tests in an authenticated workspace. Repair verified engine defects separately from deck design and reauthenticate the runtime.
5. HQ decides whether to authorize the smallest gameplay smoke. Only after reliable smoke and review consider a 900-game isolation. No auto-promotion.

## Gate B — Other nine decks (after Gate A gameplay evaluation)
1. Inventory and deduplicate each frozen deck's card abilities; map unresolved Oracle and pilot coverage and observed game frequency. Prioritize the highest-risk, high-impact gaps.
2. **Validate before replacing.** A card with missing documentation is a validation opportunity, not automatically a weak card. Prefer adding generic deterministic tests for shared actions.
3. Design Studio proposes a small, coherent versioned sandbox package in one deck at a time. Choose swaps that preserve Standard legality, identity, synergy and gameplay fundamentals; explicitly state expected mechanic coverage and balance effects.
4. Cardcade validates mechanics and runs only HQ-authorized experiments with unchanged opponents, seeds and schedule where comparable. Compare coverage novelty only under compatible instrumentation/runtime.
5. Preserve all old decklists, hashes, pilot versions and telemetry; no silent roster change or Baseline 005 overwrite.

## Stop/rollback criteria
Pause expansion for unsupported critical mechanics, pilot inability to exercise proposed cards, semantic failures, or unreliable telemetry. Return to prior one-card probes if larger coverage-oriented packages do not produce more actionable evidence. Do not change engine assumptions to push win rates toward 50%.

## Current gate
Bad Guys sandbox exists; deterministic validation has NOT yet run. Other nine deck swaps are NOT authorized for execution until Bad Guys is tested and Design Studio presents a reviewable plan. The next action is authenticated Cardcade test execution and a coverage matrix, not a large calibration.
