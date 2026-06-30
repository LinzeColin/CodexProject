# S05-P2 测试结果

| 命令 | 结果 |
|---|---|
| `python3 -m json.tool KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/excel_owner_decision_packet.json >/dev/null` | PASS: parseable JSON |
| `python3 -m json.tool KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/excel_owner_decision_intake_contract.json >/dev/null` | PASS: parseable JSON |
| `python3 -m json.tool KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/excel_resolution_manifest.json >/dev/null` | PASS: parseable JSON |
| `python3 -m json.tool KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/private_backfill_manifest.json >/dev/null` | PASS: parseable JSON |
| `python3 - <<'PY' ... validate resolution/control/stage/event JSONL ... PY` | PASS: approval, stage status and governance JSONL files parse |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_s05_p2_excel_owner_decision -q` | PASS: Ran 2 tests; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s05_p2_excel_owner_decision.py` | PASS: allowed_decisions=3, pending_fields=5, status=awaiting_owner_or_authorized_decision |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_s05_p2_owner_decision_intake -q` | PASS: Ran 4 tests; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s05_p2_owner_decision_intake.py` | PASS: contract_status=ready_for_owner_decision_record, decision_status=no_decision_supplied, decision_code=none |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_s05_p2_owner_decision_templates -q` | PASS: Ran 3 tests; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s05_p2_owner_decision_templates.py` | PASS: template_count=3, active_decision_records=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_s05_p2_completion_gate -q` | PASS: Ran 4 tests; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s05_p2_completion_gate.py --expect-blocked` | PASS: blocked as expected, pending_fields=5, decision_code=none |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s05_p2_completion_gate.py` | BLOCKED as expected: pending_fields=5, decision_code=none |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_a0_golden_fixture -q` | PASS: 3 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/a0_golden_fixture.py --private-fields-csv <private-path> --generated-at 2026-06-30T02:30:00+10:00 --check-only` | PASS: candidates=45, fields_per_candidate=5, private_value_hash_recorded=40, private_value_pending=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/a0_golden_fixture.py --private-fields-csv <private-path> --generated-at 2026-06-30T02:30:00+10:00` | PASS: A0 golden fixture candidate metadata generated with 40 hash-recorded / 5 pending |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_golden_fixture.py` | PASS: fixture_candidates=45, fields_per_candidate=5, private_value_hash_recorded=40, private_value_pending=5, source_anchor_recorded=40, source_anchor_pending=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_a0_golden_fixture KMFA.tests.test_s05_p2_excel_owner_decision KMFA.tests.test_s05_p2_owner_decision_intake KMFA.tests.test_s05_p2_owner_decision_templates KMFA.tests.test_s05_p2_completion_gate KMFA.tests.test_a0_file_register KMFA.tests.test_file_import_register KMFA.tests.test_source_check_matrix KMFA.tests.test_source_priority KMFA.tests.test_amount_tools KMFA.tests.test_field_standardization KMFA.tests.test_basic_tool_boundaries -q` | PASS: Ran 45 tests; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_file_registration.py` | PASS: files=9, pdf=8, excel=1, member_sha256_recorded=0, member_sha256_pending=9, candidates=9 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS: dirs=8, files=19, identifiers=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=276, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: required KMFA v1.2 HTML/UIUX/report samples are present (html=45, core=7) |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS: raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS: quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS: no KMFA Python float money usage found |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: root checked; projects checked KMFA; errors=0; warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: root checked; projects checked KMFA; errors=0; warnings=0 |
| `git diff --check -- README.md governance/projects.yaml KMFA` | PASS: no whitespace errors |
| `find KMFA -path 'KMFA/taskpack/v1_2/*' -prune -o -path 'KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/*' -prune -o -type f \( -name '*.zip' -o -name '*.xls' -o -name '*.xlsx' -o -name '*.pdf' -o -name '*.sqlite' -o -name '*.db' -o -name '*.sqlite-shm' -o -name '*.sqlite-wal' \) -print` | PASS: no raw archive/spreadsheet/PDF/database files found outside taskpack baseline exclusions |
| `private path and unrelated uploaded finance zip marker scan` | PASS: no matches |
| `rg -n --hidden -i '(sk-[A-Za-z0-9_-]{20,}\|api[_-]?key\s*[:=]\|password\s*[:=]\|secret\s*[:=]\|银行流水\|纳税申报\|工资明细\|身份证\|银行卡号)' KMFA -g '!KMFA/taskpack/v1_2/**' -g '!KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/**'` | PASS_WITH_POLICY_TEXT_MATCHES_ONLY |

## 说明

- `private_value_hash_recorded=40` 来自仓库外私有 CSV；公开仓库只记录 hash/private refs/status，不记录 CSV 路径或字段明文。
- `private_value_pending=5` 是预期结果：1 个 Excel A0 候选已机器复核但仍需后续私有映射或 owner/授权人工确认。
- Excel resolution manifest 只记录候选/file id、字段 key、计数、状态和证据引用，不记录业务明文值。
- Excel owner decision packet 只定义允许决策和所需证据，并已有专门 validator 覆盖；不等同于 Q4/Q5 确认，不完成 S05-P2。
- Excel owner decision intake contract 只验证后续决策记录格式、actor role、禁止明文键和 Q4/Q5 边界；当前没有 owner 决策记录，不完成 S05-P2。
- Excel owner decision templates 只是三种允许决策的 public-safe 非决策模板；当前没有 active owner 决策记录，不完成 S05-P2。
- Excel completion gate 是关闭 S05-P2 的硬门：当前 5 条 Excel 字段 pending 且没有 active owner/授权决策，因此默认命令返回 BLOCKED；`--expect-blocked` 用于记录当前阻断证据。
- 本机提供的 `销售绩效考核.zip` 整包 hash/size 与登记 source package 不匹配；真实 9 个业务成员 hash 与 Stage2 Ring4 registry 匹配。
- 未提交 raw PDF、Excel、zip、私有 CSV、合同额、支出合计、毛利、毛利率、成本分类明文、银行流水、合同、薪资、税务申报或业务明细。
