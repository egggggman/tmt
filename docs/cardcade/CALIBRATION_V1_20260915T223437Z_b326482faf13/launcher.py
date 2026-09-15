"""Single authorized V6 attempt. Frozen runtime; operational evidence only."""
import datetime
import hashlib
import itertools
import py_compile
import json
import pathlib
import platform
import shutil
import subprocess
import sys
import traceback

OUT = pathlib.Path(__file__).resolve().parent
ROOT = OUT.parents[2]
RUN_ID = OUT.name
BASELINE = '3d3df748f78d4403fa9872c90b97c15589b3a32f'
RUNTIME = 'ab2f8fb8a71d812e188f7955df9447e9a8fc5c6d'
PROTOCOL = '96fc43ec3203938eb385618f6187f8496b93ecd3'
SEED_HASH = '6BE94F69A2E9432E615AEA7A8592D68B6537998B3F7355A60191A29E71DC6E5C'
launcher_bytes = pathlib.Path(__file__).read_bytes()
py_compile.compile(str(pathlib.Path(__file__)), doraise=True)
if pathlib.Path(__file__).read_bytes() != launcher_bytes:
    raise RuntimeError('launcher changed during compile validation')
sys.path.insert(0, str(ROOT / 'src'))
from tmnt_design_studio.calibration_runner import execute_protocol, load_members, _atomic_write
from tmnt_design_studio.calibration_executor import execute_member, _frozen_deck_path
from tmnt_design_studio.stage002 import build_stage_manifest, reconcile_snapshot, DeckSpec, GameSpec

attempted = 0
returned = 0
current = None
stage_manifest = None
started = datetime.datetime.now(datetime.timezone.utc).isoformat()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def save(name, value):
    path = OUT / name
    if path.exists():
        raise RuntimeError('refusing to overwrite existing evidence: ' + name)
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    _atomic_write(path, raw)
    if path.read_bytes() != raw:
        raise RuntimeError('evidence read-back mismatch: ' + name)
    _atomic_write(OUT / (name + '.sha256'), (sha(raw) + '\n').encode())
    return sha(raw)

def capture(exc):
    frames = []
    tb = exc.__traceback__
    while tb:
        local = tb.tb_frame.f_locals
        frame = {'function': tb.tb_frame.f_code.co_name, 'line': tb.tb_lineno}
        for key in ('result', 'report'):
            if isinstance(local.get(key), dict):
                frame[key] = local[key]
        if 'game' in local and hasattr(local['game'], 'snapshot'):
            try:
                frame['authoritative_snapshot'] = local['game'].snapshot()
            except Exception as snapshot_error:
                frame['snapshot_error'] = repr(snapshot_error)
        frames.append(frame)
        tb = tb.tb_next
    return {'identity': current, 'error': str(exc), 'exception_type': type(exc).__name__,
            'traceback': traceback.format_exc(), 'frames': frames}

def executor(member, duplicate):
    global attempted, returned, current
    current = {'member_id': member.member_id, 'duplicate_index': duplicate,
               'protocol_execution_id': f'CP1:b{member.block:04d}:p{member.pair_index:02d}:o{"C" if member.orientation == "canonical" else "R"}:r{duplicate + 1}',
               'block': member.block, 'pair_index': member.pair_index,
               'orientation': member.orientation, 'seed': member.seed, 'decks': member.decks}
    try:
        if shutil.disk_usage(OUT).free < 64 * 1024 * 1024:
            raise RuntimeError('storage reserve exhausted before next execution')
        attempted += 1
        result = execute_member(ROOT, member, duplicate)
        returned += 1
        save(member.member_id + f'.r{duplicate + 1}.json', result)
        spec = GameSpec(member.member_id, f'p{member.pair_index:02d}', member.seed,
                        member.orientation, tuple(DeckSpec(deck, _frozen_deck_path(ROOT, deck)) for deck in member.decks))
        report = reconcile_snapshot(spec, result, stage_manifest)
        save(member.member_id + f'.r{duplicate + 1}.validation.json', report)
        if report['invariant_violations']:
            raise RuntimeError('invariant violation: ' + member.member_id)
        if report['stop_records']:
            kinds = sorted({item['kind'] for item in report['stop_records']})
            raise RuntimeError(f'conformance stop {kinds}: {member.member_id}')
        if attempted % 100 == 0:
            print(json.dumps({'run_id': RUN_ID, 'attempted_executions': attempted,
                              'returned_executions': returned, 'free_disk_bytes': shutil.disk_usage(OUT).free}), flush=True)
        return result
    except BaseException as exc:
        save('FAILED_EXECUTION.json', capture(exc))
        raise

