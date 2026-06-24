from __future__ import annotations
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import threading
import time
import types
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent / 'current_code_snapshot'
results: list[dict[str, Any]] = []

def add(probe_id, title, observed, expected, passed, evidence=None, severity='info'):
    results.append({
        'probe_id': probe_id,
        'title': title,
        'observed': observed,
        'expected': expected,
        'probe_passed': bool(passed),
        'evidence': evidence or {},
        'severity': severity,
    })

def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

# Fake package dependencies.
pkg = types.ModuleType('auditpkg')
pkg.__path__ = []
sys.modules['auditpkg'] = pkg
config = types.ModuleType('auditpkg.config')
config.DEFAULT_TIMEZONE = 'Australia/Sydney'
config.PROJECT_NAME = 'arxiv-daily-push'
config.DEFAULT_RECIPIENT = 'owner@example.com'
sys.modules['auditpkg.config'] = config
storage_stub = types.ModuleType('auditpkg.storage')
storage_stub.inspect_database = lambda p: {'model_id':'adp-sqlite-data-model-v1','action':'inspect','status':'pass','schema_version':1,'journal_mode':'wal','object_tables':[],'fts5_ready':True,'blocking_reasons':[]}
storage_stub.validate_storage_report = lambda r: []
sys.modules['auditpkg.storage'] = storage_stub

runtime = load_module('auditpkg.stage1_runtime', ROOT/'stage1_runtime.py')

# P01 lock leak on write error
with tempfile.TemporaryDirectory() as td:
    state = Path(td)
    original = runtime._write_json
    def boom(*a, **k):
        raise OSError('forced write failure')
    runtime._write_json = boom
    raised = None
    try:
        runtime.run_tick(state_dir=state, generated_at='2026-06-24T00:00:00Z', write=True)
    except Exception as e:
        raised = type(e).__name__
    finally:
        runtime._write_json = original
    remains = (state/runtime.STAGE1_RUNTIME_LOCK_FILENAME).exists()
    add('P01','tick 写入异常后锁清理', {'exception':raised,'lock_remains':remains}, '异常后锁必须在 finally 中释放', not remains, severity='P1')

# P02 dry-run claims lock checked
with tempfile.TemporaryDirectory() as td:
    r = runtime.run_tick(state_dir=td, generated_at='2026-06-24T00:00:00Z', write=False)
    claimed = r.get('single_instance_lock_checked')
    add('P02','write=False 的锁检查声明', claimed, False, claimed is False, evidence={'report_status':r.get('status')}, severity='P2')

# P03 future timestamp freshness
age = runtime._age_seconds('2026-06-25T00:00:00Z','2026-06-24T00:00:00Z')
add('P03','未来 heartbeat 时间戳', age, '负值或明确 clock_skew 错误', age is None or age < 0, severity='P1')

# P04 restore manifest path traversal
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    backupdir = root/'backup'
    backupdir.mkdir()
    outside = root/'outside.sqlite3'
    sqlite3.connect(outside).close()
    digest = hashlib.sha256(outside.read_bytes()).hexdigest()
    manifest = {'model_id':runtime.STAGE1_RUNTIME_MODEL_ID,'files':[{'role':'database','path':'../outside.sqlite3','sha256':digest}]}
    mf=backupdir/'backup_manifest.json'; mf.write_text(json.dumps(manifest),encoding='utf-8')
    target=root/'restored.sqlite3'
    r=runtime.restore_runtime_backup(manifest_path=mf,target_db_path=target,generated_at='2026-06-24T00:00:00Z',confirm_restore=True)
    copied=target.exists()
    add('P04','恢复清单路径穿越', {'status':r.get('status'),'copied_outside_file':copied}, '拒绝包含 ../ 或逃逸备份根目录的路径', not copied, severity='P0')

# P05 restore overwrites live target before validation
with tempfile.TemporaryDirectory() as td:
    root=Path(td); backupdir=root/'backup'; backupdir.mkdir()
    backup=backupdir/'bad.sqlite3'; backup.write_bytes(b'not-a-valid-sqlite-db')
    mf=backupdir/'backup_manifest.json'; mf.write_text(json.dumps({'model_id':runtime.STAGE1_RUNTIME_MODEL_ID,'files':[{'role':'database','path':'bad.sqlite3','sha256':hashlib.sha256(backup.read_bytes()).hexdigest()}]}),encoding='utf-8')
    target=root/'live.sqlite3'; target.write_bytes(b'ORIGINAL-LIVE-DATA')
    original_inspect = runtime.inspect_database
    runtime.inspect_database = lambda p: {'status':'blocked','blocking_reasons':['invalid database']}
    try:
        r=runtime.restore_runtime_backup(manifest_path=mf,target_db_path=target,generated_at='2026-06-24T00:00:00Z',confirm_restore=True,allow_overwrite=True)
    finally:
        runtime.inspect_database=original_inspect
    changed=target.read_bytes()!=b'ORIGINAL-LIVE-DATA'
    add('P05','恢复失败对现有数据库的破坏', {'status':r.get('status'),'target_changed':changed,'target_bytes':target.read_bytes()[:32].decode('utf-8','replace')}, '临时文件验证通过后原子替换；失败时保留原库', not changed, severity='P0')

