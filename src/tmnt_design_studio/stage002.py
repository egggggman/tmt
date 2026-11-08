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
from tmnt_design_studio.conformance07 import opportunity_context_key, semantic_key
from tmnt_design_studio.engine07 import ActionKind, Game, TurnStep, load_deck, load_facts
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


def _runtime_token_key_from_presence(record: dict[str, object]) -> str | None:
    """Reconstruct one runtime-token key solely from its immutable presence facts."""
    definition_identity = record.get("token_definition_identity")
    object_id = record.get("initial_object_id")
    owner = record.get("owner")
    event_id = record.get("creation_event_id")
    fragment_index = record.get("fragment_index")
    fragment = record.get("oracle_fragment")
    if not (
        isinstance(definition_identity, str)
        and definition_identity.startswith("token-definition:")
        and isinstance(object_id, str)
        and isinstance(owner, int)
        and isinstance(event_id, str)
        and isinstance(fragment_index, int)
        and fragment_index >= 0
        and isinstance(fragment, str)
    ):
        return None
    runtime_identity = "runtime-token:" + stable_digest(
        {
            "token_definition_identity": definition_identity,
            "object_id": object_id,
            "owner": owner,
            "creation_event_id": event_id,
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
        ("aura_suppression", interpreter.aura_semantic_coverage(card, fragment)),
        (
            "static_team_modifier",
            interpreter.static_team_modifier_semantic_coverage(card, fragment),
        ),
        (
            "etb_artifact_draw",
            interpreter.etb_artifact_draw_semantic_coverage(card, fragment),
        ),
        (
            "etb_drain_gain_scry",
            interpreter.etb_drain_gain_scry_semantic_coverage(card, fragment),
        ),
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
        ("draw_cards", interpreter.draw_cards_semantic_coverage(card, fragment)),
        (
            "april_end_step_draw",
            interpreter.april_end_step_draw_semantic_coverage(card, fragment),
        ),
    )
    for family, interpreted in candidates:
        if interpreted is None:
            continue
        coverage = getattr(interpreted, "coverage", interpreted)
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


def _drain_priority(game: Game, pilot: Pilot, *, follow_on_empty_window: bool = False) -> None:
    while not game.terminal and game.priority_state is not None:
        if game.priority_state.resolution_pending:
            resolving_stack = bool(game.stack)
            resolving_step = game.step
            _checked_action(game, game.process_priority_resolution, "priority resolution")
            if (
                follow_on_empty_window
                and resolving_stack
                and not game.terminal
                and game.step is resolving_step
                and game.priority_state is None
                and not game.stack
            ):
                game._begin_priority_window(allow_empty=True)
            continue
        options = game.legal_priority_actions(game.priority_state.player_index)
        choice = pilot.choose_priority(
            game.priority_view(game.priority_state.player_index), options
        )
        _checked_action(
            game,
            lambda choice=choice: game.execute_priority_action(choice),
            "priority action",
        )


def _drain_ordinary_step_priority(game: Game, pilot: Pilot) -> None:
    """Offer an ordinary priority opportunity before leaving the current step."""
    if game.terminal:
        return
    if game.priority_state is None:
        game._begin_priority_window(allow_empty=True)
    _drain_priority(game, pilot, follow_on_empty_window=True)


def _begin_turn_with_priority(game: Game, pilot: Pilot) -> None:
    """Expose the existing beginning steps and service upkeep Stack/Priority."""
    from tmnt_design_studio.engine07 import TurnStep

    if game.step not in {TurnStep.SETUP, TurnStep.CLEANUP}:
        raise ValueError("begin turn requires setup or cleanup")
    while not game.terminal and game.step is not TurnStep.PRECOMBAT_MAIN:
        _checked_action(game, game.advance_step, "beginning step")
        if game.step not in {TurnStep.UNTAP, TurnStep.CLEANUP}:
            _drain_ordinary_step_priority(game, pilot)
        else:
            _drain_priority(game, pilot)


def _run_main_action_stages(game: Game, pilot: Pilot) -> None:
    """Apply the established land/activation/spell policy in either main phase."""
    active = game.active_player
    for stage in ("land", "activate", "damage", "destroy", "creature"):
        attempts = 0
        while not game.terminal:
            options = game.legal_main_actions(active)
            choice = pilot.choose_main_action(game.pilot_view(active), options, stage)
            _checked_action(
                game, lambda choice=choice: game.execute_main_action(choice), "main action"
            )
            _drain_priority(game, pilot)
            attempts += 1
            # Immediate mana abilities do not open priority. Re-enumerate once per
            # reported useful follow-up, with a hard cap against faulty pilot loops.
            if stage != "activate" or not choice.mana_followups or attempts >= 3:
                break


def _wire_damage_target_chooser(game: Game, pilot: Pilot) -> None:
    """Connect the engine's offered-target callback to this pilot's public view."""
    chooser = getattr(pilot, "choose_damage_target", None)
    if callable(chooser):
        game.damage_target_chooser = lambda controller, _source_id, offered: chooser(
            game.pilot_view(controller), offered
        )


def _resolve_combat_damage_steps(game: Game, pilot: Pilot) -> None:
    """Resolve each distinct damage step around existing Stack/Priority work."""
    while not game.terminal and game.step.value == "combat_damage":
        _checked_action(game, game.resolve_combat_damage, "combat damage")
        if not game.terminal:
            _drain_priority(game, pilot)


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
                        "creation_controller": obj.controller,
                        "card": obj.card.name,
                        "is_token": True,
                        "token_definition_identity": definition_identity,
                        "creation_event_id": event_id,
                        "creation_source_id": event.get("source_id"),
                        "fragment_index": index,
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
    _wire_damage_target_chooser(game, chosen_pilot)
    while not game.terminal and game.turn < 120:
        if game.turn >= 119:
            raise RuntimeError("attempted to begin turn 120")
        _begin_turn_with_priority(game, chosen_pilot)
        if game.terminal:
            break
        _run_main_action_stages(game, chosen_pilot)
        if game.terminal:
            break
        active = game.active_player
        _checked_action(game, game.advance_step, "advance to combat")
        _drain_ordinary_step_priority(game, chosen_pilot)
        if game.terminal:
            break
        _checked_action(game, game.advance_step, "advance to attackers")
        attack = chosen_pilot.choose_attack(
            game.pilot_view(active), game.legal_attack_options(active)
        )
        _checked_action(
            game,
            lambda attack=attack: game.execute_attack_action(attack, defer_step_transition=True),
            "attack action",
        )
        _drain_ordinary_step_priority(game, chosen_pilot)
        if game.terminal:
            break
        if game.step is not TurnStep.DECLARE_ATTACKERS or not game._attackers_declared:
            raise RuntimeError("attack declaration priority did not complete")
        _checked_action(game, game.advance_step, "advance after attacker priority")
        blocks = chosen_pilot.choose_blocks(
            game.pilot_view(1 - active), game.legal_block_options(attack, 1 - active)
        )
        _checked_action(
            game,
            lambda blocks=blocks: game.execute_block_action(blocks, defer_step_transition=True),
            "block action",
        )
        while not game.terminal and game.step is TurnStep.DECLARE_BLOCKERS:
            options = game.legal_sneak_actions(active)
            if not options:
                raise RuntimeError("Sneak decision surface unavailable")
            choice = chosen_pilot.choose_sneak(game.pilot_view(active), options)
            _checked_action(
                game,
                lambda choice=choice: game.execute_sneak_action(choice, defer_step_transition=True),
                "sneak",
            )
            _drain_priority(game, chosen_pilot)
            if choice.kind is ActionKind.PASS:
                break
        if game.terminal:
            break
        _drain_ordinary_step_priority(game, chosen_pilot)
        if game.terminal:
            break
        if game.step is not TurnStep.DECLARE_BLOCKERS or not game._blockers_declared:
            raise RuntimeError("block declaration priority did not complete")
        _checked_action(game, game.advance_step, "advance after blocker priority")
        _resolve_combat_damage_steps(game, chosen_pilot)
        if game.terminal:
            break
        if game.step is not TurnStep.END_OF_COMBAT:
            raise RuntimeError("expected end-of-combat step after damage")
        _drain_ordinary_step_priority(game, chosen_pilot)
        if game.terminal:
            break
        _checked_action(game, game.advance_step, "advance after combat")
        game.check_invariants()
        # Apply the same bounded action stages during the normal second main phase.
        _run_main_action_stages(game, chosen_pilot)
        if game.terminal:
            break
        _drain_ordinary_step_priority(game, chosen_pilot)
        if game.terminal:
            break
        _checked_action(game, game.advance_step, "advance to end step")
        _drain_ordinary_step_priority(game, chosen_pilot)
        if game.terminal:
            break
        _checked_action(game, game.advance_step, "advance to cleanup")
    if not game.terminal:
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
    Game.validate_stun_snapshot_evidence(snapshot)
    Game.validate_mill_three_snapshot_evidence(snapshot)
    Game.validate_krang_refill_snapshot_evidence(snapshot)
    Game.validate_jury_rig_snapshot_evidence(snapshot)
    Game.validate_vigilante_snapshot_evidence(snapshot)
    Game.validate_food_search_snapshot_evidence(snapshot)
    Game.validate_draw_discard_snapshot_evidence(snapshot)
    Game.validate_ltb_mutagen_snapshot_evidence(snapshot)
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
    for item in snapshot.get("etb_drain_gain_scry", []):
        add(
            "etb_drain_gain_scry",
            item.get("stack_object_id"),
            item.get("source_id"),
            item.get("oracle_fragment"),
        )
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
        if CardInterpreter.is_krang_refill_fragment(event.get("oracle_fragment")):
            if event.get("event") == "krang_refill_committed" and event["requested"] > 0:
                add(
                    "krang_refill",
                    event["stack_object_id"],
                    event["source_id"],
                    event["oracle_fragment"],
                )
            continue
        if event.get("oracle_fragment") == CardInterpreter.MILL_THREE_FRAGMENT:
            if event.get("event") == "mill_three_committed":
                add(
                    "mill_three",
                    event.get("stack_object_id"),
                    event.get("source_id"),
                    event.get("oracle_fragment"),
                )
            continue
        if event.get("oracle_fragment") == CardInterpreter.JURY_RIG_FRAGMENT:
            if event.get("event") == "jury_rig_committed":
                add(
                    "jury_rig",
                    event.get("stack_object_id"),
                    event.get("source_id"),
                    event.get("oracle_fragment"),
                )
            continue
        if event.get("effect") == "etb_vigilante":
            continue
        event_kind = event.get("event")
        if event_kind not in {
            "damage_dealt",
            "scry_committed",
            "tokens_created",
            "trigger_resolved",
            "spell_resolved",
            "spell_resolved_no_effect",
            "aura_resolved",
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


def _runtime_token_presence_is_authoritative(
    record: dict[str, object], snapshot: dict[str, object]
) -> bool:
    """Authenticate token presence from its immutable creation event and key."""
    if record.get("is_token") is not True:
        return False
    if record.get("semantic_key") != _runtime_token_key_from_presence(record):
        return False
    owner = record.get("owner")
    controller = record.get("creation_controller")
    players = snapshot.get("players", [])
    if (
        not isinstance(owner, int)
        or not 0 <= owner < len(players)
        or not isinstance(controller, int)
        or not 0 <= controller < len(players)
    ):
        return False
    player = players[owner]
    controlling_player = players[controller]
    if (
        not isinstance(player, dict)
        or not isinstance(player.get("name"), str)
        or not isinstance(controlling_player, dict)
        or not isinstance(controlling_player.get("name"), str)
    ):
        return False
    matching_events = [
        event
        for event in snapshot.get("events", [])
        if event.get("event") == "tokens_created"
        and event.get("event_id") == record.get("creation_event_id")
        and record.get("initial_object_id") in event.get("object_ids", [])
        and event.get("creator") == player["name"]
        and event.get("controller") == controlling_player["name"]
        and event.get("source_id") == record.get("creation_source_id")
    ]
    return len(matching_events) == 1


def _normalize_token_execution_reference(
    reference: dict[str, object],
    presence: list[dict[str, object]],
    snapshot: dict[str, object],
) -> dict[str, object]:
    """Bridge an authenticated mature token reference to its runtime presence key."""
    candidates = []
    for record in presence:
        fragment = record.get("oracle_fragment")
        fragment_index = record.get("fragment_index")
        if not (
            _runtime_token_presence_is_authoritative(record, snapshot)
            and isinstance(fragment, str)
            and isinstance(fragment_index, int)
            and reference.get("source_id") in record.get("object_ids", [])
            and reference.get("oracle_fragment") == fragment
            and reference.get("semantic_key") == semantic_key("", 0, fragment_index, fragment)
        ):
            continue
        candidates.append(record)
    if len(candidates) != 1:
        return reference
    return {**reference, "semantic_key": candidates[0]["semantic_key"]}


def _context_evidence_stops(
    contexts: list[dict[str, object]], witnesses: list[dict[str, object]]
) -> list[dict[str, object]]:
    """Fail closed unless every context witness resolves to reconstructive evidence."""
    stops: list[dict[str, object]] = []
    context_ids = [item.get("context_id") for item in contexts]
    duplicate_ids = sorted(
        str(context_id) for context_id, count in Counter(context_ids).items() if count != 1
    )
    if duplicate_ids:
        stops.append({"kind": "silent_approximation", "detail": duplicate_ids})
    contexts_by_id = {
        str(item["context_id"]): item
        for item in contexts
        if isinstance(item.get("context_id"), str) and context_ids.count(item["context_id"]) == 1
    }
    malformed = []
    for context_id, context in contexts_by_id.items():
        facts = context.get("facts")
        try:
            reconstructed = opportunity_context_key(
                context["context_id"],
                context["context_kind"],
                context["turn"],
                context["phase"],
                context["step"],
                context["active_player"],
                context["controller"],
                context["source_id"],
                tuple(context["subject_ids"]),
                tuple(context["subject_zones"]),
                tuple(facts.items()) if isinstance(facts, dict) else (),
                context.get("event_id"),
                context.get("stack_object_id"),
                context["state_fingerprint"],
            )
        except (KeyError, TypeError):
            reconstructed = None
        if (
            reconstructed != context.get("context_key")
            or not isinstance(context.get("state_fingerprint"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", str(context.get("state_fingerprint")))
            or not isinstance(facts, dict)
            or len(context.get("subject_ids", [])) != len(context.get("subject_zones", []))
        ):
            malformed.append(context_id)
    if malformed:
        stops.append({"kind": "silent_approximation", "detail": sorted(malformed)})
    mismatched = []
    for witness in witnesses:
        if witness.get("cause_kind") != "authoritative_context":
            continue
        context = contexts_by_id.get(str(witness.get("cause_id")))
        if context is None or not (
            context.get("source_id") == witness.get("object_id")
            and context.get("controller") == witness.get("controller")
            and context.get("controller") == witness.get("source_controller")
            and context.get("turn") == witness.get("turn")
            and context.get("phase") == witness.get("phase")
            and context.get("step") == witness.get("step")
            and context.get("subject_ids") == witness.get("cause_subject_ids")
            and context.get("subject_zones") == witness.get("cause_subject_zones")
            and witness.get("cause_event_kind") is None
        ):
            mismatched.append(str(witness.get("witness_id")))
    if mismatched:
        stops.append({"kind": "silent_approximation", "detail": sorted(mismatched)})
    return stops


def _spell_payment_evidence_stops(snapshot: dict[str, object]) -> list[dict[str, object]]:
    """Authenticate typed spell payments against mana lots and actual cast events."""
    stops: list[dict[str, object]] = []
    ledger = snapshot.get("floating_mana_ledger")
    evidence = snapshot.get("spell_payment_evidence")
    rules_events = snapshot.get("rules_event_evidence")
    if (
        not isinstance(ledger, dict)
        or not isinstance(evidence, list)
        or not isinstance(rules_events, list)
    ):
        if isinstance(ledger, dict) and any(
            allocation.get("spending_context") in {"artifact_spell", "nonartifact_spell"}
            for player in ledger.get("players", [])
            for allocation in player.get("payments", [])
        ):
            stops.append(
                {
                    "kind": "mana_payment_provenance",
                    "detail": ["spell_payment_snapshot_evidence_missing"],
                }
            )
        return stops

    production_by_event: dict[str, dict[str, object]] = {}
    payments_by_id: dict[str, list[dict[str, object]]] = {}
    expirations_by_event: dict[str, list[dict[str, object]]] = {}
    consumed_by_event: dict[str, int] = {}
    malformed = False
    ledger_players = ledger.get("players")
    if not isinstance(ledger_players, list):
        ledger_players = []
        malformed = True
    for player in ledger_players:
        if not isinstance(player, dict):
            malformed = True
            continue
        productions = player.get("productions", [])
        payments = player.get("payments", [])
        expirations = player.get("expirations", [])
        if not all(isinstance(items, list) for items in (productions, payments, expirations)):
            malformed = True
            continue
        for production in productions:
            if not isinstance(production, dict):
                malformed = True
                continue
            event_id = production.get("event_id")
            if not isinstance(event_id, str) or not event_id or event_id in production_by_event:
                malformed = True
                continue
            production_by_event[event_id] = production
        for allocation in payments:
            if not isinstance(allocation, dict):
                malformed = True
                continue
            payment_id = allocation.get("payment_id")
            production_event_id = allocation.get("production_event_id")
            quantity = allocation.get("quantity")
            if (
                not isinstance(payment_id, str)
                or not payment_id
                or not isinstance(production_event_id, str)
                or not isinstance(quantity, int)
                or isinstance(quantity, bool)
                or quantity <= 0
            ):
                malformed = True
                continue
            payments_by_id.setdefault(payment_id, []).append(allocation)
            consumed_by_event[production_event_id] = (
                consumed_by_event.get(production_event_id, 0) + quantity
            )
        for expiration in expirations:
            if not isinstance(expiration, dict):
                malformed = True
                continue
            event_id = expiration.get("production_event_id")
            if isinstance(event_id, str):
                expirations_by_event.setdefault(event_id, []).append(expiration)
            else:
                malformed = True

    event_by_id = {
        item.get("event_id"): item
        for item in rules_events
        if isinstance(item, dict) and isinstance(item.get("event_id"), str)
    }
    evidence_by_payment: dict[str, dict[str, object]] = {}
    for item in evidence:
        if not isinstance(item, dict):
            malformed = True
            continue
        payment_id = item.get("payment_id")
        if not isinstance(payment_id, str) or not payment_id or payment_id in evidence_by_payment:
            malformed = True
            continue
        evidence_by_payment[payment_id] = item
        controller = item.get("controller")
        card_object_id = item.get("card_object_id")
        spell_object_id = item.get("spell_object_id")
        event_id = item.get("spell_event_id")
        context = item.get("spending_context")
        cast_event = event_by_id.get(event_id) if isinstance(event_id, str) else None
        card_types = str(item.get("card_type_line", "")).split(" —", 1)[0].split()
        expected_context = "artifact_spell" if "Artifact" in card_types else "nonartifact_spell"
        if (
            payment_id != card_object_id
            or not isinstance(controller, int)
            or isinstance(controller, bool)
            or not isinstance(spell_object_id, str)
            or not isinstance(event_id, str)
            or context != expected_context
            or not isinstance(cast_event, dict)
            or cast_event.get("kind") != "spell_cast"
            or cast_event.get("player_index") != controller
            or cast_event.get("source_id") != spell_object_id
            or cast_event.get("subject_ids") != [spell_object_id]
            or cast_event.get("card_oracle_id") != item.get("card_oracle_id")
            or cast_event.get("card_type_line") != item.get("card_type_line")
        ):
            stops.append(
                {
                    "kind": "mana_payment_provenance",
                    "detail": [f"spell_payment_cast_link_invalid:{payment_id}"],
                }
            )
            continue

        allocations = item.get("mana_allocations")
        if not isinstance(allocations, list):
            malformed = True
            continue
        for allocation in allocations:
            if not isinstance(allocation, dict):
                malformed = True
                continue
            production_event_id = allocation.get("production_event_id")
            production = (
                production_by_event.get(production_event_id)
                if isinstance(production_event_id, str)
                else None
            )
            allowed = None if production is None else production.get("allowed_contexts")
            if allowed is not None and not isinstance(allowed, list):
                malformed = True
                allowed = []
            if (
                allocation.get("payment_id") != payment_id
                or allocation.get("controller") != controller
                or allocation.get("spending_context") != context
                or production is None
                or production.get("controller") != controller
                or not isinstance(production.get("source_id"), str)
                or not production.get("source_id")
                or production.get("color") != allocation.get("color")
                or not isinstance(allocation.get("quantity"), int)
                or isinstance(allocation.get("quantity"), bool)
                or allocation.get("quantity", 0) <= 0
                or (allowed is not None and context not in allowed)
            ):
                stops.append(
                    {
                        "kind": "mana_payment_provenance",
                        "detail": [f"spell_payment_allocation_invalid:{payment_id}"],
                    }
                )
                continue
        ledger_allocations = payments_by_id.get(payment_id, [])

        def canonical(values: list[dict[str, object]]) -> list[tuple[object, ...]]:
            return sorted(
                (
                    (
                        value.get("production_event_id"),
                        value.get("controller"),
                        value.get("color"),
                        value.get("quantity"),
                        value.get("payment_id"),
                        value.get("spending_context"),
                    )
                    for value in values
                ),
                key=repr,
            )

        if not all(isinstance(value, dict) for value in allocations) or canonical(
            [value for value in allocations if isinstance(value, dict)]
        ) != canonical(ledger_allocations):
            stops.append(
                {
                    "kind": "mana_payment_provenance",
                    "detail": [f"spell_payment_ledger_link_invalid:{payment_id}"],
                }
            )

    for payment_id, allocations in payments_by_id.items():
        if (
            any(
                item.get("spending_context") in {"artifact_spell", "nonartifact_spell"}
                for item in allocations
            )
            and payment_id not in evidence_by_payment
        ):
            stops.append(
                {
                    "kind": "mana_payment_provenance",
                    "detail": [f"spell_payment_evidence_missing:{payment_id}"],
                }
            )

    production_events: dict[str, list[dict[str, object]]] = {}
    for item in snapshot.get("events", []):
        if (
            isinstance(item, dict)
            and item.get("event") == "floating_mana_produced"
            and isinstance(item.get("stack_object_id"), str)
        ):
            production_events.setdefault(item["stack_object_id"], []).append(item)
    for event_id, production in production_by_event.items():
        quantity = production.get("quantity")
        remaining = production.get("remaining_quantity")
        production_identity_valid = any(
            item.get("source_id") == production.get("source_id")
            and (
                item.get("player_index") is None
                or item.get("player_index") == production.get("controller")
            )
            and item.get("color") == production.get("color")
            and item.get("quantity") == quantity
            for item in production_events.get(event_id, [])
        )
        if not production_identity_valid:
            stops.append(
                {
                    "kind": "mana_payment_provenance",
                    "detail": [f"mana_production_source_event_invalid:{event_id}"],
                }
            )
        if (
            not isinstance(quantity, int)
            or isinstance(quantity, bool)
            or not isinstance(remaining, int)
            or isinstance(remaining, bool)
        ):
            malformed = True

            continue
        expirations = expirations_by_event.get(event_id, [])
        expired_quantity = sum(
            item.get("quantity", 0) for item in expirations if isinstance(item.get("quantity"), int)
        )
        valid = production.get("valid")
        expired_at = production.get("expired_at")
        expiration_identity_valid = (valid is True and expired_at is None and not expirations) or (
            valid is False
            and isinstance(expired_at, str)
            and len(expirations) == 1
            and expirations[0].get("boundary_id") == expired_at
            and expirations[0].get("controller") == production.get("controller")
            and expirations[0].get("color") == production.get("color")
        )
        if not expiration_identity_valid:
            stops.append(
                {
                    "kind": "mana_payment_provenance",
                    "detail": [f"mana_lot_expiration_invalid:{event_id}"],
                }
            )
        if quantity != consumed_by_event.get(event_id, 0) + remaining + expired_quantity:
            stops.append(
                {
                    "kind": "mana_payment_provenance",
                    "detail": [f"mana_lot_conservation_invalid:{event_id}"],
                }
            )
    if malformed:
        stops.append(
            {
                "kind": "mana_payment_provenance",
                "detail": ["mana_payment_evidence_malformed"],
            }
        )
    return stops


def _activation_payment_evidence_stops(snapshot: dict[str, object]) -> list[dict[str, object]]:
    """Join restricted activation payments to their authenticated ability evidence."""
    ledger = snapshot.get("floating_mana_ledger")
    abilities = snapshot.get("activated_abilities")
    if not isinstance(ledger, dict):
        if isinstance(abilities, list) and any(
            isinstance(item, dict)
            and item.get("spending_context") == "activated_ability"
            and item.get("mana_allocations")
            for item in abilities
        ):
            return [
                {
                    "kind": "mana_payment_provenance",
                    "detail": ["activation_payment_ledger_missing"],
                }
            ]
        return []
    players = ledger.get("players")
    if not isinstance(players, list):
        return [{"kind": "mana_payment_provenance", "detail": ["activation_ledger_invalid"]}]

    has_activation_payment = any(
        isinstance(player, dict)
        and isinstance(player.get("payments"), list)
        and any(
            isinstance(payment, dict) and payment.get("spending_context") == "activated_ability"
            for payment in player["payments"]
        )
        for player in players
    )
    if not isinstance(abilities, list):
        if has_activation_payment:
            return [
                {
                    "kind": "mana_payment_provenance",
                    "detail": ["activation_payment_evidence_missing"],
                }
            ]
        return []

    productions: dict[str, dict[str, object]] = {}
    allocations_by_payment: dict[str, list[dict[str, object]]] = {}
    malformed = False
    for player in players:
        if not isinstance(player, dict):
            malformed = True
            continue
        player_productions = player.get("productions", [])
        player_payments = player.get("payments", [])
        if not isinstance(player_productions, list) or not isinstance(player_payments, list):
            malformed = True
            continue
        for production in player_productions:
            if not isinstance(production, dict):
                malformed = True
                continue
            event_id = production.get("event_id")
            if not isinstance(event_id, str) or not event_id or event_id in productions:
                malformed = True
                continue
            productions[event_id] = production
        for payment in player_payments:
            if not isinstance(payment, dict):
                malformed = True
                continue
            if payment.get("spending_context") != "activated_ability":
                continue
            payment_id = payment.get("payment_id")
            if not isinstance(payment_id, str) or not payment_id:
                malformed = True
                continue
            allocations_by_payment.setdefault(payment_id, []).append(payment)

    evidence_by_payment: dict[str, dict[str, object]] = {}
    for item in abilities:
        if not isinstance(item, dict):
            malformed = True
            continue
        raw_allocations = item.get("mana_allocations", [])
        if not isinstance(raw_allocations, list):
            malformed = True
            continue
        payment_id = item.get("payment_id")
        if payment_id is None:
            if raw_allocations:
                malformed = True
            continue
        if not isinstance(payment_id, str) or not payment_id or payment_id in evidence_by_payment:
            malformed = True
            continue
        evidence_by_payment[payment_id] = item
        if item.get("spending_context") != "activated_ability":
            malformed = True
        if (
            not isinstance(item.get("stack_object_id"), str)
            or not item.get("stack_object_id")
            or not isinstance(item.get("source_id"), str)
            or not item.get("source_id")
            or not isinstance(item.get("oracle_fragment"), str)
            or not item.get("oracle_fragment")
            or not isinstance(item.get("controller"), int)
            or isinstance(item.get("controller"), bool)
            or item.get("controller") not in {0, 1}
        ):
            malformed = True

    cost_events: dict[str, list[dict[str, object]]] = {}
    announced_events: dict[str, list[dict[str, object]]] = {}
    events = snapshot.get("events", [])
    if not isinstance(events, list):
        events = []
        malformed = True
    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get("event") == "activation_cost_paid":
            payment_id = event.get("payment_id")
            if isinstance(payment_id, str):
                cost_events.setdefault(payment_id, []).append(event)
        elif event.get("event") == "activation_announced":
            stack_id = event.get("stack_object_id")
            if isinstance(stack_id, str):
                announced_events.setdefault(stack_id, []).append(event)

    stops: list[dict[str, object]] = []

    def canonical(values: list[dict[str, object]]) -> list[tuple[object, ...]]:
        return sorted(
            (
                (
                    item.get("production_event_id"),
                    item.get("controller"),
                    item.get("color"),
                    item.get("quantity"),
                    item.get("payment_id"),
                    item.get("spending_context"),
                )
                for item in values
            ),
            key=repr,
        )

    for payment_id in sorted(set(allocations_by_payment) | set(evidence_by_payment)):
        ledger_allocations = allocations_by_payment.get(payment_id, [])
        evidence = evidence_by_payment.get(payment_id)
        detail: list[str] = []
        if evidence is None:
            detail.append(f"activation_payment_evidence_missing:{payment_id}")
        else:
            evidence_allocations = evidence.get("mana_allocations")
            if not isinstance(evidence_allocations, list) or not all(
                isinstance(item, dict) for item in evidence_allocations
            ):
                detail.append(f"activation_payment_allocations_malformed:{payment_id}")
                evidence_allocations = []
            if canonical(
                [item for item in evidence_allocations if isinstance(item, dict)]
            ) != canonical(ledger_allocations):
                detail.append(f"activation_payment_ledger_link_invalid:{payment_id}")
            controller = evidence.get("controller")
            cost_matches = cost_events.get(payment_id, [])
            stack_id = evidence.get("stack_object_id")
            announcement_matches = (
                announced_events.get(stack_id, []) if isinstance(stack_id, str) else []
            )
            cost_event = cost_matches[0] if len(cost_matches) == 1 else None
            announcement = announcement_matches[0] if len(announcement_matches) == 1 else None
            if (
                not isinstance(cost_event, dict)
                or cost_event.get("payment_id") != payment_id
                or cost_event.get("player_index") != controller
                or cost_event.get("source_id") != evidence.get("source_id")
                or cost_event.get("stack_object_id") != stack_id
                or cost_event.get("oracle_fragment") != evidence.get("oracle_fragment")
                or cost_event.get("spending_context") != "activated_ability"
                or cost_event.get("mana_source_ids") != evidence.get("mana_source_ids")
            ):
                detail.append(f"activation_payment_cost_event_invalid:{payment_id}")
            if (
                not isinstance(announcement, dict)
                or announcement.get("player_index") != controller
                or announcement.get("source_id") != evidence.get("source_id")
                or announcement.get("oracle_fragment") != evidence.get("oracle_fragment")
            ):
                detail.append(f"activation_announcement_link_invalid:{payment_id}")
            requirement = evidence.get("mana_requirement")
            if (
                not isinstance(requirement, dict)
                or not isinstance(requirement.get("generic"), int)
                or isinstance(requirement.get("generic"), bool)
                or not isinstance(requirement.get("colored"), list)
                or not isinstance(cost_event, dict)
                or cost_event.get("generic") != requirement.get("generic")
                or cost_event.get("colored") != requirement.get("colored")
            ):
                detail.append(f"activation_payment_requirement_invalid:{payment_id}")
            if isinstance(cost_event, dict):
                logged_allocations = cost_event.get("mana_allocations", [])

                def event_allocations(values: list[object]) -> list[tuple[object, ...]]:
                    return sorted(
                        [
                            (
                                item.get("production_event_id"),
                                item.get("color"),
                                item.get("quantity"),
                            )
                            for item in values
                            if isinstance(item, dict)
                        ],
                        key=repr,
                    )

                if (
                    not isinstance(logged_allocations, list)
                    or not all(isinstance(item, dict) for item in logged_allocations)
                    or event_allocations(logged_allocations)
                    != event_allocations(evidence_allocations)
                ):
                    detail.append(f"activation_payment_event_allocations_invalid:{payment_id}")
            for allocation in evidence_allocations:
                if not isinstance(allocation, dict):
                    continue
                production_event_id = allocation.get("production_event_id")
                production = (
                    productions.get(production_event_id)
                    if isinstance(production_event_id, str)
                    else None
                )
                allowed = None if production is None else production.get("allowed_contexts")
                if (
                    allocation.get("payment_id") != payment_id
                    or allocation.get("controller") != controller
                    or allocation.get("spending_context") != "activated_ability"
                    or production is None
                    or production.get("controller") != controller
                    or production.get("color") != allocation.get("color")
                    or not isinstance(allocation.get("quantity"), int)
                    or isinstance(allocation.get("quantity"), bool)
                    or allocation.get("quantity", 0) <= 0
                    or (
                        allowed is not None
                        and (not isinstance(allowed, list) or "activated_ability" not in allowed)
                    )
                ):
                    detail.append(f"activation_payment_allocation_invalid:{payment_id}")
                    break
            if isinstance(requirement, dict):
                mana_sources = evidence.get("mana_source_ids")
                allocated_quantity = sum(
                    item.get("quantity", 0)
                    for item in evidence_allocations
                    if isinstance(item, dict) and isinstance(item.get("quantity"), int)
                )
                if not isinstance(mana_sources, list) or len(
                    mana_sources
                ) + allocated_quantity != requirement.get("generic", -1) + len(
                    requirement.get("colored", [])
                ):
                    detail.append(f"activation_payment_quantity_invalid:{payment_id}")
        if detail:
            stops.append({"kind": "mana_payment_provenance", "detail": detail})
    if malformed:
        stops.append(
            {
                "kind": "mana_payment_provenance",
                "detail": ["activation_payment_evidence_malformed"],
            }
        )
    return stops


def reconcile_snapshot(
    spec: GameSpec, snapshot: dict[str, object], manifest: dict[str, object]
) -> dict[str, object]:
    """Reconcile one immutable game snapshot without inventing runtime reach."""
    index = _manifest_index(manifest)
    conformance = snapshot["conformance"]
    occurrences = conformance["semantic_occurrences"]
    witnesses = conformance["opportunity_witnesses"]
    contexts = conformance["opportunity_contexts"]
    executed = conformance["executed_references"]
    witness_occurrences = {item["occurrence_id"] for item in witnesses}
    stops = list(conformance["stop_records"])
    stops.extend(_context_evidence_stops(contexts, witnesses))
    stops.extend(_spell_payment_evidence_stops(snapshot))
    stops.extend(_activation_payment_evidence_stops(snapshot))
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
    normalized_executed = [
        _normalize_token_execution_reference(reference, presence, snapshot)
        for reference in executed
    ]
    unknown_keys = sorted(
        {
            item["semantic_key"]
            for item in [*occurrences, *normalized_executed]
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
        reference for reference in normalized_executed if execution_is_authenticated(reference)
    ]

    def occurrence_executed(item: dict[str, object]) -> bool:
        return any(
            reference["semantic_key"] == item["semantic_key"]
            and same_lineage(str(item["object_id"]), str(reference["source_id"]))
            for reference in authenticated_executed
        )

    invalid_executed = sorted(
        str(reference.get("evidence_id"))
        for reference in normalized_executed
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
        "terminal": snapshot.get("terminal"),
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
        "opportunity_contexts": contexts,
        "authoritative_evidence": {
            key: snapshot.get(key)
            for key in (
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
                "floating_mana_ledger",
                "spell_payment_evidence",
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
                "terminal",
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
        duplicate_digests = {
            "first": hashlib.sha256(first_bytes.encode()).hexdigest(),
            "second": hashlib.sha256(second_bytes.encode()).hexdigest(),
        }
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
                "duplicate_sha256": duplicate_digests["first"],
                "duplicate_execution_digests": duplicate_digests,
                "duplicate_byte_equivalent": duplicate_digests["first"]
                == duplicate_digests["second"],
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


def validate_stage_result_evidence(result: dict[str, object]) -> None:
    """Independently fail closed on malformed serialized Stage evidence."""
    aggregate = result.get("aggregate")
    if not isinstance(aggregate, dict):
        raise ValueError("Stage result lacks aggregate evidence")
    for game in aggregate.get("games", []):
        Game.validate_stun_snapshot_evidence(game.get("authoritative_evidence", {}))
        Game.validate_mill_three_snapshot_evidence(game.get("authoritative_evidence", {}))
        Game.validate_krang_refill_snapshot_evidence(game.get("authoritative_evidence", {}))
        Game.validate_jury_rig_snapshot_evidence(game.get("authoritative_evidence", {}))
        Game.validate_vigilante_snapshot_evidence(game.get("authoritative_evidence", {}))
        Game.validate_food_search_snapshot_evidence(game.get("authoritative_evidence", {}))
        Game.validate_draw_discard_snapshot_evidence(game.get("authoritative_evidence", {}))
        Game.validate_ltb_mutagen_snapshot_evidence(game.get("authoritative_evidence", {}))
        digests = game.get("duplicate_execution_digests")
        if not (
            isinstance(digests, dict)
            and set(digests) == {"first", "second"}
            and all(
                isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
                for value in digests.values()
            )
            and digests["first"] == digests["second"]
            and game.get("duplicate_sha256") == digests["first"]
            and game.get("duplicate_byte_equivalent") is True
        ):
            raise ValueError("Stage result duplicate evidence is malformed")
        context_stops = _context_evidence_stops(
            game.get("opportunity_contexts", []), game.get("opportunity_witnesses", [])
        )
        if context_stops:
            raise ValueError("Stage result opportunity-context evidence is malformed")
        report_body = {
            key: value
            for key, value in game.items()
            if key
            not in {
                "report_digest",
                "pairing_id",
                "duplicate_sha256",
                "duplicate_execution_digests",
                "duplicate_byte_equivalent",
            }
        }
        if stable_digest(report_body) != game.get("report_digest"):
            raise ValueError("Stage result game digest is malformed")
    aggregate_body = {key: value for key, value in aggregate.items() if key != "aggregate_digest"}
    if stable_digest(aggregate_body) != aggregate.get("aggregate_digest"):
        raise ValueError("Stage result aggregate digest is malformed")


def plan(root: Path) -> dict[str, object]:
    """Return the deterministic frozen plan without running a Stage #002 match."""
    return {"authorized": False, "manifest": build_stage_manifest(root)}
