"""Complete owner-choice library return followed by artifact token creation."""

from dataclasses import replace
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter, CastKind
from tmnt_design_studio.engine07 import ActionKind, CardFact, Game, load_facts

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
CARD = load_facts(
    load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json")),
    {"Return to the Sewers"},
)["Return to the Sewers"]
ISLAND = CardFact("Island", "", 0, "Basic Land — Island")
BEAR = CardFact("Ordinary Bear", "{1}{G}", 2, "Creature — Bear", power=2, toughness=2)
ARTIFACT = CardFact("Ordinary Artifact", "{2}", 2, "Artifact")


def game(*, lands=4, seed=313, chooser=None):
    current = Game(([ISLAND] * 40, [ISLAND] * 40), seed=seed, library_position_chooser=chooser)
    current.begin_turn()
    for _ in range(lands):
        current.create_permanent(ISLAND, 0)
    return current, current.set_hand_for_testing(0, [CARD])[0]


def drain(current):
    while current.priority_state is not None:
        state = current.priority_state
        if state.resolution_pending:
            current.process_priority_resolution()
        else:
            current.execute_priority_action(
                next(
                    action
                    for action in current.legal_priority_actions(state.player_index)
                    if action.kind is ActionKind.PASS_PRIORITY
                )
            )


def test_complete_parser_renamed_source_and_fail_closed_companions():
    interpreter = CardInterpreter()
    for card in (CARD, replace(CARD, name="Other Spell")):
        program = interpreter.targeted_library_return_and_token_program(card)
        assert program is not None
        assert program.token.definition.name == "Mutagen"
        assert interpreter.cast_program(card).kind is CastKind.TARGETED_LIBRARY_RETURN_AND_TOKEN
        assert interpreter.unsupported_fragments(card) == ()
        assert interpreter.token_semantic_coverage(card, card.oracle_text).fully_supported
    for text in (
        CARD.oracle_text + " Draw a card.",
        CARD.oracle_text.replace("owner", "controller"),
        CARD.oracle_text.replace("top or bottom", "top"),
        CARD.oracle_text.replace("You create a Mutagen token.", "You draw a card."),
        CARD.oracle_text.replace("Put a +1/+1 counter", "Scry 2, then put a +1/+1 counter"),
    ):
        partial = replace(CARD, oracle_text=text)
        assert interpreter.targeted_library_return_and_token_program(partial) is None
        assert interpreter.cast_program(partial).kind is CastKind.UNSUPPORTED


def test_payment_target_legality_and_owner_top_choice_at_resolution():
    choices = []

    def choose(owner, source, target, options):
        choices.append((owner, source, target, options))
        return "top"

    current, card = game(chooser=choose)
    target = current.create_permanent(BEAR, 1)
    artifact = current.create_permanent(ARTIFACT, 1)
    options = [
        action for action in current.legal_main_actions(0) if action.object_id == card.object_id
    ]
    assert {action.target_id for action in options} == {target.object_id}
    assert current.announce_spell(0, card, artifact) is None
    assert card.zone == "hand" and not choices
    current.execute_main_action(options[0])
    spell = current.stack[-1]
    assert spell.target_id == target.object_id and target.zone == "battlefield"
    assert not choices  # The target owner chooses only during resolution.
    paid = next(event for event in current.events if event["event"] == "cost_paid")
    assert paid["generic"] == 3 and paid["colored"] == ["U"]
    drain(current)
    resolved = next(
        e for e in current.events if e["event"] == "targeted_library_return_token_resolved"
    )
    assert choices == [(1, spell.object_id, target.object_id, ("top", "bottom"))]
    assert current.players[1].library[-1].object_id == resolved["destination_id"]
    assert target.zone == "former"
    token = current._objects[resolved["token_ids"][0]]
    assert token.card.type_line == "Artifact — Mutagen" and token.controller == 0
    assert any(
        e["event"] == "tokens_created" and e["source_id"] == spell.object_id for e in current.events
    )
    current.check_invariants()


def test_owner_bottom_choice_stolen_controller_and_token_followup():
    current, card = game(chooser=lambda owner, _source, _target, options: options[1])
    target = current.create_permanent(BEAR, 1)
    current.players[1].battlefield.remove(target)
    current.players[0].battlefield.append(target)
    target.controller = 0
    spell = current.announce_spell(0, card, target)
    assert spell is not None
    current.resolve_top_of_stack()
    resolved = next(
        e for e in current.events if e["event"] == "targeted_library_return_token_resolved"
    )
    assert resolved["target_owner"] == 1 and resolved["chosen_position"] == "bottom"
    assert current.players[1].library[0].object_id == resolved["destination_id"]
    token = current._objects[resolved["token_ids"][0]]
    assert current.interpreter.activated_ability_semantics(
        token.card, token.card.oracle_text
    ).coverage.fully_supported
    current.check_invariants()


def test_invalid_target_fizzles_with_no_token_and_no_owner_choice():
    for depart in (False, True):
        called = []
        current, card = game(chooser=lambda *args, called=called: called.append(args) or "top")
        target = current.create_permanent(BEAR, 1)
        spell = current.announce_spell(0, card, target)
        assert spell is not None
        if depart:
            current.move_object(target, "graveyard", reason="test_departure")
        else:
            target.type_line_override = "Artifact"
        current.resolve_top_of_stack()
        assert not called
        assert not any(e["event"] == "tokens_created" for e in current.events)
        assert any(e["event"] == "spell_resolved_no_effect" for e in current.events)
        current.check_invariants()


def test_insufficient_mana_priority_response_and_source_departure():
    current, card = game(lands=3)
    target = current.create_permanent(BEAR, 1)
    assert current.announce_spell(0, card, target) is None
    assert not any(a.object_id == card.object_id for a in current.legal_main_actions(0))
    current.create_permanent(ISLAND, 0)
    current._begin_priority_window(allow_empty=True, priority_player=0)
    response = next(a for a in current.legal_priority_actions(0) if a.object_id == card.object_id)
    current.execute_priority_action(response)
    spell = current.stack[-1]
    assert target.zone == "battlefield"
    drain(current)
    assert any(
        e["event"] == "targeted_library_return_token_resolved"
        and e["stack_object_id"] == spell.object_id
        for e in current.events
    )
    current.check_invariants()


def test_invalid_owner_choice_rejects_before_zone_movement():
    current, card = game(chooser=lambda *_args: "middle")
    target = current.create_permanent(BEAR, 1)
    current.announce_spell(0, card, target)
    try:
        current.resolve_top_of_stack()
    except ValueError as exc:
        assert "legal library position" in str(exc)
    else:
        raise AssertionError("invalid owner choice was accepted")
    assert target.zone == "battlefield"
    assert not any(e["event"] == "tokens_created" for e in current.events)


def test_seeded_replay_identical_zone_and_token_provenance():
    def run():
        current, card = game(seed=314)
        target = current.create_permanent(BEAR, 1)
        current.announce_spell(0, card, target)
        current.resolve_top_of_stack()
        current.check_invariants()
        return current.snapshot()

    assert run() == run()
