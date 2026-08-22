# Acceptance Match #001 — Prospective Opportunity-Witness Evidence

Candidate baseline: `491b196377c1e33fdbccde21870f8ae2790085de`  
Seeds: 7001–7005, two executions each  
Status: candidate evidence; independent audit required

## Result

Gameplay is unchanged: Acceptance #001 remains **18 unsupported registration events / 6 exact
pairs**, with the accepted winners and ending turns. Duplicate outputs are byte-identical and all
engine invariants remain clean.

The prospective instrumentation does **not** relabel all 18 events as reached. It records 18 exact
runtime semantic occurrences, of which:

- **14 are REACHED / UNSUPPORTED**, supported by one or more positive opportunity witnesses;
- **4 remain PRESENT / UNREACHED**;
- **32 distinct opportunity witnesses** were recorded (multiple real events can reach the same
  runtime occurrence);
- **27 generic references** point to mature Action-specific EXECUTED evidence. These references are
  an index, not an exhaustive replacement for the existing Action evidence ledgers.

## Per-seed evidence

| Seed | Result | Unsupported registrations | Reached occurrences | Present-only occurrences | Opportunity witnesses |
| ---: | --- | ---: | ---: | ---: | ---: |
| 7001 | Raphael T14 | 4 | 2 | 2 | 5 |
| 7002 | Raphael T18 | 1 | 1 | 0 | 1 |
| 7003 | Leonardo T19 | 3 | 3 | 0 | 5 |
| 7004 | Leonardo T43 | 7 | 6 | 1 | 18 |
| 7005 | Raphael T16 | 3 | 2 | 1 | 3 |
| **Aggregate** | — | **18 / 6 pairs** | **14** | **4** | **32** |

## Exact residual classification

| Exact Oracle fragment | Occurrences | Prospective result |
| --- | ---: | --- |
| Wingnut — Alliance choice of flying, menace, or haste | 5 | **5 reached**. Later authoritative controlled-creature entry events produce 17 distinct Alliance opportunities across the five games. No modal keyword effect executes. |
| Leonardo, Sewer Samurai — graveyard casting/finality compound | 5 | **4 reached, 1 present-only**. Nine represented main-phase contexts contain at least one authoritative qualifying graveyard creature across the reached occurrences. The remaining occurrence has no qualifying witnessed context. No graveyard cast or finality behavior executes. |
| Casey Jones — ETB top-four artifact filter | 2 | **2 reached** by Casey's own typed creature-entry events. No look/reveal/select/library transaction executes. |
| Raphael, Most Attitude — Alliance exile-top | 2 | **1 reached, 1 present-only**. Seed 7005 has a later controlled creature entry; seed 7001 does not. No exile executes. |
| Raphael, Most Attitude — attack-time play-exiled permission | 2 | **2 reached** by three authoritative attack events. The linked exile collection remains empty and no play permission executes. |
| Raphael, Most Attitude — Menace | 2 | **2 present-only**. No authoritative blocker candidate was considered against these Raphael objects, so presence and attacks alone do not prove Menace relevance. |

Counts of opportunities and occurrences intentionally differ. Four creature entries can make one
Wingnut occurrence relevant four separate times, while its Oracle text was registered once. The
deterministic opportunity identity prevents repeated observation of the same event from fabricating
additional opportunities.

## Executed evidence boundary

EXECUTED remains established by existing immutable Action and engine evidence: casting/Stack,
Priority/pass, triggers, damage, combat steps, Scry, filtering/Draw, discard/Draw, activated
abilities, Return, Sneak, Trample, Lifelink, Food, zones, and SBAs. The generic conformance index
only emits a reference when it can join an exact source runtime identity and Oracle fragment to a
mature evidence record. Absence from that index is not converted into unsupported or unexecuted;
the underlying typed evidence remains authoritative.

## Determinism and behavior freeze

| Seed | Duplicate SHA-256 |
| ---: | --- |
| 7001 | `5f32283de2cb5a3702cff8070477ec40e784d806d5280b44a4f9e009debe10cc` |
| 7002 | `397a086bf3d09a3cf5ea19c1dcc81eb5b900f35ffdb92fdfa11c44d506713496` |
| 7003 | `6c694e2979fae6497363547999e66e3990a7ef74fd22130f92cd065c4c444a9d` |
| 7004 | `b934f8cc60ec07a9b2ea2ae91f362206741316133346eb7306a6beeca94d88f0` |
| 7005 | `026e9b5c03f0094443134cceb013e9e1a7adba4237b169cfe2134e8c237ccf98` |

These hashes cover the new prospective evidence format; each seed's two executions match exactly.
No Stage #002 match was run. Action #13, smoke, calibration, Pilot tuning, deck changes, and
Prototype 0.3 remain unauthorized.

