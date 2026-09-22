import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V16 = ROOT / "docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V16.json"
V17 = ROOT / "docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V17.json"


def git_blob(path):
    relative = path.relative_to(ROOT).as_posix()
    return subprocess.check_output(["git", "show", f"HEAD:{relative}"])


def test_runtime_refresh_uses_existing_identity_format_and_preserves_v16():
    v16_bytes = git_blob(V16)
    v17 = json.loads(git_blob(V17))

    assert hashlib.sha256(v16_bytes).hexdigest().upper() == (
        "10BDC8CD2C78BBA7C0777E71B10E15592655DFA353859A01D6BE94DAE36A8EC8"
    )
    assert v17["scheme"] == "calibration-release-baseline-refresh-v17"
    assert v17["execution_authorized"] is False
    assert v17["main_commit"] == "60acd013b28dc9d8cb46c5c5520c11e9e3943627"
    assert v17["accepted_runtime"] == v17["main_commit"]
    assert v17["previous_runtime"] == "d0b6b728c3cf0d6d883bb80a398c4b3d99a1259e"
    assert v17["protocol_identity"] == "96fc43ec3203938eb385618f6187f8496b93ecd3"
    assert (
        v17["seed_table_v2_sha256"]
        == "6BE94F69A2E9432E615AEA7A8592D68B6537998B3F7355A60191A29E71DC6E5C"
    )
    assert v17["schedule"]["distinct_games"] == 184320
    assert v17["schedule"]["executions"] == 368640
    assert v17["historical_v16_baseline"]["immutable"] is True
    assert v17["pr_181"]["production_execution_performed"] is False
