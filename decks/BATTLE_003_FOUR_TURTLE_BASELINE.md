# Battle 003 — Four-Turtle Baseline Pod

Status: **Heuristic rehearsal complete; tabletop baseline required**

The deterministic heuristic ran 10,000 trials per pairing with seed `20260809`.

| Pairing | Result |
| --- | ---: |
| Leonardo vs Raphael | Raphael 52.34% |
| Leonardo vs Donatello | Donatello 59.04% |
| Leonardo vs Michelangelo | Michelangelo 51.41% |
| Raphael vs Donatello | Donatello 56.77% |
| Raphael vs Michelangelo | Raphael 52.10% |
| Donatello vs Michelangelo | Donatello 59.51% |

## Baseline hypotheses

- Donatello is the apparent early leader, but the heuristic may overvalue his artifact/value profile.
- Leonardo and Michelangelo appear close enough to begin unchanged.
- Raphael holds a small proxy edge over both Leonardo and Michelangelo.
- Starting-player splits remain large enough that real games must alternate play/draw.
- Michelangelo's plan-attainment proxy is about 70%, below Leonardo and Raphael but above Donatello.

These are model outputs, not Magic results. The model does not execute card text, combat, token
activation costs, removal timing, or player decisions.

## Physical/digital baseline

Play every pairing at least six times, alternating the starting player: **36 games total**. Do not
change a Prototype 0.1 list during the baseline.

For each game capture winner, starting player, mulligans, ending turn, fun for both players,
character feel, whether the deck executed its plan, and one concrete high or low moment. Balance
changes begin only after repeated table evidence identifies a pattern.
