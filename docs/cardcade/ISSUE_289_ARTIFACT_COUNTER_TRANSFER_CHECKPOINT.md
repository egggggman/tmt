# Issue #289 — countered artifact departure transfer

Draft checkpoint stacked on #340. Frozen Baseline 005, the original 172 ledger identities, prior overlays, historical games and runtime identities are unchanged. No calibration control was run.

## Selection and Oracle authority

The frozen two-copy Donatello, Mutant Mechanic clause is: “Whenever an artifact you control is put into a graveyard from the battlefield, if it had counters on it, put those counters on up to one target artifact or creature you control.” The other printed tap activation and artifact animation already execute and remain unchanged.

| Family | Frozen copies | Shared machinery and consequence | Decision |
| --- | ---: | --- | --- |
| Controlled countered-artifact departure | 2, Donatello | Departure provenance, counter snapshots and placement already exist; optional targeting remains | Selected: bounded trigger and targeting |
| Enrage damage-to-mana | 2, Raphael | Damage events and mana units exist; retained mana across step and phase boundaries remains | Open: broader resource duration change |
| Combat-damage artifact copy | 2, Donatello, Gadget Master | Combat event exists; copying arbitrary target artifact characteristics, counters and token identities is more involved | Open |
| Other remaining families | 2–3 per card | Combat modifier, recursion, Equipment copy and hidden-zone effects | Open; ranked in readiness JSON |

## Executed rule and validation

A complete Oracle parser recognizes a controlled artifact put into a graveyard from the battlefield with counters. It snapshots **all** counter kinds and quantities before departure, the prior controller, artifact type, source incarnation and exact departure event. A trigger is put on the stack with an optional target artifact or creature controlled by that trigger's controller. The target is chosen at stack placement, may be declined, and is rechecked for identity, control, type and protection on resolution. An illegal or departed target receives no counters; the trigger can resolve after its source leaves. Counter placement uses the normal counter pipeline and state-based actions. Exile, an opponent-controlled artifact, a nonartifact, and a zero-counter departure do not trigger. No card- or deck-name branch executes the rule.

Focused tests cover multiple counter types, self-departure, ability suppression, source departure, priority, optional choice, changing control/type, removed targets, tampered history, generic renamed sources, the exact frozen Oracle card and deterministic replay. A recoverable code commit was published before the full regression.

Six authenticated frozen-deck diagnostics, each run twice with exact result and pilot-observation digests, recorded 49 legal Donatello cast offerings, four selections and casts, and two countered-artifact departures across games. They recorded **zero** matching triggers, target choices, resolutions or counter placements. The forced frozen-card fixture proves execution, while this small natural sample does not establish trigger frequency or any deck-balance conclusion. Trigger costs are zero; ordinary spell-cast payment is unchanged.

The machine overlay `ISSUE_289_ARTIFACT_COUNTER_TRANSFER_CHECKPOINT.json` preserves 172 row identities and closes exactly one previously identified blocker. `ISSUE_289_ARTIFACT_COUNTER_TRANSFER_CALIBRATION_READINESS.json` independently ranks the remaining entries; `ISSUE_289_ARTIFACT_COUNTER_TRANSFER_SMOKE.json` preserves game results, observations and replays. Reproducers are in `tools/report_issue289_artifact_counter_transfer.py` and `tools/run_issue289_artifact_counter_transfer_smoke.py`.

## Gates

**Checkpoint acceptance:** READY only after final-head CI passes. **Baseline 005 calibration: BLOCKED.** Zero critical, eleven important entries, seven identified calibration blockers and four unbounded effects remain. Raphael's damage-to-mana and Donatello, Gadget Master's artifact-copy effects are next in the ranked evidence. No deck revision, control, merge or promotion is authorized.
