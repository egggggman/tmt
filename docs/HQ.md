# Mutants the Gathering HQ

HQ coordinates the Mutants the Gathering project without taking work away from its specialist departments. This page is the project-level map and current-status view. It points to canonical artifacts; it does not replace their specifications or histories.

For a newcomer-oriented overview, start with [Outsider Continuity](OUTSIDER_CONTINUITY.md).

## Department authority

| Department | Authority and boundary |
| --- | --- |
| HQ | Coordinates roadmap, project status, governance, major milestones, and decisions that cross department boundaries. HQ does not duplicate specialist work. |
| Design Studio | Owns deck construction, Design Intent, character/deck identity, prototypes, and deck revisions. It decides whether playtest evidence warrants a deck change and preserves earlier prototypes when creating a new one. |
| TMNT the Cardcade Game | Owns automated simulation, reproducible playtesting, telemetry, matchup evidence, engine validation, and calibration reports. Cardcade reports observations and hypotheses; it does not redesign decks or authorize revisions. |
| Mr. Paperback | Owns physical products and print deliverables, including boxes, dividers, tokens, counters, manuals, reference cards, trackers, templates, dielines, stickers/stamps, and print testing. A deliverable is not complete until it prints, cuts, folds, fits, or plays correctly. |
| Canon / Source Material | Owns thematic/source research, relationships, flavor, setting, and canon consistency. It supports Design Studio and Mr. Paperback but does not override gameplay quality when literal interpretation would make the game worse. |
| The Underground Press | Operates as a distinct associated creative publication. Its editorial and production workflow remains separate from deck design and Cardcade unless work genuinely overlaps. |

When ownership is unclear or multiple departments would otherwise solve the same problem, HQ assigns the owner before work proceeds.

## Source of truth

GitHub is the durable project record. Accepted specifications, deck/prototype history, engine code, schemas, simulation artifacts, calibration reports, production specifications, governance, and durable decisions belong in this repository.

Project chats are working rooms for discussion, exploration, analysis, review, coordination, and creative development. A decision that becomes durable policy must be recorded in GitHub rather than left only in chat history.

Primary orientation and governance records:

- [Outsider Continuity](OUTSIDER_CONTINUITY.md)
- [Project Constitution](PROJECT_CONSTITUTION.md)
- [Design Principles](DESIGN_PRINCIPLES.md)
- [Architecture](ARCHITECTURE.md)
- [Accepted Decisions](DECISIONS.md)
- [Roadmap](ROADMAP.md)
- [The Sewer Status Board](SEWER_STATUS_BOARD.md)
- [THERECORD](THERECORD.md)
- [The Underground Press](UNDERGROUND_PRESS.md)

## Master Project Map

| System, artifact, or product | Owner | Current durable state | Dependencies / Gate | Repository location |
| --- | --- | --- | --- | --- |
| Project governance and cross-department roadmap | HQ | Active; department authority model established | Accepted department evidence | `docs/HQ.md`, `docs/OUTSIDER_CONTINUITY.md` |
| SewerGraph / Design Studio analytical foundation through Deck Analysis v0.5.0 | Design Studio | Implemented | Scryfall facts, capabilities, database migrations | `src/tmnt_design_studio/`, `docs/ARCHITECTURE.md`, `docs/DATABASE.md`, `docs/DECK_ANALYSIS.md` |
| Design Intent contract | Design Studio | Accepted RFC | Canon/source support and analysis layers | `docs/rfcs/006-design-intent.md` |
| Ten-deck Prototype 0.1 history | Design Studio | Preserved | Design Intent and Standard legality | `decks/` |
| Ten-deck Prototype 0.2 environment | Design Studio | **Frozen** | Await credible Cardcade evidence before revision review | `decks/` |
| Cardcade Engine 0.8 architectural foundation | Cardcade | **Accepted**; Foundation Matrix 10 GREEN / 10 YELLOW / 0 RED | Continue mechanical coverage | `src/tmnt_design_studio/engine07.py`, `docs/cardcade/`, `tests/` |
| Create Token / Deal Damage / Scry / First+Double Strike coverage | Cardcade | Merged through PR #33 | Continue smallest evidence-backed mechanics coverage | Cardcade code, tests, acceptance evidence |
| Broad calibration / large smoke | Cardcade | **Blocked by Gate** | Simulator mechanical credibility | Cardcade testing protocol/evidence |
| Prototype 0.3 | Design Studio | **NOT AUTHORIZED** | Cardcade evidence + explicit Design Studio decision | Future preserved prototype when authorized |
| Deck-box structural prototype | Mr. Paperback | p0.2 geometry physically validated; artwork/productization continues | Print/cut/fold/fit and final production stock | Physical-product records/specs |
| Sewer Stamps | Mr. Paperback | Prototype needed | Standardized stamp frame + print/cut/apply test | Physical-product records/specs |
| Canon/source research | Canon / Source Material | Active support function | Department requests | `docs/Knowledge-Architecture.md`, `docs/WORLD_GUIDE.md`, `encyclopedia/` |
| Underground Press Issue #1 | The Underground Press | In production | Reusable component/template workflow | `docs/UNDERGROUND_PRESS.md`, editorial assets |
| Sewer Status Board | HQ | Operating standard documented | Durable GitHub evidence | `docs/SEWER_STATUS_BOARD.md` |
| THERECORD | HQ / instrumentation | Specification established; weekly archive to be appended over time | Observable usage/output evidence | `docs/THERECORD.md` and future weekly records |
| Ten-deck starter/battle set | HQ coordinating all departments | Target product; not production-ready | Credible deck baseline, human fun testing, validated physical deliverables | Component locations above |

