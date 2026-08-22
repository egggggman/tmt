# Acceptance Stage #002 Readiness Audit

Audit baseline: `491b196377c1e33fdbccde21870f8ae2790085de`  
Design under audit: `ACCEPTANCE_STAGE_002_DESIGN.md`  
Design SHA-256 before/after audit: `d740d532f5e0c61d90b00c479c09100760b6353a23b18bc4621093ded826c624`  
Authoritative snapshot: 472 prints / 332 Oracle objects, SHA-256
`56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`

This was an evidence-only audit. No design, engine, Pilot, deck, or test file was modified. No Stage
#002 match was run.

## Frozen-pairing evidence

### Donatello vs. Krang

Static exposure is correctly artifact-heavy: both Prototype 0.2 decks repeatedly contain Fugitive
Droid, Buzz Bots, Crustacean Commando, Sewer-veillance Cam, Bespoke Bō, and artifact-focused
legends. Oracle evidence includes artifact-entry counters (`Donatello, Way with Machines`), Affinity
and artifact-count P/T/Draw (`Krang, Master Mind`), artifact-copy tokens, sacrifice activations,
counterspells, cycling, and compound Draw.

Currently executable semantics are much narrower than the design's target language suggests:
ordinary casting/cost/Stack/Priority, artifact and creature runtime identity, zones, combat, and
SBAs execute; `Donatello, Gadget Master` has bounded executable Sneak. The authoritative interpreter
does not classify the pairing's artifact-entry trigger, Affinity reduction, artifact-count
characteristics, sacrifice activations, counterspells, token copies, cycling, or compound Draw as
fully supported Action paths.

Intended target that is defensible: repeated artifact object/type/zone handling and explicit
unsupported-boundary preservation. Intended targets that are not yet evidence-backed as execution
claims: artifact-count dependency, artifact-entry counter delivery, or Affinity. This pairing is
dominated by unsupported thematic mechanics, but still supplies useful core-permanent and negative-
boundary conformance if relabeled accordingly. It is poor evidence for an "artifact infrastructure
executes" claim.

### Michelangelo vs. Bebop & Rocksteady

Static exposure supports the design's token/resource claim. Oracle text includes fixed and variable
Mutagen creation, Food creation/reminders, canonical Food activation, Mutagen activation, token
replacement/quantity effects, Trample, sacrifice-or-discard combat triggers, and compound removal.
Representative cards include Courier of Comestibles, Zoo Escapees, Michelangelo, Weirdness to 11,
Mutagen Man, Living Ooze, Tainted Treats, and Bebop & Rocksteady.

Currently executable named semantics include intrinsic Trample on Mutagen Man and bounded Sneak on
Michelangelo, Improviser, plus ordinary casting/combat/cost/zone/SBA behavior. The corpus inventory
finds no fully supported Create Token parent in these two decks and no fully supported complete Food
creation context. Canonical Food activation is executable only if an authoritative Food permanent
exists; these decks do not make Food creation itself fully executable. Mutagen activation, variable
token quantity, replacement effects, leaves/ETB parents, and sacrifice-or-discard choice remain
unsupported.

Intended target that is defensible: recognition/support-boundary evidence for Food, Mutagen, token,
and compound parent semantics, plus Trample/Sneak/core combat execution. Intended targets that are
not guaranteed: token creation, token cessation, Food activation, or token counter/layer execution.
The pairing is not wholly dominated because represented combat and Sneak can execute, but the
design must not promise token lifecycle execution from static exposure alone.

### Splinter vs. Shredder

Static exposure matches the design: multiple Sneak cards, Foot Mystic Lifelink/Disappear, Shark
Shredder Double Strike, Menace, permanent-departure counters, Draw/life-loss combat triggers,
removal, and creature-heavy combat occur across the two black decks.

Currently executable semantics are comparatively strong: Splinter, Oroku Saki, Shark Shredder, and
Shredder, Unrelenting expose bounded Sneak; Shark Shredder exposes intrinsic Double Strike; Foot
Mystic exposes intrinsic Lifelink. These reuse Stack/Priority, return-as-cost identity, tapped-and-
attacking entry, combat steps, damage-result life gain, legend/lethal SBAs, and cleanup. Menace,
Disappear token delivery, generic permanent-left counters, and compound Draw/life loss remain
explicitly unsupported.

This is the best-supported Stage #002 pairing. Its intended Sneak, strike, Lifelink, combat, zone,
and SBA targets are evidence-backed, subject to actual draw/cast/choice reach. Departure-event and
counter targets are primarily opportunity/negative-boundary targets, not guaranteed execution.

### April O'Neil vs. Casey Jones

Static exposure matches the design's interaction claim: both decks contain artifacts; April adds
counterspells, artifact ETB/leaves choices, Draw/discard, cycling, and returns; Casey adds Equipment,
artifact-token text, Manhole Missile, Null Group Biological Assets, Trample, and Double Strike.

Currently executable named semantics are concentrated on Casey's side: Manhole Missile supports
bounded Deal Damage followed by optional hand-bottom/conditional Draw; Null Group supports bounded
attack-trigger discard/conditional Draw and First Strike; Mutant Town Musicians has intrinsic
Trample. Ordinary targeting, costs, Stack/Priority, damage marking/SBAs, hidden-zone ordering, and
combat execute. Casey's ETB top-four filter is a reliable reached-unsupported fixture if Casey
resolves. April's broader Draw/discard triggers, Negate, artifact activations, Equipment/equip,
artifact-copy/token parents, and broader target/choice semantics remain unsupported.

