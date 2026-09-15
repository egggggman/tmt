import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "calibration_v6_preflight", ROOT / "scripts/calibration_v6_preflight.py"
)
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
load_v6_seed_identity = _MODULE.load_v6_seed_identity

V6 = ROOT / "docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V6.json"
EXPECTED = "6BE94F69A2E9432E615AEA7A8592D68B6537998B3F7355A60191A29E71DC6E5C"


def test_real_v6_packet_uses_nested_accepted_seed_hash():
    identity = load_v6_seed_identity(V6)
    assert identity["seed_table_sha256"] == EXPECTED


def test_v6_schema_rejects_missing_nested_seed_object(tmp_path):
    packet = {"scheme": "calibration-release-baseline-refresh-v6", "execution_authorized": False}
    path = tmp_path / "v6.json"
    path.write_text(json.dumps(packet))
    with pytest.raises(ValueError, match="missing required fields"):
        load_v6_seed_identity(path)
