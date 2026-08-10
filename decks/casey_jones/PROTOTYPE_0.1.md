# Casey Jones Prototype 0.1

Status: **Playable beta prototype**

## Thesis

Casey grabs whatever gear is nearby and charges into trouble. His deck combines improvised
Equipment, artifact-producing Robots, risky card velocity, and oversized combat. Unlike Raphael's
team-pressure deck, Casey should feel like one scrappy vigilante turning junk into weapons.

## Decklist — 60 cards

### Creatures — 23

- 4 Casey Jones, Jury-Rig Justiciar
- 3 Casey Jones, Vigilante
- 3 Mutant Town Musicians
- 2 Null Group Biological Assets
- 4 Purple Dragon Punks
- 4 Ravenous Robots
- 3 Rock Soldiers

### Noncreature spells — 15

- 4 Hard-Won Jitte
- 4 Improvised Arsenal
- 3 Manhole Missile
- 2 Mouser Foundry
- 2 Spicy Oatmeal Pizza

### Lands — 22

- 22 Mountain

## Play pattern and baseline questions

Jury-Rig Justiciar finds gear, Purple Dragon Punks helps deploy or activate it, and Ravenous Robots
turn each artifact into another body. Casey's Vigilante incarnation borrows three cards before
random consequences arrive. Mutant Town Musicians turns artifact-Robot entries into pressure, while
Null Group Biological Assets exchanges awkward gear or duplicates.

Strict analysis rejected Commander-only **Casey Jones, Asphalt Hooligan** and **Casey Jones, Back
Alley Brute**. Failed Deck Version #9 is preserved; Prototype 0.1a replaces them with three **Mutant
Town Musicians** and two **Null Group Biological Assets**.

Test whether Equipment is exciting rather than cumbersome, whether the deck has enough creatures
to carry it, whether Vigilante's randomness is fun for both players, whether double strike creates
too many sudden kills, and whether Casey remains distinct from Raphael.

## Deck Analysis baseline

Normal run **#14** succeeded for immutable Deck Version **#10** using engine **2026.08.0**,
Scryfall import **#3**, and Capability run **#3**.

- 60 cards: 22 lands, 38 nonlands, 23 creatures, and 19 artifacts.
- Curve: 25 at MV 2, 10 at MV 3, and 3 at MV 4.
- Average nonland mana value: 2.42; median and mode: 2.
- Artifact synergy: 20 copies across 6 cards; Equipment synergy: 8 across 2 cards.
- Card draw: 8 copies; token creation: 6; threat density: 60.5%.
- The catalog reports zero interaction despite three Manhole Missiles. Treat removal quality,
  equipment density, and the absence of one-mana plays as table hypotheses.

Use [PROTOTYPE_0.1.txt](PROTOTYPE_0.1.txt) and [PLAYTEST_LOG.md](PLAYTEST_LOG.md) unchanged for the
first beta games.
