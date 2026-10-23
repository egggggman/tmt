# Bad Guys — Shredder's Cronies — sandbox candidate 0.2

**Status:** Exact 60-card proposal, independently unvalidated; not simulated, not promoted. 2026-10-21.

## Recovery provenance
The earlier black-green exploratory sandbox list was NOT recovered as an exact card-level artifact. Only aggregate claims (20 basic lands, 30 creatures, zero 1-mana spells, six 5–6 mana cards) survive in earlier design notes. Do not attribute this new candidate to that lost list.

Exact preserved baseline recovered: docs/objective-balance-lab/baselines/BEBOP_ROCKSTEADY_OBL_BASELINE_005.txt. **22 lands total**, including 10 Swamp, 10 Forest, 2 Illegitimate Business (Land). Earlier note calling it 20 total lands was incorrect. Preserve baseline bytes and PR #358 R9-B evidence.

## New candidate (60)
```text
Deck
2 Mutagen Man, Living Ooze
2 Frog Butler
4 Bebop & Rocksteady
4 Foot Elite
3 Ice Cream Kitty
3 Foot Mystic
2 Paramecia Coloniex
2 Bebop, Warthog Warrior
4 Rocksteady, Crash Courser
3 Cowabunga!
3 Stomped by the Foot
1 Tainted Treats
3 Mutant Chain Reaction
2 Illegitimate Business
2 Primordial Pachyderm
10 Swamp
10 Forest
```

**Diff from Baseline 005:** −4 Zoo Escapees / +4 Foot Elite; −3 Putrid Pals / +3 Foot Mystic. Everything else preserved. 60 cards, 26 creatures, 12 nonland noncreature spells, 22 lands (20 basic + 2 dual). This is a themed *candidate*, not a validated improvement. Compared to R9-B, Frog Butler/Stomped quantities also differ; use Baseline 005 as the explicit comparison control to avoid misleading attribution.

## Preliminary role and curve assessment
- Foot Elite: 3 MV, 2/4, attack trigger gives another friendly creature +1/+0 and indestructible. Black-green can pay the {W/B} hybrid using black. Standard legal in the 2026-10-21 public card record: https://mtg.wtf/card/tmt/146/Foot-Elite
- Foot Mystic: 4 MV, 2/4 lifelink, conditional disappear Ninja token on entry if friendly permanent left this turn. Standard legal: https://mtg.wtf/card/tmt/63/Foot-Mystic
- Foot Ninjas: 6 MV, Sneak, **not Standard legal** according to public record; EXCLUDED. https://mtg.wtf/card/tmt/147/Foot-Ninjas
- Two swapped slots have verified MV 3 and 4, but the **complete curve remains uncomputed** until all baseline card mana values are retrieved from authoritative snapshot. Never present guessed curve bins as measured.
- First-turn play risk remains a hypothesis. The candidate deliberately leaves land count unchanged so that first controlled experiment tests Foot synergy rather than mana changes.
- Roles: 26 creatures; Foot Elite supports attacking combat units; Foot Mystic supports recovery/board density when disappear is enabled; 3 Stomped by the Foot and 3 Mutant Chain Reaction are interaction candidates, not guarantees of executed semantics.

## Structural and engine gates
1. Resolve all 15 unique card identities and legality against current Oracle/Scryfall data. Recompute exact mana-value histogram, curve average, colors and land-source consistency; ensure all nonbasic lands count as lands.
2. Validate existing and newly introduced action fragments, especially Foot Elite's targeted attack trigger/indestructible and Foot Mystic's conditional ETB token, with deterministic engine tests and pilot targeting checks.
3. Independent audit must certify 60-card Standard legality, card provenance, simulator readiness, and frozen control identity.
4. Only then request HQ approval for a small isolated smoke test; do not automatically run 900 games or claim win-rate improvement.

## Design interpretation
Bebop & Rocksteady remain the face; Foot Elite represents organized Foot combat support, and Foot Mystic adds Foot bodies/lifelink. This changes thematic scope without absorbing Shredder's command/control or Krang's technology. No guarantee of improved balance; weak Splinter/Casey/Raphael matchups require diagnostics.

References: Issue #359, PR #358, PR #361, PR #363.
