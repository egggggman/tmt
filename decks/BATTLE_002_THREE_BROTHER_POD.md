# Battle 002 — Three-Brother Prototype 0.1 Pod

Status: **Heuristic rehearsal complete; tabletop round robin required**

## Reproducible rehearsal

`simulate_round_robin_0_1.py` ran 10,000 seeded trials per pairing with seed `20260809`.

| Pairing | First deck | Second deck |
| --- | ---: | ---: |
| Leonardo vs Raphael | 47.66% | 52.34% |
| Leonardo vs Donatello | 40.96% | 59.04% |
| Raphael vs Donatello | 43.23% | 56.77% |

Functional plan-attainment proxies were 76.9% for Leonardo, 84.7–85.2% for Raphael, and
64.6–65.3% for Donatello. Donatello's apparent matchup strength despite lower plan attainment is a
warning that the heuristic's authored weights may overvalue its development, artifacts, or broad
interaction. These are not real game results and must not justify tuning by themselves.

## Table round robin

Play each pairing at least six times, alternating the starting player: 18 games total. Keep all
three Prototype 0.1 lists unchanged.

Record:

1. Match winner, starting player, mulligans, and ending turn.
2. Whether each deck executed its recognizable plan.
3. Fun for pilot and opponent, with one concrete moment.
4. Whether Donatello actually suppresses both creature decks or merely looks favored in the proxy.
5. Whether Leonardo has enough closing power and Raphael enough recovery.
6. Any repeated non-game caused by mana, legendary duplicates, or unanswered snowballing.

The first pod change should address a repeated observed pattern with the smallest possible edit.
