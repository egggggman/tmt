# Objective Balance Lab Round 5 — candidate plan

This is a pre-simulation design gate, **not a completed experiment**. All candidates start independently from the exact [OBL-BASELINE-002 manifest](baselines/OBL_BASELINE_002_MANIFEST.json). They do not alter the seven frozen decks, official deck files, Cardcade, promotion history, or the experiment ledger. The [diagnostic](ROUND_5_DIAGNOSTIC.md) explains why these three decks, slots, and levers were selected. [Machine-readable plan](ROUND_5_CANDIDATE_PLAN.json).

## Surviving candidates

Each diff moves **two slots** (two removed copies plus two added copies), changes no land, and leaves an exact 60-card deck. SHA-256 values identify the preserved candidate's Git-authored LF bytes; validation normalizes a possible Windows CRLF checkout before hashing.

| ID | Exact diff from Baseline 002 | Candidate SHA-256 | Evidence class | Gate |
|---|---|---|---|---|
| `OBL-R5-SHREDDER-A` | -1 Dream Beavers; -1 Squirrelanoids; +2 Tunnel Rats | `7431daaed35e68d663a88f6e529444e468500b393d4676aaa658bb0c2a564139` | `NEW_LEVER` | `READY_FOR_ROUND_5_SIMULATION` |
| `OBL-R5-SHREDDER-B` | -1 Dream Beavers; -1 Shark Shredder, Killer Clone; +2 Tunnel Rats | `1ce0828b6ac107bc8cdf2e0b965d919e83941316803880a71d11bbbb48902fc1` | `NEW_LEVER` | `READY_FOR_ROUND_5_SIMULATION` |
| `OBL-R5-APRIL_ONEIL-A` | -2 Negate; +1 April, Reporter of the Weird; +1 Utrom Scientists | `ebaff265d90b5cfbec4f7e9662a9d105f9ef8f58a17b06949626ed2ff898b8b7` | `NEW_LEVER` | `READY_FOR_ROUND_5_SIMULATION` |
| `OBL-R5-KRANG-A` | -2 Negate; +2 Mouser Mark III | `565b5e0c0486d04c631ccefa238fc0c16af13d13c4b6d409fd12d4ea82a24ca9` | `NEW_LEVER` | `READY_FOR_ROUND_5_SIMULATION` |
| `OBL-R5-KRANG-B` | -2 Negate; +2 Donatello, Turtle Techie | `d1691343e948d96f454468fb360c85e2f68dbe04ae7eed545430560153816bcd` | `VARIANT_OF_PROMISING_LEVER` | `READY_FOR_ROUND_5_SIMULATION` |

Parent file SHA-256: Shredder `818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2`; April `684c898760a39c5dfc584206ef4675c49d96cfe6bd419f03f86bd0b8358d09f4`; Krang `5a52bc59b5de1034721ba17d1c1d4f12c493ec70681c1a910c8230808e4e4f96`. Paths and hashes are also in the machine plan. Mono-black Shredder, mono-blue April, and mono-blue Krang retain 22 basics each.

### Falsifiable hypotheses and predicted observables

- **Shredder A (primary):** Replacing one copy each of two frequently cast one-drops with two-mana rats will delay early board presence and lower aggregate WR, mean balance error, and extreme counts while retaining Shredder's villain-minion pressure. If turn-3 presence does not fall, or power/balance worsens, the dilution hypothesis fails. The rat's graveyard-return text is *not* part of the measurable claim.
- **Shredder B:** Replacing one early Dream Beaver and one four-mana Shark Shredder with the same lower-impact rats will reduce both opening pressure and late closing, with fewer extremes and preserved Shredder identity. Using the same replacement as A isolates whether the late conversion slot matters; it does not retest the R3 Oroku/Technique replacement.
- **April A (primary):** Converting two reactive Negates into a Reporter body and a stun-capable Utrom Scientist will improve board development and survival (earlier presence, higher WR, lower balance error, fewer extremes) while reducing reactive-cast density. The Reporter combat-draw trigger is not represented, so any observed result tests board/tempo, **not** information-card advantage.
- **Krang A (primary):** Turning two reactive Negates into artifact-conditioned two-mana Mouser attackers will let the existing technology board produce earlier pressure, increasing WR and presence and reducing balance error/extremes. The Mouser must still have another artifact to attack; that gate is part of the test.
- **Krang B:** Turning the same reactive slots into artifact-conditioned 3/4 ETB-draw bodies will improve midgame board conversion and card flow without more Does Machines or eight-mana Krang. WR and midgame presence should rise, balance error/extremes should fall; two Donatello cameos are an identity risk to assess after results, not a pre-approved promotion.

Predictions are hypotheses, not simulated outcomes. No candidate is marked `ACCEPT_FOR_COMBINED_MATRIX` here.

## Frozen-card and semantic pre-screen

The following is the **exact rules text** of every addition from the [frozen Standard-legal snapshot](../../cardcade/scryfall-tmt-pza-tmc-2026-08-13.json). All five names resolve and have `legalities.standard = legal`. The Pilot casts legal creature actions during its creature stage; that is supported by existing unit tests and current deck telemetry. Text that is not executed is called out rather than silently counted as a payoff.

