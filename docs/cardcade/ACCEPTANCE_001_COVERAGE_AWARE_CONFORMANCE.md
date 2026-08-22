# Acceptance Match #001 — Retrospective Coverage-Aware Conformance

Evidence baseline: `98becb91aea5f393a5b5d298a0a4d0f171330b5a`  
Seeds: 7001–7005, two runs each  
Model: `COVERAGE_AWARE_CONFORMANCE_SPEC.md` v0.1  
Status: retrospective evidence; no engine instrumentation or behavior change

## Method and limitation

Fresh duplicate replays were byte-identical and reproduced **18 unsupported events / 6 exact
pairs**, zero Food transactions, **44 Priority grants / 44 passes**, one block rejection, and zero
invariant violations.

Existing `unsupported_semantics` events are emitted when a card's unresolved text is registered on
resolution. They prove PRESENT, but do not by themselves prove that a later trigger, permission,
choice, or combat restriction became actionable. This retrospective therefore promotes an
occurrence to REACHED / UNSUPPORTED only when another authoritative event proves the enabling
condition. Where the snapshot lacks enough option/state history, it conservatively retains
PRESENT / UNREACHED with `reach_not_proven`.

## Per-seed summary

| Seed | Result | Reconstructive executed evidence | Unsupported occurrences | Reached / unsupported | Present / unreached |
| ---: | --- | --- | ---: | --- | --- |
| 7001 | Raphael T14 | 9 casts; 8 creatures; 3 Deal Damage; 2 Scry; 1 hand-bottom/Draw; 2 discard/Draw; 9 triggers; 16 combat-damage steps | 4 | Raphael attack permission (attack declared) | Wingnut modal Alliance; Raphael Menace; Raphael Alliance exile |
| 7002 | Raphael T18 | 13 casts; 12 creatures; 1 Deal Damage; 1 hand-bottom/Draw; 5 discard/Draw; 2 activations; 1 Return; 11 triggers; 24 combat-damage steps | 1 | Wingnut Alliance condition subsequently reached by another controlled creature entry | none among residual pairs |
| 7003 | Leonardo T19 | 16 casts; 15 creatures; 5 Deal Damage; 4 Scry; 1 hand-bottom/Draw; 1 activation; 1 Sneak; 11 triggers; 23 combat-damage steps | 3 | Casey ETB selection sequence | Wingnut modal Alliance; Sewer Samurai graveyard/finality permission (`reach_not_proven`) |
| 7004 | Leonardo T43 | 28 casts; 26 creatures; 3 Deal Damage; 4 Scry; 2 hand-bottom/Draw; 3 activations; 2 Returns; 1 Sneak; 1 Lifelink; 12 triggers; 56 combat-damage steps | 7 | Casey ETB; Wingnut Alliance condition for at least one occurrence | remaining Wingnut occurrence; four Sewer Samurai occurrences (`reach_not_proven`) |
| 7005 | Raphael T16 | 14 casts; 13 creatures; 5 Deal Damage; 5 Scry; 1 hand-bottom/Draw; 5 activations/Returns; 1 Sneak; 11 triggers; 16 combat-damage steps | 3 | Raphael Alliance exile condition (later controlled creature entry); Raphael attack permission | Raphael Menace |

Counts above describe evidence records, not unique Oracle semantics. Combat-damage-step counts are
authoritative step-resolution events; ordinary combat damage is not recounted as Deal Damage Action
transactions.

## Aggregate EXECUTED evidence

Across the five first-run artifacts, the represented engine executed and recorded:

- **80 spell casts**, including **74 creature resolutions**;
- **68 land plays**;
- **17 Deal Damage transactions**;
- **15 Scry transactions**;
- **6 optional hand-bottom / conditional Draw transactions**;
- **7 optional discard / conditional Draw transactions**;
- **11 activated-ability transactions**, including **8 Targeted Returns**;
- **3 Sneak casting transactions**;
- **1 Lifelink result** and the previously accepted genuine Trample split;
- **54 trigger-stack resolutions**;
- **135 represented combat-damage-step resolutions**;
- **44 Priority grants / 44 passes**.

