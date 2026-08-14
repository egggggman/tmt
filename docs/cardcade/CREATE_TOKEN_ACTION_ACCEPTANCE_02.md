# Create Token Action Acceptance Audit 02

Audit date: 2026-08-14 EDT

Committed baseline: `2218b68f0786dc01e0155c7388a769e9ab927086`

Candidate: corrected, uncommitted Create Token implementation and tests.

Historical evidence: `CREATE_TOKEN_ACTION_ACCEPTANCE.md` remains unchanged as the first rejection
record. This audit did not modify implementation, tests, decks, prototypes, pilots, calibration, or
smoke evidence. This report is the only audit write.

## Recommendation

REJECT

Both original behavioral rejection blockers are resolved. Exact coverage membership, semantic
boundary behavior, engine delivery gating, token transactions, exclusions, deterministic acceptance
replay, and all validation gates pass.

One explicit architecture acceptance criterion remains unmet: the semantic-support contract is not
reusable by future Actions. `TokenSemanticCoverage` contains a `TokenCreationProgram` and derives
payload and follow-up state directly from token-specific `executable` and `retained_limitation`
fields. A future Draw, Damage, Counter, or other Action cannot use this contract without copying its
shape or changing it. This is a Create Token-specific coverage wrapper, despite embodying the right
four-level distinction.

The smallest evidence-backed correction is to extract a generic semantic-coverage value, parameterized
by an Action payload but storing generic `payload_executable`, `parent_executable`,
`followup_executable`, `fully_supported`, and `limitations` state. Create Token should populate that
generic value with its `TokenCreationProgram`. Existing transaction, parser, engine gating,
coverage membership, telemetry, and tests need not change behavior. Add one structural test proving
the contract can represent a non-token dummy Action without depending on token-program fields.

## Candidate and repository integrity

- local HEAD: `2218b68f0786dc01e0155c7388a769e9ab927086`;
- branch: `agent/cardcade-create-token` tracking the matching remote committed HEAD;
- pre-report candidate files: modified `card_interpreter07.py`, modified `engine07.py`, and untracked
  `test_create_token_action.py`;
- preserved first rejection report remained untracked and unchanged;
- no deck, prototype, pilot, calibration, smoke, or unrelated Action change was found;
- `git diff --check` passed before this report was added.

## Original blocker 1: semantic support boundary

The corrected implementation explicitly exposes:

- `payload_executable`;
- `parent_executable` and `parent_limitation`;
- `followup_executable`;
- `fully_supported`;
- an ordered, deduplicated limitations tuple.

`unsupported_fragments()` emits every limitation attached to a recognized token fragment. A corpus
probe confirmed that all 65 non-fully-supported recognized fragments have at least one explicit
limitation and that the limitations are present in unsupported reporting. Only six fragments are
fully supported and omit unsupported telemetry.

Engine delivery independently revalidates both `payload_executable` and `parent_executable` before
placing a triggered token ability or executing the selected Alliance token mode. Unsupported
conditions, triggers, activations, and choices were presented to represented ETB and attack paths;
no transaction was attributed to any unsupported fragment.

### Reinspection of the 18 first-audit fragments

Per-fragment event attribution was used because Biogenic Ooze contains one supported ETB fragment
and a separate unsupported activation.

