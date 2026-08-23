# Coverage-Aware Engine Smoke Stage 0.1 First-Execution Failure Audit #1

## Audit constraints

- Frozen execution baseline: `5b5cdf02452ebd77c2c1bcc9f885d85290d53cdd`
- Original transcript SHA-256: `0a475bd1a162a8ca5af44baf251758660797df3d7d6d1d9dcd4a9250cb0b283f`
- Original gate report SHA-256: `ae2fe8ef909cf2046745dd00f8b5689e3c1a04e7cb241d42bcf5cdbd9a1b4be5`
- Original evidence banked unchanged at commit: `6d5cfb3`
- Smoke games executed during this audit: **0**
- Implementation/tests modified: none

The audit separates the semantic-registration stop from the later failure-artifact write failure.

## Primary stop verdict

**VALID FAIL-CLOSED STOP — generic engine resolution-order defect.**

The engine correctly rejected semantic presence whose referenced runtime object was no longer authoritative. The defect is upstream ordering: creature resolution permits synchronous ETB trigger processing and state-based actions to invalidate the newly resolved permanent before unsupported-semantic presence is registered.

### Reconstructed execution identity

The frozen matrix deterministically establishes the first attempted distinct game as:

- game: `april_oneil--bebop_rocksteady:canonical:8001`;
- pairing: April O'Neil vs. Bebop & Rocksteady;
- seed: 8001;
- orientation: canonical;
- duplicate member: first;
- accepted completed distinct games before the stop: zero.

The traceback proves the stop occurred during `execute_main_action → cast → resolve_top_of_stack`, in the creature-permanent resolution branch, at `report_unsupported_abilities(..., source=permanent)`.

The first-game deck and supported trigger paths identify the code-consistent source as a newly resolved second **Ray Fillet, Man Ray**. Ray Fillet is the only legendary creature in that first deck whose supported ETB path synchronously creates a Mutagen token and therefore invokes state-based actions before the later registration call. With another Ray Fillet already present, the legend-rule chooser can retain the older permanent and move the just-resolved incarnation away. The local `permanent` reference then names a former, nonauthoritative object.

The first fragment `unsupported_fragments()` attempts to register for Ray Fillet is `Flying`; the same card also exposes the Mutagen reminder limitation and unsupported counter-removal/Draw activation. Registration fails before any of them can be durably attached to the stale incarnation.

The exact runtime object ID cannot be independently recovered. It existed only in the in-memory `SmokeGameFailure.snapshot`; failure-artifact persistence failed before serialization. This audit does not fabricate that ID. Card/fragment and lifecycle reconstruction are supported by the deterministic matrix and unique engine path, while object-number provenance remains unavailable historical evidence.

### Ownership and authoritative expectation

This is not a Smoke matrix or reconciliation defect. The runner legally selected an engine-generated main action and the engine owned cast, Stack resolution, battlefield creation, ETB delivery, SBAs, and semantic registration.

Immediately after `move_object(..., battlefield)`, the new `Permanent` is authoritative. `resolve_top_of_stack()` then calls `_process_creature_entered_triggers()` before registration. That method creates the ETB event, puts triggers on the Stack, synchronously drains supported triggers, and permits their resolution/SBA boundaries. Token creation explicitly calls `check_state_based_actions()`. The legend rule can therefore make the local permanent former before line 5810 registers presence.

The rejected authority check is correct and must not be weakened. A stale former object must never acquire semantic presence.

### Smallest correction

Correct only the generic creature-resolution ordering so unsupported semantic presence is registered while the newly created battlefield incarnation is still authoritative, before synchronous ETB-trigger resolution can move it. The existing ETB rules-event producer already iterates registered occurrences, so registering presence before event/trigger delivery preserves prospective opportunity witnessing without card-name dispatch.

Adversarial regression requirements:

1. a normal creature resolution still registers unsupported presence and processes ETB triggers;
2. a second legendary creature with a supported ETB effect may be removed by the legend rule without stale-object registration or exception;
3. the kept and departed runtime identities remain distinct and authoritative;
4. ETB opportunity witnesses retain exact event/source/fragment provenance;
5. no semantic presence is ever created after its source becomes former;
6. ordinary creature, token-creating ETB, Stack/Priority, legend-rule, and Stage #002 behavior remain unchanged.

Do not special-case Ray Fillet, Mutagen, either deck, Smoke, or the legend rule.

## Failure-artifact persistence verdict

**ENVIRONMENT-SPECIFIC WRITE-AUTHORIZATION FAILURE — the accepted artifact contract was not satisfied for this launch, but no runner implementation defect is established.**

The runner caught the primary `SmokeGameFailure`, constructed the failure payload, and reached `_atomic_write()`. It then failed on the first temporary-file creation under `docs/cardcade` with `PermissionError`. No partial success artifact, failure artifact, sidecar, or temporary file remained.

Repository ACL inspection shows `NT AUTHORITY\\Authenticated Users` has inherited `Modify` permission and administrators/system have full control. The same checkout accepted explicitly authorized repository writes and atomic pytest artifacts. The failed Smoke command, however, ran inside a restricted tool sandbox whose writable roots did not include `C:\\Projects\\tmt`; read/execute access was available but repository writes were denied. This explains the exact boundary without invoking Windows newline behavior, OneDrive, Git locking, or runner corruption.

The accepted `_atomic_write()` implementation and its adversarial tests remain structurally sound. The contract nevertheless failed operationally for this execution because the launch environment lacked output authorization.

### Smallest persistence correction

No runner code change is justified. Before any future authorized rerun, execute the unchanged command in an environment with explicit write permission to the frozen repository output directory, and independently prove a preflight-only synthetic failure can atomically create its failure JSON and sidecar there. That infrastructure probe must not instantiate or execute a Smoke game.

If the authorized probe still fails, stop and investigate filesystem/runner behavior. Do not conflate that result with the primary engine-ordering correction.

## Overall gate

- Primary fail-closed behavior: **correct**
- Primary defect owner: **engine creature-resolution ordering**
- Artifact persistence owner: **launch environment authorization**
- Gameplay/card balance conclusion: **none**
- Smoke Stage 0.1: **BLOCKED**

Preserve this audit, implement only the bounded generic engine-ordering correction, validate it independently, and separately prove authorized atomic failure persistence. Do not rerun Smoke Stage 0.1 until both gates are accepted and integrated on a newly frozen merged-main baseline.

Action #14, calibration, Pilot/deck changes, Prototype 0.3, and the historical 900-game smoke remain blocked.
