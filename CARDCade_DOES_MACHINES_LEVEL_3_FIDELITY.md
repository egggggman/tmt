# Does Machines Level 3 — Correction Candidate

## Status

**Candidate for independent review. No complete games were run.** This change is on `fix/does-machines-level-3`, based on `origin/main` commit `1454e657310c4e5ffc8e3468a8da6ff1ccc3a6de`. It does not edit the frozen Stage 002 checkout or historical results.

## Card contract

The authoritative card-data record is Does Machines, Oracle ID `df54b79d-f31d-4582-86c0-1d34ec77be0f`, from `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json` (SHA-256 `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`; manifest SHA-256 `6b5271af75150a361f77e7b89306c709959dfdf497c448dfdc978e5dc9a17950`). Its Level 3 text is:

> `{4}{U}: Level 3`
>
> At the beginning of combat on your turn, put three +1/+1 counters on target artifact you control. If it isn't a creature, it becomes a 0/0 Robot creature in addition to its other types.

The card's Class instruction requires sorcery timing for level activations. The Level 3 cost is four generic and one blue mana. It can be activated only from Level 2. The Level 3 ability applies at the beginning of its controller's combat while the Class is level 3. It targets an artifact the controller controls when the trigger is put on the stack. On resolution it adds three +1/+1 counters. A noncreature artifact becomes a 0/0 Robot creature and retains its other types; an artifact creature receives only the counters. These are permanent changes with no stated expiration. An Equipment that becomes a creature becomes unattached under the Equipment rules and the TMNT release notes.

Rules references: CR 107.16a and 716.2a (Class level bars and level abilities), CR 500.6 (beginning-of-combat trigger timing), CR 122.1a (+1/+1 counter effect), and CR 301.5c / 704.5n (Equipment attachment legality and state-based detachment). [Magic Comprehensive Rules, June 19, 2026](https://media.wizards.com/2026/downloads/MagicCompRules%2020260619.pdf); [TMNT release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes).

## Before and after

The preserved Stage 002 analysis found 62 reached Level 3 occurrences across 46 games and no authenticated execution references. That historical evidence remains untouched. Its frozen source identities are `card_interpreter07.py` blob `7b39e4fcb2402385e7d46893f08300ffdf862540`, `engine07.py` blob `62fb52e18e2747d4b758f041de6279032c887435`, and `stage002.py` blob `bed173e3f4f3f13b0d1320a3a910153c38d844be` at preserved source commit `32a80228714674327aca62f8b86b70c4c4afc929`.

The preserved deterministic failure placed Does Machines at Level 2 with five untapped Islands and both a noncreature artifact and an artifact creature on the battlefield. The interpreter marked `{4}{U}: Level 3` unsupported; legal main actions omitted it, its payment plan was unavailable, and neither level state nor artifact state changed.

The same bounded case now offers the action, pays exactly five mana including blue, resolves to level 3, and emits a resolved activation record. At the next beginning of combat, a legal controlled artifact is selected and the trigger resolves once. Synthetic outcomes verify:

- `Sewer-veillance Cam`: becomes an Artifact Creature — Robot, 3/3 from its three counters, and is attack-eligible when it was controlled since the beginning of the turn.
- `Fugitive Droid`: keeps its artifact-creature types and receives three counters, changing from 1/1 to 4/4.
- `Quintessential Katana`: when targeted while attached, retains Equipment as a subtype, becomes a 3/3 Robot creature, receives three counters, and detaches.
- Four available mana rejects the activation without tapping lands or changing the level. With no controlled artifact, the beginning-of-combat trigger is not put on the stack.
- Trigger and activation records are indexed by Stage 002's authoritative execution index and join the exact source and Oracle fragment. The result event records its source, trigger, target, before/after characteristics, counters, and resulting state.
- Deterministic runs produce equivalent target state and Does Machines events. Cleanup leaves the type change and counters in place; a resolved trigger cannot resolve a second time.

The synthetic combat case exposed one narrow engine dependency: combat legality read the printed card type instead of the permanent's current type. Attacker and blocker eligibility now use the authoritative permanent type, so the newly animated artifact participates in combat rules.

## Correction and coverage

The correction adds exact Does Machines Level 3 activation semantics, checks that the Class is at level 2 and the player has sorcery timing and sufficient `{4}{U}`, advances the level on resolution, and generates the Level 3 beginning-of-combat trigger. Trigger target selection, provenance checks, effect application, Equipment detachment, state-based checks, and authenticated telemetry use the engine's existing architecture. No pilot or deck-name behavior changed.

The activation-coverage regression ledger remains at 164 recognized fragments and 136 distinct Oracle identities. Fully executable activation coverage increases from 24 to 25 fragments (still 23 distinct card names); the executable digest changes from `dfaf418f90e12257bec9b36233a8e2567d8ba3226ddf841e1223189bd013898d` to `2d882b7b874858b0f2ebec1d5817959d001a532802f44fe6ab3461036807225d`. No historical game classification was rewritten.

## Validation

Executed with the existing workstation Python 3.12 and pytest 8.4.2, using bytecode generation disabled:

- `test_does_machines_level_three.py`, `test_does_machines_level_two.py`, and `test_activated_abilities.py`: **44 passed, 1 deselected**. The deselected test launches a complete game and was excluded by directive.
- Stage 002 execution-authentication cases (`genuine_transaction`, fabricated execution identity, and ordinary execution key): **4 passed, 44 deselected**.
- `git diff --check`: clean.

The 900-game calibration, complete-game smoke test, broader game suite, and independent review have not been performed. The frozen 62/46 evidence gap describes historical outcomes and is not reclassified by this synthetic correction. Request an independent code review of this branch before any further gameplay or calibration is authorized.
