# S04-P2 测试结果

更新时间: 2026-06-29

## 已运行

```bash
python3 -m unittest KMFA.tests.test_field_standardization -q
```

结果:

```text
Ran 5 tests
OK
```

```bash
python3 KMFA/tools/check_no_float_money.py
```

结果:

```text
PASS: no KMFA Python float money usage found
```

```bash
python3 -m unittest KMFA.tests.test_amount_tools -q
python3 -m unittest KMFA.tests.test_source_priority -q
python3 -m unittest KMFA.tests.test_source_check_matrix -q
python3 -m unittest KMFA.tests.test_file_import_register -q
python3 KMFA/tools/check_required_html.py
python3 KMFA/tools/no_omission_check.py
python3 KMFA/tools/immutability_policy_check.py
python3 KMFA/tools/metadata_protocol_check.py
python3 KMFA/tools/check_report_grade_gate.py
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
git diff --check -- README.md governance/projects.yaml KMFA
find KMFA -type f \( -name '*.zip' -o -name '*.xls' -o -name '*.xlsx' -o -name '*.pdf' -o -name '*.sqlite' -o -name '*.db' -o -name '*.sqlite-shm' -o -name '*.sqlite-wal' \) -print
```

结果:

```text
PASS: KMFA metadata protocol check passed
PASS: KMFA no omission check passed
PASS: required KMFA v1.2 HTML/UIUX/report samples are present
PASS: KMFA immutability policy check passed
PASS: KMFA report grade gate check passed
PASS: CodexProject governance validation errors 0 / warnings 0
PASS: git diff --check no output
PASS: sensitive file suffix scan no output
```

## 待最终复跑

Stage 4 全部 Phase 完成后，需在 Stage 4 整体复审中复跑完整 validator 组合并修复复审问题后才允许整体上传 GitHub。
