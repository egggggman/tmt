# Issue #289 — top-library creature-selection checkpoint

Stack: draft PR #317 (`55c89da648a80562d44f44009ec0fca36cef3dcb`) → this checkpoint. Baseline 005, the original 172-row ledger, every earlier overlay, and historical games are unchanged.

## Intervention choice

| Family | Frozen copies / remaining critical rows | Identity impact | Implementation surface |
| --- | ---: | --- | --- |
| Michelangelo's Technique | 2 / 1 gap | A top-eight creature pair can create a substantial board at once. | Private top-card descriptions, combinatorial legal choice, fixed Sneak, deterministic bottom shuffle, and deferred entry triggers already exist. |
| Raphael, Most Attitude | 2 / 2 partial | Linked exile and later play enable repeated card access. | Remaining permissions span more casting families, timing, payment and independent linked objects. |

A complete generic Sorcery/Instant grammar requires the exact bounded effect and, if present, a complete fixed Sneak preface. The chooser sees only its own inspected card descriptions and receives enumerated legal zero-, one-, or two-creature choices with combined mana value at most six for the frozen card. Choice occurs on resolution, after casting and priority. Chosen cards enter with new battlefield identities, then all remaining inspected cards are randomized onto the library bottom. Entry triggers are enqueued after both selected cards enter; state-based actions and priority complete through the existing stack path. Unsupported or altered clauses fail closed.

Focused tests exercise normal payment, Sneak return/mana costs, optional choices, illegal or duplicate combinations, hidden inspection, chooser mutation rejection, zone identity, bottom order, entry triggers, zero-toughness state-based actions, countering, source provenance and exact replay. The Equipment trigger guard from #317 is retained; an additional test attaches and removes a real ability-suppressing Aura, checking granted combat triggers in both states.

Four authenticated frozen Baseline 005 diagnostics use Michelangelo versus Leonardo and Donatello, seed 317, with both starting positions and exact replays. Two normal Michelangelo's Technique payments and resolutions occur; no Sneak payment occurs naturally in this small sample. Focused deterministic fixtures prove the Sneak branch. See [machine diagnostic](ISSUE_289_TOP_CREATURE_SELECTION_SMOKE.json). These games do not support a balance conclusion.

## Coverage and gates

The [machine overlay](ISSUE_289_TOP_CREATURE_SELECTION_CHECKPOINT.json) checks the predecessor SHA-256 `43b4f0ca8e66a898a99a3d2e74d55f119884964e130a4c850365e6d3e7a550c8`, original ledger SHA-256 `56660440820f130bb5582cbe4b2aa46df983950aa0978a171ec7ee95cfe00100`, and frozen manifest SHA-256 `c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac` before regenerating all 172 rows. Critical entries go **3 → 2**, both partial Raphael linked-permission rows. The row-level audit also reconciles five stale important Sneak rows: Michelangelo's newly supported spell and four complete spells from earlier checkpoints (The Last Ronin's, Leonardo's, Raphael's and Splinter's Techniques). Each has a complete executable cast program, fully supported fixed Sneak semantics, no unsupported fragments, and focused normal/Sneak fixture coverage. The original ledger and older overlays retain their historical classifications. **56 important** gaps remain, down from 61; four of those five closures reflect earlier engine work, not additional behavior added here.

The remaining important work includes high-copy gameplay clauses: Leader's Talent counters and levels (four copies), Krang's artifact scaling (two), Rocksteady's blocking restriction (four), Ravenous Robots/Mouser Foundry artifact-token triggers (four each), and shared Ninja Teen level/recursion effects across Splinter and Shredder. The current severity label alone cannot certify a mechanically trustworthy ten-deck calibration.

Before semantic runtime: `5b3992c75837fbffee40d3eb641af9042b43505ec5e4eeab78c8334b7e9d8780`.
After semantic runtime: `7451f647b6d89b6fa6ee83c673aa29f6056cbadfe72f3e90ac9ab93c95299571`.

Checkpoint acceptance: **pending final-head CI**. Local focused tests: 37 passed. Full regression: 1,883 passed, 10 skipped. Structural Baseline 005 validation, Ruff check and format, authenticated four-game diagnostic with four exact deterministic replays, and diff check passed. Baseline 005 calibration readiness: **BLOCKED** by two partial critical rows and important deck-identity gaps. No 4,500-game control, deck revision, merge or promotion is authorized.
