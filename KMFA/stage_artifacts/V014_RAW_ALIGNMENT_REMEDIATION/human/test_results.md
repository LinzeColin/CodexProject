# KMFA v0.1.4 Raw Alignment Remediation Test Results

- status: `PASS`
- task_id: `KMFA-V014-RAW-ALIGNMENT-REMEDIATION-20260705`
- decision: `NO_GO`
- raw_alignment_complete: `false`
- github_upload_performed: `false`
- app_reinstall_performed: `false`
- formal_report_performed: `false`
- business_execution_performed: `false`

## Commands

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_raw_alignment_remediation.py KMFA/tools/check_v014_raw_alignment_remediation.py KMFA/tests/test_v014_raw_alignment_remediation.py` -> PASS
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_raw_alignment_remediation -q` -> PASS
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_raw_alignment_remediation.py --require-private-diagnostic` -> PASS
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA` -> PASS
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA` -> PASS
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync` -> PASS
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py` -> PASS
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py` -> PASS
- changed/untracked JSON JSONL CSV structured parse checks -> PASS
- changed/untracked YAML parse checks -> PASS
- changed/untracked raw/private suffix scan -> PASS
- high-signal secret scan across changed/untracked KMFA text files -> PASS
- scoped raw alignment remediation public artifact boundary scan -> PASS
- `git diff --check -- KMFA scripts` -> PASS
