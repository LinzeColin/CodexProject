# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_resolution_intake_blocker_final_recheck_after_final_check_closure` failed before implementation because the generator module did not exist.
- Generator: PASS, observation=`3`, threshold=`true`, blockers=`48`, goal=`blocked`, decision=`NO_GO`.
- Validator: PASS with `--require-private-final-recheck`.
- Focused unittest: PASS, `Ran 1 test`, `OK`.
- Project governance validator: PASS, `0` errors / `0` warnings.
- Lean governance validator: PASS, `0` errors / `0` warnings.
- Governance sync validator: PASS, `0` errors / `0` warnings.
- CSV shape: parameter registry `1287` rows / width `34` / bad `0`; traceability matrix `449` rows / width `12` / bad `0`.
- `git diff --check -- KMFA`: PASS.
- Changed/untracked raw or private filename scan: no hits.
- Added-line and untracked hard-secret scan: no hits.
- Private-runtime tracked-file scan: `0`; all current private outputs are gitignored.
- Public-safe matrix result: `12/12 PASS`.
- Local commit evidence: verify with `git log -1 --oneline`; no GitHub push is performed by this phase.
