# Issue #289 — granted Sneak legal-action correction

This checkpoint is stacked on draft PR #326's consolidated family triage. The
request's #314 state (seven critical, 61 important) is historical: the accepted
#315–#325 chain already closed those critical rows. The current Baseline 005
deck reference, original 172-row ledger, older overlays and game evidence
remain frozen.

## Reproduced defect and generic correction

The #326 [machine diagnostic](ISSUE_289_FAMILY_TRIAGE.json) recorded a
Splinter-first versus Shredder game, seed 326, in which Ninja Teen was offered
Sneak from **hand** using its level-three text. That text grants Sneak only to
creature cards in the controller's graveyard. Ninja Teen itself is an
Enchantment — Class. The pilot paid `{3}{B}` and returned an unblocked
attacker; after priority passes, a noncreature permanent was marked tapped
and attacking and the invariant raised
`noncreature Sneak evidence has a battlefield result`. Both predecessor
attempts produced the same failure snapshot digest
`ce34b19eddc71d3b8ffec271be328e7e5871db2213ef68c7c0b320e23f7e3490`.

The interpreter now models **granted** and **direct printed** Sneak as
different executable instruction origins. A Class grant stays available to
eligible graveyard creature recipients, but it is not enumerated as a printed
Sneak action on the Class card. The normal legal-action, payment, priority,
zone and source-provenance paths are retained. No card or deck name drives
execution. The resolution invariant was not weakened.

The two focused regression tests failed on the predecessor. They now verify
the origin distinction; that a renamed Class in hand is not offered or
payable via Sneak and a forged action is rejected transactionally; that
grant-source cards in exile and graveyard are not eligible; and that the
actual graveyard creature still casts, resolves tapped and attacking, and
retains its permission provenance after the Class departs. The whole
state/event trace replays identically. Existing tests exercise direct printed
creature Sneak, noncreature spell Sneak, blocked attackers, cost shortage,
stale objects and alternative printed/granted costs.

## Bounded frozen-deck verification

The [authenticated diagnostic](ISSUE_289_SNEAK_LEGALITY_SMOKE.json) checks all
ten frozen deck hashes, Baseline 005 manifest SHA-256
`c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`,
original ledger SHA-256
`56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`,
and the exact predecessor overlay and failing trace. It covers
Splinter–Shredder at seeds 323 and 326, and Splinter–Michelangelo at seed
323, both starting orientations. **Six of six games completed; six of six
deterministic replays matched; ten legitimate graveyard Sneak casts and zero
wrong-zone/noncreature grant casts were recorded; zero runtime errors.** The
exact former failing GameSpec now completes through turn 35 with digest
`cd2e4e8370dcd23466def935b6742855f78561aa1c966e36af63badcc5596e76`.
These games diagnose execution only; their game outcomes are not balance
evidence.

The new semantic runtime is
`2e140950578ddbfabf9fdb931a7edde800d9775c56c1e54bb438e09317c3ccf6`.
The earlier runtime `a95807a7bf0a8a87b78155c425fe275da8b223190941e167d859ecf9f90902d9`
and its historical evidence remain intact. The concise row delta is empty:
**zero critical, 35 important, 31 calibration blockers and four unbounded**
remain. Repairing a legal action did not close an unsupported Oracle clause.

Focused Sneak suites: **29 passed**. Full local regression: **1,948 passed,
10 skipped**. Baseline 005 structural validation and repository Ruff
check/format passed. Final-head GitHub CI is recorded on the draft PR after
publication.

**Checkpoint acceptance:** pending final-head CI. **Baseline 005 calibration:
BLOCKED** by 31 important blockers and four unbounded residuals. The next
gap-closing recommendation remains the shared Robot-token trigger batch from
#326, subject to HQ's independent review. No deck revision, calibration
control, merge or promotion occurred.
