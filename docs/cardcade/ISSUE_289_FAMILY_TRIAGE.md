# Issue #289 — consolidated readiness triage

This assessment follows [HQ's process directive on PR #322](https://github.com/egggggman/tmt/pull/322#issuecomment-6195137139).
It is a planning and diagnostic checkpoint on validated draft PR #325, with
**no semantic change**. The 172 original row identities, Baseline 005 deck
bytes, all earlier overlays and game evidence are unchanged. The starting
#322 snapshot had 47 important rows, 43 blockers and four unbounded entries;
#323–#325 closed 12 rows by implementation, leaving **zero critical, 35
important, 31 blockers and four unbounded**. The reproducible
[machine evidence](ISSUE_289_FAMILY_TRIAGE.json) checks those hashes and
retains each open row's deck, card and exact Oracle fragment under one of ten
planning families. The current semantic runtime is
`a95807a7bf0a8a87b78155c425fe275da8b223190941e167d859ecf9f90902d9`.

## New runtime defect: repair before further semantic expansion

In a frozen Splinter-first versus Shredder diagnostic, seed **326**, the pilot
was offered Sneak for **Ninja Teen itself in hand**. The Class text instead
grants Sneak only to **creature cards in the graveyard**; Ninja Teen is an
Enchantment — Class. The interpreter reports its grant as a direct Sneak
ability when examining that card in hand. The pilot paid `{3}{B}`, returned
an unblocked attacker, and cast the enchantment during declare blockers.
After both players passed priority, the engine put it onto the battlefield
*tapped and attacking*, then raised `noncreature Sneak evidence has a
battlefield result` at turn 35. Both runs failed identically with snapshot
SHA-256 `ce34b19eddc71d3b8ffec271be328e7e5871db2213ef68c7c0b320e23f7e3490`.
Fifteen other diagnostic games and their replays completed, but this result
blocks mechanical readiness. The affected source is the general distinction
between a text grant and a direct keyword; the correction should constrain
legal actions, not relax the invariant or special-case Ninja Teen.

## Family ranking

The table ranks prospective batches **after** repairing that legal-action
defect. Copies count distinct frozen card copies, not the sum of repeated
Oracle-clause rows. The bounded sample has eight pairings, both starts,
one fixed seed per pairing, and 16 deterministic replays. “Casts” are actual
pilot spell casts. “Presence” is the engine's unsupported-fragment registration
on a battlefield object; it is not successful resolution. Existing opportunity
witnesses and event counts establish exposure only. For unsupported clauses,
legal availability, pilot selection and effect resolution are unknown or
unimplemented; a zero in this sample is **not** evidence of negligible impact.
These games do not estimate win rates.

| Rank | Family | Rows / copies / decks | Bounded observation | Gameplay risk and coherent scope |
| ---: | --- | ---: | --- | --- |
| 1 | Artifact token engines | 4 / 10 / 2 | Five Mouser Foundry and six Ravenous Robots casts/entries; 11 fragment presences | Missing Robot bodies alter Casey's board and artifact economy. Start with the shared 1/1 Robot creation payload for Foundry entry/leave and Robots artifact-cast triggers; Mutagen Man's variable X ETB remains a separate cost/choice subfamily. |
| 2 | Class counter engines | 5 / 4 / 1 | Five Leader's Talent casts; 40 departure witnesses and 158 witnesses each for level 2 and level 3 | Repeatable counters and level transitions change Leonardo's combat and card use. A complete Class level and trigger batch is larger than the Robot-token batch. |
| 3 | Combat and death recursion | 4 / 9 / 3 | Three Shark Shredder casts, two player-damage events; two Improviser casts and hits | Shark's opponent-graveyard selection and tapped-attacking entry can swing two decks. Pain 101 and Improviser are distinct payloads; do not close them together without separate resolution tests. |
| 4 | Combat legality and team effects | 4 / 12 / 4 | Two Rocksteady casts, five Splinter casts, eight family entries, 15 player-damage events | Multiple-blocker limits and team modifiers alter legal combat. Includes two still-unbounded rows; event counts do not prove a changed block decision. |
| 5 | Artifact counters and animation | 5 / 5 / 1 | Three Way with Machines and one Mutant Mechanic casts | Donatello's counters, counter transfer, and persistent animation affect board identity; reuse existing generic layer and counter paths. |
| 6 | Activated resource conversion | 5 / 3 / 1 | Ice Cream Kitty not drawn/cast in this bounded sample | Sacrifice-to-draw/life competes with casting and changes B&R resources. Exposure and pilot propensity remain unknown. |
| 7 | Artifact copy effects | 4 / 5 / 2 | One Gadget Master cast and player-damage event | Copying artifacts and Equipment needs complete copied characteristics, attachment and event provenance. |
| 8 | Damage to mana | 1 / 2 / 1 | One Raphael, Ninja Destroyer cast; two player-damage events, no evidence it was dealt damage | Restricted floating mana could affect resources, but the relevant damage trigger was not observed. |
| 9 | Temporary combat effects | 2 / 5 / 2 | One Guac & Marshmallow Pizza cast | ETB targeting/untap and a separate scry combat spell; one unbounded row. |
| 10 | Artifact scaling | 1 / 2 / 1 | No Krang, Master Mind cast | Continuous power scaling remains a blocker; exposure unobserved here. |

The family names organize work; they do not mark partial clauses supported.
Each of the 35 row references and the prior per-row score remain in the JSON.
The four unbounded entries retain their status. The earlier completed
Disappear end-step batch recorded five conditional trigger resolutions in six
games; Ninja Teen level-three grant recorded three graveyard Sneak casts in six
games; Does Machines recorded seven level-three advances, 19 combat target
resolutions and two lasting animations in six games. These preserved
[Disappear](ISSUE_289_DISAPPEAR_END_STEP_SMOKE.json),
[Sneak](ISSUE_289_CLASS_GRAVEYARD_SNEAK_SMOKE.json), and
[animation](ISSUE_289_CLASS_ARTIFACT_ANIMATION_SMOKE.json) observations
show genuine execution, while the new illegal Sneak action shows that
earlier passing fixtures did not exhaust action legality.

## Recommended smallest coherent batch and gate

**Batch zero, required:** correct the generic direct-Sneak versus granted-
Sneak distinction in legal-action generation. A grant that applies to
graveyard creature cards must never become an activation on its source
enchantment in hand, exile or graveyard. Keep legitimate printed creature
Sneak and Class-granted creature Sneak available with normal timing, payment,
stack, zone and priority rules. Test an illegal noncreature grant source,
legal printed and granted creature paths, source departure, and exact
deterministic replay of seed 326. This is a newly reproduced runtime defect,
not an extra row closed by reclassification.

**First gap-closing batch after that gate:** generic triggered creation of
1/1 Robot artifact creature tokens for Foundry's own entry and departure
and Robots' controller casting an artifact spell. Both parents use the same
token payload, the existing event/stack system, and ordinary token-entry
events. Test each trigger, simultaneous or repeated events, controller
changes, source departure, artifact casts from allowed zones, priority,
countered spells, state-based actions, resulting Robot characteristics,
deterministic replays, and action telemetry. Record the chain from parent
event to trigger availability/selection to resolution and board change.
Retain Mutagen Man's X-token and cost-reduction rows as open until complete.

Focused fixtures must reject incomplete Oracle variants. During iteration,
run focused tests; before acceptance run full regression, repository Ruff,
structural validation, and authenticated deterministic frozen-deck games,
including the failing seed. Regenerate the overlay and independent
calibration assessment from the frozen 172-row ledger with a concise row
delta. A future 4,500-game control requires a **separate** independent
readiness decision after runtime invariants pass and material blockers are
closed or empirically bounded.

**Triage evidence:** READY for HQ review. **Engine checkpoint:** BLOCKED by
the reproduced runtime failure. **Baseline 005 calibration:** **BLOCKED** by that failure,
31 important blockers, and four unbounded residuals. No deck change,
semantic implementation, control run, merge, or baseline promotion occurred.
