# Accepted Decisions

This document summarizes the product and architecture decisions accepted before the v0.1.0 foundation freeze. Detailed decisions may also receive individual ADR files.

## Product decisions

1. **Sewer Deck terminology**  
   A Sewer Deck is a 60-card, Standard-legal TMNT-themed Magic deck. The project does not use Commander terminology for these decks.

2. **Standard-only Version 1**  
   Version 1 supports Standard only. Additional formats are future work and must be justified by experience with the working system.

3. **Balance identity and strength**  
   A Sewer Deck should faithfully express its Character and Design Intent while being as strong as reasonably possible within Standard.

4. **Characters are multifaceted**  
   A Character directly owns multiple Design Intents. Each Intent may produce a distinct, authentic playstyle without overwriting other interpretations.

5. **Context-aware recommendations**  
   Recommendations evaluate the current deck state rather than rating cards only in isolation.

6. **Leonardo first**  
   Leonardo is the reference implementation used to prove the architecture before expanding to the remaining Sewer Decks.

## Knowledge-model decisions

7. **Separate facts, mechanics, capabilities, and themes**  
   - Facts are imported objective data.
   - Mechanics are objective rules features.
   - Capabilities describe what a card accomplishes.
   - Themes describe what a TMNT Character or Design Intent values.

8. **Hybrid Capability Engine**  
   Capabilities are derived by explicit rules by default. Designers may add documented overrides for exceptional cases or evidence discovered during playtesting.

9. **Only curate what cannot be derived**  
   Human effort should focus on TMNT-specific interpretation, overrides, decisions, and evidence rather than re-entering objective Magic data.

10. **Recommendations are computed**  
    Recommendation scores and explanations are not canonical stored facts. They must be reproducible from current facts, intent, rules, and deck state.

11. **Deck Profiles are computed analysis**  
    Curve, theme coverage, capability balance, identity drift, and deck health are generated from a Deck Version.

12. **Preserve evidence and interpretation separately**  
    Objective playtest observations and subjective designer opinions must remain distinguishable.

## Engineering decisions

13. **Python**  
    The application uses modern Python with type hints.

14. **SQLite**  
    SewerGraph uses SQLite for Version 1.

15. **uv project management**  
    Dependencies and execution use `uv` and `pyproject.toml`.

16. **No ORM initially**  
    The first implementation uses `sqlite3` behind explicit repositories and services.

17. **CLI before GUI**  
    A working command-line interface proves the system and service boundaries before any graphical interface.

18. **Immutable migrations**  
    Released migrations are never rewritten. Changes use new ordered migrations.

19. **GitHub is canonical**  
    The repository is the durable project source, supported by local and release backups.

20. **Golden rule**  
    Store facts. Compute intelligence. Preserve decisions.


## Capability Engine decisions

21. **Oracle-level derivation**
    Oracle cards are Capability Engine analysis units; faces contribute attributed evidence.

22. **Replace derivations, preserve audit**
    Current derivations are atomically replaceable computed intelligence. Rule-set identity, source
    import, evidence, run outcomes, and explicit overrides form the durable audit trail.

23. **Confidence and override precedence**
    Confidence measures objective evidence strength only. Rules combine by maximum confidence.
    One active add, remove, or signed adjustment decision applies after derivation. Conflicts are
    invalid rather than implicit last-write-wins.

## Deck Analysis Engine decisions

24. **Separate metrics from interpretation**
    Objective Deck Metrics are computed first. Analysis statements are a second, deterministic
    layer whose named metric and exact threshold are persisted.

25. **Strict, source-linked analysis**
    Normal runs require exactly 60 Standard-legal cards, resolved printings, and a Capability run
    for the latest successful Scryfall import. Diagnostic mode relaxes only deck size.

26. **Neutral outputs only**
    Mana availability, density, redundancy, and relationships are facts. Character judgment,
    Design Intent scoring, recommendations, tuning, matchup prediction, and qualitative grades
    belong to later systems.
