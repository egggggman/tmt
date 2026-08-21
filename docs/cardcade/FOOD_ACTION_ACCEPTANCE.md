# Canonical Food Activation Acceptance Audit #1

## Audit identity

- Branch: `agent/cardcade-food`
- Evidence checkpoint: `43ed7cf6896f672db65ff46cf97a5a985df6c71f`
- Audited uncommitted candidate fingerprint: `6a8b4c1ec8d0644c9f1ffc99386fd0355ff78a59`
- Scope: evidence-only audit; implementation and tests were not modified
- Recommendation: **REJECT**

## Rules basis

The audit used the August 19, 2026 official Comprehensive Rules text (download SHA-256
`4381ad1b39ab2c05f7d03633a20f711ed37277074d3266dcba5f38cbb527423f`). Relevant
rules include CR 111.10b (the canonical Food ability), 602.2 and 601.2h (activation and
complete cost payment), 701.21a (sacrifice), 400.7 (zone-change identity), 111.7–111.8
and 704.5d (token cessation), 117.5 (SBA/trigger processing before priority), and 119.3
(life gain).

## Transaction and identity findings

The ordinary canonical path is substantively correct. A controller activates an authoritative
Food permanent; `{2}`, tap, and sacrifice are validated and paid atomically; sacrifice occurs
before Priority; an independent activated-ability object reaches the Stack; engine-owned
Priority/pass precedes resolution; and resolution gains exactly 3 life. Nontoken Food reaches
its owner's graveyard as a new object. A sacrificed Food token reaches the nonbattlefield zone
and ceases at the next SBA boundary while immutable evidence survives. Represented life-gain
triggers are queued separately rather than folded into the Food effect.

The focused probes also passed insufficient mana, tapped source, wrong controller, non-Food
source, stale/fabricated source, source already gone, duplicate activation, failure atomicity,
token cessation, and normal post-resolution SBA/trigger processing. The candidate remains
bounded: it does not implement generic sacrifice costs, generic life gain, arbitrary token
activation, Treasure, Clue, or Mutagen.

## Material blocker: Stack/source linkage is not authoritative

The malformed-linkage adversarial gate fails. After a legal Food activation, replacing the
`ActivatedAbilityObject.source_id` with the ID of a different, registered battlefield permanent
is accepted by `check_invariants()`. Passing Priority then resolves the object and grants 3 life.
The resulting immutable records disagree: the generic activation/Food evidence retains the
actual Food source while the authoritative Stack object names the unrelated registered source.

This is not merely an evidence-label defect. A Stack object whose source linkage has been
corrupted still authorizes the Food effect. The existing invariant checks establish that each ID
exists and that evidence refers to an activated-ability object, but do not cross-validate the
ability's source/controller/program and cost identities against the immutable announcement and
Food evidence. A fabricated unregistered ID is noticed by an invariant check, but resolution
itself still lacks the required pre-effect linkage revalidation.

Smallest evidence-backed correction:

1. Before Food resolution, cross-validate the Stack object's source, controller, Oracle fragment,
   program, and paid-cost identities against both generic activation evidence and Food evidence.
2. Enforce the same linkage in invariants, including the sacrificed destination/new-object ID.
3. Reject a mismatch before life or any other effect mutation.
4. Add regressions for both an unregistered fabricated source ID and a different valid registered
   source ID; prove failure is mutation-free.

This correction does not require broadening Food, sacrifice, or life-gain semantics.

## Semantic coverage

Independent corpus inspection reproduced:

- recognized: **5 objects / 5 fragments**;
- bounded payload executable: **5 / 5**;
- fully supported context: **1 / 1**, `Lita, Little Orphan Amphibian`;
- recognized objects: `Courier of Comestibles`, `Featherbrained Filcher`, `Lita, Little
  Orphan Amphibian`, `Ninja Pizza`, and `Tainted Treats`;
- recognized/executable digest:
  `e1c69b4367b09798f301c185cf1e02dbe97552b1c3283733ffbbe297badf96a8`;
- full digest: `f0a75bdda5429dc58c6fbf524a86ef1fcc35e900118b94da60922e6a38b7b444`;
- frozen recognized/executable digest:
  `7d98d8e6dafc83d7eb4b60e5911f4fc55904cf761c1daaaa15cbfeda253b78b8`.

The other four fragments retain their surrounding unsupported conditions, triggers, or preceding
effects and are not falsely fully supported. `SemanticCoverage` remains Action-generic.

## Acceptance replay

The exact merged-main baseline was independently replayed at **20 unsupported events / 7 exact
pairs**. The candidate duplicate artifacts were byte-identical for every seed and reproduced
**18 unsupported events / 6 exact pairs**, zero Food transactions, **44 Priority grants / 44
passes**, one block-restriction rejection, and zero invariant violations. Trajectories were:

| Seed | Winner | Turn |
|---:|---|---:|
| 7001 | Raphael | 14 |
| 7002 | Raphael | 18 |
| 7003 | Leonardo | 19 |
| 7004 | Leonardo | 43 |
| 7005 | Raphael | 16 |

Exact-set comparison found one removed pair and no added pair: Lita's Food reminder fragment,
observed twice in the baseline. No unrelated limitation disappeared. Zero runtime Food
transactions means this match supplies recognition/telemetry evidence, not execution evidence.

## Validation

- Full suite: **493 passed / 1 skipped**
- Food: **14 passed**
- Activation/Stack/cost: **42 passed**
- Token/zone/SBA/identity: **98 passed**
- Life-total: **16 passed**
- SemanticCoverage + card data: **10 passed**
- Ruff format check: clean
- Ruff check: clean
- `git diff --check`: clean
- Candidate fingerprint after audit: `6a8b4c1ec8d0644c9f1ffc99386fd0355ff78a59`

## Recommendation

**REJECT — malformed authoritative Stack/source linkage remains executable; add pre-resolution
and invariant cross-validation against immutable activation evidence.**
