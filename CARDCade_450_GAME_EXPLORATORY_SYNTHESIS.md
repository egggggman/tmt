# Cardcade 450-Game Exploratory Synthesis

## Decision

**TARGETED FIDELITY CORRECTION REQUIRED** before relying on a 900-game calibration for affected card paths. The three exploratory batches completed: 50 + 100 + 300 = 450 games. This synthesis does not authorize more games, calibration promotion, deck changes, or source changes.

The latest 300-game telemetry repeatedly marks Casey Jones's enter-the-battlefield top-four artifact-selection ability as `reached_unsupported` (126 occurrences in 84 games). This is a strongly evidenced **execution-evidence gap** for a frequent card-selection effect that can change hand quality and future plays. It is not proof that the effect was resolved incorrectly or that it changed a winner. Before calibration, narrowly establish—using deterministic synthetic states and authenticated action evidence—that the effect's reveal/selection/library-bottoming path is correctly executed and recorded. If that evidence establishes a correct existing path, document the result; if it exposes a defect, correct only that path. No broad simulator audit is recommended.

## Batch evidence and coverage

All three reports record successful, sequential executions with no retries: 50/50, 100/100, and 300/300. They use the same frozen gameplay commit, `32a80228714674327aca62f8b86b70c4c4afc929`, and frozen Baseline 005 inputs.

Recorded plan identities: 50-game digest `0324db919911aee38c66475a406ef88c87a4ede9fd3bfea12c60b7a49959d005`; 100-game canonical digest `0f1b0b7a93ad23937614f5a677039b67dc321bd294f5402f078f2abf4a1450f4`; 300-game schedule digest `9206c4267027473218f18e9482abcccb8a64dcfc62a7511d39b711a427a2179c`. The reports pin the Baseline 005 manifest at `c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac` and card snapshot at `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`.

| Batch | Seeds / pairing coverage | Deck appearances and seats | Turns per game: mean / median / range | Fidelity evidence |
|---|---|---|---|---|
| 50 | Seeds 9001–9050; all 45 unordered pairings, with five additional pairings replayed in reversed orientation | 10 appearances per deck; orientation is recorded per game | 18.92 / 19 / 11–30 | 521 unsupported-semantics warning events; 150 opportunity witnesses; all 50 games had warnings. |
| 100 | Seeds 9101–9200; all 45 pairings represented, with varied repetition | April, Bebop & Rocksteady, Krang, Splinter: 23 games each; other decks: 18 each. Seat counts are 11/12 or 9/9 per deck. | 19.64 / 18.5 / 11–41 | 1,092 warning events; 346 witnesses; 99/100 games had warnings. |
| 300 | Seeds 10001–10300; all 45 pairings, 15 played six times and 30 played seven times | 60 games per deck, 30 in each seat | 19.85 / 18.5 / 11–53 | 3,025 structured semantic occurrences in 299 results: 2,456 present-unreached and 569 reached-unsupported. |

The warning units differ: the 50/100 reports count warning events, while the 300 review aggregates snapshot semantic occurrences. Do not sum them into one warning total. The weighted mean turn count over the three batches is approximately 19.70; a cumulative median is not reported. The earlier 50/100 batches have uneven matchup emphasis and should not be treated as a single balanced sample with the 300-game round robin.

All 300 schedule-assigned result files were present and their run IDs matched the approved schedule during the read-only 300-game warning review. The execution report records all 30 blocks as verified complete and preserves their block manifests, authorization-consumption records, logs, checkpoints, artifact inventories, and raw telemetry. No historical results were overwritten. Independent signed batch receipts were deferred by HQ and were not produced.

Earlier integrity records report 73,400 artifact-hash checks for the 50-game run and 146,795 for the 100-game run. The 300-game block verifiers rechecked 14,680 artifact hashes per block (440,400 rechecks total, not unique files). These are execution-report verification counts, not new hash calculations from this synthesis.

## Ten-deck scorecard

