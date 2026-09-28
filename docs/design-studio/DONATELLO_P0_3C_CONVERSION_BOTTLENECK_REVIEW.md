# Donatello Prototype 0.3c Conversion Bottleneck Review

Status: post-smoke Design Studio review. This document records analysis only; it
does not authorize a deck edit, runtime edit, Pilot edit, or another smoke run.

## 1. Evidence chain

The review is based on the authenticated P0.3c frozen smoke and its preserved
event logs:

- Repository at smoke execution: `ecf05b0aaba9ab944c38e3da6186e4183dfa8c9a`.
- Results: [`PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3C_RESULTS.md`](PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3C_RESULTS.md).
- Raw evidence: [`PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3C_EVIDENCE.json.gz`](PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3C_EVIDENCE.json.gz).
- P0.3c input: `b0d8a0dc42b267ac1a162096fe6e0336176f92db9a79a95f1c7dbd0d5c2d2cc6`.
- Prior design diagnosis: [`DONATELLO_P0_3B_FAILURE_REVIEW.md`](DONATELLO_P0_3B_FAILURE_REVIEW.md).

The run completed all 240 scheduled games with zero runtime errors, malformed
games, draws, or turn caps. Counts below are preserved-event-log counts. Where
the logs do not retain an exact legal-action snapshot, the review labels the
result as estimated rather than presenting it as an exact opportunity count.

## 2. P0.3c improvement summary

| Version | Donatello result | Descriptive percentage |
| --- | ---: | ---: |
| P0.3a | 18–102 | 15.0% |
| P0.3b | 15–105 | 12.5% |
| P0.3c | 26–94 | 21.7% |

P0.3c improved by eight wins over P0.3a and eleven over P0.3b. Its matchup
results were 10–30 versus Shredder, 5–35 versus Raphael, and 11–29 versus
Casey Jones. This is meaningful directional improvement, not calibrated
balance evidence.

The package was functional: Mouser Mark III produced 83 cast/resolution
records, 67 blocks, and 152 direct combat damage; Way with Machines produced
42 artifact-entry triggers/counters and 205 direct combat damage. The result
therefore does not support treating Mouser's card text or artifact identity as
the sole problem. The remaining bottleneck is conversion timing and access to
interaction.

## 3. Mouser draw/cast opportunity funnel

The event logs record 117 Mouser draw records across 88 games in which Mouser
entered from the library. The draw timing in those games was:

| First library entry | Games |
| --- | ---: |
| Opening hand | 32 |
| Turns 1–3 | 5 |
| Turns 4–5 | 15 |
| Later | 36 |

There were also 18 games with Mouser returned from a graveyard to hand. The
combined evidence shows Mouser entering hand in 93 games and being cast in 66
games. The smoke telemetry records 83 total casts/resolutions, including
recovered-card casts.

For the 64 library-drawn games with a Mouser cast, the estimated first legal
mana opportunity was derived from the first relevant hand entry and the second
Donatello land event. This is a diagnostic proxy, not a replacement for a
turn-by-turn legal-action trace:

| Funnel measure | Result |
| --- | ---: |
| Library-drawn games | 88 |
| Games with Mouser cast after library entry | 64 |
| Estimated games with a legal opportunity that was not immediately used | 23 |
| Average estimated opportunity-to-cast delay | 4.19 turns |
| Median estimated opportunity-to-cast delay | 4 turns |
| All-cast average reported by smoke telemetry | 11.82 turns |
| Cast by turn 2 / 3 / 4 / 5 | 0 / 4 / 8 / 9 |

In all 23 estimated declined-opportunity cases, another Donatello spell was
cast later; in 41 delayed cases an alternative same-turn play was visible.
These observations identify a real timing bottleneck, while preserving the
distinction between an estimated opportunity and an exact legal-action record.

## 4. Mouser timing diagnosis

The problem has two substantial components:

- **`DRAW_TIMING`: material.** Only five of the 88 library-drawn games first
  received Mouser on turns 1–3; 36 first received it later. A two-mana body
  cannot stabilize a turn that it has not reached the hand in.
- **`MANA_CONSTRAINT`: not primary.** The drawn-game casts generally had the
  estimated two-land opportunity before the eventual cast. Hybrid blue payment
  and the card's 2/3 artifact representation are covered by focused tests.
- **`PILOT_PRIORITY`: primary execution bottleneck.** The current main-action
  policy considers draw/setup effects before the creature stage, and creature
  choices compete with other legal creatures. The 23 estimated missed
  opportunities and the visible alternative plays show that available mana is
  often spent on value or setup instead of the early body.
- **`ENGINE_LEGALITY`: not primary.** Mouser casts and resolves, and the smoke
  records 83 successful cast/resolution pairs. No evidence indicates that the
  attack restriction or hybrid payment stranded the card.

Mouser is therefore late because of both draw timing and deterministic priority
selection, not because the card is unusable. When present, it blocks and deals
damage. Its 54 observed deaths also show that it is not an invulnerable closer;
it is doing the intended early-body job often enough to validate the direction,
but not often enough or early enough to erase Donatello's broader deficit.

