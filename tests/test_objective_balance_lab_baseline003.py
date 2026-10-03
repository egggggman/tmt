"""Baseline 003 is an exact direct promotion of Combined 005 evidence."""

from copy import deepcopy

import pytest

from tools import validate_objective_balance_lab_baseline003_metrics as metrics


def test_combined_005_metrics_are_exact_baseline_003_reference():
    result = metrics.validate()
    assert result["status"] == "PASS"
    assert result["matchups"] == 45
    assert result["logical_games"] == 4500
    assert result["new_simulations"] == 0
    assert result["mean_matchup_balance_error"] == 0.176667


def test_direct_promotion_rejects_stale_metadata(monkeypatch):
    original_read = metrics.read

    def altered_read(relative):
        value = original_read(relative)
        if relative.endswith("OBL_BASELINE_003_MANIFEST.json"):
            value = deepcopy(value)
            value["environment_metrics"]["mean_matchup_balance_error"] = 0.189556
        return value

    monkeypatch.setattr(metrics, "read", altered_read)
    with pytest.raises(ValueError, match="Direct-promotion global metric mismatch"):
        metrics.validate()
