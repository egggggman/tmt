# Prototype 0.3 Smoke Review

Status: **Post-smoke Design Studio review**

This review is based on `main` at `74fd6c34efa5081a4ef344fa5155c52847e1742f`. It records a
bounded Design Studio decision only. It does not change a decklist, engine, runtime, or Pilot.

## 1. Authority/evidence chain

The governing chain is:

- [`PROTOTYPE_0_3_PREBALANCE_AUTHORIZATION.md`](PROTOTYPE_0_3_PREBALANCE_AUTHORIZATION.md), which authorized one bounded lever per named
  deck and required this review after the diagnostic smoke;
- [`PROTOTYPE_0_3_PREBALANCE_SMOKE_PLAN.md`](PROTOTYPE_0_3_PREBALANCE_SMOKE_PLAN.md), which fixed the six-matchup, 240-game schedule,
  seeds `3000..3039`, and 20/20 starting-player split;
- [`PROTOTYPE_0_3_PREBALANCE_SMOKE_RESULTS.md`](PROTOTYPE_0_3_PREBALANCE_SMOKE_RESULTS.md) and its authenticated [evidence JSON](PROTOTYPE_0_3_PREBALANCE_SMOKE_EVIDENCE.json), with the
  banked readiness decision `PREBALANCE_REVIEW_REQUIRED`;
- the [Donatello](DONATELLO_PROTOTYPE_0_3_CANDIDATE_PACKET.md), [Shredder](SHREDDER_PROTOTYPE_0_3_CANDIDATE_PACKET.md), [Raphael](RAPHAEL_PROTOTYPE_0_3_CANDIDATE_PACKET.md), and [Casey Jones](CASEY_JONES_PROTOTYPE_0_3_CANDIDATE_PACKET.md) Prototype 0.3 candidate packets;
- preserved Donatello [Prototype 0.1](../../decks/donatello/PROTOTYPE_0.1.md), [0.2](../../decks/donatello/PROTOTYPE_0.2.md), and [0.3](../../decks/donatello/PROTOTYPE_0.3.md) deck documents;
- [RFC 006 Design Intent](../rfcs/006-design-intent.md) and the preserved deck/play-pattern history.

The smoke report identifies repository execution SHA `d3812b924607b114744d40181e41e6e9a33c4c97`,
the harness digest `b10234588e7e5d39e20c46337ceeae7248da0fe10b750f2ea03068647753cc4d`, and evidence
JSON SHA-256 `4bf8ec492ab7de42ad033a1e7740ba44bc413b98d7297e43ab01a6415ee98d56`. Those are
preserved evidence identities, not this review's base commit.

## 2. Smoke completion summary

The fixed smoke attempted 240 games and completed 238. It recorded 0 malformed results, 0 draws,
0 turn-cap outcomes, and 2 runtime failures. The two failures were preserved without retry.

| Matchup | Completed result | Runtime failures |
| --- | ---: | ---: |
| Shredder / Raphael | Shredder 22–17 Raphael | 1 |
| Shredder / Casey Jones | Shredder 22–18 Casey Jones | 0 |
| Shredder / Donatello | Shredder 35–5 Donatello | 0 |
| Raphael / Casey Jones | Raphael 24–15 Casey Jones | 1 |
| Raphael / Donatello | Raphael 35–5 Donatello | 0 |
| Casey Jones / Donatello | Casey Jones 32–8 Donatello | 0 |

The aggregate descriptive records are Shredder 79–40 with 1 runtime error, Raphael 76–42 with 2,
Casey Jones 65–54 with 1, and Donatello 18–102 with 0. These are directional smoke observations,
not calibrated win rates and are not used as a 50% tuning target.

## 3. Shredder review

Shredder remained functional. It was much closer against Raphael and Casey than against Donatello;
the single Shredder/Raphael runtime failure prevents treating that matchup as fully complete, but
does not indicate a Shredder deck problem. Decision: **`HOLD_CURRENT_PREBALANCE_LISTS`**. No further
Shredder card change is required before the next smoke/human-play gate.

## 4. Raphael review

Raphael remained functional and was reasonably close against Casey. Its strong Donatello result is
directional evidence of Donatello's pressure problem, not a reason to tune Raphael. The
Raphael/Casey runtime failure is separated below. Decision: **`HOLD_CURRENT_PREBALANCE_LISTS`**.

## 5. Casey Jones review

Casey remained functional after the Equipment-density reduction and was close against Shredder and
Raphael in this diagnostic. The one Raphael/Casey failure is a runtime concern, not balance
evidence. Decision: **`HOLD_CURRENT_PREBALANCE_LISTS`**.

## 6. Donatello diagnosis

The P0.1 identity is a proactive artifact network: assemble small components, use them to learn or
adapt, and convert preparation into battlefield advantage. Does Machines selects and recovers
components. Donatello's Technique rewards an unblocked route by converting that route into cards;
it is therefore a setup-to-payoff and closing-conversion card, not generic card quality.

P0.2 removed two Does Machines and two Technique, adding two Negate and two Return to the Sewers.
Its own design record says this was intended to reduce repeated setup-to-payoff conversion while
retaining a technical answer package. P0.3 restored only the two Does Machines copies, leaving
three Does Machines, zero Technique, and four Return to the Sewers.

The smoke now shows a coherent directional diagnosis: restoring setup/recovery access alone did
not recover Donatello. It completed every game but lost 5–35 in each matchup. The most supported
working hypothesis is that Donatello can assemble the network more reliably again but lacks enough
setup-to-payoff and closing conversion to capitalize on it. This remains a mixed deck/Pilot/
semantic hypothesis, not a claim that the simulator established a true win rate.

