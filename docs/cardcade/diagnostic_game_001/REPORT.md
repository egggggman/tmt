# Controlled Diagnostic Game 001

## Recommendation

**BLOCKED — SPECIFIC CAUSE:** The one authorized Acceptance Match reached a terminal win for Casey, but the Stage 002 runner raised while advancing out of combat after lethal damage. The runner therefore did not return normally. Reconciliation also records an illegal-mutation stop and two silent-approximation records. Do not infer integrated readiness from the terminal winner alone.

No correction or second game was attempted. HQ should decide whether to authorize a bounded terminal-transition/evidence correction before another diagnostic.

## Source and frozen inputs

- Repository: `egggggman/tmt`
- Accepted implementation: PR #404, `67b9bb3083c9f4b2fe02e7fed258c4739581225f`
- Worktree: `C:\projects\tmt\.diag001-pr404-67b9bb3` (detached, clean at run)
- Accepted `main`: `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`
- Python: 3.12.10, `C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe`
- Stage 002 source SHA-256: `c9d7c637bcd8168a5613e20e0cb8689709e4065b0be00bdd8536b9d8491fbbfb`
- Stage manifest digest: `a556f5c03765732f3343270949d09e4a87145e72921582188858ab249e5f98df`
- Frozen card-data JSON SHA-256: `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`
- Frozen card-data manifest SHA-256: `6b5271af75150a361f77e7b89306c709959dfdf497c448dfdc978e5dc9a17950`
- April Prototype 0.1 SHA-256: `684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4`
- Casey Prototype 0.1 SHA-256: `0fc0adbb370ecfddad03692a4229a04b23268739914a8f2a004b8e042ff3cebb`
- Baseline 005 manifest SHA-256: `532bad7e489eb25f3184b5a90487e1361f7a2b19b8c02cac3c4115a0fc3e14bc`

The committed `stage_games()` specification and Acceptance Match #001 documents agree: `april-casey:canonical:7231`, April in seat 0, Casey in seat 1, canonical orientation, seed 7231. The runner constructs one `Game` per `run_game` call, has no outer retry or batch loop, and stops at terminal state or raises at the turn-120 guard.

## Invocation and count

The sole game call was:

```powershell
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe' -B 'C:\projects\tmt\.cardcade-diagnostic-001-pr404-67b9bb3-20261107\run_once.py'
```

The wrapper called `stage002.run_game(ROOT, spec, stage002.AcceptancePilot())` exactly once; metadata records one call, zero retries, zero additional seeds, and no batch/calibration. Two earlier wrapper launches failed before reaching the game call (an output-directory guard mismatch and then a malformed generated newline); the wrapper was corrected, the output directory was confirmed to contain only the wrapper, and only then was the one game invocation made. No game state was created by those preflight failures.

Environment and invocation details are preserved in `evidence/run_metadata.json`; the exact wrapper is `evidence/run_once.py`.

## Observed game

- One game, seed 7231; game ID `april-casey:canonical:7231`.
- The game reached turn 16, regular combat damage.
- April reached −5 life and was marked lost; Casey remained at 17 life and is the recorded winner.
- Snapshot: `terminal=true`, `winner=casey-jones-p0.1`, empty Stack, no active priority.
- 1,864 events: 16 `turn_started`, 11 `spell_cast`, 19 triggers stacked and 19 resolved, 6 activated abilities resolved, 4 April end-step draw commits, 324 priority grants and 324 passes, and 78 `rules_event` records.
- No invariant-violation events. The floating-mana ledger contains no mana productions or payments; this match therefore did not exercise floating-mana production provenance. Spell-payment evidence records 11 casts paid from lands.

The full snapshot, raw events, focused priority/Stack/combat trace, stage manifest, and reconciler result are retained under `evidence/`.

## Failure and classification

The last events show three player-damage assignments in turn-16 combat damage, April's `player_lost` event, and `combat_damage_step_resolved`. The driver then called `Game.resolve_combat_damage`; its continuation attempted `transition_to(END_OF_COMBAT)`, which raised:

```text
ValueError: cannot advance a terminal game
```

The traceback is preserved in `evidence/exception.json`. The final snapshot is terminal and identifies Casey as winner, but the runner call returned abnormally while trying to advance after termination. This is an **engine/runner terminal-control-flow defect**. The reconciler records `illegal_mutation` at turn 16 / combat damage with before/after fingerprints. It reports zero invariant violations, so the captured invariant result does not clear that stop.

The reconciler also records two `silent_approximation` findings: `presence_evidence_missing`, and an unsupported trample/combat evidence set. These are **semantic-coverage/evidence limitations**, separate from the terminal-transition exception. Reconciliation itself completed successfully; its findings remain blocking evidence and are not treated as a clean acceptance.

The pilot made legal actions through the run; this single result does not establish overall pilot fidelity or balance. No repair was made and no automatic continuation occurred.

## Artifact integrity and preservation

The original run output was written to:

`C:\projects\tmt\.cardcade-diagnostic-001-pr404-67b9bb3-20261107`

All run files were copied byte-for-byte into this report under `evidence/`. `evidence/artifact_sha256.json` lists SHA-256 values for the generated run artifacts; the same complete set is present in the original output directory. `evidence/run_status.json` and `evidence/reconciliation.json` preserve the stop classification and counts.

The diagnostic used a separate detached worktree and a new output directory. Accepted main, PR #404, Baseline 005, Smoke 001, frozen decks, and historical outputs were not modified. No source branch, deck, baseline, or historical artifact was changed; no merge, calibration, or additional game was performed.

## Raw evidence index

- `evidence/run_metadata.json` — exact SHA, environment, pairing, seed, input hashes, invocation count.
- `evidence/run_once.py` — one-shot wrapper used for the sole runner call.
- `evidence/stage_manifest.json` — built Stage 002 manifest and digest.
- `evidence/snapshot.json` — complete terminal game snapshot.
- `evidence/events.json` — complete event stream.
- `evidence/priority_stack_combat_trace.json` — focused progression trace.
- `evidence/reconciliation.json` — full reconciliation and stop records.
- `evidence/exception.json` — runner exception and traceback.
- `evidence/run_status.json` — terminal/result/event summary.
- `evidence/artifact_sha256.json` — artifact SHA-256 index.

**Next gate:** HQ review of the terminal-transition defect and separate unsupported evidence findings. No further execution is authorized by this report.
