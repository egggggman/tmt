# DECKDAEMON 0.1 — Gate B native Windows GUI prototype

**Status:** Draft review candidate. No Windows GUI smoke or independent acceptance has been performed. Gate A was integrated at `2e2b43413953d43775793b7fefc5edbab5cea346`, with validation documentation integrated at `fd6b5dfce1fa1a3ce530f9c6016c28e23665ae3e`.

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

## Synthetic review (not yet validated)

Run only selected Gate A and Gate B tests from the exact candidate in an isolated Python 3.12 environment:

```powershell
python -m pytest -q -rs tests/test_deckdaemon_reader.py tests/test_deckdaemon_presentation.py
python -m ruff check src/deckdaemon_viewer tests/test_deckdaemon_reader.py tests/test_deckdaemon_presentation.py
python -m ruff format --check src/deckdaemon_viewer tests/test_deckdaemon_reader.py tests/test_deckdaemon_presentation.py
git diff --check HEAD~3 HEAD
```

Do not claim success until actual command output exists. No full simulator suite or games.

## Gate B Windows smoke acceptance checklist

Record exact SHA, Windows version, Python/Tk version, test root identifier, and tests/check exit codes.

1. Confirm no implicit directory scan: launching without `--snapshot-root` exits via argument validation. Verify no global "Open any file" action.
2. Launch with a bounded synthetic fixture root; observe title **INSPECTION ONLY — NO GAMEPLAY**, visible root and unverified warning.
3. Navigate all ten deck selections, including keyboard selection; confirm exact source and historical version labeling, no encoding/rendering errors.
4. Open Baseline 005; confirm historical classification and existing raw metrics only. Do not imply new calibration.
5. Missing file, corrupt manifest, oversized input, wrong path, and symlink/junction protections must visibly reject via Gate A; test cases only where fixtures and permissions support them, and report skips.
6. Verify window focus, scrolling, keyboard access, DPI scaling/resizing, clean close and no uncaught exception.
7. Observe file/directory write activity and imports as practicable; verify no engine/launcher code, subprocess, socket/network, archive, claims, decks, or workflow mutation. Desktop GUI libraries may perform OS-managed incidental operations; do not claim a general sandbox.
8. Preserve test fixture hashes before/after and inspect modified-file status. No deck edits or generated match outputs.

## Acceptance gate

**BLOCKED pending** exact-source selected tests, Windows native GUI smoke evidence, independent scope review and HQ decision. A GUI is not a production security boundary. Real NTFS reparse/ACL, hostile concurrent mutation, and immutable snapshot trust remain separate gates. Gate C packaging remains unauthorized. Preserve PR #434 engine defect and PR #435 architecture draft without modification.
