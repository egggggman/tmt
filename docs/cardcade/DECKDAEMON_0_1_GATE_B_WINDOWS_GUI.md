# DECKDAEMON 0.1 — Gate B native Windows GUI prototype

**Status:** Draft review candidate. Exact-source selected Windows checks and bounded owner-reported GUI smoke are recorded below. Independent review at `0f5eefdd6c8aefe9a358d9d5f4c3d9b29f59334d` returned **BLOCKED on documentation consistency only**; this documentation correction requires fresh review at its resulting source SHA. Gate B is not accepted or merged. Gate A was integrated at `2e2b43413953d43775793b7fefc5edbab5cea346`, with validation documentation integrated at `fd6b5dfce1fa1a3ce530f9c6016c28e23665ae3e`.

**Scope:** Source-only Python 3.12 Tkinter/ttk desktop viewer, inspection only. No packaging, EXE, installer, gameplay, diagnostic execution, archive writes, engine imports, deck editing, calibration or workflow activation.

## Launch (Windows development workstation, only after checkout of exact Gate B candidate)

The application is not a standalone executable. Run from a dedicated, clean worktree with Python 3.12 and `src` importable (for example `$env:PYTHONPATH = (Join-Path (Get-Location) "src")`), then:

```powershell
python -m deckdaemon_viewer.gui --snapshot-root C:\path\to\explicit\test\snapshot
```

The caller **must** specify the intended local fixture/snapshot root. This path is not discovered, enumerated or used to launch a game. The reader may reject missing files and unsafe paths. The window intentionally displays the selected root and always labels unpinned evidence **UNVERIFIED LOCAL SNAPSHOT**. It does not certify Standard legality, contemporary balance, or runtime engine correctness.

## Fixed views

- Ten fixed, preserved `PROTOTYPE_0.1.txt` deck choices. Selection delegates only to Gate A's `read_prototype_01` API and shows inert text, path, provenance and observed digest.
- **Historical Baseline 005** button. Delegates only to Gate A's `read_baseline_005` API. Raw manifest is rendered as inert text, with historical labeling; no new games or calculations.
- Invalid/absent/oversized/ill-formed inputs display `REJECTED — EVIDENCE NOT VERIFIED`. No fallback data, repair, import, or trust promotion. No diagnostic evidence browser without a separately audited fixture list.

## Selected Windows validation — recorded evidence

The owner ran the following bounded checks in the isolated Python 3.12 environment at exact GitHub head `0f5eefdd6c8aefe9a358d9d5f4c3d9b29f59334d`. The first candidate `f2dd16a1747bee850b7f4c8cb0b278841fe300d1` passed the tests but **failed** Ruff lint/format; the corrected candidate below passed all selected checks. Earlier failures remain preserved in PR #438's discussion.

Commands for the recorded corrected candidate:

```powershell
python -m pytest -q -rs tests/test_deckdaemon_reader.py tests/test_deckdaemon_presentation.py
python -m ruff check src/deckdaemon_viewer tests/test_deckdaemon_reader.py tests/test_deckdaemon_presentation.py
python -m ruff format --check src/deckdaemon_viewer tests/test_deckdaemon_reader.py tests/test_deckdaemon_presentation.py
git diff --check HEAD~7 HEAD
```

**Actual Windows receipt at `0f5eefdd`:** pytest **25 passed, 1 skipped** (actual symlink creation not permitted on host); Ruff lint **PASS** (`All checks passed!`); Ruff format **PASS** (`6 files already formatted`); `git diff --check HEAD~7 HEAD` **PASS**; detached worktree clean. These are **selected** checks, not a full Cardcade simulator suite, not a new game, and not an independent locked-environment reproduction. A later documentation-only SHA is not the exact SHA of these Windows execution results.

## Gate B Windows GUI smoke — reported outcomes and remaining limitations

Owner's Windows screenshot at the same tested source SHA showed the native Tkinter viewer open with an explicit local root, all ten allowed selectors, `casey_jones` preserved Prototype 0.1 displayed, observed digest and **UNVERIFIED LOCAL SNAPSHOT**. Copied application output showed the expected historical Baseline 005 manifest (including its path, `OBL-BASELINE-005` identity and historical provenance), without claiming new calibration. Owner additionally reported that all deck controls, resize and normal close worked, and later opened/verified/closed a separate empty `%TEMP%` root rejection test (missing approved deck/baseline sources). Those interaction results are **owner-reported**, not instrumented automated UI logs. The actual host OS build, Tk/DPI details, and immutable evidence-file before/after hashes were not captured in the PR receipts.

Retain the full scope checklist below, distinguishing covered items from follow-up evidence not yet established:

1. Confirm no implicit directory scan: launching without `--snapshot-root` exits via argument validation. Verify no global "Open any file" action.
2. Launch with a bounded synthetic fixture root; observe title **INSPECTION ONLY — NO GAMEPLAY**, visible root and unverified warning.
3. Navigate all ten deck selections, including keyboard selection; confirm exact source and historical version labeling, no encoding/rendering errors.
4. Open Baseline 005; confirm historical classification and existing raw metrics only. Do not imply new calibration.
5. Missing file, corrupt manifest, oversized input, wrong path, and symlink/junction protections must visibly reject via Gate A; test cases only where fixtures and permissions support them, and report skips.
6. Verify window focus, scrolling, keyboard access, DPI scaling/resizing, clean close and no uncaught exception.
7. Observe file/directory write activity and imports as practicable; verify no engine/launcher code, subprocess, socket/network, archive, claims, decks, or workflow mutation. Desktop GUI libraries may perform OS-managed incidental operations; do not claim a general sandbox.
8. Preserve test fixture hashes before/after and inspect modified-file status. No deck edits or generated match outputs.

## Acceptance gate

**BLOCKED pending fresh independent review of the resulting documentation-only head and HQ acceptance decision.** The earlier independent technical review of `0f5eefdd6c8aefe9a358d9d5f4c3d9b29f59334d` at [PR #438 review](https://github.com/egggggman/tmt/pull/438#pullrequestreview-6083174959) found the source-only inspection boundary suitable but **BLOCKED** acceptance because this document previously claimed that already-recorded Windows checks had not been run and incorrectly listed `HEAD~3 HEAD`. This change reconciles the document; it does not alter executable code or rerun Windows checks. A fresh reviewer must verify the new exact head and documentation consistency before HQ decides whether to accept Gate B.

**Known limits:** the real symlink test was skipped; three Gate A junction-classification tests use mocks and do not demonstrate real NTFS reparse/junction/ACL protection. Hostile concurrent mutation, immutable/version-pinned source provenance, independent trusted digest provisioning, fully instrumented UI accessibility/DPI/side-effect checks, and locked toolchain reproduction remain unestablished. The GUI is **not** a production security boundary. Gate C packaging, gameplay, calibration, engine changes, deck edits, archive writes and merge remain unauthorized. Preserve PR #434 engine defect and PR #435 architecture draft without modification.
