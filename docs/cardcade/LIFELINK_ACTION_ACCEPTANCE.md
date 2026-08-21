# Lifelink Damage-Result Processing Acceptance Audit #1

Status: **ACCEPT**  
Audit date: 2026-08-20  
Branch: `agent/cardcade-lifelink`  
Parent baseline: `47eee13482efef625e2a11f75163f71ac567342d`  
Evidence checkpoint: `dae9644189132438b48fb75a8a3e85883243c902`  
Audited candidate fingerprint: `50b837cb5d0801e860ccf387a26a7e7ad84fec5a`

## Audit integrity

This was an evidence-only audit. No implementation or test file was modified. The only audit
artifact created is this report.

The candidate fingerprint was independently reproduced as SHA-1 of the newline-joined,
path-sorted manifest of complete-file SHA-256 values for:

- `src/tmnt_design_studio/card_interpreter07.py`;
- `src/tmnt_design_studio/engine07.py`;
- `tests/test_lifelink_action.py`.

The reproduced fingerprint remained
`50b837cb5d0801e860ccf387a26a7e7ad84fec5a` after all probes and validation.

## Authoritative rules basis

The audit used Wizards of the Coast's current Comprehensive Rules text, effective August 7,
2026, from `https://magic.wizards.com/en/rules`:

- CR 120.3f: damage dealt by a source with Lifelink causes that source's controller to gain that
  much life in addition to the damage's other results;
- CR 120.4: damage is dealt and then processed into results before the damage event occurs;
- CR 702.15a: Lifelink is a static ability, not a triggered ability;
- CR 702.15b: the source's controller, or owner if it has no controller, gains the life;
- CR 702.15c–d: last known information and nonbattlefield zones matter in broader Magic;
- CR 702.15e: simultaneous damage by distinct Lifelink sources creates distinct life-gain events;
- CR 702.15f: multiple instances on one object are redundant;
- CR 704.5a/g: player loss and lethal marked damage are checked as state-based actions.

The accepted slice is deliberately narrower than complete CR 702.15. Every represented damage
source has an authoritative controller. The engine supports intrinsic Lifelink on an authoritative
battlefield or Stack source through its existing represented damage paths. It does not claim
general damage from arbitrary zones, a controllerless-owner fallback, last-known-information cases
where a source leaves before an effect deals damage, or prevention/replacement processing.

## Independent coverage reconstruction

The 472-print / 332-Oracle-object authoritative TMT/PZA/TMC snapshot was enumerated independently
by Oracle ID and fragment. Exact results were:

| Classification | Objects / fragments | Membership digest |
|---|---:|---|
| Recognized | **6 / 6** | `315914585ff72e84306d6e16fba01646ae382c96330f20e6ddf540efbec02761` |
| Bounded payload executable | **2 / 2** | `e1645c8d6fbcd411ecbd507968b89bdc7293567531aee5e833cf83ab38c80e53` |
| Fully supported | **2 / 2** | `e1645c8d6fbcd411ecbd507968b89bdc7293567531aee5e833cf83ab38c80e53` |

Exact recognized membership:

| Card | Oracle ID | Classification | Explicit limitations |
|---|---|---|---|
| Foot Mystic | `2043fbde-48c4-4a77-8911-8991d77de1eb` | executable / full | none |
| Hidden Hideout | `b639e1fe-d099-4cab-a0d0-a1b33c7f31dd` | recognized only | activation context; compound semantics |
| Leonardo, Cutting Edge | `933fe6e5-8d00-4411-aa54-7780382c1ea6` | executable / full | none for its standalone Lifelink fragment |
| Leonardo, the Balance | `46ea8d02-b087-44f7-8403-93ffc1d3a8ad` | recognized only | activation context; compound semantics |
| Shadowspear | `8b27326f-e7b8-4a4d-b589-df459246d19a` | recognized only | attachment context; compound semantics |
| The Last Ronin | `e1865bec-1744-40c2-9031-7d6363be5333` | recognized only | trigger context; compound semantics |

The frozen roster intersection is exactly **Foot Mystic** and **Leonardo, Cutting Edge**, spanning
the Leonardo, Shredder, and Splinter decks: **2 cards / 3 decks**.

`SemanticCoverage` remains truthful. Keyword recognition does not make an activation, attachment,
team grant, triggered temporary grant, or compound instruction executable. The seven pre-existing
context-sensitive UNKNOWN objects remain outside the Lifelink recognition set.

## Architecture and damage-result boundary

Static Lifelink recognition is Oracle-derived and contains no source-card-name dispatch. Runtime
evaluation requires the source object itself to be authoritative on the battlefield or Stack and
the interpreted Lifelink fragment to be fully supported. Token keyword facts use the same runtime
source evaluation and do not enable any unsupported grant mechanism.

The implementation does not introduce another damage engine. There are exactly two delivery call
sites into the Lifelink result operation:

1. the existing typed noncombat `DamageTransaction` path after authoritative damage mutation;
2. the existing combat-damage assignment path after its authoritative assignments are applied.

The result operation revalidates authoritative source membership and Lifelink, takes the source's
authoritative controller, performs a typed positive life gain, and records immutable evidence.
Fabricated damage-controller claims are rejected before damage or life mutation.

No Lifelink call site exists in life loss, destroy, toughness modification, counter, or zone-change
processing. Unsupported grants do not make `evaluated_lifelink` true. Zero/nonpositive assignments
produce no damage assignment and no Lifelink evidence. Prevention and replacement are not
represented and are not claimed as supported.

## Independent executable probes

The audit independently exercised the following rather than relying only on the candidate's tests:

- unblocked combat damage to a player gained exactly the damage dealt;
- blocked combat damage to a creature gained exactly the marked damage dealt;
- the existing noncombat `DamageTransaction` path produced the same bounded result;
- one Trample source splitting damage between blocker and defending player created one life-gain
  event equal to the combined damage, not two gains;
- First Strike created a gain in the first-strike step;
- Double Strike created one independently attributable gain in each damage step using that step's
  actual assignment;
- two simultaneous Lifelink sources created two distinct life-gain events;
- a source that died or moved after damage left its immutable Lifelink evidence intact;
- a damaged creature died only at the existing SBA boundary after damage and Lifelink processing;
- zero power and negative effective power produced no damage or life gain;
- fabricated equal-valued and stale source references were rejected;
- a fabricated transaction controller was rejected atomically;
- a represented controller change caused the new authoritative controller, not the owner, to gain
  life;
- unsupported temporary-grant text did not grant executable Lifelink.

### Survival and ordering probe

The defending player began at 2 life, blocked a 5-power Trample attacker with a 3/3 Lifelink
creature, and received 2 excess damage while the blocker dealt 3 damage. During the same damage
processing the defending player moved from 0 to 3 life from legitimate Lifelink and therefore did
not lose at the subsequent SBA check.

Event and mutation order was independently established as:

1. authoritative damage assignments applied;
2. Lifelink life gain and `LIFE_GAINED` event created;
3. applicable life-gain trigger detected but retained as pending;
4. Lifelink evidence committed;
5. lethal-damage and player-loss SBAs checked;
6. represented pending trigger placed on the Stack and resolved.

This proves Lifelink is a damage result rather than a delayed triggered ability, while represented
trigger delivery is not performed prematurely before SBAs.

## Immutable evidence

Each bounded transaction preserves:

- the Lifelink life-gain event ID;
- authoritative source runtime ID;
- controller index;
- actual aggregate damage amount for that source's damage event;
- combat/noncombat classification and combat-damage step where applicable;
- damaged runtime targets and/or player recipients;
- life immediately before and after the gain.

The immutable record's type and presence establish that Lifelink was authoritatively applicable;
the stored amount is also the recorded life gained. Combat records link to immutable assignments by
source, step, recipients, and amount. Noncombat records link to the existing damage log by source,
recipient, and amount. Evidence remained valid after source and recipient zone changes and
serialized deterministically in duplicate snapshots.

The broader engine still lacks a universal damage-event aggregate ID spanning every damage form.
That does not invalidate this bounded evidence because every represented Lifelink result is
uniquely reconstructable from its immutable source, step/path, recipients, amount, and before/after
life facts. Future prevention/replacement or simultaneous multi-effect work must extend this
contract rather than infer attempted damage from nominal power.

## Acceptance Match reconstruction

The parent-baseline sources were independently archived and executed, reproducing:

- **42 unsupported events / 15 exact pairs**;
- seed 7004 contained exactly two unsupported occurrences of
  `Leonardo, Cutting Edge` / `Lifelink` with reason `oracle_ability_not_implemented`.

The candidate produced:

- **40 unsupported events / 14 exact pairs**;
- exactly **1 Lifelink transaction**;
- **0 invariant violations**.

The exact two removed events and one removed pair are those two standalone Cutting Edge Lifelink
occurrences in seed 7004. No unsupported parent, grant, attachment, trigger, or compound Lifelink
fragment disappeared.

The real transaction occurred in seed 7004, turn 9, regular combat-damage step:

- source: Leonardo, Cutting Edge, runtime `object-000161`;
- recipient: Null Group Biological Assets, runtime `object-000166`;
- actual combat damage dealt: **1**;
- source controller: Leonardo player, index 0;
- controller life before: **20**;
- Lifelink life gained: **1**;
- controller life after: **21**.

Null Group simultaneously dealt 3 damage back. Cutting Edge and Null Group then left the
battlefield for lethal damage at the SBA boundary. Cutting Edge's already-represented life-gain
trigger had been detected before it left, was stacked only after SBAs, and resolved without
fabricating the departed permanent. The durable Lifelink result remained independently auditable.

The telemetry reduction is therefore execution-backed: the exact recognized fragment was present
on an authoritative source, that source actually dealt positive damage, and the correct controller
actually gained the matching amount. It is not caused merely by recognition.

## Deterministic replay

Seeds 7001–7005 were run twice. Each duplicate JSON artifact was byte-identical.

| Seed | Winner | Ending turn | Unsupported events / pairs | Lifelink transactions |
|---:|---|---:|---:|---:|
| 7001 | Raphael | 16 | 9 / 9 | 0 |
| 7002 | Raphael | 16 | 5 / 4 | 0 |
| 7003 | Leonardo | 19 | 11 / 9 | 0 |
| 7004 | Leonardo | 21 | 11 / 10 | 1 |
| 7005 | Raphael | 16 | 4 / 4 | 0 |
| **Aggregate** | | | **40 / 14** | **1** |

All runs contained zero invariant violations. Winners and ending turns match the expected candidate
trajectories.

## Validation

| Validation | Result |
|---|---:|
| Full suite | **415 passed / 1 skipped** |
| Lifelink | **16 passed** |
| Engine/combat/strike | **71 passed** |
| Strike plus turn-state focused subset | **39 passed** |
| Trample | **22 passed** |
| Deal Damage | **29 passed** |
| SemanticCoverage plus card data | **10 passed** |
| Identity/SBA/Stack/cost/trigger/layer/Token/Return regressions | **117 passed** |
| Ruff format check | clean, 37 files |
| Ruff check | clean |
| `git diff --check` | clean |

No material blocker remains within the authorized bounded scope.

## Recommendation

**ACCEPT — bounded Lifelink damage-result processing is suitable to bank.**