## 7. Donatello recovery hypothesis

Four Return to the Sewers copies create a relatively reactive answer/recovery-heavy package. The
candidate packet records that these cards require an opposing target and timing window, while the
Pilot's choices are deterministic and not equivalent to human adaptive sequencing. Against the
P0.3 result, that density is a plausible opportunity cost: the deck has setup and recovery, but
not enough proactive conversion when the opponent does not supply the ideal answer window.

The narrow hypothesis is therefore to restore two Technique copies by removing two Return to the
Sewers. This tests whether proactive conversion, not more setup or generic power, is the missing
link. It does not assert that all four Return copies are bad in human play.

## 8. Candidate change analysis

Decision: **`AUTHORIZE_DONATELLO_RECOVERY_REVISION`**.

The authorized follow-up shape is exactly:

```text
Prototype 0.3a
-2 Return to the Sewers
+2 Donatello's Technique
```

This is authorization to create a separate, preserved candidate and PR only. It does not authorize
editing or overwriting P0.3, merging a decklist, changing lands or creatures, changing Does
Machines, or changing any other deck. It is one coherent two-out/two-in lever that restores the
original P0.1 setup/payoff/recovery balance in a limited way.

The simulator represents Technique sufficiently for a diagnostic rerun at the effect level: the
historical accepted runtime evidence contains Technique resolving into the hand, and the preserved
P0.1/P0.2 design records define its unblocked-route card-conversion role. It does not represent
human-quality route, timing, or closing judgment sufficiently to make the rerun a calibration or a
substitute for human play.

Safer alternatives were considered: hold P0.3 for human evidence, restore Does Machines again, or
replace a different reactive card. Holding is safest against simulator overreach, but the complete
Donatello smoke failure across all three named pressure/Equipment matchups supplies enough bounded
evidence to authorize this diagnostic candidate. Restoring Does Machines again would repeat the
lever just tested; a different replacement would require more assumptions about early stabilization
and generic power. The Technique swap is the smallest identity-preserving test.

## 9. Identity/tradeoff analysis

The change preserves Donatello's inventive, technical, artifact-network identity: it makes a
successful prepared attack produce options and a path to close. It does not add generic threats,
alter the artifact package, turn the deck into passive draw-go control, or rebuild the mana base.

Tradeoffs are explicit. Removing two Return copies reduces reactive answers and Mutagen-producing
recovery, which may worsen pressure resilience. Restoring Technique may recreate automatic value or
repeated conversion under the Pilot. The follow-up must therefore inspect whether Technique creates
meaningful choices, whether Donatello stabilizes and closes, and whether the deck remains inventive
rather than merely generating cards. Human play remains the decisive next design gate.

## 10. Runtime-failure separation

Both failures were preserved without retry and are not Donatello evidence:

| Matchup | Seed | Error | Evidence context |
| --- | ---: | --- | --- |
| Shredder / Raphael | 3007 | `max() iterable argument is empty` | Runtime evidence has no turn, phase, traceback, or action snapshot. |
| Raphael / Casey Jones | 3001 | `max() iterable argument is empty` | Runtime evidence has no turn, phase, traceback, or action snapshot. |

The smallest useful handoff is **`RUNTIME_TRIAGE_REQUIRED`**: investigate these two exact seeds
against the preserved harness/runtime identity before the next smoke rerun, with traceback and
last game event/turn/action context captured. The source path common to both smoke executions is
the combat-selection pipeline in `smoke01.py`: AcceptancePilot `choose_attack` and
`choose_blocks` are called at lines 288–296. Both methods call `max(options, ...)` in
`pilot07.py` lines 114–120. The engine also has a separate automatic-blocking `max()` path, but
the smoke driver calls the Pilot block chooser directly.

The banked JSON cannot identify which of the two chooser calls first received an empty tuple, and
it records `turn: null`; therefore this review does not claim a narrower call site or phase than
the shared combat-selection/Pilot-choice surface. The failures are not currently identified as
empty card targeting, a Donatello interaction, or balance behavior. Cardcade should determine
whether an empty legal attack/block action set is being exposed, whether combat state/step
transition is stale, or whether another upstream choice illegally leaves the combat surface empty.
No runtime, engine, or Pilot fix is included here.

## 11. Next gates

If this review merges, the order is:

1. Create Donatello P0.3a in a separate PR with only the authorized swap and preserved P0.3.
2. Diagnose and fix the two runtime failures in a separate Cardcade PR.
3. Validate the two changes independently.
4. Rerun the same frozen six-matchup smoke without changing Shredder, Raphael, or Casey.
5. If the environment is reasonably functional, move to balanced human play rather than continuing
   simulator optimization.

Human play should record whether the artifact network becomes functional, whether Technique creates
meaningful conversion, whether four-to-two Return density was a real problem, and whether Donatello
can stabilize and close against pressure. Smoke results must not be treated as calibrated rates.

## 12. Explicit decisions

- Shredder: **`HOLD_CURRENT_PREBALANCE_LISTS`**
- Raphael: **`HOLD_CURRENT_PREBALANCE_LISTS`**
- Casey Jones: **`HOLD_CURRENT_PREBALANCE_LISTS`**
- Donatello: **`AUTHORIZE_DONATELLO_RECOVERY_REVISION`**
- Authorized candidate: create preserved **`PROTOTYPE_0.3a`** with `-2 Return to the Sewers / +2
  Donatello's Technique`; do not overwrite P0.3.
- Runtime: **`RUNTIME_TRIAGE_REQUIRED`**
- Scope: this review changes documentation only; no deck, engine, runtime, or Pilot code is changed.
