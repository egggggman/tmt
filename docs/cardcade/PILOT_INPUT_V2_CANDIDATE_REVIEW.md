# pilot-input-v2 implementation candidate — HQ review required

**Status: separately reviewable candidate, not an accepted assessment baseline.**
The implementation and validation packet are preserved together on
`candidate/pilot-input-v2`. The exact commit containing this packet identifies
the candidate; the companion JSON records exact source identities. HQ must
independently accept this candidate before any V2 baseline or sealed-fixture
construction is declared.

Accepted input-contract assessment / V1 comparison source:
`f3814ae2fc1c9b344960167fcaff5c9630a0a075`.

Frozen gameplay reference: `de52f57a24a5c29a258573ad673051a0aa5c7e5c`.
Accepted assessment specification: `ca9757b956eafc4b8d03c495dabb03eaab6fe931`.
Historical failed-readiness evidence at `e28cd6dcd5532b84d38c45d3a710077e5cb589b4`
remains V1; no historical assessment artifacts are overwritten or promoted.

## Implementation boundary

The dataflow remains authoritative state → immutable observation → unchanged
Pilot → unchanged ActionOption → existing engine execution.

- `pilot_input_v2.py` contains frozen, slotted value types and pure projection
  helpers. Every nested observation collection is a tuple. No live CardObject,
  Permanent, Stack object, event, program, dictionary, callback, registry or RNG
  state is supplied to the Pilot.
- `DecisionContextV2` describes the recipient's own hand, both public boards,
  life/counts, current turn/step and own lands played. Opponent hands have counts
  only. Libraries have counts only, except the exact already-inspected Scry slice.
- Required-context `ScryViewV2`, `HandBottomDrawViewV2` and `DiscardDrawViewV2`
  retain the old cards/requested shapes at the existing instruction point.
  The mandatory draw-first chooser remains distinct and uses its supplied owner.
  Legacy V1 classes remain available; they do not silently qualify as V2.
- `Game.pilot_view(owner)` supplies a recipient-specific GameViewV2 for main,
  attack, blocks and Sneak. The opponent hand tuple is empty and explicit
  `hand_sizes` prevents interpreting redaction as a zero-card hand. Blocks bind
  to the defender. `public_view()` remains a clearly labeled V1 diagnostic.
- `Game.priority_view(owner)` requires the exact current Priority decision
  owner and rejects resolution-pending/nondecision requests. It includes epoch,
  consecutive passes and all three supported Stack kinds in bottom-to-top order.
  Unknown Stack kinds raise an explicit observation error.
- Stack fields use an explicit allowlist. Ability source descriptions come from
  the recorded public source card and original source ID, including after source
  departure. Target descriptions resolve only against current public battlefield
  and Stack containers. Departed targets retain their original ID with
  `unresolved` status and no description or destination ID; they never rebind.
- Keyword observations enumerate existing first/double-strike, trample and
  lifelink queries, plus explicitly named `temporary_flying`, `temporary_menace`,
  `temporary_haste` and `temporary_deathtouch`. Other keywords remain printed
  card facts, without an inferred executable status. Land observations copy the
  existing fixed-color and untapped payment predicates, not cast legality.

No new gameplay rule, legality enumeration, payment, timing, Stack behavior, RNG,
target framework, hidden-zone visibility system, public history or Pilot
memory/knowledge policy was introduced. Pilot method bodies and defaults are
unchanged. Imports and Priority annotations changed to identify V2 input types.

## Validation results

| Obligation | Evidence / result |
| --- | --- |
| Both seats and nonactive Priority | Unit checks plus runtime ownership assertions at every recorded hook; every hook covered for seats 0 and 1. Nonactive Priority: 9 seat-0 and 12 seat-1 decisions. |
| Opponent-hand privacy | Redacted GameViewV2 and recipient contexts; hidden identity/card substitutions leave observations and complete main-option sequences unchanged. |
| Future-library privacy | Recursive identity scans; changing uninspected library order/card descriptions preserves Scry view and complete Scry options; empty hand/library and inspection boundaries covered. |
| Stack order/identity/controller/source/targets | Spell, triggered and activated rows; deliberately non-ID-sorted Stack; ordered multiple targets, public zones, source departure, stale target/replacement, and unknown-kind failure. |
| Deep immutability/isolation | Recursive frozen/slotted checks and mutation attempts at each nested value; changing authoritative hand/card/counter state cannot change existing observations. |
| Projection purity | Full copied game-object graph comparisons, including registry, state, evidence, interpreter and RNG; context/Game/Priority construction and reading leave it unchanged. |
| Legal options unchanged | Whole-source AST proof preserves all enumerators and execution logic; paired runs compare every full ordered option sequence, not just selected actions. |
| Frozen policies | Method-body AST, defaults and decorators checked; per-method body digests recorded. Whole normalized Pilot AST also compared. No policy changes. |
| Consequent gameplay equality | **16 V1/V2 pairs** with exact equality of full options, arguments, choices and complete resulting snapshots. Both policy classes, both orientations/seats, Stage/Smoke driver samples, filtering and legal Sneak transactions. |
| Frozen gameplay/decks/matrices | Every frozen tracked source/deck file compared. Only the enumerated interface changes are reversed for whole-module AST equality in engine/Pilot/runners; all other source/deck bytes unchanged. Stage and Smoke matrices/constants remain identical. |

