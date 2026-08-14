# Deal Damage Action Acceptance Audit #1

## Audit result

- Date: 2026-08-14
- Branch: `agent/cardcade-deal-damage`
- Evidence checkpoint: `a5c64b0e2f4c8aead759b12178eea52d1dfd20d0`
- Candidate state: validated, uncommitted implementation and tests
- Audit mode: evidence-only; implementation and tests were not modified
- Recommendation: **REJECT**

The damage transaction, represented delivery paths, semantic boundary, and acceptance
behavior are sound. The acceptance gate nevertheless fails because independent comparison
against the authoritative Oracle universe found a direct damage instruction that the
recognition grammar misses, plus one recognized multi-kind target whose limitation is
misclassified because a shorter target alternative matches first.

## 1. Coverage-universe reconciliation

The post-Create-Token report's `12 frozen cards / 8 decks / 52 Oracle objects` was an
opportunity estimate over damage-related text, not a claim that all entries were direct,
bounded Deal Damage payloads. It includes combat-damage triggers, keyword reminder text,
prevention/replacement text, damage-received triggers, and other semantics whose occurrence
of the word “damage” does not make them Deal Damage Actions. Conservative narrowing is
therefore required.

The candidate independently reproduces these claimed memberships:

| Classification | Frozen roster | Full pool |
| --- | --- | --- |
| Recognized | 6 cards / 3 decks | 27 objects / 28 fragments |
| Bounded payload executable | 4 cards / 2 decks | 12 objects / 12 fragments |
| Fully supported | 1 card / 1 deck | 2 objects / 2 fragments |

Frozen recognized membership:

- Cool but Rude
- Manhole Missile
- Mouser Foundry
- Raphael, Tough Turtle
- Spicy Oatmeal Pizza
- Tenderize

The exposed decks are Casey Jones, Michelangelo, and Raphael.

Frozen bounded-payload membership:

- Cool but Rude
- Manhole Missile
- Mouser Foundry
- Raphael, Tough Turtle

The exposed decks are Casey Jones and Raphael. Only Raphael, Tough Turtle is fully
supported in the frozen roster.

Full-pool bounded-payload membership:

- Bot Bashing Time
- Brilliance Unleashed
- City of Brass
- Cool but Rude
- Exploding Barrel
- General Traag, Heart of Stone
- Grand Coliseum
- Manhole Missile
- Mouser Foundry
- Raphael, Tough Turtle
- Slash, Reptile Rampager
- Swift Demise

Full support is limited to Raphael, Tough Turtle and Slash, Reptile Rampager.

Independent digest reproduction:

- recognized: `df39d9ef27a6e686c164306786a02a312644891b8d251a701e4443db8fc3baa3`
- bounded executable: `5c977d6a1386af69dc65c694dcb146d1e5b52a7278a085df61ae667b852a89f1`
- fully supported: `f0f5e98cedf31748f558a83a20b69834ce31fec43667aa4045de30958769a740`

Matching these digests proves that the candidate and its tests agree; it does not prove
that the recognition universe is complete.

### Exact recognized fragments and semantic coverage

`P`, `C`, `F`, and `Full` mean payload executable, parent/context executable, follow-up
executable, and full-fragment support.

