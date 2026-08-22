"""Evidence-only runner for the frozen Cardcade Acceptance Stage #002 design."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from tmnt_design_studio.card_data import CardDataCatalog, load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, TokenDefinition
from tmnt_design_studio.conformance07 import semantic_key
from tmnt_design_studio.engine07 import Game, load_deck, load_facts
from tmnt_design_studio.pilot07 import AcceptancePilot, Pilot


@dataclass(frozen=True)
class DeckSpec:
    display_id: str
    relative_path: str


@dataclass(frozen=True)
class PairingSpec:
    pairing_id: str
    first: DeckSpec
    second: DeckSpec
    seeds: tuple[int, int]


@dataclass(frozen=True)
class GameSpec:
    game_id: str
    pairing_id: str
    seed: int
    orientation: str
    seats: tuple[DeckSpec, DeckSpec]


PAIRINGS = (
    PairingSpec(
        "donatello-krang",
        DeckSpec("donatello-p0.2", "decks/donatello/PROTOTYPE_0.2.txt"),
        DeckSpec("krang-p0.2", "decks/krang/PROTOTYPE_0.2.txt"),
        (7201, 7202),
    ),
    PairingSpec(
        "michelangelo-bebop-rocksteady",
        DeckSpec("michelangelo-p0.1", "decks/michelangelo/PROTOTYPE_0.1.txt"),
        DeckSpec("bebop-rocksteady-p0.1", "decks/bebop_rocksteady/PROTOTYPE_0.1.txt"),
        (7211, 7212),
    ),
    PairingSpec(
        "splinter-shredder",
        DeckSpec("splinter-p0.1", "decks/splinter/PROTOTYPE_0.1.txt"),
        DeckSpec("shredder-p0.1", "decks/shredder/PROTOTYPE_0.1.txt"),
        (7221, 7222),
    ),
    PairingSpec(
        "april-casey",
        DeckSpec("april-oneil-p0.1", "decks/april_oneil/PROTOTYPE_0.1.txt"),
        DeckSpec("casey-jones-p0.1", "decks/casey_jones/PROTOTYPE_0.1.txt"),
        (7231, 7232),
    ),
)


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _token_definition_identity(definition: TokenDefinition) -> str:
    """Identify authoritative token characteristics without inventing an Oracle identity."""
    return "token-definition:" + stable_digest(
        {
            "name": definition.name,
            "type_line": definition.type_line,
            "colors": list(definition.colors),
            "power": definition.power,
            "toughness": definition.toughness,
            "oracle_text": definition.oracle_text,
            "keywords": list(definition.keywords),
            "mana_cost": definition.mana_cost,
            "mana_value": definition.mana_value,
        }
    )


def _runtime_token_semantic_key(
    definition: TokenDefinition,
    *,
    object_id: str,
    owner: int,
    creation_event_id: str,
    fragment_index: int,
    fragment: str,
) -> str:
    runtime_identity = "runtime-token:" + stable_digest(
        {
            "token_definition_identity": _token_definition_identity(definition),
            "object_id": object_id,
            "owner": owner,
            "creation_event_id": creation_event_id,
        }
    )
    return semantic_key(runtime_identity, 0, fragment_index, fragment)


def stage_games() -> tuple[GameSpec, ...]:
    games: list[GameSpec] = []
    for pairing in PAIRINGS:
        for orientation, seats in (
            ("canonical", (pairing.first, pairing.second)),
            ("reversed", (pairing.second, pairing.first)),
        ):
            for seed in pairing.seeds:
                games.append(
                    GameSpec(
                        f"{pairing.pairing_id}:{orientation}:{seed}",
                        pairing.pairing_id,
                        seed,
                        orientation,
                        seats,
                    )
                )
    return tuple(games)


def _deck_rows(path: Path) -> tuple[tuple[int, str], ...]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line == "Deck":
            continue
        quantity, name = line.split(" ", 1)
        rows.append((int(quantity), name))
    if sum(quantity for quantity, _name in rows) != 60:
        raise ValueError(f"{path}: Stage #002 requires an immutable 60-slot deck")
    return tuple(rows)


def _observability(
    source_name: str, fragment: str, limitations: tuple[str, ...]
) -> dict[str, object]:
    """Conservatively map static text to an accepted bounded witness family."""
    folded = fragment.casefold()
    families: list[str] = []
    if re.match(r"^(?:\{[0-9WUBRG]+\})+(?:, \{T\})?[^:]*:", fragment):
        families.append("activation_available")
    if any(term in folded for term in ("leaves the battlefield", " dies", "put into a graveyard")):
        families.append("permanent_departed")
    if "would" in folded or "instead" in folded:
        families.append("replacement_evaluation")
    if folded.startswith("counter target spell") or folded.startswith(
        "counter target noncreature spell"
    ):
        families.append("stack_response")
    if Game._artifact_dependency_mode(fragment, source_name) is not None:
        families.append("artifact_dependency")
    if Game._unconstrained_creature_target_shape(fragment):
        families.append("target_choice_available")
    if limitations and not families:
        return {
            "status": "opportunity_not_observable",
            "producer_families": [],
        }
    return {
        "status": "bounded_producer" if families else "fully_supported",
        "producer_families": sorted(set(families)),
    }


def _semantic_coverage(
    interpreter: CardInterpreter,
    card: object,
    fragment: str,
    limitations: tuple[str, ...],
) -> dict[str, object]:
    if fragment in card.keywords and not limitations:
        return {
            "family": "keyword_fact",
            "payload_executable": True,
            "parent_executable": True,
            "followup_executable": True,
            "fully_supported": True,
            "limitations": [],
        }
    candidates = (
        ("create_token", interpreter.token_semantic_coverage(card, fragment)),
        ("deal_damage", interpreter.damage_semantic_coverage(card, fragment)),
        ("hand_bottom_draw", interpreter.hand_bottom_draw_semantic_coverage(card, fragment)),
        ("discard_draw", interpreter.discard_draw_semantic_coverage(card, fragment)),
        ("scry", interpreter.scry_semantic_coverage(card, fragment)),
        ("activated_ability", interpreter.activated_ability_semantics(card, fragment)),
        ("strike", interpreter.strike_semantic_coverage(card, fragment)),
        ("trample", interpreter.trample_semantic_coverage(card, fragment)),
        ("lifelink", interpreter.lifelink_semantic_coverage(card, fragment)),
        ("sneak", interpreter.sneak_semantic_coverage(card, fragment)),
    )
    for family, interpreted in candidates:
        if interpreted is None:
            continue
        coverage = interpreted.coverage
        return {
            "family": family,
            "payload_executable": coverage.payload_executable,
            "parent_executable": coverage.parent_executable,
            "followup_executable": coverage.followup_executable,
            "fully_supported": coverage.fully_supported,
            "limitations": list(coverage.limitations),
        }
    supported = not limitations
    return {
        "family": "represented_engine" if supported else "unclassified_unsupported",
        "payload_executable": supported,
        "parent_executable": supported,
        "followup_executable": supported,
        "fully_supported": supported,
        "limitations": list(limitations),
    }


def load_catalog(root: Path) -> CardDataCatalog:
    return load_card_data(
        root / "cardcade" / "scryfall-tmt-pza-tmc-2026-08-13.json",
        root / "cardcade" / "scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )


def build_deck_manifest(root: Path, spec: DeckSpec, catalog: CardDataCatalog) -> dict[str, object]:
    path = root / spec.relative_path
    raw = path.read_bytes()
    rows = _deck_rows(path)
    names = {name for _quantity, name in rows}
    facts = load_facts(catalog, names)
    interpreter = CardInterpreter()
    cards = []
    fragment_members = []
    for quantity, name in rows:
        card = facts[name]
        unsupported: dict[str, set[str]] = {}
        for fragment, reason in interpreter.unsupported_fragments(card):
            unsupported.setdefault(fragment, set()).add(reason)
        fragments = interpreter.fragments(card) + tuple(
            keyword for keyword in card.keywords if keyword not in interpreter.fragments(card)
        )
        fragment_rows = []
        for index, fragment in enumerate(fragments):
            limitations = tuple(sorted(unsupported.get(fragment, set())))
            key = semantic_key(card.oracle_id, 0, index, fragment)
            row = {
                "semantic_key": key,
                "face_index": 0,
                "fragment_index": index,
                "oracle_fragment": fragment,
                "limitations": list(limitations),
                "static_classification": "unsupported" if limitations else "supported",
                "semantic_coverage": _semantic_coverage(interpreter, card, fragment, limitations),
                "observability": _observability(card.name, fragment, limitations),
            }
            fragment_rows.append(row)
            fragment_members.append((card.oracle_id, key, limitations))
        cards.append(
            {
                "name": name,
                "quantity": quantity,
                "oracle_id": card.oracle_id,
                "fragments": fragment_rows,
            }
        )
    membership = sorted(fragment_members)
    represented_families = sorted(
        {
            fragment["semantic_coverage"]["family"]
            for card in cards
            for fragment in card["fragments"]
            if fragment["semantic_coverage"]["fully_supported"]
        }
    )
    unsupported_families = sorted(
        {
            fragment["semantic_coverage"]["family"]
            for card in cards
            for fragment in card["fragments"]
            if fragment["limitations"]
        }
    )
    return {
        "display_id": spec.display_id,
        "deck_path": spec.relative_path,
        "deck_sha256": hashlib.sha256(raw).hexdigest(),
        "slot_count": sum(quantity for quantity, _name in rows),
        "unique_card_count": len(rows),
        "cards": cards,
        "represented_families": represented_families,
        "unsupported_families": unsupported_families,
        "fragment_membership_digest": stable_digest(membership),
    }


def build_stage_manifest(root: Path) -> dict[str, object]:
    catalog = load_catalog(root)
    specs = {
        spec.display_id: spec for pairing in PAIRINGS for spec in (pairing.first, pairing.second)
    }
    decks = [build_deck_manifest(root, specs[key], catalog) for key in sorted(specs)]
    acceptance_001_specs = (
        DeckSpec("leonardo-p0.1", "decks/leonardo/PROTOTYPE_0.1.txt"),
        DeckSpec("raphael-p0.1", "decks/raphael/PROTOTYPE_0.1.txt"),
    )
    acceptance_001_keys = {
        fragment["semantic_key"]
        for spec in acceptance_001_specs
        for card in build_deck_manifest(root, spec, catalog)["cards"]
        for fragment in card["fragments"]
    }
    for deck in decks:
        keys = {
            fragment["semantic_key"] for card in deck["cards"] for fragment in card["fragments"]
        }
        overlap = sorted(keys & acceptance_001_keys)
        novelty = sorted(keys - acceptance_001_keys)
        deck["acceptance_001_overlap"] = {
            "count": len(overlap),
            "semantic_keys": overlap,
            "digest": stable_digest(overlap),
        }
        deck["acceptance_001_novelty"] = {
            "count": len(novelty),
            "semantic_keys": novelty,
            "digest": stable_digest(novelty),
        }
    games = [
        {
            "game_id": game.game_id,
            "pairing_id": game.pairing_id,
            "seed": game.seed,
            "orientation": game.orientation,
            "seats": [seat.display_id for seat in game.seats],
        }
        for game in stage_games()
    ]
    body = {
        "stage": "acceptance-002",
        "snapshot_sha256": catalog.snapshot_sha256,
        "distinct_game_count": len(games),
        "execution_count_with_duplicates": len(games) * 2,
        "decks": decks,
        "games": games,
    }
    return {**body, "manifest_digest": stable_digest(body)}


def _checked_action(game: Game, operation: Callable[[], object], detail: str) -> object:
    before = game.authoritative_state_fingerprint()
    try:
        result = operation()
    except Exception:
        if game.authoritative_state_fingerprint() != before:
            game.record_conformance_stop("illegal_mutation", before, detail=detail)
        raise
    if result is False and game.authoritative_state_fingerprint() != before:
        game.record_conformance_stop("illegal_mutation", before, detail=detail)
        raise RuntimeError(f"illegal mutation during rejected operation: {detail}")
    return result


def _drain_priority(game: Game, pilot: Pilot) -> None:
    while game.priority_state is not None:
        if game.priority_state.resolution_pending:
            _checked_action(game, game.process_priority_resolution, "priority resolution")
            continue
        options = game.legal_priority_actions(game.priority_state.player_index)
        choice = pilot.choose_priority(game.public_view(), options)
        _checked_action(
            game,
            lambda choice=choice: game.execute_priority_action(choice),
            "priority action",
        )


def _initial_presence(game: Game) -> list[dict[str, object]]:
    records = []
    for owner, player in enumerate(game.players):
        for zone_name in ("library", "hand", "battlefield", "graveyard"):
            for obj in getattr(player, zone_name):
                fragments = game._semantic_fragments(obj.card)
                for index, fragment in enumerate(fragments):
                    records.append(
                        {
                            "initial_object_id": obj.object_id,
                            "object_ids": [obj.object_id],
                            "owner": owner,
                            "card": obj.card.name,
                            "is_token": obj.is_token,
                            "semantic_key": semantic_key(obj.card.oracle_id, 0, index, fragment),
                            "oracle_fragment": fragment,
                            "zone_history": [
                                {
                                    "turn": game.turn,
                                    "phase": game.phase,
                                    "step": game.step.value,
                                    "zone": zone_name,
                                    "object_id": obj.object_id,
                                }
                            ],
                        }
                    )
    return records


def _add_created_token_presence(
    game: Game,
    initial: list[dict[str, object]],
    events: list[dict[str, object]],
) -> None:
    tracked = {str(item["initial_object_id"]) for item in initial}
    for event in events:
        if event.get("event") != "tokens_created":
            continue
        for object_id in event.get("object_ids", []):
            if not isinstance(object_id, str) or object_id in tracked:
                continue
            obj = game._objects.get(object_id)
            if obj is None or not obj.is_token or not isinstance(obj.card, TokenDefinition):
                raise RuntimeError("token creation evidence lacks its authoritative runtime object")
            event_id = event.get("event_id")
            if not isinstance(event_id, str):
                raise RuntimeError("token creation evidence lacks its authoritative event identity")
            definition_identity = _token_definition_identity(obj.card)
            fragments = game._semantic_fragments(obj.card)
            for index, fragment in enumerate(fragments):
                initial.append(
                    {
                        "initial_object_id": object_id,
                        "object_ids": [object_id],
                        "owner": obj.owner,
                        "card": obj.card.name,
                        "is_token": True,
                        "token_definition_identity": definition_identity,
                        "creation_event_id": event_id,
                        "creation_source_id": event.get("source_id"),
                        "semantic_key": _runtime_token_semantic_key(
                            obj.card,
                            object_id=object_id,
                            owner=obj.owner,
                            creation_event_id=event_id,
                            fragment_index=index,
                            fragment=fragment,
                        ),
                        "oracle_fragment": fragment,
                        "zone_history": [
                            {
                                "turn": event["turn"],
                                "phase": event["phase"],
                                "step": event["step"],
                                "zone": "battlefield",
                                "object_id": object_id,
                            }
                        ],
                    }
                )
            tracked.add(object_id)


def _finish_presence(
    initial: list[dict[str, object]], events: list[dict[str, object]]
) -> list[dict[str, object]]:
    by_object: dict[str, list[dict[str, object]]] = {}
    for record in initial:
        by_object.setdefault(str(record["initial_object_id"]), []).append(record)
    for event in events:
        if event.get("event") != "zone_changed":
            continue
        source_id = event.get("source_object_id")
        destination_id = event.get("destination_object_id")
        if not isinstance(source_id, str) or not isinstance(destination_id, str):
            continue
        records = by_object.get(source_id, [])
        for record in records:
            record["object_ids"].append(destination_id)
            record["zone_history"].append(
                {
                    "turn": event["turn"],
                    "phase": event["phase"],
                    "step": event["step"],
                    "zone": event["destination_zone"],
                    "object_id": destination_id,
                }
            )
        if records:
            by_object[destination_id] = records
    return sorted(
        initial,
        key=lambda item: (
            int(item["owner"]),
            str(item["initial_object_id"]),
            str(item["semantic_key"]),
        ),
    )


def run_game(root: Path, spec: GameSpec, pilot: Pilot | None = None) -> dict[str, object]:
    """Run one parameterized game through the same Engine/Interpreter/Pilot boundary as #001."""
    catalog = load_catalog(root)
    paths = tuple(root / seat.relative_path for seat in spec.seats)
    names = {name for path in paths for _quantity, name in _deck_rows(path)}
    facts = load_facts(catalog, names)
    game = Game(
        (load_deck(paths[0], facts), load_deck(paths[1], facts)),
        names=tuple(seat.display_id for seat in spec.seats),
        seed=spec.seed,
    )
    presence = _initial_presence(game)
    chosen_pilot = pilot or AcceptancePilot()
    game.scry_chooser = chosen_pilot.choose_scry
    game.hand_bottom_draw_chooser = chosen_pilot.choose_hand_bottom_draw
    game.discard_draw_chooser = chosen_pilot.choose_discard_draw
    while game.winner is None and game.turn < 120:
        _checked_action(game, game.begin_turn, "begin turn")
        if game.winner is not None:
            break
        active = game.active_player
        for stage in ("land", "activate", "damage", "destroy", "creature"):
            options = game.legal_main_actions(active)
            choice = chosen_pilot.choose_main_action(game.public_view(), options, stage)
            _checked_action(
                game, lambda choice=choice: game.execute_main_action(choice), "main action"
            )
            _drain_priority(game, chosen_pilot)
        _checked_action(game, game.advance_step, "advance to combat")
        _checked_action(game, game.advance_step, "advance to attackers")
        attack = chosen_pilot.choose_attack(game.public_view(), game.legal_attack_options(active))
        _checked_action(
            game,
            lambda attack=attack: game.execute_attack_action(attack),
            "attack action",
        )
        _drain_priority(game, chosen_pilot)
        blocks = chosen_pilot.choose_blocks(
            game.public_view(), game.legal_block_options(attack, 1 - active)
        )
        _checked_action(
            game,
            lambda blocks=blocks: game.execute_block_action(blocks),
            "block action",
        )
        while game.step.value == "declare_blockers":
            options = game.legal_sneak_actions(active)
            choice = chosen_pilot.choose_sneak(game.public_view(), options)
            _checked_action(game, lambda choice=choice: game.execute_sneak_action(choice), "sneak")
            _drain_priority(game, chosen_pilot)
        while game.step.value == "combat_damage":
            _checked_action(game, game.resolve_combat_damage, "combat damage")
        _checked_action(game, game.advance_step, "advance after combat")
        game.check_invariants()
        _checked_action(game, game.end_turn, "end turn")
    if game.winner is None:
        game.log("acceptance_incomplete", reason="turn_limit")
    snapshot = game.snapshot()
    _add_created_token_presence(game, presence, snapshot["events"])
    snapshot["stage002_presence"] = _finish_presence(presence, snapshot["events"])
    return snapshot


