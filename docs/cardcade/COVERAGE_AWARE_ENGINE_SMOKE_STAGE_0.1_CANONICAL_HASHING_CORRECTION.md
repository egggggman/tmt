# Coverage-Aware Engine Smoke Stage 0.1 Canonical Hashing Correction

Status: **EVIDENCE-CONTRACT CORRECTION — EXECUTION REMAINS BLOCKED**

## Reason

PR #53 Linux CI correctly rejected the original Smoke 0.1 frozen-input contract. The original
runner hashed raw Windows working-tree bytes. Git checked the same tracked text out with LF on
Linux and CRLF on Windows, so semantically identical Git content produced different SHA-256 values.

This was an evidence portability defect, not a gameplay defect. Runner Audit #2 remains valid for
candidate `467b470962354ee82ef412221546a69eddacc410` under its then-defined Windows-byte contract. The
runner, Readiness Audit #1, and both runner acceptance reports remain preserved unchanged.

## Versioned hashing contract

Smoke 0.1 now records `smoke-frozen-input-hashing-v2` and identifies the scheme for every artifact.

### Tracked text — `git-clean-blob-oid-sha1-v1`

Tracked text identity is the Git blob object ID obtained by applying Git clean-filter semantics to
the current working file with `core.autocrlf=true` explicitly set for the identity operation. This
produces canonical LF Git content regardless of checkout representation while still detecting
working-tree textual changes.

The runner first requires `git ls-files --error-unmatch` for the declared repository path. Missing,
untracked, or wrong paths fail closed. The SHA-1 algorithm here is the repository's Git object
identity algorithm, including Git's blob framing; it is not a raw-file checksum claim.

### Binary or non-Git input — `raw-bytes-sha256-v1`

Binary or explicitly non-Git inputs retain exact raw-byte SHA-256 identity. No newline or encoding
normalization is applied. Smoke 0.1 currently freezes tracked repository text through the first
scheme; the second scheme is implemented and adversarially tested for future binary/runtime inputs.

The authoritative card snapshot additionally retains its existing internal raw snapshot SHA-256
validation through `load_card_data()` and the imported snapshot manifest.

## Deliberately regenerated tracked identities

| Artifact | Git clean-blob OID |
|---|---|
| `cardcade/roster-0.2.json` | `bad8104fcef826ef5cfd7fec1bdfe921cdd4c306` |
| `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json` | `761376d5f932fe6cfbbe140d5c76793c9dd5b169` |
| `cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json` | `768d25bbed8392a2f92b7b7f06ae8a34e2602423` |
| `decks/leonardo/PROTOTYPE_0.1.txt` | `99e082b2cbcc2446159b4a01c3ca9f89d59a2a3e` |
| `decks/raphael/PROTOTYPE_0.1.txt` | `964ceb42e13fd0d60fd43346c0b2415bbbe19c30` |
| `decks/donatello/PROTOTYPE_0.2.txt` | `ec05b95268ba72cd6f0d6b64d9a5dfa1ecd81317` |
| `decks/michelangelo/PROTOTYPE_0.1.txt` | `70e5104e109405b2ad0a3bdd93e16c5bf75f39e9` |
| `decks/splinter/PROTOTYPE_0.1.txt` | `354e56cf9dca8e84e8824afe20cd6239d076fd37` |
| `decks/april_oneil/PROTOTYPE_0.1.txt` | `aa02bd4cd5ce78b182d78d2f4d1b819693e2e033` |
| `decks/casey_jones/PROTOTYPE_0.1.txt` | `ebcddef99784da507055ff1bac84134e5d355ac6` |
| `decks/shredder/PROTOTYPE_0.1.txt` | `306fd267482b72f188c69222d57fcc547d654091` |
| `decks/krang/PROTOTYPE_0.2.txt` | `ecdffa18463076503f5d338687041f42a3a599d9` |
| `decks/bebop_rocksteady/PROTOTYPE_0.1.txt` | `d12cb8dca2412eb5267496ef3530f9b95e3032a1` |
| `src/tmnt_design_studio/engine07.py` | `6e09f224fc75b8afe6cb6945a403ab43ab64f70e` |
| `src/tmnt_design_studio/card_interpreter07.py` | `2c316320c927d137dbfb9c91bf33291972573755` |
| `src/tmnt_design_studio/pilot07.py` | `3eb8bfd8654294e1ef7e6137882651801bf1e2d6` |
| `src/tmnt_design_studio/stage002.py` | `b384f4e06021b902431d8224ac0ae40664b77a6d` |
| `src/tmnt_design_studio/conformance07.py` | `f2fa5e1b3433a749b7b6e1a862a242f4940af1e6` |

These identities were produced from the current accepted repository content. They replace the
working-tree-byte hashes only for the corrected Smoke runner contract; historical reports retain
their original values as evidence of the rejected portability assumption.

## Required validation and gate

Tests must prove:

- LF and CRLF representations of identical tracked text have one identity;
- a textual change changes that identity;
- any binary byte change changes raw SHA-256 identity;
- untracked, missing, and wrong paths fail closed;
- the complete frozen plan remains 45 pairings / 180 games / 360 executions;
- all Smoke Runner Audit #2 balance, label, duplicate, conformance, and atomic-failure invariants
  remain passing.

This correction requires an independent Canonical Frozen-Input Hashing Acceptance Audit #1,
Windows validation, exact-SHA Linux CI PASS, runner acceptance-invariant confirmation, and
Readiness Audit #2 before any Smoke 0.1 execution.
