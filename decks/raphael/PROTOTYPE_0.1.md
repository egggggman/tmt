# Raphael Prototype 0.1

Status: **Playable prototype**

Design direction: the first contrast test for RFC 006. Raphael is impulsive, confrontational, resilient through momentum, and willing to turn cards and creatures into immediate pressure. This is a playtest artifact, not a tournament claim.

## Decklist — 60 cards

### Creatures — 24

- 4 Casey Jones, Jury-Rig Justiciar
- 4 Raphael, Tough Turtle
- 4 Wingnut, Bat on the Belfry
- 3 Mutant Town Musicians
- 3 Null Group Biological Assets
- 2 Raphael, Most Attitude
- 2 Raphael, Ninja Destroyer
- 2 Raphael, the Nightwatcher

### Noncreature spells — 14

- 2 Skateboard
- 3 Cool but Rude
- 4 Manhole Missile
- 3 Mouser Attack!
- 2 Raphael's Technique

### Lands — 22

- 22 Mountain

## Intent and play pattern

Raphael should establish a two-drop, attack early, and make combat uncomfortable. Tough Turtle turns every follow-up creature into damage; Wingnut and Mutant Town Musicians reward committing more bodies; Manhole Missile clears a blocker; Mouser Attack! is either another Alliance trigger or a reckless combat boost. Cool but Rude and Null Group Biological Assets turn excess or awkward cards into fresh looks. Nightwatcher is the signature burst: return an unblocked attacker and give the attacking team double strike. Raphael's Technique is an intentionally volatile reload when the hand is nearly empty.

Unlike Leonardo, this deck spends protection and long-term coordination for haste, menace, forced blocks, rummaging, and burst damage. The opponent can interact with its creatures, punish overextension, or stabilize behind efficient trades; the deck contains no lock or solitaire combo.

## Prototype questions and risks

1. Does Tough Turtle plus repeated creature entry feel like Raphael's pressure, or like generic Alliance math?
2. Does Nightwatcher create memorable all-in turns without ending too many games from nowhere?
3. Are 22 Mountains enough for eight normal four-mana Raphael copies, even with Sneak on Nightwatcher?
4. Is Raphael's Technique a satisfying empty-hand reload, or does symmetric draw-seven help the opponent too often?
5. Does legendary congestion strand Raphael copies?
6. Does the deck fold too sharply after its first wave is answered?
7. Most importantly, does the pilot get a moment that feels like Raphael choosing confrontation over caution?

## Deck Analysis baseline

Analyzed as immutable Deck Version **#2** with Deck Analysis Engine **2026.08.0**, Scryfall import
**#3**, and Capability run **#3**. Normal analysis run **#9** succeeded, confirming the exact
60-card main deck passed structural, copy-limit, resolved-printing, Standard-legality, and
provenance checks.

- 60 cards: 22 lands and 38 nonlands; 24 creatures.
- Nonland mana values: 2 at MV 1, 22 at MV 2, 6 at MV 3, 6 at MV 4, and 2 at MV 6.
- Average nonland mana value: 2.63; median and mode: 2.
- Card draw: 10 copies across 3 cards; card selection: 4 copies.
- Artifact synergy: 4 copies; token creation: 3; equipment synergy: 2; evasion: 2; finishers: 2.
- Threat density: 63.2% of nonlands.

The engine reports 42 red pips against 22 unrestricted red sources, no board wipe, and zero
recognized targeted removal or interaction. Treat these as hypotheses: specifically track missed
land drops, stranded four- and six-mana cards, and whether Manhole Missile supplies useful removal
despite the current Capability result.

## Playtest readiness

Use [PROTOTYPE_0.1.txt](PROTOTYPE_0.1.txt) for digital import or as a physical pull list. Play the
list unchanged for the first 3–5 games and record observations in
[PLAYTEST_LOG.md](PLAYTEST_LOG.md). Changes become Prototype 0.2 rather than silently rewriting this
snapshot.