def _manifest_index(manifest: dict[str, object]) -> dict[str, dict[str, object]]:
    result = {}
    for deck in manifest["decks"]:
        for card in deck["cards"]:
            for fragment in card["fragments"]:
                prior = result.get(fragment["semantic_key"])
                if prior is not None and prior != fragment:
                    raise ValueError("semantic key has inconsistent static evidence")
                result[fragment["semantic_key"]] = fragment
    return result


def _authoritative_execution_index(
    snapshot: dict[str, object],
) -> dict[tuple[str, str], list[dict[str, str]]]:
    """Index only mature serialized evidence capable of authenticating EXECUTED."""
    result: dict[tuple[str, str], list[dict[str, str]]] = {}

    def add(kind: str, evidence_id: object, source_id: object, fragment: object) -> None:
        if not all(
            isinstance(value, str) and value for value in (evidence_id, source_id, fragment)
        ):
            return
        result.setdefault((kind, str(evidence_id)), []).append(
            {"source_id": str(source_id), "oracle_fragment": str(fragment)}
        )

    for item in snapshot.get("activated_abilities", []):
        if item.get("resolved"):
            add(
                "activated_ability",
                item.get("stack_object_id"),
                item.get("source_id"),
                item.get("oracle_fragment"),
            )
    for item in snapshot.get("food_activations", []):
        if item.get("resolved"):
            add(
                "food_activation",
                item.get("stack_object_id"),
                item.get("source_id"),
                item.get("oracle_fragment"),
            )
    for item in snapshot.get("sneak", []):
        if item.get("resolved_object_id") is not None:
            add(
                "sneak",
                item.get("stack_object_id"),
                item.get("hand_object_id"),
                item.get("oracle_fragment"),
            )
    for collection, kind in (
        ("hand_bottom_draw", "hand_bottom_draw"),
        ("discard_draw", "discard_draw"),
    ):
        for item in snapshot.get(collection, []):
            add(kind, item.get("event_id"), item.get("source_id"), item.get("oracle_fragment"))
    for item in snapshot.get("lifelink", []):
        add("lifelink", item.get("event_id"), item.get("source_id"), "Lifelink")
    for step in snapshot.get("combat_damage", {}).get("evidence", []):
        sequence = step.get("sequence")
        for assignment in step.get("assignments", []):
            source_id = assignment.get("source_id")
            if assignment.get("trample"):
                add(
                    "trample",
                    f"combat:{sequence}:{source_id}:trample",
                    source_id,
                    "Trample",
                )
            role = assignment.get("role")
            keyword = (
                "First strike"
                if role == "first_strike"
                else "Double strike"
                if role in {"double_strike_first", "double_strike_second"}
                else None
            )
            if keyword is not None:
                add(
                    "strike_damage_step",
                    f"combat:{sequence}:{source_id}:{keyword}",
                    source_id,
                    keyword,
                )
    for event in snapshot.get("events", []):
        event_kind = event.get("event")
        if event_kind not in {
            "damage_dealt",
            "scry_committed",
            "tokens_created",
            "trigger_resolved",
        }:
            continue
        evidence_id = event.get("event_id") or event.get("stack_object_id")
        add(
            str(event_kind),
            evidence_id,
            event.get("source_id"),
            event.get("oracle_fragment"),
        )
    return result


