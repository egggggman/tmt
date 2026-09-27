# Donatello P0.3a — Does Machines Level-2 Diagnostic

Decision: `DOES_MACHINES_LEVEL_TWO_VALIDATED`

This is a deterministic semantic diagnostic, not a balance result. No decklist,
runtime semantics, Pilot strategy, or smoke schedule was changed.

## Identities

- Repository: `d7c86b121a9a8db45c61d184a18a9d11c6d143ba`
- Harness: repository-owned `run_smoke_game`
- Runtime: merged Does Machines level-2 Cardcade implementation
- `engine07.py` SHA-256: `1a958dd10c77389fd937af7e36826592009daabac5a32c0c9c90d012357a6f5a`
- `card_interpreter07.py` SHA-256: `574c71c1f53682d221cf32fd959f3ade7acfd7919e6be29bba91a828a3e78d13`
- `pilot07.py` SHA-256: `b69e6141ac63295454aa9641dcfa09045c28c8611b66e033d181a9c6b8848a82`
- Donatello P0.3a SHA-256: `25812e2d7f0ac64ae2476c0d62298db35196d1719c9376b5369d5080faa6aad1`
- Shredder P0.3 SHA-256: `818e9a847fcdf8521f53ab9b49c0f054ddd6f9bce95e9fd57c89cb6c94da2ed2`
- Raphael P0.3 SHA-256: `220ea90ccc579e09bef38ce972ba84f661c2382b92c7a4559667d24a5eec6f51`
- Casey Jones P0.3 SHA-256: `f18d2dd6591520e495a0c723e1d15f5d3f4f6ce8a2693e4f93be0cd6660e838f`

## Diagnostic design

Seeds `3000–3009` were run once for each Donatello-first pairing:

| Matchup | Games |
| --- | ---: |
| Donatello / Shredder | 10 |
| Donatello / Raphael | 10 |
| Donatello / Casey Jones | 10 |
| Total | 30 |

A read-only counting wrapper observed legal level-up options and delegated every
choice to the unchanged `AcceptancePilot`. No second orientation or full smoke was
run. All 30 games completed without runtime errors.

## Does Machines level-up telemetry

| Measure | Result |
| --- | ---: |
| Does Machines draw occurrences | 26 |
| Games with Does Machines drawn | 17 / 30 |
| Does Machines casts | 26 |
| Setup-trigger resolutions | 26 |
| Legal level-2 option occurrences | 109 across 15 games |
| Level-2 activations | 21 |
| Successful level advancements | 21 |
| Games reaching level 2 | 15 / 30 |
| Advancement payments | 21 × `{1}{U}`; 42 mana symbols total |
| Level-2 recovery triggers/actions | 21 |
| Eligible artifact target IDs offered | 59 |
| Artifacts returned | 36 |
| Zero-target recoveries | 3 |
| Downstream recovered-card cast/resolution events | 28 |

AcceptancePilot did spend mana for level 2 whenever the generated activation was
legal. Advancements occurred in normal precombat main phases, mostly on turns 5,
9, 11, and 17. Recovery therefore became a real game-state action rather than only
a synthetic test path.

Recovered cards were:

| Card | Returned |
| --- | ---: |
| Sewer-veillance Cam | 9 |
| Fugitive Droid | 15 |
| Bespoke Bō | 6 |
| Buzz Bots | 6 |

## Graveyard provenance

The diagnostic classified Donatello-owned artifact movements using authoritative
`zone_changed` records and the setup trigger's object IDs:

| Source | Artifact cards entering Donatello's graveyard |
| --- | ---: |
| Does Machines mill | 9 |
| Does Machines discard | 29 |
| Ordinary lethal damage / creature death | 84 |
| Other ordinary artifact sources | 0 |

Thus, unlike the pre-level-2 setup diagnostic, the current runtime demonstrates
that both setup mill and setup discard can create legal recovery targets. Ordinary
gameplay also supplies many artifact targets through creature deaths. The 59 offered
IDs and 36 returned cards show that target availability is not merely theoretical;
three triggers correctly resolved with no legal target.

## Representative event evidence

Donatello / Shredder seed `3002` reached level 2 on turn 5. The event sequence
contained:

1. `class_level_advanced` with `{1}{U}: Level 2`, `from_level: 1`, and `to_level: 2`;
2. `class_level_recovery_targets_selected` with two offered and two selected IDs;
3. `class_level_artifact_recovery_resolved` with two recovered IDs;
4. subsequent card movement and normal cast/resolution events for recovered cards.

Seeds with zero-target recovery also emitted the target-selection and resolution
events with empty selected/recovered ID lists, preserving safe behavior.

## Technique confirmation

| Measure | Result |
| --- | ---: |
| Technique draw occurrences | 12 |
| Games with Technique drawn | 12 / 30 |
| Technique casts | 12 |
| Technique resolutions | 12 |
| Cards drawn through Technique | 24 |
| Sneak executions | 0 |

Technique remains executable and resolves its draw effect. The zero Sneak count is
consistent with this compact normal-play sample; existing semantic regression tests
continue to cover the Sneak path.

## Descriptive outcomes

Results are from Donatello's perspective and are directional only:

| Matchup | Donatello W–L |
| --- | ---: |
| vs Shredder | 1–9 |
| vs Raphael | 0–10 |
| vs Casey Jones | 2–8 |
| Aggregate | 3–27 |

The prior setup diagnostic was 3–27. This unchanged small-sample result is not
evidence that level 2 or recovery is inert; the telemetry shows both are exercised.

## Findings and next gate

Level 2 is validated: legal advancement occurs, the permanent state changes to
level 2, recovery selects only legal artifact cards, zone movement is correct, and
recovered cards produce subsequent actions. The remaining low win result is better
explained by broader unsupported Donatello permanents and the still-unsupported
level-3 path than by missing level-2 representation.

The next highest-leverage gate is another semantic slice: implement and diagnose the
`Donatello, Way with Machines` artifact-entry trigger before another 240-game smoke.
That capability directly tests whether the recovered artifact package produces the
intended permanent-value conversion. Does Machines level 3, Gadget Master, Mutant
Mechanic, Sewer-veillance Cam, and Bespoke Bō remain subsequent documented gaps.