try:
    if (OUT / 'RUN_MANIFEST.json').exists() or (OUT / 'RUN_STOP.json').exists():
        raise RuntimeError('attempt already exists; restart prohibited')
    if git('rev-parse', 'HEAD').decode().strip() != BASELINE:
        raise RuntimeError('release baseline mismatch')
    if git('diff', '--name-only', RUNTIME, BASELINE, '--', 'src', 'decks', 'cardcade', 'pyproject.toml', 'uv.lock').strip():
        raise RuntimeError('frozen runtime differs from release baseline')
    if git('diff', 'HEAD', '--', 'src', 'decks', 'cardcade', 'docs/cardcade/CALIBRATION_SEED_TABLE_V1.json', 'pyproject.toml', 'uv.lock').strip():
        raise RuntimeError('working runtime/input drift')
    refresh_path = ROOT / 'docs/cardcade/CALIBRATION_RELEASE_BASELINE_REFRESH_V6.json'
    refresh = json.loads(refresh_path.read_bytes())
    if refresh['accepted_runtime'] != RUNTIME or refresh['protocol_identity'] != PROTOCOL or refresh['seed_table_sha256'] != SEED_HASH:
        raise RuntimeError('V6 identity mismatch')
    if sha(refresh_path.read_bytes()).upper() != refresh_path.with_suffix('.json.sha256').read_text().strip().upper():
        raise RuntimeError('V6 sidecar mismatch')
    verified = {}
    def verify_nodes(value):
        if isinstance(value, dict):
            if 'windows_checkout_sha256' in value and 'path' in value:
                path = value['path']
                if sha((ROOT/path).read_bytes()).upper() != value['windows_checkout_sha256']:
                    raise RuntimeError('frozen checkout hash mismatch: ' + path)
                if sha(git('show', BASELINE + ':' + path)).upper() != value['git_blob_sha256']:
                    raise RuntimeError('frozen committed hash mismatch: ' + path)
                verified[path] = value
            for child in value.values():
                verify_nodes(child)
        elif isinstance(value, list):
            for child in value:
                verify_nodes(child)
    verify_nodes(refresh)
    release_manifest = json.loads((ROOT/'docs/cardcade/CALIBRATION_RELEASE_MANIFEST_CAPACITY_V1.json').read_bytes())
    if platform.python_version() != release_manifest['environment']['python']:
        raise RuntimeError('Python patch version mismatch')
    seed_path = OUT / 'frozen_v2_table.json'
    seed_path.write_bytes(git('show', BASELINE + ':docs/cardcade/CALIBRATION_SEED_TABLE_V2.json'))
    schedule = load_members(seed_path, strict=True, expected_sha256=SEED_HASH)
    pairs = list(itertools.combinations(sorted(refresh['decks'].keys()), 2))
    for index, member in enumerate(schedule):
        block, offset = divmod(index, 90)
        pair, orientation = divmod(offset, 2)
        decks = pairs[pair] if orientation == 0 else pairs[pair][::-1]
        if (member.block, member.pair_index, member.orientation, member.decks) != (block, pair, ('canonical','reversed')[orientation], decks):
            raise RuntimeError('frozen schedule order/deck membership mismatch: ' + member.member_id)
        if orientation and member.seed != schedule[index-1].seed:
            raise RuntimeError('paired orientation seed mismatch: ' + member.member_id)
    stage_manifest = build_stage_manifest(ROOT)
    save('RUN_MANIFEST.json', {'run_id': RUN_ID, 'started_utc': started, 'release_baseline': BASELINE,
         'frozen_runtime': RUNTIME, 'protocol_identity': PROTOCOL,
         'authorization': 'Explicit HQ Calibration Protocol V1 execution re-authorization in current session',
         'seed_table_sha256': SEED_HASH, 'verified_identities': verified, 'release_refresh': refresh,
         'python': sys.version, 'platform': platform.platform(), 'free_disk_bytes': shutil.disk_usage(OUT).free,
         'blocks': 2048, 'matchups_per_block': 45, 'distinct_games': 184320, 'executions': 368640,
         'strict': True, 'max_members': None, 'replacement_seeds': False, 'launcher_compile_sha256': sha(launcher_bytes), 'balance_analysis': False,
         'evidence_directory': str(OUT), 'launcher_sha256': sha(pathlib.Path(__file__).read_bytes()),
         'operational_validation': 'Frozen Stage002 reconcile_snapshot and its invariant/stop checks per execution; no outcome aggregation',
         'storage_reserve_bytes': 64 * 1024 * 1024})
    save('STAGE_VALIDATION_MANIFEST.json', stage_manifest)
    print(json.dumps({'run_id': RUN_ID, 'status': 'STARTING_FULL_SCHEDULE', 'output': str(OUT)}), flush=True)
    result = execute_protocol(seed_path, OUT, executor, strict=True, expected_seed_table_sha256=SEED_HASH)
    if result['completed_members'] != 184320 or attempted != 368640 or returned != 368640:
        raise RuntimeError('incomplete full schedule')
    save('RUN_RESULT.json', {'run_id': RUN_ID, 'status': 'COMPLETE_PENDING_AUDIT',
         'release_baseline': BASELINE, 'frozen_runtime': RUNTIME, 'completed_distinct_games': 184320,
         'completed_executions': returned, 'duplicate_mismatch_count': 0, 'failure_count': 0})
except BaseException as exc:
    ledger_path = OUT / 'EXECUTION_LEDGER.json'
    ledger = json.loads(ledger_path.read_bytes()) if ledger_path.exists() else {}
    stop = {'run_id': RUN_ID, 'status': 'FAIL_CLOSED_STOP', 'started_utc': started,
         'stopped_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'release_baseline': BASELINE, 'frozen_runtime': RUNTIME, 'protocol_identity': PROTOCOL,
         'seed_table_sha256': SEED_HASH, 'failed_execution': current,
         'attempted_executions': attempted, 'returned_executions': returned,
         'completed_distinct_games': ledger.get('completed_members', 0),
         'authenticated_duplicate_pairs': ledger.get('completed_members', 0),
         'failure_count': 1, 'duplicate_mismatch_count': int('duplicate mismatch:' in str(exc)),
         'error': str(exc), 'traceback': traceback.format_exc(), 'calibration_observations': 0}
    save('RUN_STOP.json', stop)
    inventory = {p.name:sha(p.read_bytes()) for p in OUT.iterdir() if p.is_file()}
    save('ARTIFACT_CHECKSUMS.json', inventory)
    print(json.dumps(stop), flush=True)
    sys.exit(1)
inventory = {p.name:sha(p.read_bytes()) for p in OUT.iterdir() if p.is_file()}
save('ARTIFACT_CHECKSUMS.json', inventory)
print(json.dumps({'run_id':RUN_ID,'status':'COMPLETE_PENDING_AUDIT','output':str(OUT)}),flush=True)