Commands and final results:

```text
.venv/Scripts/python.exe -m pytest -q
1340 passed, 1 skipped, 1 warning in 36.19s

.venv/Scripts/python.exe -m ruff check .
All checks passed!

.venv/Scripts/python.exe -m ruff format --check .
All checked files already formatted.

git diff --check
(no output)

.venv/Scripts/python.exe scripts/validate_pilot_input_v2.py --output docs/cardcade/PILOT_INPUT_V2_CANDIDATE_VALIDATION.json
16 paired runs; CANDIDATE_VALIDATION_ONLY
```

The pytest warning concerns inability to write the local pytest cache, not a
validation failure. The 29 dedicated V2 interface tests are included in the full
suite. Paired execution is authorized **interface compatibility validation**,
not Pilot Fitness scoring, Smoke recalibration or balance evidence.

The initial driver sample did not open a Sneak decision window. Its options,
choices and snapshots matched, but coverage was incomplete. Dedicated legal
Sneak transactions for both seats closed that test-coverage gap without changing
policy or gameplay. The preserved final packet includes those cases.

## Historical test migration and baseline guards

Three existing historical plan-reconstruction tests initially rejected the
candidate's changed engine/Pilot/runner file hashes. They now explicitly opt
into `frozen_v1_source_files`, a test-only fixture that reads the exact frozen
source bytes with `git show` and hashes those bytes through the original Git
identity function. It does not fabricate expected digests. Remaining deck,
catalog and input checks still use the actual workspace inputs.

Production `plan()` and `build_smoke_manifest()` retain their original hash
guards. They continue to reject unaccepted V2 source identities. The frozen
hash constants and both production matrices are unchanged. This is not a new
Smoke/Stage execution baseline or authorization to run calibration.

## Review packet and reproduction

- `PILOT_INPUT_V2_CANDIDATE_VALIDATION.json`: source/deck LF SHA-256 identities,
  frozen Git blob identities, per-method policy AST digests, all paired case
  identities, complete options/choices and consequent snapshot digests, and
  runtime owner coverage counts.
- `PILOT_INPUT_V2_CANDIDATE_VALIDATION.traces.json.gz`: complete V1 and V2
  recorded option/choice sequences and snapshots, with a digest in the JSON.
  These are evaluator-side evidence and are never supplied to a Pilot.
- `scripts/validate_pilot_input_v2.py`: reproducible audit and comparison. V1
  source is extracted from the exact accepted-assessment commit into a temporary
  directory; V1/V2 run in separate processes, with the same inputs/seeds. The
  recorder observes arguments/results and delegates selection to the unchanged
  policy. It does not add evaluator state to a policy call.
- `tests/test_pilot_input_v2.py`: adversarial privacy, immutable snapshot,
  owner-binding, inspection, Stack and purity checks.
- SHA-256 sidecars authenticate the report, JSON and compressed traces.

The source audit verifies that V1 source/decks equal the gameplay freeze before
comparing V2. Candidate source files have their own identities; this packet does
not claim that changed interface files retain V1 whole-file hashes.

## Explicit limits and gates

Target announcement-zone provenance is unavailable in the bounded stored
structures, so `announcement_zone` is explicitly null. No history system is
introduced to recover it. Public announced choices, raw choice IDs and payment
history are omitted. A fixture depending on those unavailable observations,
graveyard/exile contents, a combat assignment/history or unsupported keyword
semantics requires a separate dependency assessment.

The finite paired corpus proves compatibility for the recorded executions; it
does not certify all future policies or all possible game states. The preserved
whole-source comparison additionally establishes that enumerator and execution
logic have not changed. No identity allocator or general hidden-information
noninterference framework was added.

**HQ acceptance remains pending.** The 96-fixture packet remains waiting for an
accepted V2 baseline. Pilot scoring, Action #33, calibration and Prototype 0.3
remain unauthorized/blocked. No quota, tactical oracle, Pilot fitness or balance
conclusion is asserted here.
