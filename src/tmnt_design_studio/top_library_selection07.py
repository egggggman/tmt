"""Generic bounded top-library selection with hidden-information safeguards."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TopLibrarySelectionOption:
    card_id: str | None


@dataclass(frozen=True)
class TopLibrarySelectionView:
    controller: int
    # Only inspected cards are exposed, in top-first order.
    cards: tuple[tuple[str, str, str], ...]


class TopLibrarySelectionMixin:
    def _init_top_library_selection(self, chooser):
        self.top_library_selection_chooser = chooser or (lambda _view, options: options[0])
        self._top_library_selection_history: list[dict[str, object]] = []
        self._top_library_selection_active = False

    @staticmethod
    def _top_library_selection_eligible(obj, program) -> bool:
        if obj.is_token:
            return False
        types, _, subtypes = obj.card.type_line.partition(" — ")
        if "land" in program.eligible_types and "Land" in types.split():
            return True
        lowered = {part.casefold() for part in subtypes.split()}
        return bool(lowered.intersection(program.eligible_types))

    def _choose_top_library_selection(self, ability):
        from tmnt_design_studio.engine07 import CardObject

        program = self.interpreter.top_library_selection_program(ability.card)
        if program is None or not program.executable:
            raise ValueError("top-library selection has no executable program")
        player = self.players[ability.controller]
        library = tuple(player.library)
        if any(
            not isinstance(obj, CardObject)
            or obj.is_token
            or not self.is_authoritative(obj, "library")
            or obj.owner != ability.controller
            for obj in library
        ):
            raise ValueError("top-library selection library identity is invalid")
        inspected = tuple(reversed(library[-min(program.quantity, len(library)) :]))
        eligible = tuple(
            obj for obj in inspected if self._top_library_selection_eligible(obj, program)
        )
        options = tuple(TopLibrarySelectionOption(obj.object_id) for obj in eligible) + (
            TopLibrarySelectionOption(None),
        )
        view = TopLibrarySelectionView(
            ability.controller,
            tuple((obj.object_id, obj.card.name, obj.card.type_line) for obj in inspected),
        )
        self._top_library_selection_active = True
        try:
            choice = self.top_library_selection_chooser(view, options)
            if type(choice) is not TopLibrarySelectionOption or choice not in options:
                raise ValueError("top-library chooser must return a listed option")
            selected = next((obj for obj in eligible if obj.object_id == choice.card_id), None)
            before = [obj.object_id for obj in library]
            untouched = list(library[: -len(inspected)]) if inspected else list(library)
            remaining = [obj for obj in inspected if obj is not selected]
            selected_id = selected.object_id if selected is not None else None
            self.log(
                "top_library_selection_decided",
                stack_object_id=ability.object_id,
                controller=ability.controller,
                inspected_ids=[obj.object_id for obj in inspected],
                eligible_ids=[obj.object_id for obj in eligible],
                selected_id=selected_id,
                pre_library_ids=before,
            )
            hand_id = None
            if selected is not None:
                self.log(
                    "top_library_selection_revealed",
                    stack_object_id=ability.object_id,
                    controller=ability.controller,
                    library_object_id=selected.object_id,
                    card=selected.card.name,
                    type_line=selected.card.type_line,
                )
                hand_id = self.move_object(selected, "hand", reason="top_library_selection")
                hand_id = hand_id.object_id
            state = self.rng.export_state()
            domain = f"top_library_selection:{ability.object_id}"
            bottom = self.rng.shuffled(remaining, domain=domain)
            rng_record = self.rng.records[-1]
            replacement = bottom + untouched
            if len(replacement) != len(player.library) or {id(x) for x in replacement} != {
                id(x) for x in player.library
            }:
                raise ValueError("top-library selection changed library membership")
            player.library[:] = replacement
            self.log(
                "top_library_selection_bottom_ordered",
                stack_object_id=ability.object_id,
                input_ids=[obj.object_id for obj in remaining],
                output_ids=[obj.object_id for obj in bottom],
                domain=domain,
                rng_state_before=state,
                sequence=rng_record.sequence,
                state_before=rng_record.state_before,
                state_after=rng_record.state_after,
                permutation=list(rng_record.result),
            )
            committed = {
                "stack_object_id": ability.object_id,
                "controller": ability.controller,
                "selected_id": selected_id,
                "hand_id": hand_id,
                "post_library_ids": [obj.object_id for obj in player.library],
                "post_hand_ids": [obj.object_id for obj in player.hand],
            }
            self.log("top_library_selection_committed", **committed)
            self._top_library_selection_history.append(committed)
            return committed
        finally:
            self._top_library_selection_active = False

    def _resolve_top_library_selection(self, spell):
        return self._choose_top_library_selection(spell)
