# WP-LOCAL-RUNNER-MANIFEST-01 — Establish committed Local Runner manifest

Owner: Cardcade
Status: In progress — candidate ready for Windows validation
Starting SHA: 3fcce8ca7c7edff49327ec123c319b6704f544f5
Related PR: #65

## Objective
Add the repository-owned `.cardcade/runner.json` contract required for the provisioned Windows Cardcade Local Runner to establish a signed heartbeat and perform genuine deterministic local validation against `egggggman/tmt`.

## Scope
- Add `.cardcade/runner.json` on this candidate branch.
- Bind it to this Work Packet and the authoritative repository.
- Declare only explicit deterministic validation commands already supported by the repository.
- Use an evidence location outside Git blobs for generated local evidence.
- Add or adjust only documentation/tests strictly necessary to validate the manifest contract.

## Prohibited changes
- No deck revisions.
- No Prototype 0.3 authorization.
- No calibration or Stage execution.
- No simulator semantics, Actions, balance assumptions, or gameplay changes.
- No Control Room/Replit feature work.
- No weakening of clean-checkout, committed-manifest, signed-heartbeat, candidate-identity, audit, or two-key integration gates.
- No direct merge to `main` without independent audit and Owner authorization.

## Inputs
- `docs/hq/WORK_PACKET_SPEC.md`.
- Current `main` starting SHA above.
- `docs/hq/RECOVERY.md`, which documents the repository's `uv` validation workflow.
- `pyproject.toml`, which declares Python >=3.12 plus pytest and Ruff development tooling.
- Provisioned Windows validator identity already registered in Control Room.
- Control Room Local Runner contract requiring a tracked, HEAD-clean `.cardcade/runner.json`.

## Authoritative command bindings
The manifest uses only commands already documented or directly supported by the repository configuration:

1. `uv run pytest` — full repository test suite.
2. `uv run ruff check .` — repository lint check.
3. `uv run ruff format --check .` — repository format check.
4. `git diff --check` — Git whitespace/error check.

`tools/validate_repo.py` is not declared because it is not present on current `main`. No command is invented to stand in for it.

The evidence directory is `C:\Projects\tmt-evidence-archive\local-runner`, outside ordinary repository history.

## Acceptance contract
- `.cardcade/runner.json` is valid JSON and tracked in Git.
- It identifies `WP-LOCAL-RUNNER-MANIFEST-01`, baseline `main`, bounded scope summary, external evidence directory, and explicit executable/argument command entries.
- No shell interpolation or arbitrary command text is introduced.
- Local validation on the exact candidate must prove repository/path/HEAD/cleanliness, manifest tracked-and-unmodified status, declared commands, and evidence bindings.
- All four declared commands must pass on Windows through the Local Runner.
- Candidate SHA/fingerprint and validation evidence are preserved for independent audit.
- Independent audit is required before Owner integration authorization.
- Successful implementation does not authorize Stage execution, calibration, deck revision, or Prototype 0.3.

## Stop conditions
- The Control Room rejects this manifest schema or command contract.
- Windows validation exposes a missing dependency, dirty checkout, command failure, identity mismatch, or evidence-binding defect.
- Any correction would broaden beyond repository runner commissioning.
- Candidate identity cannot be bound reproducibly to the exact tested commit.

## Required handoff
Report candidate branch and exact SHA/fingerprint; changed files; manifest fields and command bindings; Windows validation results; evidence locations/hashes; known limitations; push status; independent-audit status; and exact recommended next action.

## Current candidate
- Branch: `cardcade/local-runner-manifest`
- Manifest addition checkpoint: `b284da8e1cd102f46c78c8573916488ee49ccfe8`
- Changed implementation/configuration: `.cardcade/runner.json`
- Governance record: this Work Packet
- Windows validation: **required; not yet performed**
- Independent audit: **required; not yet performed**

## Gate authorization
This packet authorizes only construction and validation of the repository Local Runner manifest. It does **not** authorize merge, Stage execution, calibration, deck revisions, or Prototype 0.3.
