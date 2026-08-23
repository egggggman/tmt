# Coverage-Aware Engine Smoke Stage 0.1 Readiness Audit #2

## Verdict

**READY — the specification and corrected runner are mechanically auditable and may be executed unchanged after PR integration and merged-main validation freeze the execution baseline.**

No Smoke Stage 0.1 game was run during this audit. This verdict does not authorize Action #14, the historical 900-game smoke, calibration, Pilot/deck changes, or Prototype 0.3.

## Frozen audit chain

- Stage 0.1 specification SHA-256: `cdf17e0a13c9aaa57e04df84460fa557c144203db0012d7bf964709e0cb66c90`
- Readiness Audit #1 SHA-256: `509d90c4b8811c94539201921c318f8e8d9a4613b05041eef886d3bb6c16cc8d`
- Corrected runner candidate: `a3c5738a02b57f64174f54cb4e181ca2931bc4f8`
- Canonical Hashing Audit #1 SHA-256: `bc8fb0828686dc48ee1433a66a005361fcc63466fbde5d070ad46d91850acb42`
- Evidence-banked audit commit: `0937d21`
- Current reconstructed plan digest: `5f222b653a25013528baf39c59cb589875a58c4d00de5f2cefd34e064fac162c`

The specification and Readiness Audit #1 remain byte-identical. The accepted canonical-hashing correction deliberately versions and replaces only the old working-tree-byte identities in the Smoke runner contract; it does not change the frozen semantic inputs, decks, runtime, Pilot, or matrix.

## Re-audit of the original NOT READY findings

### Frozen inputs and plan reconstruction — PASS

Plan mode reconstructs all ten decks, roster, authoritative card snapshot and manifest, accepted runtime/conformance files, Pilot, runner, and execution commit. It validates 472 print records and 332 Oracle objects, resolves every deck membership, records each input's hashing method and digest, and fails closed on drift.

Tracked text uses accepted Git-clean identity contract `smoke-frozen-input-hashing-v2`; binary/non-Git inputs retain exact byte hashing. Cross-platform LF/CRLF equivalence, substantive dirty-text rejection, raw binary sensitivity, and missing/untracked rejection are independently accepted.

Plan construction does not instantiate a Game or consume RNG.

### Matrix and duplicate policy — PASS

Independent reconstruction yields exactly:

- 10 frozen decks;
- 45 unordered cross-deck pairings;
- two fixed seeds per pairing, 8001–8090;
- canonical and reversed orientations;
- 180 collision-free distinct game IDs;
- exactly two fresh executions per game, 360 executions total.

Duplicates remain evidence, never additional samples. The successful artifact preserves both complete canonical snapshots, both independently recomputable SHA-256 digests, explicit byte equivalence, RNG terminal state, and authoritative state fingerprints. Any mismatch stops the entire stage.

### Prospective conformance authentication — PASS

The runner reuses the accepted Stage #002 evidence model rather than creating a Smoke-specific semantic model. EXECUTED references authenticate against exact authoritative transaction/event identity, source, fragment, semantic key, and lineage. REACHED / UNSUPPORTED witnesses authenticate typed-event or opportunity-context provenance. PRESENT / UNREACHED remains the conservative default when applicability is not proven.

Malformed, missing, borrowed, duplicated, or mismatched transaction, context, witness, source, controller, zone, event, Stack, fragment, or lineage evidence fails closed. Opportunity evidence cannot promote EXECUTED.

### Exactly one game classification — PASS

For every completed duplicate-authenticated game, the runner reconstructs the Stage #002 report and derives exactly one label:

- `mechanically_clean_coverage_complete`; or
- `mechanically_clean_coverage_limited`.

Stops, invariant violations, unknown classifications, duplicate occurrence IDs, or incomplete games are mechanically invalid and stop the stage. PRESENT / UNREACHED alone does not make a game coverage-limited. Aggregate memberships and counts are rebuilt from per-game evidence and reject even re-signed substitutions.

### Structural balance exclusion — PASS

`balance_valid` is derived, not trusted, and is always `false` in Smoke 0.1. Coverage-limited games are absent from the future-candidate projection. Coverage-complete games may appear only as future candidates and still carry `balance_valid: false` because Pilot and statistical-design gates are absent. Re-signed attempts to forge balance validity fail semantic validation.

Thus a completed game cannot silently become balance evidence.

### Atomic success and failure evidence — PASS

Preflight drift before game #1 writes no success result and atomically preserves a deterministic failure artifact plus SHA-256 sidecar. Execution failures preserve active game/pairing/seed/orientation, duplicate member, ordinal, completed-game count, available duplicate evidence, prior accepted report digests, exception data, and available authoritative Stack/Priority/state summary. The artifact explicitly records `accepted_aggregate: false` and cannot validate as success.

Successful output is written only after all 360 executions pass. It includes the manifest, all 180 reports, duplicate evidence, reconstructed coverage aggregation, aggregate digest, raw-body digest, and external file SHA-256 sidecar.

Adversarial regressions cover preflight drift, incomplete games, duplicate nondeterminism, tampered duplicate/context/execution evidence, re-signed balance/classification substitution, and post-duplicate failure preservation.

## Validation

- Full suite: **622 passed / 1 skipped**
- Focused Smoke + Stage #002: **62 passed**
- Ruff check and format: clean
- `git diff --check`: clean
- Exact implementation SHA Linux CI: PASS, runs `32614293920` and `32614296488`
- Smoke games executed during readiness work: **0**

## Execution gate

Readiness Audit #1's four tooling blockers—Smoke-specific plan/runner, independently preserved duplicates, derived mechanical/balance classifications, and atomic success/failure evidence—are resolved. The canonical portability defect subsequently found by Linux CI is also resolved and independently accepted.

PR #53 must now integrate the accepted runner and evidence chain. Merged `main` must pass CI and local validation, and plan mode must reconstruct and freeze the resulting execution commit, runner identity, manifest digest, and clean worktree. Because execution commit is an authenticated manifest field, the merged-main plan digest is expected to differ from the audit-branch digest; that deterministic regeneration is part of the contract, not a runner change.

After those integration checks, Coverage-Aware Engine Smoke Stage 0.1 is authorized to start from game #1 using the accepted 45/180/360 matrix unchanged. Any fail-closed condition stops the complete stage and becomes evidence; no mid-run correction or retry is authorized.
