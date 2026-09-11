# Hand-bottom/Draw U-quota feasibility audit

**FEASIBILITY AUDIT / QUOTA BLOCKED / NOT SEALED. Specification V2 remains accepted and unchanged.**

This is a feasibility audit only. It does not score Pilots, alter quotas, modify the gameplay engine or policies, or authorize Action #33. Commits `3f60166` and `1673eab` remain intact as failed-preparation evidence.

The bounded evidence covers both frozen decks containing Manhole Missile (Casey Jones and Raphael), the existing supported filter endpoint, two legal setup schedules, both seats, and the permitted horizon of filter resolution plus state-based and automatic-trigger draining. It admits at most one replacement Draw and no second hidden Draw. Raphael has four Manhole Missile copies, but no separate supported Hand-bottom/Draw instruction was found in its frozen list. Empty-library return behavior remains a B boundary, not a U role.

The prior search contributes 76 prospective probes and an independent audit of 1,612 complete-prior action/outcome rows. It found 9 strict objective reversals, 18 visible support failures, 2 setup multiplicity failures, and 47 unresolved survivors. All positive prior weights remain; failed completions are not removed or renormalized. The optimistic two-seat strict-retention capacity is one, while V2 requires two disjoint strict-retention roles.

| Required role | Result | Evidence disposition |
| --- | --- | --- |
| 2 strict filter-preferred | NO WITNESS IN BOUNDED SEARCH | The Casey land-filter witness reverses under land-development versus creature-retention objectives. No reversal-free two-seat witness was certified; Raphael was structurally screened but not given a complete witness reconstruction. |
| 2 strict retention-preferred | FEASIBLE BUT UNCONSTRUCTED | One optimistic two-seat singleton-Mountain land-context witness survives the screened predicate. It lacks the complete objective, transformation and canonical fixture certificates, and the second disjoint role is absent. |
| 1 competing-hand-identity | STRUCTURALLY OBSTRUCTED | Tested two-card comparisons reverse under plausible objectives or fail support/multiplicity consistency. No stable two-seat comparison remains. |
| 1 exact-EV tie | NO WITNESS IN BOUNDED SEARCH | The Mountain/Mountain apparent land tie changes under the creature-availability objective, so it is not a stable exact-EV tie. |

The classifications are prospective feasibility dispositions, not fixture labels. “Feasible but unconstructed” means a bounded screened witness exists; it is not permission to count it. “No witness in bounded search” does not claim universal impossibility. “Structurally obstructed” records that the role failed the controlling objective/support tests in the tested family.

The narrow answer is that the accepted Hand-bottom/Draw quota cannot currently be shown honestly satisfiable. Construction is paused. This audit does not shrink the quota and does not rewrite Specification V2. A Specification V3 discussion requires HQ direction after deciding whether a larger bounded search is methodologically justified.

## Reproduce

```powershell
.venv/Scripts/python.exe scripts/hand_bottom_u_quota_feasibility_audit.py
.venv/Scripts/python.exe scripts/audit_pilot_fitness_v2_replacements.py
```

The JSON and this report have SHA-256 sidecars using canonical UTF-8/LF bytes. Pilot invocation count is zero; the 72-fixture packet remains unsealed; calibration remains blocked.
