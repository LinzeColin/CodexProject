#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json, sys
from collections import defaultdict, deque
from pathlib import Path

def normalize_compact_block_sequences(text):
    """Support the PyYAML-accepted `key:\n- item` form in fallback mode."""
    pending_sequence_indents = set()
    shifted_sequence_indents = set()
    normalized = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith('#'):
            normalized.append(raw)
            continue
        indent = len(raw) - len(raw.lstrip(' '))
        is_sequence_item = stripped == '-' or stripped.startswith('- ')
        shifted_sequence_indents = {
            level
            for level in shifted_sequence_indents
            if indent > level or (is_sequence_item and indent == level)
        }
        pending_sequence_indents = {level for level in pending_sequence_indents if level <= indent}
        if (not is_sequence_item) and ':' not in stripped and normalized:
            normalized[-1] = normalized[-1].rstrip() + ' ' + stripped
            continue
        if is_sequence_item and indent in pending_sequence_indents:
            shifted_sequence_indents.add(indent)
        if not is_sequence_item and indent in pending_sequence_indents:
            pending_sequence_indents.remove(indent)
        effective_indent = indent + (2 * len([level for level in shifted_sequence_indents if indent >= level]))
        if (not is_sequence_item) and ':' in stripped:
            key, value = stripped.split(':', 1)
            if key.strip() and not value.strip():
                pending_sequence_indents.add(indent)
        if stripped.startswith('- - '):
            normalized.append(' ' * effective_indent + '-')
            normalized.append(' ' * (effective_indent + 2) + stripped[2:].lstrip(' '))
            continue
        normalized.append(' ' * effective_indent + raw.lstrip(' '))
    return '\n'.join(normalized) + ('\n' if text.endswith('\n') else '')

def load(path):
    text = path.read_text(encoding='utf-8')
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text) or {}
    except ModuleNotFoundError:
        repo_scripts = Path(__file__).resolve().parents[5] / 'scripts'
        if repo_scripts.is_dir():
            sys.path.insert(0, str(repo_scripts))
            from validate_project_governance import fallback_yaml_load

            return fallback_yaml_load(normalize_compact_block_sequences(text)) or {}
        raise

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.')
    root=Path(ap.parse_args().root).resolve(); errors=[]; warnings=[]
    files={
      'product':root/'machine_readable/product_contract_v7.yaml','roadmap':root/'ROADMAP/roadmap_v7.yaml',
      'req':root/'machine_readable/requirements_v7.yaml','stop':root/'machine_readable/stop_codes_v7.yaml',
      'findings':root/'machine_readable/audit_findings_v7_1.yaml','merge':root/'machine_readable/merge_policy_v7_1.yaml',
      'life':root/'machine_readable/operational_lifecycle_v7_1.yaml'}
    for k,p in files.items():
        if not p.is_file(): errors.append(f'missing {k}: {p}')
    if errors: print('\n'.join('ERROR '+x for x in errors)); return 2
    data={k:load(p) for k,p in files.items()}
    cv=data['product'].get('contract_version')
    for k in ['roadmap','req','stop','merge','life']:
        if data[k].get('contract_version')!=cv: errors.append(f'{k} contract_version mismatch')
    codes=set(data['stop'].get('stop_codes') or {})
    tasks={}; deps={}
    for st in data['roadmap'].get('stages',[]):
      for c in st.get('stop_conditions',[]) or []:
        if c not in codes: errors.append(f'unknown stage stop code {c}')
      for ph in st.get('phases',[]):
        for c in ph.get('stop_conditions',[]) or []:
          if c not in codes: errors.append(f'unknown phase stop code {ph.get("phase_id")}:{c}')
        for t in ph.get('tasks',[]):
          tid=t.get('task_id')
          if not tid or tid in tasks: errors.append(f'duplicate/missing task id {tid}')
          tasks[tid]=t; deps[tid]=list(t.get('dependencies') or [])
          for c in t.get('stop_conditions',[]) or []:
            if c not in codes: errors.append(f'unknown task stop code {tid}:{c}')
    for tid,ds in deps.items():
      for d in ds:
        if d not in tasks: errors.append(f'{tid} missing dependency {d}')
    # cycle detection
    indeg={x:0 for x in tasks}; out=defaultdict(list)
    for x,ds in deps.items():
      for d in ds:
        if d in tasks: indeg[x]+=1; out[d].append(x)
    q=deque([x for x,v in indeg.items() if v==0]); seen=0
    while q:
      x=q.popleft(); seen+=1
      for y in out[x]:
        indeg[y]-=1
        if indeg[y]==0:q.append(y)
    if seen!=len(tasks): errors.append('task dependency graph contains a cycle')
    for r in data['req'].get('requirements',[]):
      tids=r.get('task_ids')
      if not isinstance(tids,list) or not tids: errors.append(f'{r.get("requirement_id")} task_ids must be list')
      else:
       for tid in tids:
        if tid not in tasks: errors.append(f'{r.get("requirement_id")} references unknown task {tid}')
    for f in data['findings'].get('findings',[]):
      for key in ['id','track','title','severity','merge_block','evidence_type','fix','task']:
        if not f.get(key): errors.append(f'finding missing {key}: {f.get("id")}')
      if f.get('severity') not in {'P0','P1','P2','P3'}: errors.append(f'bad severity {f.get("id")}')
      if f.get('task') not in tasks: errors.append(f'finding {f.get("id")} references unknown task {f.get("task")}')
    required=[root/'HANDOFF/00_下一Agent先读.md',root/'09_并行审查/并行审查汇总与合并结论.md',root/'evidence/probe_results_v7_1.json']
    for p in required:
      if not p.is_file(): errors.append(f'missing required handoff/evidence {p}')
    result={'status':'PASS' if not errors else 'FAIL','contract_version':cv,'task_count':len(tasks),'finding_count':len(data['findings'].get('findings',[])),'errors':errors,'warnings':warnings}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if not errors else 2
if __name__=='__main__': raise SystemExit(main())
