# Action #29 authorization audit: Casey Jones, Vigilante

Audited exact evidence head `f11ed7efb5e7bd6cd7da73f0ced2aa83ebb89468` on clean local `main`. Audit only; no production changes or new semantic support. The authoritative Issue #96 baseline remains `e63c6aad53464aae37f8a3b7326f2478c5ad1094` with 25 / 5 / 134. Vigilante has two reached-unsupported witnesses; witness count alone is not the selection criterion.

## Decision for HQ

**Conditionally feasible as one bounded semantic.** No foundational turn-engine replacement appears necessary from code inspection. However, delayed scheduling is not already implemented: upkeep has no delivery hook and the runners currently advance through it without servicing a Stack. Authorization must explicitly include a one-shot delayed record, authenticated upkeep event/delivery, and a small runner integration change. If those additions are excluded, this candidate is blocked; simply combining draw and discard is insufficient.

This is an architecture assessment, not proof of an implemented delayed transaction and not authorization. Stop and return to HQ if implementation requires a general event scheduler, arbitrary delayed grammar, extra-turn/skip-step machinery, or unrelated rule expansion.

Exact bounded fragment, as preserved in the Issue #96 ranking:

> When Casey Jones enters, draw three cards. At the beginning of your next upkeep, discard three cards at random.

## Existing primitives and gaps

References below refer to the audited SHA.

| Area | Existing evidence | Bounded addition required |
|---|---|---|
| Turn/upkeep boundary | `engine07.py:5824` transition_to enforces sequential NEXT_STEP, increments turn/active player, logs step_started and calls _on_enter_step; `:5858` advance_to visits every intermediate step. UPKEEP already exists. | Emit/authenticate an upkeep-began event only on the real transition; detect due records there. No alternate turn engine. |
| Scheduling | `engine07.py:5867` _on_enter_step implements untap/draw/combat/cleanup but no upkeep delivery. RulesEventKind/TriggerEffect have no delayed-upkeep case. | One immutable record per resolved ETB, keyed by creation identity, controller, source/event/Stack provenance and creation boundary; pending/delivered/consumed lifecycle. This record is new work. |
| Runner boundary | `engine07.py:5931` begin_turn advances straight to precombat main. `stage002.py:576` and `smoke01.py:266` call it. transition_to rejects a nonempty Stack. | Runners must traverse the beginning steps explicitly and drain existing Priority before advancing from upkeep to draw. Reuse `stage002.py:412` _drain_priority and unchanged Pilot choices. Do not auto-resolve the delayed effect or weaken the unresolved-Stack guard. Keep the compatibility helper's contract explicit. |
| ETB and Stack/Priority | `engine07.py:3613` _enqueue_trigger, `:3713` _put_pending_triggers_on_stack, `:6246` process_priority_resolution and `:6311` _begin_priority_window provide registration, deterministic APNAP delivery and all-pass resolution. | Exact-fragment ETB effect plus a dedicated delayed effect using this lifecycle. Delayed delivery must authenticate the scheduling record; do not require its original source to remain on the battlefield or reread its current controller. |
| Draw | `engine07.py:5809` draw accepts count and moves each top-library incarnation through move_object; empty-library failure is recorded for state-based actions. Stockman `:3205` demonstrates resolution-time draw with evidence. | Draw three at ETB resolution; record all actual movements, partial draw and failure state. A failed later draw must not erase earlier draws or bypass existing loss processing. Existing boolean return alone is insufficient evidence for a three-card transaction. |
| Randomness | `engine07.py:1117` DeterministicRNG exports/restores state and records domain-separated shuffled permutations or bounded randrange transitions. | At delayed resolution, sample authoritative current hand identities without replacement using this service. Do not use a chooser, global random, preselected ETB hand, or arbitrary hidden-zone scripting. |
| Discard/identity | `engine07.py:1547` move_object rejects unregistered/former/relinked or wrongly zoned objects and creates destination incarnations. Stockman uses hand-to-graveyard movement, but its chooser-based single discard is not a random-three API. | Validate the whole current hand; discard min(3, hand size) distinct sampled objects through move_object, retaining hand/graveyard identity pairs. Empty/short hands must finish legally. Preserve remaining hand order. |
| Evidence/classification | Stockman's validator `engine07.py:3252`, Courier `food_search07.py:267`, `_executed_conformance_references` at `engine07.py:9254`, and `stage002.py:633,873,1187` provide bounded reconstruction patterns. | Add a linked ETB/scheduling/upkeep/Stack/random-discard ledger and independent serialized reconstruction. Draw-only trigger_resolved evidence must not silently certify the entire compound semantic as complete. Preserve pending delayed obligations and distinguish pending, delivered, resolved, and terminal-game cases. |

