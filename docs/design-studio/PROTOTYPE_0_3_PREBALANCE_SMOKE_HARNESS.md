# Prototype 0.3 Pre-Balance Smoke Harness

The historical `src/tmnt_design_studio/smoke01.py` remains preserved for its frozen Prototype
0.1/0.2, 180-game contract. It is not modified or overloaded for the authorized Prototype 0.3
smoke.

The dedicated `tools/run_prototype_0_3_prebalance_smoke.py` harness executes only the matrix in
`PROTOTYPE_0_3_PREBALANCE_SMOKE_PLAN.md`:

- the four authenticated Prototype 0.3 deck files;
- six named unordered matchups;
- seeds 3000 through 3039 for every matchup;
- even seeds start the alphabetically earlier deck and odd seeds start the other deck;
- 40 games per matchup, 20 per starting position, 240 games total.

The harness verifies the expected repository revision, a clean worktree, exact deck SHA-256
identities, 60-card/recognized/Standard-valid decks, and the complete schedule before invoking
the existing accepted single-game runtime. Any preflight failure starts zero games. Runtime
failures are recorded as smoke failures; no replacement or adaptive games are permitted.

The harness is execution plumbing only. It does not authorize deck changes, engine or Pilot
changes, a new calibration, iterative tuning, or any change to Calibration V1 evidence. The smoke
is diagnostic and its results are not calibrated balance estimates.
