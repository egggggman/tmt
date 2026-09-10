"""Reproducible V1/V2 interface comparison. Never produces fitness/balance scores."""

from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1 = "f3814ae2fc1c9b344960167fcaff5c9630a0a075"
FROZEN = "de52f57a24a5c29a258573ad673051a0aa5c7e5c"
CHANGED = {"engine07.py", "pilot07.py", "stage002.py", "smoke01.py"}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def encode(value):
    if is_dataclass(value):
        return encode(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [encode(v) for v in value]
    return value


def digest(value):
    return hashlib.sha256(json.dumps(encode(value), sort_keys=True).encode()).hexdigest()


def ast_text(node):
    return ast.dump(node, include_attributes=False)


def source_audit():
    """Compare the whole frozen source after reversing only audited interface edits."""
    identities = {}
    policy_bodies = {}
    for relative in (
        git("ls-tree", "-r", "--name-only", FROZEN, "src", "decks").decode().splitlines()
    ):
        old = git("show", f"{FROZEN}:{relative}")
        v1 = git("show", f"{V1}:{relative}")
        current = (ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
        assert old == v1, f"V1 differs from gameplay freeze: {relative}"
        identities[relative] = {
            "frozen_git_blob": git("rev-parse", f"{FROZEN}:{relative}").decode().strip(),
            "candidate_lf_sha256": hashlib.sha256(current).hexdigest(),
        }
        if Path(relative).name not in CHANGED:
            assert old.replace(b"\r\n", b"\n") == current, f"frozen file changed: {relative}"
            continue
        before, after = ast.parse(old), ast.parse(current)
        filename = Path(relative).name
        if filename == "pilot07.py":
            for original_class in before.body:
                if not isinstance(original_class, ast.ClassDef):
                    continue
                updated_class = next(
                    n
                    for n in after.body
                    if isinstance(n, ast.ClassDef) and n.name == original_class.name
                )
                for method, updated in zip(original_class.body, updated_class.body, strict=True):
                    assert type(method) is type(updated)
                    if isinstance(method, ast.FunctionDef):
                        assert ast_text(ast.Module(body=method.body, type_ignores=[])) == ast_text(
                            ast.Module(body=updated.body, type_ignores=[])
                        ), f"policy body changed: {original_class.name}.{method.name}"
                        assert ast_text(ast.Module(body=method.args.defaults, type_ignores=[])) == (
                            ast_text(ast.Module(body=updated.args.defaults, type_ignores=[]))
                        )
                        assert [ast_text(x) for x in method.decorator_list] == [
                            ast_text(x) for x in updated.decorator_list
                        ]
                        policy_bodies[f"{original_class.name}.{method.name}"] = digest(
                            [ast_text(n) for n in method.body]
                        )
            # Only imports and Priority's annotation may differ.
            after.body = [n for n in after.body if not isinstance(n, ast.ImportFrom)]
            before.body = [n for n in before.body if not isinstance(n, ast.ImportFrom)]
            for node in ast.walk(after):
                if isinstance(node, ast.Name) and node.id == "PriorityViewV2":
                    node.id = "GameView"
        elif filename == "engine07.py":
            after.body = [
                n
                for n in after.body
                if not (
                    isinstance(n, ast.ImportFrom)
                    and n.module == "tmnt_design_studio.pilot_input_v2"
                )
            ]
            old_game = next(
                n for n in before.body if isinstance(n, ast.ClassDef) and n.name == "Game"
            )
            new_game = next(
                n for n in after.body if isinstance(n, ast.ClassDef) and n.name == "Game"
            )
            new_game.body = [
                n
                for n in new_game.body
                if not (
                    isinstance(n, ast.FunctionDef) and n.name in ("pilot_view", "priority_view")
                )
            ]
            old_public = next(n for n in old_game.body if getattr(n, "name", "") == "public_view")
            new_public = next(n for n in new_game.body if getattr(n, "name", "") == "public_view")
            new_public.body[0] = old_public.body[0]
            for node in ast.walk(after):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    lengths = {"ScryViewV2": 3, "HandBottomDrawViewV2": 2, "DiscardDrawViewV2": 2}
                    if node.func.id in lengths:
                        node.args = node.args[: lengths[node.func.id]]
                        node.func.id = node.func.id.removesuffix("V2")
        else:
            for node in ast.walk(after):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("pilot_view", "priority_view")
                ):
                    node.func.attr = "public_view"
                    node.args = []
        assert ast_text(before) == ast_text(after), f"non-interface logic changed: {relative}"
    return {
        "source_identities": identities,
        "policy_body_ast_sha256": policy_bodies,
        "whole_source_after_interface_reversal_equal": True,
    }


def worker(source, version, output):
    sys.path.insert(0, str(source))
    from tmnt_design_studio import engine07 as engine
    from tmnt_design_studio import pilot07, smoke01, stage002
    from tmnt_design_studio.card_interpreter07 import HandBottomDrawProgram, ScryProgram

    binding_counts = Counter()

    class Recorder:
        """Test-only passive recorder; the frozen method makes every choice."""

        def __init__(self, policy):
            self.policy = policy
            self.calls = []

        def __getattr__(self, hook):
            method = getattr(self.policy, hook)

            def choose(view, options, *args):
                if version == "v2":
                    assert view.schema_version == 2
                    context = getattr(view, "context", view)
                    owner = context.observer_index
                    if hook == "choose_priority":
                        assert view.priority_player == owner
                        assert all(o.player_index == owner for o in options)
                        assert all(o.priority_epoch == view.priority_epoch for o in options)
                        if owner != context.active_player:
                            binding_counts[f"nonactive_priority:{owner}"] += 1
                    elif hasattr(view, "player_index"):
                        assert view.player_index == owner
                    else:
                        assert all(o.player_index == owner for o in options)
                        assert view.hands[1 - owner] == ()
                    binding_counts[f"{hook}:{owner}"] += 1
                choice = method(view, options, *args)
                assert choice in options
                self.calls.append(encode((hook, options, args, choice)))
                return choice

            return choose

    results = []
    for policy_type in (pilot07.AcceptancePilot, pilot07.PassingPilot):
        for runner_name, runner, specs in (
            ("stage", stage002.run_game, (stage002.stage_games()[0], stage002.stage_games()[2])),
            ("smoke", smoke01.run_smoke_game, smoke01.smoke_games()[:2]),
        ):
            for spec in specs:
                recorder = Recorder(policy_type())
                snapshot = runner(ROOT, spec, recorder)
                results.append(
                    {
                        "case": f"{policy_type.__name__}:{runner_name}:{spec.game_id}",
                        "calls": recorder.calls,
                        "snapshot": snapshot,
                    }
                )
        for seat in (0, 1):
            recorder = Recorder(policy_type())
            land = engine.CardFact("Plains", "", 0, "Basic Land — Plains")
            game = engine.Game(([land] * 30, [land] * 30), seed=411)
            game.begin_turn()
            game._active_player = seat
            game.scry_chooser = recorder.choose_scry
            game.hand_bottom_draw_chooser = recorder.choose_hand_bottom_draw
            game.discard_draw_chooser = recorder.choose_discard_draw
            game.scry(seat, ScryProgram(2), source_card="Public", oracle_fragment="Scry 2.")
            program = HandBottomDrawProgram(1, 1, True, True)
            plan = game.choose_hand_bottom_draw(seat, program)
            game.commit_hand_bottom_draw(
                seat,
                program,
                plan,
                source_id="public-source",
                oracle_fragment="You may put a card from your hand on the bottom of your "
                "library. If you do, draw a card.",
            )
            text = "Whenever this creature attacks, you may discard a card. If you do, draw a card."
            attacker = game.create_permanent(
                engine.CardFact("Public attacker", "", 0, "Creature", text, 2, 2),
                seat,
                summoning_sick=False,
            )
            game.advance_to(engine.TurnStep.DECLARE_ATTACKERS)
            game.resolve_attack_pt_effects([attacker])
            stage002._drain_priority(game, recorder)
            assert game.discard_draw_evidence
            results.append(
                {
                    "case": f"{policy_type.__name__}:private-transactions:{seat}",
                    "calls": recorder.calls,
                    "snapshot": game.snapshot(),
                }
            )
            recorder = Recorder(policy_type())
            game = engine.Game(([land] * 30, [land] * 30), seed=412)
            game.begin_turn()
            game._active_player = seat
            sneak_text = (
                "Sneak {W} (You may cast this spell for {W} if you also return an unblocked "
                "attacker you control to hand during the declare blockers step. "
                "It enters tapped and attacking.)"
            )
            game.set_hand_for_testing(
                seat,
                [
                    engine.CardFact(
                        "Public Sneak", "{3}{W}", 4, "Creature", sneak_text, 4, 4, ("Sneak",)
                    )
                ],
            )
            game.create_permanent(land, seat, summoning_sick=False)
            attacker = game.create_permanent(
                engine.CardFact("Public attacker", "", 0, "Creature", "", 2, 2),
                seat,
                summoning_sick=False,
            )
            game.advance_to(engine.TurnStep.DECLARE_ATTACKERS)
            game.execute_attack_action(
                engine.ActionOption(
                    engine.ActionKind.DECLARE_ATTACKERS, seat, attacker_ids=(attacker.object_id,)
                )
            )
            game.execute_block_action(
                engine.ActionOption(engine.ActionKind.DECLARE_BLOCKERS, 1 - seat)
            )
            assert game.step is engine.TurnStep.DECLARE_BLOCKERS
            while game.step is engine.TurnStep.DECLARE_BLOCKERS:
                options = game.legal_sneak_actions(seat)
                view = game.pilot_view(seat) if version == "v2" else game.public_view()
                choice = recorder.choose_sneak(view, options)
                game.execute_sneak_action(choice)
                stage002._drain_priority(game, recorder)
            stage002._resolve_combat_damage_steps(game, recorder)
            results.append(
                {
                    "case": f"{policy_type.__name__}:sneak-transaction:{seat}",
                    "calls": recorder.calls,
                    "snapshot": game.snapshot(),
                }
            )
    output.write_text(json.dumps({"results": results, "bindings": dict(binding_counts)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("v1", "v2"))
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.worker:
        worker(args.source, args.worker, args.output)
        return
    packet = {
        "status": "CANDIDATE_VALIDATION_ONLY",
        "v1_commit": V1,
        "frozen_gameplay_commit": FROZEN,
        "assessment_baseline_accepted": False,
        "fitness_scoring": False,
        "source_audit": source_audit(),
    }
    with tempfile.TemporaryDirectory(prefix="pilot-v2-", dir=ROOT) as temp:
        work = Path(temp)
        archive = git("archive", "--format=zip", V1, "src")
        with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
            zipped.extractall(work)
        for version, source in (("v1", work / "src"), ("v2", ROOT / "src")):
            subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--worker",
                    version,
                    "--source",
                    str(source),
                    "--output",
                    str(work / f"{version}.json"),
                ],
                check=True,
                cwd=ROOT,
            )
        old = json.loads((work / "v1.json").read_text())
        new = json.loads((work / "v2.json").read_text())
        assert old["results"] == new["results"], "STOP: options, choices or gameplay traces differ"
        packet["paired_runs"] = [
            {
                "case": row["case"],
                "decision_count": len(row["calls"]),
                "complete_options_and_choices_sha256": digest(row["calls"]),
                "consequent_snapshot_sha256": digest(row["snapshot"]),
                "v1_v2_equal": True,
            }
            for row in new["results"]
        ]
        packet["decision_owner_bindings"] = new["bindings"]
        trace_path = args.output.with_suffix(".traces.json.gz")
        trace_path.write_bytes(
            gzip.compress(json.dumps({"v1": old, "v2": new}, sort_keys=True).encode(), mtime=0)
        )
        packet["paired_trace_artifact"] = {
            "path": str(trace_path.relative_to(ROOT))
            if trace_path.is_absolute()
            else str(trace_path),
            "sha256": hashlib.sha256(trace_path.read_bytes()).hexdigest(),
        }
        for seat in (0, 1):
            for hook in (
                "choose_main_action",
                "choose_attack",
                "choose_blocks",
                "choose_sneak",
                "choose_scry",
                "choose_hand_bottom_draw",
                "choose_discard_draw",
            ):
                assert new["bindings"].get(f"{hook}:{seat}", 0) > 0, (hook, seat)
            assert new["bindings"].get(f"nonactive_priority:{seat}", 0) > 0
    for relative in (
        "src/tmnt_design_studio/pilot_input_v2.py",
        "scripts/validate_pilot_input_v2.py",
        "tests/test_pilot_input_v2.py",
        "tests/conftest.py",
        "tests/test_smoke01_runner.py",
        "tests/test_stage02_runner.py",
    ):
        packet["source_audit"]["source_identities"][relative] = {
            "candidate_lf_sha256": hashlib.sha256(
                (ROOT / relative).read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()
        }
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "packet": str(args.output),
                "paired_runs": len(packet["paired_runs"]),
                "status": packet["status"],
            }
        )
    )


if __name__ == "__main__":
    main()
