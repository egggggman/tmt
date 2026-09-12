# Canonical execution proof; full scoring remains blocked

Pre-run authority: `9fb8574`. Failed execution: `32e692b`. Specification V3: `c18a8fc`. Generic-state attempt `b353537` is also not scoring evidence. All prior commits and scoring artifacts are preserved.

The runner now reads canonical inputs from the pre-run Git tree, verifies current implementation blobs and sealed source hashes, checks the original observation/branches/oracle digest, reconstructs typed immutable inputs with an exact serialization round trip, invokes both actual choose_attack hooks, and compares their returned actions to the sealed acceptable set.

The tiny proof executed V3-P1-002 twice, once per Pilot. AcceptancePilot returned attacker object-000135 (acceptable); PassingPilot returned an empty attacker set (unacceptable). The JSON records complete inputs, acceptable actions and actual returned actions. These are two proof calls, not part of a completed 384-call run.

The source candidate files do preserve canonical observations and oracles, correcting the overly broad missing-data conclusion in ISSUE_106_RECONSTRUCTION_STOP. However, seal_v3_phase1_packet.py and seal_v3_phase2_deterministic.py record privacy eligibility and paired counts without constructing authoritative hidden-state pairs. Repeating canonical observations cannot demonstrate the requested paired-state execution. The runner therefore rejects full execution before any calls. Recovering the original pre-run paired-state inputs or an authoritative pre-run reconstruction recipe is required; none has been substituted or newly designed.

Validation: proof completed; deserialized inputs round-trip exactly; sealed replay digest matches; full-run command exits 2 before execution; runner Ruff checks pass. Fixtures, oracles, Pilot code and seal remain unchanged. No suite PASS/FAIL is claimed. Filtering remains INCONCLUSIVE and calibration remains BLOCKED.
