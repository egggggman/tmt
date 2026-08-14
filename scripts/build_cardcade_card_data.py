"""Build Cardcade's authoritative normalized TMT/PZA/TMC card-data foundation."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from audit_cardcade_scryfall import SET_CODES, USER_AGENT, normalized_card, set_cards


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-output", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    args = parser.parse_args()

    cards = []
    sets = []
    identifiers = []
    for code in SET_CODES:
        metadata, records, urls = set_cards(code)
        normalized = [normalized_card(record) for record in records]
        for card in normalized:
            card["keywords"] = sorted(card["keywords"] or [])
        cards.extend(normalized)
        identifiers.extend(urls)
        sets.append(
            {
                "code": code,
                "id": metadata["id"],
                "name": metadata["name"],
                "released_at": metadata["released_at"],
                "print_count": len(records),
                "unique_oracle_object_count": len(
                    {record.get("oracle_id") for record in records if record.get("oracle_id")}
                ),
            }
        )
    cards.sort(key=lambda card: (card["set"], card["collector_number"], card["id"]))
    encoded = json.dumps(cards, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
        "utf-8"
    )
    checksum = hashlib.sha256(encoded).hexdigest()
    args.snapshot_output.write_bytes(encoded)
    manifest = {
        "schema_version": "1.0.0",
        "retrieved_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "source": {
            "provider": "Scryfall",
            "api": "https://api.scryfall.com",
            "set_codes": list(SET_CODES),
            "request_user_agent": USER_AGENT,
            "identifiers": identifiers,
        },
        "snapshot": {
            "path": args.snapshot_output.name,
            "canonicalization": (
                "Audited normalized fields; keyword arrays sorted; UTF-8 JSON with sorted keys "
                "and compact separators; records sorted by set/collector_number/id"
            ),
            "sha256": checksum,
            "print_count": len(cards),
            "unique_oracle_object_count": len(
                {card["oracle_id"] for card in cards if card["oracle_id"]}
            ),
            "sets": sets,
        },
    }
    args.manifest_output.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
