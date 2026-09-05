# Action #19 ? Stun Counters candidate

Status: implementation candidate for independent review. The owner supplied independent acceptance of the post-Action-18 measurement and authorization to implement Action #19. This document does not self-accept the candidate, authorize a merge, or authorize Action #20.

## Baseline and preserved evidence

Accepted gameplay baseline: `0f679bb766695bbfe0ea634785e97b934f239464` (Action #18 ? Alliance).
Evidence-only parent commit: `c186cefc095a63daf54c7544f53f4f24fa44742c`.
Candidate branch: `codex/cardcade-action19-stun-counters`.
The implementation commit containing this document is the frozen candidate; its full SHA is reported in the handoff.

The evidence commit contains exactly these four files, with original bytes preserved:

- `docs/cardcade/POST_ACTION_18_ACCEPTANCE_STAGE_002_RESULTS.json`
- `docs/cardcade/POST_ACTION_18_ACCEPTANCE_STAGE_002_RESULTS.json.sha256`
- `docs/cardcade/POST_ACTION_18_MEASUREMENT_ACTION_19_PROPOSAL.md`
- `docs/cardcade/POST_ACTION_18_UNSUPPORTED_RANKING.json`

Raw result SHA-256, verified against both the committed blob and the untouched local file:
`2daa13956f2a8571d3d77f6c48d9f373ec516ad206eb47e387d78c42b72796ec`.
Raw size: 11,936,567 bytes.
Git initially normalized line endings in the unpushed evidence commit. That commit was corrected before candidate freezing, without editing or regenerating any artifact. All four final committed blobs equal the original local bytes. Staged evidence whitespace validation used `git -c core.whitespace=cr-at-eol diff --cached --check` to recognize the preserved CRLF endings; ordinary whitespace checks pass for the implementation.

The accepted screening sample found 9 occurrences, 6 games, 2 matchups, and 0 solo-clearance games for the selected semantic. This establishes priority only. It supplies no balance conclusion, optimal win-rate change, or guarantee of maximal game clearance. The preserved measurement predates Action #19 and is not a measurement of this candidate.

## Frozen semantic and bounded behavior

Frozen corpus: `cardcade/card-model-0.6.json`, Utrom Scientists, Oracle ID `89793c8c-98a3-4621-ad3d-cfc5949c65da`, first fragment:

> When this creature enters, tap up to one target creature and put a stun counter on it. (If a permanent with a stun counter would become untapped, remove one from it instead.)

Semantic key:
`89793c8c-98a3-4621-ad3d-cfc5949c65da:0:0:37ce5a4d7762180cb84023a47a371810a02d0a49c7788466bf3c6c2192346f20`.

Recognition requires the exact fragment and a creature source, without card-name dispatch. Changed quantities, target classes, parent triggers, or other near-neighbor grammars remain unsupported.

The existing self-ETB detection creates a normal trigger. At stack placement, an injected deterministic chooser receives sorted creature incarnation IDs plus `None`; the default chooses the first ID, and `None` declines the optional target. Both controllers' creatures, including the source and already-tapped creatures, are eligible within the supported target model. This is deterministic choice plumbing, not Pilot optimization.

Resolution requires the existing Stack/Priority all-pass lifecycle. Frozen references bind the original rules event, trigger, stack ability, source, target, and card incarnations. A legitimate source departure does not cancel its stacked ability. The target is rechecked at resolution; departure or loss of creature type produces no effect and cannot redirect to a new incarnation. A controller change alone does not invalidate an unrestricted creature target. Fabrication, same-ID object substitution, target relinking, trigger relabeling, and altered provenance fail closed.

A legal target is tapped and receives one stun counter through existing `place_counters` storage and state-based-action checks. Existing counter placement replacement-opportunity reporting is retained. The counter is also placed when the target was already tapped.

The existing turn untap path now calls `untap_permanent`. A tapped permanent with stun counters stays tapped and loses exactly one counter per attempted untap. The last counter's dictionary key is removed, consistent with existing counter invariants. A later attempt untaps normally. Already-untapped permanents retain their counters. Repeated supported ETBs can create multiple counters. Zone changes create new objects and do not transfer stun state.

## Evidence and conformance

The bounded immutable history records target selection, tap state, counter placement, trigger resolution, and prevented untaps. Entries include relevant object IDs, trigger/event IDs, controller, before/after values, and counter-placement cursors. Live invariants cross-check the registered source/target objects, original rules events, immutable event records, and current stun totals.

Snapshots preserve the stun history and targeted trigger IDs. Stage #002 reconciliation and saved-result validation cross-check the serialized history against tap/counter/resolution records before treating a stun trigger as EXECUTED. Legacy evidence with no stun history remains readable unless it asserts an unbacked stun execution. No new coverage measurement was run.

## Changed implementation paths

- `src/tmnt_design_studio/card_interpreter07.py`
- `src/tmnt_design_studio/engine07.py`
- `src/tmnt_design_studio/stage002.py`
- `src/tmnt_design_studio/smoke01.py`
- `tests/test_stun_counters_action.py`
- `docs/cardcade/ACTION_19_STUN_COUNTERS_CANDIDATE.md`

Smoke bookkeeping updates only the three intentionally changed source identities, using existing path-aware Git-clean blob hashing:

- `engine07.py`: `bce87c841e38558794fda7a6d269df9883148d55`
- `card_interpreter07.py`: `5587960afc3c47a071ba01dafecb37192f561402`
- `stage002.py`: `5bd2711bdc3cbc37d2315c2cbd9b59e8ae5eaf02`

Frozen decks, corpus, historical measurement contents, and other source identities are unchanged.

## Validation ? 2026-09-05

Used the existing local `.venv/Scripts/python.exe` with `-B`; pytest used `-p no:cacheprovider`. No dependencies were installed.

- Focused Action #19 tests: 48 cases, all passed as part of the final combined run.
- `pytest tests/test_stun_counters_action.py tests/test_smoke01_runner.py tests/test_stage02_runner.py tests/test_stage002_runner.py -q -p no:cacheprovider --tb=short`: **172 passed**.
- `pytest -q -p no:cacheprovider --tb=short`: **865 passed, 1 skipped**.
- `ruff check`: **passed**.
- `ruff format --check`: **273 files already formatted**.
- `git diff --check`: **passed**.

Focused cases cover real frozen-corpus recognition, generic recognition, negative grammars, Stack/Priority, optional targets, tapped targets, repeated counters, actual turn untap, later normal untapping, source departure, target type/controller changes, zone reincarnation, fabricated/relinked objects, event and counter-state tampering, serialized Stage evidence, unsupported targeting dependencies, and identical-seed replay.

## Remaining boundaries and dependencies

There is one current gameplay untap path, the turn untap step; it uses the shared bounded operation. No new untap spell, activated untap ability, or untap-cost subsystem is implemented.

Shroud, Hexproof, Ward, Protection, and explicit cannot-be-targeted text on a chosen target trigger an explicit unsupported-dependency error. These systems are not implemented here; the guard is conservative and may reject a situation that a complete rules engine could resolve. Arbitrary external continuous targeting restrictions remain outside the bounded model. Other absent replacement effects, counter transfer/removal, proliferate, and unrelated counter abilities are not supplied by this Action.

Rules scoping was checked against Wizards' [Dominaria United release notes](https://magic.wizards.com/en/news/feature/dominaria-united-release-notes-2022-08-26): one counter replaces each untap attempt, and already-tapped targets can receive counters. The implementation does not add a general replacement-effect framework.

No Fugitive Droid, unrelated Utrom Scientists behavior, deck changes, balance tuning, calibration, broad gameplay batch, Prototype 0.3, GUI, packaging, or infrastructure work was performed. This candidate awaits independent review of its exact frozen SHA; no acceptance or merge is implied.
