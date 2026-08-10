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

7. **Playable first, explainable increasingly**
   Produce and play bounded deck prototypes as soon as current facts and analysis can support them.
   Design Intent targets remain hypotheses until playtest evidence challenges or supports them.
   Alignment, Recommendations, and a structured Playtesting Engine do not gate deck construction or
   lightweight playtest notes.

## Knowledge-model decisions

8. **Separate facts, mechanics, Capabilities, and themes**
   Magic Facts are objective imports; mechanics are rules features; Capabilities describe gameplay
   function; themes and Design Intent interpret Character meaning.

9. **Hybrid Capability Engine**
   Explicit rules derive Capabilities. Documented Overrides handle evidence-backed edge cases.

10. **Only curate what cannot be derived**
   Human effort focuses on interpretation, Overrides, decisions, and evidenceâ€”not re-entering Magic
   Facts.

11. **Recommendations are computed**
    Recommendation scores and explanations are reproducible intelligence, not canonical facts.

12. **Deck Analysis is computed**
    Objective Deck Metrics and deterministic Findings are generated from a Deck Version. An earlier
    umbrella name for deck-wide analysis was superseded by the narrower v0.5.0 vocabulary; future
    Alignment and Recommendation layers remain separate responsibilities.

13. **Preserve evidence and interpretation separately**
    Objective playtest observations and subjective design interpretation remain distinguishable.

## Engineering decisions

14. **Python** â€” use modern Python with type hints.
15. **SQLite** â€” SewerGraph uses SQLite for Version 1.
16. **uv project management** â€” dependencies and execution use uv and `pyproject.toml`.
17. **No ORM initially** â€” use `sqlite3` behind explicit services.
18. **CLI before GUI** â€” prove boundaries and workflows before graphical presentation.
19. **Immutable migrations** â€” released migrations are never rewritten.
20. **GitHub is canonical** â€” preserve durable project history in the repository and releases.
21. **Golden rule** â€” Store facts. Compute intelligence. Preserve decisions.

## Capability Engine decisions

22. **Oracle-level derivation** â€” Oracle Cards own Capabilities; Card Faces contribute Evidence.
23. **Replace derivations, preserve audit** â€” current computed results are atomically replaceable;
    Rule Set identity, source import, Evidence, outcomes, and Overrides remain durable.
24. **Confidence and Override precedence** â€” Confidence measures Evidence strength; rules combine by
    maximum; one active add/remove/adjust Override applies; conflicts are invalid.

## Deck Analysis Engine decisions

25. **Separate metrics from interpretation** â€” Deck Metrics precede Findings, and every Finding cites
    a named metric and exact threshold.
26. **Strict, source-linked analysis** â€” normal runs require exactly 60 Standard-legal cards,
    resolved Printings, and current Capability Provenance; diagnostic mode relaxes only deck size.
27. **Neutral outputs only** â€” current analysis does not perform Character judgment, Design Intent
    scoring, Recommendations, tuning, matchup prediction, or qualitative grading.

Future hard-to-reverse decisions should receive an ADR in `docs/adr/` when that directory is
introduced. No ADR files existed at this governance review.

