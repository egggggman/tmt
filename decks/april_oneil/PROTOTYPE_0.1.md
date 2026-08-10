# April O'Neil Prototype 0.1

Status: **Playable beta prototype**

## Thesis

April gets the story by entering danger, observing what changes, and adapting faster than anyone
else. This mono-blue tempo deck mixes creatures, artifacts, instants, and enchantments so that
investigation feels active rather than passive. April should reveal information and improvise—not
duplicate Donatello's artifact construction engine.

## Decklist — 60 cards

### Creatures — 22

- 4 Fugitive Droid
- 4 Buzz Bots
- 4 Crustacean Commando
- 3 April, Reporter of the Weird
- 3 Utrom Scientists
- 2 April O'Neil, Hacktivist
- 2 Ray Fillet, Man Ray

### Noncreature spells — 16

- 4 Sewer-veillance Cam
- 3 Negate
- 3 Mind Transfer Protocol
- 2 Bespoke Bō
- 2 Retro-Mutation
- 2 Return to the Sewers

### Lands — 22

- 22 Island

## Play pattern and hypotheses

Deploy an evasive or replaceable observer, use Cam and Utrom Scientists to manipulate combat, and
clear a route for Reporter of the Weird. Mind Transfer Protocol changes the facts mid-scene;
Retro-Mutation and Return to the Sewers answer dangerous subjects without hard-locking the game.
Hacktivist rewards reporting across card types, while Ray Fillet creates Mutagen and converts
accumulated counters into more cards.

The first materialized candidate used two copies of **April O'Neil, Human Element**. Strict analysis
rejected that Commander-only printing. Failed Deck Version #7 is preserved; Standard-legal
Prototype 0.1a uses **Ray Fillet, Man Ray** instead.

Test whether Reporter connects often enough, whether Hacktivist rewards interesting sequencing,
whether 22 Islands support the four-mana Aprils, whether the deck is fun to face, and—most
importantly—whether it feels like April pursuing a story rather than Donatello building machines.

## Deck Analysis baseline

Normal run **#13** succeeded for immutable Deck Version **#8** using engine **2026.08.0**, Scryfall
import **#3**, and Capability run **#3**.

- 60 cards: 22 lands, 38 nonlands, 22 creatures, and 17 artifacts.
- Curve: 8 at MV 1, 11 at MV 2, 13 at MV 3, and 6 at MV 4.
- Average nonland mana value: 2.45; median: 2.5; mode: 3.
- Card draw: 18 copies across 6 cards; evasion: 10; token creation: 8.
- Interaction density: 10.5%; threat density: 57.9%.
- The catalog reports no targeted removal despite Retro-Mutation and Return to the Sewers. Test
  actual answer quality and closing power rather than treating the classification as a verdict.

Use [PROTOTYPE_0.1.txt](PROTOTYPE_0.1.txt) and [PLAYTEST_LOG.md](PLAYTEST_LOG.md) for unchanged beta
games.
