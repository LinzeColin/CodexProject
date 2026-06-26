# PHASE S2PMT03 State Consistency A-008

## 状态

- status: `completed_local_validation`
- phase: `S2PM`
- task_id: `S2PMT03`
- finding_id: `A-008`
- finding_title: `current_state 与 state_history 末态可不一致`
- completed_at: `2026-06-26T20:24:28+10:00`

## 范围

本记录只覆盖 V7.1 inherited P1 finding `A-008` 的 RunRecord 状态一致性局部修复证据：

- `current_state` 必须匹配 `state_history` 末条 `to_state`。
- `status` 必须匹配 `current_state` 的显式状态映射。
- RunRecord 记录 `schema_version=1`。
- RunRecord 记录 `row_version`，且 `row_version == len(state_history) - 1`。
- 状态转换时 `row_version` 随有效 transition 单调递增。

## 非范围

本记录不启用 SMTP、scheduler、Release、production restore、真实生产队列、公共 Schema、DB migration、source adapter、ranking、`CURRENT` 或 V7.1/V7.2 合同文件；不关闭 inherited P0/P1；不声明 `INTEGRATED_PRODUCTION_ACCEPTED`、`DAILY_OPERATION` 或 Stage 2 生产通过。

## 代码证据

- `arxiv-daily-push/src/arxiv_daily_push/state_machine.py`
- `arxiv-daily-push/tests/test_state_machine.py`
- `governance/run_manifests/ADP-S2PMT03-STATE-CONSISTENCY-A008-20260626.json`

## 验证

- `py_compile`: PASS
- `python3 -m unittest arxiv-daily-push/tests/test_state_machine.py arxiv-daily-push/tests/test_pipeline.py arxiv-daily-push/tests/test_handoff.py arxiv-daily-push/tests/test_stage2_lease_fencing.py -q`: 24 OK
- `python3 -m unittest arxiv-daily-push/tests/test_user_center_candidate_pool.py -q`: 7 OK
- `python3 -m unittest discover -s arxiv-daily-push/tests -q`: 504 OK
- `scripts/validate_project_governance.py --project arxiv-daily-push`: errors 0 / warnings 0
- `docs/pursuing_goal/v7_2/tools/validate_v7_2_contract.py --root docs/pursuing_goal/v7_2`: PASS
- `python3 -m json.tool governance/run_manifests/ADP-S2PMT03-STATE-CONSISTENCY-A008-20260626.json`: OK
- `git diff --check`: PASS

## 剩余阻断

- 本修复只提供 A-008 的局部实现与回归测试证据。
- inherited V7.1 P0=8 / P1=37 在独立复审前保持 open。
- S2PMT07 final gate precheck 仍为 blocked。
