# First Strike / Double Strike Combat Damage Steps Acceptance Audit #2

## Decision

**ACCEPT — corrected First Strike / Double Strike combat-damage steps are suitable to bank.**

The CR 511.3 lifecycle blocker from Audit #1 is corrected at the engine-owned transition into postcombat main. All mutable state for the completed combat is cleared at that boundary, no equivalent stale field remains, and immutable combat evidence survives. The correction does not alter strike eligibility, the first-to-regular damage-step sequence, the intervening state-based-action boundary, coverage membership, or deterministic Acceptance Match behavior.

## Audit identity and controls

- Branch: `agent/cardcade-strike-damage-steps`
- Evidence checkpoint: `8abac929cee3e111a4acfb9366d388858fdcbdae`
- Corrected candidate fingerprint: `1368b5399aecbf5ae24415cd359e301c6192c969`
- Audit type: independent, evidence-only
- Implementation and tests were not modified during this audit.
- Historical Audit #1 SHA-256 before and after Audit #2: `824177f2483558b21a678709e05736b4469cdfe6efff469a5b1c57bd3a9a179e`

## Reproduction and correction of REJECT #1

Audit #1 preserved the original executable failure signature:

```text
end_of_combat: attacker IDs present; attackers_declared=True; step_kind=complete
postcombat_main: attacker IDs still present; attackers_declared=True; step_kind=complete
```

The corrected candidate was independently exercised through the same lifecycle. State remained present during End of Combat, then transition into postcombat main produced:

```text
attackers=()
blocks=()
attackers_declared=False
blockers_declared=False
combat_damage_resolved=False
step_kind=none
sequence=0
total_steps=0
first_qualified_ids=()
first_double_strike_ids=()
regular_initial_ids=()
```

The original stale-state condition is therefore no longer present.

## Complete per-combat state inventory

Source inspection found the following mutable current-combat fields:

| Field | Semantic role | During relevant combat | Postcombat main |
|---|---|---|---|
| `_combat_attackers` | authoritative attacking object IDs | retained | empty |
| `_combat_blocks` | attacker/blocker assignments | retained | empty |
| `_attackers_declared` | declaration completion | retained | false |
| `_blockers_declared` | declaration completion | retained | false |
| `_combat_damage_resolved` | active step resolution guard | retained/updated | false |
| `_combat_damage_step_kind` | none/first/regular/complete | retained/updated | `NONE` |
| `_combat_damage_step_number` | current step sequence | retained | zero |
| `_combat_damage_total_steps` | one- or two-step sequence | retained | zero |
| `_first_damage_qualified_ids` | initial First/Double Strike eligibility | retained across steps | empty |
| `_first_double_strike_ids` | first-step Double Strike role evidence | retained across steps | empty |
| `_regular_damage_initial_ids` | initially ordinary second-step eligibility | retained across steps | empty |

No other mutable per-combat participant or eligibility collection was found. `combat_damage_evidence` is deliberately excluded from this reset because it is immutable historical evidence rather than current combat state.

## Correct lifecycle boundary

Independent probes established that the reset is not premature:

- Attackers remain authoritative after Declare Attackers.
- Attackers and blocker assignments remain authoritative after Declare Blockers.
- All declaration and eligibility fields survive first-strike damage and the intervening SBA processing.
- The regular damage step begins with the required initial and current eligibility data intact.
- Completed declarations and `CombatDamageStepKind.COMPLETE` remain available during End of Combat.
- They are cleared only when the engine enters `POSTCOMBAT_MAIN`.

The reset is implemented by `Game._on_enter_step`, which invokes the engine-owned `_reset_current_combat_state` at postcombat-main entry. Neither the Pilot nor Acceptance runner performs the reset. The runner calls the generic engine invariant after transition only as an assertion of engine truth.

## Historical evidence preservation

An independent blocked Double Strike probe retained a two-record `combat_damage_evidence` tuple across the postcombat reset. It continued to prove:

- a first-strike damage step occurred;
- a regular damage step occurred;
- the Double Strike source assigned in both steps;
- the ordinary blocker assigned in the regular step;
- assignment sources, targets, amounts, and roles;
- objects removed before a later step, where applicable;
- the completed two-step sequence.

Current combat state and historical evidence are architecturally separate: `_reset_current_combat_state` does not modify `combat_damage_evidence` or the typed event ledger.

## Terminal-game behavior

Independent first-step lethal-player probes and Acceptance seeds 7001 and 7003 confirmed:

- `player_lost` occurs during first-step damage/SBA processing.
- The resolved first-step evidence is recorded.
- No regular damage step is fabricated or resolved.
- The engine remains coherently in End of Combat with `COMPLETE` state and historical evidence.
- A direct later damage-resolution attempt is rejected.
- No artificial postcombat-main transition is required to satisfy the invariant; the invariant permits valid terminal End of Combat state.

The lifecycle correction therefore does not continue combat after a legal game end and does not require cleanup after termination merely to manufacture a clean state.

## Fresh subsequent combat

