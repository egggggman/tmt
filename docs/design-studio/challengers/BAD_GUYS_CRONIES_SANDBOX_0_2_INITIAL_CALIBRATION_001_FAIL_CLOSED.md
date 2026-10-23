# Bad Guys 0.2 Initial Calibration — Fail-Closed Checkpoint

**Status: CALIBRATION BLOCKED**

The authorized 900-game control was not accepted. The persisted execution checkpoint contains 1,211 game rows and duplicate matchup blocks (200 rows in several cells), while the authorized schedule is exactly 900 games: 100 per nine matchups, split 50/50 by starting player. This is an evidence-integrity failure, so no matchup or balance result is admissible.

Runtime: `c087f84bab4916b516ec6745f5a8e9f2a2d33f9117856bf959da4eb9a7be8e54`  
Candidate SHA-256: `cacc77648a4d1659b8ae640d95ac2672694e6951553980246e6d001e5152bfb4`  
Baseline 005 B&R SHA-256: `aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed`  
Snapshot SHA-256: `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`  
Overlay: `OBL-BASELINE-005-PROVENANCE-OVERLAY-001`

The raw checkpoint was preserved unchanged for forensics under SHA-256 `c74ad8c537b73480bc25e2495371bc18df8b3567a230a734cde6f1bb831c30f4`. No retry, schedule correction, deck change, simulator change, or balance interpretation was performed. A new calibration control is not authorized by this checkpoint.

