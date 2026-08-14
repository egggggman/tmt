# Cardcade Engine Foundation Matrix

Re-audit date: 2026-08-13 EDT

Committed baseline: `78b66f2` (validated post-0.8a Foundation Matrix)

Candidate under review: uncommitted Engine 0.8b working tree

Rules basis: [Magic Comprehensive Rules, effective June 19, 2026](https://media.wizards.com/2026/downloads/MagicCompRules%2020260619.pdf)

Primary references: [Wizards rules index](https://magic.wizards.com/en/rules),
[TMNT rules update bulletin](https://magic.wizards.com/en/news/announcements/teenage-mutant-ninja-turtles-update-bulletin),
[TMNT release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes),
and the committed [authoritative snapshot manifest](../../cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json).

## Audit boundary and method

This is an evidence-only re-audit. Engine 0.8b was not modified or committed. The assessment compares:

1. current Comprehensive Rules (CR), especially CR 109 and 400.7 for objects and zone changes;
2. the checksum-verified TMT/PZA/TMC foundation: 472 prints, **332 unique Oracle objects**, and
   **102 unique cards / 600 resolved slots** in the ten frozen decks;
3. committed post-0.8a code and findings at `78b66f2`;
4. the actual uncommitted `engine07.py`, interpreter, pilot, runner, and boundary tests; and
5. executable adversarial tests, the full suite, and Acceptance Match #001 seeds 7001–7005.

Status means:

- **GREEN** — correct for the declared scope and demonstrated to provide a clean extension path;
- **YELLOW** — incomplete, but extensible without significant rework to the represented foundation;
- **RED** — current representation/control flow conflicts with required future behavior;
- **UNKNOWN** — evidence is insufficient. Unsupported alone is not RED.

Pool pressure remains unchanged. Across the 332 Oracle objects / 102 roster cards respectively are
26 / 17 Sneak cards, 10 / 6 Alliance cards, 15 / 6 Equipment cards, 19 / 10 Mutagen references,
9 / 4 Disappear cards, and one / one Negate.

## Classification progression

| Audit | GREEN | YELLOW | RED | UNKNOWN |
| --- | ---: | ---: | ---: | ---: |
| **PRE-0.8a (`4a8c17b`)** | **2** | **7** | **11** | **0** |
| **POST-0.8a (`78b66f2`)** | **3** | **8** | **9** | **0** |
| **POST-0.8b candidate** | **4** | **8** | **8** | **0** |

Across the two checkpoints, Object Identity became GREEN, Zones became YELLOW, and Rules Engine ↔
Card Interpreter ↔ Pilot separation became GREEN. No dependent row was upgraded automatically.

## Reconciled 20-row matrix

| Foundation row | Post-0.8a | Post-0.8b candidate | Current CR/pool/code/test evidence | Remaining rework risk |
| --- | :---: | :---: | --- | --- |
| Card Data / Oracle | **GREEN** | **GREEN** | CR 108.1 makes Oracle authoritative; CR 200–208 defines characteristics/faces. `card_data.py` still verifies 472 prints / 332 Oracle objects, exposes the normalized characteristics/identifiers/legalities, and resolves all 600 slots. `test_card_data.py` remains green. | Extend the authoritative interface as more characteristics enter play; do not add parallel card-fact tables. |
| Object Identity | **GREEN** | **GREEN** | CR 109 and 400.7 require identity independent of equal characteristics. `CardObject` and `Permanent` use `eq=False`, deterministic `object-NNNNNN` IDs, and an identity-valued registry. 0.8b action options carry IDs only; fabricated IDs/options are revalidated and rejected. The original exploit and 0.8a adversarial identity tests still pass. | Future tokens, copies, merged permanents, face-down objects, last-known information, and explicit CR 400.7 exceptions must use this identity service. Those are extensions, not replacement of the model. |
| Zones | **YELLOW** | **YELLOW** | CR 400–408 and 400.7 require authoritative membership and normally a new object after movement. Library, hand, battlefield, and graveyard contain registered objects and supported movement uses `move_object()`. Pilots receive tuple views, not the mutable zone lists, and the acceptance runner no longer reads them. Existing transactional/new-object tests pass. | Stack/exile/command, same-zone ordering, CR exceptions, and encapsulated internal collections remain absent. Internal engine/tests can still reach lists directly, so GREEN is not justified. |
| Turn Structure | **RED** | **RED** | CR 500–514 still requires explicit phases/steps. `phase` remains a string; `begin_turn`, monolithic `combat`, and `end_turn` still skip priority-bearing upkeep/draw/combat/end-step structure needed by Sneak and Disappear. 0.8a did not change this. | Replace string-led control flow with a phase/step machine and turn-based action scheduler. |
| Combat State | **RED** | **RED** | CR 506–511 requires persistent attacking/blocking state, defenders, blocked status, multiple blockers, damage order, and windows. 0.8b exposes immutable attack/block options and revalidates participant IDs; a fabricated attack cannot tap anything. Combat remains one monolithic method with one blocker per attacker and no persistent combat object. | Add a combat-state object over the new IDs; decompose declaration, blockers, damage, and step transitions. |
| Costs | **RED** | **RED** | CR 118 and 601.2f–h still require total-cost construction and atomic payment. `can_afford`, `_pay`, and direct `cast` resolution remain. Sneak alternative/nonmana cost and Equip activation cannot be represented. Zone transactions do not make casting transactional. | Add typed cost/cast/activation proposals and commit payment plus stack movement atomically. |
| Choices vs Targets | **YELLOW** | **YELLOW** | CR 115 and 601.2b–d distinguish targets from resolution choices. `ActionOption` now carries immutable target IDs, legal options are engine-generated, and stale/fabricated targets are revalidated before mutation. Legend/counter/Alliance hooks receive immutable IDs/strings. General target locking, optional choices, division, modes, and resolution-time revalidation remain absent. | Generalize the option record into typed target/choice requests and eventually store locked targets on stack objects. |
| Events | **YELLOW** | **YELLOW** | Zone and control changes now emit deterministic records containing old/new object IDs, owner, zones, and reason. This materially improves Disappear/last-known-information groundwork. `Game.log` is still passive telemetry, not a typed authoritative event stream with simultaneity, source/cause chains, replacements, or last-known information. | Project transactional mutations into typed events; retain logs as an audit view rather than rules input. |
| Triggers | **RED** | **RED** | CR 603 and 117.5 still require event detection, SBA checks, pending triggers, APNAP ordering, stack placement, then resolution. Alliance/attack/ETB regex handlers still execute immediately. Identity makes moved-source references possible but does not repair sequencing. | Replace immediate resolver hooks with trigger instances, pending queues, last-known information, APNAP ordering, and stack resolution. |
| Stack | **RED** | **RED** | CR 112.1 and 405 require spell/ability stack objects. No stack zone exists; `move_object` deliberately supports only library/hand/battlefield/graveyard. Negate remains honestly unsupported and direct spell branches bypass a stack. | Add stack objects and hand→stack→destination transactions; split announcement/payment from resolution/countering. |
| Priority | **RED** | **RED** | CR 117 requires action windows, pass sequences, and all-pass resolution. No priority player or pass state exists. Runtime IDs do not change Sneak's need for declare-blockers priority. | Integrate priority/APNAP with the future step machine and stack. |
| State-Based Actions | **YELLOW** | **YELLOW** | CR 704 and 117.5 require simultaneous applicable SBAs at priority boundaries. Legend/lethal registry entries and repeat-until-stable behavior remain. 0.8a ensures graveyard transitions create the correct new owner-zone object and stale battlefield identities cease being authoritative. Checks remain narrow, sequential, and manually invoked. | Collect/apply simultaneous SBA batches at priority boundaries; add zero toughness, token cleanup, illegal attachments, counter annihilation, and other applicable cases. |
| Counters | **GREEN** | **GREEN** | CR 122 puts counters on objects, not card definitions. Existing separation of printed P/T, counters, and modifiers remains. New tests now prove counters stay on the former object and the new incarnation has none; fabricated targets cannot receive counters. Existing accumulation/persistence/P/T tests still pass. | Add counter-type semantics and the +1/+1/−1/−1 SBA; finality still depends on replacement/exile support. |
| Continuous Effects | **YELLOW** | **YELLOW** | CR 611–613 governs continuous effects. 0.8a proves temporary/persistent modifier records do not migrate to a new object and stale references do not bind by equal value. The represented additive P/T subset is still sound, but effects remain stored on targets and static sources are regex-rescanned. | Create independent effect instances keyed to runtime IDs with affected-set queries, source/LKI, timestamps, dependencies, and characteristic operations. |
| Layers | **RED** | **RED** | CR 613 still requires ordered layers/sub-layers, timestamps, and dependencies. Derived P/T remains `printed + counter delta + summed modifiers`; 0.8a changes identity, not characteristic evaluation. | Replace direct arithmetic with a layer pipeline before Equipment/base-setting/type/copy effects. |
| Durations | **YELLOW** | **YELLOW** | CR 611.2a and 514.2 govern effect duration and cleanup. Existing persistent/EOT expiration tests pass; 0.8a additionally proves no duration follows a new object. End-of-combat, next-turn, conditional, source-linked, and attachment lifetimes remain absent. | Generalize duration predicates on independent effect instances while retaining cleanup expiration. |
| Attachments | **YELLOW** | **YELLOW** | CR 301.5, 303.4, 701.3, and 704.5m–n require identity-based attachment relations. No Equipment/attachment behavior was added. A regression demonstrates a reference keyed to an old object ID cannot silently address its new incarnation, removing the prior equality hazard. | Add attachment edges over runtime IDs, attach legality, Equip cost/timing, detachment on zone change, continuous effects, and attachment SBAs. |
| Deterministic RNG | **RED** | **RED** | CR 103.3/701.20 random operations still need one auditable stream. Runtime identity allocation is deterministic and duplicate candidate runs are identical, but `random.Random(seed)` is still discarded after initial shuffles. Casey Jones-style random ordering remains structurally unsafe to add locally. | Retain a game-owned RNG service, log consumption, and serialize/replay its position or decisions. |
| Invariants | **YELLOW** | **YELLOW** | 0.8a registry/zone invariants remain intact. 0.8b adds option revalidation and immutable pilot views; stale, illegal, fabricated-target, and fabricated-combat options fail without mutation. Global card conservation, checks at every transaction boundary, stack/priority/event causality, attachments, and richer combat invariants remain absent. | Extend invariants to conservation and future subsystems; encapsulate zone collections and formalize option/version invalidation. |
| Rules Engine ↔ Card Interpreter ↔ Pilot separation | **RED** | **GREEN** | CR 601/608 separates legal procedure from card instructions and player choices. `Game` owns state, legal option generation, costs/targets/combat/SBAs currently represented, revalidation, and mutation. `CardInterpreter` is pure: it derives frozen cast programs and reusable Oracle matches without game state or Pilot dependencies, including an Oracle-derived renamed-card probe. Pilots receive frozen `GameView`/`ActionOption` values and only select options; the runner no longer reads `game.players` or calls mutation methods. Eleven adversarial tests plus stale/fabricated probes pass. | Extend the same boundary to future typed costs, triggers, stack objects, priority choices, and effects. Current trigger-like execution inside `Game` is rules execution over interpreter constructs, not strategy/interpretation coupling; its timing defect remains classified under Triggers/Stack/Priority. |

No row is UNKNOWN: current rules, the authoritative pool, committed history, candidate code, and
executable tests are sufficient for all requested classifications.

## Classification changelog

### Object Identity: RED → GREEN

The original conflict is removed rather than patched at combat. Identity is now non-value runtime
identity, registry lookups require the exact Python object for its deterministic ID, every supported
zone change creates another ID, and legality/effect entry points validate authoritative battlefield
membership. The original fabricated-object attack and expanded attacker/blocker/target/movement
variants are rejected without state mutation.

### Zones: RED → YELLOW

All currently supported gameplay movement uses one validate-then-commit path, preserves owner,
establishes destination controller, creates the CR 400.7 new object, resets runtime state, and logs
old/new identities. It is not GREEN because stack/exile/command and same-zone ordering are absent,
zone collections are not encapsulated, and CR 400.7 exceptions are not modeled.

### Rules Engine ↔ Card Interpreter ↔ Pilot separation: RED → GREEN

The previous conflict is removed for the represented rules surface. `Game` generates immutable
legal options, revalidates selected IDs against current authoritative state, and alone executes
mutation. `CardInterpreter` derives frozen constructs and Oracle-pattern matches without access to a
game or pilot. `AcceptancePilot` and `PassingPilot` receive only frozen views/options. The runner no
longer inspects mutable zones or calls `play_land`, `cast`, or `combat` directly. Fabricated/stale
options, IDs, targets, attackers, and blocks fail before mutation; a deliberately poor PASS/no-attack
choice remains legal.

The trigger-like handlers in `Game` do not keep this row RED. They perform rules execution while
querying interpreter-owned constructs, and chooser hooks expose IDs/strings rather than mutable
objects. Their immediate execution, missing APNAP ordering, and lack of a stack are independent
conflicts already classified RED under Triggers, Stack, and Priority.

All other rows retain their post-0.8a classifications. Options and immutable views improve evidence
for Combat, Choices / Targets, and Invariants, but do not supply their missing rules architecture.

## Cross-system and adversarial evidence

| Probe | Candidate result | Conclusion |
| --- | --- | --- |
| Original fabricated attacker | Spoofed equal-valued `Permanent` raises `illegal attacker`; defender remains at 20; real/fake remain untapped. | Original exploit fixed. |
| Same card definition × two objects | Runtime instances have different IDs, identity inequality, and reproducible sequences across equal seeds. | Card definition and game object are separated. |
| Fabricated blocker / target | Spoofed blocker is rejected before attacker tap; spoofed Manhole Missile target leaves card and mana unspent. | Combat and current targeting use authoritative identity. |
| Invalid / duplicate-zone movement | Unregistered movement consumes no ID and changes no container; duplicate occupancy makes the invariant and transaction fail. | Supported movement validates before mutation. |
| Owner × controller × graveyard | Control moves the same object without changing owner; battlefield→graveyard creates a new owner-zone object controlled by owner. | Owner/controller distinction is structurally correct for supported paths. |
| New object × counters/effects/damage/tap | Battlefield→hand→battlefield changes ID each time; new permanent has no counters/modifiers/damage/tap state and has a new entry turn/summoning state. | General CR 400.7 reset behavior is correct for represented state. |
| Old reference × new incarnation | Old and intermediate objects become `former`; registry checks reject them and old-ID reference maps do not match the new ID. | Equal characteristics cannot silently rebind stale references. |
| Counter/P/T/evasion/SBA regressions | Existing counter accumulation, cleanup, derived P/T, blocking legality, legend, and lethal tests pass. | Identity migration did not break represented cross-system behavior. |
| Fabricated/stale ActionOption | Unknown IDs, illegal target IDs, fabricated attackers, and replayed stale cast options are rejected without mutation. | Pilot selection cannot override current engine legality. |
| Immutable pilot view | Frozen dataclasses and nested tuples reject field/item mutation and expose no `players` collection. | Pilot API does not expose authoritative mutable objects. |
| Strategy swap × legality | Acceptance and deliberately passing pilots select differently from the same option tuple; option generation remains identical. | Poor strategy is legal, but strategy cannot define legality. |
| Interpreter × strategy/state | Renamed-card Oracle probe yields the same cast construct; interpreter has no Pilot, players, zones, or mutation access. | Card semantics are interpreter-owned and strategy-independent. |
| Choice hooks × mutable objects | Legend/counter/Alliance hooks receive object IDs or strings; engine resolves and validates the response. | Rules choices no longer leak mutable permanents. |
| Acceptance runner × state authority | Static inspection finds no `game.players`, direct cast/land/combat call, or zone-list mutation. | Acceptance Pilot operates only through legal-option APIs. |
| Alliance × legend SBA | Immediate Alliance effect still precedes legend processing. | Trigger RED remains. |
| Negate × stack | No stack object/zone; Negate remains unsupported. | Stack/Priority REDs remain. |
| Equipment × attachment | Old IDs are safe reference keys, but no attachment/equip semantics exist. | Attachment remains YELLOW. |

## New-object behavior boundary

For supported movements, the source object ID becomes non-authoritative (`zone == "former"`) and a
new deterministic ID is registered in the destination. The immutable `CardFact` reference and owner
persist. Controller persists only while control changes on the same battlefield object; a
nonbattlefield incarnation is controlled by its owner, and a battlefield destination receives its
specified controller or owner by default. Counters, P/T modifiers, damage, tap state, and prior
battlefield-entry state reset. The new permanent receives a fresh battlefield-entry turn and
summoning-sickness state. Old references remain references to the former object and fail live-zone
checks. Unsupported CR 400.7 exceptions are not approximated.

## Architectural probes after 0.8b

- **Sneak:** owner-aware return and a distinct recast/attacking object now have a sound identity/zone
  base. Stack presence, alternative/nonmana cost, priority in declare blockers, and enters-attacking
  combat state remain RED dependencies.
- **Negate:** a future target can safely reference a specific runtime stack object, but stack,
  priority, casting transactions, target locking, and countering remain absent.
- **Alliance:** runtime source/target identity is sound; immediate regex execution still violates
  CR 603/117.5 sequencing and APNAP/stack requirements. Oracle recognition now belongs to the
  interpreter and ID-only choices return to the engine, so the remaining defect is Trigger/Stack,
  not Pilot coupling.
- **Equipment:** attachment edges can now safely use object IDs and will not rebind after movement.
  Equipment casting, Equip activation/cost/timing, layers, detachment, and SBAs remain missing.
- **Mutagen:** token instances and sacrifice targets can build on runtime IDs and zone transactions.
  Token definitions/lifecycle, activated costs, sorcery timing, sacrifice, targeting, and applicable
  SBAs remain missing.
- **Disappear:** deterministic zone-change records now identify old/new objects and controller/owner
  context. They are audit logs, not yet typed trigger events with last-known information/history.

## Decision answers

1. **Can a pilot make an illegal action legal?** No. Every selection is compared with freshly
   generated legal options and its IDs are resolved by the engine.
2. **Can a pilot directly mutate authoritative state?** Not through the Pilot contract: it receives
   frozen views/options only. Direct internal engine APIs still exist for rules/tests, not in Pilot.
3. **Can a pilot fabricate or replay objects/actions?** It can construct values, but fabricated and
   stale values are rejected before state mutation.
4. **Does the Card Interpreter depend on Pilot strategy or mutable state?** No; executable probes and
   static inspection show pure Oracle/card-definition input to frozen constructs.
5. **Do trigger-like handlers keep Separation RED?** No. Their remaining problem is incorrect trigger
   timing/stack behavior, already represented by the Triggers/Stack/Priority REDs.
6. **Separation classification?** **GREEN**, previously RED.
7. **Which other classifications changed in 0.8b?** None; Combat, Choices / Targets, and Invariants
   gained evidence but retain independent missing capabilities.
8. **How many REDs remain?** **8**.
9. **Highest-priority remaining RED?** **Turn Structure**, implemented together with the coupled
   Combat State / Priority / Stack kernel so real action windows and Sneak timing are representable.
10. **Proceed further now?** No in this checkpoint. First bank 0.8b and this re-audit separately.

## Remaining RED priority

1. Explicit turn/combat state plus priority and stack kernel (Turn Structure is the lead row).
2. Transactional casting, activation, and typed costs.
3. Typed events and CR 117.5-compliant trigger queue.
4. Layered characteristic evaluation.
5. Persistent deterministic RNG service.

Turn/Combat, Stack, and Priority remain separately classified RED rows even though their corrections
form a coupled kernel. Identity/zone and separation work are no longer on this RED list.

## Acceptance and validation evidence

Acceptance gameplay summaries are unchanged from Engine 0.8a; unsupported telemetry remains **81
events / 23 exact fragment pairs**, and the six block-restriction rejections remain 0/2/0/1/3 by
seed.

| Seed | Winner / ending turn | Unsupported events / limitation pairs | Candidate deterministic SHA-256 |
| --- | --- | --- | --- |
| 7001 | Raphael / 16 | 14 / 13 | `7715193bf350c2b6c9b42633c35ccdc0830b9007bc89d6e5a5a8eb76b2c71f5b` |
| 7002 | Leonardo / 17 | 14 / 8 | `7bf1b90782522339f255fbdefa2dd14b874e805768db3aaecc6c1f3adac08811` |
| 7003 | Leonardo / 17 | 19 / 13 | `08d1b7c6f233b6b2a2171bf3ee7bc2985ee9d3742583605baf28723b0ef3a9fb` |
| 7004 | Leonardo / 21 | 21 / 18 | `8a65ada6e3e329f9fabf452f9df8a9481bb60377e5f2d104066346559236d6c4` |
| 7005 | Raphael / 16 | 13 / 8 | `409c9948e5e9e427f760dec26308d758882c61f72a24c5f394676902410271be` |

Candidate snapshots are intentionally not byte-equal to 0.8a because the engine version is
`cardcade-0.8.0-alpha.2`. Duplicate candidate runs are byte-identical. Winners, ending turns,
unsupported counts, limitation-pair counts, block-rejection evidence, and represented gameplay
execution are unchanged; there is no balance evidence here.

Validation at audit time:

- adversarial separation suite: 11 passed;
- extra stale/fabricated/view/interpreter probes: all passed;
- full suite: 143 passed, 1 skipped;
- Ruff format: clean;
- Ruff check: clean;
- `git diff --check`: clean;
- deterministic duplicate acceptance seeds 7001–7005: exact matches per seed;
- authoritative card-data tests: included in the passing full suite.

## Governance boundary

This re-audit changes only this document. Candidate Engine 0.8b code/tests remain uncommitted and
unmodified by the audit. No Action, Draw/Discard/Selection, stack, priority, trigger system, deck,
prototype, historical evidence, calibration, or 900-game smoke was added or changed.
