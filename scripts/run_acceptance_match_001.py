"""Run the focused, deterministic Leonardo P0.1 vs Raphael P0.1 acceptance match."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.engine07 import Game, load_deck, load_facts
from tmnt_design_studio.pilot07 import AcceptancePilot, Pilot


def run(root: Path, seed: int, pilot: Pilot | None = None) -> dict[str, object]:
    catalog = load_card_data(
        root / "cardcade" / "scryfall-tmt-pza-tmc-2026-08-13.json",
        root / "cardcade" / "scryfall-tmt-pza-tmc-2026-08-13.manifest.json",
    )
    deck_paths = (
        root / "decks" / "leonardo" / "PROTOTYPE_0.1.txt",
        root / "decks" / "raphael" / "PROTOTYPE_0.1.txt",
    )
    names = {
        line.split(" ", 1)[1]
        for path in deck_paths
        for line in path.read_text(encoding="utf-8").splitlines()
        if line and line != "Deck"
    }
    facts = load_facts(catalog, names)
    decks = (
        load_deck(deck_paths[0], facts),
        load_deck(deck_paths[1], facts),
    )
    game = Game(decks, names=("leonardo-p0.1", "raphael-p0.1"), seed=seed)
    pilot = pilot or AcceptancePilot()
    game.scry_chooser = pilot.choose_scry
    game.hand_bottom_draw_chooser = pilot.choose_hand_bottom_draw
    game.discard_draw_chooser = pilot.choose_discard_draw
    while game.winner is None and game.turn < 120:
        game.begin_turn()
        if game.winner is not None:
            break
        active = game.active_player
        for stage in ("land", "activate", "damage", "destroy", "creature"):
            options = game.legal_main_actions(active)
            chosen = pilot.choose_main_action(game.public_view(), options, stage)
            game.execute_main_action(chosen)
            while game.priority_state is not None:
                if game.priority_state.resolution_pending:
                    game.process_priority_resolution()
                    continue
                priority_options = game.legal_priority_actions(game.priority_state.player_index)
                priority_choice = pilot.choose_priority(game.public_view(), priority_options)
                game.execute_priority_action(priority_choice)

        game.advance_step()
        game.advance_step()
        attack_options = game.legal_attack_options(active)
        attack = pilot.choose_attack(game.public_view(), attack_options)
        game.execute_attack_action(attack)
        while game.priority_state is not None:
            if game.priority_state.resolution_pending:
                game.process_priority_resolution()
                continue
            priority_options = game.legal_priority_actions(game.priority_state.player_index)
            priority_choice = pilot.choose_priority(game.public_view(), priority_options)
            game.execute_priority_action(priority_choice)
        block_options = game.legal_block_options(attack, 1 - active)
        blocks = pilot.choose_blocks(game.public_view(), block_options)
        game.execute_block_action(blocks)
        while game.step.value == "declare_blockers":
            sneak_options = game.legal_sneak_actions(active)
            sneak_choice = pilot.choose_sneak(game.public_view(), sneak_options)
            game.execute_sneak_action(sneak_choice)
            while game.priority_state is not None:
                if game.priority_state.resolution_pending:
                    game.process_priority_resolution()
                    continue
                priority_options = game.legal_priority_actions(game.priority_state.player_index)
                priority_choice = pilot.choose_priority(game.public_view(), priority_options)
                game.execute_priority_action(priority_choice)
        while game.step.value == "combat_damage":
            game.resolve_combat_damage()
        game.advance_step()
        game.check_invariants()
        game.end_turn()
    if game.winner is None:
        game.log("acceptance_incomplete", reason="turn_limit")
    return game.snapshot()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=7001)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = run(root, args.seed)
    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
