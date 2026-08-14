# Cardcade Engine 0.8 Foundation Acceptance Audit

Audit date: 2026-08-14 EDT

Audited HEAD: `24a87cdb3463c645b87cfb5235240a19ab4fb128`

Branch: `agent/cardcade-engine-0.7`

Pull request: [#27](https://github.com/egggggman/tmt/pull/27)

## Recommendation

**ACCEPT**

Engine 0.8 foundation is suitable to become the new Cardcade architectural baseline and PR #27 is
eligible for merge.

This recommendation accepts the represented architecture, not complete Magic coverage. The audit
independently confirms **10 GREEN / 10 YELLOW / 0 RED / 0 UNKNOWN**. The ten YELLOW rows are explicit,
extension-safe limitations. No evidence requires a RED classification, and no audit failure was
silently repaired.

## Audit boundary and repository integrity

The audit began with a clean worktree. Local `HEAD`, the checked-out branch, the refreshed
`origin/agent/cardcade-engine-0.7` ref, and PR #27's `headRefOid` all identified the audited SHA above.
PR #27 remained open throughout the audit and was not merged. At final remote inspection it was
**MERGEABLE / CLEAN**, and both GitHub Actions test jobs passed.

The refreshed PR comparison against `origin/main` contains 27 commits and 25 changed files. Its
history preserves the intended Engine 0.7 checkpoints (`d62e7ab` through `0f01c08`), the initial
Foundation Matrix (`4a8c17b`), and paired Engine 0.8 implementation/re-audit checkpoints through
0.8h. Historical Engine 0.1–0.6 code and evidence already on the base remain present. The historical
Engine 0.6 `cardcade/card-model-0.6.json` blob has SHA-1
`6394080e24c9277827bf967766b54611ed9baf00`, exactly matching its introducing commit, and still
contains 103 records.

No deck or `cardcade/runs` file is changed by PR #27. No `PROTOTYPE_0.3` path exists. Frozen deck
prototypes, historical smoke/calibration evidence, and the Engine 0.6 model are therefore preserved,
not regenerated or repurposed. The matrix document preserves the requested progression:

| Audit | GREEN | YELLOW | RED | UNKNOWN |
| --- | ---: | ---: | ---: | ---: |
| Pre-0.8a | 2 | 7 | 11 | 0 |
| Post-0.8a | 3 | 8 | 9 | 0 |
| Post-0.8b | 4 | 8 | 8 | 0 |
| Post-0.8c | 5 | 10 | 5 | 0 |
| Post-0.8h | 10 | 10 | 0 | 0 |

## Authoritative card-data result

The integrated runner loads the checksum-verified normalized TMT/PZA/TMC snapshot through
`CardDataCatalog`; `load_facts()` derives engine facts from catalog records, and deck loading then
uses those derived facts. The Engine 0.6 export is referenced only by preservation/equivalence tests,
not as the current engine source.

Independent tests and a temporary live regeneration confirmed:

- 472 print records and 332 unique Oracle objects;
- 10 frozen decks and 600/600 resolved slots;
- all 472 records expose Scryfall ID, Oracle ID, name, Oracle text or complete face text, keywords,
  type line, mana-cost field, mana value, set, collector number, and legality data;
- all 265 creature print records contain power and toughness;
- the one multiface print exposes two complete faces;
- the production normalization path regenerated the exact committed snapshot SHA-256
  `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`;
- field-by-field comparison of all required normalized fields found zero differences from live data.

The test-only `HISTORICAL_ACCEPTANCE_PT` map verifies removal of the former table; production engine
and runner code do not import it. No separate production P/T truth table has returned.

The standalone audit script's transient checksum differs because that script does not sort keyword
arrays before hashing, while the production builder does. Its counts and records were unchanged; the
production rebuild matched exactly. This is a documented audit-tool canonicalization nuance, not a
card-data integrity failure.

## Independent 20-row Foundation Matrix verification

| Foundation row | Result | Independent executable/structural evidence | Explicit boundary or extension path |
| --- | :---: | --- | --- |
| Card Data / Oracle | **GREEN** | Checksum validation, required-field tests, live regeneration, and 600/600 deck resolution pass. | Extend the normalized catalog for additional characteristics; do not add parallel fact tables. |
| Object Identity | **GREEN** | Registry membership uses object identity, zone movement creates new runtime IDs, and fabricated/equal/stale objects fail adversarial tests. | Tokens, copies, face-down/merged objects, LKI, and CR 400.7 exceptions must use the same service. |
| Zones | **YELLOW** | Library, hand, stack, battlefield, graveyard, and former-object state are authoritative and invariant-checked. | Exile, command, same-zone ordering, exceptions, and fully encapsulated collections are absent. |
| Turn Structure | **GREEN** | Engine-owned read-only turn state enforces the represented CR 500-series successor graph and rejects unresolved-stack advancement. | Priority windows, extra turns/phases/combats, team turns, hand-size cleanup, and repeated cleanup remain future work. |
| Combat State | **YELLOW** | Step-bound attacker/blocker declarations, revalidation, damage, cleanup, and reset tests pass. | Defender choice, arbitrary subsets, multiple blockers/order, trample, extra damage, planeswalkers/battles, and attack costs are unsupported. |
| Costs | **GREEN** | Frozen requirements/plans, precommit revalidation, exact colored/generic selection, and injected-failure rollback pass. | Hybrid, Phyrexian, snow, X, modifiers, mana abilities, player-selected payments, and additional/alternative/nonmana costs extend the transaction. |
| Choices vs Targets | **YELLOW** | Represented targets are locked as runtime IDs and revalidated at resolution; fabricated/stale/illegal targets fail safely. | Typed requests, modes, divisions, optional/multiple/partial targets, and resolution choices are absent. |
| Events | **YELLOW** | Frozen rules events carry deterministic IDs, kind, player, and subject runtime IDs; logs are projections rather than rules input. | Simultaneous batches, replacements/prevention, richer causes, and LKI snapshots are absent. |
| Triggers | **GREEN** | Oracle-pattern detection creates typed trigger instances and independent ability stack objects; source departure, APNAP grouping, stack interaction, and deterministic telemetry tests pass. | Player ordering, target/mode timing, intervening-if, delayed/leaves/dies/cast triggers, complete APNAP/priority, and broader patterns remain unsupported. |
| Stack | **GREEN** | Represented casts traverse Hand→authoritative spell object→shared LIFO stack→battlefield/graveyard with new identities; stale/fabricated operations and bypassed advancement fail. | Activated abilities, copies, face-down spells, countering, replacement destinations, and full casting/priority steps remain unsupported. |
| Priority | **YELLOW** | Stack resolution and turn-transition seams exist, but represented casts/triggers use documented immediate compatibility draining. | Priority ownership, legal instant/ability windows, pass cycles, and all-pass resolution are unimplemented. |
| State-Based Actions | **YELLOW** | Legend and lethal-damage actions repeat until stable at represented engine boundaries. | Complete simultaneous SBA collection and the remaining CR 704 actions require future priority boundaries. |
| Counters | **GREEN** | Typed counter maps persist on the object, combine through layer 7c, and reset on zone change; invalid state is invariant-rejected. | Additional counter semantics and +1/+1/−1/−1 annihilation extend the same state. |
| Continuous Effects | **YELLOW** | Printed values remain immutable; typed set/add/switch effects and existing modifiers are independently recomputed. | Game-wide affected-set queries, source-linked lifecycle, and non-P/T operations are absent. |
| Layers | **GREEN** | Represented P/T effects order by layer/sublayer, dependency, and timestamp; reverse insertion, dependency, cycle, operation, and zone-reset tests pass. | Other CR 613 characteristics, automatic dependency discovery, and multi-object affected sets extend the evaluator. |
| Durations | **YELLOW** | Persistent and until-end-of-turn modifiers are distinct; EOT effects survive End Step and expire on Cleanup with marked damage. | End-of-combat, next-turn, conditional/source/attachment durations, delayed scheduling, and repeated cleanup are absent. |
| Attachments | **YELLOW** | No attachment semantics are silently modeled; identity, main-phase timing, cost, and layer foundations provide extension seams. | Attachment edges, Equip activation/targets, legality, detachment, effects, and SBAs are unimplemented. |
| Deterministic RNG | **GREEN** | One game-owned seeded stream persists, logs domain/result and state-chain digests, supports JSON state restore, matches legacy shuffle exactly, and is duplicate-replay stable. | New random Oracle operations must use this service; none were added for the audit. |
| Invariants | **YELLOW** | Zone uniqueness, registry identity, stack types, object state, layer graphs, counters, and RNG chains are checked and adversarially tested. | Global conservation, every-transaction checking, versioned options, encapsulation, and broader causal validation remain incomplete. |
| Rules Engine ↔ Card Interpreter ↔ Pilot separation | **GREEN** | Engine owns state/options/revalidation/mutation; interpreter is pure Oracle-pattern construction; pilots receive frozen views and select engine options; runner calls only engine transitions/actions. | Preserve the boundary as more choices, effects, and Oracle constructs are represented. |

Later 0.8d–0.8h changes do not invalidate earlier GREEN findings: every earlier boundary suite was
included in the 85-test focused run and the 179-test full run.

## Identity, zone, separation, turn, and combat regressions

The original equal-valued-object exploit is closed. Executable adversarial coverage rejects a
fabricated attacker, blocker, target, movement request, action option, stack occupant, trigger
ability, and payment plan. Two equal `CardFact` definitions produce distinct registered runtime
objects. Stale references cannot bind to zone-change replacements. Invariants reject duplicate-zone
occupation and aliased/unregistered objects. Failed movement and payment transactions leave zones,
identity allocation, cards, and tapped state coherent.

Zone changes preserve owner, reset nonbattlefield controller to owner, and create clean objects:
counters, temporary effects, characteristic effects, damage, tap state, and stale identity do not
follow. Control changes move the same battlefield object while preserving ownership.

The rules engine generates and revalidates immutable `ActionOption` values and owns mutation. The
interpreter derives generic constructs from normalized Oracle text and has no game/pilot state. The
pilot contains strategy only and cannot legalize fabricated options or mutate frozen views. The
Acceptance runner loads authoritative facts/decks, requests legal options, submits selections, and
uses engine-owned turn/combat methods; it does not assign authoritative state or mutate zones.

The represented sequence is Setup→Untap→Upkeep→Draw→Precombat Main→Beginning of Combat→Declare
Attackers→Declare Blockers→Combat Damage→End of Combat→Postcombat Main→End Step→Cleanup. Tests prove
rotation, the starting-player draw exception, active-player untap, land reset, summoning sickness,
step-specific attack/block/damage, cleanup expiration, marked-damage clearing, and combat reset.
Broader combat remains absent and documented, not approximated.

## Stack, cost, trigger, layer, and RNG findings

The five post-0.8c former REDs are architectural implementations rather than documentation-only
claims:

- **Stack:** `announce_spell()` validates and commits Hand→Stack through `move_object()`;
  `resolve_top_of_stack()` requires the authoritative top object and moves represented permanent or
  nonpermanent spells to the correct destination. New identities are created at every zone change.
- **Costs:** `ManaRequirement` and `PaymentPlan` separate calculation from commitment. The plan is
  revalidated, sources are authoritative IDs, taps roll back on movement failure, and unsupported
  symbols never pay or move.
- **Triggers:** typed `RulesEvent`, `TriggerInstance`, `TriggerEffect`, and
  `TriggeredAbilityObject` values separate detection, queueing, stack placement, and resolution.
  Oracle-pattern dispatch—not card-name dispatch—selects represented behavior. Immediate draining
  is explicitly the YELLOW Priority compatibility boundary.
- **Layers:** printed characteristics are immutable inputs. Counters, legacy modifiers, and typed
  characteristic effects are recomputed through ordered P/T sublayers with timestamps and declared
  dependencies; invalid graphs fail before state corruption.
- **Deterministic RNG:** `Game` retains the sole `DeterministicRNG`; opening shuffles and future
  bounded draws consume its explicit state. Sequence/domain/result and before/after digests are
  auditable, and serialized state resumes exactly.

## Card-name and silent-approximation audit

No prohibited card-name semantic dispatch or silent approximation was found.

Every suspicious occurrence was classified as follows:

- `AcceptancePilot` checks **Manhole Missile** and **Make Your Move** to preserve Acceptance Match
  strategy. This is category C, a pilot-only compatibility strategy; legality and effects remain
  engine/interpreter-owned.
- `_mana_color()` contains a five-basic-land name fallback after first parsing “Add {color}” from
  Oracle text. This is category A/C: a standard basic-land fact and compatibility path for minimal
  test fixtures with empty Oracle text. It does not dispatch card effects, and production catalog
  lands are authoritative.
- Legend-rule grouping uses permanent names because same-name grouping is the represented rules
  predicate. This is category B, generic rules behavior, not named-card dispatch.
- Remaining `.card.name` uses are telemetry, display, snapshots, deterministic ordering, or source
  attribution. They do not choose semantics.
- The runner's Leonardo/Raphael deck paths and player names identify Acceptance Match #001 only.
  They do not provide card facts or bypass engine actions.
- Test fixture names and `HISTORICAL_ACCEPTANCE_PT` are category C historical/regression evidence;
  production modules do not import them.

Unsupported spells, keywords, Oracle fragments, target states, mana symbols, modal branches, and
priority/trigger breadth either reject without mutation or emit explicit unsupported telemetry.
No TODO/comment was found whose runtime fallback contradicts claimed coverage.

## Acceptance Match #001 reproducibility

Each seed was executed twice into temporary files. Duplicate JSON snapshots were byte-identical.

| Seed | Winner / ending turn | Unsupported events / exact pairs | Block rejections | Invariant violations | Final stack |
| ---: | --- | ---: | ---: | ---: | ---: |
| 7001 | Raphael / 16 | 14 / 13 | 0 | 0 | 0 |
| 7002 | Leonardo / 17 | 14 / 8 | 2 | 0 | 0 |
| 7003 | Leonardo / 17 | 19 / 13 | 0 | 0 | 0 |
| 7004 | Leonardo / 21 | 21 / 18 | 1 | 0 | 0 |
| 7005 | Raphael / 16 | 13 / 8 | 3 | 0 | 0 |
| **Aggregate** | expected trajectories | **81 / 23** | **6** | **0** | **0** |

These trajectories are deterministic execution evidence, not balance evidence.

## Validation results

- focused Engine 0.7/0.8 identity, boundary, turn, stack, cost, trigger, layer, and RNG suites:
  **85 passed**;
- focused authoritative card-data suite: **5 passed**;
- full suite: **179 passed, 1 skipped**;
- Ruff format: clean (122 files already formatted);
- Ruff check: clean;
- `git diff --check`: clean before the report was created;
- canonical retired-terminology scan: clean;
- tracked-text mojibake scan: clean;
- temporary live card audit and production snapshot regeneration: passed;
- deterministic Acceptance Match duplicate replay: passed for all five seeds;
- GitHub Actions: two test jobs passed.

The one skipped test is the established opt-in live-endpoint validation in
`tests/test_scryfall.py` (`TMNT_SCRYFALL_SMOKE=1`); the full-suite count exactly matches the expected
179/1 gate.

## PR #27 diff classification

| Classification | Files | Finding |
| --- | ---: | --- |
| Expected engine/interpreter/pilot changes | 4 | `engine07.py`, `card_data.py`, `card_interpreter07.py`, and `pilot07.py`; all in scope. |
| Card-data foundation | 2 | Normalized snapshot and checksum/count manifest; exact production regeneration passed. |
| Tests | 9 | Card-data, Engine 0.7, and Engine 0.8b–0.8h executable evidence. |
| Acceptance/data tooling | 3 | Acceptance runner plus Scryfall audit/build scripts; no deck mutation. |
| Foundation/evidence documentation | 6 | Matrix, card-data/rules/Scryfall evidence, and the bounded engine overview. |
| Repository hygiene | 1 | `.deps/` ignore entry only. |
| Historical evidence preservation | 0 changed | Engine 0.1–0.6 records and Engine 0.6 model are preserved on the base. |
| Deck/prototype/calibration/smoke changes | 0 | No changed files; no Prototype 0.3 exists. |
| Unexpected or unrelated | 0 | None found. |

## Blockers

None.

## Final recommendation

**ACCEPT**

Engine 0.8 foundation is suitable to become the new Cardcade architectural baseline and PR #27 is
eligible for merge.
