# V3 Phase 1 preparation inventory and readiness stop

**Phase 1 scope: Main Action, Attack, Blocks, Priority. No Pilot invocation.**

Specification V3 remains governing at `c18a8fc`; the design assessment and all
prior evidence remain intact. This candidate does not alter the engine, Pilots,
quotas, evaluator, or scoring authorization.

## What was constructed

The existing frozen Acceptance Stage 002 records were re-indexed into a Phase 1
reachability inventory. They contain 16 authenticated game records across
canonical and reversed orientations, opportunity witnesses, transaction counts,
seeds, seat bindings and invariant results. These are genuine engine evidence
that represented states and timing boundaries occur. They are deliberately
marked `REACHABILITY_ONLY_UNSEALED`; they are not silently promoted to fitness
fixtures.

Each candidate record still lacks the complete Pilot observation and option
payload, an independent T/R/B oracle and acceptable set, a genuinely justified
seat counterpart, option-order and runtime-ID transformations, and privacy
eligibility. Those fields are mandatory V3 seal evidence.

## Structural U applicability

For these four direct decision surfaces, U is structurally outside the hook:

- Main Action generates the action choice before execution. The supported
  hand-bottom replacement decision is a separate nested chooser after a spell
  resolves, so it belongs to Hand-bottom/Draw rather than Main Action U.
- Attack and Blocks enumerate combat choices from visible current combat state;
  no replacement Draw is part of either choice surface.
- Priority enumerates pass/represented responses at a fixed engine-owned epoch;
  Draws from later resolved effects are not inputs to the Priority decision.

This structural record supports `U NOT APPLICABLE` for Phase 1, subject to HQ's
independent review of the frozen option generators. It does not make T, R or B
pass, and it does not waive their witness requirements.

## Current Phase 1 status

| Hook | T | R | U | B | Status |
| --- | --- | --- | --- | --- | --- |
| Main Action | INCONCLUSIVE: no fitness oracle witness | INCONCLUSIVE: no resource table | NOT APPLICABLE by structural record | INCONCLUSIVE: no sealed boundary witness | Not sealable |
| Attack | INCONCLUSIVE: no fitness oracle witness | CONDITIONALLY REQUIRED where a concrete equal-safety resource comparison is represented; none sealed | NOT APPLICABLE by structural record | INCONCLUSIVE: no sealed boundary witness | Not sealable |
| Blocks | INCONCLUSIVE: no fitness oracle witness | CONDITIONALLY REQUIRED where represented; none sealed | NOT APPLICABLE by structural record | INCONCLUSIVE: no sealed boundary witness | Not sealable |
| Priority | INCONCLUSIVE: no fitness oracle witness | CONDITIONALLY REQUIRED where represented; none sealed | NOT APPLICABLE by structural record | INCONCLUSIVE: no sealed boundary witness | Not sealable |

The stopping condition is specific: the required T/B evidence and any applicable
R evidence have not been independently reconstructed into V3 oracle witnesses.
The existing acceptance records prove reachability and engine behavior, but do
not prove Pilot competence. This is not a claim that these competencies are
unsupported by the frozen engine; it identifies the exact missing construction
work.

No canonical fixtures are counted. `F`, privacy `K`, and the final invocation
count remain null; the formula remains `24F + 4K`. No Phase 2 work, including
Hand-bottom/Draw, was performed.

## Reproduction

```powershell
.venv/Scripts/python.exe scripts/prepare_v3_phase1_packet.py
```

The generated inventory and this report have SHA-256 sidecars using canonical
UTF-8/LF bytes. Pilot scoring remains unauthorized.
