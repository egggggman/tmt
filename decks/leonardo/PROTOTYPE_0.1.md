# Leonardo Prototype 0.1

Status: **Playable prototype**

Design contract: RFC 006 — Design Intent

## Prototype thesis

Leonardo should feel like a disciplined field leader. The deck develops a small coordinated team, creates deliberate attacks, repositions creatures through Sneak, protects key pieces, and converts preparation into a decisive combat step.

This is intentionally a **playtest artifact**, not a claim of optimal construction. It exists to generate useful table evidence.

## Decklist — 60 cards

### Creatures — 24

- 4 Prehistoric Pet
- 3 Leonardo, Leader in Blue
- 4 April O'Neil, Kunoichi Trainee
- 3 Leonardo, Cutting Edge
- 3 Lita, Little Orphan Amphibian
- 4 Leonardo, Big Brother
- 2 Leonardo, Sewer Samurai

### Noncreature spells — 15

- 2 Quintessential Katana
- 3 Leader's Talent
- 2 Hamato Guardian Stance
- 3 Make Your Move
- 2 The Last Ronin's Technique
- 2 Leonardo's Technique
- 1 Mighty Mutanimals

### Lands — 22

- 22 Plains

## Why these cards

### Sneak and tactical repositioning

**Prehistoric Pet** is the prototype's quiet enabler. It can attack into larger boards because creatures with greater power cannot block it, making it a natural creature to return for a Sneak cost. Its activated ability also lets us deliberately return another creature to hand during our turn.

The four Leonardo identities create different tactical payoffs without requiring a splash:

- **Leonardo, Leader in Blue** is an efficient early attacker and a late surprise team pump when cast for Sneak.
- **Leonardo, Cutting Edge** rewards the life-gain subtheme and can enter through Sneak for one white mana.
- **Leonardo, Big Brother** rewards building a team and can likewise Sneak in cheaply after blockers.
- **Leonardo, Sewer Samurai** is the higher-end leader: double strike plus the ability to recover small creatures from the graveyard during our turn.

The intended feel is not "play the same legendary creature repeatedly." The different Leonardo cards represent different tactical expressions of the same character and can coexist because they have different card names.

### Sequencing matters

**April O'Neil, Kunoichi Trainee** gives the deck inexpensive card selection and attacks through many large blockers. Returning April to pay a Sneak cost creates a real choice: keep the attacker, or trade current board presence for another tactical entry and replay April later for another scry 2.

**Lita, Little Orphan Amphibian** rewards sequencing creature entries. Her Alliance modes create small but meaningful decisions between development, life/counter support, and card selection.

**Leader's Talent** may be the prototype's most important glue card. It rewards attacking, then later rewards countered creatures leaving the battlefield—the exact event Sneak asks us to perform. Its final level turns later spellcasting into team-wide development.

### Protection and disciplined interaction

**Hamato Guardian Stance** is a deliberately small protection/combat tool. It also scries, reinforcing the "plan the next move" feel.

**Make Your Move** gives flexible answers without turning the deck into removal-heavy control.

### Team payoffs and recovery

**The Last Ronin's Technique** can be a normal token-maker or a Sneak-speed combat reinforcement. Three bodies also increase Leonardo, Big Brother's pressure and trigger Alliance.

**Leonardo's Technique** rebuilds after trades or removal and can itself be cast for Sneak, rewarding the deck for playing a real interactive game instead of protecting one irreplaceable threat.

**Mighty Mutanimals** is a one-copy prototype test for a heavier team-development payoff. Its ETB creates another creature and its Alliance trigger spreads counters across the squad.

### Equipment / life loop

**Quintessential Katana** automatically attaches when a Ninja enters, making the many Ninja creatures and Sneak entries feel connected to Leonardo's signature weapon. Its combat-damage life gain can grow Leonardo, Cutting Edge and gives the deck some staying power without making lifegain the primary strategy.

## Expected play pattern

### Early game

Establish one- and two-mana attackers, especially Prehistoric Pet, Leonardo, Leader in Blue, April, Cutting Edge, or Lita. Use Leader's Talent when there is room to invest without losing tempo.

### Midgame

Attack to create information. Once blocks are declared, decide whether an unblocked creature is more valuable staying in combat or returning to hand to enable a Sneak card. Replaying returned ETB creatures later should create the feeling of repositioning the team rather than simply losing tempo.

Use Make Your Move and Hamato Guardian Stance to keep combat interactive rather than trying to race blindly.

### Closing game

A developed board can finish through Leonardo, Big Brother's scaling power, a Sneak-cast Leonardo, Leader in Blue team pump, The Last Ronin's Technique adding surprise attackers, or accumulated Leader's Talent / Alliance counters.