## 5. Ooze Spill opportunity funnel

Ooze Spill was recorded 150 times in draw events and zero times as a cast or
resolution. The authoritative card text is an instant with cost `{1}{U}{U}`:
“Counter target spell. Create a Mutagen token.” The direct synthetic
counterspell/Mutagen tests pass, so this is not evidence that the card's core
resolution semantics are absent.

The preserved game logs provide the following response-window audit:

| Measure | Result |
| --- | ---: |
| Opponent-spell events while Ooze was in hand | 49 |
| Those events with estimated three-land availability | 25 |
| Donatello priority windows after an opponent spell | 37 |
| Ooze cast/resolution records | 0 / 0 |
| Hand-instant Ooze legal actions exposed by the runtime | 0 observed |

The count of 25 is again an estimated mana filter; the evidence does not retain
all tapped/untapped details. It is nevertheless enough to show that “no one
ever cast an opposing spell while Ooze was held” is false.

## 6. Ooze zero-cast diagnosis

The zero-cast result is best classified as **`PRIORITY_MODEL_LIMITATION`**, not
as a deck-slot verdict. Cardcade's ordinary priority action surface exposes
passes and supported activated-ability choices; it does not expose a hand-held
instant counterspell as a selectable response to an opponent's spell. The
AcceptancePilot can choose a counter activation when one is supplied, but it
has no hand-instant response decision to make here.

Thus the normal games contain opponent-spell and priority events, but no legal
Ooze action is generated. The 150 draws demonstrate availability; they do not
demonstrate 150 missed legal counterspell decisions. Calling Ooze weak on that
basis would conflate an unevaluable deck slot with a runtime access problem.

## 7. Deck-level remaining weaknesses

Even with perfect access to currently represented cards, Donatello remains
structurally behind. The P0.3c package improves early bodies, but the engine
still asks the deck to spend mana and turns on Does Machines levels, recovery,
and value before it has a reliable protected closing board. Way with Machines
attacked in only 35 recorded combat assignments despite 66 casts/resolutions;
its counters and 205 damage are meaningful, but not a consistent conversion
engine by themselves.

The deck also remains thin on early bodies beyond Mouser and lacks a clearly
reliable answer when an opposing threat is already established. This is most
visible against Raphael at 5–35, while Shredder at 10–30 and Casey at 11–29
show that the issue is shared rather than a single matchup quirk. The deck
problem is therefore delayed stabilization and closing quality, not merely
missing card advantage.

## 8. Pilot/runtime limitations

Two limitations are separable:

1. AcceptancePilot's main-action ordering can select draw/setup value before a
   legal Mouser body. A narrowly scoped creature-priority diagnostic or policy
   change could test that hypothesis; a general AI rewrite is not justified.
2. The response model does not currently offer hand-held instant counterspells
   as responses to opponent spells. Ooze's direct semantics work when invoked
   through the supported synthetic path, but normal games cannot reach that
   choice.

These limitations explain why the smoke is not a clean test of Ooze's deck
value and why Mouser's card-level contribution is under-realized. They do not
erase the deck-level evidence that Donatello still closes poorly after setup.

## 9. Ownership classification

**`MIXED_DECK_AND_PILOT`**

The P0.3c result is partly a deck-power problem: even functioning Mouser and
Way activity do not reliably turn setup into a winning battlefield. It is also
partly a Pilot/runtime problem: Mouser is often deferred despite an estimated
early opportunity, and Ooze cannot be selected in the normal response model.
No single ownership category describes all observed losses without discarding
one of these concrete findings.

## 10. Mouser conclusion

**`MOUSER_DECK_DIRECTION_VALIDATED`**

Mouser is a functional 2/3 artifact body that blocks, attacks when enabled,
feeds artifact entry, and contributed materially to P0.3c's improvement from
18–102 and 15–105 to 26–94. Its late deployment is an execution-density and
priority problem, not evidence that the card direction is insufficient. This
does not authorize another deck revision.

## 11. Ooze conclusion

**`OOZE_RUNTIME_RESPONSE_SUPPORT_REQUIRED`**

Ooze should not be replaced solely because it recorded zero casts. The card was
drawn, opponent spells occurred while it was held, and the card's counterspell
and Mutagen resolution path is covered in direct tests. The missing evidence is
a normal-game legal response opportunity and a bounded Pilot choice.

## 12. Next-gate decision

**`AUTHORIZE_NARROW_RESPONSE_SEMANTIC_FIX`**

The next gate is one bounded Cardcade capability change: expose a castable
hand-held instant counterspell as a legal response during an opponent's stack
priority window, subject to the card's mana and target legality, and let the
existing deterministic Pilot choose it under the existing response convention.
This is not authorization for a general priority or AI redesign, and no such
change is made in this review.

After that narrow capability is validated, human play should be considered
seriously: the project goal is “Playable first. Explainable increasingly.” If
the response surface is made evaluable and P0.3c remains weak, human evidence
is more valuable than continuing to chase a simulator percentage. No P0.3d is
authorized by this document.
