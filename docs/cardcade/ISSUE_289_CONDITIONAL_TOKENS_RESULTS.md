# Issue #289 — conditional Sneak token checkpoint

Stack: draft PR #316 (`e7ddf47d53d6dec9f6d177f58e9ab0498280b65d`) → this checkpoint. No deck list, baseline, calibration control, or historical simulation evidence changes.

## Selection

| Family | Frozen copies / ledger rows | Impact | Existing support and risk |
| --- | ---: | --- | --- |
| The Last Ronin's Technique conditional tokens | 1 / 2 identical critical rows | Three bodies and a possible three unblocked combat damage after Sneak | Fixed Sneak payment, batched token entry, and combat already exist; bounded conditional entry is the smallest complete intervention. Both original row identities are retained. |
| Michelangelo's Technique top-eight choice | 2 / 1 critical row | Board development and deck identity | Requires coupled private selection of up to two creatures under a total mana-value limit, simultaneous entry, and randomized library bottom. |
| Raphael, Most Attitude linked permissions | 2 / 2 partial critical rows | Repeatable resource access and identity | Requires broader legal casting families from linked exile with timing, costs, and source-independent duration. |

The selected generic spell parser requires the complete printed two-fragment Sneak/token form. The engine offers normal casting at main-phase or instant priority, or fixed Sneak after blockers with an unblocked attacker returned as a cost. Its batch token creation enters untapped outside Sneak and tapped and attacking the defending player after Sneak. The three objects join the current combat without declaring attacks or acquiring blocks. Entry events, mana payment, stack resolution, state-based actions, zone identities, and attack damage are recorded deterministically. A malformed or incomplete spell remains unsupported.

A four-game frozen Baseline 005 diagnostic uses authenticated deck files, two seeds and both seat assignments. Each game matches an exact replay; seed 319 has one ordinary payment/resolution and seed 320 has one Sneak payment/resolution (both Leonardo first against April). The other two games have no token cast. This is execution evidence, not balance evidence. See [machine diagnostic](ISSUE_289_CONDITIONAL_TOKENS_SMOKE.json).

The diagnostic also reproduced a pre-existing Equipment/ability-loss invariant error in April-first vs Leonardo, seed 320, on the unchanged PR #316 runtime, before any conditional token spell resolved. An attached Equipment's granted combat trigger was considered after a later ability-loss effect; event provenance then rejected that trigger. The generic enqueue guard now observes the same timestamp restriction as the trigger validator. A focused test exercises the suppressed and unsuppressed branches. The four diagnostics complete after the correction.

## Preservation and readiness

The [172-row overlay](ISSUE_289_CONDITIONAL_TOKENS_CHECKPOINT.json) is regenerated from the immutable prior checkpoint and the [original ledger](ISSUE_289_COVERAGE_LEDGER.csv) after verifying their SHA-256 values. The duplicate Last Ronin rows close together: **5 → 3 critical**, of which **2 remain partial Raphael rows**. **61 important** rows remain. Michelangelo's top-eight selection remains a complete critical gap. The historical Baseline 005 manifest SHA-256 remains `c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac`.

Before runtime: `2e4135b43d16e587175a96608bf54c723c2d772cf67fe8bd4f4c695393388598`.
After runtime: `61d1822d4ebe01aae002305f12b48375c3a943df4871fe1ab6a3c6f199a0c458`.

Checkpoint acceptance: **pending final-head tests and CI**. Baseline 005 calibration readiness: **BLOCKED** by three critical entries and important limitations. No 4,500-game control or balance conclusion is authorized.
