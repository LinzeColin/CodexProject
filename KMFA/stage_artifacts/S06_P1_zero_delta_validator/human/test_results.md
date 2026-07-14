# S06-P1 测试结果

## TDD 红灯

| 命令 | 结果 |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_zero_delta_validator -q` | FAIL as expected before implementation: `ModuleNotFoundError: No module named 'KMFA.tools.zero_delta_validator'` |

## S06-P1 验证

| 命令 | 结果 |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_zero_delta_validator -q` | PASS: 6 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/zero_delta_validator.py --fixture KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_fixture.json --result-json KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_zero_delta_result.json --mismatch-report KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_report.csv` | PASS_EXPECTED_FAILURE_EXIT_1: synthetic 1 cent mismatch produced `status=failed`, `zero_delta_passed=false`, `mismatch_count=1` |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q` | PASS: 59 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS: no KMFA Python float money usage found |

## 治理与质量门禁

| 命令 | 结果 |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=300, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS: raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS: dirs=8, files=19, identifiers=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS: quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors=0, warnings=0 |
| `git diff --check -- README.md governance/projects.yaml KMFA` | PASS |

## 安全扫描

| 检查 | 结果 |
|---|---|
| raw 文件扫描 | PASS: no raw zip/xlsx/xls/pdf/sqlite/db/private csv found outside taskpack and allowlisted public-safe protocol/synthetic CSV files |
| secret scan | PASS: no OpenAI key, AWS key, private key, password assignment, API key assignment or secret assignment found |
| JSON/JSONL parse | PASS: S06-P1 JSON artifacts parse; `stage_status=300`, `events=34`, `development_events=34` |

## 边界确认

- 本次未读取或提交 `/Users/linzezhang/Downloads/PRIVATE_RAW_SOURCE_002.xlsx` 或 `/Users/linzezhang/Downloads/PRIVATE_RAW_SOURCE_003.xlsx`。
- 本次未提交真实 Excel、PDF、zip、私有 CSV、银行流水、合同、薪资、税务申报或字段明文。
- 本次未写入 `KMFA/metadata/quality/zero_delta_results.jsonl` 或正式运行时 `mismatch_report.csv`。
- 本次未执行 S06-P2、S06-P3、Stage 6 整体复审或 GitHub upload。