| Oracle object / fragment shape | Payload | Parent | Follow-up | Fully supported | Exact transactions from represented ETB/attack probes | Explicit limitation |
| --- | --- | --- | --- | --- | ---: | --- |
| Biogenic Ooze — creature ETB | yes | yes | yes | yes | 1 | none |
| Jennika, Bad Apple Big Sister — self ETB | yes | yes | yes | yes | 1 | none |
| Slash, Reptile Rampager — attacks | yes | yes | yes | yes | 1 | none |
| Baxter Stockman — self ETB | yes | yes | yes | yes | 1 | none |
| Mechanized Ninja Cavalry — creature ETB | yes | yes | yes | yes | 1 | none |
| Mighty Mutanimals — creature ETB | yes | yes | yes | yes | 1 | none |
| Waste Not — discard trigger | yes | no | yes | no | 0 | `token_trigger_context_not_implemented` |
| Rat King, Pale Piper — leaves trigger | yes | no | yes | no | 0 | `token_trigger_context_not_implemented` |
| Biogenic Ooze — activated ability | yes | no | yes | no | 0 | `token_activation_context_not_implemented` |
| Ravenous Robots — artifact-cast trigger | yes | no | yes | no | 0 | `token_trigger_context_not_implemented` |
| Dark Leo & Shredder — combat-damage trigger and life-loss follow-up | yes | no | no | no | 0 | trigger context; follow-up semantics |
| Turtle Blimp — noncreature Vehicle ETB | yes | no | yes | no | 0 | `token_trigger_context_not_implemented` |
| Rat King, Verminister — conditional end step and counter follow-up | yes | no | no | no | 0 | condition context; follow-up semantics |
| Uneasy Alliance — activated ability | yes | no | yes | no | 0 | `token_activation_context_not_implemented` |
| Foot Mystic — conditional ETB | yes | no | yes | no | 0 | `token_condition_context_not_implemented` |
| Lord Dregg, Insect Invader — conditional end step | yes | no | yes | no | 0 | `token_condition_context_not_implemented` |
| Mouser Attack! — unsupported modal delivery | yes | no | yes | no | 0 | `token_choice_context_not_implemented` |
| Mouser Foundry — artifact enter/leave trigger | yes | no | yes | no | 0 | `token_trigger_context_not_implemented` |

The six supported parents created exactly one correctly attributed token batch each. The twelve
unsupported parents created zero batches attributed to their fragments and retained every expected
limitation. The original silent-upgrade blocker is resolved.

## Original blocker 2: recognition universe

An independent scan used a separate case-insensitive Oracle grammar,
`creates? ... tokens?`, over one representative print for every Oracle ID. It did not use the
candidate's `CREATE_TOKEN` regular expression to choose the recognition population.

The independent set and candidate set were identical:

- 66 recognized Oracle objects;
- 71 recognized Oracle fragments;
- zero missing fragments;
- zero extra fragments;
- 49 objects with a bounded executable token payload;
- 50 bounded executable payload fragments;
- 6 objects / 6 fragments with supported parent, payload, and follow-up.

Stable exact-membership digests also matched:

- recognized `(oracle_id, fragment)` set:
  `c7cc01b61f3498a8cdb2576532d572815e852c7c47efc6af3a45579aabbc92f8`;
- bounded executable `(oracle_id, fragment)` set:
  `3fdec6260d5627e3e2c0e57b9a8e56b71ea35e59c51efcbb574de10f67254d55`.

### Exact full-pool recognized object membership

April O'Neil, Human Element; April O'Neil, Live on the Scene; Baxter Stockman; Big Apple,
3 a.m.; Big Mother Mouser; Biogenic Ooze; Casey & Raph, Hotheads; Chrome Dome; Coin of Mastery;
Courier of Comestibles; Crustacean Commando; Dark Leo & Shredder; Donatello, Gadget Master;
Doubling Season; Endless Foot Assault; Featherbrained Filcher; Foot Chopper; Foot Mystic; Genghis
Frog; Here Comes a New Hero!; Improvised Arsenal; Jennika, Bad Apple Big Sister; Lita, Little
Orphan Amphibian; Lord Dregg, Insect Invader; Mechanized Ninja Cavalry; Michelangelo, Mutant BFF;
Michelangelo, Weirdness to 11; Michelangelo, the Heart; Mighty Mutanimals; Mona Lisa, Ever
Adaptable; Mouser Attack!; Mouser Foundry; Mutagen Man, Living Ooze; Mutant Chain Reaction; Ninja
Pizza; Old Hob, Alleycat Blues; Ooze Spill; Party Dude; Pizza Face, Gastromancer; Plague of Vermin;
Raphael, the Muscle; Rat King, Pale Piper; Rat King, Verminister; Ravenous Robots; Ray Fillet, Man
Ray; Return to the Sewers; Roadkill Rodney; Sally Pride, Lioness Leader; Shellshock; Shredder,
Shadow Master; Slash, Reptile Rampager; Slithering Cryptid; Splinter & Leo, Father & Son; Splinter,
the Mentor; Tainted Treats; Tempestra, Dame of Games; The Cloning of Shredder; The Last Ronin's
Technique; The Ooze; Tokka & Rahzar, Unsupervised; Triceraton Commander; Turtle Blimp; Uneasy
Alliance; Waste Not; Wooden Cane; Zoo Escapees.

