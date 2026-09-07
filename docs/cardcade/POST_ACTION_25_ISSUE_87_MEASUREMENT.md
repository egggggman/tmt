# Issue #87: post-Action #25 bounded Stage #002 evidence

Baseline: `dbfa85fc101bb14467f00d9935dc4b9f7c2181e1` (authoritative Action #25 merge).
The local worktree was clean and HEAD was checked immediately before execution.
Command: `.venv/Scripts/python.exe scripts/run_acceptance_stage_002.py --execute --output docs/cardcade/POST_ACTION_25_ISSUE_87_STAGE_002_RESULTS.json`.

## Execution and integrity

The existing accepted runner completed exactly 16 distinct games / 32 executions: Donatello / Krang (7201, 7202), Michelangelo / Bebop & Rocksteady (7211, 7212), Splinter / Shredder (7221, 7222), and April / Casey (7231, 7232), both orientations and two executions per game. No additional games were run for analysis.

All duplicate executions were byte-equivalent. Invariant violations: 0. Runner stops: 0. Serialized evidence validation passed. The static manifest matched `build_stage_manifest` exactly. All 16 report bodies reconstructed exactly through `reconcile_snapshot` from the serialized authoritative evidence, presence, semantic occurrences, execution references, contexts and witnesses. Authenticated EXECUTED claims, report digests and aggregate digest passed the existing validator and reconstruction checks.

The fresh result JSON is serialized with LF line endings. Its raw SHA-256 is `b64c23e443db3a52456fe0c172857d0b289905b0b39c5805ea00fa8ebd46fc55`. The result, inventory and ranking each have a verified raw-byte SHA-256 sidecar. The narrowly scoped `.gitattributes` entry keeps only these new Issue #87 files LF-stable across Git checkouts.

Historical artifact integrity observation: all three comparison sidecars match their existing Windows checkout bytes and their serialized evidence validators pass. Their Git blob bytes use LF and do not match those historical CRLF-byte sidecars. No historical file or sidecar was changed. This is an existing checksum portability issue, not a fresh evidence-validation failure or a simulator continuity failure; reviewers validating the historical sidecars from Git blobs must account for their original CRLF serialization. Fresh Issue #87 sidecars are verified against both working and staged Git bytes.

## Inventory and continuity

Counts are semantic occurrence rows across the 16 distinct games, with duplicates counted once. Physical card/token presence is a separate inventory: 72 EXECUTED, 8 REACHED / UNSUPPORTED, 3645 PRESENT / UNREACHED presence rows; these are not added to semantic-occurrence counts.

| Measurement | EXECUTED | REACHED / UNSUPPORTED | PRESENT / UNREACHED |
| --- | ---: | ---: | ---: |
| Original post-Action #24 | 19 | 11 | 133 |
| Post-Action #24 with Action #21 continuity correction | 21 | 9 | 133 |
| Fresh Issue #87 post-Action #25 | 22 | 8 | 133 |

Shredder's exact deathtouch fragment clears from REACHED / UNSUPPORTED to EXECUTED in `splinter-shredder:reversed:7222` (1 occurrence). Action #21 Donatello's artifact-entry self-counter remains EXECUTED in `donatello-krang:canonical:7201` and `donatello-krang:reversed:7202` (2 occurrences). There are no remaining REACHED / UNSUPPORTED occurrences for either fragment.

No previously EXECUTED game/semantic occurrence count decreases in comparisons with the original post-Action #24, corrected Action #21 continuity, or candidate-era post-Action #25 artifacts. The fresh aggregate is identical to the candidate-era post-Action #25 aggregate; it was independently rerun at the merged baseline, not copied. This frozen matrix therefore does not distinguish the no-target correction; its focused regression tests supplied that coverage in PR #86.

No semantic continuity anomaly or foundational simulator blocker was observed within this bounded matrix. This is not a claim about unreached semantics or general simulator completeness. Existing opportunity-witness classification fields are retained as recorded by the runner; final classifications come from reconstructed reports, which prioritize authenticated execution references.

## Remaining unsupported ranking

Ranking uses reached-unsupported occurrence count, then distinct game count, then matchup count, descending, with alphabetical ties. It measures observed evidence leverage only.

| Rank | Card | Occurrences | Games | Matchups |
| --- | --- | ---: | ---: | ---: |
| 1 | Casey Jones, Jury-Rig Justiciar | 3 | 3 | 1 |
| 2 | Casey Jones, Vigilante | 2 | 2 | 1 |
| 3 | Courier of Comestibles | 1 | 1 | 1 |
| 4 | Stockman, Mad Fly-entist | 1 | 1 | 1 |
| 5 | Zoo Escapees | 1 | 1 | 1 |

The exact Oracle fragments, limitations, game/object/occurrence identifiers, opportunity witnesses and authenticated execution references are preserved in `POST_ACTION_25_ISSUE_87_INVENTORY.json` and `POST_ACTION_25_ISSUE_87_UNSUPPORTED_RANKING.json`. All three semantic classifications have complete occurrence inventories. Full presence and underlying authoritative events remain in `POST_ACTION_25_ISSUE_87_STAGE_002_RESULTS.json`.

## Handoff

Evidence only for Issue #87. Prior measurements, engine, interpreter, runner, decks and Pilot are unchanged. HQ must independently interpret the inventory and choose any next step. Action #26 remains NOT AUTHORIZED. This evidence makes no balance or calibration claim.
