# Bad Guys — Baseline 005 Provenance Recovery 001

Status: **ROOT CAUSE VERIFIED — EVIDENCE-ONLY CHECKPOINT**  
Date: 2026-10-23  
Scope: Michelangelo and Splinter Baseline 005 SHA-256 mismatches  
Gameplay simulations: **NOT RUN**

## Finding

The two mismatches are line-ending drift in inherited hash metadata, not deck-content drift. The published manifest hashes are exactly the SHA-256 values of the same files encoded with CRLF line endings. The checked-out Git files use LF. After LF/CRLF normalization, historical and current files are byte-for-byte equivalent and their parsed card lists are identical.

| Deck | Manifest SHA-256 | Current LF SHA-256 | Current bytes converted to CRLF | Result |
|---|---|---|---|---|
| Michelangelo | `f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9` | `a35dfd61a87ec5377d7eda930afc22449d86bb2385b6d5e59d40e23211fe514f` | `f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9` | exact match after CRLF conversion |
| Splinter | `74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a` | `a6c61786654f6d37c7b7ee779fdcb4252ee77d9d43a6e0160154831c204d8e42` | `74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a` | exact match after CRLF conversion |

The eight other frozen deck hashes match their LF checkout bytes; this is isolated to these two inherited records.

## Content and lineage verification

- Michelangelo has 14 quantity/name rows and Splinter has 13. Parsed rows match exactly between the current files and the historical Git source after newline normalization.
- The files at repository commit `df15e8bff151d07ea5018d8766bba3553eb7b200` match the current files after newline normalization.
- The same Git blobs are present at Baseline 005 promotion commit `479920496961d1fd98985a3743780a2f54effc8c0`; no source-file diff exists between the source commit, promotion commit, and current checkout.
- Git history shows the deck files were last content-authored by commit `ed3ec1e5c01a238c4028c3c61c8a9e1972631ca4` (“Build Cardcade through Engine 0.6 card-fact modeling (#15)”). No later deck-content commit changed either file.
- The Baseline 005 manifest was created at `479920496961d1fd98985a3743780a2f54effc8c0`, but the two expected values were inherited from earlier baseline/evidence metadata. The same values occur in Baselines 001–004 and earlier calibration evidence. Baseline 005 did not introduce a deck change.
- Git blob identities are stable: Michelangelo `70e5104e109405b2ad0a3bdd93e16c5bf75f39e9`; Splinter `354e56cf9dca8e84e8824afe20cd6239d076fd37`.

## Classification

`FORMAT_DRIFT_IN_INHERITED_MANIFEST_HASHING`

This is not a card-list change, not a deck-content change, and not a runtime semantic change. The historical values are valid hashes under the historical CRLF serialization convention, but are not directly comparable to LF-normalized Git checkout bytes. The previously published smoke preflight therefore failed closed correctly when it compared raw LF bytes to CRLF-derived manifest values.

## Safe correction proposed for HQ authorization

No historical file, manifest, deck, runtime, or simulation artifact should be rewritten in this checkpoint. The smallest safe forward-only correction is:

1. Preserve all original manifests and their recorded hashes unchanged.
2. Add a provenance overlay/validator record that explicitly stores the hash serialization (`LF` or `CRLF`) and the normalized-content identity for these two files.
3. Have future preflight compare canonical normalized content, while retaining the original manifest hash as `historical_manifest_sha256`; record both the current LF hash and the CRLF-compatible hash.
4. If raw historical CRLF bytes are recovered from the Windows worktree, preserve them as a separately identified forensic artifact. A reconstructed CRLF byte stream must be labeled reconstructed, not presented as the original raw artifact.

This correction should be authorized and reviewed separately. It must not retroactively authenticate the failed smoke attempt or convert its zero-game result into gameplay evidence.

## Evidence boundaries

- The original Baseline 005 manifest, deck files, historical reports, and R9-B evidence remain unchanged.
- The earlier controlled-smoke result remains excluded: `0/180` valid games because preflight failed; no gameplay result is being reclassified here.
- No gameplay simulation was run for this investigation.

Recommendation to HQ: **READY to authorize the forward-only provenance overlay/validator correction; BLOCKED for gameplay testing until that correction is independently accepted.**
