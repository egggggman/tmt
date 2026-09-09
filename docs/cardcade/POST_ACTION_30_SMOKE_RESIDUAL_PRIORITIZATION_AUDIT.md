# Smoke Residual Prioritization Audit

Exact checkpoint/evidence base: `9ec82e25e4a83a49b139d41b1d19e01498a93327`.

**Recommendation: prioritize a bounded authorization audit for Paramecia Coloniex's ETB mill-three fragment, followed by Krang's conditional hand refill.** Tunnel Rats merits a source-permission/timing architecture audit before any implementation authorization. Menace has the highest measured exposure but belongs in a separately scoped multi-blocker combat program.

This is an evidence-only recommendation. It does not authorize Action #31, implementation, new simulations, calibration, Pilot/deck changes or Prototype 0.3. No production, test, deck or runner changes were made. No Stage or Smoke runs occurred.

## Evidence and ranking method

The accepted `POST_ACTION_30_SMOKE01_RESULTS.json.gz` supplies 180 distinct games / 360 executions across all 45 frozen pairings. Its compressed SHA-256 is `7fce9bd9feab5a8e1d2075f9b0cbd8155923d8a433c5a505cf31724bcac22829`. The sidecar was verified and the complete saved-artifact validator passed, including duplicate/report reconstruction. The exact checkpoint was verified clean before this audit.

Every REACHED-UNSUPPORTED occurrence was joined to its exact Oracle fragment and physical lineage using `semantic_key` plus membership of `object_id` in `presence.object_ids`. The [derived evidence inventory](POST_ACTION_30_SMOKE_RESIDUAL_PRIORITIZATION_EVIDENCE.json) preserves all 133 witness rows, exact game/object/occurrence IDs, fragment groups, game memberships, conservative terminal cases and overlap counts. Its SHA-256 sidecar authenticates the derived inventory.

Affected games are unique `game_id` values, counting each duplicated game once. Menace is grouped across its three cards because its identical omitted rule has one implementation boundary. Raphael's exile/play pair is assessed as a linked implementation, using the union of game IDs rather than adding its two six-game counts. No outcomes, win rates or deck-strength statistics were used.

Calibration impact below is a qualitative assessment of the legal-play/resource/combat behavior omitted, not a measured outcome effect. Boundedness and reuse are source-inspection judgments, not completed architecture authorization audits. The recommended priority favors material exposure with a credible narrow completion path. It is deliberately not a numeric weighted score: the separate exposure rank makes visible where a lower-exposure bounded candidate is preferred over a broad engine program.

## Separate terminal incompleteness from implementation omissions

Raw Smoke has 75 coverage-limited games and 133 reached-unsupported occurrences, grouped as 16 card/fragment clusters or 14 exact-fragment groups.

Eight occurrences do not support a new implementation request:

- **Vigilante: 3 occurrences / 3 games.** Existing schedules are pending when the game ends before completion; complete delayed-chain validation passes. These are conservative terminal cases, not missing random-discard scheduling.
- **Zoo Escapees: 5 occurrences / 5 games.** In each case the source leaves during terminal combat, with the accepted `ltb_mutagen` trigger still pending or on the Stack when the game ends. Four snapshots retain a pending trigger; `michelangelo--shredder:reversed:8082` retains the uncompleted triggered ability on the Stack. There is no completed token-creation chain to credit. The fragment's retained `token_activated_ability_not_implemented` limitation must not be mistaken for evidence that Mutagen activation was actually reached in these five games. Token creation is already implemented.

Excluding these eight only for prioritization leaves **125 candidate omission occurrences across 69 distinct games**. Six games contain only terminal residuals; two of the Zoo cases overlap other omissions. Official 75-game coverage-limited labels and all original occurrence classifications remain unchanged. Neither this filtering nor a residual count proves that an omitted choice would have changed a winner.

Mutagen activation remains a known dependency of the full Ooze Spill compound fragment, but the terminal Zoo rows supply no standalone materially reached activation priority.

## Exposure ranking and four-factor assessment

`G / O` means distinct affected games / semantic occurrences. Game counts overlap across rows. Boundedness is graded Narrow, Conditional, or Broad; reuse describes the actual seams available rather than assuming a full implementation exists.

