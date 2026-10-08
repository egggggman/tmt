# Human Playtest 001 — Department Work Packet

Owner: HQ coordination. Evidence: `docs/hq/HUMAN_PLAYTEST_001_2026-10-08.md`.
Scope: move forward without changing Baseline 005 or inferring a statistically valid balance result from three games.

## Priority 1 — Mr. Paperback: table quick-reference prototype

Produce a one-page, legible table reference for casual human testing.

Topics surfaced by players:
- Skateboard: exact current Oracle text, timing, and how it is played/used.
- Haste versus summoning sickness.
- Artifact versus artifact creature; Equipment if relevant to Skateboard.
- Double strike combat sequence and overkill.
- Sneak (using the specific printed cards in this environment).
- Mana cost/color symbols and multicolor-card interpretation.
- Food token activation and timing.
- Where to consult official Oracle card text during a game.

Do not invent or paraphrase unfamiliar card abilities without verifying authoritative Oracle text. Cite card-specific text source/version and relevant official rules sections in the working source. Flag unresolved ambiguities instead of printing guesses.

Acceptance: print at actual size, read at table distance, use in a physical test game, log any failed explanation and revise. Owner: Mr. Paperback; Canon may support rules/source checking.

## Priority 2 — Cardcade: read-only interaction and evidence audit

Audit generic runtime support for Skateboard and the relevant haste, artifact, equipment (if applicable), double strike, and combat sequencing.

Distinguish: (a) actual Oracle/rules semantics; (b) runtime implementation and tests; (c) pilot behavior; (d) observed human game; (e) hypothesis.

Check preserved Baseline 005 Raphael vs Casey evidence for early pressure and relevant card frequencies where telemetry supports it. No new large simulations unless a specific validated engine issue requires an authorized run. No card revisions.

Deliver a compact evidence/hypothesis report with reproducible references and any exact semantic gaps.

## Priority 3 — Design Studio: review only

Review the human observation that Raphael felt outlying/oppressive and the potential early concentration of Skateboards.

Do not treat one game, multiple mulligans, or three Skateboards in a draw as proof of broken balance. Assess interaction with mana issues, first-player advantage, double strike, and human rules interpretation. Consider whether additional unchanged-list human games are needed before a smallest-change hypothesis.

Preserve exact Baseline 005 and prior versions. Design Studio alone owns any future deck revision.

## Human test protocol — next opportunity

Play unchanged decks with a verified reference sheet. Record:
- winner and first player;
- exact mulligan counts per player and whether opening mana was the cause;
- approximate ending turn;
- key Skateboard appearance/cast/equip/attack turns if relevant;
- close/interactive/fun/replay assessment;
- rules lookups and unresolved interpretations.

If Raphael was excluded from the later two games, retain that selection effect. Do not infer win rates from this small convenience sample.

## Outstanding factual clarification

Game 2 Splinter vs Michelangelo winner not explicitly identified in raw notes; final-life notation -5/6 is not mapped to deck order. Leave unknown until confirmed. This does not block the departmental work above.

## Gate

No deck changes, simulator tuning to target 50%, large calibration, or baseline promotion authorized by this packet. Human feedback informs decisions but does not alone validate mechanical implementation.

COWABUNGA.
