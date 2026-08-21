# Trample Combat-Damage Assignment Acceptance Audit #2

Status: **ACCEPT**  
Audit date: 2026-08-20  
Branch: `agent/cardcade-trample`  
Parent baseline: `2bbbeb34a00a2328e550cbd8eaadbd9fa83ff881`  
Evidence checkpoint: `d6581549caa2a9bd6a63439300a66eb2c5dc531e`  
Corrected candidate fingerprint: `e0af6fe1a6151771ecef7c8c3506e24e319adee8`

## Audit integrity

This audit made no implementation or test changes. Audit #1 remained byte-identical at SHA-256
`6d7e3c99869759b4f60e3e04d0f63156135445ece36997f67113312896a7e609`.

The candidate fingerprint was independently reproduced as SHA-1 of the newline-joined,
path-sorted manifest of the complete-file SHA-256 values for
`card_interpreter07.py`, `engine07.py`, and `test_trample_action.py`.

## Rules basis

The implementation was compared with the 2026-08-07 Magic Comprehensive Rules:

- CR 510.1a: creatures assigning 0 or less combat damage do not assign damage;
- CR 510.4 and 702.4/702.7: First Strike and Double Strike establish distinct applicable
  combat-damage steps;
- CR 702.19a: Trample changes attacking combat-damage assignment and has no effect while
  blocking or dealing noncombat damage;
- CR 702.19b: lethal assignment accounts for damage already marked before excess may be
  assigned to the defending player;
- CR 702.19d: a blocked Trample attacker may assign to the defending player after all blockers
  have left combat;
- CR 704.5a/g: player loss and lethal marked damage are state-based results.

The corrected candidate remains intentionally bounded to the existing authoritative
one-attacker/one-blocker, player-defender model. It does not claim multiple-blocker division,
deathtouch-modified lethal assignment, planeswalkers/battles, attachment-derived Trample,
unsupported temporary grants, or unsupported activation/trigger delivery.

## Audit #1 blocker 1: zero/nonpositive assignment

Independent probes used a printed 0-power Trample attacker and a printed 2-power attacker with
an authoritative -3/-0 continuous modifier. In both cases effective power was 0 or -1.

Both probes produced:

- no `CombatDamageAssignment` for the attacker;
- no combat-damage log entry representing zero damage;
- no `TrampleDamageEvidence`;
- no defending-player life change from 20;
- no blocker marked damage;
- normal transition through the combat-damage step to end of combat;
- successful invariant and SBA processing.

The same suppression applies to a blocker with nonpositive power. The candidate now rejects any
persisted nonpositive combat assignment through an invariant, preventing a zero assignment from
silently re-entering historical evidence.

**Finding: blocker resolved.**

## Audit #1 blocker 2: immutable evidence

Every positive bounded Trample result now produces an immutable `TrampleDamageEvidence` record
containing:

- attacker and blocker runtime IDs;
- damage-step kind;
- evaluated attacker power;
- evaluated blocker toughness and marked damage before assignment;
- calculated lethal requirement;
- damage assigned to the blocker and defending player;
- defending-player index and life immediately before and after the assignment;
- blocker marked damage after resolution when it survives;
- explicit blocker survival status.

The enclosing immutable damage-step evidence retains the SBA removal set. If the blocker has
already left before a later Double Strike step, the second-step record retains its historical
runtime ID, records unavailable current blocker characteristics as `None`, uses lethal requirement
0, and preserves the complete player assignment and life result. If the blocker dies from the
current damage, its pre-damage facts, assignment, and removal result survive while its post-SBA
marked-damage field is correctly `None`.

Snapshot serialization independently reproduced every field. Mutating a surviving blocker from
5 marked damage to 999 after the transaction did not change either the typed evidence or its
serialized snapshot. Duplicate snapshot generation and duplicate Acceptance runs were
byte-identical.

Structural invariants independently enforce:

- positive attacker power for each Trample record;
- conservation of attacker power across blocker and player assignments;
- `life_after = life_before - player_assignment`;
- `lethal = max(0, toughness - marked_before)` when a current blocker exists;
- agreement between blocker-survival and post-damage marked state.

**Finding: blocker resolved.**

## Marked-damage reconstruction

Independent probes reproduced the authoritative calculation matrix:

| Power | Toughness | Marked before | Lethal required | Blocker assigned | Player assigned | Player life after |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 2 | 0 | 2 | 2 | 3 | 17 |
| 5 | 5 | 0 | 5 | 5 | 0 | 20 |
| 5 | 5 | 2 | 3 | 3 | 2 | 18 |
| 5 | 6 | 2 | 4 | 4 | 1 | 19 |
| 5 | 6 | 3 | 3 | 3 | 2 | 18 |

The 6-toughness rows prove marked damage is subtracted exactly once. The evidence stores both
inputs and the resulting lethal requirement rather than recomputing from a later battlefield
object.

## First Strike and Double Strike

