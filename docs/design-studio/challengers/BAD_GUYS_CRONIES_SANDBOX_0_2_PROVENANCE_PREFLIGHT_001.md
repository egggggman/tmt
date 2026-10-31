# Bad Guys 0.2 — Baseline 005 Provenance Preflight 001

Status: **PROVENANCE PREFLIGHT READY — REQUEST HQ SMOKE REAUTHORIZATION**  
Gameplay simulations: **NOT RUN**  
Semantic runtime: `c087f84bab4916b516ec6745f5a8e9f2a2d33f9117856bf959da4eb9a7be8e54`

## Authentication

The ten Baseline 005 source records authenticate under the forward-only overlay `OBL-BASELINE-005-PROVENANCE-OVERLAY-001`:

| Deck | Method |
|---|---|
| Leonardo | raw bytes |
| Raphael | raw bytes |
| Donatello | raw bytes |
| Michelangelo | authorized CRLF equivalence |
| Splinter | authorized CRLF equivalence |
| Shredder | raw bytes |
| Krang | raw bytes |
| Bebop & Rocksteady | raw bytes |
| April O'Neil | raw bytes |
| Casey Jones | raw bytes |

For Michelangelo and Splinter, the overlay records historical manifest SHA-256, current LF SHA-256, CRLF-equivalent SHA-256, canonical normalized-content SHA-256, serialization convention, source path, Git commit, and Git blob identity. The validator accepts the CRLF form only because the overlay explicitly authenticates that convention; it still requires canonical content, exact deck rows, safe paths, and the expected Git object.

The Bad Guys candidate authenticates as:

`cacc77648a4d1659b8ae640d95ac2672694e6951553980246e6d001e5152bfb4`

The pinned Scryfall snapshot authenticates as:

`56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`

The original Baseline 005 manifest is unchanged. Smoke Attempt 001 remains excluded and is not reclassified. Baseline 005, R9-B, historical simulation evidence, and gameplay semantics are unchanged.

## Validator safeguards

Deterministic tests cover:

- successful authentication of all ten decks, including the two authorized LF/CRLF cases;
- modified card content;
- wrong or missing paths;
- wrong Git identity;
- incorrect canonical, LF, CRLF, or historical hashes;
- unauthorized serialization declarations;
- invalid UTF-8, BOMs, bare carriage returns, malformed rows, and wrong deck counts.

Results: **4 focused provenance tests passed; full suite 1694 passed, 10 skipped; Ruff format/check passed; terminology and diff checks passed.**

No gameplay simulation or smoke run was executed.

Recommendation: **PROVENANCE PREFLIGHT READY — REQUEST HQ SMOKE REAUTHORIZATION**.
