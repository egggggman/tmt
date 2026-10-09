# Complete Ten-Deck Build and Test — HQ Work Packet

Authority: user requested completion and testing of remaining six decks after Human Playtest 001.
Owner: HQ coordination; Design Studio owns deck changes; Cardcade owns simulator testing; Mr. Paperback owns physical assembly/print materials.
Status: **execution authorized for inventory/build preparation and staged validation**, not authorization to silently alter lists, bypass semantic gates, or claim unrun simulations.

## Freeze and roster

Preserve the four existing physical Human Game Day Candidate 0.1 decks unchanged:
- Raphael
- Michelangelo
- Splinter
- Casey Jones

Prepare the remaining **six exact OBL-BASELINE-005** deck lists:
- Leonardo
- Donatello
- Shredder
- Krang
- Bebop & Rocksteady
- April O'Neil

Use authenticated Baseline 005 source manifests from the repository, not speculative reconstruction from older deck prototypes. Do not substitute cards for physical shortages; report exact shortages and, for casual testing only, label exact-card proxies with player consent. Physical card inventory has **not yet been checked** for the six new decks.

## Physical build gate — Mr. Paperback

1. Resolve all six exact Baseline 005 60-card manifests and verify identities/hashes against accepted sources.
2. Produce per-deck card-pull checklists and one consolidated inventory demand sheet accounting for simultaneous copies across all ten decks.
3. Pull/sleeve/count 60 cards per deck; record shortages and exact-card proxy needs separately.
4. Confirm basic lands, nonbasic lands, token requirements, equipment/counters, and rules reminders per deck.
5. Label deck boxes; print and physically test the one-page Oracle-verified reference from Human Playtest 001.
6. Mark each deck **ready**, **proxy-ready for casual play**, or **blocked**, without treating an unverified inventory as assembled.

Deliver: six verified manifests, inventory/shortage register, physical assembly signoff.

## Cardcade validation gate

Do not assume previous Baseline 005 balance evidence establishes full rules fidelity.

1. Freshness audit: current main, accepted Baseline 005 identity, active semantic runtime, open engine work, and known defects.
2. Structural validation: all ten lists, legality, copy limits, 60-card counts, card-data resolution, deck hashes.
3. Semantic coverage: audit relevant cards/actions for all ten; specifically resolve or quarantine April's Reporter of the Weird combat-damage draw/discard trigger, and inspect Skateboard/haste/double strike and Sneak raised by Human Playtest 001.
4. Deterministic smoke and invariant testing under the authenticated runtime. Stop if a materially consequential action is unimplemented or incorrect; fix generic engine semantics and retest before using win rates.
5. If the runtime remains identical and prior Baseline 005 evidence is authenticated, reuse its preserved 45-cell matrix rather than needlessly rerunning. If semantics change, establish a new unchanged Baseline 005 control and replay under the new runtime before interpreting balance.
6. Only after engine readiness: authorize appropriately sized, reproducible matchup testing with balanced starting-player splits, fixed seeds, deck hashes, runtime ID, replay checks, telemetry, and preserved artifacts.
7. Report aggregate and per-matchup performance, first-player effects, pace, interaction failures, synergy execution, and semantic confidence. Separate simulator limitations from deck issues.

Deliver: reproducible validation report and explicit GO/STOP gate; no autonomous deck revisions.

## Design Studio review

Read Cardcade and Human Playtest 001 evidence together. Preserve historical baselines. Prioritize:
- Raphael/Skateboard perceived oppression versus rules confusion, multiple mulligans, and draw variance.
- April semantic uncertainty before judging its deck balance.
- B&R and other known matchup deficits only after credible runtime evidence.
- Human fun, deck identity, replayability, and meaningful interaction.

Only Design Studio may propose exact minimal card changes, as separate candidates with their own authorizations and validation.

## Human test expansion

Start with the current four, introduce **Shredder** as fifth if physically ready, then add the remaining five in a manner that keeps balanced and exploratory matchups distinct.

Track per game: matchup, players, starting player, winner, approximate ending turn, mulligans and land difficulties, rules lookups, close/interactive, fun, frustrating, replay desire, standout cards. Preserve original notes verbatim. Avoid interpreting a few human games as statistically valid win rates.

## Stop conditions

Stop the affected gate, not the entire project, for:
- unresolved exact decklist identity;
- structural invalidity;
- critical missing simulator semantics;
- mismatched runtime/control evidence;
- physical shortage that prevents an accurate casual proxy or legal game;
- any proposed deck redesign without Design Studio authority.

## Immediate next move

**Cardcade:** perform read-only Baseline 005 manifest/runtime/semantic readiness audit.  
**Mr. Paperback:** derive six exact card-pull lists and combined ten-deck inventory.  
**HQ:** review gate outcomes and authorize the smallest next execution step.  

No claim of six physically assembled decks or newly completed simulation games is made by this work packet.

COWABUNGA.
