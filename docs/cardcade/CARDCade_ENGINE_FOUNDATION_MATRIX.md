# Cardcade Engine Foundation Matrix

Re-audit date: 2026-08-14 EDT

Committed base: `f196665` (validated post-0.8g Foundation Matrix)

Candidate under review: uncommitted Engine 0.8h Deterministic RNG Foundation working tree

Rules basis: [Magic Comprehensive Rules, effective June 19, 2026](https://media.wizards.com/2026/downloads/MagicCompRules%2020260619.pdf)

Primary references: [Wizards rules index](https://magic.wizards.com/en/rules),
[TMNT rules update bulletin](https://magic.wizards.com/en/news/announcements/teenage-mutant-ninja-turtles-update-bulletin),
[TMNT release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes),
and the committed [authoritative snapshot manifest](../../cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json).

## Audit boundary and method

This is an evidence-only post-0.8h re-audit. The candidate implementation and tests were not
modified or committed. The only audit edit is this document. Assessment uses:

1. current CR 103.3 and 701.20 randomness requirements, with reproducibility, consumption-ledger,
   state-export, and exact legacy-permutation evidence;
2. the checksum-verified TMT/PZA/TMC pool: 472 prints, **332 unique Oracle objects**, and
   **102 unique cards / 600 resolved slots** in the ten frozen decks;
3. committed Engine 0.8g at `f196665` versus the actual uncommitted 0.8h working tree;
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
| **Post-0.8g (`f196665`)** | **9** | **10** | **1** | **0** |
| **Post-0.8h candidate** | **10** | **10** | **0** | **0** |

Engine 0.8h changes exactly one classification: Deterministic RNG **RED → GREEN** for represented
random operations. No dependent row was upgraded automatically.

## Reconciled 20-row matrix

| Foundation row | Post-0.8g | Post-0.8h candidate | Current CR/pool/code/test evidence | Remaining rework risk |
| --- | :---: | :---: | --- | --- |
| Card Data / Oracle | **GREEN** | **GREEN** | CR 108.1 makes Oracle authoritative; CR 200–208 defines characteristics and faces. `card_data.py` still checksum-verifies 472 prints / 332 Oracle objects, exposes normalized facts and legalities, and resolves all 600 slots. Full data tests pass. | Extend the authoritative interface when more characteristics enter play; never add parallel hard-coded fact tables. |
| Object Identity | **GREEN** | **GREEN** | CR 109 and 400.7 identity remains registry-backed, non-value, and deterministic. Combat declarations now persist runtime IDs across three steps; stale/fabricated action IDs are revalidated. Identity and transactional-zone regressions pass. | Future tokens, copies, face-down objects, merged permanents, last-known information, and CR 400.7 exceptions must use the same service. |
| Zones | **YELLOW** | **YELLOW** | CR 400–408 now includes an authoritative shared Stack alongside library, hand, battlefield, and graveyard. All represented Hand→Stack→destination movement uses `move_object()` and CR 400.7 new identities. | Exile/command, same-zone ordering, CR exceptions, and encapsulated internal collections remain absent. |
| Turn Structure | **GREEN** | **GREEN** | The exact CR 500-series turn graph remains authoritative. `transition_to()` now also rejects advancement while a represented stack object is unresolved, so callers cannot skip resolution. Existing turn and cleanup regressions pass. | Priority-bearing windows, extra turns/phases, additional combat phases, simultaneous team turns, hand-size cleanup, and repeated cleanup remain future extensions. |
| Combat State | **YELLOW** | **YELLOW** | Staged CR 506–511 combat state is unchanged and its regressions pass. The spell lifecycle does not fabricate combat timing or add Sneak/enters-attacking behavior. | Defender choice, arbitrary attacker subsets, multiple blockers, blocking order, extra damage steps, trample assignment, planeswalkers/battles, and attack costs remain absent. |
| Costs | **GREEN** | **GREEN** | CR 118/601.2f–h is now represented by frozen `ManaRequirement` and `PaymentPlan` values. Fixed generic/colored symbols construct exact totals; plans lock authoritative source IDs; colored sources are selected before deterministic generic sources; the plan is revalidated at commit; and every tap rolls back if Hand→Stack movement fails. Unsupported symbols are explicit and never pay. | Hybrid/phyrexian/snow/X costs, reductions/increases, cost-setting, mana abilities, player-selected payments, additional/alternative costs, activation costs, and nonmana costs remain unsupported extensions over the typed transaction. |
| Choices vs Targets | **YELLOW** | **YELLOW** | Represented targets are locked as immutable runtime IDs on `StackObject` and revalidated under CR 608.2b at resolution. Fabricated, friendly, stale, and power-ineligible targets are rejected or resolve with no effect as appropriate. | Add typed target/choice requests, modes, divisions, optional choices, multiple targets, partial legality, and resolution-time non-target choices. |
| Events | **YELLOW** | **YELLOW** | Frozen `RulesEvent` values now authoritatively identify creature-entry, life-gain, and attacker-declaration events with deterministic IDs, player, and subject IDs. Logs project their lifecycle but are not rules input. | Add simultaneous event batches, replacements/prevention, richer source/cause chains, LKI snapshots, and broader event kinds. |
| Triggers | **GREEN** | **GREEN** | Represented Alliance, life-gain, attack, and conditional ETB shapes are now detected from typed events into frozen `TriggerInstance` values, queued, ordered deterministically by APNAP/controller/source, placed as independent `TriggeredAbilityObject` entries on the shared stack, and resolved top-first. Source departure does not delete the ability. Immediate mutation-path handlers are gone from actual spell resolution. | Optional/mode/target choices should move fully to stack-placement time where required; add intervening-if checks, delayed triggers, leaves/dies/cast triggers, LKI payloads, simultaneous SBA/trigger collection, player ordering choices, and broader interpreter shapes. These extend the represented pipeline rather than replace it. |
| Stack | **GREEN** | **GREEN** | The shared stack now contains both card-backed spells and independent triggered-ability objects. Unified top resolution preserves an underlying spell while an ability resolves above it; type/registration/zone invariants cover both. | Activated abilities, copies, face-down spells, countering, replacement destinations, and complete casting steps remain unsupported extensions. |
| Priority | **YELLOW** | **YELLOW** | CR 117 priority ownership and all-pass sequencing remain unimplemented. Trigger batches use deterministic immediate compatibility draining after stack placement; the unified resolver and transition gate remain clean future controller seams. | Add APNAP priority ownership, legal instant/ability options, pass cycles, all-pass top resolution, and empty-stack step advancement. |
| State-Based Actions | **YELLOW** | **YELLOW** | CR 704/117.5 repeat-until-stable legend/lethal behavior remains. Cleanup and combat damage invoke represented SBA checks at deterministic engine boundaries, but no priority controller supplies every required boundary and checks remain narrow/sequential. | Collect simultaneous SBA batches at every future priority boundary; add zero toughness, counter annihilation, token cleanup, attachment SBAs, and other applicable cases. |
| Counters | **GREEN** | **GREEN** | CR 122 counter state remains separate and is now projected as a typed layer 7c additive effect rather than added by a parallel arithmetic path. Accumulation, persistence, zone reset, and SBA interactions pass. | Add more counter-type semantics and the +1/+1/−1/−1 SBA; finality depends on replacement/exile support. |
| Continuous Effects | **YELLOW** | **YELLOW** | Represented additive modifiers and new typed set/add/switch test effects are independent inputs to characteristic evaluation with timestamps and dependencies. Affected-set queries, source-linked lifecycle, non-P/T operations, and automatic broader Oracle interpretation remain absent. | Build game-owned effect registries/queries and extend typed operations beyond P/T without bypassing the evaluator. |
| Layers | **GREEN** | **GREEN** | CR 613 ordering is now represented by `CharacteristicLayer`, P/T sublayers 7a–7d, typed operations, stable timestamps, and dependency-aware topological ordering. Existing counters and modifiers are projected into 7c; 7b set, 7c modify, and 7d switch execute in order regardless of insertion. Cycles/wrong operations are rejected and zone changes reset effect state. | Copy/control/text/type/color/ability operations, CDAs beyond P/T tests, automatic dependency discovery, multi-object affected sets, and full characteristic coverage remain unsupported extensions. The represented evaluator no longer conflicts with base-setting or Equipment-style additive P/T effects. |
| Durations | **YELLOW** | **YELLOW** | CR 611.2a and 514.2 represented “until end of turn” semantics are now structurally stronger: effects survive through End Step and expire only on entry to engine-owned Cleanup; marked damage clears at the same boundary. Persistent modifiers survive. Independent probes and regressions verify no premature/late expiration. | End-of-combat, next-turn, “for as long as,” source-linked, attachment-linked, delayed, and conditional durations remain absent. Repeated cleanup under CR 514.3 requires the future trigger/priority loop. |
| Attachments | **YELLOW** | **YELLOW** | CR 301.5, 303.4, 701.3, and 704.5m–n remain unsupported but identity-safe. Main-phase state supplies the correct future sorcery-timing input for Equip; no attachment/equip semantics were added. | Add runtime-ID attachment edges, legality, typed Equip cost/activation, detachment, effects/layers, and attachment SBAs. |
| Deterministic RNG | **RED** | **GREEN** | CR 103.3/701.20 represented randomness now flows through one game-owned `DeterministicRNG`. Every consumption records a contiguous sequence, semantic domain, operation, result, and before/after state digests. State can be exported and restored for exact continuation. Opening libraries retain the exact legacy `random.shuffle` permutation and stream state, so all five acceptance trajectories remain unchanged. | New random operations must use the same scoped service. Player-verifiable random procedures, multiplayer shared randomness, cryptographic commitments, and Oracle-specific random choices remain unsupported extensions. |
| Invariants | **YELLOW** | **YELLOW** | RNG records now join characteristic, stack, trigger, zone, and identity invariants: sequences must be contiguous, state transitions must form one chain, and the ledger tail must match the current stream digest. Adversarial tampering is rejected. | Add global conservation, checks at every transaction, option/state versioning, encapsulated collections, and cross-object effect causality. |
| Rules Engine ↔ Card Interpreter ↔ Pilot separation | **GREEN** | **GREEN** | The engine owns effect registration/validation and the sole retained RNG service; interpreter and pilot code cannot own or consume random state. Existing interpreter-derived modifiers enter the layer pipeline, and pilots cannot write effects, characteristics, or randomness. | Preserve this boundary for broader Oracle effect construction, random choice requests, affected-set selection, attachments, copies, and type/ability changes. |

No row is UNKNOWN: current rules, authoritative data, committed history, candidate code, and executable
probes are sufficient for all twenty classifications.

## Classification changes

### Deterministic RNG: RED → GREEN

The previous RED condition was structural: game construction created a local `random.Random(seed)`,
shuffled two libraries, and discarded the stream. Any later random operation would have required a
second source or an unreplayable control path. Engine 0.8h replaces that local use with one retained,
game-owned service. Its typed records capture sequence, domain, operation, result, and state-chain
digests, while export/restore proves exact continuation from serialized state.

GREEN is scoped to represented random operations. Opening-library shuffles preserve the exact prior
algorithm, permutations, and continued stream state. Future Oracle-specific random choices remain
unsupported, but they extend this service instead of introducing a competing randomness path. No
Foundation Matrix row remains RED.

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
| Two legacy-compatible shuffles | Exact permutations and subsequent stream state match `random.Random(seed)`. | Centralization does not change represented gameplay randomness. |
| Consecutive scoped RNG operations | Contiguous records retain domain, operation, result, and matching before/after digests. | Every represented consumption is auditable. |
| Export, JSON round trip, and restore | Restored service produces the exact next result and state digest. | Replay can resume from retained state. |
| Empty domain / invalid bound | Rejected with no ledger entry or stream advance. | Unscoped or malformed random requests cannot consume state. |
| Ledger sequence/state tampering | Invariant failure. | Corrupted randomness evidence cannot pass validation. |
| Static random-source inspection | Only `DeterministicRNG` constructs `random.Random`. | Engine, interpreter, pilot, and runner cannot create parallel streams. |
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

## Architectural dependency probes after 0.8h

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
- **Casey Jones / future random choices:** the game-owned service now supplies a scoped, logged,
  replayable random operation path. No Casey Jones behavior was implemented; its currently
  unsupported semantics remain explicit until the interpreter and rules engine represent the actual
  choice requested by Oracle text.

The RNG foundation removes the discarded-stream conflict and supplies the sole path required by
future random operations without implementing any new card behavior or Action.

## Decision answers

1. **Is Deterministic RNG still RED?** No. It is **GREEN** for represented random operations.
2. **Is the stream retained?** Yes. `Game` owns one `DeterministicRNG` for its lifetime.
3. **Is every represented consumption auditable?** Yes. Sequence, domain, operation, result, and
   before/after state digests are recorded.
4. **Can execution resume exactly?** Yes. Exported state survives a JSON round trip and restoration
   produces the exact next result and state.
5. **Did shuffle behavior change?** No. Opening-library permutations and all five gameplay
   trajectories exactly match the prior implementation.
6. **Can callers consume malformed or unscoped randomness?** No. Such requests fail without state
   advancement or a ledger entry.
7. **Was any card-specific random behavior implemented?** No. Unsupported Oracle semantics remain
   explicit.
8. **How many REDs remain?** **0**.
9. **Next single architectural correction?** None. The authorized cycle stops at zero RED.

## Remaining RED priority

None. The Foundation Matrix has reached **zero RED**. Ten YELLOW rows describe explicit unsupported
extensions, not architectural conflicts, and do not authorize another checkpoint in this cycle.

## Acceptance and validation evidence

Acceptance outcomes are unchanged from Engine 0.8g. Unsupported telemetry remains **81 events / 23
exact fragment pairs**, and block-restriction rejections remain **0/2/0/1/3** by seed, six total.

| Seed | Winner / ending turn | Unsupported events / seed pairs | Block rejections | Final stack |
| --- | --- | --- | ---: | ---: |
| 7001 | Raphael / 16 | 14 / 13 | 0 | 0 |
| 7002 | Leonardo / 17 | 14 / 8 | 2 | 0 |
| 7003 | Leonardo / 17 | 19 / 13 | 0 | 0 |
| 7004 | Leonardo / 21 | 21 / 18 | 1 | 0 |
| 7005 | Raphael / 16 | 13 / 8 | 3 | 0 |

Duplicate candidate runs match exactly per seed. Candidate snapshots are intentionally not
byte-identical to 0.8g because Engine 0.8h adds the RNG state digest, consumption ledger, and a new
engine version. Winners, ending turns, unsupported counts, exact semantic pairs, block rejections,
and gameplay trajectories are unchanged.

Validation at audit time:

- focused RNG, Layers, and Trigger suites: **18 passed**;
- focused `test_engine08h_rng.py`: **6 passed**;
- full suite: **179 passed, 1 skipped**;
- Ruff format: clean;
- Ruff check: clean;
- `git diff --check`: clean;
- deterministic duplicate Acceptance Match #001 seeds 7001–7005: exact per-seed matches;
- authoritative card-data and 0.8a–0.8g boundary tests: included in the passing full suite.

## Governance boundary

This re-audit changes only this document. Engine 0.8h implementation/tests remain uncommitted and
unmodified by the audit. No card-specific random behavior, Equipment/attachment, full priority
sequencing, counterspell, new Action, deck, prototype, historical evidence, calibration, or smoke
test was added or changed.
