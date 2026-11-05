# Cardcade 300-Game Exploratory Results

## Execution outcome

**300-GAME EXPLORATION STOPPED - SPECIFIC CAUSE**

- Scheduled attempts: 300
- Actual attempts: 0
- Completed games: 0
- Authorizations issued by this run: 0
- Games launched: 0

## Approved schedule and preflight evidence

The preserved schedule digest was verified as `9206c4267027473218f18e9482abcccb8a64dcfc62a7511d39b711a427a2179c`. The previously completed read-only preflight records show 30 of 30 block manifests passed with the recorded controller bundle, issuer, supervisor, runtime, dependency and resource identities. No schedule, seed, matchup or orientation was regenerated or substituted in this execution attempt.

The required limits remained 600 seconds per game and an effective Job Object memory limit of 2,997,489,664 bytes. No limit was changed.

## Stop cause

The approved PowerShell batch wrapper at `.diag003-memory-independent-review/300-game-exploratory-r1/execute_approved_batch.ps1` passed PowerShell parser validation, but the host refused to load it: `PSSecurityException: running scripts is disabled on this system` (`Restricted` effective execution policy; all policy scopes were `Undefined`). The wrapper has no `Zone.Identifier` stream, so this was not a downloaded-file mark.

The script was not evaluated. Consequently its first-block preflight/issuance sequence did not run, no grant was issued, and no worker or game was launched. The dedicated execution evidence directory `execution-r1` remains absent. Existing authorization and consumption stores contain prior records; they were not modified. The failed attempt did not invoke the issuer or controller.

No execution-policy override, alternate script-loading path, or manual dispatch was used because that would bypass the host's execution control and the approved wrapper's pre-dispatch safeguards.

## Evidence and limitations

- Wrapper syntax: PowerShell parser check passed.
- Effective policy: `Restricted`; MachinePolicy, UserPolicy, Process, CurrentUser and LocalMachine scopes were all `Undefined`.
- Wrapper `Zone.Identifier`: absent.
- New execution evidence directory: absent.
- No gameplay telemetry, outcomes, durations, or per-block scorecards exist for this attempt.
- No historical checkpoints, RUN_STOP state, frozen decks, prior diagnostics, or prior batch results were accessed or changed.

## Smallest next action

The workstation owner must provide an approved way to execute this exact wrapper under the established host policy (for example, authorize/sign the reviewed wrapper through the normal trusted process). Then rerun the exact preflighted schedule only under a fresh explicit HQ execution authorization if the present authorization is no longer valid. Do not change policy or use an alternate launcher merely to bypass the refusal.

## Subsequent HQ-authorized launch attempt - 2026-11-02

HQ and the workstation owner approved the exact Path A wrapper and a process-scoped `RemoteSigned` PowerShell invocation. The wrapper SHA-256 matched the approved identity `d715ba13d17a1510a980300549f956c853cef070d61baf6229ae090fda24327f`. Immediately before launch, schedule integrity passed for digest `9206c4267027473218f18e9482abcccb8a64dcfc62a7511d39b711a427a2179c` (30 blocks, 300 games), all 30 read-only issuer preflights passed, and no grants were issued by those preflights. The process-scoped command was:

`powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File "C:\projects\tmt\.diag003-memory-independent-review\300-game-exploratory-r1\execute_approved_batch.integrity-v2.ps1"`

The wrapper stopped at its repository identity gate with `Git top-level does not identify the approved repository` (line 22). This occurred before the schedule/helper preflight inside the wrapper, execution evidence directory creation, any `--issue-batch` call, or worker dispatch. Per HQ's stop rule, no retry or alternate launch method was attempted.

- This attempt: **0 games attempted, 0 completed, 0 grants issued, 0 games launched**.
- New gameplay output and block checkpoints: none.
- Termination: wrapper pre-dispatch failure at Git top-level identity validation.
- Independent signed batch receipts: not used, under the limited HQ deferral; no receipt was generated.
- The effective machine/user policy was not changed. The process-scoped invocation ended with this PowerShell process.
- Prior report text above remains preserved as the record of the earlier `Restricted`-policy refusal. No prior game results, authorization records, historical checkpoints, RUN_STOP state, decks, or diagnostics were modified.

**Current batch status: STOPPED - SPECIFIC CAUSE.** The next action is to resolve the repository identity mismatch in the approved workspace and obtain fresh approval if required. Do not rerun this wrapper or substitute a launch method under the current stop instruction.

## Repository identity gate diagnosis and correction preparation — 2026-11-02

**Disposition: REPOSITORY IDENTITY CLEARED — HQ EXECUTION REVIEW REQUESTED**

