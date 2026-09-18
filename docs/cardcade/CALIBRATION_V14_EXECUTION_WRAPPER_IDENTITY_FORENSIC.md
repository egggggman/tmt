# V14 execution-wrapper identity parameterization forensic

## Classification

`FAIL_CLOSED_STOP ? execution_wrapper_identity_parameterization_mismatch`

Run `CALIBRATION_V1_20260918T133024Z_b64ec548` is permanently stopped. It is non-resumable and non-reusable. Its preserved gameplay evidence is not valid calibration evidence, and no balance analysis occurred.

## Authenticated identities

- Authorized prospective execution-wrapper SHA-256: `24ECBFA3F3D4C210B15AF0FE0551FF385180F2B64DE474FC73F49C9DD3BFE9F3`
- Actual launched execution-wrapper SHA-256: `4068E62F5F7AA8FCC5E2F1F08D03780B79092BC8E8262F0A2A7465B6AA6A7848`
- Preserved stopped-run `FAIL_CLOSED_STOP.json` SHA-256: `3A100520DDB1C04904F672131B55CDD3100221C0B4BA81F4443026D2D4620E3A`

The actual launcher bytes match their sidecar exactly. The rendered prospective and actual wrappers are not byte-identical.

## Exact rendering difference

All committed release inputs were identical: the V14 packet, V13 launcher identity, V2 seed table identity, and frozen seed hash. The only differing explicit generation input was `output_rel`.

```text
Authorized prospective output_rel:
docs/cardcade/CALIBRATION_V1_FUTURE_RUN_REQUIRES_SEPARATE_HQ_AUTHORIZATION

Actual launched output_rel:
docs/cardcade/CALIBRATION_V1_20260918T133024Z_b64ec548
```

The byte comparison has exactly one differing generated source line:

```text
actual:      output_path = ROOT / 'docs/cardcade/CALIBRATION_V1_20260918T133024Z_b64ec548'
prospective: output_path = ROOT / 'docs/cardcade/CALIBRATION_V1_FUTURE_RUN_REQUIRES_SEPARATE_HQ_AUTHORIZATION'
```

That run-specific path is embedded in the generated wrapper and necessarily changes its SHA-256. Rendering was deterministic for each identical complete input set; the authorization authenticated a placeholder parameterization rather than the final run-specific parameterization.

## Final stopped boundary

- Members completed / attempted: 238 / 239
- Executions returned / attempted: 476 / 477
- Distinct games completed: 238
- Authenticated duplicate pairs: 238
- Observed duplicate mismatches: 0
- Unique schedule seeds touched: 120
- Active member at stop: `b0002-p29-canonical`

The launcher process tree was terminated with no target process remaining. The run directory, generated launcher and sidecar, heartbeat, logs, completed member evidence, and stop record are preserved unchanged.

## V15 remediation conclusion

No production generator, Protocol V1, runtime, seed, or gameplay change is indicated. The smallest remediation is corrected release/authentication sequencing:

1. Create the unique run identity without executing it.
2. Render the exact wrapper using that identity and its exact `output_rel`.
3. Hash and preserve that exact wrapper.
4. Obtain HQ authentication and execution authorization for that exact run ID and wrapper SHA.
5. Execute that unchanged authenticated wrapper only after the separate authorization.

Authentication must continue to include the run-specific `output_rel`; it must not be ignored, wildcarded, or replaced with a placeholder hash.
