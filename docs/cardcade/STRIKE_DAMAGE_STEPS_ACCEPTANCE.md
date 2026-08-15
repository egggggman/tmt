# First Strike / Double Strike Combat Damage Steps Acceptance Audit #1

## Decision

**REJECT — one material combat-state lifecycle blocker remains.**

The candidate correctly implements the bounded First Strike / Double Strike combat-damage sequence, including the state-based-action boundary between damage steps. However, it does not clear represented combat state when the end-of-combat step ends. After transition to postcombat main, `_combat_attackers`, declaration flags, and `CombatDamageStepKind.COMPLETE` remain authoritative until cleanup. This contradicts Comprehensive Rules 511.3 and fails the audit's explicit End of Combat reset gate.

Smallest evidence-backed correction: when leaving `END_OF_COMBAT` (or equivalently when entering `POSTCOMBAT_MAIN`), clear the current combat declarations and active damage-step bookkeeping while retaining immutable historical `combat_damage_evidence`. Add a regression proving postcombat main has no current combatants or active/completed damage-step state. No strike grammar, keyword semantics, damage assignment, pilot behavior, or adjacent combat capability needs redesign.

## Audit identity and scope

- Branch: `agent/cardcade-strike-damage-steps`
- Evidence checkpoint: `8abac929cee3e111a4acfb9366d388858fdcbdae`
- Audited candidate implementation fingerprint: `74b78153fb319f75bb6e89a7b94ef1a9bbc73db5`
- Audit type: independent, evidence-only
- Implementation and tests were not modified.
- This report is the only repository artifact created by the audit.

## Authoritative rules finding

The audit used Wizards' current Comprehensive Rules publication and independently checked CR 510.4, 511.3, 704.5, 702.4, and 702.7.

CR 510.4 requires a first combat-damage step if at least one attacker or blocker has First Strike or Double Strike as the combat-damage step begins. Only those creatures deal damage in that first step. A second combat-damage step then occurs; it includes remaining combatants that initially had neither keyword and remaining combatants that currently have Double Strike. First Strike alone therefore does not deal twice, while Double Strike participates once in each eligible step. CR 511.3 removes all represented combatants from combat when the end-of-combat step ends.

The candidate correctly implements the CR 510.4 sequence. It snapshots initial first-step eligibility and initially ordinary combatants, reevaluates current Double Strike for the second step, and prevents transition to End of Combat while an active damage step is unresolved. It does not implement Double Strike as an unconditional duplicate damage call.

The lifecycle failure is confined to CR 511.3: transition from `END_OF_COMBAT` to `POSTCOMBAT_MAIN` does not reset the represented combat state.

## Highest-priority SBA boundary

Independent executable probes confirmed:

- Lethal first-strike damage removes a normal blocker before that blocker can deal regular damage.
- A 4/4 First Strike attacker versus a 2/3 Double Strike blocker produced simultaneous first-step assignments, removed the Double Strike blocker through SBA processing, and produced no second assignment from that blocker.
- A surviving Double Strike creature remained eligible and assigned in both steps.
- Marked nonlethal damage persisted from the first step into the regular step.
- A creature moved from the battlefield between steps did not assign later damage.
- A player reduced to zero during first-step processing caused a winner to be set; the damage-step state became `COMPLETE`, transition proceeded to End of Combat, and a direct attempt to resolve another combat-damage step was rejected.
- Assignment evidence is assembled per authoritative object and the invariant rejects more than one assignment from one source in one damage step.

Acceptance seeds 7001 and 7003 ended during first-strike damage/SBA processing. In both event streams, `player_lost` is followed by resolution evidence for that same first-strike step and no regular damage-step start or resolution. This explains the aggregate 10 first-strike steps but only 8 following regular steps.

## Combat state-machine and identity findings

Passing findings:

- `FIRST_STRIKE` and `REGULAR` are distinct authoritative `CombatDamageStepKind` states with sequence and total-step evidence.
- End of Combat cannot be entered before the active damage step resolves.
- The first step cannot be skipped, repeated, or resolved after it completes; regular damage cannot be resolved early.
- Combat declarations remain stable across the first-to-regular boundary.
- Duplicate attackers or blockers are rejected.
- Fabricated, stale, nonpermanent, and wrong-zone combatants cannot deal damage.
- A removed blocker leaves the attacker blocked; the candidate does not silently approximate Trample.
- Cleanup ultimately clears combat declarations and damage-step bookkeeping.

Blocking finding:

An independent probe completed both strike damage steps and then advanced from End of Combat to postcombat main. The observed state was:

```text
end_of_combat: attacker IDs present; attackers_declared=True; step_kind=complete
postcombat_main: attacker IDs still present; attackers_declared=True; step_kind=complete
```

The state is eventually cleared at cleanup or the next beginning of combat, but CR 511.3 requires creatures to be removed from combat when the end-of-combat step ends. Retaining live current-combat state through postcombat main is an architectural state-machine defect, even though current action legality does not exploit it.

## Damage-assignment matrix

The focused suite and independent probes covered all required pairings:

| Pairing | First step | Regular step | Finding |
|---|---|---|---|
| First Strike attacker vs normal blocker | attacker | surviving normal blocker | correct |
| Normal attacker vs First Strike blocker | blocker | surviving normal attacker | correct |
| First Strike vs First Strike | both | neither | correct |
| Double Strike attacker vs normal blocker | attacker | surviving attacker and blocker | correct |
| Normal attacker vs Double Strike blocker | blocker | surviving attacker and blocker | correct |
| Double Strike vs First Strike | both | surviving Double Strike creature | correct |
| Double Strike vs Double Strike | both | both survivors | correct |
| Unblocked First Strike | once | no second assignment | correct |
| Unblocked Double Strike | once | once | correct |

Lethal and nonlethal first-step interactions and explicit removal between steps also behaved correctly. Each source assigned no more than once in each damage step for which it was eligible.

## Coverage truthfulness

Independent enumeration of the authoritative 472-print / 332-Oracle-object snapshot reproduced the claimed membership:

- Recognized: 12 Oracle objects / 12 fragments
- Bounded payload executable: 12 / 12
- Fully supported parent + payload + follow-up: 7 / 7
- Frozen recognized: 7 cards across 5 decks
- Frozen fully supported: 4 cards across 5 decks

Membership digests reproduced exactly:

- Recognized: `32e10abed618dd875abd28047910371b0ee1be4ad7b634f071bab0e6dbf93725`
- Executable: `32e10abed618dd875abd28047910371b0ee1be4ad7b634f071bab0e6dbf93725`
- Fully supported: `7c03c57d6d1c84a769e0a834597914c718d6bb983381a408b50dc35a553f8ebc`

Recognized objects:

1. Baxter Stockman
2. Casey Jones, Asphalt Hooligan
3. Hard-Won Jitte
4. Leonardo, Leader in Blue
5. Leonardo, Sewer Samurai
6. Leonardo, Worldly Warrior
7. Mouser Attack!
8. Null Group Biological Assets
9. Raphael, the Nightwatcher
10. Shark Shredder, Killer Clone
11. Ticked Off
12. Tokka & Rahzar, Unsupervised

Fully supported objects:

1. Casey Jones, Asphalt Hooligan
2. Leonardo, Sewer Samurai
3. Leonardo, Worldly Warrior
4. Null Group Biological Assets
5. Raphael, the Nightwatcher
6. Shark Shredder, Killer Clone
7. Tokka & Rahzar, Unsupervised

Partial objects preserve explicit limitations:

- Baxter Stockman: unsupported trigger delivery and unsupported vigilance follow-up.
- Hard-Won Jitte: unsupported attachment context.
- Leonardo, Leader in Blue: unsupported activated-ability delivery.
- Mouser Attack!: unsupported modal/targeted temporary-grant context.
- Ticked Off: unsupported targeted temporary-grant context.

