# PHASE S2PMT03 SMTP Identity A-017

## 状态

- status: `completed_local_validation`
- phase: `S2PM`
- task_id: `S2PMT03`
- finding_id: `A-017`
- finding_title: `SMTP delivery_id 不含正文/内容版本，且缺标准 Message-ID`
- completed_at: `2026-06-26T20:53:17+10:00`

## 范围

本记录补强 V7.1 inherited P1 finding `A-017` 的本地 SMTP identity 证据：

- `deliver_notification` 显式生成 `mail_key`、`content_revision_id`、`delivery_id` 和标准 `Message-ID`。
- `mail_key` 由 `cycle_id + product_id + recipient` 派生；daily runner 路径传入日期 cycle 与 `M1` 邮件产品。
- `content_revision_id` 由 subject、plain body hash 和 HTML body hash 派生；同内容重试保持不变，正文或 HTML 修订会变化。
- 实际 mock SMTP message 写入 `X-ADP-Delivery-ID`、`X-ADP-Mail-Key`、`X-ADP-Content-Revision-ID` 和标准 `Message-ID`。
- delivery report 写明 resend policy：同 `mail_key + content_revision_id` 重试保持同一 `Message-ID`；内容修订必须显式 supersede 或 resend。

## 非范围

本记录不启用真实 SMTP，不安装 scheduler，不改变生产授权，不修改公共 Schema、DB migration、source adapter、ranking、`CURRENT` 或 V7.1/V7.2 合同文件；不关闭 inherited P0/P1；不声明 `INTEGRATED_PRODUCTION_ACCEPTED`、`DAILY_OPERATION` 或 Stage 2 生产通过。

## 代码证据

- `arxiv-daily-push/src/arxiv_daily_push/smtp_delivery.py`
- `arxiv-daily-push/src/arxiv_daily_push/scheduled_execution.py`
- `arxiv-daily-push/src/arxiv_daily_push/local_runner.py`
- `arxiv-daily-push/tests/test_smtp_delivery.py`
- `governance/run_manifests/ADP-S2PMT03-SMTP-IDENTITY-A017-20260626.json`

## 验证

- `py_compile`: PASS
- `python3 -m unittest arxiv-daily-push/tests/test_smtp_delivery.py arxiv-daily-push/tests/test_notifications.py arxiv-daily-push/tests/test_scheduled_execution.py -q`: 14 OK
- `python3 -m unittest arxiv-daily-push/tests/test_local_runner.py -q`: 8 OK
- `python3 -m unittest arxiv-daily-push/tests/test_smtp_delivery.py arxiv-daily-push/tests/test_notifications.py arxiv-daily-push/tests/test_scheduled_execution.py arxiv-daily-push/tests/test_local_runner.py -q`: 22 OK
- `python3 -m unittest arxiv-daily-push/tests/test_user_center_candidate_pool.py arxiv-daily-push/tests/test_stage2_owner_ux.py -q`: 16 OK
- `python3 -m unittest arxiv-daily-push/tests/test_trial_recovery.py -q`: 1 OK
- `python3 -m unittest discover -s arxiv-daily-push/tests -q`: 511 OK
- `python3 scripts/validate_project_governance.py --project arxiv-daily-push`: errors 0 / warnings 0
- `python3 scripts/validate_governance_sync.py`: errors 0 / warnings 0
- `python3 arxiv-daily-push/docs/pursuing_goal/v7_2/tools/validate_v7_2_contract.py --root arxiv-daily-push/docs/pursuing_goal/v7_2`: PASS
- `python3 -m json.tool governance/run_manifests/ADP-S2PMT03-SMTP-IDENTITY-A017-20260626.json`: PASS
- `git diff --check`: PASS

## 剩余阻断

- 本修复只提供 A-017 的本地身份与幂等证据。
- inherited V7.1 P0=8 / P1=37 在独立复审前保持 open。
- S2PMT07 final gate precheck 仍为 blocked。
