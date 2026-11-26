# PR #425 Final Independent Integration Review

## Verdict

**ACCEPT for merge** of PR #425's cumulative source into `main`, subject to HQ's separate merge decision.

This is a code-integration verdict only. It does not approve runner deployment, production signing keys, real permits, or gameplay. No merge or gameplay was performed during this review.

## Exact source and ancestry

- Candidate reviewed: `92a29a3263d8555029904e8d4c9f097f38c50605`.
- Accepted `main`: `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`; confirmed as the remote and local main at review time.
- Candidate is exactly 105 commits ahead and zero behind main; main is its merge base and ancestor.
- PR #425 points to the candidate SHA and targets main. It is open, draft, and GitHub reports it mergeable.
- Fresh independent detached worktree: `C:\\projects\\tmt\\.audit-pr425-final`; HEAD matched the candidate and source worktree remained clean.

The 65-file cumulative diff was independently enumerated and classified:

| Area | Files | Review |
| --- | ---: | --- |
| Runtime modules | 5 | Engine, mana ledger, interpreter, pilot, Stage 002 |
| Tools | 2 | Diagnostic launcher and historical stop-ledger tool |
| Tests/support | 30 | Synthetic mechanics, integration, launcher, capture, and evidence coverage |
| Documentation/evidence reports | 25 | Acceptance records and preserved provenance |
| Project config | 3 | `.gitignore`, `pyproject.toml`, `uv.lock` |
| **Total** | **65** | **16 modified, 49 added** |

No deck, card-data, or Baseline 005 path is changed. The implementation ancestry is preserved; no report-only audit branch was introduced into the source history.

### PR #425 description correction

The PR body now accurately states that candidate HEAD `92a29a3263d8555029904e8d4c9f097f38c50605` has parent `d0dcf247a7ef0fc78e3e34f6841433dfb7903b6a`, and its exact commit subject is `[skip ci] Document reconciliation authenticity correction`. This changed PR metadata only; candidate source HEAD is unchanged.

## Independent validation

The 198 executions recorded in PR #425 were independently rerun at the exact candidate SHA. The selections overlap, so 198 is not a count of unique test cases.

| Selection | Result |
| --- | --- |
| Launcher, exact source/input binding, signatures, single-use claims, capture, terminal combat, reconciliation, valid-digest forgeries | 55 passed, 0 failed, 0 skipped |
| Combined PR #381–#386 engine and final-fidelity selection | 56 passed, 0 failed, 0 skipped |
| Pilot fidelity selection | 56 passed, 0 failed, 0 skipped |
| Restricted ability-payment compatibility | 27 passed, 0 failed, 0 skipped |
| Main-cast trigger/priority composition | 4 passed, 0 failed, 0 skipped |
| **Total across selections** | **198 passed, 0 failed, 0 skipped** |

The exact selected nodes are documented in the candidate's launcher, reconciliation, combined validation, pilot fidelity, and restricted-payment acceptance reports. The main-cast selection includes Punks → Pizza → Ravenous Robots via the ordinary main-action path. All selected cases use synthetic fixtures; no complete game or automated match ran.

Environment: Python 3.12.10, pytest 8.4.2, cryptography 46.0.7, Ruff 0.16.1. A fresh locked environment was created offline from `uv.lock`; `uv lock --check` passed. All 37 changed Python files passed Ruff format and lint. The full base-to-candidate `git diff --check` passed.

## Authorization and evidence boundaries

Source inspection and the synthetic selection confirm:

- The production `TRUSTED_HQ_AUTHORIZATION_KEYS` registry is empty. No real authorization can pass; unknown/unconfigured signing keys fail closed.
- The launcher verifies exact source and input identities, Ed25519-signed approval and run-authorization documents, and the bound run fields.
- Authorization claims use exclusive file creation and `fsync`; cross-process duplicate claims and claim persistence after execution failure are covered by the passing synthetic tests.
- The launcher preserves supplied and trusted reconciliation reports, compares complete canonical reports from independent deep-copied inputs, and blocks inconsistent or incomplete evidence.
- The source currently pins `ACCEPTED_MAIN` to `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`. After integration changes main, the launcher will fail closed on that mismatch until a reviewed follow-up updates the expected source baseline and HQ approves the resulting exact source.

These checks support merging the source while keeping diagnostic execution blocked pending a later, separately reviewed trust-anchor and source-pin update.

## Historical preservation

All six approved frozen-input hashes matched. All nine files in the preserved PR #406 replay artifact manifest matched; the manifest SHA-256 is `8d37d74145fa0349d86515fc96c0ba8155247343febd2b48db811bbc189d596d`. The three replay stop records remain unchanged:

1. `stop-000001`: `illegal_mutation`, turn 16, `combat_damage`.
2. `silent_approximation`: `presence_evidence_missing`.
3. `silent_approximation`: the preserved trample/combat event and object references.

Deck prototypes, Baseline 005, frozen card data, and historical artifacts were not modified.

## Separate deployment concern

The proposed Windows runner design on PR #424 is documentation only. No production runner has been designated, no ACLs were changed, and no revocation or permit-expiry service is implemented. The current shared development tree's broad ACLs are unsuitable for deployment. The launcher has no online revocation lookup or expiry mechanism. These are deployment blockers, not source-merge blockers: the empty production key registry keeps the candidate fail-closed.

## Handoff

**Recommendation: ACCEPT PR #425 for merge.** Keep deployment, real permits, and gameplay behind separate HQ gates.