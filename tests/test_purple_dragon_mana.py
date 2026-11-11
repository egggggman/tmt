from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.engine07 import (
    ActionKind,
    CardFact,
    CastKind,
    Game,
    StackObject,
    TurnStep,
)
from tmnt_design_studio.mana_ledger07 import ManaSpendingContext
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, reconcile_snapshot

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
MANIFEST = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json"
PUNKS_ORACLE_ID = "d1edb950-a118-4b4d-a0ef-9a6683d74c9f"
PUNKS_FRAGMENT = (
    "{T}: Add {R}. Spend this mana only to cast an artifact spell or to activate an ability."
)
LAND = CardFact("Mountain", "", 0, "Basic Land — Mountain", "({T}: Add {R}.)")
PAID_ABILITY = CardFact(
    "Synthetic Red Ability",
    "",
    0,
    "Creature — Test Hero",
    "{R}: Synthetic Red Ability gains first strike until end of turn.",
    2,
    2,
)


def purple_dragon_punks() -> CardFact:
    catalog = load_card_data(SNAPSHOT, MANIFEST)
    row = catalog.resolve_name("Purple Dragon Punks")
    assert (
        catalog.snapshot_sha256
        == "56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402"
    )
    assert row.oracle_id == PUNKS_ORACLE_ID
    assert row.oracle_text == PUNKS_FRAGMENT
    return CardFact(
        row.name,
        row.mana_cost,
        int(row.mana_value),
        row.type_line,
        row.oracle_text,
        int(row.power) if row.power is not None else None,
        int(row.toughness) if row.toughness is not None else None,
        row.keywords,
        row.oracle_id,
    )


def game_with_punks(*, summoning_sick: bool = False, haste: bool = False):
    game = Game(([LAND] * 20, [LAND] * 20), seed=38720)
    game.begin_turn()
    card = purple_dragon_punks()
    if haste:
        card = CardFact(
            card.name,
            card.mana_cost,
            card.mana_value,
            card.type_line,
            card.oracle_text,
            card.power,
            card.toughness,
            card.keywords + ("Haste",),
            card.oracle_id,
        )
    source = game.create_permanent(card, 0, summoning_sick=summoning_sick)
    return game, source


def produce_punks_mana(game: Game, source):
    return game.announce_activated_ability(0, source, PUNKS_FRAGMENT)


def test_frozen_purple_dragon_punks_mana_ability_is_offered_and_activates():
    game, source = game_with_punks()
    priority_before = game.priority_state
    stack_before = tuple(game.stack)

    options = game.legal_main_actions(0)
    option = next(
        (
            item
            for item in options
            if item.kind is ActionKind.ACTIVATE_ABILITY
            and item.object_id == source.object_id
            and item.oracle_fragment == PUNKS_FRAGMENT
        ),
        None,
    )
    assert option is not None
    ability = game.announce_activated_ability(0, source, PUNKS_FRAGMENT)
    assert ability is not None
    assert ability.zone == "former"
    assert tuple(game.stack) == stack_before
    assert game.priority_state is priority_before
    assert source.tapped
    assert game.floating_mana.snapshot(0, ManaSpendingContext.ARTIFACT_SPELL) == {"R": 1}
    lots = game.floating_mana.lots(0)
    assert len(lots) == 1
    lot = lots[0]
    assert lot.production.source_id == source.object_id
    assert lot.production.event_id == ability.object_id
    assert lot.production.controller == 0
    assert lot.production.color == "R" and lot.production.quantity == 1
    assert lot.production.allowed_contexts == frozenset(
        {ManaSpendingContext.ARTIFACT_SPELL, ManaSpendingContext.ACTIVATED_ABILITY}
    )
    assert lot.remaining_quantity == 1 and lot.valid
    evidence = game.activation_evidence[-1]
    assert evidence.resolved
    assert evidence.source_id == source.object_id
    assert evidence.oracle_fragment == PUNKS_FRAGMENT
    production_events = [
        event
        for event in game.events
        if event["event"] == "floating_mana_produced"
        and event["stack_object_id"] == ability.object_id
    ]
    assert len(production_events) == 1
    assert production_events[0]["allowed_contexts"] == (
        "artifact_spell",
        "activated_ability",
    )
    assert not any(
        event["event"] == "activated_ability_stacked"
        and event["stack_object_id"] == ability.object_id
        for event in game.events
    )
    assert (
        game.snapshot()["floating_mana_ledger"]["players"][0]["productions"][0]["source_id"]
        == source.object_id
    )


