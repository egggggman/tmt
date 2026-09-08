# Action #29 candidate: Vigilante draw / next-upkeep random discard

Implements Issue #97 from exact audit base `cd41d6c661cde66e3eb440002f5f87a711aaa425`, following authoritative Issue #96 evidence head `f11ed7efb5e7bd6cd7da73f0ced2aa83ebb89468`. Candidate is for independent HQ review only.

The exact frozen Oracle fragment now draws three through the original ETB Stack/Priority resolution and captures one immutable, one-shot next-upkeep obligation. The captured controller's first subsequently entered upkeep delivers the delayed trigger through the existing Trigger/Stack/Priority lifecycle. After all players pass, it discards up to three distinct cards from the current hand using deterministic RNG and authoritative zone movement. Source departure, reentry, and later control changes do not erase or transfer the captured obligation.

## Bounded implementation and changed paths

- `src/tmnt_design_studio/vigilante07.py`: dedicated exact-semantic transaction, immutable schedule identity, one-shot delivery/consumption, source/event/Stack/RNG identity checks, and independent full-chain reconstruction. No generic scheduling API or arbitrary delayed grammar.
- `src/tmnt_design_studio/card_interpreter07.py`: only the exact frozen fragment, with no card/deck-name gameplay dispatch.
- `src/tmnt_design_studio/engine07.py`: narrow ETB/upkeep hooks and ordinary Priority effects; snapshots expose pending/delivered/resolved/terminal evidence. Immediate ETB draw resolution is excluded from whole-semantic EXECUTED references.
- `src/tmnt_design_studio/stage002.py` and `smoke01.py`: explicit beginning-step traversal that drains existing Priority before advancing from upkeep. No unresolved-Stack guard weakening, Pilot policy changes, roster changes, or seed changes. Smoke frozen identities include the new module.
- `tests/test_vigilante_upkeep_action.py`: 52 focused proofs including both controllers, boundary timing, independent records, source lifetime, identity tampering, current-hand sampling, RNG, live/serialized evidence, pending/terminal states, and runner ordering.
- `docs/cardcade/.gitattributes` and new Action #29 evidence/handoff artifacts: stable LF text and binary gzip.

RNG policy: exactly one domain-separated shuffled-copy record at delayed resolution for every hand size, including zero. Select the first `min(3,n)` identities; move each through `move_object`; preserve remaining hand order. Empty/singleton shuffles may leave RNG state unchanged but still produce an auditable record. Equal-valued cards remain identity-distinct.

## Validation

- Focused Vigilante: **52 passed**.
- Combined Vigilante, turn-state, RNG, Stockman, Courier, Zoo, and trigger regressions: **194 passed**.
- Final full pytest: **1095 passed, 1 skipped**.
- Ruff check, Ruff format check, canonical terminology scan, and working/staged `git diff --check`: passed.
- Stage #002 final accepted run: **16 distinct games / 32 executions**, byte-equivalent duplicates, **zero invariant violations / zero runner stops**. All 16 reports reconstruct exactly; frozen manifest matches.
- Stage development history: one prior explicit attempt stopped at the reconstruction gate because live RNG tuples were compared directly with serialized lists. No accepted result was produced by that attempt. Canonical JSON comparison and live-snapshot regression coverage fixed it; the second explicit attempt completed the same frozen matrix. These attempts are separate from the per-matrix 16/32 budget and existing test-suite fixtures. No broadened matrix was used.
- Existing Smoke 0.1: **180 distinct games / 360 executions**, completed and independently validated. This required engine smoke run is not calibration or authorization for balance work.
- Natural full delayed chains, four controlled lifecycle snapshots, artifact hashes, frozen inputs, and exact witness code identities verified. No prior artifact overwritten.

## Observed Stage result and continuity

**27 EXECUTED / 4 REACHED-UNSUPPORTED / 134 PRESENT-UNREACHED.** Counts are observed results, not a forced target.

Both original Vigilante witnesses complete their entire delayed chain in `april-casey:canonical:7231` and `april-casey:canonical:7232`. Their next-upkeep random discards resolve and their records are consumed.

The changed trajectory naturally creates one additional Vigilante ETB in `april-casey:canonical:7231` (source `object-000196`, schedule `object-000198`). That game ends before the obligation's next upkeep. Its record is **pending / terminal_without_resolution**, and its immediate draw is **not** credited as whole-semantic EXECUTED. Under the existing three-class taxonomy it remains REACHED-UNSUPPORTED; this row represents an uncompleted terminal obligation, not missing random-discard implementation.

| Remaining REACHED-UNSUPPORTED semantic | Occurrences | Games | Matchups | Interpretation |
|---|---:|---:|---:|---|
| Casey Jones, Jury-Rig Justiciar | 3 | 3 | 1 | Excluded, unimplemented semantic |
| Casey Jones, Vigilante | 1 | 1 | 1 | Additional terminal-pending obligation; no false EXECUTED credit |

No previously EXECUTED game/semantic occurrence count decreased against Issue #96. Courier, Zoo Escapees, Stockman, Action #21 Donatello, Action #25 Shredder, and all other banked execution witnesses retain continuity. No foundational scheduling blocker was observed in the authorized implementation and validation scope.

## Preserved evidence

- `POST_ACTION_29_STAGE_002_RESULTS.json`: complete frozen result.
- `POST_ACTION_29_STAGE_002_WITNESS.json`: complete semantic inventory, observed ranking, original/terminal Vigilante records, all EXECUTED witnesses, continuity deltas, and exact code blob identities.
- `POST_ACTION_29_DELAYED_CHAIN_EVIDENCE.json`: complete authoritative evidence for both natural games containing Vigilante chains, including the additional terminal-pending chain.
- `POST_ACTION_29_LIFECYCLE_FIXTURES.json`: independently reconstructed controlled pending, delivered, resolved/consumed, and terminal-pending snapshots; synthetic focused fixtures, not additional Stage games.
- `POST_ACTION_29_SMOKE01_RESULTS.json.gz`: lossless Smoke result. `.json.gz.sha256` hashes the compressed Git artifact; `.json.sha256` preserves the decompressed JSON identity `a836a459062324ab16dc122e57eaa6228a363e5bfe85fa6b4afb3b942956f233`.
- `POST_ACTION_29_VALIDATION.json`: final checks and run accounting. JSON artifacts have adjacent SHA-256 sidecars.

Candidate SHA, final clean-worktree status and PR URL are reported in the external handoff rather than embedded in their own commit.

## Review boundary

Jury-Rig untouched. No generic scheduler, broad turn-engine replacement, extra-turn/skip-step machinery, unrelated hidden-zone rules, deck revisions, or Pilot tuning. Calibration remains BLOCKED; Prototype 0.3 and Action #30 remain NOT AUTHORIZED. No self-acceptance or merge; HQ must independently review this candidate.