## Current Status

### Overall Status

**ACTIVE DEVELOPMENT**

### Critical Path

**Cardcade mechanical coverage and validation.**

Engine 0.8's architectural foundation is accepted. The remaining problem is no longer a zero-RED architecture gate; it is whether the simulator executes enough of the mechanics encountered by the ten-deck environment to justify broad calibration and downstream Design Studio review.

### What changed recently

- Engine 0.8 foundation accepted after Foundation Matrix reached 10 GREEN / 10 YELLOW / 0 RED / 0 UNKNOWN.
- Create Token merged in PR #30.
- Deal Damage merged in PR #31.
- Scry merged in PR #32.
- First Strike / Double Strike combat damage steps merged in PR #33.
- At PR #33 the full suite reported 314 passed / 1 skipped, deterministic Acceptance Match #001, zero invariant violations, and 61 unsupported events / 18 exact pairs.
- Sewer Status Board and THERECORD operating specifications are being made durable through the outsider-continuity audit.

These are simulator-credibility milestones, not deck-balance conclusions.

### Gate — What's required?

Cardcade must reach sufficient mechanical credibility for the current ten-deck environment before broad calibration can be trusted.

The Gate is not "make every deck 50%." It is trustworthy rules execution, explicit unsupported behavior, reproducibility, and evidence strong enough that downstream balance conclusions mean something.

### Blockers — What must be fixed?

The current blocker is incomplete mechanical coverage encountered by real games. Missing mechanics should be handled as reusable, rules-grounded Actions/systems rather than card-name shortcuts or pilot assumptions.

### Holds — Intentionally waiting

- Prototype 0.3 authorization.
- Broad calibration runs.
- Large smoke batches.
- Design Studio deck revisions based on Cardcade balance results.
- Human fun testing as the primary authority, until the mechanical baseline is credible.

### Actionable now

- Continue Cardcade mechanical coverage and validation.
- Continue Mr. Paperback physical prototyping that does not depend on deck revisions.
- Prototype Sewer Stamps as a modular print/sticker system.
- Continue Underground Press Issue #1 production and reusable component-library work.
- Provide targeted Canon/source support when another department requests it.
- Improve durable project documentation and archive evidence when working-room decisions become policy.

### Risks / watch list

- Treating architectural acceptance as if all Magic mechanics are already supported.
- Starting large simulations before represented mechanics are trustworthy.
- Using Cardcade results as automatic deck-edit instructions.
- Allowing physical/design assets or dashboard conventions to live only in conversation history.
- Inventing usage metrics or Plus-plan percentages that the underlying product does not expose.

## Sewer Status Board

The **Sewer Status Board** is HQ's visual operational dashboard. It summarizes current project state from durable repository evidence and must not become a competing source of truth.

`PIZZAGRIND` is the working-room invocation codeword. The word itself does **not** appear inside the board.

The board must emphasize clear operational language, including:

- **What Changed Since Last Board?**
- **Gate — What's Required?**
- **Blocker — What Must Be Fixed?**
- **Hold — Intentionally Waiting**
- **Actionable — What Can We Work On Now?**
- **Critical Path — What Controls the Next Unlock?**
- **Evidence — What Supports This Status?**
- **Next Move — What Should We Do Next?**
- **Milestone — What Meaningful Checkpoint Is Complete?**

Detailed usage analytics belong in THERECORD, not on the Sewer Status Board. A small plan-pressure health signal may appear only when operationally relevant.

See [The Sewer Status Board specification](SEWER_STATUS_BOARD.md).

## THERECORD

THERECORD is the append-only weekly instrumentation archive for message/activity usage, efficiency, durable output, plan pressure, and trend analysis. It exists to identify process efficiencies over time and must distinguish measured values from metrics that are not exposed.

See [THERECORD](THERECORD.md).

## Next Move

**Continue Cardcade mechanical-coverage validation while preserving productive parallel work in Mr. Paperback, The Underground Press, and Canon. Do not authorize Prototype 0.3 or broad calibration until the Gate is credibly met.**

## Change discipline

Preserve meaningful prototypes, simulation results, physical prototypes, and accepted decisions. Distinguish simulator, deck construction, balance, theme, physical-product, and subjective-fun problems. Change the smallest relevant layer, and never tune decklists to compensate for a simulator defect or tune the simulator merely to force balanced win rates.
