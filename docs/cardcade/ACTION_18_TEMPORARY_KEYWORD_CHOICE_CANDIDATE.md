# Action #18 — Temporary Keyword Choice candidate

Status: frozen implementation candidate for independent review only. Not accepted; merge and Action #19 are unauthorized.

## Baseline and scope

Starting main: `aa4c3371c931b4ef4cb6f36393c3346af22cf285` (banked Action #17).
Branch: `codex/cardcade-action18-temporary-keyword-choice`.
The candidate commit containing this document is the freeze reference; its exact SHA is reported in the handoff.

Changed paths:
- `src/tmnt_design_studio/card_interpreter07.py`
- `src/tmnt_design_studio/engine07.py`
- `src/tmnt_design_studio/smoke01.py`
- `tests/test_temporary_keyword_choice_action.py`
- `docs/cardcade/ACTION_18_TEMPORARY_KEYWORD_CHOICE_CANDIDATE.md`

## Frozen corpus and grammar

Corpus: `cardcade/card-model-0.6.json`, Wingnut, Bat on the Belfry, Oracle ID `392a71c7-8f6d-46b8-bcc3-613e086d86ed`.
Exact first Oracle fragment:

> Alliance — Whenever another creature you control enters, Wingnut gains your choice of flying, menace, or haste until end of turn.

The anchored grammar requires this Alliance wording, this ordered three-keyword choice, and this duration. Its source reference must match the source card's full name or comma-delimited short name. This is generic self-reference validation, not Wingnut-specific execution dispatch. Near-neighbor wording and mismatched self-reference remain unsupported.

## Preserved implementation

The interpreter represents the bounded choice explicitly. Alliance queues a normal trigger and resolves through the existing Stack/Priority lifecycle. A generic injected chooser follows the existing Alliance chooser pattern; its deterministic default selects the first available keyword (flying). Resolution validates the choice, grants exactly one temporary keyword to the authenticated source incarnation, and records the selected keyword, duration, source, trigger, and event lineage. Existing temporary-effect storage and cleanup expire the grant. Temporary Haste is observed by attack eligibility. Trigger provenance rejects fabricated or relinked sources; a departed source does not pass its grant to a replacement incarnation.

No gameplay code was changed during checkpoint completion. The only test edit was Ruff's import-block fix. Smoke bookkeeping replaces only the two intentionally changed canonical Git-clean blob identities using the existing `_git_text_identity` mechanism (`core.autocrlf=true`, path-aware `git hash-object`):

- engine07.py: `98b7483ffba3a7127ddee79ccc4dc8075bc35eda`
- card_interpreter07.py: `ea2b6e7c824d8451d48959ac75f7839d616ec1f2`

Historical evidence and Action #17 remain intact.

## Local Windows validation (2026-09-05)

- `uv run pytest tests/test_temporary_keyword_choice_action.py tests/test_smoke01_runner.py tests/test_stage02_runner.py tests/test_stage002_runner.py -q`: **140 passed**.
- `uv run pytest -q`: **817 passed, 1 skipped**.
- `uv run ruff check`: **passed**.
- `uv run ruff format --check`: **270 files already formatted**.
- `git diff --check`: **passed**.

Both pytest runs emitted one cache-write permission warning for `.pytest_cache/v/cache`; all tests completed. The preserved 814 passed / 3 failed / 1 skipped result is superseded by the full result above after the canonical identity update. No broad calibration or simulation batch was run.

## Dependencies and evidence limits

Flying and Menace are authoritatively granted, but their broader combat restrictions remain unsupported dependencies; this candidate does not implement those subsystems. Haste support is bounded to the existing attack-eligibility path. The chosen keyword is recorded in engine history; this packet does not claim a new measured conformance or recovery-coverage result.

The historical prioritization figures (15 reached occurrences, 14 games, 7 matchups, 2 solo-clearance opportunities) were supplied in the work order. They were not independently recovered from current GitHub-resident artifacts in this completion pass and are not new durable measurements.

Independent review must assess the exact frozen commit and its bounded semantics, provenance, deterministic choice, temporary lifetime, dependency reporting, and regression evidence. Stop after pushing this candidate: no self-acceptance, merge, Action #19, deck revision, or scope expansion.
