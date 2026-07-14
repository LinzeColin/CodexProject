# KMFA v0.1.4 S16-P1 test results

- Generated task: KMFA-V014-S16-P1-SUBCONTRACT-PROCUREMENT-20260705
- Required checks: generator, validator, legacy S16-P1 validator, Stage 15 review validator, unit test, governance validator, public evidence scan, raw/private suffix scan, and local commit.
- Result: PASS local-only. No raw/private inbox access, procurement execution, payment approval, payment execution, bank operation, business execution, S16-P2, S16-P3, Stage 16 review, GitHub upload, protected source matching, lineage full check, formal report, live connector, app reinstall, OpMe integration, collection action or legal action was performed.

## Commands

- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s16_p1_subcontract_procurement.py KMFA/tools/check_v014_s16_p1_subcontract_procurement.py KMFA/tests/test_v014_s16_p1_subcontract_procurement.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s16_p1_subcontract_procurement.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s15_stage_review.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s16_p1_subcontract_procurement.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s16_p1_subcontract_procurement.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s16_p1_subcontract_procurement -q`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- PASS: changed/untracked JSON/JSONL/CSV structured parse checks.
- PASS: changed/untracked Ruby YAML parse checks.
- PASS: changed/untracked raw/private suffix scan found no disallowed raw business artifacts.
- PASS: high-signal secret scan across changed/untracked KMFA text files.
- PASS: scoped S16-P1 public artifact boundary scan.
- PASS: `git diff --check -- KMFA scripts`.
