# PHASE S2PMT01 Input URL Safety A-012

## 状态

- status: `completed_local_validation`
- phase: `S2PM`
- task_id: `S2PMT01`
- finding_id: `A-012`
- finding_title: `邮件原文链接未限制 URL scheme`
- completed_at: `2026-06-26T20:36:13+10:00`

## 范围

本记录补强 V7.1 inherited P1 finding `A-012` 的 B1 报告/邮件构建入口证据：

- `daily_input.source_item.canonical_url` 在报告和邮件渲染前必须通过 `sanitize_public_url`。
- `daily_input.source_item.content_refs[].uri/url` 在报告和邮件渲染前必须通过 `sanitize_public_url`。
- `javascript:`、`data:`、`file:`、带 userinfo 凭据的 URL 必须在输入级 blocked。
- blocked package 不携带 `report_markdown`、`email_plain` 或 `email_html`，避免危险 URL 进入前台内容或正式 artifact。

## 非范围

本记录不启用 SMTP、scheduler、Release、production restore、真实生产队列、公共 Schema、DB migration、source adapter、ranking、`CURRENT` 或 V7.1/V7.2 合同文件；不关闭 inherited P0/P1；不声明 `INTEGRATED_PRODUCTION_ACCEPTED`、`DAILY_OPERATION` 或 Stage 2 生产通过。

## 代码证据

- `arxiv-daily-push/src/arxiv_daily_push/stage1_b1_report.py`
- `arxiv-daily-push/tests/test_stage1_b1_report.py`
- `governance/run_manifests/ADP-S2PMT01-INPUT-URL-SAFETY-A012-20260626.json`

## 验证

- `py_compile`: PASS
- `python3 -m unittest arxiv-daily-push/tests/test_stage1_b1_report.py arxiv-daily-push/tests/test_security_boundary.py arxiv-daily-push/tests/test_mail_templates.py -q`: 16 OK
- `python3 -m unittest arxiv-daily-push/tests/test_stage1_b1_report.py arxiv-daily-push/tests/test_security_boundary.py arxiv-daily-push/tests/test_mail_templates.py arxiv-daily-push/tests/test_stage1_historical_previews.py -q`: 21 OK
- `python3 -m unittest arxiv-daily-push/tests/test_user_center_candidate_pool.py -q`: 7 OK
- `python3 -m unittest discover -s arxiv-daily-push/tests -q`: 507 OK
- `scripts/validate_project_governance.py --project arxiv-daily-push`: errors 0 / warnings 0
- `docs/pursuing_goal/v7_2/tools/validate_v7_2_contract.py --root docs/pursuing_goal/v7_2`: PASS
- `python3 -m json.tool governance/run_manifests/ADP-S2PMT01-INPUT-URL-SAFETY-A012-20260626.json`: OK
- `git diff --check`: PASS

## 剩余阻断

- 本修复只提供 A-012 的输入级 URL 安全补强证据。
- inherited V7.1 P0=8 / P1=37 在独立复审前保持 open。
- S2PMT07 final gate precheck 仍为 blocked。
