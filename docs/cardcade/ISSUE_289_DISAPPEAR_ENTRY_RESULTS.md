# Issue #289 — conditional-entry Disappear checkpoint

Stacked on draft PR #319 at `eb89ad8e5eecd5887e053157adb3ed0645b9805c`.

## Selection and Oracle rule

The shared high-copy intervention is departure history plus complete conditional
creature-entry effects. Foot Mystic has six frozen copies across Splinter and
Shredder; Putrid Pals has three in Bebop & Rocksteady. Both use the same
departure-time-controller test, but Foot Mystic has an intervening-if ETB trigger
and Putrid Pals has an entry replacement effect. Insectoid Exterminator and
Michelangelo, Game Master each have three frozen copies and use end-step
intervening-if triggers; those clauses remain unsupported and are not marked
closed. This checkpoint does not implement a blanket “Disappear” keyword.

The official [TMNT release notes](https://magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-release-notes)
identify Foot Mystic and Michelangelo's intervening-if trigger condition. The
[mechanics article](https://www.magic.wizards.com/en/news/feature/teenage-mutant-ninja-turtles-mechanics)
states that Disappear looks back through the entire turn, even before the source
entered the battlefield. The engine records a departure for any permanent,
including a controlled permanent owned by an opponent; merely changing control
does not count. It does not require a watcher to be on the battlefield when the
departure occurs.

## Implemented and checked

- Generic Oracle grammar recognizes conditional ETB token creation and creature
  entry with a fixed number of +1/+1 counters. It rejects appended unrepresented
  instructions. No deck or card name is used in execution dispatch.
- Every real battlefield exit logs the old object identity, destination identity,
  controller at departure, type, and turn. Invariants join each history record to
  its zone transition. Existing typed leave-trigger event numbering remains
  unchanged when there are no watching abilities.
- Foot Mystic creates the trigger only when the condition holds at entry. Its
  trigger uses the existing stack/priority path, rechecks the condition on
  resolution, and survives source departure. The token uses generic token-entry
  events and state-based actions.
- Putrid Pals receives two counters on the new object before its entry event and
  before state-based actions. It receives none when the condition is false.
- Focused tests cover owner/controller disagreement, actual control change,
  hand/exile/graveyard departures, source leaving before trigger resolution,
  turn rollover, forged history rejection, false condition, renamed fixture,
  and repeatable event logs.

The authenticated six-game frozen diagnostic used both starting positions in
Splinter–Shredder, Splinter–Bebop & Rocksteady, and Shredder–Bebop & Rocksteady;
all six replays had identical digests. It observed 66 departures but no qualifying
Foot Mystic token trigger or Putrid Pals counter entry. The focused fixtures are
the direct execution evidence; these six games are only a runtime smoke check,
not balance evidence.

## Coverage and calibration gate

The original 172-row ledger and every earlier overlay remain untouched. The
new [overlay](ISSUE_289_DISAPPEAR_ENTRY_CHECKPOINT.json) closes exactly three
important rows: Foot Mystic in Splinter and Shredder, and Putrid Pals in Bebop &
Rocksteady. The separate [risk assessment](ISSUE_289_DISAPPEAR_ENTRY_CALIBRATION_READINESS.json)
retains 53 important gaps: 49 calibration blockers and four consequential
two-copy effects whose impact remains unbounded. There are zero critical gaps.
The two end-step Disappear rows remain blockers. Class levels, artifact
animation, combat restrictions, recursion, and token engines remain high priority.
No previously unsupported row was closed by reinterpreting older evidence.

The ten manifest deck contents were checked. Michelangelo and Splinter are LF in
this checkout while their manifest hashes were originally computed over CRLF;
normalizing line endings reproduces those exact frozen hashes. All other eight
files match byte for byte. No deck file or historic game evidence was changed.

Semantic runtime: `c4e4d098b06194d58f45f10d78e2bf3cb6aa2606248656e210943d5f8ea800c4`.
Focused semantic suite: **126 passed**. Full local regression: **1,914 passed,
10 skipped**. Repository-wide Ruff check and format, Baseline 005 structural
validator, diff whitespace check, and six deterministic diagnostic replays pass.

**Checkpoint acceptance: pending final-head CI. Baseline 005 calibration:
BLOCKED.** No control, balance experiment, merge, deck revision, or promotion.
