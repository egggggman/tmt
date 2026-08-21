# Post-Food Engine Validation Assessment

Assessment date: 2026-08-21  
Merged baseline: `98becb91aea5f393a5b5d298a0a4d0f171330b5a`  
Merged PR: #42 — accepted bounded canonical Food activation  
Decision: **Acceptance #001 credible → define the next validation stage**

## Question and gate

This assessment does not rank Action #13. It asks whether any of Acceptance Match #001's six
remaining unsupported pairs reveals a foundation conflict that makes the engine untrustworthy.

Classification meanings:

- **FOUNDATIONAL BLOCKER** — current architecture or execution cannot be trusted without the
  semantic, including silent approximation, invalid authority, or state corruption.
- **ACCEPTANCE-RELEVANT EXTENSION** — omitted semantics can materially change a game, but are
  explicitly bounded and have a credible extension path over the accepted foundation.
- **DEFERABLE SEMANTIC** — explicit unsupported behavior that is not exercised at a decision point
  capable of changing these replay trajectories and is safe to leave outside this validation stage.

Result: **zero foundational blockers, five acceptance-relevant extensions, and one deferable
semantic**. Acceptance #001 is credible as deterministic, bounded-scope engine-validation evidence.
It is not complete Magic gameplay, balance, or calibration evidence.

## Merged-main verification

- Local `main` and `origin/main`: `98becb91aea5f393a5b5d298a0a4d0f171330b5a`
- GitHub Actions on merged SHA: **PASS**
- Full suite: **499 passed / 1 skipped**
- Food: **20 passed**
- Activation/Stack/cost: **42 passed**
- Token/zone/SBA/identity: **98 passed**
- Life totals: **16 passed**
- SemanticCoverage + card data: **10 passed**
- Ruff format/check: clean
- `git diff --check`: clean before this evidence report
- Audit #1 repository-blob SHA-256:
  `38a9082f14becdb655d71821a587a824e692df67b37eedbdc407497092b37fc0`
- Audit #2 repository-blob SHA-256:
  `5950c74f272d4fbf52083c4aaf37d308c45eb5c313c404d00a17400fac5b47a5`

Acceptance seeds 7001–7005 were replayed twice. Duplicate files were byte-identical. Integrated
evidence remains **18 unsupported events / 6 exact pairs**, zero Food transactions, **44 Priority
grants / 44 passes**, one block-restriction rejection, and zero invariant violations. Trajectories
remain Raphael T14, Raphael T18, Leonardo T19, Leonardo T43, and Raphael T16.

## Residual-six assessment

### 1. Wingnut, Bat on the Belfry — 5 events

Oracle fragment: `Alliance — Whenever another creature you control enters, Wingnut gains your
choice of flying, menace, or haste until end of turn.`

Classification: **ACCEPTANCE-RELEVANT EXTENSION**.

The typed creature-entry event, generic trigger pipeline, immutable choice boundary, durations,
and characteristic evaluator provide an extension path. The exact ability remains truthfully
unsupported because all three offered outcomes must be legal: Flying affects block legality,
Haste affects attack/tap restrictions, and Menace requires multiple blockers. Omitting the trigger
can change combat, so it matters to gameplay; it does not corrupt represented state or silently
claim support. One narrow child or generic trigger expansion cannot clear the complete pair.

Exposure: Wingnut is in the Raphael deck; the exact modal payload is 1 object / 1 fragment.
Alliance reaches 6 frozen cards / 3 decks and 10 full-pool objects / 10 fragments.

### 2. Leonardo, Sewer Samurai — 5 events

Oracle fragment: `During your turn, you may cast creature spells with power or toughness 1 or less
from your graveyard. If you cast a spell this way, that creature enters with a finality counter on
it. (If a creature with a finality counter on it would die, exile it instead.)`

Classification: **ACCEPTANCE-RELEVANT EXTENSION**.

The omission can change available plays and board development. It is nevertheless explicit and
does not bypass Hand casting or fabricate a graveyard option. Truthful support requires a linked
lifecycle: alternate-zone casting permission, turn/controller and P/T qualification, casting
provenance, entry with a finality counter, Exile, and the dies replacement. Existing zones, costs,
Stack/Priority, counters, and identity supply extension seams; the compound fragment cannot be
cleared by a disconnected graveyard-casting shortcut.

Exposure: one exact frozen card in the Leonardo deck; graveyard creature casting reaches 2 frozen
cards / 3 decks and 2 full-pool objects / 2 fragments; finality is 1 / 1.

### 3. Casey Jones, Jury-Rig Justiciar — 2 events

Oracle fragment: `When Casey Jones enters, look at the top four cards of your library. You may
reveal an artifact card from among them and put it into your hand. Put the rest on the bottom of
your library in a random order.`