def test_summoning_sick_punks_cannot_tap_for_mana_without_mutation():
    game, source = game_with_punks(summoning_sick=True)
    before = game.snapshot()
    assert not any(
        option.kind is ActionKind.ACTIVATE_ABILITY and option.object_id == source.object_id
        for option in game.legal_main_actions(0)
    )
    assert produce_punks_mana(game, source) is None
    assert game.snapshot() == before


def test_haste_allows_summoning_sick_punks_mana_activation():
    game, source = game_with_punks(summoning_sick=True, haste=True)
    assert produce_punks_mana(game, source) is not None
    assert source.tapped and game.floating_mana.snapshot(
        0, ManaSpendingContext.ACTIVATED_ABILITY
    ) == {"R": 1}


def test_tapped_punks_cannot_activate_again_or_duplicate_mana():
    game, source = game_with_punks()
    first = produce_punks_mana(game, source)
    assert first is not None
    before = game.snapshot()
    assert produce_punks_mana(game, source) is None
    assert game.snapshot() == before
    assert len(game.floating_mana.productions(0)) == 1


def test_punks_mana_is_immediately_available_during_priority_without_epoch_change():
    game, source = game_with_punks()
    dummy = StackObject(game._allocate_object_id(), PAID_ABILITY, 1, 1, CastKind.CREATURE)
    game._register(dummy)
    game.stack.append(dummy)
    game._begin_priority_window()
    priority = game.priority_state
    epoch = priority.epoch
    action = next(
        option
        for option in game.legal_priority_actions(0)
        if option.kind is ActionKind.ACTIVATE_ABILITY
        and option.object_id == source.object_id
        and option.oracle_fragment == PUNKS_FRAGMENT
    )
    assert game.execute_priority_action(action)
    assert game.priority_state is priority and game.priority_state.epoch == epoch
    assert game.stack == [dummy]
    assert game.floating_mana.snapshot(0, ManaSpendingContext.ARTIFACT_SPELL) == {"R": 1}


def test_restricted_punks_mana_pays_artifact_spell_with_exact_lineage():
    game, source = game_with_punks()
    production = produce_punks_mana(game, source)
    artifact = CardFact("Synthetic Artifact", "{R}", 1, "Artifact", "")
    card = game.set_hand_for_testing(0, [artifact])[0]
    payment_id = card.object_id
    assert production is not None and game.can_afford(0, card)
    spell = game.announce_spell(0, card)
    assert spell is not None and spell.zone == "stack"
    payment = game.floating_mana.consumptions(0)[0]
    assert payment.source_event_id == production.object_id
    assert payment.payment_id == payment_id
    assert payment.controller == 0 and payment.color == "R" and payment.quantity == 1
    assert payment.spending_context is ManaSpendingContext.ARTIFACT_SPELL
    assert game.floating_mana.snapshot(0) == {}


def test_restricted_punks_mana_cannot_pay_nonartifact_spell():
    game, source = game_with_punks()
    assert produce_punks_mana(game, source) is not None
    card = game.set_hand_for_testing(
        0, [CardFact("Synthetic Red Creature", "{R}", 1, "Creature", "", 1, 1)]
    )[0]
    before = game.snapshot()
    assert not game.can_afford(0, card)
    assert game.announce_spell(0, card) is None
    assert game.snapshot() == before


def test_restricted_punks_mana_pays_supported_activated_ability():
    game, source = game_with_punks()
    production = produce_punks_mana(game, source)
    ability_source = game.create_permanent(PAID_ABILITY, 0, summoning_sick=False)
    plan = game.activation_payment_plan(0, ability_source, PAID_ABILITY.oracle_text)
    assert plan is not None and plan.mana_payment is not None
    assert plan.mana_payment.payment_id == plan.payment_id
    ability = game.announce_activated_ability(0, ability_source, PAID_ABILITY.oracle_text)
    assert ability is not None and ability in game.stack
    payment = game.floating_mana.consumptions(0)[0]
    assert payment.source_event_id == production.object_id
    assert payment.payment_id == ability.object_id == plan.payment_id
    assert payment.spending_context is ManaSpendingContext.ACTIVATED_ABILITY


