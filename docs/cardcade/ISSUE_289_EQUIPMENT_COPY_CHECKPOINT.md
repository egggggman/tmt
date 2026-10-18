# Issue #289 — Equipment self-copy checkpoint

## Scope

This checkpoint implements the smallest complete artifact-copy family supported by
the frozen Baseline 005 evidence: a generic activated ability whose Oracle text
creates a token copy of the source Equipment. It is not a Donatello combat-damage
trigger implementation and does not change any deck list.

The accepted fixture is **Improvised Arsenal** in Casey Jones:

`{4}{R}: Create a token that's a copy of this Equipment.`

The parser recognizes the rule from card type and Oracle structure, not from a
card or deck name. Activation uses normal mana payment and stack priority. On
resolution, the source must still be the authoritative battlefield permanent;
otherwise the ability resolves with no effect. A successful copy uses copiable
characteristics only, enters as an independent unattached artifact Equipment
token, and retains source/controller/stack provenance. Counters, attachments,
temporary effects, and other noncopiable state are not copied.

## Evidence

- Semantic runtime: `150b7b5c599371819dee1d9a35ee4c4cfe06a2d30e54e39162e700c2cf97b762`
- Coverage overlay: `ISSUE_289_EQUIPMENT_COPY_CHECKPOINT.json`
- Readiness assessment: `ISSUE_289_EQUIPMENT_COPY_CALIBRATION_READINESS.json`
- Frozen diagnostic: `ISSUE_289_EQUIPMENT_COPY_SMOKE.json`
- Original ledger remains 172 rows; Baseline 005 manifest and deck hashes are unchanged.

Focused fixtures cover generic renamed Equipment recognition, rejection of a
partial target-copy clause and a non-Equipment copy clause, legal payment,
stacked activation, source departure before resolution, independent token
identity, unattached entry, and deterministic replay. The focused combined suite
passes 29 tests. The frozen diagnostic runs six games (each replayed once): 53
activation opportunities, two selections, two payments, two casts, and two
battlefield entries. No copy token resolved naturally in those short games; the
semantic fixture is the execution proof, and the diagnostic is pilot-exposure
evidence only.

## Remaining risk and gates

The two Donatello, Gadget Master combat-damage artifact-copy rows remain open.
They require a separate generic damage-trigger target-selection and copy path and
were deliberately not folded into this activated-ability checkpoint. Hamato
Guardian Stance and Michelangelo Improviser remain explicit unbounded important
effects. Accordingly, checkpoint acceptance can be READY after regression and CI,
but Baseline 005 calibration readiness remains BLOCKED.

No calibration control, deck revision, merge, promotion, or balance conclusion
is authorized by this checkpoint.
