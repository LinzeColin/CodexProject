# KMFA S17-P3 Operations SOP Test Results

generated_at: 2026-07-01T23:59:30+10:00

## TDD Red Evidence

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_operations_sop.py
ModuleNotFoundError: No module named 'KMFA.tools.operations_sop'
```

## Green Evidence

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_operations_sop.py` | PASS: 6 tests |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/operations_sop.py --check-only --generated-at 2026-07-01T23:59:30+10:00` | PASS: runbooks=4, knowledge_items=2, drill_logs=2, metadata_only=true, manual_execution_only=true, stage17_review=false, github_upload=false |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/operations_sop.py --generated-at 2026-07-01T23:59:30+10:00` | PASS: generated S17-P3 operations SOP artifacts |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s17_p3_operations_sop.py` | PASS: runbooks=4, knowledge_items=2, drill_logs=2, metadata_only=true, manual_execution_only=true, stage17_review=false, github_upload=false |

## Final Local Gate Evidence

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q` | PASS: 245 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors=0 warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors=0 warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --enforce-sync` | PASS: errors=0 warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, status_records=517, tasks=162, v1.2_html=45+ |
| `git diff --check` | PASS |
| `ruby -ryaml ... KMFA/docs/governance/*.yaml KMFA/metadata/project/project.yaml KMFA/metadata/model_registry.yaml` | PASS: YAML parse OK |
| `python3 changed-path raw/private scan --untracked-files=all` | PASS: 33 KMFA changed paths checked |
| `python3 high-signal secret scan --untracked-files=all` | PASS: 33 KMFA changed text files checked |

## Boundary Result

- `metadata_only=true`
- `manual_execution_only=true`
- `live_connector=false`
- `external_service_call=false`
- `production_restore=false`
- `formal_report=false`
- `business_execution=false`
- `stage17_review=false`
- `github_upload=false`
- `raw_business_data=false`
