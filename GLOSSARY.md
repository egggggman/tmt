# Glossary

## Project-wide terms

**TMNT Design Studio**  
The complete knowledge-driven system used to design, document, analyze, playtest, and preserve TMNT-themed Magic decks.

**Sewer Deck**  
A 60-card, Standard-legal Magic deck built to express a TMNT Character through a specific Design Intent while remaining as competitively strong and cohesive as reasonably possible.

**SewerGraph**  
The SQLite knowledge database used by TMNT Design Studio.

**Character**  
The TMNT person, ally, villain, team, or faction represented by one or more Design Intents.

**Design Intent**  
A stored, human-authored interpretation of a Character. It defines the intended gameplay identity, themes, capability priorities, experience goals, strengths, and accepted weaknesses for a Sewer Deck.

**Deck Version**  
An immutable historical snapshot of a Sewer Deck at a particular point in its development.

**Magic Fact**  
Objective card information imported from Scryfall, such as name, mana cost, Oracle text, card types, keywords, and legality.

**Mechanic**  
An objective rules feature of a card, such as Flying, Vigilance, Ward, or Flash.

**Capability**  
A gameplay function derived from card facts and mechanics, such as Card Draw, Spot Removal, Protection, Token Generation, or Mana Fixing.

**Capability Rule**  
An explainable, testable rule used to derive a Capability from objective card data.

**Capability Override**  
A documented designer addition, removal, or adjustment to a derived Capability. Overrides are exceptions and must include a rationale and history.

**Theme**  
A curated narrative or character concept, such as Leadership, Brotherhood, Honor, Discipline, Technology, or Mutation.

**Theme-to-Capability Mapping**  
The stored relationship explaining which gameplay Capabilities express a Theme and how strongly they support it.

**Deck Profile**  
Computed analysis of a current deck state, including mana curve, capability totals, theme coverage, synergy, interaction density, and deck health. It is analysis, not canonical stored truth.

**Context-Aware Recommendation**  
A recommendation calculated for a specific Design Intent and current deck state. It considers character fit, deck synergy, missing capabilities, curve needs, theme coverage, legality, and evidence.

**Card Dossier**  
A human-readable presentation of everything the system knows about a card: facts, mechanics, capabilities, overrides, theme matches, notes, deck use, playtesting, and recommendations.

**Character Dossier**  
A human-readable presentation of a Character and its Design Intents, current decks, priorities, history, and findings.

**Design Note**  
A human-authored observation, opinion, strategy note, reminder, or playtest interpretation.

**Design Decision**  
A durable record of an important project or deck-design choice, including its rationale and status.

**Playtest Observation**  
Recorded evidence or feedback from testing a specific Deck Version.

## Encyclopedia-specific legacy terms

**Core Truth**  
A foundational design principle used in editorial analysis.

**Design Echo**  
A mechanic or theme reinforcing a larger design idea.

**Character Suite**  
An Encyclopedia presentation compiling analysis about a TMNT character. This is an editorial output, not the database entity that drives Sewer Deck construction.
