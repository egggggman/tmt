# Semantic Registration / ETB Ordering Correction Acceptance Audit #1

## Verdict

**ACCEPT — the bounded semantic-registration / ETB event-ordering correction is suitable to freeze and integrate.**

## Audit target

- Candidate branch: `agent/cardcade-etb-registration-order`
- Candidate fingerprint: `81b29800dcc7c70b81a81a926aae1dab03240fff`
- Evidence checkpoint: `fc23619`
- Baseline engine identity: `590db7fe144963be52b8c7abaa0e20f3fc6da2d9`
- Corrected engine identity: `f581d2dbf5e70606525de7d50e664e9b1721c0e2`

The audit did not modify the four candidate files and did not execute Smoke Stage 0.1.

## Scope integrity

The candidate changes exactly four files:

- `src/tmnt_design_studio/engine07.py`
- `src/tmnt_design_studio/smoke01.py`
- `tests/test_conformance07.py`
- `tests/test_engine07.py`

The `smoke01.py` delta changes only the frozen Git-clean identity for `engine07.py`. The Smoke matrix, runner behavior, classifications, failure handling, and `45 / 180 / 360` plan are unchanged. No Action, Pilot, deck, or named-card dispatch was added.

## Authoritative lifecycle

Creature spell resolution now performs the bounded lifecycle established by the failure audit:

1. create and register the new battlefield incarnation;
2. emit its authoritative `CREATURE_ENTERED` rules event;
3. register semantic presence for that exact authoritative incarnation;
4. detect and deliver triggers through the existing machinery;
5. apply the existing SBA boundary.

The ordering is implemented through an optional post-event callback in the generic creature-entry processor. The callback runs after `_new_rules_event()` has allocated and stored the event, but before trigger detection and synchronous trigger/SBA consequences. The applicability validator was not weakened.

`SemanticOccurrence.registration_event_cursor` therefore equals the exact event number of the source object's `CREATURE_ENTERED` event. Registration's existing-event join can authenticate that event without accepting an earlier or later event.

## Independent adversarial reconstruction

An audit-only external probe constructed two adjacent creature-entry events for identical Oracle definitions and registered each semantic through the corrected lifecycle. It independently established:

- two distinct authoritative `CREATURE_ENTERED` event identities;
- two distinct runtime object identities and semantic occurrences;
- each occurrence cursor exactly matched its own entry event;
- each witness referenced only its own entry event;
- neither adjacent event could be borrowed by the other occurrence;
- cursor substitutions at `N-1` and `N+1` failed applicability validation;
- controller, runtime-object, and Oracle-fragment substitutions failed closed;
- the resulting state passed engine invariants.

The live applicability path now also explicitly rejects a semantic occurrence whose recorded controller disagrees with the authoritative source controller. Historical witnesses continue to use their immutable recorded controller and are not invalidated by later ordinary state changes.

## Synchronous departure boundary

The generic legendary-permanent regression reconstructs the previous ordering defect's critical case:

- the new legendary battlefield incarnation receives its `CREATURE_ENTERED` event;
- semantic presence is registered afterward against that same incarnation and event cursor;
- synchronous ETB processing occurs;
- the legend-rule SBA removes the new incarnation;
- the semantic occurrence remains legitimate historical presence for the now-`former` object;
- presence does not imply `EXECUTED` without authoritative execution evidence.

Thus the cursor correction does not reintroduce the earlier stale-object failure: registration still occurs while the new incarnation is authoritative, before synchronous processing can remove it.

## Preserved boundaries

- Non-ETB semantic presence continues to use its existing coherent registration provenance.
- Create Token and other entry callers receive no callback unless they explicitly request one; their ordering and behavior are unchanged.
- Trigger delivery, Stack/Priority behavior, and SBAs remain on their existing paths.
- Stale, fabricated, relinked, wrong-controller, wrong-object, wrong-fragment, and adjacent-event provenance remains fail-closed.
- No Smoke game was run and no prior Smoke failure artifact was altered.

## Validation evidence

- Full regression suite: `624 passed / 1 skipped`
- Focused engine/conformance/Smoke-runner suite: `96 passed`
- Independent audit provenance probe: PASS
- Ruff format: clean
- Ruff check: clean
- `git diff --check`: clean
- Candidate fingerprint after audit: `81b29800dcc7c70b81a81a926aae1dab03240fff`

## Decision

The correction binds self-ETB semantic applicability to the exact authoritative entry event while preserving authoritative incarnation evidence through synchronous departure. It is bounded, generic, deterministic, and does not change Smoke behavior beyond updating the frozen engine identity.

**ACCEPT — the bounded semantic-registration / ETB event-ordering correction is suitable to freeze and integrate.**