Wins and losses are shown separately by batch before the cumulative exploratory totals. Sample sizes differ in the first two batches; cumulative totals are not balance rankings.

| Deck | 50 games W–L (n=10) | 100 games W–L (n=18/23) | 300 games W–L (n=60) | Cumulative W–L (n) |
|---|---:|---:|---:|---:|
| April O'Neil | 1–9 | 9–14 (23) | 15–45 | 25–68 (93) |
| Bebop & Rocksteady | 8–2 | 13–10 (23) | 22–38 | 43–50 (93) |
| Casey Jones | 5–5 | 8–10 (18) | 37–23 | 50–38 (88) |
| Donatello | 5–5 | 6–12 (18) | 28–32 | 39–49 (88) |
| Krang | 2–8 | 10–13 (23) | 28–32 | 40–53 (93) |
| Leonardo | 5–5 | 8–10 (18) | 24–36 | 37–51 (88) |
| Michelangelo | 5–5 | 8–10 (18) | 18–42 | 31–57 (88) |
| Raphael | 4–6 | 11–7 (18) | 43–17 | 58–30 (88) |
| Shredder | 6–4 | 12–6 (18) | 45–15 | 63–25 (88) |
| Splinter | 9–1 | 15–8 (23) | 40–20 | 64–29 (93) |

Every deck won and lost games in the 300-game batch. The win variation identifies observations for Design Studio, not proof that any deck is unable to function or needs revision. The 300-game report does not yet aggregate per-deck action/resource metrics.

The combined 50/100 telemetry provides concrete strategy-execution signals for all ten decks: April's stun-target line; Bebop & Rocksteady's creature/activation lines; Casey's Jury-Rig, Rock Soldiers, and utility-artifact actions; Donatello's Does Machines and Sneak lines; Krang's refill; Leonardo's Sneak; Michelangelo's Food search; Raphael's Skateboard and utility-artifact actions; Shredder's Deathtouch-grant target; and Splinter's Sneak and Ninja-creature package. These are observed casts or selected actions, not proof of strategic quality or complete rules execution. No aggregate reliably measures mana screw, missed land drops, unused mana, or pilot quality. Land/draw totals alone do not establish resource consistency.

## Fidelity findings and consequence

Under the frozen Stage 002 reconciliation, `reached_unsupported` means a matching opportunity witness exists but `occurrence_executed` has no authenticated executed reference for that semantic. It identifies a gap in verified execution evidence; by itself it does not prove the game applied the wrong effect. Of the 569 such occurrences in 222 games, the most frequent families were:

| Reached family | Occurrences | Games | Why it matters |
|---|---:|---:|---|
| Casey Jones ETB: inspect four and select/reveal an artifact | 126 | 84 | Changes card access and hand quality; highest-frequency reached gap. |
| Creature leaves: create a Mutagen token | 91 | 58 | Can change later counters, board development, and resources. |
| Creature ETB: search for Food or create Food | 63 | 42 | Can affect card access and life/resource options. |
| Does Machines / level 3 activation | 62 | 46 | Can alter artifact board development and combat. |
| Casey Jones ETB: draw three, delayed random discard | 55 | 40 | Can materially affect hand size and card access. |
| ETB artifact removal | 33 | 29 | Can change board state and remove relevant permanents. |
| Shredder grants Deathtouch; small-creature graveyard casting; Raphael's exiled-card play | 49 combined | 48 combined* | Can affect combat, board presence, and available plays. |

*Counts by family are 20/20, 16/15, and 13/13 respectively; game counts overlap, so 48 is the sum of family-game counts, not distinct games.

Other reached families include mill-three, Stockman's draw/discard, Donatello artifact counters, Alliance exile, counter replacement, Krang's hand refill, and counterspell-plus-Mutagen. The 300 summary groups by oracle text, not fully by owning deck; deck attribution should be confirmed from per-game object/event context before assigning a deck-level defect.

