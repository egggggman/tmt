# Restricted Mana Ledger Foundation Acceptance

## Source identities

- Authorized source and PR base: `review/cardcade-purple-mana-audit` at `992da84b4ec97248e55c6073fbfa038016fc576e` (PR #391).
- Isolated worktree: `C:\projects\tmt\.cardcade-restricted-mana-ledger`.
- Implementation branch: `review/cardcade-restricted-mana-ledger`.
- Preserved failing reproduction: `0e1e497228123fe44d2a96b3cd056a11a23c4dc4`.
- Initial tested implementation and test source: `a0f83c97b42d4a080e04fb6ba6488712f20ec54d`.
- Final tested implementation and test source: `6af128283b9138acba7414ef999b13e5c59b0ba0`.
- Accepted `main` remains `10d2ac80ef5b81b3a209a3133eb0a84633a1f944`.

The first commit after the approved source adds a deterministic failing test. With source A's red mana expired, then source B's red mana produced, paying one red incorrectly recorded source A as consumed. This confirmed that the aggregate pool could become inconsistent with the historical production-order allocator. The test passes with the lot-based ledger.

## Data contract and behavior

`FloatingManaLedger` remains the single mana source of truth. Its live totals are now derived from production lots. Each immutable production identifies source, controller, color, original quantity, production event, optional allowed spending contexts, and expiration boundary. The ledger tracks remaining quantity and validity separately while retaining all production history.

`ManaPaymentPlan` and `ManaAllocation` identify the player, payment ID, spending context, colored requirements, and exact production lots and quantities. The ledger issues plans and verifies the exact issued plan before commit. Commit validates all allocations and the complete cost before mutating any lot. It rejects unissued or altered plans, stale or expired lots, duplicate lots/payment IDs, incorrect controllers, wrong colors, over-quantity allocations, and disallowed contexts. Successful consumption and expiry are immutable evidence records. Legacy `consume()` is fail-closed for restricted mana when a typed purpose is absent; unrestricted mana retains stable production-order allocation.

Supported context values are `artifact_spell`, `nonartifact_spell`, and `activated_ability`. Unrestricted production remains available to the existing ordinary payment paths. This checkpoint does not activate any card-specific restriction or implement Purple Dragon Punks.

## Engine state and provenance

Existing immediate mana production supplies the controller, production source identity, and current-step expiration boundary. Step transitions expire active lots while preserving the original production records and recording the expired quantity and exact boundary. Expired mana cannot become live through later same-color production.

Game snapshots now include `floating_mana_ledger` with production, remaining, validity, payment, and expiration records. The authoritative state fingerprint also includes the canonical ledger state, so production, consumption, and expiry mutations change the fingerprint. Existing Frog Butler source/event lineage and snapshot behavior were checked. Stage 002 reconciliation has not yet been extended to authenticate typed restricted-mana payment allocations; that work belongs with payment-path integration.

## Payment-path audit and boundary

- Ordinary spells and the supported graveyard/exile alternative-casting paths use `Game.payment_plan()` and `_commit_announcement_payment()`. Their existing floating-mana view is untyped and therefore sees unrestricted lots only. Its legacy consumption remains available for unrestricted mana.
- The exceptional Tunnel Rats graveyard activation reads and consumes floating mana through the same unrestricted-only compatibility interface.
- Ordinary activated-ability payment planning and Sneak planning currently select lands rather than consuming floating mana. No restricted lot is offered or treated as unrestricted there.
- Existing immediate Frog Butler mana production and its authenticated production/expiry records remain compatible.

Accordingly, the ledger contract can represent and safely validate restricted allocations, but the engine's spell and activated-ability plans do not yet create/commit typed `ManaPaymentPlan` objects. The next implementation boundary is to thread the appropriate purpose and exact allocations through each supported payment plan, including alternate-casting and graveyard paths, and extend execution evidence/reconciliation to link each payment to its production lots. Until then, restricted lots are intentionally unavailable to all legacy payment consumers.

The payment-path audit also found that legacy casting may call `consume()` once per color while reusing one spell payment ID. A selected synthetic regression initially failed on the second color after typed plan IDs became single-use. The compatibility wrapper now allocates directly from eligible lots without registering a typed plan, preserving repeated legacy consumption under one payment ID while keeping typed payment plans single-use.

## Synthetic validation

Environment: Python 3.12.10, pytest 8.4.2, Ruff 0.16.1. Executables:

- Python: `C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe`
- Ruff: `C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\ruff.exe`

Executed against final code/test HEAD `6af128283b9138acba7414ef999b13e5c59b0ba0` with `PYTHONDONTWRITEBYTECODE=1` and `PYTHONPATH=C:\projects\tmt\.cardcade-restricted-mana-ledger\src`:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='C:\projects\tmt\.cardcade-restricted-mana-ledger\src'
& 'C:\projects\tmt\.cardcade-fidelity-correction\.venv\Scripts\python.exe' -B -m pytest -q `
  tests\test_restricted_mana_ledger.py::test_expiration_does_not_reuse_an_older_same_color_production_lot `
  tests\test_restricted_mana_ledger.py::test_context_restrictions_and_unrestricted_lots_are_distinct `
  tests\test_restricted_mana_ledger.py::test_mixed_lots_and_partial_payment_preserve_exact_remaining_quantity `
  tests\test_restricted_mana_ledger.py::test_payment_rejections_are_atomic_for_forged_duplicate_and_wrong_context_allocations `
  tests\test_restricted_mana_ledger.py::test_expired_or_incorrect_controller_allocations_cannot_be_committed `
  tests\test_restricted_mana_ledger.py::test_lifecycle_evidence_preserves_consumption_expiration_and_boundary `
  tests\test_restricted_mana_ledger.py::test_legacy_payment_can_consume_multiple_colors_under_one_payment_id `
  tests\test_restricted_mana_ledger.py::test_game_snapshot_and_fingerprint_include_authenticated_frog_mana_lifecycle `
  tests\test_mana_ledger07.py::test_production_and_exact_lineage_consumption `
  tests\test_mana_ledger07.py::test_invalid_or_duplicate_consumption_fails_closed `
  tests\test_mana_ledger07.py::test_unused_mana_empties_deterministically `
  tests\test_frog_butler_mana.py::test_frog_butler_produces_chosen_color_with_source_provenance `
  tests\test_frog_butler_mana.py::test_frog_butler_mana_ability_rejects_summoning_sick_source `
  tests\test_frog_butler_mana.py::test_frog_butler_mana_is_immediate_and_empties_at_step_end `
  tests\test_pr386_final_fidelity_gate.py::test_frog_mana_action_produces_pays_and_expires_with_authenticated_lineage `
  tests\test_pr386_final_fidelity_gate.py::test_frog_mana_ability_is_an_immediate_priority_action_with_color_choice
```

Result: **16 passed, 0 failed, 0 skipped**. The selected new synthetic tests cover the expired-source reproduction, restricted versus unrestricted contexts, mixed lots, partial consumption, unissued/altered/duplicate/wrong-color/over-quantity/wrong-controller/disallowed/stale allocations, atomic rejection, exact lineage, immutable expiry evidence, snapshot/fingerprint inclusion, and multi-color legacy consumption under one payment ID. Selected legacy nodes cover ordinary ledger behavior and Frog Butler mana production, summoning-sickness legality, immediate resolution, payment, expiry, and existing provenance reconciliation.

Quality checks on the same code/test source:

```powershell
ruff format --check src\tmnt_design_studio\mana_ledger07.py src\tmnt_design_studio\engine07.py tests\test_restricted_mana_ledger.py
ruff check src\tmnt_design_studio\mana_ledger07.py src\tmnt_design_studio\engine07.py tests\test_restricted_mana_ledger.py
git diff --check
```

Formatting, lint, and diff checks passed. No complete game, runner, smoke test, or unrestricted test selection was run.

## Limits

This PR establishes the lot lifecycle and exact allocation contract only. It does not implement Purple Dragon Punks' activation, authorize restricted mana through existing game payment plans, or add reconciler linkage for restricted payments. No original PR branch, accepted main, deck, frozen card data, or historical artifact was modified.