The adversarial sequence combat A → postcombat main → cleanup → later turn → combat B was exercised. Combat B began with empty attackers, blockers, declaration flags, strike qualification sets, and damage-step bookkeeping. A permanent surviving combat A retained its runtime identity as a battlefield object, but its former attacker/blocker role did not survive and did not become a valid combat reference in combat B without a new authoritative declaration.

## Engine invariant

The new invariant was independently exercised in four states:

- valid live combat state passed;
- clean postcombat state passed;
- deliberately injected postcombat attacker state plus `CombatDamageStepKind.COMPLETE` failed with `completed combat state leaked outside the combat phase`;
- the failed invariant check did not mutate the deliberately fabricated state.

The invariant covers every inventoried per-combat field rather than only attackers or the step kind. The Acceptance runner calls `Game.check_invariants()` after engine transition to postcombat main. An audit-only instrumented `Game` subclass additionally inspected all fields after every such transition; 174 postcombat transitions across two complete five-seed replay sets were clean.

## Strike and SBA regression

Previously accepted Audit #1 findings were reconfirmed by source inspection, focused tests, and executable probes:

- A first damage step is created only if an attacker or blocker has First Strike or Double Strike at the required boundary.
- First Strike sources assign only in the first step.
- Double Strike sources assign once in the first step and, if still present and currently eligible, once in the regular step.
- Initially ordinary surviving combatants assign in the regular step.
- End of Combat cannot occur between unresolved damage steps.
- SBAs run after first-step damage and before the regular step.
- Lethal first-step damage removes ordinary and Double Strike creatures before later assignments.
- Nonlethal marked damage persists into the regular step.
- Creatures removed between steps do not deal later damage.
- Fabricated, stale, duplicate, nonpermanent, and wrong-zone combatants cannot participate.
- First-step game loss prevents later combat damage.
- Static and printed keyword evaluation remains Oracle-derived and card-name independent.
- Unsupported activations, attachments, triggers, temporary grants, and follow-ups remain explicit.

No regression was found in deterministic progression or authoritative damage assignment.

## Coverage verification

Independent corpus enumeration and locked regression evidence reproduced:

- Recognized: 12 Oracle objects / 12 fragments
- Bounded payload executable: 12 / 12
- Fully supported: 7 / 7
- Frozen recognized: 7 cards across 5 decks
- Frozen fully supported: 4 cards across 5 decks

Digests reproduced exactly:

- Recognized: `32e10abed618dd875abd28047910371b0ee1be4ad7b634f071bab0e6dbf93725`
- Executable: `32e10abed618dd875abd28047910371b0ee1be4ad7b634f071bab0e6dbf93725`
- Fully supported: `7c03c57d6d1c84a769e0a834597914c718d6bb983381a408b50dc35a553f8ebc`

The seven fully supported objects remain Casey Jones, Asphalt Hooligan; Leonardo, Sewer Samurai; Leonardo, Worldly Warrior; Null Group Biological Assets; Raphael, the Nightwatcher; Shark Shredder, Killer Clone; and Tokka & Rahzar, Unsupervised.

Leonardo, Leader in Blue remains recognized with an executable strike payload but unsupported activated-ability delivery. The five remaining Acceptance events / one exact pair retain `strike_activation_context_not_implemented`; runtime evaluation does not grant First Strike without activation delivery.

## Acceptance Match reconciliation

Seeds 7001–7005 were replayed twice through an audit-only postcombat-state probe. Duplicate serialized results were byte-equivalent, and every postcombat transition was clean.

| Seed | Winner | Ending turn |
|---:|---|---:|
| 7001 | Raphael | 16 |
| 7002 | Leonardo | 17 |
| 7003 | Leonardo | 17 |
| 7004 | Leonardo | 21 |
| 7005 | Raphael | 16 |

Aggregate evidence matched exactly:

- Unsupported telemetry: 61 events / 18 exact pairs
- First-strike damage steps: 10
- Following regular steps: 8
- Terminal first-step combats: 2
- First Strike assignments: 2
- Double Strike first-step assignments: 10
- Double Strike second-step assignments: 2
- Creatures removed between steps: 5
- Scry transactions: 8
- Deal Damage transactions: 16
- Block-restriction rejections: 6
- Invariant violations: 0
- Winners and ending turns: unchanged
- Duplicate runs: byte-equivalent
- Audited postcombat transitions: 174 / 174 clean

The difference between 10 first steps and 8 following regular steps is fully accounted for by the two legal first-step game endings.

## Validation

- Full suite: **314 passed / 1 skipped**
- Focused strike suite: **33 passed**
- Combat/state-machine regressions: **44 passed**
- Generic SemanticCoverage: **5 passed**
- Card-data integrity: **5 passed**
- Ruff format check: clean (38 files already formatted)
- Ruff check: clean
- `git diff --check`: clean
- Historical Audit #1 SHA-256: unchanged at `824177f2483558b21a678709e05736b4469cdfe6efff469a5b1c57bd3a9a179e`

No material blocker remains within the bounded First Strike / Double Strike combat-damage-step checkpoint.

## Final recommendation

**ACCEPT — corrected First Strike / Double Strike combat-damage steps are suitable to bank.**
