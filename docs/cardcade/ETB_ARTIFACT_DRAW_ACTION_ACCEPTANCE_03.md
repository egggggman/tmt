# Action #16 — ETB Artifact-Condition Draw Acceptance Audit #3

**Candidate:** `e3265d40abbad25ed53b4be5849292c5fa954c52`  
**Audit type:** independent, evidence-only  
**Verdict:** **ACCEPT**

## Historical preservation and scope

The candidate and rejection chain independently reconstructed before audit:

- original candidate: `586518efa0671f3898f86122210df0f778698cb7`;
- Audit #2 candidate: `499ea571d2d6113eff567aa22e848ddf50bf1363`;
- Audit #1: `330ecbd0d79301a803b39fcde206bdcb3fe1418d310228a8cff1f2f9ec40e199`;
- Audit #2: `f592ec96c0f5c22c28afe89228adf889d2b62cc9ef6fe4ccf7ef226b6740abb4`.

The six candidate implementation/test files were not modified or committed. Smoke Stage 0.1 was
not run.

## Audit #1 reproduction

Independent states constructed outside the committed candidate regressions proved all three
characteristic defects remain closed:

| State | Result |
|---|---|
| Printed Artifact with authoritative battlefield type `Enchantment` before ETB | no trigger |
| Printed Enchantment with authoritative battlefield type `Artifact` before ETB | trigger and one Draw |
| Initially qualifying Artifact changed to `Enchantment` before resolution | existing trigger resolved with false condition and no Draw |

Trigger-time qualification derives from the creation-time event's frozen evaluated battlefield
characteristics. Resolution derives from current authoritative `Permanent.type_line` for the frozen
trigger controller. Printed `CardDefinition.type_line` is not substituted at either checkpoint.

## Audit #2 reproduction

The fully re-signed Audit #2 attack was independently reconstructed. A valid nonartifact decoy was
substituted as the historical qualifier, Artifact was removed from the genuine qualifier, and the
typed rules-event registry, trigger registry and Stack ability event pointer were changed together.

The forged downstream chain agreed internally. `check_invariants()` nevertheless rejected it with:

`rules event disagrees with immutable original evidence`

The authoritative state fingerprint was identical before and after rejection. No Draw or other
payload mutation occurred.

## Independent event-evidence trust anchor

The candidate creates one frozen `RulesEventEvidence` record at the same transition that creates the
typed `RulesEvent`, before downstream trigger or Stack delivery. It preserves:

- event ID and numeric cursor;
- event kind;
- player/controller index;
- subject incarnation IDs;
- source, target and amount fields;
- turn, step and active player;
- battlefield object/controller authority;
- evaluated battlefield type-line characteristics;
- relevant last-known battlefield facts.

The record is serialized separately as `rules_event_evidence`. `check_invariants()` requires unique,
contiguous evidence IDs/cursors and exact agreement among the frozen record, original serialized
`rules_event` ledger, typed rules-event registry, trigger record and Stack ability.

Independent isolated mutations of event ID, event cursor, event kind, controller, subject identity,
battlefield authority and evaluated characteristics all failed invariants. The candidate regressions
also cover source incarnation, qualifier identity/controller/type, Stack→trigger, trigger→event and
registry→original-ledger substitutions. Missing, duplicated or borrowed anchor records fail the
ledger membership/uniqueness checks.

This is an independent trust join, not another digest calculated from the mutually relinkable live
registry objects.

## Historical versus current state

The evidence anchor authenticates history without freezing future gameplay. Independent legitimate
mutation probes remained invariant-clean when, after trigger creation:

- the historical qualifier lost Artifact;
- it left or changed controller;
- a different current permanent acquired Artifact;
- a new artifact entered;
- the source changed controller or left;
- the source returned as a distinct incarnation.

The historical event continued to authenticate. Resolution independently asked whether the frozen
trigger controller currently controlled any artifact. It neither required the original qualifier nor
borrowed the source's current controller.

## CR 603.4 and Draw lifecycle

The current official Comprehensive Rules at <https://magic.wizards.com/en/rules> require an
intervening-`if` condition at trigger creation and again at resolution. The candidate reproduces all
four cases:

- true / true → one Draw;
- true / false → legitimate trigger resolves without Draw;
- false / later true → no trigger exists;
- false / false → no trigger exists.

The complete represented lifecycle remains:

`authoritative ETB → qualified trigger → Stack → Priority/pass → current-condition check → Draw one → failed-Draw/SBA processing`

The frozen trigger controller draws exactly one card. Source departure and reincarnation do not
relink the ability. Artifact tokens, noncreature artifacts, multiple mixed-characteristic artifacts
and self-qualifying entering Artifact Creatures work. Empty-library Draw produces the normal
terminal loss with no post-terminal Priority. Child triggers generated during resolution remain
deferred until after the parent's `trigger_resolved` boundary.

## Corpus and scope

The independently reconstructed fully supported corpus is exactly:

- Donatello, Turtle Techie;
- Oracle `f84850bc-6348-449e-bd82-bb39e2119bec`;
- TMT collector `37`;
- fragment `When Donatello enters, if you control an artifact, draw a card.`;
- digest `0fc23089e6083ca46b39b7f0cce35adf23e94db7d3e1b0b0e57ed50176f314f4`.

Near-neighbor grammar remains unsupported. Source inspection found no Donatello, deck, matchup,
Pilot, Acceptance, Stage #002 or Smoke-specific gameplay dispatch. The Stage #002 change only
serializes the new authoritative event evidence; `smoke01.py` changes only frozen identities.

Canonical identities independently reconstruct exactly:

- Engine: `1f0bceb95680b37eb4ef9dd6f9eea09ec5aac97e`;
- Interpreter: `ba2f2809bdd64e63c25088635141140c17af8ca6`;
- Stage #002: `98248213ab696ef6da2e33ef61f593c1ff9a323a`.

## Validation

- Full suite: **725 passed / 1 skipped**.
- Focused Action #16, ETB, trigger, Draw, conformance and card-data suite: **258 passed**.
- Dedicated Action #16 suite: **42 passed**.
- Ruff check: clean.
- Ruff format check: **51 files already formatted**.
- `git diff --check`: clean.

Acceptance #001 seeds 7001–7005 were independently replayed twice. Duplicate outputs were
byte-identical and accepted trajectories remained Raphael T14, Raphael T18, Leonardo T19, Leonardo
T43 and Raphael T16. Duplicate digests were:

- 7001: `fa46070f0562d8b37c57c40f214cc9bff817c603994b46e6c44f079ad8224235`;
- 7002: `e6d40a5edfcf8f330c54bd2db2b097415af9fe5a9f1ffb68acc8d435c57f7c0a`;
- 7003: `d4212c880e1bee8e78a7fad1d819bc26e8c743528c5ce44d6a992ef991c32b54`;
- 7004: `e657c25d96d4cf28bf5d9ab734acaafdd1e2111cd8453c86763bfd681196d352`;
- 7005: `1e0f8c8551bc1153df3109e8755954f09dbe55582ebd71a67b4eaf1b871b1f73`.

**ACCEPT — Action #16 correctly implements the bounded ETB artifact-condition Draw transaction,
and its trigger-time battlefield-characteristics decision is reconstructively authenticated through
independent immutable original rules-event evidence.**
