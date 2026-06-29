#!/usr/bin/env python3
from pathlib import Path
import csv, sys
root = Path(__file__).resolve().parents[1]
req_file = root / '04_KMFA_需求追溯矩阵_v1_1.csv'
roadmap = root / '02_KMFA_Codex_Development_Roadmap_18_Stages_v1_1.md'
if not req_file.exists() or not roadmap.exists():
    print('FAIL: required files missing')
    sys.exit(1)
text = roadmap.read_text(encoding='utf-8')
missing = []
with req_file.open('r', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        stages = [s.strip() for s in row['覆盖Codex开发Stage'].split(',')]
        for s in stages:
            if s and s not in text:
                missing.append((row['需求ID'], s))
if missing:
    print('FAIL: missing stage coverage', missing)
    sys.exit(1)
print('PASS: no omission check passed')
