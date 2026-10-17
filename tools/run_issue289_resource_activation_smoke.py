"""Six frozen-deck, balanced-seat deterministic resource diagnostics."""

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
OVERLAY = DOCS / "ISSUE_289_RESOURCE_ACTIVATION_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_RESOURCE_ACTIVATION_CALIBRATION_READINESS.json"
OUTPUT = DOCS / "ISSUE_289_RESOURCE_ACTIVATION_SMOKE.json"
NAME = "Ice Cream Kitty"
DRAW = "{2}, Sacrifice another creature or token: Draw a card. Activate only as a sorcery."
LIFE = "{2}, {T}, Sacrifice this creature: You gain 3 life."


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ObservedPilot(AcceptancePilot):
    """Record offered versus selected resource actions without altering choices."""

    def __init__(self):
        self.offered: set[tuple[int, str, str, str]] = set()
        self.selected: list[tuple[int, str, str]] = []

    def choose_main_action(self, view, options, stage):
        for option in options:
            if option.kind is ActionKind.ACTIVATE_ABILITY and option.oracle_fragment in (
                DRAW,
                LIFE,
            ):
                self.offered.add((view.turn, stage, option.object_id, option.oracle_fragment))
        choice = super().choose_main_action(view, options, stage)
        if choice.kind is ActionKind.ACTIVATE_ABILITY and choice.oracle_fragment in (DRAW, LIFE):
            self.selected.append((view.turn, stage, choice.oracle_fragment))
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
    for opponent, seed in (("raphael", 3006), ("shredder", 3021), ("donatello", 3034)):
        for seats in (
            (decks["bebop_rocksteady"], decks[opponent]),
            (decks[opponent], decks["bebop_rocksteady"]),
        ):
            spec = GameSpec(
                f"issue289-resource-activation-{seats[0].display_id}-{seats[1].display_id}-{seed}",
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
                observations.append((pilot.offered, pilot.selected))
            first, replay = results
            if (
                first.get("error")
                or replay.get("error")
                or stable_digest(first) != stable_digest(replay)
                or observations[0] != observations[1]
            ):
                raise ValueError(f"frozen replay failed: {spec.game_id}: {first.get('error')}")
            events = first["events"]
            activations = [
                event
                for event in events
                if event["event"] == "activation_announced" and event.get("source") == NAME
            ]
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
                    "offered_resource_opportunities": len(observations[0][0]),
                    "selected_resource_actions": len(observations[0][1]),
                    "draw_activations": sum(e["oracle_fragment"] == DRAW for e in activations),
                    "life_activations": sum(e["oracle_fragment"] == LIFE for e in activations),
                    "source_ids": sorted({e["source_id"] for e in activations}),
                    "runtime_error": None,
                }
            )
    OUTPUT.write_text(
        json.dumps(
            {
                "schema": "issue289-resource-activation-smoke-v1",
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
                "offered": sum(g["offered_resource_opportunities"] for g in games),
                "selected": sum(g["selected_resource_actions"] for g in games),
                "draws": sum(g["draw_activations"] for g in games),
                "life": sum(g["life_activations"] for g in games),
                "runtime": runtime,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
