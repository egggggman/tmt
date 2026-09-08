"""Bounded self-ETB Food-card search transaction; no general tutor grammar."""

import json
from copy import deepcopy
from dataclasses import dataclass

from tmnt_design_studio.card_interpreter07 import CardInterpreter


@dataclass(frozen=True)
class FoodSearchOption:
    search: bool
    card_id: str | None = None


@dataclass(frozen=True)
class FoodSearchView:
    controller: int
    cards: tuple[tuple[str, str], ...]


class FoodSearchMixin:
    @staticmethod
    def _is_food_card(obj):
        # Food is a subtype, not a name or a synonym for artifact.
        return (
            not obj.is_token
            and "Food" in obj.card.type_line.split("\u2014", 1)[-1].split()
            and "\u2014" in obj.card.type_line
        )

    def _choose_food_search(self, ability):
        player = self.players[ability.controller]
        library = tuple(player.library)
        if any(
            not self.is_authoritative(obj, "library") or obj.owner != ability.controller
            for obj in library
        ):
            raise ValueError("Food search library identity is invalid")
        candidates = tuple(obj for obj in library if self._is_food_card(obj))
        options = tuple(FoodSearchOption(True, obj.object_id) for obj in candidates) + (
            FoodSearchOption(False),
            FoodSearchOption(True),
        )
        view = FoodSearchView(
            ability.controller, tuple((obj.object_id, obj.card.name) for obj in candidates)
        )
        registry_object = self._objects
        registry = dict(registry_object)
        player_states = [(p, dict(vars(p))) for p in self.players]
        zones = [(zone, tuple(zone)) for zone in self._all_zone_lists()]
        memo = {id(obj): obj for obj in registry.values()}
        memo.update({id(obj.card): obj.card for obj in registry.values() if hasattr(obj, "card")})
        memo.update(
            {
                id(obj.source_card): obj.source_card
                for obj in registry.values()
                if hasattr(obj, "source_card")
            }
        )
        memo.update({id(event): event for event in self._rules_events.values()})
        states = [(obj, deepcopy(vars(obj), memo)) for obj in registry.values()]
        events = deepcopy(self.events)
        rng_state, rng_records = self.rng.export_state(), list(self.rng.records)
        next_id = self._next_object_number
        self._food_search_choice_active = True
        try:
            choice = self.food_search_chooser(view, options)
            if not isinstance(choice, FoodSearchOption) or choice not in options:
                raise ValueError("Food search chooser must return a listed option")
            if (
                self._objects is not registry_object
                or set(self._objects) != set(registry)
                or any(
                    vars(p) != state
                    or any(
                        isinstance(value, list) and vars(p).get(key) is not value
                        for key, value in state.items()
                    )
                    for p, state in player_states
                )
                or any(a is not b for a, (b, _) in zip(self._all_zone_lists(), zones, strict=True))
                or any(self._objects[key] is not obj for key, obj in registry.items())
                or any(
                    len(zone) != len(before)
                    or any(a is not b for a, b in zip(zone, before, strict=True))
                    for zone, before in zones
                )
                or any(
                    vars(obj) != state or ("card" in state and obj.card is not state["card"])
                    for obj, state in states
                )
                or self.events != events
                or self.rng.export_state() != rng_state
                or self.rng.records != rng_records
                or self._next_object_number != next_id
            ):
                raise ValueError("Food search chooser mutated authoritative state")
            self._validate_etb_food_search_trigger(ability)
        except Exception:
            self._objects = registry_object
            for p, state in player_states:
                vars(p).clear()
                vars(p).update(state)
            self._objects.clear()
            self._objects.update(registry)
            for zone, before in zones:
                zone[:] = before
            for obj, state in states:
                vars(obj).clear()
                vars(obj).update(state)
            self.events[:] = events
            self.rng.restore_state(rng_state)
            self.rng.records[:] = rng_records
            self._next_object_number = next_id
            raise
        finally:
            self._food_search_choice_active = False
        selected = next((obj for obj in candidates if obj.object_id == choice.card_id), None)
        return choice, selected, candidates

    def _resolve_etb_food_search(self, ability):
        self._validate_etb_food_search_trigger(ability)
        if ability.zone != "former":
            raise ValueError("ETB Food search requires Priority resolution")
        choice, selected, candidates = self._choose_food_search(ability)
        self._food_search_consumed.add(ability.trigger_id)
        player = self.players[ability.controller]
        start = len(self.events)
        before_library = [obj.object_id for obj in player.library]
        before_hand = [obj.object_id for obj in player.hand]
        self.log(
            "food_search_decided",
            stack_object_id=ability.object_id,
            controller=ability.controller,
            search=choice.search,
            selected_library_id=choice.card_id,
            candidates=[
                {"object_id": obj.object_id, "name": obj.card.name, "type_line": obj.card.type_line}
                for obj in candidates
            ],
            library=[
                {
                    "object_id": obj.object_id,
                    "name": obj.card.name,
                    "type_line": obj.card.type_line,
                    "is_token": obj.is_token,
                }
                for obj in player.library
            ],
            pre_hand_ids=before_hand,
        )
        hand_id = None
        if selected is not None:
            self.log(
                "food_card_revealed",
                stack_object_id=ability.object_id,
                controller=ability.controller,
                library_object_id=selected.object_id,
                card=selected.card.name,
                type_line=selected.card.type_line,
            )
            moved = self.move_object(selected, "hand", reason="food_search")
            if (
                not self.is_authoritative(moved, "hand")
                or moved.card is not selected.card
                or moved.owner != ability.controller
            ):
                raise ValueError("Food search hand movement is not authoritative")
            hand_id = moved.object_id
        if choice.search:
            state = self.rng.export_state()
            before = [obj.object_id for obj in player.library]
            domain = f"food_search:{ability.object_id}"
            player.library[:] = self.rng.shuffled(list(player.library), domain=domain)
            record = self.rng.records[-1]
            self.log(
                "food_search_shuffled",
                stack_object_id=ability.object_id,
                domain=domain,
                rng_state_before=state,
                state_before=record.state_before,
                state_after=record.state_after,
                sequence=record.sequence,
                permutation=list(record.result),
                pre_library_ids=before,
                post_library_ids=[obj.object_id for obj in player.library],
            )
        tokens = []
        if hand_id is None:
            program = self.interpreter.token_creation_program("Create a Food token.")
            assert program is not None
            tokens = self.create_tokens(
                ability.controller,
                program,
                source_card=ability.source_card.name,
                source_id=ability.source_id,
                oracle_fragment=ability.oracle_fragment,
            )
            if (
                len(tokens) != 1
                or tokens[0].card is not CardInterpreter.PREDEFINED_TOKENS["food"]
                or not self.is_authoritative(tokens[0], "battlefield")
            ):
                raise ValueError("Food search fallback token is not authoritative")
        self.log(
            "etb_food_search_committed",
            event_id=ability.event.event_id,
            trigger_id=ability.trigger_id,
            stack_object_id=ability.object_id,
            source_id=ability.source_id,
            controller=ability.controller,
            oracle_fragment=ability.oracle_fragment,
            start_event_cursor=start,
            pre_library_ids=before_library,
            pre_hand_ids=before_hand,
            selected_library_id=choice.card_id,
            search=choice.search,
            hand_id=hand_id,
            token_ids=[obj.object_id for obj in tokens],
            post_library_ids=[obj.object_id for obj in player.library],
            post_hand_ids=[obj.object_id for obj in player.hand],
        )

        self._food_search_history.append((start, json.dumps(self.events[start:], sort_keys=True)))

    def food_search_snapshot_evidence(self):
        records = []
        for start, encoded in self._food_search_history:
            events = json.loads(encoded)
            if json.dumps(self.events[start : start + len(events)], sort_keys=True) != encoded:
                raise ValueError("Food search original transaction evidence was altered")
            records.append({"start_event_cursor": start, "events": events})
        return records

    def _validate_etb_food_search_trigger(self, ability) -> None:
        from tmnt_design_studio.engine07 import TriggerEffect

        if not self._priority_resolution_in_progress and (
            self.priority_state is None or not self.priority_state.resolution_pending
        ):
            raise ValueError("ETB Food search requires Priority resolution")
        anchor = self._food_search_anchors.get(ability.object_id)
        if anchor is None:
            raise ValueError("ETB Food search lacks Stack provenance")
        original, trigger, source, card = anchor
        self._authenticate_original_rules_event(ability.event)
        if (
            ability is not original
            or self._objects.get(ability.object_id) is not ability
            or self._triggers.get(ability.trigger_id) is not trigger
            or self._objects.get(trigger.source_id) is not source
            or source.card is not card
            or source.object_id != trigger.source_id
            or source.zone not in {"battlefield", "former"}
            or ability.source_card is not card
            or ability.source_id != trigger.source_id
            or ability.controller != trigger.controller
            or ability.oracle_fragment != trigger.oracle_fragment
            or ability.effect is not TriggerEffect.ETB_FOOD_SEARCH
            or ability.event is not trigger.event
            or self._rules_events.get(trigger.event.event_id) is not trigger.event
            or ability.trigger_id in self._food_search_consumed
            or self.interpreter.etb_food_search_semantic_coverage(card, ability.oracle_fragment)
            is None
        ):
            raise ValueError("ETB Food search trigger provenance is invalid or consumed")

    @staticmethod
    def validate_food_search_snapshot_evidence(snapshot: dict[str, object]) -> None:
        """Reconstruct the bounded ETB transaction from independent event records."""
        from tmnt_design_studio.engine07 import DeterministicRNG

        events = snapshot.get("events", [])
        committed = [
            (i, e) for i, e in enumerate(events) if e.get("event") == "etb_food_search_committed"
        ]
        resolutions = [
            e
            for e in events
            if e.get("event") == "trigger_resolved" and e.get("effect") == "etb_food_search"
        ]
        if len(committed) != len(resolutions):
            raise ValueError("ETB Food search evidence lacks a unique resolution")
        if committed and "food_search_evidence" not in snapshot:
            raise ValueError("ETB Food search evidence does not reconstruct")
        if "food_search_evidence" in snapshot:
            originals = snapshot["food_search_evidence"] or []
            if len(originals) != len(committed):
                raise ValueError("ETB Food search evidence does not reconstruct")
            for original, (cursor, item) in zip(originals, committed, strict=True):
                start = original["start_event_cursor"]
                if start != item["start_event_cursor"] or json.dumps(
                    original["events"], sort_keys=True
                ) != json.dumps(events[start : cursor + 1], sort_keys=True):
                    raise ValueError("ETB Food search evidence does not reconstruct")
        seen = set()
        for cursor, item in committed:
            try:
                stack_id = item["stack_object_id"]
                assert stack_id not in seen
                seen.add(stack_id)
                source_id, event_id = item["source_id"], item["event_id"]
                controller = item["controller"]
                assert controller in (0, 1)
                entry = [
                    (i, e)
                    for i, e in enumerate(events[:cursor])
                    if e.get("event") == "rules_event" and e.get("event_id") == event_id
                ]
                assert len(entry) == 1
                entry_cursor, entry_event = entry[0]
                assert entry_event["rules_event"] == "creature_entered"
                assert entry_event["subject_ids"] == [source_id]
                assert {"object_id": source_id, "controller": controller} in entry_event[
                    "battlefield_authority"
                ]
                pending = [
                    (i, e)
                    for i, e in enumerate(events[:cursor])
                    if e.get("event") == "trigger_pending"
                    and e.get("trigger_id") == item["trigger_id"]
                ]
                stacked = [
                    (i, e)
                    for i, e in enumerate(events[:cursor])
                    if e.get("event") == "trigger_stacked" and e.get("stack_object_id") == stack_id
                ]
                permitted = [
                    (i, e)
                    for i, e in enumerate(events[:cursor])
                    if e.get("event") == "stack_resolution_permitted"
                    and e.get("stack_object_id") == stack_id
                ]
                resolved = [
                    (i, e)
                    for i, e in enumerate(events)
                    if e.get("event") == "trigger_resolved" and e.get("stack_object_id") == stack_id
                ]
                assert len(pending) == len(stacked) == len(permitted) == len(resolved) == 1
                pending_cursor, pending_event = pending[0]
                stacked_cursor, stacked_event = stacked[0]
                permitted_cursor, permission = permitted[0]
                resolved_cursor, resolution = resolved[0]
                assert pending_event["event_id"] == stacked_event["event_id"] == event_id
                assert stacked_event["trigger_id"] == item["trigger_id"]
                assert pending_event["oracle_fragment"] == item["oracle_fragment"]
                assert (
                    pending_event["controller"]
                    == stacked_event["controller"]
                    == entry_event["player"]
                )
                assert resolution["event_id"] == event_id and resolution["source_id"] == source_id
                assert resolution["trigger_id"] == item["trigger_id"]
                assert resolution["oracle_fragment"] == item["oracle_fragment"]
                assert resolution["effect"] == "etb_food_search"
                start = item["start_event_cursor"]
                assert (
                    entry_cursor
                    < pending_cursor
                    < stacked_cursor
                    < permitted_cursor
                    < start
                    <= cursor
                    < resolved_cursor
                )
                passes = [
                    e
                    for e in events[stacked_cursor:permitted_cursor]
                    if e.get("event") == "priority_passed"
                    and e.get("priority_epoch") == permission["priority_epoch"]
                ]
                assert len(passes) >= 2 and passes[-1]["resolution_pending"] is True
                assert {passes[-1]["player_index"], passes[-2]["player_index"]} == {0, 1}
                if "rules_event_evidence" in snapshot:
                    originals = [
                        e for e in snapshot["rules_event_evidence"] if e["event_id"] == event_id
                    ]
                    assert len(originals) == 1
                    original = originals[0]
                    assert (
                        original["kind"] == "creature_entered"
                        and original["player_index"] == controller
                    )
                    for key in (
                        "source_id",
                        "subject_ids",
                        "battlefield_authority",
                        "battlefield_characteristics",
                    ):
                        assert original[key] == entry_event[key]
                steps = events[start:cursor]
                assert item["oracle_fragment"] == CardInterpreter.ETB_FOOD_SEARCH_FRAGMENT
                decision = steps[0]
                assert decision["event"] == "food_search_decided"
                assert (
                    decision["stack_object_id"] == stack_id and decision["controller"] == controller
                )
                assert decision["search"] is item["search"]
                assert decision["selected_library_id"] == item["selected_library_id"]
                library = decision["library"]
                library_ids = [obj["object_id"] for obj in library]
                assert library_ids == item["pre_library_ids"]
                assert len(set(library_ids + item["pre_hand_ids"])) == len(
                    library_ids + item["pre_hand_ids"]
                )
                assert decision["pre_hand_ids"] == item["pre_hand_ids"]
                candidates = [
                    {k: obj[k] for k in ("object_id", "name", "type_line")}
                    for obj in library
                    if not obj["is_token"]
                    and "\u2014" in obj["type_line"]
                    and "Food" in obj["type_line"].split("\u2014", 1)[1].split()
                ]
                assert candidates == decision["candidates"]
                selected, hand = item["selected_library_id"], item["hand_id"]
                reveals = [e for e in steps if e["event"] == "food_card_revealed"]
                moves = [e for e in steps if e["event"] == "zone_changed"]
                creations = [e for e in steps if e["event"] == "tokens_created"]
                shuffles = [e for e in steps if e["event"] == "food_search_shuffled"]
                if selected is not None:
                    assert item["search"] is True
                    candidate = next(obj for obj in candidates if obj["object_id"] == selected)
                    assert hand and hand not in library_ids + item["pre_hand_ids"]
                    assert not item["token_ids"] and not creations
                    assert len(reveals) == len(moves) == 1
                    reveal, move = reveals[0], moves[0]
                    assert (
                        reveal["library_object_id"] == selected
                        and reveal["stack_object_id"] == stack_id
                    )
                    assert (
                        reveal["card"] == candidate["name"]
                        and reveal["type_line"] == candidate["type_line"]
                    )
                    assert reveal["controller"] == controller
                    assert (
                        move["source_object_id"] == selected
                        and move["destination_object_id"] == hand
                    )
                    assert (
                        move["source_zone"] == "library"
                        and move["destination_zone"] == "hand"
                        and move["reason"] == "food_search"
                    )
                    assert steps.index(reveal) < steps.index(move) < steps.index(shuffles[0])
                    assert item["post_hand_ids"] == item["pre_hand_ids"] + [hand]
                else:
                    assert hand is None and not reveals and not moves
                    assert item["post_hand_ids"] == item["pre_hand_ids"]
                    assert len(item["token_ids"]) == len(creations) == 1
                    creation = creations[0]
                    assert creation["object_ids"] == item["token_ids"]
                    assert (
                        creation["source_id"] == source_id
                        and creation["oracle_fragment"] == item["oracle_fragment"]
                    )
                    token_events = [
                        e
                        for e in steps
                        if e["event"] == "rules_event" and e.get("event_id") == creation["event_id"]
                    ]
                    assert len(token_events) == 1
                    token_event = token_events[0]
                    if "rules_event_evidence" in snapshot:
                        originals = [
                            e
                            for e in snapshot["rules_event_evidence"]
                            if e["event_id"] == creation["event_id"]
                        ]
                        assert len(originals) == 1 and originals[0]["player_index"] == controller
                        for key in (
                            "source_id",
                            "subject_ids",
                            "battlefield_authority",
                            "battlefield_characteristics",
                        ):
                            assert originals[0][key] == token_event[key]
                    assert (
                        token_event["rules_event"] == "tokens_created"
                        and token_event["subject_ids"] == item["token_ids"]
                    )
                    assert {
                        "object_id": item["token_ids"][0],
                        "controller": controller,
                    } in token_event["battlefield_authority"]
                    assert {
                        "object_id": item["token_ids"][0],
                        "controller": controller,
                        "type_line": CardInterpreter.PREDEFINED_TOKENS["food"].type_line,
                    } in token_event["battlefield_characteristics"]
                    if shuffles:
                        assert steps.index(shuffles[0]) < steps.index(creation)
                remaining = [obj for obj in library_ids if obj != selected]
                if item["search"]:
                    assert len(shuffles) == 1
                    shuffle = shuffles[0]
                    assert shuffle["stack_object_id"] == stack_id
                    assert shuffle["domain"] == f"food_search:{stack_id}"
                    rng = DeterministicRNG(0)
                    rng.restore_state(shuffle["rng_state_before"])
                    assert rng.state_digest == shuffle["state_before"]
                    after = rng.shuffled(remaining, domain=shuffle["domain"])
                    assert shuffle["permutation"] == list(rng.records[-1].result)
                    assert shuffle["state_after"] == rng.state_digest
                    assert shuffle["pre_library_ids"] == remaining
                    assert shuffle["post_library_ids"] == item["post_library_ids"] == after
                    if "rng" in snapshot:
                        records = snapshot["rng"]["records"]
                        record = next(r for r in records if r["sequence"] == shuffle["sequence"])
                        assert (
                            record["domain"] == shuffle["domain"]
                            and record["operation"] == "shuffle"
                        )
                        assert (
                            record["state_before"] == shuffle["state_before"]
                            and record["state_after"] == shuffle["state_after"]
                        )
                        assert record["result"] == shuffle["permutation"]
                else:
                    assert item["search"] is False and selected is None and not shuffles
                    assert remaining == item["post_library_ids"]
            except (
                AssertionError,
                KeyError,
                TypeError,
                ValueError,
                IndexError,
                StopIteration,
            ) as error:
                raise ValueError("ETB Food search evidence does not reconstruct") from error
