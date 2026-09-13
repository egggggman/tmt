# Menace / Multiple Blockers — Pre-change Architecture Checkpoint

Baseline: `5f575c98bc4e1a7e0b67a916d2285767cf7c6402` (planning merge present; no Menace implementation changes).

Current representation is `ActionOption.blocks: tuple[tuple[str, str], ...]`, with `_combat_blocks` carrying the same attacker/blocker pairs. The intended shape can name repeated attacker IDs, but the legal generator does not use that capacity: `legal_block_options()` calls `generate_blocks()`, which greedily assigns at most one available blocker per attacker and returns `dict[str, Permanent]`. `execute_block_action()` reconstructs the same one-to-one mapping and rejects any stale or fabricated tuple. `resolve_combat_damage()` also materializes `dict[attacker_id, blocker]`, so only one blocker reaches allocation/evidence for each attacker.

`blocking_restriction()` currently handles the two power-based printed restrictions. Menace is represented in the keyword enum/interpreter vocabulary but is not a blocker-count legality rule. Existing combat damage evidence supports one blocker, trample split, first strike/double strike, deathtouch-derived lethal values, lifelink and terminal cleanup; all must retain their existing one-block behavior.

Affected surfaces: `ActionOption`, `legal_block_options`, `generate_blocks`, `execute_block_action`, `_unblocked_attackers`, `resolve_combat_damage`, combat snapshot/evidence, and the compatibility `Game.combat()` adapter. Existing tests cover ordinary block legality, one-to-one generation, trample, first/double strike, lifelink, Sneak timing, invariants, stale identities, and explicit rejection of repeated-attacker multi-block tuples. The Menace packet will add deterministic multi-block fixtures and update only assertions whose old one-to-one expectation is intentionally superseded.

Evidence requirement: every accepted multi-block assignment must preserve attacker order, blocker order, source/target identity, legality reason, allocation order and damage-step identity in authoritative event and `CombatDamageStepEvidence` records. No evaluator-only Menace result is sufficient.
