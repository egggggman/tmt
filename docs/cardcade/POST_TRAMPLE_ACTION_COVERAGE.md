# Post-Trample Action Coverage

Status: evidence-only Action #8 recommendation
Audited date: 2026-08-20
Audited branch: `main`
Audited HEAD: `47eee13482efef625e2a11f75163f71ac567342d`
Integrated change: PR #37, accepted bounded Trample combat-damage assignment

## Decision

Recommend exactly **Action #8: bounded Lifelink life-gain attribution**.

This report does not implement Action #8. It authorizes no deck revision, Prototype 0.3 work,
calibration, smoke testing, Pilot tuning, or unrelated combat-keyword expansion.

## Integration evidence

PR #37 was based on `main` at
`2bbbeb34a00a2328e550cbd8eaadbd9fa83ff881`. The accepted head was
`59dc351db6f5aef2c23131bfe85dcfc570f85af1`; remote `main` now points to its squash merge,
`47eee13482efef625e2a11f75163f71ac567342d`. A fresh fetch found local `main`, remote `main`, and
the audited HEAD identical, with no intervening commit and a clean worktree before this report.

The PR diff contains exactly six paths: the prior post-Targeted-Return evidence checkpoint, the
Trample interpreter and engine implementation, the focused Trample test module, and the two
Trample acceptance reports. No deck, Pilot, prototype, calibration, or unrelated product file is
present.

Both PR check runs passed before merge. The squash merge itself is conclusive historical evidence
that GitHub accepted the head against that base; GitHub reports merged PRs as `UNKNOWN` rather
than retaining a live post-merge `CLEAN` mergeability value.

Audit #1 is the same Git blob (`ae4525e7e5b3c6fab9d8999a12adac1f3088bcab`) at the accepted head
and merged `main`. Its canonical blob SHA-256 remains
`6d7e3c99869759b4f60e3e04d0f63156135445ece36997f67113312896a7e609`. A Windows CRLF checkout
has working-file SHA-256 `0cb44db5142c9549548191422cd43885a1dfc2debf6df09e9f719916baa5d7e5`;
that checkout conversion does not change the committed bytes.

Merged-main validation reproduced:

- full suite: **399 passed / 1 skipped**;
- Acceptance seeds 7001–7005 replayed twice with byte-identical duplicate snapshots;
- **42 unsupported events / 15 exact card-fragment pairs**;
- **1 genuine Trample split**, in seed 7003;
- **0 invariant violations**.

## Remaining Acceptance surface

Every remaining event is attributed to its missing semantic boundary rather than to an already
supported child Action.

| Missing capability | Events | Pairs | Exact current exposure |
|---|---:|---:|---|
| Sneak casting transaction | 16 | 5 | Five Leonardo Sneak cards |
| Filtering plus Draw | 8 | 2 | Manhole Missile hand-bottom/draw 4; Null Group discard/draw 4 |
| Exile/graveyard/play permissions | 7 | 3 | Sewer Samurai graveyard/finality 3; Raphael exile-top 2; Raphael play-exiled 2 |
| Remaining combat keywords | 7 | 3 | Wingnut modal keyword 3; Lifelink 2; Menace 2 |
| Look/selection | 2 | 1 | Casey Jones look-four artifact selection |
| Food activation/use | 2 | 1 | Lita Food activation and use |
| **Total** | **42** | **15** | |

The former standalone Mutant Town Musicians Trample pair is absent. No remaining pair is charged
to bounded Trample.

## Evidence universe

The comparison uses the authoritative 472-print / 332-Oracle-object TMT/PZA/TMC snapshot and the
frozen 102-card roster across all 10 decks. Previously reproduced corpus counts remain applicable
because PR #37 changed interpretation and combat execution, not the card snapshot or decks.

