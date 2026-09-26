# Donatello Prototype 0.3a Representation Audit

This audit asks whether the P0.3a change and Donatello's central artifact plan
are represented, chosen, and resolved meaningfully by Cardcade. It is not a
deck-change authorization and does not replay the 240-game smoke.

## 1. Evidence chain

- Expected synchronized main: `0d0830ad22d21a1b2fb24c2806baecc818a8b4d0`
- Donatello P0.3a: `decks/donatello/PROTOTYPE_0.3a.txt`
- P0.3a rerun evidence: `docs/design-studio/PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3A_EVIDENCE.json`
- P0.3a rerun review: `docs/design-studio/PROTOTYPE_0_3_PREBALANCE_SMOKE_RERUN_P0_3A_REVIEW.md`
- P0.3 smoke evidence and review: `docs/design-studio/PROTOTYPE_0_3_PREBALANCE_SMOKE_EVIDENCE.json` and
  `docs/design-studio/PROTOTYPE_0_3_SMOKE_REVIEW.md`
- Design Intent/history: `decks/donatello/PROTOTYPE_0.1.md`, `decks/donatello/PROTOTYPE_0.2.md`,
  `decks/donatello/PROTOTYPE_0.3a.md`, and `docs/design-studio/DONATELLO_PROTOTYPE_0_3_CANDIDATE_PACKET.md`
- Relevant implementation surfaces: `src/tmnt_design_studio/card_interpreter07.py`,
  `src/tmnt_design_studio/engine07.py`, `src/tmnt_design_studio/pilot07.py`, and
  `src/tmnt_design_studio/stage002.py`

The corrected rerun was clean but identical at the aggregate level: Donatello
was 18–102, including 5–35 versus Shredder, 5–35 versus Raphael, and 8–32
versus Casey Jones. The rerun evidence does not preserve full action histories,
so the focused deterministic comparison below used existing `run_smoke_game`
and snapshot/event surfaces for the 40 Shredder/Donatello seeds 3000–3039 in
both P0.3 and P0.3a. No 240-game smoke was run for this audit.

## 2. Exact P0.3/P0.3a comparison

The only deck difference was `-2 Return to the Sewers / +2 Donatello's
Technique`. In the same 40 Shredder/Donatello seeds:

| Diagnostic | P0.3 | P0.3a |
| --- | ---: | ---: |
| Donatello's Technique card draws | 0 | 22 occurrences in 18 games |
| Donatello's Technique casts | 0 | 0 |
| Donatello's Technique resolutions | 0 | 0 |
| Return to the Sewers draw occurrences | 49 | 27 |
| Opening-hand/draw history changed | — | 18 / 40 games versus P0.3 |
| Event history changed | — | 40 / 40 games versus P0.3 |
| Deck-normalized winner changed | — | 0 / 40 games |
| Turn count changed | — | 0 / 40 games |

The composition changed the library and opening/draw paths, but it did not
create a Technique cast or resolution. Event histories diverged because the
changed draws alter available cards and subsequent actions; the deck-level
winner stayed the same because the added card never became an executable
conversion and the surrounding plan remained weak. The raw winner labels use
different versioned deck IDs, so those IDs are not outcome changes.

## 3. Per-card semantic inventory

The manifest is the authoritative representation check. “Pilot” below means
AcceptancePilot's current deterministic policy, not a recommendation for a new
strategy.

