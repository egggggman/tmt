"""Authoritative, checkpointed launcher for the Bad Guys 0.2 calibration contract.

This module owns the input preflight and schedule construction only.  Result
persistence is delegated to :func:`run_checkpointed_schedule`; there is no
second checkpoint format or legacy writer in this entrypoint.  Tests inject a
mock executor, so the integrity contract can be exercised without running the
Magic simulator.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from collections.abc import Callable
from pathlib import Path

try:  # Script execution puts ``tools`` on sys.path; package imports do not.
    from baseline005_provenance import ProvenanceError, verify_overlay
except ModuleNotFoundError:  # pragma: no cover - exercised by package imports
    from tools.baseline005_provenance import ProvenanceError, verify_overlay
from tmnt_design_studio.calibration_integrity import validate_schedule
from tmnt_design_studio.calibration_runner import run_checkpointed_schedule
from tmnt_design_studio.smoke01 import run_smoke_game
from tmnt_design_studio.stage002 import DeckSpec, GameSpec

try:
    from validate_baseline005_provenance import validate
except ModuleNotFoundError:  # pragma: no cover - exercised by package imports
    from tools.validate_baseline005_provenance import validate

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = "c087f84bab4916b516ec6745f5a8e9f2a2d33f9117856bf959da4eb9a7be8e54"
CANDIDATE_PATH = "docs/design-studio/challengers/BAD_GUYS_CRONIES_SANDBOX_0_2_CANDIDATE.md"
SNAPSHOT_PATH = "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
OVERLAY_PATH = "docs/objective-balance-lab/baselines/OBL_BASELINE_005_PROVENANCE_OVERLAY_001.json"
MANIFEST_PATH = "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json"
OVERLAY_ID = "OBL-BASELINE-005-PROVENANCE-OVERLAY-001"
CANDIDATE_SHA256 = "cacc77648a4d1659b8ae640d95ac2672694e6951553980246e6d001e5152bfb4"
SNAPSHOT_SHA256 = "56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402"
BEBOP_ROCKSTEADY_SHA256 = "aaa61d3a3d65f7c8ab74062cc8f41d220a46066b44c28e3c71921c570a6b66ed"
EXPECTED_GAMES = 900
EXPECTED_MATCHUPS = 9
GAMES_PER_MATCHUP = 100


def _candidate_text(root: Path) -> str:
    text = (root / CANDIDATE_PATH).read_text(encoding="utf-8")
    match = re.search(r"```text\n(Deck\n.*?\n)```", text, flags=re.DOTALL)
    if match is None:
        raise ProvenanceError("candidate deck block is missing")
    return match.group(1)


def authenticate_inputs(root: Path = ROOT) -> dict[str, object]:
    """Authenticate every frozen input before an executor can be called."""
    result = validate(root, root / OVERLAY_PATH)
    if result["semantic_runtime"] != RUNTIME:
        raise ProvenanceError("semantic runtime identity mismatch")
    overlay = json.loads((root / OVERLAY_PATH).read_text(encoding="utf-8"))
    if overlay.get("overlay_id") != OVERLAY_ID:
        raise ProvenanceError("unexpected provenance overlay identity")
    verified = verify_overlay(root, root / OVERLAY_PATH)["verified_decks"]
    if len(verified) != 10:
        raise ProvenanceError("all ten Baseline 005 decks are required")
    manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    rows = {row["deck_key"]: row for row in manifest.get("decks", [])}
    if rows.get("bebop_rocksteady", {}).get("sha256") != BEBOP_ROCKSTEADY_SHA256:
        raise ProvenanceError("Baseline 005 Bebop & Rocksteady identity mismatch")
    _candidate_text(root)  # Ensure the candidate is parseable before dispatch.
    return {
        **result,
        "overlay_id": OVERLAY_ID,
        "baseline_deck_count": len(verified),
        "bebop_rocksteady_sha256": BEBOP_ROCKSTEADY_SHA256,
        "manifest_path": MANIFEST_PATH,
        "candidate_path": CANDIDATE_PATH,
        "snapshot_path": SNAPSHOT_PATH,
    }


def build_schedule(root: Path = ROOT) -> list[dict[str, object]]:
    """Build the immutable 9 x 100, balanced, deterministic schedule."""
    manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    decks = {row["deck_key"]: row for row in manifest["decks"]}
    opponents = sorted(key for key in decks if key != "bebop_rocksteady")
    schedule: list[dict[str, object]] = []
    for opponent_index, opponent in enumerate(opponents):
        for offset in range(GAMES_PER_MATCHUP):
            orientation = "candidate_first" if offset < 50 else "opponent_first"
            seed = 1_000_000 + opponent_index * GAMES_PER_MATCHUP + offset
            schedule.append(
                {
                    "game_id": f"bad_guys_cronies_sandbox_0_2--{opponent}:{orientation}:{seed}",
                    "pairing_id": f"bebop_rocksteady--{opponent}",
                    "opponent": opponent,
                    "orientation": orientation,
                    "seed": seed,
                    "seats": ["bad_guys_cronies_sandbox_0_2", opponent]
                    if orientation == "candidate_first"
                    else [opponent, "bad_guys_cronies_sandbox_0_2"],
                }
            )
    validate_schedule(
        schedule,
        expected_games=EXPECTED_GAMES,
        expected_matchups=EXPECTED_MATCHUPS,
        games_per_matchup=GAMES_PER_MATCHUP,
    )
    return schedule


def run_calibration(
    root: Path = ROOT,
    checkpoint: Path | None = None,
    *,
    executor: Callable[[dict[str, object]], dict[str, object]] | None = None,
    writer_id: str = "bad-guys-cronies-sandbox-0-2",
) -> dict[str, object]:
    """Authenticate, construct, and run the guarded schedule.

    Supplying ``executor`` is the supported integrity-test seam.  The default
    executor is the only path that invokes the actual game simulator, and it is
    reached only after input authentication and schedule validation.
    """
    authenticate_inputs(root)
    schedule = build_schedule(root)
    if checkpoint is None:
        raise ValueError("a new checkpoint path is required")
    if executor is None:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as candidate_file:
            candidate_file.write(_candidate_text(root))
            candidate_path = Path(candidate_file.name)

        def execute(row: dict[str, object]) -> dict[str, object]:
            opponent = str(row["opponent"])
            manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
            opponent_row = next(item for item in manifest["decks"] if item["deck_key"] == opponent)
            candidate = DeckSpec("bad_guys_cronies_sandbox_0_2", str(candidate_path))
            opponent_spec = DeckSpec(opponent, opponent_row["source_path"])
            seats = (candidate, opponent_spec)
            if row["orientation"] == "opponent_first":
                seats = (opponent_spec, candidate)
            spec = GameSpec(
                str(row["game_id"]),
                str(row["pairing_id"]),
                int(row["seed"]),
                str(row["orientation"]),
                seats,
            )
            result = run_smoke_game(root, spec)
            return {"game_id": str(row["game_id"]), **result}

    else:
        execute = executor
    return run_checkpointed_schedule(
        schedule,
        checkpoint,
        execute,
        writer_id=writer_id,
        expected_matchups=EXPECTED_MATCHUPS,
        games_per_matchup=GAMES_PER_MATCHUP,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    args = parser.parse_args()
    payload = run_calibration(checkpoint=args.checkpoint)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

