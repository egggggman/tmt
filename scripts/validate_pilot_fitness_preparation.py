"""Read-only Pilot Fitness interface preflight; never imports or invokes a Pilot.

This is a preparation diagnostic, not the complete assessment/scoring harness.
Exit 2 means HQ must resolve suite readiness; it is not a Pilot failure.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE_REF = "de52f57a24a5c29a258573ad673051a0aa5c7e5c"
SPEC_REF = "ca9757b956eafc4b8d03c495dabb03eaab6fe931"
SOURCE_PATHS = (
    "src/tmnt_design_studio/engine07.py",
    "src/tmnt_design_studio/pilot07.py",
    "src/tmnt_design_studio/stage002.py",
)
HOOKS = (
    "choose_main_action",
    "choose_attack",
    "choose_blocks",
    "choose_sneak",
    "choose_scry",
    "choose_hand_bottom_draw",
    "choose_discard_draw",
    "choose_priority",
)


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def fields(tree: ast.Module, name: str) -> list[str]:
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
    return [
        n.target.id
        for n in cls.body
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
    ]


def report() -> dict:
    sources = {}
    for path in SOURCE_PATHS:
        frozen = git("show", f"{ENGINE_REF}:{path}")
        current = (ROOT / path).read_bytes()
        # Git's clean representation accommodates the repository's Windows checkout.
        clean_blob = git("hash-object", "--path=" + path, path).decode().strip()
        frozen_blob = git("rev-parse", f"{ENGINE_REF}:{path}").decode().strip()
        if clean_blob != frozen_blob:
            raise ValueError(f"Frozen source drift: {path}")
        sources[path] = {
            "git_blob": frozen_blob,
            "frozen_sha256": hashlib.sha256(frozen).hexdigest(),
            "checkout_sha256": hashlib.sha256(current).hexdigest(),
        }
    tree = ast.parse((ROOT / SOURCE_PATHS[0]).read_text(encoding="utf-8"))
    observed = {
        name: fields(tree, name)
        for name in (
            "GameView",
            "ScryView",
            "HandBottomDrawView",
            "DiscardDrawView",
            "ActionOption",
        )
    }
    expected = {
        "GameView": ["turn", "active_player", "phase", "step", "life", "hands", "battlefields"],
        "ScryView": ["player_index", "requested", "cards"],
        "HandBottomDrawView": ["player_index", "cards"],
        "DiscardDrawView": ["player_index", "cards"],
    }
    for name, names in expected.items():
        if observed[name] != names:
            raise ValueError(f"Interface premise changed: {name}")
    pilot_tree = ast.parse((ROOT / SOURCE_PATHS[1]).read_text(encoding="utf-8"))
    protocol = next(n for n in pilot_tree.body if isinstance(n, ast.ClassDef) and n.name == "Pilot")
    hooks = [n.name for n in protocol.body if isinstance(n, ast.FunctionDef)]
    if hooks != list(HOOKS):
        raise ValueError("Pilot protocol changed")
    spec_path = "docs/cardcade/POST_ACTION_32_PILOT_FITNESS_ASSESSMENT_SPEC.md"
    spec = git("show", f"{SPEC_REF}:{spec_path}")
    if git("hash-object", "--path=" + spec_path, spec_path) != git(
        "rev-parse", f"{SPEC_REF}:{spec_path}"
    ):
        raise ValueError("Accepted specification changed")
    return {
        "schema": "pilot-fitness-preparation-preflight-v1",
        "status": "INCONCLUSIVE_SUITE_READINESS",
        "is_sealed_assessment_packet": False,
        "engine_reference": ENGINE_REF,
        "specification_commit": SPEC_REF,
        "gate_audit_commit": "e28cd6dcd5532b84d38c45d3a710077e5cb589b4",
        "specification_sha256": hashlib.sha256(spec).hexdigest(),
        "source_identities": sources,
        "preflight_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "observed_view_fields": observed,
        "hook_assignment": [
            {
                "hook": h,
                "required_canonical_fixtures": 12,
                "forced": 4,
                "resource": 4,
                "boundary": 4,
            }
            for h in HOOKS
        ],
        "required_canonical_fixtures": 96,
        "sealed_canonical_fixtures": 0,
        "required_seats": [0, 1],
        "required_variants": ["canonical", "option_permutation", "identity_renaming"],
        "required_replays": 2,
        "planned_pilots": ["AcceptancePilot", "PassingPilot"],
        "privacy_eligible_fixture_list": None,
        "K": None,
        "final_invocation_count": None,
        "invocation_formula": "2304 + 4*K; K counts eligible seat versions",
        "pilot_invocations_performed": 0,
        "game_simulations_performed": 0,
        "blockers": [
            {
                "id": "PRIVATE_CHOICE_CONTEXT",
                "hooks": list(HOOKS[4:7]),
                "finding": (
                    "Only card identities/names and player index (plus Scry requested "
                    "count) are supplied."
                ),
                "missing_oracle_inputs": [
                    "life",
                    "battlefield",
                    "mana",
                    "library size",
                    "turn context",
                ],
                "consequence": (
                    "Context-dependent tactical obligations cannot be judged against "
                    "omitted facts; required forced-action quotas are not established."
                ),
            },
            {
                "id": "PRIORITY_STACK_CONTEXT",
                "hooks": ["choose_priority"],
                "finding": (
                    "GameView has no Stack description; ActionOption target_id "
                    "identifies the counter target but does not describe that spell or "
                    "its target/effect."
                ),
                "consequence": (
                    "Legality of countering is observable; tactical necessity and "
                    "target comparison are not established by legality alone."
                ),
            },
        ],
        "resolution_required": (
            "HQ must revise fixture/claim requirements or separately authorize "
            "an input-contract change; neither is performed here."
        ),
        "scoring_authorized": False,
    }


def main() -> int:
    print(json.dumps(report(), indent=2, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
