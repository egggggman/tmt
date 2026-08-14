# Cardcade Engine Foundation Matrix

Re-audit date: 2026-08-13 EDT

Committed base: `6878369` (validated post-0.8b Foundation Matrix)

Candidate under review: uncommitted Engine 0.8c working tree

Rules basis: [Magic Comprehensive Rules, effective June 19, 2026](https://media.wizards.com/2026/downloads/MagicCompRules%2020260619.pdf)

Primary references: [Wizards rules index](https://magic.wizards.com/en/rules),
[TMNT rules update bulletin](https://magic.wizards.com/en/news/announcements/teenage-mutant-ninja-turtles-update-bulletin),
[TMNT release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes),
and the committed [authoritative snapshot manifest](../../cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json).

## Audit boundary and method

This is an evidence-only post-0.8c re-audit. The candidate implementation and tests were not
modified or committed. The only audit edit is this document. Assessment uses:

1. current CR 500–514 turn structure, with related CR 117 priority, 302.6 attack timing,
   506–511 combat, 603 triggers, 611.2a durations, and 514 cleanup requirements;
2. the checksum-verified TMT/PZA/TMC pool: 472 prints, **332 unique Oracle objects**, and
   **102 unique cards / 600 resolved slots** in the ten frozen decks;
3. committed Engine 0.8b at `6878369` versus the actual uncommitted 0.8c working tree;
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
| **Post-0.8c candidate** | **5** | **10** | **5** | **0** |

Engine 0.8c changes exactly three classifications: Turn Structure **RED → GREEN**, Combat State
**RED → YELLOW**, and Priority **RED → YELLOW**. No dependent row was upgraded automatically.

## Reconciled 20-row matrix

| Foundation row | Post-0.8b | Post-0.8c candidate | Current CR/pool/code/test evidence | Remaining rework risk |
| --- | :---: | :---: | --- | --- |
| Card Data / Oracle | **GREEN** | **GREEN** | CR 108.1 makes Oracle authoritative; CR 200–208 defines characteristics and faces. `card_data.py` still checksum-verifies 472 prints / 332 Oracle objects, exposes normalized facts and legalities, and resolves all 600 slots. Full data tests pass. | Extend the authoritative interface when more characteristics enter play; never add parallel hard-coded fact tables. |
| Object Identity | **GREEN** | **GREEN** | CR 109 and 400.7 identity remains registry-backed, non-value, and deterministic. Combat declarations now persist runtime IDs across three steps; stale/fabricated action IDs are revalidated. Identity and transactional-zone regressions pass. | Future tokens, copies, face-down objects, merged permanents, last-known information, and CR 400.7 exceptions must use the same service. |
| Zones | **YELLOW** | **YELLOW** | CR 400–408 support is unchanged: library, hand, battlefield, and graveyard use registered objects and `move_object()`. The turn machine neither bypasses nor weakens transactions. | Stack/exile/command, same-zone ordering, CR exceptions, and encapsulated internal collections remain absent. |
| Turn Structure | **RED** | **GREEN** | CR 500.1, 500.5, and 501–514 require ordered turns, phases, and steps. `TurnStep`, `TurnPhase`, `NEXT_STEP`, read-only `turn`/`active_player`/`step`/derived `phase`, and exact `transition_to()` validation now represent Untap through Cleanup. Independent probes reject skipped/out-of-order transitions and external setters. First draw, active-player rotation, untap, land reset, summoning sickness, combat boundaries, end-step persistence, and cleanup are tested. | Priority-bearing windows, extra turns/phases, additional combat phases, simultaneous team turns, hand-size cleanup, and repeated cleanup are explicit future extensions. They do not conflict with the represented deterministic 1v1 graph, so they do not keep this row RED or YELLOW. |
| Combat State | **RED** | **YELLOW** | CR 506–511 requires declaration and damage as distinct turn-based actions. `_combat_attackers`, `_combat_blocks`, declaration flags, and a damage-resolved gate persist authoritative state across Declare Attackers, Declare Blockers, Combat Damage, and End of Combat. Step-specific legal-option generation and execution reject actions outside their steps; combat state resets at Beginning of Combat and Cleanup. The former monolithic phase jump is gone from the runner. | Defender choice, arbitrary attacker subsets, multiple blockers, blocking order, first/double strike damage steps, trample assignment, planeswalkers/battles, attack costs, and a richer combat-state abstraction remain absent. These are additions over the staged state rather than replacement of monolithic flow. |
| Costs | **RED** | **RED** | CR 118 and 601.2f–h still require constructed total costs and atomic payment. Main-phase state improves timing input, but `can_afford`, `_pay`, and direct `cast` resolution remain. Sneak alternative/nonmana costs, Equip activation, Mutagen costs, and additional costs cannot be represented transactionally. | Add typed cast/activation proposals, cost construction, choices, and atomic payment plus stack movement. |
| Choices vs Targets | **YELLOW** | **YELLOW** | CR 115 and 601.2b–d support is unchanged. Immutable target IDs and choice hooks remain revalidated by `Game`; phase/step state adds timing context but not target locking or resolution choices. | Add typed target/choice requests, modes, divisions, optional choices, and stack-time target revalidation. |
| Events | **YELLOW** | **YELLOW** | Step transitions and turn-based combat actions now emit deterministic contextual logs, while zone/control records retain old/new IDs and reasons. `Game.log` remains passive telemetry, not a typed authoritative event stream with simultaneity, replacements, source/cause chains, or LKI. | Project state transactions and step changes into typed events; do not use audit logs as rules input. |
| Triggers | **RED** | **RED** | CR 603 and 117.5 require event detection, pending triggers after SBAs, APNAP ordering, stack placement, and resolution. `_on_enter_step()` is a clean hook for future upkeep/beginning-of-combat/end-step scheduling, and Disappear now has an authoritative end step. However Alliance/ETB/attack handlers still execute immediately inside mutation paths. The general architectural conflict therefore remains. | Replace immediate resolver calls with trigger instances, a pending queue, LKI, APNAP ordering, intervening-if checks, and stack resolution. Do not confuse the new step hook with a trigger pipeline. |
| Stack | **RED** | **RED** | CR 112.1 and 405 still require spell/ability stack objects. No stack zone/object exists; represented spells resolve directly from `cast`. Explicit steps do not make Negate executable. | Add stack objects and hand→stack→destination transactions; split announcement/payment from resolution and countering. |
| Priority | **RED** | **YELLOW** | CR 117 requires priority windows and all-pass sequencing. No priority player or pass state exists, so no priority behavior is credited. The former architectural blocker—no authoritative place to attach windows—is removed: all progression is centralized in `transition_to`/`advance_step`, and combat actions are distinct. A future priority controller can gate transitions and resolution at those seams without replacing turn state. | Add APNAP priority ownership, legal instant/ability options, pass cycles, all-pass stack resolution, and empty-stack step advancement. Existing combat action methods currently advance immediately and must yield to that controller. |
| State-Based Actions | **YELLOW** | **YELLOW** | CR 704/117.5 repeat-until-stable legend/lethal behavior remains. Cleanup and combat damage invoke represented SBA checks at deterministic engine boundaries, but no priority controller supplies every required boundary and checks remain narrow/sequential. | Collect simultaneous SBA batches at every future priority boundary; add zero toughness, counter annihilation, token cleanup, attachment SBAs, and other applicable cases. |
| Counters | **GREEN** | **GREEN** | CR 122 counter state remains separate from immutable printed P/T and modifiers. Turn-state migration preserves accumulation, persistence, derived P/T, zone reset, and SBA interactions. | Add more counter-type semantics and the +1/+1/−1/−1 SBA; finality depends on replacement/exile support. |
| Continuous Effects | **YELLOW** | **YELLOW** | CR 611–613 represented additive P/T effects remain sound. Engine-owned step context improves future duration predicates but does not add independent effect instances, affected-set queries, timestamps, dependencies, or non-P/T operations. | Build independent continuous-effect instances over runtime IDs and a characteristic-evaluation pipeline. |
| Layers | **RED** | **RED** | CR 613 still requires layers, sublayers, timestamps, and dependencies. `printed + counters + summed modifiers` is unchanged by turn state. Equipment/base-setting/type/copy effects would conflict with this evaluator. | Replace direct arithmetic with a layer pipeline. |
| Durations | **YELLOW** | **YELLOW** | CR 611.2a and 514.2 represented “until end of turn” semantics are now structurally stronger: effects survive through End Step and expire only on entry to engine-owned Cleanup; marked damage clears at the same boundary. Persistent modifiers survive. Independent probes and regressions verify no premature/late expiration. | End-of-combat, next-turn, “for as long as,” source-linked, attachment-linked, delayed, and conditional durations remain absent. Repeated cleanup under CR 514.3 requires the future trigger/priority loop. |
| Attachments | **YELLOW** | **YELLOW** | CR 301.5, 303.4, 701.3, and 704.5m–n remain unsupported but identity-safe. Main-phase state supplies the correct future sorcery-timing input for Equip; no attachment/equip semantics were added. | Add runtime-ID attachment edges, legality, typed Equip cost/activation, detachment, effects/layers, and attachment SBAs. |
| Deterministic RNG | **RED** | **RED** | CR 103.3/701.20 random operations still need a retained auditable stream. Turn progression and duplicate acceptance runs are deterministic, but `random.Random(seed)` is still discarded after shuffle. Casey Jones-style later randomness remains structurally unsafe. | Retain a game-owned RNG service, log consumption, and serialize/replay its state or decisions. |
| Invariants | **YELLOW** | **YELLOW** | Existing registry/zone/identity invariants pass. New combat gates reject leaving unresolved Combat Damage, repeated damage, and off-step actions; immutable turn properties prevent fabricated public state. Global card conservation, explicit turn/combat invariant checks at every transaction, option versioning, and future subsystem causality remain absent. | Formalize turn/combat invariants in `check_invariants`, add conservation, encapsulate mutable collections, and extend to stack/events/attachments. |
| Rules Engine ↔ Card Interpreter ↔ Pilot separation | **GREEN** | **GREEN** | `Game` owns read-only turn state, transition validation, legal actions, and mutation. `CardInterpreter` remains pure and strategy-free. Pilots see frozen `GameView` including phase/step and immutable options. Static inspection finds no runner assignment to engine state; it calls `begin_turn`, `advance_step`, and staged legal execution methods. Strategy cannot fabricate a phase or bypass timing. | Preserve this boundary when priority choices, stack objects, costs, triggers, and effects are introduced. Compatibility helpers are engine methods and still traverse validated transitions; they are not Pilot authority. |

No row is UNKNOWN: current rules, authoritative data, committed history, candidate code, and executable
probes are sufficient for all twenty classifications.

## Classification changes

### Turn Structure: RED → GREEN

The previous RED condition was specific: a mutable string phase plus `begin_turn`, monolithic
`combat`, and `end_turn` skipped the CR 500-series structure, leaving no authoritative upkeep,
draw, combat-step, end-step, or cleanup boundaries. That representation is gone. The candidate has
one exact next-step graph, engine-owned turn/player/step state, a phase derived from step, deterministic
entry actions, and rejected setters/out-of-order transitions. Represented timing restrictions query
the engine step directly. Unsupported priority, extra turns/phases, and repeated cleanup remain
explicit, but no longer require replacement of the represented turn foundation. GREEN applies only
to the declared deterministic two-player scope; it does not claim complete CR 500–514 gameplay.

### Combat State: RED → YELLOW

The previous monolithic combat operation declared, blocked, damaged, and jumped phases in one call.
The candidate stores attacker/block pairs and completion flags across explicit steps, generates and
revalidates options only at the correct step, and prevents leaving Combat Damage before resolution.
This removes the architectural conflict. It is not GREEN because the choice model and damage model
do not cover multiple blockers, damage ordering, extra damage steps, defender selection, trample,
or other full combat requirements.

### Priority: RED → YELLOW

No priority semantics were implemented or credited. The classification changes because the reason
for RED—no authoritative phases/steps or reliable window attachment points—no longer exists.
Central transition and staged action boundaries give a future priority controller a single clean
place to stop progression, offer options, collect passes, and resume. Existing immediate transition
calls will need localized delegation to that controller, not replacement of turn state. Stack remains
RED independently.

## Independent adversarial evidence

| Probe | Result | Architectural conclusion |
| --- | --- | --- |
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

## Architectural dependency probes after 0.8c

- **Sneak:** Declare Blockers is now an authoritative state, removing the old “no place to act” turn
  conflict. Sneak still cannot work: it needs priority during that step, stack casting, an alternative
  mana cost plus returning an unblocked attacker as an additional cost, and enters-attacking combat
  integration. Turn Structure is no longer one of its RED dependencies; Costs and Stack remain RED,
  while Priority and Combat are incomplete YELLOW dependencies.
- **Negate:** explicit steps provide locations for future priority windows but no spell stack object
  exists. Negate remains correctly unsupported; Stack is RED and Priority is YELLOW/unimplemented.
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
  stays unsupported and Triggers/Stack remain RED.

Authoritative timing therefore removes real architectural incompatibilities for Sneak, Equipment,
Mutagen, and Disappear, but it does not implement or approximate any of their semantics.

## Decision answers

1. **Is Turn Structure still RED?** No. It is **GREEN** for the represented deterministic 1v1 scope.
2. **Does Combat State change?** Yes, **RED → YELLOW**. Persistent staged combat removes the
   monolithic architecture conflict, but coverage is incomplete.
3. **Is there a clean future Priority attachment point?** Yes. Central transitions and staged combat
   actions provide it. Priority itself is not implemented and is **YELLOW**, not GREEN.
4. **Is there a clean future trigger-scheduling attachment point?** Step entry is a clean hook for
   step triggers, but immediate general trigger handlers still conflict with CR 603/117.5. Triggers
   remains **RED** until those handlers become queued trigger instances.
5. **Are represented cleanup/duration semantics structurally correct?** Yes. EOT effects and marked
   damage persist through End Step and clear at Cleanup. Other durations and repeated cleanup remain
   unsupported, so Durations remains **YELLOW**.
6. **Did conflicts become unsupported future capabilities?** Yes: Turn’s former conflict is resolved;
   Combat and Priority become incomplete but extensible YELLOW capabilities. No other RED moves.
7. **How many REDs remain?** **5**: Costs, Triggers, Stack, Layers, and Deterministic RNG.
8. **Highest-priority RED?** **Stack**. It blocks Negate, ordinary non-immediate spell resolution,
   and the later priority/trigger pipeline. Costs is tightly coupled but remains a separate RED.
9. **Next single architectural correction?** Implement a reusable stack-object and spell lifecycle
   foundation: announcement creates an authoritative stack object; resolution/countering moves it
   transactionally to the correct zone. Keep priority pass sequencing and generic trigger scheduling
   out of that checkpoint, while exposing their future hooks.

## Remaining RED priority

1. **Stack** — authoritative spell/ability stack objects and transactional spell lifecycle.
2. **Costs** — typed cost construction and atomic payment integrated with stack announcement.
3. **Triggers** — typed event detection, pending/APNAP queue, and eventual stack placement.
4. **Layers** — ordered characteristic evaluation for Equipment and wider effects.
5. **Deterministic RNG** — persistent, logged, replayable randomness service.

Priority is deliberately absent from this RED list because the state-machine foundation removes its
architectural conflict. It remains YELLOW and wholly unsupported until a later priority controller is
implemented.

## Acceptance and validation evidence

Acceptance outcomes are unchanged from Engine 0.8b. Unsupported telemetry remains **81 events / 23
exact fragment pairs**, and block-restriction rejections remain **0/2/0/1/3** by seed, six total.

| Seed | Winner / ending turn | Unsupported events / seed pairs | Block rejections | Candidate canonical replay SHA-256 |
| --- | --- | --- | ---: | --- |
| 7001 | Raphael / 16 | 14 / 13 | 0 | `9fb5fb5087ce4759d45fa0c1ed6156680b236a9922b058434504ed1827870b81` |
| 7002 | Leonardo / 17 | 14 / 8 | 2 | `3c027d31f02080e200bdbc86feb3f9dfebf7341c0bce999e8321decab6384e21` |
| 7003 | Leonardo / 17 | 19 / 13 | 0 | `c515161d8f8b075183e76f10612ca0500c596600289588f44d4bea4039c97ea5` |
| 7004 | Leonardo / 21 | 21 / 18 | 1 | `980ee76e634068808f0f8bce2605d0c0097bd8b00a4f5cc198b915f510794eee` |
| 7005 | Raphael / 16 | 13 / 8 | 3 | `0b5bde9ccc558a81f0ed43f3498ae7ef6d868d70d4dfa35c8882a180e2a95129` |

Each hash is over canonical audit rendering (`json.dumps(snapshot, indent=2) + "\n"`, UTF-8 LF).
Duplicate candidate runs match exactly per seed. Candidate snapshots are intentionally not
byte-identical to 0.8b because Engine 0.8c adds authoritative `step` state/events and changes the
engine version. Winners, ending turns, unsupported counts, exact semantic pairs, block rejections,
and represented gameplay trajectories are unchanged; this is execution evidence, not balance
evidence.

Validation at audit time:

- independent adversarial turn-state probes: 5 grouped probes passed;
- focused `test_engine08c_turn_state.py`: 6 passed;
- full suite: 149 passed, 1 skipped;
- Ruff format: clean;
- Ruff check: clean;
- `git diff --check`: clean;
- deterministic duplicate Acceptance Match #001 seeds 7001–7005: exact per-seed matches;
- authoritative card-data and 0.8a/0.8b boundary tests: included in the passing full suite.

## Governance boundary

This re-audit changes only this document. Engine 0.8c implementation/tests remain uncommitted and
unmodified by the audit. No Action, Draw/Discard/Selection, priority, stack, trigger system, cost,
layer, RNG behavior, deck, prototype, historical evidence, calibration, or smoke test was added or
changed.
