# Scry Action Acceptance Audit #1

## Decision

**ACCEPT — Scry is suitable to bank with its documented bounded coverage.**

The audited candidate is the uncommitted Scry implementation on
`agent/cardcade-scry`, based on evidence checkpoint
`72bb822476c11e21cbc13eec664dba4754b38196`. This was an evidence-only audit:
implementation and tests were not modified.

## Audit scope and authority

The rules baseline was the Wizards of the Coast *Magic: The Gathering
Comprehensive Rules*, 7 August 2026 edition, rule 701.22:

- 701.22a requires looking at the top N cards, putting any number on the bottom
  in any order, and putting the rest on top in any order;
- 701.22b says scry 0 produces no scry event;
- 701.22c covers simultaneous multiplayer Scry and remains outside Cardcade's
  represented deterministic 1v1 delivery scope;
- 701.22d places the Scry event after the process completes, even where some or
  all component actions were impossible.

Authoritative source:
<https://media.wizards.com/2026/downloads/MagicCompRules%2020260807.txt>

The candidate intentionally represents positive, fixed-N Scry only. Dynamic
amounts and Scry 0 are explicit non-executable limitations; the authoritative
472-print / 332-Oracle-object snapshot contains no recognized Scry 0 fragment.

## Rules correctness

Executable inspection and adversarial probes confirmed:

- the library's end is the authoritative top, and the engine inspects
  `min(N, library size)` objects in top-first order;
- every partition of the inspected cards is available, including putting zero
  cards or all cards on the bottom;
- both retained-top and moved-bottom groups allow every ordering;
- `ScryOption.top_ids` is top-first and is reversed only when written back to
  the engine's end-backed library representation;
- `ScryOption.bottom_ids` is bottom-first and is written at the library's
  beginning in that order;
- a library smaller than N inspects only its available cards;
- an empty library accepts the sole empty choice, preserves the empty library,
  and emits the positive-N Scry event required by 701.22d;
- successful transactions preserve the exact object-identity set and library
  size.

The grammar recognizes only an explicit `scry N`, `scry X`, or `scry that many`
instruction. The last two are recognized but non-executable. Look/top-N
selection, draw, surveil, explore, reveal, reorder, mill, and search text do not
enter the Scry program.

## Hidden information and pilot boundary

The inspected information path is:

`Interpreter → Engine → immutable ScryView/ScryOption values → Pilot → Engine
revalidation → authoritative library mutation`.

The engine retains the sole authoritative `CardObject` library. `ScryView`
contains immutable `(object_id, name)` values only for the currently inspected
top cards; `ScryOption` contains immutable ID tuples. Neither contains an
authoritative object or a deeper-library value. The pilot receives no `Game`,
`PlayerState`, library list, or mutable card object.

`GameView` contains public hands and battlefield views but no library contents.
The opposing pilot is never passed the active player's `ScryView`. Ordinary
`ActionOption` values do not contain Scry information. `ScryEvidence` is frozen
internal audit evidence and is not included in `GameView`; the acceptance
snapshot's detailed event log is runner/audit output produced after engine
execution, not pilot input. The acceptance runner passes only `ScryView` and
legal choices into `choose_scry`.

No mutable authoritative value crosses this boundary. A deliberately poor
`PassingPilot` choice that moves every inspected card to the bottom remains
legal, demonstrating that legality is independent of strategy.

No material hidden-information leak was found.

## Identity and transactionality

The engine enumerates legal choices from authoritative inspected object IDs,
then revalidates the returned immutable value against that exact option set and
the unchanged library. Independent probes and the focused suite confirmed:

- fabricated and foreign-library IDs are rejected;
- stale choices are absent from the current option set and rejected;
- duplicate, omitted, and extra IDs are rejected;
- chooser-side library mutation is detected and the pre-transaction library is
  restored;
- failed choices append neither typed Scry evidence nor a commit event;
- successful choices preserve runtime object identity and cause no duplication
  or disappearance;
- submitted top/bottom order is reproduced exactly.

The engine validates complete membership before commitment and additionally
checks the replacement library's size and Python object-identity set before the
single slice assignment.

## SemanticCoverage and corpus reconciliation

An independent pass over unique Oracle IDs in the authoritative snapshot found
seven objects and seven fragments. All seven have a bounded fixed positive
payload; two have a currently executable parent and follow-up.

| Oracle object | Payload | Parent/context | Follow-up | Full fragment | Limitation |
| --- | --- | --- | --- | --- | --- |
| April O'Neil, Kunoichi Trainee | executable | executable direct ETB | executable | yes | none |
| Dream Beavers | executable | unsupported | executable | no | `scry_preceding_or_trigger_context_not_implemented` |
| Hamato Guardian Stance | executable | unsupported | executable | no | `scry_preceding_effect_not_implemented` |
| Insectoid Exterminator | executable | unsupported conditional context | executable | no | `scry_condition_context_not_implemented` |
| Lita, Little Orphan Amphibian | executable | represented Alliance choice | executable | yes | none |
| Nobody | executable | unsupported | executable | no | `scry_preceding_or_trigger_context_not_implemented` |
| Path of Ancestry | executable | unsupported mana-spent trigger context | executable | no | `scry_preceding_or_trigger_context_not_implemented` |