## Prototype questions

Playtesting should answer these before large structural changes:

1. Does Sneak actually feel tactical, or does returning an attacker feel like an annoying tax?
2. Does the deck produce enough unblocked attackers to make Sneak reliable without becoming evasive solitaire?
3. Is Leader's Talent fun glue or too slow / snowbally?
4. Does having several different Leonardo cards make the deck feel *more* like Leonardo or merely repetitive?
5. Does Quintessential Katana create satisfying signature-weapon moments without consuming too much tempo?
6. Does Leonardo, Sewer Samurai's graveyard recursion matter often enough to justify the four-mana slot?
7. Are 22 Plains enough when several cards have four-mana normal costs but cheaper Sneak costs?
8. Is the deck interactive enough to be fun across the future battle box without becoming a generic white midrange deck?
9. Is there enough comeback potential after a sweeper or multiple removal spells?
10. Most important: after a game, can the pilot describe a moment that felt specifically like **Leonardo leading a team**?

## Initial risk register

### Risk: legendary congestion

Multiple copies of four Leonardo legends plus Lita and April may produce duplicate dead cards. This is intentional in 0.1 because Sneak and return-to-hand effects may mitigate the problem, but duplicate friction should be recorded explicitly.

### Risk: low raw card advantage

The deck has selection, recursion, and replay value but little straightforward draw. If it empties its hand too quickly, solve the observed problem before adding a generalized draw package.

### Risk: underpowered one-drops

Prehistoric Pet is included primarily for evasion/repositioning utility. If it does not create meaningful Sneak decisions, it should not survive merely because it fits the theory.

### Risk: mana count

22 lands is a purposeful starting point for a low-curve mono-white deck with alternate Sneak costs. Record missed land drops and stranded four-mana spells before changing the count.

## Legality and scope

Prototype 0.1 uses only cards from **Magic: The Gathering | Teenage Mutant Ninja Turtles (TMT)** plus basic Plains. TMT is currently legal in Standard. The main deck contains exactly 60 cards and uses no more than four copies of any nonbasic card.

No TMC-only Turtle Team-Up / Commander card is used, because those new-to-Magic cards are not Standard-legal merely by appearing in the TMNT product line.

## Deck Analysis baseline

Analyzed as immutable Deck Version **#1** with Deck Analysis Engine **2026.08.0**, Scryfall import
**#3**, and Capability run **#3**. The normal (non-diagnostic) run succeeded, confirming the exact
60-card main deck passed the engine's structural, copy-limit, resolved-printing, Standard-legality,
and current-provenance preconditions.

### Structure and curve

- 60 cards: 22 lands and 38 nonlands.
- 24 creature cards (40.0% of the deck); the earlier section label of 23 was corrected because
  Mighty Mutanimals is also a Creature.
- Nonland mana values: 11 at MV 1, 13 at MV 2, 7 at MV 3, and 7 at MV 4.
- Average nonland mana value: 2.26; median: 2; modal value: 2.
- 22 unrestricted white sources for 39 white mana symbols. The engine reports its conservative
  `mana.shortfall.w` warning; treat this as a sequencing/missed-land-drop playtest hypothesis, not a
  verdict, because pip count is not a castability simulation.

### Capability findings

- Card selection: 9 copies across 3 cards.
- Token creation: 6 copies across 3 cards.
- Life gain: 5 copies across 2 cards.
- Evasion: 4 copies; targeted removal: 3 copies; combat support: 3 copies; equipment synergy: 2
  copies.
- Interaction density: 7.9% of nonlands; threat density: 63.2% of nonlands.
- The engine classifies 0 protection, 0 recursion, 0 finishers, and 0 board wipes. These objective
  rule outputs expose gaps between authored intent language and the current Capability catalog;
  they do not prove the play patterns are absent. Test protection, recovery, and closing power at
  the table before changing either cards or rules.

The run also found one artifact/equipment-synergy relationship. No Alignment or Recommendation
judgment was performed.

## Next step

Sleeve or import this exact list and play it unchanged for 3–5 games. A plain-text digital import
list and physical pull checklist are available in
[PROTOTYPE_0.1.txt](PROTOTYPE_0.1.txt). The existing Deck Analysis Engine has completed its normal
validation path; no Alignment or Recommendation result is required.

For physical play, pull the quantities in the text list, verify 60 cards with no sideboard, and
sleeve it as a fixed snapshot. For digital play, import the text list directly; it contains only the
deck-import lines and no annotations.

Use [PLAYTEST_LOG.md](PLAYTEST_LOG.md) for the first games. Preserve this list as Prototype 0.1;
changes informed by play become a new Deck Version.

Do **not** build Alignment or Recommendations first.
