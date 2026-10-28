"""Read-only validation of the fd28 native snapshot envelope and authority tuple."""

from __future__ import annotations

import hashlib
import random
import re

from tmnt_design_studio.fresh900_identity import encoded, require

LIST_FIELDS = frozenset(
    [
        "rules_event_evidence",
        "stack",
        "pending_triggers",
        "stun_history",
        "scry",
        "etb_drain_gain_scry",
        "lifelink",
        "hand_bottom_draw",
        "discard_draw",
        "activated_abilities",
        "food_activations",
        "sneak",
        "players",
        "limitations",
        "events",
        "stage002_presence",
        "jury_rig_evidence",
        "food_search_evidence",
    ]
)
DICT_FIELDS = frozenset(
    [
        "conformance",
        "mill_three_evidence",
        "krang_refill_evidence",
        "vigilante_evidence",
        "rng",
        "combat_damage",
        "authoritative_state_fingerprint_preimage",
    ]
)
REQUIRED_FIELDS = (
    LIST_FIELDS
    | DICT_FIELDS
    | {
        "engine_version",
        "turn",
        "turns_started",
        "terminal",
        "active_player",
        "phase",
        "step",
        "winner",
        "authoritative_state_fingerprint",
        "priority",
    }
)
AUTHORITY_FIELDS = [
    "mill_three_evidence",
    "krang_refill_evidence",
    "jury_rig_evidence",
    "vigilante_evidence",
    "winner",
    "food_search_evidence",
    "rng",
    "stack",
    "priority",
    "pending_triggers",
    "rules_event_evidence",
    "scry",
    "etb_drain_gain_scry",
    "stun_history",
    "combat_damage",
    "lifelink",
    "hand_bottom_draw",
    "discard_draw",
    "activated_abilities",
    "food_activations",
    "sneak",
    "players",
    "events",
]


def _ids(value):
    require(
        type(value) is list and all(type(v) is str and v for v in value),
        "invalid native object IDs",
    )
    require(len(set(value)) == len(value), "duplicate native object IDs")
    return tuple(value)


def _hash(value):
    require(
        type(value) is str and bool(re.fullmatch(r"[0-9a-f]{64}", value)), "invalid native digest"
    )
    return value


