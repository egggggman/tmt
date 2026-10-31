# Bad Guys — Shredder's Cronies Sandbox 0.2
## Refreshed Oracle-to-engine coverage audit (C8 runtime)

**Decision: BLOCKED for gameplay testing and further remediation packets pending HQ review.**

This is a coverage-only checkpoint. No gameplay simulation, matchup batch, deck
change, Baseline 005 change, or R9-B evidence change was made. The audit is
regenerated after generic C8 Paramecia death/exile recursion support.

### Provenance

| Item | Value |
|---|---|
| Candidate SHA-256 | `cacc77648a4d1659b8ae640d95ac2672694e6951553980246e6d001e5152bfb4` |
| Baseline 005 SHA-256 | `aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed` |
| Pinned card snapshot | `56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402` |
| Pre-A/B semantic runtime | `d4466241f0ffeaca809cd6a05210ad53b9af1011a1d7f833de88657c1cf00924` |
| Accepted A/B semantic runtime | `00fc49eb47d9ffd3d0243564cc7c9763d11738ca9698811306102747a060d374` |
| C1 semantic runtime | `960df6898bcfa765a572f6128391dba735d322f9ce579e2866dcc3d1874bca4b` |
| C2 semantic runtime | `c95426fe7baba7794884782e781df1deda0c8d162cf70df03f0a8da1528a6691` |
| C3 semantic runtime | `ab38515951c7faa1b1006a3e03ec4620c03a646538c2a3e54e44733716f44a37` |
| C4 semantic runtime | `6b2f86bf1834aece9dc1b3bc3817451601fb5c88e8581f1c7f6ba2a1d50d63a0` |
| C5 semantic runtime | `5860e357c084973aac2eae3f4b5f27b9948caa866bad3bf3d5c48cc8d5db4cf8` |
| C6 semantic runtime | `7bfaa315f3c54a184be1b49dddaad7b598211f91c0f66d47fd0aaafe8af2d3b8` |
| C7 semantic runtime | `197c2acd50c95d669d549f1fe99342740a48b7d7a7fe8ff814c21a449927209f` |
| C8 semantic runtime | `832c37effb02af7351f7d29836c9eb793a008de29c8d77b2ae79431eb9445ad7` |
| Candidate change | −4 Zoo Escapees, −3 Putrid Pals, +4 Foot Elite, +3 Foot Mystic |

The candidate remains 60 cards (28 creatures, 10 noncreature/nonland spells, 22
lands). Baseline 005 and all historical evidence remain byte-for-byte unchanged.

### Coverage overlay (C6 runtime)

| Mechanic family | Status after A/B | Accuracy consequence |
|---|---|---|
| Foot Elite attack trigger: another creature, +1/+0, temporary indestructible | **SUPPORTED** | Generic attack trigger, legal target filtering, resolution recheck, end-of-turn cleanup, lethal-damage and destroy prevention are executable. |
| Foot Mystic lifelink | **SUPPORTED** | Existing lifelink path remains green. |
| Foot Mystic conditional Disappear ETB and Ninja token | **SUPPORTED** | Typed permanent-left history, controller and turn identity, intervening-if creation, resolution recheck, and generic token entry execute. |
| Rocksteady Forestcycling `{2}` | **SUPPORTED** | Generic cycling/search/reveal/shuffle path is covered. |
| Rocksteady/Boar single-block restriction | **SUPPORTED** | Generic direct and controller-scoped quality restrictions filter declarations live, including source departure and control changes. |
| Bebop & Rocksteady mandatory attack/block sacrifice-or-discard | **SUPPORTED** | Generic triggered resolution offers legal discard or sacrifice choices, handles empty-resource cases, and preserves source-independent provenance. |
| Generic variable-X token creation (including Mutagen Man) | **SUPPORTED** | Announcement-time X, payment legality, stack persistence, exact ETB quantity, controller, and source-independent resolution execute generically. |
| Generic kicker sacrifice payment and conditional temporary creature removal | **SUPPORTED** | Complete kicker choice, artifact/creature sacrifice payment, legal target selection, resolution-time recheck, −2/−2 versus −5/−5, lethal state-based actions, and cleanup execute generically. |
| Mutagen artifact-token activation discount | **UNSUPPORTED** | Changes activated-ability payment legality and token value. |
| Mutant Chain Reaction optional removal then Mutagen creation | **SUPPORTED** | Generic optional target selection, resolution-time target recheck, removal-before-token ordering, token entry, and independent source provenance execute. |
| Tainted Treats conditional Food creation | **SUPPORTED** | Generic artifact-or-creature targeting, resolution-time legality, last-known mana value threshold, removal, conditional Food entry, and provenance execute. |
| Cowabunga! top-four selection and randomized bottom order | **SUPPORTED** | Generic hidden top-four view, eligible Mutant/Ninja/Turtle/land reveal, hand movement, random bottom ordering, short-library handling, and deterministic replay execute. |
| Paramecia Coloniex death/exile recursion | **SUPPORTED** | Generic death-event provenance, optional exile, post-exile target selection, graveyard target recheck, top-of-library movement, object incarnation, controller/owner identity, and deterministic fail-closed replay execute. |
| Menace and Rhino-wide menace grants | **UNSUPPORTED** | Continuous keyword grants and block legality remain incomplete. |
| Intrinsic deathtouch, trample, reach, ordinary land entry | **PARTIAL** | Individual intrinsic mechanics exist, but complete card behavior remains limited by the rows above. |

