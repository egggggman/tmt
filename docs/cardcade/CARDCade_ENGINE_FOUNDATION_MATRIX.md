# Cardcade Engine Foundation Matrix

Re-audit date: 2026-08-13 EDT

Committed base: `04bb091` (validated post-0.8c Foundation Matrix)

Candidate under review: uncommitted Engine 0.8d Stack Foundation working tree

Rules basis: [Magic Comprehensive Rules, effective June 19, 2026](https://media.wizards.com/2026/downloads/MagicCompRules%2020260619.pdf)

Primary references: [Wizards rules index](https://magic.wizards.com/en/rules),
[TMNT rules update bulletin](https://magic.wizards.com/en/news/announcements/teenage-mutant-ninja-turtles-update-bulletin),
[TMNT release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes),
and the committed [authoritative snapshot manifest](../../cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json).

## Audit boundary and method

This is an evidence-only post-0.8d re-audit. The candidate implementation and tests were not
modified or committed. The only audit edit is this document. Assessment uses:

1. current CR 400.7, 405, 601.2, and 608 spell/stack lifecycle, with related CR 117 priority,
   603 triggers, 613 layers, and 701.20 randomness requirements;
2. the checksum-verified TMT/PZA/TMC pool: 472 prints, **332 unique Oracle objects**, and
   **102 unique cards / 600 resolved slots** in the ten frozen decks;
3. committed Engine 0.8c at `04bb091` versus the actual uncommitted 0.8d working tree;
4. static inspection of the rules engine, interpreter, pilot, and Acceptance Match runner;
5. independent adversarial probes, candidate tests, the full suite, and duplicate Acceptance Match
   #001 seeds 7001–7005.

Status means:

- **GREEN** — correct for the declared represented scope and demonstrated to have a clean extension
  path;
- **YELLOW** — incomplete, but extensible without significant rework to the represented foundation;
- **RED** — current representation or control flow conflicts with required future behavior;
- **UNKNOWN** — evidence is insufficient. Unsupported alone is not RED.

Pool pressure is unchanged. Across the 332 Oracle objects / 102 roster cards respectively are
26 / 17 Sneak cards, 10 / 6 Alliance cards, 15 / 6 Equipment cards, 19 / 10 Mutagen references,
9 / 4 Disappear cards, and one / one Negate.

## Classification progression

| Audit | GREEN | YELLOW | RED | UNKNOWN |
| --- | ---: | ---: | ---: | ---: |
| **Pre-0.8a (`4a8c17b`)** | **2** | **7** | **11** | **0** |
| **Post-0.8a** | **3** | **8** | **9** | **0** |
| **Post-0.8b (`6878369`)** | **4** | **8** | **8** | **0** |
| **Post-0.8c (`04bb091`)** | **5** | **10** | **5** | **0** |
| **Post-0.8d candidate** | **6** | **10** | **4** | **0** |

Engine 0.8d changes exactly one classification: Stack **RED → GREEN** for the represented spell
scope. No dependent row was upgraded automatically.

## Reconciled 20-row matrix

| Foundation row | Post-0.8c | Post-0.8d candidate | Current CR/pool/code/test evidence | Remaining rework risk |
| --- | :---: | :---: | --- | --- |
| Card Data / Oracle | **GREEN** | **GREEN** | CR 108.1 makes Oracle authoritative; CR 200–208 defines characteristics and faces. `card_data.py` still checksum-verifies 472 prints / 332 Oracle objects, exposes normalized facts and legalities, and resolves all 600 slots. Full data tests pass. | Extend the authoritative interface when more characteristics enter play; never add parallel hard-coded fact tables. |
| Object Identity | **GREEN** | **GREEN** | CR 109 and 400.7 identity remains registry-backed, non-value, and deterministic. Combat declarations now persist runtime IDs across three steps; stale/fabricated action IDs are revalidated. Identity and transactional-zone regressions pass. | Future tokens, copies, face-down objects, merged permanents, last-known information, and CR 400.7 exceptions must use the same service. |
| Zones | **YELLOW** | **YELLOW** | CR 400–408 now includes an authoritative shared Stack alongside library, hand, battlefield, and graveyard. All represented Hand→Stack→destination movement uses `move_object()` and CR 400.7 new identities. | Exile/command, same-zone ordering, CR exceptions, and encapsulated internal collections remain absent. |
| Turn Structure | **GREEN** | **GREEN** | The exact CR 500-series turn graph remains authoritative. `transition_to()` now also rejects advancement while a represented stack object is unresolved, so callers cannot skip resolution. Existing turn and cleanup regressions pass. | Priority-bearing windows, extra turns/phases, additional combat phases, simultaneous team turns, hand-size cleanup, and repeated cleanup remain future extensions. |
| Combat State | **YELLOW** | **YELLOW** | Staged CR 506–511 combat state is unchanged and its regressions pass. The spell lifecycle does not fabricate combat timing or add Sneak/enters-attacking behavior. | Defender choice, arbitrary attacker subsets, multiple blockers, blocking order, extra damage steps, trample assignment, planeswalkers/battles, and attack costs remain absent. |
| Costs | **RED** | **RED** | CR 118 and 601.2f–h still require constructed total costs and atomic payment. `announce_spell()` validates represented timing/targets before `_pay`, but mana tapping and Hand→Stack movement are not one rollback-capable transaction; only simple mana value/color is modeled. | Add typed cast/activation proposals, total-cost construction, ordered choices, mana abilities, additional/alternative costs, and atomic payment/rollback integrated with announcement. |
| Choices vs Targets | **YELLOW** | **YELLOW** | Represented targets are locked as immutable runtime IDs on `StackObject` and revalidated under CR 608.2b at resolution. Fabricated, friendly, stale, and power-ineligible targets are rejected or resolve with no effect as appropriate. | Add typed target/choice requests, modes, divisions, optional choices, multiple targets, partial legality, and resolution-time non-target choices. |
| Events | **YELLOW** | **YELLOW** | Deterministic `spell_cast`, Hand→Stack, Stack→destination, resolved, and all-targets-illegal telemetry now exposes the represented lifecycle. `Game.log` remains passive telemetry rather than a typed authoritative event stream with simultaneity, replacements, source/cause chains, or LKI. | Project transactions into typed events; do not use audit logs as rules input. |
| Triggers | **RED** | **RED** | CR 603 and 117.5 still require event detection, pending triggers after SBAs, APNAP ordering, stack placement, and resolution. Alliance/ETB/attack handlers still execute immediately inside mutation paths; adding a spell stack does not cure that conflict. | Replace immediate resolver calls with trigger instances, a pending queue, LKI, APNAP ordering, intervening-if checks, and ability-stack resolution. |
| Stack | **RED** | **GREEN** | CR 405/601.2a is now represented by registered `StackObject` instances in one ordered authoritative zone. Controller, immutable card facts, cast kind, and locked target ID are retained; Hand→Stack and Stack→Battlefield/Graveyard create new identities; only the top resolves LIFO; CR 608.2b target revalidation is tested. `cast()` is an explicit immediate-resolution adapter until Priority exists. | Activated/triggered ability objects, copies, face-down spells, characteristics modified on stack, countering, replacement destinations, split/Adventure cases, and complete casting steps remain unsupported extensions. The represented spell-stack foundation does not require replacement, so GREEN is scoped rather than comprehensive. |
| Priority | **YELLOW** | **YELLOW** | CR 117 priority ownership and all-pass sequencing remain unimplemented. The new `announce_spell()`/`resolve_top_of_stack()` split and unresolved-stack transition gate provide concrete controller seams, but `cast()` deliberately resolves immediately for compatibility. | Add APNAP priority ownership, legal instant/ability options, pass cycles, all-pass top resolution, and empty-stack step advancement. |
| State-Based Actions | **YELLOW** | **YELLOW** | CR 704/117.5 repeat-until-stable legend/lethal behavior remains. Cleanup and combat damage invoke represented SBA checks at deterministic engine boundaries, but no priority controller supplies every required boundary and checks remain narrow/sequential. | Collect simultaneous SBA batches at every future priority boundary; add zero toughness, counter annihilation, token cleanup, attachment SBAs, and other applicable cases. |
| Counters | **GREEN** | **GREEN** | CR 122 counter state remains separate from immutable printed P/T and modifiers. Turn-state migration preserves accumulation, persistence, derived P/T, zone reset, and SBA interactions. | Add more counter-type semantics and the +1/+1/−1/−1 SBA; finality depends on replacement/exile support. |
| Continuous Effects | **YELLOW** | **YELLOW** | CR 611–613 represented additive P/T effects remain sound. Engine-owned step context improves future duration predicates but does not add independent effect instances, affected-set queries, timestamps, dependencies, or non-P/T operations. | Build independent continuous-effect instances over runtime IDs and a characteristic-evaluation pipeline. |
| Layers | **RED** | **RED** | CR 613 still requires layers, sublayers, timestamps, and dependencies. `printed + counters + summed modifiers` is unchanged by turn state. Equipment/base-setting/type/copy effects would conflict with this evaluator. | Replace direct arithmetic with a layer pipeline. |
| Durations | **YELLOW** | **YELLOW** | CR 611.2a and 514.2 represented “until end of turn” semantics are now structurally stronger: effects survive through End Step and expire only on entry to engine-owned Cleanup; marked damage clears at the same boundary. Persistent modifiers survive. Independent probes and regressions verify no premature/late expiration. | End-of-combat, next-turn, “for as long as,” source-linked, attachment-linked, delayed, and conditional durations remain absent. Repeated cleanup under CR 514.3 requires the future trigger/priority loop. |
| Attachments | **YELLOW** | **YELLOW** | CR 301.5, 303.4, 701.3, and 704.5m–n remain unsupported but identity-safe. Main-phase state supplies the correct future sorcery-timing input for Equip; no attachment/equip semantics were added. | Add runtime-ID attachment edges, legality, typed Equip cost/activation, detachment, effects/layers, and attachment SBAs. |
| Deterministic RNG | **RED** | **RED** | CR 103.3/701.20 random operations still need a retained auditable stream. Turn progression and duplicate acceptance runs are deterministic, but `random.Random(seed)` is still discarded after shuffle. Casey Jones-style later randomness remains structurally unsafe. | Retain a game-owned RNG service, log consumption, and serialize/replay its state or decisions. |
| Invariants | **YELLOW** | **YELLOW** | Registry/zone/identity checks now include stack-only type, registration, zone, controller, cast-kind, and target-registration invariants. Adversarial tests reject fabricated stack occupants and unresolved-stack advancement. | Add global card conservation, checks at every transaction, option/state versioning, encapsulated collections, and subsystem causality. |
| Rules Engine ↔ Card Interpreter ↔ Pilot separation | **GREEN** | **GREEN** | `Game` alone owns stack storage, announcement legality, target revalidation, resolution, and mutation. `CardInterpreter` still supplies frozen strategy-free `CastProgram`; pilots still select immutable engine options and never receive mutable stack objects. | Preserve this boundary when priority choices, typed costs, ability objects, triggers, and effects are introduced. |

No row is UNKNOWN: current rules, authoritative data, committed history, candidate code, and executable
probes are sufficient for all twenty classifications.

## Classification changes

### Stack: RED → GREEN

The previous RED condition was structural: represented spells paid and resolved directly from hand,
so there was no spell object, shared ordered stack zone, top-object rule, announcement/resolution
boundary, or CR 400.7 identity transition. Engine 0.8d removes that representation. Every supported
spell is proposed as a registered `StackObject` containing authoritative controller, immutable card
facts, interpreter-derived cast kind, and locked target ID. Hand→Stack and Stack→destination are
validate-then-commit movements that create new runtime identities. Only the top object resolves;
turn progression refuses to bypass an unresolved object; and targeted spells revalidate the locked
runtime ID before applying effects.

GREEN is deliberately scoped to represented card spells and their lifecycle. It does not claim
priority, countering, activated/triggered ability objects, copies, complete casting steps, or every
resolution rule. Those capabilities can extend the shared stack and resolver seams without replacing
the represented foundation. Costs and Triggers remain independently RED.

## Independent adversarial evidence

| Probe | Result | Architectural conclusion |
| --- | --- | --- |
| Hand→Stack→Battlefield creature lifecycle | Three distinct registered runtime IDs; exact zone events. | CR 400.7 identity and CR 405 spell existence are authoritative. |
| Two announced creature spells | Resolve top-first in LIFO order. | Shared stack ordering follows CR 405.2. |
| Advance the turn with a spell pending | Rejected without mutation. | Callers cannot bypass represented resolution. |
| Target leaves before resolution | Spell moves Stack→Graveyard with no effect. | Locked IDs are revalidated under CR 608.2b. |
| Fabricated/stale spell or illegal announcement target | Rejected before mana or zone mutation. | Pilot/caller cannot fabricate a represented spell lifecycle. |
| Unsupported spell | Explicit telemetry; stays in hand; pays no mana. | Stack support does not approximate unsupported semantics. |
| Fabricated stack occupant / empty resolution | Invariant failure / `ValueError`. | Only registered top objects resolve. |
| Skip Setup→Draw / out-of-order transitions | `ValueError`; exact expected successor reported. | Runner or caller cannot skip the state graph. |
| Leave Combat Damage unresolved | Rejected. | Damage cannot be skipped. |
| Resolve damage before the step / resolve twice | Both rejected. | Damage execution is step-bound and single-use. |
| Assign `turn`, `active_player`, `phase`, or `step` | Read-only property assignment raises `AttributeError`. | Engine owns authoritative turn state. |
| Mutate pilot `GameView.step` | Frozen dataclass raises `FrozenInstanceError`. | Pilot cannot fabricate public phase/step state. |
| Attack outside Declare Attackers | No legal options; submitted option rejected without mutation. | Attack legality is engine-step-owned. |
| Block outside Declare Blockers | No legal block options; submitted option rejected. | Block legality is engine-step-owned. |
| Combat damage outside Combat Damage | Rejected. | Runner cannot call damage opportunistically. |
| Land/cast during combat or ending | No main options; direct represented entry points reject. | Current sorcery-speed timing uses authoritative main steps. |
| First-player first draw | Player 0 remains at seven on turn 1; player 1 draws on turn 2. | CR 103.8 first-turn draw exception is narrow and correct. |
| Untap / land reset / summoning sickness | Only active player untaps; allowance resets at that Untap; a creature remains sick through the opponent turn and clears on its controller’s next Untap. | Represented beginning-phase boundaries are correct. |
| End Step versus Cleanup | EOT P/T and damage persist through End Step and clear on Cleanup entry. | No premature or late represented cleanup. |
| Combat state across combat/turn | Declarations clear at Cleanup and Beginning of Combat; the next combat begins empty. | No combat-state leakage. |
| Acceptance runner static inspection | No assignment to turn/player/phase/step and no mutable zone access; progression uses engine methods. | Runner drives, but does not fabricate, state. |
| Identity/zone transactions during staged combat | Existing fabricated participant, stale object, new-object, and atomic movement tests pass. | Turn migration preserves 0.8a/0.8b guarantees. |

The compatibility `combat()` and `end_turn()` helpers remain engine-owned adapters and traverse the
same validated state/actions. The Acceptance runner no longer uses `combat()` and does not manually
set phase state.

## Architectural dependency probes after 0.8d

- **Sneak:** Declare Blockers is now an authoritative state, removing the old “no place to act” turn
  conflict. Sneak still cannot work: it needs priority during that step, stack casting, an alternative
  mana cost plus returning an unblocked attacker as an additional cost, and enters-attacking combat
  integration. Stack is now structurally available; Costs remains RED, while Priority and Combat
  are incomplete YELLOW dependencies.
- **Negate:** represented card spells now have authoritative stack objects, removing the old Stack
  conflict. Negate remains correctly unsupported because countering and priority sequencing are out
  of scope; Priority is YELLOW/unimplemented.
- **Alliance:** step context can timestamp future events, but current Alliance/ETB matches still
  execute immediately instead of becoming pending trigger instances after SBA processing. Triggers
  remains RED; the new state graph does not rationalize the sequencing defect.
- **Equipment:** pre/postcombat main states supply correct future “activate only as a sorcery” timing
  input. Equip still needs typed activation costs, targets, attachment edges, layers, and SBAs. Costs
  and Layers remain RED; Attachments remains YELLOW.
- **Mutagen:** authoritative main steps can express the timing portion of sorcery-speed activations.
  Token lifecycle, activated/additional costs, sacrifice, targeting, and associated SBAs remain
  missing. No Mutagen behavior is credited.
- **Disappear:** End Step now exists and is logged, so delayed/end-step scheduling has a legitimate
  future boundary. Typed events, delayed triggers, LKI, and stack placement remain absent; Disappear
  stays unsupported and Triggers remains RED. The Stack foundation is ready for future ability objects.

The Stack foundation removes a real architectural incompatibility for ordinary spells, Negate,
Sneak, triggers, and Disappear, but it does not implement or approximate their remaining semantics.

## Decision answers

1. **Is Stack still RED?** No. It is **GREEN** for represented card spells and their lifecycle.
2. **Are Stack objects authoritative?** Yes. Registration, controller, ordering, zone membership,
   target identity, and transitions are engine-owned and invariant-checked.
3. **Are Hand→Stack→destination identity changes correct?** Yes. Each boundary creates a new object
   under CR 400.7; stale incarnations cannot act again.
4. **Does resolution revalidate targets?** Yes for the represented single-target spells. All-illegal
   targets cause no effect and the spell goes to its owner's graveyard under CR 608.2b.
5. **Was Priority implemented?** No. `cast()` immediately resolves through explicit lifecycle seams;
   a future priority controller can call announcement and top resolution separately.
6. **Were Costs fixed automatically?** No. Prevalidation improved, but `_pay` and movement are not one
   typed rollback-capable transaction. Costs remains **RED**.
7. **Were Triggers fixed automatically?** No. Immediate Alliance/ETB/attack execution remains an
   architectural conflict. Triggers remains **RED**.
8. **How many REDs remain?** **4**: Costs, Triggers, Layers, and Deterministic RNG.
9. **Next single architectural correction?** Implement typed total-cost construction and atomic
   payment/rollback integrated with spell announcement, without adding new card Actions.

## Remaining RED priority

1. **Costs** — typed cost construction and atomic payment/rollback integrated with announcement.
2. **Triggers** — typed event detection, pending/APNAP queue, and eventual ability-stack placement.
3. **Layers** — ordered characteristic evaluation for Equipment and wider effects.
4. **Deterministic RNG** — persistent, logged, replayable randomness service.

Priority is deliberately absent from this RED list because the state-machine foundation removes its
architectural conflict. It remains YELLOW and wholly unsupported until a later priority controller is
implemented.

## Acceptance and validation evidence

Acceptance outcomes are unchanged from Engine 0.8c. Unsupported telemetry remains **81 events / 23
exact fragment pairs**, and block-restriction rejections remain **0/2/0/1/3** by seed, six total.

| Seed | Winner / ending turn | Unsupported events / seed pairs | Block rejections | Final stack |
| --- | --- | --- | ---: | ---: |
| 7001 | Raphael / 16 | 14 / 13 | 0 | 0 |
| 7002 | Leonardo / 17 | 14 / 8 | 2 | 0 |
| 7003 | Leonardo / 17 | 19 / 13 | 0 | 0 |
| 7004 | Leonardo / 21 | 21 / 18 | 1 | 0 |
| 7005 | Raphael / 16 | 13 / 8 | 3 | 0 |

Duplicate candidate runs match exactly per seed. Candidate snapshots are intentionally not
byte-identical to 0.8c because Engine 0.8d adds stack lifecycle events, new runtime IDs for spells,
an explicit empty-stack snapshot field, and a new engine version. Winners, ending turns, unsupported
counts, exact semantic pairs, block rejections, and represented gameplay trajectories are unchanged.

Validation at audit time:

- focused Stack plus Engine 0.7/0.8 boundary suites: **61 passed**;
- focused `test_engine08d_stack.py`: **6 passed**;
- full suite: **155 passed, 1 skipped**;
- Ruff format: clean;
- Ruff check: clean;
- `git diff --check`: clean;
- deterministic duplicate Acceptance Match #001 seeds 7001–7005: exact per-seed matches;
- authoritative card-data and 0.8a–0.8c boundary tests: included in the passing full suite.

## Governance boundary

This re-audit changes only this document. Engine 0.8d implementation/tests remain uncommitted and
unmodified by the audit. No full priority sequencing, generic trigger system, counterspell, new
Action, cost foundation, layer, RNG behavior, deck, prototype, historical evidence, calibration, or
smoke test was added or changed.
