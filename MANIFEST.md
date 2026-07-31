# TMNT Design Studio Manifest

## Mission

Build and preserve a knowledge-driven system for designing Standard-legal TMNT-themed Magic: The Gathering Sewer Decks. The system should help designers create cohesive decks that express a chosen Character and Design Intent while remaining as strong as reasonably possible within Standard.

## Core principles

1. **GitHub is the canonical source.**
2. **Preserve everything important.** Important knowledge should not depend on one chat, device, or memory.
3. **Separate facts, intent, analysis, and presentation.**
4. **Store facts. Compute intelligence. Preserve decisions.**
5. **One source of truth.** Every fact or decision should have one canonical home.
6. **Every recommendation must be explainable.**
7. **Recommendations are context-aware.** Improve the current Sewer Deck, not an imaginary generic deck.
8. **Standard first.** Version 1 proves one format well before considering expansion.
9. **Automate what can be derived; curate what requires judgment.**
10. **Allow documented designer overrides.** Flexibility is permitted, but every exception needs a reason and history.
11. **Balance identity and strength.** Never erase a Character to gain a small competitive advantage, and do not accept needless weakness when an equally thematic stronger option exists.
12. **Decks evolve through evidence.** Preserve Deck Versions, design decisions, and playtest observations.
13. **Quality over quantity.** Leonardo is the first reference implementation; expansion follows proof.
14. **Build for the long term.** Standard rotations should replace card pools without destroying design knowledge.

## Design hierarchy

```text
Character
└── Design Intent
    └── Sewer Deck
        └── Deck Version
```

Characters are multifaceted. A Character can directly own multiple Design Intents, each representing an authentic but distinct gameplay interpretation.
