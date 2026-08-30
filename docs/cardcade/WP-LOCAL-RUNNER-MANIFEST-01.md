# WP-LOCAL-RUNNER-MANIFEST-01 — Establish committed Local Runner manifest

Owner: Cardcade
Status: Authorized
Starting SHA: 3fcce8ca7c7edff49327ec123c319b6704f544f5

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
- Existing repository validation entry points and their committed documentation/configuration.
- Provisioned Windows validator identity already registered in Control Room.
- Control Room Local Runner contract requiring a tracked, HEAD-clean `.cardcade/runner.json`.

## Acceptance contract
- `.cardcade/runner.json` is valid JSON and tracked in Git.
- It identifies `WP-LOCAL-RUNNER-MANIFEST-01`, an explicit baseline ref, bounded scope summary, evidence directory, and explicit executable/argument command entries.
- Every declared command is verified against existing repository-supported validation entry points; no shell interpolation or arbitrary command text is introduced.
- Local validation on the exact candidate must prove repository/path/HEAD/cleanliness, manifest tracked-and-unmodified status, declared commands, and evidence bindings.
- Relevant repository validation, tests, lint/format, terminology/encoding checks, and `git diff --check` pass as applicable.
- Candidate SHA/fingerprint and validation evidence are preserved for independent audit.
- Independent audit is required before Owner integration authorization.
- Successful implementation does not authorize Stage execution, calibration, deck revision, or Prototype 0.3.

## Stop conditions
- The repository does not expose enough authoritative information to construct the manifest without guessing command semantics or schema.
- The Control Room manifest schema contradicts repository governance or requires broader architecture work.
- Any required validation command would change simulator/gameplay behavior rather than validate it.
- Candidate identity cannot be bound reproducibly to the exact tested commit.
- Scope would need to expand beyond the runner-manifest commissioning blocker.

## Required handoff
Report candidate branch and exact SHA/fingerprint; changed files; manifest fields and command bindings; validation results; evidence locations/hashes; known limitations; push status; independent-audit status; and the exact recommended next action.

## Gate authorization
This packet authorizes only construction and validation of the repository Local Runner manifest. It does **not** authorize merge, Stage execution, calibration, deck revisions, or Prototype 0.3.