Classification: **ACCEPTANCE-RELEVANT EXTENSION**.

This ETB would occur when Casey resolves and can alter Hand/library state. The engine explicitly
withholds it rather than approximating Scry or Draw. A credible path exists through typed ETB
events, hidden-information views, immutable choices, runtime identity, ordered library zones, and
engine-owned deterministic RNG. Full support must atomically cover look-N, optional artifact
selection/reveal, Library-to-Hand movement, and random ordering of all remaining cards.

Exposure: Casey appears in the Casey Jones and Raphael decks; the exact family is 1 full-pool
object / 1 fragment.

### 4. Raphael, Most Attitude — Alliance exile — 2 events

Oracle fragment: `Alliance — Whenever another creature you control enters, you may exile the top
card of your library.`

Classification: **ACCEPTANCE-RELEVANT EXTENSION**.

Creature-entry events and represented Alliance delivery exist, but the optional choice, Exile zone
transaction, top-card provenance, and source-linked collection do not. The omission can affect
future resources, while telemetry remains explicit. Implementing exile alone would not complete
Raphael's gameplay because pair 5 consumes the linked cards.

Exposure: one frozen card / Raphael deck; exact exile-top payload 1 / 1, with Alliance at 10 / 10
in the full pool.

### 5. Raphael, Most Attitude — attack-time play permission — 2 events

Oracle fragment: `Whenever Raphael attacks, until end of turn, you may play a card exiled with
Raphael.`

Classification: **ACCEPTANCE-RELEVANT EXTENSION**.

Authoritative attack events and trigger/Stack delivery exist. Missing semantics are source-linked
exile identity, temporary permission, the land-play versus spell-cast distinction, timing/cost
validation, and expiration. This pair depends on pair 4; implementing it independently cannot
produce a legal option. The linked two-fragment lifecycle is gameplay-relevant but is an extension
over clean Zones, Identity, Costs, Stack, Priority, Events, Triggers, and Durations seams rather
than a repair to those foundations.

Exposure: one frozen card / Raphael deck; exact fragment 1 / 1, with broader `exiled with` linked
play handling at 4 full-pool objects / 4 fragments.

### 6. Raphael, Most Attitude — Menace — 2 events

Oracle fragment: `Menace (This creature can't be blocked except by two or more creatures.)`

Classification: **DEFERABLE SEMANTIC** for Acceptance #001's present trajectories.

Menace is explicitly unsupported and the combat model remains bounded to one blocker per attacker.
Fresh replay inspection shows Raphael, Most Attitude dealt player damage unblocked in the relevant
seeds; no one-blocker assignment against it supplied false Menace gameplay evidence. Supporting
Menace still requires a substantial multiple-blocker expansion: legal declaration enumeration,
blocker ordering, multi-recipient damage assignment, Trample/strike-step interaction, SBAs, and
immutable combat evidence. That work has meaningful future value but is not required to trust the
transactions actually observed here.

Exposure: one exact frozen card / Raphael deck; Menace reaches 6 frozen cards / 4 decks and 17
full-pool objects / 18 fragments.

## Why no pair is a foundational blocker

All six pairs remain visible in exact card/Oracle-fragment telemetry. None is classified as
supported, used as an engine authority input, or replaced with a superficially equivalent Action.
Their absence does not violate runtime identity, transactional zones/costs, Stack/Priority,
determinism, invariants, or the Engine–Interpreter–Pilot boundary. Accepted child capabilities are
not counted again when an unsupported parent or compound sibling prevents full execution.

This distinction matters: omitted abilities can make the resulting winners and turn counts differ
from complete Magic, but a known omission is not an architectural conflict. Acceptance #001 can
therefore validate reproducibility and the interactions among represented Actions while remaining
unsuitable as balance evidence or proof of complete roster fidelity.

## Gate decision and next validation stage

**Acceptance #001 credible → define the next validation stage.**

Pause Action-by-Action construction. The next stage should be an evidence specification, not Action
#13: a coverage-aware conformance suite that separates (a) transactions actually executed,
(b) legal semantic opportunities reached but explicitly declined/unsupported, and (c) card text
merely present on resolved objects. It should include targeted cross-Action scenarios for identity,
cost/Stack/Priority sequencing, trigger provenance, combat-step interactions, SBA boundaries,
hidden-zone ordering, deterministic replay, and unsupported-boundary non-execution.

That stage may use the six residual pairs as negative-boundary fixtures, but it should not require
implementing them, changing decks, creating Prototype 0.3, calibrating, smoke testing, or tuning the
Pilot. A later governance decision can promote an acceptance-relevant extension only if the new
validation evidence identifies a concrete fidelity gate.
