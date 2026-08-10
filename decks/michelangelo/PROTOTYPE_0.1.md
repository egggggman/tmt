# Michelangelo Prototype 0.1

Status: **Playable prototype**

## Thesis

Michelangelo turns snacks, Mutagen, and spontaneous combat tricks into joyful momentum. The deck
should feel playful and surprising: attack, improvise, protect a friend, grow the team, and sometimes
find an outrageous pair of creatures with Michelangelo's Technique. It must still offer meaningful
counterplay rather than becoming an unstoppable counters snowball.

## Decklist — 60 cards

### Creatures — 22

- 4 Courier of Comestibles
- 4 Zoo Escapees
- 4 Michelangelo, Weirdness to 11
- 3 Slithering Cryptid
- 3 Michelangelo, Game Master
- 2 Michelangelo, Mutant BFF
- 2 Michelangelo, Improviser

### Noncreature spells — 16

- 3 Cowabunga!
- 3 Guac & Marshmallow Pizza
- 3 Saved by the Shell
- 3 Tenderize
- 2 Mutant Chain Reaction
- 2 Michelangelo's Technique

### Lands — 22

- 22 Forest

## Expected play pattern

Courier finds Pizza or brings Food; Zoo Escapees, Slithering Cryptid, and the Michelangelo cards generate Mutagen and
counter payoffs. Weirdness to 11 makes every counter event bigger. The Heart rewards attacking with
growth and snacks. Game Master turns used Food, Mutagen, or a Sneak return into personal momentum.

Guac & Marshmallow Pizza creates surprise wins in combat while remaining a Food. Saved by the Shell
protects a Turtle and creates counter synergy. Tenderize and Mutant Chain Reaction let the cheerful
deck interact instead of goldfishing. Mutant BFF helps a countered team push through, while
Improviser and Michelangelo's Technique provide the big improvisational turns.

## Baseline hypotheses

1. Does the deck feel joyful and surprising rather than like generic green counters?
2. Are Food and Mutagen meaningful choices or merely objects to track?
3. Does Weirdness to 11 snowball too quickly when unanswered?
4. Is Michelangelo's Technique exciting often enough with only 22 creatures?
5. Do the combat tricks create fun counterplay or frustrating blowouts?
6. Can the deck recover after spending its creatures and tokens?
7. Does legendary congestion interfere with the party?
8. Most importantly: does each game produce a memorable improvised Mikey moment?

The initial materialized candidate used three copies of **Michelangelo, the Heart**. Strict analysis
correctly rejected that card as non-Standard. The failed Deck Version is preserved as validation
evidence; Prototype 0.1a replaces those copies with **Slithering Cryptid**.

## Deck Analysis baseline

Normal analysis run **#11** succeeded for immutable Deck Version **#5** using Deck Analysis Engine
**2026.08.0**, Scryfall import **#3**, and Capability run **#3**.

- 60 cards: 22 lands, 38 nonlands, and 22 creatures.
- Curve: 6 at MV 1, 18 at MV 2, 8 at MV 3, 4 at MV 4, and 2 at MV 5.
- Average nonland mana value: 2.42; median and mode: 2.
- Token creation: 19 copies across 6 cards; card selection: 5 copies.
- Threat density: 57.9%.
- The engine recognizes no targeted removal, interaction, protection, or finisher. Tenderize, Mutant
  Chain Reaction, and Saved by the Shell make those catalog gaps explicit playtest hypotheses.
- Slithering Cryptid's hybrid `{G/U}` symbol creates a conservative blue-source warning even though
  every copy can be cast with green mana. No blue source is required for this list.

## Playtest readiness

Use [PROTOTYPE_0.1.txt](PROTOTYPE_0.1.txt) for digital import or physical pulling. Keep the first
3–5 games unchanged and record them in [PLAYTEST_LOG.md](PLAYTEST_LOG.md).
