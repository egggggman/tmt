# HQ research record — Turtle Team-Up and Bad Guys deck direction

**Recorded:** 2026-10-21  
**Status:** Reference preserved; Design Studio investigation pending. Not a deck promotion or simulation authorization.  
**Ownership:** HQ records decisions; Design Studio owns deck design; Cardcade owns simulator validation and match evidence; Canon supports thematic verification.

## Why this record exists

The project may shift to other priorities. Preserve the official Turtle Team-Up reference and the reasoning behind broadening the underperforming Bebop & Rocksteady deck slot, so work can resume without reconstructing chat discussions.

## Approved thematic direction

- The **Bad Guys** deck slot replaces **Bebop & Rocksteady** as the intended *future identity*, with the subtitle **Shredder's Cronies**.
- Focus on **Shredder's minions**, not an unrestricted collection of all TMNT villains. Bebop & Rocksteady remain featured characters; Foot Soldiers, mutant henchmen and other Shredder-aligned lackeys are thematic candidates.
- Distinguish this deck from the separate **Shredder** deck (leader/mastermind) and **Krang** deck (technology/artifact engine).
- Initial exploration may retain black-green to isolate the impact of a wider theme; any color change needs explicit rationale.
- **Design Studio** may prepare a new, separate sandbox prototype and design intent. This does not overwrite or automatically promote any historical list.

**Decision thread:** https://github.com/egggggman/tmt/issues/359

## Official Wizards of the Coast source

- **Turtle Team-Up contents and decklists:** https://magic.wizards.com/en/news/announcements/teenage-mutant-ninja-turtles-turtle-team-up-contents
- **Cooperative play context:** https://wpn.wizards.com/en/news/turtle-team-up-a-cooperative-way-to-play-and-teach-magic
- **Release notes / Oracle and mechanic interpretation reference:** https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes

The product provides four 60-card hero decks (Leonardo, Donatello, Raphael, Michelangelo) and a distinct **38-card cooperative enemy deck** with bosses and event cards. The four hero lists each use **24 basic lands / 36 nonlands**, while the preserved R9-B Bebop & Rocksteady candidate uses **20 lands / 40 nonlands**. This is a construction comparison, **not proof** that the candidate needs 24 lands.

The enemy deck is a useful **theme/role reference**: Foot Disciple (5), Foot Skirmisher (3), Foot Enforcer (2), and bosses such as Shredder, Bebop, Rocksteady and Karai. Its boss and event systems are **not** equivalent to Standard-legal cards for conventional 60-card head-to-head play. The official lists include TMC cards; inclusion in a product is not proof of Standard legality. Check each proposed card individually, including exact printing/Oracle rules and format legality.

## Historical Cardcade evidence and caveats

**R9-B candidate** `OBL-R9-BEBOP-A`: −1 Frog Butler / +1 Stomped by the Foot versus Baseline 005. Completed 900/900 games, 900 deterministic replay games, nine matching replay cells, zero runtime errors.

- R9-B: **323/900 (35.89%)**.
- Preserved historical control summary: **316/900 (35.11%)**, a **+0.78 percentage-point** change. Original raw 4,500-game control artifact is unavailable/unverified; HQ accepted the preserved machine-readable report with an explicit evidence limitation.
- Weak candidate matchups: **Splinter 17/100**, **Casey Jones 28/100**, **Raphael 31/100**.
- Other candidate matchups: April 48, Donatello 36, Krang 36, Leonardo 43, Michelangelo 39, Shredder 45 wins per 100.
- Results are **observations**, not proof that theme breadth, land count, Oracle text, or a specific card caused losses.
- The runner verifies the frozen semantic runtime identity, candidate diff and replay determinism, but this does **not independently establish complete Oracle correctness**.
- Cardcade should inspect attack/block requirements, triggered/activated ability execution, pilot action selection, and matchup loss signatures before attributing weaknesses to deck construction.

**Evidence:** https://github.com/egggggman/tmt/pull/358 and `docs/objective-balance-lab/ROUND_9_B_BEBOP_RESULTS.md`.

## Research tasks when work resumes

1. **Design Studio:** Create a comparison matrix of the four official hero precons: lands, mana curve, early plays, interaction, threats, copy counts, theme execution. Record whether official precon card legality transfers to the target Standard format (do not assume).
2. **Design Studio + Canon:** Audit the enemy deck's Shredder-aligned cast and distinguish thematic reference material from playable Standard-legal cards. Identify synergistic Bad Guys options that do not erase Shredder or Krang identity.
3. **Cardcade:** Analyze preserved B&R games versus Splinter, Casey and Raphael, separating Oracle implementation defects, pilot shortcomings, mana consistency, and genuine deck issues. No autonomous deck revisions or unapproved batches.
4. **Design Studio:** Draft **Bad Guys — Shredder's Cronies** as a new sandbox prototype with clear Design Intent, legal 60-card list, candidate rationale and a smallest useful test hypothesis.
5. **HQ gate:** Review findings and decide whether to authorize an isolated experiment. Do not promote to Baseline 005 or silently alter the roster's historical record.

## Preservation and authority

Keep **Baseline 005**, earlier Bebop & Rocksteady prototypes, R8 and R9-B evidence, simulator/runtime hashes, and prior accepted decisions unchanged. The official Turtle Team-Up lists are **design references**, not competitive win-rate targets. This record captures a design-direction decision and open research, not a proven fix or final production deck.

**Related issue:** https://github.com/egggggman/tmt/issues/359  
**R9-B evidence PR:** https://github.com/egggggman/tmt/pull/358

Playable first. Explainable increasingly. **COWABUNGA.**