def reconcile_snapshot(
    spec: GameSpec, snapshot: dict[str, object], manifest: dict[str, object]
) -> dict[str, object]:
    """Reconcile one immutable game snapshot without inventing runtime reach."""
    index = _manifest_index(manifest)
    conformance = snapshot["conformance"]
    occurrences = conformance["semantic_occurrences"]
    witnesses = conformance["opportunity_witnesses"]
    executed = conformance["executed_references"]
    witness_occurrences = {item["occurrence_id"] for item in witnesses}
    stops = list(conformance["stop_records"])
    presence = snapshot.get("stage002_presence")
    if not isinstance(presence, list):
        stops.append({"kind": "silent_approximation", "detail": ["presence_evidence_missing"]})
        presence = []
    runtime_dynamic_index = {
        item["semantic_key"]: {
            "semantic_key": item["semantic_key"],
            "oracle_fragment": item["oracle_fragment"],
            "origin": "runtime_token",
        }
        for item in presence
        if item.get("is_token") is True
    }
    combined_index = {**runtime_dynamic_index, **index}
    execution_index = _authoritative_execution_index(snapshot)
    unknown_keys = sorted(
        {
            item["semantic_key"]
            for item in [*occurrences, *executed]
            if item["semantic_key"] not in combined_index
        }
    )
    if unknown_keys:
        stops.append({"kind": "silent_approximation", "detail": unknown_keys})
    unknown_presence = sorted(
        {
            item["semantic_key"]
            for item in presence
            if item.get("semantic_key") not in combined_index
        }
    )
    if unknown_presence:
        stops.append({"kind": "silent_approximation", "detail": unknown_presence})
    lineage_by_object: dict[str, frozenset[str]] = {}
    for item in presence:
        lineage = frozenset(str(value) for value in item["object_ids"])
        for object_id in lineage:
            prior = lineage_by_object.get(object_id)
            if prior is not None and prior != lineage:
                stops.append(
                    {"kind": "illegal_mutation", "detail": [f"overlapping_lineage:{object_id}"]}
                )
            lineage_by_object[object_id] = lineage

    def same_lineage(first: str, second: str) -> bool:
        return first == second or second in lineage_by_object.get(first, frozenset())

    def execution_is_authenticated(reference: dict[str, object]) -> bool:
        return (
            reference.get("semantic_key") in combined_index
            and isinstance(reference.get("oracle_fragment"), str)
            and combined_index.get(reference.get("semantic_key"), {}).get("oracle_fragment")
            == reference.get("oracle_fragment")
            and any(
                record["source_id"] == reference.get("source_id")
                and record["oracle_fragment"] == reference.get("oracle_fragment")
                for record in execution_index.get(
                    (str(reference.get("evidence_kind")), str(reference.get("evidence_id"))), []
                )
            )
            and any(
                reference.get("semantic_key") == item.get("semantic_key")
                and str(reference.get("source_id")) in item.get("object_ids", [])
                for item in presence
            )
        )

    authenticated_executed = [
        reference for reference in executed if execution_is_authenticated(reference)
    ]

    def occurrence_executed(item: dict[str, object]) -> bool:
        return any(
            reference["semantic_key"] == item["semantic_key"]
            and same_lineage(str(item["object_id"]), str(reference["source_id"]))
            for reference in authenticated_executed
        )

    invalid_executed = sorted(
        str(reference.get("evidence_id"))
        for reference in executed
        if not execution_is_authenticated(reference)
    )
    if invalid_executed:
        stops.append({"kind": "silent_approximation", "detail": invalid_executed})

    witnessed_context_ids = {
        item["cause_id"] for item in witnesses if item["cause_kind"] == "authoritative_context"
    }
    orphan_contexts = sorted(
        item["context_id"]
        for item in conformance["opportunity_contexts"]
        if item["context_id"] not in witnessed_context_ids
    )
    if orphan_contexts:
        stops.append({"kind": "unclassified_reach", "detail": orphan_contexts})
    rows = []
    for item in occurrences:
        classification = (
            "executed"
            if occurrence_executed(item)
            else "reached_unsupported"
            if item["occurrence_id"] in witness_occurrences
            else "present_unreached"
        )
        rows.append(
            {
                "occurrence_id": item["occurrence_id"],
                "semantic_key": item["semantic_key"],
                "object_id": item["object_id"],
                "classification": classification,
                "limitations": item["limitations"],
            }
        )
    present_rows = []
    for item in presence:
        lineage = frozenset(str(value) for value in item["object_ids"])
        item_executed = any(
            reference["semantic_key"] == item["semantic_key"]
            and str(reference["source_id"]) in lineage
            for reference in authenticated_executed
        )
        item_reached = any(
            occurrence["semantic_key"] == item["semantic_key"]
            and str(occurrence["object_id"]) in lineage
            and occurrence["occurrence_id"] in witness_occurrences
            for occurrence in occurrences
        )
        classification = (
            "executed"
            if item_executed
            else "reached_unsupported"
            if item_reached
            else "present_unreached"
        )
        present_rows.append({**item, "classification": classification})
    body = {
        "game_id": spec.game_id,
        "seed": spec.seed,
        "orientation": spec.orientation,
        "seats": [seat.display_id for seat in spec.seats],
        "winner": snapshot["winner"],
        "turn": snapshot["turn"],
        "rng_state_digest": snapshot["rng"]["state_digest"],
        "occurrences": sorted(rows, key=lambda item: item["occurrence_id"]),
        "presence": present_rows,
        "classification_sets": {
            classification: sorted(
                {
                    item["semantic_key"]
                    for item in present_rows
                    if item["classification"] == classification
                }
            )
            for classification in ("executed", "reached_unsupported", "present_unreached")
        },
        "executed_references": executed,
        "authenticated_executed_references": authenticated_executed,
        "opportunity_witnesses": witnesses,
        "authoritative_evidence": {
            key: snapshot.get(key)
            for key in (
                "rng",
                "stack",
                "priority",
                "pending_triggers",
                "scry",
                "combat_damage",
                "lifelink",
                "hand_bottom_draw",
                "discard_draw",
                "activated_abilities",
                "food_activations",
                "sneak",
                "players",
                "events",
            )
        },
        "stop_records": stops,
        "invariant_violations": [
            item for item in snapshot["events"] if item.get("event") == "invariant_violation"
        ],
        "transaction_counts": dict(
            sorted(Counter(item["evidence_kind"] for item in authenticated_executed).items())
        ),
        "engine_boundary_counts": dict(
            sorted(
                Counter(
                    item.get("event", "")
                    for item in snapshot["events"]
                    if item.get("event")
                    in {
                        "priority_granted",
                        "priority_passed",
                        "stack_resolution_permitted",
                        "trigger_stacked",
                        "trigger_resolved",
                        "block_restriction_rejected",
                        "zone_changed",
                    }
                ).items()
            )
        ),
    }
    return {**body, "report_digest": stable_digest(body)}