The 300 batch also has many `present_unreached` records: Flying (297 occurrences), conditional artifact-entry unblockability (243), Flying/vigilance (225), Deathtouch (193), and Menace text/keyword forms (153 combined). These do not establish that the ability was exercised. Menace legality/evidence and Deathtouch state-based actions have prior independent synthetic acceptance, but that does not validate every live interaction. The 50/100 reports separately record the known post-terminal `step_started` telemetry marker after `player_lost`; this is not evidence of a post-loss pilot action or changed winner. The 300 report has not independently aggregated terminal anomalies.

Two earlier 50-game event types remain review candidates: 10 `activated_ability_resolved_no_effect` records and 4 `rock_soldiers_no_target` records. The reports do not demonstrate that these were erroneous decisions. No comparable 300-game decision-quality aggregate was produced.

No demonstrated gameplay defect or winner-changing error is established by the warning summaries. However, the repeated reached gap for Casey Jones's card-selection effect is frequent and plausibly outcome-relevant enough that the affected calibration path should not be treated as validated until its resolution and evidence are established. Other fidelity warnings remain documented limitations; they do not by themselves require a broad rules-engine audit.

## Deck functionality and next action

**No deck is shown to be unable to function.** Every deck had wins in the 300-game batch, and the first 150 games show signature casts/actions across all ten. Pilot quality, strategic success, and resource consistency are not measured well enough to separate simulator limits from deck construction. Do not revise decks from these win totals.

**Recommended next action:** authorize one narrow synthetic fidelity verification/correction for Casey Jones's top-four artifact-selection ETB path, including its choice and resulting library/hand state evidence. Then review that exact result before deciding whether to prepare 900-game calibration. Do not launch games under this recommendation.

**450-GAME SYNTHESIS COMPLETE — HQ CALIBRATION DECISION REQUESTED**

## Dated evidence correction — 2026-11-03

This addendum preserves the historical telemetry and the raw occurrence totals above. It corrects the interpretation of the raw classification field using the focused Casey review and a read-only Stage 002 reconciliation of the 300 preserved snapshots against the frozen Stage 002 manifest.

- The original 300-game raw snapshot totals remain **3,025 semantic occurrences: 2,456 `present_unreached` and 569 `reached_unsupported`**. These are the recorded raw labels and are not rewritten.
- The focused Casey report, [`CARDCade_CASEY_JONES_ARTIFACT_SELECTION_FIDELITY.md`](CARDCade_CASEY_JONES_ARTIFACT_SELECTION_FIDELITY.md), independently validated the effect implementation and evidence. All **126 Casey occurrences in 84 games** reconciled as `executed`, with matching commit events, ledger entries, and authenticated references.
- Reconciliation of all 300 stored snapshots against the frozen manifest yields **460 `executed`, 119 `reached_unsupported`, and 2,446 `present_unreached`** (3,025 total). Thus raw `reached_unsupported` is not itself the final Stage 002 execution classification. The previous Casey-specific “execution-evidence gap” recommendation is superseded; no Casey code correction or new game is indicated.
- The remaining 119 reconciled `reached_unsupported` occurrences are in 87 games. The largest documented family is **Does Machines, `{4}{U}: Level 3` — 62 occurrences in 46 games**. This class ability says that at the beginning of combat on its controller’s turn, it puts three +1/+1 counters on a target artifact they control and makes it a 0/0 Robot creature if it is not already one. This could affect board development and combat. The current evidence establishes an unresolved execution-evidence gap, not that the effect was incorrectly resolved.
- Full-snapshot reconciliation also produced 485 `silent_approximation` stop records across the broader batch. Their non-Casey causes are not analyzed in this addendum; they are not silently cleared by the Casey result.

The 300-game batch remains exploratory and does not become certified balance evidence. For the planned calibration, the remaining Does Machines level-3 gap is the narrowest demonstrated concern that could materially distort Donatello’s results. The next action is a targeted synthetic and telemetry reconciliation of that single effect before final 900-game readiness approval. No additional games are authorized here.
