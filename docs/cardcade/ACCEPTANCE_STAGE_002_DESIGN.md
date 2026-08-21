# Cardcade Acceptance Stage #002 Design

Design baseline: `98becb91aea5f393a5b5d298a0a4d0f171330b5a`  
Conformance checkpoint: `491b196377c1e33fdbccde21870f8ae2790085de`  
Status: evidence-only design; execution not yet authorized

## Validation question

Does Cardcade remain deterministic, invariant-clean, and truthful about its represented semantic
scope when exposed to all eight frozen decks not used by Acceptance Match #001?

Stage #002 is a conformance-diversity exercise. It is not a tournament, win-rate sample,
calibration run, balance study, smoke test, deck revision, or request for Action #13.

## Design principles

1. Use only the frozen ten-deck roster and authoritative TMT/PZA/TMC snapshot.
2. Preserve every decklist byte-for-byte; Prototype 0.3 remains unauthorized.
3. Cover all eight decks outside Leonardo/Raphael exactly once in the primary pairing matrix.
4. Choose pairings for concentrated semantic pressure, not expected competitiveness.
5. Run both seat orientations so first-player rules and active/nonactive sequencing are exercised.
6. Use a tiny fixed seed set and duplicate every run before considering broader sampling.
7. Classify runtime semantics as EXECUTED, REACHED / UNSUPPORTED, or PRESENT / UNREACHED under the
   accepted conformance specification.
8. Stop on an invariant violation, nondeterminism, illegal option/state transition, silent
   approximation, or evidence that cannot authenticate an executed claim.
9. Do not fail merely because unsupported telemetry is large or a Pilot makes a poor legal choice.

## Primary four-pair matrix

### A. Donatello vs. Krang — artifact infrastructure pressure

Frozen decks: Donatello Prototype 0.2 and Krang Prototype 0.2.

Why selected:

- both decks have the roster's highest artifact concentration, making artifact creatures and
  noncreature permanents routine rather than incidental;
- repeated Fugitive Droid, Buzz Bots, Crustacean Commando, Sewer-veillance Cam, Bespoke Bō, and
  related entries stress type information, battlefield identity, artifact counts, costs, targeting,
  and zone changes;
- Donatello's artifact-entry counter path and Krang's artifact-dependent characteristics expose
  trigger/counter/layer boundaries;
- Affinity, sacrifice activations, counterspells, token copies, cycling, and compound Draw remain
  useful negative-boundary evidence rather than implied support.

Primary represented systems: Stack/Priority, mana costs, artifact/permanent identity, counters,
layers, typed entry events, combat, SBAs, and unsupported-parent preservation.

### B. Michelangelo vs. Bebop & Rocksteady — token/resource and combat pressure

Frozen decks: Michelangelo Prototype 0.1 and Bebop & Rocksteady Prototype 0.1.

Why selected:

- Courier of Comestibles, Zoo Escapees, Michelangelo cards, Mutagen Man, Tainted Treats, and related
  cards concentrate Food/Mutagen/token text;
- the match can distinguish recognized token payloads from unsupported ETB, leaves-battlefield,
  variable-quantity, replacement, activation, and compound-parent semantics;
- represented Trample, Lifelink, counters/layers, damage, token cessation, and SBAs receive a
  different board texture than Acceptance #001;
- Bebop & Rocksteady's attack/block sacrifice-or-discard text tests whether unsupported choices and
  nonmana costs remain explicit at a real combat boundary.

Primary represented systems: token identity and cessation, Food recognition/activation boundary,
combat damage, Trample, Lifelink, counters/layers, sacrifice-zone identity, and trigger opportunity
classification.

### C. Splinter vs. Shredder — villain, departure, and Sneak pressure

Frozen decks: Splinter Prototype 0.1 and Shredder Prototype 0.1.

Why selected:

- both decks generate dense black-creature combat while exposing Sneak through different cards;
- Foot Mystic, Super Shredder, Oroku Saki, Dream Beavers, Squirrelanoids, Shark Shredder, and removal
  spells pressure creature entry/departure provenance, counters, Lifelink, and SBAs;
- accepted Sneak can be exercised outside Leonardo/Raphael, including return-as-cost, Stack/Priority,
  tapped-and-attacking entry, identity replacement, and postcombat cleanup;
- Menace, Disappear, generic leaves-permanent triggers, Draw/life-loss compounds, and broader removal
  remain explicit boundaries whose opportunities should be measured rather than approximated.

Primary represented systems: Sneak, Stack/Priority, combat/strike steps, Lifelink, departure events,
counter/layer state, lethal/legend SBAs, and runtime provenance.

### D. April O'Neil vs. Casey Jones — choices, artifacts, and interaction pressure

Frozen decks: April O'Neil Prototype 0.1 and Casey Jones Prototype 0.1.

Why selected:

- April combines artifact permanents with interaction and Draw/discard text; Casey combines
  Equipment, artifact tokens, Manhole Missile, and Null Group Biological Assets;
- accepted Deal Damage, hand-bottom/conditional Draw, discard/conditional Draw attack triggers,
  Scry/library ordering where encountered, and strike-step semantics can interact in one match;
