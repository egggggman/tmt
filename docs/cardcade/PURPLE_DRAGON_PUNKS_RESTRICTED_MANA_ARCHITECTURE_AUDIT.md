# Purple Dragon Punks Restricted-Mana Architecture Audit

## Audit identity and frozen Oracle contract

- Audited source: `7121cd785d3f59b9952abe5631125b54acfc0d2d`, branch `review/cardcade-ravenous-robots`.
- Audit branch/worktree: `review/cardcade-purple-mana-audit`, `.cardcade-purple-mana-audit`.
- Frozen card snapshot SHA-256: `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402`.
- Frozen manifest SHA-256: `6b5271af75150a361f77e7b89306c709959dfdf497c448dfdc978e5dc9a17950`.
- Purple Dragon Punks Scryfall ID: `bbe1d7e5-68e2-4458-aa3f-5e97fa8e7cae`.
- Oracle ID: `d1edb950-a118-4b4d-a0ef-9a6683d74c9f`.
- Frozen type line and cost: `Creature — Human Rogue`, `{1}{R}`.
- Exact frozen Oracle text: `{T}: Add {R}. Spend this mana only to cast an artifact spell or to activate an ability.`

This produces one red mana. Its allowed spending contexts are limited to casting an artifact spell or paying for an activated ability. The source must be tappable; because it is a creature, the existing summoning-sickness rule applies unless it has haste. The text gives no sorcery-only timing restriction. The ability has no target and directly produces mana, so it is a mana ability: it resolves immediately without the Stack. It must not be modeled as unrestricted red mana. The mana restriction stays attached to each produced unit after Purple Dragon Punks leaves the battlefield.

## Current architecture findings

| Area | Existing support | Gap for this ability |
|---|---|---|
| Mana ability interpretation | `card_interpreter07.py` has `ADD_ANY_COLOR_MANA`, but its recognition is currently tied to Frog Butler's exact name and `{T}: Add one mana of any color.` text. The engine executes that effect immediately, without putting the ability on the Stack. | No typed fixed-color output or allowed-spending restriction exists. Purple Dragon Punks is not recognized. |
| Mana records | `mana_ledger07.py` retains producer source ID, color, quantity, event ID, and consumption source-event ID/payment ID. The engine logs `floating_mana_produced` and records activation evidence. | Production has no explicit controller, allowed contexts, or expiration boundary. `consume` assigns FIFO by color without checking why mana is spent. |
| Spell payment | `PaymentPlan` and `payment_plan` use floating mana by color and retain only `floating_colors`; artifact identity is available from the card's type line. | Plans do not identify production lots or payment purpose, so an artifact-only restriction cannot be enforced or authenticated at commit. |
| Ability payment | `ActivationPaymentPlan` selects untapped lands and currently ignores floating mana. A special graveyard path can consume floating black mana, also without restriction metadata. | Ordinary activated abilities, hand/graveyard actions, and some special cast paths have distinct payment code. Eligible restricted mana must be accepted consistently for supported activated abilities. |
| Mixed payment | Existing planners support colored and generic costs, and limited hybrid selection. The ledger can retain partial consumption internally. | Selection sees aggregate color counts, not permitted lots. Plans cannot reserve exact lots, so mixed restricted/unrestricted payments cannot be checked reliably. |
| Expiration | `transition_to` empties each player's floating pool at a step transition and logs the prior color totals. | The pool loses no restrictions because none exist, but the production ledger has no explicit expired/remaining state or boundary identity. |
| Snapshot and reconciliation | Snapshots contain activation evidence and the `floating_mana_produced` / `mana_pool_emptied` event log records. | The floating pool, production ledger, and consumption ledger are not serialized into `Game.snapshot()` or the authoritative state fingerprint. The production log has color/quantity/source and activation object ID, while payment logs do not serialize exact floating production allocations. Reconciliation cannot currently prove restricted payment lineage. |
| Action visibility | Main and priority legal-action generation can offer the existing mana ability only when the interpreter recognizes it. Main actions include activation options; priority actions include immediate mana abilities. | Once recognized, the normal AcceptancePilot selects a non-cycling activation in its main `activate` stage, but its priority policy generally passes when a mana action has no target. A restricted mana action may therefore be legal and visible at priority without the pilot choosing it to enable a response. |

Current all-pass Stack behavior for ordinary activated abilities is already distinct from the immediate Frog mana path. Purple Dragon Punks should use the immediate mana-ability path, while the later ability it pays for follows that ability's ordinary Stack/timing rules.

## Minimum extension recommendation

Keep `FloatingManaLedger` as the sole source of floating-mana truth. Represent each production lot with the existing producer/source and event identity plus:

- Producing controller/player index, fixed color and quantity.
- A bounded allowed-spending set, such as `cast_artifact_spell` and `activate_ability`.
- Creation turn/phase/step and the step-transition expiration boundary.
- Remaining unspent quantity, derived consistently from production minus exact consumption records.