This pairing is asymmetric but useful: it can reproduce several accepted transactions while
pressuring explicit unsupported interaction. Scry is not a supported guaranteed target in either
deck, and Equipment-granted Double Strike cannot be counted as executed without Equip/attachment
support.

## Major-system matrix

Legend: **E** = executable if the relevant card/state is reached; **U** = useful explicit unsupported
boundary; **—** = no meaningful targeted exposure.

| Pairing | Core cast/cost/Stack/Priority | Identity/zones/SBAs | Combat/damage | Sneak | Strike | Trample/Lifelink | Tokens/Food | Choices/library | Artifact dependencies | Triggers |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Donatello / Krang | E | E | E | E | — | — | U | U | U | U |
| Michelangelo / Bebop & Rocksteady | E | E | E | E | — | E | U | U | — | U |
| Splinter / Shredder | E | E | E | E | E | E | U | U | — | E/U |
| April / Casey | E | E | E | — | E/U | E | U | E/U | U | E/U |

The matrix confirms useful diversity, but it also exposes a design overclaim: the artifact and token
pairings predominantly observe unsupported boundaries rather than execute their named thematic
systems.

## Important represented systems omitted by all four

No pairing provides a fully supported, reliably reachable parent for accepted Create Token or
canonical Food activation. None provides the accepted Targeted Return lifecycle used by Prehistoric
Pet. No pairing has a clearly fully supported Scry parent comparable to Acceptance #001. These are
important accepted subsystems and must be listed as Stage #002 exclusions unless the static manifest
proves a fully supported occurrence overlooked by this audit.

Other incompletely sampled foundations include actual token cessation, Food Stack/source evidence,
Trample split assignment (rather than intrinsic keyword presence), failed-Draw loss, and the
specific targeted-return new-object lifecycle. Stage #002 need not cover every accepted Action, but
its aggregate report must not imply that all represented systems generalized.

## Run arithmetic and duplicate semantics

The design arithmetic is correct:

- 4 pairings × 2 fixed seeds × 2 seat orientations = **16 distinct games**;
- one exact duplicate of every distinct game = **32 total executions**;
- duplicates are reproducibility evidence and do not increase the distinct-game denominator.

Using the same seed across mirrored orientations is deterministic and suitable for a seat-order
probe, provided orientation is part of the run identity and no win-rate claim is derived.

## Stop-condition enforceability

| Stop condition | Current mechanical status |
| --- | --- |
| Invariant violation | **Enforceable.** `check_invariants()` and serialized violation evidence can fail the run. |
| Nondeterminism | **Enforceable.** Canonical duplicate artifacts can be compared byte-for-byte, including RNG evidence. |
| Illegal mutation | **Partly enforceable.** Existing transaction/invariant tests and before/after evidence catch represented violations, but the Stage runner needs a canonical failure flag when option revalidation or mutation atomicity fails. |
| Silent approximation | **Not generally enforceable prospectively.** Current registration telemetry identifies unsupported text, but there is no universal opportunity/result join proving that an unsupported semantic mattered and was declined rather than silently bypassed. |

An invariant-clean run is therefore necessary but insufficient for the design's full stop contract.

## Three-class reporting readiness

- **EXECUTED:** available for Actions with reconstructive immutable evidence and for core engine
  transitions carrying authoritative IDs and before/after state. It is not uniformly keyed to the
  specification's Oracle/face/fragment occurrence identity.
- **PRESENT / UNREACHED:** partially available from authoritative object/zone history and registered
  unsupported fragments. Complete first/last involvement history and canonical fragment keys are
  not yet emitted prospectively.
- **REACHED / UNSUPPORTED:** **not authoritatively available as a generic runtime class**. Existing
  `unsupported_semantics` events are emitted on text registration. Trigger-condition matches,
  rejected activation/cast opportunities, combat-restriction evaluation, replacement conditions,
  and compound instruction reach do not share a generic typed opportunity witness.

Retrospective correlation cannot fill this gap without violating the accepted conservative model.
Consequently Stage #002 cannot currently produce the report it makes a pass criterion.

## Required readiness correction

Before banking or executing the 16-game matrix, add a separate evidence-only instrumentation
checkpoint—no gameplay behavior—that:

1. emits canonical Oracle/face/fragment occurrence keys for PRESENT evidence;
2. emits typed opportunity witnesses for trigger, activation/cast, target/choice, combat restriction,
   replacement, and sequential-instruction boundaries actually encountered;
3. joins every explicit unsupported decision to its opportunity ID and static `SemanticCoverage`;
4. joins existing reconstructive Action results to the same semantic occurrence key;
5. produces deterministic per-class manifests/digests and a machine-failing flag for silent
   approximation or unclassified reached opportunities;
6. validates the instrumentation on focused synthetic fixtures before any Stage #002 match.

The design should also relabel Donatello/Krang and Michelangelo/Bebop targets so artifact-count,
Affinity, token creation/cessation, and Food activation are not promised as executed coverage.
Accepted subsystems absent from the matrix must be explicit exclusions, not assumed aggregate
coverage.

This is an evidence architecture correction, not Action #13 and not permission to change engine
gameplay, decks, or Pilot strategy.

## Verdict

**NOT READY — the current runtime cannot authoritatively distinguish generic REACHED / UNSUPPORTED from PRESENT / UNREACHED, so Stage #002 cannot enforce its conformance and silent-approximation gates; add the bounded opportunity-witness instrumentation checkpoint before execution.**
