# Bad Guys — Shredder's Cronies Sandbox 0.2
## Controlled gameplay smoke — fail-closed preflight checkpoint

**Recommendation: SMOKE BLOCKED — Baseline 005 deck-identity mismatch**

No controlled smoke matrix was executed. Calibration remains blocked.

### Authorized inputs

| Input | Value |
|---|---|
| PR | #363, head `de266d95ccd25948c0b387575df81f51cd0ff7ec` |
| Semantic runtime | `c087f84bab4916b516ec6745f5a8e9f2a2d33f9117856bf959da4eb9a7be8e54` |
| Bad Guys candidate SHA-256 | `cacc77648a4d1659b8ae640d95ac2672694e6951553980246e6d001e5152bfb4` |
| Baseline 005 Bebop & Rocksteady SHA-256 | `aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed` |
| Pinned Scryfall snapshot SHA-256 | `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402` |
| Authorized schedule | 9 matchups × 20 games; balanced first-player assignments |
| Games in valid smoke matrix | **0** |

Candidate, Baseline 005 B&R, and the pinned snapshot authenticate correctly. The candidate remains 60 cards and differs from Baseline 005 only by −4 Zoo Escapees / +4 Foot Elite and −3 Putrid Pals / +3 Foot Mystic.

### Blocking discrepancy

The authenticated Baseline 005 manifest records these deck identities, but the corresponding source files at the authoritative PR #363 head have different SHA-256 bytes:

| Deck | Source path | Manifest SHA-256 | Current PR-head SHA-256 |
|---|---|---|---|
| Michelangelo | `decks/michelangelo/PROTOTYPE_0.1.txt` | `f5dd228b6e3636bd0de367b9d1a2bd836c0388bf37b00f0c0c047a932973ebf9` | `a35dfd61a87ec5377d7eda930afc22449d86bb2385b6d5e59d40e23211fe514f` |
| Splinter | `decks/splinter/PROTOTYPE_0.1.txt` | `74b6d7f4cab4bcda9eeb80ffc7a779529115c98c161345f13ac1251d85163b0a` | `a6c61786654f6d37c7b7ee779fdcb4252ee77d9d43a6e0160154831c204d8e42` |

GitHub file retrieval at the PR head confirms the same source identities, so this is not merely a local checkout problem. The smoke cannot proceed while the comparison deck identity is ambiguous.

### Preflight probe handling

Before the complete ten-deck identity audit finished, one exploratory single game was invoked to validate the runner shape: seed `50000`, candidate-first versus Raphael, winner Raphael, turn 12, result digest `90815aa18e877f5d0baa52f0c6fdd192e80865456dbb78e00ed26cfc492443cb`. It is **not part of the smoke matrix, not balance evidence, and not used for any result**. No replay or complete artifact was published for it; this checkpoint records the event so it cannot be mistaken for authorized smoke evidence.

No runtime error, illegal action, invalid payment, or replay mismatch was observed in that probe. It does not cure the deck-identity failure.

### Required recovery

HQ/Cardcade must first reconcile the two manifest identities with the authoritative deck bytes—either recover the exact historical source files or issue a provenance decision that explicitly supersedes those identities. No deck content, Baseline 005, R9-B evidence, or historical artifact was changed here.

**SMOKE BLOCKED — specific defect: Baseline 005 Michelangelo and Splinter deck hashes do not authenticate against their PR-head source files.**
