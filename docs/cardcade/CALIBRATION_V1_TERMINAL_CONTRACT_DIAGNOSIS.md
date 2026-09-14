# Calibration V1 terminal-contract diagnosis and regression

## Finding

The preserved first member `b0000-p00-canonical` (seed `1000000`, canonical April O'Neil / Bebop & Rocksteady) legitimately ended on turn 19. The original raw result records winner `april_oneil`, authoritative winner index `0`, and the losing player's life `-5`, `lost: true`, and `player_lost` event with reason `life_zero_or_less`.

`Game.snapshot()` exposed `winner` and `turn` but neither `terminal` nor `turns_started`. Stage 002 returned that snapshot unchanged. The executor required `terminal` and therefore rejected a legitimate terminal result. Its unused turn fallback also referred to `turns`, although the actual field was `turn`.

This is the first proposed diagnosis (a legitimate terminal condition whose terminal flag was not exposed), together with an engine/executor schema mismatch. The saved game did not stop at a Stage 002 bound and did not end prematurely. The winner is forensic regression evidence only, not balance evidence. No draw was reported or reclassified; this change adds no draw rule.

## Minimal correction

- `Game.snapshot()` now serializes `terminal` directly from authoritative `Game.winner` and `turns_started` directly from authoritative `Game.turn`. Existing winner, player-loss, event, RNG and fingerprint evidence is retained.
- The executor requires boolean `terminal: true` and an integer `turns_started` matching `turn`, below 120. It no longer manufactures a count through the incorrect fallback.
- Boundary inspection also found the old Stage 002 loop could enter turn 120 from turn 119. It now raises before beginning that turn when no winner exists. An authoritative win on turn 119 is still accepted.

No deck, seed, Pilot, choice policy, or game outcome rule changed. The frozen failed attempt is preserved in [PR #136](https://github.com/egggggman/tmt/pull/136), head `23f3bdadf6495b9a79c69ce3020c8381c68e8e6e`. The fix PR is based on that evidence branch so its regression can authenticate against the original result.

## Required evidence

The focused regression executes only the exact failed member twice. It checks the accepted seed-table hash and first-row identity, authoritative winner index and losing-player state, loss event, and all 19 `turn_started` events. Removing the newly exposed contract fields and member identity gives exactly the saved original raw result, including events, RNG and state fingerprints.

Both canonical UTF-8 JSON executions are retained independently under `CALIBRATION_V1_TERMINAL_CONTRACT_REGRESSION/`, with SHA-256:

`26fb0106bdc6f482a08668d14c5a43ddab0e25bb42b78d33abef81dc31c95c6f`

`REGRESSION.json` records their byte equality and terminal evidence. `VALIDATION.json` binds the changed and exercised source files with canonical Git/LF source hashes. The raw evidence files and manifests have SHA-256 sidecars and Git attributes preserving exact bytes.

Additional regressions verify nonterminal opening state, authoritative wins for either seat, missing/false/nonboolean terminal rejection, missing/inconsistent/invalid turn-count rejection, turn-119 win acceptance, and prevention of every turn-120 event on the bounded nonterminal path. The existing strict runner boundary test remains passing.

Local validation: **20 focused tests passed; 1,416 full-suite tests passed, 1 skipped**. Repository-wide Ruff format and lint checks passed. GitHub CI results are reported on the PR head.

These are diagnostic test executions, including repetition by the full suite and CI, not a calibration restart or authenticated calibration observations. No new release seal or calibration execution is authorized by this packet. Independent HQ review is required before any new calibration authorization. No balance interpretation, deck changes, or Prototype 0.3 work was performed.