| Card | Interpreted rules/actions | Unsupported or approximated text | Pilot cast/choice behavior | Targets, payoff, and closing effect |
| --- | --- | --- | --- | --- |
| Does Machines | Recognized Class; card is loaded and level activations are recognized as a bounded activation surface. | Class ETB mill/draw/discard, level-2 artifact recovery, level-3 counter/Robot conversion, and level transitions are unsupported. | AcceptancePilot takes the first available activation, but no executable Does Machines level path is exposed by the current interpreter. It does not select this generic noncreature spell in main action. | No meaningful selection, recovery, or artifact payoff reaches the board; this central setup-to-payoff engine is effectively inert. |
| Donatello's Technique | Recognized Sorcery; the card text and Sneak keyword are catalogued. | Noncreature Sneak is explicitly unsupported; `Draw two cards` is unclassified/unsupported. | No legal Technique Sneak CAST option is generated. AcceptancePilot also does not choose generic main-phase spells. | No target or card draw is executed; no combat conversion or closing effect is possible. |
| Return to the Sewers | Recognized Instant; target-creature return-to-library payload is represented on the targeted-return surface. | Mutagen token's activated ability and the full token-follow-up are unsupported; manifest marks the overall parent/follow-up as incomplete. | It can be legal when a valid creature target exists, but AcceptancePilot's main-action policy does not select generic Return casts. Target quality and top/bottom choice are not human-adaptive. | The answer can remove a creature if actually cast; the Mutagen counter payoff is not meaningfully resolved by this model. |
| Sewer-veillance Cam | Recognized one-mana Artifact. | Flash; enter/leave tap-or-untap choice; sacrifice-to-draw ability are unsupported. | Not selected by AcceptancePilot's generic noncreature main-action policy; no supported activation choice is surfaced. | Artifact presence alone can feed represented predicates, but the Cam's own interaction and two-card conversion do not execute. |
| Bespoke Bō | Recognized Equipment. | ETB nonland return, +2/+1/vigilance attachment effect, and Equip target/timing are unsupported. | Not selected by generic spell policy and no meaningful Equip choice is exposed. | No bounce, attachment, combat enhancement, or closing conversion is available. |
| Donatello, Way with Machines | Creature body is cast by the creature stage. | Flying and “artifact enters, put a counter on Donatello” are unsupported. | AcceptancePilot can cast it as a creature at the creature stage, using lowest-cost creature selection. | The body enters, but the central artifact-entry growth trigger and evasive closing identity are absent. |
| Donatello, Gadget Master | Creature cast and fixed-cost Sneak are fully supported. | Combat-damage artifact-copy trigger is unsupported (`token_copy_not_implemented`, `token_trigger_context_not_implemented`). | AcceptancePilot chooses the first legal Sneak CAST after blockers, otherwise passes. | Sneak can produce a tapped attacking body, but the adaptive copy payoff never resolves, removing the principal technical conversion. |
| Donatello, Turtle Techie | Creature ETB draw-if-artifact is fully supported. | No material limitation was reported for this fragment. | AcceptancePilot can cast the creature; the ETB draw resolves when an artifact is controlled. | This is a real card-advantage payoff, but it is a single supported island in a much broader unsupported engine. |
| Donatello, Mutant Mechanic | Creature body is cast. | Artifact-counter activation, target selection, sorcery timing, Robot conversion, and counter-transfer death trigger are unsupported. | Creature can be cast; its activation is not a meaningful available choice. | The intended preservation/recursion payoff is absent, so it cannot carry closing conversion. |
| Fugitive Droid | Body and activated counterspell ability are supported as bounded actions. | Artifact-triggered unblockability is unsupported. | Creature can be cast; AcceptancePilot can take the first available activation, subject to a legal opposing spell target. | It can protect a represented artifact/creature in a narrow window, but its pressure/evasion identity is incomplete. |
| Buzz Bots | Creature body and dies-draw trigger are supported; Flying/vigilance facts are represented. | No material limitation for the dies-draw path. | Creature can be cast and its death draw can resolve when it dies. | This is a meaningful setup/departure card, but it does not itself produce the missing Technique or artifact growth conversion. |
| Crustacean Commando | Creature body and Mutagen token creation are represented. | Mutagen's activated counter ability is unsupported. | Creature can be cast; token creation may occur, but the token's important follow-up is not executable. | Board presence is real; its support-counter payoff is incomplete. |

Overall, artifact bodies and a few departure/ETB effects exist, but most of the
identity-bearing “learn, adapt, and turn preparation into a growing threat”
package is not a complete executable path.

## 4. Technique-specific audit

Donatello's Technique is recognized by the catalog and manifest, but not as a
fully executable card. The interpreter reports:

- `sneak_noncreature_spell_not_implemented` for `Sneak {U}`;
- `oracle_ability_not_implemented` for `Draw two cards`.

