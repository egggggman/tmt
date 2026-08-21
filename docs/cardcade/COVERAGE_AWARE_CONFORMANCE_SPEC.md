# Cardcade Coverage-Aware Conformance Specification

Version: 0.1  
Foundation baseline: `98becb91aea5f393a5b5d298a0a4d0f171330b5a`  
Status: evidence specification; no production behavior authorized

## Purpose

Coverage-aware conformance answers a narrower question than static Action coverage: for one
executed game, which exact semantics changed authoritative state, which became actionable but were
explicitly unsupported, and which were merely carried by encountered objects?

The model must not equate card presence with execution, repeated telemetry with distinct semantic
coverage, or a supported child payload with a supported parent/context.

## Conformance classes

### EXECUTED

An exact semantic fragment or subfragment is EXECUTED only when immutable engine evidence links:

`authoritative source/context → announced or generated rules object → validation/cost/choice/target
boundary → Stack/Priority when applicable → resolution or rules processing → authoritative state
result`.

A log message alone is insufficient. Evidence must identify runtime objects and the before/after
facts needed to reconstruct the represented result. A fully supported static rule may also count
when authoritative option generation or characteristic/combat evaluation records that the rule
changed legality or a computed result.

### REACHED / UNSUPPORTED

An exact semantic is REACHED / UNSUPPORTED only when an authoritative opportunity witness proves
that its enabling rules condition occurred and the semantic could affect the next legal decision or
state transition, while `SemanticCoverage` or runtime validation explicitly declines it.

Examples include a trigger event matching a source then present under the required controller, an
activation timing/cost opportunity, a proposed block to which an unsupported restriction applies,
or an alternate-zone cast candidate satisfying the represented filters. Card resolution by itself
does not prove that a later trigger, permission, or restriction was reached.

### PRESENT / UNREACHED

An exact semantic is PRESENT / UNREACHED when its authoritative text is attached to an object that
entered the match's observable authoritative history, but no evidence proves an execution or
actionable opportunity. This includes text on drawn, cast, resolved, moved, or otherwise involved
objects whose enabling condition never occurred—or cannot be proven to have occurred from the
available evidence.

For safety, missing reach evidence defaults to PRESENT / UNREACHED, never EXECUTED. Reports must
mark retrospective uncertainty rather than infer a trigger, legal option, or hidden-zone fact.

The three classes are mutually exclusive for one semantic occurrence. Across a whole match, the
same exact fragment may have occurrences in more than one class; aggregate status is the set of
observed classes, not a forced single label.

## Identity contract

The primary semantic key is:

`Oracle ID + face index + normalized fragment index + exact authoritative fragment hash`.

Runtime occurrences additionally carry source runtime ID, controller, turn, phase/step, and a
monotonic occurrence ID. Action-specific subfragments may add stable absolute spans, but must retain
the enclosing fragment key. Zone changes create new runtime identities under CR 400.7; the semantic
key remains stable while occurrence evidence links old and new IDs explicitly.

Card name is display metadata, not identity or dispatch authority. Print/set/collector identity may
be included for provenance but must not replace Oracle identity.

## Authoritative evidence sources

| Evidence | Permitted claim |
| --- | --- |
| Normalized authoritative card record and immutable zone/object history | PRESENT |
| Typed event plus source/controller/context snapshot | Trigger or rule condition REACHED |
| Engine-generated legal option and revalidation record | Choice, target, cast, or activation REACHED |
| Explicit unsupported decision containing semantic key and opportunity ID | REACHED / UNSUPPORTED |
| Transaction/Stack/trigger/combat/SBA evidence with before/after state | EXECUTED |
| Pilot narration, card-name inference, final state alone, or ordinary diagnostic log | No independent conformance claim |

Existing Action evidence remains authoritative where reconstructive: spell/activation/Sneak
transactions, trigger and Priority lifecycles, damage and combat-step evidence, Scry, Return,
hand-bottom/Draw, discard/Draw, Trample, Lifelink, token creation, and Food activation.

## Relationship to SemanticCoverage

`SemanticCoverage` is a static capability statement. It records payload, parent/context, follow-up,
full-fragment support, and limitations without knowing runtime state.

Conformance is runtime evidence. It consumes a frozen `SemanticCoverage` value and an authoritative
opportunity/result record. It must never infer static support from execution logs or teach
`SemanticCoverage` about engine objects. The dependency remains:

`Action interpretation → SemanticCoverage`  
`SemanticCoverage + runtime opportunity/result → conformance classification`

A payload-executable child under an unsupported parent is not EXECUTED. A fully supported fragment
that never reaches an opportunity is PRESENT / UNREACHED. Unsupported text that becomes actionable
is REACHED / UNSUPPORTED.

## Aggregation rules

1. Count occurrences first; derive exact-fragment and Oracle-object sets separately.
2. Deduplicate exact pairs by semantic key, never by card name alone.
3. Preserve per-seed membership before aggregate union.
4. Report occurrence counts and unique semantic counts side by side.
5. Never add static full-pool or frozen-roster reach to runtime counts.
6. A transaction may execute several subfragments; each needs its own semantic key and shared
   transaction ID.
7. One compound fragment is fully EXECUTED only if its required parent, choices/targets, payload,
   and follow-up all execute truthfully.
8. Repeated presence events for replacement runtime objects remain separate occurrences but one
   exact semantic pair.
9. If evidence proves presence but cannot distinguish reached from unreached, classify PRESENT /
   UNREACHED with `reach_not_proven`.
10. Invariant violations invalidate the affected game as conformance evidence; they are not another
    semantic class.

## Deterministic output contract

The durable output is canonical UTF-8 JSON with:

- baseline SHA, seed, engine version, authoritative data manifest hash, and replay RNG digest;
- semantic keys sorted by Oracle ID, face, fragment index/hash, occurrence turn/step/runtime ID;
- explicit class and reason code;
- opportunity, transaction, Stack, event, and result IDs where applicable;
- exact limitations copied without reordering;
- per-seed counts/sets and aggregate membership digests.

No Python object identity, hash iteration order, wall-clock value, absolute path, or display-only log
text may influence serialization. Duplicate seeded runs must be byte-identical.

## Required opportunity witnesses

Future conformance evidence should distinguish at least:

- trigger condition matched versus source text merely present;
- activation/cast candidate existed versus source merely occupied a zone;
- target/choice set generated versus a choice named in text;
- combat restriction evaluated against a proposed declaration versus keyword present;
- replacement/prevention condition encountered versus replacement text present;
- follow-up instruction reached versus parent object resolved;
- supported transaction committed versus option merely offered or declined.

The current engine need not be changed by this specification. Any later instrumentation proposal is
a separately reviewed validation checkpoint, not Action #13.

## Acceptance gate use

Coverage-aware conformance supports an engine-validation decision, not a coverage percentage or
balance claim. A match is credible when executed claims are reconstructive, reached omissions are
explicit, present-only text is not inflated into runtime coverage, deterministic duplicates match,
and no invariant violation or silent approximation appears.