| Exposure rank | Omission | G / O | Calibration impact | Boundedness | Existing primitive reuse and missing boundary |
|---:|---|---:|---|---|---|
| 1 | Menace across Splinter, Bebop and Raphael | 23 / 23 | High: blocker legality and combat allocation | Broad | Combat declarations, strike steps, damage and SBAs exist; current block representation is one blocker per attacker. Multiple-blocker options, ordering/assignment, Trample/strike interaction and evidence must change together. |
| 2 | Paramecia Coloniex ETB mill three | 17 / 22 | High: library/graveyard resources and future draws | Narrow candidate | ETB/Trigger/Stack/Priority, authoritative top-library identities and `move_object` to graveyard exist. Add exact mill semantics and reconstruction; no choice, RNG, exile, or new zone needed. |
| 3 | Tunnel Rats graveyard self-return tapped | 15 / 18 | High: recursive creature availability and legal plays | Conditional | Fixed mana payment, Stack, authoritative graveyard objects and battlefield incarnations exist. Activation enumeration currently scans battlefield permanents; source-zone authorization, CardObject provenance and activation timing must be audited. |
| 4 | Leonardo graveyard casting plus finality | 13 / 15 | High: repeated casting permission and death destination | Broad | Cast/cost/Stack, characteristics and counters exist. Graveyard casting permissions, complete qualification, entry provenance, exile/finality replacement and permission lifetime are coupled. |
| 5 | Paramecia death/exile/reflexive graveyard return | 12 / 16 | High: recursion and next-draw selection | Broad compound | Death LKI, targeted identities and graveyard-to-library movement exist. Exile is not an authoritative supported destination; optional exile plus the reflexive “when you do” targeted trigger requires new linked authority. |
| 6 | Raphael linked Alliance exile and attack-time play | 7 / 12 | High: additional cards/plays and temporary permissions | Broad compound | Entry/attack triggers and durations exist. Missing authoritative exile, source-linked identity, optional exile decision, land-versus-spell play permission, costs/timing and expiration. Each fragment affects six games; their union is seven. |
| 7 | Krang ETB refill toward four cards | 6 / 7 | High within affected games: hand resources | Narrow candidate | Reuse intervening-if ETB checks and authoritative `draw(count)`, including failed-draw behavior. Evaluate hand-count condition at trigger creation and resolution, then draw the current difference. |
| 8= | Frog Butler mana of any color | 4 / 4 | High within affected games: payment/color availability | Conditional | Tap and payment planning exist. Current mana-source inference selects a represented fixed color; color choice, mana-ability treatment and payment provenance need a focused audit. Do not route it as an ordinary resolving Stack ability by assumption. |
| 8= | Frog Butler temporary Reach activation | 4 / 4 | Moderate: flying-block legality during effect lifetime | Narrow candidate, timing caveat | Fixed mana activation, temporary keyword expiration and blocking predicates exist. Add exact self-Reach effect and evidence; current activation enumeration is main-phase/empty-Stack bounded, so response-window fidelity must be explicit. |
| 10 | Ooze Spill counterspell plus Mutagen | 2 / 3 | High within affected games: spell denial plus counter resource | Broad compound | Existing targeted counterspell activation/provenance, spell Stack and token creation are useful, but not a complete targeted instant cast/counter/token chain. Mutagen's sorcery-speed targeted sacrifice activation remains a dependency. |
| 11 | Michelangelo additional +1/+1 counter replacement | 1 / 1 | Moderate-to-high locally: counter growth across placements | Conditional to broad | Central `place_counters` and replacement-opportunity witnesses exist. Audit all placement paths, once-per-event application, source/controller authority and multiple replacement interaction before claiming boundedness. |

Exact Oracle text, card names and witness IDs for every row are in the derived inventory. The raw fourteen-group accounting includes the two terminal groups and keeps Raphael's two fragments distinct; bundling them and excluding the terminal groups produces eleven candidate implementation units in this table.

## Recommended priority for the next review

This is an order for scoping/authorization review, not permission to implement every item sequentially.

