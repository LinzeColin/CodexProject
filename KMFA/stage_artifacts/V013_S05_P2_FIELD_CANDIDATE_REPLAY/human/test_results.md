# KMFA v0.1.3 S05-P2 Test Results

- status: `passed_local_only_upload_deferred`

- PASS: S05-P2 generator and validator confirmed fixture_candidates=`45`, required_fields_per_candidate=`5`, hash/source-anchor recorded=`40`, pending fields=`5`, active_owner_decision=`downgrade_to_cross_source_support`, completion_gate=`ready`, github_upload=`false`.
- PASS: focused unit test passed: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s05_p2_field_candidate_replay -q`.
- PASS: legacy S05-P2 dependency validators passed: A0 golden fixture, Excel owner decision packet, owner decision intake, owner decision templates and completion gate with active decision.
- PASS: S05-P1 dependency validator passed with private diagnostic requirement; no public member backfill was claimed.
- PASS: full KMFA unittest passed: `298 tests`.
- PASS: no-float, no-omission, project governance, lean governance, governance sync, structured parse, raw/private artifact path scan, strict high-signal secret scan, S05-P2 public-safe evidence scan and diff check passed.
- PASS: this phase did not read, list, modify, delete, move, rename, overwrite or write generated/extra files inside `/Users/linzezhang/Downloads/KMFA_MetaData`; S05-P3, Stage 5 review, GitHub upload, raw value matching, formal report and business execution were not performed.
