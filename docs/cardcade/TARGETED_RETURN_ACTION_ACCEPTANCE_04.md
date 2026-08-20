# Targeted Return to Hand Acceptance Audit #4

## Audit identity

- Evidence checkpoint: `46e3c684e10a91a4e697629f069b0b24786aa0f0`
- Audited corrected candidate fingerprint: `ecfbe696c863ce18cb4457482e96cbe35f3f9148`
- Historical Audit #1 SHA-256:
  `7deae80ca008f5e4c94dcbffe817090b595fb3a7bd470bfc58be06e853d9ed3c`
- Historical Audit #2 SHA-256:
  `5e07fd3ad3487726cbef6eb5ff93dc0ccb562e919d230320b754827c69adbec0`
- Historical Audit #3 SHA-256:
  `dc0894a06bb4b23b16cceceee39f22e31b7241bf60a4d72bfd9b1c51a32898aa`
- Audit mode: evidence-only; implementation, tests, decks, and historical reports were not modified

## Executive finding

The corrected candidate resolves all three historical rejection blockers:

1. executable Return payloads cannot upgrade unsupported parent, preceding, or follow-up semantics;
2. broad/non-executable Return forms retain an identifiable clause and independently classified
   surrounding semantics;
3. `ReturnClause` is now a lossless representation of the complete original fragment around one
   absolute clause span, while normalized semantic regions remain separate classification inputs.

No material correctness, architecture, evidence, or deterministic-execution blocker remains for
the declared bounded Action.

## Lossless clause evidence

An independent enumeration of all 38 recognized Return fragments verified every instance against
the complete authoritative Oracle fragment. All passed:

- `0 <= start < end <= len(original)`;
- `original[start:end] == clause.text`;
- `original[:start] == clause.preceding_text`;
- `original[end:] == clause.following_text`;
- `preceding_text + clause.text + following_text == original`;
- repeated interpretation produces an identical span and clause value.

No normalized or stripped text appears in the raw evidence fields. Original punctuation, activation
costs, reminder text, and timing suffixes remain literal.

The three Audit #3 cases now preserve:

- Northampton Farm raw preceding text begins with
  `{2}, {T}, Sacrifice this land:` and includes the preceding return-to-battlefield instruction;
- Together Forever raw preceding text begins with `{1}:` and retains its choice/delayed-condition
  text;
- Prehistoric Pet raw preceding text is `{1}{W}, {T}: ` and raw following text is
  `. Activate only during your turn.`.

The interpreter separately stores `preceding_semantics` and `following_semantics`. These normalized
regions omit parent syntax only when it is deliberately classified by activated-ability cost/timing
logic. Altering normalization cannot mutate the original fragment, absolute span, or raw evidence.
Conversely, supported activation cost and timing text in raw evidence does not become an unsupported
Return preceding/follow-up limitation.

## Historical rejection verification

### Reject #1 — semantic composition

Activated-ability interpretation calls the generic `return_to_hand_semantics` result and contains no
second Return grammar. Generic limitations survive parent/child composition. Renamed adversarial
fixtures independently confirm that supported Return payloads remain incomplete under unsupported
parents and with unsupported text before, after, or on both sides.

### Reject #2 — compound boundaries

Broad recognized/non-executable forms locate a Return-to-hand clause without claiming payload
execution. Representative trigger, condition, conjunction, multiple-sentence, reminder,
multiple-Return, punctuation/case, and false-positive probes retain truthful boundaries and
limitations.

The required corpus examples independently classify as follows. Flags are payload / parent /
preceding / follow-up / full:

- Nobody: no / no / no / no / no — ETB before; Scry/reminder after.
- Karai, Future of the Foot: no / no / no / no / no — combat-damage trigger before; conditional
  `instead` return after.
- Northampton Farm: no / no / no / yes / no — preceding return-to-battlefield instruction;
  punctuation-only follow-up.
- Together Forever: no / no / no / yes / no — preceding choice and delayed dies condition;
  punctuation-only follow-up.
- Ashcoat of the Shadow Swarm: no / no / no / no / no — trigger/optional mill/condition before;
  mill reminder after.
- Turtles in Time: no / no / yes / no / no — no preceding semantics; shuffle/draw after.

Each unsupported region has an explicit limitation. Recognition, payload executability, and full
fragment support remain distinct.

### Reject #3 — authoritative raw representation

Corpus-wide reconstruction found zero mismatches. Raw `ReturnClause` text and absolute offsets now
refer to the same complete source fragment. Normalized effect regions are separately named and used
only for classification.

## Architecture and special-case audit

The authoritative interpretation direction is:

`Oracle fragment → ReturnClause + normalized Return semantics → ReturnToHandProgram + SemanticCoverage → activated-ability composition → engine option/transaction`

Inspection found:

- no duplicate Return parser in activated interpretation or engine execution;
- no card-name or Prehistoric Pet dispatch;
- no deck/roster dispatch;
- no Acceptance or seed special case;
- no Return dependency in generic `SemanticCoverage`;
- no engine/runtime dependency in `ReturnClause` or Return interpretation.

## Authoritative coverage regeneration

Independent enumeration of the 472-print / 332-Oracle-object snapshot reproduced:

- recognized: **37 objects / 38 fragments**;
- bounded executable: **1 / 1**;
- fully supported: **1 / 1**;
- sole executable/full member: **Prehistoric Pet**.

Digests reproduced:

- recognized:
  `59bb7f7c2a44fea44e7b94b5f47e6030beb2b25205b009f350a67b35a9b9cd59`;
- executable/full:
  `8de28e00a41e8fedc23667860d223f241c22f6dbac89b12cd218cb5bb3aeca95`.

Prehistoric Pet earns full support without a special case. Its represented chain consists of a
supported activated-ability parent, supported active-turn timing, transactional fixed `{1}{W}` and
`{T}` costs, one other creature controlled by the activating player, the bounded Return payload,
and no unsupported normalized surrounding semantics. Its generic and composed coverage values are
fully supported with no limitations.

## Transaction integrity

Code inspection, focused regressions, and executable probes reconfirm the complete represented
chain:

`legal ActionOption → target selected at announcement → transactional payment → authoritative Stack object → two-player Priority/pass → resolution target revalidation → battlefield-to-owner's-hand movement`

The candidate preserves:

- immutable engine-generated legal targets and deterministic ordering;
- announcement-time and resolution-time legality checks;
- fabricated, equal-valued, stale, wrong-zone, self, opponent-controlled, and noncreature rejection;
- atomic failure before payment/Stack mutation;
- paid costs remaining paid if the target becomes illegal later;
- owner rather than temporary controller determining the destination hand;
- new runtime identity after movement;
- reset of counters, damage, tapped/controller state, and temporary battlefield effects;
- token cessation at the post-resolution SBA boundary;
- Stack/Priority separation and no immediate-resolution shortcut;
- rejection of duplicate resolution.

## Acceptance replay

Seeds 7001–7005 were executed twice. Duplicate snapshots were byte-equivalent.

| Seed | Winner / ending turn | Unsupported events / seed pairs | Returns |
| ---: | --- | ---: | ---: |
| 7001 | Raphael / 16 | 10 / 10 | 0 |
| 7002 | Raphael / 16 | 6 / 5 | 3 |
| 7003 | Leonardo / 19 | 12 / 10 | 0 |
| 7004 | Leonardo / 21 | 13 / 11 | 0 |
| 7005 | Raphael / 16 | 6 / 5 | 5 |

Aggregate evidence:

- **47 unsupported events / 16 exact pairs**;
- eight successful Returns;
- 16 activation announcements, payments, Stack placements, and resolutions;
- 32 Priority grants and 32 passes;
- 13 Scry transactions;
- 17 Deal Damage transactions;
- one block-restriction rejection;
- zero invariant violations.

The lossless-evidence correction does not change telemetry because it changes neither semantic
coverage nor execution. The six Audit #2 corpus fragments are not executed in Acceptance Match
#001.

Seed 7002 independently retains three legal Returns: Leonardo, Big Brother on turn 9 and two later
Prehistoric Pet objects on turns 13 and 15. Leonardo subsequently loses to Raphael's combat damage
on turn 16. The validated causal chain is unchanged.

## Validation

- Full suite: **377 passed / 1 skipped**.
- Targeted Return: **33 passed**.
- Lossless Return/classifier/span subset: **19 passed**.
- Activated Ability/Priority: **30 passed**.
- SemanticCoverage: **5 passed**.
- Stack/cost/boundary: **23 passed**.
- Token/SBA: **49 passed**.
- Scry: **19 passed**.
- Deal Damage: **29 passed**.
- Strike/combat/state: **77 passed**.
- Card-data integrity: **5 passed**.
- Ruff format check: clean, 40 files.
- Ruff check: clean.
- `git diff --check`: clean.
- Candidate fingerprint independently reproduced:
  `ecfbe696c863ce18cb4457482e96cbe35f3f9148`.
- All three historical rejection reports remain byte-identical at their recorded SHA-256 values.

## Recommendation

**ACCEPT — corrected bounded Targeted Return to Hand is suitable to bank.**
