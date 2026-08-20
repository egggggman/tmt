# Activated-Ability Foundation Acceptance Audit #2

## Audit conclusion

No material blocker remains within the declared bounded scope. The formal recommendation appears
once at the end of this report.

This was an independent, evidence-only audit of the corrected uncommitted candidate on
`agent/cardcade-activated-abilities`. The implementation and tests were not modified.

## Audit identity

- Baseline evidence HEAD: `74ed492ae30305972b44bb5b529a9d6b17efe184`
- Corrected candidate fingerprint: `6575f65c1f979497bba80a2ff5c31f120f812255`
- Historical REJECT #1 SHA-256 before Audit #2:
  `7021a0f74a2b79d75ecffaf7d744d5c8f80cc816a43b4b09b139babf3721ff83`
- Audit type: evidence-only; no candidate source or test changes

## Reproduction of REJECT #1 and correction

Audit #1 rejected the original candidate because its engine-facing activation Action announced
the activation, paid costs, created an authoritative stack object, and then called
`resolve_top_of_stack()` before returning. The stack object was real but the Action exposed no
represented Priority opportunity: announcement and resolution were effectively inseparable.

That path is impossible in the corrected candidate. `activate_ability()` now stops after
`announce_activated_ability()`. Announcement pays costs, registers the ability, appends it to the
authoritative stack, and opens a `PriorityState`; it does not call a resolution method. An
activated ability is rejected by `resolve_top_of_stack()` unless engine state records the required
all-pass sequence. The runner cannot skip this because later main actions are unavailable while
Priority exists and the stack remains unresolved.

## Five distinct authoritative states

An independent executable probe established all five required states:

| State | Authoritative evidence |
| --- | --- |
| A — before activation | No new ability object; stack empty; no Priority state; no temporary First Strike. |
| B — after announcement/payment | Two lands tapped; the same authoritative `ActivatedAbilityObject` is on the stack; active player has Priority; activation evidence is unresolved; no temporary First Strike. |
| C — after first pass | The identical stack object remains authoritative and unresolved; pass ledger is `(0,)`; Priority transfers to player 1; no temporary First Strike. |
| D — after second pass | Stack object remains present; pass ledger is `(0, 1)`; `resolution_pending` is true; `stack_resolution_permitted` is emitted; payload has not executed. |
| E — after engine resolution | The authoritative top object leaves the stack for `former`; Priority clears; resolved evidence becomes true; only then is temporary First Strike present. |

No public engine Action collapses B through E. The second pass permits resolution but does not
itself execute the payload; `process_priority_resolution()` is a separate engine processing
boundary.

## Priority ownership and pilot boundary

The engine exclusively owns:

- `priority_state`, including current player, epoch, consecutive passes, and resolution permission;
- creation of immutable `PASS_PRIORITY` options for exactly the current player and epoch;
- validation and rejection of submitted options;
- transfer of Priority and reset of pass bookkeeping;
- permission to process resolution;
- selection and resolution of the authoritative top stack object;
- creation of a fresh Priority epoch when another stack object remains.

The interpreter has no Priority state or mutation path. The pilot receives a public view and an
immutable tuple of engine-generated options and selects only `PASS_PRIORITY`. Its choice names no
stack object and cannot assign the Priority player, pass for the opponent, change pass counts, or
request resolution. The acceptance runner merely asks the engine for the current player's legal
options and invokes the engine processing boundary after the engine reports resolution permission.

Passing remains a legal, deliberately poor strategy. It is not an immediate-resolution shortcut.

## Adversarial sequencing and stack identity

Focused executable probes independently confirmed:

- zero passes and one pass cannot resolve;
- a wrong player cannot pass;
- the same player cannot use a stale first option as the second pass;
- fabricated epochs and stale immutable options are rejected;
- rejected pass/resolution attempts leave the complete snapshot unchanged;
- an engine-validated represented action between passes clears consecutive passes;
- a new Priority window uses a new epoch and does not inherit prior passes;
- resolution consumes only the authoritative LIFO top object;
- a remaining stack object receives a fresh pass sequence;
- fabricated/equal-valued activated-ability objects fail authoritative-top validation;
- one ability cannot resolve twice;
- an empty stack cannot resolve;
- no child payload executes while the object waits;
- Priority clears coherently if resolution ends the game;
- no Priority state survives into combat, postcombat, end, cleanup, or a later turn.

The bounded synthetic two-object probe resolved the second object first, kept the first object on
the stack, opened a new Priority epoch, and resolved the first only after another legal all-pass
sequence.

## Costs remain costs

Mana and tap costs are committed during activation, before Priority begins. Waiting and passing do
not defer, repeat, or refund payment. Resolution does not touch the paid mana sources. If the source
leaves before resolution, the ability can resolve without delivering its source-dependent child;
the paid cost remains paid and a replacement object is not rebound.

Insufficient mana creates no stack or Priority state. A forced registration failure rolls back all
mana/source taps and object allocation. Summoning sickness is checked only when the activation cost
contains `{T}` or `{Q}`; Leonardo's fixed mana-only activation is not incorrectly prohibited merely
because its source is a creature.

## Truthful bounded Priority scope

This correction represents one deliberately bounded CR 117 seam: deterministic 1v1 Priority after
the currently supported activated-ability announcement, with active-player Priority and pass-only
choices until all players pass. It is not complete Magic Priority.

The following remain unsupported and were not made executable:

