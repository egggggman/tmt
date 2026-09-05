# Cardcade Gameplay Packet 1 Candidate

## Status

Implementation candidate only. This report is a handoff for independent review; it is not an
acceptance verdict and does not authorize merge or Gameplay Packet 2.

## Authorized semantic

> Destroy target artifact, enchantment, or creature with power 4 or greater.

The interpreter recognizes only that complete Oracle sentence as an executable direct Instant or
Sorcery. It does not generalize to different target classes, power thresholds, optional wording,
compound follow-ups, or nonspell parents.

## Frozen corpus membership

Exactly one frozen card-data record matches:

- Make Your Move
- Oracle ID `8226f31d-6f51-49c3-87f7-0c68f7f4f9ce`
- Set/collector number `TMT 20`

The SHA-256 of the canonical JSON membership record used during implementation review is
`0708b2533e419072ece30aff9e7f031b0f0978c98ace3690944387dc3b2a1ba1`.

## Implemented behavior

- Legal targets are generated from authoritative current battlefield characteristics.
- Artifacts and enchantments qualify without a controller restriction.
- Creatures qualify only when their current evaluated power is at least four.
- The selected runtime object ID is frozen on the Stack spell.
- Target authority and the same current-characteristics predicate are rechecked at resolution.
- A sole target that has become illegal produces the existing no-effect resolution outcome.
- A legal target is moved through the existing destruction/battlefield-to-graveyard machinery,
  including existing departure triggers and state-based processing.
- Successful and all-targets-illegal spell resolutions expose conformance execution references
  tied to the spell's runtime lineage and exact Oracle fragment.
- Own and opposing permanents are treated identically because the Oracle text says `target`, not
  `target an opponent controls`.

No card-name, deck-name, matchup, Pilot, Stage, or Smoke dispatch was added.

## Adversarial coverage

The dedicated suite covers artifacts, enchantments, qualifying creatures, both controllers,
printed/current type disagreement, current power changes, resolution-time illegality, stale and
wrong-zone objects, fabricated objects, replacement incarnations, exact corpus membership,
nonspell parents, and near-neighbor Oracle grammar.

## Validation

- Portable five-file implementation fingerprint (SHA-1 over canonical sorted path-to-Git-blob
  JSON): `73530fbe61a2871a40b26dfe0480473917daccf5`.
- Canonical engine identity: `39ee5749a82babf8762a6bdcc294c53d2524c13f`.
- Canonical interpreter identity: `24314732a0e24e902b1f288b976ddd6b24014227`.
- Canonical Stage #002 identity: `9bd2755a4a4062316b27bd1fedc54b352aa6bca5`.
- Focused Gameplay Packet 1 / Stack / departure-trigger / Stage #002 / Smoke 0.1 / Stage 0.2:
  `183 passed`.
- Full repository suite: `801 passed, 1 skipped`.
- Ruff lint, Ruff format-check, and `git diff --check`: required again on the final committed
  candidate after this report is banked.

## Known boundary

This packet uses the engine's existing represented-spell lifecycle. It does not add a new general
instant-response subsystem or change the established main-action compatibility driver. Unsupported
near-neighbor removal semantics remain visible to conformance accounting.

## Independent-review gate

An independent reviewer must verify the frozen commit, corpus boundary, current-characteristics
target predicate, runtime-incarnation locking, resolution recheck, conformance authentication,
regression results, and absence of special-case dispatch. The candidate must not be self-accepted.
