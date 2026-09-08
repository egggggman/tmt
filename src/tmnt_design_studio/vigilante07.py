"""Exact Vigilante ETB / one-shot next-upkeep random discard. No generic scheduler."""

import json
from dataclasses import asdict, dataclass

from tmnt_design_studio.card_interpreter07 import CardInterpreter


@dataclass(frozen=True)
class VigilanteSchedule:
    schedule_id: str
    controller: int
    source_id: str
    event_id: str
    trigger_id: str
    stack_object_id: str
    oracle_fragment: str
    created_cursor: int


class VigilanteMixin:
    def _init_vigilante(self):
        self._vigilante_rng = self.rng
        self._vigilante_sources = {}
        self._vigilante_triggers = {}
        self._vigilante_stack = {}
        self._vigilante_schedules = {}
        self._vigilante_originals = {}
        self._vigilante_states = {}
        self._vigilante_history = []
        self._vigilante_upkeeps = set()

    def _seal_vigilante(self, start):
        self._vigilante_history.append((start, json.dumps(self.events[start:], sort_keys=True)))

    def _check_vigilante_live(self):
        if self.rng is not self._vigilante_rng:
            raise ValueError("Vigilante RNG identity was relinked")
        records = self.rng.records
        if records and (
            records[-1].state_after != self.rng.state_digest
            or any(
                a.state_after != b.state_before for a, b in zip(records, records[1:], strict=False)
            )
        ):
            raise ValueError("Vigilante RNG state chain was altered")
        for start, encoded in self._vigilante_history:
            original = json.loads(encoded)
            if json.dumps(self.events[start : start + len(original)], sort_keys=True) != encoded:
                raise ValueError("Vigilante original evidence was altered")
        if self._vigilante_schedules.keys() != self._vigilante_originals.keys():
            raise ValueError("Vigilante schedule registry was altered")
        states = {}
        scheduled = {}
        for _, encoded in self._vigilante_history:
            for event in json.loads(encoded):
                if event["event"] == "vigilante_scheduled":
                    scheduled[event["schedule_id"]] = {
                        key: event[key] for key in VigilanteSchedule.__dataclass_fields__
                    }
                if event["event"] in {
                    "vigilante_scheduled",
                    "vigilante_delivered",
                    "vigilante_resolved",
                }:
                    states[event["schedule_id"]] = {
                        "vigilante_scheduled": "pending",
                        "vigilante_delivered": "delivered",
                        "vigilante_resolved": "resolved",
                    }[event["event"]]
        if states != self._vigilante_states:
            raise ValueError("Vigilante lifecycle state was altered")
        for key, record in self._vigilante_originals.items():
            if asdict(record) != scheduled.get(key):
                raise ValueError("Vigilante scheduling provenance was altered")
            if self._vigilante_schedules[key] is not record:
                raise ValueError("Vigilante schedule identity was relinked")
            initial, initial_trigger = self._vigilante_stack[record.stack_object_id]
            _, _, initial_fields = self._vigilante_triggers[record.trigger_id]
            tid, captured, origin, initial_card, effect, event = initial_fields
            self._authenticate_original_rules_event(event)
            if (
                self._objects.get(record.stack_object_id) is not initial
                or self._triggers.get(tid) is not initial_trigger
                or initial.event is not event
                or initial.source_card is not initial_card
                or initial.controller != captured
                or captured != record.controller
                or initial.source_id != origin
                or origin != record.source_id
                or initial.effect is not effect
                or initial.trigger_id != tid
                or event.event_id != record.event_id
            ):
                raise ValueError("Vigilante original ETB provenance was altered")
            source, card, source_id = self._vigilante_sources[record.source_id]
            if (
                self._objects.get(source_id) is not source
                or source.object_id != source_id
                or source.card is not card
            ):
                raise ValueError("Vigilante source identity was relinked")

    def _enqueue_vigilante(self, event, source, fragment):
        from tmnt_design_studio.engine07 import RulesEventKind, TriggerEffect

        self._check_vigilante_live()
        self._authenticate_original_rules_event(event)
        if (
            not self.is_authoritative(source, "battlefield")
            or event.kind is not RulesEventKind.CREATURE_ENTERED
            or event.subject_ids != (source.object_id,)
            or event.player_index != source.controller
            or (source.object_id, source.controller) not in event.battlefield_authority
            or fragment not in self.interpreter.fragments(source.card)
            or self.interpreter.vigilante_semantic_coverage(source.card, fragment) is None
        ):
            raise ValueError("Vigilante ETB provenance is invalid")
        if source.object_id in self._vigilante_sources:
            original, card, _ = self._vigilante_sources[source.object_id]
            if source is not original or source.card is not card:
                raise ValueError("Vigilante ETB source was relinked")
            return
        self._vigilante_sources[source.object_id] = (source, source.card, source.object_id)
        occurrence = self._register_semantic_occurrence(source, source.controller, fragment, ())
        self._witness_from_existing_events(occurrence)
        self._new_vigilante_trigger(
            source.controller, source, event, TriggerEffect.ETB_VIGILANTE, None
        )

    def _new_vigilante_trigger(self, controller, source, event, effect, schedule_id):
        from tmnt_design_studio.engine07 import TriggerInstance

        trigger = TriggerInstance(
            f"trigger-{self._next_trigger_number:06d}",
            controller,
            source.object_id,
            source.card,
            CardInterpreter.VIGILANTE_FRAGMENT,
            effect,
            event,
        )
        self._next_trigger_number += 1
        self._triggers[trigger.trigger_id] = trigger
        self.pending_triggers.append(trigger)
        self._vigilante_triggers[trigger.trigger_id] = (
            trigger,
            schedule_id,
            (trigger.trigger_id, controller, source.object_id, source.card, effect, event),
        )
        self.log(
            "trigger_pending",
            trigger_id=trigger.trigger_id,
            event_id=event.event_id,
            source=source.card.name,
            controller=self.players[controller].name,
            oracle_fragment=trigger.oracle_fragment,
        )
        return trigger

    def _anchor_vigilante(self, ability, trigger):
        if trigger.trigger_id in self._vigilante_triggers:
            self._vigilante_stack[ability.object_id] = (ability, trigger)

    def _validate_vigilante_trigger(self, ability):
        from tmnt_design_studio.engine07 import TriggerEffect

        self._check_vigilante_live()
        anchor = self._vigilante_stack.get(ability.object_id)
        if anchor is None or anchor[0] is not ability:
            raise ValueError("Vigilante Stack identity is invalid")
        trigger = anchor[1]
        original, schedule_id, fields = self._vigilante_triggers[trigger.trigger_id]
        trigger_id, controller, source_id, card, effect, event = fields
        self._authenticate_original_rules_event(event)
        source, original_card, _ = self._vigilante_sources[source_id]
        if (
            trigger is not original
            or self._triggers.get(trigger_id) is not trigger
            or self._objects.get(ability.object_id) is not ability
            or self._objects.get(source_id) is not source
            or source.card is not original_card
            or card is not original_card
            or ability.source_card is not card
            or trigger.source_card is not card
            or ability.event is not event
            or trigger.event is not event
            or ability.effect is not effect
            or trigger.effect is not effect
            or ability.controller != controller
            or trigger.controller != controller
            or ability.source_id != source_id
            or trigger.source_id != source_id
            or ability.trigger_id != trigger_id
            or ability.oracle_fragment != CardInterpreter.VIGILANTE_FRAGMENT
            or trigger.oracle_fragment != CardInterpreter.VIGILANTE_FRAGMENT
        ):
            raise ValueError("Vigilante trigger provenance is invalid")
        if effect is TriggerEffect.ETB_VIGILANTE:
            if ability.object_id in self._vigilante_schedules:
                raise ValueError("Vigilante ETB already consumed")
        elif (
            schedule_id not in self._vigilante_schedules
            or self._vigilante_states[schedule_id] != "delivered"
        ):
            raise ValueError("Vigilante delayed record is not delivered or already consumed")
        if schedule_id is not None:
            record = self._vigilante_schedules[schedule_id]
            delivered = [
                e
                for e in self.events
                if e.get("event") == "vigilante_delivered" and e.get("schedule_id") == schedule_id
            ]
            if (
                record.controller != controller
                or record.source_id != source_id
                or len(delivered) != 1
                or delivered[0]["event_id"] != event.event_id
                or delivered[0]["trigger_id"] != trigger_id
            ):
                raise ValueError("Vigilante delayed Stack is not linked to its schedule")
        if not self._priority_resolution_in_progress and (
            self.priority_state is None or not self.priority_state.resolution_pending
        ):
            raise ValueError("Vigilante requires all-pass Priority")
        return schedule_id

    def _resolve_vigilante(self, ability):
        from tmnt_design_studio.engine07 import TriggerEffect

        schedule_id = self._validate_vigilante_trigger(ability)
        if ability.zone != "former":
            raise ValueError("Vigilante requires Stack resolution")
        start = len(self.events)
        player = self.players[ability.controller]
        if ability.effect is TriggerEffect.ETB_VIGILANTE:
            before_hand = [o.object_id for o in player.hand]
            before_library = [o.object_id for o in player.library]
            success = self.draw(player, 3)
            record = VigilanteSchedule(
                ability.object_id,
                ability.controller,
                ability.source_id,
                ability.event.event_id,
                ability.trigger_id,
                ability.object_id,
                ability.oracle_fragment,
                len(self.events),
            )
            self._vigilante_schedules[record.schedule_id] = record
            self._vigilante_originals[record.schedule_id] = record
            self._vigilante_states[record.schedule_id] = "pending"
            self.log(
                "vigilante_scheduled",
                **asdict(record),
                start_event_cursor=start,
                pre_hand_ids=before_hand,
                pre_library_ids=before_library,
                post_hand_ids=[o.object_id for o in player.hand],
                post_library_ids=[o.object_id for o in player.library],
                draw_succeeded=success,
                failed_draw_pending=player.failed_draw_pending,
            )
        else:
            hand = tuple(player.hand)
            if any(
                not self.is_authoritative(o, "hand") or o.owner != ability.controller for o in hand
            ):
                raise ValueError("Vigilante current hand identity is invalid")
            before = [o.object_id for o in hand]
            graveyard = [o.object_id for o in player.graveyard]
            state = self.rng.export_state()
            domain = f"vigilante:{schedule_id}:{ability.object_id}"
            # Always one shuffle record, including empty and short hands. Sample on a copy.
            shuffled = self.rng.shuffled(list(hand), domain=domain)
            rng = self.rng.records[-1]
            selected = shuffled[:3]
            movements = []
            for obj in selected:
                moved = self.move_object(obj, "graveyard", reason="vigilante_random_discard")
                movements.append([obj.object_id, moved.object_id])
            self._vigilante_states[schedule_id] = "resolved"
            self.log(
                "vigilante_resolved",
                schedule_id=schedule_id,
                controller=ability.controller,
                source_id=ability.source_id,
                oracle_fragment=ability.oracle_fragment,
                event_id=ability.event.event_id,
                trigger_id=ability.trigger_id,
                stack_object_id=ability.object_id,
                start_event_cursor=start,
                pre_hand_ids=before,
                pre_graveyard_ids=graveyard,
                post_hand_ids=[o.object_id for o in player.hand],
                post_graveyard_ids=[o.object_id for o in player.graveyard],
                movements=movements,
                rng_state_before=state,
                rng_domain=domain,
                rng_sequence=rng.sequence,
                rng_state_digest_before=rng.state_before,
                rng_state_digest_after=rng.state_after,
                permutation=list(rng.result),
                selected_ids=[o.object_id for o in selected],
                consumed=True,
            )
        self._seal_vigilante(start)

    def _vigilante_upkeep(self):
        from tmnt_design_studio.engine07 import RulesEventKind, TriggerEffect, TurnStep

        self._check_vigilante_live()
        if self.step is not TurnStep.UPKEEP:
            raise ValueError("Vigilante delivery requires an upkeep boundary")
        key = (self.turn, self.active_player)
        if key in self._vigilante_upkeeps:
            raise ValueError("Vigilante upkeep boundary replay")
        if (
            not self.events
            or self.events[-1].get("event") != "step_started"
            or self.events[-1].get("step") != "upkeep"
        ):
            raise ValueError("Vigilante upkeep requires an original step transition")
        self._vigilante_upkeeps.add(key)
        if not any(
            self._vigilante_states[r.schedule_id] == "pending"
            and r.controller == self.active_player
            for r in self._vigilante_schedules.values()
        ):
            return
        start = len(self.events)
        event = self._new_rules_event(RulesEventKind.VIGILANTE_UPKEEP, self.active_player, ())
        self.log(
            "vigilante_upkeep",
            event_id=event.event_id,
            controller=self.active_player,
            step_cursor=start - 1,
        )
        for record in self._vigilante_schedules.values():
            if (
                self._vigilante_states[record.schedule_id] != "pending"
                or record.controller != self.active_player
            ):
                continue
            source = self._vigilante_sources[record.source_id][0]
            trigger = self._new_vigilante_trigger(
                record.controller,
                source,
                event,
                TriggerEffect.VIGILANTE_DISCARD,
                record.schedule_id,
            )
            self._vigilante_states[record.schedule_id] = "delivered"
            self.log(
                "vigilante_delivered",
                schedule_id=record.schedule_id,
                event_id=event.event_id,
                trigger_id=trigger.trigger_id,
                controller=record.controller,
            )
        if self._put_pending_triggers_on_stack():
            self._begin_priority_window()
        self._seal_vigilante(start)

    def vigilante_snapshot_evidence(self):
        self._check_vigilante_live()
        return {
            "records": [
                {
                    **asdict(record),
                    "state": self._vigilante_states[key],
                    "consumed": self._vigilante_states[key] == "resolved",
                    "terminal_without_resolution": self.winner is not None
                    and self._vigilante_states[key] != "resolved",
                }
                for key, record in self._vigilante_schedules.items()
            ],
            "terminal_game": self.winner is not None,
            "segments": [
                {"start": start, "events": json.loads(encoded)}
                for start, encoded in self._vigilante_history
            ],
        }

    @staticmethod
    def validate_vigilante_snapshot_evidence(snapshot):
        from tmnt_design_studio.engine07 import DeterministicRNG

        events = snapshot.get("events", [])
        relevant = [
            (i, e) for i, e in enumerate(events) if e.get("event", "").startswith("vigilante_")
        ]
        evidence = snapshot.get("vigilante_evidence")
        if not relevant and evidence is None:
            return
        try:
            assert isinstance(evidence, dict)
            covered = set()
            for segment in evidence["segments"]:
                start = segment["start"]
                values = segment["events"]
                assert isinstance(start, int) and start >= 0 and values
                assert json.dumps(
                    events[start : start + len(values)], sort_keys=True
                ) == json.dumps(values, sort_keys=True)
                indices = set(range(start, start + len(values)))
                assert not covered & indices
                covered.update(indices)
            assert all(i in covered for i, _ in relevant)

            def unique(kind, key, value):
                found = [
                    (i, e)
                    for i, e in enumerate(events)
                    if e.get("event") == kind and e.get(key) == value
                ]
                assert len(found) == 1
                return found[0]

            def rule(event_id, kind):
                cursor, event = unique("rules_event", "event_id", event_id)
                assert event["rules_event"] == kind
                originals = [
                    e for e in snapshot["rules_event_evidence"] if e["event_id"] == event_id
                ]
                assert len(originals) == 1
                original = originals[0]
                assert (
                    original["kind"] == kind
                    and snapshot["players"][original["player_index"]]["name"] == event["player"]
                )
                for key in (
                    "source_id",
                    "subject_ids",
                    "battlefield_authority",
                    "battlefield_characteristics",
                ):
                    assert original[key] == event[key]
                return cursor, {**event, "player_index": original["player_index"]}

            def hand_at(cursor, controller):
                hand = []
                name = snapshot["players"][controller]["name"]
                for event in events[:cursor]:
                    if event.get("event") != "zone_changed" or event.get("owner") != name:
                        continue
                    if event["source_zone"] == "hand":
                        hand.remove(event["source_object_id"])
                    if event["destination_zone"] == "hand":
                        assert event["destination_object_id"] not in hand
                        hand.append(event["destination_object_id"])
                return hand

            def lifecycle(
                stack_id, trigger_id, event_id, controller, source_id, effect, commit_cursor
            ):
                pc, pending = unique("trigger_pending", "trigger_id", trigger_id)
                sc, stacked = unique("trigger_stacked", "stack_object_id", stack_id)
                ac, permission = unique("stack_resolution_permitted", "stack_object_id", stack_id)
                rc, resolved = unique("trigger_resolved", "stack_object_id", stack_id)
                assert (
                    pending["event_id"] == stacked["event_id"] == resolved["event_id"] == event_id
                )
                assert stacked["trigger_id"] == resolved["trigger_id"] == trigger_id
                assert (
                    pending["controller"]
                    == stacked["controller"]
                    == snapshot["players"][controller]["name"]
                )
                assert resolved["source_id"] == source_id and resolved["effect"] == effect
                assert (
                    pending["oracle_fragment"]
                    == resolved["oracle_fragment"]
                    == CardInterpreter.VIGILANTE_FRAGMENT
                )
                assert pc < sc < ac < commit_cursor < rc
                passes = [
                    e
                    for e in events[sc:ac]
                    if e.get("event") == "priority_passed"
                    and e.get("priority_epoch") == permission["priority_epoch"]
                ]
                assert len(passes) >= 2 and passes[-1]["resolution_pending"] is True
                assert {passes[-1]["player_index"], passes[-2]["player_index"]} == {0, 1}
                return pc, rc

            boundaries = []
            for cursor, event in relevant:
                if event["event"] != "vigilante_upkeep":
                    continue
                rc, r = rule(event["event_id"], "vigilante_upkeep")
                step = events[event["step_cursor"]]
                assert event["step_cursor"] < rc < cursor
                assert step["event"] == "step_started" and step["step"] == "upkeep"
                assert step["turn"] == event["turn"] == r["turn"]
                assert r["player_index"] == event["controller"] == (event["turn"] - 1) % 2
                assert r["subject_ids"] == []
                boundaries.append((cursor, event))
            assert len({(e["turn"], e["controller"]) for _, e in boundaries}) == len(boundaries)
            records = evidence["records"]
            schedules = [(i, e) for i, e in relevant if e["event"] == "vigilante_scheduled"]
            assert len(records) == len(schedules)
            assert len({r["schedule_id"] for r in records}) == len(records)
            for record, (cursor, s) in zip(records, schedules, strict=True):
                for key in VigilanteSchedule.__dataclass_fields__:
                    assert record[key] == s[key]
                sid = s["schedule_id"]
                controller = s["controller"]
                source = s["source_id"]
                assert (
                    controller in (0, 1)
                    and sid == s["stack_object_id"]
                    and s["created_cursor"] == cursor
                )
                assert s["oracle_fragment"] == CardInterpreter.VIGILANTE_FRAGMENT
                ec, entry = rule(s["event_id"], "creature_entered")
                assert entry["subject_ids"] == [source] and entry["player_index"] == controller
                assert {"object_id": source, "controller": controller} in entry[
                    "battlefield_authority"
                ]
                pc, rc = lifecycle(
                    sid, s["trigger_id"], s["event_id"], controller, source, "etb_vigilante", cursor
                )
                assert ec < pc and s["start_event_cursor"] < cursor
                assert s["pre_hand_ids"] == hand_at(s["start_event_cursor"], controller)
                steps = events[s["start_event_cursor"] : cursor]
                moves = [e for e in steps if e["event"] == "zone_changed"]
                n = min(3, len(s["pre_library_ids"]))
                assert len(moves) == n
                assert len(set(s["pre_hand_ids"] + s["pre_library_ids"])) == len(
                    s["pre_hand_ids"] + s["pre_library_ids"]
                )
                for index, move in enumerate(moves):
                    assert move["source_object_id"] == s["pre_library_ids"][-1 - index]
                    assert (
                        move["source_zone"] == "library"
                        and move["destination_zone"] == "hand"
                        and move["reason"] == "draw"
                    )
                drawn = [e["destination_object_id"] for e in moves]
                assert len(set(drawn + s["pre_hand_ids"] + s["pre_library_ids"])) == len(
                    drawn + s["pre_hand_ids"] + s["pre_library_ids"]
                )
                assert s["post_hand_ids"] == s["pre_hand_ids"] + drawn
                assert s["post_library_ids"] == (
                    s["pre_library_ids"][:-n] if n else s["pre_library_ids"]
                )
                assert s["draw_succeeded"] is (n == 3)
                failed = [e for e in steps if e["event"] == "draw_failed"]
                assert len(failed) == (0 if n == 3 else 1)
                if n < 3:
                    assert s["failed_draw_pending"] is True
                due = [
                    (i, e) for i, e in boundaries if i > cursor and e["controller"] == controller
                ]
                matching_steps = [
                    (i, e)
                    for i, e in enumerate(events)
                    if i > cursor
                    and e.get("event") == "step_started"
                    and e.get("step") == "upkeep"
                    and (e["turn"] - 1) % 2 == controller
                ]
                if matching_steps:
                    assert due and due[0][1]["step_cursor"] == matching_steps[0][0]
                else:
                    assert not due
                deliveries = [
                    (i, e)
                    for i, e in relevant
                    if e["event"] == "vigilante_delivered" and e["schedule_id"] == sid
                ]
                resolutions = [
                    (i, e)
                    for i, e in relevant
                    if e["event"] == "vigilante_resolved" and e["schedule_id"] == sid
                ]
                assert len(deliveries) <= 1 and len(resolutions) <= 1
                state = "pending"
                if due:
                    assert len(deliveries) == 1
                    dc, d = deliveries[0]
                    bc, b = due[0]
                    assert (
                        d["event_id"] == b["event_id"]
                        and d["controller"] == controller
                        and rc < bc < dc
                    )
                    pending_cursor, pending = unique(
                        "trigger_pending", "trigger_id", d["trigger_id"]
                    )
                    stacks = [
                        (i, e)
                        for i, e in enumerate(events)
                        if e.get("event") == "trigger_stacked"
                        and e.get("trigger_id") == d["trigger_id"]
                    ]
                    assert len(stacks) == 1
                    sc, stacked = stacks[0]
                    assert bc < pending_cursor < dc < sc
                    assert pending["event_id"] == stacked["event_id"] == d["event_id"]
                    assert (
                        pending["controller"]
                        == stacked["controller"]
                        == snapshot["players"][controller]["name"]
                    )
                    if not resolutions:
                        current = [
                            x
                            for x in snapshot["stack"]
                            if x["object_id"] == stacked["stack_object_id"]
                        ]
                        assert len(current) == 1
                        current = current[0]
                        assert (
                            current["controller"] == controller and current["source_id"] == source
                        )
                        assert (
                            current["event_id"] == d["event_id"]
                            and current["trigger_id"] == d["trigger_id"]
                        )
                        assert current["effect"] == "vigilante_discard"
                    state = "delivered"
                else:
                    assert not deliveries and not resolutions
                if resolutions:
                    assert deliveries
                    end, t = resolutions[0]
                    dc, d = deliveries[0]
                    assert t["event_id"] == d["event_id"] and t["trigger_id"] == d["trigger_id"]
                    assert (
                        t["controller"] == controller
                        and t["source_id"] == source
                        and t["consumed"] is True
                    )
                    assert t["oracle_fragment"] == CardInterpreter.VIGILANTE_FRAGMENT
                    pc, _ = lifecycle(
                        t["stack_object_id"],
                        t["trigger_id"],
                        t["event_id"],
                        controller,
                        source,
                        "vigilante_discard",
                        end,
                    )
                    assert pc < dc < end
                    hand = t["pre_hand_ids"]
                    assert hand == hand_at(t["start_event_cursor"], controller)
                    assert len(set(hand)) == len(hand)
                    rng = DeterministicRNG(0)
                    rng.restore_state(t["rng_state_before"])
                    assert rng.state_digest == t["rng_state_digest_before"]
                    assert t["rng_domain"] == f"vigilante:{sid}:{t['stack_object_id']}"
                    chosen = rng.shuffled(hand, domain=t["rng_domain"])[:3]
                    assert t["selected_ids"] == chosen and t["permutation"] == list(
                        rng.records[-1].result
                    )
                    assert t["rng_state_digest_after"] == rng.state_digest
                    rng_records = [
                        r for r in snapshot["rng"]["records"] if r["sequence"] == t["rng_sequence"]
                    ]
                    assert len(rng_records) == 1
                    rr = rng_records[0]
                    all_rng = snapshot["rng"]["records"]
                    assert [r["sequence"] for r in all_rng] == list(range(1, len(all_rng) + 1))
                    assert all(
                        a["state_after"] == b["state_before"]
                        for a, b in zip(all_rng, all_rng[1:], strict=False)
                    )
                    assert all_rng[-1]["state_after"] == snapshot["rng"]["state_digest"]
                    assert (
                        rr["operation"] == "shuffle"
                        and rr["domain"] == t["rng_domain"]
                        and rr["result"] == t["permutation"]
                    )
                    assert (
                        rr["state_before"] == t["rng_state_digest_before"]
                        and rr["state_after"] == t["rng_state_digest_after"]
                    )
                    moves = [
                        e
                        for e in events[t["start_event_cursor"] : end]
                        if e["event"] == "zone_changed"
                    ]
                    assert len(moves) == len(chosen)
                    assert t["movements"] == [
                        [e["source_object_id"], e["destination_object_id"]] for e in moves
                    ]
                    assert [e["source_object_id"] for e in moves] == chosen
                    assert all(
                        e["source_zone"] == "hand"
                        and e["destination_zone"] == "graveyard"
                        and e["reason"] == "vigilante_random_discard"
                        for e in moves
                    )
                    destinations = [e["destination_object_id"] for e in moves]
                    assert len(set(destinations + hand + t["pre_graveyard_ids"])) == len(
                        destinations + hand + t["pre_graveyard_ids"]
                    )
                    assert t["post_hand_ids"] == [i for i in hand if i not in chosen]
                    assert t["post_graveyard_ids"] == t["pre_graveyard_ids"] + destinations
                    state = "resolved"
                assert record["state"] == state and record["consumed"] is (state == "resolved")
                assert record["terminal_without_resolution"] is (
                    evidence["terminal_game"] and state != "resolved"
                )
            if "winner" in snapshot:
                assert evidence["terminal_game"] is (snapshot["winner"] is not None)
            ids = {r["schedule_id"] for r in records}
            assert all(
                e["schedule_id"] in ids
                for _, e in relevant
                if e["event"] in {"vigilante_delivered", "vigilante_resolved"}
            )
            for e in events:
                if e.get("event") == "trigger_resolved" and e.get("effect") in {
                    "etb_vigilante",
                    "vigilante_discard",
                }:
                    kind = (
                        "vigilante_scheduled"
                        if e["effect"] == "etb_vigilante"
                        else "vigilante_resolved"
                    )
                    unique(kind, "stack_object_id", e["stack_object_id"])
        except (
            AssertionError,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            StopIteration,
        ) as error:
            raise ValueError("Vigilante delayed-chain evidence does not reconstruct") from error
