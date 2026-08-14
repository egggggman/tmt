# Create Token Action Acceptance Audit 03

Audit date: 2026-08-14 EDT

Committed baseline: `2218b68f0786dc01e0155c7388a769e9ab927086`

Candidate: corrected, uncommitted Create Token Action and reusable semantic-support contract.

Historical evidence preserved unchanged:

- `docs/cardcade/CREATE_TOKEN_ACTION_ACCEPTANCE.md`;
- `docs/cardcade/CREATE_TOKEN_ACTION_ACCEPTANCE_02.md`.

This was an evidence-only audit. The implementation and tests were not modified. This report is the
only audit write.

## Recommendation

ACCEPT

Create Token and the reusable semantic-support contract are suitable to bank. Independent import,
AST, type, executable, membership, transaction, replay, and validation evidence found no remaining
material blocker.

## Repository and candidate integrity

- local HEAD was exactly `2218b68f0786dc01e0155c7388a769e9ab927086`;
- local branch was `agent/cardcade-create-token`, tracking the matching committed remote HEAD;
- the candidate remained uncommitted;
- both prior rejection reports remained unchanged;
- no deck, prototype, pilot, calibration, smoke, or unrelated Action change was found;
- `git diff --check` passed before this report was created.

## Primary acceptance: Action-generic semantic coverage

### Dependency inspection

`src/tmnt_design_studio/semantic_coverage.py` imports only:

- `__future__.annotations`;
- `dataclasses.dataclass`.

AST and source inspection found no import, annotation, field, helper call, `isinstance` check,
attribute lookup, or hidden program introspection involving:

- `TokenCreationProgram`;
- token definitions or token grammar;
- the card interpreter;
- the rules engine or runtime state;
- any other Action-specific program.

No reverse dependency from generic semantic coverage to Create Token exists. The actual dependency
direction is:

`CardInterpreter` token interpretation → `SemanticCoverage`.

### Generic state and derivation

`SemanticCoverage` has exactly four stored fields:

- `payload_executable: bool`;
- `parent_executable: bool`;
- `followup_executable: bool`;
- `limitations: tuple[str, ...]`.

It validates only that limitations are unique, nonempty strings. It contains no program field and
does not inspect an Action object. `fully_supported` is derived solely as the conjunction of the
three generic support booleans.

An independent executable probe created a dummy Draw interpretation containing a
`DummyDrawProgram` and the same `SemanticCoverage` value. That fixture imported and constructed no
Create Token type. With payload supported, parent unsupported, and follow-up supported, full support
correctly remained false and the dummy parent limitation remained intact.

### Create Token conversion

Create Token retains its Action-specific `TokenCreationProgram` in `InterpretedTokenSemantics` and
pairs it with a separately constructed `SemanticCoverage`. The generic value neither stores nor
introspects that program.

An independent conditional-Food probe produced:

- token payload executable: true;
- parent/context executable: false;
- follow-up executable: false;
- fully supported: false;
- limitations, in exact order:
  `token_condition_context_not_implemented`,
  `token_activated_ability_not_implemented`.

The Action-specific forwarding view and generic limitations tuple were exactly equal. An executable
child payload therefore cannot upgrade an unsupported parent through the generic contract.

No concrete reverse dependency or generic-coverage correctness defect remains.

## Create Token regression integrity

### Exact coverage

Independent enumeration against the authoritative 472-print / 332-Oracle-object snapshot reproduced:

| Coverage | Frozen roster | Full pool |
| --- | ---: | ---: |
| Recognized | 21 cards / 10 decks | 66 objects / 71 fragments |
| Bounded payload executable | 17 cards / 10 decks | 49 objects / 50 fragments |
| Parent + payload + follow-up fully supported | not separately claimed | 6 objects / 6 fragments |

Exact membership digests matched:

- recognized `(oracle_id, fragment)` set:
  `c7cc01b61f3498a8cdb2576532d572815e852c7c47efc6af3a45579aabbc92f8`;
- bounded-executable `(oracle_id, fragment)` set:
  `3fdec6260d5627e3e2c0e57b9a8e56b71ea35e59c51efcbb574de10f67254d55`.

No coverage classification or grammar changed during the generic extraction.

### Parent-context classifications

All 18 first-audit fragments retained their classifications:

Supported parent, payload, and follow-up — six:

- Baxter Stockman;
- Biogenic Ooze's creature-ETB fragment;
- Jennika, Bad Apple Big Sister;
- Mechanized Ninja Cavalry;
- Mighty Mutanimals;
- Slash, Reptile Rampager.

