"""Authenticated artifact-token activation exposure and frozen deterministic replays."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.card_interpreter07 import CardInterpreter
from tmnt_design_studio.engine07 import ActionKind
from tmnt_design_studio.pilot07 import AcceptancePilot
from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, stable_digest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/cardcade"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
LEDGER = DOCS / "ISSUE_289_COVERAGE_LEDGER.csv"
OVERLAY = DOCS / "ISSUE_289_TOKEN_ACTIVATION_DISCOUNT_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_TOKEN_ACTIVATION_DISCOUNT_CALIBRATION_READINESS.json"
OUTPUT = DOCS / "ISSUE_289_TOKEN_ACTIVATION_DISCOUNT_SMOKE.json"
NAME = "Mutagen Man, Living Ooze"
ABILITY = CardInterpreter.PREDEFINED_TOKENS["mutagen"].oracle_text


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ObservedPilot(AcceptancePilot):
    def __init__(self):
        self.opportunities: set[tuple[int, str, str, str | None]] = set()
        self.selected: list[tuple[int, str, str, str | None]] = []
        self.nonselected: set[tuple[int, str, str]] = set()
        self.reducer_present: set[tuple[int, str]] = set()
        self.mutagen_present: set[tuple[int, str]] = set()

    def choose_main_action(self, view, options, stage):
        for permanent in view.battlefields[view.active_player]:
            if permanent.name == NAME:
                self.reducer_present.add((view.turn, permanent.object_id))
            if permanent.name == "Mutagen":
                self.mutagen_present.add((view.turn, permanent.object_id))
        offered = tuple(
            option
            for option in options
            if option.kind is ActionKind.ACTIVATE_ABILITY and option.oracle_fragment == ABILITY
        )
        for option in offered:
            self.opportunities.add((view.turn, stage, option.object_id, option.target_id))
        chosen = super().choose_main_action(view, options, stage)
        if chosen in offered:
            self.selected.append((view.turn, stage, chosen.object_id, chosen.target_id))
        elif offered:
            self.nonselected.add((view.turn, stage, offered[0].object_id))
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
    for opponent, seed in (("raphael", 3021), ("donatello", 3034), ("krang", 3006)):
        for seats in (
            (decks["bebop_rocksteady"], decks[opponent]),
            (decks[opponent], decks["bebop_rocksteady"]),
        ):
            spec = GameSpec(
                f"issue289-token-discount-{seats[0].display_id}-{seats[1].display_id}-{seed}",
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
                        (
                            sorted(pilot.opportunities),
                            pilot.selected,
                            sorted(pilot.nonselected),
                            sorted(pilot.reducer_present),
                            sorted(pilot.mutagen_present),
                        ),
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
                    "reducer_present": observation[3],
                    "mutagen_present": observation[4],
                    "payments": [
                        e
                        for e in events
                        if e["event"] == "activation_cost_paid"
                        and e.get("source_id")
                        in {
                            source
                            for batch in events
                            if batch["event"] == "tokens_created"
                            and batch.get("token") == "Mutagen"
                            for source in batch["object_ids"]
                        }
                    ],
                    "discounts": [
                        e
                        for e in events
                        if e["event"] == "activation_cost_reduced"
                        and e.get("oracle_fragment") == ABILITY
                    ],
                    "resolutions": [e for e in events if e["event"] == "mutagen_counter_placed"],
                    "token_batches": [
                        e
                        for e in events
                        if e["event"] == "tokens_created" and e.get("source_card") == NAME
                    ],
                }
            )
    artifact = {
        "schema": "issue289-token-activation-discount-frozen-diagnostic-v1",
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
                "opportunities": sum(len(g["opportunities"]) for g in games),
                "selections": sum(len(g["selected"]) for g in games),
                "payments": sum(len(g["payments"]) for g in games),
                "resolutions": sum(len(g["resolutions"]) for g in games),
                "discounts": sum(len(g["discounts"]) for g in games),
                "counters_placed": sum(len(g["resolutions"]) for g in games),
                "token_batches": sum(len(g["token_batches"]) for g in games),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
