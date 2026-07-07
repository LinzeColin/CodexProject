# Test Results

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_residual_difference_response_import_readiness_recheck.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_response_import_readiness_recheck.py --require-private-readiness`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_residual_difference_response_import_readiness_recheck`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA --mode required`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`
- Custom JSON/JSONL/CSV/YAML parse, diff check, staged path scan, secret scan, public artifact raw/private marker scan, private-output git-ignore scan and private-runtime tracked-file scan: PASS.

Expected matrix result: 13/13 PASS.