Unsupported parent and/or follow-up — twelve:

- Waste Not — trigger context;
- Rat King, Pale Piper — trigger context;
- Biogenic Ooze's activated fragment — activation context;
- Ravenous Robots — trigger context;
- Dark Leo & Shredder — trigger context and follow-up;
- Turtle Blimp — trigger context;
- Rat King, Verminister — condition context and follow-up;
- Uneasy Alliance — activation context;
- Foot Mystic — condition context;
- Lord Dregg, Insect Invader — condition context;
- Mouser Attack! — choice context;
- Mouser Foundry — trigger context.

Every non-fully-supported fragment retained explicit limitations. Engine delivery remained gated on
both executable payload and executable parent/context.

### Plague of Vermin and UNKNOWN

Plague of Vermin remained generically recognized and non-executable with both exact reasons:

- `variable_token_quantity_not_implemented`;
- `token_iterative_choice_context_unknown`.

Its UNKNOWN classification did not become supported. The other six preserved UNKNOWN objects were
unchanged.

### Explicit exclusions

The exclusion inventory remained unchanged:

- token copies: 10 fragments, `token_copy_not_implemented`;
- variable quantities: 9 fragments, `variable_token_quantity_not_implemented`;
- replacement effects: 1 fragment, `token_replacement_effect_not_implemented`;
- tapped-and-attacking: 1 fragment, `token_attacking_context_not_implemented`;
- attach, delayed-destruction, granted-haste, and compound follow-ups remained explicit;
- Food, Mutagen, Treasure, and Clue activation remained
  `token_activated_ability_not_implemented`.

Creating a predefined artifact token still produced no legal activation option, sacrifice, life
change, card draw, mana, counter placement, or graveyard movement.

### Card-name and fallback audit

No source-card-name dispatch, Acceptance Match branch, roster/deck branch, seed condition, silent
fallback, or new hard-coded semantic special case was introduced. Create Token remains derived from
Oracle `create` / `creates` grammar and generic characteristics. Predefined token-type facts are not
source-card dispatch.

## Transaction regression probes

Focused probes confirmed the architecture extraction did not alter runtime behavior:

- fixed quantity three produced three unique authoritative IDs;
- owner and controller matched the player under whose control the tokens entered;
- tapped state, black color, artifact/creature types, Ninja subtype, 1/1 P/T, and flying persisted;
- summoning sickness and later legal combat behavior remained correct;
- counters and temporary layered modifiers evaluated 1/1 → 6/2 → 3/3 after cleanup;
- battlefield tokens persisted through cleanup;
- typed batch and creature-entry events remained intact;
- fabricated equal-valued references were rejected;
- zone movement, SBA cessation, and post-cessation rejection remained correct;
- invalid construction remained atomic;
- deterministic identity, snapshots, and event ordering remained stable.

## Acceptance Match #001

Every seed was replayed twice. Duplicate rendered snapshots were byte-equivalent.

| Seed | Winner / ending turn | Unsupported events / exact pairs | Block rejections | Invariant violations | Token transactions |
| ---: | --- | ---: | ---: | ---: | ---: |
| 7001 | Raphael / 16 | 14 / 13 | 0 | 0 | 0 |
| 7002 | Leonardo / 17 | 14 / 8 | 2 | 0 | 0 |
| 7003 | Leonardo / 17 | 19 / 13 | 0 | 0 | 0 |
| 7004 | Leonardo / 21 | 21 / 18 | 1 | 0 | 0 |
| 7005 | Raphael / 16 | 13 / 8 | 3 | 0 | 0 |
| **Aggregate** | expected trajectories | **81 / 23** | **6** | **0** | **0** |

Zero acceptance token transactions means Acceptance Match #001 does not independently exercise
Create Token. Create Token execution evidence comes from the dedicated corpus and adversarial tests.

## Validation

- full suite: **233 passed / 1 skipped**;
- dedicated Create Token tests: **49 passed**;
- generic semantic-coverage tests: **5 passed**;
- authoritative card-data integrity tests: **5 passed**;
- Ruff format check: passed, 35 files already formatted;
- Ruff check: passed;
- `git diff --check`: passed before this report was created;
- deterministic duplicate acceptance replay: passed for all seeds.

The successful tests agree with independent structural and executable evidence. Acceptance is based
on the absence of a concrete reverse dependency or semantic defect, not on test results alone.
