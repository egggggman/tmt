# Post-Targeted-Return Action Coverage

Status: evidence-only Action #7 recommendation  
Audited date: 2026-08-20  
Audited branch: `main`  
Audited HEAD: `2bbbeb34a00a2328e550cbd8eaadbd9fa83ff881`  
Integrated change: PR #36, accepted bounded Targeted Return to Hand

## Decision

Recommend **Action #7: bounded Trample combat-damage assignment**.

This recommendation is limited to the represented deterministic combat model. It does not authorize multiple blockers, deathtouch, damage prevention or redirection, planeswalker or battle combat, new pilot strategy, or unrelated keyword work.

## Integration evidence

PR #36 was based on the then-current `main` (`0c9018b7a4f3472bfe2af05b486c5d2ec3d2d489`), with no intervening main commit. Its diff contained only the post-Action #5 evidence checkpoint, the accepted Targeted Return implementation and tests, and its four-report acceptance history. It was squash-merged as `2bbbeb34a00a2328e550cbd8eaadbd9fa83ff881`.

The historical acceptance reports remain preserved with these SHA-256 values:

| Report | Result | SHA-256 |
|---|---:|---|
| `TARGETED_RETURN_ACTION_ACCEPTANCE.md` | REJECT #1 | `7deae80ca008f5e4c94dcbffe817090b595fb3a7bd470bfc58be06e853d9ed3c` |
| `TARGETED_RETURN_ACTION_ACCEPTANCE_02.md` | REJECT #2 | `5e07fd3ad3487726cbef6eb5ff93dc0ccb562e919d230320b754827c69adbec0` |
| `TARGETED_RETURN_ACTION_ACCEPTANCE_03.md` | REJECT #3 | `dc0894a06bb4b23b16ccecee39f22e31b7241bf60a4d72bfd9b1c51a32898aa` |
| `TARGETED_RETURN_ACTION_ACCEPTANCE_04.md` | ACCEPT | `9b423238cc7ec644c0e9467a1ed1434c18f3ca183c4973f8b180be94aa306693` |

Merged-main verification passed: 377 tests passed and 1 skipped; the five card-data integrity tests passed; Ruff formatting and lint checks passed; `git diff --check` passed. GitHub Actions run 32426601156 passed on the audited HEAD.

Acceptance Match #001 seeds 7001–7005 were replayed twice with byte-identical duplicates. Results remained 47 unsupported events / 16 exact pairs, 8 Return transactions, 16 activation announcements, 13 Scry transactions, 17 Deal Damage transactions, 1 block-restriction rejection, and 0 invariant violations. Trajectories were Raphael T16, Raphael T16, Leonardo T19, Leonardo T21, and Raphael T16 respectively.

## Evidence universe

The ranking was recomputed against the authoritative 472-print / 332-Oracle-object TMT/PZA/TMC snapshot and the frozen 102-card roster across all 10 decks. It accounts for Engine 0.8, Create Token, Deal Damage, Scry, First/Double Strike damage steps, Activated-Ability delivery, and Targeted Return.

Targeted Return remains recognized for 37 Oracle objects / 38 fragments and bounded executable and fully supported for 1 / 1. Its supported payload is not charged again when another parent, cost, target form, choice, or follow-up remains unsupported.

The seven context-sensitive UNKNOWN objects remain unchanged: Arcane Signet, Chromatic Lantern, Command Tower, Double Jump // Flying Kick, Exotic Orchard, Fast Forward, and Plague of Vermin.

## Residual Acceptance attribution

Every remaining event is attributed to the missing semantic boundary, not to an already-supported child Action.

| Missing capability | Events | Pairs | Exact current exposure |
|---|---:|---:|---|
| Sneak casting transaction | 16 | 5 | Leonardo, Big Brother; Leonardo, Leader; Sewer Samurai; Cutting Edge; Nightwatcher |
| Combat keyword semantics | 12 | 4 | Trample 5; Wingnut modal keyword 3; Lifelink 2; Menace 2 |
| Filtering plus Draw | 8 | 2 | Manhole Missile hand-bottom/draw 4; Null Group attack-trigger discard/draw 4 |
| Exile/graveyard/play permissions | 7 | 3 | Sewer Samurai graveyard/finality 3; Raphael exile-top 2; Raphael play-exiled 2 |
| Look/selection | 2 | 1 | Casey Jones look-four selection 2 |
| Food activation/use | 2 | 1 | Lita Food activation/use 2 |
| **Total** | **47** | **16** | |

The former 69/17 baseline therefore improved to 47/16 through genuine Return execution. No residual pair is attributed to Targeted Return itself.

