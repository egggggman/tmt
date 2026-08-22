# Acceptance Stage #002 Readiness Audit #03

Audit baseline: merged `main` `4ed03aa2519451c65d97b30cac564faa4fbd5985`  
Merged PR: #44 — accepted Stage #002 opportunity-witness coverage  
Design under audit: `ACCEPTANCE_STAGE_002_DESIGN.md`  
Status: **NOT READY**

## Audit integrity

This is an evidence-only readiness audit. No Stage #002 match was run. No engine, conformance,
Pilot, deck, prototype, gameplay, calibration, smoke, or test file was modified.

PR #44 was squash-merged after its branch and PR workflows passed with GitHub reporting a clean
merge. Local `main` and `origin/main` are synchronized at the audit baseline with a clean worktree
before this report. Merged-main GitHub Actions passed in run `32547701620`.

The accepted witness-coverage history remains durable:

- Audit #1 REJECT SHA-256:
  `cfbf1c9d5745bc701d25bba11e4c6d81306312c6e15eeeaa8a538e1d273a82a0`;
- Audit #2 REJECT SHA-256:
  `fe745c5a05cd0aaafc3288d4d412b0aff5308febe5096ed412a81753ba9891f1`;
- Audit #3 ACCEPT SHA-256:
  `a3b9ef723432b2c2c4a44d0126d9dc0afa2d9713570cb3a7f5b8b9268efc2ef7`.

## Merged-main validation

- Full suite: **534 passed / 1 skipped**;
- runtime conformance: **35 passed**;
- card-data integrity: **5 passed**;
- Ruff format/check: clean;
- `git diff --check`: clean;
- merged-main CI: **PASS**;
- worktree: clean before this report.

Acceptance #001 seeds 7001–7005 were replayed twice. Duplicate snapshots were byte-identical and
the accepted prospective classification remained:

- **18 registrations / 6 exact pairs**;
- **11 REACHED / UNSUPPORTED**;
- **7 PRESENT / UNREACHED**;
- **18 authoritative witnesses**;
- **0 invariant violations**;
- trajectories unchanged: Raphael T14, Raphael T18, Leonardo T19, Leonardo T43, Raphael T16.

## Witness-coverage result

The accepted instrumentation resolves the semantic-provenance defects from Readiness Audit #02.
It supplies an immutable, Action-neutral opportunity context; validates it at creation and through
engine invariants; and deterministically joins bounded activation, departure, replacement,
artifact-entry/self-count, Stack-response, target/choice, and instruction-reach opportunities.

Audit #3 establishes the important conservative boundaries:

- target/choice evidence is bound to the exact instruction occurrence by semantic key, fragment
  hash/index, and occurrence identity;
- artifact entry cannot authenticate unrelated artifact text;
- the supported self-specific artifact-count form freezes and validates the exact counted identity
  set and excludes the affected source;
- Equipment characteristic reach remains PRESENT / UNREACHED because attachment state is not
  authoritatively represented;
- unsupported or unobservable shapes are not heuristically promoted;
- existing Action evidence remains the only authority for EXECUTED.

The frozen witness inventory remains **78 unique cards, 127 unique fragment/limitation members,
and 243 deck memberships**, with membership digest
`57ab1be61f03606003345a5cd1aa1a8f8f7f5a98d162476666582dbe2ab6365c`.

## Remaining execution-readiness gap

The evidence layer is accepted, but the unchanged Stage #002 design requires a generalized runner
and frozen pre-run inventories. The merged repository still contains only the fixed
Leonardo/Raphael `run_acceptance_match_001.py`; it has no runner that parameterizes arbitrary
frozen deck paths and stable display identities for the four Stage #002 pairings.

No executable Stage #002 tooling currently:

1. materializes and freezes the required per-deck 60-slot Oracle/fragment manifests and their
   membership digests;
2. reconciles every participating semantic occurrence against an existing bounded producer or an
   explicit `opportunity_not_observable` classification before play;
3. emits the required per-game EXECUTED, REACHED / UNSUPPORTED, and PRESENT / UNREACHED report with
   compound joins and deterministic membership digests;
4. automatically records and stops on an `unclassified_reach` or `silent_approximation` result;
5. wraps rejected actions with the authoritative-state fingerprint to turn an actual mutation into
   the canonical `illegal_mutation` stop;
6. aggregates the 16 distinct games while proving that the duplicate 16 executions are comparisons,
   not additional games.

`ConformanceStopRecord` and `authoritative_state_fingerprint()` provide the accepted primitives,
and their focused tests are sound. They are not wired into a Stage #002 execution harness. Running
the matrix manually or by adapting Acceptance #001 ad hoc would not satisfy the design's mechanical
stop and reporting contract.

## Stop-condition status

| Stop condition | Readiness after PR #44 |
| --- | --- |
| Invariant violation | **Mechanically enforceable** by engine checks. |
| Nondeterminism | **Mechanically enforceable** once the Stage runner serializes duplicate artifacts. |
| Illegal mutation | **Primitive accepted; Stage runner integration absent.** |
| Silent approximation | **Witness primitives accepted; exhaustive Stage occurrence reconciliation and stop integration absent.** |

## Pairing assessment

The four pairings remain evidence-backed and none must be redesigned. The accepted producers make
their bounded activation, departure, replacement, artifact, response, target/choice, and compound
contexts prospectively classifiable. Conservative exclusions, including Equipment attachment and
unrepresented grammar, can truthfully remain PRESENT / UNREACHED. The readiness failure is common
runner/reconciliation infrastructure, not a pairing dominated by unsupported semantics.

The seed structure remains exactly **4 pairings × 2 seeds × 2 orientations = 16 distinct games**.
One exact duplicate of each produces **32 executions**, without increasing the distinct-game count.

## Smallest correction

Add evidence-only Stage #002 execution tooling that consumes the frozen design and accepted witness
inventory without changing gameplay:

1. generate and verify the required static deck/Oracle/fragment manifests;
2. parameterize the existing Acceptance runner over two frozen decks, stable seat identities, and
   the design's fixed seeds/orientations;
3. reconcile all static occurrences to EXECUTED, witnessed REACHED / UNSUPPORTED, or conservative
   PRESENT / UNREACHED, emitting explicit unobservable classifications;
4. wire canonical invariant, nondeterminism, illegal-mutation, unclassified-reach, and
   silent-approximation stops into the runner;
5. produce deterministic per-game and aggregate artifacts and verify duplicate byte equality.

This is conformance tooling, not Action #13 and not new semantic execution. It requires independent
audit before any Stage #002 game is authorized.

## Verdict

**NOT READY — the accepted opportunity-witness instrumentation now provides credible bounded
semantic provenance, but Stage #002 still lacks the parameterized manifest/reconciliation runner
needed to enforce its stop conditions and produce the designed 16-game/32-execution evidence
mechanically. Do not run Stage #002 until that evidence-only runner is implemented and audited.**
