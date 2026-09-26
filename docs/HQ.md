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
| Post-foundation Actions and engine corrections | Cardcade | Banked through Action #32 where repository evidence supports acceptance | Preserve unsupported boundaries; Action #33 remains unauthorized | Cardcade code, tests, acceptance evidence |
| Pilot Fitness V3 | Cardcade | Bounded pass completed | Preserve fitness limits; no automatic deck revision | `docs/cardcade/PILOT_FITNESS_V3_*` |
| Calibration Protocol V1 / Seed Table V2 | Cardcade | Protocol governed; seed table frozen and immutable | Fresh run identity, exact artifacts, separate authorization | `docs/cardcade/` calibration records |
| V16 calibration run | Cardcade | Incomplete at 121,808 / 184,320; storage/evidence failure | Never resume or use for partial balance conclusions | V16 run and preserved archive |
| Calibration Protocol V1 | Cardcade | **Complete and audited; interpretation merged** | Limited Design Studio authorization record | `docs/cardcade/` and `docs/design-studio/` |
| Prototype 0.3 | Design Studio | **LIMITED DESIGN-CYCLE AUTHORIZATION; FILES NOT AUTHORIZED** | Candidate packets and later explicit card-level approval | Future preserved prototype when authorized |
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

**Bounded Design Studio candidate-packet investigation for Shredder, Raphael, Donatello, and Casey Jones.**

Engine 0.8 is accepted, and banked evidence reaches Action #32 where supported. Pilot Fitness V3 and Calibration Protocol V1 are the governing preparation records. V16 is permanently incomplete after local storage exhaustion, not balance evidence.

### What changed recently

- Action #32 is banked; Action #33 remains **NOT AUTHORIZED**.
- V16 run `CALIBRATION_V1_20260919T012117Z_65775003` reached 121,808 / 184,320 distinct games (66.09%) before failing closed from local storage exhaustion.
- PR #172, merged at `58a8bac85600318ccd727959770b60869003c017`, established the fail-closed run-ID reservation contract.
- The migrated host is qualified: `C:\Projects\tmt` is code/runtime and `G:\` is prospective evidence storage with NTFS, 976.56 GiB capacity, 874.66 GiB free, and 2,000/2,000 atomic cycles successful.
- V16 historical evidence remains preserved and must not be resumed, combined, or used for partial balance conclusions.
- Calibration V1 run `CALIBRATION_V1_20260923T141649Z_3f838930291e` completed 184,320 / 184,320 distinct games and passed the completion audit; its statistical analysis is banked for Design Studio interpretation.

These are simulator-credibility milestones, not deck-balance conclusions.

### Gate — What's required?

Design Studio has authorized limited candidate-packet investigation; actual Prototype 0.3 deck files remain closed.

The Gate is not "make every deck 50%." It is reproducible rules execution, explicit unsupported behavior, authenticated evidence, deterministic replays, and enough mechanical credibility that downstream balance conclusions mean something.

### Blockers — What must be fixed?

The current blocker is evidence-to-card translation: candidate packets and human-play questions must be reviewed before any card-level approval. No deck file is changed by this authorization.

### Holds — Intentionally waiting

- Actual Prototype 0.3 deck-file authorization.
- Exact deck changes until ownership and tradeoffs are independently reviewed.
- Exact card-level revision approval after candidate packets and human evidence.
- Design Studio deck revisions based on Cardcade results.
- Human fun testing as the primary authority, until a credible automated baseline exists.

### Actionable now

- Prepare only the four authorized candidate packets.
- Review human-play evidence before any card-level approval.
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

**Prepare and review bounded candidate packets for the four authorized decks.** No card-level revision or Prototype 0.3 file creation is authorized by this state alone.

## Change discipline

Preserve meaningful prototypes, simulation results, physical prototypes, and accepted decisions. Distinguish simulator, deck construction, balance, theme, physical-product, and subjective-fun problems. Change the smallest relevant layer, and never tune decklists to compensate for a simulator defect or tune the simulator merely to force balanced win rates.