1. **Paramecia ETB mill three.** Best combination of 17-game exposure and a short, reusable transaction. The audit should verify top-to-graveyard order/new incarnations, `min(3, library size)`, no failed-Draw loss from milling, no pre-all-pass mutation, and complete ETB-to-movement evidence. Preserve the death/exile sibling as unsupported. Stop if implementation unexpectedly needs new zones or a general hidden-zone language.
2. **Krang conditional refill.** Six-game exposure is lower, but the condition plus existing Draw machinery is especially bounded. Reuse the accepted intervening-if pattern rather than checking hand size only at resolution. No generic variable-action language is necessary for this exact fragment.
3. **Tunnel Rats — architecture audit only.** Its 15-game exposure is worth checking next, but battlefield-only activation assumptions are a real boundary. Verify source-zone permission, lifecycle while the source is in the graveyard, legal instant-speed activation windows, mana/cost provenance and tapped entry. Do not label this a simple `move_object` call or promise full coverage through a sorcery-speed-only approximation.
4. **Frog Butler Reach — timing audit first.** Strong action/keyword reuse and a small payload, but four-game exposure and no standalone raw clearance give it less immediate value than mill/refill. Restrict any future claim to an independently approved timing contract.
5. **Menace — separate combat specification.** Largest exposure and high calibration impact justify a dedicated design decision. It should not be smuggled into the next small Action merely because it is one keyword. It can move ahead of smaller items if HQ chooses a broader combat program explicitly.
6. **Paramecia death/exile/reflexive return.** Twelve games, but exile and a second targeted trigger make the full transaction materially broader than its ETB sibling. Mill support does not clear this fragment.
7. **Leonardo graveyard/finality lifecycle.** Thirteen games and substantial fidelity value, but a larger permission/replacement lifecycle than the single death transaction. Treat as its own program.
8. **Frog Butler colored mana.** Only four games in this sample; audit payment integration and mana-ability semantics before interpreting apparent tap-cost reuse as readiness.
9. **Raphael linked exile/play.** Seven-game union, two inseparable authority domains and no authoritative exile zone. Implementing only exile would not establish linked play fidelity.
10. **Ooze Spill compound counter/token/activation.** Two games, several distinct missing child/parent boundaries. Existing counter activation is reuse evidence, not proof the whole instant and its token activation are already executable.
11. **Michelangelo replacement.** One game gives little immediate coverage leverage while replacement composition risks a wider change surface. Reassess if a later authorized artifact demonstrates broader exposure; no new run is requested here.

Within the narrow-candidate class, mill and refill are the clear first two. Exposure-only ordering would put Menace first; the recommendation instead accounts for boundedness and existing primitive reuse. This is an explicit tradeoff, not a claim that Menace has low calibration impact.

## Static overlap context, not simulated forecasts

Holding the historical trajectories fixed, the number of games whose entire raw residual set consists only of the named unit is: mill 3, Krang refill 6, Tunnel Rats 5, Menace 10, Leonardo 10, Paramecia death 0, Frog Reach 0, Frog mana 0, Raphael linked pair 5, Ooze Spill 1, Michelangelo replacement 1.

These set counts explain why a frequent omission may clear few games alone. They are not predictions of the post-implementation coverage-complete total: changed cards, draws, attacks and RNG consumption can change later opportunities. Nor does historical clearance make any selected game calibration-valid. No fixed coverage target is recommended.

## Source-inspection anchors

All paths refer to the exact checkpoint tree:

- `src/tmnt_design_studio/engine07.py`: `move_object` (supported zones, same-zone prohibition, new incarnations, library top/bottom position); `_enqueue_trigger` and `_resolve_triggered_ability`; `_validate_etb_artifact_draw_provenance`; `draw`.
- `src/tmnt_design_studio/card_interpreter07.py`: `etb_artifact_draw_semantic_coverage`, `activated_ability_semantics`, `ltb_mutagen_semantic_coverage`, `_token_semantics`; the last two preserve the distinction between accepted token delivery and retained activation limitations.
- `engine07.py`: `legal_activated_ability_actions` (battlefield source enumeration, active-player main phases and empty Stack); `_mana_color`/payment planning; `_validate_counterspell_provenance`; temporary-keyword methods and blocking predicates.
- `engine07.py`: `generate_blocks`, `legal_block_options`, `execute_block_action`, strike/damage methods; the current one-to-one block model is the concrete Menace boundary.
- `engine07.py`: `place_counters` records the unsupported replacement opportunity while placing the represented quantity; its existence does not prove every counter-entry or replacement-composition path is covered.
- `src/tmnt_design_studio/jury_rig07.py`, `food_search07.py` and `vigilante07.py`: accepted library identity, mutation guards, movement and delayed-chain evidence patterns. No general scheduler or hidden-zone rewrite is implied by their reuse.

## Handoff

Preserve this audit and its derived witness inventory with SHA-256 sidecars. No historical artifacts or classifications are overwritten. The existing Engine Validation Checkpoint's **NOT READY for calibration** conclusion remains: semantic prioritization does not supply the missing Pilot fitness evidence or prospective calibration protocol.

Next recommended HQ decision: whether to authorize a small **Paramecia ETB mill-three architecture/authorization audit**, using this exact evidence base and leaving all sibling semantics untouched. Action #31 remains NOT AUTHORIZED. Calibration remains BLOCKED. Prototype 0.3 remains NOT AUTHORIZED.
