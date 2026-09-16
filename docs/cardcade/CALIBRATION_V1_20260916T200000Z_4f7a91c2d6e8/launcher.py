from pathlib import Path
import json, py_compile
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'docs/cardcade/CALIBRATION_V1_20260916T200000Z_4f7a91c2d6e8'
PACKET=json.loads((ROOT/'docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V10.json').read_bytes())
assert PACKET['scheme']=='calibration-release-baseline-refresh-v10'
assert PACKET['execution_authorized'] is False
assert PACKET['accepted_runtime']=='05f6b87c0977ee99d650a016215ea9606eb1fe33'
assert PACKET['protocol_identity']=='96fc43ec3203938eb385618f6187f8496b93ecd3'
SEED_HASH='6BE94F69A2E9432E615AEA7A8592D68B6537998B3F7355A60191A29E71DC6E5C'
assert PACKET['seed_table_v2']['accepted_sha256']==SEED_HASH
assert PACKET['seed_table_v2']['accepted_entropy_sha256']=='E5E3824A4B0590F275F643E86BE87D0E5230FDBEABEF5C798A92DFAE8CBC64BB'
assert PACKET['seed_table_v2']['rows']==184320 and PACKET['seed_table_v2']['orientation_pairs']==92160
from tmnt_design_studio.calibration_runner import execute_protocol
from tmnt_design_studio.calibration_executor import execute_member
launcher=Path(__file__)
before=launcher.read_bytes()
py_compile.compile(str(launcher),doraise=True)
assert launcher.read_bytes()==before
execute_protocol(ROOT/'docs/cardcade/CALIBRATION_SEED_TABLE_V2.json',OUT,lambda m,d: execute_member(ROOT,m,d),strict=True,expected_seed_table_sha256=SEED_HASH)