| Candidate | Acceptance leverage | Frozen-roster reach | Full-pool reach | Readiness, impact, and complexity |
|---|---:|---:|---:|---|
| **Bounded Lifelink** | **2 events / 1 complete pair** | **2 cards / 3 decks** | **6 objects** | Damage attribution, combat steps, noncombat damage transactions, source identity, SBAs, and events already exist. Small–medium complexity; direct life-race impact. |
| Draw Cards | 8 / 2, but no pair completes alone | 17 / 7 | 54 | Draw primitives exist and reach is excellent. Acceptance delivery is still gated by discard or hand-bottom choice and, for Null Group, trigger delivery. Medium complexity and high general impact. |
| Sneak transaction | 16 / 5 | 18 / 6 | 27 | Highest raw leverage and strong identity impact, but needs a special casting window, return-as-cost, alternate costs, Stack/Priority integration, and tapped-and-attacking entry. Very high complexity. |
| Trigger-delivery expansion | Parent of at least 9 events | 54 / 10 | 171 | Exceptional dependency reach, but exposed children still need modal keyword, filtering/Draw, or exile semantics. High breadth and complexity; completes no pair alone. |
| Menace/blocker-count expansion | 2 / 1 | 6 / 4 | 17 | Direct pair leverage and meaningful combat impact, but requires widening the authoritative one-blocker combat model. High structural complexity. |
| Exile/graveyard/play permissions | 7 / 3 | 8 / 7 | 33 | Good reach and gameplay impact, but heterogeneous zones, durations, permissions, replacement behavior, and tracked identity make this several slices. High complexity. |
| Discard/filtering | 8 / 2 as compound children | 10 / 6 | 16 | Useful dependency for Draw; choice, ordering, and trigger delivery still gate current pairs. Medium–high complexity. |
| Food activation/use | 2 / 1 | 3 / 3 | 5 | Direct pair leverage, but requires sacrifice/nonmana costs and life gain. Medium complexity; narrower than Lifelink. |
| Casey look/selection | 2 / 1 | 1 / 2 | narrow | Completes one pair only with hidden-information selection, reveal, hand movement, random bottom ordering, and trigger delivery. High complexity for its reach. |

## Re-ranked candidates

| Rank | Candidate | Evidence-based result |
|---:|---|---|
| 1 | **Bounded Lifelink** | Only small, dependency-ready candidate that completes a current pair by itself; the accepted damage and strike/Trample transaction evidence supplies the correct reusable seam. |
| 2 | Draw Cards | Best broad reusable reach, but current Acceptance leverage is compound-gated and therefore not eight independently removable events. |
| 3 | Sneak casting transaction | Highest direct pressure, but too many coupled casting, cost, zone, timing, and combat-entry dependencies for the next bounded Action. |
| 4 | Trigger-delivery expansion | Best infrastructure reach; no exposed pair completes without another child semantic family. |
| 5 | Food activation/use | Can complete a pair, but first requires sacrifice-cost and life-gain work; Lifelink establishes the more reusable life-gain attribution boundary. |
| 6 | Menace/blocker-count expansion | Can complete a pair, but widens the represented combat topology beyond one blocker. |
| 7 | Exile/graveyard/play permissions | Three exposed pairs, but they are heterogeneous rather than one honest bounded Action. |
| 8 | Discard/filtering | Valuable with Draw, but compound choice and trigger dependencies prevent standalone completion. |
| 9 | Casey look/selection | Lowest reusable reach and several hidden-information/ordering dependencies. |

## Action #8 recommendation

Implement a reusable, Oracle-derived **bounded Lifelink** capability that attributes life gain to
damage actually dealt by a source with authoritative Lifelink. It should cover represented combat
damage steps and any already-supported noncombat damage path only where source identity and final
damage dealt are authoritative. Life gain must be part of the damage transaction, preserve
before/after evidence, work with simultaneous damage and player-loss SBAs, and use runtime identity
rather than card names, roster membership, Pilot behavior, or Acceptance seeds.

Keep unsupported semantics explicit: temporary or modal Lifelink grants, unsupported parent
triggers or activations, damage prevention/replacement/redirection not represented by the engine,
multiple blockers, and any life-gain trigger or payoff not independently implemented. Wingnut's
modal trigger and Menace remain unsupported.

Lifelink outranks Draw because it removes one current pair without requiring a second Action and
fits the established damage transaction boundary. Draw has much greater pool reach, but both of
its current pairs remain incomplete without filtering choices and one also needs trigger delivery.
Lifelink outranks Sneak because Sneak is a compound casting system rather than the next smallest
reusable Action.

No Action #8 implementation is included.
