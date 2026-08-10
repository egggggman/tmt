# Mutants the Gathering HQ

HQ coordinates the Mutants the Gathering project without taking work away from its specialist
departments. This page is the project-level map and current-status view. It points to canonical
artifacts; it does not replace their specifications or histories.

## Department authority

| Department | Authority and boundary |
| --- | --- |
| HQ | Coordinates roadmap, project status, governance, major milestones, and decisions that cross department boundaries. HQ does not duplicate specialist work. |
| Design Studio | Owns deck construction, Design Intent, character and deck identity, prototypes, and deck revisions. It decides whether playtest evidence warrants a deck change and preserves earlier prototypes when creating a new one. |
| TMNT the Cardcade Game | Owns automated simulation, reproducible playtesting, telemetry, matchup evidence, engine validation, and calibration reports. Cardcade reports observations and hypotheses; it does not redesign decks or authorize revisions. |
| Mr. Paperback | Owns physical products and print deliverables, including boxes, dividers, tokens, counters, manuals, reference cards, trackers, templates, dielines, and print testing. A deliverable is not complete until it prints, cuts, folds, fits, or plays correctly. |
| Canon / Source Material | Owns thematic and source research, relationships, flavor, setting, and canon consistency. It supports Design Studio and Mr. Paperback but does not override gameplay quality when literal interpretation would make the game worse. |
| The Underground Press | Operates as a distinct associated creative publication. Its editorial and production workflow remains separate from deck design and Cardcade unless work genuinely overlaps. |

When ownership is unclear or multiple departments would otherwise solve the same problem, HQ assigns
the owner before work proceeds.

## Source of truth

GitHub is the durable project record. Accepted specifications, deck and prototype history, engine
code, schemas, simulation artifacts, calibration reports, production specifications, governance,
and durable decisions belong in this repository.

Project chats are working rooms for discussion, exploration, analysis, review, coordination, and
creative development. A decision that becomes durable policy must be recorded in GitHub rather than
left only in chat history. Existing canonical documents retain their authority:

- [Project Constitution](PROJECT_CONSTITUTION.md) governs mission and judgment.
- [Design Principles](DESIGN_PRINCIPLES.md) governs how contributors make decisions.
- [Architecture](ARCHITECTURE.md) governs technical layers and implementation boundaries.
- [Accepted Decisions](DECISIONS.md) records durable product and architecture decisions.
- [Roadmap](ROADMAP.md) records milestone direction and history.
- [The Underground Press](UNDERGROUND_PRESS.md) governs that publication.

## Master Project Map

Status describes the repository's current durable record. A pull request is pending evidence, not
accepted history, until merged.

| System, artifact, or product | Owner | Status | Dependencies | Repository location |
| --- | --- | --- | --- | --- |
| Project governance and cross-department roadmap | HQ | Active; department model established here | Canonical governance documents and department evidence | `docs/HQ.md`, `docs/PROJECT_CONSTITUTION.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md` |
| SewerGraph and analytical foundation through Deck Analysis v0.5.0 | Design Studio | Implemented on `main` | Scryfall facts, capabilities, database migrations | `src/tmnt_design_studio/`, `docs/ARCHITECTURE.md`, `docs/DATABASE.md`, `docs/DECK_ANALYSIS.md` |
| Design Intent contract | Design Studio | Accepted RFC; implementation remains a Design Studio concern | Canon/source research and existing analysis layers | `docs/rfcs/006-design-intent.md` |
| Leonardo Prototype 0.1 | Design Studio | Preserved on `main` | Design Intent, Standard legality, deck analysis | `decks/leonardo/PROTOTYPE_0.1.md` |
| Ten-deck Prototype 0.1 baseline and Prototype 0.2 candidates | Design Studio | Pending in Cardcade PR #15; do not duplicate or revise from HQ | Design Intent and Cardcade evidence | `decks/` in PR #15 |
| Cardcade engine, rosters, smoke runs, calibration, and audit evidence | TMNT the Cardcade Game | Pending in draft PR #15; engine stability gate is not yet satisfied | Frozen deck versions and reproducible card facts | `cardcade/`, `src/tmnt_design_studio/cardcade.py`, and `tests/test_cardcade.py` in PR #15 |
| Physical battle-set products and print specifications | Mr. Paperback | Planned; no accepted production package yet | Stable deck dimensions/content, token needs, brand and print tests | Repository location to be assigned when the first specification is accepted |
| Canon and source research | Canon / Source Material | Foundation present; expand only as deck or product work requires | Attributed TMNT sources and project interpretation | `docs/Knowledge-Architecture.md`, `docs/WORLD_GUIDE.md`, `encyclopedia/` |
| Underground Press publication system | The Underground Press | Governed; production remains distinct | World continuity and bounded project milestones | `docs/UNDERGROUND_PRESS.md`, `docs/Editorial-Bible.md` |
| Ten-deck starter/battle set | HQ coordinating all departments | Target product; not yet production-ready | Credible balanced deck baseline, human fun testing, and validated print deliverables | Component locations above; consolidated product specification not yet accepted |

## Current Status

### Active milestones

- Preserve the implemented v0.1.0-v0.5.0 analytical foundation and Leonardo Prototype 0.1.
- Review Cardcade PR #15 as a separate evidence package. It preserves Prototype 0.1, introduces
  bounded Prototype 0.2 candidates, and records Cardcade through Engine 0.6 without authorizing
  Prototype 0.3.
- Establish this HQ map as the coordination surface for later Design Studio, Cardcade, Canon,
  Paperback, and Underground Press work.

### Blockers

- Cardcade's Engine 0.6 stability gate fails in PR #15, so larger calibration and Design Studio deck
  revisions remain blocked pending credible engine behavior.
- Physical-product specifications depend on sufficiently stable deck contents and identified token,
  reference, and packaging requirements.

### Immediate priorities

1. Review and resolve PR #15 on its own merits without mixing HQ governance into it.
2. Keep Prototype 0.3 frozen until Cardcade evidence is credible and Design Studio explicitly
   authorizes a revision hypothesis.
3. After Cardcade evidence is accepted, route findings to Design Studio for the smallest
   evidence-backed deck decision.
4. Add Master Project Map rows when a meaningful system, artifact, prototype, or physical product
   gains an owner or accepted repository location; do not create duplicate trackers.

## Change discipline

Preserve meaningful prototypes, simulation results, and accepted decisions. Distinguish simulator,
deck construction, balance, theme, physical-product, and subjective-fun problems. Change the
smallest relevant layer, and never tune decklists to compensate for a simulator defect or tune the
simulator merely to force balanced win rates.
