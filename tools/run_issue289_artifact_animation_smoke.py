"""Six frozen-deck, balanced-seat deterministic artifact-animation diagnostics."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from objective_balance_lab_semantic_identity import identity

from tmnt_design_studio.engine07 import ActionKind
from tmnt_design_studio.pilot07 import AcceptancePilot
from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, load_catalog, stable_digest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/cardcade"
MANIFEST = ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
LEDGER = DOCS / "ISSUE_289_COVERAGE_LEDGER.csv"
OVERLAY = DOCS / "ISSUE_289_ARTIFACT_ANIMATION_CHECKPOINT.json"
READINESS = DOCS / "ISSUE_289_ARTIFACT_ANIMATION_CALIBRATION_READINESS.json"
OUTPUT = DOCS / "ISSUE_289_ARTIFACT_ANIMATION_SMOKE.json"
NAME = "Donatello, Mutant Mechanic"
EFFECT = (
    "{T}: Put three +1/+1 counters on target artifact you control. "
    "If it isn't a creature, it becomes a 0/0 Robot creature in addition "
    "to its other types. Activate only as a sorcery."
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ObservedPilot(AcceptancePilot):
    """Observe options and normal pilot decisions without changing a choice."""

    def __init__(self):
        self.offered: set[tuple[int, str, str]] = set()
        self.selected: list[tuple[int, str, str]] = []
        self.present: set[tuple[int, str]] = set()
        self.offered_activations: set[tuple[int, str, str, str | None]] = set()
        self.selected_activations: list[tuple[int, str, str, str | None]] = []
        self.cheaper_cast_selected = 0

    def choose_main_action(self, view, options, stage):
        hand = {item[0]: item for item in view.hands[view.active_player]}
        battlefield = {obj.object_id: obj for side in view.battlefields for obj in side}
        for option in options:
            if (
                option.kind is ActionKind.CAST
                and hand.get(option.object_id, (None, None))[1] == NAME
            ):
                self.offered.add((view.turn, stage, option.object_id))
            if (
                option.kind is ActionKind.ACTIVATE_ABILITY
                and option.oracle_fragment == EFFECT
                and battlefield.get(option.object_id) is not None
                and battlefield[option.object_id].name == NAME
            ):
                self.offered_activations.add((view.turn, stage, option.object_id, option.target_id))
        for side in view.battlefields:
            for permanent in side:
                if permanent.name == NAME:
                    self.present.add((view.turn, permanent.object_id))
        choice = super().choose_main_action(view, options, stage)
        if choice.kind is ActionKind.CAST and hand.get(choice.object_id, (None, None))[1] == NAME:
            self.selected.append((view.turn, stage, choice.object_id))
        if (
            choice.kind is ActionKind.CAST
            and self.offered
            and hand.get(choice.object_id)
            and any(key[:2] == (view.turn, stage) for key in self.offered)
            and hand[choice.object_id][2] < ROW_MANA_VALUE
        ):
            self.cheaper_cast_selected += 1
        if choice.kind is ActionKind.ACTIVATE_ABILITY and choice.oracle_fragment == EFFECT:
            self.selected_activations.append((view.turn, stage, choice.object_id, choice.target_id))
        return choice


ROW_MANA_VALUE = int(load_catalog(ROOT).resolve_name(NAME).mana_value)


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
    for opponent, seed in (("bebop_rocksteady", 3006), ("raphael", 3021), ("krang", 3034)):
        for seats in (
            (decks["donatello"], decks[opponent]),
            (decks[opponent], decks["donatello"]),
        ):
            spec = GameSpec(
                f"issue289-artifact-animation-{seats[0].display_id}-{seats[1].display_id}-{seed}",
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
                observations.append(
                    (
                        pilot.offered,
                        pilot.selected,
                        pilot.present,
                        pilot.offered_activations,
                        pilot.selected_activations,
                        pilot.cheaper_cast_selected,
                    )
                )
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
                event
                for event in events
                if event["event"] == "activated_counter_artifact_animation_resolved"
            ]
            entries = {
                event["destination_object_id"]
                for event in events
                if event["event"] == "zone_changed"
                and event.get("destination_zone") == "battlefield"
                and event.get("card") == NAME
            }
            announced = {
                event["stack_object_id"]
                for event in events
                if event["event"] == "activation_announced"
                and event.get("oracle_fragment") == EFFECT
                and event.get("source_id") in entries
            }
            if any(
                event["source_id"] not in entries
                or event["stack_object_id"] not in announced
                or event["counters"] != 3
                or event["target_id"] is None
                or event["resulting_power"] is None
                for event in changes
            ):
                raise ValueError("artifact animation lacks source or resolution provenance")
            payments = [
                e
                for e in events
                if e["event"] == "activation_cost_paid" and e.get("stack_object_id") in announced
            ]
            resolutions = [
                e
                for e in events
                if e["event"] == "activated_ability_resolved"
                and e.get("stack_object_id") in announced
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
                    "offered_cast_opportunities": len(observations[0][0]),
                    "selected_cast_actions": len(observations[0][1]),
                    "battlefield_presence_turns": len(observations[0][2]),
                    "offered_activation_options": len(observations[0][3]),
                    "selected_activations": len(observations[0][4]),
                    "successful_activation_payments": len(payments),
                    "stack_resolutions": len(resolutions),
                    "delivered_outcomes": len(changes),
                    "cheaper_casts_selected_while_source_castable": observations[0][5],
                    "source_ids": sorted({e["source_id"] for e in changes}),
                    "runtime_error": None,
                }
            )
    OUTPUT.write_text(
        json.dumps(
            {
                "schema": "issue289-artifact-animation-smoke-v1",
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
                "activation_options": sum(g["offered_activation_options"] for g in games),
                "activation_selections": sum(g["selected_activations"] for g in games),
                "payments": sum(g["successful_activation_payments"] for g in games),
                "resolutions": sum(g["stack_resolutions"] for g in games),
                "outcomes": sum(g["delivered_outcomes"] for g in games),
                "runtime": runtime,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
