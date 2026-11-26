from __future__ import annotations
import hashlib, json, platform, subprocess, sys, traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(r'C:\projects\tmt\.diag001-pr404-67b9bb3')
OUT = Path(r'C:\projects\tmt\.cardcade-diagnostic-001-pr404-67b9bb3-20261107')
EXPECTED = '67b9bb3083c9f4b2fe02e7fed258c4739581225f'
OUT.mkdir(parents=True, exist_ok=True)
if any(p.name != 'run_once.py' for p in OUT.iterdir()): raise RuntimeError('unexpected pre-run output files')
sys.path.insert(0, str(ROOT / 'src'))
from tmnt_design_studio import stage002

def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()
def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args], text=True).strip()
head=git('rev-parse','HEAD')
status=git('status','--porcelain=v1')
main=git('rev-parse','origin/main')
if head != EXPECTED: raise RuntimeError(f'HEAD mismatch: {head}')
if status: raise RuntimeError(f'worktree not clean: {status}')
if main != '10d2ac80ef5b81b3a209a3133eb0a84633a1f944': raise RuntimeError(f'accepted main changed: {main}')
specs=[g for g in stage002.stage_games() if g.game_id == 'april-casey:canonical:7231']
if len(specs) != 1: raise RuntimeError(f'canonical game spec count mismatch: {len(specs)}')
spec=specs[0]
inputs=[
'src/tmnt_design_studio/stage002.py',
'decks/april_oneil/PROTOTYPE_0.1.txt',
'decks/casey_jones/PROTOTYPE_0.1.txt',
'cardcade/scryfall-tmt-pza-tmc-2026-08-13.json',
'cardcade/scryfall-tmt-pza-tmc-2026-08-13.manifest.json',
'docs/objective-balance-lab/baselines/OBL_BASELINE_005_MANIFEST.json',
]
manifest=stage002.build_stage_manifest(ROOT)
metadata={
 'run_id':'cardcade-diagnostic-game-001','authorized_head':EXPECTED,'observed_head':head,
 'accepted_main':main,'branch':git('branch','--show-current') or '(detached HEAD)',
 'worktree':str(ROOT),'output_directory':str(OUT),'python_version':platform.python_version(),
 'python_executable':sys.executable,'game_id':spec.game_id,'pairing_id':spec.pairing_id,
 'orientation':spec.orientation,'seed':spec.seed,
 'seats':[{'display_id':s.display_id,'deck_path':s.relative_path} for s in spec.seats],
 'stage_manifest_digest':manifest['manifest_digest'],
 'input_sha256':{p:sha256(ROOT/p) for p in inputs},
 'invocation':'tmnt_design_studio.stage002.run_game(ROOT, spec, stage002.AcceptancePilot())',
 'run_game_call_count':1,'retry_count':0,'additional_seeds':0,'batch_or_calibration':False,
 'started_utc':datetime.now(timezone.utc).isoformat(),
 'runner_control_flow':'single Game constructed inside one run_game call; loop terminates on terminal state or raises at turn 120; no outer game loop/retry',
}
write_json('stage_manifest.json',manifest)
write_json('run_metadata.json',metadata)
snapshot=None
error=None
try:
    snapshot=stage002.run_game(ROOT,spec,stage002.AcceptancePilot())
except BaseException as exc:
    error={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    tb=sys.exc_info()[2]
    frame=None
    while tb is not None:
        if 'game' in tb.tb_frame.f_locals: frame=tb.tb_frame
        tb=tb.tb_next
    if frame is not None:
        live=frame.f_locals['game']
        try:
            snapshot=live.snapshot()
            presence=frame.f_locals.get('presence')
            if isinstance(presence,list):
                stage002._add_created_token_presence(live,presence,snapshot['events'])
                snapshot['stage002_presence']=stage002._finish_presence(presence,snapshot['events'])
        except BaseException as cap_exc:
            error['snapshot_capture_error']=f'{type(cap_exc).__name__}: {cap_exc}'
if error is not None: write_json('exception.json',error)
if snapshot is not None:
    write_json('snapshot.json',snapshot)
    events=snapshot.get('events',[])
    write_json('events.json',events)
    trace_names={'priority_granted','priority_passed','priority_window_closed','stack_resolution_permitted','trigger_stacked','trigger_resolved','attack_declared','attackers_declared','block_declared','blockers_declared','sneak','combat_damage','step_changed'}
    write_json('priority_stack_combat_trace.json',[e for e in events if e.get('event') in trace_names])
    try:
        report=stage002.reconcile_snapshot(spec,snapshot,manifest)
        write_json('reconciliation.json',report)
        recon_error=None
    except BaseException as exc:
        report=None
        recon_error={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
        write_json('reconciliation_error.json',recon_error)
    counts=Counter(str(e.get('event')) for e in events)
    status={
      'run_returned_normally':error is None,'reconciliation_completed':recon_error is None,
      'winner':snapshot.get('winner'),'terminal':snapshot.get('terminal'),
      'turn':snapshot.get('turn'),'step':snapshot.get('step'),'event_count':len(events),
      'event_counts':dict(sorted(counts.items())),
      'invariant_violation_count':sum(e.get('event')=='invariant_violation' for e in events),
      'acceptance_incomplete_count':sum(e.get('event')=='acceptance_incomplete' for e in events),
      'reconciliation_stop_records':report.get('stop_records',[]) if report else None,
      'reconciliation_invariant_violations':report.get('invariant_violations',[]) if report else None,
    }
else: status={'run_returned_normally':False,'snapshot_captured':False}
metadata['finished_utc']=datetime.now(timezone.utc).isoformat()
write_json('run_metadata.json',metadata)
write_json('run_status.json',status)
hashes={p.name:sha256(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact_sha256.json'}
write_json('artifact_sha256.json',hashes)
print(json.dumps({'output':str(OUT),'metadata':metadata,'status':status,'artifact_sha256':hashes},sort_keys=True))
if error is not None or snapshot is None: sys.exit(2)


