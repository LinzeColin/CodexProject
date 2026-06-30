# S05-P3 测试结果

| 命令 | 结果 |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_s05_p3_authority_baseline_lock -q` | PASS: Ran 4 tests; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/a0_authority_baseline_lock.py --locked-at 2026-06-30T12:00:00+10:00 --locked-by-ref codex_delegate_s05p3_public_safe_lock_20260630 --check-only` | PASS: q5_locked_fields=40, excluded_fields=5, formal_report_allowed=False |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/a0_authority_baseline_lock.py --locked-at 2026-06-30T12:00:00+10:00 --locked-by-ref codex_delegate_s05p3_public_safe_lock_20260630` | PASS: generated public-safe S05-P3 lock artifacts |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_authority_baseline_lock.py` | PASS: q5_locked_fields=40, excluded_fields=5, authority_records=45, formal_report_allowed=False |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_a0_golden_fixture KMFA.tests.test_s05_p2_excel_owner_decision KMFA.tests.test_s05_p2_owner_decision_intake KMFA.tests.test_s05_p2_owner_decision_templates KMFA.tests.test_s05_p2_owner_decision_application KMFA.tests.test_s05_p2_completion_gate KMFA.tests.test_s05_p3_authority_baseline_lock KMFA.tests.test_a0_file_register KMFA.tests.test_file_import_register KMFA.tests.test_source_check_matrix KMFA.tests.test_source_priority KMFA.tests.test_amount_tools KMFA.tests.test_field_standardization KMFA.tests.test_basic_tool_boundaries -q` | PASS: Ran 53 tests; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_file_registration.py` | PASS: files=9, pdf=8, excel=1, member_sha256_recorded=0, member_sha256_pending=9, candidates=9 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_golden_fixture.py` | PASS: fixture_candidates=45, private_value_hash_recorded=40, private_value_pending=5, source_anchor_recorded=40, source_anchor_pending=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s05_p2_completion_gate.py --decision KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/excel_owner_resolution_decision.json` | PASS: ready via owner_downgrade_to_cross_source_support |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=291, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS: dirs=8, files=19, identifiers=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS: raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS: quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS: no KMFA Python float money usage found |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors=0, warnings=0 |
| `git diff --check -- README.md governance/projects.yaml KMFA` | PASS |
| `find KMFA -path 'KMFA/taskpack/v1_2/*' -prune -o -path 'KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/*' -prune -o -type f \( -name '*.zip' -o -name '*.xls' -o -name '*.xlsx' -o -name '*.pdf' -o -name '*.sqlite' -o -name '*.db' -o -name '*.sqlite-shm' -o -name '*.sqlite-wal' \) -print` | PASS: no forbidden raw file artifacts found outside allowed taskpack/archive exclusions |
| `rg -n --hidden -i '(sk-[A-Za-z0-9_-]{20,}\|api[_-]?key\s*[:=]\|password\s*[:=]\|secret\s*[:=]\|银行流水\|纳税申报\|工资明细\|身份证\|银行卡号)' KMFA -g '!KMFA/taskpack/v1_2/**' -g '!KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/**'` | PASS_WITH_POLICY_TEXT_MATCHES_ONLY |
| `jsonl parse check` | PASS: authority_records=45, stage_status=291, events=31, development_events=31, control_events=5, resolution_events=5 |

## 说明

- 40 条 PDF 字段记录基于 S05-P2 private hash/source anchor 被锁定为 public-safe Q5 calculation baseline。
- 5 条 Excel 字段记录基于 S05-P2 active owner/授权降级决策被排除为 `cross_source_support_only`。
- S05-P3 lock 不提交 raw values、normalized values、原始文件、私有 CSV 或业务明文。
- S05-P3 lock 不代表 Stage 5 review、zero-delta、lineage 或正式报告发布完成。
- Stage 5 review 和 GitHub upload 未执行。
