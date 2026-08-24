# Action #15 — Permanent-Leaves-Battlefield +1/+1 Counter Acceptance Audit #2

Date: 2026-08-24  
Candidate fingerprint: `398aeb6fafdc46dc2ec766d4eff8631989b0fcfa`  
Audit #1 REJECT SHA-256: `1473f5c6d816a2fa57231c141414c0887004aae2c2338b5203dc2aee0ab6f8c3`

## Verdict

**ACCEPT — corrected bounded permanent-leaves-battlefield +1/+1 counter action is suitable to bank with its documented coverage.**

## Immutable candidate and historical evidence

The audit began and ended with the same four candidate-file hashes:

| Path | SHA-256 |
| --- | --- |
| `src/tmnt_design_studio/card_interpreter07.py` | `be4d2a7bebc7933b812c36d9b78f3286460245c47ca4004f60be46ffaeb90ea8` |
| `src/tmnt_design_studio/engine07.py` | `09d81203ec714fc0effbde9cb85926f60d0a6725786fa1c2afbb458f4fe8e66a` |
| `src/tmnt_design_studio/smoke01.py` | `eb4ccfe42f0763b5089cbf1a27742bf00e429e752c503ea2678658e79dcfe837` |
| `tests/test_permanent_left_counter_action.py` | `c1d6004dcadd991f7154f6094456d6f888f39a0a6f094d5075792a57a0328f60` |

The path-sorted candidate fingerprint reconstructed exactly as
`398aeb6fafdc46dc2ec766d4eff8631989b0fcfa`. Audit #1 remained byte-identical at
`1473f5c6d816a2fa57231c141414c0887004aae2c2338b5203dc2aee0ab6f8c3`.

Canonical Git-clean identities independently reconstructed as:

- Engine: `bb2ecc54bb815839a5ec400e53fd1b9feaec9d67`;
- Interpreter: `5dc2e210bafcc77520b7c378c3eef384b9ccac9a`.

## Audit #1 blocker closure

The recognizer was attacked with synthetic definitions rather than inferred solely from the frozen
corpus.

| Probe | Reconstructed result |
| --- | --- |
| exact `this source` | recognized, executable, fully supported |
| exact matching card name | recognized, executable, fully supported |
| literal `this permanent` | not recognized as Action #15 |
| unrelated card name | recognized shape only; not executable/full; `permanent_left_counter_source_mismatch` retained |
| Instant with otherwise exact text | recognized shape only; not executable/full; `permanent_left_counter_source_is_not_a_permanent` retained |
| Sorcery with otherwise exact text | same explicit nonpermanent-source limitation |
| Artifact, Battle, Creature, Enchantment, Land, and Planeswalker definitions | executable/full when the exact grammar and self-reference requirements also match |

Near-neighbor probes for dies-only, creature-only, `one or more`, optional, opponent-scoped,
different counter amount/type, self-departure, and altered instruction forms remained unsupported.
No synthetic probe entered the frozen fully-supported corpus.

The authoritative frozen card-data reconstruction contains exactly one member:

- Super Shredder;
- Oracle ID `b7ee76bf-d15a-489e-8f05-414788f8f649`;
- TMT collector numbers `83`, `217`, `285`, and `295`.

## Gameplay lifecycle re-audit

Independent adversarial probes and the dedicated Action suite reconstructed the bounded lifecycle:

`authoritative battlefield departure → another-permanent qualification/LKI → trigger → Stack → Priority/pass → resolution → exactly one +1/+1 counter on the authoritative source incarnation`.

The probes established:

- creature and noncreature departures qualify across the represented battlefield-to-graveyard,
  battlefield-to-hand, and battlefield-to-library paths;
- tokens use their authoritative runtime identities and remain reconstructible after leaving;
- each qualifying permanent in a simultaneous departure creates its own trigger;
- the source never triggers for its own departure, while another permanent leaving simultaneously
  is still observed from the pre-departure state;
- multiple sources independently observe the same departure;
- ownership does not restrict the trigger, and the trigger retains its controller from creation;
- a later source-controller change does not relink the trigger;
- source departure before resolution prevents counter placement on an absent source;
- a later battlefield incarnation of the same card cannot receive a counter from an old
  incarnation's trigger;
- multiple valid resolved triggers accumulate exactly one +1/+1 counter apiece and feed the
  existing power/toughness and SBA machinery;
- trigger work created during another Stack object's resolution remains pending until the generic
  post-resolution delivery boundary;
- stale, fabricated, relinked, and borrowed departure/trigger evidence fails both invariant and
  resolution authentication.

The recognizer-only correction did not alter this previously audited engine lifecycle. Searches and
diff inspection found no Super Shredder, deck, matchup, Pilot, Stage #002, or Smoke-specific gameplay
dispatch.

## Regression and determinism evidence

- dedicated Action #15 suite: **36 passed**;
- independent lifecycle/adversarial probes: **9 passed**;
- focused trigger/Stack/conformance/Action regressions: **135 passed**;
- full suite: **683 passed / 1 skipped**;
- Ruff check: clean;
- Ruff format check: 50 files already formatted;
- `git diff --check`: clean.

Acceptance #001 seeds 7001–7005 were replayed twice. Each seed's duplicate JSON artifacts were
byte-identical, there were zero invariant-violation events, and the accepted trajectories remained:

| Seed | Result |
| --- | --- |
| 7001 | Raphael T14 |
| 7002 | Raphael T18 |
| 7003 | Leonardo T19 |
| 7004 | Leonardo T43 |
| 7005 | Raphael T16 |

No Smoke game was run. The audit modified no candidate implementation or test file and made no
commit.
