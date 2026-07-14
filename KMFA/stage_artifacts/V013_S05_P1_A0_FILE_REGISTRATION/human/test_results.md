# KMFA v0.1.3 S05-P1 Test Results

| Command | Expected Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s05_p1_a0_file_registration.py` | PASS: evidence generated |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s05_p1_a0_file_registration.py --require-private-diagnostic` | PASS: public manifest and private diagnostic boundary validated |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s05_p1_a0_file_registration -q` | PASS: focused unit test |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_a0_file_registration.py` | PASS: legacy A0 registration remains valid |

## Actual Results

- PASS: S05-P1 generator produced public-safe evidence with files=9、candidates=9、raw_zip_openable=true、package_hash_match=false、github_upload=false.
- PASS: S05-P1 validator confirmed public_backfill=false、private diagnostic boundary、raw inbox mutation=false、S05-P2=false、Stage 5 review=false、GitHub upload=false.
- PASS: focused S05-P1 unit test passed: `Ran 1 test`.
- PASS: legacy A0 registration validator passed with files=9、pdf=8、excel=1、member_sha256_recorded=0、member_sha256_pending=9、candidates=9.
- PASS: S04 stage review dependency validator passed with phases=3、findings_open=0、quality=Q2、report=D、release=blocked、github_upload=false.
- PASS: full KMFA unittest passed: `Ran 297 tests`.
- PASS: no-float scanner, no-omission check, project governance, lean governance and governance sync all passed with errors=0 warnings=0.
- PASS: structured parse, raw/private artifact path scan, ignored private diagnostic check, public-safe content scan, high-signal secret scan and `git diff --check -- KMFA scripts` passed.

## Evidence Snapshot

- status: `completed_validated_local_only_no_go_upload_deferred_private_source_mismatch`
- raw_zip_present: `true`
- raw_zip_openable: `true`
- local_raw_package_hash_matches_registered: `false`
- local_raw_package_size_matches_registered: `false`
- member_sha256_public_backfill_blocked_reason: `local_raw_package_hash_or_size_mismatch`
- private_diagnostic_written: `true`
- No GitHub upload, S05-P2, Stage 5 review, raw value matching, formal report, or business execution was performed.
