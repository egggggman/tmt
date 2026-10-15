# Issue #289 — Robot-token trigger checkpoint

This draft checkpoint stacks on PR #327. Baseline 005 and all ten decks remain
frozen. The original 172-row ledger, all earlier overlays, and historical games
remain unchanged. The prior grant versus printed Sneak correction remains in
the runtime.

## Selection and Oracle scope

| Frozen fixture | Copies / deck | Exact missing clause | Event |
| --- | ---: | --- | --- |
| Mouser Foundry / Casey Jones | 4 | “When this artifact enters or leaves the battlefield, create a 1/1 colorless Robot artifact creature token.” | Its own entry or departure, regardless of destination |
| Ravenous Robots / Casey Jones | 4 | “Whenever you cast an artifact spell, create a 1/1 colorless Robot artifact creature token.” | Its controller's artifact spell cast, before resolution |

The [prior family triage](ISSUE_289_FAMILY_TRIAGE.json) observed five Foundry
casts/entries and six Ravenous Robots casts/entries in bounded frozen-deck
diagnostics; the missing Robot production affected repeated board development.
Both clauses produce the same token payload through different trigger contexts.
The generic token interpreter validates complete instructions and rejects
unsupported companions. Foundry's separate activated damage and Ravenous's
token-haste activation already had supported paths. Mutagen Man has two copies
in B&R and remains separate: its variable `X` token count and token-ability
cost reduction were not implemented or reclassified.

## Execution and provenance

The engine now recognizes complete self artifact entry/leave and controlled
artifact spell-cast trigger grammar without source-card dispatch. An authenticated
typed spell-cast event is emitted after payment and announcement. Zone events use
entry authority or departure-time last-known control. Each eligible source
queues its own trigger; APNAP stack placement and a real priority window precede
resolution. Token creation uses the existing generic token creation, permanent
entry and state-based paths. Triggers retain their original controller and source
incarnation if the source leaves or changes control afterward. An artifact
entering the battlefield does not count as casting it; the casting source itself
must already be on the battlefield to observe a cast. The compatibility casting
helper yields to priority when a cast trigger is stacked above its spell.

The focused fixtures use renamed synthetic sources and check complete parser
coverage, invalid continuation rejection, entry and leave, changed control,
reentry, simultaneous departures, multiple watchers, nonartifact/opponent casts,
source departure, countered spells, stack ordering, all-pass resolution,
fabricated cast rejection, and whole-trace
determinism. Frozen [diagnostics](ISSUE_289_ROBOT_TOKEN_SMOKE.json) authenticate
all ten manifest deck hashes and record six completed games with six matching
replays, ten pending Robot triggers and ten resolved Robot tokens. They include
Foundry entry and Ravenous cast occurrences. Their wins are **not** balance
evidence; self-leave is verified by focused deterministic fixtures.

## Readiness

The new semantic runtime is
`cec7e566458101e12c0dabd1d3e469960444543122a4443afc44bcdaef7837c3`.
The predecessor runtime is
`2e140950578ddbfabf9fdb931a7edde800d9775c56c1e54bb438e09317c3ccf6`.
The [new overlay](ISSUE_289_ROBOT_TOKEN_CHECKPOINT.json) closes **two** complete
Oracle rows and preserves all 172 original row identities. The separate
[readiness assessment](ISSUE_289_ROBOT_TOKEN_CALIBRATION_READINESS.json) is now
**0 critical, 33 important, 29 calibration blockers, four unbounded**.
No Mutagen Man row closed. The remaining high-value families include Shark
Shredder's combat-damage recursion (four copies across two decks), Leader's
Talent's Class levels/counter engine (four Leonardo copies), Rocksteady's Boar
blocking restriction (four B&R copies), and Mutagen Man's variable token engine.
The four unbounded residuals remain unbounded pending execution or exposure
evidence. The row-level ranking is retained in the readiness JSON.

Focused tests: **10 passed**. Full regression and final-head CI: **pending**.
Structural Baseline 005 validation and Ruff checks passed. Diagnostic replays:
**6/6 matched, zero runtime errors**.

**Checkpoint acceptance: pending final-head CI. Baseline 005 calibration:
BLOCKED.** No deck revision, 4,500-game control, merge or promotion occurred.