This section supplements the preserved execution-attempt records above. It does not change or reinterpret either prior stop record.

### Read-only reproduction

- Approved wrapper that failed: `C:\projects\tmt\.diag003-memory-independent-review\300-game-exploratory-r1\execute_approved_batch.integrity-v2.ps1`
- Wrapper SHA-256: `d715ba13d17a1510a980300549f956c853cef070d61baf6229ae090fda24327f`
- Expected repository root embedded in the wrapper: `C:\projects\tmt`
- Actual caller working directory: `C:\projects\tmt`
- `git -C C:\projects\tmt rev-parse --show-toplevel`: `C:/projects/tmt` (exit 0)
- Git directory and common directory: `.git` and `.git`; the approved checkout is a regular worktree, not a linked worktree.
- Configured origin: `https://github.com/egggggman/tmt.git`
- Current checkout: branch `main`, commit `657750035bc395382c820191b5ccc58d5058a55d`.
- Git also lists sibling worktrees at `C:/projects/tmt-calibration-001`, `C:/projects/tmt-r9b-recovery`, and `C:/projects/tmt-recovery-repair`. They were not the caller or wrapper checkout and did not cause this failure.

At wrapper line 21 (reported as the line-22 identity gate), the code compared the trimmed Git output directly to the expected root with `StringComparison.OrdinalIgnoreCase`. Case-insensitive comparison does not normalize `/` versus `\\`, so the valid Git path was rejected. The working-directory check, script-derived root check, wrapper-under-root check, and origin check all identify the intended checkout. Evidence supports a path-format comparison defect, not invocation from the wrong directory or a repository/origin mismatch.

The rejection occurs before the wrapper's schedule helper, execution evidence directory creation, grant issuance, or worker dispatch. The recorded outcome remains 0 grants and 0 games.

### Minimal correction candidate

The original approved wrapper remains unchanged at SHA-256 `d715ba13d17a1510a980300549f956c853cef070d61baf6229ae090fda24327f`.

A separate, unapproved candidate is at:

`C:\projects\tmt\.diag003-memory-independent-review\300-game-exploratory-r1\execute_approved_batch.integrity-v3-path-normalization-candidate.ps1`

Candidate SHA-256: `3aa753e07916f1f49a66f3278e91527341bfc074bc673b5b82e9918aebe3a100`.

Its sole source change normalizes the single Git-reported top-level path using `[IO.Path]::GetFullPath(...Trim())` before the existing strict `OrdinalIgnoreCase` comparison. It retains the fixed approved root, exact caller working-directory requirement, wrapper-under-root requirement, Git origin validation, and all later identity checks. It does not remove or bypass the repository gate. The candidate was parsed but never invoked.

### Validation evidence

- Candidate PowerShell parser: 0 parse errors.
- Disposable path-comparison cases: 6/6 passed: Git forward-slash output for the approved root accepted; case variation accepted; wrong repository rejected; alternate worktree path rejected; traversal path canonicalized and rejected; wrong caller working directory rejected.
- Read-only schedule integrity helper: `SCHEDULE_MANIFESTS_VERIFIED`; canonical SHA-256 `9206c4267027473218f18e9482abcccb8a64dcfc62a7511d39b711a427a2179c`; 30 blocks and 300 games verified.
- Existing `test_batch_integrity_validation.py` was not rerun successfully in this environment: the qualified isolated Python 3.13.15 runtime reports `No module named pytest`; the repository `.venv` Python launcher fails with `uv trampoline failed to spawn Python child process (entity not found)`. No assertion failure was observed. This is a test-environment limitation, not a passing test result.
- No production wrapper was invoked; no grants, game workers, gameplay, or execution outputs were created.

### Launch disposition and next gate

The previously approved `integrity-v2.ps1` launch is **not usable**: it deterministically rejects the verified checkout because of the separator mismatch. The proposed v3 candidate is not yet an approved replacement. Before any execution, an independent reviewer must approve its exact SHA-256 and the preserved synthetic boundary results; HQ/workstation-owner approval must then identify that new artifact and invocation. The original schedule, inputs, source, existing authorizations, RUN_STOP state, and historical evidence were not changed.


## Final authorized Path A execution — 2026-11-02 to 2026-11-03

**300-GAME EXPLORATION COMPLETE — HQ RESULTS REVIEW REQUESTED**

The earlier zero-attempt stop records and repository-gate diagnosis above are preserved as historical records. This section records the subsequent HQ- and workstation-owner-approved run using the corrected Path A wrapper.

### Execution identity and launch

