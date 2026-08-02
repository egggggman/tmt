# Accepted Decisions

This document summarizes durable product and architecture decisions. Canonical definitions live in
the [Glossary](GLOSSARY.md); implementation status lives in [Architecture](ARCHITECTURE.md).

## Product decisions

1. **Sewer Deck terminology**  
   A Sewer Deck is a 60-card, Standard-legal TMNT-themed Magic deck. This is the canonical deck term.

2. **Standard-only Version 1**  
   Additional formats require evidence from a complete, working Standard path.

3. **Balance identity and strength**  
   A Sewer Deck should faithfully express its Character and Design Intent while remaining as strong
   and coherent as reasonably possible within Standard.

4. **Characters are multifaceted**  
   A Character may own multiple Design Intents without one overwriting another.

5. **Context-aware Recommendations**  
   Future Recommendations evaluate a specific Design Intent and Deck Version rather than cards only
   in isolation.

6. **Leonardo first**  
   Leonardo is the first end-to-end reference Character before broad expansion.

## Knowledge-model decisions

7. **Separate facts, mechanics, Capabilities, and themes**  
   Magic Facts are objective imports; mechanics are rules features; Capabilities describe gameplay
   function; themes and Design Intent interpret Character meaning.

8. **Hybrid Capability Engine**  
   Explicit rules derive Capabilities. Documented Overrides handle evidence-backed edge cases.

9. **Only curate what cannot be derived**  
   Human effort focuses on interpretation, Overrides, decisions, and evidenceâ€”not re-entering Magic
   Facts.

10. **Recommendations are computed**  
    Recommendation scores and explanations are reproducible intelligence, not canonical facts.

11. **Deck Analysis is computed**  
    Objective Deck Metrics and deterministic Findings are generated from a Deck Version. An earlier
    umbrella name for deck-wide analysis was superseded by the narrower v0.5.0 vocabulary; future
    Alignment and Recommendation layers remain separate responsibilities.

12. **Preserve evidence and interpretation separately**  
    Objective playtest observations and subjective design interpretation remain distinguishable.

## Engineering decisions

13. **Python** â€” use modern Python with type hints.
14. **SQLite** â€” SewerGraph uses SQLite for Version 1.
15. **uv project management** â€” dependencies and execution use uv and `pyproject.toml`.
16. **No ORM initially** â€” use `sqlite3` behind explicit services.
17. **CLI before GUI** â€” prove boundaries and workflows before graphical presentation.
18. **Immutable migrations** â€” released migrations are never rewritten.
19. **GitHub is canonical** â€” preserve durable project history in the repository and releases.
20. **Golden rule** â€” Store facts. Compute intelligence. Preserve decisions.

## Capability Engine decisions

21. **Oracle-level derivation** â€” Oracle Cards own Capabilities; Card Faces contribute Evidence.
22. **Replace derivations, preserve audit** â€” current computed results are atomically replaceable;
    Rule Set identity, source import, Evidence, outcomes, and Overrides remain durable.
23. **Confidence and Override precedence** â€” Confidence measures Evidence strength; rules combine by
    maximum; one active add/remove/adjust Override applies; conflicts are invalid.

## Deck Analysis Engine decisions

24. **Separate metrics from interpretation** â€” Deck Metrics precede Findings, and every Finding cites
    a named metric and exact threshold.
25. **Strict, source-linked analysis** â€” normal runs require exactly 60 Standard-legal cards,
    resolved Printings, and current Capability Provenance; diagnostic mode relaxes only deck size.
26. **Neutral outputs only** â€” current analysis does not perform Character judgment, Design Intent
    scoring, Recommendations, tuning, matchup prediction, or qualitative grading.

Future hard-to-reverse decisions should receive an ADR in `docs/adr/` when that directory is
introduced. No ADR files existed at this governance review.

