# v0.1.4 S12-P1 Test Results

Final validation status: PASS.

- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s12_p1_manual_resolution_events.py KMFA/tools/check_v014_s12_p1_manual_resolution_events.py KMFA/tests/test_v014_s12_p1_manual_resolution_events.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s12_p1_manual_resolution_events.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s11_stage_review.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s12_p1_manual_resolution_events.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s12_p1_manual_resolution_events.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s12_p1_manual_resolution_events -q`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- PASS: structured parse checks for changed governance/evidence files.
- PASS: changed-file path scan and scoped artifact boundary scan.
- PASS: scoped secret scan for changed text files.
- PASS: `git diff --check -- KMFA scripts`

Locked boundary: S12-P1 only. S12-P2, S12-P3, Stage 12 review, GitHub upload, formal report release, business execution and raw/private inbox access were not performed.
