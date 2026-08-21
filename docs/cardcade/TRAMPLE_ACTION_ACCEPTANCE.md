# Trample Combat-Damage Assignment Acceptance Audit #1

Status: **REJECT**  
Audit date: 2026-08-20  
Branch: `agent/cardcade-trample`  
Parent baseline: `2bbbeb34a00a2328e550cbd8eaadbd9fa83ff881`  
Evidence checkpoint: `d6581549caa2a9bd6a63439300a66eb2c5dc531e`

## Candidate integrity

The audited candidate consisted of exactly:

- modified `src/tmnt_design_studio/card_interpreter07.py`;
- modified `src/tmnt_design_studio/engine07.py`;
- untracked `tests/test_trample_action.py`.

No implementation or test file was changed during this audit. The candidate fingerprint is
`7279f4ca9da65c4ac7582a5f397372899b9de81d`, calculated as SHA-1 of the newline-joined,
path-sorted manifest of these three complete-file SHA-256 values:

| File | SHA-256 |
|---|---|
| `src/tmnt_design_studio/card_interpreter07.py` | `dcd437e0269f13eabc6f251b7314da12dd8981a4e697c353a42f3b2da012fef3` |
| `src/tmnt_design_studio/engine07.py` | `97bbca059497f613f80747be5c4dc64137eed70f82db4620fb540a4e6bc230bc` |
| `tests/test_trample_action.py` | `efd7f331dbf6ed0634dacac2c0d044ce8b7243006d1c716b00080f044486300a` |

## Authoritative rules comparison

The audit used the 2026-08-07 Magic Comprehensive Rules. The bounded one-blocker algorithm
correctly reflects these represented rules:

- CR 702.19a: Trample modifies an attacking creature's combat-damage assignment and has no
  effect while that creature blocks or deals noncombat damage.
- CR 702.19b: lethal assignment accounts for damage already marked before excess can be
  assigned to the defending player.
- CR 702.19d: a blocked Trample attacker whose blockers are gone may assign its damage to the
  defending player.
- CR 510.4 and 702.4/702.7: First Strike and Double Strike use separate applicable damage
  steps, with authoritative state and SBAs between them.
- CR 704.5a/g: zero-life loss and lethal marked damage are state-based results.

The candidate fails CR 510.1a, which states that a creature that would assign 0 or less combat
damage does not assign combat damage at all. The candidate instead creates a typed assignment
with amount `0`, applies/logs that assignment, and includes it in immutable combat evidence.
The candidate test suite explicitly expects this incorrect zero assignment for both zero and
negative effective power.

Independent probes reproduced:

| Power | Blocker toughness | Marked before | Required lethal | Blocker assignment | Excess |
|---:|---:|---:|---:|---:|---:|
| 5 | 2 | 0 | 2 | 2 | 3 |
| 5 | 5 | 0 | 5 | 5 | 0 |
| 5 | 5 | 2 | 3 | 3 | 2 |
| 5 | 6 | 2 | 4 | 4 | 1 |
| 3 | 6 | 2 | 4 | 3 | 0 |
| 0 | 2 | 0 | 2 | **0 assignment emitted** | 0 |
| -2 | 2 | 0 | 2 | **0 assignment emitted** | 0 |

The 5/6 blocker carrying 2 damage demonstrated that marked damage is subtracted once: the
candidate required 4, assigned 4, and assigned 1 excess. The 3/6 case correctly assigned all 3
to the blocker with no excess. Those calculations are sound; the zero/nonpositive assignment is
not.

## Coverage reconstruction

Coverage was independently recomputed from the authoritative 472-print / 332-Oracle-object
snapshot rather than imported from the candidate tests.

| Classification | Objects | Fragments | Digest |
|---|---:|---:|---|
| Recognized | 25 | 26 | `1110d74154eec8dd568fd31387db2a2be243dd7d5ad27bd2f2c89206cc29786e` |
| Bounded payload executable | 20 | 20 | `eb31687830676ca3d020256f0226cb0ab4fd7861903dd5f433ae93cf97ff15b5` |
| Fully supported fragment | 15 | 15 | `84bb2753b742e60f61e1790af18080b9f5c5bbfaaa786b502554eaa1ac03e67b` |

