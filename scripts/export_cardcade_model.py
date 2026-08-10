"""Export the frozen card facts used by Cardcade from the project database."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def deck_names(root: Path, roster_path: Path) -> set[str]:
    roster = json.loads(roster_path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for deck in roster["decks"]:
        in_deck = False
        for line in (root / deck["decklist"]).read_text(encoding="utf-8").splitlines():
            if line.strip() == "Deck":
                in_deck = True
                continue
            if in_deck and line.strip():
                names.add(line.split(" ", 1)[1])
    return names


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--roster", type=Path, default=Path("cardcade/roster-0.2.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    names = set().union(
        *(deck_names(root, roster) for roster in sorted((root / "cardcade").glob("roster-*.json")))
    )
    with sqlite3.connect(args.database) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT oracle_id,name,mana_cost,mana_value,type_line,oracle_text FROM cards "
            f"WHERE name IN ({','.join('?' for _ in names)}) ORDER BY name",
            sorted(names),
        ).fetchall()
        keywords = {
            row["oracle_id"]: [
                item[0]
                for item in connection.execute(
                    "SELECT k.name FROM keywords k JOIN card_keywords ck ON ck.keyword_id=k.id "
                    "WHERE ck.oracle_id=? ORDER BY k.name",
                    (row["oracle_id"],),
                )
            ]
            for row in rows
        }
    found = {row["name"] for row in rows}
    if missing := names - found:
        raise SystemExit(f"Missing card facts: {sorted(missing)}")
    payload = {
        "schema_version": "1.0.0",
        "source": "tmnt-design-studio.db cards/keywords; frozen for Engine 0.6",
        "cards": {
            row["name"]: {
                "oracle_id": row["oracle_id"],
                "mana_cost": row["mana_cost"] or "",
                "mana_value": int(row["mana_value"]),
                "type_line": row["type_line"],
                "oracle_text": row["oracle_text"] or "",
                "keywords": keywords[row["oracle_id"]],
            }
            for row in rows
        },
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
