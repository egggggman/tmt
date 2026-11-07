from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
MANIFEST = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json"
PUNKS_ORACLE_ID = "d1edb950-a118-4b4d-a0ef-9a6683d74c9f"
PUNKS_FRAGMENT = (
    "{T}: Add {R}. Spend this mana only to cast an artifact spell or to activate an ability."
)
LAND = CardFact("Mountain", "", 0, "Basic Land — Mountain", "({T}: Add {R}.)")


def purple_dragon_punks() -> CardFact:
    catalog = load_card_data(SNAPSHOT, MANIFEST)
    row = catalog.resolve_name("Purple Dragon Punks")
    assert catalog.snapshot_sha256 == "56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402"
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


def test_frozen_purple_dragon_punks_mana_ability_is_offered_and_activates():
    game = Game(([LAND] * 20, [LAND] * 20), seed=38720)
    game.begin_turn()
    source = game.create_permanent(purple_dragon_punks(), 0, summoning_sick=False)

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
