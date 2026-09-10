# Pilot Fitness preparation: return to HQ

**INCONCLUSIVE SUITE READINESS. This is a preserved preparation diagnostic, not the sealed assessment packet.** No Pilot has been invoked or scored. The requested 96-fixture packet and full assessment harness are incomplete. No fitness claim is made.

Preparation base: `ca9757b956eafc4b8d03c495dabb03eaab6fe931`.
Frozen engine: `de52f57a24a5c29a258573ad673051a0aa5c7e5c`.
Gate audit: `e28cd6dcd5532b84d38c45d3a710077e5cb589b4`.
The latest HQ instruction accepts the specification and authorizes preparation only. Its historical PROPOSED label is preserved rather than rewritten.

## Why preparation stops here

The accepted specification requires four forced tactical fixtures per hook, at least two action-required and two conservative-choice cases per hook, and judgments based on information actually available to the Pilot. Section 3 explicitly requires INTERFACE-LIMITED attribution when necessary public facts are absent. Section 4 says: "Do not construct a false obligation merely to fill a quota: inability to supply a valid represented case is a suite-readiness limitation requiring HQ revision before scoring."

Source inspection exposes two concrete input-contract gaps that prevent establishing those tactical quotas on the currently proposed basis:

1. `ScryView` contains only player_index, requested and inspected card IDs/names. `HandBottomDrawView` and `DiscardDrawView` contain only player_index and hand card IDs/names. They do not carry life, battlefield, mana, library size or turn context. A claim such as "filter this land because enough mana is already available" depends on facts absent from the hook. A discard/Draw decision involving the public fact of an empty library likewise cannot be justified to this hook using that fact. Using a hidden next card to force a profitable filter is separately prohibited. Card names alone do not establish these context-dependent resource objectives.
2. `choose_priority` receives GameView plus legal ActionOptions. GameView has no Stack objects, spell names/effects or target relationships. The counter option's target_id is a Stack identity, not a description of the spell being countered or its threatened permanent. The engine checks that the opponent's spell targets a controlled creature/artifact, but that legality predicate does not establish which legal response is tactically necessary. Scoring an expensive counter against an unspecified spell as obligatory would leak the evaluator's state into the oracle.

These are source-backed limitations, not a proof that no narrowly constructed fixture of any kind could ever work. Empty-hand, singleton-option, identity and pass-legality cases are feasible, but substituting them for the required tactical and useful-action quotas would weaken the accepted specification. Likewise an externally stated "always prefer card X" objective would not establish gameplay competence from the actual hook inputs. No such substitutions were made.

The broader GameView opponent-hand exposure remains a separate risk already recorded in the specification. Correcting that exposure would not by itself supply the missing private-choice context or Stack description.

## Work preserved and validation

`scripts/validate_pilot_fitness_preparation.py` is a read-only AST/source-identity preflight entry point. It imports neither the engine nor either Pilot, instantiates no Game and has no scoring mode. It authenticates the frozen engine/Pilot/runner Git blobs and accepted specification, inventories actual dataclass fields and protocol hooks, and reports the required quotas alongside the unresolved state. Its deliberate exit code 2 means suite readiness is inconclusive; this is not an exception or Pilot failure.

The saved JSON is its reproducible output, including source identities and preflight source SHA-256. Two executions produced identical output and exit code 2. Ruff check and format check passed after correcting initial import/line-format findings. No gameplay simulation, Stage/Smoke batch, Pilot invocation, oracle outcome evaluation or deck revision occurred. JSON and this report have SHA-256 sidecars. The preflight script identity is sealed inside the JSON rather than relying on a self-referential commit hash.

Reproduce with `.venv/Scripts/python.exe scripts/validate_pilot_fitness_preparation.py`; compare canonical JSON with the saved artifact and authenticate its sidecar. Current checkout hashes are explicitly distinguished from frozen Git blob hashes for Windows line-ending differences. Source drift raises an error rather than reinterpreting the frozen reference.

## Packet accounting

| Required deliverable | Preserved status |
| --- | --- |
| 96 canonical fixtures, 12 per hook / 4 per category | Required quotas inventoried; zero fixtures sealed. Not a completed manifest. |
| Both seats, permutations, identity transforms | Required design inventoried; no fabricated variants or claims of validation. |
| Privacy list and K | Undetermined, represented as null, not zero. |
| Final invocation count | Undetermined; remains 2,304 + 4K, not a runnable commitment. |
| Acceptable sets, horizons, seeds and reconstruction | Not sealed; depend on resolving admissible input-grounded tactical fixtures. |
| Source identities | Exact frozen engine/Pilot/runner blobs, spec digest and diagnostic source digest preserved. |
| Decision ownership | Existing eight Pilot hooks retained; engine-default choices are not reassigned. |
| Actual invocations / scoring | Zero; scoring remains NOT AUTHORIZED. |

No candidate is being offered as ready for a scoring gate. Preserving this diagnostic prevents an unreviewed reduction of the intended assessment from appearing later as compliance.

## HQ decision needed

Resolve the input/fixture contract before continuing the 96-fixture packet. HQ can either authorize a separately scoped input-contract assessment/change, with a new versioned assessment baseline, or revise the initial specification to separate feasible interface/legality checks from unassessable tactical competence. Neither route is authorized or implemented here. If HQ provides an input-grounded fixture construction that satisfies the existing quotas without changes, preparation can instead resume under the existing spec after that construction is reviewed.

The recommended next decision is a bounded input-contract review for the three private-choice hooks and Priority, explicitly keeping engine semantics and both Pilot policies frozen. This is a recommendation only. No automatic Action #33, interface adapter, extra context, Pilot memory, runner expansion or replacement oracle has been introduced.

Engine, both Pilots, decks and Stage/Smoke matrices remain unchanged. Actual calibration remains BLOCKED; Action #33 and Prototype 0.3 remain NOT AUTHORIZED. HQ review is required before revising preparation; Pilot scoring is still prohibited.
