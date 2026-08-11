"""Run the focused, deterministic Leonardo P0.1 vs Raphael P0.1 acceptance match."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tmnt_design_studio.engine07 import Game, load_deck, load_facts


def run(root: Path, seed: int) -> dict[str, object]:
    facts = load_facts(root / "cardcade" / "card-model-0.6.json")
    decks = (
        load_deck(root / "decks" / "leonardo" / "PROTOTYPE_0.1.txt", facts),
        load_deck(root / "decks" / "raphael" / "PROTOTYPE_0.1.txt", facts),
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
        blockers = [
            permanent
            for permanent in game.players[1 - active].battlefield
            if permanent.card.is_creature and not permanent.tapped
        ]
        blocks = {
            id(attacker): blocker for attacker, blocker in zip(attackers, blockers, strict=False)
        }
        game.combat(attackers, blocks)
        game.phase = "ending"
        game.log("turn_ended", player=player.name)
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
