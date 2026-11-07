# Ravenous Robots Artifact-Cast Trigger Acceptance

## Source and frozen inputs

- Authorized source and base branch: `review/cardcade-april-end-step-draw` at `09d14fd7e968b35d06c30a6c5bf3a904fe28f2b3`.
- Isolated branch: `review/cardcade-ravenous-robots` in `.cardcade-ravenous-robots`.
- Preserved failing reproduction: `e2fc3d04397b0b4f19f5e779d434999fe84c084d`.
- Tested implementation and test source: `e87d4b37fa96cdacc33a42104635e6b4720f710e`.
- Frozen card data: `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json`, SHA-256 `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`.
- Frozen card-data manifest: `cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json`, SHA-256 `6b5271af75150a361f77e7b89306c709959dfdf497c448dfdc978e5dc9a17950`.
- Ravenous Robots Oracle identity: Oracle ID `45873747-f2a4-4d83-9492-bfc97df7b605`; frozen text: “Whenever you cast an artifact spell, create a 1/1 colorless Robot artifact creature token.”
- Spicy Oatmeal Pizza Oracle ID: `9665f940-c0a4-4d3e-b889-8049cf549a4f`; it is an `Artifact — Food` spell.

The original regression was committed before the engine correction. At `e2fc3d0`, casting Pizza generated one authenticated `SPELL_CAST` event with `Artifact` in its type line, but no Ravenous Robots `CREATE_TOKEN` trigger. The selected regression failed on the absent trigger. It remains as the first commit on this branch.

## Implemented behavior

The shared spell-cast event recorder now dispatches artifact-cast token triggers after authenticating the original `SPELL_CAST` event. It checks the event's card type line, casting player, source identity, and battlefield snapshot, then scans only that player's authoritative battlefield for fully supported matching token abilities. It uses the existing token parser, trigger object, Stack, priority, token creation, artifact-entry, and reconciliation paths.

Each matching Ravenous Robots source creates one trigger for the cast. The trigger sits above the cast spell, retains its source and cast-event identity if Ravenous Robots leaves, and resolves only after both players pass priority. Resolution creates the parser-derived 1/1 colorless Robot artifact creature token. Direct artifact permanent entry does not count as a cast. Nonartifact casts and opponent casts do not qualify. Repeated delivery of the same event is deduplicated. The original cast evidence remains after the spell is countered.

Existing battlefield-entry token triggers retain their prior immediate compatibility behavior; the all-pass gate applies specifically to token abilities whose authenticated event is `SPELL_CAST`. April's cast-history behavior is unchanged.

## Synthetic validation

Environment: Python 3.12.10, pytest 8.4.2, Ruff 0.16.1. Python executable: `C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe`; Ruff executable: `C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\ruff.exe`.

Executed on code/test HEAD `e87d4b37fa96cdacc33a42104635e6b4720f710e`:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='C:\projects\tmt\.cardcade-ravenous-robots\src'
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe' -B -m pytest -q `
  tests\test_ravenous_robots_artifact_cast.py `
  tests\test_april_end_step_draw.py::test_countered_spell_remains_in_april_cast_history `
  tests\test_april_end_step_draw.py::test_sneak_announcement_creates_one_authenticated_cast_event
```

Result: **17 passed, 0 failed, 0 skipped**. The 15 Ravenous nodes cover ordinary Pizza and artifact-creature casts, nonartifact and opponent exclusions, non-cast entry, late source entry, source departure, multiple sources, trigger deduplication, Stack order, two-player priority, token characteristics and artifact-entry tracking, event reconciliation, countering, and April compatibility. The additional selected April nodes verify historical cast evidence after countering and a single authenticated Sneak cast event.

Quality checks on the same source:

```powershell
ruff format --check src\tmnt_design_studio\engine07.py src\tmnt_design_studio\card_interpreter07.py tests\test_ravenous_robots_artifact_cast.py
ruff check src\tmnt_design_studio\engine07.py src\tmnt_design_studio\card_interpreter07.py tests\test_ravenous_robots_artifact_cast.py
git diff --check
```

Results: formatting check passed; lint passed; `git diff --check` passed. Reconciliation produced no stop records. The execution index contained the expected `tokens_created` and `trigger_resolved` references, each linked to the Ravenous source. No complete games or game runner were executed.

## Limits and preservation

Dispatch is bounded to the exact artifact-cast token ability pattern and token payloads already fully supported by the existing parser. Unsupported token wording remains unimplemented and does not receive fabricated execution evidence. No deck, pilot, accepted-main, PR #386/#388/#389, frozen card data, or historical artifact changes are part of this candidate.
