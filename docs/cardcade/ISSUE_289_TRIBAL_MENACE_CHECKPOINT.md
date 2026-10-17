# Issue #289 — controlled-subtype menace grant

Draft checkpoint stacked on #344. All ten Baseline 005 deck files, the original 172-row ledger, prior overlays and historical game evidence remain unchanged. No calibration or balance batch was launched.

## Selection and frozen authority

The two-copy Bebop, Warthog Warrior has the complete clause **“Rhinos you control have menace.”** It was one of four important effects whose calibration impact remained unbounded. A complete generic controlled-subtype continuous keyword grant can reuse the existing menace and block-declaration rules, including Rocksteady's separate restriction that it cannot be blocked by more than one creature. While the grant applies, the two requirements make Rocksteady unblockable.

The other candidates are larger or distinct rules families:

| Frozen clause | Copies | Assessment and disposition |
| --- | ---: | --- |
| Donatello, Gadget Master: combat damage to a player creates a copy of target artifact you control | 2 | Copiable-values and independent token identity plus triggered targeting; two ledger entries remain calibration blockers. |
| Improvised Arsenal: `{4}{R}` creates a copy of this Equipment | 3 | Same copy foundation, but paid activation, Equipment characteristics and attachment independence need separate completion; two ledger entries remain blockers. |
| Hamato Guardian Stance: targeted +1/+3, flying, then scry 1 | 2 | Compound spell and hidden top-card choice; **still unresolved**, impact unbounded. |
| Michelangelo, Improviser: combat damage may put a creature and/or land from hand onto the battlefield | 2 | Optional hidden-hand selections, entry events and land handling; **still unresolved**, impact unbounded. |
| Michelangelo, Mutant BFF: countered creatures you control cannot be blocked by more than one creature | 2 | Dynamic counters, control and combat restriction; **still unresolved**, impact unbounded. |
| Bebop, Warthog Warrior: Rhino-wide menace | 2 | **Implemented** with a generic layer-six grant and actual attack evidence. |

The previous numerical priority score did not determine this choice: the copy effects rank higher in impact, but require a broader foundation and two distinct execution paths. This bounded intervention closes one complete effect while preserving the copy work as explicit blockers. No remaining unbounded effect is claimed credibly bounded.

## Executed rules and evidence

The interpreter accepts the full controlled plural-creature-subtype menace clause on a permanent and rejects unsupported neighboring wording. Runtime evaluation checks the current source, controller, subtype and layer-six ability status. Recipient subtype and control changes recalculate immediately; source departure or ability suppression removes the grant. Ability loss on a recipient applies in timestamp order. The existing generic menace block rule rejects one blocker, and the existing Rocksteady rule prevents two blockers, with no named-card execution branch. The attack event records source object, recipient and Oracle fragment.

Focused fixtures verify the frozen clause and a renamed source, parser rejection, subtype and controller changes, source departure, source and recipient ability suppression, Aura removal, one/two-block legality, the frozen Rocksteady conjunction, and exact deterministic replay. Six authenticated frozen-deck games put Bebop & Rocksteady against Raphael, Donatello and Casey Jones in both starting positions; each was replayed exactly. The pilot observed 13 legal Bebop cast offerings across decision stages, selected and paid for it three times, and it entered three times. Three selected attacks logged the shared grant. An offering is a decision-stage observation, not a distinct card or game. These diagnostics prove pilot exposure and event provenance; they are not balance measurements.

`ISSUE_289_TRIBAL_MENACE_CHECKPOINT.json` preserves all 172 ledger identities and closes exactly the Bebop row. `ISSUE_289_TRIBAL_MENACE_CALIBRATION_READINESS.json` ranks the seven remaining important entries and gives all four formerly unbounded effects individual dispositions. `ISSUE_289_TRIBAL_MENACE_SMOKE.json` stores the authenticated game and replay digests. Reproducers are `tools/report_issue289_tribal_menace.py` and `tools/run_issue289_tribal_menace_smoke.py`.

## Gates

**Checkpoint acceptance: READY subject to final-head CI.** **Baseline 005 calibration readiness: BLOCKED.** Zero critical rows remain. Seven important rows remain: four artifact-copy ledger entries and three effects without a credible calibration bound. No deck revision, 4,500-game control, merge or baseline promotion is authorized.