Frozen recognized cards are Hard-Won Jitte; Leonardo, Leader in Blue; Leonardo, Sewer Samurai; Mouser Attack!; Null Group Biological Assets; Raphael, the Nightwatcher; and Shark Shredder, Killer Clone. Frozen fully supported cards are Leonardo, Sewer Samurai; Null Group Biological Assets; Raphael, the Nightwatcher; and Shark Shredder, Killer Clone. Both sets touch the expected Casey Jones, Leonardo, Raphael, Shredder, and Splinter decks.

## Leonardo activation and SemanticCoverage

The remaining Leonardo, Leader in Blue fragment is recognized with an executable strike payload but `parent_executable=False` and limitation `strike_activation_context_not_implemented`. Runtime keyword evaluation consumes only fully supported semantics, so Leonardo does not opportunistically gain First Strike. Acceptance evidence retains exactly 5 unsupported events / 1 exact pair for this activation. The missing capability is activated-ability delivery, not strike combat semantics.

## Runtime keyword derivation and architecture scan

Runtime strike state comes from authoritative printed keyword characteristics plus fully supported, Oracle-derived static semantics. The supported dynamic cases are bounded to “During your turn, this creature has first strike” and “Attacking creatures you control have double strike.” Controller and attacker state are evaluated authoritatively.

Source inspection found no card-name dispatch, hard-coded Acceptance card or runtime object ID, pilot-controlled legality, manual duplicated damage loop masquerading as Double Strike, stale-object reuse, or silent strike fallback. The card interpreter emits Action-specific strike semantics paired with generic `SemanticCoverage`; the engine applies only `fully_supported` results.

Unsupported temporary grants, losses, activated abilities, triggers, choices, and attachments remain explicit. This checkpoint does not claim or approximate multiple-blocker ordering, Trample, Deathtouch, Lifelink, defender-selection expansion, extra combats, priority-dependent tricks, activated abilities, or attachment semantics.

## Acceptance Match reconciliation

Seeds 7001–7005 were each replayed twice. Each duplicate JSON artifact was byte-identical.

| Seed | Winner | Ending turn | Unsupported events | Exact pairs | First steps | Following regular steps |
|---:|---|---:|---:|---:|---:|---:|
| 7001 | Raphael | 16 | 10 | 10 | 2 | 1 |
| 7002 | Leonardo | 17 | 13 | 7 | 0 | 0 |
| 7003 | Leonardo | 17 | 13 | 10 | 2 | 1 |
| 7004 | Leonardo | 21 | 15 | 13 | 6 | 6 |
| 7005 | Raphael | 16 | 10 | 7 | 0 | 0 |

Aggregate evidence:

- Unsupported telemetry: 69 events / 21 pairs → 61 events / 18 pairs.
- Exactly 8 events / 3 pairs disappeared through supported strike execution.
- Remaining Leonardo activation limitation: 5 events / 1 pair.
- First-strike damage steps: 10.
- Following regular steps: 8.
- Games ending in first-step damage/SBAs: 2 (seeds 7001 and 7003).
- Assignment roles: 2 First Strike; 10 Double Strike first-step; 2 Double Strike second-step; 108 regular.
- Creatures removed after first damage and before the next step: 5.
- Scry transactions: 8.
- Deal Damage transactions: 16.
- Block-restriction rejections: 6.
- Invariant violations: 0.
- Winners and ending turns: unchanged.

The two missing following regular steps are not omissions: seeds 7001 and 7003 legally ended during first-step damage/SBA processing, and their event streams contain no later regular damage processing.

## Validation

- Full suite: **310 passed / 1 skipped**
- Focused First Strike / Double Strike suite: **29 passed**
- Combat/state-machine regressions (`test_engine07.py` plus `test_engine08c_turn_state.py`): **44 passed**
- Generic SemanticCoverage: **5 passed**
- Card-data integrity: **5 passed**
- Ruff format check: clean (38 files already formatted)
- Ruff check: clean
- `git diff --check`: clean

Passing tests do not waive the independently demonstrated CR 511.3 lifecycle defect.

## Final recommendation

**REJECT — clear current combat declarations and damage-step bookkeeping when End of Combat ends, preserve historical evidence, and add a postcombat-state regression. No other correction is justified by this audit.**
