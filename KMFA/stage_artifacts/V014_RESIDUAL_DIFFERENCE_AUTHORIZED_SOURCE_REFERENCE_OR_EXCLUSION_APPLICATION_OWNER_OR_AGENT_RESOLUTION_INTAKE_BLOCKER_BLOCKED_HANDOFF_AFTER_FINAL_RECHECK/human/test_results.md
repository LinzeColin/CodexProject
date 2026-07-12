# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_resolution_intake_blocker_blocked_handoff_after_final_recheck` failed before implementation because the generator module did not exist.
- Generator: PASS, blocked handoff=`48`, owner-resolution queue=`48`, goal=`blocked`, decision=`NO_GO`.
- Validator: PASS with `--require-private-blocked-handoff`.
- Focused unittest: PASS, `Ran 1 test`, `OK`.
- Project governance validator: PASS, `0` errors / `0` warnings.
- Lean governance validator: PASS, `0` errors / `0` warnings.
- Governance sync validator: PASS, `0` errors / `0` warnings.
- YAML parse: PASS for assurance, version, delivery-task, formula and both model registries.
- Active registry counts: parameters=`1289`, formulas=`270`.
- CSV shape: parameter registry `1290` rows / width `34` / bad `0`; traceability matrix `450` rows / width `12` / bad `0`.
- New parameter selector/value counts: `21/21`, `33/33`, `22/22`.
- Current phase model-registry mirror block: PASS.
- `git diff --check -- KMFA`: PASS.
- Changed/untracked files: `37`; forbidden raw/private paths=`0`; non-governance CSV=`0`.
- Added-line and untracked high-signal secret hits: `0`.
- Private-runtime tracked-file count: `0`; all current private outputs remain gitignored.
- Public-safe matrix result: `12/12 PASS`.
- Local commit evidence: verify with `git log -1 --oneline`; no GitHub push is performed by this phase.
