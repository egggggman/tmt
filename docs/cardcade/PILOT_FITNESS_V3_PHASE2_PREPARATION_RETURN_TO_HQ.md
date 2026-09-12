# V3 Phase 2 preparation candidate

**CANDIDATE / NOT SEALED. Pilot scoring remains unauthorized.**

Phase 1 remains banked unchanged at `af6ba95`. This candidate covers only Scry,
Sneak, Discard/Draw and Hand-bottom/Draw under Specification V3 `c18a8fc`.

## Reconstructed deterministic candidates

The companion JSON contains two no-Pilot reconstructed candidates:

- `V3-P2-001`: Scry 2 R candidate. It captures the recipient-specific Scry
  view, complete legal partition/order options, executes the selected option,
  and records the concrete endpoint objective that the top inspected card is a
  creature.
- `V3-P2-002`: Sneak T candidate. It captures the active player's legal Sneak
  options after attackers and blockers, executes the Sneak branch through
  Priority and combat damage, and records the lethal endpoint result.

The script uses only engine primitives and does not import either Pilot.

## Boundary and uncertainty dispositions

Scry and Sneak boundary candidates are recorded as prospective pass-only/empty
surfaces and require the same seat, transformation and privacy checks before a
future seal. No boundary is counted here.

Discard/Draw is `INCONCLUSIVE`: no complete V3 discard/Draw oracle and stable
objective direction has been sealed in this phase. The accepted engine audit
proves transaction semantics, not Pilot fitness.

Hand-bottom/Draw is `INCONCLUSIVE`: the preserved bounded audit at `a577c0c`
found no certified strict filter witness and one optimistic but unconstructed
retention candidate. Competing identity and exact tie remain optional under V3,
but B/integrity evidence is still required where reachable. No unrestricted
search was restarted and no witness was manufactured.

Because these conditional competencies lack valid final dispositions, Phase 2
cannot yet be sealed. This is a specific oracle/applicability blocker, not a
claim that the deterministic candidates are unreachable.

No canonical Phase 2 `F` or privacy `K` is assigned. Pilot invocation count is
zero. The global invocation formula remains derived only after all canonical
fixtures are sealed.