These claims are supported by typed events and/or reconstructive Action evidence. Canonical Food is
statically supported but had **zero EXECUTED occurrences** in Acceptance #001.

## Residual exact-pair classification

| Exact pair | Presence events | Seeds present | Retrospective conformance | Evidence and boundary |
| --- | ---: | --- | --- | --- |
| Wingnut — Alliance choice of flying/menace/haste | 5 | 7001, 7002, 7003, 7004 | **Mixed: REACHED / UNSUPPORTED and PRESENT / UNREACHED** | Controlled creature-entry evidence proves at least the seed-7002 and one seed-7004 Alliance opportunities. Other occurrences lack a durable source-lifetime/opportunity join in the current snapshot. No keyword mode executed. |
| Leonardo, Sewer Samurai — graveyard casting/finality | 5 | 7003, 7004 | **PRESENT / UNREACHED (`reach_not_proven`)** | The card resolved, but current evidence does not preserve per-main-phase eligible graveyard candidates, generated alternate-zone options, or their absence. No graveyard cast/finality transaction executed. |
| Casey Jones — ETB top-four artifact filter | 2 | 7003, 7004 | **REACHED / UNSUPPORTED** | Casey's authoritative creature-entry event necessarily reached its ETB condition. No look/filter/reveal/movement transaction followed. |
| Raphael, Most Attitude — Menace | 2 | 7001, 7005 | **PRESENT / UNREACHED** | Raphael attacked and dealt player damage unblocked. No block was assigned to Raphael, so the records do not show Menace changing a declaration. The engine must not claim Menace execution. |
| Raphael, Most Attitude — Alliance exile-top | 2 | 7001, 7005 | **Mixed** | Seed 7005 has a later controlled creature entry and therefore a reached Alliance condition; seed 7001 has no proven later qualifying entry before game end. No exile transaction executed. |
| Raphael, Most Attitude — attack-time play-exiled permission | 2 | 7001, 7005 | **REACHED / UNSUPPORTED parent; child unavailable** | Raphael attacked, proving the trigger condition. Because no card was exiled with Raphael, the linked play choice had no represented candidate. Neither trigger permission nor play-from-exile executed. |

The 18 presence events therefore cannot responsibly be restated as 18 reached failures. The current
artifacts prove at least **six reached unsupported occurrences**: two Casey ETBs, one Wingnut
Alliance opportunity, one Raphael Alliance-exile opportunity, and Raphael's attack-permission
context in each of seeds 7001 and 7005 (six if those two attacks are counted separately). The exact
Wingnut seed-7004 multiplicity cannot be reconstructed without stronger source-lifetime joins, so
the report deliberately avoids a false precise reached total.

## What was merely present elsewhere

The frozen libraries contain many Oracle fragments that never acquire a runtime involvement witness
in these games. They are outside this runtime report even though static corpus coverage knows them.
Cards drawn or resolved contribute PRESENT semantics only for their exact authoritative fragments;
text remaining solely in an unobserved library position must not inflate match conformance.

The current final snapshots do not preserve a complete per-turn semantic inventory for every Hand,
library, and graveyard object. Consequently this retrospective reports the six known involved
unsupported pairs and reconstructive executed families, not a fabricated exhaustive count of all
PRESENT fragments. The v0.1 specification requires future canonical output to record that inventory
at the moment an object becomes involved.

## Determinism and trust result

- Duplicate output: byte-identical for every seed
- Unsupported telemetry: **18 events / 6 exact pairs**
- Invariant violations: **0**
- Foundational blockers among residual pairs: **0**
- Acceptance #001 status: **credible for represented-scope engine conformance**
- Full-Magic or balance claim: **not authorized**

## Next-stage decision input

The retrospective supports pausing Action development. The next validation checkpoint should test
the conformance evidence model itself: exact semantic keys, opportunity witnesses, compound-fragment
joins, and deterministic aggregation. It should be reviewed before deciding among broader
acceptance matches, a larger frozen-deck sample, another engine feature, or calibration.

Action #13, Prototype 0.3, calibration, smoke testing, and Pilot tuning remain outside this evidence
pass.