First Strike Trample used the first-strike damage step and the existing SBA boundary. A creature
with only First Strike did not assign again in the regular step.

Two Double Strike cases were independently reconstructed:

1. **Blocker survives first step:** a 5-power Double Strike/Trample attacker faced a 0/6 blocker.
   First-step evidence recorded toughness 6, marked-before 0, lethal 6, assignment 5, marked-after
   5, and survival. Second-step evidence read the authoritative surviving state: toughness 6,
   marked-before 5, lethal 1, blocker assignment 1, player assignment 4, and player life 20 → 16.
2. **Blocker dies first step:** against a 0/2 blocker, first-step evidence recorded assignment 2 to
   the blocker, 3 excess, life 20 → 17, and blocker removal. The attacker remained blocked. The
   regular-step record retained the blocker ID but correctly had no current blocker characteristics,
   lethal 0, assignment 0 to the absent blocker, assignment 5 to the player, and life 17 → 12 under
   CR 702.19d.

A removed attacker produced no later assignment. Stale attacker/blocker references did not bind
to equal-valued replacement objects. Fabricated attacker and blocker IDs were rejected before
state mutation.

## Coverage reconstruction

Coverage was independently enumerated from the authoritative 472-print / 332-Oracle-object
snapshot. All classifications and digests remain unchanged:

| Classification | Objects | Fragments | Digest |
|---|---:|---:|---|
| Recognized | 25 | 26 | `1110d74154eec8dd568fd31387db2a2be243dd7d5ad27bd2f2c89206cc29786e` |
| Bounded executable | 20 | 20 | `eb31687830676ca3d020256f0226cb0ab4fd7861903dd5f433ae93cf97ff15b5` |
| Fully supported | 15 | 15 | `84bb2753b742e60f61e1790af18080b9f5c5bbfaaa786b502554eaa1ac03e67b` |

The correction changes combat lifecycle and evidence only. Unsupported grants, attachment,
activation, trigger, deathtouch, defender, and compound semantics remain explicit.

## Acceptance Match #001

Seeds 7001–7005 were run twice. Every duplicate pair was byte-identical.

| Seed | Winner | Turn | Unsupported events / pairs | Trample results | Split results |
|---:|---|---:|---:|---:|---:|
| 7001 | Raphael | 16 | 9 / 9 | 0 | 0 |
| 7002 | Raphael | 16 | 5 / 4 | 0 | 0 |
| 7003 | Leonardo | 19 | 11 / 9 | 1 | 1 |
| 7004 | Leonardo | 21 | 13 / 11 | 0 | 0 |
| 7005 | Raphael | 16 | 4 / 4 | 0 | 0 |
| **Aggregate** | | | **42 / 15** | **1** | **1** |

The original checkpoint was independently reproduced at 47 / 16. The exact removed limitation
remains Mutant Town Musicians — standalone `Trample`, five events / one pair. Each occurrence is
an intrinsic static keyword, not an unsupported grant, trigger, activation, attachment, or compound
parent. The 47/16 → 42/15 reduction therefore remains legitimate.

Acceptance retained 13 Scry commits, 17 Deal Damage transactions, 8 Returns, 16 activation
announcements and cost payments, 32 Priority grants, 32 passes, 1 block-candidate rejection, and
0 invariant violations. Strike-step evidence and all winners/turns remained coherent.

## Seed 7003 forensic reconstruction

The serialized regular combat-damage-step record proves:

- attacker `object-000193`: **Mutant Town Musicians**;
- blocker `object-000208`: **Leonardo, Leader in Blue**;
- Mutant Town Musicians' authoritative standalone Oracle fragment is `Trample` and its keyword is
  executable at that step;
- attacker power: **2**;
- blocker toughness: **1**;
- blocker marked damage before: **0**;
- lethal requirement: **1**;
- blocker assignment: **1**;
- excess assignment to Leonardo's controller: **1**;
- blocker marked damage after SBA: `None`, blocker survived: false;
- defending player: player 0, life **11 → 10**;
- damage step: **regular**.

The rejected candidate's preserved replay already contained, on turn 18, both a 1-damage
`combat_damage_assignment` from Mutant Town Musicians to Leonardo, Leader in Blue and a
1-damage `combat_damage_player` entry from the same source. Thus the combat behavior predates
the correction. Audit #1 counted zero because the snapshot omitted the Trample flag and complete
transaction record. The correction made the existing split independently countable and
reconstructable; it did not manufacture or alter it.

## Validation

| Validation | Result |
|---|---:|
| Full suite | 399 passed / 1 skipped |
| Trample suite | 22 passed |
| Combat/strike/state | 77 passed |
| SemanticCoverage + card data | 10 passed |
| Identity/SBA/trigger/layer regressions | 72 passed |
| Ruff format check | clean, 36 files |
| Ruff check | clean |
| `git diff --check` | clean |

No material blocker remains within the authorized bounded scope.

ACCEPT — corrected bounded Trample combat-damage assignment is suitable to bank.
