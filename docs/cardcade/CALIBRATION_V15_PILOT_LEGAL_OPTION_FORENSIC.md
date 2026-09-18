# V15 Pilot legal-option forensic

## Classification

`FAIL_CLOSED_STOP -- pilot_legal_option_contract_violation`

Run `CALIBRATION_V1_20260918T142356Z_a870c302` is permanently stopped, non-resumable, and non-reusable. The 2,238 completed games are preserved evidence only; they are not calibration results. No balance analysis occurred.

## Exact failed member

- Member: `b0024-p39-canonical`
- Seed: `63820883886144908208898368752266474304091256763206841102941792321513094444178`
- Orientation: `canonical`
- Seats/decks: `michelangelo` vs `raphael`
- Frozen runtime: `ed332cbae15d49b6690bb004cc5f39bbc8cecdb3`
- V2 seed table SHA-256: `6BE94F69A2E9432E615AEA7A8592D68B6537998B3F7355A60191A29E71DC6E5C`

The stopped run records 2,238 completed members, 4,476 returned duplicate executions, 2,238 authenticated duplicate pairs, and zero observed duplicate mismatches before the failure.

## Preserved reconstruction evidence

- Stopped-run record SHA-256: `BFE92E5FF63592DC55F2FAD4F8D8B576C2DA56E02C9262ECE8ABB725D26DFFE6`
- Complete instrumented decision-state reconstruction SHA-256: `6304D65FC218A66211B4DD90E232C170DB52D4DD0BB37CC8073306D1D6B73CD4`
- Complete state, legal options, Pilot view, stack, call sequence, and duplicate/reversed outcomes are preserved at `CALIBRATION_V1_20260918T142356Z_a870c302/PILOT_LEGAL_OPTION_FORENSIC.json`.

The canonical member was replayed twice from the frozen runtime and seed. Both replays reached the same empty option tuple, same guard state, and the same pre-decision snapshot SHA-256 `6221E3C1E4D844B938CAEE77892150C642FA5EFBC52B0C1CE7E7E4D6AE8F1C5E`. The reversed member `b0024-p39-reversed` completed normally.

## Exact decision surface

At the failing `AcceptancePilot.choose_sneak` call:

- Turn/step: 14 / `declare_blockers`
- Active player / winner: 1 / `raphael`
- Pilot observation life totals: `[0, 20]`
- Legal Sneak options supplied to the Pilot: `[]`
- Engine state: blockers declared, active player correct, priority state `None`, but stack depth 2.

The remaining stack objects were triggered abilities from `Wingnut, Bat on the Belfry` and `Mutant Town Musicians`. Earlier in the same blockers step, the engine supplied three legal Sneak CAST options plus PASS. The Pilot selected a CAST; resolving its resulting triggers included Raphael damage that set the opposing player's life to zero. Two triggers remained on the stack.

`Game.legal_sneak_actions` returns an empty tuple when its guard sees a nonempty stack. PASS therefore was not incorrectly omitted: it was illegal at that exact engine state. `AcceptancePilot.choose_sneak` expects a CAST and eagerly evaluates a PASS fallback, so it raised `StopIteration` when presented with the empty tuple.

## Exact call path

```text
stage002.run_game
  -> while game.step == declare_blockers
  -> game.legal_sneak_actions(active)
  -> AcceptancePilot.choose_sneak(game.pilot_view(active), options)
  -> StopIteration while evaluating PASS fallback
```

The engine had previously validated Sneak availability from `execute_block_action`. The later call occurred after `_drain_priority` changed the state to winner `raphael` with unresolved stack entries, while the Stage 002 loop condition checked only `step == declare_blockers` and did not re-check the terminal state.

## Owner and smallest remediation hypothesis

The evidence assigns the immediate ownership to Stage 002 combat-loop control flow, not deck balance and not an engine omission of PASS. The smallest evidence-backed remediation hypothesis is a Stage 002 runner boundary guard: after Sneak action priority draining, stop the blockers/Sneak loop before another Pilot decision whenever the game has a winner (and, defensively, do not solicit a Sneak decision unless the engine currently supplies a legal decision surface).

A focused regression should reproduce this member/state and prove the runner does not call `choose_sneak` after terminal resolution. No production change is included in this evidence PR.
