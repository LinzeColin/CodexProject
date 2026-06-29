# KMFA S01-P3 Test Results

更新时间: 2026-06-29

```text
PASS: python3 KMFA/tools/no_omission_check.py
  requirements=20
  P0=9
  P1=8
  status_records=234
  tasks=162
PASS: python3 scripts/lean_governance.py validate --project KMFA
  errors=0
  warnings=0
PASS: python3 scripts/validate_project_governance.py --project KMFA
  errors=0
  warnings=0
PASS: python3 -m py_compile KMFA/tools/no_omission_check.py
PASS: JSON/JSONL parse checks
PASS: git diff --check -- README.md governance/projects.yaml KMFA
PASS: sensitive/raw file suffix scan under KMFA
PASS: common secret pattern scan under KMFA
```
