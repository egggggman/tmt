"""Bounded generic static-team semantics required by Krang R6-B."""

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, Game, TurnStep
from tmnt_design_studio.stage002 import _semantic_coverage, load_catalog
from tools.run_objective_balance_lab_round1 import catalog, game_metrics
from tools.validate_chrome_dome_r6b_readiness import validate as validate_readiness

ROOT = Path(__file__).resolve().parents[1]
CARD = load_catalog(ROOT).resolve_name("Chrome Dome")
CHROME = CardFact(
    CARD.name,
    CARD.mana_cost,
    int(CARD.mana_value),
    CARD.type_line,
    CARD.oracle_text,
    power=int(CARD.power),
    toughness=int(CARD.toughness),
)
BOT = CardFact("Fixture Bot", "{2}", 2, "Artifact Creature — Robot", power=2, toughness=2)
BEAR = CardFact("Fixture Bear", "{2}", 2, "Creature — Bear", power=2, toughness=2)
BLOCKER = CardFact("Fixture Blocker", "{2}", 2, "Creature — Bear", power=2, toughness=3)
LAND = CardFact("Plains", "", 0, "Basic Land — Plains")


def game() -> Game:
    return Game(([LAND] * 30 + [BOT] * 30, [LAND] * 30 + [BEAR] * 30), seed=7)


def enter(current: Game, card: CardFact, controller: int):
    permanent = current.create_permanent(card, controller, summoning_sick=False)
    current.place_on_battlefield(permanent)
    current.refresh_static_pt_modifiers()
    return permanent


def changes(current: Game) -> list[dict]:
    return [e for e in current.events if e["event"] == "pt_static_team_modifier_changed"]


def test_frozen_chrome_dome_clause_and_partial_interpreter_coverage():
    assert CARD.mana_cost == "{2}"
    assert CARD.type_line == "Artifact Creature — Robot Ninja"
    assert (CARD.power, CARD.toughness) == ("1", "3")
    assert CARD.legalities["standard"] == "legal"
    assert CARD.oracle_text == (
        "Other artifact creatures you control get +1/+0.\n"
        "{5}: Create a token that's a copy of another target artifact you control. "
        "That token gains haste. Sacrifice it at the beginning of the next end step."
    )
    interpreter = CardInterpreter()
    clause, copy_ability = interpreter.fragments(CHROME)
    interpreted = interpreter.static_team_modifier_semantic_coverage(CHROME, clause)
    assert interpreted is not None and interpreted.coverage.fully_supported
    assert (
        interpreted.program.quality,
        interpreted.program.power,
        interpreted.program.toughness,
    ) == ("artifact", 1, 0)
    assert interpreted.program.other
    clause_coverage = _semantic_coverage(interpreter, CHROME, clause, ())
    assert clause_coverage["family"] == "static_team_modifier"
    assert clause_coverage["fully_supported"]
    assert not interpreter.supports_pt_fragment(copy_ability)
    unsupported = interpreter.unsupported_fragments(CHROME)
    assert all(fragment != clause for fragment, _reason in unsupported)
    assert any(fragment == copy_ability for fragment, _reason in unsupported)
    assert any(reason == "token_copy_not_implemented" for _fragment, reason in unsupported)
    copy_limitations = tuple(reason for fragment, reason in unsupported if fragment == copy_ability)
    assert not _semantic_coverage(interpreter, CHROME, copy_ability, copy_limitations)[
        "fully_supported"
    ]


def test_r6b_readiness_fingerprint_and_candidate_identity():
    # R6-B's execution gate must reject the new Aura runtime, preserving its old evidence.
    with pytest.raises(AssertionError):
        validate_readiness()


