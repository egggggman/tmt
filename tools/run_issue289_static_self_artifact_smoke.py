"""Six frozen-deck, balanced-seat deterministic artifact-scaling diagnostics."""

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
OVERLAY = DOCS / "ISSUE_289_STATIC_SELF_ARTIFACT_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_STATIC_SELF_ARTIFACT_CALIBRATION_READINESS.json"
OUTPUT = DOCS / "ISSUE_289_STATIC_SELF_ARTIFACT_SMOKE.json"
NAME = "Krang, Master Mind"
EFFECT = "Krang gets +1/+0 for each other artifact you control."


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ObservedPilot(AcceptancePilot):
    """Record offered versus selected casts and battlefield use without changing choices."""

    def __init__(self):
        self.offered: set[tuple[int, str, str]] = set()
        self.selected: list[tuple[int, str, str]] = []
        self.present: set[tuple[int, str]] = set()

    def choose_main_action(self, view, options, stage):
        hand = {item[0]: item[1] for item in view.hands[view.active_player]}
        for option in options:
            if option.kind is ActionKind.CAST and hand.get(option.object_id) == NAME:
                self.offered.add((view.turn, stage, option.object_id))
        for side in view.battlefields:
            for permanent in side:
                if permanent.name == NAME:
                    self.present.add((view.turn, permanent.object_id))
        choice = super().choose_main_action(view, options, stage)
        if choice.kind is ActionKind.CAST and hand.get(choice.object_id) == NAME:
            self.selected.append((view.turn, stage, choice.object_id))
        return choice


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
        if deck["sha256"] not in {
            hashlib.sha256(raw).hexdigest(),
            hashlib.sha256(crlf).hexdigest(),
        }:
            raise ValueError("frozen deck differs from authenticated manifest")
        decks[deck["deck_key"]] = DeckSpec(deck["deck_key"], deck["source_path"])
    if len(decks) != 10:
        raise ValueError("Baseline 005 is incomplete")
    games = []
    for opponent, seed in (("bebop_rocksteady", 3006), ("raphael", 3021), ("donatello", 3034)):
        for seats in (
            (decks["krang"], decks[opponent]),
            (decks[opponent], decks["krang"]),
        ):
            spec = GameSpec(
                f"issue289-static-self-artifact-{seats[0].display_id}-{seats[1].display_id}-{seed}",
                "issue289-diagnostic-only",
                seed,
                f"{seats[0].display_id}-first",
                seats,
            )
            observations = []
            results = []
            for _ in range(2):
                pilot = ObservedPilot()
                results.append(run_smoke_game(ROOT, spec, pilot=pilot))
                observations.append((pilot.offered, pilot.selected, pilot.present))
            first, replay = results
            if (
                first.get("error")
                or replay.get("error")
                or stable_digest(first) != stable_digest(replay)
                or observations[0] != observations[1]
            ):
                raise ValueError(f"frozen replay failed: {spec.game_id}: {first.get('error')}")
            events = first["events"]
            changes = [
                event for event in events if event["event"] == "pt_static_self_quality_changed"
            ]
            entries = {
                event["destination_object_id"]
                for event in events
                if event["event"] == "zone_changed"
                and event.get("destination_zone") == "battlefield"
                and event.get("card") == NAME
            }
            if any(
                event["source_id"] not in entries
                or event["oracle_fragment"] != EFFECT
                or event["quality"] != "Artifact"
                or event["power"] != event["qualifying_count"]
                or event["toughness"] != 0
                for event in changes
            ):
                raise ValueError("static artifact count lacks authenticated source and modifier")
            games.append(
                {
                    "game_id": spec.game_id,
                    "first_player": seats[0].display_id,
                    "second_player": seats[1].display_id,
                    "seed": seed,
                    "result_digest": stable_digest(first),
                    "replay_equal": True,
                    "ending_turn": first["turn"],
                    "event_count": len(events),
                    "source_casts": sum(
                        event["event"] == "spell_cast" and event.get("card") == NAME
                        for event in events
                    ),
                    "offered_cast_opportunities": len(observations[0][0]),
                    "selected_cast_actions": len(observations[0][1]),
                    "battlefield_presence_turns": len(observations[0][2]),
                    "modifier_changes": len(changes),
                    "maximum_qualifying_artifacts": max(
                        (event["qualifying_count"] for event in changes), default=0
                    ),
                    "source_ids": sorted({e["source_id"] for e in changes}),
                    "runtime_error": None,
                }
            )
    OUTPUT.write_text(
        json.dumps(
            {
                "schema": "issue289-static-self-artifact-smoke-v1",
                "kind": "diagnostic_only_not_balance_evidence",
                "baseline_id": "OBL-BASELINE-005",
                "manifest_sha256": sha(MANIFEST),
                "original_ledger_sha256": sha(LEDGER),
                "checkpoint_overlay_sha256": sha(OVERLAY),
                "semantic_runtime_sha256": runtime,
                "game_count": len(games),
                "deterministic_replay_count": len(games),
                "games": games,
                "calibration_readiness": "BLOCKED",
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "games": len(games),
                "replays": len(games),
                "casts": sum(g["source_casts"] for g in games),
                "offered": sum(g["offered_cast_opportunities"] for g in games),
                "selected": sum(g["selected_cast_actions"] for g in games),
                "presence_turns": sum(g["battlefield_presence_turns"] for g in games),
                "modifier_changes": sum(g["modifier_changes"] for g in games),
                "runtime": runtime,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
