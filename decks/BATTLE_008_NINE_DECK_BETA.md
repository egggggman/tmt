# Battle 008 — Nine-Deck Beta Baseline

Status: **Goldfish-development rehearsal only; not rules-complete Magic**

Krang's seeded 10,000-trial pairing results:

| Opponent | Krang proxy result |
| --- | ---: |
| Leonardo | 47.94% |
| Raphael | 44.80% |
| Donatello | 37.64% |
| Michelangelo | 46.51% |
| Splinter | 47.61% |
| April | 48.15% |
| Casey | 47.95% |
| Shredder | 45.48% |

The heuristic places Krang low, but it treats `Krang, Master Mind` as an eight-mana spell and does
not execute affinity. This is a known systematic modeling error, so the result must not trigger a
buff. Real games must record artifacts controlled, actual mana paid, casting turn, and whether Krang
stabilized or closed after resolving.
