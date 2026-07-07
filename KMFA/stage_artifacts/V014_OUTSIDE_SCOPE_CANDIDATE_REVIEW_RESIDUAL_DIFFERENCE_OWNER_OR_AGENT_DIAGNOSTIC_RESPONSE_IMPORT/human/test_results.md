# Test Results

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import.py --require-private-import`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA --mode required`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`
- `ruby -e 'require "yaml"; ARGV.each { |p| YAML.load_file(p) }' KMFA/docs/governance/*.yaml KMFA/metadata/*.yaml`
- `git diff --check -- KMFA`
- Custom changed-path raw/private extension scan, changed-file secret scan, current-phase public artifact raw/private marker scan, private-output git-ignore scan and private-runtime tracked-file scan: PASS.

Expected matrix result: 13/13 PASS.