Represent payment as an explicit context and exact allocation, not a color-only tuple. Each payment allocation should identify production event, color, quantity, payment/stack object ID, and spending context. A pure plan must allocate colored and generic symbols only from lots allowed for that context; committing must revalidate the exact allocation and all other costs before any mutation. Spell context is artifact or nonartifact based on the authoritative card type line. Ability context is an actual legal activated-ability payment, including supported battlefield, hand, and graveyard activation paths. Ordinary lands and unrestricted floating mana remain eligible under their current rules.

Extend activation semantics with a bounded generic fixed-color mana-production description and parse the “Spend this mana only…” clause into the produced mana's restriction metadata. The fixed output must be derived from the card text (`R`, quantity one), not a Purple Dragon Punks name exception. Preserve the current immediate mana path: tap cost and summoning-sickness checks are validated, the activation evidence/source event is unique, the ability does not enter the Stack, and the authenticated production is recorded once.

Serialize active pools and production/consumption allocations in the snapshot and include active floating mana plus its restrictions in the authoritative fingerprint. Preserve historical production and consumption records after expiry, with an explicit boundary/expiration record. Extend the existing evidence and reconciler path to authenticate the source, controller, Oracle fragment, production event, payment context, exact consumed quantity, and remaining/expired amount. No new parallel pool or card-name-specific payment exception is needed.

For pilot visibility, expose a deterministic mana-ability action when the legal payment planner can identify a supported artifact spell or activated ability that the restricted unit can enable. The current main `activate` stage already considers legal activation actions; priority selection needs a small context-aware policy if supported response casts should use this mana. This is a pilot-choice concern separate from payment legality.

## Synthetic acceptance proposal

All tests should use a constructed `Game` and individually selected nodes; none needs to launch a complete game.

1. Frozen Oracle parses `{T}` and one `{R}` with the two allowed contexts. A legal, nonsummoning-sick Purple Dragon Punks action taps the source and adds exactly one restricted red unit immediately; Stack identity and priority epoch do not change.
2. A summoning-sick Punks source offers no legal tap action, and a rejected direct announcement leaves source tap, pool, evidence, events, object sequence, and fingerprint unchanged.
3. The restricted red unit pays for a normally cast artifact spell and a legal activated ability. Each payment records the exact production event and consumption quantity.
4. A nonartifact spell cannot use the restricted unit. If ordinary red mana is also available, the planner uses eligible ordinary sources and leaves the restricted unit untouched; otherwise no cast option is offered and direct rejection mutates nothing.
5. Combine restricted mana with ordinary lands and unrestricted floating mana across colored and generic costs. Verify deterministic legal allocations, partial spending, and the correct remaining lots.
6. Expire unspent mana at the existing step boundary and prove the next step cannot spend it. Preserve its historical production and explicit expiration evidence.
7. Remove Punks after production; the controller can still spend the already produced restricted mana in an allowed context until expiration.
8. Reject stale, relinked, duplicate, wrong-controller, wrong-color, over-quantity, nonartifact, and disallowed-context payment allocations before mutation.
9. Verify event and snapshot/reconciler lineage from Punks source and activation through production, exact payment, and any remaining/expired mana; no false execution reference or silent approximation.
10. Verify engine legal-action generation and AcceptancePilot visibility at main and priority windows, including that it can choose the immediate mana action when that action enables a legal artifact spell or activated ability.

## Compatibility families and estimated scope

Likely compatibility validation should include `tests/test_mana_ledger07.py`, all three individually named tests in `tests/test_frog_butler_mana.py`, and `tests/test_pr386_final_fidelity_gate.py::test_frog_mana_action_produces_pays_and_expires_with_authenticated_lineage` plus `::test_frog_mana_ability_is_an_immediate_priority_action_with_color_choice`. Add focused spell-payment, activated-ability, hand/graveyard action, Sneak/alternate-cast, and snapshot/reconciliation nodes; inspect each test body before execution. Existing generic payment, counterspell, and action-option tests are relevant because plans and legal actions must remain deterministic.

Expected bounded implementation scope: `card_interpreter07.py` for parsed mana semantics; `mana_ledger07.py` for restriction-aware lot allocation and consumption; `engine07.py` for mana production, all applicable payment plans, action generation, serialization, and fingerprint validation; `pilot07.py` only for spend-aware priority choice; `stage002.py` if reconciliation evidence needs a corresponding contract; and focused tests in the mana ledger, Frog mana, and payment/action families. No code or tests were changed or executed during this read-only audit.

## Recommendation

The restriction cannot be safely implemented by adding a color to the current aggregate pool. The existing single ledger and deterministic payment architecture can support it with per-production restrictions, exact plan allocations, and evidence serialization. **READY FOR HQ IMPLEMENTATION AUTHORIZATION.**