## Smallest acceptable design boundary

1. Recognize only the frozen exact fragment; no card/deck-name gameplay dispatch or generic delayed grammar.
2. Resolve the original ETB through existing Priority: draw three, create one one-shot scheduling record with captured controller and original provenance. Multiple entries create independent records, even for the same physical card returning as a new incarnation.
3. Fire on the first subsequently entered upkeep of that captured controller. The opponent's upkeep does not qualify. Creation after an upkeep has begun must wait for a later matching upkeep. Use authenticated boundary identity/order, not an unqualified turn+1 calculation. No source-presence dependency.
4. At the matching upkeep, atomically mark delivery and enqueue one ordinary triggered Stack object from the record. Multiple due records use existing deterministic delivery ordering. Mark delivery separately from resolution so repeated boundary processing cannot enqueue twice; each record can resolve at most once.
5. Resolve mandatory random discard from the hand as it exists then, after all players pass. An auditable shuffled copy of hand identities followed by the first min(3,n) identities is sufficient for a bounded uniform sample without replacement. Log RNG domain/state/permutation and every movement. Choose and document RNG consumption for n=0 and n<=3; do not mutate unrelated zones.
6. Reconstruct the whole chain, including controller, due boundary, original source incarnation, scheduling-record identity, trigger/Stack identities, resolution-time hand, RNG and graveyard results. The source may depart or change control without erasing or transferring the scheduled obligation.

The runner change is a scheduling integration requirement, not Pilot tuning. It must preserve roster, seeds, orientations, action policy and 16/32 budget. Existing Stage trajectories may change naturally after support is implemented; prior 25 / 5 / 134 is a comparison, never a forced result.

## Required proofs if HQ authorizes implementation

- Exact grammar/near-neighbor fail-closed; one ETB/one schedule; no early draw/discard; real Priority for both Stack resolutions.
- Both controllers; opponent upkeep skipped; creation during/after own upkeep; multiple independent records; source departure/reentry/control change; repeated upkeep processing and replay rejection.
- Random sample identity distinction for equal-valued cards, hand sizes 0/1/2/3/>3, changed hand between ETB and upkeep, fixed-seed replay, stale/relinked/fabricated identities and forged scheduling/RNG evidence.
- No advance to draw/main with unresolved upkeep Stack; all runner transitions remain legal; no direct auto-resolution shortcut.
- Partial/failed draws, game termination before the due upkeep, pending versus completed evidence, and no false EXECUTED claim from only the immediate draw.
- Full reconstruction and existing Courier/Zoo/Stockman/Donatello/Shredder continuity. Then the authorized focused/full/Stage/Smoke checks; no additional matrix was executed for this audit.

## Audit validation and preservation

Read-only source inspection plus existing primitive regressions:

```
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/test_engine08c_turn_state.py tests/test_engine08h_rng.py tests/test_stockman_draw_discard_action.py
```

**46 passed.** These establish existing primitives only; they do not test a delayed implementation. No production or test changes, no new Stage games, and no changes to prior evidence. This audit and its SHA-256 sidecar are the only new artifacts.

**HQ gate: bounded authorization review ready, with the explicit scheduling/runner additions above. Action #29 implementation remains NOT AUTHORIZED pending HQ decision. Jury-Rig untouched. Calibration BLOCKED. Prototype 0.3 NOT AUTHORIZED.**
