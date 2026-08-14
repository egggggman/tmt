# Cardcade Engine Foundation Matrix

Re-audit date: 2026-08-13 EDT

Committed base: `c52e31e` (validated post-0.8f Foundation Matrix)

Candidate under review: uncommitted Engine 0.8g Layers Foundation working tree

Rules basis: [Magic Comprehensive Rules, effective June 19, 2026](https://media.wizards.com/2026/downloads/MagicCompRules%2020260619.pdf)

Primary references: [Wizards rules index](https://magic.wizards.com/en/rules),
[TMNT rules update bulletin](https://magic.wizards.com/en/news/announcements/teenage-mutant-ninja-turtles-update-bulletin),
[TMNT release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes),
and the committed [authoritative snapshot manifest](../../cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json).

## Audit boundary and method

This is an evidence-only post-0.8g re-audit. The candidate implementation and tests were not
modified or committed. The only audit edit is this document. Assessment uses:

1. current CR 613 layer/sublayer, timestamp, and dependency ordering, with related CR 122 counters,
   611 continuous effects, and 701.20 randomness requirements;
2. the checksum-verified TMT/PZA/TMC pool: 472 prints, **332 unique Oracle objects**, and
   **102 unique cards / 600 resolved slots** in the ten frozen decks;
3. committed Engine 0.8f at `c52e31e` versus the actual uncommitted 0.8g working tree;
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
| **Post-0.8d (`dc62779`)** | **6** | **10** | **4** | **0** |
| **Post-0.8e (`3a8de43`)** | **7** | **10** | **3** | **0** |
| **Post-0.8f (`c52e31e`)** | **8** | **10** | **2** | **0** |
| **Post-0.8g candidate** | **9** | **10** | **1** | **0** |

Engine 0.8g changes exactly one classification: Layers **RED → GREEN** for represented P/T
characteristic evaluation. No dependent row was upgraded automatically.

## Reconciled 20-row matrix

| Foundation row | Post-0.8f | Post-0.8g candidate | Current CR/pool/code/test evidence | Remaining rework risk |
| --- | :---: | :---: | --- | --- |
| Card Data / Oracle | **GREEN** | **GREEN** | CR 108.1 makes Oracle authoritative; CR 200–208 defines characteristics and faces. `card_data.py` still checksum-verifies 472 prints / 332 Oracle objects, exposes normalized facts and legalities, and resolves all 600 slots. Full data tests pass. | Extend the authoritative interface when more characteristics enter play; never add parallel hard-coded fact tables. |
| Object Identity | **GREEN** | **GREEN** | CR 109 and 400.7 identity remains registry-backed, non-value, and deterministic. Combat declarations now persist runtime IDs across three steps; stale/fabricated action IDs are revalidated. Identity and transactional-zone regressions pass. | Future tokens, copies, face-down objects, merged permanents, last-known information, and CR 400.7 exceptions must use the same service. |
| Zones | **YELLOW** | **YELLOW** | CR 400–408 now includes an authoritative shared Stack alongside library, hand, battlefield, and graveyard. All represented Hand→Stack→destination movement uses `move_object()` and CR 400.7 new identities. | Exile/command, same-zone ordering, CR exceptions, and encapsulated internal collections remain absent. |
| Turn Structure | **GREEN** | **GREEN** | The exact CR 500-series turn graph remains authoritative. `transition_to()` now also rejects advancement while a represented stack object is unresolved, so callers cannot skip resolution. Existing turn and cleanup regressions pass. | Priority-bearing windows, extra turns/phases, additional combat phases, simultaneous team turns, hand-size cleanup, and repeated cleanup remain future extensions. |
| Combat State | **YELLOW** | **YELLOW** | Staged CR 506–511 combat state is unchanged and its regressions pass. The spell lifecycle does not fabricate combat timing or add Sneak/enters-attacking behavior. | Defender choice, arbitrary attacker subsets, multiple blockers, blocking order, extra damage steps, trample assignment, planeswalkers/battles, and attack costs remain absent. |
| Costs | **RED** | **GREEN** | CR 118/601.2f–h is now represented by frozen `ManaRequirement` and `PaymentPlan` values. Fixed generic/colored symbols construct exact totals; plans lock authoritative source IDs; colored sources are selected before deterministic generic sources; the plan is revalidated at commit; and every tap rolls back if Hand→Stack movement fails. Unsupported symbols are explicit and never pay. | Hybrid/phyrexian/snow/X costs, reductions/increases, cost-setting, mana abilities, player-selected payments, additional/alternative costs, activation costs, and nonmana costs remain unsupported extensions over the typed transaction. |
| Choices vs Targets | **YELLOW** | **YELLOW** | Represented targets are locked as immutable runtime IDs on `StackObject` and revalidated under CR 608.2b at resolution. Fabricated, friendly, stale, and power-ineligible targets are rejected or resolve with no effect as appropriate. | Add typed target/choice requests, modes, divisions, optional choices, multiple targets, partial legality, and resolution-time non-target choices. |
| Events | **YELLOW** | **YELLOW** | Frozen `RulesEvent` values now authoritatively identify creature-entry, life-gain, and attacker-declaration events with deterministic IDs, player, and subject IDs. Logs project their lifecycle but are not rules input. | Add simultaneous event batches, replacements/prevention, richer source/cause chains, LKI snapshots, and broader event kinds. |
| Triggers | **RED** | **GREEN** | Represented Alliance, life-gain, attack, and conditional ETB shapes are now detected from typed events into frozen `TriggerInstance` values, queued, ordered deterministically by APNAP/controller/source, placed as independent `TriggeredAbilityObject` entries on the shared stack, and resolved top-first. Source departure does not delete the ability. Immediate mutation-path handlers are gone from actual spell resolution. | Optional/mode/target choices should move fully to stack-placement time where required; add intervening-if checks, delayed triggers, leaves/dies/cast triggers, LKI payloads, simultaneous SBA/trigger collection, player ordering choices, and broader interpreter shapes. These extend the represented pipeline rather than replace it. |
| Stack | **GREEN** | **GREEN** | The shared stack now contains both card-backed spells and independent triggered-ability objects. Unified top resolution preserves an underlying spell while an ability resolves above it; type/registration/zone invariants cover both. | Activated abilities, copies, face-down spells, countering, replacement destinations, and complete casting steps remain unsupported extensions. |
| Priority | **YELLOW** | **YELLOW** | CR 117 priority ownership and all-pass sequencing remain unimplemented. Trigger batches use deterministic immediate compatibility draining after stack placement; the unified resolver and transition gate remain clean future controller seams. | Add APNAP priority ownership, legal instant/ability options, pass cycles, all-pass top resolution, and empty-stack step advancement. |
| State-Based Actions | **YELLOW** | **YELLOW** | CR 704/117.5 repeat-until-stable legend/lethal behavior remains. Cleanup and combat damage invoke represented SBA checks at deterministic engine boundaries, but no priority controller supplies every required boundary and checks remain narrow/sequential. | Collect simultaneous SBA batches at every future priority boundary; add zero toughness, counter annihilation, token cleanup, attachment SBAs, and other applicable cases. |
| Counters | **GREEN** | **GREEN** | CR 122 counter state remains separate and is now projected as a typed layer 7c additive effect rather than added by a parallel arithmetic path. Accumulation, persistence, zone reset, and SBA interactions pass. | Add more counter-type semantics and the +1/+1/−1/−1 SBA; finality depends on replacement/exile support. |
| Continuous Effects | **YELLOW** | **YELLOW** | Represented additive modifiers and new typed set/add/switch test effects are independent inputs to characteristic evaluation with timestamps and dependencies. Affected-set queries, source-linked lifecycle, non-P/T operations, and automatic broader Oracle interpretation remain absent. | Build game-owned effect registries/queries and extend typed operations beyond P/T without bypassing the evaluator. |
| Layers | **RED** | **GREEN** | CR 613 ordering is now represented by `CharacteristicLayer`, P/T sublayers 7a–7d, typed operations, stable timestamps, and dependency-aware topological ordering. Existing counters and modifiers are projected into 7c; 7b set, 7c modify, and 7d switch execute in order regardless of insertion. Cycles/wrong operations are rejected and zone changes reset effect state. | Copy/control/text/type/color/ability operations, CDAs beyond P/T tests, automatic dependency discovery, multi-object affected sets, and full characteristic coverage remain unsupported extensions. The represented evaluator no longer conflicts with base-setting or Equipment-style additive P/T effects. |
| Durations | **YELLOW** | **YELLOW** | CR 611.2a and 514.2 represented “until end of turn” semantics are now structurally stronger: effects survive through End Step and expire only on entry to engine-owned Cleanup; marked damage clears at the same boundary. Persistent modifiers survive. Independent probes and regressions verify no premature/late expiration. | End-of-combat, next-turn, “for as long as,” source-linked, attachment-linked, delayed, and conditional durations remain absent. Repeated cleanup under CR 514.3 requires the future trigger/priority loop. |
| Attachments | **YELLOW** | **YELLOW** | CR 301.5, 303.4, 701.3, and 704.5m–n remain unsupported but identity-safe. Main-phase state supplies the correct future sorcery-timing input for Equip; no attachment/equip semantics were added. | Add runtime-ID attachment edges, legality, typed Equip cost/activation, detachment, effects/layers, and attachment SBAs. |
| Deterministic RNG | **RED** | **RED** | CR 103.3/701.20 random operations still need a retained auditable stream. Turn progression and duplicate acceptance runs are deterministic, but `random.Random(seed)` is still discarded after shuffle. Casey Jones-style later randomness remains structurally unsafe. | Retain a game-owned RNG service, log consumption, and serialize/replay its state or decisions. |
| Invariants | **YELLOW** | **YELLOW** | Characteristic-effect IDs, dependencies, operations, cycles, timestamps, and zone reset are now adversarially covered alongside existing stack/trigger invariants. | Add global conservation, checks at every transaction, option/state versioning, encapsulated collections, and cross-object effect causality. |
| Rules Engine ↔ Card Interpreter ↔ Pilot separation | **GREEN** | **GREEN** | The engine owns effect registration/validation and permanents expose pure ordered evaluation. Existing interpreter-derived modifiers enter the same pipeline; pilots cannot write effects or characteristics. | Preserve this boundary for broader Oracle effect construction, affected-set selection, attachments, copies, and type/ability changes. |

No row is UNKNOWN: current rules, authoritative data, committed history, candidate code, and executable
probes are sufficient for all twenty classifications.

## Classification changes

### Layers: RED → GREEN

The previous RED condition was structural: `Permanent.power`/`toughness` directly added printed
values, counters, and a flat modifier list. Base-setting, switches, timestamps, dependencies, copy/
type effects, and Equipment would have required replacing that evaluator. Engine 0.8g removes the
direct arithmetic path. Typed `CharacteristicEffect` values identify layer, sublayer, operation,
timestamp, declared dependencies, and source. The evaluator orders layers/sublayers first, then
dependency-ready effects and stable timestamps; counters and existing modifiers enter layer 7c;
and set/add/switch operations execute in 7b/7c/7d order regardless of insertion.

GREEN is scoped to represented P/T characteristic evaluation. Other layer operations, automatic
dependency discovery, affected-set calculation, copies, type/color/ability changes, and complete
continuous-effect lifecycle remain unsupported. They extend the typed ordering pipeline rather than
replace flat arithmetic. Deterministic RNG is the only remaining RED.

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
| Fixed generic/colored cost construction | Exact frozen `ManaRequirement`. | Total cost is explicit rather than inferred from mana value. |
| Mixed-color deterministic payment | Correct color sources selected before generic source. | Payment is legal and replay-stable. |
| Stale/fabricated `PaymentPlan` | Rejected before mutation. | Callers cannot substitute sources or reuse obsolete plans. |
| Injected Hand→Stack failure | Every payment source restored; card remains in hand. | Payment and announcement are one rollback-capable transaction. |
| Hybrid/unrepresented symbol | Explicit unsupported telemetry; no tap or movement. | Unsupported costs are not approximated. |
| Creature-entered trigger with drain paused | Frozen event and independent ability object visible before effect. | Detection, placement, and resolution are distinct. |
| Source leaves before resolution | Ability remains and resolves from retained source facts. | Trigger existence is source-independent. |
| Three simultaneous triggers across controllers | Deterministic APNAP groups and source order. | Stack order is reproducible and extensible to player choices. |
| Trigger above existing spell | Ability resolves; underlying spell stays on stack. | Spell and ability objects share one authoritative stack. |
| Fabricated ability object | Resolution and invariants reject it. | Callers cannot inject triggers. |
| Duplicate trigger replay | Event/pending/stack/resolved telemetry matches exactly. | Trigger execution is deterministic. |
| Existing counters plus modifiers | Same P/T through typed layer 7c effects. | Migration preserves represented gameplay. |
| Insert switch, modify, set in reverse order | Evaluates 7b→7c→7d to the expected result. | Sublayers, not mutation order, control characteristics. |
| Two independent set effects | Stable timestamp order. | Later effects apply deterministically. |
| Declared dependency with inverse timestamps | Dependency order wins inside the sublayer. | Dependency-ready evaluation is real, not metadata-only. |
| Cyclic dependency / wrong operation | Rejected without authoritative state corruption. | Invalid layer graphs cannot silently evaluate. |
| Zone round trip | New object has no prior characteristic effects. | CR 400.7 resets layer state. |
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

## Architectural dependency probes after 0.8g

- **Sneak:** Declare Blockers is now an authoritative state, removing the old “no place to act” turn
  conflict. Sneak still cannot work: it needs priority during that step, stack casting, an alternative
  mana cost plus returning an unblocked attacker as an additional cost, and enters-attacking combat
  integration. Stack and the fixed-cost transaction are structurally available, but its alternative
  mana plus return-an-attacker additional cost remains unsupported; Priority and Combat are YELLOW.
- **Negate:** represented card spells now have authoritative stack objects, removing the old Stack
  conflict. Negate remains correctly unsupported because countering and priority sequencing are out
  of scope; Priority is YELLOW/unimplemented.
- **Alliance:** represented Alliance matches now become pending trigger instances and ability-stack
  objects. Unsupported Alliance branches remain explicit; full player ordering/target timing and
  simultaneous SBA collection remain future extensions.
- **Equipment:** pre/postcombat main states, typed costs, runtime identities, and layer 7c additive
  evaluation are structurally available. Equip still needs activation target types, attachment edges,
  effect lifecycle, and SBAs; Attachments remains YELLOW without keeping Layers RED.
- **Mutagen:** authoritative main steps can express the timing portion of sorcery-speed activations.
  Token lifecycle, activated/additional costs, sacrifice, targeting, and associated SBAs remain
  missing. No Mutagen behavior is credited.
- **Disappear:** End Step now exists and is logged, so delayed/end-step scheduling has a legitimate
  future boundary. The typed pipeline is ready, but delayed scheduling and LKI payloads are not yet
  represented, so Disappear stays unsupported without making Triggers structurally RED.

The Layers foundation removes the flat P/T arithmetic conflict and supplies the evaluator required by
future Equipment/base-setting work without implementing those Actions or attachments.

## Decision answers

1. **Are Layers still RED?** No. They are **GREEN** for represented P/T evaluation.
2. **Did direct P/T arithmetic remain?** No. Printed values are the base and every represented counter,
   modifier, set, add, and switch is ordered through the typed evaluator.
3. **Are sublayers correct?** Yes for represented 7a–7d ordering; tests prove set→modify→switch is
   independent of insertion order.
4. **Are timestamps represented?** Yes. Independent effects within a sublayer apply in stable order.
5. **Are dependencies represented?** Yes. Declared dependencies override timestamps within a group;
   cycles and missing dependencies are rejected.
6. **Does CR 400.7 reset effects?** Yes. New battlefield objects have empty effect state.
7. **Were Equipment or broader effects implemented?** No. Attachments, Actions, affected sets, and
   non-P/T operations remain unsupported extensions.
8. **How many REDs remain?** **1**: Deterministic RNG.
9. **Next single architectural correction?** Retain a game-owned deterministic RNG service, log every
   consumption with sequence/domain/result evidence, and expose serializable replay state.

## Remaining RED priority

1. **Deterministic RNG** — persistent, logged, replayable randomness service.

Priority is deliberately absent from this RED list because the state-machine foundation removes its
architectural conflict. It remains YELLOW and wholly unsupported until a later priority controller is
implemented.

## Acceptance and validation evidence

Acceptance outcomes are unchanged from Engine 0.8f. Unsupported telemetry remains **81 events / 23
exact fragment pairs**, and block-restriction rejections remain **0/2/0/1/3** by seed, six total.

| Seed | Winner / ending turn | Unsupported events / seed pairs | Block rejections | Final stack |
| --- | --- | --- | ---: | ---: |
| 7001 | Raphael / 16 | 14 / 13 | 0 | 0 |
| 7002 | Leonardo / 17 | 14 / 8 | 2 | 0 |
| 7003 | Leonardo / 17 | 19 / 13 | 0 | 0 |
| 7004 | Leonardo / 21 | 21 / 18 | 1 | 0 |
| 7005 | Raphael / 16 | 13 / 8 | 3 | 0 |

Duplicate candidate runs match exactly per seed. Candidate snapshots are intentionally not
byte-identical to 0.8f because Engine 0.8g adds effect timestamps, characteristic-effect snapshot
state, and a new engine version. Winners, ending turns, unsupported counts, exact semantic pairs,
block rejections, and trajectories are unchanged.

Validation at audit time:

- focused Layers, Engine 0.7, and Trigger suites: **50 passed**;
- focused `test_engine08g_layers.py`: **6 passed**;
- full suite: **173 passed, 1 skipped**;
- Ruff format: clean;
- Ruff check: clean;
- `git diff --check`: clean;
- deterministic duplicate Acceptance Match #001 seeds 7001–7005: exact per-seed matches;
- authoritative card-data and 0.8a–0.8f boundary tests: included in the passing full suite.

## Governance boundary

This re-audit changes only this document. Engine 0.8g implementation/tests remain uncommitted and
unmodified by the audit. No Equipment/attachment, full priority sequencing, counterspell, new Action,
RNG behavior, deck, prototype, historical evidence, calibration, or smoke test was added or changed.
