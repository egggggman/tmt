# Canonical Frozen-Input Hashing Acceptance Audit #1

## Verdict

**ACCEPT — canonical frozen-input hashing is semantically trustworthy and suitable to bank.**

This accepts immutable candidate `a3c5738a02b57f64174f54cb4e181ca2931bc4f8`. It does not authorize Smoke Stage 0.1 execution; Readiness Audit #2 and integration gates still apply.

## Scope

- Accepted Audit #2 checkpoint: `ab27e89`
- Correction document SHA-256: `b58778610e391a128bb3503fed7872b102ba2214090e112ee41c19d9de4c9467`
- Runner Audit #1 SHA-256: `7c7d82ead1249aa4294f3947ac70c161ca1380614a875e2d2f0f0684d52d8141`
- Runner Audit #2 SHA-256: `fb5612dabb774610ca8097944983a8080244727ba9af7a4fd3d5e4c48c3a0681`

The candidate is exactly one commit beyond Audit #2 and changes only `smoke01.py`, its tests, and the hashing-correction document. No engine, Action, Pilot, deck, or gameplay file changed. No Smoke games were run.

## Independent contract audit

Tracked text uses `git -c core.autocrlf=true hash-object --path=<tracked-path> <candidate-file>` after requiring the path in `git ls-files`. Independent probes established that LF and CRLF representations of identical tracked text have one Git-clean identity; a substantive textual change changes that identity; and missing or untracked required inputs fail closed.

The implementation hashes the actual working-tree file through Git's clean filter, not `HEAD:<path>`. A dirty substantive edit therefore cannot borrow the committed identity: manifest preflight observes a different digest and rejects execution.

Binary/non-Git input uses `raw-bytes-sha256-v1`; any byte change, including CRLF versus LF bytes, changes its identity.

The reconstructed manifest records `smoke-frozen-input-hashing-v2`, `git-clean-blob-oid-sha1-v1`, `raw-bytes-sha256-v1`, each input's scheme/digest, and the runner identity. The matrix remains exactly 45 pairings, 180 distinct games, and 360 duplicate executions.

## Reconfirmed runner invariants

Focused Smoke and Stage #002 regressions reconfirmed duplicate evidence, authenticated and exclusive EXECUTED/REACHED/PRESENT classifications, reconstructed per-game and aggregate labels, derived `balance_valid: false`, re-signed tamper rejection, and atomic preflight/post-duplicate failure evidence.

## Validation

- Full suite: **622 passed / 1 skipped**
- Focused Smoke + Stage #002: **62 passed**
- Ruff check and format: clean (**48 files already formatted**)
- `git diff --check`: clean
- Exact-candidate Linux CI: PASS, runs `32614293920` and `32614296488`
- PR #53: OPEN, non-draft, MERGEABLE / CLEAN, head exactly `a3c5738a02b57f64174f54cb4e181ca2931bc4f8`

## Gate

Bank this report unchanged, then perform Readiness Audit #2 against the complete Stage 0.1 contract. This audit alone does not authorize integration or Smoke execution.
