# Deal Damage Action Acceptance Audit #2

## Audit result

- Date: 2026-08-14
- Branch: `agent/cardcade-deal-damage`
- Evidence checkpoint: `a5c64b0e2f4c8aead759b12178eea52d1dfd20d0`
- Candidate state: corrected, validated, and uncommitted
- Audit mode: evidence-only; implementation and tests were not modified
- Historical Audit #1 SHA-256:
  `F84F1DD6CAF75374919F36FCC38CB17738593C091D2E69E6DAB7C60FE7F628CB`
- Recommendation: **ACCEPT**

## 1. Audit #1 correction verification

### Storm of Steel

Authoritative Oracle text:

> Storm of Steel deals 2 damage to each of one or two targets.

The instruction is now recognized by reusable target grammar for `each of one or two
targets`. The same grammar accepts the equivalent bounded syntax `each of up to N targets`.
Production source contains no reference to Storm of Steel or its name.

The resulting generic coverage is:

- recognized: yes;
- payload executable: no;
- parent spell context executable: yes;
- follow-up executable: yes;
- fully supported: no;
- limitation: `variable_count_multiple_damage_targets_not_implemented`.

That limitation accurately describes the represented boundary: the number and identities
of multiple recipients require target selection not implemented by this bounded Action.
The text does not divide one damage amount among recipients, so the limitation does not
incorrectly claim divided-amount semantics.

Recognition does not produce a cast program. An independently constructed renamed spell
with the same grammar is absent from represented cast options, announcement returns no
stack object, life and marked damage remain unchanged, and no `DAMAGE_DEALT` event or
`damage_dealt` evidence is produced.

### All Will Be One

Authoritative Oracle text:

> Whenever you put one or more counters on a permanent or player, this enchantment deals
> that much damage to target opponent, creature an opponent controls, or planeswalker an
> opponent controls.

The parser now considers the complete multi-kind target phrase before the narrower `target
opponent` alternative. Independent interpretation produces exactly:

- `dynamic_damage_amount_not_implemented`
- `damage_multi_kind_target_not_implemented`
- `damage_trigger_context_not_implemented`

Payload and parent/context are non-executable, follow-up is executable, and full support is
false. `damage_followup_semantics_not_implemented` is absent. The unsupported targeting
requirement is therefore attached to its real semantic boundary rather than being created
by a truncated match.

## 2. Exact coverage reconciliation

The authoritative 472-print / 332-Oracle-object corpus independently yields:

| Classification | Frozen roster | Full pool |
| --- | --- | --- |
| Recognized | 6 cards / 3 decks | 28 objects / 29 fragments |
| Bounded payload executable | 4 cards / 2 decks | 12 objects / 12 fragments |
| Fully supported | 1 card / Raphael deck | 2 objects / 2 fragments |

### Frozen membership

Recognized:

- Cool but Rude
- Manhole Missile
- Mouser Foundry
- Raphael, Tough Turtle
- Spicy Oatmeal Pizza
- Tenderize

Recognized deck exposure is Casey Jones, Michelangelo, and Raphael.

Bounded payload executable:

- Cool but Rude
- Manhole Missile
- Mouser Foundry
- Raphael, Tough Turtle

Executable deck exposure is Casey Jones and Raphael. Raphael, Tough Turtle is the sole
fully supported frozen-roster object and is exposed in the Raphael deck.

### Full-pool recognized membership

- All Will Be One
- Blasphemous Act
- Bot Bashing Time
- Brilliance Unleashed
- Casey Jones, Back Alley Brute
- City of Brass
- Cool but Rude
- Electric Seaweed — two recognized fragments
- Everything Pizza
- Exploding Barrel
- General Traag, Heart of Stone
- Go Ninja Go
- Grand Coliseum
- Hamato Ninpō
- Jennika's Technique
- Manhole Missile
- Mouser Foundry
- Raphael, Tough Turtle
- Shellshock
- Slash, Reptile Rampager
- Special Move
- Spicy Oatmeal Pizza
- Storm of Steel
- Super Combo
- Swift Demise
- Tenderize
- Tokka & Rahzar, Terrible Twos
- Weather Maker

Relative to rejected Audit #1 membership, Storm of Steel is the only added object and
fragment. No other corpus member moved into or out of recognition.

### Full-pool bounded executable membership

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

### Fully supported membership

- Raphael, Tough Turtle
- Slash, Reptile Rampager

### Independent digests

- recognized: `b8aa5f14cda90075a37af4cac2fab889d6c5f3299973cf4303f603e180e0d39a`
- bounded executable: `5c977d6a1386af69dc65c694dcb146d1e5b52a7278a085df61ae667b852a89f1`
- fully supported: `f0f5e98cedf31748f558a83a20b69834ce31fec43667aa4045de30958769a740`

