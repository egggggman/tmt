# PR #408 Independent Evidence Audit

## Verdict: REWORK

The evidence-triage diagnosis is reproducible and substantially correct, but the wrapper omission it identifies must be fixed and independently verified before another diagnostic game. Historical stop records remain intact and are not cleared by this verdict.

## Source and preserved artifact identities

- Evidence report source: `12167fba59d27428af8558f73569028caae1508b` (PR #408).
- Original game engine source: `67b9bb3083c9f4b2fe02e7fed258c4739581225f` (PR #404).
- Evidence directory: `C:\projects\tmt\.cardcade-diagnostic001-report\docs\cardcade\diagnostic_game_001\evidence`.
- Preserved output directory: `C:\projects\tmt\.cardcade-diagnostic-001-pr404-67b9bb3-20261107`.
- Reviewer source import for replay: `C:\projects\tmt\.diag001-pr404-67b9bb3\src\tmnt_design_studio\stage002.py`.
- Python 3.12.10; read-only replay only. No game was run.

All nine files listed in `artifact_sha256.json` were independently rehashed and matched. The event stream and snapshot contain 1,864 events. The exception, status, trace, snapshot, reconciliation, and manifest were read without modification.

Using the preserved PR #404 source, the canonical `april-casey:canonical:7231` spec, and saved snapshot, the Stage 002 manifest digest matched the saved manifest and `reconcile_snapshot()` reproduced the saved reconciliation object exactly. The output contains the same three stop records.

## Stop record findings

1. **`illegal_mutation` after terminal combat — genuine engine control-flow stop.** The preserved exception follows lethal first-strike damage and a `player_lost` event. The turn-16 game state is already terminal: Casey is the winner, April is below zero life and marked lost, Casey is at 17 and not lost, Stack is empty, and no priority is open. The tail is combat damage → player loss → damage-step resolved; the exception is the prohibited attempted transition after that terminal state. This is the PR #407 correction's target. PR #407 independently passes its historical reproduction and synthetic terminal checks, but the historical record remains unchanged.

2. **`presence_evidence_missing` — confirmed evidence-capture omission.** In `run_once.py`, the exception walker overwrites its selected traceback frame whenever a frame contains local `game`. It therefore retains the innermost `_checked_action` frame, which has `game` but lacks the `presence` ledger. The outer `run_game` frame has both, but is not selected. Exception handling consequently captures a snapshot without `stage002_presence`; ordinary finalization was skipped because `run_game` raised. This is not evidence that the historical game lacked the objects. It is a capture-path defect that must be corrected and verified before a new diagnostic.

3. **28 invalid execution references — evidence dependency, not independently proven false attribution.** Under PR #404's authoritative execution index, all 28 references match their semantic key/Oracle fragment and source/evidence identity. The set comprises 17 resolved triggers, six activated abilities, two damage events, one Food activation, one token creation, and one trample reference. The trample reference is `combat:1:object-000175:trample`, sourced from object `object-000175` (Casey’s Mutant Town Musicians). The reconciler still rejects these references because it requires their `source_id` to be present in `stage002_presence`. Missing presence therefore prevents final authentication; static identity agreement alone cannot replace the missing presence ledger. Do not delete or reclassify these stops.

The preservation directory and frozen historical G: archive were not modified. No deck, baseline, or historical event data was rewritten.

## Next smallest correction and acceptance conditions

Correct only the exception-capture wrapper so it retrieves the `run_game` frame (or otherwise captures both the live `game` and the matching `presence` ledger) without changing the saved game snapshot or attribution rules. Preserve current historical outputs. Add a deterministic wrapper-level synthetic test that injects an exception after at least one presence record exists and verifies the resulting snapshot contains that same presence evidence. Then run the saved PR #406 snapshot through reconciliation and show the historical three stops remain unchanged; separately prove a newly captured synthetic exception snapshot retains and authenticates presence evidence. Independently review the correction before authorizing another game.

Until that bounded wrapper correction is independently accepted, the next controlled diagnostic is **BLOCKED**. PR #407's terminal fix is accepted separately; the evidence-capture requirement remains outstanding. No new complete game was executed or authorized by this audit.
