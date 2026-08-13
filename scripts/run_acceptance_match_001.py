"""Run the focused, deterministic Leonardo P0.1 vs Raphael P0.1 acceptance match."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.engine07 import Game, load_deck, load_facts


def run(root: Path, seed: int) -> dict[str, object]:
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
    while game.winner is None and game.turn < 120:
        game.begin_turn()
        if game.winner is not None:
            break
        active = game.active_player
        player = game.players[active]
        land = next((card for card in player.hand if card.is_land), None)
        if land:
            game.play_land(active, land)

        # Resolve only the two safely-grounded target-aware interactions in this slice.
        opponent_creatures = [
            permanent
            for permanent in game.players[1 - active].battlefield
            if permanent.card.is_creature
        ]
        missile = next((card for card in player.hand if card.name == "Manhole Missile"), None)
        if missile and opponent_creatures:
            game.cast(
                active, missile, min(opponent_creatures, key=lambda p: p.toughness - p.damage)
            )
        move = next((card for card in player.hand if card.name == "Make Your Move"), None)
        large_target = next((p for p in opponent_creatures if p.power >= 4), None)
        if move and large_target:
            game.cast(active, move, large_target)

        # Cast the cheapest supported creature; unsupported spells stay visible in hand/limitations.
        creatures = sorted(
            (card for card in player.hand if card.is_creature),
            key=lambda card: (card.mana_value, card.name),
        )
        for card in creatures:
            if game.cast(active, card):
                break

        attackers = game.legal_attackers(active)
        game.combat(attackers, auto_assign_blockers=True)
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
