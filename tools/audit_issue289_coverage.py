"""Reproducible, read-only classification of frozen Baseline 005 Oracle gaps.

The classifier is an audit overlay, never used by the simulator. Unknown card
clauses fail closed. Rows retain every original per-deck scanner reason.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from tmnt_design_studio.card_data import load_card_data
from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import load_facts

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
CATALOG = ROOT / "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_COVERAGE_LEDGER.csv"

# Independently tested paths outside the interpreter's fragment inventory.
COVERED_CARDS = {
    "Buzz Bots",
    "Courier of Comestibles",
    "Dream Beavers",
    "Leonardo, Sewer Samurai",
    "Michelangelo, Weirdness to 11",
    "Mouser Mark III",
    "Ooze Spill",
    "Paramecia Coloniex",
    "Primordial Pachyderm",
    "Ray Fillet, Man Ray",
    "Rock Soldiers",
    "Stockman, Mad Fly-entist",
}
COVERED_KEYWORDS = {"Flying", "Flying, vigilance", "Menace", "Reach, trample"}
COVERED_PREFIXES = (
    "Menace (",
    "This creature can't be blocked by more than one creature.",
    "Rocksteady can't be blocked by more than one creature.",
)
KNOWN_CARDS = {
    "Anchovy & Banana Pizza",
    "April O'Neil, Hacktivist",
    "Bebop & Rocksteady",
    "Bebop, Warthog Warrior",
    "Cool but Rude",
    "Cowabunga!",
    "Death in the Family",
    "Does Machines",
    "Donatello, Gadget Master",
    "Donatello, Mutant Mechanic",
    "Donatello, Way with Machines",
    "Foot Mystic",
    "Frog Butler",
    "Fugitive Droid",
    "Guac & Marshmallow Pizza",
    "Hamato Guardian Stance",
    "Ice Cream Kitty",
    "Illegitimate Business",
    "Improvised Arsenal",
    "Insectoid Exterminator",
    "Krang, Master Mind",
    "Leader's Talent",
    "Leonardo's Technique",
    "Michelangelo's Technique",
    "Michelangelo, Game Master",
    "Michelangelo, Improviser",
    "Michelangelo, Mutant BFF",
    "Mind Transfer Protocol",
    "Mouser Attack!",
    "Mouser Foundry",
    "Mutagen Man, Living Ooze",
    "Mutant Chain Reaction",
    "Negate",
    "Ninja Teen",
    "Oroku Saki, Shredder Rising",
    "Pain 101",
    "Purple Dragon Punks",
    "Putrid Pals",
    "Quintessential Katana",
    "Raphael's Technique",
    "Raphael, Most Attitude",
    "Raphael, Ninja Destroyer",
    "Ravenous Robots",
    "Return to the Sewers",
    "Rocksteady, Crash Courser",
    "Saved by the Shell",
    "Shark Shredder, Killer Clone",
    "Shredder's Armor",
    "Shredder's Technique",
    "Shredder, Unrelenting",
    "Spicy Oatmeal Pizza",
    "Splinter's Technique",
    "Splinter, Hamato Yoshi",
    "Squirrelanoids",
    "Stomped by the Foot",
    "Super Shredder",
    "Tainted Treats",
    "Tenderize",
    "The Last Ronin's Technique",
}
P0_ALL = {
    "April O'Neil, Hacktivist",
    "Bebop & Rocksteady",
    "Cowabunga!",
    "Death in the Family",
    "Frog Butler",
    "Fugitive Droid",
    "Illegitimate Business",
    "Krang, Master Mind",
    "Mind Transfer Protocol",
    "Mouser Attack!",
    "Mutant Chain Reaction",
    "Negate",
    "Oroku Saki, Shredder Rising",
    "Purple Dragon Punks",
    "Saved by the Shell",
    "Spicy Oatmeal Pizza",
    "Squirrelanoids",
    "Tainted Treats",
    "Tenderize",
    "Anchovy & Banana Pizza",
    "Return to the Sewers",
}
TECHNIQUES = {
    "Leonardo's Technique",
    "Michelangelo's Technique",
    "Raphael's Technique",
    "Shredder's Technique",
    "Splinter's Technique",
    "The Last Ronin's Technique",
}


def classify(card: str, fragment: str) -> tuple[str, str, str, str]:
    """Execution, impact priority, mechanic family, and concrete disposition."""
    if card not in KNOWN_CARDS | COVERED_CARDS:
        raise AssertionError(f"New card requires review: {card}")
    if card in COVERED_CARDS:
        return "covered", "none", "inventory", "Other tested execution path"
    if fragment in COVERED_KEYWORDS or fragment.startswith(COVERED_PREFIXES):
        return "covered", "none", "combat", "Printed keyword/block restriction executes"
    if fragment in {"Cycling", "Landcycling", "Typecycling"}:
        return "covered", "none", "cycling", "Landcycling executed; catalog tags duplicate it"
    if fragment.startswith("(Gain the next level") or fragment == "Choose one —":
        return "annotation", "none", "syntax", "Reminder/header; child clauses reviewed separately"
    if card in {"Donatello, Way with Machines", "Insectoid Exterminator"} and fragment == "Flying":
        return "covered", "none", "combat", "Printed flying affects block legality"
    if card in {
        "Bebop, Warthog Warrior",
        "Raphael, Most Attitude",
        "Splinter, Hamato Yoshi",
    } and fragment.startswith("Menace"):
        return "covered", "none", "combat", "Printed menace affects block legality"
    if card == "Super Shredder" and fragment == "Menace":
        return "covered", "none", "combat", "Printed menace affects block legality"
    if card == "Raphael, Most Attitude":
        return (
            "partial",
            "P0",
            "linked exile",
            "Stacked linked trigger incorrectly stops after source removal",
        )
    if card == "Shredder, Unrelenting" and fragment.startswith("Whenever Shredder"):
        return "partial", "P0", "combat", "Grant trigger executes; lethal deathtouch does not"
    if card == "Illegitimate Business" and fragment.startswith("{T}: Add"):
        return "partial", "P0", "mana", "Only black, not alternative green mana, is available"

    if card in TECHNIQUES:
        priority = "P1" if fragment.startswith("Sneak ") else "P0"
    elif card == "Krang, Master Mind" and fragment.startswith("Krang gets"):
        priority = "P1"
    elif card in P0_ALL:
        priority = "P0"
    elif card == "Raphael, Ninja Destroyer":
        priority = "P0" if fragment.startswith("Raphael must") else "P1"
    elif card == "Stomped by the Foot":
        priority = "P1" if fragment.startswith("Kicker") else "P0"
    elif card == "Cool but Rude":
        priority = (
            "P0" if fragment.startswith(("Whenever you attack", "Whenever you discard")) else "P1"
        )
    elif card == "Quintessential Katana" or card == "Improvised Arsenal":
        priority = "P0" if fragment.startswith("Equipped creature") else "P1"
    elif card == "Shredder's Armor":
        priority = "P0" if fragment.startswith("Equip") else "P1"
    elif card == "Mouser Foundry":
        priority = "P0" if fragment.startswith("{4}{R}") else "P1"
    elif card in {"Shredder, Unrelenting", "Putrid Pals"} and fragment == "Deathtouch":
        priority = "P0"
    else:
        priority = "P1"

    if card in {"Illegitimate Business", "Purple Dragon Punks"}:
        family = "mana"
    elif card in {
        "Negate",
        "Spicy Oatmeal Pizza",
        "Anchovy & Banana Pizza",
        "Mouser Foundry",
        "Stomped by the Foot",
        "Death in the Family",
        "Tenderize",
        "Tainted Treats",
        "Mutant Chain Reaction",
        "Return to the Sewers",
        "Shredder's Technique",
    }:
        family = "interaction" if priority == "P0" else "token"
    elif (
        card in {"Leader's Talent", "Ninja Teen", "Does Machines", "Cool but Rude"}
        and priority == "P1"
    ):
        family = "class identity"
    elif (
        card in {"Frog Butler", "Squirrelanoids", "Putrid Pals", "Shredder, Unrelenting"}
        and fragment == "Deathtouch"
    ) or any(
        word in fragment.casefold()
        for word in ("block", "attack", "trample", "flying", "equipped", "damage")
    ):
        family = "combat"
    elif any(word in fragment.casefold() for word in ("draw", "search", "mana", "hand", "scry")):
        family = "resource"
    elif any(word in fragment.casefold() for word in ("token", "copy")):
        family = "token"
    elif any(word in fragment.casefold() for word in ("cost", "equip", "kicker", "level")):
        family = "casting"
    else:
        family = "board/zone"

    # The observation names the missing payload; the literal fragment and reason
    # alongside it supply the precise card-specific execution contract.
    disposition = (
        "Cast/payment/target/stack path missing or incomplete"
        if priority == "P0" and card in TECHNIQUES | {"Mouser Attack!", "Mind Transfer Protocol"}
        else "Printed clause absent or materially incomplete"
    )
    return "gap", priority, family, disposition


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    catalog = load_card_data(CATALOG, CATALOG.with_suffix(".manifest.json"))
    interpreter = CardInterpreter()
    rows = []
    for deck in manifest["decks"]:
        quantities = {
            name: int(count)
            for count, name in (
                line.split(" ", 1)
                for line in (ROOT / deck["source_path"])
                .read_text(encoding="utf-8")
                .splitlines()[1:]
            )
        }
        facts = load_facts(catalog, set(quantities))
        for name, copies in quantities.items():
            for fragment, reason in interpreter.unsupported_fragments(facts[name]):
                if (
                    name in {"Plains", "Island", "Swamp", "Mountain", "Forest"}
                    and reason == "activation_nested_context_not_implemented"
                ):
                    continue
                execution, impact, family, disposition = classify(name, fragment)
                rows.append(
                    {
                        "deck": deck["deck_key"],
                        "card": name,
                        "copies": copies,
                        "oracle_fragment": fragment,
                        "scanner_reason": reason,
                        "execution_review": execution,
                        "impact_priority": impact,
                        "family": family,
                        "disposition": disposition,
                    }
                )
    assert len(rows) == 172, len(rows)
    assert len({(r["card"], r["oracle_fragment"]) for r in rows}) == 130
    with OUTPUT.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=tuple(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print("execution", dict(Counter(r["execution_review"] for r in rows)))
    print("impact", dict(Counter(r["impact_priority"] for r in rows)))
    for deck in manifest["decks"]:
        subset = [r for r in rows if r["deck"] == deck["deck_key"]]
        print(deck["deck_key"], len(subset), dict(Counter(r["impact_priority"] for r in subset)))


if __name__ == "__main__":
    main()
