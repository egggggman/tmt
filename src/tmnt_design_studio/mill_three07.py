"""Exact Paramecia ETB mill-three transaction and authenticated reconstruction."""

import json

from tmnt_design_studio.card_interpreter07 import CardInterpreter


def _encoded(value):
    return json.dumps(value, sort_keys=True)


class MillThreeMixin:
    def _init_mill_three(self):
        self._mill_three_sources = {}
        self._mill_three_anchors = {}
        self._mill_three_consumed = set()
        self._mill_three_history = []
        self._mill_three_pre_states = {}
        self._mill_three_births = {}
        self._mill_three_registry = self._objects
        self._mill_three_rng = self.rng

    def _mill_three_register(self, obj):
        # Immutable birth identity, not a trigger-time library/top-card capture.
        if hasattr(obj, "card") and hasattr(obj, "is_token"):
            descriptor = dict(
                object_id=obj.object_id,
                owner=obj.owner,
                card=obj.card.name,
                type_line=obj.card.type_line,
                oracle_text=obj.card.oracle_text,
                is_token=obj.is_token,
                birth_zone=obj.zone,
            )
            self._mill_three_births[obj.object_id] = (obj, obj.card, _encoded(descriptor))

    def _mill_three_identity(self, obj):
        birth = self._mill_three_births.get(getattr(obj, "object_id", None))
        if birth is None or birth[0] is not obj or birth[1] is not obj.card:
            raise ValueError("Mill-three object/card identity was relinked")
        original = json.loads(birth[2])
        if (
            self._objects.get(obj.object_id) is not obj
            or obj.owner != original["owner"]
            or obj.card.name != original["card"]
            or obj.card.type_line != original["type_line"]
            or obj.card.oracle_text != original["oracle_text"]
            or obj.is_token != original["is_token"]
        ):
            raise ValueError("Mill-three original object identity was mutated")
        return original

    def _check_mill_three_history(self):
        if self._objects is not self._mill_three_registry or self.rng is not self._mill_three_rng:
            raise ValueError("Mill-three registry/RNG identity was relinked")
        commits = [e for e in self.events if e.get("event") == "mill_three_committed"]
        if len(commits) != len(self._mill_three_history):
            raise ValueError("Mill-three original transaction ledger is incomplete")
        consumed = set()
        for _start, encoded in self._mill_three_history:
            original = json.loads(encoded)
            if _encoded(self.events[_start : _start + len(original)]) != encoded:
                raise ValueError("Mill-three original transaction was altered")
            consumed.add(original[-1]["stack_object_id"])
        if consumed != set(self._mill_three_pre_states):
            raise ValueError("Mill-three original pre-state ledger was altered")
        for _start, encoded in self._mill_three_history:
            original = json.loads(encoded)
            if self._mill_three_pre_states[original[-1]["stack_object_id"]] != _encoded(
                original[0]
            ):
                raise ValueError("Mill-three original pre-state was altered")
        if consumed != self._mill_three_consumed:
            raise ValueError("Mill-three consumed state was altered")
        for source, card, event, _ in self._mill_three_sources.values():
            self._mill_three_identity(source)
            if source.card is not card:
                raise ValueError("Mill-three source card was relinked")
            self._authenticate_original_rules_event(event)

    def _enqueue_mill_three(self, event, source, fragment):
        from tmnt_design_studio.engine07 import RulesEventKind, TriggerEffect, TriggerInstance

        self._check_mill_three_history()
        self._authenticate_original_rules_event(event)
        if (
            not self.is_authoritative(source, "battlefield")
            or event.kind is not RulesEventKind.CREATURE_ENTERED
            or event.subject_ids != (source.object_id,)
            or event.player_index != source.controller
            or (source.object_id, source.controller) not in event.battlefield_authority
            or fragment not in self.interpreter.fragments(source.card)
            or self.interpreter.mill_three_semantic_coverage(source.card, fragment) is None
        ):
            raise ValueError("Mill-three entry provenance is invalid")
        if source.object_id in self._mill_three_sources:
            original, card, _, _ = self._mill_three_sources[source.object_id]
            if original is not source or card is not source.card:
                raise ValueError("Mill-three source was relinked")
            return
        self._mill_three_sources[source.object_id] = (source, source.card, event, source.controller)
        occurrence = self._register_semantic_occurrence(source, source.controller, fragment, ())
        self._witness_from_existing_events(occurrence)
        trigger = TriggerInstance(
            f"trigger-{self._next_trigger_number:06d}",
            source.controller,
            source.object_id,
            source.card,
            fragment,
            TriggerEffect.ETB_MILL_THREE,
            event,
        )
        self._next_trigger_number += 1
        self._triggers[trigger.trigger_id] = trigger
        self.pending_triggers.append(trigger)
        self.log(
            "trigger_pending",
            trigger_id=trigger.trigger_id,
            event_id=event.event_id,
            source=source.card.name,
            controller=self.players[source.controller].name,
            oracle_fragment=fragment,
        )

    def _anchor_mill_three(self, ability, trigger):
        from tmnt_design_studio.engine07 import TriggerEffect

        if ability.effect is TriggerEffect.ETB_MILL_THREE:
            self._mill_three_anchors[ability.object_id] = (ability, trigger, trigger.trigger_id)

    def _validate_mill_three_trigger(self, ability):
        from tmnt_design_studio.engine07 import TriggerEffect

        self._check_mill_three_history()
        anchor = self._mill_three_anchors.get(ability.object_id)
        if anchor is None or anchor[0] is not ability:
            raise ValueError("Mill-three Stack identity is invalid")
        _, trigger, trigger_id = anchor
        source_anchor = self._mill_three_sources.get(ability.source_id)
        if source_anchor is None:
            raise ValueError("Mill-three source provenance is invalid")
        source, card, event, controller = source_anchor
        self._authenticate_original_rules_event(event)
        if (
            self._objects.get(ability.object_id) is not ability
            or self._triggers.get(trigger_id) is not trigger
            or ability.source_id != source.object_id
            or trigger.source_id != source.object_id
            or ability.source_card is not card
            or trigger.source_card is not card
            or ability.event is not event
            or trigger.event is not event
            or ability.controller != controller
            or trigger.controller != controller
            or ability.trigger_id != trigger_id
            or trigger.trigger_id != trigger_id
            or ability.effect is not TriggerEffect.ETB_MILL_THREE
            or trigger.effect is not TriggerEffect.ETB_MILL_THREE
            or ability.oracle_fragment != CardInterpreter.MILL_THREE_FRAGMENT
            or trigger.oracle_fragment != CardInterpreter.MILL_THREE_FRAGMENT
            or ability.object_id in self._mill_three_consumed
        ):
            raise ValueError("Mill-three trigger provenance is invalid or consumed")
        if not self._priority_resolution_in_progress and (
            self.priority_state is None or not self.priority_state.resolution_pending
        ):
            raise ValueError("Mill-three requires all-pass Priority")

    def _preflight_mill_three(self, ability):
        from tmnt_design_studio.engine07 import CardObject

        self._validate_mill_three_trigger(ability)
        player = self.players[ability.controller]
        anchored_player, library_zone, graveyard_zone = self._mill_three_zones[ability.controller]
        if (
            player is not anchored_player
            or player.library is not library_zone
            or player.graveyard is not graveyard_zone
            or type(player.library) is not list
            or type(player.graveyard) is not list
        ):
            raise ValueError("Mill-three zone container was relinked")
        library, graveyard = tuple(player.library), tuple(player.graveyard)
        for zone, objects in (("library", library), ("graveyard", graveyard)):
            for obj in objects:
                self._mill_three_identity(obj)
                if (
                    not isinstance(obj, CardObject)
                    or obj.is_token
                    or obj.owner != ability.controller
                    or not self.is_authoritative(obj, zone)
                    or sum(self._identity_contains(items, obj) for items in self._all_zone_lists())
                    != 1
                ):
                    raise ValueError("Mill-three zone identity is invalid")
            if len({id(obj) for obj in objects}) != len(objects):
                raise ValueError("Mill-three zone contains duplicate identities")
        number = self._next_object_number
        if (
            type(number) is not int
            or number != max(int(key.split("-")[1]) for key in self._objects) + 1
        ):
            raise ValueError("Mill-three allocation provenance is invalid")
        n = min(3, len(library))
        return library, graveyard, tuple(reversed(library[-n:])) if n else ()

    def _resolve_mill_three(self, ability):
        if ability.zone != "former":
            raise ValueError("Mill-three requires Stack resolution")
        library, graveyard, milled = self._preflight_mill_three(ability)
        player = self.players[ability.controller]
        start = len(self.events)
        number = self._next_object_number
        registered = set(self._objects)
        hands = [[obj.object_id for obj in p.hand] for p in self.players]
        failed = [p.failed_draw_pending for p in self.players]
        rng_before = (self.rng.state_digest, len(self.rng.records))
        try:
            self.log(
                "mill_three_started",
                stack_object_id=ability.object_id,
                controller=ability.controller,
                pre_library_ids=[obj.object_id for obj in library],
                pre_graveyard_ids=[obj.object_id for obj in graveyard],
                milled_ids=[obj.object_id for obj in milled],
                hand_ids=hands,
                failed_draw_pending=failed,
                rng_state=rng_before[0],
                rng_records=rng_before[1],
            )
            original_pre_state = _encoded(self.events[-1])
            moved = [self.move_object(obj, "graveyard", reason="etb_mill_three") for obj in milled]
            untouched = library[: -len(milled)] if milled else library
            if (
                len(player.library) != len(untouched)
                or any(a is not b for a, b in zip(player.library, untouched, strict=True))
                or len(player.graveyard) != len(graveyard) + len(moved)
                or any(
                    a is not b
                    for a, b in zip(player.graveyard, graveyard + tuple(moved), strict=True)
                )
                or hands != [[obj.object_id for obj in p.hand] for p in self.players]
                or failed != [p.failed_draw_pending for p in self.players]
                or rng_before != (self.rng.state_digest, len(self.rng.records))
            ):
                raise ValueError("Mill-three transaction changed unrelated state")
            self.log(
                "mill_three_committed",
                event_id=ability.event.event_id,
                trigger_id=ability.trigger_id,
                stack_object_id=ability.object_id,
                source_id=ability.source_id,
                controller=ability.controller,
                oracle_fragment=ability.oracle_fragment,
                start_event_cursor=start,
                new_graveyard_ids=[obj.object_id for obj in moved],
                post_library_ids=[obj.object_id for obj in player.library],
                post_graveyard_ids=[obj.object_id for obj in player.graveyard],
                hand_ids=hands,
                failed_draw_pending=failed,
                rng_state=self.rng.state_digest,
                rng_records=len(self.rng.records),
            )
        except Exception:
            # Only library->graveyard moves occur here; no callback or nested trigger runs.
            player.library[:] = library
            player.graveyard[:] = graveyard
            for obj in library:
                obj.zone = "library"
            for key in set(self._objects) - registered:
                self._objects.pop(key)
                self._mill_three_births.pop(key, None)
            self._next_object_number = number
            del self.events[start:]
            raise
        self._mill_three_pre_states[ability.object_id] = original_pre_state
        self._mill_three_consumed.add(ability.object_id)
        self._mill_three_history.append((start, _encoded(self.events[start:])))

    def mill_three_snapshot_evidence(self):
        self._check_mill_three_history()
        transactions = [
            {"start": start, "events": json.loads(encoded)}
            for start, encoded in self._mill_three_history
        ]
        ids = set()
        for item in transactions:
            first, last = item["events"][0], item["events"][-1]
            ids.update(
                first["pre_library_ids"]
                + first["pre_graveyard_ids"]
                + last["new_graveyard_ids"]
                + [last["source_id"]]
            )
        for event in self.events:
            if event.get("event") == "token_ceased" and transactions:
                ids.add(event["object_id"])
        return {
            "pre_states": {
                key: json.loads(value) for key, value in self._mill_three_pre_states.items()
            },
            "transactions": transactions,
            "identities": [json.loads(self._mill_three_births[key][2]) for key in sorted(ids)],
        }

    @staticmethod
    def validate_mill_three_snapshot_evidence(snapshot):
        events = snapshot.get("events", [])
        commits = [(i, e) for i, e in enumerate(events) if e.get("event") == "mill_three_committed"]
        resolved = [
            e
            for e in events
            if e.get("event") == "trigger_resolved" and e.get("effect") == "etb_mill_three"
        ]
        evidence = snapshot.get("mill_three_evidence")
        if evidence is None and not commits and not resolved:
            return
        try:
            ledger = evidence["transactions"]
            identities = evidence["identities"]
            births = {o["object_id"]: o for o in identities}
            assert len(births) == len(identities)
            assert isinstance(ledger, list) and len(ledger) == len(commits) == len(resolved)

            def unique(kind, key, value):
                found = [
                    (i, e)
                    for i, e in enumerate(events)
                    if e.get("event") == kind and e.get(key) == value
                ]
                assert len(found) == 1
                return found[0]

            seen = set()
            for original, (cursor, commit) in zip(ledger, commits, strict=True):
                start = commit["start_event_cursor"]
                assert type(start) is int and 0 <= start < cursor and original["start"] == start
                assert _encoded(original["events"]) == _encoded(events[start : cursor + 1])
                stack_id, source_id, controller = (
                    commit["stack_object_id"],
                    commit["source_id"],
                    commit["controller"],
                )
                assert stack_id not in seen and type(controller) is int and controller in (0, 1)
                seen.add(stack_id)
                fragment = CardInterpreter.MILL_THREE_FRAGMENT
                assert commit["oracle_fragment"] == fragment
                source = births[source_id]
                assert "Creature" in source["type_line"].split("\u2014", 1)[0].split()
                assert fragment in source["oracle_text"].splitlines()
                ec, entry = unique("rules_event", "event_id", commit["event_id"])
                assert entry["rules_event"] == "creature_entered" and entry["subject_ids"] == [
                    source_id
                ]
                assert {"object_id": source_id, "controller": controller} in entry[
                    "battlefield_authority"
                ]
                originals = [
                    e
                    for e in snapshot["rules_event_evidence"]
                    if e["event_id"] == commit["event_id"]
                ]
                assert len(originals) == 1
                origin = originals[0]
                assert origin["kind"] == "creature_entered" and origin["player_index"] == controller
                for key in (
                    "source_id",
                    "subject_ids",
                    "battlefield_authority",
                    "battlefield_characteristics",
                ):
                    assert _encoded(origin[key]) == _encoded(entry[key])
                pc, pending = unique("trigger_pending", "trigger_id", commit["trigger_id"])
                sc, stacked = unique("trigger_stacked", "stack_object_id", stack_id)
                ac, permission = unique("stack_resolution_permitted", "stack_object_id", stack_id)
                rc, resolution = unique("trigger_resolved", "stack_object_id", stack_id)
                assert ec < pc < sc < ac < start < cursor < rc
                assert (
                    pending["event_id"]
                    == stacked["event_id"]
                    == resolution["event_id"]
                    == commit["event_id"]
                )
                assert stacked["trigger_id"] == resolution["trigger_id"] == commit["trigger_id"]
                assert pending["oracle_fragment"] == resolution["oracle_fragment"] == fragment
                assert (
                    resolution["effect"] == "etb_mill_three"
                    and resolution["source_id"] == source_id
                )
                name = snapshot["players"][controller]["name"]
                assert pending["controller"] == stacked["controller"] == entry["player"] == name
                assert pending["source"] == stacked["source"] == source["card"]
                passes = [
                    e
                    for e in events[sc:ac]
                    if e.get("event") == "priority_passed"
                    and e.get("priority_epoch") == permission["priority_epoch"]
                ]
                assert len(passes) >= 2 and passes[-1]["resolution_pending"] is True
                assert (
                    passes[-2]["consecutive_passes"] == 1 and passes[-1]["consecutive_passes"] == 2
                )
                assert {passes[-1]["player_index"], passes[-2]["player_index"]} == {0, 1}
                steps = events[start:cursor]
                pre = steps[0]
                assert _encoded(evidence["pre_states"][stack_id]) == _encoded(pre)
                assert (
                    pre["event"] == "mill_three_started"
                    and pre["stack_object_id"] == stack_id
                    and pre["controller"] == controller
                )
                library, graveyard = pre["pre_library_ids"], pre["pre_graveyard_ids"]
                assert len(set(library + graveyard)) == len(library + graveyard)
                assert all(
                    births[key]["owner"] == controller and births[key]["is_token"] is False
                    for key in library + graveyard
                )
                n = min(3, len(library))
                milled = list(reversed(library[-n:])) if n else []
                assert pre["milled_ids"] == milled
                moves = steps[1:]
                assert len(moves) == n and all(e["event"] == "zone_changed" for e in moves)
                destinations = []
                for key, move in zip(milled, moves, strict=True):
                    dest = move["destination_object_id"]
                    assert move["source_object_id"] == key and move["source_zone"] == "library"
                    assert (
                        move["destination_zone"] == "graveyard"
                        and move["reason"] == "etb_mill_three"
                    )
                    assert move["owner"] == name and move["card"] == births[key]["card"]
                    assert move["library_position"] is None
                    assert dest not in library + graveyard + destinations
                    assert births[dest]["birth_zone"] == "graveyard"
                    for field in ("owner", "card", "type_line", "oracle_text", "is_token"):
                        assert births[key][field] == births[dest][field]
                    assert not any(e.get("destination_object_id") == dest for e in events[:start])
                    destinations.append(dest)
                assert commit["new_graveyard_ids"] == destinations
                assert commit["post_library_ids"] == (library[:-n] if n else library)
                assert commit["post_graveyard_ids"] == graveyard + destinations
                for field in ("hand_ids", "failed_draw_pending", "rng_state", "rng_records"):
                    assert commit[field] == pre[field]
                assert len(pre["hand_ids"]) == len(pre["failed_draw_pending"]) == 2
                assert all(type(flag) is bool for flag in pre["failed_draw_pending"])
                records = snapshot["rng"]["records"]
                assert all(
                    a["state_after"] == b["state_before"]
                    for a, b in zip(records, records[1:], strict=False)
                )
                assert records[-1]["state_after"] == snapshot["rng"]["state_digest"]
                count = pre["rng_records"]
                assert type(count) is int and 0 < count <= len(records)
                assert records[count - 1]["state_after"] == pre["rng_state"]
                assert [e["sequence"] for e in records] == list(range(1, len(records) + 1))
                # Join hand/graveyard to the independent preceding zone history.
                for owner, player in enumerate(snapshot["players"]):
                    hand, yard = [], []
                    for event in events[:start]:
                        if event.get("owner") != player["name"]:
                            continue
                        if event.get("event") == "token_ceased":
                            token = births[event["object_id"]]
                            assert token["is_token"] is True and token["owner"] == owner
                            assert token["card"] == event["token"]
                            assert event["state_based_action"] == "token_ceases"
                            if event["previous_zone"] == "hand":
                                hand.remove(event["object_id"])
                            elif event["previous_zone"] == "graveyard":
                                yard.remove(event["object_id"])
                            continue
                        if event.get("event") != "zone_changed":
                            continue
                        for zone, values in (("hand", hand), ("graveyard", yard)):
                            if event["source_zone"] == zone:
                                values.remove(event["source_object_id"])
                            if event["destination_zone"] == zone:
                                values.append(event["destination_object_id"])
                    assert hand == pre["hand_ids"][owner]
                    if owner == controller:
                        assert yard == graveyard
            assert seen == set(evidence["pre_states"])
            covered = {
                i
                for cursor, commit in commits
                for i in range(commit["start_event_cursor"], cursor + 1)
            }
            assert all(
                i in covered
                for i, e in enumerate(events)
                if e.get("event", "").startswith("mill_three_")
            )
        except (
            AssertionError,
            KeyError,
            TypeError,
            ValueError,
            IndexError,
            StopIteration,
        ) as error:
            raise ValueError("Mill-three transaction evidence does not reconstruct") from error
