# Chrome Dome semantic readiness for OBL-R6-KRANG-B

Cardcade verified the immutable candidate in [Design Studio PR #260](https://github.com/egggggman/tmt/pull/260): head `6315561e92c76142d3d3527538024ba55f4694ec`, Git blob `53af73af05c475832bd3e8a08c67264a0ff8fd44`, canonical LF SHA-256 `5460b9d1288d193db3f8db7a78076dfeb38f734c79acdd1ddbe898da030b3bdf`. Its only diff from Baseline 003 Krang is **−1 Negate, +1 Chrome Dome**. The candidate was not copied into or edited by this PR. [Machine-readable readiness](ROUND_6_B_CHROME_DOME_READINESS.json) includes the exact ordered candidate rows and source identities.

The [frozen card snapshot](../../cardcade/scryfall-tmt-pza-tmc-2026-08-13.json) identifies Chrome Dome as a Standard-legal `{2}` Artifact Creature — Robot Ninja, 1/3. Cardcade now executes the exact clause: “Other artifact creatures you control get +1/+0.” This is a bounded, generic static-team modifier—not a Chrome Dome name check. It applies to each other qualifying artifact creature under the source controller, tracks each source and affected permanent, and removes/reapplies derived modifiers as the battlefield changes. Repeated layer refreshes do not duplicate the modifier or its change telemetry.

Coverage is deliberately partial:

| Component | Status |
|---|---|
| Creature/permanent cast and battlefield body | SUPPORTED |
| Static `other artifact creatures you control get +1/+0` | SUPPORTED |
| `{5}` token-copy activation | UNSUPPORTED; outside the R6-B hypothesis |
| Whole card fully executable | NO |
| R6-B hypothesis semantics | **READY** |

Existing cast and battlefield zone-change events, plus new generic `pt_static_team_modifier_changed` events, make casts, source entries/exits, affected objects, source objects, qualifying-target counts, P/T deltas, and apply/remove transitions observable. The OBL game recorder retains these events for a later R6-B experiment. No match simulations were run here.

Semantic runtime: `78bcce5b5f635f11c67247df91f90fef2bf0dbf948973c5c1ac38419f28b0e25` → `252f00317d8efbf552512768503d5f453ef9594ade48e27a94f95f05c7625982`. Baseline 003 remains the official *deck* environment, but its historical simulation evidence used the old runtime and must not be silently composed with new-runtime R6-B evidence. Historical validators authenticate those records against their pinned source commit; their game-execution modes still reject the changed live runtime. This readiness gate does not authorize R6-B games, a candidate redesign, or promotion.
