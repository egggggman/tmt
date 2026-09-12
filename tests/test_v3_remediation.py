"""Focused regression checks for the four authorized repairs."""

import importlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from tmnt_design_studio.engine07 import ActionKind
from tmnt_design_studio.pilot07 import AcceptancePilot, PassingPilot
from tmnt_design_studio.pilot_input_v2 import PriorityViewV2

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def runner(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("run_v3_remediation")


@pytest.fixture
def plan():
    return json.loads(
        (ROOT / "docs/cardcade/PILOT_FITNESS_V3_REMEDIATION_96_EXECUTION_PLAN.json").read_text()
    )


def test_four_corrected_domains_and_objectives(runner, plan):
    assert runner.fixtures() == plan["fixtures"]
    fixtures = {f["fixture_id"]: f for f in plan["fixtures"]}
    assert set(fixtures) == set(runner.IDS)
    priority = fixtures[runner.IDS[0]]
    assert [b["target_zone"] for b in priority["branches"]] == ["gone", "battlefield"]
    main = fixtures[runner.IDS[1]]["base"]
    assert main["view"]["hands"] == [[], []]
    assert [o["kind"] for o in main["options"]] == ["pass"]
    scry = fixtures[runner.IDS[2]]
    creatures = {
        c["object_id"]
        for c in scry["base"]["view"]["inspected_cards"]
        if "Creature" in c["type_line"]
    }
    expected = [o for o in scry["base"]["options"] if o["top_ids"] and o["top_ids"][0] in creatures]
    assert len(expected) == 4
    assert scry["oracle"]["acceptable"] == expected
    sneak = fixtures[runner.IDS[3]]["base"]
    assert sneak["view"]["step"] == "declare_blockers"
    assert [o["kind"] for o in sneak["options"]] == ["pass"]


def test_priority_contract_counter_and_pass_fallback(runner, plan):
    for o in plan["observations"]:
        if o["hook"] != "priority":
            continue
        view, options = runner.typed_inputs(o)
        assert isinstance(view, PriorityViewV2)
        assert view.priority_player == view.context.observer_index == o["seat"]
        chosen = AcceptancePilot().choose_priority(view, options)
        assert runner.encode(chosen) in o["expected_actions"]
        passed = PassingPilot().choose_priority(view, options)
        assert passed.kind is ActionKind.PASS_PRIORITY
        assert AcceptancePilot().choose_priority(view, (passed,)) == passed
        assert (
            AcceptancePilot().choose_priority(replace(view, stack_bottom_to_top=()), options)
            == passed
        )


def test_affected_policies_and_transform_inversion(runner, plan):
    canonical = {
        o["fixture_id"]: o
        for o in plan["observations"]
        if o["seat"] == 0 and o["variant"] == "canonical"
    }
    assert len(plan["observations"]) == 24
    for o in plan["observations"]:
        package = {k: o[k] for k in ("base", "expected_actions")}
        package = runner.original.rename(package, {v: k for k, v in o["id_mapping"].items()})
        if o["mirrored"]:
            package = runner.mirror(package)
        if o["variant"] == "option_permutation":
            package["base"]["options"].reverse()
        assert package == {k: canonical[o["fixture_id"]][k] for k in package}
        view, options = runner.typed_inputs(o)
        for cls in (AcceptancePilot, PassingPilot):
            returned = getattr(cls(), o["hook_method"])(view, options, **o["hook_kwargs"])
            assert returned in options
            match = runner.encode(returned) in o["expected_actions"]
            assert match == (cls is AcceptancePilot or o["category"] == "B")


def test_priority_pass_seat_sequence_mirror(runner):
    value = {"priority_player": 0, "consecutive_passes": [0, 1]}
    assert runner.mirror(value) == {"priority_player": 1, "consecutive_passes": [1, 0]}
    assert runner.mirror(runner.mirror(value)) == value
