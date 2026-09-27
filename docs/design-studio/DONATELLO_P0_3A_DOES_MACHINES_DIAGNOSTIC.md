# Donatello P0.3a — Does Machines Diagnostic

Decision: `DOES_MACHINES_SETUP_VALIDATED`

This is a semantic diagnostic, not a balance result. No decklist, engine behavior,
Pilot policy, or card semantics were changed for this run.

## Runtime and inputs

- Repository: `f445eaebbbccd3d606f4d9614afd71365a64f122`
- Runtime under test: Does Machines setup coverage from the merged Cardcade slice
- Runtime file SHA-256:
  - `card_interpreter07.py`: `c899ae7d61f1d7be06b4d0491143ca6c93cd140c8fb16193f6288eade8b7dc9d`
  - `engine07.py`: `6489860fc6b16e375d54884951a86751f113d622b88544770fe19b551303a532`
  - `pilot07.py`: `b69e6141ac63295454aa9641dcfa09045c28c8611b66e033d181a9c6b8848a82`
- Donatello input: `decks/donatello/PROTOTYPE_0.3a.txt`
- Donatello SHA-256: `25812e2d7f0ac64ae2476c0d62298db35196d1719c9376b5369d5080faa6aad1`
- Opponents: Shredder P0.3, Raphael P0.3, Casey Jones P0.3
- Harness path: repository-owned `run_smoke_game`

## Diagnostic design

Seeds `3000–3009` were run once for each Donatello-first pairing:

| Pairing | Games |
| --- | ---: |
| Donatello / Shredder | 10 |
| Donatello / Raphael | 10 |
| Donatello / Casey Jones | 10 |
| Total | 30 |

No full 240-game smoke was run. A read-only diagnostic Pilot wrapper counted legal
cast-option occurrences and delegated every choice to the unchanged AcceptancePilot.

## Does Machines telemetry

| Measure | Result |
| --- | ---: |
| Draw occurrences | 26 |
| Games with Does Machines drawn | 17 / 30 |
| Legal cast opportunities | 63 occurrences across 17 games |
| Casts | 26 |
| Resolutions | 26 |
| Successful enter/setup triggers | 26 |
| Cards milled | 52 |
| Cards drawn | 52 |
| Cards discarded | 52 |
| Games with a later Donatello cast after setup | 17 / 17 setup-drawn games |
| Artifact cards among setup-milled/discarded cards | 0 |

Every Does Machines cast in the sample resolved and produced the expected four-card
graveyard movement plus two-card draw sequence. The committed trigger records show
different hand and graveyard IDs before and after resolution; each setup moved two
cards from library to graveyard, drew two, and moved two hand cards to graveyard.

The zero artifact count matters: this sample demonstrates real setup state changes,
but it does not yet demonstrate that the setup sequence creates useful level-2
artifact-recovery targets. The later-cast count shows continued game progression,
not causal proof that Does Machines alone produced those actions.

## Technique telemetry

| Measure | Result |
| --- | ---: |
| Draw occurrences | 16 |
| Games with Technique drawn | 13 / 30 |
| Legal cast opportunities | 39 occurrences across 12 games |
| Casts | 15 |
| Resolutions | 15 |
| Cards drawn through Technique | 30 |
| Sneak opportunities | 0 |
| Sneak executions | 0 |

Technique coverage remains active after the Does Machines implementation. The zero
Sneak count is consistent with the compact normal-play sample and does not invalidate
the existing deterministic Sneak regression coverage.

## Representative event evidence

For Donatello / Shredder seed `3002`, Does Machines entered during turn 3 in
`precombat_main`. The event sequence includes:

1. `spell_cast` for Does Machines;
2. `permanent_resolved` for Does Machines;
3. `etb_mill_draw_discard_committed` with two `milled_ids`, `draw_count: 2`, and two
   `discarded_ids`;
4. `trigger_resolved` with effect `etb_mill_draw_discard`.

The committed record reports distinct pre/post hand and graveyard contents. Later
events include a Donatello `Fugitive Droid` cast, demonstrating continued action
execution after the setup trigger.

## Descriptive outcomes

Results are from Donatello's perspective and are directional only:

| Matchup | Result |
| --- | ---: |
| Donatello / Shredder | 1–9 |
| Donatello / Raphael | 0–10 |
| Donatello / Casey Jones | 2–8 |
| Aggregate | 3–27 |

The prior Technique-only 30-game diagnostic was 4–26 aggregate, with results of
2–8, 0–10, and 2–8 respectively. This small movement is not balance evidence.

## State-divergence findings

Does Machines now materially diverges from the pre-coverage behavior: it is cast,
resolves, and changes both hand and graveyard state in ordinary deterministic games.
AcceptancePilot uses the generated cast options, and all 17 games in which setup was
drawn had a later Donatello cast after the trigger. However, the sample produced no
artifact cards from the setup mill/discard movements, so level-2 recovery cannot yet
be evaluated as a conversion path. The unchanged weak descriptive result is therefore
not evidence that setup semantics are inert; it leaves the missing level/recovery path
as the next unresolved bottleneck.

## Remaining Does Machines gaps

These remain unsupported and were not implemented here:

- Class progression and sorcery-speed level advancement;
- level-2 recovery of up to two artifact cards from the graveyard;
- level-3 artifact animation and +1/+1 counters.

The broader Donatello gaps also remain, including Donatello, Way with Machines,
Gadget Master, Mutant Mechanic, Sewer-veillance Cam, and Bespoke Bō semantics.

## Next gate

The setup milestone is validated, but the diagnostic does not justify another smoke
as the immediate next action. Implement Does Machines level-2 artifact recovery first,
with deterministic legal target selection and no level-3 approximation. Then run the
focused recovery diagnostic before deciding whether to rerun the frozen 240-game smoke.
