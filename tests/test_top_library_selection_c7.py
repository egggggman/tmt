"""C7: generic hidden top-library selection and random-bottom transaction."""

import json

import pytest

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import CardFact, CastKind, Game
from tmnt_design_studio.top_library_selection07 import TopLibrarySelectionOption

LAND = CardFact("Forest", "", 0, "Basic Land — Forest")
MUTANT = CardFact("Mutant", "{1}{G}", 2, "Creature — Mutant", power=2, toughness=2)
PLAIN = CardFact("Plain", "{1}", 1, "Creature — Human", power=1, toughness=1)
SPELL = CardFact(
    "Selection Spell",
    "{G}",
    1,
    "Sorcery",
    "Look at the top four cards of your library. You may reveal a Mutant, Ninja, "
    "Turtle, or land card from among them and put it into your hand. Put the rest "
    "on the bottom of your library in a random order.",
)


def setup(cards, chooser=None, seed=7701):
    game = Game(([LAND] * 30, [LAND] * 30), seed=seed, top_library_selection_chooser=chooser)
    game.begin_turn()
    game.create_permanent(LAND, 0, summoning_sick=False)
    game.set_hand_for_testing(0, [SPELL])
    for obj in tuple(game.players[0].library):
        game.move_object(obj, "graveyard", reason="c7_setup")
    for card in cards:
        game.players[0].library.append(game._create_card_object(card, 0, "library"))
    return game


def test_exact_generic_grammar_and_cast_kind():
    interpreter = CardInterpreter()
    assert interpreter.top_library_selection_program(SPELL).quantity == 4
    assert interpreter.cast_program(SPELL).kind is CastKind.TOP_LIBRARY_SELECTION
    assert interpreter.top_library_selection_semantic_coverage(SPELL, SPELL.oracle_text)
    assert (
        interpreter.top_library_selection_program(
            CardFact("Bad", "{G}", 1, "Sorcery", SPELL.oracle_text + " Draw a card.")
        )
        is None
    )


@pytest.mark.parametrize("size", [0, 1, 3, 4, 6])
def test_bounded_selection_preserves_identity_and_handles_short_library(size):
    game = setup([PLAIN] * size)
    before = tuple(obj.object_id for obj in game.players[0].library)
    assert game.cast(0, game.players[0].hand[0])
    after = tuple(obj.object_id for obj in game.players[0].library)
    assert set(after) <= set(before)
    assert len(after) == size
    decision = next(e for e in game.events if e["event"] == "top_library_selection_decided")
    assert decision["eligible_ids"] == []
    assert decision["selected_id"] is None


def test_eligible_selection_reveals_only_inspected_card_and_orders_remainder():
    seen = []

    def choose(view, options):
        seen.append(view)
        assert len(view.cards) == 4
        assert len(options) == 2 and options[-1] == TopLibrarySelectionOption(None)
        return options[0]

    game = setup([PLAIN, PLAIN, PLAIN, MUTANT], choose)
    # The final appended object receives obj-34 after the 30-card setup library.
    selected = game.players[0].library[-1]
    assert selected.card is MUTANT
    assert game.cast(0, game.players[0].hand[0])
    assert seen[0].cards[0][1] == "Mutant"
    commit = next(e for e in game.events if e["event"] == "top_library_selection_committed")
    assert commit["selected_id"] == selected.object_id
    assert any(
        obj.object_id != selected.object_id and obj.card is MUTANT for obj in game.players[0].hand
    )
    assert selected.object_id not in [obj.object_id for obj in game.players[0].library]
    assert any(e["event"] == "top_library_selection_bottom_ordered" for e in game.events)


def test_invalid_choice_is_rejected_without_mutation():
    def choose(_view, _options):
        return TopLibrarySelectionOption("forged")

    game = setup([PLAIN, PLAIN, PLAIN, MUTANT], choose)
    before = tuple(obj.object_id for obj in game.players[0].library)
    with pytest.raises(ValueError, match="listed option"):
        game.cast(0, game.players[0].hand[0])
    assert tuple(obj.object_id for obj in game.players[0].library) == before


def test_deterministic_bottom_order_and_exact_replay():
    snapshots = []
    for _ in range(2):
        game = setup([PLAIN, MUTANT, PLAIN, LAND, PLAIN], seed=7702)
        assert game.cast(0, game.players[0].hand[0])
        snapshots.append(json.loads(json.dumps(game.snapshot())))
    assert snapshots[0] == snapshots[1]
    bottom = next(
        e for e in snapshots[0]["events"] if e["event"] == "top_library_selection_bottom_ordered"
    )
    assert bottom["domain"].startswith("top_library_selection:")


def test_private_view_hides_uninspected_library():
    observed = []

    def choose(view, options):
        public = game.public_view()
        assert not hasattr(public, "libraries")
        assert len(view.cards) == 4
        observed.append(view)
        return options[-1]

    game = setup([CardFact("Secret", "{1}", 1, "Creature — Human")] + [PLAIN] * 4, choose)
    game.cast(0, game.players[0].hand[0])
    assert observed
    assert "Secret" not in repr(observed[0])
