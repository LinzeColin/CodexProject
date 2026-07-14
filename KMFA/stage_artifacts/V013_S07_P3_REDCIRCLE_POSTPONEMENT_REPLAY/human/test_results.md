# Test Results

- PASS: legacy S07-P3 Redcircle postponement validator passed before replay.
- PASS: legacy S07-P3 unit tests passed before replay.
- PASS: v0.1.3 S06 Stage review dependency validator passed before replay.
- PASS: v0.1.3 S07-P1 dependency validator passed before replay.
- PASS: v0.1.3 S07-P2 dependency validator passed before replay.
- PASS: v0.1.3 S07-P3 replay generator wrote manifest and human evidence.
- PASS: v0.1.3 S07-P3 replay validator confirmed templates=4, rollback_plans=4, d15_connector_allowed=false, stage7_review=false, github_upload=false.
- PASS: v0.1.3 S07-P3 focused unit test passed.
- PASS: legacy S07-P3 Redcircle postponement validator and legacy unit tests passed.
- PASS: v0.1.3 S07-P2, S07-P1 and S06 dependency validators passed.
- PASS: full KMFA unittest discovery passed: 311 tests in 687.401s.
- PASS: no-float, no-omission, project governance, lean governance, governance sync, JSON/JSONL/CSV parse, YAML parse, parameter registry shape, changed/untracked raw/private artifact path scan, S07-P3 public-safe evidence scan, strict high-signal secret scan and diff check passed.
- PASS: Stage 7 review, GitHub upload, raw value matching, lineage full check, formal report, live connector, Redcircle automatic connector and business execution were not performed.
- PASS: raw data inbox was not read, listed, modified, deleted, moved, renamed, overwritten or written.

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s07_p3_redcircle_postponement_replay.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_p3_redcircle_postponement_replay.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s07_p3_redcircle_postponement_replay -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s07_p3_redcircle_postponement.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_redcircle_postponement_policy -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_p2_wps_file_adapter_replay.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_p1_finance_file_adapter_replay.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_stage_review.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync
ruby -ryaml -e "ARGV.each { |p| YAML.load_file(p) }; puts 'PASS: yaml parse ok for VERSION_MATRIX, ASSURANCE_STATUS, delivery_tasks'" KMFA/docs/governance/VERSION_MATRIX.yaml KMFA/docs/governance/ASSURANCE_STATUS.yaml KMFA/docs/governance/delivery_tasks.yaml
git diff --check -- KMFA
```

- manifest: `KMFA/stage_artifacts/V013_S07_P3_REDCIRCLE_POSTPONEMENT_REPLAY/machine/redcircle_postponement_replay_manifest.json`
- report: `KMFA/stage_artifacts/V013_S07_P3_REDCIRCLE_POSTPONEMENT_REPLAY/human/redcircle_postponement_replay_report.md`
- status: `completed_validated_local_only_no_go_upload_deferred_redcircle_postponement_replayed`
