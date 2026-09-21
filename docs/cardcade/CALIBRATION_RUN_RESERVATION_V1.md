# Calibration Protocol V1 run reservation

`scripts/calibration_run_reservation.py` is the repository-owned reservation entry point. It reserves an identity only; it does not render a wrapper, load the seed table, execute a game, or authorize calibration.

## Contract

- A run ID is `CALIBRATION_V1_<UTC-second>Z_<12 lowercase hex digits>`.
- The timestamp is an explicit UTC identity input. The suffix is the first 12 hex digits of SHA-256 over the canonical JSON identity containing the audited `HEAD`, accepted runtime, V16 baseline blob hash, Protocol V1 identity, and timestamp.
- The authoritative reservation is an atomically created directory at `docs/cardcade/<run_id>/`.
- The directory is sealed with `RESERVATION.json` and `RESERVATION.json.sha256`. It records `execution_authorized: false`, zero games, zero seeds, and `wrapper_generated: false`.
- The future wrapper path is exactly `docs/cardcade/<run_id>/launcher.py`; reservation does not create that file.
- Any existing target directory, malformed timestamp, unauthenticated V16 baseline, or authorizing baseline fails closed.
- A reservation is not execution authorization. HQ must independently authenticate the later run-specific wrapper bytes and separately authorize execution.

For a reviewed and merged change, reserve the real next identity with:

```text
python -m scripts.calibration_run_reservation --repository-root .
```

That command is intentionally not run by this infrastructure change.
