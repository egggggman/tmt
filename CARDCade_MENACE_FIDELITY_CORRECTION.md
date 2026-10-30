# Cardcade Menace Fidelity Correction

**Recommendation:** READY FOR INDEPENDENT REVIEW
**Frozen parent:** `fd28f68915c4e7cb6af3444bf41b96608dee712c`
**Review branch:** `review/menace-fidelity-evidence`
**Correction commit:** `c3ae05e` — `Record Menace block options and pilot selection`
**Scope:** Menace block legality inspection and decision-evidence correction; synthetic validation only

## Menace rules contract

The current official Comprehensive Rules define Menace as an evasion ability and say a creature with Menace cannot be blocked except by two or more creatures (CR 702.111a–c). The declare-blockers rules require chosen blockers to be untapped creatures, each chosen blocker to be assigned to one attacking creature, and restrictions to be obeyed (CR 509.1a–b). Requirements are checked separately (CR 509.1c). [Official Comprehensive Rules (June 19, 2026)](https://media.wizards.com/2026/downloads/MagicCompRules%2020260619.pdf). The Wizards keyword glossary gives the same Menace definition. [Menace glossary entry](https://magic.wizards.com/en/keyword-glossary).

The frozen card data used by Diagnostic 001 identifies Menace on Super Shredder and Raphael, Most Attitude. This review does not change those cards or infer additional card text.

## Demonstrated engine behavior

Inspection was performed against the exact frozen source checkout at `fd28f68915c4e7cb6af3444bf41b96608dee712c`; its detached checkout remained unchanged. The implementation on that source path behaves as follows:

1. `Game.legal_block_options()` enumerates assignments using the untapped creature blockers and the current attackers. A blocker is removed from the remaining set after assignment, so one blocker is not reused across attackers.
2. `_valid_block_assignment()` checks each attacker group. If an attacker has Menace, it rejects a nonempty group with fewer than two blockers. It also checks pairwise blocking legality and the supported single-block restriction.
3. `Game.execute_block_action()` revalidates the pilot’s option against a freshly generated legal-option set before declaring blocks. A fabricated one-block assignment against a Menace attacker is rejected.
4. Stage 002 passes the engine-generated options to `Pilot.choose_blocks()`. This defines the legal action surface; the pilot separately chooses one member of that surface. A chosen action is not proof of strategic quality.
5. Combat damage groups the accepted blocker assignments by attacker and resolves damage against those assigned blockers. Existing synthetic Menace, Trample, and strike-step tests cover the supported interactions exercised here.

**Legality verdict:** No Menace blocking legality defect was demonstrated in the frozen authoritative Stage 002 path. Menace legality was already implemented. This correction does not change option generation, action validation, block assignment, or damage resolution.

Diagnostic 001’s `unsupported_semantics` Menace warning is not, by itself, proof that runtime Menace legality was absent: the exact frozen engine contains the direct keyword checks and revalidation described above. The warning/conformance record and the engine’s concrete legality path are separate evidence surfaces.

The frozen source also contains a legacy `generate_blocks()` helper that greedily returns at most one blocker per attacker, but no call site in the frozen Stage 002 execution path uses it. This correction does not broaden that helper’s contract.

## Diagnostic 001 evidence gap

The preserved result records the T18 attackers as Squirrelanoids `object-000158` and `object-000163`, Super Shredder `object-000177`, and Tunnel Rats `object-000189`. Its accepted assignment is Raphael, Most Attitude `object-000192` blocking Tunnel Rats `object-000189`. The event does not contain the offered block options or the pairwise eligible-blocker map.

The verified frozen rules path and recorded T18 state make one point more certain: the final snapshot contains only one Raphael creature, Raphael, Most Attitude, and the accepted Tunnel Rats block is legal. With only that one blocker, Raphael could not legally block Menace Super Shredder. There is no evidence of an illegal Menace block or a damage assignment caused by one. Diagnostic 001 still does not disclose the exact options presented to the pilot or its decision process, and its result remains a one-game observation. Other fidelity limitations identified in the Diagnostic 001 review remain separate.

## Correction and changed files

The correction adds two audit events for combat declarations containing at least one Menace attacker:

- `block_options_presented` records attacker IDs, Menace attacker IDs, untapped creature blocker IDs, individually legal blocker IDs per attacker, and the exact legal configurations passed to the pilot. Recording occurs before the pilot is called, so the opportunity record survives a pilot exception.
- `block_option_selected` records the pilot’s returned configuration and whether that exact option appeared in the presented options. It is emitted before engine revalidation. The existing `blockers_declared` event remains the evidence of an accepted declaration.

Ordinary combat with no Menace attacker does not gain these additional events. All existing events remain intact. No combat state or decision policy is changed.

Files in correction commit `c3ae05e`:

| File | Change |
|---|---|
| `src/tmnt_design_studio/engine07.py` | Add Menace block-option and selection evidence methods. |
| `src/tmnt_design_studio/stage002.py` | Record options before `choose_blocks()` and the returned choice before engine validation. |
| `tests/test_menace_decision_evidence.py` | Add deterministic synthetic tests. |

The report itself is maintained as a separate review artifact and is not part of the correction commit.

## Synthetic validation

All tests construct disposable in-memory `Game` combat states. No `run_game`, Stage 002 full-game simulation, smoke game, or real gameplay was run.

| Validation | Result |
|---|---:|
| New Menace decision-evidence tests | **9 passed** |
| Existing Menace legality tests | Included below |
| Existing combat regression group: Menace, block-option enumeration, Trample, and strike damage steps | **73 passed** |
| Combined targeted total | **82 passed** |
| Ruff lint on the three changed code/test files | **Passed** |
| Ruff formatting check on the three changed code/test files | **Passed** |
| Git whitespace check and direct trailing-whitespace scan | **Passed** |

The new synthetic cases cover one eligible blocker, two blockers, three blockers, multiple Menace attackers with shared blockers, a supported power restriction, Menace conflicting with a supported maximum-one-blocker restriction, no legal Menace block opportunity, a selected configuration not present in the offered set, rejection of a fabricated single block, and preservation of the existing ordinary `blockers_declared` telemetry. The named cases overlap within nine tests.

The current engine does not model general “must block” requirements or requirement optimization. The Comprehensive Rules’ CR 509.1c requirement/conflict behavior is therefore outside this narrow correction and is not claimed as validated. Existing supported blocking restrictions were used in the synthetic cases; no unsupported requirement behavior was invented.

Tests ran on Windows with CPython 3.12.10 using the workspace’s existing test packages, with `PYTHONPATH` pointed at this review branch’s source. This was a disposable synthetic test environment; it is not the qualified runtime used by Diagnostic 001.

## Remaining limitations

- The new event records options and selection but does not explain the pilot’s strategy or prove that its choice is optimal.
- Full legal-option evidence can grow with the number of attackers and blockers. It is emitted only when at least one attacker has Menace; current combat generation already materializes the same option tuple.
- General blocking requirements and requirement conflicts remain unsupported in this engine.
- No new game was run, and this evidence-only correction does not retroactively add decision records to Diagnostic 001.
- Independent review of branch commit `c3ae05e` is still required before using the new telemetry in another diagnostic.

**READY FOR INDEPENDENT REVIEW**
