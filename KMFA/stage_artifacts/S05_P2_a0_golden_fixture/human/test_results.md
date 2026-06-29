# S05-P2 测试结果

| 命令 | 结果 |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_a0_golden_fixture -q` | PASS: 3 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/a0_golden_fixture.py --check-only --generated-at 2026-06-30T01:00:00+10:00` | PASS: candidates=45, fields_per_candidate=5, private_value_hash_recorded=0, private_value_pending=45 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/a0_golden_fixture.py --generated-at 2026-06-30T01:00:00+10:00` | PASS: A0 golden fixture candidate metadata generated |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_golden_fixture.py` | PASS: fixture_candidates=45, fields_per_candidate=5, private_value_hash_recorded=0, private_value_pending=45, source_anchor_recorded=0, source_anchor_pending=45 |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_a0_golden_fixture KMFA.tests.test_a0_file_register KMFA.tests.test_file_import_register KMFA.tests.test_source_check_matrix KMFA.tests.test_source_priority KMFA.tests.test_amount_tools KMFA.tests.test_field_standardization KMFA.tests.test_basic_tool_boundaries -q` | PASS: Ran 32 tests in 0.550s; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_file_registration.py` | PASS: files=9, pdf=8, excel=1, member_sha256_recorded=0, member_sha256_pending=9, candidates=9 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS: dirs=8, files=19, identifiers=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=249, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: required KMFA v1.2 HTML/UIUX/report samples are present (html=45, core=7) |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS: raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS: quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS: no KMFA Python float money usage found |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: root checked; projects checked KMFA; errors=0; warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: root checked; projects checked KMFA; errors=0; warnings=0 |
| `git diff --check -- README.md governance/projects.yaml KMFA` | PASS: no whitespace errors |
| `find KMFA -type f \( -name '*.zip' -o -name '*.xls' -o -name '*.xlsx' -o -name '*.pdf' -o -name '*.sqlite' -o -name '*.db' -o -name '*.sqlite-shm' -o -name '*.sqlite-wal' \) -print` | PASS: no raw archive/spreadsheet/PDF/database files found outside taskpack baseline exclusions |
| `rg -n --hidden -i '(sk-[A-Za-z0-9_-]{20,}\|api[_-]?key\s*[:=]\|password\s*[:=]\|secret\s*[:=]\|银行流水\|纳税申报\|工资明细\|身份证\|银行卡号)' KMFA -g '!KMFA/taskpack/v1_2/**' -g '!KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/**'` | PASS_WITH_POLICY_TEXT_MATCHES_ONLY |

## 说明

- `private_value_pending=45` 是预期结果：本机没有私有 `销售绩效考核.zip` 或授权字段抽取 CSV，公开仓库只记录字段合同、private refs、hash 状态、source anchor 状态和 Q3/Q4/Q5 门禁。
- 未提交 raw PDF、Excel、zip、合同额、支出合计、毛利、毛利率、成本分类明文、银行流水、合同、薪资、税务申报或业务明细。
- 合成私有 CSV 单测只在临时目录中使用，验证工具能够将 private raw values 转为 hash-only public metadata；合成值未进入仓库。
