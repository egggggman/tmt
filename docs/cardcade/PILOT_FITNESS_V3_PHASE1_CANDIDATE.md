# V3 Phase 1 fitness candidate

**CANDIDATE / NOT SEALED FOR SCORING.** Specification V3 remains governing at
`c18a8fc`; reachability baseline `20fbfad` is preserved. No Pilot was imported,
invoked or scored.

The reconstruction script creates eight authentic candidate records from the
frozen engine without either Pilot:

| IDs | Hook/category | Witness |
| --- | --- | --- |
| V3-P1-001 | Main Action / T | Manhole Missile clears a blocker, then a Giant attacks through the sealed combat horizon. Cast wins; pass does not. |
| V3-P1-002 | Attack / T | A 20-power Giant attacks an undefended opponent. Attack wins; pass does not. |
| V3-P1-003 | Blocks / T | A defender blocks a lethal 20-power Giant. Block preserves life; pass loses. |
| V3-P1-004 | Priority / T | A Fugitive Droid activation counters a targeted damage spell. Activation preserves the target; pass allows damage. |
| V3-P1-005 | Main Action / B | Empty-hand main phase exposes pass-only behavior. |
| V3-P1-006 | Attack / B | No attackers exposes pass-only attack behavior. |
| V3-P1-007 | Blocks / B | No blockers exposes pass-only block behavior. |
| V3-P1-008 | Priority / B | A Stack window with no counter source exposes pass-only Priority behavior. |

For every candidate the packet records the recipient-specific V2 view, complete
engine-generated options, every relevant option branch, the supported horizon,
and an independent acceptable set. T branches use winner/life or preservation
consequences; B branches preserve the exact empty/pass-only boundary.

U is sealed `NOT APPLICABLE` for these four direct surfaces under the structural
record in the Phase 1 inventory. The replacement Draw is a separate chooser or
a later resolved effect, not an input to these decisions.

The candidate is not yet pre-run sealed. Remaining required evidence is explicit
in the JSON: justified opposite-seat counterparts, executed option-order and
runtime-ID transformations, privacy eligibility/pairs, and independent oracle
review. No candidate is counted as a scored fixture until those checks are
completed. `F = 8` is provisional and `K` remains null; the formula is
`24F + 4K` only after canonical sealing.

Reproduce with:

```powershell
.venv/Scripts/python.exe scripts/build_v3_phase1_fitness_packet.py
```
