# DECKDAEMON 0.1 — Gate A read-only reader (accepted and integrated)

**Scope:** HQ accepted read-only synthetic data contract only, based on architecture draft PR #435. Gate A was squash-merged to `main` through PR #436 at `2e2b43413953d43775793b7fefc5edbab5cea346` from reviewed source `ff9cddb38dde7d678afd492c780b551f0ae17d32`. This is not a GUI, Windows executable, production security certification, or gameplay launcher.

**Parent source:** `main` `66fb857272365c1427450797ffdf69003365192c`.
**Engine defect remains separate:** draft PR #434 at `415cd2762b8c6435c314dd1c51619dd46c8b451f`; no edits to that PR or to engine code.

## Explicitly allowlisted sources

- The ten exact `decks/<slug>/PROTOTYPE_0.1.txt` paths only, using the canonical fixed roster in `src/deckdaemon_viewer/reader.py`. All ten exact filename presences were verified in GitHub at the parent source. No `PROTOTYPE_0.2`, `0.3`, generic filesystem browse, or path guessing.
- `docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json` only. The manifest has historical `OBL-BASELINE-005` provenance, not a live calibration result.
- **No diagnostic reports yet**: those require a separate reviewed fixture inventory, allowlist and schema audit. Return *not available*, not a fallback to a runtime launcher or a guessed report.

A caller may supply an **independently established** SHA-256 digest. When it matches the exact file bytes, `verified=True`; without it, the output is labeled **unverified local snapshot** and includes an *observed* SHA-256 only. Do not treat a digest supplied by the same mutable input as independent verification. Packaging needs a separately accepted immutable digest table and release-input selection.

## API

```python
from deckdaemon_viewer import read_prototype_01, read_baseline_005

deck = read_prototype_01(snapshot_root, "leonardo", expected_sha256=trusted_deck_digest)
historical = read_baseline_005(snapshot_root, expected_sha256=trusted_manifest_digest)
```

No CLI entry point. No GUI. No `engine07`, `stage002`, diagnostic launcher, `subprocess`, `socket`, database, or simulator import. No file or network writes in the reader.

## Fail-closed contract

- Static path components and frozen deck slug allowlist; reject traversal/unknown deck.
- Reject symlink **and Windows junction** root/path components and out-of-root resolution; require regular file.
- Bounded read: deck <= 1 MiB, manifest <= 256 KiB, strict UTF-8.
- Reject missing/inaccessible files, invalid or mismatched SHA-256, malformed JSON, duplicate JSON keys, NaN, incorrect schema/identity/roster, invalid win rates or matchup cell coverage.
- Explicit historical result labeling; never certify Standard legality, current balance, new gameplay, or trust in mutable files.
- OS-level sandboxing and hostile concurrent mutation are **not established** by this reader. Production installation must use a version-pinned immutable snapshot, with Windows reparse/junction/ACL checks as a later gate.

## Historical Windows correction and junction-classification amendment

The first exact Windows candidate `212168a...` failed due to a CRLF-sensitive test fixture and formatting; preserved. The later `02707ac416a735091fee43338834a48947515c81` candidate passed **16 tests with 1 symlink-creation skip**, plus Ruff lint, format and diff checks.

This new isolated review changes only the reader's link-component rejection and adds **three synthetic junction-classification tests** (root, intermediate and leaf) using monkeypatching of Python 3.12 `Path.is_junction()`, so Windows user privilege to create symlinks is not required for these test cases. These are tests of the explicit rejection branch, **not real NTFS junction/reparse behavior under concurrent changes**. The original link-creation test remains skipped on unprivileged Windows and must remain reported as a skip. A future real junction test and immutable/ACL-qualified snapshot are separate verification gates.

**Historical note:** the amendment above preceded exact-SHA validation of subsequent candidates. The final reviewed source passed the bounded Windows checks as recorded below.

## Accepted synthetic Gate A validation and limitations

The early Python 3.13.5 / pytest 9.0.2 **analogous candidate** ran **17 passed** in 0.08 seconds and `compileall` passed; this was preliminary historical evidence, **not** acceptance evidence for the final GitHub SHA.

The exact reviewed source `ff9cddb38dde7d678afd492c780b551f0ae17d32` was validated on Windows using Python 3.12.10 in the existing environment and in a fresh temporary `uv` environment: **19 passed, 1 skipped** in each. The single skip was the real symlink-creation test because the host did not permit creating symlinks. Ruff lint and format and `git diff --check HEAD^ HEAD` passed; the validation worktree was clean. The fresh `uv` environment installed pytest 8.4.2 and Ruff 0.17.6 from version ranges, **not a locked dependency reproduction**. See PR #436 Windows receipts and the [independent technical ACCEPT comment review](https://github.com/egggggman/tmt/pull/436#pullrequestreview-6067266155). GitHub recorded this as **COMMENTED**, not formal APPROVED, because the connected account was the PR author.

**Gate A acceptance is restricted to the synthetic, read-only reader contract.** The three junction tests mock `Path.is_junction()` and do not verify real NTFS reparse-point, junction or ACL behavior; the real symlink test was skipped. Hostile concurrent mutation protection, immutable version-pinned snapshot provenance, locked toolchain reproducibility, Windows packaging and production trust remain unestablished. An inspected mutable local file without an independently supplied trusted digest is an **unverified local snapshot**.

**Next move:** Consider a separately scoped Gate B native Python GUI smoke proposal through HQ. Gate A integration does **not** authorize a GUI, executable, gameplay, calibration, deck edits, full simulation suite, workflow activation, or archive writes. Preserve all baseline/prototype histories and PR #436 test receipts.
