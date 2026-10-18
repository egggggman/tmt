"""Authenticated generic Equipment self-copy exposure with frozen-deck replays."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.engine07 import ActionKind
from tmnt_design_studio.pilot07 import AcceptancePilot
from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/cardcade"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
LEDGER = DOCS / "ISSUE_289_COVERAGE_LEDGER.csv"
OVERLAY = DOCS / "ISSUE_289_EQUIPMENT_COPY_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_EQUIPMENT_COPY_CALIBRATION_READINESS.json"
OUTPUT = DOCS / "ISSUE_289_EQUIPMENT_COPY_SMOKE.json"
NAME = "Improvised Arsenal"
FRAGMENT = "{4}{R}: Create a token that's a copy of this Equipment."


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ObservedPilot(AcceptancePilot):
    def __init__(self):
        self.opportunities: set[tuple[int, str, str]] = set()
        self.selected: list[tuple[int, str, str]] = []
        self.nonselected: set[tuple[int, str, str]] = set()

    def choose_main_action(self, view, options, stage):
        active = view.active_player
        hand_ids = {row[0] for row in view.hands[active] if row[1] == NAME}
        offered = tuple(
            option
            for option in options
            if option.kind is ActionKind.CAST and option.object_id in hand_ids
        )
        for option in offered:
            self.opportunities.add((view.turn, stage, option.object_id))
        chosen = super().choose_main_action(view, options, stage)
        if chosen in offered:
            self.selected.append((view.turn, stage, chosen.object_id))
        elif offered:
            self.nonselected.add((view.turn, stage, offered[0].object_id))
        return chosen

    def choose_priority_action(self, view, options):
        offered = tuple(
            option
            for option in options
            if option.kind is ActionKind.ACTIVATE_ABILITY and option.oracle_fragment == FRAGMENT
        )
        for option in offered:
            self.opportunities.add((view.turn, "priority", option.object_id))
        chosen = super().choose_priority_action(view, options)
        if chosen in offered:
            self.selected.append((view.turn, "priority", chosen.object_id))
        elif offered:
            self.nonselected.add((view.turn, "priority", offered[0].object_id))
        return chosen


def main() -> None:
    manifest, overlay, readiness = (
        json.loads(path.read_text()) for path in (MANIFEST, OVERLAY, READINESS)
    )
    runtime = identity()["aggregate_semantic_runtime_sha256"]
    if (
        sha(MANIFEST) != overlay["baseline_manifest_sha256"]
        or sha(LEDGER) != overlay["base_ledger_sha256"]
        or sha(OVERLAY) != readiness["checkpoint_overlay_sha256"]
        or runtime != overlay["semantic_runtime_sha256"]
        or len(overlay["rows"]) != 172
    ):
        raise ValueError("frozen runtime, manifest or ledger lineage changed")
    decks = {}
    for deck in manifest["decks"]:
        raw = (ROOT / deck["source_path"]).read_bytes()
        crlf = raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        if deck["sha256"] not in (
            hashlib.sha256(raw).hexdigest(),
            hashlib.sha256(crlf).hexdigest(),
        ):
            raise ValueError("frozen deck differs from authenticated manifest")
        decks[deck["deck_key"]] = DeckSpec(deck["deck_key"], deck["source_path"])
    games = []
    for opponent, seed in (("donatello", 3034), ("raphael", 3021), ("casey_jones", 3006)):
        for seats in (
            (decks["michelangelo"], decks[opponent]),
            (decks[opponent], decks["michelangelo"]),
        ):
            spec = GameSpec(
                f"issue289-equipment-copy-{seats[0].display_id}-{seats[1].display_id}-{seed}",
                "issue289-diagnostic-only",
                seed,
                f"{seats[0].display_id}-first",
                seats,
            )
            runs = []
            for _ in range(2):
                pilot = ObservedPilot()
                result = run_smoke_game(ROOT, spec, pilot=pilot)
                runs.append(
                    (
                        result,
                        (sorted(pilot.opportunities), pilot.selected, sorted(pilot.nonselected)),
                    )
                )
            (first, observation), (replay, replay_observation) = runs
            if (
                first.get("error")
                or replay.get("error")
                or stable_digest(first) != stable_digest(replay)
                or observation != replay_observation
            ):
                raise ValueError(f"frozen replay failed: {spec.game_id}: {first.get('error')}")
            events = first["events"]
            games.append(
                {
                    "game_id": spec.game_id,
                    "seed": seed,
                    "seats": [seat.display_id for seat in seats],
                    "result_sha256": stable_digest(first),
                    "opportunities": observation[0],
                    "selected": observation[1],
                    "nonselected": observation[2],
                    "casts": [
                        e for e in events if e["event"] == "spell_cast" and e.get("card") == NAME
                    ],
                    "payments": [
                        e for e in events if e["event"] == "cost_paid" and e.get("card") == NAME
                    ],
                    "entries": [
                        e
                        for e in events
                        if e["event"] == "zone_changed"
                        and e.get("card") == NAME
                        and e.get("destination_zone") == "battlefield"
                    ],
                    "copied_tokens": [
                        e for e in events if e["event"] == "copied_artifact_token_created"
                    ],
                    "activation_announced": [
                        e for e in events if e["event"] == "activated_ability_stacked"
                    ],
                    "activation_cost_paid": [
                        e for e in events if e["event"] == "cost_paid" and e.get("card") == NAME
                    ],
                }
            )
    artifact = {
        "schema": "issue289-equipment-copy-frozen-diagnostic-v1",
        "baseline_id": "OBL-BASELINE-005",
        "purpose": "mechanical_and_pilot_exposure_only_no_balance_inference",
        "semantic_runtime_sha256": runtime,
        "manifest_sha256": sha(MANIFEST),
        "ledger_sha256": sha(LEDGER),
        "overlay_sha256": sha(OVERLAY),
        "replay_count": len(games),
        "games": games,
    }
    OUTPUT.write_text(json.dumps(artifact, indent=2) + "\n")
    print(
        json.dumps(
            {
                "games": len(games),
                **{
                    key: sum(len(g[key]) for g in games)
                    for key in (
                        "opportunities",
                        "selected",
                        "casts",
                        "payments",
                        "entries",
                        "copied_tokens",
                        "activation_announced",
                        "activation_cost_paid",
                    )
                },
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
