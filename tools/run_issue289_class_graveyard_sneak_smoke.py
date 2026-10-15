"""Small authenticated Class/graveyard Sneak diagnostics, never balance evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_CLASS_GRAVEYARD_SNEAK_SMOKE.json"
MANIFEST_SHA = "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac"


def main() -> None:
    if hashlib.sha256(MANIFEST.read_bytes()).hexdigest() != MANIFEST_SHA:
        raise ValueError("Baseline 005 manifest changed")
    decks = {}
    for entry in json.loads(MANIFEST.read_text(encoding="utf-8"))["decks"]:
        key = entry["deck_key"]
        if key not in {"splinter", "michelangelo", "shredder"}:
            continue
        source = (ROOT / entry["source_path"]).read_bytes()
        canonical_crlf = source.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        if entry["sha256"] not in {
            hashlib.sha256(source).hexdigest(),
            hashlib.sha256(canonical_crlf).hexdigest(),
        }:
            raise ValueError(f"frozen {key} deck changed")
        decks[key] = DeckSpec(key, entry["source_path"])
    if len(decks) != 3:
        raise ValueError("frozen diagnostic deck missing")
    games = []
    for left, right in (
        ("splinter", "shredder"),
        ("splinter", "michelangelo"),
        ("michelangelo", "shredder"),
    ):
        for seats in (
            (decks[left], decks[right]),
            (decks[right], decks[left]),
        ):
            spec = GameSpec(
                f"issue289-class-sneak-{seats[0].display_id}-{seats[1].display_id}",
                "issue289-diagnostic",
                323,
                f"{seats[0].display_id}-first",
                seats,
            )
            first, replay = (run_smoke_game(ROOT, spec) for _ in range(2))
            digest = stable_digest(first)
            if first.get("error") or replay.get("error") or digest != stable_digest(replay):
                raise ValueError(f"frozen replay failure: {spec.game_id}")
            events = first["events"]
            games.append(
                {
                    "game_id": spec.game_id,
                    "seed": spec.seed,
                    "first_player": spec.seats[0].display_id,
                    "replay_equal": True,
                    "result_digest": digest,
                    "event_count": len(events),
                    "class_level_three_activations": sum(
                        e["event"] == "class_level_advanced" and e.get("to_level") == 3
                        for e in events
                    ),
                    "graveyard_sneak_announcements": sum(
                        e["event"] == "sneak_announced" and e.get("source_zone") == "graveyard"
                        for e in events
                    ),
                    "graveyard_spell_cast_events": sum(
                        e["event"] == "spell_cast" and e.get("source_zone") == "graveyard"
                        for e in events
                    ),
                    "runtime_error": None,
                }
            )
    result = {
        "kind": "diagnostic_only_not_balance_evidence",
        "baseline_manifest_sha256": MANIFEST_SHA,
        "semantic_runtime_sha256": identity()["aggregate_semantic_runtime_sha256"],
        "game_count": len(games),
        "replay_count": len(games),
        "games": games,
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "games": len(games),
                "replays": len(games),
                "class_level_three_activations": sum(
                    g["class_level_three_activations"] for g in games
                ),
                "graveyard_sneak_announcements": sum(
                    g["graveyard_sneak_announcements"] for g in games
                ),
                "graveyard_spell_cast_events": sum(g["graveyard_spell_cast_events"] for g in games),
            }
        )
    )


if __name__ == "__main__":
    main()
