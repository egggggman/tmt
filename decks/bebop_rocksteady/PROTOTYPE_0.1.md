# Bebop & Rocksteady Prototype 0.1

Status: **Playable beta candidate**

## Thesis

Bebop and Rocksteady are powerful together and terrible at resource management. They discard cards,
sacrifice whatever is nearby, smash through blockers, and somehow keep stumbling forward. The deck
should feel reckless, funny, and dangerous—not precise, controlling, or secretly optimal.

## Decklist — 60 cards

### Creatures — 24

- 2 Mutagen Man, Living Ooze
- 2 Frog Butler
- 4 Bebop & Rocksteady
- 4 Zoo Escapees
- 3 Ice Cream Kitty
- 3 Putrid Pals
- 2 Paramecia Coloniex
- 2 Bebop, Warthog Warrior
- 2 Rocksteady, Crash Courser

### Noncreature spells — 12

- 3 Cowabunga!
- 3 Stomped by the Foot
- 3 Tainted Treats
- 3 Mutant Chain Reaction

### Lands — 24

- 4 Illegitimate Business
- 10 Swamp
- 10 Forest

## Play pattern and baseline questions

Early creatures provide expendable bodies, Mutagen, and mana. The combined Bebop & Rocksteady demands a discard
or sacrifice every time it fights—an intentional test of whether reckless strength produces fun
decisions. Ice Cream Kitty converts spare tokens into cards, while Putrid Pals rewards resources
leaving. The five- and six-mana bruisers can cycle for lands when the draw is awkward.

Test whether the mana works, whether the duo's mandatory payment is funny or miserable, whether
discard/sacrifice decisions matter, whether cycling prevents expensive cards from clogging, whether
the partners snowball, and whether the deck provides both players adequate counterplay.

Strict analysis rejected Commander-only **Bebop, Skull & Crossbones** and **Rocksteady, Mutant
Marauder**. Failed Deck Version #13 is preserved. Prototype 0.1a replaces them with two **Mutagen
Man, Living Ooze** and two **Frog Butler** while keeping the combined duo as the centerpiece.

## Deck Analysis baseline

Normal run **#17** succeeded for immutable Deck Version **#14** using engine **2026.08.0**,
Scryfall import **#3**, and Capability run **#3**.

- 60 cards: 24 lands, 36 nonlands, and 24 creatures.
- Curve: 3 at MV 1, 16 at MV 2, 10 at MV 3, 3 at MV 4, 2 at MV 5, and 2 at MV 6.
- Average nonland mana value: 2.75; median and mode: 2.
- Token creation: 12 copies across 4 cards; sacrifice support: 10 across 3 cards.
- Threat density: 66.7%; interaction density: 8.3%.
- Both colors have 14 unrestricted land sources plus two Frog Butler fixing copies. Test the
  conservative black-source warning, tapped-land tempo, cycling decisions, and actual closing power.

Use [PROTOTYPE_0.1.txt](PROTOTYPE_0.1.txt) and [PLAYTEST_LOG.md](PLAYTEST_LOG.md) unchanged once strict
analysis accepts the list.
