# Action #16 — ETB Artifact-Condition Draw Acceptance Audit #1

**Candidate:** `586518efa0671f3898f86122210df0f778698cb7`  
**Audit type:** independent, evidence-only  
**Verdict:** **REJECT**

## Scope integrity

The candidate fingerprint independently reconstructed exactly. The frozen candidate consists of:

- `src/tmnt_design_studio/card_interpreter07.py`;
- `src/tmnt_design_studio/engine07.py`;
- `src/tmnt_design_studio/smoke01.py`;
- `src/tmnt_design_studio/stage002.py`;
- `tests/test_etb_artifact_draw_action.py`.

The audit did not modify those files, commit the candidate, or run Smoke Stage 0.1.

## Rules basis

The current official Magic Comprehensive Rules published from
<https://magic.wizards.com/en/rules> establish the relevant lifecycle.

- CR 603.4 defines an intervening-`if` clause. Its condition must be true when the triggering
  event occurs or the ability does not trigger. The condition is checked again as the ability
  resolves; if false then, the ability does nothing.
- CR 603.3a fixes the triggered ability's controller when it is put on the Stack. A later source
  control change does not substitute the source's current controller for that frozen ability
  controller.
- CR 603.6a evaluates an enters-the-battlefield trigger after the permanent is on the battlefield.
  An entering Artifact Creature can therefore satisfy this condition itself.

The candidate correctly represents the two intervening-`if` checkpoints structurally, but its
artifact predicate does not use the permanent's authoritative evaluated battlefield type.

## Corpus and recognition

The frozen TMT/PZA/TMC corpus independently reconstructs exactly one fully supported member:

| Card | Oracle ID | Set / collector | Exact fragment |
|---|---|---|---|
| Donatello, Turtle Techie | `f84850bc-6348-449e-bd82-bb39e2119bec` | TMT `37` | `When Donatello enters, if you control an artifact, draw a card.` |

The canonical membership payload hashes to:

`0fc23089e6083ca46b39b7f0cce35adf23e94db7d3e1b0b0e57ed50176f314f4`

The digest is not an Oracle ID. The required Donatello Oracle ID is the UUID shown above.

The recognizer accepts the authorized generic form (`this source` / `its controller controls`) and
the established printed self-name form (`Donatello` / `you control`). Adversarial near neighbors
remain unrecognized or nonexecutable: different controlled permanent types, Draw amounts,
`unless`, optional Draw, opponent conditions, artifact-count thresholds, artifact search,
non-ETB triggers, generic `this source` combined with unproven `you control` normalization, and
mismatched card names.

## Intervening-if and transaction behavior that passed

The existing and independently repeated probes establish:

- artifact at trigger time and resolution: one trigger, normal Stack/Priority/pass, exactly one
  Draw by the frozen trigger controller;
- artifact at trigger time but absent at resolution: the legitimate trigger remains on the Stack,
  resolves, records a false second condition, and draws nothing;
- no artifact at trigger time, artifact later: no trigger is created;
- no artifact at either checkpoint: no trigger is created;
- noncreature artifacts, artifact tokens, multiple artifacts, and an entering Artifact Creature's
  self-satisfaction work for unchanged printed types;
- adjacent entries and multiple sources preserve distinct event, trigger, and Stack identities;
- source departure or reincarnation does not relink the trigger;
- source control changes do not replace the frozen trigger controller;
- artifact controller changes before resolution are rechecked for the frozen controller;
- empty-library Draw enters the normal failed-Draw/SBA loss lifecycle with no continuing Priority;
- a legitimate child trigger generated during the parent resolution is not stacked until after the
  parent's `trigger_resolved` boundary;
- fabricated event subject provenance fails invariants and resolution before Draw mutation.

## Material blocker — printed type substituted for authoritative battlefield type

Both artifact-condition evaluators inspect `permanent.card.type_line`:

- `_controlled_artifact_ids()` performs the current resolution-time condition check using the
  printed definition;
- `_validate_etb_artifact_draw_provenance()` reconstructs the event-time artifact set by applying
  the same printed-type test to IDs in the event's battlefield authority snapshot.

