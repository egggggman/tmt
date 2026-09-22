# PIZZAGRIND Visual Standard 1.0

Status: canonical HQ visual policy candidate

## Purpose

PIZZAGRIND summons the Mutants the Gathering **Sewer Status Board**. It is a project-state refresh of a stable visual instrument, not an invitation to redesign the dashboard.

**Canonical rule:** update the data; preserve the visual language.

Any material redesign requires explicit project-owner authorization and must preserve the previous standard as historical evidence.

## Canonical visual reference

The project owner selected the terminal/CRT Sewer Status Board supplied to HQ on 2026-09-08 as the canonical visual reference for Visual Standard 1.0.

Reference image SHA-256:

`6034d0a447bea738ee6b52c680ad0a4de662298cdcfeb834fa7fd9fbfec4299d`

Intended repository asset path:

`docs/hq/assets/sewer_status_board/PIZZAGRIND_CANONICAL_REFERENCE.png`

The exact reference PNG has precedence over generative interpretation. If a renderer cannot directly inspect the reference asset, this specification is the fallback contract; it must not invent a new art direction.

## Local repository boundaries

Mutants the Gathering uses two intentionally different local locations under `C:\Projects`.

### Development checkout

`C:\Projects\tmt`

This is the normal authoritative local Git working checkout for implementation and deterministic execution:

- active branches and commits;
- Cardcade source and tests;
- pytest / Ruff / validation;
- deterministic replays and authorized simulations;
- evidence generation intended for repository review.

### Chat artifact archive

`C:\Projects\downloads`

This is the local archive for material saved from ChatGPT or other working-room output before intentional promotion into the Git repository, including:

- generated images and visual references;
- PDFs and printable exports;
- local presentation/production artifacts;
- temporary deliverables and prototypes;
- other chat-generated files worth retaining outside the executable checkout.

The archive is **not** a second authoritative Git checkout and must not silently override GitHub or `C:\Projects\tmt`.

### Promotion rule

**Working code/state → `C:\Projects\tmt`**  
**Chat-generated/local artifacts → `C:\Projects\downloads`**  
**Durable/accepted project material → GitHub**

When an archived artifact becomes canonical, copy the exact approved file into the appropriate path under `C:\Projects\tmt`, verify identity where required, then commit it through the normal GitHub review/acceptance workflow. Preserve the archive copy rather than treating promotion as permission to erase history.

For the PIZZAGRIND Visual Standard 1.0 reference specifically, the owner-selected PNG should be retained in `C:\Projects\downloads` and promoted unchanged to:

`docs/hq/assets/sewer_status_board/PIZZAGRIND_CANONICAL_REFERENCE.png`

Its promoted bytes must match the locked SHA-256 above before the repository copy is accepted.

## Locked art direction

Preserve these characteristics:

- black CRT / terminal background;
- ASCII / ANSI / terminal-pixel construction rather than comic-book illustration;
- restrained neon palette led by green, purple, cyan, amber/yellow, red and warm off-white;
- large ASCII turtle shell at upper left;
- ASCII `MTG` header with the orange Magic-style center mark;
- green `MUTANTS THE GATHERING` title;
- purple `THE SEWER STATUS BOARD` subtitle;
- `BUILD → MEASURE → UNDERSTAND → REFINE` directly beneath the title;
- purple terminal-pipe framing and sewer details;
- thin dashed/pixel module borders;
- dense but highly legible terminal typography;
- minimal decorative glow around structural elements, not body text;
- modular dashboard composition rather than poster composition;
- wide landscape format with strong horizontal information hierarchy;
- bottom progression strip and restrained `COWABUNGA` footer treatment.

The board should feel like a secret 1991 sewer operations terminal: technical, playful, readable and evidence-driven.

## Explicit anti-drift rules

Unless the project owner explicitly authorizes a redesign, PIZZAGRIND must **not**:

- become a colorful comic-book poster;
- use rendered/cartoon turtle characters as the dominant visual language;
- replace the ASCII shell with illustrated character art;
- put the summon word `PIZZAGRIND` anywhere inside the board;
- replace the terminal grid with floating cards, banners or poster panels;
- introduce photorealism, glossy 3D UI, modern SaaS-dashboard styling or unrelated aesthetics;
- shrink body text merely to fit more information;
- invent completion percentages or decorative progress metrics;
- invent dates, PR numbers, Actions, SHAs, milestones, test counts or project state;
- silently rename departments or change project governance;
- treat an old board's content as current merely because its layout is canonical.

## Information architecture

The exact amount of text may vary with current evidence, but the canonical board should preserve the same hierarchy.

### Header band

- Overall Status
- Critical Path
- Project Health

### Primary department modules

Each department reports **where it is** and **what is next**:

- HQ
- Design Studio
- TMNT the Cardcade Game
- Mr. Paperback
- Canon / Source
- The Underground Press

### Cardcade module

Cardcade is the critical-path module while engine credibility is unresolved. Show current evidence rather than historical engine shorthand. Useful content includes:

- latest accepted milestone;
- current validation stage;
- accepted Actions / semantic coverage when relevant;
- deterministic/invariant status;
- explicit blockers and holds;
- the next authorized gate.

### Project Milestones

Show durable project milestones and their actual state. Do not imply a milestone is complete merely because preparatory work exists.

### Project Next Move

The board must contain one unmistakable **PROJECT NEXT MOVE (HIGHEST PRIORITY)** derived from current evidence and governance.

### Next Major Unlock

Preserve a bottom progression strip showing the route from current engine credibility through Design Studio review, prototype decision, calibration/balance work, human fun testing and starter-set completion. The exact labels may be updated as project governance evolves, but the strip remains a roadmap, not a claim that future gates are already authorized.

## Status semantics

Use status language consistently:

- **BLOCKED** — cannot proceed because a required condition is unmet.
- **HOLD** — intentionally waiting.
- **ACTIONABLE** — productive work may proceed now.
- **READY** — can start when selected/authorized.
- **ACCEPTED / COMPLETE** — durable evidence or governance has banked the item.

Do not convert a HOLD into a BLOCKED state or a candidate into ACCEPTED merely for visual simplicity.

## Freshness protocol

Every PIZZAGRIND render begins with a freshness sweep against GitHub before visual generation.

At minimum determine:

1. current authoritative `main` state / relevant latest commit;
2. meaningful merges since the previous board;
3. relevant open PRs and Work Packets;
4. current authorized Action or experiment;
5. current Cardcade evidence checkpoint and gates;
6. Design Studio prototype authorization state;
7. meaningful department changes that affect the board;
8. documentation/status drift that would make an old board misleading.

When current repository evidence contradicts an old board, **current evidence wins for content and the canonical reference wins for visual form**.

## Render protocol

The normal PIZZAGRIND sequence is:

**GitHub freshness sweep → derive current board facts → apply canonical reference/spec → render Sewer Status Board.**

The invocation itself should normally produce the board rather than a prose dashboard. Do not substitute Markdown for the visual board when the visual can be rendered.

## Readability requirements

- Prioritize accurate readable text over decorative detail.
- Use larger body type than would be typical for a dense poster.
- Keep small text crisp with little or no glow.
- Preserve strong contrast and generous module padding.
- Prefer fewer accurate lines over tiny exhaustive text.
- Rotate secondary modules when necessary rather than overcrowding the board.
- `WHAT CHANGED`, blockers/gates and `WHAT TO DO NEXT` are high-value modules when current evidence supports them.

## Data versus design

The board has two independent layers:

1. **Visual shell — stable.** Governed by this standard and the canonical reference.
2. **Project data — dynamic.** Refreshed from durable evidence for every invocation.

A stale board must never be preserved simply to maintain visual fidelity. A current board must never be visually redesigned simply because its data changed.

## Governance

PIZZAGRIND Visual Standard 1.0 is HQ-owned project presentation policy.

Minor readability corrections that preserve the reference language are allowed. Material changes to composition, aesthetic, visual identity, invocation behavior or core information hierarchy require explicit project-owner authorization and should create a new preserved visual-standard version rather than overwrite this one.

**PIZZAGRIND is a data refresh of the canonical Sewer Status Board, not a request to redesign the dashboard.**
