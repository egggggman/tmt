# Action #15 — Permanent-Leaves-Battlefield +1/+1 Counter Acceptance Audit #1

Date: 2026-08-24  
Candidate fingerprint: `0169af2bc6ce816743d91f4935ed61b87e72256f`  
Audit mode: evidence-only; the four candidate files were not modified or committed; Smoke Stage 0.1 was not run.

## Verdict

**REJECT.** The authoritative departure, “another,” trigger, Stack/Priority, incarnation-identity, simultaneous-departure, and counter-resolution implementation is strong and passed independent adversarial reconstruction. The exact recognizer nevertheless has two related material scope defects:

1. it fully supports the unrequested literal self-reference `this permanent`, although the authorized generic form is `this source` and the frozen corpus requires a matching card-name self-reference; and
2. it classifies an Instant or Sorcery card definition carrying the matched text as fully supported, even though such a source is not a represented battlefield permanent capable of supplying this trigger.

Those false-positive classifications broaden Action #15 beyond its authorized Oracle/corpus boundary and can suppress an unsupported limitation in `SemanticCoverage`. No gameplay redesign is required.

## Frozen candidate integrity

The candidate remained unchanged throughout the audit. Its SHA-1 fingerprint was independently reconstructed from the newline-joined, path-sorted complete-file SHA-256 values:

| Candidate path | SHA-256 |
|---|---|
| `src/tmnt_design_studio/card_interpreter07.py` | `4f2b13d90f96a59e946d56c4c86b4dec17d9d25fa080e22cabd8376e9297ca24` |
| `src/tmnt_design_studio/engine07.py` | `09d81203ec714fc0effbde9cb85926f60d0a6725786fa1c2afbb458f4fe8e66a` |
| `src/tmnt_design_studio/smoke01.py` | `d8069f563f3bec100559886a78a446761a3ae229d441428e9f251b46ce1a34a8` |
| `tests/test_permanent_left_counter_action.py` | `59ceb6d427f930aea30d32a9a7f4194959e8e2b21795e1f400716ff5665d628b` |

Reconstructed candidate fingerprint: `0169af2bc6ce816743d91f4935ed61b87e72256f`.

Canonical Git-clean identities also independently reconstruct exactly:

- engine: `bb2ecc54bb815839a5ec400e53fd1b9feaec9d67`;
- interpreter: `9c2aee3da396b63e57accb93fe522381ee15ec27`.

## Corpus membership

The authoritative frozen TMT/PZA/TMC card-data snapshot contains exactly four recognized print records representing one Oracle object:

| Card | Oracle ID | Set | Collector numbers |
|---|---|---|---|
| Super Shredder | `b7ee76bf-d15a-489e-8f05-414788f8f649` | TMT | `83`, `217`, `285`, `295` |

No second Oracle object in the snapshot matches and fully supports the candidate grammar. The frozen Shredder deck contains four copies of Super Shredder. No named-card or named-deck dispatch was found in the implementation; the card name appears only in the corpus-membership regression.

## Independently accepted lifecycle evidence

### Departure and “another” qualification

Independent probes established that the trigger is generated only by an authoritative runtime `Permanent` leaving the battlefield through a supported zone transition. Battlefield-to-graveyard, battlefield-to-hand, and battlefield-to-library transitions all produced one authenticated `PERMANENT_LEFT` event per departed object. Both creature and noncreature permanents qualified. A represented token departure produced the same trigger, and the token subsequently ceased at the SBA boundary without invalidating the trigger evidence.

The event freezes the departed object ID/controller/type and the pre-departure battlefield authority. The source is captured from the same battlefield snapshot. The provenance validator requires the exact registered event, source card, trigger record, source ID, departed subject ID, battlefield authority, and unique battlefield-origin `zone_changed` record.

The `another` boundary passed its adversarial probes:

- a source leaving alone produced no self-trigger;
- two qualifying permanents leaving simultaneously produced two distinct triggers for one surviving source;
- a source and two other permanents leaving simultaneously produced two source triggers even when the source was processed first, and no trigger for its own departure;
- two sources observing the same two departures produced four distinct trigger IDs and each accumulated two counters;
- when two sources and another permanent all left simultaneously, each source observed the other source and the ordinary permanent, but never itself.

These results reconstruct from the shared pre-departure authority snapshot rather than post-departure battlefield presence.

### Ownership, control and incarnation identity

The trigger correctly observes every other permanent, without an owner/controller restriction. Independent probes covered both an opponent controlling a permanent owned by the trigger controller and the trigger controller controlling an opponent-owned permanent.

The source controller at trigger creation is frozen into the trigger. A later control change did not invalidate the trigger or redirect its controller identity. A source leaving after triggering caused the trigger to resolve with no counter recipient, as required. Returning that physical card created a new battlefield object ID; the old trigger did not put a counter on the new incarnation.