The engine's `legal_sneak_actions` accepts only cards whose interpreted Sneak
coverage is fully supported. Because Technique is a Sorcery and the current
Sneak program is bounded to supported creature Sneak, no Technique CAST option
is generated. AcceptancePilot therefore cannot legally select it, regardless
of whether it is in hand. Its `choose_sneak` policy would select the first CAST
if one existed, but the engine supplies only the PASS path for Technique.

In the focused 40-seed comparison, P0.3a drew 22 Technique card occurrences
across 18 games, cast 0, and resolved 0. No measurable card draw, combat
conversion, target choice, or closing effect followed. The card is therefore
effectively inert in the current simulator, not merely poorly timed by the
Pilot.

## 5. Pilot behavior

AcceptancePilot's main-action policy passes generic casts except for narrowly
named damage/destruction cards and chooses the lowest-cost creature at the
creature stage. Its Sneak policy chooses the first CAST option, otherwise PASS.
This means:

- Technique cannot reach the Pilot because semantic coverage removes its legal
  option first;
- even a fully supported generic noncreature spell would need a corresponding
  main-action policy path before AcceptancePilot would choose it;
- Gadget Master can reach the supported creature Sneak surface, but its
  combat-damage copy trigger is still unsupported;
- creature bodies and Turtle Techie's ETB draw are the most reliable central
  actions currently exercised.

The Pilot is therefore a secondary limitation, but it is not the only or first
failure: Technique and several other central effects are unavailable before
Pilot choice.

## 6. Deterministic seed comparison

The 40-seed P0.3/P0.3a comparison used identical Shredder P0.3 input,
matchup, orientation, and seeds 3000–3039. P0.3a changed opening/draw history
in 18 games and event history in all 40. Return-to-the-Sewers occurrences
fell from 49 to 27 in the sample, confirming the intended density change.

The deck-normalized winner and turn count were unchanged in all 40 pairs.
There was no Technique action-state branch to compare: Technique never entered
the legal CAST set. Thus the changed game states were mostly different hand and
library availability, not different setup-to-payoff or combat-conversion
decisions.

## 7. Ownership classification

`SEMANTIC_COVERAGE_DOMINANT`

Concrete reasons:

1. The changed card was drawn repeatedly but never cast or resolved because its
   central Sneak and draw text are unsupported.
2. Way with Machines' artifact-entry growth, Gadget Master's copy trigger,
   Does Machines' levels/recovery, Mutant Mechanic's counter continuity,
   Cam's interaction/draw, and Bō's equipment conversion are also incomplete.
3. The Pilot has real limitations, especially generic noncreature spell
   selection, but those limitations cannot explain Technique's zero casts by
   themselves: no legal Technique option exists at the engine/interpreter
   boundary.

This is not a claim that Pilot quality is irrelevant. It means deck power
cannot be interpreted until the central semantic surfaces are executable.

## 8. Further simulator-driven deck tuning

Further simulator-driven buffing is not justified. Adding stronger cards could
change bodies or mana efficiency, but it would not answer whether the intended
Technique card advantage, artifact-network growth, copy, recursion, equipment,
or Mutagen decisions work. The same unsupported or unchosen game plan could
remain weak, and a new deck change would confound ownership further.

No deck change, P0.3b/P0.4 candidate, engine change, Pilot change, or full
calibration is authorized by this audit.

## 9. Human-play recommendation

Human play may be more informative than another simulator balance iteration,
because humans can cast Technique as intended, choose when to hold or deploy
Does Machines, select Cam/Bō/Mutant Mechanic targets, and evaluate Gadget
Master copy lines. The clean runtime and repeatable 15% simulator result do not
make that result a faithful measure of the physical deck's technical identity.

However, the immediate next gate is a bounded simulator-coverage correction
for Technique's noncreature Sneak plus draw resolution and the adjacent central
artifact payoff surfaces. Human play should be planned in parallel, but no
simulator-derived deck revision should be authorized before that coverage
question is resolved.

## 10. Next-gate decision

`FIX_DONATELLO_SIMULATOR_COVERAGE_FIRST`

The next work should establish a minimal executable/observable path for
Technique and identify which adjacent artifact-payoff gaps are required to
interpret Donatello. Re-run only focused deterministic diagnostics after that
work; do not launch another 240-game smoke or alter the deck in this PR.
