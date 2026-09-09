# Action #31 merged-baseline Smoke remeasurement

Exact evidence base: `f00233033b305fd182a32105396622a79dd9c202`.
Comparison candidate: `494872c5849616daaf126885a864483662e9be21`.

One unchanged Smoke invocation completed the frozen 180-game / 360-execution matrix. The current frozen manifest matches exactly; only execution_commit and manifest_digest differ from the accepted candidate manifest. No production, deck, matrix, or prior artifact was changed.

Observed: **490 EXECUTED / 118 REACHED-UNSUPPORTED / 1,530 PRESENT-UNREACHED**. Mechanical labels: **108 coverage-complete / 72 coverage-limited / 0 invalid**. Stops, invariant violations, and duplicate mismatches: **0 / 0 / 0**.

All 180 reports reconstruct with validate_smoke_result, including snapshot digests, authoritative transaction evidence, classifications, and aggregate labels. All 2,828 fresh execution references independently authenticate. The 21 mill-three transactions across 17 games reconstruct; no reached-unsupported mill-three occurrence remains.

Every game has identical duplicate snapshots, authenticated references, and occurrence classifications to the accepted candidate. There are no new continuity losses. The historical Action #30 witness audit and its 2,829 banked references remain preserved in POST_ACTION_31_CONTINUITY.json; that historical reference count is distinct from the 2,828 fresh runtime references. The candidate?s four explained runtime occurrence reductions are unchanged; counts were not forced.

## Remaining reached-unsupported clusters

| Fragment / card | Distinct games | Occurrences |
| --- | ---: | ---: |
| Bebop, Warthog Warrior, Raphael, Most Attitude, Splinter, Hamato Yoshi: Menace (This creature can't be blocked except by two or more creatures.) | 24 | 24 |
| Tunnel Rats: {4}{B}: Return this card from your graveyard to the battlefield tapped. | 16 | 19 |
| Leonardo, Sewer Samurai: During your turn, you may cast creature spells with power or toughness 1 or less from your graveyard. If you cast a spell this way, that creature enters with a finality counter on it. (If a creature with a finality counter on it would die, exile it instead.) | 13 | 15 |
| Paramecia Coloniex: When this creature dies, you may exile it. When you do, put target creature card from your graveyard on top of your library. | 12 | 13 |
| Frog Butler: {2}: This creature gains reach until end of turn. | 8 | 8 |
| Frog Butler: {T}: Add one mana of any color. | 8 | 8 |
| Krang, Master Mind: When Krang enters, if you have fewer than four cards in hand, draw cards equal to the difference. | 6 | 7 |
| Raphael, Most Attitude: Alliance — Whenever another creature you control enters, you may exile the top card of your library. | 6 | 6 |
| Raphael, Most Attitude: Whenever Raphael attacks, until end of turn, you may play a card exiled with Raphael. | 6 | 6 |
| Zoo Escapees: When this creature leaves the battlefield, create a Mutagen token. (It's an artifact with "{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature. Activate only as a sorcery.") | 5 | 5 |
| Casey Jones, Vigilante: When Casey Jones enters, draw three cards. At the beginning of your next upkeep, discard three cards at random. | 3 | 3 |
| Ooze Spill: Counter target spell. Create a Mutagen token. (It's an artifact with "{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature. Activate only as a sorcery.") | 2 | 3 |
| Michelangelo, Weirdness to 11: If one or more +1/+1 counters would be put on a creature you control, that many plus one +1/+1 counters are put on it instead. | 1 | 1 |

Clusters overlap games; game counts must not be summed. Zoo Escapees and Vigilante retain the accepted candidate?s conservative terminal-pending classifications; this inventory does not turn those obligations into newly missing implementations. Full identity-level occurrence rows and exact fragments are preserved in the inventory and ranking JSON.

## Evidence packet

- POST_ACTION_31_MERGED_SMOKE01_RESULTS.json.gz: complete fresh raw result, both duplicate snapshots, authoritative event/transaction chains; compressed and decompressed SHA-256 sidecars.
- POST_ACTION_31_MERGED_RECONSTRUCTION.json: reconstruction summary, all per-game continuity checks, and mill execution references into the full result.
- POST_ACTION_31_MERGED_SMOKE_INVENTORY.json: every observed semantic occurrence and identity lineage join.
- POST_ACTION_31_MERGED_UNSUPPORTED_RANKING.json: residual clusters ordered by affected distinct games and occurrence counts.
- This report and every derived JSON have SHA-256 sidecars. Compression round-trip and staged sidecar bytes are verified before commit.

No further simulations or implementation work were performed. Action #32 and Prototype 0.3 remain NOT AUTHORIZED; calibration remains BLOCKED. HQ determines the next gate.