Borrowing an event between two otherwise-valid departures failed both invariant-time and resolution-time authentication because the immutable trigger ID still referred to its original event. Missing last-known source evidence, fabricated subjects, empty battlefield authority, and relinked events also failed closed before any counter mutation.

### Stack, Priority, counters and SBAs

Each qualifying event created a distinct trigger object. The trigger reached the Stack and received the existing two-player Priority/pass lifecycle before resolution. Exactly one `+1/+1` counter was placed per resolving trigger on the still-authoritative source incarnation. Multiple independent triggers accumulated counters and updated evaluated power/toughness through the existing counter layer.

An already-lethal source was moved by the SBA before pending trigger work could save it; the later trigger resolved without a counter. This confirms that Action #15 does not bypass SBA ordering. The duplicate combat/readiness and existing counter machinery remained strict.

When a qualifying departure occurred during resolution of another Stack object, the parent recorded `spell_resolved` before the child trigger was stacked. The generated departure trigger then used the generic post-resolution Stack/Priority boundary. It was not silently resolved inside the parent transaction.

## Scope defect evidence

The authorized generic abstraction and frozen Oracle member require either `this source` in the generic test form or the exact matching source-card name in printed Oracle text. The recognizer currently also returns full support for an additional literal form:

```text
Whenever another permanent leaves the battlefield, put a +1/+1 counter on this permanent.
```

Independent output:

```text
this source    -> SemanticCoverage(True, True, True, ())
this permanent -> SemanticCoverage(True, True, True, ())
card name      -> SemanticCoverage(True, True, True, ())
```

`this permanent` is neither present in the authoritative membership nor required by the accepted grammar. It is therefore an untested neighboring Oracle shape being silently promoted.

The recognizer also omits a permanent-source predicate. An independently constructed Instant named `Audit Spell` with the exact matched sentence returned:

```text
SemanticCoverage(payload_executable=True,
                 parent_executable=True,
                 followup_executable=True,
                 limitations=())
unsupported_fragments == ()
```

That classification is not truthful: the candidate's generic producer scans authoritative battlefield permanents, and an ordinary Instant or Sorcery definition cannot occupy that represented source role. This is a `SemanticCoverage` recognition defect, not evidence that Instant/Sorcery gameplay should be added.

All explicitly listed near-neighbor payload/trigger forms were otherwise rejected: self departure, creature-only departure, dies-only wording, “one or more,” opponent-only scope, optional counter placement, different counter quantity, and different counter type. A mismatched source name was recognized only with an explicit source-mismatch limitation and was not executable.

## Regression evidence

Independent validation reproduced:

- dedicated Action #15 suite: `26 passed`;
- external adversarial audit probes: `9 passed`;
- focused Action/trigger/combat/conformance/card-data suite: `225 passed`;
- full suite: `673 passed / 1 skipped`;
- Ruff check: clean;
- Ruff format check: clean;
- `git diff --check`: clean.

Acceptance #001 seeds 7001–7005 were each executed twice with byte-identical duplicate snapshots and the accepted trajectories:

| Seed | Winner | Turn | Snapshot SHA-256 |
|---:|---|---:|---|
| 7001 | Raphael | 14 | `899a1189be71a1efca47c29d70ace474e2704f1c1732b6a6d0ac22491d63acfd` |
| 7002 | Raphael | 18 | `ee915ff592d23c287b1a8b2edd1814dcce43bf209865462b56d40786e963b803` |
| 7003 | Leonardo | 19 | `9b4b6df3ef94084c090b74d9ecd9c804b3076a3ef6d4d76e684dca2a985136f7` |
| 7004 | Leonardo | 43 | `277231b3004fb3e9df49aa3c8fed6c2491d1be9f1ad89b9d2b8e16c212516f17` |
| 7005 | Raphael | 16 | `448703c5aa315eea31591e6cc3b133cb73a3221a85d5a4c9de7da2e1716852f0` |

No Super Shredder, Shredder-deck, matchup, Pilot, Acceptance, Stage #002, or Smoke-specific gameplay dispatch was found. The `smoke01.py` delta is limited to the independently reconstructed engine/interpreter frozen identities.

## Smallest evidence-backed correction

Do not alter the departure transaction, trigger delivery, Stack/Priority lifecycle, simultaneous-batch handling, counter effect, or gameplay scope.

Correct only Action #15 recognition:

1. permit the authorized generic `this source` abstraction and an exact matching card-name self-reference; remove the unsupported `this permanent` spelling unless authoritative corpus evidence later establishes it as a separately audited shape;
2. require the source definition to be a permanent card type for full support, while retaining exact recognition with an explicit limitation for Instant/Sorcery or otherwise nonpermanent sources; and
3. add adversarial regressions for both cases while preserving the exact Super Shredder membership and all accepted lifecycle behavior.

After that bounded correction, freeze a new candidate for Action #15 Acceptance Audit #2. Do not rerun Smoke merely to correct this recognition boundary.

