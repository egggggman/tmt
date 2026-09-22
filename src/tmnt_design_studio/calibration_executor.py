"""Adapter from ProtocolMember records to fresh Cardcade Stage 002 games."""

import hashlib
import json
from functools import cache
from pathlib import Path

from tmnt_design_studio.calibration_runner import ProtocolMember
from tmnt_design_studio.pilot07 import AcceptancePilot
from tmnt_design_studio.stage002 import DeckSpec, GameSpec, run_game


@cache
def _frozen_release_manifest(root_text: str) -> dict:
    root = Path(root_text)
    return json.loads(
        (root / "docs/cardcade/CALIBRATION_RELEASE_MANIFEST_CAPACITY_V1.json").read_text()
    )


@cache
def _frozen_deck_path_cached(root_text: str, deck: str) -> str:
    root = Path(root_text)
    expected = _frozen_release_manifest(root_text)["deck_hashes"][deck].lower()
    for candidate in sorted((root / "decks" / deck).glob("PROTOTYPE_*.txt")):
        if hashlib.sha256(candidate.read_bytes()).hexdigest().lower() == expected:
            return candidate.relative_to(root).as_posix()
    raise RuntimeError(f"frozen deck artifact not found: {deck}")


def _frozen_deck_path(root: Path, deck: str) -> str:
    return _frozen_deck_path_cached(str(root.resolve()), deck)


def execute_member(
    root: Path, member: ProtocolMember, duplicate_index: int = 0
) -> dict[str, object]:
    """Run one fresh game; duplicate_index is identity only and never changes inputs."""
    seats = tuple(DeckSpec(deck, _frozen_deck_path(root, deck)) for deck in member.decks)
    spec = GameSpec(
        member.member_id, f"p{member.pair_index:02d}", member.seed, member.orientation, seats
    )
    result = run_game(root, spec, AcceptancePilot())
    if result.get("terminal") is not True:
        raise RuntimeError("executor returned without terminal state")
    turns_started = result.get("turns_started")
    if type(turns_started) is not int or turns_started != result.get("turn"):
        raise RuntimeError("executor returned without authoritative turns_started")
    if not 0 <= turns_started < 120:
        raise RuntimeError("attempted to begin turn 120")
    result["member_id"] = member.member_id
    return result