- Approved schedule SHA-256: `9206c4267027473218f18e9482abcccb8a64dcfc62a7511d39b711a427a2179c`
- Corrected wrapper: `C:\projects\tmt\.diag003-memory-independent-review\300-game-exploratory-r1\execute_approved_batch.integrity-v3-path-normalization-candidate.ps1`
- Wrapper SHA-256: `3aa753e07916f1f49a66f3278e91527341bfc074bc673b5b82e9918aebe3a100`
- Invocation, from `C:\projects\tmt`: `powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File "C:\projects\tmt\.diag003-memory-independent-review\300-game-exploratory-r1\execute_approved_batch.integrity-v3-path-normalization-candidate.ps1"`
- The process-scoped launch reported `RemoteSigned`; MachinePolicy, UserPolicy, CurrentUser and LocalMachine were `Undefined`. No persistent policy was changed.
- Git root resolved to the approved checkout and origin `https://github.com/egggggman/tmt.git`.
- Gameplay source commit: `32a80228714674327aca62f8b86b70c4c4afc929`.
- Baseline input manifest SHA-256: `c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`.
- Card-data SHA-256: `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`.
- Qualified CPython: 3.13.15; executable SHA-256 `85b71d8c6ec1905935f74be0c9869aae198d00e98f39df699ec66f9c5a84cecd`; lock SHA-256 `0c9863fb82c65e8c457b6903b13ab978e1012dc9252e9cca3e95807ef3ded11a`.
- Controller SHA-256: `25d8bbba9adbde68d92b98b552d9603f05db3015ceb562023a12a8d013e1495b`.
- Issuer SHA-256: `47d4adee5c4ff36f0117375777ae76d8c34217e40d63812f505ad202bb702e23`.
- Supervisor SHA-256: `f23939f4bb656de73588ae9202437d093b38fc7cbaf4e92b7776cb542ee22b1d`.
- Post-run verifier SHA-256: `259c5f18edbfe262778ba351651c28f845901f687764193afb2d0ef85402f39a`.
- Approved limits remained 2,997,489,664 bytes for Job Object/process committed memory and 600 seconds per game. No limit failure was reported by the supervisor or block verification. The sandbox could not independently reopen per-worker Job Object readback records on protected G:. No automatic retry occurred.

### Execution and evidence integrity

