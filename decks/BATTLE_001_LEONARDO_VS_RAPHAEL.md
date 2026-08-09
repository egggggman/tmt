# Battle 001 — Leonardo 0.1 vs Raphael 0.1

Status: **Heuristic rehearsal complete; tabletop battle required**

## Reproducible rehearsal

`simulate_prototypes_0_1.py` ran 10,000 deterministic-seed trials using seed `20260808`.

- Raphael proxy wins: **52.63%**
- Leonardo proxy wins: **47.37%**
- Leonardo on the play: **52.54%**
- Leonardo on the draw: **42.20%**
- Leonardo plan-attainment proxy: **77.59%**
- Raphael plan-attainment proxy: **85.52%**

This is not a Magic rules engine and the sampling interval measures only random sampling inside its
own authored heuristic. It approximates opening hands, land drops, mana use, development, and broad
role weights; it does not execute card text, combat choices, removal timing, Sneak, Alliance,
legendary conflicts, or player skill. The result is a **playtest hypothesis**, not evidence that
Raphael is stronger.

## Table battle protocol

Play at least six games, alternating the starting player. Keep both Prototype 0.1 lists unchanged.
Record mulligans, missed land drops, result and ending turn, then answer:

1. Is the apparent play/draw sensitivity real?
2. Can Leonardo's tactical interaction blunt Raphael's first wave?
3. Can Raphael rebuild after Leonardo stabilizes?
4. Does Nightwatcher end games with adequate warning and counterplay?
5. Do the decks feel unmistakably different and fun on both sides?

Do not tune from the rehearsal alone. The first change must be supported by repeated table evidence.