def test_restricted_punks_mana_combines_with_land_and_leaves_payment_provenance():
    game, source = game_with_punks()
    production = produce_punks_mana(game, source)
    ability_source = game.create_permanent(
        CardFact(
            "Synthetic Generic Red Ability",
            "",
            0,
            "Creature — Test Hero",
            "{1}{R}: Synthetic Generic Red Ability gains first strike until end of turn.",
            2,
            2,
        ),
        0,
        summoning_sick=False,
    )
    land = game.create_permanent(LAND, 0, summoning_sick=False)
    plan = game.activation_payment_plan(0, ability_source, ability_source.card.oracle_text)
    assert plan is not None and plan.mana_source_ids == (land.object_id,)
    ability = game.announce_activated_ability(0, ability_source, ability_source.card.oracle_text)
    assert ability is not None and land.tapped
    allocation = game.floating_mana.consumptions(0)[0]
    assert allocation.source_event_id == production.object_id
    assert allocation.payment_id == ability.object_id
    assert allocation.quantity == 1 and allocation.color == "R"
    assert game.floating_mana.snapshot(0) == {}


def test_unspent_punks_mana_expires_at_step_boundary_with_source_history():
    game, source = game_with_punks()
    ability = produce_punks_mana(game, source)
    assert ability is not None
    game.transition_to(TurnStep.BEGINNING_OF_COMBAT)
    lot = game.floating_mana.lots(0)[0]
    assert lot.remaining_quantity == 0 and not lot.valid
    assert lot.expired_at == f"turn-{game.turn}:step-end:{TurnStep.PRECOMBAT_MAIN.value}"
    assert game.floating_mana.snapshot(0) == {}
    assert game.floating_mana.expirations(0)[0].production_event_id == ability.object_id


def test_produced_restricted_mana_remains_spendable_after_source_leaves():
    game, source = game_with_punks()
    ability = produce_punks_mana(game, source)
    assert ability is not None
    game.destroy(source)
    assert source not in game.players[0].battlefield
    artifact = CardFact("Synthetic Artifact After Source Departure", "{R}", 1, "Artifact", "")
    card = game.set_hand_for_testing(0, [artifact])[0]
    spell = game.announce_spell(0, card)
    assert spell is not None
    assert game.floating_mana.consumptions(0)[0].source_event_id == ability.object_id


def test_punks_activation_and_following_ability_reconcile_without_fabricated_execution():
    game, source = game_with_punks()
    production = produce_punks_mana(game, source)
    ability_source = game.create_permanent(PAID_ABILITY, 0, summoning_sick=False)
    activated = game.announce_activated_ability(0, ability_source, PAID_ABILITY.oracle_text)
    assert production is not None and activated is not None
    snapshot = game.snapshot()
    snapshot["stage002_presence"] = []
    spec = GameSpec(
        "synthetic-purple-dragon-mana",
        "synthetic-purple-dragon-mana",
        game.rng.seed,
        "canonical",
        (DeckSpec("A", ""), DeckSpec("B", "")),
    )
    report = reconcile_snapshot(spec, snapshot, {"decks": [{"cards": []}, {"cards": []}]})
    assert not [
        item for item in report["stop_records"] if item["kind"] == "mana_payment_provenance"
    ]
    executed = report["executed_references"]
    assert len(executed) == 1
    assert executed[0]["evidence_id"] == production.object_id
    assert executed[0]["source_id"] == source.object_id
    assert executed[0]["oracle_fragment"] == PUNKS_FRAGMENT
    production = next(
        item
        for item in snapshot["floating_mana_ledger"]["players"][0]["productions"]
        if item["event_id"] == production.object_id
    )
    assert production["allowed_contexts"] == ["activated_ability", "artifact_spell"]
    payment = snapshot["floating_mana_ledger"]["players"][0]["payments"][0]
    assert payment["production_event_id"] == production["event_id"]
    assert payment["payment_id"] == activated.object_id


def test_frozen_card_identity_and_interpreter_contract_are_not_name_dispatched():
    from tmnt_design_studio.card_interpreter07 import ActivatedEffectKind, CardInterpreter

    original = purple_dragon_punks()
    renamed = CardFact(
        "Renamed Test Creature",
        original.mana_cost,
        original.mana_value,
        original.type_line,
        original.oracle_text,
        original.power,
        original.toughness,
        original.keywords,
        original.oracle_id,
    )
    semantics = CardInterpreter().activated_ability_semantics(renamed, PUNKS_FRAGMENT)
    assert semantics is not None and semantics.coverage.fully_supported
    assert semantics.program.effect_kind is ActivatedEffectKind.ADD_FIXED_COLOR_MANA
    assert semantics.program.mana_color == "R"
    assert set(semantics.program.mana_allowed_contexts or ()) == {
        "artifact_spell",
        "activated_ability",
    }
