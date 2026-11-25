# DECKDAEMON 0.1 — Gate A reader candidate

**Scope:** HQ authorized read-only data contract only, based on draft architecture PR #435. This is an **unmerged synthetic prototype**, not a GUI, Windows executable, or gameplay launcher.

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
- Reject symlink root/path components and out-of-root resolution; require regular file.
- Bounded read: deck <= 1 MiB, manifest <= 256 KiB, strict UTF-8.
- Reject missing/inaccessible files, invalid or mismatched SHA-256, malformed JSON, duplicate JSON keys, NaN, incorrect schema/identity/roster, invalid win rates or matchup cell coverage.
- Explicit historical result labeling; never certify Standard legality, current balance, new gameplay, or trust in mutable files.
- OS-level sandboxing and hostile concurrent mutation are **not established** by this reader. Production installation must use a version-pinned immutable snapshot, with Windows reparse/junction/ACL checks as a later gate.

## Synthetic evidence and remaining validation

A local Python 3.13.5 / pytest 9.0.2 **analogous candidate** ran **17 passed** in 0.08 seconds on temporary synthetic fixtures, and `compileall` passed. Because GitHub files were published separately, **this does NOT count as exact-GitHub-head Windows acceptance**. Ruff wasn't installed in the isolated local container and has **not** been claimed as passing. A fresh Windows exact-SHA `uv` test, Ruff lint and format, and `git diff --check` are mandatory before Gate A acceptance. A full suite, real games, workflow activation, GUI and EXE are not authorized.

**Next move:** validate the exact PR head in a fresh isolated Windows worktree, inspect Windows-specific path behavior, and review any test/format failures. Maintain draft/unmerged status pending HQ review. No baseline/prototype edits or historical evidence overwrites.
