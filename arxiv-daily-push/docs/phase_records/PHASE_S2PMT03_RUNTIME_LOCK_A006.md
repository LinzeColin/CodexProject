# PHASE S2PMT03 Runtime Lock A-006

## 状态

- status: `completed_local_validation`
- phase: `S2PM`
- task_id: `S2PMT03`
- finding_id: `A-006`
- finding_title: `tick 写入异常时 runtime.lock 永久残留`
- completed_at: `2026-06-26T20:02:43+10:00`

## 范围

本记录只覆盖 V7.1 inherited P1 finding `A-006` 的 Stage 1 runtime lock 局部修复证据：

- `run_tick` 的 `runtime.lock` 获取与释放改为私有 context manager。
- lock payload 增加 `owner_id`、`host`、`pid`、`lease_until`、`fencing_token` 和 lease 秒数。
- checkpoint 写入前执行一次续租，并要求磁盘锁中的 `fencing_token` 与当前 owner 匹配。
- heartbeat 或 checkpoint 任一步写入异常时，已获取的 `runtime.lock` 必须在 `finally` 中释放。
- 对过期且 owner 进程已死亡的旧 lock，允许本次 tick 先安全接管，再使用新的 fencing token 写入。

## 非范围

本记录不启用 SMTP、scheduler、Release、production restore、真实生产队列、公共 Schema、DB migration、source adapter、ranking、`CURRENT` 或 V7.1/V7.2 合同文件；不关闭 inherited P0/P1；不声明 `INTEGRATED_PRODUCTION_ACCEPTED`、`DAILY_OPERATION` 或 Stage 2 生产通过。

## 代码证据

- `arxiv-daily-push/src/arxiv_daily_push/stage1_runtime.py`
- `arxiv-daily-push/tests/test_stage1_runtime.py`
- `governance/run_manifests/ADP-S2PMT03-RUNTIME-LOCK-A006-20260626.json`

## 验证

- `py_compile`: PASS
- `python3 -m unittest arxiv-daily-push/tests/test_stage1_runtime.py -q`: 14 OK
- `python3 -m unittest arxiv-daily-push/tests/test_stage1_runtime.py arxiv-daily-push/tests/test_s2pmt07_review_receipts.py -q`: 17 OK
- `python3 -m unittest arxiv-daily-push/tests/test_user_center_candidate_pool.py -q`: 5 OK
- `python3 -m unittest discover -s arxiv-daily-push/tests -q`: 498 OK
- `scripts/validate_project_governance.py --project arxiv-daily-push`: errors 0 / warnings 0
- `docs/pursuing_goal/v7_2/tools/validate_v7_2_contract.py --root docs/pursuing_goal/v7_2`: PASS
- `python3 -m json.tool governance/run_manifests/ADP-S2PMT03-RUNTIME-LOCK-A006-20260626.json`: OK
- `git diff --check`: PASS

## 剩余阻断

- 本修复只提供 A-006 的局部实现与回归测试证据。
- inherited V7.1 P0=8 / P1=37 在独立复审前保持 open。
- S2PMT07 final gate precheck 仍为 blocked。