The remaining unrecognized damage-text objects were inspected individually. They are
combat-damage triggers, double strike/trample/deathtouch or indestructible reminder text,
damage-received triggers, Fight reminder text, damage doubling, or prevention/replacement
semantics. None is another missed direct Deal Damage instruction in this bounded Action.

The seven pre-existing context-sensitive UNKNOWN objects remain unchanged:

- Arcane Signet
- Chromatic Lantern
- Command Tower
- Double Jump // Flying Kick
- Exotic Orchard
- Fast Forward
- Plague of Vermin

## 3. SemanticCoverage regression

`DamageProgram` remains Action-specific and produces the accepted generic
`SemanticCoverage` value. Recognition, payload execution, parent/context execution,
follow-up execution, and full support remain separate.

Independent probes confirm:

- Storm recognition does not imply payload execution or full support;
- executable payloads under unsupported triggers, activations, and choices remain
  undelivered;
- targeting limitations are attached to payload/target semantics rather than follow-up;
- parent limitations prevent opportunistic delivery;
- follow-up limitations survive even after a damage payload executes.

Manhole Missile still executes its fixed three-damage transaction through Hand → Stack →
resolution while retaining `damage_followup_semantics_not_implemented` for its optional
hand-to-library and draw instruction. Raphael, Tough Turtle remains fully supported for the
represented Alliance delivery and target-opponent payload.

## 4. Focused transaction regression

The focused adversarial suite and direct state/event probes reconfirm:

- exact player-life reduction and the existing life-zero loss boundary;
- marked creature damage without base-toughness mutation;
- nonlethal marked damage persistence until Cleanup;
- lethal-damage processing through the SBA;
- authoritative source and recipient identity;
- fabricated equal-valued and stale runtime object rejection;
- atomic invalid transactions with no partial life, damage, zone, event, or object mutation;
- typed source ID, recipient, amount, fragment, and noncombat evidence;
- separation from life loss, destroy, and `-N/-N` semantics;
- deterministic duplicate execution.

No contradictory transaction evidence was found.

## 5. Architecture and special-case scan

Production searches found no Storm of Steel or All Will Be One name dispatch, roster
membership dispatch, acceptance-seed handling, pilot coupling, or hard-coded corpus result.
Those names occur only in coverage tests that lock independently derived membership.

The longest multi-kind target alternative is evaluated before the narrower target-opponent
alternative. Equivalent variable-count multiple-target grammar follows the same generic
classification. No broader target phrase in the current authoritative corpus is silently
swallowed by a shorter recognized alternative.

The correction changes interpretation and evidence classification only. It does not add a
damage target kind, casting path, transaction branch, replacement rule, or silent fallback.

## 6. Acceptance replay

Seeds 7001–7005 were each replayed twice. Duplicate snapshots were byte-equivalent.

| Seed | Winner | Ending turn | Unsupported events | Exact pairs | Damage transactions |
| ---: | --- | ---: | ---: | ---: | ---: |
| 7001 | Raphael | 16 | 14 | 13 | 3 |
| 7002 | Leonardo | 17 | 14 | 8 | 3 |
| 7003 | Leonardo | 17 | 18 | 13 | 5 |
| 7004 | Leonardo | 21 | 21 | 18 | 0 |
| 7005 | Raphael | 16 | 11 | 8 | 5 |

Aggregate:

- 78 unsupported events / 23 exact pairs;
- 16 noncombat damage transactions;
- 12 Raphael, Tough Turtle transactions;
- four Manhole Missile transactions;
- four explicit Manhole Missile follow-up limitations;
- six block-restriction rejections;
- zero invariant violations;
- unchanged winners and ending turns.

The recognition-only correction causes no gameplay or acceptance-telemetry movement.
These trajectories remain execution evidence, not balance evidence.

## 7. Validation

- Full suite: **262 passed / 1 skipped**
- Dedicated Deal Damage suite: **29 passed**
- Generic SemanticCoverage suite: **5 passed**
- Card-data integrity: **5 passed**
- Ruff format: clean; 31 files already formatted
- Ruff check: clean
- `git diff --check`: clean
- Historical Audit #1 SHA-256:
  `F84F1DD6CAF75374919F36FCC38CB17738593C091D2E69E6DAB7C60FE7F628CB`

## 8. Recommendation

**ACCEPT — corrected Deal Damage Action is suitable to bank with its documented bounded
coverage.**

The two Audit #1 blockers are resolved at the Oracle recognition and classification layer.
No material transaction, delivery, architecture, identity, determinism, telemetry, or
corpus-coverage defect remains within the accepted bounded scope. Unsupported damage
semantics remain explicit and must not be credited as implemented by this acceptance.
