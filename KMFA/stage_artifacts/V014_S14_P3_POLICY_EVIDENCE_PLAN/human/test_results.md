# KMFA v0.1.4 S14-P3 Test Results

- task_id: `KMFA-V014-S14-P3-POLICY-EVIDENCE-PLAN-20260705`
- status: `passed_local_validation`

## Commands

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s14_p3_policy_evidence_plan.py KMFA/tools/check_v014_s14_p3_policy_evidence_plan.py KMFA/tests/test_v014_s14_p3_policy_evidence_plan.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s14_p3_policy_evidence_plan.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s14_p3_policy_evidence_plan.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s14_p3_policy_evidence_plan.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s14_p3_policy_evidence_plan -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- changed/untracked JSON/JSONL/CSV structured parse checks
- changed/untracked Ruby YAML parse checks
- changed/untracked raw/private suffix scan
- high-signal secret scan across changed/untracked KMFA text files
- scoped S14-P3 public artifact boundary scan
- `git diff --check -- KMFA scripts`

## Results

- PASS: py_compile completed for generator, validator and focused unit test.
- PASS: v0.1.4 S14-P3 generator completed with policy_programs=5, evidence_directories=5, evidence_gaps=5, risk_tips=5, pending_reconciliation=12, report_grade=D, formal policy conclusion=false, policy submission=false, stage14_review=false and github_upload=false.
- PASS: legacy S14-P3 validator passed.
- PASS: v0.1.4 S14-P3 validator passed.
- PASS: focused unit test ran 1 test and passed.
- PASS: project governance validator returned errors=0 warnings=0.
- PASS: Lean governance validator returned errors=0 warnings=0.
- PASS: changed-only governance sync returned errors=0 warnings=0.
- PASS: no-float money check passed.
- PASS: no-omission check passed with requirements=20, P0=9, P1=8, status_records=795, tasks=162 and v1.2_html=45+.
- PASS: structured parse, Ruby YAML parse, raw/private suffix scan, high-signal secret scan, scoped S14-P3 public artifact boundary scan and diff check passed.

## Boundary

- raw/private inbox access: not performed.
- Stage 14 review: not performed.
- GitHub upload: not performed.
- protected source matching and lineage full check: not performed.
- formal report, formal policy qualification conclusion, policy filing, subsidy application, tax filing, invoice issuance, payment, bank operation, loan management and business execution: not performed.
