# Baseline 005 Artifact Recovery Checkpoint 001

Status: **BLOCKED — exact historical recovery unavailable**

The two repaired-control artifacts recorded by the historical reports cannot be authenticated in the current repository. Their tracked Git blobs are the same bytes as the workspace copies, but both byte streams fail gzip validation. The recorded hashes are preserved unchanged; no simulation was regenerated and no historical file was overwritten.

| Control | Recorded SHA-256 | Current SHA-256 | Size | Gzip |
|---|---|---|---:|---|
| `OBL-BASELINE-005-REPAIRED-CONTROL-001` | `45c4cd…15d7` | `a9dda1…d253` | 786,444 | invalid compressed data |
| `OBL-BASELINE-005-REPAIRED-PILOT-CONTROL-001` | `f42348…96b8` | `8a5283…3809` | 786,444 | invalid compressed data |

## Investigation

- Git history contains one blob for each artifact (`6c1d125…` and `a471e14…`); neither matches its recorded SHA or decompresses.
- PR heads 351–356 were inspected. No alternate artifact bytes were found.
- The associated GitHub Actions test run (run `39098482115`) completed successfully but produced no workflow artifacts.
- PR comments/attachments exposed no raw artifact copies.
- The surviving reports retain schedule, runtime, failure records, and completed-cell claims, but reports are not independent byte authentication.

Corrupted bytes are preserved separately under `forensics/BASELINE_005_ARTIFACT_RECOVERY_001/`. They must not be used as calibration evidence.

## Evidence disposition

The historical failure records and report metadata remain useful for narrative and failure-signature review. The raw compressed telemetry and reproducibility-critical control artifacts are not independently verifiable. Exact recovery is unresolved; these files must not be regenerated and relabeled as historical originals.

Recommendation: **BLOCKED for calibration preflight.** HQ must separately decide whether a narrowly documented provenance exception or superseding evidence package is acceptable. No calibration run, deck change, hash replacement, merge, or promotion was performed.
