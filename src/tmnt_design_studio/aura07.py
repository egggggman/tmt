"""Creature-Aura attachment and source-bound continuous suppression (CR 303/613)."""

from __future__ import annotations

import re


class AuraMixin:
    def _effect_timestamp(self):
        timestamp = (self.turn, self._next_effect_number)
        self._next_effect_number += 1
        return timestamp

    def legal_aura_target(self, card, target, controller, *, targeted=True):
        from tmnt_design_studio.engine07 import Permanent

        if (
            self.interpreter.aura_program(card) is None
            or not isinstance(target, Permanent)
            or not self.is_authoritative(target, "battlefield")
            or not target.is_creature
        ):
            return False
        text = " ".join((*target.rules_card.keywords, target.rules_card.oracle_text))
        # Refuse unrepresented targeting/attachment dependencies, as the stun path does.
        if re.search(r"\bprotection\b|can't be enchanted", text, re.I):
            raise ValueError("Aura attachment dependency is not implemented")
        if targeted:
            if re.search(r"\bward\b|can't be (?:the )?target", text, re.I):
                raise ValueError("Aura targeting dependency is not implemented")
            if re.search(r"\bshroud\b", text, re.I):
                return False
            if target.controller != controller and re.search(r"\bhexproof\b", text, re.I):
                return False
        return True

    def attach_aura(self, aura, target):
        """Attach or move an existing Aura; invalid requests are mutation-free."""
        if (
            not self.is_authoritative(aura, "battlefield")
            or aura.is_creature
            or aura is target
            or not self.legal_aura_target(aura.card, target, aura.controller, targeted=False)
        ):
            raise ValueError("illegal Aura attachment")
        if aura.attached_to == target.object_id:
            return
        previous = aura.attached_to
        aura.attached_to = target.object_id
        aura.attachment_timestamp = self._effect_timestamp()
        self.refresh_static_pt_modifiers()
        self.log(
            "aura_attached",
            card=aura.card.name,
            source_id=aura.object_id,
            controller=aura.controller,
            target_id=target.object_id,
            target=target.card.name,
            previous_target_id=previous,
            timestamp=list(aura.attachment_timestamp),
            power=target.power,
            toughness=target.toughness,
            type_line=target.type_line,
            abilities_removed=target.ability_loss_timestamp is not None,
            cant_attack=bool(target.aura_attack_restrictions),
        )

    def refresh_aura_effects(self):
        """Rebuild layers 4, 6 and 7b from live Aura/source/target incarnations."""
        from tmnt_design_studio.engine07 import (
            CharacteristicEffect,
            CharacteristicLayer,
            CharacteristicOperation,
            PowerToughnessSubLayer,
        )

        permanents = [p for player in self.players for p in player.battlefield]
        before = {
            p.object_id: (
                p.aura_creature_type,
                p.ability_loss_timestamp,
                p.aura_attack_restrictions,
                tuple(p.aura_effect_ids),
            )
            for p in permanents
        }
        for target in permanents:
            target.characteristic_effects = [
                e
                for e in target.characteristic_effects
                if e.effect_id not in target.aura_effect_ids
            ]
            target.aura_effect_ids = ()
            target.aura_creature_type = None
            target.ability_loss_timestamp = None
            target.aura_attack_restrictions = ()
        for aura in sorted(permanents, key=lambda p: (p.attachment_timestamp, p.object_id)):
            program = self.interpreter.aura_program(aura.card)
            target = self._objects.get(aura.attached_to or "")
            if (
                program is None
                or aura.is_creature
                or not self.legal_aura_target(aura.card, target, aura.controller, targeted=False)
            ):
                continue
            target.aura_creature_type = program.creature_type
            if program.loses_abilities:
                target.ability_loss_timestamp = aura.attachment_timestamp
            if program.cant_attack:
                target.aura_attack_restrictions += ((aura.object_id, program.oracle_fragment),)
            effect_id = f"aura:{aura.object_id}:base_pt"
            target.aura_effect_ids += (effect_id,)
            target.characteristic_effects.append(
                CharacteristicEffect(
                    effect_id,
                    CharacteristicLayer.POWER_TOUGHNESS,
                    PowerToughnessSubLayer.SET_BASE,
                    CharacteristicOperation.SET,
                    program.power,
                    program.toughness,
                    aura.attachment_timestamp,
                    source_card=aura.card.name,
                )
            )
        for target in permanents:
            after = (
                target.aura_creature_type,
                target.ability_loss_timestamp,
                target.aura_attack_restrictions,
                tuple(target.aura_effect_ids),
            )
            if before[target.object_id] != after:
                self.log(
                    "aura_effects_recalculated",
                    target_id=target.object_id,
                    target=target.card.name,
                    type_line=target.type_line,
                    power=target.power if target.is_creature else None,
                    toughness=target.toughness if target.is_creature else None,
                    abilities_removed=target.ability_loss_timestamp is not None,
                    cant_attack=bool(target.aura_attack_restrictions),
                    source_ids=[source for source, _ in target.aura_attack_restrictions],
                )

    def aura_state_based_actions(self):
        invalid = tuple(
            aura
            for player in self.players
            for aura in player.battlefield
            if self.interpreter.aura_program(aura.card) is not None
            and (
                aura.is_creature
                or aura.attached_to == aura.object_id
                or not self.legal_aura_target(
                    aura.card,
                    self._objects.get(aura.attached_to or ""),
                    aura.controller,
                    targeted=False,
                )
            )
        )
        if invalid:
            self.put_permanents_into_graveyard(invalid, state_based_action="illegal_aura")
        return bool(invalid)

    def _aura_cast_options(self, player_index, *, priority=False):
        from tmnt_design_studio.engine07 import ActionKind, ActionOption

        options = []
        for card in self.players[player_index].hand:
            program = self.interpreter.aura_program(card.card)
            if program is None or self.payment_plan(player_index, card) is None:
                continue
            if priority and "Flash" not in self.interpreter.fragments(card.card):
                continue
            for player in self.players:
                for target in player.battlefield:
                    if self.legal_aura_target(card.card, target, player_index):
                        options.append(
                            ActionOption(
                                ActionKind.CAST,
                                player_index,
                                object_id=card.object_id,
                                target_id=target.object_id,
                                oracle_fragment=program.oracle_fragment,
                                priority_epoch=self.priority_state.epoch if priority else None,
                            )
                        )
        return tuple(options)
