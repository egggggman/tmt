from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(1,str(ROOT))
from scripts.calibration_runtime_wrapper import preflight
preflight(ROOT,'docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V16.json','10BDC8CD2C78BBA7C0777E71B10E15592655DFA353859A01D6BE94DAE36A8EC8','docs/cardcade/CALIBRATION_V1_20260922T003835Z_7b0b688c7051/LAUNCHER_RELEASE_MANIFEST_V1.json','6FFE6933692E2C2010672720F2C7A0960A088A45AC01BE996C6A4236D31B4E00')
from tmnt_design_studio.calibration_runner import execute_protocol
from tmnt_design_studio.calibration_executor import execute_member
seed_path = ROOT / 'docs/cardcade/CALIBRATION_SEED_TABLE_V2.json'
output_path = Path('G:\\cardcade\\calibration-runs\\CALIBRATION_V1_20260922T003835Z_7b0b688c7051')
execute_protocol(
    seed_path,
    output_path,
    lambda member, duplicate: execute_member(ROOT, member, duplicate),
    strict=True,
    expected_seed_table_sha256='6BE94F69A2E9432E615AEA7A8592D68B6537998B3F7355A60191A29E71DC6E5C',
)
