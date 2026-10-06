# Krang Round 7-A — package conversion candidate

**Owner:** 🧪 Design Studio  
**Candidate:** `OBL-R7-KRANG-A`  
**Parent:** `OBL-BASELINE-003` Krang Prototype 0.2  
**Status:** DESIGN_FROZEN_PENDING_CARDCade_READINESS  
**Design branch:** `design-studio-krang-r7-a`

## Round 6 closure

Round 6 tested three one-slot replacements for one dormant Negate:

- R6-A: `-1 Negate / +1 Donatello, Turtle Techie`
- R6-B: `-1 Negate / +1 Chrome Dome`
- R6-C: `-1 Negate / +1 Retro-Mutation`

All three made Krang stronger in at least some cells, but none smoothed the matchup distribution. R6-C executed its suppression mechanism under the validated Aura runtime and still worsened distribution. The one-slot family is therefore closed for this round.

**Falsified for Round 6:** a one-card replacement of one dormant Negate, whether proactive material, artifact stabilization, or threat suppression, is sufficient to smooth Krang's matchup distribution.

## Candidate

Exact diff from Baseline 003 Krang:

- `Does Machines`: 2 → 1
- `Negate`: 3 → 2
- `Ray Fillet, Man Ray`: 3 → 4
- `Stockman, Mad Fly-entist`: 2 → 3

No land changes. No changes to Sewer-veillance Cam, Bespoke Bō, the core artifact creature package, Krang count, Ooze Spill, or Retro-Mutation.

## Design hypothesis

Krang's severe Raphael and Shredder matchups are not primarily a shortage of generic permanents. Preserved loss-signature evidence instead associates Krang's rare wins with higher-impact sequences involving Ray Fillet, Stockman, and Utrom Scientists.

R7-A tests whether reducing one setup slot and one reactive slot while increasing density of two already-demonstrated conversion/value cards can improve the weak cells without reproducing Round 6's April/Leonardo over-conversion.

This is a package-level hypothesis. It does not assign causal credit to card-presence correlations.

## Why these cuts

### Does Machines — 2 → 1

Historical Krang testing that increased Does Machines density worsened aggregate performance and balance. The preserved card-role dataset records a tested package with +2 Does Machines at -3.78 pp aggregate WR and +2.67 pp balance error. This is package-level evidence, not a single-card causal estimate, but it is sufficient to avoid protecting setup density by default.

### Negate — 3 → 2

Negate has repeatedly been behaviorally dormant in Krang experiment telemetry. Round 5/6 established that one copy can be removed without claiming counterspell execution as the source of candidate gains. R7-A removes only one copy; it does not continue the now-closed "one Negate for one generally useful card" experiment family.

## Why these additions

### Ray Fillet, Man Ray — 3 → 4

In the preserved Round 6 loss-signature diagnostic, Ray Fillet had positive win-presence lifts of:

- +33.6 pp vs Raphael
- +49.6 pp vs Shredder

A prior experiment replacing Ray Fillet with additional Krang, Master Mind copies was strongly negative. R7-A therefore restores emphasis on the demonstrated midgame conversion role rather than adding more top-end Krang density.

### Stockman, Mad Fly-entist — 2 → 3

In the same diagnostic, Stockman had positive win-presence lifts of:

- +57.0 pp vs Raphael
- +45.1 pp vs Shredder

Stockman is already part of Krang's identity and supported execution surface. R7-A increases access to that role by one copy without introducing a new card or semantic family.

## Diagnostic priorities

1. **Raphael — primary:** must improve materially beyond the Aura-runtime control baseline.
2. **Shredder — co-primary:** must improve materially while preserving the different loss-signature mechanism.
3. **April O'Neil — anti-polarization sentinel:** must not become another substantial Krang-favored extreme.
4. **Leonardo — anti-polarization sentinel:** must not reproduce the R6-C 72% Krang result.
5. Aggregate WR is secondary to distribution quality.

## Rejection criteria

Reject or return to Design Studio if any of the following occur:

- Raphael and Shredder remain effectively unchanged while healthier matchups create most of the aggregate gain.
- Mean matchup balance error worsens materially.
- Strict >60/40 or >70/30 counts increase without a compelling offset in the primary cells.
- April or Leonardo shows another disproportionate favorable swing.
- Runtime/semantic behavior differs between control and candidate in a way that prevents a clean comparison.
- Any card or rule required by this candidate is not semantically executable; fail closed rather than redesigning the deck.

## Identity

R7-A preserves mono-blue Krang's technology/artifact-engine identity while shifting two slots toward demonstrated midgame conversion and value. It does not add off-theme cards, another Turtle Techie/Chrome Dome-style generic body, or additional high-end Krang copies.

## Cardcade handoff

**NEXT MOVE → 🕹️ Cardcade**

Perform semantic/readiness review for the exact frozen `OBL-R7-KRANG-A` list. If the current merged runtime can execute the candidate and a runtime-compatible Baseline 003 control is available, run the isolated validation under the established frozen schedule. If runtime semantics must change, first perform the required unchanged Baseline 003 control refresh under the new runtime.

Do not redesign R7-A. Do not change Baseline 003. Do not run combined validation or promote anything. Preserve all evidence and return results to 🧪 Design Studio for interpretation.
