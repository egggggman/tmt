"""Round 6-A results remain tied to the preserved candidate and frozen cells."""

import json

import pytest

from tools import run_objective_balance_lab_round6a as r6
from tools.validate_objective_balance_lab_round6a import validate


def test_round6a_authenticated_result():
    validate()


def test_round6a_cell_mutation_fails_closed():
    payload = json.loads(r6.EVIDENCE.read_text(encoding="utf-8"))
    payload["cells"]["shredder"][0]["schedule"]["seed"] += 1
    with pytest.raises(AssertionError):
        r6.verify(payload, r6.r1.schedule())
