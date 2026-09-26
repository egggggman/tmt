# Donatello Prototype 0.3a Semantic Diagnostic

Status: post-PR #210 capability diagnostic; not a balance result.

## Runtime and inputs

- Repository: `4799d0bad092b8e2035fff1c96b67dd348253b79`
- Runtime change under test: PR #210, Cardcade semantic coverage for direct draw
  spells and noncreature Draw/Sneak resolution
- Runtime file SHA-256 identities:
  - `card_interpreter07.py`: `580ac99a9d0aa4c07a42a6b661dfe96be07302516a446d2fd34417e8e756ca44`
  - `engine07.py`: `9e03ac0758ac81e82e557822890977664e730a376ffcb13301b73ae362fda207`
  - `pilot07.py`: `478074ec72fb4c5389ecf1cfa9639a8773b54fdafef5fc3b70e48fbbdeba1363`
  - `stage002.py`: `3ab1b23e28e00bdb840e59e1df034a0899e638c9ba200b56af4e90865ff50d13`
- Donatello input: `decks/donatello/PROTOTYPE_0.3a.txt`
- Donatello SHA-256: `25812e2d7f0ac64ae2476c0d62298db35196d1719c9376b5369d5080faa6aad1`
- Held opponents: Shredder P0.3, Raphael P0.3, Casey Jones P0.3
- No decklists were changed.

## Diagnostic design

The repository-owned `run_smoke_game` path was used with the frozen orientation rule
and seeds `3000–3009` for each Donatello pairing:

- Donatello / Shredder: 10 games
- Donatello / Raphael: 10 games
- Donatello / Casey Jones: 10 games

Total: 30 deterministic games. No full 240-game smoke was run. A read-only observer
around `AcceptancePilot` counted legal Technique cast options without changing choices.

## Technique evidence

| Measure | Result |
|---|---:|
| Technique card occurrences drawn | 12 |
| Games with Technique drawn | 11 / 30 |
| Legal main-phase cast option occurrences | 30 |
| Games with a legal Technique cast option | 11 / 30 |
| Technique casts | 12 |
| Technique resolutions | 12 |
| Cards drawn through Technique | 24 |
| Draw-resolution events with success | 12 |
| Technique Sneak legal-option occurrences | 0 |
| Technique Sneak executions | 0 |

The 30 legal-option count is an opportunity count across repeated main-phase decision
windows, not a game count. In every game where Technique was drawn and became legally
castable, AcceptancePilot cast it; all 12 casts resolved and each drew two cards.

The zero Sneak count is informative: AcceptancePilot used Technique proactively in the
main phase whenever the represented draw spell was legal, so the normal sample did not
exercise the alternative-cost combat window. The dedicated semantic regression suite
still covers the actual noncreature Sneak payment, return of an unblocked attacker,
resolution, and deterministic two-card draw. This diagnostic therefore validates the
new Draw path in real games and the Sneak path in the same engine’s deterministic
semantic tests, without changing Pilot strategy for this measurement.

## Representative event evidence

For Shredder / Donatello seed `3006`, Technique resolved on turn 5 in
`precombat_main`:

1. `cost_paid` for `{2}{U}`;
2. `spell_cast` with a stack object;
3. `draw_spell_resolved`, `quantity: 2`, `draw_succeeded: true`;
4. `spell_resolved` with the Technique Oracle fragment and no target.

Across the 11 games with a Technique resolution, 11 had later meaningful game events;
the diagnostic recorded 469 such subsequent events, including later plays, casts,
combat actions, and draws. This demonstrates state progression after resolution, not a
claim that all later value came solely from Technique.

## Descriptive outcomes

These 30 games are directional diagnostics only:

| Matchup | Result from Donatello perspective |
|---|---:|
| Donatello / Shredder | 2–8 |
| Donatello / Raphael | 0–10 |
| Donatello / Casey Jones | 2–8 |
| Aggregate | 4–26 |

The results are not balance evidence and do not authorize card tuning.

## Remaining semantic gaps

The diagnostic did not implement or claim coverage for the remaining central package:

- Does Machines: Class levels, mill/draw/discard entry effect, artifact recovery, and
  level-3 artifact animation/counters remain incomplete.
- Donatello, Way with Machines: artifact-entry counter trigger remains outside this
  diagnostic.
- Donatello, Gadget Master: artifact-copy combat-damage trigger and target choice remain
  outside this diagnostic.
- Donatello, Mutant Mechanic: counter/animation activation and counter-transfer trigger
  remain outside this diagnostic.
- Sewer-veillance Cam: enter/leave tap-or-untap choice and sacrifice draw activation
  remain outside this diagnostic.
- Bespoke Bō: its exact supporting semantics remain outside this diagnostic.

These gaps can still limit conversion of Technique-generated cards into competitive
board states. No claim is made that Donatello is balanced or fully represented.

## Decision and next gate

Decision: `SEMANTIC_COVERAGE_VALIDATED`

The critical capability criterion is met: Technique was drawn, became legally castable,
was selected by AcceptancePilot, resolved in ordinary deterministic games, and produced
real two-card draw effects. The unchanged weak descriptive results are not grounds for
another immediate deck revision because the purpose of this run was semantic validation.

Next gate: proceed to the exact frozen 240-game Prototype 0.3 pre-balance smoke rerun,
with no deck changes and no further simulator optimization in this diagnostic PR.
