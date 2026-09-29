# Objective Balance Lab — Promotion History

## Initial state

No Objective Balance Lab candidate has yet been promoted into a new official combined baseline.

The current frozen environment is `OBL-BASELINE-000` at repository commit `4f2d69d87bf5a3cbb4d8d9a2508be3851eb2e836`. Its official deck lineage predates OBL and remains the preserved Prototype set recorded in [ENVIRONMENT_REGISTRY.md](ENVIRONMENT_REGISTRY.md).

Round 1 and Round 2 candidates remain experimental evidence. Accepted candidates are eligible for the next combined-matrix selection gate, not automatically promoted.

## Future append-only promotion records

Every future promotion must append a record containing:

- promotion ID;
- prior and new environment IDs;
- changed deck builds and exact hashes;
- candidate experiment IDs;
- combined-matrix evidence and SHA-256;
- environment metric delta;
- date and repository commit;
- explicit authorization.

No future record may rewrite or delete this initial state.
