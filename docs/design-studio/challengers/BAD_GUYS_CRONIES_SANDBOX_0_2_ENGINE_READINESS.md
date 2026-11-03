# Bad Guys 0.2 — Cardcade engine-readiness audit

**Decision: BLOCKED for gameplay testing**  
**Candidate:** `BAD_GUYS_CRONIES_SANDBOX_0_2_CANDIDATE.md`  
**Audited commit:** `aac80ce4c876696a971f6136197a07e6f9445af2` (PR #363)  
**Semantic runtime:** `d4466241f0ffeaca809cd6a05210ad53b9af1011a1d7f833de88657c1cf00924`

This is an engine-readiness audit only. No gameplay simulations, matchup batches, deck changes, or baseline changes were run.

## Authentication

- Candidate totals: **60 cards**.
- Authorized diff from the preserved Baseline 005 Bebop & Rocksteady list: `−4 Zoo Escapees`, `−3 Putrid Pals`, `+4 Foot Elite`, `+3 Foot Mystic`; no other card or land changes.
- Candidate source SHA-256: `cacc77648a4d1659b8ae640d95ac2672694e6951553980246e6d001e5152bfb4`.
- Baseline source SHA-256: `aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed` (330 bytes). Baseline file is byte-for-byte unchanged.
- Pinned card snapshot: `cardcade/scryfall-tmt-pza-tmc-2026-08-13.json`, SHA-256 `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`; manifest checksum verification passed.
- All 17 unique candidate identities resolve unambiguously in that snapshot and report `standard: legal`. Quantities are within the four-copy limit.

The authenticated candidate structure is **28 creatures, 10 noncreature/nonland spells, and 22 lands** (20 basic plus 2 `Illegitimate Business`). The candidate Markdown still contains a stale sentence saying “26 creatures, 12 nonland noncreature spells”; that is documentation drift only. The decklist and recomputed counts are 28/10/22.

## Recomputed mana curve

The complete snapshot-derived curve is:

| Mana value | Copies |
|---:|---:|
| 0 (lands) | 22 |
| 1 | 3 |
| 2 | 12 |
| 3 | 12 |
| 4 | 5 |
| 5 | 2 |
| 6 | 4 |

Nonland weighted total is 117 across 38 nonlands, so mean nonland mana value is **117/38 = 3.078947**. `Mutagen Man, Living Ooze` has printed mana value 2 despite its variable-X cost. Land sources are 10 Swamps, 10 Forests, and 2 tapped black/green duals.

## Oracle-to-engine coverage

| Required family | Result | Evidence / limitation |
|---|---|---|
| Foot Elite attack trigger, “another” creature target, +1/+0, temporary indestructible | **BLOCKED** | `oracle_ability_not_implemented`; no generic attack-trigger implementation for this fragment. |
| Foot Mystic lifelink | Supported | Existing lifelink semantics and focused tests pass. |
| Foot Mystic Disappear ETB condition and Ninja token | **BLOCKED** | Token payload parses, but `token_condition_context_not_implemented`; permanent-left history is not connected to this ETB effect. |
| Rocksteady Forestcycling {2} | Supported | Generic landcycling grammar, cost/discard/search/reveal/shuffle path, and tests pass. |
| Rocksteady / Boar “can’t be blocked by more than one” | **BLOCKED** | Both continuous combat restrictions are `oracle_ability_not_implemented`. |
| Bebop & Rocksteady attack/block sacrifice-or-discard obligation | **BLOCKED** | `oracle_ability_not_implemented`; mandatory choice and payment are not executable. |
| Mutagen Man variable-X token quantity | **BLOCKED** | `variable_token_quantity_not_implemented`. |
| Mutagen artifact-token activation discount | **BLOCKED** | `oracle_ability_not_implemented`. |
| Stomped by the Foot kicker and −2/−2 or −5/−5 resolution | **BLOCKED** | Kicker cost and damage/removal spell fragment are unsupported. |
| Mutant Chain Reaction optional removal plus Mutagen creation | **BLOCKED** | Removal-before-token compound effect is `token_preceding_effect_not_implemented`. |
| Tainted Treats conditional Food creation | **BLOCKED** | Mana-value condition is `token_condition_context_not_implemented`. |
| Cowabunga! top-four qualified selection and random bottom order | **BLOCKED** | `oracle_ability_not_implemented`. |
| Paramecia Coloniex death/exile recursion | **BLOCKED** | `oracle_ability_not_implemented`. |
| Menace / Rhino menace grant | **BLOCKED** | Keyword and continuous grant fragments are unsupported. |
| Deathtouch, trample, reach, ordinary land entry, and other intrinsic facts | Partial | Some intrinsic keywords are modeled, but the unsupported companion clauses above prevent complete card execution. |

These are existing coverage limitations, not evidence of a failing generic implementation. No card-name or deck-name branch was added.

## Validation executed

Commands run from the PR #363 checkout:

```text
uv run pytest tests/test_create_token_action.py tests/test_lifelink_action.py \
  tests/test_landcycling_activation.py tests/test_activated_abilities.py -q
101 passed

uv run pytest -q
1627 passed, 10 skipped

uv run ruff check .
All checks passed!

uv run ruff format --check .
673 files already formatted

uv run python tools/validate_objective_balance_lab_baseline005.py
Baseline 005 promotion draft: PASS; B&R only; 20 basics unchanged, 24 -> 22 total lands; 0 new games
```

The focused and full tests establish regression health; they do **not** upgrade the unsupported Oracle rows to supported coverage. No simulator or semantic source file was modified by this audit, so the runtime remains `d4466241…00924`.

## Readiness recommendation

**BLOCKED.** Structural authentication, legality, snapshot integrity, baseline preservation, regression, Ruff, and formatting all pass. Cardcade is not ready for even a bounded gameplay smoke test because the candidate’s central mechanics and retained Bad Guys interaction package include unsupported attack triggers, conditional Disappear, combat restrictions, mandatory attack/block costs, removal/kicker effects, and variable token semantics.

The smallest corrective path is a bounded generic semantic batch covering (1) Foot Elite’s targeted attack trigger with end-of-turn effects, (2) the existing permanent-left history as a conditional ETB trigger for Foot Mystic, and (3) the already-shared Bad Guys combat/payment/removal families only as needed by this exact list. Reassess coverage with deterministic fixtures after that work. Do not launch gameplay testing or alter Baseline 005 until HQ independently accepts the repaired coverage.
