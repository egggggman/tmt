# Action #16 — ETB Artifact-Condition Draw Acceptance Audit #2

**Corrected candidate:** `499ea571d2d6113eff567aa22e848ddf50bf1363`  
**Historical rejected candidate:** `586518efa0671f3898f86122210df0f778698cb7`  
**Audit #1 SHA-256:** `330ecbd0d79301a803b39fcde206bdcb3fe1418d310228a8cff1f2f9ec40e199`  
**Audit type:** independent, evidence-only  
**Verdict:** **REJECT**

## Preservation and scope

The corrected candidate fingerprint and Audit #1 digest independently reconstructed exactly before
the audit. The five candidate files were not modified or committed. Smoke Stage 0.1 was not run.

## Audit #1 correction

All three defects that rejected Audit #1 are closed in independent states constructed outside the
candidate regression suite:

| Adversarial authoritative state | Required result | Corrected result |
|---|---|---|
| Printed Artifact; battlefield type overridden to `Enchantment` before ETB | no trigger | no trigger |
| Printed Enchantment; battlefield type overridden to `Artifact` before ETB | trigger and Draw if still true at resolution | one trigger and one Draw |
| Artifact qualified at ETB; battlefield type changed to `Enchantment` before resolution | existing trigger resolves without Draw | existing trigger resolved with `condition_met: false` and no Draw |

`_controlled_artifact_ids()` now reads authoritative `Permanent.type_line`. The ETB rules event now
freezes `(object ID, controller, evaluated type line)` facts in `battlefield_characteristics`.
Action #16's trigger-time validator derives the historical artifact set from those facts rather than
from printed `CardDefinition.type_line` or later battlefield state.

## CR 603.4 lifecycle

The current official Comprehensive Rules at <https://magic.wizards.com/en/rules> establish that an
intervening-`if` condition is checked when the ability would trigger and again as it resolves.
Independent probes and regression inspection establish all four outcomes:

- true / true: trigger, Stack, Priority/pass, one Draw by the frozen trigger controller;
- true / false: the legitimate trigger remains and resolves without Draw;
- false / later true: no trigger exists;
- false / false: no trigger exists.

The corrected implementation also passes the represented boundaries for artifact tokens,
noncreature artifacts, multiple mixed printed/current characteristics, self-qualifying entering
Artifact Creatures, printed Artifact/current nonartifact entering sources, artifact departure,
controller change, replacement artifacts, frozen source controller, source departure and source
reincarnation. Resolution asks whether the frozen trigger controller currently controls any
authoritative artifact; it does not require the original qualifying artifact to remain.

The Draw transaction remains ordered as ETB event → qualified trigger → Stack → Priority/pass →
second condition check → Draw one → failed-Draw/SBA processing. Empty-library Draw terminates
normally, and child trigger delivery remains after the parent's `trigger_resolved` boundary.

## Material blocker — fully relinked historical facts are not independently authenticated

The new event characteristics are immutable within a `RulesEvent`, but the invariant authenticates
them only through circular live links:

- `TriggeredAbilityObject.event`;
- `_triggers[trigger_id].event`;
- `_rules_events[event_id]`.

No invariant reconciles the linked typed event's frozen characteristics with the independently
serialized `rules_event` ledger entry created when the event actually occurred.

An independent re-signed tampering probe started with a valid ETB trigger and three battlefield
objects: the real printed/current Artifact, the triggering creature, and a real nonartifact decoy.
It then:

1. changed the real artifact's frozen historical type to `Enchantment`;
2. changed the decoy's frozen historical type to `Artifact`;
3. replaced the rules-event registry entry with that forged immutable event;
4. replaced the trigger registry entry with a correspondingly relinked immutable trigger; and
5. relinked the Stack ability to the same forged event.

The original event ledger still recorded:

- real artifact → `Artifact`;
- source → `Creature — Turtle`;
- decoy → `Enchantment`.

The forged linked event instead recorded:

- real artifact → `Enchantment`;
- source → `Creature — Turtle`;
- decoy → `Artifact`.

`check_invariants()` returned successfully: **`ACCEPTED_FORGERY`**. Thus internally consistent
relinking can substitute the qualifying historical object and evaluated type while retaining the
claimed trigger-time decision. This directly fails Audit #2's forged type-line, artifact relinking,
fabricated qualifying artifact, and removal-of-the-real-qualifier attacks.

The candidate's existing tampering test changes only `TriggeredAbilityObject.event`. It correctly
fails because the other two pointers still reference the original event, but it does not prove
independent authentication of the historical facts after all live links are re-signed.

The rules behavior is now correct in ordinary execution; the remaining blocker is reconstructive
provenance/invariant strength.

## Corpus, identities and scope boundary

The independently reconstructed fully supported corpus remains exactly:

- Donatello, Turtle Techie;
- Oracle `f84850bc-6348-449e-bd82-bb39e2119bec`;
- TMT collector `37`;
- exact fragment `When Donatello enters, if you control an artifact, draw a card.`;
- corpus digest `0fc23089e6083ca46b39b7f0cce35adf23e94db7d3e1b0b0e57ed50176f314f4`.

Canonical identities reconstruct exactly:

- Engine: `dee953771ec107a5fef0e88b9c006df22e12c1e1`;
- Interpreter: `ba2f2809bdd64e63c25088635141140c17af8ca6`;
- Stage #002: `f26e59c2aa736b3c57cfa9ddefe8ccf8ac1aa524`.

Near-neighbor forms remain unsupported. Inspection found no Donatello, deck, matchup, Pilot,
Acceptance #001, Stage #002, or Smoke-specific gameplay dispatch. `smoke01.py` changes remain
frozen-identity bookkeeping only.

## Validation

- Full suite: **713 passed / 1 skipped**.
- Focused Action #16, ETB, trigger, Draw, conformance and card-data suite: **246 passed**.
- Ruff check: clean.
- Ruff format check: **51 files already formatted**.
- `git diff --check`: clean.

Acceptance #001 seeds 7001–7005 were replayed twice. Duplicate outputs were byte-identical and
accepted trajectories remained Raphael T14, Raphael T18, Leonardo T19, Leonardo T43, and Raphael
T16. Their corrected-candidate duplicate digests were:

- 7001: `608ea008572358beb721dbc9855262f3c1eb09c42fe39d991204a00e4f81ef83`;
- 7002: `a483006f210e70bf114fcbe76c1b95e6c0e1813cfcd752b95e66e34a97336e2b`;
- 7003: `38a3cf80da07b5b5004d75cbeec4770aa92fb8ec51005d262a1612bddab92d81`;
- 7004: `5e02196dbd593de8dbab7996f65db3cbfc37a43e16b122095f3dd9c564e3cfd9`;
- 7005: `126a85c50b3bcec83114f02c4ecb799bc086ccda35f6628d83618cf11649cc2d`.

## Smallest generic correction

Do not change Action #16 grammar, corpus, condition evaluation, or Draw lifecycle.

Add an independent immutable rules-event evidence record (or equivalently authenticate the typed
event against the existing original event ledger) that freezes the event ID, kind, subjects,
controller, battlefield authority and evaluated battlefield characteristics. Both invariants and
Action #16 resolution must require exact agreement among:

`original event evidence → typed RulesEvent → TriggerInstance → Stack ability`.

Reject missing, duplicate, altered, substituted, or borrowed historical characteristic records.
Add adversarial coverage that re-signs all three live links while leaving the original event evidence
unchanged; it must fail before Draw or any payload mutation. Preserve the now-correct current
`Permanent.type_line` resolution check.

**REJECT — the CR 603.4 battlefield-characteristics behavior is corrected, but fully relinked event,
trigger and Stack references can substitute forged historical artifact facts because invariants do
not authenticate them against independent original rules-event evidence.**
