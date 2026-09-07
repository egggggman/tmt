# Post-Action #24 Stage #002 Remeasurement

Baseline: `ba9eddaa5dabdfdabdd4a76aea10190527387bca`

This evidence-only run used `scripts/run_acceptance_stage_002.py --execute` with the frozen 16-game / 32-execution matrix (seeds 7201/7202, 7211/7212, 7221/7222, and 7231/7232; both orientations; duplicate executions).

The run produced **11 REACHED / UNSUPPORTED occurrences across 7 semantics**. Duplicate executions were byte-equivalent; invariant violations and runner stops were both zero. The raw JSON SHA-256 is `3c4ed1b42d139464c7af7b896e6f1380efcfc87287136f235cbf56752ffc8c21`.

Ray Fillet, Man Ray cleared from REACHED / UNSUPPORTED: its prior 4 occurrences across 4 games and 2 matchups are now represented as 4 EXECUTED occurrences across those games/matchups. The existing runner does not emit solo-clearance opportunities for this fresh artifact; the prior inventory recorded one.

Fresh ranking by occurrence count:

1. **Casey Jones, Jury-Rig Justiciar** — 3 occurrence(s), 3 game(s), 1 matchup(s).
   `When Casey Jones enters, look at the top four cards of your library. You may reveal an artifact card from among them and put it into your hand. Put the rest on the bottom of your library in a random order.`
2. **Casey Jones, Vigilante** — 2 occurrence(s), 2 game(s), 1 matchup(s).
   `When Casey Jones enters, draw three cards. At the beginning of your next upkeep, discard three cards at random.`
3. **Donatello, Way with Machines** — 2 occurrence(s), 2 game(s), 1 matchup(s).
   `Whenever an artifact you control enters, put a +1/+1 counter on Donatello.`
4. **Courier of Comestibles** — 1 occurrence(s), 1 game(s), 1 matchup(s).
   `When this creature enters, you may search your library for a Food card, reveal it, put it into your hand, then shuffle. If you don't put a card into your hand this way, create a Food token. (It's an artifact with "{2}, {T}, Sacrifice this token: You gain 3 life.")`
5. **Shredder, Unrelenting** — 1 occurrence(s), 1 game(s), 1 matchup(s).
   `Whenever Shredder enters or attacks, another target creature you control gains deathtouch until end of turn.`
6. **Stockman, Mad Fly-entist** — 1 occurrence(s), 1 game(s), 1 matchup(s).
   `When Stockman enters, draw a card, then discard a card.`
7. **Zoo Escapees** — 1 occurrence(s), 1 game(s), 1 matchup(s).
   `When this creature leaves the battlefield, create a Mutagen token. (It's an artifact with "{1}, {T}, Sacrifice this token: Put a +1/+1 counter on target creature. Activate only as a sorcery.")`

This ranking is implementation-priority evidence only. It does not make balance, win-rate, or clearance claims and does not authorize Action #25. No foundational simulator blocker was observed.
