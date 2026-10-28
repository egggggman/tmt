"""Complete artificial native envelopes. Never constructs Game or plays a turn."""

import hashlib
import random

from tmnt_design_studio.fresh900_native import AUTHORITY_FIELDS, DICT_FIELDS, LIST_FIELDS


def native_snapshot(spec):
    snapshot = {name: [] for name in LIST_FIELDS}
    snapshot.update({name: {} for name in DICT_FIELDS})
    names = [seat.display_id for seat in spec.seats]
    players, authority_players, zones = [], [], []
    for index, name in enumerate(names):
        ids = [f"audit-library-{index}"]
        player = dict(
            name=name,
            life=20 if index == 0 else 0,
            library=1,
            library_object_ids=ids,
            hand=[],
            hand_object_ids=[],
            battlefield=[],
            graveyard=[],
            graveyard_object_ids=[],
            lost=index != 0,
            loss_reason=None if index == 0 else "life_zero_or_less",
            failed_draw_pending=False,
        )
        preimage = dict(
            library_object_ids=ids,
            hand_object_ids=[],
            battlefield_object_ids=[],
            graveyard_object_ids=[],
            exile_object_ids=[],
            life=player["life"],
            lost=player["lost"],
            failed_draw_pending=False,
        )
        players.append(player)
        authority_players.append(preimage)
        zones.append((tuple(ids), (), (), (), (), player["life"], player["lost"], False))
    initial = hashlib.sha256(repr(random.Random(spec.seed).getstate()).encode()).hexdigest()
    state = "a" * 64
    authority = (10, 0, "precombat_main", (), (), (), tuple(zones), state, 0)
    snapshot.update(
        engine_version="cardcade-0.9.0-alpha.1",
        turn=10,
        turns_started=10,
        terminal=True,
        active_player=names[0],
        phase="main",
        step="precombat_main",
        winner=names[0],
        priority=None,
        players=players,
        authoritative_state_fingerprint=hashlib.sha256(repr(authority).encode()).hexdigest(),
        authoritative_state_fingerprint_preimage=dict(
            scheme="engine07-authoritative-state-fingerprint-preimage-v1",
            turn=10,
            active_player_index=0,
            step="precombat_main",
            stack_object_ids=[],
            combat_attacker_ids=[],
            combat_blocks=[],
            players=authority_players,
            rng_state_digest=state,
            winner_index=0,
        ),
        rng=dict(
            seed=spec.seed,
            state_digest=state,
            records=[
                dict(
                    sequence=1,
                    domain="AUDIT_SYNTHETIC",
                    operation="shuffle",
                    result=[0],
                    state_before=initial,
                    state_after=state,
                    detail="retain RNG evidence",
                )
            ],
        ),
        events=[
            dict(
                event="AUDIT_SYNTHETIC",
                kind="synthetic",
                value=17,
                turn=10,
                phase="main",
                step="precombat_main",
            )
        ],
        conformance=dict(
            semantic_occurrences=[],
            opportunity_witnesses=[],
            opportunity_contexts=[],
            executed_references=[],
            stop_records=[],
        ),
        mill_three_evidence=dict(pre_states={}, transactions=[], identities=[]),
        krang_refill_evidence=dict(entries=[], transactions=[], pre_states={}, identities=[]),
        vigilante_evidence=dict(records=[], terminal_game=True, segments=[]),
        combat_damage=dict(
            step_kind="none",
            sequence=0,
            total_steps=0,
            first_qualified_ids=[],
            regular_initial_ids=[],
            evidence=[],
        ),
        native_extra={"nested": [1, {"complete": "retain all"}]},
    )
    return snapshot


def reconciliation(spec, raw, _manifest):
    """Mock conformance output with the real frozen report identity/evidence roles."""
    return dict(
        game_id=spec.game_id,
        seed=spec.seed,
        orientation=spec.orientation,
        seats=[seat.display_id for seat in spec.seats],
        winner=raw["winner"],
        turn=raw["turn"],
        rng_state_digest=raw["rng"]["state_digest"],
        authoritative_evidence={key: raw[key] for key in AUTHORITY_FIELDS},
        stop_records=[],
        invariant_violations=[],
    )
