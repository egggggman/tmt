"""Adapter from ProtocolMember records to fresh Cardcade Stage 002 games."""

import hashlib
import json
from pathlib import Path

from tmnt_design_studio.calibration_runner import ProtocolMember
from tmnt_design_studio.pilot07 import AcceptancePilot
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, run_game


def _frozen_deck_path(root: Path, deck: str) -> str:
    manifest = json.loads(
        (root / "docs/cardcade/CALIBRATION_RELEASE_MANIFEST_CAPACITY_V1.json").read_text()
    )
    expected = manifest["deck_hashes"][deck].lower()
    for candidate in sorted((root / "decks" / deck).glob("PROTOTYPE_*.txt")):
        if hashlib.sha256(candidate.read_bytes()).hexdigest().lower() == expected:
            return candidate.relative_to(root).as_posix()
    raise RuntimeError(f"frozen deck artifact not found: {deck}")


def execute_member(
    root: Path, member: ProtocolMember, duplicate_index: int = 0
) -> dict[str, object]:
    """Run one fresh game; duplicate_index is identity only and never changes inputs."""
    seats = tuple(DeckSpec(deck, _frozen_deck_path(root, deck)) for deck in member.decks)
    spec = GameSpec(
        member.member_id, f"p{member.pair_index:02d}", member.seed, member.orientation, seats
    )
    result = run_game(root, spec, AcceptancePilot())
    if not result.get("terminal", False):
        raise RuntimeError("executor returned without terminal state")
    result["turns_started"] = int(result.get("turns_started", result.get("turns", 0)))
    result["member_id"] = member.member_id
    return result
