# Four-fixture remediation candidate

Implementation: `533bdd1d3211e7d8129a3a6da270dbbd5ccfc06f`. Original evidence d880c36 and diagnosis decb9eb2 preserved.

96 actual hooks: four fixtures, two seats, three variants, two replays, two Pilots. No clean competencies rerun.

Priority uses PriorityViewV2; AcceptancePilot takes a supplied opposing-spell counter; PassingPilot remains pass-only. Scry policy is unchanged; all four creature-top actions are acceptable. Main has an empty hand and only pass. Sneak spends its sole cast, drains Priority, then offers a genuine pass in declare_blockers; the old no-unblocked-attacker label is replaced.

| Fixture | Pilot | Calls | Returns | Exceptions | Legal | Matches | Stable |
|---|---|---:|---:|---:|---:|---:|---|
| V3-P1-004 | AcceptancePilot | 12 | 12 | 0 | 12 | 12 | True |
| V3-P1-004 | PassingPilot | 12 | 12 | 0 | 12 | 0 | True |
| V3-P1-005 | AcceptancePilot | 12 | 12 | 0 | 12 | 12 | True |
| V3-P1-005 | PassingPilot | 12 | 12 | 0 | 12 | 12 | True |
| V3-P2-001 | AcceptancePilot | 12 | 12 | 0 | 12 | 12 | True |
| V3-P2-001 | PassingPilot | 12 | 12 | 0 | 12 | 0 | True |
| V3-P2-004 | AcceptancePilot | 12 | 12 | 0 | 12 | 12 | True |
| V3-P2-004 | PassingPilot | 12 | 12 | 0 | 12 | 12 | True |

HQ decision pending; calibration BLOCKED; decks / Prototype 0.2 FROZEN; Action #33 / Prototype 0.3 NOT AUTHORIZED. Privacy and filtering unchanged. This affected-fixture result does not replace the original run or establish broader Pilot competence.

Validation: 62 focused regression, replay-harness, Priority engine and V2 input-contract tests passed; targeted Ruff and git diff --check passed. Regression policy calls are separate from the 96 recorded scoring calls. Offline audit verified all 96 membership comparisons and artifact hashes. All pre-existing docs/cardcade artifacts and decks are unchanged against decb9eb2. The initial preservation check also counted the newly added execution plan and failed; the corrected check excludes additions. No scoring calls were repeated.
