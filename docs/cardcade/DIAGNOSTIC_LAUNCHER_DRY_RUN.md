# Cardcade Diagnostic Launcher Dry Run

## Source and scope

- Authorized starting source: PR #413 `6612ba7ee36d7eeeb2b090a3a7664662d6fcdeac`.
- Tested launcher implementation: `688a53b707b03c56dbc01225d4078df6bf28dc2f`.
- Implementation branch: `feat/cardcade-diagnostic-launcher-dry-run`.
- Intended PR base: `fix/cardcade-diagnostic-capture-lifecycle` (PR #413).
- Accepted main verified locally and remotely: `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.
- Worktree was clean at test time. The launcher explicitly loads `src/tmnt_design_studio/stage002.py` from its own checkout and refuses a mismatched imported module path.
- Runtime: Python 3.12.10, pytest 8.4.2, Ruff 0.16.1.

This checkpoint did **not** invoke `stage002.run_game`, enter the gameplay loop, or execute a complete game. The injected executor only constructed a deterministic initial `Game`, bound its presence ledger through `DiagnosticExecutionCapture`, serialized the initial snapshot, and returned or raised an injected exception.

## Launcher behavior

`tools/cardcade_diagnostic_launcher.py` is fixed to the committed Acceptance Match #001 specification: April O'Neil vs. Casey Jones, canonical orientation, seed 7231, seats `april-oneil-p0.1` and `casey-jones-p0.1`. It verifies the clean source, accepted-main identity, ancestry from PR #413, exact imported Stage 002 path, and the unique committed match specification before dispatch.

Each launcher instance is consumed by its first call. A local call guard permits one executor invocation. The CLI has no executor override, pairing loop, seed expansion, retry, batch, or calibration option. Evidence is created in a new child of `.cardcade-diagnostic-runs`; existing directories and paths outside that root are rejected. JSON writes use temporary files and atomic replacement. The final manifest records SHA-256 for each artifact, while run metadata records the match, interpreter, code/data identities, and explicit zero-retry/one-call controls.

On execution failure, the launcher uses the accepted `DiagnosticExecutionCapture`, writes the original error and traceback, serializes an available authoritative snapshot and presence ledger, attempts reconciliation, and re-raises the original exception. An unbound failure does not receive a fabricated snapshot. If evidence persistence fails after a successful invocation, the launcher raises `EvidencePersistenceError` and states that it must not be retried. Exception-path persistence failures are attached as an exception note when supported; the original exception remains the raised exception.

The environment check caught that the reusable Python environment had another editable Cardcade checkout installed. The launcher now prioritizes its own `src` directory and preflight rejects any Stage 002 module imported from another worktree. This was corrected before the final run.

## Exact synthetic selection and result

Command, from the isolated worktree:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; & C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe -B -m pytest -q `
  tests\test_cardcade_diagnostic_launcher.py::test_synthetic_success_serializes_reconciliation_and_integrity_hashes `
  tests\test_cardcade_diagnostic_launcher.py::test_injected_failure_preserves_original_exception_and_bound_snapshot `
  tests\test_cardcade_diagnostic_launcher.py::test_failure_before_binding_is_persisted_without_fabricated_snapshot `
  tests\test_cardcade_diagnostic_launcher.py::test_launcher_instance_cannot_be_reused_for_second_invocation `
  tests\test_cardcade_diagnostic_launcher.py::test_existing_output_directory_is_rejected_before_executor_call `
  tests\test_cardcade_diagnostic_launcher.py::test_persistence_failure_after_synthetic_execution_is_never_retried `
  tests\test_cardcade_diagnostic_launcher.py::test_committed_match_configuration_is_exact `
  tests\test_cardcade_diagnostic_launcher.py::test_output_directory_cannot_escape_isolated_diagnostic_root
```

Result: **8 passed, 0 failed, 0 skipped**. The successful synthetic invocation recorded one executor call, zero retries, zero additional seeds, no batch/calibration, successful reconciliation, zero invariant violations, and no reconciliation stop records. The exception cases retained original exception identity and did not cause a second invocation.

## Synthetic artifact integrity

The successful fixture output is preserved locally at:

`.cardcade-diagnostic-runs/diagnostic-game-test-pytest-16-test_synthetic_success_seriali0`

The synthetic game state is at setup/turn 0; this is fixture construction evidence, not a played game. Reconciliation completed. Artifact manifest SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| `events.json` | `ba66ea73fda4ea377387f3f3e7ee6e92e766a50ea5a9a6df26a7fae1bef53794` |
| `priority_stack_combat_trace.json` | `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570` |
| `reconciliation.json` | `e0d9e585393841ebfdf585f86bc8df2a7716d35a4b4017baea704fcef583ffbc` |
| `run_metadata.json` | `06563681f16d5e4d2de47dcf1541a674d4a1008f711b62ef01cb7ad8871e4ad5` |
| `run_status.json` | `3eb0590ba28cbe155895c15d34a9af5a2d8fa1e86cc80d808b45d65f1597b0f7` |
| `snapshot.json` | `6ffb044515e4137ee037d92f1057568ec8b2690f72f7f48df6ce97f42ec08a9c` |
| `stage_manifest.json` | `e8fefc0bd0defb31478efcab4b51c5bb77da0d4839d730572a4fa1a19d5f5db6` |

The stage-manifest digest was `a556f5c03765732f3343270949d09e4a87145e72921582188858ab249e5f98df`. Frozen input identities recorded by the launcher:

| Input | SHA-256 |
| --- | --- |
| Frozen card data JSON | `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402` |
| Frozen card data manifest | `6b5271af75150a361f77e7b89306c709959dfdf497c448dfdc978e5dc9a17950` |
| April prototype deck | `684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4` |
| Casey prototype deck | `0fc0adbb370ecfddad03692a4229a04b23268739914a8f2a004b8e042ff3cebb` |
| Baseline 005 manifest | `532bad7e489eb25f3184b5a90487e1361f7a2b19b8c02cac3c4115a0fc3e14bc` |
| Stage 002 source | `69ecb217234ac892509de0fbe6417601826909b3fceba77f4a865d4959db8f1b` |

## Quality checks

- Ruff format check on the two changed Python files: passed.
- Ruff lint on the two changed Python files: passed.
- `git diff --check`: passed.
- The launcher and tests are the only added Python files; `.gitignore` adds only `.cardcade-diagnostic-runs/` so diagnostic output cannot dirty the validated worktree.
- Accepted main, PR #413, frozen decks, Baseline 005 inputs, and historical evidence were not changed.

## Remaining limits and recommendation

This validates the launcher's fixed configuration, opt-in capture integration, serialization, reconciliation, output isolation, exception handling, and one-call controls using synthetic state. It does not establish that a complete game finishes, that all live gameplay evidence is complete, or that the CLI's actual game path is safe to authorize. The executable entrypoint remains intentionally uninvoked.

**Recommendation: READY FOR INDEPENDENT LAUNCHER AUDIT.** HQ authorization is still required before any complete game is started.