## Corpus reach

Fresh lexical/interpreter census results provide comparative reach, not automatic support claims:

| Family | Full-pool objects / fragments | Frozen cards / decks | Readiness note |
|---|---:|---:|---|
| Draw Cards | 54 / 54 | 17 / 7 | Broad, but current Acceptance occurrences also require filtering or trigger/choice delivery |
| Sneak | 27 / 32 | 18 / 6 | Highest direct telemetry, but depends on a new casting window, return-as-cost, alternate costs, and tapped-and-attacking entry |
| Trample | 25 / 26 | 3 / 4 | Existing combat, damage-step, marked-damage, and SBA foundations make a bounded implementation directly reachable |
| Direct trigger language | 171 / 200 | 54 / 10 | Very broad parent infrastructure; current exposed children still need modal, filtering, exile, or permission semantics |
| Discard | 16 / 19 | 10 / 6 | Current pair also needs Draw and trigger delivery |
| Menace | 17 / 18 | 6 / 4 | Requires blocker-count/generalized blocking work outside the current single-blocker model |
| Lifelink | 6 / 6 | 2 / 3 | Small bounded keyword, but less direct and corpus leverage than Trample |
| Exile/play-zone language | 33 / 34 | 8 / 7 | Heterogeneous permissions, durations, zones, and tracking identities |
| Food use | 5 / 5 | 3 / 3 | Requires sacrifice/nonmana cost and life-gain semantics; creating Food remains separate |
| Hand-bottom filtering | 1 / 1 | 1 / 2 | Needs target/choice ordering plus Draw |

## Re-ranked candidates

| Rank | Candidate | Direct Acceptance leverage | Dependency and complexity assessment |
|---:|---|---|---|
| 1 | **Bounded Trample** | **5 events / 1 pair** | High readiness: extends authoritative combat assignment already shared by regular and first/double-strike steps. Medium bounded complexity and 25-object pool reach. |
| 2 | Draw Cards | 8 events / 2 pairs only as a compound child | Excellent 54-object reach, but no exposed pair becomes complete without discard/hand-bottom selection and, for Null Group, trigger delivery. |
| 3 | Sneak casting transaction | 16 / 5 | Highest raw exposure, but materially larger than one Action: special timing, casting from hand during declare blockers, return-as-cost, alternate/additional costs, Stack/Priority, and tapped-and-attacking entry. |
| 4 | Trigger-delivery expansion | Parent of at least 9 exposed events | Strong dependency leverage and broad corpus reach, but its exposed children still require modal keyword, filtering/Draw, or exile semantics; it presently completes no pair alone. |
| 5 | Discard / hand-to-library filtering | 8 / 2 as compound semantics | Useful with Draw, but requires choice/order handling and one path also requires trigger delivery. |
| 6 | Lifelink | 2 / 1 | Existing damage events help, but noncombat/combat source linkage and life-gain trigger implications need conservative boundaries. |
| 7 | Menace / blocker-count expansion | 2 / 1 | Requires expansion of the represented combat model beyond a single blocker. |
| 8 | Exile/graveyard/play permissions | 7 / 3 | Good exposure but heterogeneous zone permission and duration semantics create multiple dependencies. |
| 9 | Food activation/use | 2 / 1 | Requires sacrifice/nonmana costs and life gain; does not follow merely from accepted token creation or activation delivery. |
| 10 | Casey look/selection | 2 / 1 | Narrow and choice-heavy, with low reusable leverage compared with the candidates above. |

## Action #7 recommendation

Implement a reusable, Oracle-derived **bounded Trample** capability. For the currently represented one-attacker/one-blocker combat, it should calculate lethal assignment to the blocker and permit excess combat damage to the defending player through the authoritative combat-damage transaction. It should operate consistently in ordinary and represented first/double-strike damage steps, preserve marked-damage and SBA boundaries, and use runtime identity rather than card names.

The checkpoint must keep unsupported semantics explicit, including multiple blockers or blockers ordered for assignment, deathtouch-modified lethal assignment, damage prevention/replacement/redirection, planeswalkers and battles, and any unsupported compound parent or keyword-grant context. Wingnut's modal trigger must not become executable merely because Trample itself is supported.

Trample outranks Draw because it can eliminate a currently exposed pair by itself using foundations already present, while every exposed Draw occurrence remains gated by at least one other missing semantic family. It outranks Sneak because Sneak's five pairs depend on several coupled casting, cost, timing, zone, and combat-entry extensions that cannot truthfully be delivered as the next smallest reusable Action.

No Action #7 implementation is included in this evidence checkpoint.
