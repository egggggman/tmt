# Donatello Ooze Spill Response Coverage

Status: bounded Cardcade response capability. This is not a deck change and is
not a full Magic priority/stack implementation.

## 1. Authority

This change is authorized by
[`DONATELLO_P0_3C_CONVERSION_BOTTLENECK_REVIEW.md`](DONATELLO_P0_3C_CONVERSION_BOTTLENECK_REVIEW.md),
which classified the zero-cast result as `OOZE_RUNTIME_RESPONSE_SUPPORT_REQUIRED`
and authorized `AUTHORIZE_NARROW_RESPONSE_SEMANTIC_FIX`.

## 2. Exact card requirement

The contracted card surface is:

- Ooze Spill
- `{2}{U}`
- Instant
- `Counter target spell. Create a Mutagen token.`

The response path does not hard-code a Donatello cost. It reuses the loaded
card's authoritative mana requirement and the existing supported `OOZE_SPILL`
interpreter program, so payment, hand ownership, and target legality remain
engine-owned. No card-data or decklist change is included here.

## 3. Runtime limitation before the fix

The P0.3c smoke recorded 150 Ooze draw events, 49 opponent-spell windows, and
zero casts. Before this change, the bounded priority surface exposed passes and
supported activated-ability responses, but not a supported instant in hand as a
response to a pending opponent spell. Ooze's direct resolution tests already
covered countering a stack spell and creating Mutagen; normal games could not
reach that choice.

## 4. Implemented response model

Cardcade now exposes a small generic hand-response hook for the currently
supported counterspell program:

`opponent spell on stack -> response window -> supported Ooze instant in hand ->
deterministic selection -> response resolves -> original spell is removed`

The engine checks all of the following before exposing an option:

- the responder has priority;
- the pending top object is an opponent `StackObject` spell;
- the hand card is an Instant with the supported Ooze counterspell program;
- the card is still in the responder's hand;
- the existing mana-payment plan succeeds;
- the pending spell is a legal target.

Only the single original pending spell is exposed to this new hand-response
surface. Nested hand-instant responses and counter-wars remain out of scope.
The existing activated-ability counter path is unchanged.

When selected, the engine pays the card's mana, moves the card from hand to the
stack, targets the pending opponent spell, resolves the existing Ooze program,
moves the countered spell to its graveyard, creates the existing Mutagen token,
and prevents the original spell from resolving. Lands are not stack spells and
already-resolved permanents are not legal targets.

## 5. Pilot behavior

AcceptancePilot has one minimum extension: when a supplied priority option is a
supported cast targeting an opposing stack spell, it selects that option before
passing. Options remain engine-generated and ordered by the responder's hand
order, then target order. No mana reservation, bluffing, threat scoring, or
general priority strategy was added. PassingPilot continues to pass.

## 6. Event sequence

The response path records enough information to reconstruct the transaction:

1. `spell_cast` records the opponent spell.
2. `response_window_opened` records the bounded window.
3. `legal_response_exposed` records the hand response and target.
4. `response_selected` records the Pilot choice.
5. `cost_paid` records mana sources and colored/generic payment.
6. `spell_cast` records the Ooze stack object with `response: true`.
7. `response_target_selected` records the target spell.
8. `ooze_spill_resolved` records the countered spell and Mutagen token.
9. The original spell is moved to the graveyard and does not produce its
   creature, noncreature, or other spell effect.

## 7. Regression coverage

Focused tests cover:

- legal Ooze response exposure and deterministic AcceptancePilot selection;
- authoritative Ooze card data against a creature spell;
- countering a noncreature spell without resolving its effect;
- Mutagen creation and zone invariants;
- no Ooze response with insufficient mana or against an own spell;
- response event logging and deterministic replay through the existing tests;
- the pre-existing activated counterspell path remains covered separately.

The focused response and counterspell suite passes. Broader Mouser, Donatello,
Flying/Reach, combat, and smoke-invariant suites remain part of validation.

## 8. Known limitations

This is intentionally not a complete priority system. It does not implement

- arbitrary nested response chains or counter-wars;
- general instant-speed combat tricks;
- triggered-ability stack ordering beyond existing support;
- broad hand-instant semantics unrelated to the supported Ooze counterspell;
- strategic mana reservation or threat evaluation.

Unsupported or unrecognized instant cards remain unavailable rather than being
silently approximated. Uncounterable behavior remains out of scope unless an
existing card-specific semantic already provides it.

## 9. Explicit boundary

No decklist, Prototype 0.3d, smoke schedule, smoke rerun, or general Magic
priority rewrite is part of this change.

## 10. Next diagnostic gate

Run a small deterministic Donatello diagnostic before any new 240-game smoke.
Measure Ooze draws, exposed legal response windows, selections, casts,
resolutions, countered spells, Mutagen creation, and whether the response
changes survival or conversion. Treat the result as semantic/runtime evidence,
not as an automatic deck revision.
