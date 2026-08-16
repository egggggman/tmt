# The Sewer Status Board

## Purpose

The Sewer Status Board is HQ's operational eye-in-the-sky view of Mutants the Gathering. It exists to reduce project-recovery overhead and make the current state obvious: what changed, what is blocked, what is intentionally waiting, what work is actionable, what the current Gate requires, and what the Next Move is.

The board is a presentation layer over durable project evidence. It is not a competing source of truth.

## Invocation

`PIZZAGRIND` is the conversation codeword for rendering the current Sewer Status Board.

The word **PIZZAGRIND must not appear inside the board itself**. It is an invocation convention, not product branding.

The text-only detailed counterpart is called **The Sewer Board Text**.

## Locked visual identity

The board should preserve a stable command-center identity while allowing its information modules to rotate with current work.

Locked direction:

- header hierarchy: `MTG` / `MUTANTS THE GATHERING` / `THE SEWER STATUS BOARD`;
- dark sewer/brick background;
- purple pipe framing;
- split turtle-shell imagery around the header;
- restrained neon module colors on black panels;
- simple single-color neon-outline Turtle head icons;
- crisp, high-contrast informational typography;
- decorative glow belongs on headings, frames, pipes, and icons rather than small body text.

The board's visual identity should not be redesigned every time project priorities change. **The template stays stable; the status data and relevant modules change.**

## Readability standard

The board is a glanceable command center, not an exhaustive report.

- Prefer larger body text and generous line spacing over information density.
- Shorten status language instead of shrinking type to make it fit.
- Reduce glow behind dense informational text.
- Use The Sewer Board Text for exhaustive detail.
- A module should earn space because it helps answer: **What changed? What needs TLC? What can we do now? What happens next?**

## Required information

Every board should make the following understandable at a glance:

1. project identity and Build → Measure → Understand → Refine;
2. Overall Status;
3. Critical Path;
4. department status and department Next Move;
5. current 10-deck prototype environment;
6. current Cardcade Gate / validation status;
7. **What Changed Since Last Board?**;
8. **Gate — What's Required?**;
9. **Blocker — What Must Be Fixed?** where relevant;
10. Actionable Options;
11. Risks / Watch List;
12. recent Milestones;
13. **Next Move**;
14. what unlocks if the current Gate clears.

The exact supporting modules may rotate according to current priorities.

## Humanized terminology

The board intentionally teaches project-management vocabulary through plain-language subtitles.

- **Gate — What's required?** The condition that must be satisfied to move forward.
- **Blocker — What must be fixed?** Something preventing the next stage from proceeding.
- **Hold — Intentionally waiting.** Work paused by choice or dependency; not automatically a problem.
- **Actionable — What can we work on now?** Productive work available immediately.
- **Critical Path — What controls the next unlock?** The work that determines when the larger project can move forward.
- **Evidence — What supports this status?** Durable facts or accepted records behind the conclusion.
- **Next Move — What should we do next?** The best immediate project action.
- **Milestone — What meaningful checkpoint is complete?** A durable completion worth preserving.

## Usage analytics boundary

Detailed usage analytics do not belong on the Sewer Status Board. Those are owned by `THERECORD`.

The board may display a tiny plan/usage health signal only when it affects current project decisions, for example `PLAN PRESSURE: COMFORTABLE` or an active usage-related blocker. Message counts, hours, session trends, efficiency charts, and historical usage analysis belong in THERECORD.

## Evidence and provenance

GitHub is the durable source of truth for accepted project state. Board content should distinguish:

- durable repository evidence;
- current working status;
- HQ interpretation or inference.

The board must not silently turn an inference into a durable fact.

## Department boundaries

The board coordinates work; it does not take ownership away from departments.

- Cardcade reports simulation evidence and hypotheses.
- Design Studio owns deck revisions.
- Mr. Paperback owns physical product execution.
- Canon owns source support.
- The Underground Press owns its editorial/production workflow.
- HQ owns cross-project coordination and the board itself.

## Next Move rule

Every board must include a Next Move.

The Next Move identifies the single highest-priority immediate action or project unlock supported by current evidence and the Critical Path. Actionable alternatives may also be shown so productive work can continue when the Critical Path is intentionally paused or another department needs attention.

## Preservation

The preferred visual reference should be stored as a durable repository asset when the binary artwork workflow is available. Until then this document is the canonical visual/behavioral specification; generated board images are working renders rather than authoritative project state.