### Ranked remaining work

Priority is based on candidate copies, gameplay consequence, cross-card reuse,
and bounded implementation risk—not on row count alone.

1. **Menace/Rhino grant family:** continuous keyword grants and block legality
   remain unsupported; keep separate from the completed single-block predicate.
2. **Recursion family:** Paramecia Coloniex. Requires zone identity and permission
   duration; isolate from ordinary graveyard recursion.

### Suggested independently reviewable batches

| Batch | Scope | Acceptance boundary |
|---|---|---|
| C1 | Generic block-restriction predicates | **COMPLETE** — valid/invalid declarations, quality grants, control changes, source departure, combat resolution, and deterministic replay. |
| C2 | Mandatory sacrifice/discard at attack/block declaration | **COMPLETE** — legal choices, no-option resolution, source departure, and deterministic replay. |
| C3 | Variable-X announcement and token quantity | **COMPLETE** — X=0, insufficient/malformed payment, countered spell, exact X tokens, source departure, independent X values, and no partial resolution. |
| C4 | Stomped modal/kicker removal | **COMPLETE** — Kicker payment, target legality, resolution-time recheck, −2/−2 versus −5/−5, lethal state-based actions, and cleanup. |
| C5 | Mutant Chain Reaction compound resolution | **COMPLETE** — Optional removal, target recheck, token creation ordering, simultaneous lethal handling, and strict provenance. |
| C6 | Tainted Treats conditional Food | **COMPLETE** — mana-value condition, target recheck, removal, Food entry, negative cases, and deterministic replay. |
| C7 | Cowabunga hidden-zone choice | **COMPLETE** — Top-four information boundary, eligible selection, random bottom ordering, short-library handling, and exact replay. |
| C8 | Paramecia recursion | **COMPLETE** — Death/exile identity, optional action, post-exile target selection, target recheck, top-library movement, source independence, and deterministic replay. |

The artifact-token activation discount remains a separate follow-up; C7 does not
implement or imply activation-cost reduction. C8 and later packets are not
authorized by this report.

### Validation evidence

The accepted A/B checkpoint recorded three focused Work Packet A/B tests, 86
focused existing semantic/permanent-left/Mutagen-related tests, and a full
regression of 1,629 passed, 10 skipped. C2 adds eight focused tests, C3 adds
five focused variable-X tests, C4 adds four focused tests, C5 adds five focused
compound-resolution tests, C6 adds seven focused conditional-Food tests, and C7
adds ten focused hidden-zone tests. C8 adds eight dedicated Paramecia tests;
the focused mill/Paramecia boundary total is 69 passing tests. No simulations
are authorized or run.

The C8 final-head full regression passed **1,676 tests with 10 skipped**;
Ruff format/check and structural checks passed locally.

**Recommendation to HQ:** accept this refreshed audit as the current coverage
reference; keep gameplay testing and C9 **BLOCKED** until HQ independently
reviews this checkpoint.