- Scheduled/attempted/completed/failed: **300 / 300 / 300 / 0**.
- All 30 blocks passed issuer, controller and verification exit-code checks (all `0`); each had 10 attempts, 10 completions, 0 failures and 0 automatic retries.
- Every block verifier reported `VERIFIED_COMPLETE` and rechecked **14,680 artifact hashes**. Total hash rechecks across blocks: **440,400** (this is a count of checks, not a count of unique files).
- All game status summaries were `RETURNED`; all 300 had a winner and no recorded failure.
- The preserved block manifests, issuer/controller/verifier logs, scorecards and final control summary are under `.diag003-memory-independent-review\300-game-exploratory-r1\execution-integrity-v2\`. The final `batch-summary.json` has SHA-256 `23540ef43c44f8d36fb409fae7d4fb82e9e9350ff96a9c925adc21525874175a` and state `ALL_BLOCKS_VERIFIED`.
- Per-game outputs and detailed raw telemetry remain under `G:\cardcade\diagnostics\` in their assigned run directories. The block verifier checked the protected artifact inventory. At initial report drafting, the sandboxed review process could not directly read those protected G: files; the later read-only HQ hold addendum below summarizes their semantic-warning records without modifying them.
- Independent signed batch receipts were **not used**, under HQ's explicit deferral. Artifact hash verification and grant-consumption checks are not represented as equivalent to independent signed receipts.
- No change was made to frozen Baseline 005 decks, Diagnostic 001–003, prior batch evidence, Durable 001, or `RUN_STOP.json`.

### Exploratory gameplay scorecard

The schedule used unique seeds 10001–10300 and covered all 45 unordered deck pairings (15 pairings played six times; 30 played seven times). Each deck appeared in seat 1 thirty times and seat 2 thirty times. Summary outcomes give a mean of **19.85 turns**, median **18.5 turns**, and range **11–53 turns**. Seat 1 won 172 games and seat 2 won 128; this is an exploratory observation, not a seat-balance conclusion.

| Deck | Games | Wins | Losses | Mean ending turn |
|---|---:|---:|---:|---:|
| April O'Neil | 60 | 15 | 45 | 20.75 |
| Bebop & Rocksteady | 60 | 22 | 38 | 18.17 |
| Casey Jones | 60 | 37 | 23 | 21.68 |
| Donatello | 60 | 28 | 32 | 19.20 |
| Krang | 60 | 28 | 32 | 20.37 |
| Leonardo | 60 | 24 | 36 | 23.47 |
| Michelangelo | 60 | 18 | 42 | 20.00 |
| Raphael | 60 | 43 | 17 | 17.92 |
| Shredder | 60 | 45 | 15 | 17.38 |
| Splinter | 60 | 40 | 20 | 19.53 |

These results are exploratory signals only. They are not certified balance rankings and should not trigger automatic deck revisions.

### Telemetry limits and next review

The compact control summary records run ID, seed, pairing, seats, game state, winner, ending turn and failure. It does not aggregate per-game duration, cards cast, ability use, unsupported-mechanic warnings, opportunity witnesses, or terminal anomalies. The dated HQ hold addendum below summarizes semantic warnings; duration, card/ability totals, opportunity-witness totals and terminal anomalies remain unaggregated in this report. Treat the outcomes as fidelity-qualified exploratory data, not rules-correctness proof or calibration evidence.

**Recommended next action:** HQ review the 300-game scorecard and preserved telemetry, then decide whether to continue exploratory testing or request a focused analysis. No further games are authorized by this completed batch.


**300-GAME EXPLORATION COMPLETE — HQ RESULTS REVIEW REQUESTED**

## HQ hold and mechanics-warning review — 2026-11-03

**HQ decision: HOLD at the completed 300-game checkpoint.** No larger batch is started, no deck is revised, and these exploratory results are not promoted to an accepted calibration baseline. All 30 verified blocks and their execution, authorization-consumption, artifact-hash, and checkpoint evidence remain preserved. Further testing requires a new HQ authorization after evidence review.

### Read-only warning summary

I read the `result.json` at each of the 300 schedule-assigned output paths and checked that each recorded `run_id` matched its schedule entry. All 300 result files were present and matched. This was a read-only telemetry review; it did not change the results or independently recompute the earlier block verifier's artifact-hash inventory.

The structured conformance records contain **3,025 semantic occurrences across 299 games**:

| Classification | Occurrences | Games | Meaning in the recorded schema |
|---|---:|---:|---|
| `present_unreached` | 2,456 | 299 | An ability/semantic was present, but the telemetry did not establish a matching opportunity witness. This is not evidence that its effect was incorrectly applied. |
| `reached_unsupported` | 569 | 222 | The engine recorded a relevant authoritative opportunity context for a semantic the conformance layer does not classify as executed. This is a fidelity warning, not by itself proof of an incorrect result. |

Most frequent **reached unsupported** families, by occurrence count (the game count is the number of distinct games containing that family):

| Mechanic family | Occurrences | Games |
|---|---:|---:|
| Casey Jones ETB: look at four, reveal an artifact, put it in hand, bottom the rest | 126 | 84 |
| Creature leaves battlefield: create a Mutagen token | 91 | 58 |
| Creature ETB: search for Food, otherwise create a Food token | 63 | 42 |
| Krang level 3 activation | 62 | 46 |
| Casey Jones ETB: draw three, then discard three at next upkeep | 55 | 40 |
| Creature ETB: destroy up to one target noncreature artifact | 33 | 29 |
| Creature ETB: mill three | 25 | 20 |
| Stockman ETB: draw then discard | 22 | 20 |
| Shredder ETB/attack: grant another creature Deathtouch | 20 | 20 |
| Cast small creatures from graveyard with finality counter | 16 | 15 |
| Raphael attack: play a card exiled with Raphael | 13 | 13 |
| Donatello artifact ETB: add a +1/+1 counter | 12 | 12 |
| Alliance: another creature enters, may exile the top card | 10 | 10 |
| +1/+1 counter replacement effect | 9 | 9 |
| Krang ETB: draw up to four cards in hand | 6 | 4 |
| Counter target spell and create Mutagen token | 6 | 3 |

The records also contain high-frequency **present-but-unreached** families: Flying (297 occurrences/159 games), the conditional artifact-entry unblockability ability (243/124), Flying plus vigilance (225/114), Deathtouch (193/110), and Menace text/keyword occurrences (153 total occurrences across the two text forms; the forms appear in 74 and 37 games respectively and may overlap). These counts describe recorded semantic presence, not actual use or a demonstrated combat error.

The reached families involving library choices, delayed discard, triggered tokens, counters, graveyard casting, and combat damage can affect resources or board state when their decisions matter. The telemetry flags them for review but does not alone establish which effects changed a winner. No new gameplay defect or rules-correctness conclusion is asserted here. Previously accepted synthetic Menace and Deathtouch validations remain separate evidence and do not resolve every one of these live paths.

**Review disposition:** Keep the 300-game outcomes exploratory and fidelity-qualified. HQ evidence review is the next gate. Do not start another batch, revise decks, or promote calibration status before that review and a new authorization.

