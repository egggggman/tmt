# Issue #289 — counter-conditioned block restriction

Draft checkpoint stacked on #345. The ten Baseline 005 deck files, original 172-row ledger, every prior overlay and historical simulation evidence remain unchanged. No calibration or balance batch was launched.

## Selection and frozen authority

The two-copy **Michelangelo, Mutant BFF** has the full clause: “Each creature you control with a counter on it can't be blocked by more than one creature.” Its other printed clause creates a Mutagen token when Michelangelo enters or attacks and was already executable. This checkpoint changes only the counter-conditioned restriction. The existing one-block assignment rule supplies its combat consequence; the new condition evaluates the current controlled creature and any positive counter count. There is no spell cost, trigger or target for this static clause.

| Remaining family | Frozen copies | Engine/risk assessment |
| --- | ---: | --- |
| Mutant BFF's counter-conditioned restriction | 2 | Complete bounded extension of existing block legality and live counters; **implemented**. |
| Hamato Guardian Stance's targeted +1/+3, flying and scry 1 | 2 | Compound instant, targeting and hidden top-card choice; **still unresolved**, unbounded. |
| Michelangelo, Improviser's optional creature and/or land entry from hand | 2 | Combat-damage trigger plus hidden-hand choices and distinct entry rules; **still unresolved**, unbounded. |
| Donatello, Gadget Master's targeted artifact-copy damage trigger | 2 | Copiable-values and independent token identity plus triggered target selection; two ledger entries remain blockers. |
| Improvised Arsenal's paid self-copy activation | 3 | Shares copy foundation but needs its own activation/payment and Equipment behavior; two ledger entries remain blockers. |

The artifact-copy foundation remains the highest shared blocker and can eventually support both copy cards, but its two action families and copiable-values model make it larger than the complete Mutant BFF rule. The remaining compound effects do not become harmless merely because natural samples may not select them. The readiness file preserves their unbounded status.

## Rule execution and evidence

The generic parser recognizes the whole controlled-creature-with-counter restriction on a permanent and rejects incomplete variants. Combat legality evaluates the source's current controller and ability, the attacker's current creature status and controller, and **any** current positive counter type at block declaration. Counter placement or removal, control changes, source departure or ability loss recalculate available blocks. Ability loss on the recipient does not erase an external restriction. The prior source/subtype one-block cases and menace remain independent; menace plus an active one-block maximum permits no legal blockers. An applied-limit event retains the source and attacker object identities, Oracle fragment and blocker count. No card or deck name dispatch implements this behavior.

Focused fixtures use the frozen card and a renamed generic source. They cover parser rejection, +1/+1, stun and finality counters, counter removal, zero counts, source/control changes, creature status, source suppression, recipient suppression, invalid two-block actions, block assignment, menace conjunction, Bebop and Rocksteady regression, and deterministic replay. Six authenticated frozen-deck diagnostics used Michelangelo versus Raphael, Donatello and Bebop & Rocksteady in both seats; every game matched an exact replay. The pilot observed 21 legal Mutant BFF cast offerings across decision stages, selected and cast it twice, and it entered three times (two spell resolutions and one library-to-battlefield entry). Six attack declarations logged the active block restriction. The diagnostic also logged 25 counter-placement events and 101 attack declarations across all six games. These are separate exposure measures, **not balance estimates**; offerings can repeat across decision stages.

`ISSUE_289_COUNTERED_BLOCK_LIMIT_CHECKPOINT.json` preserves all 172 ledger identities and closes exactly this row. `ISSUE_289_COUNTERED_BLOCK_LIMIT_CALIBRATION_READINESS.json` independently ranks the six remaining important entries and retains dispositions for all four originally unbounded effects. `ISSUE_289_COUNTERED_BLOCK_LIMIT_SMOKE.json` contains the game evidence and replay digests. Reproducers are `tools/report_issue289_countered_block_limit.py` and `tools/run_issue289_countered_block_limit_smoke.py`.

## Gates

**Checkpoint acceptance: READY subject to successful final-head CI.** **Baseline 005 calibration readiness: BLOCKED.** Zero critical rows remain. Six important rows remain: four artifact-copy ledger entries and two unbounded compound effects. No deck revision, 4,500-game control, merge or promotion is authorized.
