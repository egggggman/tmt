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
    while game.winner is None and game.turn < 120:
        game.begin_turn()
        if game.winner is not None:
            break
        active = game.active_player
        for stage in ("land", "damage", "destroy", "creature"):
            options = game.legal_main_actions(active)
            chosen = pilot.choose_main_action(game.public_view(), options, stage)
            game.execute_main_action(chosen)

        attack_options = game.legal_attack_options(active)
        attack = pilot.choose_attack(game.public_view(), attack_options)
        block_options = game.legal_block_options(attack, 1 - active)
        blocks = pilot.choose_blocks(game.public_view(), block_options)
        game.execute_combat_actions(attack, blocks)
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