### Exact bounded-executable object membership

April O'Neil, Human Element; April O'Neil, Live on the Scene; Baxter Stockman; Biogenic Ooze;
Casey & Raph, Hotheads; Coin of Mastery; Courier of Comestibles; Crustacean Commando; Dark Leo &
Shredder; Featherbrained Filcher; Foot Chopper; Foot Mystic; Genghis Frog; Jennika, Bad Apple Big
Sister; Lita, Little Orphan Amphibian; Lord Dregg, Insect Invader; Mechanized Ninja Cavalry;
Michelangelo, Mutant BFF; Michelangelo, Weirdness to 11; Michelangelo, the Heart; Mighty Mutanimals;
Mona Lisa, Ever Adaptable; Mouser Attack!; Mouser Foundry; Mutant Chain Reaction; Ninja Pizza; Old
Hob, Alleycat Blues; Ooze Spill; Party Dude; Pizza Face, Gastromancer; Raphael, the Muscle; Rat King,
Pale Piper; Rat King, Verminister; Ravenous Robots; Ray Fillet, Man Ray; Return to the Sewers;
Roadkill Rodney; Slash, Reptile Rampager; Slithering Cryptid; Splinter & Leo, Father & Son; Splinter,
the Mentor; Tainted Treats; The Ooze; Tokka & Rahzar, Unsupervised; Turtle Blimp; Uneasy Alliance;
Waste Not; Wooden Cane; Zoo Escapees.

### Exact fully supported object membership

- Baxter Stockman;
- Biogenic Ooze, creature-ETB fragment only;
- Jennika, Bad Apple Big Sister;
- Mechanized Ninja Cavalry;
- Mighty Mutanimals;
- Slash, Reptile Rampager.

### Frozen-roster membership

Recognized, 21 cards across all ten decks:

Courier of Comestibles; Crustacean Commando; Donatello, Gadget Master; Foot Mystic; Improvised
Arsenal; Lita, Little Orphan Amphibian; Michelangelo, Mutant BFF; Michelangelo, Weirdness to 11;
Mighty Mutanimals; Mouser Attack!; Mouser Foundry; Mutagen Man, Living Ooze; Mutant Chain Reaction;
Ooze Spill; Ravenous Robots; Ray Fillet, Man Ray; Return to the Sewers; Slithering Cryptid; Tainted
Treats; The Last Ronin's Technique; Zoo Escapees.

Bounded payload, 17 cards across all ten decks: the same set excluding Donatello, Gadget Master;
Improvised Arsenal; Mutagen Man, Living Ooze; and The Last Ronin's Technique.

### Plague of Vermin and UNKNOWN preservation

Plague of Vermin is generically recognized through `creates`, not a card-name branch. It remains
non-executable with both required classifications:

- `variable_token_quantity_not_implemented`;
- `token_iterative_choice_context_unknown`.

It remains one of the seven UNKNOWN objects with Command Tower, Arcane Signet, Exotic Orchard,
Chromatic Lantern, Fast Forward, and Double Jump // Flying Kick. No UNKNOWN object became supported.

## Token transaction regression

Independent in-memory probes, separate from the candidate tests, confirmed:

- a fixed quantity of three produced exactly three fresh, distinct runtime IDs;
- owner and controller both matched the player under whose control the tokens entered;
- tapped state was preserved;
- the derived definition preserved black color, `Artifact Creature — Ninja`, 1/1 P/T, and flying;
- creature tokens were initially summoning sick and became legal attackers on a later controller
  turn;
