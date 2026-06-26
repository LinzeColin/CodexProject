# PHASE S2PMT03 Optimistic Fencing A-009

## 状态

- status: `completed_local_validation`
- phase: `S2PM`
- task_id: `S2PMT03`
- finding_id: `A-009`
- finding_title: `状态转换缺少乐观并发控制与 fencing token`
- completed_at: `2026-06-26T20:30:07+10:00`

## 范围

本记录只覆盖 V7.1 inherited P1 finding `A-009` 的本地乐观并发与 fencing 局部修复证据：

- 本地 CAS claim 仓库以单锁模拟数据库 `UPDATE ... WHERE work_id=? AND row_version=?` 的原子语义。
- 同一旧 `row_version` 下 100 个并发 claimant 只能有 1 个 `affected_rows=1`。
- 失败 claimant 返回 `affected_rows=0` 和 `row_version compare-and-swap failed`。
- fenced state transition 同时校验 `row_version` 和 `fencing_token`；过期 worker 写入返回 `affected_rows=0`。
- claim attempt 记录 append-only event log，用于审计每次 claimant 的命中/阻断结果。

## 非范围

本记录不启用 SMTP、scheduler、Release、production restore、真实生产队列、公共 Schema、DB migration、source adapter、ranking、`CURRENT` 或 V7.1/V7.2 合同文件；不关闭 inherited P0/P1；不声明 `INTEGRATED_PRODUCTION_ACCEPTED`、`DAILY_OPERATION` 或 Stage 2 生产通过。

## 代码证据

- `arxiv-daily-push/src/arxiv_daily_push/stage2_lease_fencing.py`
- `arxiv-daily-push/tests/test_stage2_lease_fencing.py`
- `governance/run_manifests/ADP-S2PMT03-OPTIMISTIC-FENCING-A009-20260626.json`

## 验证

- `py_compile`: PASS
- `python3 -m unittest arxiv-daily-push/tests/test_stage2_lease_fencing.py arxiv-daily-push/tests/test_state_machine.py -q`: 17 OK
- `python3 -m unittest arxiv-daily-push/tests/test_stage2_lease_fencing.py arxiv-daily-push/tests/test_state_machine.py arxiv-daily-push/tests/test_pipeline.py arxiv-daily-push/tests/test_handoff.py -q`: 25 OK
- `python3 -m unittest arxiv-daily-push/tests/test_user_center_candidate_pool.py -q`: 7 OK
- `python3 -m unittest discover -s arxiv-daily-push/tests -q`: 505 OK
- `scripts/validate_project_governance.py --project arxiv-daily-push`: errors 0 / warnings 0
- `docs/pursuing_goal/v7_2/tools/validate_v7_2_contract.py --root docs/pursuing_goal/v7_2`: PASS
- `python3 -m json.tool governance/run_manifests/ADP-S2PMT03-OPTIMISTIC-FENCING-A009-20260626.json`: OK
- `git diff --check`: PASS

## 剩余阻断

- 本修复只提供 A-009 的局部实现与回归测试证据。
- inherited V7.1 P0=8 / P1=37 在独立复审前保持 open。
- S2PMT07 final gate precheck 仍为 blocked。
