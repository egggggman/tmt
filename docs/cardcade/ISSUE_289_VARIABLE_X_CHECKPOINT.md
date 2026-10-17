# Issue #289 — variable-X spell and entry-token checkpoint

Stacked on draft PR #338. Baseline 005's ten source deck files, the original 172-row ledger, all earlier overlays, and historical game results remain unchanged. This checkpoint is a simulator change, not a deck experiment.

## Selection and exact frozen clause

Mutagen Man, Living Ooze is a two-copy Bebop & Rocksteady card with `{X}{G}{G}` and “When Mutagen Man enters, create X Mutagen tokens.” The parenthetical defines the artifacts' counter-placing sorcery-speed activated ability. The separate artifact-token activation discount remains open. The frozen catalog and manifest hashes are authenticated by `tools/report_issue289_variable_x.py`.

| Mechanic | Frozen copies | Impact and current support | Decision |
| --- | ---: | --- | --- |
| Variable-X cast and X-dependent Mutagen entry | 2, B&R | Previously uncastable; shared payment, trigger, and token machinery already exists | Selected as one complete intervention |
| Artifact-token activation discount | 2, B&R | Separate cost-reduction rule with its own payment legality | Open |
| Donatello counter transfer | 2, Donatello | Departure counter snapshot and target selection | Open |
| Raphael damage-to-mana trigger | 2, Raphael | Damage event and retained mana across steps | Open |

## Rules and evidence

The engine announces each affordable nonnegative X as a distinct legal action, pays the complete colored and generic cost transactionally, carries X through the stack incarnation to the entered permanent, and places the entry trigger on the stack. The trigger checks its original entry event and source incarnation even if the permanent leaves. Its resolution creates exactly X Mutagen artifacts with the printed characteristics; X=0 creates none, including entry without casting. Countered spells never enter and never trigger. A normal pilot chooses the largest affordable X after it has selected the creature. The legal-action option schema remains unchanged for sealed pilot fixtures.

Focused tests cover X=0/1/3, insufficient mana and malformed announcements, countering, source departure, priority, token identity, state-based invariants, and identical replay. The frozen diagnostic includes three opponents in both seats, six games and six matching replays, with legal opportunities, pilot choices, payments, resolutions, and token batches in `ISSUE_289_VARIABLE_X_SMOKE.json`. This short diagnostic measures mechanical execution and pilot exposure only.

The machine overlay `ISSUE_289_VARIABLE_X_CHECKPOINT.json` preserves 172 identities and closes exactly one entry. Runtime identity and the independent ranked residual assessment are in `ISSUE_289_VARIABLE_X_CALIBRATION_READINESS.json`.

## Gates

Checkpoint acceptance: **READY** after full regression, structural checks, replay verification, and successful final-head CI. Baseline 005 calibration: **BLOCKED**. Thirteen important entries remain; nine are identified calibration blockers and four have unbounded impact. The next high-priority bounded families are Donatello's counter transfer, Mutagen Man's separate artifact-token activation discount, and Raphael's damage-to-mana trigger. No 4,500-game control is authorized.