Recognized Oracle objects were General Traag, Heart of Stone; Genghis Frog; Groundchuck &
Dirtbag; Heroes in a Half Shell; Krang, Utrom Warlord; Leatherhead, Iron Gator; Leatherhead,
Swamp Stalker; Leonardo, the Balance; Michelangelo, On the Scene; Michelangelo, the Heart;
Mutagen Man, Living Ooze; Mutant Town Musicians; Novel Nunchaku; Primordial Pachyderm; Raph &
Mikey, Troublemakers; Rocksteady, Mutant Marauder; Savanti Romero, Time's Exile; Saved by the
Shell; Shadowspear; Technodrome; The Last Ronin; Vigor; Voracious Hydra; West Wind Avatar; and
Zog, Triceraton Castaway. Krang contributed two recognized fragments.

The 20 executable objects exclude the five unsupported parent/delivery objects: Leonardo, the
Balance; Novel Nunchaku; Saved by the Shell; Shadowspear; and The Last Ronin. Krang's static
self-keyword fragment is executable, while its separate grant to other artifact creatures remains
non-executable.

The 15 fully supported fragments are General Traag; Genghis Frog; Groundchuck & Dirtbag;
Leatherhead, Iron Gator; Leatherhead, Swamp Stalker; Michelangelo, On the Scene; Michelangelo,
the Heart; Mutagen Man; Mutant Town Musicians; Raph & Mikey; Rocksteady; Savanti Romero;
Vigor; Voracious Hydra; and West Wind Avatar. Compound keyword lines containing unsupported
Flying, Vigilance, Menace, Indestructible, or Reach retain explicit follow-up limitations.

Frozen-roster reconstruction also matched:

- recognized: Mutagen Man, Living Ooze; Mutant Town Musicians; Saved by the Shell — 3 cards
  across Bebop/Rocksteady, Casey Jones, Michelangelo, and Raphael decks;
- executable/full: Mutagen Man and Mutant Town Musicians — 2 cards across Bebop/Rocksteady,
  Casey Jones, and Raphael decks.

Unsupported attachment, activation, trigger, choice/grant, deathtouch-modified lethal, and
compound follow-up semantics remain explicit. Multiple blockers are not generated by the legal
combat option model. Planeswalker/battle defenders and broader defender selection are not
claimed.

## Independent transaction probes

Independent in-memory probes, separate from candidate test assertions, established:

- unblocked Trample used ordinary player combat damage;
- one blocker received the computed lethal amount before excess went to the defending player;
- exact lethal and insufficient power produced no excess;
- marked damage and effective toughness were read at assignment time;
- effective attacker power was read at assignment time;
- Trample had no effect while its creature blocked;
- First Strike and Double Strike used the existing separate damage steps and SBA boundary;
- a blocker surviving a Double Strike first step retained its damage, causing the second-step
  requirement to be recalculated as `toughness - marked damage`;
- a blocker dying in the first step left the attacker blocked, but CR 702.19d allowed the Double
  Strike second-step damage to be assigned to the player;
- a removed attacker did not bind to an equal-valued replacement;
- a removed blocker did not bind to an equal-valued replacement;
- fabricated attacker and blocker IDs were rejected before mutation;
- player damage used the existing 20-life model, and a 25-power attacker blocked by a 1-toughness
  creature assigned 1 to the blocker and 24 to the player, producing life -4 and the correct winner.

The blocker-survives Double Strike probe also exposed a zero-power blocker assignment in the
second step. That is the same CR 510.1a defect, not a separate cause.

## Immutable evidence finding

`CombatDamageAssignment` preserves source ID, blocker ID or target player, assigned amount,
damage-step role, a Trample flag, and `lethal_required`. `CombatDamageStepEvidence` preserves
the step and objects removed by the following SBA check. This is enough to reconstruct the
chosen assignment and its lethal threshold.