The engine already represents authoritative battlefield characteristic changes through
`Permanent.type_line` / `type_line_override`. Magic asks whether the trigger controller actually
controls an artifact at each checkpoint, not whether a controlled permanent's printed card
definition contains `Artifact`.

Independent adversarial probes produced all three prohibited results:

| Authoritative state | Correct result | Candidate result |
|---|---|---|
| Printed Artifact with battlefield type overridden to `Enchantment` before the source ETB | no trigger | one trigger placed on Stack |
| Printed Enchantment with battlefield type overridden to `Artifact` before the source ETB | trigger | no trigger |
| Printed Artifact qualified initially, then battlefield type changed to `Enchantment` before resolution | trigger resolves without Draw | condition recorded true and one card drawn |

The first and third cases are silent false execution. The second is a false nonexecution. The
event-time evidence also fails the requested reconstructive standard: `battlefield_authority`
freezes object/controller membership, but it does not freeze the evaluated artifact characteristic
used by the condition. Re-reading a printed definition later cannot authenticate the historical
condition.

This defect is generic and rules-material even though the frozen Donatello games may not currently
apply a type-changing effect to the relevant artifacts.

## Canonical identities and regression gates

The candidate identities independently reconstruct exactly:

- Engine: `fc6b5247036af158e275dde50cb8274352c5613b`;
- Interpreter: `ba2f2809bdd64e63c25088635141140c17af8ca6`;
- Stage #002: `f26e59c2aa736b3c57cfa9ddefe8ccf8ac1aa524`.

Validation reproduced:

- full suite: **707 passed / 1 skipped**;
- focused Action #16 plus ETB/trigger/Draw/conformance/card-data regressions: **240 passed**;
- Ruff check: clean;
- Ruff format check: **51 files already formatted**;
- `git diff --check`: clean.

Acceptance #001 seeds 7001–7005 were each executed twice. Duplicate artifacts were byte-identical,
with the accepted trajectories unchanged:

| Seed | Winner | Turn | Duplicate digest |
|---:|---|---:|---|
| 7001 | Raphael | 14 | `899a1189be71a1efca47c29d70ace474e2704f1c1732b6a6d0ac22491d63acfd` |
| 7002 | Raphael | 18 | `ee915ff592d23c287b1a8b2edd1814dcce43bf209865462b56d40786e963b803` |
| 7003 | Leonardo | 19 | `9b4b6df3ef94084c090b74d9ecd9c804b3076a3ef6d4d76e684dca2a985136f7` |
| 7004 | Leonardo | 43 | `277231b3004fb3e9df49aa3c8fed6c2491d1be9f1ad89b9d2b8e16c212516f17` |
| 7005 | Raphael | 16 | `448703c5aa315eea31591e6cc3b133cb73a3221a85d5a4c9de7da2e1716852f0` |

Inspection found no Donatello, deck, matchup, Pilot, Acceptance, Stage #002, or Smoke-specific
gameplay dispatch. `smoke01.py` changes only canonical frozen identities.

## Smallest evidence-backed correction

Do not broaden Action #16 grammar or corpus membership.

1. Evaluate the current condition from each authoritative permanent's evaluated battlefield type
   (`Permanent.type_line`), not its printed `card.type_line`.
2. At trigger creation, freeze the authoritative artifact-condition facts needed to reconstruct the
   initial intervening-`if` result: at minimum the qualifying artifact incarnation IDs and their
   evaluated type/controller facts at that event.
3. Bind that immutable condition evidence to the ETB event and trigger, validate it in invariants,
   and reject fabricated/relinked historical artifact provenance.
4. At resolution, independently evaluate current authoritative battlefield state for the frozen
   trigger controller. Do not require historical qualifying artifacts to remain present.
5. Add the three type-change adversarial regressions above in both directions while preserving all
   currently passing lifecycle tests.

**REJECT — Action #16 uses printed card types instead of authoritative evaluated battlefield
characteristics for both intervening-if artifact checks; freeze event-time artifact-condition
provenance and evaluate the resolution condition from current authoritative permanent types.**
