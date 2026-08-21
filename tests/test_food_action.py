import hashlib
import inspect
import json
from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import (
    ActivatedEffectKind,
    CardInterpreter,
    TokenCreationProgram,
)
from tmnt_design_studio.engine07 import (
    ActionKind,
    ActivatedAbilityObject,
    CardFact,
    Game,
    Permanent,
)

ROOT = Path(__file__).resolve().parents[1]
LAND = CardFact("Plains", "", 0, "Basic Land — Plains", "({T}: Add {W}.)")
CANONICAL = CardInterpreter.CANONICAL_FOOD_ACTIVATION


def catalog():
    return load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )


def setup_food(*, mana=2, tapped=False, controller=0, token=True):
    current = Game(([LAND] * 40, [LAND] * 40), seed=1201)
    current.begin_turn()
    for _ in range(mana):
        current.create_permanent(LAND, 0, summoning_sick=False)
    if token:
        program = TokenCreationProgram(CardInterpreter.PREDEFINED_TOKENS["food"], 1)
        source = current.create_tokens(
            0,
            program,
            controller=controller,
            source_card="Anonymous creator",
            oracle_fragment="Create a Food token.",
        )[0]
    else:
        source = current.create_permanent(
            CardFact("Anonymous Provision", "", 0, "Artifact — Food", CANONICAL),
            0,
            controller=controller,
            summoning_sick=False,
        )
    source.tapped = tapped
    return current, source


def activation_option(current, player=0):
    return next(
        option
        for option in current.legal_main_actions(player)
        if option.kind is ActionKind.ACTIVATE_ABILITY
    )


def pass_and_resolve(current):
    while current.priority_state is not None:
        if current.priority_state.resolution_pending:
            current.process_priority_resolution()
        else:
            option = current.legal_priority_actions(current.priority_state.player_index)[0]
            current.execute_priority_action(option)


def coverage_sets():
    interpreter = CardInterpreter()
    recognized = []
    executable = []
    full = []
    seen = set()
    for card in sorted(catalog().cards, key=lambda item: (item.name, item.oracle_id)):
        if card.oracle_id in seen:
            continue
        seen.add(card.oracle_id)
        for fragment in interpreter.fragments(card):
            semantics = interpreter.food_activation_semantic_coverage(card, fragment)
            if semantics is None:
                continue
            member = (card.oracle_id, card.name, fragment)
            recognized.append(member)
            if semantics.coverage.payload_executable:
                executable.append(member)
            if semantics.coverage.fully_supported:
                full.append(member)
    return recognized, executable, full


