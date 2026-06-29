# S05-P1 测试结果

| 命令 | 结果 |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_a0_file_register -q` | PASS: 3 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/a0_file_register.py --check-only --generated-at 2026-06-30T00:00:00+10:00` | PASS: files=9, pdf=8, excel=1, member_sha256_recorded=0, member_sha256_pending=9 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/a0_file_register.py --generated-at 2026-06-30T00:00:00+10:00` | PASS: A0 metadata generated |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_file_registration.py` | PASS: files=9, pdf=8, excel=1, member_sha256_recorded=0, member_sha256_pending=9, candidates=9 |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_a0_file_register KMFA.tests.test_file_import_register KMFA.tests.test_source_check_matrix KMFA.tests.test_source_priority KMFA.tests.test_amount_tools KMFA.tests.test_field_standardization KMFA.tests.test_basic_tool_boundaries -q` | PASS: 29 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS: no KMFA Python float money usage found |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS: dirs=8, files=19, identifiers=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=244, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS: raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS: quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors 0 / warnings 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors 0 / warnings 0 |
| `git diff --check -- README.md governance/projects.yaml KMFA` | PASS: no whitespace errors |
| `find KMFA -type f \( -name '*.zip' -o -name '*.xls' -o -name '*.xlsx' -o -name '*.pdf' -o -name '*.sqlite' -o -name '*.db' -o -name '*.sqlite-shm' -o -name '*.sqlite-wal' \) -print` | PASS: no raw file-like artifacts found |
| `rg -n --hidden -i '(sk-[A-Za-z0-9_-]{20,}\|api[_-]?key\s*[:=]\|password\s*[:=]\|secret\s*[:=]\|银行流水\|纳税申报\|工资明细\|身份证\|银行卡号)' KMFA -g '!KMFA/taskpack/v1_2/**' -g '!KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/**'` | PASS_WITH_POLICY_TEXT_MATCHES_ONLY |

## 说明

- `member_sha256_pending=9` 是预期结果：本机没有私有 `销售绩效考核.zip`，公开仓库只记录 source package SHA256、public-safe inventory 指纹和待补状态。
- 未提交 raw PDF、Excel、zip、银行流水、合同、薪资、税务申报或业务明细。
- 首次跨阶段测试发现 `a0_file_register.py` 使用 `float()` 转换 inventory KB，触发 `check_no_float_money.py`；已改为保留 CSV 字符串并复跑通过。
- 当前 KMFA worktree 为 sparse checkout。治理 validator 首次因缺少 root governance 模板和注册项目入口路径失败；已把 sparse checkout 精确扩展到 validator 必要 root 文件和其他项目最小入口文件后复跑通过，未读取或修改其他项目业务内容。
