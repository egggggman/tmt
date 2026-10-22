# Bad Guys — Shredder's Cronies Sandbox 0.2
## Refreshed Oracle-to-engine coverage audit (C3 runtime)

**Decision: BLOCKED for gameplay testing and further remediation packets pending HQ review.**

This is a coverage-only checkpoint. No gameplay simulation, matchup batch, deck
change, Baseline 005 change, or R9-B evidence change was made. The audit is
regenerated after generic C3 variable-X announcement/payment and token support.

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
| Candidate change | −4 Zoo Escapees, −3 Putrid Pals, +4 Foot Elite, +3 Foot Mystic |

The candidate remains 60 cards (28 creatures, 10 noncreature/nonland spells, 22
lands). Baseline 005 and all historical evidence remain byte-for-byte unchanged.

### Coverage overlay (C3 runtime)

| Mechanic family | Status after A/B | Accuracy consequence |
|---|---|---|
| Foot Elite attack trigger: another creature, +1/+0, temporary indestructible | **SUPPORTED** | Generic attack trigger, legal target filtering, resolution recheck, end-of-turn cleanup, lethal-damage and destroy prevention are executable. |
| Foot Mystic lifelink | **SUPPORTED** | Existing lifelink path remains green. |
| Foot Mystic conditional Disappear ETB and Ninja token | **SUPPORTED** | Typed permanent-left history, controller and turn identity, intervening-if creation, resolution recheck, and generic token entry execute. |
| Rocksteady Forestcycling `{2}` | **SUPPORTED** | Generic cycling/search/reveal/shuffle path is covered. |
| Rocksteady/Boar single-block restriction | **SUPPORTED** | Generic direct and controller-scoped quality restrictions filter declarations live, including source departure and control changes. |
| Bebop & Rocksteady mandatory attack/block sacrifice-or-discard | **SUPPORTED** | Generic triggered resolution offers legal discard or sacrifice choices, handles empty-resource cases, and preserves source-independent provenance. |
| Generic variable-X token creation (including Mutagen Man) | **SUPPORTED** | Announcement-time X, payment legality, stack persistence, exact ETB quantity, controller, and source-independent resolution execute generically. |
| Mutagen artifact-token activation discount | **UNSUPPORTED** | Changes activated-ability payment legality and token value. |
| Stomped by the Foot kicker and conditional removal | **UNSUPPORTED** | Changes spell modes, payment, targeting, and removal. |
| Mutant Chain Reaction optional removal then Mutagen creation | **UNSUPPORTED** | Compound resolution is incomplete; partial execution is rejected. |
| Tainted Treats conditional Food creation | **UNSUPPORTED** | Conditional token creation remains unavailable. |
| Cowabunga! top-four selection and randomized bottom order | **UNSUPPORTED** | Hidden-zone choices and library ordering are unavailable. |
| Paramecia Coloniex death/exile recursion | **UNSUPPORTED** | Graveyard/exile identity and permission effects are unavailable. |
| Menace and Rhino-wide menace grants | **UNSUPPORTED** | Continuous keyword grants and block legality remain incomplete. |
| Intrinsic deathtouch, trample, reach, ordinary land entry | **PARTIAL** | Individual intrinsic mechanics exist, but complete card behavior remains limited by the rows above. |

### Ranked remaining work

Priority is based on candidate copies, gameplay consequence, cross-card reuse,
and bounded implementation risk—not on row count alone.

1. **Menace/Rhino grant family:** continuous keyword grants and block legality
   remain unsupported; keep separate from the completed single-block predicate.
2. **Removal and kicker family:** Stomped by the Foot, then Mutant Chain Reaction.
   Implement spell mode/payment/target legality first; keep compound removal →
   token resolution separately reviewable.
3. **Conditional token family:** Tainted Treats. Reuse condition-context and token
   machinery only after its full mana-value condition is represented.
4. **Hidden-zone selection family:** Cowabunga! top-four selection and bottom
   ordering. High identity value but higher choice/replay risk; bounded after the
   combat/resource packets.
5. **Recursion family:** Paramecia Coloniex. Requires zone identity and permission
   duration; isolate from ordinary graveyard recursion.

### Suggested independently reviewable batches

| Batch | Scope | Acceptance boundary |
|---|---|---|
| C1 | Generic block-restriction predicates | **COMPLETE** — valid/invalid declarations, quality grants, control changes, source departure, combat resolution, and deterministic replay. |
| C2 | Mandatory sacrifice/discard at attack/block declaration | **COMPLETE** — legal choices, no-option resolution, source departure, and deterministic replay. |
| C3 | Variable-X announcement and token quantity | **COMPLETE** — X=0, insufficient/malformed payment, countered spell, exact X tokens, source departure, independent X values, and no partial resolution. |
| C4 | Stomped modal/kicker removal | Kicker payment, target legality, resolution-time recheck, −2/−2 versus −5/−5, and cleanup. |
| C5 | Mutant Chain Reaction compound resolution | Optional removal, token creation ordering, simultaneous lethal handling, and strict provenance. |
| C6 | Tainted Treats conditional Food | Condition context, trigger/resolution rechecks, token entry, and negative cases. |
| C7 | Cowabunga hidden-zone choice | Top-four information boundary, eligible selection, random bottom ordering, and exact replay. |
| C8 | Paramecia recursion | Death/exile identity, permissions, timing, costs, source independence, and cleanup. |

The artifact-token activation discount remains a separate follow-up; C3 does not
implement or imply activation-cost reduction. No C4 batch is authorized by this
report.

### Validation evidence

The accepted A/B checkpoint recorded three focused Work Packet A/B tests, 86
focused existing semantic/permanent-left/Mutagen-related tests, and a full
regression of 1,629 passed, 10 skipped. C2 adds eight focused tests and C3 adds
five focused variable-X tests; the current full regression is **1,646 passed,
10 skipped**, with Ruff, formatting, diff, and the Baseline 005 structural
validator green. These results establish the C3 runtime but do not authorize
simulations or close any unsupported family listed above.

**Recommendation to HQ:** accept this refreshed audit as the current coverage
reference; keep gameplay testing and C4 **BLOCKED** until HQ independently
reviews this checkpoint.
