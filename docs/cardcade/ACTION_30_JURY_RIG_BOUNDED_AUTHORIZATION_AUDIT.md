# Action #30 bounded authorization audit: Jury-Rig Justiciar

Audited exact evidence head `2b331acb887eadf00abe028d8d8a4a4f653a8320` on clean local `main`. Audit only: no implementation, production/test changes, Stage/Smoke runs, or new authorization.

## Conclusion for HQ

**Bounded feasibility supported by the existing architecture.** Courier supplies authoritative library selection, protected chooser, reveal/hand-movement and reconstruction patterns. Scry already supplies bounded private top-library inspection and identity-preserving same-zone reordering. DeterministicRNG supplies the permutation evidence. No foundational hidden-zone architecture gap was identified by this audit.

A dedicated exact-semantic transaction is still required; these primitives are not a drop-in Jury-Rig implementation. Authorization should explicitly include a private top-four chooser, atomic remainder-to-bottom permutation, and complete evidence validation. No scheduler, turn-engine or Stage/Smoke step-loop changes appear necessary. Action #30 remains NOT AUTHORIZED until HQ decides.

Frozen exact fragment, verified in the merged-baseline ranking:

> When Casey Jones enters, look at the top four cards of your library. You may reveal an artifact card from among them and put it into your hand. Put the rest on the bottom of your library in a random order.

## Primitive assessment

All source references below are at the audited head, under `src/tmnt_design_studio/`.

| Requirement | Existing support | Bounded work still needed |
|---|---|---|
| Library identity and private inspection | `engine07.py:3465` Scry snapshots the top available objects and exposes immutable IDs/names; library end is top. `food_search07.py:31` validates authoritative owner/library identity. | Inspect exactly min(4, library size) at resolution, not at ETB creation. View only these inspected cards; candidates only artifact cards among them. No access to lower-library or opponent hidden cards through the chooser interface. |
| Optional artifact choice | Courier's frozen FoodSearchOption/View and guarded chooser (`food_search07.py:10-112`) validate offered identities and guard zones/registry/card identity/RNG. | Dedicated option of one qualifying ID or decline. Inspect all top four even if none qualify; selecting is optional, inspection and bottoming are not. Determine Artifact from represented card type, including artifact creatures, not name, Food subtype, or arbitrary substring matches. Exclude non-card/token identities. |
| Reveal and hand movement | Courier logs the exact reveal and calls authoritative move_object (`food_search07.py:156-174`). `engine07.py:1547` validates source identity/zone and produces a new destination incarnation. | Reveal only the selected object and link its old library ID to its new hand ID; exactly one move or none. No fabricated reveal when declined/no artifact. |
| Bottom ordering | Scry constructs a checked replacement list preserving library membership and object identities (`engine07.py:3511-3529`). `move_object` rejects same-zone movement; cross-zone bottom insertion uses index 0 (`:1662`). | Reorder unselected inspected objects in-place within the library. Do not call library-to-library move_object, invent a staging zone, or assign new incarnations to reordered cards. Preserve the uninspected portion's exact identity/order. |
| Deterministic randomness | `engine07.py:1121` DeterministicRNG and `shuffled` provide domain, sequence, state and permutation records; Courier's validator replays them. | Shuffle only the remaining inspected IDs, never the full library. The chooser must not choose their order. Define and test consumption for zero/one remainder; one explicit shuffled-copy record per transaction is a bounded proposed policy, not existing Jury-Rig behavior. |
| ETB/Stack/Priority and source lifetime | Courier's exact ETB anchors and one-use validation (`food_search07.py:236`) plus existing Trigger/Stack/Priority integration. | Deliver once from authoritative self-ETB; perform no inspection/reveal/movement/RNG before all-pass resolution. Source leaving later must not erase a valid trigger. No delayed scheduling is involved. |
| Evidence | Courier's immutable transaction history and independent validator (`food_search07.py:270`); mature execution references (`engine07.py:9288`); Stage indexing/validation (`stage002.py:644,1203`). | Authenticate the whole top-four/selection/reveal/move/random-bottom chain before EXECUTED. A reveal, movement, or generic trigger_resolved log alone is insufficient. Preserve complete pre/post order, including uninspected library. |