def test_controller_other_artifact_filter_and_no_op_refresh_are_deterministic():
    current = game()
    source = enter(current, CHROME, 0)
    first = enter(current, BOT, 0)
    second = enter(current, BOT, 0)
    ordinary = enter(current, BEAR, 0)
    opponent = enter(current, BOT, 1)
    assert (source.power, source.toughness) == (1, 3)
    assert (first.power, first.toughness) == (second.power, second.toughness) == (3, 2)
    assert (ordinary.power, ordinary.toughness) == (opponent.power, opponent.toughness) == (2, 2)
    applied = changes(current)
    assert len(applied) == 2
    assert {event["target_object_id"] for event in applied} == {first.object_id, second.object_id}
    assert all(
        event["source_object_id"] == source.object_id
        and event["power_delta"] == 1
        and event["toughness_delta"] == 0
        and event["action"] == "applied"
        for event in applied
    )
    assert [event["qualifying_targets"] for event in applied] == [1, 2]
    before = list(applied)
    current.refresh_static_pt_modifiers()
    current.refresh_static_pt_modifiers()
    assert changes(current) == before
    assert (first.power, second.power) == (3, 3)


def test_source_exit_reentry_and_target_entry_exit_refresh_without_stale_modifiers():
    current = game()
    source = enter(current, CHROME, 0)
    first = enter(current, BOT, 0)
    assert first.power == 3
    current.put_into_graveyard(source)
    assert first.power == 2
    assert changes(current)[-1]["action"] == "removed"
    assert changes(current)[-1]["source_object_id"] == source.object_id
    replacement = enter(current, CHROME, 0)
    assert replacement.object_id != source.object_id
    assert first.power == 3
    second = enter(current, BOT, 0)
    assert second.power == 3
    first.type_line_override = "Creature — Robot"
    current.refresh_static_pt_modifiers()
    assert first.power == 2 and second.power == 3
    assert changes(current)[-1]["target_object_id"] == first.object_id
    assert changes(current)[-1]["power_delta"] == -1
    current.put_into_graveyard(second)
    assert all(
        modifier.source_object_id != replacement.object_id for modifier in first.pt_modifiers
    )
    assert any(
        event["target_object_id"] == second.object_id and event["action"] == "removed"
        for event in changes(current)
    )


def test_two_chrome_domes_modify_each_other_and_stack_for_other_artifacts():
    current = game()
    first = enter(current, CHROME, 0)
    second = enter(current, CHROME, 0)
    bot = enter(current, BOT, 0)
    assert (first.power, first.toughness) == (second.power, second.toughness) == (2, 3)
    assert (bot.power, bot.toughness) == (4, 2)
    assert {modifier.source_object_id for modifier in bot.pt_modifiers} == {
        first.object_id,
        second.object_id,
    }
    assert all(
        modifier.source_object_id != permanent.object_id
        for permanent in (first, second)
        for modifier in permanent.pt_modifiers
    )
    current.refresh_static_pt_modifiers()
    assert (first.power, second.power, bot.power) == (2, 2, 4)
    current.put_into_graveyard(first)
    assert (second.power, bot.power) == (1, 3)


def test_static_team_modifier_uses_generic_oracle_values_not_card_identity():
    source_card = CardFact(
        "Fixture Foundry",
        "{3}",
        3,
        "Artifact",
        "Other artifact creatures you control get +2/+1.",
    )
    current = game()
    enter(current, source_card, 0)
    bot = enter(current, BOT, 0)
    assert (bot.power, bot.toughness) == (4, 3)
    assert [(event["power_delta"], event["toughness_delta"]) for event in changes(current)] == [
        (2, 1)
    ]


def test_existing_per_other_creature_static_effect_keeps_its_own_refresh_accounting():
    captain = CardFact(
        "Captain Bot",
        "{2}",
        2,
        "Artifact Creature — Robot",
        "Captain Bot gets +1/+0 for each other creature you control.",
        power=1,
        toughness=3,
    )
    current = game()
    enter(current, CHROME, 0)
    source = enter(current, captain, 0)
    enter(current, BEAR, 0)
    assert source.power == 4  # printed 1, two other creatures, Chrome +1
    own_events = [e for e in current.events if e["event"] == "pt_static_modifier_refreshed"]
    team_events = list(changes(current))
    current.refresh_static_pt_modifiers()
    current.refresh_static_pt_modifiers()
    assert source.power == 4
    assert [e for e in current.events if e["event"] == "pt_static_modifier_refreshed"] == own_events
    assert changes(current) == team_events