It is not enough to reconstruct the complete damage result without later state. The evidence does
not preserve the attacker's evaluated power, the blocker's evaluated toughness and pre-damage
marked damage, the blocker's post-damage marked total when it survives, or the defending
player's life before and after damage. `lethal_required` alone cannot prove its authoritative
inputs, and the final snapshot's life/damage state may include later events. This fails the audit's
explicit immutable-evidence requirement.

## Acceptance telemetry

The committed checkpoint was exported to an isolated temporary tree and replayed, reproducing
the baseline **47 unsupported events / 16 exact pairs**. The candidate was replayed twice for
each seed and reproduced **42 / 15** with byte-identical duplicates.

The exact removed pair was:

- Mutant Town Musicians — `Trample`: **5 events**, one per seed.

All five occurrences are the intrinsic standalone `Trample` fragment on Mutant Town Musicians.
None depends on an unsupported grant, trigger, activation, attachment, choice, or compound
context. The candidate generically recognizes that fragment and can execute its bounded
one-blocker assignment modifier. Therefore the telemetry reduction is genuine capability
coverage rather than suppression.

The evidence categories remain distinct:

- keyword recognized: yes, for the five Mutant Town Musicians occurrences;
- bounded Trample capability available: yes, because each is an intrinsic standalone static
  keyword on an authoritative creature;
- Trample actually modified an Acceptance damage assignment: **zero**.

In the observed games Mutant Town Musicians was unblocked or was itself blocking when it dealt
damage. Trample correctly made no special assignment in either situation. Focused probes, not
Acceptance Match #001, provide the split-assignment execution evidence.

Acceptance results:

| Seed | Winner | Turn | Unsupported events / pairs | Trample-modified assignments |
|---:|---|---:|---:|---:|
| 7001 | Raphael | 16 | 9 / 9 | 0 |
| 7002 | Raphael | 16 | 5 / 4 | 0 |
| 7003 | Leonardo | 19 | 11 / 9 | 0 |
| 7004 | Leonardo | 21 | 13 / 11 | 0 |
| 7005 | Raphael | 16 | 4 / 4 | 0 |
| **Aggregate** | | | **42 / 15** | **0** |

Aggregate execution remained 13 Scry commits, 17 Deal Damage transactions, 8 Returns, 16
activation announcements, 32 Priority grants, 32 passes, 1 block-candidate rejection, and 0
invariant violations.

## Validation

| Validation | Result |
|---|---:|
| Full suite | 398 passed / 1 skipped |
| Trample suite | 21 passed |
| Combat/strike/state | 77 passed |
| SemanticCoverage | 5 passed |
| Card data | 5 passed |
| Identity/zone/SBA/trigger/layer regressions | 72 passed |
| Ruff format check | clean, 36 files |
| Ruff check | clean |
| `git diff --check` | clean |

Passing tests do not override the independently demonstrated CR 510.1a defect; the candidate's
own zero/nonpositive-power test currently codifies the wrong result.

## Blockers and smallest correction

1. **Zero/nonpositive combat damage assignment:** omit combat-damage assignments entirely when
   authoritative effective power is 0 or less, for attacking and blocking creatures alike. Do not
   log, apply, or preserve a 0-damage assignment. Replace the current tests that expect an amount-0
   assignment with assertions that no assignment or damage result exists. Preserve all positive
   Trample calculations.
2. **Incomplete immutable result evidence:** extend immutable combat/Trample evidence with the
   minimum authoritative before/after facts required to audit the transaction: evaluated attacker
   power; blocker effective toughness and marked damage before assignment; lethal requirement;
   blocker and player assigned amounts; blocker marked damage after dealing; defending-player
   life before/after; and the existing removal result. These values must be captured during the
   transaction, not reconstructed from later mutable objects.

No broader combat redesign is required. The recognized/executable/full memberships and
Acceptance telemetry need not change merely to correct these blockers.

REJECT — omit zero/nonpositive-power assignments and preserve the minimum immutable before/after damage facts needed to audit each Trample result.