# P06 duplicate basename in backup support files
with tempfile.TemporaryDirectory() as td:
    root=Path(td); db=root/'source.sqlite3'; sqlite3.connect(db).close()
    a=root/'a'; b=root/'b'; a.mkdir(); b.mkdir(); (a/'same.txt').write_text('A'); (b/'same.txt').write_text('B')
    r=runtime.create_runtime_backup(db_path=db,backup_dir=root/'backups',generated_at='2026-06-24T00:00:00Z',include_paths=[a/'same.txt',b/'same.txt'])
    paths=[x.get('path') for x in r.get('files',[]) if x.get('role')=='supporting_file']
    add('P06','备份同名辅助文件冲突', {'manifest_paths':paths,'unique_count':len(set(paths)),'entry_count':len(paths)}, '每个来源路径必须映射到唯一、安全、可追踪的备份路径', len(set(paths))==len(paths), severity='P1')

# P07 scheduler path quoting
text='\n'.join(x['content'] for x in runtime._scheduler_templates('linux',Path('/tmp/Project With Space;echo injected'),Path('/tmp/state dir'),uninstall=False))
unsafe='WorkingDirectory=/tmp/Project With Space;echo injected' in text or '--state-dir /tmp/state dir' in text
add('P07','调度模板路径转义', {'unsafe_fragment_present':unsafe,'snippet':text[:500]}, '结构化参数或严格 shell escaping', not unsafe, severity='P1')

# P07B macOS plist XML validity
import plistlib
plist_text=runtime._scheduler_templates('macos',Path('/tmp/project'),Path('/tmp/state'),uninstall=False)[0]['content']
plist_error=''
try:
    plistlib.loads(plist_text.encode('utf-8'))
except Exception as e:
    plist_error=f'{type(e).__name__}: {e}'
add('P07B','macOS launchd plist 可解析性', {'parse_error':plist_error,'snippet':plist_text[:500]}, 'plistlib 可解析的合法 XML plist', not plist_error, severity='P1')

# P08 simple concurrent tick pressure probe
with tempfile.TemporaryDirectory() as td:
    state=Path(td)
    orig=runtime._write_json
    lock=threading.Lock()
    def slow_write(path,payload):
        time.sleep(0.02)
        return orig(path,payload)
    runtime._write_json=slow_write
    try:
        def one(i):
            return runtime.run_tick(state_dir=state,generated_at=f'2026-06-24T00:00:{i%60:02d}Z',write=True)['status']
        with concurrent.futures.ThreadPoolExecutor(max_workers=32) as ex:
            statuses=list(ex.map(one,range(64)))
    finally:
        runtime._write_json=orig
    passes=statuses.count('pass'); blocked=statuses.count('blocked')
    add('P08','64 并发 tick 单实例探针', {'pass':passes,'blocked':blocked,'other':[s for s in statuses if s not in {'pass','blocked'}]}, '同一瞬间仅一个成功，其他明确阻塞且最终无残锁', passes==1 and blocked==63 and not (state/runtime.STAGE1_RUNTIME_LOCK_FILENAME).exists(), severity='info')

# state machine stubs
contracts=types.ModuleType('auditpkg.contracts')
for n in ['validate_evidence_claim','validate_lesson','validate_publication','validate_source_item','validate_storyboard']:
    setattr(contracts,n,lambda x: [])
contracts.stable_content_hash=lambda x: hashlib.sha256(json.dumps(x,sort_keys=True,default=str).encode()).hexdigest()
sys.modules['auditpkg.contracts']=contracts
state=load_module('auditpkg.state_machine',ROOT/'state_machine.py')

rec=state.initial_run_record('r','2026-06-24','Australia/Sydney')
rec['current_state']='health_checked'; rec['status']='running'; rec['state_history'].append({'from_state':'tampered','to_state':'health_checked','reason':'x','at':'2026-06-24T00:00:00Z'})
errs=state.validate_run_record(rec)
add('P09','状态历史 from_state 防篡改', {'errors':errs}, '识别 from_state 与前一 to_state 不一致', any('from_state' in e for e in errs), severity='P1')

