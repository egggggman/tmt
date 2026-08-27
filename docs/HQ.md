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
- [HQ Current State](hq/CURRENT_STATE.md)
- [Tool Resilience](hq/TOOL_RESILIENCE.md)
- [Recovery Guide](hq/RECOVERY.md)
- [Work Packet Specification](hq/WORK_PACKET_SPEC.md)

## Master Project Map

| System, artifact, or product | Owner | Current durable state | Dependencies / Gate | Repository location |
| --- | --- | --- | --- | --- |
| Project governance and cross-department roadmap | HQ | Active; department authority model established | Accepted department evidence | `docs/HQ.md`, `docs/OUTSIDER_CONTINUITY.md` |
| SewerGraph / Design Studio analytical foundation through Deck Analysis v0.5.0 | Design Studio | Implemented | Scryfall facts, capabilities, database migrations | `src/tmnt_design_studio/`, `docs/ARCHITECTURE.md`, `docs/DATABASE.md`, `docs/DECK_ANALYSIS.md` |
| Design Intent contract | Design Studio | Accepted RFC | Canon/source support and analysis layers | `docs/rfcs/006-design-intent.md` |
| Ten-deck Prototype 0.1 history | Design Studio | Preserved | Design Intent and Standard legality | `decks/` |
| Ten-deck Prototype 0.2 environment | Design Studio | **Frozen** | Await credible Cardcade evidence before revision review | `decks/` |
| Cardcade Engine 0.8 architectural foundation | Cardcade | **Accepted**; Foundation Matrix 10 GREEN / 10 YELLOW / 0 RED | Continue mechanical coverage | `src/tmnt_design_studio/engine07.py`, `docs/cardcade/`, `tests/` |
| Post-foundation Actions and engine corrections | Cardcade | Accepted through Action #16 / PR #60 | Continue evidence-backed validation; preserve unsupported boundaries | Cardcade code, tests, acceptance evidence |
| Engine Validation Stage 0.2 tooling | Cardcade | Runner + plan-only launcher accepted in PR #61; gameplay execution not authorized by that merge | Merged-main readiness decision | Cardcade Stage/Smoke specs, runners, evidence |
| Broad calibration | Cardcade | **Blocked by Gate** | Successful engine-validation evidence + explicit authorization | Cardcade testing protocol/evidence |
| Prototype 0.3 | Design Studio | **NOT AUTHORIZED** | Cardcade evidence + explicit Design Studio decision | Future preserved prototype when authorized |
| Deck-box structural prototype | Mr. Paperback | p0.2 geometry physically validated; artwork/productization continues | Print/cut/fold/fit and final production stock | Physical-product records/specs |
| Sewer Stamps | Mr. Paperback | Prototype registered; physical iteration remains actionable | Print/cut/apply testing | Physical-product records/specs |
| Canon/source research | Canon / Source Material | Active support function | Department requests | `docs/Knowledge-Architecture.md`, `docs/WORLD_GUIDE.md`, `encyclopedia/` |
| Underground Press Issue #1 | The Underground Press | In production | Reusable component/template workflow | `docs/UNDERGROUND_PRESS.md`, editorial assets |
| Sewer Status Board | HQ | Operating standard documented | Durable GitHub evidence | `docs/SEWER_STATUS_BOARD.md` |
| THERECORD | HQ / instrumentation | Specification established; weekly archive to be appended over time | Observable usage/output evidence | `docs/THERECORD.md` and future weekly records |
| HQ Resilience 0.1 | HQ | **Active** — GitHub Can Run the Project | Portable Work Packets, recovery docs, synchronized state, tool-independent validation | `docs/hq/` |
| Cardcade GUI / DECKDAEMON (DD.0) | Cardcade / HQ tracking | Future product goal; subordinate to engine credibility | Authoritative engine/evidence state stable enough to present | Roadmap / future GUI specs |
| Ten-deck starter/battle set | HQ coordinating all departments | Target product; not production-ready | Credible deck baseline, human fun testing, validated physical deliverables | Component locations above |

## Current Status

### Overall Status

**ACTIVE DEVELOPMENT**

### Critical Path

**Cardcade engine validation toward a credible controlled calibration gate.**

Engine 0.8's architecture remains accepted. Cardcade has advanced through Action #16 and now has accepted coverage-aware Stage 0.2 evidence tooling. The immediate question is no longer whether the foundation exists; it is whether merged-main readiness evidence authorizes the next bounded engine-validation execution.

### What changed recently

- Actions #13–#16 were accepted through PRs #50, #58, #59, and #60.
- Generic engine corrections preserved Stack/Priority ordering, ETB provenance, terminal combat SBA handling, and fail-closed evidence.
- PR #61 merged the accepted Engine Validation Stage 0.2 evidence runner and plan-only launcher.
- PR #61's accepted Stage 0.2 contract records 45 pairings / 225 distinct planned games / 450 executions / 900 per-execution commitment artifacts.
- PR #61 reported 784 passed / 1 skipped locally and passing exact-head CI.
- Stage 0.2 gameplay was **not** authorized or executed by PR #61; a merged-main readiness decision remains required.
- HQ Resilience 0.1 has started so GitHub, rather than any one AI tool or chat, can run the project.

These are simulator-credibility milestones, not deck-balance conclusions.

### Gate — What's required?

Cardcade must produce trustworthy engine-validation evidence before controlled calibration can be treated as meaningful.

The Gate is not "make every deck 50%." It is reproducible rules execution, explicit unsupported behavior, authenticated evidence, deterministic replays, and enough mechanical credibility that downstream balance conclusions mean something.

### Blockers — What must be fixed?

The immediate blocker is **authorization/readiness for the next Stage 0.2 execution**, not a lack of a runner. Any failure exposed by readiness or execution must be corrected at the smallest appropriate engine/evidence layer before increasing test volume.

### Holds — Intentionally waiting

- Prototype 0.3 authorization.
- Calibration as balance evidence.
- Design Studio deck revisions based on Cardcade results.
- Human fun testing as the primary authority, until a credible automated baseline exists.

### Actionable now

- Complete the merged-main Stage 0.2 readiness decision.
- Continue HQ Resilience 0.1 and portable Work Packet adoption.
- Continue Mr. Paperback physical prototyping that does not depend on deck revisions.
- Continue Underground Press Issue #1/component work.
- Provide targeted Canon/source support when requested.
- Keep dashboards and front-door documents synchronized to merged GitHub evidence.

### Risks / watch list

- Treating accepted tooling as authorization to run the next stage.
- Treating engine-validation evidence as balance-valid evidence.
- Letting current state drift behind merged PRs.
- Depending on Codex or another single tool for project continuity.
- Allowing task intent, acceptance criteria, or local evidence to live only in chat.
- Using Cardcade results as automatic deck-edit instructions.

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

**Complete the merged-main readiness decision for Cardcade Engine Validation Stage 0.2. In parallel, complete HQ Resilience 0.1 so the next authorized task can move between Codex, another tool, or a human through GitHub without reconstructing chat history.**

## Change discipline

Preserve meaningful prototypes, simulation results, physical prototypes, and accepted decisions. Distinguish simulator, deck construction, balance, theme, physical-product, and subjective-fun problems. Change the smallest relevant layer, and never tune decklists to compensate for a simulator defect or tune the simulator merely to force balanced win rates.
