# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_audit` failed before implementation because the generator module did not exist.
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_audit.py --generated-at 2026-07-08T00:00:00+10:00`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_audit.py --require-private-audit`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_audit`
- PASS: governance validators, YAML parse, CSV shape checks, diff check, raw/private marker scan, secret scan and private-runtime tracked-file scan passed before commit.

Expected matrix result: 12/12 PASS.