- two +1/+1 counters and a temporary +3/-1 effect evaluated 1/1 to 6/2, then cleanup removed only
  the temporary modifier and left 3/3;
- battlefield tokens persisted through cleanup;
- one typed token-batch event and three typed creature-entry events were emitted;
- fabricated equal-valued objects were rejected;
- a nonbattlefield token could not move again before the SBA boundary;
- the token ceased at the SBA boundary and post-cessation references were rejected;
- an invalid token definition caused no mutation and consumed no identity;
- duplicate seeded creation produced equal snapshots and event ledgers.

The correction did not damage the original sound token transaction.

## Explicit exclusions

Independent full-pool enumeration found:

| Exclusion | Result |
| --- | --- |
| Token copies | 10 fragments explicitly `token_copy_not_implemented` |
| Variable quantities | 9 fragments explicitly `variable_token_quantity_not_implemented`, including Plague of Vermin |
| Replacement effects | 1 fragment explicitly `token_replacement_effect_not_implemented` |
| Tapped-and-attacking | 1 fragment explicitly `token_attacking_context_not_implemented` |
| Attach / delayed destruction / granted haste / other follow-ups | Wooden Cane, Foot Chopper, Dark Leo & Shredder, Rat King, Verminister, and Old Hob retain follow-up limitations |
| Food / Mutagen / Treasure / Clue activation | 31 creation fragments retain `token_activated_ability_not_implemented` |

Creating Food, Mutagen, Treasure, or Clue produced no legal option referencing that token, no
sacrifice, no life change, and no graveyard object. Creation does not imply use support.

## Architecture and special-case inspection

No source-card-name comparison, roster/deck branch, seed branch, Acceptance Match special case,
silent fallback, TODO, or FIXME was found in the Create Token interpreter or engine delivery paths.
The `create` / `creates` grammar is Oracle-derived. Predefined Food, Mutagen, Treasure, and Clue
names are token-definition facts, not source-card dispatch.

The engine/interpreter boundary is sound: the interpreter derives immutable token and coverage
constructs; the engine revalidates coverage, owns runtime identity and zones, places triggers on the
authoritative stack, and mutates state. The pilot and acceptance runner do not create tokens or make
unsupported contexts executable.

The remaining blocker is solely the contract's direct dependence on `TokenCreationProgram`, which
prevents direct reuse by future Actions.

## Acceptance Match #001

Each seed was executed twice. Rendered duplicate snapshots were byte-equivalent.

| Seed | Winner / ending turn | Unsupported events / exact pairs | Block rejections | Invariant violations | Token transactions |
| ---: | --- | ---: | ---: | ---: | ---: |
| 7001 | Raphael / 16 | 14 / 13 | 0 | 0 | 0 |
| 7002 | Leonardo / 17 | 14 / 8 | 2 | 0 | 0 |
| 7003 | Leonardo / 17 | 19 / 13 | 0 | 0 | 0 |
| 7004 | Leonardo / 21 | 21 / 18 | 1 | 0 | 0 |
| 7005 | Raphael / 16 | 13 / 8 | 3 | 0 | 0 |
| **Aggregate** | expected trajectories | **81 / 23** | **6** | **0** | **0** |

Zero acceptance token transactions means Acceptance Match #001 does not itself provide Create Token
execution evidence. Execution evidence comes from the dedicated corpus and adversarial probes.

## Validation

- full suite: **227 passed / 1 skipped**;
- dedicated Create Token suite: **48 passed**;
- authoritative card-data integrity: **5 passed**;
- Ruff format check: passed, 33 files already formatted;
- Ruff check: passed;
- `git diff --check`: passed before this report was created;
- deterministic acceptance duplicate replay: passed for all seeds;
- acceptance aggregate: 81 unsupported events / 23 exact pairs, six block rejections, zero invariant
  violations, and zero token transactions.

The corrected candidate is behaviorally sound, but it is not suitable to bank until the semantic
coverage value is made Action-generic as required by this audit's architecture gate.