rec2=state.initial_run_record('r','2026-06-24','Australia/Sydney')
rec2['current_state']='source_collected'; rec2['status']='running'
errs2=state.validate_run_record(rec2)
add('P10','current_state 与历史末态一致性', {'errors':errs2}, '识别 current_state 与 state_history 末态不一致', bool(errs2), severity='P1')

# SMTP probes
notifications=types.ModuleType('auditpkg.notifications')
class EmailNotification:
    def __init__(self,recipient,subject,body,html_body=''):
        self.recipient=recipient; self.subject=subject; self.body=body; self.html_body=html_body
notifications.EmailNotification=EmailNotification
sys.modules['auditpkg.notifications']=notifications
smtp=load_module('auditpkg.smtp_delivery',ROOT/'smtp_delivery.py')
n1=EmailNotification('owner@example.com','Same','Body A')
n2=EmailNotification('owner@example.com','Same','Body B')
id1=smtp._delivery_id(n1,'2026-06-24T00:00:00Z'); id2=smtp._delivery_id(n2,'2026-06-24T00:00:00Z')
add('P11','SMTP delivery_id 内容敏感性', {'id_body_a':id1,'id_body_b':id2}, '内容修订应有 revision/content hash，同时保持明确幂等键', id1!=id2, severity='P1')
msg=smtp._email_message(n1,sender='sender@example.com',delivery_id=id1)
add('P12','标准 Message-ID 头', {'Message-ID':msg.get('Message-ID'),'X-ADP-Delivery-ID':msg.get('X-ADP-Delivery-ID')}, '提供稳定标准 Message-ID 并绑定 outbox 记录', bool(msg.get('Message-ID')), severity='P2')

# Lesson probes
# Replace evidence_gate module
evidence=types.ModuleType('auditpkg.evidence_gate')
evidence.build_claim_ledger=lambda source,claims,extracted_at: {'source_id':source['source_id'],'status':'pass','blocking_reasons':[],'claims':[dict(c,support_status='supported') for c in claims]}
sys.modules['auditpkg.evidence_gate']=evidence
contracts.validate_lesson=lambda x: []
contracts.validate_source_item=lambda x: []
lesson=load_module('auditpkg.lesson',ROOT/'lesson.py')
source={'source_id':'arxiv:1','title':'A title','metadata':{'arxiv':{'summary':'A summary','primary_category':'cs.AI'}}}
c1={'claim_id':'C1','statement':'Statement A','priority':'P0'}
c2={'claim_id':'C1','statement':'Changed statement','priority':'P0'}
l1=lesson.generate_lesson(source,[c1],generated_at='2026-06-24T00:00:00Z')
l2=lesson.generate_lesson(source,[c2],generated_at='2026-06-24T00:00:00Z')
add('P13','lesson_id 对 claim 内容/证据版本敏感', {'lesson_id_a':l1['lesson_id'],'lesson_id_b':l2['lesson_id']}, 'Claim 内容或证据版本变化时生成可追踪的新 revision', l1['lesson_id']!=l2['lesson_id'], severity='P1')
frontstage_has_claims=all('claim_ids' in v if isinstance(v,dict) else False for v in [])  # explicit below
add('P14','frontstage 推断的证据绑定', {'frontstage_keys':sorted(l1['frontstage'].keys()),'claim_ids_present':'claim_ids' in l1['frontstage']}, '一行结论、机制链、映射、行动均含 claim/evidence 或明确标注 inference', 'claim_ids' in l1['frontstage'], severity='P0')

# Report module probes
# Exceptions and stubs
evidence.EvidenceGateError=ValueError
lesson.LessonGenerationError=ValueError
# Ensure module imports use current lesson module
report=load_module('auditpkg.stage1_b1_report',ROOT/'stage1_b1_report.py')
render_email_html_original = report._render_email_html
with tempfile.TemporaryDirectory() as td:
    pkg={'date':'2026-06-24','source_id':'x','report_markdown':'abc','report_html':'<p>a</p>','email_plain':'p','email_html':'h','run_id':'r'}
    refs=report._write_artifacts(pkg,Path(td))
    p=Path(refs['report_markdown']['path'])
    actual=hashlib.sha256(p.read_bytes()).hexdigest(); claimed=refs['report_markdown']['sha256']
    add('P15','artifact_files.sha256 语义', {'claimed':claimed,'actual_file_sha256':actual}, '字段 sha256 必须是文件字节标准 SHA-256', claimed==actual, severity='P1')