def validate_native(snapshot: dict, spec) -> None:
    """Validate existing serialized evidence, never run/advance/repair a game."""
    require(
        type(snapshot) is dict and snapshot.keys() >= REQUIRED_FIELDS,
        "incomplete native snapshot envelope",
    )
    encoded(snapshot)  # No cycles, NaN or opaque non-JSON payloads in accepted records.
    for field in LIST_FIELDS:
        require(type(snapshot[field]) is list, f"invalid native list: {field}")
        if field != "limitations":
            require(
                all(type(v) is dict for v in snapshot[field]),
                f"invalid native evidence entries: {field}",
            )
    for field in DICT_FIELDS:
        require(type(snapshot[field]) is dict, f"invalid native object: {field}")
    require(
        snapshot["priority"] is None or type(snapshot["priority"]) is dict,
        "invalid native priority",
    )
    require(snapshot["engine_version"] == "cardcade-0.9.0-alpha.1", "native engine mismatch")
    require(snapshot["terminal"] is True, "nonterminal native result")
    require(
        type(snapshot["turn"]) is int
        and 0 < snapshot["turn"] <= 120
        and type(snapshot["turns_started"]) is int
        and snapshot["turns_started"] == snapshot["turn"],
        "invalid native turn",
    )
    require(
        all(type(snapshot[k]) is str and snapshot[k] for k in ("phase", "step")),
        "invalid native phase/step",
    )
    require(
        snapshot["events"]
        and all(
            {"event", "turn", "phase", "step"} <= v.keys()
            and type(v["event"]) is str
            and v["event"]
            and type(v["turn"]) is int
            and v["turn"] >= 0
            and type(v["phase"]) is str
            and type(v["step"]) is str
            for v in snapshot["events"]
        ),
        "missing native event evidence",
    )
    require(all(type(v) is str for v in snapshot["limitations"]), "invalid native limitations")
    conformance = snapshot["conformance"]
    for field in (
        "semantic_occurrences",
        "opportunity_witnesses",
        "opportunity_contexts",
        "executed_references",
        "stop_records",
    ):
        require(
            type(conformance.get(field)) is list
            and all(type(v) is dict for v in conformance[field]),
            f"missing native conformance: {field}",
        )

    players = snapshot["players"]
    names = [seat.display_id for seat in spec.seats]
    require(
        len(players) == 2 and [p.get("name") for p in players] == names,
        "native participants disagree with seats",
    )
    authority = snapshot["authoritative_state_fingerprint_preimage"]
    require(
        authority.get("scheme") == "engine07-authoritative-state-fingerprint-preimage-v1",
        "native fingerprint scheme mismatch",
    )
    winner = authority.get("winner_index")
    active = authority.get("active_player_index")
    require(
        type(winner) is int and winner in (0, 1) and snapshot["winner"] == names[winner],
        "native winner authority mismatch",
    )
    require(
        type(active) is int and active in (0, 1) and snapshot["active_player"] == names[active],
        "native active-player mismatch",
    )
    require(
        type(authority.get("turn")) is int
        and authority["turn"] == snapshot["turn"]
        and authority.get("step") == snapshot["step"],
        "native turn/step authority mismatch",
    )
    require(
        type(authority.get("players")) is list and len(authority["players"]) == 2,
        "missing native player authority",
    )
    zones = []
    all_ids = []
    for index, (player, preimage) in enumerate(zip(players, authority["players"], strict=True)):
        require(type(preimage) is dict, "invalid native player preimage")
        require(
            {
                "name",
                "life",
                "library",
                "library_object_ids",
                "hand",
                "hand_object_ids",
                "battlefield",
                "graveyard",
                "graveyard_object_ids",
                "lost",
                "loss_reason",
                "failed_draw_pending",
            }
            <= player.keys(),
            "incomplete native player evidence",
        )
        ids = [
            _ids(preimage.get(zone + "_object_ids"))
            for zone in ("library", "hand", "battlefield", "graveyard", "exile")
        ]
        all_ids.extend(value for zone in ids for value in zone)
        require(
            type(player["library"]) is int and player["library"] == len(ids[0]),
            "native library count mismatch",
        )
        for zone, position in (("library", 0), ("hand", 1), ("graveyard", 3)):
            require(
                _ids(player[zone + "_object_ids"]) == ids[position],
                f"native {zone} authority mismatch",
            )
        require(
            type(player["hand"]) is list
            and len(player["hand"]) == len(ids[1])
            and type(player["graveyard"]) is list
            and len(player["graveyard"]) == len(ids[3]),
            "native zone evidence count mismatch",
        )
        require(
            type(player["battlefield"]) is list
            and all(type(v) is dict for v in player["battlefield"])
            and tuple(v.get("object_id") for v in player["battlefield"]) == ids[2],
            "native battlefield authority mismatch",
        )
        require(
            type(preimage.get("life")) is int
            and type(player["life"]) is int
            and player["life"] == preimage["life"],
            "native life authority mismatch",
        )
        for flag in ("lost", "failed_draw_pending"):
            require(
                type(preimage.get(flag)) is bool and player[flag] is preimage[flag],
                f"native {flag} authority mismatch",
            )
        require(player["lost"] is (index != winner), "contradictory native terminal player state")
        zones.append((*ids, preimage["life"], preimage["lost"], preimage["failed_draw_pending"]))
    require(len(all_ids) == len(set(all_ids)), "native object occupies multiple player zones")
    rng = snapshot["rng"]
    require(type(rng.get("seed")) is int and rng["seed"] == spec.seed, "native RNG seed mismatch")
    state = _hash(rng.get("state_digest"))
    require(authority.get("rng_state_digest") == state, "native RNG authority mismatch")
    records = rng.get("records")
    require(type(records) is list and bool(records), "missing native RNG records")
    previous = hashlib.sha256(repr(random.Random(spec.seed).getstate()).encode()).hexdigest()
    for sequence, record in enumerate(records, 1):
        require(
            type(record) is dict
            and record.get("sequence") == sequence
            and type(record.get("sequence")) is int
            and type(record.get("domain")) is str
            and bool(record["domain"])
            and record.get("operation") in ("shuffle", "randrange")
            and "result" in record
            and record.get("state_before") == previous,
            "invalid native RNG record chain",
        )
        previous = _hash(record.get("state_after"))
        result = record["result"]
        if record["operation"] == "shuffle":
            require(
                type(result) is list
                and all(type(v) is int for v in result)
                and sorted(result) == list(range(len(result))),
                "invalid native shuffle evidence",
            )
        else:
            require(type(result) is int and result >= 0, "invalid native randrange evidence")
    require(previous == state, "native RNG tail mismatch")
    stack = _ids(authority.get("stack_object_ids"))
    require(
        stack == tuple(v.get("object_id") for v in snapshot["stack"]),
        "native stack authority mismatch",
    )
    attackers = _ids(authority.get("combat_attacker_ids"))
    blocks = authority.get("combat_blocks")
    require(
        type(blocks) is list
        and all(
            type(v) is list and len(v) == 2 and all(type(s) is str and s for s in v) for v in blocks
        ),
        "invalid native combat blocks",
    )
    preimage = (
        snapshot["turn"],
        active,
        snapshot["step"],
        stack,
        attackers,
        tuple(tuple(v) for v in blocks),
        tuple(zones),
        state,
        winner,
    )
    require(
        _hash(snapshot["authoritative_state_fingerprint"])
        == hashlib.sha256(repr(preimage).encode()).hexdigest(),
        "native fingerprint mismatch",
    )


def validate_reconciliation(snapshot: dict, spec, report: dict) -> None:
    require(type(report) is dict, "reconciliation object required")
    expected = dict(
        game_id=spec.game_id,
        seed=spec.seed,
        orientation=spec.orientation,
        seats=[seat.display_id for seat in spec.seats],
        winner=snapshot["winner"],
        turn=snapshot["turn"],
        rng_state_digest=snapshot["rng"]["state_digest"],
    )
    for key, value in expected.items():
        require(
            key in report and encoded(report[key]) == encoded(value),
            f"reconciliation identity conflict: {key}",
        )
    evidence = report.get("authoritative_evidence")
    require(type(evidence) is dict, "missing reconciliation authority")
    for key in AUTHORITY_FIELDS:
        require(
            key in evidence and encoded(evidence[key]) == encoded(snapshot[key]),
            f"reconciliation evidence conflict: {key}",
        )
    require(
        report.get("invariant_violations")
        == [item for item in snapshot["events"] if item.get("event") == "invariant_violation"],
        "reconciliation invariant mismatch",
    )
    require(
        type(report.get("stop_records")) is list
        and all(
            encoded(item) in [encoded(v) for v in report["stop_records"]]
            for item in snapshot["conformance"]["stop_records"]
        ),
        "reconciliation lost native stop evidence",
    )