| Added card | MV / mana / type | Exact rules text | Legality, Pilot use, prior evidence, thematic role |
|---|---|---|---|
| Tunnel Rats | 2 / `{1}{B}` / Creature — Rat | `{4}{B}: Return this card from your graveyard to the battlefield tapped.` | Mono-black legal. The 2/2 creature can be cast/used by the Pilot; no authenticated graveyard-activation usage exists, so only the slower body is a credible pressure lever. No prior OBL candidate added it. Undercity minion, not another signature Shredder threat. |
| April, Reporter of the Weird | 3 / `{2}{U}` / Legendary Creature — Human Detective | `Whenever April deals combat damage to a player, draw that many cards, then discard a card.` | Mono-blue legal and cast as a creature (750 baseline signature casts); interpreter does not execute the combat-draw trigger. R3-A used one extra copy in a value-density package; here it replaces reactive Negate and contributes a body. Maintains reporting identity but value effect is **not** evidence. |
| Utrom Scientists | 3 / `{2}{U}` / Artifact Creature — Utrom Robot Scientist | `When this creature enters, tap up to one target creature and put a stun counter on it. (If a permanent with a stun counter would become untapped, remove one from it instead.)` | Mono-blue legal; baseline April 662 casts and engine has bounded ETB tap/stun semantics. Existing baseline card, not an untested new effect. One extra copy provides an active board-plus-tempo lever, albeit with an artifact-themed supporting cameo. |
| Mouser Mark III | 2 / `{1}{U/R}` / Artifact Creature — Robot | `This creature can't attack unless you control another artifact.` | Standard legal; the hybrid symbol is payable with an Island, as the [Mouser unit tests](../../tests/test_mouser_mark_iii_semantics.py) verify. Its attack gate is unit-tested with/without another artifact. Existing Donatello artifact piece, not a previous Krang candidate. Converts Krang's own artifact density into an attacking body. Its formal hybrid color identity is U/R, but it is color-*payable* in this mono-blue Standard deck; this is not Commander. |
| Donatello, Turtle Techie | 4 / `{3}{U}` / Legendary Creature — Mutant Ninja Turtle | `When Donatello enters, if you control an artifact, draw a card.` | Mono-blue Standard legal. Creature casting and conditional ETB artifact draw have [engine tests](../../tests/test_etb_artifact_draw_action.py); R2 Donatello-A used extra copies successfully. It is a technology cameo in Krang, not generic rate alone. The 4-mana cost is a midgame conversion experiment, not the cheap-payoff A hypothesis. |

The removal-side screen matters too: Dream Beavers and Squirrelanoids are one-mana Shredder creatures with 1,061 and 981 signature casts; Shark Shredder has 594; April's and Krang's Negates are reactive cards while those decks' first-creature proxies are late. All five candidate additions are active creature spells, unlike Shredder Armor, Anchovy Pizza, Cam, and Bespoke Bō, which show draws but zero casts in the current-runtime Baseline 002 evidence. No proposed package is functionally identical to a previous Shredder Oroku/Technique, April interaction-density, or Krang setup/high-end swap.

### Rejected before simulation

| Deck | Screened idea | Status | Reason |
|---|---|---|---|
| April | April O'Neil, Kunoichi Trainee | `REJECT_PRE_SCREEN` | Its mana cost is `{1}{W}` in the frozen snapshot; mono-blue cannot cast it. Earlier OBL appearance does not override color legality. |
| April | More Negate / Retro-Mutation | `REJECT_PRE_SCREEN` / `REPEATS_FALSIFIED_LEVER` | R3-B already worsened balance; reactive density does not answer board conversion. |
| April | A second reporting/value-density variant | `NEEDS_SEMANTIC_SUPPORT` | Reporter combat draw and Hacktivist end-step draw are not executable, and repeating R3-A would conflate body count and information value. **No April-B file was created.** |
| Shredder | Shredder's Revenge or more Anchovy & Banana Pizza | `REJECT_PRE_SCREEN` | Modal sorcery not Pilot-cast; current Pizza casts zero and R2 tried a Pizza replacement. |
| Krang | Chrome Dome / Technodrome | `NEEDS_SEMANTIC_SUPPORT` | Relevant artifact-pump/copy or attack-gate/activated payoff semantics are incomplete. |
| Krang | More Does Machines / eight-mana Krang / Omni-Cheese setup | `REJECT_PRE_SCREEN` / `REPEATS_FALSIFIED_LEVER` | R2/R3 isolated and combined evidence already weakens or falsifies these directions. |

## Next-PR execution contract

If these **five** designs remain approved at execution, each plays nine OBL-BASELINE-002 opponents for 100 games, 50 starts per seat: **900 games per candidate, 4,500 candidate games total** (the six-candidate ceiling would be 5,400). Reuse the frozen schedule `b5fd8ab57016b15662fca420d508c9aab3633ad14b7f7515d667492b0f8abf27`, with no adaptive or replacement seeds and no candidate-vs-candidate cells. Do not regenerate Baseline 002. Composition may later reuse unchanged Baseline 002 cells and authenticated isolated cells **only** after deck-byte, schedule, orientation, and semantic-runtime identity checks; candidate-vs-candidate pairings would require new games. This PR creates no match-simulation outputs or verdicts.
