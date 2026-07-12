# v0.1.4 S12-P3 Test Results

Focused RED was recorded before implementation:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s12_p3_manual_rerun_mechanism -q`
- Initial result: failed because the v0.1.4 S12-P3 generator/validator modules were absent.

Final local validation:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s12_p3_manual_rerun_mechanism.py KMFA/tools/check_v014_s12_p3_manual_rerun_mechanism.py KMFA/tests/test_v014_s12_p3_manual_rerun_mechanism.py` -> PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s12_p3_manual_rerun_mechanism.py` -> PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s12_p2_manual_impact_preview.py` -> PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s12_p3_manual_rerun_mechanism.py` -> PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s12_p3_manual_rerun_mechanism -q` -> PASS, 1 test.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA` -> PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA` -> PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync` -> PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py` -> PASS.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py` -> PASS.
- Structured parse checks for changed JSON, JSONL, CSV and YAML files -> PASS.
- Changed-file forbidden raw/private suffix scan -> PASS.
- High-signal secret scan across changed text files -> PASS.
- Scoped S12-P3 artifact boundary scan -> PASS.
- `git diff --check -- KMFA scripts` -> PASS.

Boundaries preserved: Stage 12 review, GitHub upload, protected source matching, lineage full check, formal report release, live connector, app reinstall, OpMe integration and business execution were not performed.
