"""Preserve source-based V2 readiness findings; never import Game or a Pilot."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "fa3f4944a7209f22e70d783d9a7f9abca3b37534"
GAMEPLAY = "de52f57a24a5c29a258573ad673051a0aa5c7e5c"
SPEC = "docs/cardcade/POST_ACTION_32_PILOT_FITNESS_ASSESSMENT_SPEC.md"
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


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def lf(path):
    return path.read_bytes().replace(b"\r\n", b"\n")


def build():
    identities = {}
    for relative in (
        git("ls-tree", "-r", "--name-only", BASELINE, "src", "decks").decode().splitlines()
    ):
        accepted = git("show", f"{BASELINE}:{relative}").replace(b"\r\n", b"\n")
        current = lf(ROOT / relative)
        if current != accepted:
            raise ValueError(f"accepted source/deck drift: {relative}")
        identities[relative] = {
            "accepted_git_blob": git("rev-parse", f"{BASELINE}:{relative}").decode().strip(),
            "lf_sha256": sha(current),
        }
    if lf(ROOT / SPEC) != git("show", f"{BASELINE}:{SPEC}").replace(b"\r\n", b"\n"):
        raise ValueError("accepted specification drift")
    projection = ast.parse(lf(ROOT / "src/tmnt_design_studio/pilot_input_v2.py"))
    fields = {
        node.name: [row.target.id for row in node.body if isinstance(row, ast.AnnAssign)]
        for node in projection.body
        if isinstance(node, ast.ClassDef)
    }
    engine_path = "src/tmnt_design_studio/engine07.py"
    source = lf(ROOT / engine_path).decode()
    tree = ast.parse(source)
    game = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Game")
    anchors = {}
    for name in (
        "choose_hand_bottom_draw",
        "commit_hand_bottom_draw",
        "choose_discard_draw",
        "commit_discard_draw",
        "draw",
    ):
        method = next(n for n in game.body if isinstance(n, ast.FunctionDef) and n.name == name)
        anchors[name] = {
            "source": engine_path,
            "start_line": method.lineno,
            "end_line": method.end_lineno,
            "body_ast_sha256": sha(ast.dump(method, include_attributes=False).encode()),
            "source_excerpt": ast.get_source_segment(source, method),
        }
    return {
        "status": "INCONCLUSIVE_SUITE_READINESS",
        "artifact_kind": "source_based_preparation_diagnostic_not_sealed_fixture_packet",
        "conclusion_method": "manual oracle-feasibility review; script authenticates sources only",
        "accepted_interface_baseline": {"name": "pilot-input-v2", "commit": BASELINE},
        "main_fast_forward_commit": BASELINE,
        "frozen_gameplay_reference": GAMEPLAY,
        "accepted_specification_commit": "ca9757b956eafc4b8d03c495dabb03eaab6fe931",
        "specification_lf_sha256": sha(lf(ROOT / SPEC)),
        "diagnostic_source_lf_sha256": sha(lf(Path(__file__))),
        "source_identities": identities,
        "v2_dataclass_fields": fields,
        "transaction_source_anchors": anchors,
        "blocking_hooks": ["choose_hand_bottom_draw", "choose_discard_draw"],
        "unresolved_obligation": (
            "At least two input-grounded action-required cases per hook, alongside four forced, "
            "four resource and four boundary cases; no hidden-Draw or belief-model oracle."
        ),
        "design_paths_reviewed": [
            {
                "path": "nonempty_library_filter_for_needed_resource",
                "finding": "A needed card on the hidden top cannot establish guaranteed improvement.",
                "countercase": "An unseen duplicate of the selected card supplies no new card facts.",
            },
            {
                "path": "filter_redundant_land_or_unpayable_card",
                "finding": "Visible redundancy does not establish a strictly better hidden replacement.",
            },
            {
                "path": "hand_bottom_empty_library",
                "finding": "The selected card is bottomed then drawn; no required resource gain proven.",
            },
            {
                "path": "discard_empty_library",
                "finding": "Taking the option causes failed Draw; supports restraint, not useful action.",
            },
            {
                "path": "empty_hand_or_singleton_option",
                "finding": "Boundary/legality checks cannot substitute for tactical/useful-action quota.",
            },
            {
                "path": "discard_synergy_recursion_or_prior_inspection",
                "finding": "No concrete eligible oracle established; cannot add missing rules, "
                "graveyard/history observations or a Pilot memory/knowledge policy.",
            },
        ],
        "claim_limit": "Not a universal impossibility proof and not a measured Pilot failure.",
        "quota_accounting": {
            hook: {
                "required": {"forced": 4, "resource": 4, "boundary": 4},
                "sealed": 0,
                "status": "unresolved"
                if hook in ("choose_hand_bottom_draw", "choose_discard_draw")
                else "not_certified_after_controlling_stop",
            }
            for hook in HOOKS
        },
        "canonical_fixtures_required": 96,
        "canonical_fixtures_sealed": 0,
        "privacy_K": None,
        "final_planned_pilot_invocations": None,
        "unsealed_count_formula": "2304 + 4*K",
        "seeds_transformations_reconstruction": "unsealed; no partial suite promoted",
        "actual_pilot_invocations_this_preparation": 0,
        "actual_game_instantiations_this_preparation": 0,
        "oracle_continuations_executed_this_preparation": 0,
        "fitness_scoring_authorized": False,
        "calibration": "BLOCKED",
        "action_33_authorized": False,
        "prototype_0_3_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build()
    payload = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
    args.output.write_bytes(payload)
    args.output.with_name(args.output.name + ".sha256").write_bytes(
        (sha(payload) + "  " + args.output.name + "\n").encode()
    )
    print(result["status"] + "; Pilot invocations: 0; canonical fixtures sealed: 0")
    raise SystemExit(2)


if __name__ == "__main__":
    main()
