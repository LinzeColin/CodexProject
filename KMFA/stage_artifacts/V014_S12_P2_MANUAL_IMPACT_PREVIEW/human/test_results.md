# v0.1.4 S12-P2 Test Results

Status: `PASS`

## Phase Validators

- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s12_p2_manual_impact_preview.py KMFA/tools/check_v014_s12_p2_manual_impact_preview.py KMFA/tests/test_v014_s12_p2_manual_impact_preview.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s12_p2_manual_impact_preview.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s12_p1_manual_resolution_events.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s12_p2_manual_impact_preview.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s12_p2_manual_impact_preview.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s12_p2_manual_impact_preview -q` ran 1 test in 145.656s.

## Governance And Safety

- PASS: `scripts/validate_project_governance.py --project KMFA`.
- PASS: `scripts/lean_governance.py validate --project KMFA`.
- PASS: `scripts/validate_governance_sync.py --changed-only --enforce-sync`.
- PASS: `KMFA/tools/check_no_float_money.py`.
- PASS: `KMFA/tools/no_omission_check.py`.
- PASS: JSON/JSONL/CSV structured parse checks.
- PASS: YAML structured parse checks using system Ruby YAML parser because Python PyYAML is unavailable in this environment.
- PASS: S12-P2 artifact boundary scan.
- PASS: high-signal secret scan across changed KMFA text files.
- PASS: `git diff --check -- KMFA scripts`.

## Locked Boundary

- Raw/private inbox read/list/stat/hash/mutation: `false`
- S12-P3 rerun mechanism performed: `false`
- Stage 12 review performed: `false`
- GitHub upload performed: `false`
- Formal report/business decision basis/business execution: `false`
