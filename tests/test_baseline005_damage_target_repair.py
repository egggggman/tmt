"""Exact regression fixtures for the Baseline 005 damage-target failures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from run_objective_balance_lab_round1 import ROOT, DeckSpec, GameSpec  # noqa: E402

from tmnt_design_studio.pilot07 import AcceptancePilot  # noqa: E402
from tmnt_design_studio.stage002 import run_game  # noqa: E402

SEEDS = (
    108687052940046901150408742631474974084904382487031619852802729825648363318082,
    63960804773867057066244079686420048244385109677095274722534118927427377020047,
)


def _spec(seed: int) -> GameSpec:
    import json

    manifest = json.loads(
        (ROOT / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json").read_text()
    )
    paths = {row["deck_key"]: row["source_path"] for row in manifest["decks"]}
    return GameSpec(
        "baseline005-damage-target-regression",
        "krang-vs-raphael",
        seed,
        "canonical",
        (DeckSpec("krang", paths["krang"]), DeckSpec("raphael", paths["raphael"])),
    )


def test_preserved_krang_raphael_seeds_complete_deterministically():
    for seed in SEEDS:
        first = run_game(ROOT, _spec(seed), AcceptancePilot())
        second = run_game(ROOT, _spec(seed), AcceptancePilot())
        assert json.dumps(first, sort_keys=True, separators=(",", ":")) == json.dumps(
            second, sort_keys=True, separators=(",", ":")
        )
        assert first["winner"] in {"krang", "raphael"}
