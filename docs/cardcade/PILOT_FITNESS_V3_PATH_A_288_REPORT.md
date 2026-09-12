# Pilot Fitness V3: Path A 288-call execution

Runner commit: `fe5cba6e36390363c1341236d5eb1607d44508b4`. Pre-run: `9fb8574`; spec: `c18a8fc`; Path A: `43bda04`. Preserved invalid attempts: `32e692b` / `b353537`; proof: `37054b7`; defect: `4bb9ed61`.

Actual hook invocations: **288**; returned decisions: **264**; exceptions without a returned decision: **24**. Each scheduled hook was entered once. No retries, option additions, oracle edits, game-state construction, or privacy calls occurred.

The JSONL records every actual return or exception with complete input and expected actions. The committed execution plan records source hashes, frozen oracles, transformations, hook arguments and known input limitations before this run.

| Fixture | Hook/category | Pilot | Calls | Returns | Exceptions | Matches | Stable normalized outcomes |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| V3-P1-001 | main/T | AcceptancePilot | 12 | 12 | 0 | 12 | True |
| V3-P1-001 | main/T | PassingPilot | 12 | 12 | 0 | 0 | True |
| V3-P1-002 | attack/T | AcceptancePilot | 12 | 12 | 0 | 12 | True |
| V3-P1-002 | attack/T | PassingPilot | 12 | 12 | 0 | 0 | True |
| V3-P1-003 | blocks/T | AcceptancePilot | 12 | 12 | 0 | 12 | True |
| V3-P1-003 | blocks/T | PassingPilot | 12 | 12 | 0 | 0 | True |
| V3-P1-004 | priority/T | AcceptancePilot | 12 | 12 | 0 | 0 | True |
| V3-P1-004 | priority/T | PassingPilot | 12 | 12 | 0 | 0 | True |
| V3-P1-005 | main/B | AcceptancePilot | 12 | 12 | 0 | 12 | True |
| V3-P1-005 | main/B | PassingPilot | 12 | 12 | 0 | 12 | True |
| V3-P1-006 | attack/B | AcceptancePilot | 12 | 12 | 0 | 12 | True |
| V3-P1-006 | attack/B | PassingPilot | 12 | 12 | 0 | 12 | True |
| V3-P1-007 | blocks/B | AcceptancePilot | 12 | 12 | 0 | 12 | True |
| V3-P1-007 | blocks/B | PassingPilot | 12 | 12 | 0 | 12 | True |
| V3-P1-008 | priority/B | AcceptancePilot | 12 | 12 | 0 | 12 | True |
| V3-P1-008 | priority/B | PassingPilot | 12 | 12 | 0 | 12 | True |
| V3-P2-001 | scry/R | AcceptancePilot | 12 | 12 | 0 | 0 | True |
| V3-P2-001 | scry/R | PassingPilot | 12 | 12 | 0 | 0 | True |
| V3-P2-002 | sneak/T | AcceptancePilot | 12 | 12 | 0 | 12 | True |
| V3-P2-002 | sneak/T | PassingPilot | 12 | 12 | 0 | 0 | True |
| V3-P2-003 | scry/B | AcceptancePilot | 12 | 12 | 0 | 12 | True |
| V3-P2-003 | scry/B | PassingPilot | 12 | 12 | 0 | 12 | True |
| V3-P2-004 | sneak/B | AcceptancePilot | 12 | 0 | 12 | 0 | True |
| V3-P2-004 | sneak/B | PassingPilot | 12 | 0 | 12 | 0 | True |

## Interpretation limits recorded before execution

- Priority inputs are sealed GameViewV2 objects, not the annotated PriorityViewV2 type. They are passed unchanged to the actual priority hook; policy output does not certify this interface.
- V3-P1-005 includes land-play options despite its empty/pass-only label. Only the frozen boundary predicate is compared; the input contradiction is unresolved.
- V3-P2-004 supplies zero Sneak options despite its pass-only label. An exception is a no-return outcome, not an invented pass action.
- V3-P2-002 records winner null despite its lethal objective. Matching the sealed cast does not independently demonstrate lethal play.
- Seats/IDs are invertible structural transforms; option order is reversed. Their exact reconstructed instances and main-stage argument are explicit in the pre-call plan. Canonical seal digests are not misrepresented as hashes of newly reconstructed variants.

No pooled Pilot Fitness PASS/FAIL is issued; HQ review is pending. Privacy 96 remains INCONCLUSIVE/unexecuted; filtering unchanged; calibration blocked. Action #33 and Prototype 0.3 remain unauthorized.