- arbitrary opponent responses or generic instant-speed Actions;
- other Priority windows and timing permissions;
- arbitrary targets and choices;
- complex, variable, sacrifice, discard, life, counter-removal, and other nonmana costs;
- Food, Mutagen, Treasure, and Clue use;
- Equipment, Sneak, Draw, and generic trigger delivery;
- compound activated abilities and unsupported follow-ups.

The engine helper for a future represented action records the mandatory pass reset, but the current
Priority option universe contains only PASS. No synthetic response is exposed to a pilot or claimed
as supported.

## Leonardo and dispatch audit

No card-name, deck-name, seed, or Acceptance-specific dispatch exists in the interpreter,
activation option generator, announcement transaction, Priority controller, or resolver. The sole
executable corpus member is reached through generic stages:

`recognized activation → fixed mana cost → authoritative source → stack object → bounded Priority/pass → LIFO resolution → supported self First Strike until end of turn`

Renaming the source while preserving its Oracle structure remains executable. Leonardo is the only
authoritative-pool consumer of that bounded structure, not a hard-coded exception.

## Independent coverage reconciliation

Coverage was regenerated from the authoritative 332-Oracle-object snapshot:

| Classification | Oracle objects | Fragments |
| --- | ---: | ---: |
| Recognized activated abilities | 131 | 156 |
| Bounded child executable | 1 | 1 |
| Fully supported parent/cost/choice/child/follow-up | 1 | 1 |

- Frozen recognized: 45 cards across all 10 decks.
- Frozen executable/full: Leonardo, Leader in Blue in the Leonardo deck.
- Recognized membership digest:
  `35ccf2712e06f6cd0b93d03dbb867e909a6c8350e3e84616d0cee9b14f067190`
- Executable membership digest:
  `9c019f17c42f36208edf15d43eb29b10f2470a3fbcc5019c7c022a74945235f3`
- Fully supported membership digest:
  `9c019f17c42f36208edf15d43eb29b10f2470a3fbcc5019c7c022a74945235f3`

The fully supported classification is now evidence-backed for the declared bounded contract because
announcement and resolution are separated by an authoritative pass cycle. It does not assert that
the fragment supports arbitrary responses.

The seven context-sensitive UNKNOWN objects remain unchanged: Arcane Signet, Chromatic Lantern,
Command Tower, Double Jump // Flying Kick, Exotic Orchard, Fast Forward, and Plague of Vermin.
Recognition of activated syntax did not upgrade any of them to executable support.

## Acceptance Match reconciliation

Seeds 7001–7005 were executed twice each. Duplicate JSON outputs were byte-equivalent.

| Seed | Winner | Ending turn | Unsupported events |
| ---: | --- | ---: | ---: |
| 7001 | Raphael | 16 | 10 |
| 7002 | Leonardo | 19 | 17 |
| 7003 | Leonardo | 19 | 12 |
| 7004 | Leonardo | 21 | 16 |
| 7005 | Raphael | 16 | 14 |

Aggregate evidence:

- 69 unsupported events / 17 exact card-fragment pairs;
- 8 activation announcements;
- 8 cost payments;
- 8 authoritative ability stack placements;
- 16 Priority grants: active player then opponent for each activation;
- 16 PASS actions: two for each activation;
- 8 successful all-pass permissions and 8 resolutions;
- 8 temporary First Strike grants, every one ordered after its resolution permission;
- 0 represented response Actions;
- 8 Scry transactions;
- 16 Deal Damage transactions;
- 6 block-restriction rejections;
- 0 invariant violations.

The previously audited `61 / 18 → 69 / 17` explanation remains exact. Five Leonardo activation
events and their one pair disappear. Six Prehistoric Pet exposures retain the same pair but replace
one broad report with three precise limitations, adding twelve events. Changed game length adds one
more occurrence of the existing Lita Food pair. Therefore events reconcile as
`61 - 5 + 12 + 1 = 69`, while pairs reconcile as `18 - 1 = 17`. The Priority correction creates no
new unsupported pair and masks no telemetry regression.

## Combat and life integration

The represented match begins with both players at 20 life. A complete seed-7002 trace shows, on turn
3, activation announcement, cost payment, stack placement, active-player grant/pass, opponent
grant/pass, resolution permission, temporary keyword delivery during resolution, and resolved
evidence. Only afterward does combat enter a first-strike damage step, apply damage and state-based
actions, and proceed to the appropriate regular step. The match remains deterministic and ends with
Leonardo winning on turn 19.

Focused combat probes confirm the temporary First Strike grant changes strike-step eligibility,
expires at cleanup, does not mutate printed characteristics, and leaves no Priority/pass state in
combat or later phases. Costs do not change life; life changes remain attributable to represented
damage/effects.

## Historical evidence integrity

`docs/cardcade/ACTIVATED_ABILITY_FOUNDATION_ACCEPTANCE.md` remains the durable REJECT #1 record.
Its SHA-256 after this audit remains:

`7021a0f74a2b79d75ecffaf7d744d5c8f80cc816a43b4b09b139babf3721ff83`

## Validation

- Full suite: **344 passed / 1 skipped**
- Activated Ability / Priority: **30 passed**
- Stack / cost / boundary: **23 passed**
- Strike / combat / state: **77 passed**
- SemanticCoverage: **5 passed**
- Card-data integrity: **5 passed**
- Ruff format check: clean, 39 files
- Ruff check: clean
- `git diff --check`: clean
- Candidate fingerprint after audit:
  `6575f65c1f979497bba80a2ff5c31f120f812255`

## Recommendation

**ACCEPT — corrected bounded Activated-Ability Announcement / Delivery foundation is suitable to bank.**