## Minimal transaction contract

At resolution let L be the authoritative library in stored bottom-to-top order; I is the top min(4,len(L)) identities exposed in explicit top-first order; U is the untouched lower-library prefix. Freeze these identities and their card facts while the private chooser runs. Offer only qualifying artifact-card IDs from I and decline.

After validating the choice and all authoritative dependencies, reveal/move selected S to hand if present. Let R contain every identity in I except S, with an explicitly documented input order. Randomly permute a copy of R with the existing game RNG and a transaction-specific domain. Treat the resulting P as stored bottom-to-top order and commit final library `P + U`. If no card is selected, R is all inspected cards; with fewer than four available cards, U is empty. The empty-library case is a valid empty inspection, not a failed draw or an attempt to search the entire library.

Postconditions: no duplicates/loss; unchanged U order and identities; R retains library incarnations; exactly one new hand incarnation only when S was chosen; no other zone mutation; remaining bottom order is RNG-selected, not chooser-selected. A top-first input versus bottom-first storage convention must be explicit and regression-tested.

Reuse the protected chooser pattern, not Courier's Food filter/full-library shuffle/token fallback or Scry's user-selected partitions/order and SCRIED event. Scry's narrower rollback guard is not a substitute for full transaction protection. Guard against registry replacement, zone replacement, source/event/Stack relinking and RNG-object/state mutation; reject invalid choices before commitment. Keep validation/commit ownership in the engine. The private callback is an interface boundary, not a sandbox for arbitrary hostile Python code or a reason to build a global hidden-zone security framework.

Chooser integration can follow Courier's dedicated Game callback and deterministic default-option precedent. HQ should freeze the default rule (for example, first qualifying inspected artifact, otherwise decline) as a bounded implementation choice; it must not introduce strategy tuning or expose the whole library through GameView. No generic hidden-zone query language or new Pilot search policy is needed.

## Evidence and required proofs upon authorization

Reconstruct original ETB -> trigger/Stack/all-pass permission -> exact pre-library and top-four identities -> authoritative eligible candidates and decision -> selected reveal and new hand incarnation, if any -> RNG input/state/permutation of R -> unchanged U and final library/hand -> single completed transaction. Tie serialized evidence to independent rule events, movement records, RNG records and immutable transaction history. Validate both live snapshots and JSON round trips, and reject corruption even when duplicate event copies are changed together.

Required focused cases: exact frozen grammar/near-neighbors; both controllers; source departure/reentry; duplicate ETB/replay; no pre-resolution information or mutation; libraries of sizes 0/1/2/3/4/>4; no artifact/decline/success/multiple artifacts; artifact creatures and equal-valued identity-distinct cards; a qualifying fifth card excluded; changed library before resolution; selected card only revealed; exact untouched-prefix order; no replacement IDs for bottomed cards; deterministic random order and defined zero/one RNG policy; stale/fabricated/relinked selections; chooser mutation and rollback; simultaneous corruption of evidence copies. Prove the real public view does not gain inspected hidden data. Then authorized full/focused/Stage/Smoke validation and banked execution continuity, without forcing witness counts.

Stop and return to HQ if this requires arbitrary hidden-zone scripting, generic look/search/reorder grammar, new staging zones, a global visibility rewrite, broad chooser/Pilot changes, or relaxed identity/Stack/evidence guards. None is required by the bounded design identified here.

## Audit validation

Existing suites only:

```
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/test_courier_food_search_action.py tests/test_scry_action.py tests/test_hand_bottom_draw_action.py tests/test_engine08h_rng.py
```

**100 passed.** These verify existing primitives; they are not tests of a Jury-Rig implementation. No additional simulation matrix was run. Only this audit and its SHA-256 sidecar were created.

HQ decision pending. Action #30 remains NOT AUTHORIZED. Calibration remains BLOCKED. Prototype 0.3 remains NOT AUTHORIZED.