def test_static_change_telemetry_is_deterministic_without_noop_events():
    def trace() -> list[dict]:
        current = game()
        source = enter(current, CHROME, 0)
        enter(current, BOT, 0)
        current.refresh_static_pt_modifiers()
        current.put_into_graveyard(source)
        return changes(current)

    assert trace() == trace()
    assert [event["action"] for event in trace()] == ["applied", "removed"]


def test_obl_game_metrics_retains_generic_static_and_source_zone_telemetry():
    current = game()
    source = enter(current, CHROME, 0)
    target = enter(current, BOT, 0)
    current.refresh_static_pt_modifiers()
    current.put_into_graveyard(source)
    metrics = game_metrics(current.snapshot(), ("krang", "shredder"), catalog())
    changes = metrics["static_modifier_changes"]
    assert [(event["action"], event["power_delta"]) for event in changes] == [
        ("applied", 1),
        ("removed", -1),
    ]
    assert all(event["target_object_id"] == target.object_id for event in changes)
    zones = metrics["static_source_zone_changes"]
    assert [(event["source_zone"], event["destination_zone"]) for event in zones] == [
        ("battlefield", "graveyard")
    ]
    assert zones[0]["source_object_id"] == source.object_id


def test_cast_uses_generic_static_path_and_existing_cast_entry_telemetry():
    current = game()
    current.begin_turn()
    bot = enter(current, BOT, 0)
    enter(current, LAND, 0)
    enter(current, LAND, 0)
    current.players[0].hand = current.set_hand_for_testing(0, [CHROME])
    assert current.cast(0, current.players[0].hand[0])
    source = next(p for p in current.players[0].battlefield if p.card.name == "Chrome Dome")
    assert (source.power, source.toughness) == (1, 3)
    assert bot.power == 3
    assert any(
        event["event"] == "spell_cast" and event["card"] == "Chrome Dome"
        for event in current.events
    )
    assert any(
        event["event"] == "permanent_resolved" and event["card"] == "Chrome Dome"
        for event in current.events
    )
    assert any(event["target_object_id"] == bot.object_id for event in changes(current))
    metrics = game_metrics(current.snapshot(), ("krang", "shredder"), catalog())
    assert any(
        event["card"] == "Chrome Dome" and event["destination_zone"] == "battlefield"
        for event in metrics["static_source_zone_changes"]
    )


def test_persistent_temporary_counters_sba_and_combat_use_layered_power():
    current = game()
    current.begin_turn()
    enter(current, CHROME, 0)
    bot = enter(current, BOT, 0)
    current.place_counters(bot, "+1/+1", 1, source_card="Fixture", oracle_fragment="Counter")
    current.apply_pt_modifier(
        bot, 2, 0, duration="until_end_of_turn", source_card="Fixture", oracle_fragment="Temporary"
    )
    assert (bot.power, bot.toughness) == (6, 3)
    current.refresh_static_pt_modifiers()
    assert (bot.power, bot.toughness) == (6, 3)
    current.end_turn()
    assert (bot.power, bot.toughness) == (4, 3)

    @dataclass
    class PowerWitness:
        name: str = "power_witness"
        seen: list[int] = field(default_factory=list)

        def apply(self, _game: Game) -> bool:
            self.seen.append(bot.power)
            return False

    witness = PowerWitness()
    current.state_based_actions = (witness,)
    current.check_state_based_actions()
    assert witness.seen == [4]

    combat = game()
    combat.begin_turn()
    source = enter(combat, CHROME, 0)
    attacker = enter(combat, BOT, 0)
    blocker = enter(combat, BLOCKER, 1)
    combat.advance_to(TurnStep.DECLARE_ATTACKERS)
    combat.combat([source, attacker], {attacker.object_id: blocker})
    assert any(card.name == BLOCKER.name for card in combat.players[1].graveyard)
    assert any(card.name == BOT.name for card in combat.players[0].graveyard)
