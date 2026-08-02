# Deck Analysis Engine

## Contract and provenance

The engine answers objective questions about one immutable Deck Version. A normal run requires a
60-card main deck, Standard legality, normal copy limits (including basic-land and Oracle-text
exceptions), at least one resolved printing per Oracle card, the latest successful Scryfall import,
and a successful Capability derivation over that same import. Diagnostic mode relaxes only the
60-card requirement and records a warning.

Every run records the Deck Version and canonical deck checksum, Scryfall import and checksum,
Capability run and rule-set checksum, and Deck Analysis engine version and checksum. Metrics,
findings, relationships, and the current pointer commit together. A failed run retains its error but
cannot expose partial results or replace the prior current pointer.

## Metrics layer

Counts are main-deck copy counts unless called unique. The engine reports total and unique Oracle
cards; land/nonland and non-exclusive card-type counts; a copy-weighted nonland mana-value histogram,
average, and median; colored mana symbols by copy; and land production by color split into
unrestricted, conditional, and restricted sources. Hybrid symbols count once for every represented
color. Nonland fixing and ramp copies remain separate from land sources.

For each of the 20 canonical Capabilities, the engine reports raw copy count, unique Oracle-card
count, and `sum(copy quantity × effective confidence)`. These values remain separate. Interaction
density is nonland copies with targeted removal, board wipe, protection, counterspell, graveyard
interaction, or tempo divided by nonland count. Threat density uses Creature, Planeswalker, Battle,
or finisher copies. Finisher density uses finisher copies. Land and creature ratios divide their
counts by total cards. Duplicate groups are Oracle identities with multiple copies; redundancy groups
are Capabilities represented by multiple unique Oracle cards.

## Analysis layer

The initial `2026.08.0` engine emits only these deterministic statements:

- every modal mana-value bin is reported when bins tie for the maximum;
- a color warning occurs when colored pips exceed unrestricted land sources of that color;
- zero board-wipe copies produces a warning;
- targeted-removal count, finisher count, and creature ratio are informational observations.

Each statement persists its severity, rule key, source metric, message, and literal threshold. The
minimal relationship rules expose Artifact with artifact synergy, Equipment with equipment synergy,
token creation with sacrifice support, and graveyard interaction with recursion only when both facts
exist, including the contributing Oracle IDs. Co-occurrence is not a claim of quality or combo value.

## Known limitations

Mana production is intentionally conservative. It recognizes basic land subtypes, explicit
`Add {W/U/B/R/G}` clauses, and “one mana of any color,” then flags common restriction language. It
does not simulate sequencing, probability, modal choices, cost reducers, treasure timing, land faces,
or arbitrary rules interactions. Deck entries attach to Oracle identities, so the engine can verify
that a printing exists but cannot preserve a user-selected printing.

The engine contains no Character or Design Intent judgment, Deck Profile/theme scoring,
recommendations, add/cut guidance, matchup prediction, tuning, deck-health grade, or AI heuristic.
