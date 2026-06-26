# PHASE S2PMT03 State History A-007

## 状态

- status: `completed_local_validation`
- phase: `S2PM`
- task_id: `S2PMT03`
- finding_id: `A-007`
- finding_title: `状态历史不验证声明的 from_state`
- completed_at: `2026-06-26T20:12:40+10:00`

## 范围

本记录只覆盖 V7.1 inherited P1 finding `A-007` 的 RunRecord state history 局部修复证据：

- `state_history[0]` 初始化必须包含 `reason=initial` 和可解析 `at`。
- 每条 `state_history` 必须有非空 `reason`。
- 每条 `state_history` 必须有可解析 ISO `at`。
- `state_history.at` 必须按记录顺序非递减。
- 既有 `from_state` 必须匹配上一条 `to_state`、非法跳转必须失败、`current_state` 必须匹配历史末态的规则继续保留。

## 非范围

本记录不启用 SMTP、scheduler、Release、production restore、真实生产队列、公共 Schema、DB migration、source adapter、ranking、`CURRENT` 或 V7.1/V7.2 合同文件；不关闭 inherited P0/P1；不声明 `INTEGRATED_PRODUCTION_ACCEPTED`、`DAILY_OPERATION` 或 Stage 2 生产通过。

## 代码证据

- `arxiv-daily-push/src/arxiv_daily_push/state_machine.py`
- `arxiv-daily-push/tests/test_state_machine.py`
- `governance/run_manifests/ADP-S2PMT03-STATE-HISTORY-A007-20260626.json`

## 验证

- `py_compile`: PASS
- `python3 -m unittest arxiv-daily-push/tests/test_state_machine.py arxiv-daily-push/tests/test_stage2_lease_fencing.py -q`: 14 OK
- `python3 -m unittest arxiv-daily-push/tests/test_state_machine.py arxiv-daily-push/tests/test_stage2_lease_fencing.py arxiv-daily-push/tests/test_pipeline.py arxiv-daily-push/tests/test_handoff.py -q`: 22 OK
- `python3 -m unittest arxiv-daily-push/tests/test_user_center_candidate_pool.py -q`: 7 OK
- `python3 -m unittest discover -s arxiv-daily-push/tests -q`: 502 OK
- `scripts/validate_project_governance.py --project arxiv-daily-push`: errors 0 / warnings 0
- `docs/pursuing_goal/v7_2/tools/validate_v7_2_contract.py --root docs/pursuing_goal/v7_2`: PASS
- `python3 -m json.tool governance/run_manifests/ADP-S2PMT03-STATE-HISTORY-A007-20260626.json`: OK
- `git diff --check`: PASS

## 剩余阻断

- 本修复只提供 A-007 的局部实现与回归测试证据。
- inherited V7.1 P0=8 / P1=37 在独立复审前保持 open。
- S2PMT07 final gate precheck 仍为 blocked。
