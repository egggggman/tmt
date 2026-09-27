from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import load_facts
from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec

ROOT = Path(__file__).resolve().parents[1]


def _does_machines():
    catalog = load_card_data(
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json",
        ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )
    return load_facts(catalog, {"Does Machines"})["Does Machines"]


def test_does_machines_is_recognized_as_an_executable_permanent_with_setup_coverage():
    card = _does_machines()
    interpreter = CardInterpreter()

    assert interpreter.cast_program(card).kind is CastKind.PERMANENT
    fragment = next(
        fragment
        for fragment in interpreter.fragments(card)
        if interpreter.etb_mill_draw_discard_semantic_coverage(card, fragment) is not None
    )
    semantics = interpreter.etb_mill_draw_discard_semantic_coverage(card, fragment)
    assert semantics is not None
    assert semantics.program.mill_quantity == 2
    assert semantics.program.draw_quantity == 2
    assert semantics.program.discard_quantity == 2
    assert any(
        fragment.startswith("When this Class becomes level 2")
        for fragment, _reason in interpreter.unsupported_fragments(card)
    )


def test_does_machines_seed_3000_casts_and_resolves_setup_sequence():
    spec = GameSpec(
        "does-machines-3000",
        "shredder/donatello",
        3000,
        "other",
        (
            DeckSpec("shredder-p0.3", "decks/shredder/PROTOTYPE_0.3.txt"),
            DeckSpec("donatello-p0.3a", "decks/donatello/PROTOTYPE_0.3a.txt"),
        ),
    )
    result = run_smoke_game(ROOT, spec)
    events = result["events"]
    setup = [event for event in events if event.get("event") == "etb_mill_draw_discard_committed"]

    assert result.get("error") is None
    assert any(
        event.get("event") == "spell_cast" and event.get("card") == "Does Machines"
        for event in events
    )
    assert any(
        event.get("event") == "permanent_resolved" and event.get("card") == "Does Machines"
        for event in events
    )
    assert len(set(event["trigger_id"] for event in setup)) == 1
    assert setup[0]["draw_count"] == 2
    assert len(set(setup[0]["milled_ids"])) == 2
    assert len(set(setup[0]["discarded_ids"])) == 2
    assert any(
        event.get("event") == "trigger_resolved" and event.get("effect") == "etb_mill_draw_discard"
        for event in events
    )


def test_does_machines_setup_replays_deterministically():
    spec = GameSpec(
        "does-machines-replay-3000",
        "shredder/donatello",
        3000,
        "other",
        (
            DeckSpec("shredder-p0.3", "decks/shredder/PROTOTYPE_0.3.txt"),
            DeckSpec("donatello-p0.3a", "decks/donatello/PROTOTYPE_0.3a.txt"),
        ),
    )
    first = run_smoke_game(ROOT, spec)
    second = run_smoke_game(ROOT, spec)
    first_setup = [
        event
        for event in first["events"]
        if event.get("event") == "etb_mill_draw_discard_committed"
    ]
    second_setup = [
        event
        for event in second["events"]
        if event.get("event") == "etb_mill_draw_discard_committed"
    ]
    assert first["events"] == second["events"]
    assert first_setup == second_setup