# Patch builder internals to force post-write validation failure
with tempfile.TemporaryDirectory() as td:
    source={'source_id':'arxiv:1','source_type':'arxiv','title':'T','canonical_url':'https://arxiv.org/abs/1','metadata':{'arxiv':{'primary_category':'cs.AI'}}}
    daily={'run_id':'r','publication_id':'p','date':'2026-06-24','generated_at':'2026-06-24T00:00:00Z','source_item':source,'claims':[{'claim_id':'C1'}]}
    report._validate_daily_input=lambda x: []
    report.build_claim_ledger=lambda *a,**k: {'blocking_reasons':[],'claims':[{'claim_id':'C1','priority':'P0','support_status':'supported','statement':'S'}], 'ledger_id':'L'}
    report.generate_lesson=lambda *a,**k: {'frontstage':{}}
    report._render_report_markdown=lambda **k:'报告\n'
    report._markdown_to_simple_html=lambda *a,**k:'<p>报告</p>'
    report._render_email_plain=lambda **k:'中文邮件'
    report._render_email_html=lambda **k:'<p>中文邮件</p>'
    report._evidence_audit=lambda x:{'critical_claim_coverage_percent':100.0,'evidence_boundary':'x','unsupported_critical_claim_ids':[]}
    report._content_ledger_update=lambda **k:{}
    report._email_subject=lambda *a,**k:'20260624 -- P -- G -- T'
    report.validate_b1_report_email_package=lambda p:['forced-invalid-after-write']
    out=report.build_b1_report_email_package(daily,generated_at='2026-06-24T00:00:00Z',artifact_dir=td,write=True)
    files=list(Path(td).rglob('*.*'))
    add('P16','先写文件后质量验证', {'status':out.get('status'),'file_count_after_block':len(files),'files':[str(x.relative_to(td)) for x in files]}, '质量验证通过后才原子发布；失败不得留下正式产物', len(files)==0, severity='P1')

# URL scheme in email
html_out=render_email_html_original(subject='S',report_id='R',daily_input={'run_id':'run'},source_item={'title':'T','canonical_url':'javascript:alert(1)','metadata':{'arxiv':{}}},lesson={'frontstage':{}},evidence_audit={'evidence_boundary':'x'},candidate_queue_summary='q')
add('P17','邮件链接 scheme 白名单', {'javascript_href_present':'href="javascript:alert(1)"' in html_out}, '仅允许 https/http 且可选来源域白名单', 'href="javascript:alert(1)"' not in html_out, severity='P1')

# Storage concurrency and identity probes
# Reload real storage into a separate package with validate source stub
storepkg=types.ModuleType('storepkg'); storepkg.__path__=[]; sys.modules['storepkg']=storepkg
store_contracts=types.ModuleType('storepkg.contracts')
store_contracts.stable_content_hash=lambda x: hashlib.sha256(json.dumps(x,sort_keys=True,default=str).encode()).hexdigest()
store_contracts.validate_source_item=lambda x: []
sys.modules['storepkg.contracts']=store_contracts
storage=load_module('storepkg.storage',ROOT/'storage.py')
with tempfile.TemporaryDirectory() as td:
    db=Path(td)/'db.sqlite3'; mig=storage.migrate_database(db)
    def item(i):
        return {'source_id':f'arxiv:{i}','source_type':'arxiv','source_adapter':'arxiv_atom','stable_id':str(i),'retrieved_at':'2026-06-24T00:00:00Z','title':f'Title {i}','canonical_url':f'https://arxiv.org/abs/{i}','metadata':{'summary':'x'},'license':{}}
    errors=[]
    def store_one(i):
        try: return storage.store_source_item(db,item(i),fetch_run_id=f'fetch:{i}')['status']
        except Exception as e: return f'{type(e).__name__}:{e}'
    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as ex:
        ss=list(ex.map(store_one,range(120)))
    failures=[x for x in ss if x!='pass']
    conn=sqlite3.connect(db); count=conn.execute('select count(*) from canonical_documents').fetchone()[0]; conn.close()
    add('P18','SQLite 120 项/24 并发写入探针', {'migration_status':mig.get('status'),'pass_count':ss.count('pass'),'failure_count':len(failures),'sample_failures':failures[:5],'document_count':count}, '无 database locked、数据数量守恒', len(failures)==0 and count==120, severity='info' if len(failures)==0 else 'P1')

out=ROOT.parent/'probe_results_v7_1.json'
out.write_text(json.dumps({'generated_at':'2026-06-24','scope':'targeted isolated probes; not a full repository test run','results':results,'summary':{'total':len(results),'passed':sum(1 for r in results if r['probe_passed']),'failed':sum(1 for r in results if not r['probe_passed'])}},ensure_ascii=False,indent=2),encoding='utf-8')
print(out)
print(json.dumps({'total':len(results),'passed':sum(1 for r in results if r['probe_passed']),'failed':sum(1 for r in results if not r['probe_passed'])},ensure_ascii=False))
for r in results:
    print(('PASS' if r['probe_passed'] else 'FAIL'),r['probe_id'],r['title'])
