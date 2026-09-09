# Action #30 candidate — Jury-Rig Justiciar

Authorized base: `40149d0ca6d231af7dd46aae30ce67446e8670b4` (Issue #99). Existing branch: `codex/cardcade-action30-jury-rig`. Candidate SHA is supplied by the PR head and final handoff; this report does not self-accept or authorize merge.

The exact frozen entry fragment now resolves through existing Trigger / Stack / Priority. The dedicated Jury-Rig module privately inspects the resolution-time top min(4, library size), permits one qualifying artifact or decline, reveals/moves only the selection through authoritative zone movement, and records exactly one deterministic shuffle of only the unchosen inspected cards. Its output is bottom-to-top ahead of the untouched lower prefix. Same-zone objects retain their identities. Remainder sizes zero and one still produce one shuffle record while leaving RNG state unchanged; dedicated tests prove this policy. The default chooser selects the first qualifying artifact in top-first order.

The immutable chooser view contains only inspected identities/names/types. A transaction-local callback guard detects and rolls back authoritative state/RNG mutations while retaining original object references. Original entry, source and Stack identities anchor execution; source departure does not cancel the trigger. The independent serialized validator reconstructs entry, trigger, all-pass permission, inspection/candidates/decision, optional reveal and new hand incarnation, remainder RNG permutation, untouched prefix and final library/hand. EXECUTED references require the committed chain rather than generic resolution events.

## Validation

- Focused Action #30: 60 passed. Focused plus Courier, Scry, hand-bottom/draw, deterministic RNG, Vigilante and Trigger regressions: 218 passed.
- Full pytest: 1,155 passed, 1 skipped.
- Frozen Stage #002: one invocation, 16 distinct games / 32 executions. All duplicate evidence matches, zero stops/violations, all 16 reports independently reconstruct. Three natural Jury-Rig transactions reconstruct.
- Smoke: one invocation, 180 distinct games / 360 executions. All duplicates and reports reconstruct, zero stops/violations. 68 Jury-Rig transactions. Mechanical labels: 105 clean coverage-complete, 75 clean coverage-limited, zero invalid. These are coverage labels, not calibration approval.
- Ruff check, Ruff format check, canonical terminology scan and git diff checks passed. Sidecars are checked against staged bytes before commit.
- Two development full-suite failures were fixed: null-ledger compatibility for legacy synthetic Stage fixtures and subsequent frozen source hash refresh. Final full suite passed. The Stage run preceded that validator-only compatibility fix; all saved reports reconstruct with final code, with no later gameplay change or extra Stage execution.

## Observed Stage result and continuity

| Measurement | EXECUTED | REACHED-UNSUPPORTED | PRESENT-UNREACHED |
|---|---:|---:|---:|
| Accepted post-Action #29 | 27 | 4 | 134 |
| Action #30 candidate | 30 | 1 | 133 |

The frozen game matrix and card snapshot are unchanged. Semantic coverage metadata changes to recognize Jury-Rig. Every prior EXECUTED game/semantic occurrence count is retained, including Courier and resolved Vigilante chains. The three previously unsupported Jury-Rig occurrences are now EXECUTED. Other present-unreached occurrence changes follow the observed gameplay trajectories; no count was forced.

The sole remaining unsupported occurrence is Casey Jones, Vigilante in `april-casey:canonical:7231`, whose game ends before the delayed obligation's due upkeep. It is conservatively retained as REACHED-UNSUPPORTED. Jury-Rig has no remaining reached-unsupported occurrence in this matrix.

## Evidence and changed paths

Production changes: `card_interpreter07.py`, `engine07.py`, new `jury_rig07.py`, `stage002.py`, and `smoke01.py` (frozen source identities only). Tests: new `tests/test_jury_rig_action.py`. Evidence attributes: `docs/cardcade/.gitattributes`.

Fresh artifacts under `docs/cardcade/`, each with SHA-256 sidecar:

- `POST_ACTION_30_STAGE_002_RESULTS.json`: complete Stage reports and authoritative evidence.
- `POST_ACTION_30_SMOKE01_RESULTS.json.gz`: complete Smoke result including both duplicate snapshots. The `.json.gz.sha256` authenticates compressed bytes; `.json.sha256` authenticates the exact decompressed original runner output. Gzip round-trip was verified before removal of the redundant raw working file.
- `POST_ACTION_30_JURY_RIG_TRANSACTIONS.json`: all three natural Stage chains plus complete controlled selection, decline, no-artifact and empty-library snapshots. Controlled fixtures add no Stage/Smoke games.
- `POST_ACTION_30_INVENTORY.json`: all occurrences, exact references and comparison deltas; accepted prior artifact checked against its committed SHA-256.
- `POST_ACTION_30_UNSUPPORTED_RANKING.json`: remaining Vigilante witness.
- `POST_ACTION_30_VALIDATION.json`: validation results, attempts, final source/test Git blob identities and decompressed Smoke hash.
- This handoff and its sidecar.

Historical artifacts are preserved. No generic hidden-zone grammar, staging zone, Pilot redesign, scheduler, turn-engine change, deck revision or unrelated rule expansion is included. Action #31 remains NOT AUTHORIZED. Calibration remains BLOCKED. Prototype 0.3 remains NOT AUTHORIZED. Independent HQ review is required before merge.
