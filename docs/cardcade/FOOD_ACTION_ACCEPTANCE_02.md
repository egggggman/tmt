# Canonical Food Activation Acceptance Audit #2

Status: **ACCEPT**  
Audit date: 2026-08-21  
Branch: `agent/cardcade-food`  
Corrected candidate fingerprint: `c6066b1402dd924dcfda26a620887cb9ed8e64b4`

## Audit integrity

This was an evidence-only audit. No implementation or test file was modified. This report is the
only artifact created by Audit #2. Audit #1 remained byte-identical at SHA-256
`38a9082f14becdb655d71821a587a824e692df67b37eedbdc407497092b37fc0`, and it continues to
record the rejected candidate fingerprint
`6a8b4c1ec8d0644c9f1ffc99386fd0355ff78a59`.

The corrected fingerprint was independently reproduced as SHA-1 of the newline-joined,
path-sorted complete-file SHA-256 values for the five candidate implementation/test files. It
remained `c6066b1402dd924dcfda26a620887cb9ed8e64b4` after inspection, probes, validation, and
duplicate replay.

## Blocker re-audit

The correction authenticates a Food `ActivatedAbilityObject` against exactly one generic
`ActivationEvidence` record and exactly one `FoodActivationEvidence` record bearing its Stack
identity. Before effect execution it cross-validates source identity, controller, Oracle fragment,
interpreted payload, mana-source identities, tap payment, sacrifice payment, sacrificed
destination identity, and immutable source card/owner/token facts. The same validation is invoked
by engine invariants independently of resolution.

Independent adversarial construction reproduced rejection of:

- a Food A Stack object relinked to another registered Food B;
- relinking to a registered non-Food permanent;
- controller/source-controller mismatch;
- Action/payload replacement;
- mana, tap, or sacrifice-cost evidence mismatch;
- sacrificed destination/source-identity mismatch;
- evidence borrowed from a separate valid Food activation;
- Stack/evidence identities swapped between otherwise valid activations;
- duplicated or fabricated evidence;
- stale or unregistered source identity; and
- a second attempt to resolve an already-resolved activation.

Each malformed live Stack case was rejected by `check_invariants()` before resolution and again
by authoritative validation when Priority/pass attempted resolution. Life remained unchanged,
the Stack object remained unresolved, and no Food payload or post-life-gain processing occurred.
Duplicate resolution was rejected because the former ability was no longer the authoritative top
Stack object.

## Legitimate sacrificed-source lifecycle

The correction does not require the original permanent to remain on the battlefield. Both token
and nontoken probes retained the valid lifecycle:

`Food permanent → announcement → atomic {2} + tap + sacrifice → independent Stack object →
Priority/pass → resolution → gain 3 life → SBA/trigger processing`.

The original source becomes a historical former object. A nontoken's new graveyard object and a
token's post-SBA former destination remain sufficient immutable cost evidence. Token cessation
therefore does not invalidate the independent Stack object or erase its provenance. Successful
resolution changed life only at resolution, by exactly 3.

## Architecture and scope

The check joins immutable activation/Food evidence by authoritative Stack identity and verifies
the interpreted Food payload. It does not reconstruct authority from current battlefield
membership and contains no source-card-name dispatch. `SemanticCoverage` was unchanged and
remains Action-generic. The generic activated-ability, Stack, cost, and Priority suites passed,
showing the Food-specific provenance check does not reject unrelated legitimate Stack objects.

The correction did not implement generic sacrifice costs, generic life gain, arbitrary token
activation, Treasure, Clue, or Mutagen.

## Coverage

Independent corpus tests reproduced exactly:

- recognized: **5 objects / 5 fragments**;
- bounded payload executable: **5 / 5**;
- fully supported: **1 / 1 — Lita, Little Orphan Amphibian**;
- recognized/executable digest:
  `e1c69b4367b09798f301c185cf1e02dbe97552b1c3283733ffbbe297badf96a8`;
- fully-supported digest:
  `f0a75bdda5429dc58c6fbf524a86ef1fcc35e900118b94da60922e6a38b7b444`;
- frozen recognized/executable digest:
  `7d98d8e6dafc83d7eb4b60e5911f4fc55904cf761c1daaaa15cbfeda253b78b8`.

`Courier of Comestibles`, `Featherbrained Filcher`, `Ninja Pizza`, and `Tainted Treats` retain
their explicit unsupported surrounding trigger, condition, or preceding-effect limitations. An
executable canonical Food payload does not make those complete fragments fully supported.

## Acceptance replay

Seeds 7001–7005 were run twice. Each duplicate pair was byte-identical. Aggregate evidence was:

- **18 unsupported events / 6 exact pairs**;
- **0 Food transactions**;
- **44 Priority grants / 44 passes**;
- **1 block-restriction rejection**;
- **0 invariant violations**.

| Seed | Winner | Ending turn |
|---:|---|---:|
| 7001 | Raphael | 14 |
| 7002 | Raphael | 18 |
| 7003 | Leonardo | 19 |
| 7004 | Leonardo | 43 |
| 7005 | Raphael | 16 |

The pre-Food-to-candidate movement remains **20/7 → 18/6**. Exact-set comparison attributes the
two removed events and one removed pair only to Lita's now-supported Food reminder fragment. No
unrelated limitation was suppressed. Because no Food activation occurs in Acceptance Match #001,
this reduction is coverage/support evidence rather than runtime Food execution evidence.

## Regression gate

- Full suite: **499 passed / 1 skipped**
- Food: **20 passed**
- Activation/Stack/cost: **42 passed**
- Token/zone/SBA/identity: **98 passed**
- Life totals: **16 passed**
- SemanticCoverage + card data: **10 passed**
- Ruff format check: clean
- Ruff check: clean
- `git diff --check`: clean
- Corrected candidate fingerprint after audit:
  `c6066b1402dd924dcfda26a620887cb9ed8e64b4`

No material transaction, provenance, identity, architecture, coverage, telemetry, or regression
blocker remains within the bounded canonical Food activation scope.

## Verdict

**ACCEPT — corrected bounded canonical Food activation is suitable to bank with its documented coverage.**
