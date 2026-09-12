"""Harness checks use recording doubles, never the frozen Pilot policies."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def runner(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    return importlib.import_module("run_v3_path_a_scoring")


@pytest.fixture
def observations():
    path = ROOT / "docs/cardcade/PILOT_FITNESS_V3_PATH_A_288_EXECUTION_PLAN.json"
    return json.loads(path.read_text(encoding="utf-8"))["observations"]


@pytest.mark.parametrize(
    ("hook", "method"),
    [
        ("main", "choose_main_action"),
        ("attack", "choose_attack"),
        ("blocks", "choose_blocks"),
        ("priority", "choose_priority"),
        ("scry", "choose_scry"),
        ("sneak", "choose_sneak"),
    ],
)
def test_invokes_requested_hook_with_exact_sealed_inputs(runner, observations, hook, method):
    observation = next(o for o in observations if o["hook"] == hook)
    received = []

    def choose(self, view, options, **kwargs):
        received.append((runner.encode(view), runner.encode(options), kwargs))
        return options[0]

    recording_pilot = type("RecordingPilot", (), {method: choose})
    result = runner.invoke(observation, recording_pilot)
    assert received == [
        (observation["base"]["view"], observation["base"]["options"], observation["hook_kwargs"])
    ]
    assert result["returned_action"] == observation["base"]["options"][0]
    assert result["outcome"] == "RETURNED"


def test_legal_option_is_not_automatically_acceptable(runner, observations):
    observation = next(o for o in observations if o["fixture_id"] == "V3-P1-002")

    class EmptyAttack:
        def choose_attack(self, view, options):
            return next(o for o in options if not o.attacker_ids)

    result = runner.invoke(observation, EmptyAttack)
    assert result["legal_option_member"] is True
    assert result["returned_matches_expectation"] is False


def test_exception_is_recorded_once_without_fabricating_action(runner, observations):
    observation = next(o for o in observations if o["fixture_id"] == "V3-P2-004")
    seen = []

    class EmptySneak:
        def choose_sneak(self, view, options):
            seen.append(options)
            raise StopIteration("no supplied option")

    result = runner.invoke(observation, EmptySneak)
    assert seen == [()]
    assert result["outcome"] == "EXCEPTION"
    assert result["returned_action"] is None
    assert result["returned_matches_expectation"] is False
    assert result["exception"] == {"type": "StopIteration", "message": "no supplied option"}


def test_every_observation_is_typed_and_transforms_invert(runner, observations):
    assert len(observations) == 72
    canonical = {
        o["fixture_id"]: o
        for o in observations
        if o["variant"] == "canonical" and o["seat"] == o["source_seat"]
    }
    for o in observations:
        runner.typed_inputs(o)
        package = {"base": o["base"], "expected_actions": o["expected_actions"]}
        package = runner.rename(package, {v: k for k, v in o["id_mapping"].items()})
        if o["mirrored"]:
            package = runner.mirror(package)
        if o["variant"] == "option_permutation":
            package["base"]["options"].reverse()
        original = canonical[o["fixture_id"]]
        assert package == {
            "base": original["base"],
            "expected_actions": original["expected_actions"],
        }
