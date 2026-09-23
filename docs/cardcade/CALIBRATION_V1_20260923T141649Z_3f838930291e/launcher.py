from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(1,str(ROOT))
from scripts.calibration_runtime_wrapper import preflight
preflight(ROOT,'docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V16.json','10BDC8CD2C78BBA7C0777E71B10E15592655DFA353859A01D6BE94DAE36A8EC8','docs/cardcade/CALIBRATION_V1_20260923T141649Z_3f838930291e/LAUNCHER_RELEASE_MANIFEST_V1.json','6F0C0F9852BCCBA912A168133ECA307F78F98F82AB3B26945A0511DB98B5C7B6')
from tmnt_design_studio.calibration_runner import execute_protocol
from tmnt_design_studio.calibration_executor import execute_member
seed_path = ROOT / 'docs/cardcade/CALIBRATION_SEED_TABLE_V2.json'
output_path = Path('G:\\cardcade\\calibration-runs\\CALIBRATION_V1_20260923T141649Z_3f838930291e')
execute_protocol(
    seed_path,
    output_path,
    lambda member, duplicate: execute_member(ROOT, member, duplicate),
    strict=True,
    expected_seed_table_sha256='6BE94F69A2E9432E615AEA7A8592D68B6537998B3F7355A60191A29E71DC6E5C',
)
