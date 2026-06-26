# PHASE S2PAT05 ROI Disclosure A-018

## 状态

- status: `completed_local_validation`
- phase: `S2PA`
- task_id: `S2PAT05`
- finding_id: `A-018`
- finding_title: `V7 要求展示 ROI，但旧邮件验证明确禁止 ROI`
- completed_at: `2026-06-26T21:05:24+10:00`

## 范围

本记录补强 V7.1 inherited P1 finding `A-018` 的本地 ROI 披露证据：

- B1 report/email package 不再把所有 `ROI` 字符串一概视为邮件违规。
- B1 package 新增 `roi_disclosure` 结构，区分 `Expected ROI` 与 `Actual ROI`。
- `Expected ROI` 只能作为假设披露，必须带 assumptions、evidence_refs、cost_basis 和 probability_basis。
- `Actual ROI` 默认为 `not_calculable`，只有在有可验证成本、收益和证据时才允许 `calculated`。
- 可见文本禁止保证收益、保证回报、稳赚、必赚等无证据收益承诺。
- 当前 Email V1 runtime 仍不展示内部 `roi_total_score` 排名词；本修复只让 B1 package validator 接受结构化 ROI 披露并阻断无证据收益声明。

## 非范围

本记录不启用真实 SMTP，不安装 scheduler，不上传 Release，不改 Email V1 路由，不改公共 Schema、DB migration、source adapter、ranking、`CURRENT` 或 V7.1/V7.2 合同文件；不关闭 inherited P0/P1；不声明 `INTEGRATED_PRODUCTION_ACCEPTED`、`DAILY_OPERATION` 或 Stage 2 生产通过。

## 代码证据

- `arxiv-daily-push/src/arxiv_daily_push/stage1_b1_report.py`
- `arxiv-daily-push/tests/test_stage1_b1_report.py`
- `governance/run_manifests/ADP-S2PAT05-ROI-DISCLOSURE-A018-20260626.json`

## 验证

- `py_compile`: PASS
- `python3 -m unittest arxiv-daily-push/tests/test_stage1_b1_report.py -q`: 12 OK
- `python3 -m unittest arxiv-daily-push/tests/test_mail_templates.py arxiv-daily-push/tests/test_scheduled_execution.py -q`: 7 OK
- `python3 -m unittest arxiv-daily-push/tests/test_stage1_b1_report.py arxiv-daily-push/tests/test_mail_templates.py arxiv-daily-push/tests/test_scheduled_execution.py -q`: 19 OK
- `python3 -m unittest discover -s arxiv-daily-push/tests -q`: 513 OK
- `python3 scripts/validate_project_governance.py --project arxiv-daily-push`: errors 0 / warnings 0
- `python3 scripts/validate_governance_sync.py`: errors 0 / warnings 0
- `python3 arxiv-daily-push/docs/pursuing_goal/v7_2/tools/validate_v7_2_contract.py --root arxiv-daily-push/docs/pursuing_goal/v7_2`: PASS
- `python3 -m json.tool governance/run_manifests/ADP-S2PAT05-ROI-DISCLOSURE-A018-20260626.json`: PASS
- `git diff --check`: PASS

## 剩余阻断

- 本修复只提供 A-018 的本地结构化 ROI 披露证据。
- inherited V7.1 P0=8 / P1=37 在独立复审前保持 open。
- S2PMT07 final gate precheck 仍为 blocked。