def digest(members):
    encoded = json.dumps(members, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def frozen_names():
    roster = json.loads((ROOT / "cardcade/roster-0.2.json").read_text(encoding="utf-8"))
    names = set()
    for deck in roster["decks"]:
        for line in (ROOT / deck["decklist"]).read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped[:1].isdigit() and " " in stripped:
                names.add(stripped.split(" ", 1)[1])
    return names


def test_canonical_food_is_oracle_derived_and_card_name_independent():
    renamed = CardFact("Anonymous Provision", "", 0, "Artifact — Food", CANONICAL)
    semantics = CardInterpreter().activated_ability_semantics(renamed, CANONICAL)

    assert semantics is not None and semantics.coverage.fully_supported
    assert semantics.program.cost.mana_cost == "{2}"
    assert semantics.program.cost.tap_source
    assert semantics.program.cost.sacrifice_source
    assert semantics.program.effect_kind is ActivatedEffectKind.GAIN_THREE_LIFE
    source = inspect.getsource(CardInterpreter.activated_ability_semantics)
    assert "Anonymous Provision" not in source
    assert not any(name in source for name in ("Lita", "Courier", "Tainted Treats"))


def test_food_activation_uses_atomic_cost_stack_priority_and_life_result():
    current, food = setup_food()
    lands = tuple(
        permanent for permanent in current.players[0].battlefield if permanent.card.is_land
    )
    before_life = current.players[0].life

    assert current.execute_main_action(activation_option(current))
    ability = current.stack[-1]
    assert isinstance(ability, ActivatedAbilityObject)
    assert ability.source_id == food.object_id
    assert ability.sacrifice_source
    assert all(land.tapped for land in lands)
    assert food.zone == "former"
    evidence = current.food_activation_evidence[-1]
    sacrificed = current._objects[evidence.sacrificed_destination_id]
    assert sacrificed.zone == "former"
    assert not current.players[0].graveyard
    assert current.priority_state is not None
    assert evidence.final_source_disposition == "former"

    pass_and_resolve(current)

    assert current.players[0].life == before_life + 3
    evidence = current.food_activation_evidence[-1]
    assert evidence.resolved
    assert (evidence.life_before, evidence.life_after, evidence.amount_gained) == (20, 23, 3)
    current.check_invariants()


def test_nontoken_food_uses_same_semantics_and_remains_in_graveyard():
    current, food = setup_food(token=False)
    current.execute_main_action(activation_option(current))

    evidence = current.food_activation_evidence[-1]
    destination = current._objects[evidence.sacrificed_destination_id]
    assert destination in current.players[0].graveyard
    assert destination.zone == "graveyard"
    assert evidence.final_source_disposition == "graveyard"
    assert food.zone == "former"


def test_controller_activates_but_sacrificed_card_returns_to_owners_graveyard():
    current = Game(([LAND] * 40, [LAND] * 40), seed=1202)
    current.begin_turn()
    current.end_turn()
    current.begin_turn()
    for _ in range(2):
        current.create_permanent(LAND, 1, summoning_sick=False)
    current.create_permanent(
        CardFact("Borrowed Provision", "", 0, "Artifact — Food", CANONICAL),
        0,
        controller=1,
        summoning_sick=False,
    )

    current.execute_main_action(activation_option(current, 1))
    evidence = current.food_activation_evidence[-1]
    destination = current._objects[evidence.sacrificed_destination_id]

    assert destination in current.players[0].graveyard
    assert destination not in current.players[1].graveyard
    assert evidence.source_owner == 0 and evidence.controller == 1
    pass_and_resolve(current)
    assert current.players[1].life == 23


@pytest.mark.parametrize("mana,tapped", [(1, False), (2, True)])
def test_insufficient_mana_or_tapped_food_generates_no_activation(mana, tapped):
    current, food = setup_food(mana=mana, tapped=tapped)
    before = current.snapshot()

    assert not any(
        option.kind is ActionKind.ACTIVATE_ABILITY for option in current.legal_main_actions(0)
    )
    assert current.snapshot() == before
    assert current.is_authoritative(food, "battlefield")


def test_wrong_controller_and_nonfood_source_are_not_legal():
    current, controlled_food = setup_food(controller=1)
    fake_food = current.create_permanent(
        CardFact("Ordinary Relic", "", 0, "Artifact", CANONICAL),
        0,
        summoning_sick=False,
    )

    assert current.activation_payment_plan(0, controlled_food, CANONICAL) is None
    assert current.activation_payment_plan(0, fake_food, CANONICAL) is None
    assert not current.announce_activated_ability(0, controlled_food, CANONICAL)
    assert not current.announce_activated_ability(0, fake_food, CANONICAL)


def test_fabricated_equal_valued_and_stale_sources_fail_without_mutation():
    current, food = setup_food(token=False)
    fabricated = Permanent(
        food.object_id,
        food.card,
        food.owner,
        food.controller,
        tapped=food.tapped,
        summoning_sick=food.summoning_sick,
    )
    before = current.snapshot()

    assert not current.announce_activated_ability(0, fabricated, CANONICAL)
    assert current.snapshot() == before

    option = activation_option(current)
    current.put_into_graveyard(food)
    moved = current.snapshot()
    with pytest.raises(ValueError, match="not currently legal"):
        current.execute_main_action(option)
    assert current.snapshot() == moved


def test_duplicate_activation_and_payment_are_rejected():
    current, food = setup_food()
    option = activation_option(current)
    current.execute_main_action(option)
    after_first = current.snapshot()

    with pytest.raises(ValueError, match="not currently legal"):
        current.execute_main_action(option)
    assert current.snapshot() == after_first
    assert food.zone == "former"


def test_injected_commit_failure_rolls_back_every_cost(monkeypatch):
    current, food = setup_food()
    before = current.snapshot()
    original_register = current._register

    def fail_ability(obj):
        if isinstance(obj, ActivatedAbilityObject):
            raise RuntimeError("injected stack failure")
        return original_register(obj)

    monkeypatch.setattr(current, "_register", fail_ability)
    with pytest.raises(RuntimeError, match="injected stack failure"):
        current.announce_activated_ability(0, food, CANONICAL)

    assert current.snapshot() == before
    assert current.is_authoritative(food, "battlefield")
    assert not food.tapped


def test_life_gain_trigger_waits_for_food_resolution_and_gets_its_own_stack_object():
    current, _food = setup_food()
    watcher = current.create_permanent(
        CardFact(
            "Growing Bear",
            "",
            0,
            "Creature — Bear",
            "Whenever you gain life, put a +1/+1 counter on Growing Bear.",
            2,
            2,
        ),
        0,
        summoning_sick=False,
    )
    current.execute_main_action(activation_option(current))
    while current.priority_state is not None and not current.priority_state.resolution_pending:
        option = current.legal_priority_actions(current.priority_state.player_index)[0]
        current.execute_priority_action(option)
    current.process_priority_resolution()

    assert watcher.counters == {}
    assert current.stack
    assert current.priority_state is not None
    pass_and_resolve(current)
    assert watcher.counters == {"+1/+1": 1}


def test_food_evidence_is_reconstructive_and_serialization_is_deterministic():
    first, _ = setup_food()
    first.execute_main_action(activation_option(first))
    pass_and_resolve(first)
    second, _ = setup_food()
    second.execute_main_action(activation_option(second))
    pass_and_resolve(second)

    assert first.snapshot() == second.snapshot()
    row = first.snapshot()["food_activations"][0]
    assert row["source_name"] == "Food"
    assert row["source_type_line"] == "Artifact — Food"
    assert row["source_zone_before"] == "battlefield"
    assert row["mana_requirement"] == {"generic": 2, "colored": []}
    assert len(row["mana_source_ids"]) == 2
    assert row["tap_paid"] and row["sacrifice_paid"] and row["resolved"]
    assert row["priority_passes"] == [0, 1]
    assert row["resolution_permitted"]
    assert row["final_source_disposition"] == "former"
    assert (row["life_before"], row["life_after"], row["amount_gained"]) == (20, 23, 3)


def assert_malformed_food_does_not_resolve(current, *, life=20):
    with pytest.raises(AssertionError):
        current.check_invariants()
    while current.priority_state is not None and not current.priority_state.resolution_pending:
        current.execute_priority_action(
            current.legal_priority_actions(current.priority_state.player_index)[0]
        )
    with pytest.raises(AssertionError, match="Food stack object"):
        current.process_priority_resolution()
    assert current.players[0].life == life
    assert current.stack and current.stack[-1].zone == "stack"
    assert not current.food_activation_evidence[-1].resolved


@pytest.mark.parametrize("replacement_kind", ["food", "nonfood", "stale"])
def test_food_stack_rejects_relinked_source_identity(replacement_kind):
    current, _food = setup_food(token=False)
    current.execute_main_action(activation_option(current))
    ability = current.stack[-1]
    if replacement_kind == "food":
        replacement_source = current.create_permanent(
            CardFact("Other Food", "", 0, "Artifact — Food", CANONICAL),
            0,
            summoning_sick=False,
        )
        ability.source_id = replacement_source.object_id
    elif replacement_kind == "nonfood":
        replacement_source = current.create_permanent(LAND, 0, summoning_sick=False)
        ability.source_id = replacement_source.object_id
    else:
        ability.source_id = "object-999999"
    assert_malformed_food_does_not_resolve(current)


def test_food_stack_rejects_controller_payload_and_cost_provenance_tampering():
    mutations = (
        lambda ability: setattr(ability, "controller", 1),
        lambda ability: setattr(
            ability,
            "program",
            replace(
                ability.program,
                effect_kind=ActivatedEffectKind.GRANT_SELF_FIRST_STRIKE_UNTIL_EOT,
            ),
        ),
        lambda ability: setattr(ability, "mana_source_ids", ()),
        lambda ability: setattr(ability, "sacrificed_destination_id", "object-999999"),
    )
    for mutate in mutations:
        current, _food = setup_food(token=False)
        current.execute_main_action(activation_option(current))
        mutate(current.stack[-1])
        assert_malformed_food_does_not_resolve(current)


def test_food_stack_rejects_reused_or_swapped_activation_evidence():
    current, _ = setup_food(mana=4, token=False)
    current.execute_main_action(activation_option(current))
    pass_and_resolve(current)
    for permanent in current.players[0].battlefield:
        permanent.tapped = False
    current.create_permanent(
        CardFact("Second Food", "", 0, "Artifact — Food", CANONICAL),
        0,
        summoning_sick=False,
    )
    current.execute_main_action(activation_option(current))
    first, second = current.food_activation_evidence
    current.food_activation_evidence[:] = [
        replace(first, stack_object_id=second.stack_object_id),
        replace(second, stack_object_id=first.stack_object_id),
    ]
    assert_malformed_food_does_not_resolve(current, life=23)


def test_food_stack_rejects_fabricated_evidence_and_duplicate_resolution():
    current, _ = setup_food(token=False)
    current.execute_main_action(activation_option(current))
    current.food_activation_evidence.append(
        replace(current.food_activation_evidence[0], source_id="object-999999")
    )
    assert_malformed_food_does_not_resolve(current)

    legitimate, _ = setup_food(token=False)
    legitimate.execute_main_action(activation_option(legitimate))
    ability = legitimate.stack[-1]
    pass_and_resolve(legitimate)
    before = legitimate.snapshot()
    with pytest.raises(ValueError, match="authoritative top stack object"):
        legitimate._resolve_activated_ability(ability)
    assert legitimate.snapshot() == before


def test_other_token_activations_and_arbitrary_sacrifice_costs_remain_unsupported():
    interpreter = CardInterpreter()
    for name in ("mutagen", "treasure", "clue"):
        token = interpreter.PREDEFINED_TOKENS[name]
        semantics = interpreter.activated_ability_semantics(token, token.oracle_text)
        assert semantics is not None and not semantics.coverage.fully_supported
        assert "activation_nonmana_cost_not_implemented" in semantics.limitations
    arbitrary = CardFact(
        "Anonymous Relic",
        "",
        0,
        "Artifact",
        "{2}, {T}, Sacrifice this artifact: You gain 3 life.",
    )
    semantics = interpreter.activated_ability_semantics(arbitrary, arbitrary.oracle_text)
    assert semantics is not None and not semantics.coverage.fully_supported


def test_food_corpus_memberships_and_digests_are_exact():
    recognized, executable, full = coverage_sets()

    assert (len({row[0] for row in recognized}), len(recognized)) == (5, 5)
    assert (len({row[0] for row in executable}), len(executable)) == (5, 5)
    assert (len({row[0] for row in full}), len(full)) == (1, 1)
    assert {row[1] for row in full} == {"Lita, Little Orphan Amphibian"}
    assert digest(recognized) == "e1c69b4367b09798f301c185cf1e02dbe97552b1c3283733ffbbe297badf96a8"
    assert digest(executable) == "e1c69b4367b09798f301c185cf1e02dbe97552b1c3283733ffbbe297badf96a8"
    assert digest(full) == "f0a75bdda5429dc58c6fbf524a86ef1fcc35e900118b94da60922e6a38b7b444"
    roster = frozen_names()
    frozen_recognized = [row for row in recognized if row[1] in roster]
    frozen_executable = [row for row in executable if row[1] in roster]
    frozen_full = [row for row in full if row[1] in roster]
    assert {row[1] for row in frozen_recognized} == {
        "Courier of Comestibles",
        "Lita, Little Orphan Amphibian",
        "Tainted Treats",
    }
    assert frozen_executable == frozen_recognized
    assert frozen_full == full
    assert digest(frozen_recognized) == (
        "7d98d8e6dafc83d7eb4b60e5911f4fc55904cf761c1daaaa15cbfeda253b78b8"
    )
