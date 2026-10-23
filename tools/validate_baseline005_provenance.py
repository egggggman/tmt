"""Authenticate Baseline 005 inputs without launching gameplay."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tmnt_design_studio.baseline005_provenance import ProvenanceError, verify_overlay

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = "c087f84bab4916b516ec6745f5a8e9f2a2d33f9117856bf959da4eb9a7be8e54"
CANDIDATE = "docs/design-studio/challengers/BAD_GUYS_CRONIES_SANDBOX_0_2_CANDIDATE.md"
SNAPSHOT = "cardcade/scryfall-tmt-pza-tmc-2026-08-13.json"
EXPECTED = {
    CANDIDATE: "cacc77648a4d1659b8ae640d95ac2672694e6951553980246e6d001e5152bfb4",
    SNAPSHOT: "56a53af4d0e6f92d8500b7330bbfd37215ab54fbfded0ca600a5452adc06d402",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path = ROOT, overlay: Path | None = None) -> dict[str, object]:
    overlay = (
        overlay
        or root
        / "docs/objective-balance-lab/baselines/OBL_BASELINE_005_PROVENANCE_OVERLAY_001.json"
    )
    verified = verify_overlay(root, overlay)
    identity: dict[str, str] = {}
    for relative, expected in EXPECTED.items():
        path = root / relative
        if not path.is_file():
            raise ProvenanceError(f"required identity is missing: {relative}")
        actual = sha256(path)
        if actual != expected:
            raise ProvenanceError(f"identity mismatch for {relative}: {actual} != {expected}")
        identity[relative] = actual
    return {
        "status": "PROVENANCE_PREFLIGHT_READY",
        "semantic_runtime": RUNTIME,
        "overlay_id": verified["schema"],
        "verified_deck_count": len(verified["verified_decks"]),
        "deck_methods": {row["deck_key"]: row["method"] for row in verified["verified_decks"]},
        "candidate_sha256": identity[CANDIDATE],
        "snapshot_sha256": identity[SNAPSHOT],
        "gameplay_simulation": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    result = validate()
    rendered = json.dumps(result, indent=2) + "\n"
    if args.json_output:
        args.json_output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
