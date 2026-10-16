# Issue #289: artifact-entry trigger provenance correction

## Authority and reproduced defect

This checkpoint is stacked on draft PR #334. Baseline 005, the original 172-row ledger, earlier overlays, historical game evidence, and prior runtime identities are untouched. The first code revision was published recoverably at `cbafb44b36c47075325b68cbf44de1f466970029` before extended validation. No calibration control was run.

The authenticated catalog gives **Donatello, Way with Machines** (three frozen Donatello copies) the complete clause “Whenever an artifact you control enters, put a +1/+1 counter on Donatello.” The existing recognizer, trigger creation, stack, and counter placement execute, but the old resolution required the entering artifact to remain an artifact on the battlefield under its original controller. Reproduction: create Donatello and an artifact, stack its trigger, move the artifact to the graveyard in a priority response, then resolve. The previous runtime emitted `artifact_entry_counter_failed_closed` and placed zero counters on Donatello.

This triggered ability does **not target** the artifact or Donatello. Its qualification is determined when the artifact enters. The generic correction authenticates the immutable entry-event snapshot and matching trigger record at resolution. The original source permanent must still be on the battlefield to receive the counter; its controller may have changed, and an incarnation that left and returned cannot receive a counter from the old trigger. The entering artifact may have left, changed type, or changed controller. The resolution event retains the original entry event ID, entered object ID, and source object ID. Ability suppression after triggering does not remove the ability from the stack.

## Focused and frozen-deck evidence

- Tests use both renamed fixture semantics and the frozen clause's existing recognizer. They exercise priority between entry and resolution, entering artifact departure, source departure/reentry, source and artifact control changes, type changes, independent simultaneous entries, forged event rejection without consuming the stack, counter placement, resulting P/T and state-based checks, and repeated deterministic traces. Existing nonartifact/wrong-controller negative tests remain.
- Six authenticated unchanged Baseline 005 diagnostics pair Donatello against Shredder, Raphael, and Leonardo with balanced seats. All six deterministic replays matched; zero runtime errors occurred. The pilot cast Donatello four times and resolved four artifact-entry counters. No sampled game contained an entering artifact leaving while this trigger awaited resolution; focused fixtures prove that case. The diagnostics do not measure balance.
- Full regression, structural validation, Ruff, and final-head CI are publication gates. Reproduce the overlay with `tools/report_issue289_artifact_entry_counter.py` and the diagnostic with `tools/run_issue289_artifact_entry_counter_smoke.py`. Their machine records are `ISSUE_289_ARTIFACT_ENTRY_COUNTER_CHECKPOINT.json`, `ISSUE_289_ARTIFACT_ENTRY_COUNTER_CALIBRATION_READINESS.json`, and `ISSUE_289_ARTIFACT_ENTRY_COUNTER_SMOKE.json`.

Semantic runtime: `24441ed6387b01e0e1b26d6181b5d5879a2b20243eacb99078b94a4ae50af7f2`; predecessor: `bd3262a9787b5568ce6f9208d95c3e89eefbe5792319eab21e110c069eadb018`. The original ledger SHA-256 remains `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`. The scanner's historical `scanner_reason` is preserved; the reviewed execution and disposition fields close exactly the Donatello trigger row. This is a correction of existing simulator behavior, not a new ability family or retroactive balance validation.

## Remaining resource and calibration risk

| Family | Frozen copies | State |
| --- | ---: | --- |
| Ice Cream Kitty resource activations | 3 | Five ledger entries remain open for its two distinct Oracle abilities. Sorcery-speed sacrifice and draw, plus tap-and-self-sacrifice for life, require transactional resource/cost and pilot assessment. |
| Mutagen Man, Living Ooze | 2 | Two entries remain open: artifact-token activation discount and X Mutagen creation on entry. Both need complete variable-payment/token and cost-modifier execution. |

These are subsequent mechanic families; neither was implemented or reclassified here. The four unbounded important entries remain unchanged until their effects execute or their calibration impact is credibly bounded. Other important gaps remain ranked in the machine readiness record.

**Checkpoint acceptance: subject to final-head CI.** Exactly one complete Oracle fragment closes through a simulator defect correction. The original 172 row identities and all frozen deck hashes are authenticated.

**Baseline 005 calibration readiness: BLOCKED.** There are 0 critical, 23 important, 19 calibration-blocking, and 4 unbounded important entries. No control, deck revision, merge, or promotion follows from this checkpoint.
