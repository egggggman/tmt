# Bad Guys — Shredder's Cronies Sandbox 0.2
## Consolidated engine-readiness audit (accepted C10 runtime)

This audit is a new C10-era authority record. Earlier A/B and C1–C10 packet reports remain historical evidence and are not rewritten.

**Recommendation: READY FOR HQ GAMEPLAY AUTHORIZATION**

This recommendation authorizes no gameplay by itself. HQ retains the separate authorization gate.

## Authenticated inputs

| Item | Identity |
|---|---|
| Semantic runtime | `c087f84bab4916b516ec6745f5a8e9f2a2d33f9117856bf959da4eb9a7be8e54` |
| Candidate file SHA-256 | `cacc77648a4d1659b8ae640d95ac2672694e6951553980246e6d001e5152bfb4` |
| Baseline 005 file SHA-256 | `aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed` |
| Pinned Scryfall snapshot SHA-256 | `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402` |
| Gameplay simulations | **None run** |

The candidate list parses to 60 cards: 28 creatures, 10 noncreature/nonland spells, and 22 lands (20 basics plus 2 Illegitimate Business). Its exact list differs from Baseline 005 only by −4 Zoo Escapees / +4 Foot Elite and −3 Putrid Pals / +3 Foot Mystic. Baseline 005, R9-B, and all historical simulation evidence were not modified.

The candidate document contains stale descriptive prose saying “26 creatures” and “12 nonland noncreature spells.” That is documentation drift, not a list-byte or engine-input discrepancy; the fenced deck block and authenticated hash are authoritative. It should be corrected in a future documentation-only change, not by changing the candidate.

## Recomputed curve and snapshot authentication

All 17 unique candidate identities resolve against the pinned snapshot and are Standard-legal. The exact mana-value histogram for all 60 cards is:

| MV | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| Count | 22 | 3 | 12 | 12 | 5 | 2 | 4 |

The all-card mean mana value is **1.95**; among the 38 nonland cards it is **2.925**. The 2 Illegitimate Business cards are lands and count as lands, not nonland spells.

## Card-by-card Oracle-to-engine coverage

| Card | Required behavior | Engine evidence | Classification | Gameplay impact of any residual |
|---|---|---|---|---|
| Mutagen Man, Living Ooze | X casting; X Mutagen ETB; trample; artifact-token activation discount | C3/C10 tests; generic trample coverage | Supported | None identified in printed candidate clauses |
| Frog Butler | Deathtouch; tap mana; temporary reach | `test_frog_butler_mana.py`, `test_frog_butler_reach.py`; combat tests | Partial (intrinsic keyword audit label) | Low; intrinsic combat keyword evidence is narrower than the activated/reach evidence |
| Bebop & Rocksteady | Attack/block sacrifice-or-discard obligation | C2 focused tests and full regression | Supported | None identified |
| Foot Elite | Attack trigger, another creature, +1/+0 and indestructible EOT | `test_bad_guys_work_packets.py` and focused packet tests | Supported | None identified |
| Ice Cream Kitty | Sorcery sacrifice/draw; Food sacrifice/life gain | C2-era activation/sacrifice regressions | Supported | None identified |
| Foot Mystic | Lifelink; conditional Disappear ETB Ninja token | `test_bad_guys_work_packets.py`, lifelink/Disappear regressions | Supported | None identified |
| Paramecia Coloniex | Mill-three ETB; dies/exile; target graveyard creature to library top | `test_paramecia_death_reflexive_return.py`, mill tests | Supported | None identified |
| Bebop, Warthog Warrior | Menace; Rhino menace grant; Swampcycling | C9 menace/grant tests; landcycling tests | Supported | None identified |
| Rocksteady, Crash Courser | At-most-one blocker restrictions; Boar restriction; Forestcycling | C1 and landcycling tests | Supported | None identified |
| Cowabunga! | Top-four hidden-zone selection; reveal eligible card; random bottom order | C7 hidden-zone tests | Supported | None identified |
| Stomped by the Foot | Optional kicker sacrifice; -2/-2 or -5/-5 EOT | C4 kicker/removal tests | Supported | None identified |
| Tainted Treats | Destroy artifact/creature; MV-gated Food | C6 conditional-Food tests | Supported | None identified |
| Mutant Chain Reaction | Optional legal removal; Mutagen creation and ordering | C5 compound-resolution tests | Supported | None identified |
| Illegitimate Business | Tapped land entry; ETB life; B/G mana | land-entry, life-gain, and ordinary land-play regression coverage | Partial (ordinary land-entry audit label) | Low; no candidate-specific unresolved interaction found |
| Primordial Pachyderm | Reach, trample, ETB gain 2 | `test_etb_self_life_gain_readiness.py`, flying/trample tests | Supported | None identified |
| Swamp | Ordinary basic land play and B mana | engine land-play/resource regressions | Supported | None identified |
| Forest | Ordinary basic land play and G mana | engine land-play/resource regressions | Supported | None identified |

The conservative partial labels are retained rather than silently erased: intrinsic deathtouch/trample/reach and ordinary land-entry are exercised by deterministic tests, but the audit ledger’s dedicated card-fragment accounting does not provide the same packet-level proof record for every intrinsic/ordinary clause. They are not currently critical blockers for this candidate because the relevant combat, reach, trample, ETB-life, land-play, and mana paths execute and replay deterministically.

## Cross-mechanic acceptance

The acceptance set combines the packet fixtures with the full regression and includes opening/resource progression, casting and legal-action generation, activated costs, trigger ordering, combat/block legality, state-based actions, token creation/sacrifice, death/exile/graveyard movement, hidden-zone ordering, controller/object identity, terminal outcomes, and deterministic replay. Relevant interaction fixtures include:

- C3 X announcement/payment → token entry → C10 artifact-token activation discount.
- C9 menace grants → C1 maximum-blocker restrictions.
- C2 combat obligation → sacrifice/discard zone/resource accounting.
- C4 kicker payment → resolution-time target legality → lethal SBA/cleanup.
- C5 optional removal → Mutagen entry and simultaneous-lethal handling.
- C6 conditional removal → Food creation.
- C7 hidden selection → deterministic randomized bottom ordering.
- C8 departure/recursion → source-independent trigger provenance.

No illegal action generation, invalid resource payment, unsupported silent execution, card/deck-name dispatch in the C10 intervention, unexplained terminal outcome, or nondeterministic replay was observed in this audit.

## Regression and skipped-test accounting

Current final-head validation: **1,690 passed, 10 skipped**. Ruff format/check and structural validation passed. The ten skips are:

- 1 Windows-only PowerShell-sharing test.
- 1 archived terminal-frame test requiring the Aura runtime.
- 7 archived R6-C evidence tests requiring the Aura runtime.
- 1 opt-in live Scryfall smoke test.

These skips do not cover the Bad Guys candidate or accepted C1–C10 runtime behavior and are therefore non-blocking for this audit. They are not reclassified as passes.

## Remaining limitations and remediation plan

The only retained partial classifications are the intrinsic-keyword/ordinary-land-entry accounting rows described above. They are bounded, low-impact for the candidate, and supported by direct deterministic combat/resource fixtures. If HQ requires zero partial rows before gameplay authorization, the smallest follow-up is a documentation/coverage-evidence batch that promotes those existing fixtures into explicit per-card audit records; no engine redesign is indicated.

No gameplay simulation, smoke test, calibration, deck revision, baseline promotion, merge, or historical-evidence rewrite was performed.

## Final handoff

**READY FOR HQ GAMEPLAY AUTHORIZATION**

This is an engine-readiness recommendation only. HQ must separately authorize any Bad Guys gameplay test.

