# Cardcade Engine Foundation Matrix

Re-audit date: 2026-08-13 EDT

Committed baseline: `4a8c17b` (pre-0.8a Foundation Matrix)

Candidate under review: uncommitted Engine 0.8a working tree

Rules basis: [Magic Comprehensive Rules, effective June 19, 2026](https://media.wizards.com/2026/downloads/MagicCompRules%2020260619.pdf)

Primary references: [Wizards rules index](https://magic.wizards.com/en/rules),
[TMNT rules update bulletin](https://magic.wizards.com/en/news/announcements/teenage-mutant-ninja-turtles-update-bulletin),
[TMNT release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes),
and the committed [authoritative snapshot manifest](../../cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json).

## Audit boundary and method

This is an evidence-only re-audit. Engine 0.8a was not modified or committed. The assessment compares:

1. current Comprehensive Rules (CR), especially CR 109 and 400.7 for objects and zone changes;
2. the checksum-verified TMT/PZA/TMC foundation: 472 prints, **332 unique Oracle objects**, and
   **102 unique cards / 600 resolved slots** in the ten frozen decks;
3. committed pre-0.8a code and findings at `4a8c17b`;
4. the actual uncommitted `engine07.py` and `test_engine07.py` candidate; and
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
| **POST-0.8a candidate** | **3** | **8** | **9** | **0** |

Two RED classifications are resolved: Object Identity becomes GREEN and Zones becomes YELLOW.
No dependent row was upgraded merely because it now has object IDs available.

## Reconciled 20-row matrix

| Foundation row | Previous | Current | Current CR/pool/code/test evidence | Remaining rework risk |
| --- | :---: | :---: | --- | --- |
| Card Data / Oracle | **GREEN** | **GREEN** | CR 108.1 makes Oracle authoritative; CR 200–208 defines characteristics/faces. `card_data.py` still verifies 472 prints / 332 Oracle objects, exposes the normalized characteristics/identifiers/legalities, and resolves all 600 slots. `test_card_data.py` remains green. | Extend the authoritative interface as more characteristics enter play; do not add parallel card-fact tables. |
| Object Identity | **RED** | **GREEN** | CR 109 and 400.7 require identity independent of equal characteristics. `CardObject` and `Permanent` use `eq=False`, deterministic `object-NNNNNN` IDs, and an identity-valued registry. The exact old exploit now raises `illegal attacker` with life/tap state unchanged. Spoofed-ID attackers, blockers, targets, movement requests, counters, and P/T effects fail registry-plus-identity checks. Two copies of one `CardFact` remain distinct and reproducible. | Future tokens, copies, merged permanents, face-down objects, last-known information, and explicit CR 400.7 exceptions must use this identity service. Those are extensions, not replacement of the model. |
| Zones | **RED** | **YELLOW** | CR 400–408 and 400.7 require authoritative membership and normally a new object after movement. Library, hand, battlefield, and graveyard now contain registered runtime objects. `move_object()` validates registry/source/exactly-one-zone/destination before mutation, creates a new ID, preserves owner, resets nonbattlefield controller to owner, and emits `zone_changed`. Draw, land play, creature resolution, named spell resolution, destroy, and graveyard movement use it. Tests cover duplicate occupancy, invalid atomic movement, battlefield→hand→battlefield, and owner/controller transitions. | Stack/exile/command do not exist; same-zone ordering and CR exceptions are unsupported. Zone lists remain directly reachable Python collections, although invariants reject unauthorized aliasing. Encapsulate collections and add the missing zones as later foundations. |
| Turn Structure | **RED** | **RED** | CR 500–514 still requires explicit phases/steps. `phase` remains a string; `begin_turn`, monolithic `combat`, and `end_turn` still skip priority-bearing upkeep/draw/combat/end-step structure needed by Sneak and Disappear. 0.8a did not change this. | Replace string-led control flow with a phase/step machine and turn-based action scheduler. |
| Combat State | **RED** | **RED** | CR 506–511 requires persistent attacking/blocking state, defenders, blocked status, multiple blockers, damage order, and windows. 0.8a correctly changes attacker/block-map references from value/process identity to runtime IDs and rejects fabricated participants before mutation. Combat remains one method with one blocker per attacker and no persistent combat object. | Add a combat-state object over the new IDs; decompose declaration, blockers, damage, and step transitions. |
| Costs | **RED** | **RED** | CR 118 and 601.2f–h still require total-cost construction and atomic payment. `can_afford`, `_pay`, and direct `cast` resolution remain. Sneak alternative/nonmana cost and Equip activation cannot be represented. Zone transactions do not make casting transactional. | Add typed cost/cast/activation proposals and commit payment plus stack movement atomically. |
| Choices vs Targets | **YELLOW** | **YELLOW** | CR 115 and 601.2b–d distinguish targets from resolution choices. 0.8a now proves current battlefield targets are authoritative live runtime objects, so a fabricated equal target cannot resolve or spend resources. Callbacks/ad hoc target parameters still lack typed requests, locked targets, optional choices, division, and resolution revalidation. | Build typed choice/target records on the identity foundation and eventually store them on stack objects. |
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
| Invariants | **YELLOW** | **YELLOW** | 0.8a adds registry uniqueness, exactly-one-zone membership, container/zone agreement, registered-object identity, owner/controller placement, nonbattlefield controller reset, future-entry timestamp checks, and former-object exclusion. Adversarial duplicate-zone and spoofed-object tests pass. Global card conservation, transaction checks at every boundary, stack/priority/event causality, attachments, and richer combat invariants remain absent. | Extend the registry invariants to conservation and future subsystems; encapsulate zone collections so invalid intermediate states cannot be manually constructed. |
| Rules Engine ↔ Card Interpreter ↔ Pilot separation | **RED** | **RED** | Runtime-object and movement authority appropriately live in `Game`, but `Game` still also parses Oracle regexes and dispatches named cards; the runner still owns card-name pilot branches and can request automatic blockers inside combat. 0.8a did not address this RED. | Introduce typed ability/effect IR; Rules Engine executes legal typed actions, Card Interpreter supplies programs, and Pilot only selects legal actions/choices. |

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

All other rows retain their classifications. Identity-sensitive evidence improved Combat, Choices /
Targets, Events, SBAs, Counters, Continuous Effects, Durations, Attachments, and Invariants, but their
independent missing architecture remains.

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

## Architectural probes after 0.8a

- **Sneak:** owner-aware return and a distinct recast/attacking object now have a sound identity/zone
  base. Stack presence, alternative/nonmana cost, priority in declare blockers, and enters-attacking
  combat state remain RED dependencies.
- **Negate:** a future target can safely reference a specific runtime stack object, but stack,
  priority, casting transactions, target locking, and countering remain absent.
- **Alliance:** runtime source/target identity is sound; immediate regex execution still violates
  CR 603/117.5 sequencing and APNAP/stack requirements.
- **Equipment:** attachment edges can now safely use object IDs and will not rebind after movement.
  Equipment casting, Equip activation/cost/timing, layers, detachment, and SBAs remain missing.
- **Mutagen:** token instances and sacrifice targets can build on runtime IDs and zone transactions.
  Token definitions/lifecycle, activated costs, sorcery timing, sacrifice, targeting, and applicable
  SBAs remain missing.
- **Disappear:** deterministic zone-change records now identify old/new objects and controller/owner
  context. They are audit logs, not yet typed trigger events with last-known information/history.

## Decision answers

1. **Is the fabricated-object exploit fixed?** Yes; exact replay and expanded variants reject it.
2. **Is runtime identity authoritative rather than value equality?** Yes; `eq=False`, deterministic
   IDs, registry identity, and exact zone membership jointly establish authority.
3. **Are supported zone movements transactional?** Yes for the represented gameplay paths: all
   domain validation precedes mutation and invalid attempts leave containers/ID allocation unchanged.
4. **Is new-object behavior structurally correct?** Yes for represented state and supported zones;
   unsupported CR exceptions are explicitly outside scope.
5. **Object Identity classification?** **GREEN**, previously RED.
6. **Zones classification?** **YELLOW**, previously RED; missing zones/encapsulation prevent GREEN.
7. **Which other classifications changed?** None. Several gained positive evidence only.
8. **How many REDs remain?** **9**.
9. **Highest-priority remaining RED?** **Rules Engine ↔ Card Interpreter ↔ Pilot separation**. It
   should precede new action families so stack/turn/cost/event work does not deepen monolithic parsing
   and named-card dispatch.
10. **Proceed to the next architectural correction?** Yes. Evidence supports banking 0.8a, then
    correcting the engine/interpreter/pilot boundary as a separate checkpoint. It does not support
    implementing another card Action first.

## Remaining RED priority

1. Rules Engine ↔ Card Interpreter ↔ Pilot separation.
2. Explicit turn/combat state plus priority and stack kernel.
3. Transactional casting, activation, and typed costs.
4. Typed events and CR 117.5-compliant trigger queue.
5. Layered characteristic evaluation.
6. Persistent deterministic RNG service.

Turn/Combat, Stack, and Priority remain separately classified RED rows even though their corrections
form a coupled kernel. Identity/zone work is no longer on this RED list.

## Acceptance and validation evidence

Acceptance gameplay summaries are unchanged from Engine 0.7g; unsupported telemetry remains **81
events / 23 exact fragment pairs**.

| Seed | Winner / ending turn | Unsupported events / limitation pairs | Candidate deterministic SHA-256 |
| --- | --- | --- | --- |
| 7001 | Raphael / 16 | 14 / 13 | `e9a945ce2e92d96a18893e6b102fce3687be0d3b941199497a88105d2f317edc` |
| 7002 | Leonardo / 17 | 14 / 8 | `1e68173db17c41a3e2e7c638e51c5a4ca908b3aef8f63478a7a3e04acfe5802d` |
| 7003 | Leonardo / 17 | 19 / 13 | `1335f33ac6b00bb315c113f1560ee9eb9faf706e4ba4a391df651b1e52f35cb8` |
| 7004 | Leonardo / 21 | 21 / 18 | `4b618e25e21de1759b81a855c6bcfcdcc28973fd3b53cc7a75f195221bb09df4` |
| 7005 | Raphael / 16 | 13 / 8 | `1d34a34fe9e3164becbebec1a2a2e161fa013a35117970e28833dbd6d74b9533` |

Candidate snapshots are intentionally not byte-equal to pre-0.8a snapshots: engine version,
deterministic runtime IDs, new battlefield identity fields, and 56/60/65/73/59 `zone_changed`
records are new architectural evidence. Duplicate candidate runs are byte-identical. Winners,
ending turns, unsupported counts, limitation-pair counts, life/combat execution, and pilot decisions
are unchanged; this is not balance evidence.

Validation at audit time:

- adversarial identity/zone selection: 10 passed;
- full suite: 132 passed, 1 skipped;
- Ruff format: clean;
- Ruff check: clean;
- `git diff --check`: clean;
- deterministic duplicate acceptance seeds 7001–7005: exact matches per seed;
- authoritative card-data tests: included in the passing full suite.

## Governance boundary

This re-audit changes only this document. Candidate Engine 0.8a code/tests remain uncommitted and
unmodified by the audit. No Action, Draw/Discard/Selection, stack, priority, trigger system, deck,
prototype, historical evidence, calibration, or 900-game smoke was added or changed.
