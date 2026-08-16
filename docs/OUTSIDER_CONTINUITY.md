# Mutants the Gathering — Outsider Continuity Guide

## What this project is

Mutants the Gathering is a community-driven tabletop Magic: The Gathering fan project focused on building a cohesive battle/starter set of ten fun, distinct, themed, Standard-legal 60-card TMNT decks designed primarily to play against one another.

The project extends beyond deck construction into automated playtesting, physical products, printed materials, worldbuilding, and presentation.

Core development philosophy:

> Playable first. Explainable increasingly.
>
> Build → Measure → Understand → Refine.

Theme, synergy, balance, character identity, mechanical coherence, and fun are first-class requirements.

## The target product

The long-term product is a cohesive ten-deck Mutants the Gathering starter/battle set supported by individual deck boxes, a master collector box, tokens and counters, a life counter, a Field Manual, deck dividers, quick-reference materials, matchup tracking, character/art cards, stickers/stamps, and other printed extras.

The ten decks are Leonardo, Raphael, Donatello, Michelangelo, Splinter, Shredder, Krang, Bebop & Rocksteady, April O'Neil, and Casey Jones.

## Departments and authority

### HQ
Coordinates roadmap, priorities, cross-department decisions, project status, governance, milestones, and conflicts between department goals. HQ coordinates work rather than duplicating specialist work.

### Design Studio
Owns playable deck construction, Design Intent, card selection, character identity, synergy, structural validation, prototype versions, interpretation of playtest evidence, and deck revisions. Historical prototypes are preserved. Cardcade may report evidence and hypotheses; Design Studio decides whether decks change.

### TMNT the Cardcade Game
The automated simulation and playtesting subsystem. It owns reproducible gameplay simulation, telemetry, matchup matrices, engine validation, consistency and balance evidence, synergy-execution analysis, and calibration artifacts. It does not redesign decks. Simulator defects must not be compensated for by deck changes.

### Mr. Paperback
Owns physical products and deliverables: boxes, dividers, stickers/stamps, tokens, counters, Field Manual, quick-reference cards, trackers, templates, dielines, print files, and physical prototypes. Department rule: if it does not print, cut, fold, fit, or play correctly, it is not finished.

### Canon / Source Material
Provides source-backed character research, relationships, flavor, setting, and thematic consistency. Canon informs Design Studio and Mr. Paperback but does not override gameplay quality when literal interpretation would make the game worse.

### The Underground Press
An associated creative publication within the project universe. Its editorial and production workflow remains distinct from deck design and Cardcade unless work genuinely overlaps.

## Source of truth

GitHub is the durable technical and project record. Accepted specifications, deck lists, prototype history, Cardcade code, schemas, simulation artifacts, calibration reports, governance, decisions, production specifications, and durable project documentation belong here.

ChatGPT Project conversations are working rooms for discussion, exploration, analysis, review, coordination, and creative development. Important decisions made there should be promoted into GitHub when they become durable policy. Conversation history alone is not sufficient archival evidence.

## Current development boundary

The ten-deck Prototype 0.2 environment is frozen while Cardcade establishes a sufficiently credible mechanical baseline. Prototype 0.3 requires Design Studio authorization after adequate Cardcade evidence; it is not an automatic simulator output.

Cardcade development proceeds progressively: structural validation → smoke testing → engine validation → calibration → Design Studio review → revised prototype → repeat. Large simulation batches must not be used to create false confidence while simulator behavior remains questionable.

Historical prototypes, simulation results, and accepted decisions are evidence and must not be overwritten merely because newer work exists.

## Project-management language

- **Gate** — what is required to move forward.
- **Blocker** — what must be fixed before proceeding.
- **Hold** — intentionally waiting; not necessarily a problem.
- **Actionable** — productive work that can be done now.
- **Critical Path** — work controlling what unlocks next.
- **Evidence** — durable support for a status or conclusion.
- **Next Move** — best immediate action.
- **Milestone** — a meaningful completed checkpoint.

## The Sewer Status Board

The Sewer Status Board is HQ's eye-in-the-sky operational dashboard. Its purpose is to make current project state understandable at a glance: what changed, what is blocked, what is actionable, what the current gate requires, risks, milestones, and the Next Move.

`PIZZAGRIND` is the conversation invocation codeword for rendering The Sewer Status Board. The word PIZZAGRIND is not board branding and must not appear inside the board itself.

The visual identity uses the MTG / Mutants the Gathering / The Sewer Status Board header, dark sewer-board presentation, purple pipe framing, restrained neon module colors, simple neon-outline Turtle heads, and modular panels. Modules may rotate as project priorities change; the visual identity should remain stable. Small text should favor legibility over information density.

**The Sewer Board Text** is the text-only counterpart for detailed status when visual density would hurt readability.

The board is not the archive. It presents current evidence-backed operational truth.

## THERECORD

THERECORD is the project's historical instrumentation and efficiency dashboard. It is intentionally separate from The Sewer Status Board.

THERECORD tracks weekly usage and operating metrics when they are actually observable: message/session activity, active hours, peak periods, durable output, GitHub throughput, artifacts and prototypes, rework/context-recovery signals, plan-pressure events, limit interruptions, and other useful efficiency measures.

Weekly records are append-only snapshots rather than a single overwritten dashboard. This allows week-over-week and rolling trend analysis. Metrics that are not exposed by the underlying product must be marked **NOT EXPOSED** rather than estimated as fact.

PIZZAGRIND should contain only minimal usage/plan-pressure information when it affects project decisions; the detailed metrics belong in THERECORD.

## Change discipline

When possible, distinguish simulator problems, deck-construction problems, balance problems, theme problems, physical-product problems, and subjective fun problems. Change one layer at a time and prefer the smallest evidence-backed change capable of testing a hypothesis.

Automated simulation establishes a credible baseline; it cannot determine whether humans enjoy playing a deck. Once the mechanical baseline is credible, human playtesting becomes authoritative for subjective fun.

## Licensing boundary

This is an independent, non-commercial, community-driven fan project. Original project-created systems, software, infrastructure, workflows, governance, documentation, design systems, and production materials are licensed only to the extent the project has rights to license them. TMNT and Magic: The Gathering names, characters, trademarks, card content, artwork, and other third-party protected materials remain solely with their respective rights holders. See `LICENSE` and `NOTICE` for the repository's formal boundary.

## How to orient yourself

A newcomer should begin with this guide, `README.md`, `PROJECT_STATE.md`, `docs/HQ.md`, `docs/ROADMAP.md`, `docs/DECISIONS.md`, and the department-specific records. When documents disagree, prefer accepted repository evidence and newer durable decisions while preserving older documents as historical evidence rather than silently rewriting history.

The project should always make one question easy to answer:

> What is the Next Move, and what evidence says it is the right one?
