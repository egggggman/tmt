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
