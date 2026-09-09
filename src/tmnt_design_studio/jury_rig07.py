"""Exact Jury-Rig top-four artifact selection and random-bottom transaction."""

import json
from dataclasses import dataclass
from enum import Enum

from tmnt_design_studio.card_interpreter07 import CardInterpreter


@dataclass(frozen=True)
class JuryRigOption:
    card_id: str | None


@dataclass(frozen=True)
class JuryRigView:
    controller: int
    # Only the inspected cards, explicitly top-first. No live objects or lower library.
    cards: tuple[tuple[str, str, str], ...]


class JuryRigMixin:
    def _init_jury_rig(self, chooser):
        self.jury_rig_chooser = chooser or (lambda _view, options: options[0])
        self._jury_rig_sources = {}
        self._jury_rig_anchors = {}
        self._jury_rig_history = []
        self._jury_rig_consumed = set()
        self._jury_rig_choice_active = False
        self._jury_rig_rng = self.rng

    @staticmethod
    def _jury_rig_artifact(obj):
        from tmnt_design_studio.engine07 import CardObject

        return (
            isinstance(obj, CardObject)
            and not obj.is_token
            and "Artifact" in obj.card.type_line.split("\u2014", 1)[0].split()
        )

    def _check_jury_rig_history(self):
        if self.rng is not self._jury_rig_rng:
            raise ValueError("Jury-Rig RNG identity was relinked")
        committed = [e for e in self.events if e.get("event") == "jury_rig_committed"]
        if len(committed) != len(self._jury_rig_history):
            raise ValueError("Jury-Rig transaction ledger is incomplete")
        consumed = set()
        for start, encoded in self._jury_rig_history:
            values = json.loads(encoded)
            if json.dumps(self.events[start : start + len(values)], sort_keys=True) != encoded:
                raise ValueError("Jury-Rig original transaction evidence was altered")
            consumed.add(values[-1]["stack_object_id"])
        if consumed != self._jury_rig_consumed:
            raise ValueError("Jury-Rig consumed state was altered")
        for source_id, (source, card, event, _controller) in self._jury_rig_sources.items():
            self._authenticate_original_rules_event(event)
            if (
                self._objects.get(source_id) is not source
                or source.object_id != source_id
                or source.card is not card
            ):
                raise ValueError("Jury-Rig source identity was relinked")

    def _enqueue_jury_rig(self, event, source, fragment):
        from tmnt_design_studio.engine07 import RulesEventKind, TriggerEffect, TriggerInstance

        self._check_jury_rig_history()
        self._authenticate_original_rules_event(event)
        if (
            not self.is_authoritative(source, "battlefield")
            or event.kind is not RulesEventKind.CREATURE_ENTERED
            or event.subject_ids != (source.object_id,)
            or event.player_index != source.controller
            or (source.object_id, source.controller) not in event.battlefield_authority
            or fragment not in self.interpreter.fragments(source.card)
            or self.interpreter.jury_rig_semantic_coverage(source.card, fragment) is None
        ):
            raise ValueError("Jury-Rig entry provenance is invalid")
        if source.object_id in self._jury_rig_sources:
            original, card, _, _ = self._jury_rig_sources[source.object_id]
            if original is not source or card is not source.card:
                raise ValueError("Jury-Rig source was relinked")
            return
        self._jury_rig_sources[source.object_id] = (source, source.card, event, source.controller)
        occurrence = self._register_semantic_occurrence(source, source.controller, fragment, ())
        self._witness_from_existing_events(occurrence)
        trigger = TriggerInstance(
            f"trigger-{self._next_trigger_number:06d}",
            source.controller,
            source.object_id,
            source.card,
            fragment,
            TriggerEffect.ETB_JURY_RIG,
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

    def _anchor_jury_rig(self, ability, trigger):
        from tmnt_design_studio.engine07 import TriggerEffect

        if ability.effect is TriggerEffect.ETB_JURY_RIG:
            self._jury_rig_anchors[ability.object_id] = (ability, trigger, trigger.trigger_id)

    def _validate_jury_rig_trigger(self, ability):
        from tmnt_design_studio.engine07 import TriggerEffect

        self._check_jury_rig_history()
        anchor = self._jury_rig_anchors.get(ability.object_id)
        if anchor is None or anchor[0] is not ability:
            raise ValueError("Jury-Rig Stack identity is invalid")
        _, trigger, trigger_id = anchor
        source_anchor = self._jury_rig_sources.get(ability.source_id)
        if source_anchor is None:
            raise ValueError("Jury-Rig source provenance is invalid")
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
            or ability.effect is not TriggerEffect.ETB_JURY_RIG
            or trigger.effect is not TriggerEffect.ETB_JURY_RIG
            or ability.oracle_fragment != CardInterpreter.JURY_RIG_FRAGMENT
            or trigger.oracle_fragment != CardInterpreter.JURY_RIG_FRAGMENT
            or ability.object_id in self._jury_rig_consumed
        ):
            raise ValueError("Jury-Rig trigger provenance is invalid or consumed")
        if not self._priority_resolution_in_progress and (
            self.priority_state is None or not self.priority_state.resolution_pending
        ):
            raise ValueError("Jury-Rig requires all-pass Priority")

    def _choose_jury_rig(self, ability):
        from tmnt_design_studio.engine07 import CardObject

        library = tuple(self.players[ability.controller].library)
        if any(
            not isinstance(obj, CardObject)
            or obj.is_token
            or not self.is_authoritative(obj, "library")
            or obj.owner != ability.controller
            for obj in library
        ):
            raise ValueError("Jury-Rig library identity is invalid")
        n = min(4, len(library))
        inspected = tuple(reversed(library[-n:])) if n else ()
        options = tuple(
            JuryRigOption(obj.object_id) for obj in inspected if self._jury_rig_artifact(obj)
        ) + (JuryRigOption(None),)
        view = JuryRigView(
            ability.controller,
            tuple((obj.object_id, obj.card.name, obj.card.type_line) for obj in inspected),
        )
        # Local callback guard: preserve the existing Game state graph and object identities.
        # This is not a public chooser framework or a sandbox for arbitrary Python code.
        self._jury_rig_choice_active = True
        nodes = []
        seen = set()

        def capture(value):
            if id(value) in seen:
                return
            seen.add(id(value))
            if isinstance(value, dict):
                items = tuple(value.items())
                nodes.append(("dict", value, items))
                for key, child in items:
                    capture(key)
                    capture(child)
            elif isinstance(value, list):
                nodes.append(("list", value, tuple(value)))
                for child in value:
                    capture(child)
            elif isinstance(value, set):
                nodes.append(("set", value, set(value)))
                for child in value:
                    capture(child)
            elif isinstance(value, tuple):
                for child in value:
                    capture(child)
            elif (
                not isinstance(value, (type, Enum))
                and not callable(value)
                and type(value).__module__.startswith("tmnt_design_studio")
                and hasattr(value, "__dict__")
            ):
                nodes.append(("attrs", value, vars(value)))
                capture(vars(value))

        capture(self)
        random_object = self.rng._random
        random_state = random_object.getstate()
        try:
            choice = self.jury_rig_chooser(view, options)
            if type(choice) is not JuryRigOption or choice not in options:
                raise ValueError("Jury-Rig chooser must return a listed option")
            for kind, obj, original in nodes:
                if kind == "dict":
                    valid = len(obj) == len(original) and all(
                        key in obj and obj[key] is value for key, value in original
                    )
                elif kind == "list":
                    valid = len(obj) == len(original) and all(
                        a is b for a, b in zip(obj, original, strict=True)
                    )
                elif kind == "set":
                    valid = obj == original
                else:
                    valid = vars(obj) is original
                if not valid:
                    raise ValueError("Jury-Rig chooser mutated authoritative state")
            if random_object.getstate() != random_state:
                raise ValueError("Jury-Rig chooser mutated RNG state")
            self._validate_jury_rig_trigger(ability)
        except Exception:
            for kind, obj, original in nodes:
                if kind == "dict":
                    obj.clear()
                    obj.update(original)
                elif kind == "list":
                    obj[:] = original
                elif kind == "set":
                    obj.clear()
                    obj.update(original)
                else:
                    object.__setattr__(obj, "__dict__", original)
            random_object.setstate(random_state)
            raise
        finally:
            self._jury_rig_choice_active = False
        return library, inspected, choice

    def _resolve_jury_rig(self, ability):
        self._validate_jury_rig_trigger(ability)
        if ability.zone != "former":
            raise ValueError("Jury-Rig requires Stack resolution")
        library, inspected, choice = self._choose_jury_rig(ability)
        player = self.players[ability.controller]
        selected = next((obj for obj in inspected if obj.object_id == choice.card_id), None)
        untouched = library[: -len(inspected)] if inspected else library
        remaining = [obj for obj in inspected if obj is not selected]
        start = len(self.events)
        pre_hand = [obj.object_id for obj in player.hand]
        self.log(
            "jury_rig_decided",
            stack_object_id=ability.object_id,
            controller=ability.controller,
            library=[
                {
                    "object_id": obj.object_id,
                    "name": obj.card.name,
                    "type_line": obj.card.type_line,
                    "owner": obj.owner,
                    "is_token": obj.is_token,
                }
                for obj in library
            ],
            inspected_ids=[obj.object_id for obj in inspected],
            eligible_ids=[obj.object_id for obj in inspected if self._jury_rig_artifact(obj)],
            selected_id=choice.card_id,
            pre_hand_ids=pre_hand,
        )
        hand_id = None
        if selected is not None:
            self.log(
                "jury_rig_revealed",
                stack_object_id=ability.object_id,
                controller=ability.controller,
                library_object_id=selected.object_id,
                card=selected.card.name,
                type_line=selected.card.type_line,
            )
            moved = self.move_object(selected, "hand", reason="jury_rig_selection")
            hand_id = moved.object_id
        state = self.rng.export_state()
        domain = f"jury_rig:{ability.object_id}"
        bottom = self.rng.shuffled(list(remaining), domain=domain)
        rng = self.rng.records[-1]
        replacement = bottom + list(untouched)
        if len(replacement) != len(player.library) or {id(obj) for obj in replacement} != {
            id(obj) for obj in player.library
        }:
            raise ValueError("Jury-Rig reorder changed library membership")
        player.library[:] = replacement
        self.log(
            "jury_rig_bottom_ordered",
            stack_object_id=ability.object_id,
            input_ids=[obj.object_id for obj in remaining],
            output_ids=[obj.object_id for obj in bottom],
            rng_state_before=state,
            domain=domain,
            sequence=rng.sequence,
            state_before=rng.state_before,
            state_after=rng.state_after,
            permutation=list(rng.result),
        )
        self.log(
            "jury_rig_committed",
            event_id=ability.event.event_id,
            trigger_id=ability.trigger_id,
            stack_object_id=ability.object_id,
            source_id=ability.source_id,
            controller=ability.controller,
            oracle_fragment=ability.oracle_fragment,
            start_event_cursor=start,
            selected_id=choice.card_id,
            hand_id=hand_id,
            untouched_ids=[obj.object_id for obj in untouched],
            post_library_ids=[obj.object_id for obj in player.library],
            post_hand_ids=[obj.object_id for obj in player.hand],
        )
        self._jury_rig_consumed.add(ability.object_id)
        self._jury_rig_history.append((start, json.dumps(self.events[start:], sort_keys=True)))

    def jury_rig_snapshot_evidence(self):
        self._check_jury_rig_history()
        return [
            {"start": start, "events": json.loads(encoded)}
            for start, encoded in self._jury_rig_history
        ]

    @staticmethod
    def validate_jury_rig_snapshot_evidence(snapshot):
        from tmnt_design_studio.engine07 import DeterministicRNG

        events = snapshot.get("events", [])
        commits = [(i, e) for i, e in enumerate(events) if e.get("event") == "jury_rig_committed"]
        resolved = [
            e
            for e in events
            if e.get("event") == "trigger_resolved" and e.get("effect") == "etb_jury_rig"
        ]
        if not commits and not resolved and snapshot.get("jury_rig_evidence") is None:
            return
        try:
            ledger = snapshot["jury_rig_evidence"]
            assert isinstance(ledger, list) and len(ledger) == len(commits) == len(resolved)
            seen = set()

            def unique(kind, key, value):
                found = [
                    (i, e)
                    for i, e in enumerate(events)
                    if e.get("event") == kind and e.get(key) == value
                ]
                assert len(found) == 1
                return found[0]

            for original, (cursor, commit) in zip(ledger, commits, strict=True):
                start = commit["start_event_cursor"]
                assert type(start) is int and 0 <= start < cursor and original["start"] == start
                assert json.dumps(original["events"], sort_keys=True) == json.dumps(
                    events[start : cursor + 1], sort_keys=True
                )
                stack_id = commit["stack_object_id"]
                controller = commit["controller"]
                source_id = commit["source_id"]
                assert stack_id not in seen and controller in (0, 1)
                seen.add(stack_id)
                fragment = CardInterpreter.JURY_RIG_FRAGMENT
                assert commit["oracle_fragment"] == fragment
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
                evidence = originals[0]
                assert (
                    evidence["kind"] == "creature_entered"
                    and evidence["player_index"] == controller
                )
                for key in (
                    "source_id",
                    "subject_ids",
                    "battlefield_authority",
                    "battlefield_characteristics",
                ):
                    assert evidence[key] == entry[key]
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
                    resolution["effect"] == "etb_jury_rig" and resolution["source_id"] == source_id
                )
                name = snapshot["players"][controller]["name"]
                assert pending["controller"] == stacked["controller"] == entry["player"] == name
                passes = [
                    e
                    for e in events[sc:ac]
                    if e.get("event") == "priority_passed"
                    and e.get("priority_epoch") == permission["priority_epoch"]
                ]
                assert len(passes) >= 2 and passes[-1]["resolution_pending"] is True
                assert {passes[-1]["player_index"], passes[-2]["player_index"]} == {0, 1}
                steps = events[start:cursor]
                decision = steps[0]
                assert (
                    decision["event"] == "jury_rig_decided"
                    and decision["stack_object_id"] == stack_id
                    and decision["controller"] == controller
                )
                library = decision["library"]
                ids = [o["object_id"] for o in library]
                n = min(4, len(ids))
                assert len(set(ids + decision["pre_hand_ids"])) == len(
                    ids + decision["pre_hand_ids"]
                )
                assert all(o["owner"] == controller and o["is_token"] is False for o in library)
                inspected = list(reversed(library[-n:])) if n else []
                inspected_ids = [o["object_id"] for o in inspected]
                eligible = [
                    o["object_id"]
                    for o in inspected
                    if "Artifact" in o["type_line"].split("\u2014", 1)[0].split()
                ]
                assert (
                    decision["inspected_ids"] == inspected_ids
                    and decision["eligible_ids"] == eligible
                )
                selected = commit["selected_id"]
                hand_id = commit["hand_id"]
                assert decision["selected_id"] == selected and (
                    selected is None or selected in eligible
                )
                reveals = [e for e in steps if e["event"] == "jury_rig_revealed"]
                moves = [e for e in steps if e["event"] == "zone_changed"]
                if selected is None:
                    assert hand_id is None and not reveals and not moves
                    assert commit["post_hand_ids"] == decision["pre_hand_ids"]
                else:
                    assert len(reveals) == len(moves) == 1
                    reveal, move = reveals[0], moves[0]
                    card = next(o for o in inspected if o["object_id"] == selected)
                    assert (
                        reveal["stack_object_id"] == stack_id and reveal["controller"] == controller
                    )
                    assert (
                        reveal["library_object_id"] == selected
                        and reveal["card"] == card["name"]
                        and reveal["type_line"] == card["type_line"]
                    )
                    assert (
                        move["source_object_id"] == selected
                        and move["destination_object_id"] == hand_id
                    )
                    assert (
                        move["source_zone"] == "library"
                        and move["destination_zone"] == "hand"
                        and move["reason"] == "jury_rig_selection"
                    )
                    assert move["owner"] == name and move["card"] == card["name"]
                    assert hand_id not in ids + decision["pre_hand_ids"] and isinstance(
                        hand_id, str
                    )
                    assert commit["post_hand_ids"] == decision["pre_hand_ids"] + [hand_id]
                    assert steps.index(reveal) < steps.index(move)
                ordered = [e for e in steps if e["event"] == "jury_rig_bottom_ordered"]
                assert len(ordered) == 1
                order = ordered[0]
                assert steps[-1] is order
                assert [e["event"] for e in steps] == (
                    [
                        "jury_rig_decided",
                        "jury_rig_revealed",
                        "zone_changed",
                        "jury_rig_bottom_ordered",
                    ]
                    if selected is not None
                    else ["jury_rig_decided", "jury_rig_bottom_ordered"]
                )
                assert (
                    order["stack_object_id"] == stack_id
                    and order["domain"] == f"jury_rig:{stack_id}"
                )
                remaining = [i for i in inspected_ids if i != selected]
                assert order["input_ids"] == remaining
                rng = DeterministicRNG(0)
                rng.restore_state(order["rng_state_before"])
                assert rng.state_digest == order["state_before"]
                output = rng.shuffled(remaining, domain=order["domain"])
                assert order["output_ids"] == output and order["permutation"] == list(
                    rng.records[-1].result
                )
                assert order["state_after"] == rng.state_digest
                records = snapshot["rng"]["records"]
                assert [r["sequence"] for r in records] == list(range(1, len(records) + 1))
                assert all(
                    a["state_after"] == b["state_before"]
                    for a, b in zip(records, records[1:], strict=False)
                )
                assert records[-1]["state_after"] == snapshot["rng"]["state_digest"]
                matching = [r for r in records if r["sequence"] == order["sequence"]]
                assert len(matching) == 1
                record = matching[0]
                assert record["operation"] == "shuffle" and record["domain"] == order["domain"]
                assert (
                    record["state_before"] == order["state_before"]
                    and record["state_after"] == order["state_after"]
                    and record["result"] == order["permutation"]
                )
                prefix = ids[:-n] if n else ids
                assert (
                    commit["untouched_ids"] == prefix
                    and commit["post_library_ids"] == output + prefix
                )
                assert (
                    len(set(commit["post_library_ids"]))
                    == len(commit["post_library_ids"])
                    == len(ids) - (selected is not None)
                )
                assert set(commit["post_library_ids"]) == set(ids) - (
                    {selected} if selected is not None else set()
                )
                # Hand membership/order has an independent authoritative zone-movement history.
                prior_hand = []
                for e in events[:start]:
                    if e.get("event") != "zone_changed" or e.get("owner") != name:
                        continue
                    if e["source_zone"] == "hand":
                        prior_hand.remove(e["source_object_id"])
                    if e["destination_zone"] == "hand":
                        prior_hand.append(e["destination_object_id"])
                assert prior_hand == decision["pre_hand_ids"]
            relevant = [
                i for i, e in enumerate(events) if e.get("event", "").startswith("jury_rig_")
            ]
            covered = {
                i
                for (cursor, commit) in commits
                for i in range(commit["start_event_cursor"], cursor + 1)
            }
            assert all(i in covered for i in relevant)
        except (
            AssertionError,
            KeyError,
            TypeError,
            ValueError,
            IndexError,
            StopIteration,
        ) as error:
            raise ValueError("Jury-Rig transaction evidence does not reconstruct") from error
