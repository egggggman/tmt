"""Exact Krang ETB hand-refill transaction and authenticated reconstruction."""

import json

from tmnt_design_studio.card_interpreter07 import CardInterpreter


def _encoded(value):
    return json.dumps(value, sort_keys=True)


class KrangRefillMixin:
    def _init_krang_refill(self):
        self._krang_refill_entries = {}
        self._krang_refill_sources = {}
        self._krang_refill_anchors = {}
        self._krang_refill_consumed = set()
        self._krang_refill_history = []
        self._krang_refill_pre_states = {}
        self._krang_refill_births = {}
        self._krang_refill_registry = self._objects
        self._krang_refill_rng = self.rng

    def _krang_refill_register(self, obj):
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
            self._krang_refill_births[obj.object_id] = (obj, obj.card, _encoded(descriptor))

    def _krang_refill_identity(self, obj):
        birth = self._krang_refill_births.get(getattr(obj, "object_id", None))
        if birth is None or birth[0] is not obj or birth[1] is not obj.card:
            raise ValueError("Krang refill object/card identity was relinked")
        original = json.loads(birth[2])
        if (
            self._objects.get(obj.object_id) is not obj
            or obj.owner != original["owner"]
            or obj.card.name != original["card"]
            or obj.card.type_line != original["type_line"]
            or obj.card.oracle_text != original["oracle_text"]
            or obj.is_token != original["is_token"]
        ):
            raise ValueError("Krang refill original object identity was mutated")
        return original

    def _check_krang_refill_history(self):
        if (
            self._objects is not self._krang_refill_registry
            or self.rng is not self._krang_refill_rng
        ):
            raise ValueError("Krang refill registry/RNG identity was relinked")
        commits = [e for e in self.events if e.get("event") == "krang_refill_committed"]
        if len(commits) != len(self._krang_refill_history):
            raise ValueError("Krang refill original transaction ledger is incomplete")
        consumed = set()
        for _start, encoded in self._krang_refill_history:
            original = json.loads(encoded)
            if _encoded(self.events[_start : _start + len(original)]) != encoded:
                raise ValueError("Krang refill original transaction was altered")
            consumed.add(original[-1]["stack_object_id"])
        if consumed != set(self._krang_refill_pre_states):
            raise ValueError("Krang refill original pre-state ledger was altered")
        for _start, encoded in self._krang_refill_history:
            original = json.loads(encoded)
            if self._krang_refill_pre_states[original[-1]["stack_object_id"]] != _encoded(
                original[0]
            ):
                raise ValueError("Krang refill original pre-state was altered")
        if consumed != self._krang_refill_consumed:
            raise ValueError("Krang refill consumed state was altered")
        for key, (cursor, encoded) in self._krang_refill_entries.items():
            if _encoded(self.events[cursor]) != encoded or self.events[cursor]["source_id"] != key:
                raise ValueError("Krang entry condition evidence was altered")
        if len(self._krang_refill_entries) != sum(
            e.get("event") == "krang_refill_entry" for e in self.events
        ):
            raise ValueError("Krang entry ledger was altered")
        for source, card, event, _ in self._krang_refill_sources.values():
            self._krang_refill_identity(source)
            if source.card is not card:
                raise ValueError("Krang refill source card was relinked")
            self._authenticate_original_rules_event(event)

    def _krang_zones(self, controller):
        from tmnt_design_studio.engine07 import CardObject

        player, library, hand = self._krang_refill_zones[controller]
        if (
            self.players[controller] is not player
            or player.library is not library
            or player.hand is not hand
        ):
            raise ValueError("Krang zone container was relinked")
        for zone, objects in (("library", library), ("hand", hand)):
            if type(objects) is not list:
                raise ValueError("Krang zone is not authoritative")
            for obj in objects:
                self._krang_refill_identity(obj)
                if (
                    not isinstance(obj, CardObject)
                    or obj.is_token
                    or obj.owner != controller
                    or not self.is_authoritative(obj, zone)
                    or sum(self._identity_contains(z, obj) for z in self._all_zone_lists()) != 1
                ):
                    raise ValueError("Krang zone object is invalid")
            if len({id(o) for o in objects}) != len(objects):
                raise ValueError("Krang duplicate zone identity")
        return tuple(library), tuple(hand)

    def _enqueue_krang_refill(self, event, source, fragment):
        from tmnt_design_studio.engine07 import RulesEventKind, TriggerEffect, TriggerInstance

        self._check_krang_refill_history()
        self._authenticate_original_rules_event(event)
        self._krang_refill_identity(source)
        if (
            not self.is_authoritative(source, "battlefield")
            or event.kind is not RulesEventKind.CREATURE_ENTERED
            or event.subject_ids != (source.object_id,)
            or event.player_index != source.controller
            or (source.object_id, source.controller) not in event.battlefield_authority
            or fragment not in self.interpreter.fragments(source.card)
            or not self.interpreter.krang_refill_semantic_coverage(source.card, fragment)
        ):
            raise ValueError("Krang entry provenance is invalid")
        if source.object_id in self._krang_refill_entries:
            old = self._krang_refill_sources[source.object_id]
            if old[0] is not source or old[2] is not event:
                raise ValueError("Krang entry was replayed/relinked")
            return
        _, hand = self._krang_zones(source.controller)
        self._krang_refill_sources[source.object_id] = (
            source,
            source.card,
            event,
            source.controller,
        )
        cursor = len(self.events)
        self.log(
            "krang_refill_entry",
            source_id=source.object_id,
            event_id=event.event_id,
            controller=source.controller,
            oracle_fragment=fragment,
            hand_ids=[o.object_id for o in hand],
            hand_size=len(hand),
            condition=len(hand) < 4,
        )
        self._krang_refill_entries[source.object_id] = (cursor, _encoded(self.events[-1]))
        if len(hand) >= 4:
            return
        occurrence = self._register_semantic_occurrence(source, source.controller, fragment, ())
        self._witness_from_existing_events(occurrence)
        trigger = TriggerInstance(
            f"trigger-{self._next_trigger_number:06d}",
            source.controller,
            source.object_id,
            source.card,
            fragment,
            TriggerEffect.ETB_KRANG_REFILL,
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

    def _anchor_krang_refill(self, ability, trigger):
        from tmnt_design_studio.engine07 import TriggerEffect

        if ability.effect is TriggerEffect.ETB_KRANG_REFILL:
            self._krang_refill_anchors[ability.object_id] = (ability, trigger, trigger.trigger_id)

    def _preflight_krang_refill(self, ability):
        from tmnt_design_studio.engine07 import TriggerEffect

        self._check_krang_refill_history()
        anchor = self._krang_refill_anchors.get(ability.object_id)
        source_anchor = self._krang_refill_sources.get(ability.source_id)
        if anchor is None or anchor[0] is not ability or source_anchor is None:
            raise ValueError("Krang Stack/source identity is invalid")
        _, trigger, tid = anchor
        source, card, event, controller = source_anchor
        entry = json.loads(self._krang_refill_entries[source.object_id][1])
        if (
            self._objects.get(ability.object_id) is not ability
            or self._triggers.get(tid) is not trigger
            or not entry["condition"]
            or ability.object_id in self._krang_refill_consumed
        ):
            raise ValueError("Krang authority is invalid or consumed")
        for obj in (ability, trigger):
            if (
                obj.source_id != source.object_id
                or obj.source_card is not card
                or obj.event is not event
                or obj.controller != controller
                or obj.trigger_id != tid
                or obj.effect is not TriggerEffect.ETB_KRANG_REFILL
                or obj.oracle_fragment != entry["oracle_fragment"]
            ):
                raise ValueError("Krang original trigger provenance was altered")
        if not self._priority_resolution_in_progress and (
            self.priority_state is None or not self.priority_state.resolution_pending
        ):
            raise ValueError("Krang requires all-pass Priority")
        permissions = [
            e
            for e in self.events
            if e.get("event") == "stack_resolution_permitted"
            and e.get("stack_object_id") == ability.object_id
        ]
        if len(permissions) != 1:
            raise ValueError("Krang lacks unique Stack permission")
        number = self._next_object_number
        if (
            type(number) is not int
            or number != max(int(k.split("-")[1]) for k in self._objects) + 1
        ):
            raise ValueError("Krang allocator provenance invalid")
        return self._krang_zones(controller)

    def _resolve_krang_refill(self, ability):
        if ability.zone != "former":
            raise ValueError("Krang requires actual Stack resolution")
        library, hand = self._preflight_krang_refill(ability)
        player = self.players[ability.controller]
        n = max(0, 4 - len(hand))
        start = len(self.events)
        number, registered = self._next_object_number, set(self._objects)
        failed = player.failed_draw_pending
        rng = self.rng.state_digest, len(self.rng.records)
        try:
            self.log(
                "krang_refill_started",
                stack_object_id=ability.object_id,
                controller=ability.controller,
                pre_library_ids=[o.object_id for o in library],
                pre_hand_ids=[o.object_id for o in hand],
                hand_size=len(hand),
                requested=n,
                failed_draw_pending=failed,
                rng_state=rng[0],
                rng_records=rng[1],
            )
            original = _encoded(self.events[-1])
            successes = 0
            for ordinal in range(n):
                success = self.draw(player, 1)
                successes += int(success)
                self.log(
                    "krang_refill_attempt",
                    stack_object_id=ability.object_id,
                    ordinal=ordinal + 1,
                    success=success,
                )
            k = min(n, len(library))
            if (
                successes != k
                or tuple(player.library) != (library[:-k] if k else library)
                or any(a is not b for a, b in zip(player.hand[: len(hand)], hand, strict=True))
                or len(player.hand) != len(hand) + k
                or rng != (self.rng.state_digest, len(self.rng.records))
                or player.failed_draw_pending != (failed or k < n)
            ):
                raise ValueError("Krang Draw transaction changed unexpected state")
            self.log(
                "krang_refill_committed",
                event_id=ability.event.event_id,
                trigger_id=ability.trigger_id,
                stack_object_id=ability.object_id,
                source_id=ability.source_id,
                controller=ability.controller,
                oracle_fragment=ability.oracle_fragment,
                start_event_cursor=start,
                requested=n,
                attempted=n,
                successful=successes,
                failed=n - successes,
                post_library_ids=[o.object_id for o in player.library],
                post_hand_ids=[o.object_id for o in player.hand],
                failed_draw_pending=player.failed_draw_pending,
                rng_state=rng[0],
                rng_records=rng[1],
            )
        except Exception:
            player.library[:] = library
            player.hand[:] = hand
            player.failed_draw_pending = failed
            for obj in library:
                obj.zone = "library"
            for key in set(self._objects) - registered:
                self._objects.pop(key)
                self._krang_refill_births.pop(key, None)
                self._mill_three_births.pop(key, None)
            self._next_object_number = number
            del self.events[start:]
            raise
        self._krang_refill_pre_states[ability.object_id] = original
        self._krang_refill_consumed.add(ability.object_id)
        self._krang_refill_history.append((start, _encoded(self.events[start:])))

    def krang_refill_snapshot_evidence(self):
        self._check_krang_refill_history()
        entries = [
            {"cursor": c, "record": json.loads(v)} for c, v in self._krang_refill_entries.values()
        ]
        tx = [{"start": c, "events": json.loads(v)} for c, v in self._krang_refill_history]
        ids = set()
        for item in entries:
            ids.update(item["record"]["hand_ids"] + [item["record"]["source_id"]])
        for item in tx:
            for e in item["events"]:
                for key in ("pre_hand_ids", "pre_library_ids", "post_hand_ids", "post_library_ids"):
                    ids.update(e.get(key, []))
        return {
            "entries": entries,
            "transactions": tx,
            "pre_states": {k: json.loads(v) for k, v in self._krang_refill_pre_states.items()},
            "identities": [json.loads(self._krang_refill_births[k][2]) for k in sorted(ids)],
        }

    def _validate_krang_refill_live(self):
        if not self._krang_refill_entries:
            self._check_krang_refill_history()
            return
        origins = []
        for item in self._rules_event_evidence:
            origins.append(
                {
                    "event_id": item.event_id,
                    "kind": item.kind.value,
                    "player_index": item.player_index,
                    "source_id": item.source_id,
                    "subject_ids": list(item.subject_ids),
                    "battlefield_authority": [
                        {"object_id": oid, "controller": c} for oid, c in item.battlefield_authority
                    ],
                    "battlefield_characteristics": [
                        {"object_id": oid, "controller": c, "type_line": t}
                        for oid, c, t in item.battlefield_characteristics
                    ],
                }
            )
        self.validate_krang_refill_snapshot_evidence(
            {
                "events": self.events,
                "krang_refill_evidence": self.krang_refill_snapshot_evidence(),
                "rules_event_evidence": origins,
                "players": [
                    {"name": p.name, "failed_draw_pending": p.failed_draw_pending}
                    for p in self.players
                ],
                "rng": {"records": [{"state_after": r.state_after} for r in self.rng.records]},
            }
        )

    @staticmethod
    def validate_krang_refill_snapshot_evidence(snapshot):
        events = snapshot.get("events", [])
        evidence = snapshot.get("krang_refill_evidence")
        relevant = [
            e
            for e in events
            if e.get("event", "").startswith("krang_refill_")
            or e.get("effect") == "etb_krang_refill"
        ]
        if evidence is None and not relevant:
            return
        try:

            def unique(kind, key, value):
                found = [
                    (i, e)
                    for i, e in enumerate(events)
                    if e.get("event") == kind and e.get(key) == value
                ]
                assert len(found) == 1
                return found[0]

            def hand_at(cursor, name):
                hand = []
                for e in events[:cursor]:
                    if e.get("owner") != name:
                        continue
                    if e.get("event") == "zone_changed":
                        if e["source_zone"] == "hand":
                            hand.remove(e["source_object_id"])
                        if e["destination_zone"] == "hand":
                            hand.append(e["destination_object_id"])
                    elif e.get("event") == "token_ceased" and e["previous_zone"] == "hand":
                        hand.remove(e["object_id"])
                return hand

            identities = evidence["identities"]
            births = {o["object_id"]: o for o in identities}
            assert len(births) == len(identities)
            entries = {}
            for item in evidence["entries"]:
                cursor, entry = item["cursor"], item["record"]
                assert events[cursor] == entry and entry["event"] == "krang_refill_entry"
                sid = entry["source_id"]
                controller = entry["controller"]
                assert sid not in entries and type(controller) is int and controller in (0, 1)
                source = births[sid]
                fragment = entry["oracle_fragment"]
                assert (
                    CardInterpreter.is_krang_refill_fragment(fragment)
                    and fragment in source["oracle_text"].splitlines()
                )
                assert fragment.removeprefix("When ").split(" enters,", 1)[0] in {
                    source["card"],
                    source["card"].split(",", 1)[0],
                }
                assert "Creature" in source["type_line"].split("—", 1)[0].split()
                ec, event = unique("rules_event", "event_id", entry["event_id"])
                assert (
                    ec < cursor
                    and event["rules_event"] == "creature_entered"
                    and event["subject_ids"] == [sid]
                )
                assert {"object_id": sid, "controller": controller} in event[
                    "battlefield_authority"
                ]
                origins = [
                    o
                    for o in snapshot["rules_event_evidence"]
                    if o["event_id"] == entry["event_id"]
                ]
                assert (
                    len(origins) == 1
                    and origins[0]["kind"] == "creature_entered"
                    and origins[0]["player_index"] == controller
                )
                for key in (
                    "source_id",
                    "subject_ids",
                    "battlefield_authority",
                    "battlefield_characteristics",
                ):
                    assert origins[0][key] == event[key]
                name = snapshot["players"][controller]["name"]
                assert event["player"] == name
                assert hand_at(ec, name) == entry["hand_ids"] == hand_at(cursor, name)
                assert len(set(entry["hand_ids"])) == len(entry["hand_ids"])
                assert entry["hand_size"] == len(entry["hand_ids"]) and entry["condition"] is (
                    entry["hand_size"] < 4
                )
                assert all(births[k]["owner"] == controller for k in entry["hand_ids"])
                pending = [
                    (i, e)
                    for i, e in enumerate(events)
                    if e.get("event") == "trigger_pending"
                    and e.get("event_id") == entry["event_id"]
                    and e.get("oracle_fragment") == fragment
                ]
                assert len(pending) == int(entry["condition"])
                if pending:
                    assert (
                        pending[0][0] > cursor
                        and pending[0][1]["controller"] == name
                        and pending[0][1]["source"] == source["card"]
                    )
                entries[sid] = (cursor, entry, pending)
            assert len(entries) == sum(e.get("event") == "krang_refill_entry" for e in events)
            seen = set()
            covered = set()
            commits = [
                (i, e) for i, e in enumerate(events) if e.get("event") == "krang_refill_committed"
            ]
            assert len(commits) == len(evidence["transactions"])
            for tx, (end, commit) in zip(evidence["transactions"], commits, strict=True):
                start = commit["start_event_cursor"]
                stack = commit["stack_object_id"]
                assert (
                    stack not in seen
                    and tx["start"] == start
                    and tx["events"] == events[start : end + 1]
                )
                seen.add(stack)
                covered.update(range(start, end + 1))
                cursor, entry, pending = entries[commit["source_id"]]
                assert (
                    entry["condition"]
                    and commit["event_id"] == entry["event_id"]
                    and commit["oracle_fragment"] == entry["oracle_fragment"]
                    and commit["controller"] == entry["controller"]
                )
                controller = commit["controller"]
                name = snapshot["players"][controller]["name"]
                pc, pending = pending[0]
                tid = commit["trigger_id"]
                sc, stacked = unique("trigger_stacked", "stack_object_id", stack)
                ac, permission = unique("stack_resolution_permitted", "stack_object_id", stack)
                rc, resolved = unique("trigger_resolved", "stack_object_id", stack)
                assert cursor < pc < sc < ac < start < end < rc
                assert (
                    pending["trigger_id"] == stacked["trigger_id"] == resolved["trigger_id"] == tid
                )
                assert stacked["event_id"] == resolved["event_id"] == entry["event_id"]
                assert (
                    stacked["controller"] == name
                    and stacked["source"] == births[commit["source_id"]]["card"]
                )
                assert (
                    resolved["effect"] == "etb_krang_refill"
                    and resolved["source_id"] == commit["source_id"]
                    and resolved["oracle_fragment"] == entry["oracle_fragment"]
                )
                passes = [
                    e
                    for e in events[sc:ac]
                    if e.get("event") == "priority_passed"
                    and e.get("priority_epoch") == permission["priority_epoch"]
                ]
                assert (
                    len(passes) == 2
                    and passes[0]["consecutive_passes"] == 1
                    and passes[1]["consecutive_passes"] == 2
                    and passes[1]["resolution_pending"] is True
                    and {e["player_index"] for e in passes} == {0, 1}
                )
                pre = events[start]
                assert (
                    pre == evidence["pre_states"][stack]
                    and pre["event"] == "krang_refill_started"
                    and pre["stack_object_id"] == stack
                    and pre["controller"] == controller
                )
                library = list(pre["pre_library_ids"])
                hand = list(pre["pre_hand_ids"])
                assert hand == hand_at(start, name) and len(set(library + hand)) == len(
                    library + hand
                )
                assert all(
                    births[k]["owner"] == controller and not births[k]["is_token"]
                    for k in library + hand
                )
                assert pre["hand_size"] == len(hand)
                n = max(0, 4 - len(hand))
                assert type(pre["requested"]) is int and pre["requested"] == n
                steps = events[start + 1 : end]
                offset = 0
                successes = 0
                failed = pre["failed_draw_pending"]
                assert type(failed) is bool
                for ordinal in range(1, n + 1):
                    if library:
                        move, draw, attempt = steps[offset : offset + 3]
                        offset += 3
                        old = library.pop()
                        new = move["destination_object_id"]
                        assert (
                            move["event"] == "zone_changed"
                            and move["source_object_id"] == old
                            and move["source_zone"] == "library"
                            and move["destination_zone"] == "hand"
                            and move["reason"] == "draw"
                            and move["owner"] == name
                            and move["card"] == births[old]["card"]
                            and move["library_position"] is None
                        )
                        assert (
                            new not in pre["pre_library_ids"] + hand
                            and births[new]["birth_zone"] == "hand"
                        )
                        for key in ("owner", "card", "type_line", "oracle_text", "is_token"):
                            assert births[new][key] == births[old][key]
                        assert not any(
                            e.get("destination_object_id") == new for e in events[:start]
                        )
                        assert (
                            draw["event"] == "card_drawn"
                            and draw["player"] == name
                            and draw["setup"] is False
                        )
                        hand.append(new)
                        successes += 1
                        success = True
                    else:
                        failure, attempt = steps[offset : offset + 2]
                        offset += 2
                        assert (
                            failure["event"] == "draw_failed"
                            and failure["player"] == name
                            and failure["reason"] == "empty_library"
                            and failure["state_based_action_pending"] is True
                        )
                        failed = True
                        success = False
                    assert (
                        attempt["event"] == "krang_refill_attempt"
                        and attempt["ordinal"] == ordinal
                        and attempt["stack_object_id"] == stack
                        and attempt["success"] is success
                    )
                assert offset == len(steps)
                assert (
                    commit["requested"] == commit["attempted"] == n
                    and commit["successful"] == successes
                    and commit["failed"] == n - successes
                )
                assert (
                    commit["post_hand_ids"] == hand
                    and commit["post_library_ids"] == library
                    and commit["failed_draw_pending"] is failed
                )
                assert (commit["rng_state"], commit["rng_records"]) == (
                    pre["rng_state"],
                    pre["rng_records"],
                )
                records = snapshot["rng"]["records"]
                count = pre["rng_records"]
                assert (
                    0 < count <= len(records)
                    and records[count - 1]["state_after"] == pre["rng_state"]
                )
                if n and failed:
                    losses = [
                        (i, e)
                        for i, e in enumerate(events)
                        if i > rc
                        and e.get("event") == "player_lost"
                        and e.get("player") == name
                        and e.get("reason") == "draw_from_empty_library"
                        and e.get("state_based_action") == "failed_draw"
                    ]
                    assert losses, "Krang failed Draw requires subsequent SBA loss evidence"
            assert seen == set(evidence["pre_states"])
            assert len(seen) == sum(
                e.get("event") == "trigger_resolved" and e.get("effect") == "etb_krang_refill"
                for e in events
            )
            assert all(
                i in covered
                for i, e in enumerate(events)
                if e.get("event", "").startswith("krang_refill_")
                and e.get("event") != "krang_refill_entry"
            )
        except (
            AssertionError,
            KeyError,
            TypeError,
            ValueError,
            IndexError,
            StopIteration,
        ) as error:
            raise ValueError("Krang refill evidence does not reconstruct") from error
