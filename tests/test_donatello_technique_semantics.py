from pathlib import Path

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec

ROOT = Path(__file__).resolve().parents[1]


def test_prior_diagnostic_seed_3000_executes_technique_after_coverage_fix():
    """Seed 3000 previously left the drawn Technique uncast and unresolved."""
    spec = GameSpec(
        "shredder-donatello-technique-3000",
        "shredder/donatello",
        3000,
        "other",
        (
            DeckSpec("shredder-p0.3", "decks/shredder/PROTOTYPE_0.3.txt"),
            DeckSpec("donatello-p0.3a", "decks/donatello/PROTOTYPE_0.3a.txt"),
        ),
    )

    result = run_smoke_game(ROOT, spec)
    technique_events = [
        event for event in result["events"] if event.get("card") == "Donatello's Technique"
    ]

    assert any(event["event"] == "spell_cast" for event in technique_events)
    assert any(
        event["event"] == "draw_spell_resolved" and event["quantity"] == 2
        for event in technique_events
    )
    assert any(event["event"] == "spell_resolved" for event in technique_events)