| Oracle object | Exact fragment | P | C | F | Full | Explicit limitations |
| --- | --- | :---: | :---: | :---: | :---: | --- |
| All Will Be One | Whenever you put one or more counters on a permanent or player, this enchantment deals that much damage to target opponent, creature an opponent controls, or planeswalker an opponent controls. | No | No | No | No | `dynamic_damage_amount_not_implemented`; `damage_trigger_context_not_implemented`; `damage_followup_semantics_not_implemented` |
| Blasphemous Act | Blasphemous Act deals 13 damage to each creature. | No | Yes | Yes | No | `multiple_damage_targets_not_implemented` |
| Bot Bashing Time | Bot Bashing Time deals 6 damage to target creature. If that creature would die this turn, exile it instead. | Yes | Yes | No | No | `damage_followup_semantics_not_implemented` |
| Brilliance Unleashed | • Brilliance Unleashed deals 5 damage to target creature. | Yes | No | Yes | No | `damage_choice_context_not_implemented` |
| Casey Jones, Back Alley Brute | Whenever you put one or more +1/+1 counters on a creature you control, Casey Jones deals that much damage to target opponent. | No | No | Yes | No | `dynamic_damage_amount_not_implemented`; `damage_trigger_context_not_implemented` |
| City of Brass | Whenever this land becomes tapped, it deals 1 damage to you. | Yes | No | Yes | No | `damage_trigger_context_not_implemented` |
| Cool but Rude | Whenever you discard a card, this Class deals 2 damage to each opponent. | Yes | No | Yes | No | `damage_trigger_context_not_implemented` |
| Electric Seaweed | When this creature enters, until end of turn, whenever another creature dies, this creature deals 1 damage to each non-Wall creature. | No | No | Yes | No | `multiple_damage_targets_not_implemented`; `damage_trigger_context_not_implemented` |
| Electric Seaweed | {T}: This creature deals 1 damage to any target. | No | No | Yes | No | `damage_any_target_not_implemented`; `damage_activation_context_not_implemented` |
| Everything Pizza | {2}{W}{U}{B}{R}{G}, {T}, Sacrifice this artifact: Target player gains 3 life and draws a card. Each of your opponents discards a card. This artifact deals 3 damage to any target. Put three +1/+1 counters on up to one target creature. | No | No | No | No | `damage_any_target_not_implemented`; `damage_activation_context_not_implemented`; `damage_followup_semantics_not_implemented` |
| Exploding Barrel | {8}, {T}, Sacrifice this artifact: It deals 20 damage to target creature. This ability costs {1} less to activate for each pressure counter on this artifact. Activate only as a sorcery. | Yes | No | No | No | `damage_activation_context_not_implemented`; `damage_followup_semantics_not_implemented` |
| General Traag, Heart of Stone | When General Traag enters, you may sacrifice another artifact. When you do, General Traag deals 4 damage to target creature. | Yes | No | Yes | No | `damage_trigger_context_not_implemented` |
| Go Ninja Go | • Go Ninja Go deals damage equal to the greatest power among creatures you control to target creature an opponent controls. | No | No | Yes | No | `dynamic_damage_amount_not_implemented`; `damage_choice_context_not_implemented` |
| Grand Coliseum | {T}: Add one mana of any color. This land deals 1 damage to you. | Yes | No | Yes | No | `damage_activation_context_not_implemented` |
| Hamato Ninpō | Hamato Ninpō deals 4 damage to target attacking or blocking creature. | No | Yes | Yes | No | `damage_target_combat_status_not_implemented` |
| Jennika's Technique | Jennika's Technique deals 2 damage to each creature. | No | Yes | Yes | No | `multiple_damage_targets_not_implemented` |
| Manhole Missile | Manhole Missile deals 3 damage to target creature. You may put a card from your hand on the bottom of your library. If you do, draw a card. | Yes | Yes | No | No | `damage_followup_semantics_not_implemented` |
| Mouser Foundry | {4}{R}, Sacrifice this artifact: It deals 3 damage to target creature. | Yes | No | Yes | No | `damage_activation_context_not_implemented` |
| Raphael, Tough Turtle | Alliance — Whenever another creature you control enters, Raphael deals 1 damage to target opponent. | Yes | Yes | Yes | Yes | None |
| Shellshock | For each opponent, choose up to one target creature that player controls. Shellshock deals X damage to each of those creatures. You create a Mutagen token for each creature dealt damage this way. (They're artifacts with "{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature. Activate only as a sorcery.") | No | No | No | No | `multiple_damage_targets_not_implemented`; `damage_preceding_effect_not_implemented`; `damage_followup_semantics_not_implemented` |
| Slash, Reptile Rampager | Alliance — Whenever another creature you control enters, Slash deals 2 damage to each opponent. | Yes | Yes | Yes | Yes | None |
| Special Move | • Foot Toss — Target creature you control deals damage equal to its power to any other target. Then sacrifice it. | No | No | No | No | `damage_any_target_not_implemented`; `damage_choice_context_not_implemented`; `damage_followup_semantics_not_implemented` |
| Spicy Oatmeal Pizza | When this artifact enters, it deals 4 damage to any target and 3 damage to you. | No | No | No | No | `damage_any_target_not_implemented`; `damage_trigger_context_not_implemented`; `damage_followup_semantics_not_implemented` |
| Super Combo | Target creature you control deals damage equal to its power to target creature an opponent controls. | No | Yes | Yes | No | `dynamic_damage_amount_not_implemented` |
| Swift Demise | Swift Demise deals 1 damage to target creature. Then destroy each creature you don't control that was dealt damage this turn. | Yes | Yes | No | No | `damage_followup_semantics_not_implemented` |
| Tenderize | Target creature you control deals damage equal to its power to target creature an opponent controls. | No | Yes | Yes | No | `dynamic_damage_amount_not_implemented` |
| Tokka & Rahzar, Terrible Twos | Whenever a player casts a spell, if the amount of mana spent to cast it was less than its mana value, Tokka & Rahzar deal 3 damage to that player. | No | No | Yes | No | `damage_referential_player_not_implemented`; `damage_trigger_context_not_implemented` |
| Weather Maker | {T}, Remove three charge counters from this artifact: It deals 3 damage to any target. | No | No | Yes | No | `damage_any_target_not_implemented`; `damage_activation_context_not_implemented` |

### Material recognition findings

The remaining damage-text objects were independently inspected. Combat-damage triggers,
double strike/trample/deathtouch reminder text, damage-received triggers, Vigor prevention,
Raphael damage doubling, and Novel Nunchaku fight reminder text are legitimately outside
this bounded Action grammar. They require combat, keyword, prevention/replacement, trigger,
or Fight semantics rather than direct recognition as a fixed Deal Damage payload.

One exclusion is not legitimate:

> Storm of Steel deals 2 damage to each of one or two targets.

This is a direct Oracle damage instruction. It is outside executable coverage because it
has multiple/divided recipients and “target” may select unsupported recipient types, but
it belongs in the recognized universe with explicit limitations. The grammar recognizes
`one or two targets` but misses the authoritative `each of one or two targets` form. This
is an accidental parser blind spot, not principled narrowing.

There is also a limitation-classification defect for All Will Be One. The target-alternative
regex matches the shorter `target opponent` alternative before the complete `target
opponent, creature an opponent controls, or planeswalker an opponent controls` phrase.
The result is a generic follow-up limitation instead of the applicable
`damage_multi_kind_target_not_implemented` limitation. Full support remains false, so no
gameplay executes incorrectly, but SemanticCoverage does not precisely describe why the
payload is unsupported.

## 2. SemanticCoverage truthfulness

For the other recognized fragments, executable probes and source inspection confirm that
payload, parent/context, follow-up, and full support are independently represented.
Unsupported triggers, activations, choices, preceding effects, dynamic values, target
classes, and follow-ups remain in unsupported telemetry. A bounded payload is delivered
only when its parent is represented.

Manhole Missile correctly traverses Hand → Stack → resolution. Its fixed three-damage
payload executes through the typed transaction. Its optional hand-to-library and draw
follow-up remains unsupported and is reported once for each of the four casts observed in
the five-seed acceptance aggregate. The child payload does not upgrade the complete Oracle
fragment.

The Storm of Steel omission and All Will Be One reason mismatch prevent a wholly truthful
claim over the authoritative recognition universe even though neither causes silent
execution.

## 3. Damage correctness

Independent executable probes confirm:

- player damage subtracts the exact amount and invokes the existing life-zero loss boundary;
- creature damage increments marked damage without changing printed/base toughness;
- nonlethal damage remains until Cleanup and then clears;
- lethal marked damage moves the creature through the lethal-damage SBA;
- damage is not implemented as destroy, life-loss telemetry, or `-N/-N` mutation;
- fabricated equal-valued sources and targets are rejected by authoritative object identity;
- stale and noncreature targets are rejected;
- invalid transactions leave life, marked damage, zones, events, and object state unchanged;
- `DAMAGE_DEALT` rules events and `damage_dealt` evidence preserve authoritative source ID,
  recipient identity/player, amount, fragment, and noncombat classification;
- duplicate executions are deterministic.

No damage-transaction correctness blocker was found.

## 4. Parent/context delivery

The represented delivery paths are:

- fixed damage spells through authoritative casting, stack membership, revalidation, and
  resolution;
- the represented Alliance creature-entered trigger through generic event detection,
  trigger identity, stack placement, and trigger resolution.

Attack triggers, unrelated ETB triggers, activation costs, modal choices, conditional
triggers, and unsupported target contexts do not opportunistically invoke the transaction.
Executable child programs under those parents remain telemetry-only limitations.

No delivery bypass was found. The recognition defects described above affect evidence
classification, not engine delivery.

## 5. Explicit exclusions

The candidate explicitly retains limitations for X/dynamic amounts, multiple recipients,
any-target forms, referential players, multi-kind targets, combat-status targets,
activations, triggers, choices, preceding effects, and compound follow-ups. Prevention,
replacement, redirection, excess damage, noncombat lifelink/deathtouch, division, and Fight
remain outside executable coverage.

Most exclusions are justified. Storm of Steel must nevertheless be recognized before it
is excluded as non-executable. All Will Be One must retain its multi-kind-target reason
rather than allowing regex ordering to disguise that unsupported target context as a
follow-up.

The seven pre-existing context-sensitive UNKNOWN Oracle objects remain unchanged. The
candidate supplies no evidence to reclassify them.

## 6. Architecture

Source searches found no damage card-name dispatch, roster dispatch, Acceptance Match
special cases, pilot coupling, direct-destroy substitution, toughness mutation, or
life-loss shorthand. Card names occur only as authoritative facts/evidence labels and in
pre-existing basic-land mana mapping.

The typed `DamageTransaction`, generic `SemanticCoverage`, `DAMAGE_DEALT` event, generic
trigger object, stack resolution, authoritative object registry, marked-damage field,
lethal SBA, Cleanup, and life-zero boundary are reusable architectural seams. The Action
does not weaken or bypass `SemanticCoverage`.

## 7. Acceptance telemetry

Seeds 7001–7005 were replayed twice. Duplicate snapshots were byte-equivalent.

| Seed | Winner | Ending turn | Unsupported events | Exact pairs | Damage transactions |
| ---: | --- | ---: | ---: | ---: | ---: |
| 7001 | Raphael | 16 | 14 | 13 | 3 |
| 7002 | Leonardo | 17 | 14 | 8 | 3 |
| 7003 | Leonardo | 17 | 18 | 13 | 5 |
| 7004 | Leonardo | 21 | 21 | 18 | 0 |
| 7005 | Raphael | 16 | 11 | 8 | 5 |

Aggregate evidence:

- 78 unsupported events / 23 exact pairs;
- six block-restriction rejections;
- zero invariant violations;
- 16 noncombat damage transactions: 12 Raphael, Tough Turtle and four Manhole Missile;
- unchanged winners and ending turns.

Arithmetic from the pre-Action baseline is exact: seven Raphael damage limitations are
removed because their supported Alliance damage now executes; four previously silent
Manhole Missile follow-up limitations become visible; `81 - 7 + 4 = 78`. The Raphael pair
leaves the exact-pair set and the Manhole follow-up pair enters it, leaving 23 exact pairs.
These trajectories are execution evidence only, not balance evidence.

## 8. Validation

- Full suite: **258 passed / 1 skipped**
- Dedicated Deal Damage: **25 passed**
- Generic SemanticCoverage: **5 passed**
- Card-data integrity: **5 passed**
- Ruff format check: clean; 31 files already formatted
- Ruff check: clean
- `git diff --check`: clean

## 9. Recommendation

**REJECT — Deal Damage is not yet suitable to bank.**

Smallest evidence-backed correction:

1. Generalize the Oracle-derived target grammar to recognize `each of one or two targets`
   and genuinely equivalent multiple-recipient forms without card-name dispatch.
2. Keep Storm of Steel non-executable with explicit multiple/divided/unsupported-target
   limitations; do not implement its damage transaction.
3. Order or parse target alternatives so All Will Be One is classified as a multi-kind
   target rather than prematurely matching `target opponent` and treating the remainder as
   a follow-up.
4. Recompute and lock exact membership and digests. Expected executable and fully-supported
   membership need not change; recognized membership should include Storm of Steel.

No transaction redesign or gameplay-behavior change is warranted by this audit.