Exact membership totals and independently reproduced digests:

| Set | Objects / fragments | SHA-256 |
| --- | ---: | --- |
| Recognized | 7 / 7 | `e62415c25929c3022801aefbcec0a0f562bba372d9ed15f2021d536179ae71a2` |
| Bounded payload executable | 7 / 7 | `e62415c25929c3022801aefbcec0a0f562bba372d9ed15f2021d536179ae71a2` |
| Fully supported | 2 / 2 | `8b1050d4ce183e29ad65f2a3b59346f2704db3bf7e5053990d732c86c5870f96` |

The frozen-roster intersection remains five recognized/bounded cards across
three decks: April O'Neil, Dream Beavers, Hamato Guardian Stance, Insectoid
Exterminator, and Lita. Only April and Lita are fully supported.

The generic `SemanticCoverage` value independently retains payload, parent,
follow-up, full-fragment, and limitation state. Recognition or payload
executability does not upgrade an unsupported parent. Unsupported activation,
trigger, condition, preceding effect, follow-up, and dynamic-amount probes all
retain explicit limitations.

The seven pre-existing context-sensitive UNKNOWN objects remain unchanged:

- Arcane Signet
- Chromatic Lantern
- Command Tower
- Double Jump // Flying Kick
- Exotic Orchard
- Fast Forward
- Plague of Vermin

## Delivery architecture

Scry uses the existing typed creature-entry event, trigger detection, pending
trigger queue, authoritative triggered-ability stack object, stack resolution,
and generic Alliance modal infrastructure. The engine re-derives and rechecks
`SemanticCoverage` when resolving a stacked Scry ability.

Direct ETB delivery requires both executable payload and executable parent plus
the generic `When … enters, scry` construction. Alliance delivery is selected
through the existing modal header/mode mechanism. Unsupported parents do not
enqueue or deliver the child payload.

Searches of interpreter, engine, pilot, and runner code found no source-card
name dispatch, April-specific branch, Scry seed condition, roster special case,
or hard-coded Scry result. The acceptance pilot's deterministic keep-on-top
choice is strategy only and is revalidated by the engine.

## Acceptance Match evidence

Seeds 7001–7005 were each replayed twice. Every duplicate JSON snapshot was
byte-identical.

| Seed | Winner / ending turn | Unsupported events / seed pairs | Scry transactions |
| ---: | --- | ---: | ---: |
| 7001 | Raphael / 16 | 12 / 12 | 2 |
| 7002 | Leonardo / 17 | 14 / 8 | 0 |
| 7003 | Leonardo / 17 | 15 / 12 | 3 |
| 7004 | Leonardo / 21 | 18 / 16 | 2 |
| 7005 | Raphael / 16 | 10 / 7 | 1 |

Aggregate evidence:

- unsupported telemetry moved from 78 events / 23 exact pairs to 69 / 21;
- eight Scry transactions occurred, all from April O'Neil's Scry 2 ETB;
- every transaction inspected two cards and selected the legal keep-all choice,
  with `top_ids` exactly equal to the pre-commit `inspected_ids` and an empty
  `bottom_ids` tuple;
- the existing 16 Deal Damage transactions remain;
- six block-restriction rejections remain;
- zero invariant violations occurred;
- winners and ending turns are unchanged.

The nine-removed-events/eight-transactions difference is correct. Eight resolved
April O'Neil objects each formerly emitted one unsupported Scry line and now
execute one Scry transaction. One Lita resolved and formerly emitted its Scry
mode as unsupported during ability reporting, but no later creature entry
selected and delivered that Alliance mode in the acceptance run. Recognizing
Lita's represented mode correctly removes that stale unsupported report without
inventing a transaction. Thus exactly nine events across the April and Lita
pairs disappear while only eight Scry transactions execute.

## Explicit exclusions

The candidate does not claim or execute:

- dynamic Scry amounts or Scry 0;
- unsupported activated, triggered, or conditional delivery;
- unsupported preceding or follow-up effects;
- Casey-style top-four selection or generic top-card selection;
- surveil, explore, draw, mill, search, reveal, or generic reorder operations;
- simultaneous multiplayer Scry/APNAP handling.

Those limits remain attached to the Scry coverage record. No excluded semantic
was observed to route through `Game.scry`.

## Validation

| Validation | Result |
| --- | --- |
| Full suite | `281 passed, 1 skipped` |
| Focused Scry suite | `19 passed` |
| Generic SemanticCoverage suite | `5 passed` |
| Card-data integrity suite | `5 passed` |
| Ruff format check | clean |
| Ruff check | clean |
| `git diff --check` | clean |

The candidate implementation/test diff fingerprint before writing this report
was `808ad224c44d4764bb356e920d98c5e5441aa534`, providing an audit guard that
the evidence-only report did not alter the candidate.

## Final recommendation

**ACCEPT — Scry is suitable to bank with its documented bounded coverage.**
