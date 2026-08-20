# Activated-Ability Foundation Acceptance Audit #1

## Decision

**REJECT — the activated-ability transaction is substantially sound, but the
engine-facing Action path resolves the newly announced stack object immediately,
without an engine-owned represented priority/pass boundary.**

This is an evidence-only audit of the uncommitted Activated-Ability Foundation
candidate on `agent/cardcade-activated-abilities`. No implementation or test was
modified during the audit.

## Audited state

- Parent Engine/Action baseline: `a21167a7680d8025fd0a0a79ed775f3d373d410c`
- Evidence checkpoint: `74ed492ae30305972b44bb5b529a9d6b17efe184`
- Candidate implementation fingerprint:
  `56a083c5dfec1ed2c62096b3afcb4a8251f5a938`
- Candidate files inspected:
  - `scripts/run_acceptance_match_001.py`
  - `src/tmnt_design_studio/card_interpreter07.py`
  - `src/tmnt_design_studio/engine07.py`
  - `src/tmnt_design_studio/pilot07.py`
  - `tests/test_activated_abilities.py`

## Authoritative rules basis

The audit used the current Wizards Comprehensive Rules, particularly CR 602.1
and 602.2. An activated ability is identified by its cost-and-effect form; its
activation is announced, targets and choices are made, costs are paid, and a
non-card ability object is placed on the stack. Illegal activation is rewound.
Resolution is a later stack operation governed by the priority rules, rather
than an inseparable part of announcement. The creature summoning-sickness
restriction applies to an activation whose cost contains the tap or untap
symbol, not to every ability of a creature.

## Primary lifecycle finding

The interpreter, engine, and pilot responsibilities are otherwise separated
appropriately:

- The interpreter identifies colon-bearing activated-ability semantics and
  produces Action-specific interpretation plus generic `SemanticCoverage`.
- The engine generates immutable legal options, revalidates selections, owns
  payment and rollback, creates the authoritative ability object, registers it
  on the stack, and applies the child effect on resolution.
- The pilot selects from engine-generated immutable options and cannot make a
  fabricated option legal.

The low-level announcement transaction is observably correct. An independent
probe found:

1. Before announcement, the stack was empty and the source lacked the temporary
   keyword.
2. After `announce_activated_ability`, mana was paid, an authoritative ability
   object was on the stack, and the keyword had not yet been granted.
3. After an explicit top-of-stack resolution, the temporary keyword was
   granted.

The public engine Action path does not preserve that boundary. Its
`ACTIVATE_ABILITY` execution calls activation announcement and then immediately
calls top-of-stack resolution in the same engine operation. The observed event
sequence was:

1. activation announced;
2. activation cost paid;
3. activated ability stacked;
4. temporary keyword granted;
5. activated ability resolved.

At return from the pilot-selected engine action, the stack was already empty
and First Strike was already active. No engine priority/pass state or legal pass
option exists between steps 3 and 4. The existing code also describes an
immediate compatibility drain pending Priority ownership of all-pass
resolution.

This is material because the candidate classifies Leonardo's complete fragment
as fully supported and removes its unsupported telemetry. The represented
engine lifecycle therefore claims more support than it delivers: stack
placement is real, but the normal Action path makes it transient and
uninterruptible without explicitly retaining that limitation.

## Transaction and adversarial regression findings

The underlying transaction passed the independently exercised checks:

- authoritative ability, source, and controller identities are retained;
- fabricated options, sources, and stack objects are rejected;
- stale source identity does not bind to a replacement object;
- the stack object remains resolvable after its source leaves, while a
  source-dependent child effect correctly does nothing;
- exact and excess fixed-mana payment work;
- insufficient mana leaves state unchanged;
- a forced registration failure rolls back tapped mana and allocation state;
- tap-cost fixtures reject tapped and summoning-sick creatures;
- Leonardo's mana-only activation is not incorrectly blocked by summoning
  sickness;
- costs remain distinct from effect delivery;
- the temporary keyword changes combat eligibility, does not mutate printed
  card data, and expires at cleanup;
- no post-terminal combat or activation was observed.

These results show that the rejection is not a request to redesign the existing
cost, stack-object, identity, rollback, or temporary-keyword transactions.

## SemanticCoverage and exact corpus reconciliation

The candidate uses generic `SemanticCoverage` and keeps recognition distinct
from executable parent, costs, targets/choices, child payload, follow-up, and
full-fragment support.

Independent corpus reconciliation against the authoritative 332-Oracle-object
snapshot produced:

| Classification | Oracle objects | Fragments |
| --- | ---: | ---: |
| Recognized activated-ability syntax | 131 | 156 |
| Top-level activations | 87 | 106 |
| Nested activations | 48 | 50 |
| Executable costs | 56 | 68 |
| Unsupported nonmana costs | 34 | 38 |
| Unsupported targets/choices | 26 | 26 |
| Unsupported timing restrictions | 6 | 6 |
| Executable child payload | 1 | 1 |
| Fully supported fragment | 1 | 1 |

Frozen-roster reconciliation found 45 recognized cards across all 10 decks.
The only bounded executable/full fragment is `Leonardo, Leader in Blue`, present
in one frozen deck.

Stable membership digests:

- Recognized: `35ccf2712e06f6cd0b93d03dbb867e909a6c8350e3e84616d0cee9b14f067190`
- Executable/full: `9c019f17c42f36208edf15d43eb29b10f2470a3fbcc5019c7c022a74945235f3`

No card-name, frozen-roster, acceptance-seed, or one-off Leonardo dispatch was
found. Leonardo is reached through the generic fixed-mana, self-targeted,
temporary First Strike form.

The seven pre-existing context-sensitive UNKNOWN Oracle objects remain
unresolved: Arcane Signet, Chromatic Lantern, Command Tower, Double Jump //
Flying Kick, Exotic Orchard, Fast Forward, and Plague of Vermin. Recognition of
colon syntax in an object does not make its unresolved semantics executable.

Food, Mutagen, Treasure, Clue, Equipment, Sneak, nonmana costs, targets,
choices, timing restrictions, compound children, and other arbitrary activated
semantics remain explicit and non-executable. Recognition did not create a
false executable positive in the audited corpus.

## Acceptance Match evidence

Seeds 7001–7005 were replayed twice and duplicate outputs were byte-equivalent.

| Seed | Winner | Ending turn | Activations |
| ---: | --- | ---: | ---: |
| 7001 | Raphael | 16 | 0 |
| 7002 | Leonardo | 19 | 1 |
| 7003 | Leonardo | 19 | 1 |
| 7004 | Leonardo | 21 | 6 |
| 7005 | Raphael | 16 | 0 |

Aggregate evidence:

- 69 unsupported events / 17 exact pairs;
- 8 announcements, 8 cost payments, 8 stack placements, 8 resolutions, and 8
  temporary-keyword grants, all for Leonardo;
- 18 first-strike damage steps and 16 following regular steps;
- 2 terminal first-step combats;
- 5 creatures removed between combat-damage steps;
- 8 Scry transactions;
- 16 Deal Damage transactions;
- 6 block-restriction rejections;
- 0 invariant violations.

The prior 61/18 telemetry reconciles exactly:

- Leonardo's five-event unsupported activation pair disappeared: -5 events and
  -1 pair.
- Six Prehistoric Pet exposures retained the same exact pair but now report
  three precise limitations instead of one: +12 events, no pair change.
- Changed game lengths added one further occurrence of the existing Lita Food
  pair: +1 event, no pair change.

Therefore `61 - 5 + 12 + 1 = 69` events and `18 - 1 = 17` pairs. The changed
turns for seeds 7002 and 7003 are execution consequences, not balance evidence.

## Validation

- Full suite: **336 passed / 1 skipped**
- Activated-ability suite: **22 passed**
- Stack/cost/boundary regressions: **23 passed**
- Strike/combat/state regressions: **77 passed**
- SemanticCoverage suite: **5 passed**
- Card-data integrity: **5 passed**
- Ruff format check: clean
- Ruff check: clean
- `git diff --check`: clean

## Exact blocker and smallest correction

The smallest evidence-backed correction is to preserve the existing activation
transaction while separating announcement from resolution in the engine-facing
Action lifecycle:

1. `ACTIVATE_ABILITY` announces, pays, and places the authoritative ability
   object on the stack, then returns without resolving it.
2. Add the smallest engine-owned represented priority/pass state and immutable
   legal pass option needed for this bounded scope.
3. Resolve the authoritative top stack object only after the represented pass
   condition, with normal revalidation.
4. Keep broader CR 117 limitations explicit; if no priority/pass mechanism is
   implemented, retain an explicit priority-window limitation and do not claim
   full-fragment support or suppress Leonardo's unsupported telemetry.

No broader activated abilities, costs, child Actions, targeting system, or
pilot strategy are required to correct this blocker.

## Recommendation

**REJECT — correct the missing engine-owned priority/pass boundary between
activated-ability stack placement and resolution, then repeat the independent
acceptance audit.**
