"""Small authenticated Baseline 005 diagnostics with exact linked-play replays."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
OUTPUT = ROOT / "docs/cardcade/ISSUE_289_LINKED_PLAY_SMOKE.json"
MANIFEST_SHA = "c6111aeaa972cd3bba0f65dce3d6ee78391ea72e122f4f8f0724ad4535ec28ac"


def main() -> None:
    if hashlib.sha256(MANIFEST.read_bytes()).hexdigest() != MANIFEST_SHA:
        raise ValueError("Baseline 005 manifest changed")
    decks = {}
    for entry in json.loads(MANIFEST.read_text(encoding="utf-8"))["decks"]:
        key = entry["deck_key"]
        if key not in {"raphael", "donatello", "casey_jones", "bebop_rocksteady"}:
            continue
        source = (ROOT / entry["source_path"]).read_bytes()
        if hashlib.sha256(source).hexdigest() != entry["sha256"]:
            raise ValueError(f"frozen {key} deck changed")
        decks[key] = DeckSpec(key, entry["source_path"])
    if len(decks) != 4:
        raise ValueError("frozen diagnostic deck missing")
    games = []
    for opponent in ("donatello", "casey_jones", "bebop_rocksteady"):
        for seats in (
            (decks["raphael"], decks[opponent]),
            (decks[opponent], decks["raphael"]),
        ):
            spec = GameSpec(
                f"issue289-linked-play-319-{seats[0].display_id}-{seats[1].display_id}",
                "issue289-diagnostic",
                319,
                f"{seats[0].display_id}-first",
                seats,
            )
            first, replay = (run_smoke_game(ROOT, spec) for _ in range(2))
            digest = stable_digest(first)
            if first.get("error") or replay.get("error") or digest != stable_digest(replay):
                raise ValueError(f"frozen replay failure: {spec.game_id}")
            events = first["events"]
            grants = [e for e in events if e["event"] == "raphael_play_permission_created"]
            uses = [e for e in events if e["event"] == "linked_play_grant_used"]
            if len({e["grant_id"] for e in grants}) != len(grants):
                raise ValueError("duplicate linked grant identity")
            if any(
                sum(use["grant_id"] == event["grant_id"] for event in grants) != 1 for use in uses
            ):
                raise ValueError("linked play use has no unique creating trigger")
            if len({e["grant_id"] for e in uses}) != len(uses):
                raise ValueError("linked play grant was used twice")
            games.append(
                {
                    "game_id": spec.game_id,
                    "seed": spec.seed,
                    "first_player": spec.seats[0].display_id,
                    "replay_equal": True,
                    "result_digest": digest,
                    "event_count": len(events),
                    "linked_exiles": sum(e["event"] == "raphael_linked_exile" for e in events),
                    "grants": len(grants),
                    "grant_uses": len(uses),
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
                "linked_exiles": sum(g["linked_exiles"] for g in games),
                "grants": sum(g["grants"] for g in games),
                "grant_uses": sum(g["grant_uses"] for g in games),
            }
        )
    )


if __name__ == "__main__":
    main()