Runner = Callable[[Path, GameSpec, Pilot | None], dict[str, object]]


def _coverage_summary(reports: list[dict[str, object]]) -> dict[str, object]:
    classes = ("executed", "reached_unsupported", "present_unreached")

    def summarize(items: list[dict[str, object]]) -> dict[str, object]:
        result = {}
        for classification in classes:
            sets = [set(item["classification_sets"][classification]) for item in items]
            result[classification] = {
                "union": sorted(set().union(*sets) if sets else set()),
                "intersection": sorted(set.intersection(*sets) if sets else set()),
            }
        return result

    dimensions: dict[str, dict[str, list[dict[str, object]]]] = {
        "pairing": {},
        "orientation": {},
        "deck": {},
    }
    for report in reports:
        dimensions["pairing"].setdefault(str(report["pairing_id"]), []).append(report)
        dimensions["orientation"].setdefault(str(report["orientation"]), []).append(report)
        for deck in report["seats"]:
            dimensions["deck"].setdefault(str(deck), []).append(report)
    return {
        "all_games": summarize(reports),
        **{
            dimension: {key: summarize(items) for key, items in sorted(groups.items())}
            for dimension, groups in dimensions.items()
        },
    }


def execute_stage(
    root: Path,
    *,
    runner: Runner = run_game,
    games: Iterable[GameSpec] | None = None,
) -> dict[str, object]:
    """Execute each authorized distinct game twice and fail closed on any gate violation."""
    manifest = build_stage_manifest(root)
    reports = []
    for spec in tuple(games) if games is not None else stage_games():
        first = runner(root, spec, None)
        second = runner(root, spec, None)
        first_bytes = canonical_json(first)
        second_bytes = canonical_json(second)
        if first_bytes != second_bytes:
            raise RuntimeError(f"nondeterministic duplicate: {spec.game_id}")
        report = reconcile_snapshot(spec, first, manifest)
        if report["invariant_violations"]:
            raise RuntimeError(f"invariant violation: {spec.game_id}")
        if report["stop_records"]:
            kinds = sorted({item["kind"] for item in report["stop_records"]})
            raise RuntimeError(f"conformance stop {kinds}: {spec.game_id}")
        reports.append(
            {
                **report,
                "pairing_id": spec.pairing_id,
                "duplicate_sha256": hashlib.sha256(first_bytes.encode()).hexdigest(),
            }
        )
    aggregate_body = {
        "stage": "acceptance-002",
        "manifest_digest": manifest["manifest_digest"],
        "distinct_game_count": len(reports),
        "execution_count": len(reports) * 2,
        "games": reports,
        "coverage": _coverage_summary(reports),
    }
    return {
        "manifest": manifest,
        "aggregate": {**aggregate_body, "aggregate_digest": stable_digest(aggregate_body)},
    }


def plan(root: Path) -> dict[str, object]:
    """Return the deterministic frozen plan without running a Stage #002 match."""
    return {"authorized": False, "manifest": build_stage_manifest(root)}
