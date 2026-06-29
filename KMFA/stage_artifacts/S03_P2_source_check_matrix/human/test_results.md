# S03-P2 验证结果

更新时间: 2026-06-29

## TDD 记录

| 顺序 | 命令 | 结果 | 说明 |
|---|---|---|---|
| RED | `python3 -m unittest KMFA.tests.test_source_check_matrix -q` | FAIL | 预期失败：`ModuleNotFoundError: No module named 'KMFA.tools.source_check_matrix'` |
| GREEN | `python3 -m unittest KMFA.tests.test_source_check_matrix -q` | PASS | `Ran 4 tests in 0.073s`，结果 `OK` |

## 当前验证状态

| 命令 | 结果 | 关键输出 |
|---|---|---|
| `python3 -m unittest KMFA.tests.test_source_check_matrix -q` | PASS | `Ran 4 tests in 0.102s` / `OK` |
| `python3 -m unittest KMFA.tests.test_file_import_register -q` | PASS | `Ran 3 tests in 0.015s` / `OK` |
| `python3 KMFA/tools/check_required_html.py` | PASS | `html=45, core=7` |
| `python3 KMFA/tools/no_omission_check.py` | PASS | `requirements=20, P0=9, P1=8, status_records=235, tasks=162, v1.2_html=45+` |
| `python3 KMFA/tools/check_report_grade_gate.py` | PASS | `quality_grades=Q0-Q5, report_grades=A-D` |
| `python3 KMFA/tools/immutability_policy_check.py` | PASS | `raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes` |
| `python3 KMFA/tools/metadata_protocol_check.py` | PASS | `dirs=8, files=16, identifiers=5` |
| `python3 scripts/lean_governance.py validate --project KMFA` | PASS | `errors: 0`, `warnings: 0` |
| `python3 scripts/validate_project_governance.py --project KMFA` | PASS | `errors: 0`, `warnings: 0` |
| `git diff --check -- KMFA` | PASS | no output |
| `find KMFA ... raw/sensitive suffix scan` | PASS | no output |
| `KMFA/tools/source_check_matrix.py` CLI smoke on `/tmp` registration JSON | PASS | `source_check_matrix_row`, `部分/阻塞`, `False` |

`completed_validated_local_only` - S03-P2 已完成本地验证；S03-P3 和 Stage 3 复审未完成，未上传 GitHub。
