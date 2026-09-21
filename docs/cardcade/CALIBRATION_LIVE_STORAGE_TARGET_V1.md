# Calibration V1 live storage target contract

The qualified live calibration volume is exactly `G:\`. The governed live evidence root is exactly:

```text
G:\cardcade\calibration-runs
```

For a banked reservation, the production output directory is deterministically:

```text
<live evidence root>\<run_id>
```

Therefore the reserved V17 run resolves to:

```text
G:\cardcade\calibration-runs\CALIBRATION_V1_20260921T050741Z_98aa7d180751
```

Resolution authenticates the repository reservation sidecar, requires the supplied run ID to match the reservation, requires an unused non-authorizing reservation, validates the target is on G:, and fails closed if the target already exists. Resolution creates no directory and writes no evidence.

The run directory must be absent before authorized execution. Reservation, target resolution, wrapper generation, exact-byte authentication, and execution authorization are separate gates. Changing the output path changes authenticated wrapper semantics and requires fresh authentication.

The wrapper renderer represents an absolute Windows output path explicitly as `Path(<absolute path>)`; it does not rely on joining an external path to the repository `ROOT`.