- Casey's ETB top-four artifact filter supplies a known REACHED / UNSUPPORTED opportunity fixture;
- Equipment/equip, Negate, artifact copy/creation parents, broader Draw, and target/choice expansion
  remain negative boundaries.

Primary represented systems: target identity/revalidation, Deal Damage/SBAs, hidden-zone ordering,
instruction-time choices, discard/Draw trigger provenance, artifacts, Double Strike characteristics,
and unsupported Equipment/counterspell boundaries.

## Run matrix and deterministic budget

Each pair uses two fixed seeds in both seat orientations:

| Pair | Canonical orientation seeds | Reversed orientation seeds | Games including duplicate run |
| --- | --- | --- | ---: |
| Donatello / Krang | 7201, 7202 | 7201, 7202 | 8 |
| Michelangelo / Bebop & Rocksteady | 7211, 7212 | 7211, 7212 | 8 |
| Splinter / Shredder | 7221, 7222 | 7221, 7222 | 8 |
| April O'Neil / Casey Jones | 7231, 7232 | 7231, 7232 | 8 |

The stage therefore contains **16 distinct deterministic games and 32 executions including exact
duplicates**. This is deliberately small and is not the retired 900-game smoke.

Using the same seed for mirrored seats is intentional: it supplies a controlled orientation probe,
not a fairness or win-rate comparison. Results must never be aggregated into deck-strength claims.

## Required pre-run static inventory

Before executing a game, freeze a manifest for each deck containing:

- deck file SHA-256 and resolved 60-slot membership;
- Oracle ID, face, exact fragment key, static `SemanticCoverage`, and limitations;
- expected represented Action families and explicit unsupported families;
- unique-card and fragment membership digests;
- overlap with Acceptance #001 and novelty contributed by the pairing.

The manifest must not claim runtime coverage. Its sole purpose is to define the semantic universe
against which runtime PRESENT/REACHED/EXECUTED evidence is reconciled.

## Required runner/evidence boundary

Stage #002 may add evidence tooling, but must not add gameplay behavior. A generalized acceptance
runner must parameterize two frozen deck paths and stable display IDs while preserving the exact
Engine–Interpreter–Pilot boundary used by #001.

For every involved semantic occurrence, output must include:

- the specification's Oracle/face/fragment key and runtime source identity;
- PRESENT witness and first/last relevant zone occurrence;
- typed opportunity witness for REACHED, or `reach_not_proven`;
- static coverage and exact limitation reasons at that moment;
- transaction/Stack/event/result IDs and immutable before/after evidence for EXECUTED;
- compound parent, child, and follow-up joins;
- per-game and aggregate deterministic membership digests.

Do not use diagnostic `unsupported_semantics` registration events alone as reached evidence.

## Per-game report

Every game reports:

- seed, seat orientation, winner/turn or bounded incomplete result;
- duplicate byte-equivalence and RNG ledger integrity;
- invariant violations and block-restriction rejections;
- EXECUTED occurrence and unique-fragment sets;
- REACHED / UNSUPPORTED occurrence and unique-fragment sets with opportunity evidence;
- PRESENT / UNREACHED sets, including `reach_not_proven`;
- transaction counts by represented Action family;
- Stack/Priority, trigger, combat-step, SBA, and zone-identity summaries;
- any trajectory-changing supported behavior, without interpreting it as balance.

## Aggregate report

Stage aggregation reports union and intersection across seeds, orientations, pairings, decks, and
semantic classes. It must answer:

1. Which accepted engine systems executed outside Leonardo/Raphael?
2. Which exact semantics repeatedly became actionable but remained unsupported?
3. Which large static families stayed merely present or entirely unobserved?
4. Did any supported claim lack reconstructive evidence?
5. Did seat orientation reveal state, Priority, trigger-order, or Pilot-boundary leakage?
6. Did any pairing reveal a foundational blocker?

No single coverage percentage is authorized. Counts must retain their denominator and evidence
class.

## Gate criteria

Stage #002 passes only if:

- all duplicate runs are byte-identical;
- every game has zero invariant violations;
- authoritative object, zone, cost, Stack, Priority, trigger, combat, and SBA boundaries remain
  coherent;
- every EXECUTED claim is reconstructive from immutable evidence;
- every unsupported actionable occurrence is explicit and tied to an opportunity witness;
- present-only text is not promoted to reached or executed;
- no unsupported parent is upgraded by a supported child;
- no deck/prototype/Pilot/gameplay change was used to improve evidence;
- all anomalies are reconciled without balance reasoning.

A foundational blocker, nondeterministic duplicate, silent approximation, illegal action, or
unreconstructable state mutation stops the stage for the smallest evidence-backed correction.
Large unsupported counts alone do not fail it.

## Decisions deferred until after Stage #002

Only audited Stage #002 evidence may support a later choice among broader acceptance matches, a
larger frozen-deck sample, a specific engine extension, or eventual smoke testing. Calibration,
Prototype 0.3, Pilot tuning, deck revisions, and Action #13 remain unauthorized by this design.
